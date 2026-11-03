"""Pruebas de la API sin red, con datos en una carpeta temporal."""

import io
import json
import os
import tempfile
from datetime import datetime, timezone
from types import SimpleNamespace

os.environ["ROYALENS_DATA"] = tempfile.mkdtemp()
os.environ["ROYALENS_MODE"] = "demo"

import httpx
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
    from backend import store

    with TestClient(app) as c:
        # Los cupos y los resultados de ejemplo se comparten entre navegadores, no entre pruebas.
        with store._db() as con:
            con.execute("DELETE FROM uso")
            con.execute("DELETE FROM ejemplos_cache")
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


def _diagnostico(medible, porcentaje=0.0, lesiones=0, avisos=()):
    from royalens.analysis import Severity
    from royalens.pipeline import Diagnosis

    severidad = Severity(1000, int(porcentaje * 10), porcentaje, lesiones, "Moderada", "#000")
    muse = {"lo_que_se_ve": "texto de prueba", "signos_de_roya": lesiones > 0, "calidad_foto": "buena"}
    overlay = Image.new("RGB", (800, 600))
    return Diagnosis(overlay, severidad, "leaf", [], muse, list(avisos), measurable=medible, dae=8 if medible else None)


@pytest.mark.parametrize("cookie,esperado", [(None, "en"), ("en", "en"), ("es", "es"), ("fr", "en")])
def test_el_idioma_de_la_interfaz_llega_a_muse(client, monkeypatch, cookie, esperado):
    from backend import service

    monkeypatch.setenv("ROYALENS_MODE", "real")
    pedidos = []

    async def analizar(_, language="es"):
        pedidos.append(language)
        return _diagnostico(True, porcentaje=2.0, lesiones=1)

    monkeypatch.setattr(service, "analyze", analizar)
    cabeceras = {"cookie": f"royalens_idioma={cookie}"} if cookie else {}
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 4}, headers=cabeceras)
    assert r.status_code == 200
    assert pedidos == [esperado] and r.json()["idioma"] == esperado


def test_foto_de_ejemplo_se_analiza_una_vez_por_idioma(client, monkeypatch):
    from backend import service

    llamadas = []
    original = service.demo.analizar_roya
    monkeypatch.setattr(service.demo, "analizar_roya", lambda img: llamadas.append(1) or original(img))
    for idioma in ("es", "es", "en", "en"):
        r = client.post("/api/ejemplos/hoja-otra-mancha", data={"lote": 1}, headers={"cookie": f"royalens_idioma={idioma}"})
        assert r.status_code == 200 and r.json()["idioma"] == idioma
    assert len(llamadas) == 2


def test_real_foto_sin_medicion_no_cuenta_en_el_lote(client, monkeypatch):
    from backend import service

    monkeypatch.setenv("ROYALENS_MODE", "real")
    antes = client.get("/api/resumen").json()["lotes"][1]["muestra"]["hojas"]

    async def sin_hoja(_, **__):
        return _diagnostico(False, avisos=["No se pudo medir."])

    monkeypatch.setattr(service, "analyze", sin_hoja)
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2})
    assert r.status_code == 200
    m = r.json()["medicion"]
    assert m["valida"] is False and m["porcentaje"] is None and m["nivel"] is None
    assert r.json()["avisos"] == ["No se pudo medir."]

    lote = client.get("/api/resumen").json()["lotes"][1]
    assert lote["muestra"]["hojas"] == antes
    assert lote["roya"] is None

    async def con_roya(_, **__):
        return _diagnostico(True, porcentaje=8.0, lesiones=3)

    monkeypatch.setattr(service, "analyze", con_roya)
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2})
    assert r.json()["medicion"]["clase_dae"] == 8
    assert r.json()["interpretacion"]["signos_de_roya"] is True

    muestra = client.get("/api/resumen").json()["lotes"][1]["muestra"]
    assert muestra == {"hojas": 1, "con_roya": 1, "incidencia": 100, "severidad": 8.0}


