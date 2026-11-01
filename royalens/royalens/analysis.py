"""Cálculos puros sobre máscaras: no llaman a ninguna API.

Aquí está la parte que convierte la segmentación en una MEDIDA:
porcentaje de la hoja afectado por roya y número de lesiones.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from . import config


@dataclass
class Instance:
    """Un objeto encontrado por SAM, ya colocado sobre la imagen completa."""

    object_id: str
    mask: np.ndarray  # bool, forma (alto, ancho) de la imagen
    box: tuple[int, int, int, int]  # left, top, right, bottom (semiabierta)
    confidence: float | None


def place_mask(
    raster: bytes,
    mask_w: int,
    mask_h: int,
    bounds: tuple[float, float, float, float],
    image_w: int,
    image_h: int,
) -> np.ndarray:
    """Coloca una máscara local de SAM (del tamaño de su caja) en la imagen completa."""
    local = np.frombuffer(raster, dtype=np.uint8).reshape(mask_h, mask_w).astype(bool)
    left, top, right, bottom = (int(round(v)) for v in bounds)
    box_w, box_h = max(right - left, 1), max(bottom - top, 1)
    if (box_w, box_h) != (mask_w, mask_h):
        resized = Image.fromarray(local.astype(np.uint8) * 255).resize(
            (box_w, box_h), Image.NEAREST
        )
        local = np.asarray(resized) > 127

    full = np.zeros((image_h, image_w), dtype=bool)
    # Recorta por si la caja toca o se sale del borde.
    x0, y0 = max(left, 0), max(top, 0)
    x1, y1 = min(left + box_w, image_w), min(top + box_h, image_h)
    if x1 <= x0 or y1 <= y0:
        return full
    full[y0:y1, x0:x1] = local[y0 - top : y1 - top, x0 - left : x1 - left]
    return full


def union(instances: list[Instance], shape: tuple[int, int]) -> np.ndarray:
    out = np.zeros(shape, dtype=bool)
    for inst in instances:
        out |= inst.mask
    return out


def classify(percent: float) -> tuple[str, str]:
    for upper, label, color in config.SEVERITY_LEVELS:
        if percent < upper:
            return label, color
    _, label, color = config.SEVERITY_LEVELS[-1]
    return label, color


@dataclass
class Severity:
    leaf_pixels: int
    lesion_pixels: int
    percent: float
    lesion_count: int
    level: str
    color: str

    def as_dict(self) -> dict:
        return {
            "pixeles_hoja": self.leaf_pixels,
            "pixeles_lesion": self.lesion_pixels,
            "porcentaje_afectado": round(self.percent, 2),
            "numero_lesiones": self.lesion_count,
            "nivel": self.level,
        }


def measure(leaf_mask: np.ndarray, lesions: list[Instance]) -> Severity:
    """% de la hoja cubierto por lesiones. Solo cuentan lesiones dentro de la hoja."""
    leaf_px = int(leaf_mask.sum())
    lesion_mask = np.zeros_like(leaf_mask)
    count = 0
    for inst in lesions:
        area = int(inst.mask.sum())
        if area == 0:
            continue
        inside = inst.mask & leaf_mask
        # Una lesión cuenta si al menos la mitad está sobre la hoja.
        if inside.sum() >= 0.5 * area:
            count += 1
            lesion_mask |= inside
    lesion_px = int(lesion_mask.sum())
    percent = 100.0 * lesion_px / leaf_px if leaf_px else 0.0
    level, color = classify(percent)
    return Severity(leaf_px, lesion_px, percent, count, level, color)


def _outline(mask: np.ndarray, thickness: int = 3) -> np.ndarray:
    """Borde de una máscara: la máscara menos su versión erosionada."""
    eroded = mask.copy()
    for _ in range(thickness):
        shrunk = eroded.copy()
        shrunk[1:, :] &= eroded[:-1, :]
        shrunk[:-1, :] &= eroded[1:, :]
        shrunk[:, 1:] &= eroded[:, :-1]
        shrunk[:, :-1] &= eroded[:, 1:]
        eroded = shrunk
    return mask & ~eroded


def render_overlay(
    image: Image.Image, leaf_mask: np.ndarray, lesions: list[Instance]
) -> Image.Image:
    """Hoja con contorno verde, fondo atenuado y lesiones pintadas en naranja-rojo."""
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    out = rgb.copy()

    if leaf_mask.any():
        out[~leaf_mask] *= 0.45  # atenúa lo que no es hoja

    lesion_mask = union(lesions, leaf_mask.shape) & (leaf_mask if leaf_mask.any() else True)
    paint = np.array([255, 69, 0], dtype=np.float32)
    out[lesion_mask] = 0.4 * out[lesion_mask] + 0.6 * paint

    out[_outline(leaf_mask)] = np.array([0, 230, 118], dtype=np.float32)
    out[_outline(lesion_mask, thickness=1)] = np.array([255, 235, 59], dtype=np.float32)
    return Image.fromarray(out.clip(0, 255).astype(np.uint8))
