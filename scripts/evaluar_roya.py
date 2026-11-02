"""Corre el flujo completo de roya sobre `fotos/` y compara con lo esperado. Gasta créditos.

Uso: PYTHONPATH=royalens .venv/bin/python scripts/evaluar_roya.py [carpetas...]
Deja overlays y `resultados.json` en data/calibracion/evaluacion/.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from pathlib import Path

from PIL import Image

from royalens.pipeline import analyze

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "data" / "calibracion" / "evaluacion"
EXTENSIONES = {".jpg", ".jpeg", ".png"}
CUPO = 3


def cumple(carpeta: str, d) -> bool:
    """Criterio de la fase 1. `roya` también admite una foto que pide repetir la toma."""
    if carpeta == "roya":
        return not d.measurable or d.severity.lesion_count > 0
    if carpeta in ("sana", "otra_enfermedad"):
        return not d.measurable or d.severity.lesion_count == 0
    return not d.measurable  # no_hoja y mala


async def evaluar(cupo, ruta):
    async with cupo:
        inicio = time.time()
        d = await analyze(Image.open(ruta))
        segundos = round(time.time() - inicio, 1)
    d.overlay.save(SALIDA / f"{ruta.stem}.jpg", quality=85)
    return {"foto": f"{ruta.parent.name}/{ruta.name}", "segundos": segundos, "cumple": cumple(ruta.parent.name, d), **d.as_dict()}


async def main() -> int:
    carpetas = sys.argv[1:] or ["roya", "sana", "otra_enfermedad", "mala", "no_hoja"]
    SALIDA.mkdir(parents=True, exist_ok=True)
    rutas = [f for c in carpetas for f in sorted((RAIZ / "fotos" / c).iterdir()) if f.suffix.lower() in EXTENSIONES]
    cupo = asyncio.Semaphore(CUPO)
    resultados = await asyncio.gather(*(evaluar(cupo, r) for r in rutas), return_exceptions=True)

    filas, fallos = [], 0
    for ruta, r in zip(rutas, resultados):
        if isinstance(r, Exception):
            print(f"ERROR {ruta.name}: {type(r).__name__}: {str(r)[:200]}")
            fallos += 1
        else:
            filas.append(r)
    (SALIDA / "resultados.json").write_text(json.dumps(filas, ensure_ascii=False, indent=1))

    for f in filas:
        m, muse = f["medicion_sam"], f["interpretacion_muse"]
        marca = "ok " if f["cumple"] else "MAL"
        fallos += not f["cumple"]
        pct = f"{m['porcentaje_afectado']:6.2f}%" if f["medible"] else "  ---  "
        print(
            f"{marca} {f['foto']:38} {pct} les={m['numero_lesiones']:3} dae={str(f['clase_dae']):4} "
            f"cafe={str(muse.get('es_hoja_de_cafe')):5} roya={str(muse.get('signos_de_roya')):5} "
            f"cal={str(muse.get('calidad_foto')):7} {f['segundos']}s"
        )
    print(f"\n{len(filas) - sum(not f['cumple'] for f in filas)} de {len(rutas)} cumplen")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