def test_real_error_de_api_no_guarda_resultado(client, monkeypatch):
    from backend import service

    monkeypatch.setenv("ROYALENS_MODE", "real")

    async def falla(_, **__):
        raise RuntimeError("401 clave inválida")

    monkeypatch.setattr(service, "analyze", falla)
    antes = len(client.get("/api/resumen").json()["recientes"])
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1})
    assert r.status_code == 502
    assert "401" not in r.json()["detail"]
    assert len(client.get("/api/resumen").json()["recientes"]) == antes


def test_roya_alta_alerta_sin_historial(client, monkeypatch):
    from backend import service

    monkeypatch.setenv("ROYALENS_MODE", "real")

    async def severa(_, **__):
        return _diagnostico(True, porcentaje=25.0, lesiones=9)

    monkeypatch.setattr(service, "analyze", severa)
    client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 4})
    alertas = client.get("/api/resumen").json()["alertas"]
    alerta = next(a for a in alertas if a["lote"] == 4)
    assert alerta["nivel"] == "alta" and "25%" in alerta["texto"]


def test_maduracion_real_cuenta_y_guarda(client, monkeypatch):
    from backend import service
    from royalens.analysis import Instance
    from royalens.pipeline import Cherry, RipenessResult
    import numpy as np

    monkeypatch.setenv("ROYALENS_MODE", "real")
    mascara = np.zeros((600, 800), dtype=bool)
    mascara[10:40, 10:40] = True
    inst = Instance("0", mascara, (10, 10, 40, 40), 0.8)

    async def contar(_, **__):
        cerezas = [Cherry(inst, "maduro")] * 6 + [Cherry(inst, "verde")] * 2
        conteo = {"verde": 2, "pinton": 0, "maduro": 6, "sobremaduro": 0}
        return RipenessResult(cerezas, conteo, {"lo_que_se_ve": "racimo", "recomendacion": "recoger"}, [], True)

    monkeypatch.setattr(service, "analyze_ripeness", contar)
    r = client.post("/api/maduracion", files={"foto": _foto(_racimo)}, data={"lote": 3})
    assert r.status_code == 200
    e = r.json()
    assert e["medicion"] == {
        "valida": True,
        "total": 8,
        "conteo": {"verde": 2, "pinton": 0, "maduro": 6, "sobremaduro": 0},
        "porcentaje_maduro": 75,
    }
    assert len({d["id"] for d in e["detecciones"]}) == 8
    assert e["interpretacion"]["recomendacion"] == "recoger"
    assert e["recomendacion"]["titulo"] == "Buen momento para recolectar"
    assert client.get("/api/resumen").json()["lotes"][2]["maduro"] == 75


def test_maduracion_real_sin_racimo_no_cuenta(client, monkeypatch):
    from backend import service
    from royalens.pipeline import RipenessResult

    monkeypatch.setenv("ROYALENS_MODE", "real")

    async def sin_racimo(_, **__):
        conteo = {"verde": 0, "pinton": 0, "maduro": 0, "sobremaduro": 0}
        return RipenessResult([], conteo, {"es_racimo_de_cafe": False}, ["No es un racimo."], False)

    monkeypatch.setattr(service, "analyze_ripeness", sin_racimo)
    antes = client.get("/api/resumen").json()["lotes"][0]["maduro"]
    r = client.post("/api/maduracion", files={"foto": _foto(_hoja)}, data={"lote": 1})
    assert r.status_code == 200
    assert r.json()["medicion"]["valida"] is False
    assert r.json()["medicion"]["porcentaje_maduro"] is None
    assert client.get("/api/resumen").json()["lotes"][0]["maduro"] == antes


@pytest.mark.parametrize(
    "texto,bloquear",
    [
        ("Aplique 2 cc por litro cada mes", True),
        ("Use 500 ml/ha en floración", True),
        ("Son 1,5 kg por hectárea", True),
        ("Compre Amistar en el almacén", True),
        ("El Lote 3 tiene 14,6% de roya y 21 lesiones", False),
        ("Evalúe 50 árboles por lote, con 10 hojas en cada rama", False),
        ("La app opera con fotos y lo verdadero es consultar", False),
    ],
)
def test_red_de_seguridad_de_dosis(texto, bloquear):
    from backend import chat

    assert chat.habla_de_dosis(texto) is bloquear


