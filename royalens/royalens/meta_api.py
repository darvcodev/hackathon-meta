"""Llamadas a Meta Model API: SAM 3.1 (segmentación) y Muse Spark (diagnóstico).

Formatos tomados de la documentación oficial:
- https://dev.meta.ai/docs/media-segmentation
- https://dev.meta.ai/docs/sam/reading-segmentation
- https://dev.meta.ai/docs/image-understanding
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import re

import numpy as np
from openai import AsyncOpenAI
from PIL import Image, ImageOps

from meta_sam_parser import (
    decode_mask_to_raster,
    image_segmentation_format,
    parse_responses_stream,
)

from . import config
from .analysis import Instance, place_mask


class MissingApiKey(RuntimeError):
    pass


def make_client() -> AsyncOpenAI:
    key = os.getenv(config.API_KEY_ENV)
    if not key:
        raise MissingApiKey(
            f"Falta la variable {config.API_KEY_ENV}. Crea tu API key en "
            "https://dev.meta.ai/ y ponla en el archivo .env"
        )
    # Sin tiempo límite, una respuesta trabada dejaría al caficultor esperando indefinidamente.
    return AsyncOpenAI(base_url=config.BASE_URL, api_key=key, timeout=config.API_TIMEOUT_SECONDS, max_retries=1)


def prepare_image(image: Image.Image) -> tuple[Image.Image, str]:
    """Corrige la rotación del celular, reduce tamaño y devuelve un data URL JPEG."""
    img = ImageOps.exif_transpose(image).convert("RGB")
    img.thumbnail((config.MAX_IMAGE_SIDE, config.MAX_IMAGE_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    data_url = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return img, data_url


def _user_message(text: str, data_url: str) -> list[dict]:
    return [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": text},
                {"type": "input_image", "image_url": data_url},
            ],
        }
    ]


async def segment(
    client: AsyncOpenAI,
    data_url: str,
    prompt: str,
    size: tuple[int, int],
    min_confidence: float = config.MIN_CONFIDENCE,
) -> list[Instance]:
    """Pide a SAM 3.1 todas las instancias de `prompt`. Cero resultados es válido."""
    width, height = size
    events = await client.responses.create(
        model=config.SAM_MODEL,
        input=_user_message(prompt, data_url),
        stream=True,
        metadata={"mask_encoding": "one_bit", "include_confidence": "true"},
    )
    return await instances_from_events(events, size, min_confidence)


async def segment_tiled(
    client: AsyncOpenAI,
    image: Image.Image,
    prompt: str,
    min_confidence: float = config.MIN_CONFIDENCE,
) -> list[Instance]:
    """SAM sobre la foto completa y sus cuatro cuadrantes, ya en coordenadas de la foto."""
    width, height = image.size
    tile_w = int(width * (0.5 + config.TILE_OVERLAP / 2))
    tile_h = int(height * (0.5 + config.TILE_OVERLAP / 2))
    origins = [(0, 0), (width - tile_w, 0), (0, height - tile_h), (width - tile_w, height - tile_h)]

    def data_url_of(img: Image.Image) -> str:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=90)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()

    whole, *tiles = await asyncio.gather(
        segment(client, data_url_of(image), prompt, image.size, min_confidence),
        *(
            segment(client, data_url_of(image.crop((x, y, x + tile_w, y + tile_h))), prompt, (tile_w, tile_h), min_confidence)
            for x, y in origins
        ),
    )

    found = list(whole)
    for (x, y), group in zip(origins, tiles):
        for inst in group:
            left, top, right, bottom = inst.box
            # Una cereza cortada por el borde interior aparece entera en el cuadrante vecino.
            cut = (x > 0 and left <= 1) or (y > 0 and top <= 1) or (
                x == 0 and right >= tile_w - 1
            ) or (y == 0 and bottom >= tile_h - 1)
            if cut:
                continue
            mask = np.zeros((height, width), dtype=bool)
            mask[y : y + tile_h, x : x + tile_w] = inst.mask
            found.append(Instance(inst.object_id, mask, (left + x, top + y, right + x, bottom + y), inst.confidence))
    return found


async def instances_from_events(events, size, min_confidence) -> list[Instance]:
    """Convierte el stream de SAM en máscaras de imagen completa (separado para tests)."""
    width, height = size
    parsed = parse_responses_stream(events, image_segmentation_format())
    result = await parsed.final_result()

    boxes = {}
    instances: list[Instance] = []
    for record in result.records:
        if record.kind == "box":
            boxes[record.object_id] = record
    for record in result.records:
        if record.kind != "mask":
            continue
        conf = record.confidence
        if conf is not None and conf < min_confidence:
            continue
        b = record.bounds
        mask = place_mask(
            decode_mask_to_raster(record.mask),
            record.mask.width,
            record.mask.height,
            (b.left, b.top, b.right, b.bottom),
            width,
            height,
        )
        box = boxes.get(record.object_id)
        box_t = (
            (int(box.left), int(box.top), int(box.right), int(box.bottom))
            if box
            else (int(b.left), int(b.top), int(b.right), int(b.bottom))
        )
        instances.append(Instance(record.object_id, mask, box_t, conf))
    return instances


DIAGNOSIS_PROMPT = """Eres un asistente agronómico para caficultores colombianos.
Analiza la foto. Una herramienta de segmentación ya MIDIÓ lo siguiente:
- Se pudo medir una hoja: {leaf_found}
- Lesiones con color de roya sobre la hoja: {lesion_count}
- Porcentaje del área de la hoja con esas lesiones: {percent:.1f}%
- Nivel según la escala de la app: {level}

