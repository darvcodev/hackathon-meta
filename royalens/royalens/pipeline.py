"""Flujo completo: foto -> SAM (hoja + lesiones) -> medición -> Muse -> resultado."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import numpy as np
from PIL import Image

from . import config
from .analysis import (
    Instance,
    Severity,
    cherries_from,
    dae_class,
    general_view,
    lesion_details,
    main_leaf,
    measure,
    render_overlay,
    ripeness,
    rust_lesions,
    union,
    visible_leaves,
)
from .meta_api import diagnose, interpret_ripeness, make_client, prepare_image, segment, segment_tiled


@dataclass
class Diagnosis:
    overlay: Image.Image
    severity: Severity
    leaf_prompt_used: str | None
    lesions: list[Instance]
    muse: dict
    warnings: list[str] = field(default_factory=list)
    measurable: bool = False  # solo una medición válida entra al historial del lote
    leaves_in_photo: int = 0
    discarded: int = 0
    dae: int | None = None
    details: dict = field(default_factory=dict)
    general: dict | None = None

    def as_dict(self) -> dict:
        return {
            "medicion_sam": self.severity.as_dict(),
            "detalle_lesiones": self.details,
            "vista_general": self.general,
            "medible": self.measurable,
            "prompt_hoja": self.leaf_prompt_used,
            "hojas_en_foto": self.leaves_in_photo,
            "descartadas_por_color": self.discarded,
            "clase_dae": self.dae,
            "lesiones": [
                {"id": i.object_id, "caja": i.box, "confianza": i.confidence}
                for i in self.lesions
            ],
            "interpretacion_muse": self.muse,
            "avisos": self.warnings,
        }


async def analyze(
    image: Image.Image,
    lesion_prompts: list[str] | None = None,
    min_confidence: float = config.MIN_CONFIDENCE,
) -> Diagnosis:
    lesion_prompts = [p.strip() for p in (lesion_prompts or config.DEFAULT_LESION_PROMPTS) if p.strip()]
    client = make_client()
    img, data_url = prepare_image(image)
    size = img.size
    shape = (size[1], size[0])
    warnings: list[str] = []

    # El primer prompt de hoja y las lesiones van en paralelo; el otro es solo un respaldo.
    first_leaf_prompt, *fallback_prompts = config.LEAF_PROMPTS
    leaves, *lesion_results = await asyncio.gather(
        segment(client, data_url, first_leaf_prompt, size, min_confidence),
        *(segment(client, data_url, p, size, min_confidence) for p in lesion_prompts),
    )
    leaf_prompt_used = first_leaf_prompt if leaves else None
    for prompt in fallback_prompts:
        if leaves:
            break
        leaves = await segment(client, data_url, prompt, size, min_confidence)
        leaf_prompt_used = prompt if leaves else None

    leaf = main_leaf(leaves, shape)
    leaf_mask = leaf.mask if leaf else np.zeros(shape, dtype=bool)
    leaf_share = 100.0 * leaf_mask.sum() / leaf_mask.size
    measurable = bool(leaf_share >= config.MIN_LEAF_PERCENT)

    candidates = [inst for group in lesion_results for inst in group]
    lesions, discarded = [], 0
    if measurable:
        lesions, discarded = rust_lesions(img, leaf_mask, candidates)
    severity = measure(leaf_mask, lesions)
    # En una foto de varias hojas también se revisan las demás, aunque no entren a la medición.
    others = visible_leaves(leaves, shape)
    general, general_lesions = general_view(img, others, candidates)

    muse = await diagnose(
        client,
        data_url,
        leaf_found=measurable,
        lesion_count=severity.lesion_count,
        percent=severity.percent,
        level=severity.level,
        leaves_checked=general["hojas"] if general else 0,
        leaves_with_spots=general["con_manchas"] if general else 0,
    )
    # Un solo motivo cuando no hay medición; los demás avisos solo aplican si la hubo.
    if muse.get("es_hoja_de_cafe") is False:
        measurable = False
        warnings.append("Esta foto no parece una hoja de café. No se cuenta en el lote.")
    elif not leaf:
        warnings.append("No se pudo medir: no se ve una hoja completa en la foto.")
    elif not measurable:
        if not general:
            warnings.append("No se pudo medir: la hoja se ve muy lejos. Acérquese hasta que ocupe buena parte de la foto.")
    elif muse.get("calidad_foto") == "mala":
        measurable = False
        warnings.append("La calidad de la foto es baja: no se cuenta en el lote. Repita la toma con mejor luz y enfoque.")
    elif muse.get("cara_visible") == "haz" and not lesions:
        # La roya sale sobre todo en el envés: por el haz no se puede dar la hoja por sana.
        measurable = False
        warnings.append("La foto muestra el haz de la hoja y la roya se ve sobre todo en el envés. Voltéela y repita la foto.")
    else:
        others = sum(1 for i in leaves if i is not leaf and i.mask.sum() >= 0.25 * leaf.mask.sum())
        if others:
            warnings.append("Hay varias hojas en la foto: se midió solo la del centro. Para mayor precisión, tome una sola.")
        if muse.get("signos_de_roya") is True and not lesions:
            warnings.append("Muse ve posibles signos de roya que la medición no marcó. Revise el envés y repita la foto.")
        elif muse.get("signos_de_roya") is False and lesions:
            warnings.append("Muse no ve signos claros de roya: las manchas medidas podrían tener otra causa.")
        if discarded:
            warnings.append("Se descartaron manchas cuyo color no corresponde a roya.")
        if severity.percent >= config.DEFOLIATION_RISK_PERCENT:
            warnings.append("Con más del 30 % de la hoja afectada, Cenicafé reporta que puede caer antes de tiempo.")

    if measurable or not general:
        overlay = render_overlay(img, leaf_mask, lesions)
    else:
        overlay = render_overlay(img, union(others, shape), general_lesions)
        lesions = general_lesions
    return Diagnosis(
        overlay,
        severity,
        leaf_prompt_used,
        lesions,
        muse,
        warnings,
        measurable=measurable,
        leaves_in_photo=len(leaves),
        discarded=discarded,
        dae=dae_class(severity.percent) if measurable else None,
        details=lesion_details(leaf_mask, lesions) if measurable else {},
        general=general if muse.get("es_hoja_de_cafe") is not False else None,
    )


@dataclass
class Cherry:
    instance: Instance
    state: str


@dataclass
class RipenessResult:
    cherries: list[Cherry]
    counts: dict[str, int]
    muse: dict
    warnings: list[str] = field(default_factory=list)
    measurable: bool = False

    def as_dict(self) -> dict:
        return {
            "medible": self.measurable,
            "total": len(self.cherries),
            "conteo": self.counts,
            "interpretacion_muse": self.muse,
            "avisos": self.warnings,
        }


async def analyze_ripeness(image: Image.Image, min_confidence: float = config.MIN_CONFIDENCE) -> RipenessResult:
    """Foto -> SAM (cerezas) -> estado por color -> conteo -> Muse explica."""
    client = make_client()
    img, data_url = prepare_image(image)
    found = await segment_tiled(client, img, config.CHERRY_PROMPT, min_confidence)

    rgb = np.asarray(img.convert("RGB"))
    cherries = [Cherry(inst, ripeness(rgb, inst.mask)) for inst in cherries_from(found)]
    counts = {state: sum(1 for c in cherries if c.state == state) for state in config.RIPENESS_STATES}

    muse = await interpret_ripeness(client, data_url, counts, len(cherries))

    # Muse confirma el tipo de foto: SAM también encuentra cualquier otro fruto redondo.
    warnings: list[str] = []
    areas = [int(c.instance.mask.sum()) for c in cherries]
    typical_share = 100.0 * float(np.median(areas)) / (img.width * img.height) if areas else 0.0
    measurable = len(cherries) >= config.MIN_CHERRIES_FOR_PERCENT and typical_share >= config.MIN_CHERRY_PERCENT
    if muse.get("es_racimo_de_cafe") is False:
        measurable = False
        warnings.append("Esta foto no parece un racimo de café. No se cuenta en el lote.")
    elif not cherries:
        warnings.append("No se contaron cerezas. Tome la foto más cerca del racimo, con buena luz y enfoque.")
    elif typical_share < config.MIN_CHERRY_PERCENT:
        warnings.append("Las cerezas se ven muy lejos. Acérquese a un racimo y repita la foto.")
    elif len(cherries) < config.MIN_CHERRIES_FOR_PERCENT:
        warnings.append("Hay muy pocas cerezas en la foto para calcular un porcentaje.")
    elif muse.get("calidad_foto") == "mala":
        warnings.append("La calidad de la foto es baja; repita la toma con mejor luz y enfoque.")
    return RipenessResult(cherries if measurable else [], counts if measurable else dict.fromkeys(counts, 0), muse, warnings, measurable)

