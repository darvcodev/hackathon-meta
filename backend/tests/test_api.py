"""Pruebas de la API sin red, con datos en una carpeta temporal."""

import io
import os
import tempfile

os.environ["ROYALENS_DATA"] = tempfile.mkdtemp()
os.environ["ROYALENS_MODE"] = "demo"

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from backend.main import app


def _foto(dibujar) -> tuple:
    img = Image.new("RGB", (800, 600), (12, 30, 18))
    dibujar(ImageDraw.Draw(img))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    return ("foto.jpg", buf.getvalue(), "image/jpeg")


def _hoja(d):
    d.ellipse((100, 50, 700, 550), fill=(110, 160, 70))
    d.ellipse((250, 200, 330, 280), fill=(230, 150, 30))
    d.ellipse((450, 300, 530, 380), fill=(230, 150, 30))


def _racimo(d):
    d.ellipse((100, 100, 170, 170), fill=(205, 30, 35))
    d.ellipse((300, 100, 370, 170), fill=(205, 30, 35))
    d.ellipse((500, 100, 570, 170), fill=(120, 170, 30))


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_roya_mide_desde_mascaras(client):
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 3})
    assert r.status_code == 200
    e = r.json()
    assert e["modo"] == "demo" and e["lote"] == 3
    assert e["medicion"]["lesiones"] == 2
    assert 0 < e["medicion"]["porcentaje"] < 10
    assert client.get(e["imagen_url"]).status_code == 200
    assert client.get(e["overlay_url"]).status_code == 200
    assert client.get(f"/api/escaneos/{e['id']}").json()["id"] == e["id"]


def test_maduracion_cuenta_por_estado(client):
    r = client.post("/api/maduracion", files={"foto": _foto(_racimo)}, data={"lote": 2})
    assert r.status_code == 200
    m = r.json()["medicion"]
    assert m["total"] == 3
    assert m["conteo"]["maduro"] == 2 and m["conteo"]["verde"] == 1
    assert m["porcentaje_maduro"] == 67


def test_archivo_invalido_es_error(client):
    r = client.post("/api/roya", files={"foto": ("x.jpg", b"no es imagen", "image/jpeg")})
    assert r.status_code == 400


def test_lote_inexistente_es_error(client):
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 9})
    assert r.status_code == 400


def test_modo_real_sin_clave_da_error_y_no_resultado(client, monkeypatch):
    monkeypatch.setenv("ROYALENS_MODE", "real")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    r = client.post("/api/roya", files={"foto": _foto(_hoja)})
    assert r.status_code == 503
    assert "medicion" not in r.json()


def test_panel_no_mezcla_demo_con_real(client, monkeypatch):
    assert client.get("/api/resumen").json()["indicadores"]["escaneos_mes"] > 0
    monkeypatch.setenv("ROYALENS_MODE", "real")
    real = client.get("/api/resumen").json()
    assert real["indicadores"]["roya_promedio"] is None
    assert real["indicadores"]["escaneos_mes"] == 0
