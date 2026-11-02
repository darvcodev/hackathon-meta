"""Historial de escaneos en SQLite. No se mezclan los datos de cada modo ni de cada visitante."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
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
ALERTA_ALTA = 12.0  # desde el nivel Alta se avisa aunque no haya con qué comparar
DIAS_MUESTRA = 30
UMBRAL_CON_ROYA = 0.05  # primer límite de la escala: por debajo no hay roya visible
DIAS_RETENCION = 30
EJEMPLO = "__ejemplo__"  # finca de ejemplo, para quien todavía no tiene escaneos
CACHE_EJEMPLOS = "__cache__"  # resultados de las fotos de ejemplo; nadie los ve directamente

# Por día: (por IP, en total). Protegen los créditos cuando el enlace es público.
LIMITES = {
    "analisis": (int(os.getenv("ROYALENS_LIMITE_ANALISIS_IP", 40)), int(os.getenv("ROYALENS_LIMITE_ANALISIS", 800))),
    "chat": (int(os.getenv("ROYALENS_LIMITE_CHAT_IP", 60)), int(os.getenv("ROYALENS_LIMITE_CHAT", 1500))),
}


class LimiteAlcanzado(RuntimeError):
    pass


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
    columnas = {c["name"] for c in con.execute("PRAGMA table_info(escaneos)")}
    if "visitante" not in columnas:
        con.execute("ALTER TABLE escaneos ADD COLUMN visitante TEXT NOT NULL DEFAULT ''")
    con.execute(
        """CREATE TABLE IF NOT EXISTS uso (
            dia TEXT NOT NULL,
            tipo TEXT NOT NULL,
            clave TEXT NOT NULL,
            cuenta INTEGER NOT NULL,
            PRIMARY KEY (dia, tipo, clave)
        )"""
    )
    con.execute(
        """CREATE TABLE IF NOT EXISTS ejemplos_cache (
            slug TEXT NOT NULL,
            modo TEXT NOT NULL,
            version TEXT NOT NULL,
            escaneo_id TEXT NOT NULL,
            PRIMARY KEY (slug, modo, version)
        )"""
    )
    return con


def nuevo_id() -> str:
    return uuid4().hex[:12]


def guardar(escaneo: dict, visitante: str) -> dict:
    with _db() as con:
        con.execute(
            "INSERT INTO escaneos (id, tipo, lote, creado, modo, payload, visitante) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                escaneo["id"],
                escaneo["tipo"],
                escaneo["lote"],
                escaneo["creado"],
                escaneo["modo"],
                json.dumps(escaneo, ensure_ascii=False),
                visitante,
            ),
        )
    return escaneo


def obtener(escaneo_id: str, modo: str, visitante: str) -> dict | None:
    with _db() as con:
        row = con.execute(
            "SELECT payload FROM escaneos WHERE id = ? AND modo = ? AND visitante = ?",
            (escaneo_id, modo, visitante),
        ).fetchone()
    return json.loads(row["payload"]) if row else None


def listar(modo: str, visitante: str) -> list[dict]:
    """Escaneos del modo y del visitante, del más antiguo al más reciente."""
    with _db() as con:
        rows = con.execute(
            "SELECT payload FROM escaneos WHERE modo = ? AND visitante = ? ORDER BY creado",
            (modo, visitante),
        ).fetchall()
    return [json.loads(r["payload"]) for r in rows]


def _borrar_medios(escaneo: dict) -> None:
    for campo in ("imagen_url", "overlay_url"):
        url = escaneo.get(campo)
        if url and url.startswith("/media/"):
            (MEDIA_DIR / Path(url).name).unlink(missing_ok=True)


def borrar_visitante(modo: str, visitante: str) -> int:
    """Borra los escaneos y las fotos de un visitante."""
    escaneos = listar(modo, visitante)
    for e in escaneos:
        _borrar_medios(e)
    with _db() as con:
        con.execute("DELETE FROM escaneos WHERE modo = ? AND visitante = ?", (modo, visitante))
    return len(escaneos)


def purgar_antiguos() -> int:
    """Borra lo que pasó el plazo de retención. Las fotos de ejemplo no son de nadie y se quedan."""
    limite = datetime.now(timezone.utc) - timedelta(days=DIAS_RETENCION)
    with _db() as con:
        filas = con.execute(
            "SELECT id, payload FROM escaneos WHERE creado < ? AND visitante NOT IN (?, ?)",
            (limite.isoformat(), EJEMPLO, CACHE_EJEMPLOS),
        ).fetchall()
        for f in filas:
            _borrar_medios(json.loads(f["payload"]))
            con.execute("DELETE FROM escaneos WHERE id = ?", (f["id"],))
        con.execute("DELETE FROM uso WHERE dia < ?", (limite.date().isoformat(),))
    return len(filas)


def consumir(tipo: str, ip: str) -> None:
    """Cuenta un uso, o falla si ya se llegó al límite de hoy."""
    por_ip, total = LIMITES[tipo]
    dia = datetime.now(timezone.utc).date().isoformat()
    clave = hashlib.sha256(ip.encode()).hexdigest()[:16]  # no se guarda la IP
    with _db() as con:
        con.execute("BEGIN IMMEDIATE")
        cuenta = lambda c: (
            con.execute("SELECT cuenta FROM uso WHERE dia = ? AND tipo = ? AND clave = ?", (dia, tipo, c)).fetchone()
            or {"cuenta": 0}
        )["cuenta"]
        if cuenta("*") >= total:
            raise LimiteAlcanzado("La app llegó a su límite de uso de hoy para cuidar los créditos. Vuelva mañana.")
        if cuenta(clave) >= por_ip:
            raise LimiteAlcanzado("Llegó a su límite de pruebas de hoy. Vuelva mañana o use las fotos de ejemplo.")
        for c in ("*", clave):
            con.execute(
                """INSERT INTO uso VALUES (?, ?, ?, 1)
                   ON CONFLICT (dia, tipo, clave) DO UPDATE SET cuenta = cuenta + 1""",
                (dia, tipo, c),
            )


def ejemplo_guardado(slug: str, modo: str, version: str) -> dict | None:
    with _db() as con:
        fila = con.execute(
            "SELECT escaneo_id FROM ejemplos_cache WHERE slug = ? AND modo = ? AND version = ?", (slug, modo, version)
        ).fetchone()
    return obtener(fila["escaneo_id"], modo, CACHE_EJEMPLOS) if fila else None


def guardar_ejemplo(slug: str, version: str, escaneo: dict) -> None:
    with _db() as con:
        con.execute("UPDATE escaneos SET payload = ? WHERE id = ?", (json.dumps(escaneo, ensure_ascii=False), escaneo["id"]))
        con.execute(
            "INSERT OR REPLACE INTO ejemplos_cache VALUES (?, ?, ?, ?)", (slug, escaneo["modo"], version, escaneo["id"])
        )


def copiar_escaneo(original: dict, lote: int, visitante: str) -> dict:
    """Copia un resultado guardado para otro visitante, con sus propias fotos."""
    copia = {**original, "id": nuevo_id(), "lote": lote, "creado": datetime.now(timezone.utc).isoformat()}
    for campo, sufijo in (("imagen_url", ""), ("overlay_url", "_overlay")):
        if original.get(campo):
            nombre = f"{copia['id']}{sufijo}.jpg"
            shutil.copy(MEDIA_DIR / Path(original[campo]).name, MEDIA_DIR / nombre)
            copia[campo] = f"/media/{nombre}"
    return guardar(copia, visitante)


def sembrar_ejemplo(modo: str) -> None:
    """Prepara la finca de ejemplo, con fechas frescas. Sus cifras son ilustrativas y se rotulan así."""
    with _db() as con:
        con.execute("DELETE FROM escaneos WHERE modo = ? AND visitante = ?", (modo, EJEMPLO))
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
                    "modo": modo,
                    "ejemplo": True,
                    "medicion": {"porcentaje": pct, "nivel": nivel, "lesiones": None},
                },
                EJEMPLO,
            )
    for lote, pct in maduracion.items():
        guardar(
            {
                "id": nuevo_id(),
                "tipo": "maduracion",
                "lote": lote,
                "creado": (ahora - timedelta(days=lote)).isoformat(),
                "modo": modo,
                "ejemplo": True,
                "medicion": {"porcentaje_maduro": pct, "total": None},
            },
            EJEMPLO,
        )


def _fecha(escaneo: dict) -> datetime:
    return datetime.fromisoformat(escaneo["creado"])


def resumen(modo: str, visitante: str) -> dict:
    """Todo lo que muestra Mi finca. Sin escaneos propios, muestra la finca de ejemplo."""
    escaneos = listar(modo, visitante)
    es_ejemplo = not escaneos
    if es_ejemplo:
        escaneos = listar(modo, EJEMPLO)
    ahora = datetime.now(timezone.utc)
    lotes = []
    alertas = []

    for lote in LOTES:
        # Una foto que no se pudo medir no dice nada del lote.
        propios = [e for e in escaneos if e["lote"] == lote and e["medicion"].get("valida", True)]
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

        # Incidencia y severidad con las fórmulas de Cenicafé, sobre las hojas escaneadas.
        muestra = [e["medicion"]["porcentaje"] for e in roya if (ahora - _fecha(e)).days < DIAS_MUESTRA]
        con_roya = sum(1 for p in muestra if p >= UMBRAL_CON_ROYA)

        nombre = f"Lote {lote}"
        lotes.append(
            {
                "id": lote,
                "nombre": nombre,
                "roya": pct,
                "nivel": ultima_roya["medicion"]["nivel"] if ultima_roya else None,
                "cambio_roya": cambio,
                "muestra": {
                    "hojas": len(muestra),
                    "con_roya": con_roya,
                    "incidencia": round(100 * con_roya / len(muestra)) if muestra else None,
                    "severidad": round(sum(muestra) / len(muestra), 1) if muestra else None,
                },
                "maduro": ultima_madur["medicion"]["porcentaje_maduro"] if ultima_madur else None,
                "dias_sin_revisar": dias,
                "evolucion": [
                    {"fecha": e["creado"], "porcentaje": e["medicion"]["porcentaje"]} for e in roya
                ],
            }
        )

        subio = pct is not None and pct >= ALERTA_ROYA and cambio is not None and cambio >= ALERTA_SUBIDA
        if subio or (pct is not None and pct >= ALERTA_ALTA):
            detalle = (
                f"La roya pasó de {previo:g}% a {pct:g}% en las últimas semanas."
                if subio
                else f"La última hoja escaneada tiene {pct:g}% de roya."
            )
            alertas.append(
                {
                    "lote": lote,
                    "nivel": "alta",
                    "titulo": f"{nombre} necesita atención",
                    "texto": f"{detalle} Consulte a su extensionista del Comité de Cafeteros.",
                }
            )
        elif dias is None or dias >= DIAS_SIN_REVISAR:
            texto = "Todavía no tiene escaneos." if dias is None else f"Último escaneo hace {dias} días."
            alertas.append(
                {"lote": lote, "nivel": "revisar", "titulo": f"Revise el {nombre}", "texto": texto}
            )

    con_roya = [l for l in lotes if l["roya"] is not None]
    con_cambio = [l for l in con_roya if l["cambio_roya"] is not None]
    con_madur = [l for l in lotes if l["maduro"] is not None]
    este_mes = [e for e in escaneos if (ahora - _fecha(e)).days < 30]

    return {
        "modo": modo,
        "es_ejemplo": es_ejemplo and bool(escaneos),
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
