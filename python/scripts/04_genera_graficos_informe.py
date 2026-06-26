from __future__ import annotations

import os
import sys
from pathlib import Path
from urllib.parse import quote_plus

import joblib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from matplotlib.colors import LinearSegmentedColormap
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


COLORS = {
    "cyan": "#22D3EE",
    "green": "#34D399",
    "amber": "#FBBF24",
    "red": "#F87171",
    "violet": "#A78BFA",
    "text": "#1A1F2E",
    "grid": "#E5E7EB",
    "muted": "#6B7280",
}

MONTH_LABELS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
FIGSIZE = (11, 6)
SOURCE_TEXT = "Fuente: MINSAL REM20 · Elaboración propia"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_config(root: Path) -> dict[str, str]:
    load_dotenv(root / ".env")
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    config = {key: os.getenv(key) for key in required}
    missing = [key for key, value in config.items() if not value]
    if missing:
        raise ValueError("Faltan variables obligatorias en .env: " + ", ".join(missing))
    return {key: str(value) for key, value in config.items()}


def database_url(config: dict[str, str]) -> str:
    user = quote_plus(config["DB_USER"])
    pwd = quote_plus(config["DB_PASSWORD"])
    host = config["DB_HOST"]
    port = config["DB_PORT"]
    name = config["DB_NAME"]
    return f"postgresql+psycopg2://{user}:{pwd}@{host}:{port}/{name}"


def create_db_engine(config: dict[str, str]) -> Engine:
    return create_engine(database_url(config), pool_pre_ping=True)


def setup_matplotlib() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": COLORS["text"],
            "axes.labelcolor": COLORS["text"],
            "axes.titlecolor": COLORS["text"],
            "xtick.color": COLORS["text"],
            "ytick.color": COLORS["text"],
            "text.color": COLORS["text"],
            "axes.grid": True,
            "grid.color": COLORS["grid"],
            "grid.linewidth": 0.8,
            "grid.alpha": 0.85,
        }
    )


def add_source(fig: plt.Figure) -> None:
    fig.text(0.99, 0.01, SOURCE_TEXT, ha="right", fontsize=8, color=COLORS["muted"])


def save_figure(fig: plt.Figure, path: Path) -> None:
    add_source(fig)
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG generado: {path}")


def month_date_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["fecha"] = pd.to_datetime(
        out["periodo"].astype(int).astype(str) + "-" + out["mes"].astype(int).astype(str).str.zfill(2) + "-01"
    )
    return out.sort_values("fecha")


def load_evolucion(engine: Engine) -> pd.DataFrame:
    query = text(
        """
        SELECT periodo, mes, indice_ocupacional_prom, letalidad_prom
        FROM rem20.v_evolucion_mensual
        ORDER BY periodo, mes
        """
    )
    df = pd.read_sql_query(query, engine)
    return month_date_frame(df)


