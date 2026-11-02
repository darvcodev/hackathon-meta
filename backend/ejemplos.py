"""Fotos de ejemplo para probar la app sin tener un cafetal cerca."""

from __future__ import annotations

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent / "frontend"
# Sube esta versión cuando cambie el análisis: los resultados guardados dejan de usarse.
VERSION_ANALISIS = "2026-11-02-fotos"

EJEMPLOS = [
    {
        "slug": "hoja-roya", "tipo": "roya", "titulo": "Hoja con roya", "generada": True,
        "credito": "Imagen generada con Muse Image, no es una foto real", "url": None,
    },
    {
        "slug": "hoja-sana", "tipo": "roya", "titulo": "Hoja sana", "generada": True,
        "credito": "Imagen generada con Muse Image, no es una foto real", "url": None,
    },
    {
        "slug": "hoja-otra-mancha", "tipo": "roya", "titulo": "Otra enfermedad", "generada": True,
        "credito": "Imagen generada con Muse Image, no es una foto real", "url": None,
    },
    {
        "slug": "hoja-generada", "tipo": "roya", "titulo": "Roya marcada", "generada": True,
        "credito": "Imagen generada con IA, no es una foto real", "url": None,
    },
    {
        "slug": "racimo-mixto", "tipo": "maduracion", "titulo": "Racimo mixto", "generada": False,
        "credito": "U. S. Fish and Wildlife Service, dominio público",
        "url": "https://commons.wikimedia.org/wiki/File:Clumps_of_coffee_berries_growing_on_a_tree,_by_Brian_Smith.jpg",
    },
    {
        "slug": "racimo-verde", "tipo": "maduracion", "titulo": "Racimo verde", "generada": False,
        "credito": "Dinkum, CC0",
        "url": "https://commons.wikimedia.org/wiki/File:Coffea_arabica_serres_du_Luxembourg.jpg",
    },
    {
        "slug": "racimo-rojo", "tipo": "maduracion", "titulo": "Racimo maduro", "generada": True,
        "credito": "Imagen generada con Muse Image, no es una foto real", "url": None,
    },
    {
        "slug": "racimo-generado", "tipo": "maduracion", "titulo": "Todos los estados", "generada": True,
        "credito": "Imagen generada con IA, no es una foto real", "url": None,
    },
]


def publicos(tipo: str) -> list[dict]:
    return [{**e, "imagen_url": f"/img/ejemplos/{e['slug']}.jpg"} for e in EJEMPLOS if e["tipo"] == tipo]


def buscar(slug: str) -> dict | None:
    return next((e for e in EJEMPLOS if e["slug"] == slug), None)


def ruta(slug: str) -> Path:
    for carpeta in ("dist", "public"):
        archivo = RAIZ / carpeta / "img" / "ejemplos" / f"{slug}.jpg"
        if archivo.exists():
            return archivo
    raise FileNotFoundError(slug)
