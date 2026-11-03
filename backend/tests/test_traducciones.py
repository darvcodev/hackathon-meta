"""Los textos fijos que el servidor muestra en la interfaz deben tener traducción al inglés."""

import json
import re
from pathlib import Path

from backend import ejemplos, service
from royalens import config

RAIZ = Path(__file__).resolve().parents[2]
EN = json.loads((RAIZ / "frontend" / "src" / "en.json").read_text(encoding="utf-8"))


def _citas(ruta: str, patron: str) -> set[str]:
    codigo = (RAIZ / ruta).read_text(encoding="utf-8")
    return set(re.findall(patron, codigo))


def textos_del_servidor() -> set[str]:
    textos = set()
    textos |= _citas("royalens/royalens/pipeline.py", r'warnings\.append\(\s*"([^"]+)"')
    textos |= _citas("backend/demo.py", r'avisos\.append\(\s*"([^"]+)"')
    textos |= _citas("backend/main.py", r'HTTPException\(\d+, "([^"]+)"')
    textos |= _citas("backend/main.py", r'"mensaje": "([^"]+)"')
    textos |= _citas("backend/store.py", r'LimiteAlcanzado\(\s*"([^"]+)"')
    textos |= _citas("backend/chat.py", r'"texto": "([^"]+)"')
    textos |= _citas("backend/chat.py", r'"titulo": "([^"]+)"')
    textos |= _citas("backend/chat.py", r'ChatNoDisponible\(\s*"([^"]+)"')
    for e in ejemplos.EJEMPLOS:
        textos |= {e["titulo"], e["credito"]}
    for total, maduro, sobre in [(0, 0, 0), (10, 0, 30), (10, 60, 0), (10, 10, 0)]:
        r = service.recomendar_cosecha(maduro, sobre, total)
        textos |= {r["titulo"], r["texto"]}
    textos |= {nombre for _, nombre, _ in config.SEVERITY_LEVELS}
    return textos


def test_textos_del_servidor_tienen_traduccion():
    faltan = sorted(t for t in textos_del_servidor() if t not in EN)
    assert not faltan, "Faltan en frontend/src/en.json:\n" + "\n".join(faltan)


def test_la_lista_de_textos_no_esta_vacia():
    # Si cambia la forma del código, el patrón dejaría de encontrar textos sin avisar.
    assert len(textos_del_servidor()) > 40
