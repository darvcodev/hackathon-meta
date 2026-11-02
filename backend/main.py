"""API de RoyaLens. En producción también sirve el frontend ya compilado."""

from __future__ import annotations

import asyncio
import io
import json
import logging
import re
from pathlib import Path

from contextlib import asynccontextmanager
from typing import Literal
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError
from pillow_heif import register_heif_opener
from pydantic import BaseModel, Field

from royalens.meta_api import MissingApiKey

from . import chat, ejemplos, service, store

register_heif_opener()  # las fotos de iPhone pueden llegar en HEIC

log = logging.getLogger("royalens")
MAX_FOTO_BYTES = 15 * 1024 * 1024
MAX_PREGUNTA = 1000
COOKIE = "royalens_visitante"
# Un análisis denso usa unos 350 MB: los demás esperan su turno en vez de agotar la memoria.
CUPO_ANALISIS = asyncio.Semaphore(3)
TIEMPO_ANALISIS = 120
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


async def _purgar_cada_hora() -> None:
    while True:
        try:
            borrados = store.purgar_antiguos()
            if borrados:
                log.info("Se borraron %s escaneos antiguos", borrados)
        except Exception:
            log.exception("Falló el borrado de escaneos antiguos")
        await asyncio.sleep(3600)


@asynccontextmanager
async def _inicio(_: FastAPI):
    store.sembrar_ejemplo(service.modo())
    tarea = asyncio.create_task(_purgar_cada_hora())
    yield
    tarea.cancel()


app = FastAPI(title="RoyaLens", lifespan=_inicio)
store.MEDIA_DIR.mkdir(parents=True, exist_ok=True)


@app.middleware("http")
async def _visitante(request: Request, siguiente):
    """Cada navegador tiene su historial, con una cookie anónima y sin cuentas."""
    actual = request.cookies.get(COOKIE, "")
    nuevo = None if re.fullmatch(r"[0-9a-f]{32}", actual) else uuid4().hex
    request.state.visitante = nuevo or actual
    respuesta = await siguiente(request)
    if nuevo and request.url.path.startswith("/api/"):
        respuesta.set_cookie(
            COOKIE,
            nuevo,
            max_age=365 * 24 * 3600,
            httponly=True,
            samesite="lax",
            secure=request.headers.get("x-forwarded-proto") == "https",
        )
    return respuesta


def _ip(request: Request) -> str:
    # Detrás del proxy de Coolify, el último valor lo agrega el proxy y el cliente no puede falsearlo.
    reenviada = request.headers.get("x-forwarded-for")
    if reenviada:
        return reenviada.split(",")[-1].strip()
    return request.client.host if request.client else "desconocida"


def _consumir(tipo: str, request: Request) -> None:
    try:
        store.consumir(tipo, _ip(request))
    except store.LimiteAlcanzado as exc:
        raise HTTPException(429, str(exc))


async def _leer_foto(foto: UploadFile) -> Image.Image:
    datos = await foto.read()
    if len(datos) > MAX_FOTO_BYTES:
        raise HTTPException(413, "La foto pesa más de 15 MB.")
    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise HTTPException(400, "El archivo no es una imagen válida.")
    return imagen


def _validar_lote(lote: int) -> None:
    if lote not in store.LOTES:
        raise HTTPException(400, f"El lote {lote} no existe.")


async def _protegido(trabajo) -> dict:
    """Convierte fallos de la API en errores que se muestran como errores, nunca como resultados."""
    try:
        async with CUPO_ANALISIS:
            return await asyncio.wait_for(trabajo, TIEMPO_ANALISIS)
    except MissingApiKey as exc:
        raise HTTPException(503, str(exc))
    except HTTPException:
        raise
    except TimeoutError:
        log.error("El análisis superó %s segundos", TIEMPO_ANALISIS)
        raise HTTPException(504, "El análisis tardó demasiado. No se guardó ningún resultado; intente de nuevo.")
    except Exception:
        log.exception("Falló el análisis")
        raise HTTPException(502, "El análisis falló. No se guardó ningún resultado; intente de nuevo.")


async def _analizar(funcion, foto: UploadFile, lote: int, request: Request) -> dict:
    _validar_lote(lote)
    imagen = await _leer_foto(foto)
    _consumir("analisis", request)
    return await _protegido(funcion(imagen, lote, request.state.visitante))


class Mensaje(BaseModel):
    rol: Literal["usuario", "asistente"]
    texto: str = Field(min_length=1, max_length=4000)


class Pregunta(BaseModel):
    mensajes: list[Mensaje] = Field(min_length=1, max_length=40)
    conversacion_id: str | None = Field(default=None, max_length=32)
    escaneo_id: str | None = Field(default=None, max_length=32)
    lote: int | None = None


