"""API de RoyaLens. En producción también sirve el frontend ya compilado."""

from __future__ import annotations

import io
import logging
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image, UnidentifiedImageError

from royalens.meta_api import MissingApiKey

from . import service, store

log = logging.getLogger("royalens")
MAX_FOTO_BYTES = 15 * 1024 * 1024
DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def _inicio(_: FastAPI):
    if service.modo() == "demo":
        store.sembrar_ejemplo()
    yield


app = FastAPI(title="RoyaLens", lifespan=_inicio)
store.MEDIA_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=store.MEDIA_DIR), name="media")


async def _leer_foto(foto: UploadFile) -> Image.Image:
    datos = await foto.read()
    if len(datos) > MAX_FOTO_BYTES:
        raise HTTPException(413, "La foto pesa más de 15 MB.")
    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.load()
    except (UnidentifiedImageError, OSError):
        raise HTTPException(400, "El archivo no es una imagen válida.")
    return imagen


def _validar_lote(lote: int) -> None:
    if lote not in store.LOTES:
        raise HTTPException(400, f"El lote {lote} no existe.")


async def _analizar(funcion, foto: UploadFile, lote: int) -> dict:
    _validar_lote(lote)
    imagen = await _leer_foto(foto)
    try:
        return await funcion(imagen, lote)
    except MissingApiKey as exc:
        raise HTTPException(503, str(exc))
    except service.MaduracionNoConectada as exc:
        raise HTTPException(501, str(exc))
    except Exception:
        log.exception("Falló el análisis")
        raise HTTPException(502, "El análisis falló. No se guardó ningún resultado; intenta de nuevo.")


@app.get("/api/estado")
def estado() -> dict:
    return {"modo": service.modo(), "lotes": store.LOTES}


@app.post("/api/roya")
async def roya(foto: UploadFile = File(...), lote: int = Form(1)) -> dict:
    return await _analizar(service.analizar_roya, foto, lote)


@app.post("/api/maduracion")
async def maduracion(foto: UploadFile = File(...), lote: int = Form(1)) -> dict:
    return await _analizar(service.analizar_maduracion, foto, lote)


@app.get("/api/escaneos/{escaneo_id}")
def escaneo(escaneo_id: str) -> dict:
    encontrado = store.obtener(escaneo_id, service.modo())
    if not encontrado:
        raise HTTPException(404, "No se encontró ese escaneo.")
    return encontrado


@app.get("/api/resumen")
def resumen() -> dict:
    return store.resumen(service.modo())


if DIST.exists():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")
    app.mount("/img", StaticFiles(directory=DIST / "img"), name="img")

    @app.get("/{ruta:path}", include_in_schema=False)
    def spa(ruta: str) -> FileResponse:
        if ruta.startswith("api/"):
            raise HTTPException(404, "Ruta no encontrada.")
        return FileResponse(DIST / "index.html")
