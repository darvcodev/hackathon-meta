"""Configuración central de RoyaLens.

Todo lo que probablemente quieras ajustar con fotos reales está aquí.
"""

import os
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """Carga un archivo .env sencillo (CLAVE=valor) sin dependencias extra."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# --- API de Meta -----------------------------------------------------------
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
API_KEY_ENV = "MODEL_API_KEY"

SAM_MODEL = os.getenv("ROYALENS_SAM_MODEL", "sam-3.1")
MUSE_MODEL = os.getenv("ROYALENS_MUSE_MODEL", "muse-spark-1.3")

# --- Segmentación ----------------------------------------------------------
# SAM funciona mejor con una frase nominal corta y concreta por petición.
LEAF_PROMPTS = ["coffee leaf", "leaf"]  # se usa el primero que encuentre algo
DEFAULT_LESION_PROMPTS = ["orange rust spot"]  # ajustable desde la interfaz

MIN_CONFIDENCE = float(os.getenv("ROYALENS_MIN_CONFIDENCE", "0.35"))

# Las fotos de celular se reducen antes de enviarlas: menos tokens y más rapidez.
MAX_IMAGE_SIDE = 1600

# --- Escala de severidad ---------------------------------------------------
# Escala ORIENTATIVA para la demo: % del área de la hoja cubierta por lesiones.
# Debe validarse con un agrónomo o con las escalas diagramáticas de Cenicafé.
SEVERITY_LEVELS = [
    (1.0, "Sin roya visible o trazas", "#2e7d32"),
    (5.0, "Leve", "#9e9d24"),
    (15.0, "Moderada", "#ef6c00"),
    (30.0, "Alta", "#d84315"),
    (100.0, "Severa", "#b71c1c"),
]
