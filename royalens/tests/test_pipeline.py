"""Pruebas sin red: simulan la respuesta de SAM con el mismo formato que la API."""

import asyncio

import numpy as np
import pytest
from PIL import Image

from meta_sam_parser._mask_codec import _encode_raster  # codificador del propio parser

from royalens.analysis import Instance, measure, place_mask, render_overlay
from royalens.meta_api import _extract_json, instances_from_events

W, H = 200, 100


def _record(obj_id, left, top, local, conf=0.9):
    """Un registro SAM: caja + máscara one_bit local a la caja."""
    h, w = local.shape
    payload = _encode_raster(local.astype(np.uint8).ravel().tolist(), w, h)
    box = f"<|box;x1={left};y1={top};x2={left + w - 1};y2={top + h - 1};w={W};h={H};c={conf}|>"
    mask = f"<|mask;x=0;y=0;c={conf};data={h},{w},{payload}|>"
    return f"{obj_id}{box}{mask}"


async def _events(line):
    lane = {"item_id": "msg_1", "output_index": 0, "content_index": 0}
    if line:
        yield {"type": "response.output_text.delta", "delta": line, **lane}
    # Sin coincidencias, la API cierra el carril de texto vacío y sin deltas.
    yield {"type": "response.output_text.done", "text": line, **lane}
    yield {"type": "response.completed", "response": {"status": "completed"}}


def _parse(line, min_conf=0.35):
    return asyncio.run(instances_from_events(_events(line), (W, H), min_conf))


def test_mask_is_placed_at_its_box():
    local = np.ones((10, 20), dtype=bool)
    insts = _parse("<0f>" + _record(0, 30, 40, local))
    assert len(insts) == 1
    m = insts[0].mask
    assert m.shape == (H, W) and m.sum() == 200
    assert m[40:50, 30:50].all() and not m[:40].any()


def test_zero_matches_is_valid():
    assert _parse("") == []


def test_low_confidence_is_filtered():
    local = np.ones((5, 5), dtype=bool)
    line = "<0f>" + _record(0, 0, 0, local, conf=0.2) + "," + _record(1, 50, 50, local, conf=0.8)
    insts = _parse(line)
    assert [i.object_id for i in insts] == ["1"]


def test_severity_percent_and_count():
    leaf = np.zeros((H, W), dtype=bool)
    leaf[0:100, 0:100] = True  # 10.000 px de hoja
    spot = np.zeros((H, W), dtype=bool)
    spot[10:20, 10:60] = True  # 500 px dentro de la hoja -> 5 %
    outside = np.zeros((H, W), dtype=bool)
    outside[10:20, 150:190] = True  # fuera de la hoja: no cuenta
    lesions = [Instance("0", spot, (10, 10, 60, 20), 0.9), Instance("1", outside, (150, 10, 190, 20), 0.9)]
    s = measure(leaf, lesions)
    assert s.lesion_count == 1
    assert s.percent == pytest.approx(5.0)
    assert s.level == "Moderada"


def test_no_leaf_gives_zero_not_crash():
    s = measure(np.zeros((H, W), dtype=bool), [])
    assert s.percent == 0 and s.lesion_count == 0


def test_place_mask_clips_at_border():
    local = np.ones((10, 10), dtype=np.uint8).tobytes()
    m = place_mask(local, 10, 10, (195, 95, 205, 105), W, H)
    assert m.sum() == 25


def test_overlay_renders():
    leaf = np.zeros((H, W), dtype=bool)
    leaf[10:90, 10:190] = True
    spot = np.zeros((H, W), dtype=bool)
    spot[40:50, 40:50] = True
    img = render_overlay(Image.new("RGB", (W, H), (60, 120, 60)), leaf, [Instance("0", spot, (40, 40, 50, 50), 0.9)])
    assert img.size == (W, H)


def test_extract_json_tolerates_extra_text():
    assert _extract_json('Claro:\n```json\n{"signos_de_roya": true}\n```') == {"signos_de_roya": True}
    assert _extract_json("sin json") is None