def _chat_real(monkeypatch):
    monkeypatch.setenv("ROYALENS_MODE", "real")
    monkeypatch.setenv("MODEL_API_KEY", "clave-de-prueba")


def _eventos(r):
    return [json.loads(linea) for linea in r.text.splitlines()]


def test_chat_transmite_eventos(client, monkeypatch):
    from backend import chat

    _chat_real(monkeypatch)

    async def falso(mensajes, visitante, escaneo_id, lote, idioma):
        assert mensajes == [{"rol": "usuario", "texto": "hola"}]
        assert lote == 2 and idioma == "en"
        yield {"tipo": "texto", "delta": "Buenos "}
        yield {"tipo": "texto", "delta": "días"}
        yield {"tipo": "fin"}

    monkeypatch.setattr(chat, "responder", falso)
    r = client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "hola"}], "lote": 2})
    assert r.status_code == 200
    assert [e["tipo"] for e in _eventos(r)] == ["texto", "texto", "conversacion", "fin"]


def test_chat_error_de_api_se_muestra_como_error(client, monkeypatch):
    from backend import chat

    _chat_real(monkeypatch)

    async def falla(*_):
        yield {"tipo": "texto", "delta": "Parcial"}
        raise RuntimeError("401 clave inválida")

    monkeypatch.setattr(chat, "responder", falla)
    r = client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "hola"}]})
    ultimo = _eventos(r)[-1]
    assert ultimo["tipo"] == "error" and "401" not in ultimo["mensaje"]


def test_chat_respuesta_vacia_de_muse_no_es_error(client, monkeypatch):
    from backend import chat

    _chat_real(monkeypatch)

    class Stream:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        def __aiter__(self):
            return self

        async def __anext__(self):
            raise StopAsyncIteration

        async def get_final_response(self):
            return SimpleNamespace(output=[])

    cliente = SimpleNamespace(responses=SimpleNamespace(stream=lambda **_: Stream()))
    monkeypatch.setattr(chat, "make_client", lambda: cliente)
    r = client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "¿Cuánto producto le echo?"}]})
    eventos = _eventos(r)
    assert [e["tipo"] for e in eventos] == ["reemplazo", "conversacion", "fin"]
    assert eventos[0]["texto"] == chat.SUSTITUTO_VACIO["en"]


@pytest.mark.parametrize(
    "mensaje,tipos",
    [
        ("The response was filtered due to the prompt triggering our content management policy.", ["reemplazo", "conversacion", "fin"]),
        ("El modelo no existe.", ["error"]),
    ],
)
def test_chat_distingue_filtro_de_contenido_de_otros_errores(client, monkeypatch, mensaje, tipos):
    from openai import BadRequestError

    from backend import chat

    _chat_real(monkeypatch)

    def rechaza(**_):
        solicitud = httpx.Request("POST", "https://api.meta.ai/v1/responses")
        raise BadRequestError(mensaje, response=httpx.Response(400, request=solicitud), body=None)

    cliente = SimpleNamespace(responses=SimpleNamespace(stream=rechaza))
    monkeypatch.setattr(chat, "make_client", lambda: cliente)
    r = client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "¿Cuánto producto le echo?"}]})
    assert [e["tipo"] for e in _eventos(r)] == tipos


def test_foto_de_ejemplo_se_marca_en_la_finca(client):
    assert client.get("/api/resumen").json()["hay_fotos_ejemplo"] is False
    assert client.post("/api/ejemplos/hoja-sana", data={"lote": 1}).status_code == 200
    datos = client.get("/api/resumen").json()
    assert datos["hay_fotos_ejemplo"] is True
    assert datos["recientes"][0]["foto_ejemplo"] is True
    assert client.get("/api/estadisticas").json()["hay_fotos_ejemplo"] is True


def test_alerta_de_foto_de_ejemplo_no_parece_de_la_finca():
    from backend import store

    visitante = "visitante-alerta"
    store.guardar(
        {
            "id": store.nuevo_id(), "tipo": "roya", "lote": 1, "modo": "demo",
            "creado": datetime.now(timezone.utc).isoformat(),
            "medicion": {"valida": True, "porcentaje": 40.0, "nivel": "Severa"},
            "foto_ejemplo": {"titulo": "Hoja", "credito": "Prueba", "url": None},
        },
        visitante,
    )
    alerta = next(a for a in store.resumen("demo", visitante)["alertas"] if a["lote"] == 1)
    assert alerta["nivel"] == "revisar" and "foto de ejemplo" in alerta["texto"]
    assert "extensionista" not in alerta["texto"]


