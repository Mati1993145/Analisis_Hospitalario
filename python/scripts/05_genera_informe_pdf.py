from __future__ import annotations

import sys
from pathlib import Path

from matplotlib import font_manager
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image as RLImage,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PRIMARY = "#1A1F2E"
CYAN = "#22D3EE"
GREEN = "#34D399"
AMBER = "#FBBF24"
RED = "#F87171"
VIOLET = "#A78BFA"
MUTED = "#6B7280"
GRID = "#E5E7EB"
SOURCE_TEXT = "Fuente: MINSAL REM20 · Elaboración propia"
FOOTER_TITLE = "Análisis de Indicadores Hospitalarios · Chile 2014–2026"
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

GRAPH_FILES = [
    "01_evolucion_ocupacion.png",
    "02_efecto_covid.png",
    "03_estacionalidad.png",
    "04_heatmap_letalidad.png",
    "05_clusters_pca.png",
    "06_predicciones_2026.png",
    "07_feature_importance.png",
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def register_fonts() -> None:
    """Registra DejaVu Sans para soportar acentos y símbolos en el PDF."""
    global FONT_REGULAR, FONT_BOLD

    try:
        regular_path = font_manager.findfont("DejaVu Sans", fallback_to_default=True)
        bold_path = font_manager.findfont(
            font_manager.FontProperties(family="DejaVu Sans", weight="bold"),
            fallback_to_default=True,
        )
        pdfmetrics.registerFont(TTFont("DejaVuSans", regular_path))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", bold_path))
        FONT_REGULAR = "DejaVuSans"
        FONT_BOLD = "DejaVuSans-Bold"
    except Exception:
        FONT_REGULAR = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"


def build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}

    styles["cover_title"] = ParagraphStyle(
        "CoverTitle",
        parent=base["Title"],
        fontName=FONT_BOLD,
        fontSize=22,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor(PRIMARY),
        spaceAfter=20,
    )
    styles["cover_subtitle"] = ParagraphStyle(
        "CoverSubtitle",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=13,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor(PRIMARY),
        spaceAfter=18,
    )
    styles["cover_meta"] = ParagraphStyle(
        "CoverMeta",
        parent=base["Normal"],
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor(MUTED),
    )
    styles["h1"] = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading1"],
        fontName=FONT_BOLD,
        fontSize=16,
        leading=21,
        textColor=colors.HexColor(PRIMARY),
        spaceBefore=8,
        spaceAfter=10,
    )
    styles["h2"] = ParagraphStyle(
        "SubHeading",
        parent=base["Heading2"],
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor(PRIMARY),
        spaceBefore=8,
        spaceAfter=6,
    )
    styles["body"] = ParagraphStyle(
        "BodyJustified",
        parent=base["BodyText"],
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        textColor=colors.HexColor(PRIMARY),
        spaceAfter=7,
    )
    styles["bullet"] = ParagraphStyle(
        "Bullet",
        parent=styles["body"],
        leftIndent=14,
        firstLineIndent=-8,
        bulletIndent=0,
        spaceAfter=5,
    )
    styles["toc"] = ParagraphStyle(
        "TOC",
        parent=styles["body"],
        alignment=TA_LEFT,
        leftIndent=8,
        spaceAfter=4,
    )
    styles["caption"] = ParagraphStyle(
        "Caption",
        parent=base["BodyText"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=colors.HexColor(MUTED),
        spaceAfter=9,
    )
    styles["table_cell"] = ParagraphStyle(
        "TableCell",
        parent=base["BodyText"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=10,
        textColor=colors.HexColor(PRIMARY),
    )
    styles["table_head"] = ParagraphStyle(
        "TableHead",
        parent=styles["table_cell"],
        fontName=FONT_BOLD,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    return styles


def paragraph(text: str, styles: dict[str, ParagraphStyle], style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def bullet(text: str, styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph(text, styles["bullet"], bulletText="•")


def scaled_image(path: Path, max_width: float) -> RLImage:
    if not path.exists():
        raise FileNotFoundError(f"No existe el PNG requerido para el informe: {path}")

    with PILImage.open(path) as img:
        width_px, height_px = img.size
    ratio = height_px / width_px
    return RLImage(str(path), width=max_width, height=max_width * ratio)


def add_graph(story: list, graph_dir: Path, filename: str, styles: dict[str, ParagraphStyle], max_width: float) -> None:
    path = graph_dir / filename
    story.append(scaled_image(path, max_width))
    story.append(paragraph(SOURCE_TEXT, styles, "caption"))


def footer(canvas, doc) -> None:
    canvas.saveState()
    width, _ = A4
    y = 1.15 * cm
    canvas.setStrokeColor(colors.HexColor(GRID))
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, y + 0.35 * cm, width - doc.rightMargin, y + 0.35 * cm)
    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(colors.HexColor(MUTED))
    canvas.drawString(doc.leftMargin, y, FOOTER_TITLE)
    canvas.drawRightString(width - doc.rightMargin, y, f"Página {doc.page}")
    canvas.drawString(doc.leftMargin, y - 0.35 * cm, SOURCE_TEXT)
    canvas.restoreState()


def cluster_table(styles: dict[str, ParagraphStyle], max_width: float) -> Table:
    headers = ["Cluster", "Perfil", "N° estab", "Ocupación", "Días estada", "Letalidad", "Rotación"]
    rows = [
        ["0", "Baja complejidad/baja demanda", "120 estab (~57%)", "43,7%", "9,8 d", "2,7%", "2,2"],
        ["1", "Alta complejidad/agudos", "82 estab (~39%)", "73,4%", "17,8 d", "10,8% (la más alta)", "2,7"],
        ["2", "Larga estadía/psiquiátricos", "4 estab (~2%)", "81,8%", "343 d", "2,2%", "baja"],
        ["3", "Atípicos/altísima rotación", "2 estab (~1%)", ">100% (camas prestadas)", "4,5 d", "", "30,4"],
    ]
    data = [[Paragraph(cell, styles["table_head"]) for cell in headers]]
    for row in rows:
        data.append([Paragraph(cell, styles["table_cell"]) for cell in row])

    col_widths = [1.2 * cm, 4.4 * cm, 2.2 * cm, 2.3 * cm, 2.1 * cm, 2.4 * cm, 1.8 * cm]
    scale = min(1, max_width / sum(col_widths))
    col_widths = [width * scale for width in col_widths]

    table = Table(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(PRIMARY)),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(GRID)),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def pipeline_table(styles: dict[str, ParagraphStyle], max_width: float) -> Table:
    steps = [
        "CSV REM20",
        "Carga validada a PostgreSQL",
        "Vistas SQL analíticas",
        "Análisis Python / modelo ML",
        "API FastAPI",
        "Dashboard web + informe PDF",
    ]
    data = [[Paragraph(step, styles["table_cell"]) for step in steps]]
    table = Table(data, colWidths=[max_width / len(steps)] * len(steps), hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9FAFB")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor(GRID)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def validate_graphs(graph_dir: Path) -> None:
    missing = [str(graph_dir / filename) for filename in GRAPH_FILES if not (graph_dir / filename).exists()]
    if missing:
        raise FileNotFoundError("Faltan PNG requeridos para el informe:\n" + "\n".join(missing))


def build_story(root: Path, graph_dir: Path, styles: dict[str, ParagraphStyle], max_width: float) -> list:
    story: list = []

    # Portada
    story.append(Spacer(1, 5.0 * cm))
    story.append(paragraph("Análisis de Indicadores Hospitalarios del Sistema Público de Salud de Chile (2014–2026)", styles, "cover_title"))
    story.append(paragraph("Estudio de ocupación, letalidad, eficiencia operativa y proyección de demanda", styles, "cover_subtitle"))
    story.append(Spacer(1, 1.0 * cm))
    story.append(paragraph("Matías Durán · Data & Business Analyst", styles, "cover_meta"))
    story.append(paragraph("Junio 2026", styles, "cover_meta"))
    story.append(paragraph("https://github.com/Mati1993145/Analisis_Hospitalario", styles, "cover_meta"))
    story.append(PageBreak())

    # Resumen ejecutivo
    story.append(paragraph("Resumen Ejecutivo", styles, "h1"))
    story.append(paragraph("Se analizaron 165.232 registros mensuales de indicadores hospitalarios REM20 del MINSAL, correspondientes a 208 establecimientos del sistema público, para el periodo 2014–2026 (13 años; 2026 parcial).", styles))
    story.append(paragraph("Los tres hallazgos más importantes, en lenguaje de negocio, son los siguientes:", styles))
    story.append(bullet("<b>El doble efecto de la pandemia:</b> en abril 2020 la ocupación cayó a su mínimo histórico (≈45,6% vs rango habitual 60–70%) por la suspensión de atención electiva, mientras la letalidad hospitalaria saltó de ~2,8% (estable 2014–2019) a 4,31% (2020) y 4,67% (2021): menos pacientes, pero más graves.", styles))
    story.append(bullet("<b>El sistema no volvió a la línea base:</b> la letalidad se estabilizó en una meseta de ~3,2% (2023–2026), por encima del ~2,8% pre-pandemia, y la ocupación se recuperó a niveles superiores a los previos, señal de presión por listas de espera.", styles))
    story.append(bullet("<b>La ocupación es altamente predecible a corto plazo:</b> un modelo Random Forest alcanza R²=0,636, y el 73% de su poder predictivo proviene de un solo factor: la ocupación del mes anterior, lag_1.", styles))
    story.append(paragraph("Se construyó un pipeline reproducible con PostgreSQL + Python, control de versiones en Git/GitHub, una API FastAPI y un dashboard web en dark mode con auto-refresh que mantiene los indicadores vigentes sin intervención manual.", styles))
    story.append(PageBreak())

    # Índice
    story.append(paragraph("Índice", styles, "h1"))
    for item in [
        "1. Contexto y objetivos",
        "2. Metodología y arquitectura",
        "3. Calidad de datos",
        "4. Análisis exploratorio",
        "5. Modelado predictivo",
        "6. Segmentación de establecimientos",
        "7. Sistema automatizado",
        "8. Conclusiones y trabajo futuro",
    ]:
        story.append(paragraph(item, styles, "toc"))
    story.append(PageBreak())

    story.append(paragraph("1. Contexto y Objetivos", styles, "h1"))
    story.append(paragraph("El REM20 del MINSAL es un registro estadístico mensual de la actividad hospitalaria, con información de camas, egresos, días de estada y letalidad por establecimiento y área funcional. Su valor analítico está en que permite medir ocupación, eficiencia operativa y resultados clínicos del sistema público con granularidad mensual.", styles))
    story.append(paragraph("Los objetivos del estudio fueron caracterizar la ocupación y su estacionalidad, cuantificar el impacto de la pandemia, evaluar la letalidad por área funcional, segmentar establecimientos según su comportamiento operativo y proyectar la demanda 2026.", styles))

    story.append(paragraph("2. Metodología y Arquitectura", styles, "h1"))
    story.append(paragraph("El stack usado combina PostgreSQL (esquema rem20, tabla indicadores y 4 vistas analíticas), Python (pandas, scikit-learn, statsmodels), FastAPI para API JSON, dashboard web HTML/JS con Plotly y un modelo Random Forest para predicción del índice ocupacional.", styles))
    story.append(pipeline_table(styles, max_width))
    story.append(Spacer(1, 0.3 * cm))
    story.append(paragraph("El flujo de trabajo se mantuvo bajo control de versiones en un repositorio público de GitHub, con commits por fase. No se versionaron secretos (.env) ni modelos pesados, incluyendo el archivo .pkl de 209 MB.", styles))

    story.append(paragraph("3. Calidad de Datos", styles, "h1"))
    story.append(paragraph("La calidad de datos fue un diferenciador clave del proyecto. Se detectaron 3 conflictos de clave primaria, equivalentes a 6 filas, donde la combinación (periodo, mes, codigo_establecimiento, cod_area_funcional) se repetía con cifras distintas: Hospital de Teno (2014-12 área 401; 2014-06 área 407) y Hospital Comunitario de Laja (2020-06 área 407).", styles))
    story.append(paragraph("La evidencia mostró que el criterio ingenuo keep=\"first\" conservaba la fila ANÓMALA. En Teno 2014-12 área 401 la fila conservada tenía índice ocupacional 7,53, anómalamente bajo, mientras la descartada tenía los datos sustantivos: 775 días-cama disponibles e índice 71,74.", styles))
    story.append(paragraph("La corrección fue caso por caso y trazable: Teno 2014-12 área 401: 7,53 → 71,74; Teno 2014-06 área 407: 2,22 → 72,13; Laja 2020-06 área 407: se mantuvo 15,0, porque la alternativa eran ceros y representaba un registro vacío. El total quedó estable en 165.232 registros.", styles))
    story.append(paragraph("Los registros no se borraron silenciosamente. El archivo CSV data/processed/conflictos_clave_primaria.csv preserva los 6 registros crudos para trazabilidad. En este tipo de análisis, documentar es más robusto que ocultar la anomalía.", styles))

    story.append(PageBreak())
    story.append(paragraph("4. Análisis Exploratorio", styles, "h1"))
    story.append(paragraph("La ocupación nacional muestra una evolución con quiebre visible durante 2020 y recuperación posterior. La estacionalidad es consistente con el invierno austral: el peak aparece en agosto, con una amplitud modesta de alrededor de 4 puntos, pasando de valores cercanos a jun–ago ~66 versus feb/dic ~62.", styles))
    add_graph(story, graph_dir, "01_evolucion_ocupacion.png", styles, max_width)
    add_graph(story, graph_dir, "03_estacionalidad.png", styles, max_width)
    story.append(paragraph("El hallazgo estrella es el doble efecto COVID: la ocupación alcanzó su mínimo en abril 2020 (45,61), mientras la letalidad subió a 4,31% en 2020 y llegó a un pico de 4,67% en 2021. El sistema tuvo menos pacientes hospitalizados, pero con mayor gravedad promedio.", styles))
    add_graph(story, graph_dir, "02_efecto_covid.png", styles, max_width)
    story.append(paragraph("El promedio de días de estada requiere un matiz importante: está dominado por hospitales psiquiátricos, como Philippe Pinel con 493 días, El Peral con 388 y Horwitz con 344 en 2025. Eso refleja el modelo de atención de larga estadía, no ineficiencia operativa por sí mismo.", styles))
    story.append(paragraph("La letalidad por área funcional muestra una meseta post-pandemia cercana a ~3,2%. Del mismo modo, los líderes de letalidad por establecimiento, como San José de Maipo con 18,3% en 2025, corresponden a hospitales de larga estadía o crónicos; esto describe perfil de paciente, no necesariamente calidad clínica.", styles))
    add_graph(story, graph_dir, "04_heatmap_letalidad.png", styles, max_width)

    story.append(PageBreak())
    story.append(paragraph("5. Modelado Predictivo", styles, "h1"))
    story.append(paragraph("Se entrenó un Random Forest para predecir indice_ocupacional. El entrenamiento usó 116.443 filas (≤2023) y el test temporal estricto usó 26.185 filas (2024–2025). El resultado fue R²=0,636 · MAE=8,13 · RMSE=19,95.", styles))
    story.append(paragraph("La lectura honesta es que el modelo tiene buen ajuste típico, pero la brecha MAE↔RMSE evidencia errores grandes en casos extremos, especialmente áreas con camas prestadas o comportamientos atípicos.", styles))
    story.append(paragraph("El principal insight operativo es que la ocupación es altamente autorregresiva: lag_1 concentra 0,73 de la importancia, rolling_3 aporta 0,12 y lag_12 aporta 0,06.", styles))
    add_graph(story, graph_dir, "07_feature_importance.png", styles, max_width)
    story.append(paragraph("Reportar R²=0,636 real, sin fuga de datos y con test temporal estricto, es preferible a presentar un número alto pero engañoso. Para decisiones de gestión, la confianza depende de la honestidad metodológica más que del atractivo de una métrica inflada.", styles))

    story.append(paragraph("6. Segmentación de Establecimientos", styles, "h1"))
    story.append(paragraph("Se aplicó KMeans con k=4, validado por método del codo, sobre indicadores agregados por establecimiento. El gráfico PCA es una representación bidimensional ilustrativa; la caracterización oficial se resume en la tabla.", styles))
    add_graph(story, graph_dir, "05_clusters_pca.png", styles, max_width)
    story.append(cluster_table(styles, max_width))
    story.append(Spacer(1, 0.3 * cm))
    story.append(paragraph("El cluster 2 agrupa establecimientos de larga estadía/psiquiátricos, incluyendo El Peral, Horwitz y Philippe Pinel. El cluster 3 reúne casos atípicos de altísima rotación y ocupación superior a 100%, asociados a camas prestadas.", styles))

    story.append(PageBreak())
    story.append(paragraph("7. Sistema Automatizado", styles, "h1"))
    story.append(paragraph("El backend FastAPI expone una API de solo lectura con indicadores y vistas como endpoints JSON, incluyendo documentación Swagger automática. El dashboard web usa dark mode y auto-refresh cada 5 minutos, con cuatro pestañas: Resumen, Efecto COVID, Establecimientos y Predicciones 2026. El backend sirve el frontend bajo el mismo origen.", styles))
    story.append(paragraph("Las predicciones 2026 corresponden a un pronóstico recursivo del índice ocupacional para los 5 hospitales de mayor egreso histórico: Barros Luco Trudeau, Sótero del Río, Guillermo Grant Benavente, Víctor Ríos Ruiz y Hernán Henríquez Aravena. El resultado contiene 84 series y 1.008 filas, con comparación real vs predicho para enero–mayo 2026.", styles))
    add_graph(story, graph_dir, "06_predicciones_2026.png", styles, max_width)
    story.append(paragraph("La vigencia operativa se mantiene porque el dashboard recarga datos automáticamente. A medida que lleguen nuevos meses, el modelo puede re-entrenarse y el pipeline puede regenerar predicciones e informe sin intervención manual sobre los cálculos base.", styles))

    story.append(paragraph("8. Conclusiones y Trabajo Futuro", styles, "h1"))
    story.append(paragraph("La pandemia dejó una huella estructural en el sistema público: mayor letalidad y presión asistencial persistente. La ocupación es estacional y altamente predecible a corto plazo, y la calidad de datos fue un eje central del estudio, no una etapa secundaria.", styles))
    story.append(paragraph("Las limitaciones son relevantes: 2026 es parcial; el R²=0,636 deja margen de error en casos extremos; el modelo no captura shocks externos como nuevas pandemias o cambios de política; y los clusters 2 y 3 son grupos muy pequeños.", styles))
    story.append(paragraph("Los próximos pasos recomendados son re-entrenamiento periódico con nuevos meses, incorporación de otras bases REM, alertas automáticas de saturación y validación clínica de los hallazgos de letalidad.", styles))

    return story


def main() -> int:
    root = project_root()
    graph_dir = root / "data" / "processed" / "graficos_informe"
    output_path = root / "data" / "processed" / "Informe_REM20_Chile_2014-2026.pdf"
    tmp_path = output_path.with_suffix(".tmp.pdf")

    try:
        validate_graphs(graph_dir)
        register_fonts()
        styles = build_styles()

        doc = SimpleDocTemplate(
            str(tmp_path),
            pagesize=A4,
            rightMargin=2 * cm,
            leftMargin=2 * cm,
            topMargin=2 * cm,
            bottomMargin=2.2 * cm,
            title="Análisis de Indicadores Hospitalarios REM20 Chile 2014-2026",
            author="Matías Durán",
        )
        story = build_story(root, graph_dir, styles, doc.width)
        doc.build(story, onFirstPage=footer, onLaterPages=footer)

        if output_path.exists():
            output_path.unlink()
        tmp_path.replace(output_path)
        print(f"PDF generado: {output_path}")
        return 0
    except Exception as exc:
        if tmp_path.exists():
            tmp_path.unlink()
        print(f"Error al generar el informe PDF: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
