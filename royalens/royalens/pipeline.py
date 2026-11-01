"""Flujo completo: foto -> SAM (hoja + lesiones) -> medición -> Muse -> resultado."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

from PIL import Image

from . import config
from .analysis import Instance, Severity, measure, render_overlay, union
from .meta_api import diagnose, make_client, prepare_image, segment


@dataclass
class Diagnosis:
    overlay: Image.Image
    severity: Severity
    leaf_prompt_used: str | None
    lesions: list[Instance]
    muse: dict
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "medicion_sam": self.severity.as_dict(),
            "prompt_hoja": self.leaf_prompt_used,
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

    # Hoja y lesiones en paralelo: son peticiones independientes a SAM.
    leaf_task = asyncio.gather(
        *(segment(client, data_url, p, size, min_confidence) for p in config.LEAF_PROMPTS)
    )
    lesion_task = asyncio.gather(
        *(segment(client, data_url, p, size, min_confidence) for p in lesion_prompts)
    )
    leaf_results, lesion_results = await asyncio.gather(leaf_task, lesion_task)

    leaf_prompt_used = None
    leaves: list[Instance] = []
    for prompt, found in zip(config.LEAF_PROMPTS, leaf_results):
        if found:
            leaf_prompt_used, leaves = prompt, found
            break
    leaf_mask = union(leaves, shape)
    if not leaf_mask.any():
        warnings.append("No se detectó ninguna hoja: el porcentaje no es confiable.")

    lesions = [inst for group in lesion_results for inst in group]
    severity = measure(leaf_mask, lesions)

    muse = await diagnose(
        client,
        data_url,
        leaf_found=bool(leaf_mask.any()),
        lesion_count=severity.lesion_count,
        percent=severity.percent,
        level=severity.level,
    )
    if muse.get("es_hoja_de_cafe") is False:
        warnings.append("Muse indica que la foto no parece una hoja de café.")
    if muse.get("calidad_foto") == "mala":
        warnings.append("La calidad de la foto es baja; repite la toma con mejor luz y enfoque.")

    overlay = render_overlay(img, leaf_mask, lesions)
    return Diagnosis(overlay, severity, leaf_prompt_used, lesions, muse, warnings)
