from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


PK_CSV = ["PERIODO", "MES", "CODIGO_ESTABLECIMIENTO", "COD_AREA_FUNCIONAL"]
PK_DB = ["periodo", "mes", "codigo_establecimiento", "cod_area_funcional"]

INTEGER_FIELDS = [
    "dias_camas_ocupadas",
    "dias_camas_disponibles",
    "dias_estada",
    "numero_egresos",
    "egresos_fallecidos",
    "traslados",
]

FLOAT_FIELDS = [
    "indice_ocupacional",
    "promedio_camas_disponible",
    "promedio_dias_estada",
    "letalidad",
    "indice_rotacion",
]

NUMERIC_FIELDS = INTEGER_FIELDS + FLOAT_FIELDS

DECISIONES = [
    {
        "periodo": 2014,
        "mes": 12,
        "codigo_establecimiento": 116101,
        "cod_area_funcional": 401,
        "detalle": "Hospital de Teno, area 401: conservar fila plausible con 775 dias disponibles.",
    },
    {
        "periodo": 2014,
        "mes": 6,
        "codigo_establecimiento": 116101,
        "cod_area_funcional": 407,
        "detalle": "Hospital de Teno, area 407: conservar fila plausible con 750 dias disponibles.",
    },
    {
        "periodo": 2020,
        "mes": 6,
        "codigo_establecimiento": 120105,
        "cod_area_funcional": 407,
        "detalle": "Hospital Comunitario de Laja, area 407: conservar fila con actividad; la otra son ceros.",
    },
]


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


