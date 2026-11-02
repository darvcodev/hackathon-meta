"""Pruebas sin red: simulan la respuesta de SAM con el mismo formato que la API."""

import asyncio

import numpy as np
import pytest
from PIL import Image

from meta_sam_parser._mask_codec import _encode_raster  # codificador del propio parser

from royalens.analysis import (
    Instance,
    cherries_from,
    classify,
    dae_class,
    has_rust_color,
    main_leaf,
    measure,
    place_mask,
    render_overlay,
    ripeness,
    rust_lesions,
)
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


def _instancia(forma, y0, y1, x0, x1, nombre="a"):
    mascara = np.zeros(forma, dtype=bool)
    mascara[y0:y1, x0:x1] = True
    return Instance(nombre, mascara, (x0, y0, x1, y1), 0.9)


def test_hoja_principal_prefiere_la_central():
    forma = (100, 100)
    esquina = _instancia(forma, 0, 40, 0, 40, "esquina")
    centro = _instancia(forma, 35, 65, 35, 65, "centro")
    assert main_leaf([esquina, centro], forma).object_id == "centro"
    assert main_leaf([], forma) is None


def test_color_separa_roya_de_mancha_parda():
    rgb = np.zeros((10, 10, 3), dtype=np.uint8)
    rgb[:5] = (235, 130, 30)  # naranja saturado
    rgb[5:] = (120, 112, 108)  # gris pardo
    naranja, gris = np.zeros((10, 10), bool), np.zeros((10, 10), bool)
    naranja[:5] = True
    gris[5:] = True
    assert has_rust_color(rgb, naranja)
    assert not has_rust_color(rgb, gris)
    assert not has_rust_color(rgb, np.zeros((10, 10), bool))


def test_lesiones_sin_duplicados_ni_otras_manchas():
    forma = (50, 50)
    rgb = np.zeros((*forma, 3), dtype=np.uint8)
    rgb[...] = (60, 140, 60)
    rgb[5:15, 5:15] = (235, 130, 30)
    rgb[30:40, 30:40] = (120, 112, 108)
    hoja = np.ones(forma, dtype=bool)
    candidatas = [
        _instancia(forma, 5, 15, 5, 15, "roya"),
        _instancia(forma, 5, 15, 5, 15, "misma roya"),
        _instancia(forma, 30, 40, 30, 40, "parda"),
    ]
    validas, descartadas = rust_lesions(Image.fromarray(rgb), hoja, candidatas)
    assert len(validas) == 1
    assert descartadas == 1


@pytest.mark.parametrize(
    "porcentaje,clase,nivel",
    [
        (0.0, None, "Sin roya visible"),
        (1.4, 1, "Leve"),
        (2.9, 2, "Leve"),
        (5.9, 4, "Moderada"),
        (11.9, 8, "Moderada"),
        (23.9, 16, "Alta"),
        (47.9, 32, "Severa"),
        (79.0, 64, "Severa"),
    ],
)
def test_escala_sigue_el_diagrama_de_cenicafe(porcentaje, clase, nivel):
    assert dae_class(porcentaje) == clase
    assert classify(porcentaje)[0] == nivel


@pytest.mark.parametrize(
    "color,estado",
    [
        ((90, 170, 50), "verde"),
        ((235, 185, 40), "pinton"),
        ((215, 35, 40), "maduro"),
        ((80, 15, 30), "sobremaduro"),
    ],
)
def test_estado_de_la_cereza_segun_su_color(color, estado):
    rgb = np.full((20, 20, 3), color, dtype=np.uint8)
    assert ripeness(rgb, np.ones((20, 20), dtype=bool)) == estado


def test_cereza_mitad_roja_mitad_verde_es_pinton():
    rgb = np.zeros((20, 20, 3), dtype=np.uint8)
    rgb[:10] = (215, 35, 40)
    rgb[10:] = (90, 170, 50)
    assert ripeness(rgb, np.ones((20, 20), dtype=bool)) == "pinton"


def test_cerezas_sin_duplicados_ni_frutos_del_fondo():
    forma = (100, 100)
    grande = _instancia(forma, 10, 30, 10, 30, "grande")
    misma = _instancia(forma, 12, 30, 12, 30, "misma")
    otra = _instancia(forma, 50, 70, 50, 70, "otra")
    fondo = _instancia(forma, 90, 93, 90, 93, "fondo")
    nombres = {i.object_id for i in cherries_from([grande, misma, otra, fondo])}
    assert nombres == {"grande", "otra"}
    assert cherries_from([]) == []


def test_cuadrantes_ubican_cerezas_y_descartan_las_cortadas(monkeypatch):
    from royalens import meta_api

    async def falso(client, url, prompt, size, min_conf=0.35):
        w, h = size
        if size == (W, H):
            return []
        entera = _instancia((h, w), 10, 30, 10, 30, "entera")
        cortada = _instancia((h, w), 40, h, 50, 70, "cortada")  # toca el borde inferior
        return [entera, cortada]

    monkeypatch.setattr(meta_api, "segment", falso)
    encontradas = asyncio.run(meta_api.segment_tiled(None, Image.new("RGB", (W, H)), "fruta"))
    # Los cuadrantes de arriba cortan esa cereza; en los de abajo toca el borde real de la foto.
    cortadas = [i for i in encontradas if i.object_id == "cortada"]
    assert len(cortadas) == 2 and all(i.box[3] == H for i in cortadas)
    # Los cuadrantes de abajo y derecha quedan desplazados: las cajas son de la foto completa.
    assert max(i.box[2] for i in encontradas) > 100
    assert all(i.mask.shape == (H, W) for i in encontradas)
    assert any(i.mask[i.box[1] + 1, i.box[0] + 1] for i in encontradas)


@pytest.mark.parametrize(
    "muse,medible",
    [
        ({"cara_visible": "enves", "calidad_foto": "buena"}, True),
        ({"cara_visible": "haz", "calidad_foto": "buena"}, False),
        ({"cara_visible": "enves", "calidad_foto": "mala"}, False),
        ({"es_hoja_de_cafe": False}, False),
    ],
)
def test_una_hoja_sin_lesiones_solo_cuenta_si_la_foto_lo_permite(monkeypatch, muse, medible):
    from royalens import pipeline

    forma = (H, W)
    hoja = _instancia(forma, 0, H, 0, W, "hoja")

    async def segmentar(client, url, prompt, size, min_conf):
        return [hoja] if "leaf" in prompt else []

    async def diagnosticar(*args, **kwargs):
        return muse

    monkeypatch.setattr(pipeline, "make_client", lambda: None)
    monkeypatch.setattr(pipeline, "segment", segmentar)
    monkeypatch.setattr(pipeline, "diagnose", diagnosticar)
    d = asyncio.run(pipeline.analyze(Image.new("RGB", (W, H), (60, 140, 60))))
    assert d.measurable is medible
    assert bool(d.warnings) is not medible
