"""Prueba rápida por terminal, sin interfaz.

Uso:  python analyze.py foto_hoja.jpg
Guarda la imagen anotada como <foto>_royalens.png e imprime el resultado en JSON.
"""

import asyncio
import json
import sys
from pathlib import Path

from PIL import Image

from royalens.pipeline import analyze


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("Uso: python analyze.py foto_hoja.jpg")
    path = Path(sys.argv[1])
    result = asyncio.run(analyze(Image.open(path)))
    out = path.with_name(path.stem + "_royalens.png")
    result.overlay.save(out)
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    print(f"\nImagen anotada: {out}")


if __name__ == "__main__":
    main()
