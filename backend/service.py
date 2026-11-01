"""Une los modos demo y real bajo una misma respuesta para la interfaz."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from PIL import Image

from royalens import config  # carga royalens/.env
from royalens.analysis import Instance
from royalens.meta_api import prepare_image
from royalens.pipeline import analyze

from . import demo, store

ESTADOS = ["verde", "pinton", "maduro", "sobremaduro"]


class MaduracionNoConectada(RuntimeError):
    pass


def modo() -> str:
    # Sin valor se usa la API real: un error de clave nunca se disfraza de resultado.
    return "demo" if os.getenv("ROYALENS_MODE", "real").lower() == "demo" else "real"


def _caja(box: tuple[int, int, int, int], size: tuple[int, int]) -> list[float]:
    w, h = size
    left, top, right, bottom = box
    return [
        round(max(left, 0) / w, 4),
        round(max(top, 0) / h, 4),
        round(min(right, w) / w, 4),
        round(min(bottom, h) / h, 4),
    ]


def _base(tipo: str, lote: int, img: Image.Image) -> dict:
    escaneo_id = store.nuevo_id()
    nombre = f"{escaneo_id}.jpg"
    img.save(store.MEDIA_DIR / nombre, quality=88)
    return {
        "id": escaneo_id,
        "tipo": tipo,
        "lote": lote,
        "creado": datetime.now(timezone.utc).isoformat(),
        "modo": modo(),
        "ejemplo": False,
        "ancho": img.width,
        "alto": img.height,
        "imagen_url": f"/media/{nombre}",
    }


def _confianza(instancias: list[Instance]) -> float | None:
    valores = [i.confidence for i in instancias if i.confidence is not None]
    return round(sum(valores) / len(valores), 2) if valores else None


def _interpretacion_muse(muse: dict) -> dict:
    # Si Muse no devolvió JSON, se muestra su texto tal cual, sin rellenar nada.
    return {
        "lo_que_se_ve": muse.get("lo_que_se_ve") or muse.get("_sin_formato") or "",
        "recomendacion": muse.get("recomendacion") or "",
        "otras_causas": muse.get("otras_causas_posibles") or [],
        "consejo_foto": muse.get("consejo_foto") or "",
    }


async def analizar_roya(image: Image.Image, lote: int) -> dict:
    img, _ = prepare_image(image)
    if modo() == "demo":
        r = demo.analizar_roya(img)
        overlay, severidad, lesiones = r["overlay"], r["severidad"], r["lesiones"]
        interpretacion, avisos = r["interpretacion"], r["avisos"]
    else:
        d = await analyze(img)
        overlay, severidad, lesiones = d.overlay, d.severity, d.lesions
        interpretacion, avisos = _interpretacion_muse(d.muse), d.warnings

    escaneo = _base("roya", lote, img)
    nombre_overlay = f"{escaneo['id']}_overlay.jpg"
    overlay.save(store.MEDIA_DIR / nombre_overlay, quality=88)
    escaneo.update(
        overlay_url=f"/media/{nombre_overlay}",
        medicion={
            "porcentaje": round(severidad.percent, 1),
            "nivel": severidad.level,
            "lesiones": severidad.lesion_count,
            "hoja_detectada": severidad.leaf_pixels > 0,
            "confianza": _confianza(lesiones),
        },
        detecciones=[
            {"id": i.object_id, "caja": _caja(i.box, img.size), "confianza": i.confidence}
            for i in lesiones
        ],
        interpretacion=interpretacion,
        avisos=avisos,
    )
    return store.guardar(escaneo)


def recomendar_cosecha(pct_maduro: int, pct_sobre: int, total: int) -> dict:
    """Regla fija sobre el conteo: no depende de un modelo de lenguaje."""
    if total == 0:
        return {
            "titulo": "No se contaron cerezas",
            "texto": "Toma la foto más cerca del racimo, con buena luz y enfoque.",
        }
    if pct_sobre >= 20:
        return {
            "titulo": "Hay cerezas pasándose",
            "texto": "Conviene hacer un pase pronto para no perder calidad con las sobremaduras.",
        }
    if pct_maduro >= 50:
        return {
            "titulo": "Buen momento para recolectar",
            "texto": "Más de la mitad del racimo está en punto. Recoge solo las maduras y vuelve después por las pintonas.",
        }
    return {
        "titulo": "Todavía conviene esperar",
        "texto": "Menos de la mitad del racimo está en punto. Vuelve a revisarlo en unos días.",
    }


async def analizar_maduracion(image: Image.Image, lote: int) -> dict:
    img, _ = prepare_image(image)
    if modo() != "demo":
        raise MaduracionNoConectada(
            "La maduración todavía no está conectada a SAM 3.1. Usa el modo demo por ahora."
        )
    r = demo.analizar_maduracion(img)
    cerezas = r["cerezas"]
    total = len(cerezas)
    conteo = {e: sum(1 for c in cerezas if c["estado"] == e) for e in ESTADOS}
    pct = lambda n: round(100 * n / total) if total else 0

    escaneo = _base("maduracion", lote, img)
    escaneo.update(
        medicion={
            "total": total,
            "conteo": conteo,
            "porcentaje_maduro": pct(conteo["maduro"]),
        },
        detecciones=[
            {"id": c["id"], "estado": c["estado"], "caja": _caja(c["caja"], img.size), "confianza": None}
            for c in cerezas
        ],
        recomendacion=recomendar_cosecha(pct(conteo["maduro"]), pct(conteo["sobremaduro"]), total),
        avisos=r["avisos"],
    )
    return store.guardar(escaneo)
