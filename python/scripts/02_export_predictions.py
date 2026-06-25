from __future__ import annotations

import math
import os
import sys
import warnings
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


MODEL_RELATIVE_PATH = Path("data") / "processed" / "modelos" / "rf_indice_ocupacional.pkl"
OUTPUT_RELATIVE_PATH = Path("data") / "processed" / "rem20_predicciones_2026.csv"
TARGET_YEAR = 2026
TOP_N_ESTABLISHMENTS = 5

EXPECTED_FEATURES = [
    "mes_sin",
    "mes_cos",
    "lag_1",
    "lag_12",
    "rolling_3",
    "area_funcional_cod",
    "cod_sss",
]

REQUIRED_COLUMNS = [
    "periodo",
    "mes",
    "codigo_establecimiento",
    "cod_area_funcional",
    "area_funcional",
    "establecimiento",
    "cod_sss",
    "numero_egresos",
    "indice_ocupacional",
]

NUMERIC_COLUMNS = [
    "periodo",
    "mes",
    "codigo_establecimiento",
    "cod_area_funcional",
    "cod_sss",
    "numero_egresos",
    "indice_ocupacional",
]

OUTPUT_COLUMNS = [
    "PERIODO",
    "MES",
    "CODIGO_ESTABLECIMIENTO",
    "ESTABLECIMIENTO",
    "AREA_FUNCIONAL",
    "INDICE_OCUPACIONAL_PREDICHO",
    "VALOR_REAL",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    raise RuntimeError(message)


def load_config(root: Path) -> dict[str, str]:
    env_path = root / ".env"
    if not env_path.exists():
        fail(f"No existe el archivo .env en la raiz del proyecto: {env_path}")

    load_dotenv(env_path)
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    config = {key: os.getenv(key) for key in required}
    missing = [key for key, value in config.items() if not value]

    if missing:
        fail("Faltan variables obligatorias en .env: " + ", ".join(missing))

    return {key: str(value) for key, value in config.items()}


def database_url(config: dict[str, str]) -> str:
    user = quote_plus(config["DB_USER"])
    password = quote_plus(config["DB_PASSWORD"])
    host = config["DB_HOST"]
    port = config["DB_PORT"]
    name = config["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


def create_db_engine(config: dict[str, str]) -> Engine:
    return create_engine(database_url(config), pool_pre_ping=True)


def load_model_bundle(model_path: Path) -> dict[str, Any]:
    if not model_path.exists():
        fail(f"No existe el modelo entrenado: {model_path}")

    bundle = joblib.load(model_path)
    if not isinstance(bundle, dict):
        fail("El archivo .pkl no contiene un dict.")

    missing_keys = [
        key for key in ["model", "features", "label_encoder_area_funcional"] if key not in bundle
    ]
    if missing_keys:
        fail("El dict del modelo no contiene las claves requeridas: " + ", ".join(missing_keys))

    features = list(bundle["features"])
    if features != EXPECTED_FEATURES:
        fail(
            "Las features del modelo no coinciden con el orden esperado. "
            f"Recibidas: {features}"
        )

    return bundle


def load_indicators(engine: Engine) -> pd.DataFrame:
    df = pd.read_sql_query(text("SELECT * FROM rem20.indicadores"), engine)
    df.columns = [column.lower() for column in df.columns]

    missing = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing:
        fail("Faltan columnas requeridas en rem20.indicadores: " + ", ".join(missing))

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    return df


def top_establishments(df: pd.DataFrame) -> list[float]:
    totals = (
        df.dropna(subset=["codigo_establecimiento"])
        .groupby("codigo_establecimiento", dropna=False)["numero_egresos"]
        .sum(min_count=1)
        .sort_values(ascending=False)
    )
    return totals.head(TOP_N_ESTABLISHMENTS).index.tolist()


def period_key(year: int, month: int) -> pd.Period:
    return pd.Period(year=int(year), month=int(month), freq="M")


def real_values_by_period(series_df: pd.DataFrame) -> dict[pd.Period, float]:
    values: dict[pd.Period, float] = {}
    for row in series_df.itertuples(index=False):
        if pd.isna(row.periodo) or pd.isna(row.mes) or pd.isna(row.indice_ocupacional):
            continue
        key = period_key(int(row.periodo), int(row.mes))
        values[key] = float(row.indice_ocupacional)
    return values


def value_for_period(
    key: pd.Period,
    real_values: dict[pd.Period, float],
    predicted_values: dict[pd.Period, float],
) -> float | None:
    if key in real_values:
        return real_values[key]
    return predicted_values.get(key)


def last_available_before(
    key: pd.Period,
    real_values: dict[pd.Period, float],
    predicted_values: dict[pd.Period, float],
) -> float | None:
    candidates = {
        period: value
        for period, value in {**predicted_values, **real_values}.items()
        if period < key and not pd.isna(value)
    }
    if not candidates:
        return None
    latest_period = max(candidates)
    return candidates[latest_period]


def rolling_3_value(
    key: pd.Period,
    real_values: dict[pd.Period, float],
    predicted_values: dict[pd.Period, float],
) -> float | None:
    values = [
        value_for_period(key - offset, real_values, predicted_values)
        for offset in range(1, 4)
    ]
    valid_values = [value for value in values if value is not None and not pd.isna(value)]
    if not valid_values:
        return None
    return float(sum(valid_values) / len(valid_values))


def actual_value_for_month(series_df: pd.DataFrame, month: int) -> float | None:
    actual = series_df.loc[
        (series_df["periodo"] == TARGET_YEAR) & (series_df["mes"] == month),
        "indice_ocupacional",
    ].dropna()
    if actual.empty:
        return None
    return float(actual.iloc[-1])


def first_non_null(series: pd.Series) -> Any:
    values = series.dropna()
    if values.empty:
        return None
    return values.iloc[0]


def predict_series(
    series_df: pd.DataFrame,
    model: Any,
    features: list[str],
    label_encoder: Any,
    warnings_list: list[str],
) -> list[dict[str, Any]]:
    series_df = series_df.sort_values(["periodo", "mes"]).copy()
    codigo_establecimiento = first_non_null(series_df["codigo_establecimiento"])
    cod_area_funcional = first_non_null(series_df["cod_area_funcional"])
    establecimiento = first_non_null(series_df["establecimiento"])
    area_funcional = first_non_null(series_df["area_funcional"])
    cod_sss = first_non_null(series_df["cod_sss"])

    if area_funcional is None:
        warnings_list.append(
            f"Serie omitida sin area_funcional: establecimiento={codigo_establecimiento}, "
            f"area={cod_area_funcional}"
        )
        return []

    area_label = str(area_funcional)
    if area_label not in set(label_encoder.classes_):
        warnings_list.append(
            f"Serie omitida por area_funcional no vista por el encoder: {area_label} "
            f"(establecimiento={codigo_establecimiento}, area={cod_area_funcional})"
        )
        return []

    if cod_sss is None or pd.isna(cod_sss):
        warnings_list.append(
            f"Serie omitida sin cod_sss: establecimiento={codigo_establecimiento}, "
            f"area={cod_area_funcional}"
        )
        return []

    real_values = real_values_by_period(series_df)
    if not real_values:
        warnings_list.append(
            f"Serie omitida sin base historica: establecimiento={codigo_establecimiento}, "
            f"area={cod_area_funcional}"
        )
        return []

    area_funcional_cod = int(label_encoder.transform([area_label])[0])
    predicted_values: dict[pd.Period, float] = {}
    rows: list[dict[str, Any]] = []

    for month in range(1, 13):
        current_key = period_key(TARGET_YEAR, month)
        lag_1 = value_for_period(current_key - 1, real_values, predicted_values)
        lag_12 = value_for_period(current_key - 12, real_values, predicted_values)
        if lag_12 is None or pd.isna(lag_12):
            lag_12 = last_available_before(current_key, real_values, predicted_values)

        rolling_3 = rolling_3_value(current_key, real_values, predicted_values)

        if lag_1 is None or rolling_3 is None or lag_12 is None:
            warnings_list.append(
                f"Mes omitido por memoria insuficiente: establecimiento={codigo_establecimiento}, "
                f"area={cod_area_funcional}, mes={month}"
            )
            continue

        feature_row = pd.DataFrame(
            [
                {
                    "mes_sin": math.sin(2 * math.pi * month / 12),
                    "mes_cos": math.cos(2 * math.pi * month / 12),
                    "lag_1": float(lag_1),
                    "lag_12": float(lag_12),
                    "rolling_3": float(rolling_3),
                    "area_funcional_cod": area_funcional_cod,
                    "cod_sss": float(cod_sss),
                }
            ],
            columns=features,
        )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=UserWarning)
            prediction = float(model.predict(feature_row)[0])

        predicted_values[current_key] = prediction
        actual_value = actual_value_for_month(series_df, month)

        rows.append(
            {
                "PERIODO": TARGET_YEAR,
                "MES": month,
                "CODIGO_ESTABLECIMIENTO": int(codigo_establecimiento),
                "ESTABLECIMIENTO": establecimiento,
                "AREA_FUNCIONAL": area_funcional,
                "INDICE_OCUPACIONAL_PREDICHO": round(prediction, 2),
                "VALOR_REAL": round(actual_value, 2) if actual_value is not None else pd.NA,
            }
        )

    return rows


def build_predictions(df: pd.DataFrame, model_bundle: dict[str, Any]) -> tuple[pd.DataFrame, list[str], int]:
    top_codes = top_establishments(df)
    filtered = df[df["codigo_establecimiento"].isin(top_codes)].copy()
    filtered = filtered.sort_values(
        ["codigo_establecimiento", "cod_area_funcional", "periodo", "mes"]
    )

    model = model_bundle["model"]
    features = list(model_bundle["features"])
    label_encoder = model_bundle["label_encoder_area_funcional"]
    warnings_list: list[str] = []
    rows: list[dict[str, Any]] = []

    grouped = filtered.groupby(
        ["codigo_establecimiento", "cod_area_funcional"],
        dropna=False,
        sort=True,
    )
    series_count = 0
    for _, series_df in grouped:
        series_count += 1
        rows.extend(predict_series(series_df, model, features, label_encoder, warnings_list))

    predictions = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    if not predictions.empty:
        predictions = predictions.sort_values(
            ["CODIGO_ESTABLECIMIENTO", "AREA_FUNCIONAL", "MES"]
        ).reset_index(drop=True)

    return predictions, warnings_list, series_count


def export_predictions(predictions: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    predictions.to_csv(output_path, sep=";", encoding="utf-8-sig", index=False)


def print_summary(predictions: pd.DataFrame, establishments_count: int, series_count: int) -> None:
    with_real = int(predictions["VALOR_REAL"].notna().sum()) if "VALOR_REAL" in predictions else 0
    print(f"Establecimientos TOP procesados: {establishments_count}")
    print(f"Series evaluadas: {series_count}")
    print(f"Filas predichas: {len(predictions)}")
    print(f"Filas con VALOR_REAL: {with_real}")
    print("Head del resultado:")
    print(predictions.head())


def main() -> int:
    root = project_root()
    model_path = root / MODEL_RELATIVE_PATH
    output_path = root / OUTPUT_RELATIVE_PATH
    engine: Engine | None = None

    try:
        model_bundle = load_model_bundle(model_path)
        config = load_config(root)
        engine = create_db_engine(config)
        df = load_indicators(engine)

        top_codes = top_establishments(df)
        predictions, warnings_list, series_count = build_predictions(df, model_bundle)
        export_predictions(predictions, output_path)

        for warning in warnings_list:
            print(f"Aviso: {warning}", file=sys.stderr)

        print_summary(predictions, len(top_codes), series_count)
        print(f"Archivo exportado: {output_path}")
        return 0
    except Exception as exc:
        print(f"Error al exportar predicciones 2026: {exc}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