@app.post("/api/chat")
async def preguntar(p: Pregunta, request: Request) -> StreamingResponse:
    ultimo = p.mensajes[-1]
    if ultimo.rol != "usuario" or len(ultimo.texto) > MAX_PREGUNTA:
        raise HTTPException(400, f"La pregunta debe tener máximo {MAX_PREGUNTA} caracteres.")
    if p.lote is not None:
        _validar_lote(p.lote)
    try:
        chat.comprobar_disponible()
    except (MissingApiKey, chat.ChatNoDisponible) as exc:
        raise HTTPException(503, str(exc))
    _consumir("chat", request)
    visitante = request.state.visitante

    async def eventos():
        try:
            async for evento in chat.conversar(
                [m.model_dump() for m in p.mensajes], visitante, p.conversacion_id, p.escaneo_id, p.lote
            ):
                yield json.dumps(evento, ensure_ascii=False) + "\n"
        except Exception:
            log.exception("Falló el asistente")
            yield json.dumps({"tipo": "error", "mensaje": "El asistente no pudo responder. Intente de nuevo."}, ensure_ascii=False) + "\n"

    return StreamingResponse(eventos(), media_type="application/x-ndjson")


@app.get("/api/estado")
def estado() -> dict:
    return {"modo": service.modo(), "lotes": store.LOTES}


@app.post("/api/roya")
async def roya(request: Request, foto: UploadFile = File(...), lote: int = Form(1)) -> dict:
    return await _analizar(service.analizar_roya, foto, lote, request)


@app.post("/api/maduracion")
async def maduracion(request: Request, foto: UploadFile = File(...), lote: int = Form(1)) -> dict:
    return await _analizar(service.analizar_maduracion, foto, lote, request)


@app.get("/api/ejemplos/{tipo}")
def lista_ejemplos(tipo: Literal["roya", "maduracion"]) -> list[dict]:
    return ejemplos.publicos(tipo)


@app.post("/api/ejemplos/{slug}")
async def analizar_ejemplo(slug: str, request: Request, lote: int = Form(1)) -> dict:
    _validar_lote(lote)
    if not ejemplos.buscar(slug):
        raise HTTPException(404, "Esa foto de ejemplo no existe.")
    return await _protegido(
        service.analizar_ejemplo(slug, lote, request.state.visitante, lambda: _consumir("analisis", request))
    )


@app.get("/api/escaneos/{escaneo_id}")
def escaneo(escaneo_id: str, request: Request) -> dict:
    encontrado = store.obtener(escaneo_id, service.modo(), request.state.visitante)
    if not encontrado:
        raise HTTPException(404, "No se encontró ese escaneo.")
    return encontrado


@app.get("/media/{nombre}", include_in_schema=False)
def medio(nombre: str, request: Request) -> FileResponse:
    """Las fotos pertenecen al visitante que creó el escaneo."""
    if not re.fullmatch(r"[0-9a-f]{12}(?:_overlay)?\.jpg", nombre):
        raise HTTPException(404, "Foto no encontrada.")
    escaneo_id = nombre[:12]
    registro = store.obtener(escaneo_id, service.modo(), request.state.visitante)
    if not registro or f"/media/{nombre}" not in (registro.get("imagen_url"), registro.get("overlay_url")):
        raise HTTPException(404, "Foto no encontrada.")
    ruta = store.MEDIA_DIR / nombre
    if not ruta.is_file():
        raise HTTPException(404, "Foto no encontrada.")
    return FileResponse(ruta, media_type="image/jpeg")


@app.get("/api/resumen")
def resumen(request: Request) -> dict:
    return store.resumen(service.modo(), request.state.visitante)


@app.get("/api/estadisticas")
def estadisticas(request: Request) -> dict:
    return store.estadisticas(service.modo(), request.state.visitante)


@app.get("/api/conversaciones")
def conversaciones(request: Request) -> list[dict]:
    return store.listar_conversaciones(service.modo(), request.state.visitante)


@app.get("/api/conversaciones/{conversacion_id}")
def conversacion(conversacion_id: str, request: Request) -> dict:
    encontrada = store.obtener_conversacion(service.modo(), request.state.visitante, conversacion_id)
    if not encontrada:
        raise HTTPException(404, "No se encontró esa conversación.")
    return encontrada


@app.delete("/api/conversaciones/{conversacion_id}")
def borrar_conversacion(conversacion_id: str, request: Request) -> dict:
    if not store.borrar_conversacion(service.modo(), request.state.visitante, conversacion_id):
        raise HTTPException(404, "No se encontró esa conversación.")
    return {"borrada": True}


@app.delete("/api/mis-datos")
def borrar_mis_datos(request: Request) -> dict:
    return {"borrados": store.borrar_visitante(service.modo(), request.state.visitante)}


def _pagina(request: Request) -> HTMLResponse:
    """Las redes sociales exigen la imagen para compartir con su dirección completa."""
    esquema = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host", "")
    html = (DIST / "index.html").read_text(encoding="utf-8")
    if esquema in ("http", "https") and re.fullmatch(r"[A-Za-z0-9.:-]+", host):
        html = html.replace('content="/img/compartir.jpg"', f'content="{esquema}://{host}/img/compartir.jpg"')
    return HTMLResponse(html)


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    app.mount("/img", StaticFiles(directory=DIST / "img"), name="img")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str, request: Request):
        if ruta.startswith(("api/", "assets/", "media/")):
            raise HTTPException(404, "Ruta no encontrada.")
        # Archivos de la raíz del frontend, como el icono de la pestaña.
        archivo = (DIST / ruta).resolve()
        if ruta and archivo.is_file() and archivo.is_relative_to(DIST.resolve()):
            return FileResponse(archivo)
        return _pagina(request)