def test_chat_valida_la_entrada(client, monkeypatch):
    _chat_real(monkeypatch)
    usuario = {"rol": "usuario", "texto": "hola"}
    assert client.post("/api/chat", json={"mensajes": []}).status_code == 422
    assert client.post("/api/chat", json={"mensajes": [{"rol": "sistema", "texto": "x"}]}).status_code == 422
    assert client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "x" * 1001}]}).status_code == 400
    assert client.post("/api/chat", json={"mensajes": [usuario, {"rol": "asistente", "texto": "y"}]}).status_code == 400
    assert client.post("/api/chat", json={"mensajes": [usuario], "lote": 9}).status_code == 400


def test_chat_sin_clave_o_en_demo_no_responde(client, monkeypatch):
    cuerpo = {"mensajes": [{"rol": "usuario", "texto": "hola"}]}
    assert client.post("/api/chat", json=cuerpo).status_code == 503  # modo demo
    monkeypatch.setenv("ROYALENS_MODE", "real")
    monkeypatch.delenv("MODEL_API_KEY", raising=False)
    assert client.post("/api/chat", json=cuerpo).status_code == 503


def test_contexto_usa_cifras_del_historial(client, monkeypatch):
    from backend import chat, service

    monkeypatch.setenv("ROYALENS_MODE", "real")

    async def con_roya(_, **__):
        return _diagnostico(True, porcentaje=8.0, lesiones=3)

    monkeypatch.setattr(service, "analyze", con_roya)
    e = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
    visitante = client.cookies["royalens_visitante"]
    contexto = chat.contexto_finca("real", visitante, e["id"], 1)
    assert "8.0%" in contexto and "Lote 1" in contexto and "pregunta sobre este escaneo" in contexto


def _otro_navegador():
    return TestClient(app)


def test_dos_navegadores_no_comparten_datos(client):
    e = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
    assert client.get(f"/api/escaneos/{e['id']}").status_code == 200
    assert client.get("/api/resumen").json()["es_ejemplo"] is False
    assert client.cookies["royalens_visitante"]

    with _otro_navegador() as otro:
        assert otro.get(f"/api/escaneos/{e['id']}").status_code == 404
        assert otro.get(e["imagen_url"]).status_code == 404
        assert otro.get(e["overlay_url"]).status_code == 404
        panel = otro.get("/api/resumen").json()
        assert panel["es_ejemplo"] is True
        assert all(r["ejemplo"] for r in panel["recientes"])


def test_cookie_de_visitante_es_segura(client):
    cabecera = client.get("/api/estado").headers["set-cookie"].lower()
    assert "httponly" in cabecera and "samesite=lax" in cabecera


def test_finca_de_ejemplo_no_se_mezcla_con_escaneos(client):
    assert client.get("/api/resumen").json()["es_ejemplo"] is True
    client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2})
    panel = client.get("/api/resumen").json()
    assert panel["es_ejemplo"] is False
    assert panel["indicadores"]["escaneos_mes"] == 1
    assert all(l["roya"] is None for l in panel["lotes"] if l["id"] != 2)


def test_limite_por_ip_y_total(client, monkeypatch):
    from backend import store

    monkeypatch.setitem(store.LIMITES, "analisis", (2, 3))
    foto = {"foto": _foto(_hoja)}
    cab = {"x-forwarded-for": "9.9.9.1"}
    assert client.post("/api/roya", files=foto, headers=cab).status_code == 200
    assert client.post("/api/roya", files=foto, headers=cab).status_code == 200
    r = client.post("/api/roya", files=foto, headers=cab)
    assert r.status_code == 429 and "límite" in r.json()["detail"]

    # Borrar la cookie no quita el límite, y el cliente no puede falsear la IP real.
    with _otro_navegador() as otro:
        assert otro.post("/api/roya", files=foto, headers=cab).status_code == 429
        assert otro.post("/api/roya", files=foto, headers={"x-forwarded-for": "1.1.1.1, 9.9.9.1"}).status_code == 429
        # Otra IP puede hasta llenar el total del día, y después tampoco.
        assert otro.post("/api/roya", files=foto, headers={"x-forwarded-for": "9.9.9.2"}).status_code == 200
        assert otro.post("/api/roya", files=foto, headers={"x-forwarded-for": "9.9.9.3"}).status_code == 429