Si no se pudo medir una hoja, ignora las cifras y no menciones porcentajes.
No cambies ni inventes estas cifras. Tu trabajo es interpretar lo que se VE.
La roya forma pústulas de polvillo naranja, sobre todo en el envés. Marca
"signos_de_roya" como true solo si ves ese polvillo o manchas amarillas compatibles;
una mancha parda o gris con centro claro no es roya.
Responde SOLO con un objeto JSON válido, sin texto adicional, con estas claves:
{{
  "es_hoja_de_cafe": true o false,
  "calidad_foto": "buena" | "regular" | "mala",
  "cara_visible": "haz" | "enves" | "no se distingue",
  "signos_de_roya": true o false,
  "lo_que_se_ve": "1-2 frases describiendo manchas, color y ubicación (haz o envés)",
  "otras_causas_posibles": ["otras enfermedades o daños que podrían confundirse"],
  "recomendacion": "2-3 frases en lenguaje sencillo para el caficultor",
  "consejo_foto": "cómo tomar una mejor foto si hace falta, o cadena vacía"
}}
Reglas: trata al caficultor de usted, con respeto y sin apodos, y escribe con naturalidad: la hoja es la que
tiene las manchas, no "usted". No inventes plazos en días
ni otras cifras. No des dosis ni marcas de productos químicos; si recomiendas manejo,
sugiere consultar al extensionista del Comité de Cafeteros o a Cenicafé.
Si la foto no es una hoja de café, dilo y no des diagnóstico."""


RIPENESS_PROMPT = """Eres un asistente agronómico para caficultores colombianos.
Analiza la foto. Una herramienta de segmentación ya CONTÓ estas cerezas:
- Total: {total}
- Verdes: {verde}. Pintonas: {pinton}. Maduras: {maduro}. Sobremaduras: {sobremaduro}

No cambies ni inventes estas cifras. Tu trabajo es interpretar lo que se VE.
Responde SOLO con un objeto JSON válido, sin texto adicional, con estas claves:
{{
  "es_racimo_de_cafe": true o false,
  "calidad_foto": "buena" | "regular" | "mala",
  "lo_que_se_ve": "1-2 frases sobre el estado de las cerezas, en lenguaje sencillo",
  "recomendacion": "2-3 frases prácticas sobre la recolección selectiva, en lenguaje de finca",
  "consejo_foto": "cómo tomar una mejor foto si hace falta, o cadena vacía"
}}
"es_racimo_de_cafe" es true solo si se ven cerezas de café en la rama.
Trata al caficultor de usted, con respeto y sin apodos, y escribe con naturalidad. No inventes plazos en días ni otras cifras.
Algunas variedades maduran amarillas: si lo parece, adviértelo en "lo_que_se_ve".
Si la foto no es un racimo de café, dilo y no des recomendación de cosecha."""


def _extract_json(text: str) -> dict | None:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


async def diagnose(
    client: AsyncOpenAI,
    data_url: str,
    *,
    leaf_found: bool,
    lesion_count: int,
    percent: float,
    level: str,
) -> dict:
    """Muse Spark interpreta la foto usando la medición de SAM como contexto."""
    prompt = DIAGNOSIS_PROMPT.format(
        leaf_found="sí" if leaf_found else "no",
        lesion_count=lesion_count,
        percent=percent,
        level=level,
    )
    response = await client.responses.create(
        model=config.MUSE_MODEL,
        input=_user_message(prompt, data_url),
    )
    return _muse_json(response)


async def interpret_ripeness(client: AsyncOpenAI, data_url: str, counts: dict, total: int) -> dict:
    """Muse Spark confirma que es un racimo y explica el conteo sin cambiarlo."""
    response = await client.responses.create(
        model=config.MUSE_MODEL,
        input=_user_message(RIPENESS_PROMPT.format(total=total, **counts), data_url),
    )
    return _muse_json(response)


def _muse_json(response) -> dict:
    text = response.output_text or ""
    parsed = _extract_json(text)
    if parsed is None:
        return {"_sin_formato": text.strip()}
    return parsed
