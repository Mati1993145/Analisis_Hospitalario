from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


PK = ["PERIODO", "MES", "CODIGO_ESTABLECIMIENTO", "COD_AREA_FUNCIONAL"]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_source_csv(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el CSV original: {csv_path}")

    df = pd.read_csv(csv_path, sep=";", encoding="utf-8", dtype=str)
    missing = [column for column in PK if column not in df.columns]
    if missing:
        raise ValueError(
            "El CSV no contiene las columnas de clave primaria requeridas: "
            + ", ".join(missing)
        )

    return df.apply(lambda column: column.str.strip() if column.dtype == "object" else column)


def find_conflicts(df: pd.DataFrame) -> pd.DataFrame:
    duplicated_pk = df.duplicated(subset=PK, keep=False)
    repeated = df.loc[duplicated_pk].copy()

    if repeated.empty:
        return repeated

    conflicting_keys = []
    for key, group in repeated.groupby(PK, dropna=False, sort=False):
        if len(group.drop_duplicates()) >= 2:
            conflicting_keys.append(key)

    if not conflicting_keys:
        return repeated.iloc[0:0].copy()

    key_index = pd.MultiIndex.from_tuples(conflicting_keys, names=PK)
    row_index = pd.MultiIndex.from_frame(df[PK], names=PK)
    conflicts = df.loc[row_index.isin(key_index)].copy()

    conflicts["GRUPO_PK"] = conflicts[PK].astype(str).agg("-".join, axis=1)
    conflicts["CONSERVADO"] = "NO"
    first_rows = ~conflicts.duplicated(subset=PK, keep="first")
    conflicts.loc[first_rows, "CONSERVADO"] = "SI"

    return conflicts


def print_summary(conflicts: pd.DataFrame) -> None:
    group_count = conflicts.groupby(PK, dropna=False).ngroups if not conflicts.empty else 0
    print(f"Grupos en conflicto: {group_count}")
    print(f"Filas exportadas: {len(conflicts)}")

    if conflicts.empty:
        return

    for key, group in conflicts.groupby(PK, dropna=False, sort=False):
        establecimiento = ""
        if "ESTABLECIMIENTO" in group.columns:
            establecimiento = str(group["ESTABLECIMIENTO"].iloc[0])
        pk_text = ", ".join(f"{column}={value}" for column, value in zip(PK, key))
        print(f"- {pk_text} | ESTABLECIMIENTO={establecimiento}")


def main() -> int:
    root = project_root()
    csv_path = root / "data" / "raw" / "indicadores_rem20_20260625.csv"
    output_path = root / "data" / "processed" / "conflictos_clave_primaria.csv"

    try:
        print(f"Leyendo CSV original: {csv_path}")
        df = read_source_csv(csv_path)

        conflicts = find_conflicts(df)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        conflicts.to_csv(output_path, sep=";", encoding="utf-8-sig", index=False)

        print_summary(conflicts)
        print(f"Archivo exportado: {output_path}")
        return 0
    except Exception as exc:
        print(f"Error al generar reporte de conflictos: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