def test_limite_del_chat(client, monkeypatch):
    from backend import chat, store

    _chat_real(monkeypatch)
    monkeypatch.setitem(store.LIMITES, "chat", (1, 100))

    async def falso(*_):
        yield {"tipo": "fin"}

    monkeypatch.setattr(chat, "responder", falso)
    cuerpo = {"mensajes": [{"rol": "usuario", "texto": "hola"}]}
    cab = {"x-forwarded-for": "9.9.8.1"}
    assert client.post("/api/chat", json=cuerpo, headers=cab).status_code == 200
    assert client.post("/api/chat", json=cuerpo, headers=cab).status_code == 429


def test_foto_de_ejemplo_se_analiza_una_sola_vez(client, monkeypatch):
    from backend import service, store

    monkeypatch.setitem(store.LIMITES, "analisis", (1, 10))
    llamadas = []
    original = service.demo.analizar_roya

    def contar(img):
        llamadas.append(1)
        return original(img)

    monkeypatch.setattr(service.demo, "analizar_roya", contar)
    cab = {"x-forwarded-for": "9.9.7.1"}
    a = client.post("/api/ejemplos/hoja-sana", data={"lote": 1}, headers=cab)
    assert a.status_code == 200, a.text
    assert client.post("/api/roya", files={"foto": _foto(_hoja)}, headers=cab).status_code == 429  # ya gastó su cupo

    with _otro_navegador() as otro:
        b = otro.post("/api/ejemplos/hoja-sana", data={"lote": 3}, headers=cab)
        assert b.status_code == 200  # reusar un resultado no gasta cupo
        assert len(llamadas) == 1
        assert b.json()["lote"] == 3
        assert b.json()["id"] != a.json()["id"] and b.json()["imagen_url"] != a.json()["imagen_url"]
        assert otro.get(b.json()["imagen_url"]).status_code == 200
        assert "Muse Image" in b.json()["foto_ejemplo"]["credito"]
        assert otro.get("/api/resumen").json()["lotes"][2]["roya"] is not None


def test_ejemplos_lista_y_valida(client):
    roya = client.get("/api/ejemplos/roya").json()
    assert len(roya) == 4
    assert all(e["credito"] for e in roya)
    assert client.post("/api/ejemplos/no-existe", data={"lote": 1}).status_code == 404
    assert client.post("/api/ejemplos/hoja-sana", data={"lote": 9}).status_code == 400


def test_borrar_mis_datos_borra_fotos_y_no_toca_a_otros(client):
    from backend import store

    mio = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
    with _otro_navegador() as otro:
        ajeno = otro.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
        assert client.delete("/api/mis-datos").json() == {"borrados": 1}
        assert not (store.MEDIA_DIR / f"{mio['id']}.jpg").exists()
        assert not (store.MEDIA_DIR / f"{mio['id']}_overlay.jpg").exists()
        assert client.get(f"/api/escaneos/{mio['id']}").status_code == 404
        assert client.get("/api/resumen").json()["es_ejemplo"] is True
        assert otro.get(f"/api/escaneos/{ajeno['id']}").status_code == 200
        assert (store.MEDIA_DIR / f"{ajeno['id']}.jpg").exists()


def test_borrado_automatico_respeta_plazo_y_ejemplos(client):
    from datetime import datetime, timedelta, timezone

    from backend import store

    viejo = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
    nuevo = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1}).json()
    hace = (datetime.now(timezone.utc) - timedelta(days=store.DIAS_RETENCION + 1)).isoformat()
    with store._db() as con:
        con.execute("UPDATE escaneos SET creado = ? WHERE id = ?", (hace, viejo["id"]))
    assert store.purgar_antiguos() == 1
    assert not (store.MEDIA_DIR / f"{viejo['id']}.jpg").exists()
    assert client.get(f"/api/escaneos/{viejo['id']}").status_code == 404
    assert client.get(f"/api/escaneos/{nuevo['id']}").status_code == 200
    assert store.listar("demo", store.EJEMPLO)


