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


_ROOT = Path(__file__).resolve().parent.parent
_load_dotenv(_ROOT / ".env")
_load_dotenv(_ROOT.parent / ".env")

# --- API de Meta -----------------------------------------------------------
BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1")
API_KEY_ENV = "MODEL_API_KEY"
API_TIMEOUT_SECONDS = 60.0

SAM_MODEL = os.getenv("ROYALENS_SAM_MODEL", "sam-3.1")
MUSE_MODEL = os.getenv("ROYALENS_MUSE_MODEL", "muse-spark-1.3")

# --- Segmentación ----------------------------------------------------------
# SAM funciona mejor con una frase nominal corta y concreta por petición.
LEAF_PROMPTS = ["coffee leaf", "leaf"]  # se usa el primero que encuentre algo
# Elegidos con fotos de prueba: el primero separa pústulas y el segundo agrega las zonas grandes.
DEFAULT_LESION_PROMPTS = ["orange rust spot", "orange patch"]

MIN_CONFIDENCE = float(os.getenv("ROYALENS_MIN_CONFIDENCE", "0.35"))

# Las fotos de celular se reducen antes de enviarlas: menos tokens y más rapidez.
MAX_IMAGE_SIDE = 1600

# --- Escala de severidad ---------------------------------------------------
# Intervalos y marcas del Diagrama de Área Estándar de Cenicafé
# (Avances Técnicos 498, 2018): límite superior del intervalo y marca de clase.
DAE_CLASSES = [(1.5, 1), (3.0, 2), (6.0, 4), (12.0, 8), (24.0, 16), (48.0, 32), (100.0, 64)]

# Los límites salen de esos intervalos. Los nombres de nivel son de RoyaLens, no de Cenicafé.
SEVERITY_LEVELS = [
    (0.05, "Sin roya visible", "#2e7d32"),
    (3.0, "Leve", "#9e9d24"),
    (12.0, "Moderada", "#ef6c00"),
    (24.0, "Alta", "#d84315"),
    (100.0, "Severa", "#b71c1c"),
]

# Cenicafé reporta posible caída prematura por encima de este % de la hoja.
DEFOLIATION_RISK_PERCENT = 30.0

# --- Filtros de medición ---------------------------------------------------
# Calibrados con fotos de prueba: las manchas de otras enfermedades dieron saturación
# de 0.19 o menos y las pústulas de roya de 0.36 o más.
RUST_HUE_RANGE = (10.0, 75.0)
RUST_MIN_SATURATION = 0.30

# Por debajo de este % de la foto, la hoja está demasiado lejos para medirla.
MIN_LEAF_PERCENT = 8.0
# En una foto de varias hojas, se revisan las que ocupan al menos este % de la imagen.
MIN_VISIBLE_LEAF_PERCENT = 1.5
# Tamaño de una lesión frente a la hoja: hasta aquí es pequeña o mediana; más arriba, grande.
SMALL_LESION_PERCENT = 0.5
LARGE_LESION_PERCENT = 2.0

# --- Maduración ------------------------------------------------------------
# "coffee cherry" no devolvió nada en fotos reales; "round fruit" encontró las cerezas.
CHERRY_PROMPT = "round fruit"
# Lo mucho más pequeño que la cereza típica está en el fondo, fuera de foco.
MIN_CHERRY_RATIO = 0.3
CHERRY_DUPLICATE_OVERLAP = 0.5
# La foto completa pierde cerezas en ramas cargadas; por cuadrantes pasó de 32 a 104.
TILE_OVERLAP = 0.15
# Por debajo de este % de la foto por cereza, se tomó la planta entera y no un racimo.
MIN_CHERRY_PERCENT = 0.05

RIPENESS_STATES = ["verde", "pinton", "maduro", "sobremaduro"]
# Tono en grados: el rojo da la vuelta al círculo de color.
RED_HUE = (325.0, 22.0)
GREEN_HUE = (50.0, 170.0)
# Brillo por debajo del cual un rojo es vino oscuro, propio de la cereza sobremadura.
OVERRIPE_MAX_VALUE = 0.42
# Fracción de la cereza que debe tener un color para asignarle ese estado.
RIPENESS_SHARE = 0.6
# Con menos cerezas, el porcentaje no representa al racimo.
MIN_CHERRIES_FOR_PERCENT = 5
