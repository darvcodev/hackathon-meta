"""Historial de escaneos en SQLite. Los datos de cada modo nunca se mezclan."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from royalens.analysis import classify

DATA_DIR = Path(os.getenv("ROYALENS_DATA", Path(__file__).resolve().parent.parent / "data"))
MEDIA_DIR = DATA_DIR / "media"
LOTES = [1, 2, 3, 4]
DIAS_SIN_REVISAR = 7
ALERTA_ROYA = 5.0
ALERTA_SUBIDA = 2.0


def _db() -> sqlite3.Connection:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATA_DIR / "royalens.db")
    con.row_factory = sqlite3.Row
    con.execute(
        """CREATE TABLE IF NOT EXISTS escaneos (
            id TEXT PRIMARY KEY,
            tipo TEXT NOT NULL,
            lote INTEGER NOT NULL,
            creado TEXT NOT NULL,
            modo TEXT NOT NULL,
            payload TEXT NOT NULL
        )"""
    )
    return con


def nuevo_id() -> str:
    return uuid4().hex[:12]


def guardar(escaneo: dict) -> dict:
    with _db() as con:
        con.execute(
            "INSERT INTO escaneos VALUES (?, ?, ?, ?, ?, ?)",
            (
                escaneo["id"],
                escaneo["tipo"],
                escaneo["lote"],
                escaneo["creado"],
                escaneo["modo"],
                json.dumps(escaneo, ensure_ascii=False),
            ),
        )
    return escaneo


def obtener(escaneo_id: str, modo: str) -> dict | None:
    with _db() as con:
        row = con.execute(
            "SELECT payload FROM escaneos WHERE id = ? AND modo = ?", (escaneo_id, modo)
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def listar(modo: str) -> list[dict]:
    """Escaneos del modo, del más antiguo al más reciente."""
    with _db() as con:
        rows = con.execute(
            "SELECT payload FROM escaneos WHERE modo = ? ORDER BY creado", (modo,)
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def sembrar_ejemplo() -> None:
    """Llena el panel en modo demo con un historial de ejemplo, si está vacío."""
    if listar("demo"):
        return
    ahora = datetime.now(timezone.utc)
    roya = {
        1: [(30, 0.2), (16, 0.3), (2, 0.4)],
        2: [(28, 2.1), (14, 2.8), (3, 3.4)],
        3: [(42, 3.0), (35, 3.9), (28, 5.2), (21, 6.6), (14, 8.0), (1, 14.6)],
        4: [(25, 0.5), (12, 0.8)],
    }
    maduracion = {1: 34, 2: 71, 3: 48, 4: 22}

    for lote, serie in roya.items():
        for dias, pct in serie:
            nivel, _ = classify(pct)
            guardar(
                {
                    "id": nuevo_id(),
                    "tipo": "roya",
                    "lote": lote,
                    "creado": (ahora - timedelta(days=dias)).isoformat(),
                    "modo": "demo",
                    "ejemplo": True,
                    "medicion": {"porcentaje": pct, "nivel": nivel, "lesiones": None},
                }
            )
    for lote, pct in maduracion.items():
        guardar(
            {
                "id": nuevo_id(),
                "tipo": "maduracion",
                "lote": lote,
                "creado": (ahora - timedelta(days=lote)).isoformat(),
                "modo": "demo",
                "ejemplo": True,
                "medicion": {"porcentaje_maduro": pct, "total": None},
            }
        )


def _fecha(escaneo: dict) -> datetime:
    return datetime.fromisoformat(escaneo["creado"])


def resumen(modo: str) -> dict:
    """Todo lo que muestra Mi finca, calculado desde los escaneos guardados."""
    escaneos = listar(modo)
    ahora = datetime.now(timezone.utc)
    lotes = []
    alertas = []

    for lote in LOTES:
        propios = [e for e in escaneos if e["lote"] == lote]
        roya = [e for e in propios if e["tipo"] == "roya"]
        madur = [e for e in propios if e["tipo"] == "maduracion"]
        ultima_roya = roya[-1] if roya else None
        ultima_madur = madur[-1] if madur else None
        ultimo = propios[-1] if propios else None
        dias = (ahora - _fecha(ultimo)).days if ultimo else None

        # Referencia: el escaneo más reciente de hace al menos dos semanas.
        previos = [e for e in roya if (ahora - _fecha(e)).days >= 14]
        pct = ultima_roya["medicion"]["porcentaje"] if ultima_roya else None
        previo = previos[-1]["medicion"]["porcentaje"] if previos else None
        cambio = round(pct - previo, 1) if pct is not None and previo is not None else None

        nombre = f"Lote {lote}"
        lotes.append(
            {
                "id": lote,
                "nombre": nombre,
                "roya": pct,
                "nivel": ultima_roya["medicion"]["nivel"] if ultima_roya else None,
                "cambio_roya": cambio,
                "maduro": ultima_madur["medicion"]["porcentaje_maduro"] if ultima_madur else None,
                "dias_sin_revisar": dias,
                "evolucion": [
                    {"fecha": e["creado"], "porcentaje": e["medicion"]["porcentaje"]} for e in roya
                ],
            }
        )

        if pct is not None and pct >= ALERTA_ROYA and cambio is not None and cambio >= ALERTA_SUBIDA:
            alertas.append(
                {
                    "lote": lote,
                    "nivel": "alta",
                    "titulo": f"{nombre} necesita atención",
                    "texto": (
                        f"La roya pasó de {previo:g}% a {pct:g}% en las últimas semanas. "
                        "Consulta a tu extensionista del Comité de Cafeteros."
                    ),
                }
            )
        elif dias is None or dias >= DIAS_SIN_REVISAR:
            texto = "Todavía no tiene escaneos." if dias is None else f"Último escaneo hace {dias} días."
            alertas.append(
                {"lote": lote, "nivel": "revisar", "titulo": f"Revisa {nombre}", "texto": texto}
            )

    con_roya = [l for l in lotes if l["roya"] is not None]
    con_cambio = [l for l in con_roya if l["cambio_roya"] is not None]
    con_madur = [l for l in lotes if l["maduro"] is not None]
    este_mes = [e for e in escaneos if (ahora - _fecha(e)).days < 30]

    return {
        "modo": modo,
        "indicadores": {
            "roya_promedio": round(sum(l["roya"] for l in con_roya) / len(con_roya), 1) if con_roya else None,
            "cambio_roya": round(sum(l["cambio_roya"] for l in con_cambio) / len(con_cambio), 1) if con_cambio else None,
            "maduro_promedio": round(sum(l["maduro"] for l in con_madur) / len(con_madur)) if con_madur else None,
            "lote_mas_maduro": max(con_madur, key=lambda l: l["maduro"])["nombre"] if con_madur else None,
            "escaneos_mes": len(este_mes),
            "lotes_por_revisar": sum(
                1 for l in lotes if l["dias_sin_revisar"] is None or l["dias_sin_revisar"] >= DIAS_SIN_REVISAR
            ),
        },
        "lotes": lotes,
        "alertas": sorted(alertas, key=lambda a: a["nivel"] != "alta"),
        "recientes": [
            {
                "id": e["id"],
                "tipo": e["tipo"],
                "lote": e["lote"],
                "creado": e["creado"],
                "medicion": e["medicion"],
                "ejemplo": e.get("ejemplo", False),
            }
            for e in reversed(escaneos[-5:])
        ],
    }