def read_conflicts(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo de conflictos: {path}")

    df = pd.read_csv(path, sep=";", encoding="utf-8-sig", dtype=str)
    df = df.apply(lambda column: column.str.strip() if column.dtype == "object" else column)

    missing = [column for column in PK_CSV if column not in df.columns]
    if missing:
        raise ValueError(
            "El archivo de conflictos no contiene las columnas PK requeridas: "
            + ", ".join(missing)
        )

    return df


def decision_mask(df: pd.DataFrame, decision: dict[str, int | str]) -> pd.Series:
    mask = pd.Series(True, index=df.index)
    for csv_col, db_col in zip(PK_CSV, PK_DB):
        mask &= pd.to_numeric(df[csv_col], errors="raise").eq(int(decision[db_col]))
    return mask


def plausible_row(group: pd.DataFrame) -> pd.Series:
    # El criterio operativo es conservar la fila con mas dias-cama disponibles.
    # Fue validado caso por caso y coincide con las decisiones del orquestador:
    # A=71.74/775, B=72.13/750, C=15.0/60 frente a ceros absolutos.
    disponibilidad = pd.to_numeric(group["DIAS_CAMAS_DISPONIBLES"], errors="raise")
    return group.loc[disponibilidad.idxmax()]


def csv_numeric_values(row: pd.Series) -> dict[str, int | float]:
    values: dict[str, int | float] = {}

    for field in INTEGER_FIELDS:
        values[field] = int(pd.to_numeric(row[field.upper()], errors="raise"))

    for field in FLOAT_FIELDS:
        values[field] = float(pd.to_numeric(row[field.upper()], errors="raise"))

    return values


def row_to_dict(row) -> dict[str, int | float]:
    mapping = row._mapping
    values: dict[str, int | float] = {}

    for field in INTEGER_FIELDS:
        values[field] = int(mapping[field])

    for field in FLOAT_FIELDS:
        values[field] = float(mapping[field])

    return values


def values_differ(current: dict[str, int | float], expected: dict[str, int | float]) -> bool:
    for field in INTEGER_FIELDS:
        if int(current[field]) != int(expected[field]):
            return True

    for field in FLOAT_FIELDS:
        if abs(float(current[field]) - float(expected[field])) > 1e-9:
            return True

    return False


def compact_values(values: dict[str, int | float]) -> dict[str, int | float]:
    keys = ["indice_ocupacional", "dias_camas_disponibles", "numero_egresos"]
    return {key: values[key] for key in keys}


def main() -> int:
    root = project_root()
    conflicts_path = root / "data" / "processed" / "conflictos_clave_primaria.csv"
    engine: Engine | None = None

    select_sql = text(
        """
        SELECT periodo, mes, codigo_establecimiento, cod_area_funcional,
               dias_camas_ocupadas, dias_camas_disponibles, dias_estada,
               numero_egresos, egresos_fallecidos, traslados,
               indice_ocupacional, promedio_camas_disponible,
               promedio_dias_estada, letalidad, indice_rotacion
        FROM rem20.indicadores
        WHERE periodo = :periodo
          AND mes = :mes
          AND codigo_establecimiento = :codigo_establecimiento
          AND cod_area_funcional = :cod_area_funcional
        """
    )

    update_sql = text(
        """
        UPDATE rem20.indicadores
        SET dias_camas_ocupadas = :dias_camas_ocupadas,
            dias_camas_disponibles = :dias_camas_disponibles,
            dias_estada = :dias_estada,
            numero_egresos = :numero_egresos,
            egresos_fallecidos = :egresos_fallecidos,
            traslados = :traslados,
            indice_ocupacional = :indice_ocupacional,
            promedio_camas_disponible = :promedio_camas_disponible,
            promedio_dias_estada = :promedio_dias_estada,
            letalidad = :letalidad,
            indice_rotacion = :indice_rotacion
        WHERE periodo = :periodo
          AND mes = :mes
          AND codigo_establecimiento = :codigo_establecimiento
          AND cod_area_funcional = :cod_area_funcional
        """
    )

    verify_sql = text(
        """
        SELECT periodo, mes, codigo_establecimiento, cod_area_funcional,
               indice_ocupacional, dias_camas_disponibles, numero_egresos
        FROM rem20.indicadores
        WHERE (periodo, mes, codigo_establecimiento, cod_area_funcional) IN (
            (:periodo_a, :mes_a, :codigo_a, :area_a),
            (:periodo_b, :mes_b, :codigo_b, :area_b),
            (:periodo_c, :mes_c, :codigo_c, :area_c)
        )
        ORDER BY periodo, mes, codigo_establecimiento, cod_area_funcional
        """
    )

    try:
        conflicts = read_conflicts(conflicts_path)
        config = load_config(root)
        engine = create_db_engine(config)

        with engine.connect() as connection:
            transaction = connection.begin()
            try:
                for decision in DECISIONES:
                    pk_params = {key: int(decision[key]) for key in PK_DB}
                    group = conflicts.loc[decision_mask(conflicts, decision)].copy()

                    if len(group) != 2:
                        raise ValueError(
                            f"Se esperaban 2 filas candidatas para {pk_params}, "
                            f"pero se encontraron {len(group)}."
                        )

                    expected = csv_numeric_values(plausible_row(group))
                    current_row = connection.execute(select_sql, pk_params).fetchone()

                    if current_row is None:
                        raise ValueError(f"No existe registro en BD para PK {pk_params}")

                    current = row_to_dict(current_row)
                    update_required = values_differ(current, expected)

                    print("\nPK:", pk_params)
                    print("Decision:", decision["detalle"])
                    print("Antes BD:", compact_values(current))
                    print("Plausible:", compact_values(expected))

                    if update_required:
                        params = {**pk_params, **expected}
                        result = connection.execute(update_sql, params)
                        if result.rowcount != 1:
                            raise RuntimeError(
                                f"UPDATE inesperado para {pk_params}: rowcount={result.rowcount}"
                            )
                        print("Resultado: UPDATE aplicado")
                    else:
                        print("Resultado: sin cambios; la BD ya contiene la fila plausible")

                transaction.commit()
            except Exception:
                transaction.rollback()
                raise

            total = int(
                connection.execute(text("SELECT COUNT(*) FROM rem20.indicadores")).scalar_one()
            )
            print(f"\nCOUNT(*) rem20.indicadores: {total}")

            verify_params = {
                "periodo_a": 2014,
                "mes_a": 12,
                "codigo_a": 116101,
                "area_a": 401,
                "periodo_b": 2014,
                "mes_b": 6,
                "codigo_b": 116101,
                "area_b": 407,
                "periodo_c": 2020,
                "mes_c": 6,
                "codigo_c": 120105,
                "area_c": 407,
            }
            print("\nVerificacion de registros corregidos:")
            for row in connection.execute(verify_sql, verify_params):
                print(dict(row._mapping))

        return 0
    except Exception as exc:
        print(f"Error al corregir conflictos de clave primaria: {exc}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