def graph_evolucion_ocupacion(evolucion: pd.DataFrame, out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(evolucion["fecha"], evolucion["indice_ocupacional_prom"], color=COLORS["cyan"], linewidth=2.4)
    ax.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2020-12-31"), color=COLORS["red"], alpha=0.11)
    ax.text(pd.Timestamp("2020-05-01"), ax.get_ylim()[0] + 1, "Desplome 2020", color=COLORS["red"], fontsize=10)
    ax.set_title("Evolución del índice ocupacional nacional 2014-2026", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Año")
    ax.set_ylabel("Índice ocupacional promedio (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator(1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "01_evolucion_ocupacion.png")


def graph_efecto_covid(evolucion: pd.DataFrame, out_dir: Path) -> None:
    df = evolucion[(evolucion["periodo"] >= 2018) & (evolucion["periodo"] <= 2022)].copy()

    fig, ax1 = plt.subplots(figsize=FIGSIZE)
    ax2 = ax1.twinx()

    ax1.axvspan(pd.Timestamp("2020-01-01"), pd.Timestamp("2021-12-31"), color=COLORS["red"], alpha=0.12, label="Periodo crítico 2020-2021")
    line1 = ax1.plot(df["fecha"], df["indice_ocupacional_prom"], color=COLORS["cyan"], linewidth=2.8, label="Ocupación promedio")
    line2 = ax2.plot(df["fecha"], df["letalidad_prom"], color=COLORS["red"], linewidth=2.8, label="Letalidad promedio")

    april_2020 = df[(df["periodo"] == 2020) & (df["mes"] == 4)]
    if not april_2020.empty:
        x = april_2020["fecha"].iloc[0]
        y = april_2020["indice_ocupacional_prom"].iloc[0]
        ax1.scatter([x], [y], s=70, color=COLORS["amber"], edgecolor=COLORS["text"], zorder=5)
        ax1.annotate(
            "Mínimo abril 2020\n45,61%",
            xy=(x, y),
            xytext=(pd.Timestamp("2019-06-01"), y - 9),
            arrowprops={"arrowstyle": "->", "color": COLORS["text"], "lw": 1},
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS["grid"]},
        )

    peak_2021 = df[df["periodo"] == 2021].sort_values("letalidad_prom", ascending=False).head(1)
    if not peak_2021.empty:
        x = peak_2021["fecha"].iloc[0]
        y = peak_2021["letalidad_prom"].iloc[0]
        ax2.scatter([x], [y], s=70, color=COLORS["red"], edgecolor=COLORS["text"], zorder=5)
        ax2.annotate(
            "Peak 2021\n≈4,67%",
            xy=(x, y),
            xytext=(pd.Timestamp("2021-07-01"), y + 0.35),
            arrowprops={"arrowstyle": "->", "color": COLORS["text"], "lw": 1},
            fontsize=10,
            bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS["grid"]},
        )

    ax1.set_title("El doble efecto de la pandemia: menos pacientes, pero más graves", fontsize=16, pad=14, weight="bold")
    ax1.set_xlabel("Mes")
    ax1.set_ylabel("Índice ocupacional promedio (%)", color=COLORS["cyan"])
    ax2.set_ylabel("Letalidad promedio (%)", color=COLORS["red"])
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax1.tick_params(axis="x", rotation=45)
    lines = line1 + line2
    labels = [line.get_label() for line in lines]
    labels.append("Periodo crítico 2020-2021")
    handles = lines + [plt.Rectangle((0, 0), 1, 1, color=COLORS["red"], alpha=0.12)]
    ax1.legend(handles, labels, loc="upper left", frameon=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "02_efecto_covid.png")


def graph_estacionalidad(evolucion: pd.DataFrame, out_dir: Path) -> None:
    monthly = evolucion.groupby("mes", as_index=False)["indice_ocupacional_prom"].mean()
    colors = [COLORS["cyan"]] * 12
    colors[7] = COLORS["amber"]

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.bar(monthly["mes"], monthly["indice_ocupacional_prom"], color=colors, edgecolor="white", linewidth=1.0)
    ax.plot(monthly["mes"], monthly["indice_ocupacional_prom"], color=COLORS["text"], linewidth=1.4, alpha=0.75)
    ax.set_title("Estacionalidad del índice ocupacional por mes", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Índice ocupacional promedio (%)")
    ax.set_xticks(range(1, 13), MONTH_LABELS)
    agosto = monthly.loc[monthly["mes"] == 8, "indice_ocupacional_prom"].iloc[0]
    ax.annotate(
        "Peak de invierno austral\nAgosto",
        xy=(8, agosto),
        xytext=(8.7, agosto + 2.0),
        arrowprops={"arrowstyle": "->", "color": COLORS["text"], "lw": 1},
        fontsize=10,
        bbox={"boxstyle": "round,pad=0.3", "fc": "white", "ec": COLORS["grid"]},
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "03_estacionalidad.png")


def graph_heatmap_letalidad(engine: Engine, out_dir: Path) -> None:
    query = text(
        """
        SELECT area_funcional, periodo, numero_egresos, egresos_fallecidos
        FROM rem20.indicadores
        WHERE numero_egresos IS NOT NULL
        """
    )
    df = pd.read_sql_query(query, engine)
    total_area = df.groupby("area_funcional")["numero_egresos"].sum()
    relevant_areas = total_area[total_area > 1000].index
    df = df[df["area_funcional"].isin(relevant_areas)].copy()

    grouped = (
        df.groupby(["area_funcional", "periodo"], as_index=False)
        .agg(numero_egresos=("numero_egresos", "sum"), egresos_fallecidos=("egresos_fallecidos", "sum"))
    )
    grouped["letalidad_pct"] = np.where(
        grouped["numero_egresos"] > 0,
        100 * grouped["egresos_fallecidos"] / grouped["numero_egresos"],
        np.nan,
    )
    top_areas = (
        grouped.groupby("area_funcional")["letalidad_pct"]
        .mean()
        .sort_values(ascending=False)
        .head(15)
        .index
    )
    pivot = (
        grouped[grouped["area_funcional"].isin(top_areas)]
        .pivot(index="area_funcional", columns="periodo", values="letalidad_pct")
        .loc[top_areas]
    )

    fig_height = max(6, 0.38 * len(pivot) + 2.2)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    cmap = LinearSegmentedColormap.from_list("custom_reds", ["#FFF7F7", "#FCA5A5", "#B91C1C"])
    image = ax.imshow(pivot.values, aspect="auto", cmap=cmap)
    ax.set_title("Letalidad por área funcional y año", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Año")
    ax.set_ylabel("Área funcional")
    ax.set_xticks(range(len(pivot.columns)), [str(int(col)) for col in pivot.columns], rotation=45)
    ax.set_yticks(range(len(pivot.index)), pivot.index)
    cbar = fig.colorbar(image, ax=ax)
    cbar.set_label("Letalidad (%)")

    if pivot.shape[0] <= 15 and pivot.shape[1] <= 14:
        for row in range(pivot.shape[0]):
            for col in range(pivot.shape[1]):
                value = pivot.iloc[row, col]
                if pd.notna(value):
                    ax.text(col, row, f"{value:.1f}", ha="center", va="center", fontsize=7, color=COLORS["text"])

    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "04_heatmap_letalidad.png")


def graph_clusters_pca(engine: Engine, out_dir: Path) -> None:
    query = text(
        """
        SELECT establecimiento, indice_ocupacional, promedio_dias_estada, letalidad, indice_rotacion
        FROM rem20.indicadores
        WHERE establecimiento IS NOT NULL
        """
    )
    df = pd.read_sql_query(query, engine)
    features = ["indice_ocupacional", "promedio_dias_estada", "letalidad", "indice_rotacion"]
    agg = df.groupby("establecimiento", as_index=False)[features].mean().dropna()

    scaler = StandardScaler()
    x_scaled = scaler.fit_transform(agg[features])
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(x_scaled)
    coords = PCA(n_components=2, random_state=42).fit_transform(x_scaled)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    cluster_colors = [COLORS["cyan"], COLORS["green"], COLORS["amber"], COLORS["violet"]]
    for cluster in range(4):
        mask = clusters == cluster
        ax.scatter(coords[mask, 0], coords[mask, 1], s=58, alpha=0.82, color=cluster_colors[cluster], label=f"Cluster {cluster}")

    ax.set_title("Segmentación de establecimientos: proyección PCA de 4 clusters", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Componente principal 1")
    ax.set_ylabel("Componente principal 2")
    ax.legend(loc="best", frameon=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "05_clusters_pca.png")


def graph_predicciones_2026(root: Path, out_dir: Path) -> None:
    csv_path = root / "data" / "processed" / "rem20_predicciones_2026.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No existe el CSV de predicciones: {csv_path}")

    df = pd.read_csv(csv_path, sep=";", encoding="utf-8-sig")
    required = ["PERIODO", "MES", "INDICE_OCUPACIONAL_PREDICHO", "VALOR_REAL"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError("Faltan columnas en rem20_predicciones_2026.csv: " + ", ".join(missing))

    df = df[df["PERIODO"] == 2026].copy()
    monthly = (
        df.groupby("MES", as_index=False)
        .agg(
            INDICE_OCUPACIONAL_PREDICHO=("INDICE_OCUPACIONAL_PREDICHO", "mean"),
            VALOR_REAL=("VALOR_REAL", "mean"),
        )
        .sort_values("MES")
    )

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(monthly["MES"], monthly["INDICE_OCUPACIONAL_PREDICHO"], color=COLORS["violet"], linewidth=2.6, linestyle="--", marker="o", label="Predicho")
    real = monthly.dropna(subset=["VALOR_REAL"])
    ax.plot(real["MES"], real["VALOR_REAL"], color=COLORS["cyan"], linewidth=2.8, marker="o", label="Real")
    ax.set_title("Real vs predicho 2026: índice ocupacional promedio", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Mes")
    ax.set_ylabel("Índice ocupacional promedio (%)")
    ax.set_xticks(range(1, 13), MONTH_LABELS)
    ax.legend(loc="best", frameon=True)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "06_predicciones_2026.png")


def graph_feature_importance(root: Path, out_dir: Path) -> None:
    model_path = root / "data" / "processed" / "modelos" / "rf_indice_ocupacional.pkl"
    if not model_path.exists():
        raise FileNotFoundError(f"No existe el modelo Random Forest: {model_path}")

    bundle = joblib.load(model_path)
    model = bundle["model"]
    features = list(bundle["features"])
    importances = np.asarray(model.feature_importances_)
    order = np.argsort(importances)

    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.barh(np.array(features)[order], importances[order], color=COLORS["cyan"])
    ax.set_title("Importancia de variables del modelo Random Forest", fontsize=16, pad=14, weight="bold")
    ax.set_xlabel("Importancia")
    ax.set_ylabel("Variable")
    for idx, value in enumerate(importances[order]):
        ax.text(value + 0.01, idx, f"{value:.2f}", va="center", fontsize=9, color=COLORS["text"])
    ax.set_xlim(0, max(importances) * 1.18)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save_figure(fig, out_dir / "07_feature_importance.png")


def main() -> int:
    root = project_root()
    out_dir = root / "data" / "processed" / "graficos_informe"
    engine: Engine | None = None

    try:
        setup_matplotlib()
        out_dir.mkdir(parents=True, exist_ok=True)

        config = load_config(root)
        engine = create_db_engine(config)
        evolucion = load_evolucion(engine)

        graph_evolucion_ocupacion(evolucion, out_dir)
        graph_efecto_covid(evolucion, out_dir)
        graph_estacionalidad(evolucion, out_dir)
        graph_heatmap_letalidad(engine, out_dir)
        graph_clusters_pca(engine, out_dir)
        graph_predicciones_2026(root, out_dir)
        graph_feature_importance(root, out_dir)

        print(f"Gráficos del informe generados en: {out_dir}")
        return 0
    except Exception as exc:
        print(f"Error al generar gráficos del informe: {exc}", file=sys.stderr)
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
