from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


TEXT_COLUMNS = ["GLOSA_SSS", "ESTABLECIMIENTO", "AREA_FUNCIONAL"]

INTEGER_COLUMNS = [
    "PERIODO",
    "TIPO_PERTENENCIA",
    "COD_SSS",
    "CODIGO_ESTABLECIMIENTO",
    "COD_AREA_FUNCIONAL",
    "MES",
    "DIAS_CAMAS_OCUPADAS",
    "DIAS_CAMAS_DISPONIBLES",
    "DIAS_ESTADA",
    "NUMERO_EGRESOS",
    "EGRESOS_FALLECIDOS",
    "TRASLADOS",
]

FLOAT_COLUMNS = [
    "INDICE_OCUPACIONAL",
    "PROMEDIO_CAMAS_DISPONIBLE",
    "PROMEDIO_DIAS_ESTADA",
    "LETALIDAD",
    "INDICE_ROTACION",
]

EXPECTED_COLUMNS = [
    "PERIODO",
    "TIPO_PERTENENCIA",
    "COD_SSS",
    "GLOSA_SSS",
    "CODIGO_ESTABLECIMIENTO",
    "ESTABLECIMIENTO",
    "COD_AREA_FUNCIONAL",
    "AREA_FUNCIONAL",
    "MES",
    "DIAS_CAMAS_OCUPADAS",
    "DIAS_CAMAS_DISPONIBLES",
    "DIAS_ESTADA",
    "NUMERO_EGRESOS",
    "EGRESOS_FALLECIDOS",
    "TRASLADOS",
    "INDICE_OCUPACIONAL",
    "PROMEDIO_CAMAS_DISPONIBLE",
    "PROMEDIO_DIAS_ESTADA",
    "LETALIDAD",
    "INDICE_ROTACION",
]

PRIMARY_KEY = ["periodo", "mes", "codigo_establecimiento", "cod_area_funcional"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(root: Path) -> dict[str, str]:
    load_dotenv(root / ".env")

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    config = {key: os.getenv(key) for key in required}
    missing = [key for key, value in config.items() if not value]

    if missing:
        raise ValueError(
            "Faltan variables obligatorias en .env: " + ", ".join(missing)
        )

    return {key: value for key, value in config.items() if value is not None}


def database_url(config: dict[str, str]) -> str:
    user = quote_plus(config["DB_USER"])
    password = quote_plus(config["DB_PASSWORD"])
    host = config["DB_HOST"]
    port = config["DB_PORT"]
    name = config["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def create_db_engine(config: dict[str, str]) -> Engine:
    return create_engine(database_url(config), pool_pre_ping=True)


def read_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el archivo CSV: {csv_path}")

    df = pd.read_csv(csv_path, sep=";", encoding="utf-8", dtype=str)

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            "El header del CSV no coincide con el esperado. "
            f"Columnas recibidas: {list(df.columns)}"
        )

    return df


def strip_columns(df: pd.DataFrame, columns: Iterable[str]) -> None:
    for column in columns:
        df[column] = df[column].str.strip()


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    strip_columns(df, TEXT_COLUMNS + INTEGER_COLUMNS + FLOAT_COLUMNS)

    for column in INTEGER_COLUMNS:
        numeric = pd.to_numeric(df[column], errors="raise")
        if numeric.isna().any():
            raise ValueError(f"La columna {column} contiene valores enteros nulos.")
        df[column] = numeric.astype("int64")

    for column in FLOAT_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="raise").astype("float64")

    df.columns = [column.lower() for column in df.columns]

    duplicates = int(df.duplicated(subset=PRIMARY_KEY, keep="first").sum())
    print(f"Duplicados detectados en la primary key: {duplicates}")

    if duplicates:
        # La PK representa la granularidad esperada; se conserva el primer registro
        # para evitar que la carga falle por violacion de clave primaria.
        df = df.drop_duplicates(subset=PRIMARY_KEY, keep="first")
        print(f"Filas luego de eliminar duplicados por primary key: {len(df)}")

    return df


# chunksize interno de to_sql con method="multi": cada INSERT agrupa
# chunksize * n_columnas parametros. La tabla tiene 20 columnas y psycopg2/
# PostgreSQL limitan a 65.535 parametros por sentencia (20 * 3.276 ~= 65.535).
# Usamos 1.000 (20.000 parametros) con amplio margen de seguridad y buen
# rendimiento. El batch externo de 25.000 solo controla el reporte de progreso.
INSERT_CHUNKSIZE = 1_000


def load_in_batches(df: pd.DataFrame, engine: Engine, batch_size: int = 25_000) -> int:
    loaded_rows = 0

    for start in range(0, len(df), batch_size):
        batch = df.iloc[start : start + batch_size]
        batch.to_sql(
            "indicadores",
            engine,
            schema="rem20",
            if_exists="append",
            index=False,
            chunksize=INSERT_CHUNKSIZE,
            method="multi",
        )
        loaded_rows += len(batch)
        print(f"Progreso de carga: {loaded_rows}/{len(df)} filas")

    return loaded_rows


def verify_count(engine: Engine) -> int:
    with engine.connect() as connection:
        return int(connection.execute(text("SELECT COUNT(*) FROM rem20.indicadores")).scalar_one())


def main() -> int:
    root = project_root()
    csv_path = root / "data" / "raw" / "indicadores_rem20_20260625.csv"
    engine: Engine | None = None
    start_time = time.perf_counter()

    try:
        config = load_config(root)
        engine = create_db_engine(config)

        print(f"Leyendo CSV: {csv_path}")
        df = read_csv(csv_path)
        print(f"Filas leidas desde CSV: {len(df)}")

        df = normalize_dataframe(df)
        loaded_rows = load_in_batches(df, engine)

        elapsed = time.perf_counter() - start_time
        table_count = verify_count(engine)

        print(f"Filas cargadas: {loaded_rows}")
        print(f"Tiempo total: {elapsed:.2f} segundos")
        print(f"Verificacion SELECT COUNT(*): {table_count}")
        return 0
    except Exception as exc:
        print(f"Error durante la carga de datos: {exc}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
