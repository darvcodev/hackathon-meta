"""Une los modos demo y real bajo una misma respuesta para la interfaz."""

from __future__ import annotations

import os
from datetime import datetime, timezone

from PIL import Image

from royalens import config  # carga royalens/.env
from royalens.analysis import Instance, dae_class, lesion_details
from royalens.meta_api import prepare_image
from royalens.pipeline import analyze, analyze_ripeness

from . import demo, ejemplos, store

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


class EjemploNoExiste(LookupError):
    pass


def _base(tipo: str, lote: int, img: Image.Image, idioma: str) -> dict:
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
        "idioma": idioma,
        "ancho": img.width,
        "alto": img.height,
        "imagen_url": f"/media/{nombre}",
    }


def _confianza(instancias: list[Instance]) -> float | None:
    valores = [i.confidence for i in instancias if i.confidence is not None]
    return round(sum(valores) / len(valores), 2) if valores else None


def _lista(valor) -> list[str]:
    return [str(v) for v in valor if str(v).strip()] if isinstance(valor, list) else []


def _comparacion(tipo: str, lote: int, visitante: str, actual: float | None) -> dict | None:
    """Compara con el escaneo válido anterior del mismo lote. La cifra sale del historial."""
    previo = store.ultimo_valido(modo(), visitante, lote, tipo)
    if previo is None or actual is None:
        return None
    campo = "porcentaje" if tipo == "roya" else "porcentaje_maduro"
    return {"fecha": previo["creado"], "valor": previo["medicion"][campo], "cambio": round(actual - previo["medicion"][campo], 1)}


def _interpretacion_muse(muse: dict) -> dict:
    # Si Muse no devolvió JSON, se muestra su texto tal cual, sin rellenar nada.
    return {
        "lo_que_se_ve": muse.get("lo_que_se_ve") or muse.get("_sin_formato") or "",
        "recomendacion": muse.get("recomendacion") or "",
        "otras_causas": muse.get("otras_causas_posibles") or [],
        "consejo_foto": muse.get("consejo_foto") or "",
        "resumen": muse.get("resumen") or "",
        "hallazgos": _lista(muse.get("hallazgos")),
        "pasos": _lista(muse.get("pasos")),
        "cuando_consultar": muse.get("cuando_consultar") or "",
        "signos_de_roya": muse.get("signos_de_roya"),
        "calidad_foto": muse.get("calidad_foto"),
        "cara_visible": muse.get("cara_visible"),
    }


async def analizar_roya(image: Image.Image, lote: int, visitante: str, idioma: str = "es") -> dict:
    img, _ = prepare_image(image)
    if modo() == "demo":
        r = demo.analizar_roya(img)
        overlay, severidad, lesiones = r["overlay"], r["severidad"], r["lesiones"]
        interpretacion, avisos = r["interpretacion"], r["avisos"]
        valida, hojas_en_foto = severidad.leaf_pixels > 0, 1
        clase = dae_class(severidad.percent) if valida else None
        detalle, general = (lesion_details(r["hoja"], lesiones) if valida else {}), None
    else:
        d = await analyze(img, language=idioma)
        overlay, severidad, lesiones = d.overlay, d.severity, d.lesions
        interpretacion, avisos = _interpretacion_muse(d.muse), d.warnings
        valida, hojas_en_foto, clase = d.measurable, d.leaves_in_photo, d.dae
        detalle, general = d.details, d.general

    escaneo = _base("roya", lote, img, idioma)
    nombre_overlay = f"{escaneo['id']}_overlay.jpg"
    overlay.save(store.MEDIA_DIR / nombre_overlay, quality=88)
    escaneo.update(
        overlay_url=f"/media/{nombre_overlay}",
        medicion={
            # Sin medición válida no hay cifra: un 0 se leería como una hoja sana.
            "valida": valida,
            "porcentaje": round(severidad.percent, 1) if valida else None,
            "nivel": severidad.level if valida else None,
            "lesiones": severidad.lesion_count if valida else None,
            "clase_dae": clase,
            "hojas_en_foto": hojas_en_foto,
            "confianza": _confianza(lesiones),
            "area_sana": round(100 - severidad.percent, 1) if valida else None,
            **detalle,
        },
        vista_general=general,
        comparacion=_comparacion("roya", lote, visitante, round(severidad.percent, 1) if valida else None),
        detecciones=[
            # Cada prompt de SAM numera desde cero: el id se asigna aquí para que sea único.
            {"id": str(n), "caja": _caja(i.box, img.size), "confianza": i.confidence}
            for n, i in enumerate(lesiones)
        ],
        interpretacion=interpretacion,
        avisos=avisos,
    )
    return store.guardar(escaneo, visitante)


