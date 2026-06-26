from __future__ import annotations

import math
import numbers
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import text

from backend.database import get_connection


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _json_value(value: Any) -> Any:
    """Convierte valores de BD/DataFrame a tipos serializables por JSON."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, numbers.Integral) and not isinstance(value, bool):
        return int(value)
    if isinstance(value, numbers.Real) and not isinstance(value, bool):
        return float(value)
    return value


def _rows_to_dicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: _json_value(value) for key, value in row.items()} for row in rows]


def _execute(query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with get_connection() as connection:
        result = connection.execute(text(query), params or {})
        rows = [dict(row) for row in result.mappings().all()]
    return _rows_to_dicts(rows)


def resumen_nacional() -> list[dict[str, Any]]:
    """KPIs nacionales calculados desde el ultimo periodo disponible."""
    return _execute(
        """
        SELECT
            periodo,
            AVG(indice_ocupacional) AS indice_ocupacional_prom,
            SUM(numero_egresos) AS total_egresos,
            100.0 * SUM(egresos_fallecidos) / NULLIF(SUM(numero_egresos), 0)
                AS letalidad_nacional,
            AVG(promedio_dias_estada) AS promedio_dias_estada_prom
        FROM rem20.indicadores
        WHERE periodo = (SELECT MAX(periodo) FROM rem20.indicadores)
        GROUP BY periodo
        """
    )


def evolucion_mensual(periodo: int | None = None) -> list[dict[str, Any]]:
    if periodo is None:
        return _execute(
            """
            SELECT
                periodo,
                mes,
                indice_ocupacional_prom,
                promedio_dias_estada_prom,
                letalidad_prom,
                numero_egresos,
                egresos_fallecidos
            FROM rem20.v_evolucion_mensual
            ORDER BY periodo, mes
            """
        )

    return _execute(
        """
        SELECT
            periodo,
            mes,
            indice_ocupacional_prom,
            promedio_dias_estada_prom,
            letalidad_prom,
            numero_egresos,
            egresos_fallecidos
        FROM rem20.v_evolucion_mensual
        WHERE periodo = :periodo
        ORDER BY periodo, mes
        """,
        {"periodo": periodo},
    )


def efecto_covid() -> list[dict[str, Any]]:
    return _execute(
        """
        SELECT
            periodo,
            mes,
            indice_ocupacional_prom,
            letalidad_prom
        FROM rem20.v_evolucion_mensual
        WHERE periodo BETWEEN 2018 AND 2022
        ORDER BY periodo, mes
        """
    )


def ranking_establecimientos(periodo: int) -> list[dict[str, Any]]:
    return _execute(
        """
        SELECT
            periodo,
            ranking,
            codigo_establecimiento,
            establecimiento,
            idx_ocup_prom,
            numero_egresos
        FROM rem20.v_ranking_establecimientos
        WHERE periodo = :periodo
        ORDER BY ranking
        """,
        {"periodo": periodo},
    )


def letalidad_por_area(periodo: int | None = None) -> list[dict[str, Any]]:
    if periodo is None:
        return _execute(
            """
            SELECT
                area_funcional,
                periodo,
                egresos_fallecidos,
                numero_egresos,
                letalidad_pct
            FROM rem20.v_letalidad_por_area
            ORDER BY periodo, letalidad_pct DESC
            """
        )

    return _execute(
        """
        SELECT
            area_funcional,
            periodo,
            egresos_fallecidos,
            numero_egresos,
            letalidad_pct
        FROM rem20.v_letalidad_por_area
        WHERE periodo = :periodo
        ORDER BY periodo, letalidad_pct DESC
        """,
        {"periodo": periodo},
    )


def clusters() -> list[dict[str, Any]]:
    csv_path = PROJECT_ROOT / "data" / "processed" / "clusters.csv"

    if csv_path.exists():
        df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
        df = df.where(pd.notnull(df), None)
        return _rows_to_dicts(df.to_dict("records"))

    return [
        {
            "cluster": 0,
            "etiqueta": "Saturación crítica",
            "descripcion": "Establecimientos con índice ocupacional muy alto y presión sostenida sobre camas.",
        },
        {
            "cluster": 1,
            "etiqueta": "Alta ocupación",
            "descripcion": "Establecimientos con uso elevado de camas, cercanos a niveles de saturación.",
        },
        {
            "cluster": 2,
            "etiqueta": "Ocupación media",
            "descripcion": "Establecimientos con utilización intermedia y margen operativo moderado.",
        },
        {
            "cluster": 3,
            "etiqueta": "Baja ocupación / subutilización",
            "descripcion": "Establecimientos con índice ocupacional bajo y posible capacidad disponible.",
        },
    ]


def predicciones_2026() -> list[dict[str, Any]]:
    csv_path = PROJECT_ROOT / "data" / "processed" / "rem20_predicciones_2026.csv"

    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el archivo de predicciones: {csv_path}")

    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    df = df.where(pd.notnull(df), None)
    return _rows_to_dicts(df.to_dict("records"))