def test_acepta_fotos_heic_de_iphone(client):
    import pillow_heif

    pillow_heif.register_heif_opener()
    img = Image.new("RGB", (800, 600), (12, 30, 18))
    _hoja(ImageDraw.Draw(img))
    buf = io.BytesIO()
    img.save(buf, format="HEIF", quality=90)
    r = client.post("/api/roya", files={"foto": ("foto.heic", buf.getvalue(), "image/heic")}, data={"lote": 1})
    assert r.status_code == 200, r.text


def test_frontend_compilado_no_expone_otros_archivos(client):
    from backend.main import DIST

    if not DIST.exists():
        pytest.skip("Sin frontend compilado")
    assert client.get("/favicon.svg").headers["content-type"].startswith("image/svg")
    pagina = client.get("/finca", headers={"x-forwarded-proto": "https", "x-forwarded-host": "royalens.ejemplo.co"})
    assert 'content="https://royalens.ejemplo.co/img/compartir.jpg"' in pagina.text
    falso = client.get("/", headers={"x-forwarded-host": 'x"><script>'})
    assert "<script>\"" not in falso.text and 'x"><script>' not in falso.text
    assert client.get("/assets/noexiste.js").status_code == 404
    assert client.get("/media/noexiste.jpg").status_code == 404
    assert client.get("/api/noexiste").status_code == 404
    assert "RoyaLens" in client.get("/..%2f..%2fbackend%2fmain.py").text
    assert "MAX_FOTO_BYTES" not in client.get("/..%2f..%2fbackend%2fmain.py").text


def test_analisis_trabado_es_error_y_no_guarda(client, monkeypatch):
    import asyncio

    from backend import main, service

    monkeypatch.setenv("ROYALENS_MODE", "real")
    monkeypatch.setattr(main, "TIEMPO_ANALISIS", 0.05)

    async def trabado(_, **__):
        await asyncio.sleep(5)

    monkeypatch.setattr(service, "analyze", trabado)
    r = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 1})
    assert r.status_code == 504 and "tardó" in r.json()["detail"]
    assert client.get("/api/resumen").json()["indicadores"]["escaneos_mes"] == 0


def test_cliente_de_la_api_tiene_tiempo_limite(monkeypatch):
    from royalens import config
    from royalens.meta_api import make_client

    monkeypatch.setenv("MODEL_API_KEY", "clave-de-prueba")
    cliente = make_client()
    assert cliente.timeout == config.API_TIMEOUT_SECONDS and cliente.max_retries == 1


def _preguntar(cliente, monkeypatch, texto, conversacion=None):
    from backend import chat

    _chat_real(monkeypatch)

    async def falso(mensajes, visitante, escaneo_id, lote, idioma):
        yield {"tipo": "texto", "delta": f"Respuesta a {mensajes[-1]['texto']}"}
        yield {"tipo": "citas", "citas": [{"titulo": "Fuente", "url": "https://ejemplo.co"}], "titulo": "Fuentes de la web"}
        yield {"tipo": "fin"}

    monkeypatch.setattr(chat, "responder", falso)
    cuerpo = {"mensajes": [{"rol": "usuario", "texto": texto}], "conversacion_id": conversacion}
    eventos = _eventos(cliente.post("/api/chat", json=cuerpo))
    return next(e for e in eventos if e["tipo"] == "conversacion")


