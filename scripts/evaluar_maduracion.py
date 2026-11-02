"""Corre el flujo real de maduración sobre `fotos/` y compara con los conteos a mano. Gasta créditos.

Uso: PYTHONPATH=royalens .venv/bin/python scripts/evaluar_maduracion.py [carpetas...]
Lee `fotos/racimo/conteos.json` y deja imágenes y `resultados.json` en data/calibracion/maduracion/.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from royalens.meta_api import prepare_image
from royalens.pipeline import analyze_ripeness

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "calibracion" / "maduracion"
EXTENSIONES = {".jpg", ".jpeg", ".png"}
COLORES = {"verde": (120, 220, 60), "pinton": (255, 210, 0), "maduro": (255, 40, 30), "sobremaduro": (190, 60, 255)}
MARGEN = 0.2


async def evaluar(cupo, ruta, conteos):
    async with cupo:
        r = await analyze_ripeness(Image.open(ruta))
    img, _ = prepare_image(Image.open(ruta))
    dibujo = ImageDraw.Draw(img)
    for c in r.cherries:
        dibujo.ellipse(c.instance.box, outline=COLORES[c.state], width=5)
    img.save(SALIDA / f"{ruta.stem}.jpg", quality=85)
    mano = conteos.get(ruta.name)
    total = len(r.cherries)
    if ruta.parent.name == "racimo":
        cumple = r.measurable and (mano is None or abs(total - mano) <= MARGEN * mano)
    else:
        cumple = not r.measurable
    return {"foto": f"{ruta.parent.name}/{ruta.name}", "a_mano": mano, "cumple": cumple, **r.as_dict()}


async def main() -> int:
    carpetas = sys.argv[1:] or ["racimo", "sueltas", "no_hoja", "mala", "sana"]
    SALIDA.mkdir(parents=True, exist_ok=True)
    archivo = RAIZ / "fotos" / "racimo" / "conteos.json"
    conteos = json.loads(archivo.read_text()) if archivo.exists() else {}
    rutas = [f for c in carpetas for f in sorted((RAIZ / "fotos" / c).iterdir()) if f.suffix.lower() in EXTENSIONES]
    cupo = asyncio.Semaphore(3)
    resultados = await asyncio.gather(*(evaluar(cupo, r, conteos) for r in rutas), return_exceptions=True)

    filas, fallos = [], 0
    for ruta, r in zip(rutas, resultados):
        if isinstance(r, Exception):
            print(f"ERROR {ruta.name}: {type(r).__name__}: {str(r)[:200]}")
            fallos += 1
        else:
            filas.append(r)
            fallos += not r["cumple"]
    (SALIDA / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1))

    for f in filas:
        c, muse = f["conteo"], f["interpretacion_muse"]
        print(
            f"{'ok ' if f['cumple'] else 'MAL'} {f['foto']:28} total={f['total']:3} mano={str(f['a_mano']):4} "
            f"V={c['verde']:3} P={c['pinton']:3} M={c['maduro']:3} S={c['sobremaduro']:3} "
            f"racimo={str(muse.get('es_racimo_de_cafe')):5} cal={muse.get('calidad_foto')}"
        )
    print(f"\n{sum(f['cumple'] for f in filas)} de {len(rutas)} cumplen")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
