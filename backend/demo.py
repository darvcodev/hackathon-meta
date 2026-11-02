"""Modo demo: segmentación local por color, sin SAM ni Muse.

Sirve para construir la interfaz sobre fotos reales sin gastar la API. Las máscaras
salen de la foto subida, pero NO son un diagnóstico: la interfaz lo marca como demo.
"""

from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

from royalens.analysis import Instance, measure, render_overlay

TEXTO_LESION = (
    "Texto de ejemplo del modo demo. Con la API real, aquí Muse Spark describe "
    "las manchas que ve en esta foto."
)
TEXTO_RECOMENDACION = (
    "Texto de ejemplo del modo demo. Con la API real, aquí aparece qué hacer en "
    "lenguaje de finca. Ante cualquier duda, consulte a su extensionista del "
    "Comité de Cafeteros o a Cenicafé."
)


def _hsv(image: Image.Image) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    arr = np.asarray(image.convert("HSV")).astype(np.int16)
    return arr[..., 0], arr[..., 1], arr[..., 2]


def _instances(mask: np.ndarray, min_area: int, prefix: str = "") -> list[Instance]:
    labels, _ = ndimage.label(mask)
    found: list[Instance] = []
    for index, slices in enumerate(ndimage.find_objects(labels), start=1):
        if slices is None:
            continue
        region = labels == index
        if region.sum() < min_area:
            continue
        ys, xs = slices
        found.append(
            Instance(f"{prefix}{index}", region, (xs.start, ys.start, xs.stop, ys.stop), None)
        )
    return found


def segmentar_hoja(image: Image.Image) -> tuple[np.ndarray, list[Instance]]:
    h, s, v = _hsv(image)
    area = h.size
    lesion = (h >= 10) & (h <= 38) & (s >= 110) & (v >= 90)
    verde = (h >= 30) & (h <= 110) & (s >= 35) & (v >= 80)

    candidata = ndimage.binary_opening(verde | lesion, iterations=3)
    candidata = ndimage.binary_closing(candidata, iterations=3)
    labels, total = ndimage.label(candidata)
    if total == 0:
        return np.zeros(h.shape, dtype=bool), []
    sizes = ndimage.sum(candidata, labels, range(1, total + 1))
    hoja = ndimage.binary_fill_holes(labels == int(np.argmax(sizes)) + 1)

    # El cierre une el polvillo de cada pústula en una sola lesión.
    lesion = ndimage.binary_closing(lesion & hoja, iterations=4) & hoja
    lesion = ndimage.binary_opening(lesion, iterations=2)
    return hoja, _instances(lesion, max(12, int(area * 0.0001)))


def analizar_roya(image: Image.Image) -> dict:
    hoja, lesiones = segmentar_hoja(image)
    severidad = measure(hoja, lesiones)
    avisos = []
    if not hoja.any():
        avisos.append("No se detectó ninguna hoja: el porcentaje no es confiable.")
    return {
        "overlay": render_overlay(image, hoja, lesiones),
        "severidad": severidad,
        "lesiones": lesiones,
        "interpretacion": {
            "lo_que_se_ve": TEXTO_LESION,
            "recomendacion": TEXTO_RECOMENDACION,
            "otras_causas": [],
        },
        "avisos": avisos,
    }


def _circulos(mascara: np.ndarray, r_min: float, r_max: float) -> list[tuple[int, int, float]]:
    """Separa cerezas que se tocan: toma el círculo más grande que cabe, una y otra vez."""
    # El cierre tapa los brillos de la piel, que rompen la silueta de la cereza.
    cerrada = ndimage.binary_closing(mascara, iterations=8)
    limpia = ndimage.binary_fill_holes(ndimage.binary_opening(cerrada, iterations=4))
    dist = ndimage.distance_transform_edt(limpia)
    alto, ancho = dist.shape
    yy, xx = np.ogrid[:alto, :ancho]
    circulos = []
    for _ in range(80):
        y, x = np.unravel_index(np.argmax(dist), dist.shape)
        r = float(dist[y, x])
        if r < r_min:
            break
        # Lo que excede r_max es una hoja o una mancha grande, no una cereza.
        if r <= r_max:
            circulos.append((int(x), int(y), r))
        dist[(xx - x) ** 2 + (yy - y) ** 2 <= (1.25 * r) ** 2] = 0
    return circulos


def analizar_maduracion(image: Image.Image) -> dict:
    h, s, v = _hsv(image)
    lado = min(h.shape)
    rojo = ((h <= 12) | (h >= 225)) & (s >= 70)
    mascaras = {
        "maduro": rojo & (v >= 120),
        "sobremaduro": rojo & (v >= 25) & (v < 120),
        "pinton": (h > 12) & (h <= 36) & (s >= 105) & (v >= 120),
        "verde": (h > 36) & (h <= 68) & (s >= 110) & (v >= 95),
    }
    candidatos = sorted(
        (
            (r, x, y, estado)
            for estado, m in mascaras.items()
            for x, y, r in _circulos(m, lado * 0.032, lado * 0.075)
        ),
        reverse=True,
    )
    cerezas: list[dict] = []
    aceptados: list[tuple[int, int, float]] = []
    for r, x, y, estado in candidatos:
        # Una cereza con dos colores no cuenta dos veces.
        if any((x - ax) ** 2 + (y - ay) ** 2 < ar**2 for ax, ay, ar in aceptados):
            continue
        aceptados.append((x, y, r))
        cerezas.append(
            {
                "id": f"{estado}-{len(cerezas) + 1}",
                "estado": estado,
                "caja": (int(x - r), int(y - r), int(x + r), int(y + r)),
            }
        )
    return {"cerezas": cerezas, "avisos": []}
