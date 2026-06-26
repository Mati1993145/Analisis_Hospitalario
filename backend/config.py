"""Configuración central del backend.

Centraliza los nombres de esquema, tabla, vistas y rutas para que el proyecto
sea reutilizable con otra base de datos sin tener que buscar literales repartidos
por el código. Para adaptar el pipeline a otra fuente de datos, en la mayoría de
los casos basta con editar las constantes de este archivo (y el DDL en
`sql/ddl/` y el script de carga `python/scripts/01_load_data.py`, que también se
documentan en el README y en CONFIG.md).

Las credenciales de conexión NO viven aquí: se leen del archivo `.env`
(ver `.env.example`). Este módulo solo define la estructura lógica del esquema.
"""
from __future__ import annotations

from pathlib import Path

# Raíz del proyecto (este archivo vive en backend/).
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# --- Variables de entorno requeridas para la conexión (se leen del .env) ---
REQUIRED_ENV_VARS = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]

# --- Estructura lógica del esquema (editar para reutilizar con otros datos) ---
SCHEMA = "rem20"
TABLE_INDICADORES = "indicadores"
VIEW_EVOLUCION_MENSUAL = "v_evolucion_mensual"
VIEW_RANKING = "v_ranking_establecimientos"
VIEW_LETALIDAD_AREA = "v_letalidad_por_area"

# Nombres completos (esquema.objeto) listos para usar en las consultas SQL.
TABLA_INDICADORES = f"{SCHEMA}.{TABLE_INDICADORES}"
VISTA_EVOLUCION_MENSUAL = f"{SCHEMA}.{VIEW_EVOLUCION_MENSUAL}"
VISTA_RANKING = f"{SCHEMA}.{VIEW_RANKING}"
VISTA_LETALIDAD_AREA = f"{SCHEMA}.{VIEW_LETALIDAD_AREA}"

# --- Rutas de artefactos de datos ---
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PREDICCIONES_CSV = DATA_PROCESSED_DIR / "rem20_predicciones_2026.csv"
CLUSTERS_CSV = DATA_PROCESSED_DIR / "clusters.csv"

# --- Frontend servido por el backend ---
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Año por defecto para los endpoints que reciben un periodo opcional.
DEFAULT_PERIODO_RANKING = 2025