def test_historial_guarda_y_continua_conversaciones(client, monkeypatch):
    c = _preguntar(client, monkeypatch, "¿Cómo reconozco la roya?")
    assert c["titulo"] == "¿Cómo reconozco la roya?"
    assert _preguntar(client, monkeypatch, "¿Y en el envés?", c["id"])["id"] == c["id"]
    otra = _preguntar(client, monkeypatch, "¿Cuándo cosecho?")
    assert otra["id"] != c["id"]

    lista = client.get("/api/conversaciones").json()
    assert {x["id"]: x["preguntas"] for x in lista} == {c["id"]: 2, otra["id"]: 1}
    guardada = client.get(f"/api/conversaciones/{c['id']}").json()
    assert [m["rol"] for m in guardada["mensajes"]] == ["usuario", "asistente", "usuario", "asistente"]
    assert guardada["mensajes"][1]["citas"][0]["url"] == "https://ejemplo.co"
    assert guardada["mensajes"][1]["tituloCitas"] == "Fuentes de la web"

    assert client.delete(f"/api/conversaciones/{otra['id']}").json() == {"borrada": True}
    assert client.get(f"/api/conversaciones/{otra['id']}").status_code == 404


def test_historial_es_privado_y_se_borra_con_mis_datos(client, monkeypatch):
    c = _preguntar(client, monkeypatch, "Mi pregunta")
    with _otro_navegador() as otro:
        assert otro.get(f"/api/conversaciones/{c['id']}").status_code == 404
        assert otro.delete(f"/api/conversaciones/{c['id']}").status_code == 404
        assert otro.get("/api/conversaciones").json() == []
        # Otro navegador tampoco puede escribir en una conversación ajena.
        ajena = _preguntar(otro, monkeypatch, "Intento", c["id"])
        assert ajena["id"] != c["id"]
    assert len(client.get(f"/api/conversaciones/{c['id']}").json()["mensajes"]) == 2
    client.delete("/api/mis-datos")
    assert client.get("/api/conversaciones").json() == []


def test_error_del_chat_no_guarda_el_turno(client, monkeypatch):
    from backend import chat

    _chat_real(monkeypatch)

    async def falla(*_):
        yield {"tipo": "texto", "delta": "Parcial"}
        raise RuntimeError("caída")

    monkeypatch.setattr(chat, "responder", falla)
    client.post("/api/chat", json={"mensajes": [{"rol": "usuario", "texto": "hola"}]})
    assert client.get("/api/conversaciones").json() == []


def test_estadisticas_calcula_desde_escaneos_y_preguntas(client, monkeypatch):
    from backend import service

    assert client.get("/api/estadisticas").json()["es_ejemplo"] is True

    monkeypatch.setenv("ROYALENS_MODE", "real")

    resultados = iter([_diagnostico(True, porcentaje=8.0, lesiones=3), _diagnostico(True, porcentaje=0.0), _diagnostico(False)])

    async def analizar(_, **__):
        return next(resultados)

    monkeypatch.setattr(service, "analyze", analizar)
    for _ in range(3):
        assert client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2}).status_code == 200
    _preguntar(client, monkeypatch, "¿Cómo va mi finca?")

    d = client.get("/api/estadisticas").json()
    assert d["es_ejemplo"] is False
    assert d["totales"]["escaneos"] == 3 and d["totales"]["hojas"] == 2 and d["totales"]["sin_medicion"] == 1
    assert d["roya"]["incidencia"] == 50 and d["roya"]["severidad"] == 4.0
    lote = d["por_lote"][1]
    assert lote["hojas"] == 2 and lote["con_roya"] == 1 and len(lote["puntos"]) == 2
    assert d["totales"]["preguntas"] == 1 and d["preguntas"][0]["texto"] == "¿Cómo va mi finca?"
    assert sum(s["escaneos"] for s in d["semanas"]) == 3 and sum(s["preguntas"] for s in d["semanas"]) == 1


def test_resultado_compara_con_el_escaneo_anterior_del_lote(client, monkeypatch):
    from backend import service

    resultados = iter([_diagnostico(True, porcentaje=8.0, lesiones=3), _diagnostico(True, porcentaje=11.0, lesiones=5)])

    async def analizar(_, **__):
        return next(resultados)

    monkeypatch.setenv("ROYALENS_MODE", "real")
    monkeypatch.setattr(service, "analyze", analizar)
    primero = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2}).json()
    assert primero["comparacion"] is None
    segundo = client.post("/api/roya", files={"foto": _foto(_hoja)}, data={"lote": 2}).json()
    assert segundo["comparacion"]["valor"] == 8.0 and segundo["comparacion"]["cambio"] == 3.0