def recomendar_cosecha(pct_maduro: int, pct_sobre: int, total: int) -> dict:
    """Regla fija sobre el conteo: no depende de un modelo de lenguaje."""
    if total == 0:
        return {
            "titulo": "Sin conteo",
            "texto": "Tome la foto más cerca del racimo, con buena luz y enfoque.",
        }
    if pct_sobre >= 20:
        return {
            "titulo": "Hay cerezas pasándose",
            "texto": "Conviene hacer un pase pronto para no perder calidad con las sobremaduras.",
        }
    if pct_maduro >= 50:
        return {
            "titulo": "Buen momento para recolectar",
            "texto": "Más de la mitad del racimo está en punto. Recoja solo las maduras y vuelva después por las pintonas.",
        }
    return {
        "titulo": "Todavía conviene esperar",
        "texto": "Menos de la mitad del racimo está en punto. Vuelva a revisarlo más adelante.",
    }


async def analizar_maduracion(image: Image.Image, lote: int, visitante: str, idioma: str = "es") -> dict:
    img, _ = prepare_image(image)
    if modo() == "demo":
        r = demo.analizar_maduracion(img)
        cerezas, avisos, interpretacion = r["cerezas"], r["avisos"], None
        valida = bool(cerezas)
    else:
        d = await analyze_ripeness(img, language=idioma)
        cerezas = [
            {"estado": c.state, "caja": c.instance.box, "confianza": c.instance.confidence} for c in d.cherries
        ]
        avisos, interpretacion, valida = d.warnings, _interpretacion_muse(d.muse), d.measurable
    total = len(cerezas)
    conteo = {e: sum(1 for c in cerezas if c["estado"] == e) for e in config.RIPENESS_STATES}
    pct = lambda n: round(100 * n / total) if total else 0

    escaneo = _base("maduracion", lote, img, idioma)
    escaneo.update(
        medicion={
            "valida": valida,
            "total": total,
            "conteo": conteo,
            # Sin conteo válido no hay cifra: un 0 se leería como un racimo verde.
            "porcentaje_maduro": pct(conteo["maduro"]) if valida else None,
        },
        detecciones=[
            {"id": str(n), "estado": c["estado"], "caja": _caja(c["caja"], img.size), "confianza": c.get("confianza")}
            for n, c in enumerate(cerezas)
        ],
        comparacion=_comparacion("maduracion", lote, visitante, pct(conteo["maduro"]) if valida else None),
        recomendacion=recomendar_cosecha(pct(conteo["maduro"]), pct(conteo["sobremaduro"]), total),
        interpretacion=interpretacion,
        avisos=avisos,
    )
    return store.guardar(escaneo, visitante)


async def analizar_ejemplo(slug: str, lote: int, visitante: str, al_analizar, idioma: str = "es") -> dict:
    """Las fotos de ejemplo se analizan una vez por idioma: las demás veces no gastan créditos ni tiempo."""
    ejemplo = ejemplos.buscar(slug)
    if not ejemplo:
        raise EjemploNoExiste(slug)
    version = f"{ejemplos.VERSION_ANALISIS}-{idioma}"
    guardado = store.ejemplo_guardado(slug, modo(), version)
    if not guardado:
        al_analizar()
        analizar = analizar_roya if ejemplo["tipo"] == "roya" else analizar_maduracion
        with Image.open(ejemplos.ruta(slug)) as foto:
            guardado = await analizar(foto, lote, store.CACHE_EJEMPLOS, idioma)
        guardado = {
            **guardado,
            "foto_ejemplo": {"titulo": ejemplo["titulo"], "credito": ejemplo["credito"], "url": ejemplo["url"]},
        }
        store.guardar_ejemplo(slug, version, guardado)
    campo = "porcentaje" if guardado["tipo"] == "roya" else "porcentaje_maduro"
    comparacion = _comparacion(guardado["tipo"], lote, visitante, guardado["medicion"].get(campo))
    return store.copiar_escaneo({**guardado, "comparacion": comparacion}, lote, visitante)
