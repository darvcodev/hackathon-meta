"""Compara prompts de lesión de SAM sobre las fotos de `fotos/`. Gasta créditos.

Uso: PYTHONPATH=royalens .venv/bin/python scripts/calibrar.py roya sana --prompts "orange rust spot" "rust"
Deja overlays y `resultados.json` en data/calibracion/<etiqueta>/.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import numpy as np
from PIL import Image

from royalens import config
from royalens.analysis import main_leaf, measure, render_overlay, rust_lesions
from royalens.meta_api import make_client, prepare_image, segment

RAIZ = Path(__file__).resolve().parent.parent
EXTENSIONES = {".jpg", ".jpeg", ".png"}


async def medir(client, cupo, ruta, prompts, min_conf, salida):
    img, data_url = prepare_image(Image.open(ruta))
    shape = (img.height, img.width)

    async def pedir(prompt):
        async with cupo:
            return await segment(client, data_url, prompt, img.size, min_conf)

    hojas, prompt_hoja = [], None
    for prompt in config.LEAF_PROMPTS:
        hojas = await pedir(prompt)
        if hojas:
            prompt_hoja = prompt
            break
    hoja = main_leaf(hojas, shape)
    mascara = hoja.mask if hoja else np.zeros(shape, dtype=bool)

    grupos = await asyncio.gather(*(pedir(p) for p in prompts))
    filas = []
    for prompt, candidatas in zip(prompts, grupos):
        lesiones, descartadas = rust_lesions(img, mascara, candidatas)
        s = measure(mascara, lesiones)
        confs = [i.confidence for i in lesiones if i.confidence is not None]
        nombre = f"{ruta.stem}__{prompt.replace(' ', '_')}.jpg"
        render_overlay(img, mascara, lesiones).save(salida / nombre, quality=85)
        filas.append(
            {
                "foto": f"{ruta.parent.name}/{ruta.name}",
                "prompt": prompt,
                "prompt_hoja": prompt_hoja,
                "hojas": len(hojas),
                "pct_hoja_en_foto": round(100 * s.leaf_pixels / (img.width * img.height), 1),
                "lesiones": s.lesion_count,
                "descartadas": descartadas,
                "pct": round(s.percent, 2),
                "nivel": s.level,
                "conf_min": round(min(confs), 2) if confs else None,
                "conf_media": round(sum(confs) / len(confs), 2) if confs else None,
                "overlay": nombre,
            }
        )
    return filas


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("carpetas", nargs="+", help="Subcarpetas de fotos/")
    p.add_argument("--prompts", nargs="+", default=config.DEFAULT_LESION_PROMPTS)
    p.add_argument("--min-conf", type=float, default=config.MIN_CONFIDENCE)
    p.add_argument("--etiqueta", default="prueba")
    args = p.parse_args()

    salida = RAIZ / "data" / "calibracion" / args.etiqueta
    salida.mkdir(parents=True, exist_ok=True)
    rutas = [
        f
        for c in args.carpetas
        for f in sorted((RAIZ / "fotos" / c).iterdir())
        if f.suffix.lower() in EXTENSIONES
    ]

    client = make_client()
    cupo = asyncio.Semaphore(4)
    resultados = await asyncio.gather(
        *(medir(client, cupo, r, args.prompts, args.min_conf, salida) for r in rutas),
        return_exceptions=True,
    )

    filas = []
    for ruta, r in zip(rutas, resultados):
        if isinstance(r, Exception):
            print(f"ERROR {ruta.name}: {type(r).__name__}: {str(r)[:200]}")
        else:
            filas.extend(r)
    (salida / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1))

    print(f"{'foto':38} {'prompt':24} {'hojas':>5} {'%foto':>6} {'les':>4} {'%':>7} {'conf':>5}  nivel")
    for f in filas:
        print(
            f"{f['foto']:38} {f['prompt'][:24]:24} {f['hojas']:>5} {f['pct_hoja_en_foto']:>6} "
            f"{f['lesiones']:>4} {f['pct']:>7} {str(f['conf_media']):>5}  {f['nivel']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
