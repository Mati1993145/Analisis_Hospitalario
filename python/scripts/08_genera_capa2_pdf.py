from __future__ import annotations

"""Genera el PDF de la Capa 2 del sub-estudio: 'COVID y patología psiquiátrica'.

Mide hospitalizaciones por DIAGNOSTICO CIE-10 (DEIS/MINSAL, F00-F99), a diferencia
de la Capa 1 (REM20, camas). Narrativa CERTIFICADA numero por numero contra el
notebook 04_covid_patologias_anual.ipynb. Mismo estilo visual que la Capa 1.

Cifras certificadas (notebook 04, serie 2001-2025):
  - pendiente pre-COVID (2001-2019) de egresos SM: +22,78/anio (p=0,7737, NO significativa)
  - cambio de nivel 2020: -3.177 (p=0,0135); cambio de pendiente post: +4.009/anio (p<0,001)
  - F de quiebre estructural: 211,67 (p<0,001)
  - contrafactual: brecha 2020-21 -1.702/anio; POST 2022+ +37,5% (+11.119/anio sobre lo esperado)
  - tasa por 10.000: POST +41,4% sobre lo esperado
  - diff-in-diff: salud mental +37,5% vs resto -3,6% => +41,1 pp
  - serie: 2019=32.695 egresos SM -> 2025=45.372 (+38,8%); tasa 196,1 -> 266,0 por 10.000
  - desglose pre(2015-19)->post(2022-24): F30-39 afectivos 8.330->12.898 (+54,8%, mayor alza
    absoluta); F40-48 ansiedad +52,3%; F60-69 personalidad +78,0%; F90-99 infanto +76,5%;
    F80-89 desarrollo +105,4%; F10-19 sustancias -10,2%; F70-79 discap. intel. -24,3%
"""

from pathlib import Path

from matplotlib import font_manager
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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
)

PRIMARY = "#1A1F2E"
MUTED = "#6B7280"
GRID = "#E5E7EB"
SOURCE_TEXT = "Fuente: DEIS/MINSAL, egresos hospitalarios CIE-10 · Elaboración propia"
FOOTER_TITLE = "Sub-estudio Capa 2: COVID y patología psiquiátrica · Chile 2001–2025"
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def register_fonts() -> None:
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
    s: dict[str, ParagraphStyle] = {}
    s["cover_title"] = ParagraphStyle("CoverTitle", parent=base["Title"], fontName=FONT_BOLD,
                                      fontSize=22, leading=28, alignment=TA_CENTER,
                                      textColor=colors.HexColor(PRIMARY), spaceAfter=18)
    s["cover_subtitle"] = ParagraphStyle("CoverSubtitle", parent=base["Normal"], fontName=FONT_REGULAR,
                                         fontSize=13, leading=18, alignment=TA_CENTER,
                                         textColor=colors.HexColor(PRIMARY), spaceAfter=16)
    s["cover_meta"] = ParagraphStyle("CoverMeta", parent=base["Normal"], fontName=FONT_REGULAR,
                                     fontSize=11, leading=16, alignment=TA_CENTER,
                                     textColor=colors.HexColor(MUTED))
    s["h1"] = ParagraphStyle("H1", parent=base["Heading1"], fontName=FONT_BOLD, fontSize=15,
                             leading=20, textColor=colors.HexColor(PRIMARY), spaceBefore=10, spaceAfter=8)
    s["body"] = ParagraphStyle("Body", parent=base["BodyText"], fontName=FONT_REGULAR, fontSize=10,
                               leading=14, alignment=TA_JUSTIFY, textColor=colors.HexColor(PRIMARY),
                               spaceAfter=7)
    s["caption"] = ParagraphStyle("Caption", parent=base["BodyText"], fontName=FONT_REGULAR, fontSize=8,
                                  leading=11, alignment=TA_CENTER, textColor=colors.HexColor(MUTED),
                                  spaceAfter=11)
    return s


def scaled_image(path: Path, max_width: float) -> RLImage:
    if not path.exists():
        raise FileNotFoundError(f"No existe el PNG requerido: {path}")
    with PILImage.open(path) as img:
        w, h = img.size
    return RLImage(str(path), width=max_width, height=max_width * (h / w))


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


# --- Narrativa certificada. Cada bloque: ("h1"|"p", texto) o ("fig", archivo, pie) ---
def content_blocks() -> list:
    return [
        ("h1", "1. Por qué una segunda capa"),
        ("p", "La primera capa de este sub-estudio respondió, con datos REM20, si el COVID causó el "
              "aumento de las <b>hospitalizaciones</b> por salud mental —el uso de camas psiquiátricas—. "
              "Su veredicto fue claro: <b>no</b>; esa tendencia ya venía desde 2014 y la pandemia no la "
              "creó. Pero REM20 mide camas y flujo, no <b>diagnóstico</b>: no puede decir si lo que "
              "aumentó fue la <b>patología</b> psiquiátrica, es decir, la enfermedad."),
        ("p", "Esta segunda capa ataca exactamente esa pregunta con una fuente distinta: los <b>egresos "
              "hospitalarios del DEIS/MINSAL</b>, que registran el <b>diagnóstico principal en CIE-10</b>. "
              "Aislando el capítulo V (F00–F99, trastornos mentales y del comportamiento) se obtiene una "
              "serie anual 2001–2025 de hospitalizaciones <b>por diagnóstico psiquiátrico</b>, y se le "
              "aplica el mismo criterio de quiebre de tendencia: ¿hubo un corte estructural en 2020 o la "
              "patología seguía una trayectoria previa?"),
        ("p", "Una precisión de alcance, igual de importante que en la Capa 1: un egreso con diagnóstico "
              "F mide una <b>hospitalización por trastorno mental</b>, no la <b>incidencia poblacional</b> "
              "de la enfermedad. Aun así, es un salto cualitativo respecto de REM20, porque ahora sí hay "
              "diagnóstico clínico detrás de cada caso."),

        ("h1", "2. Datos y metodología"),
        ("p", "La serie cubre <b>25 años (2001–2025)</b> e integra cerca de <b>776.000 egresos</b> con "
              "diagnóstico principal F00–F99, extraídos de los ~40 millones de egresos hospitalarios "
              "totales del período. La granularidad de la fuente es <b>anual</b> (no mensual como REM20), "
              "por lo que el análisis del quiebre es más grueso pero cubre un horizonte mucho más largo."),
        ("p", "Se replican las tres técnicas de la Capa 1, adaptadas a datos anuales: (i) <b>regresión "
              "segmentada de series temporales interrumpidas</b> con errores HAC, que estima la pendiente "
              "pre-COVID, el cambio de nivel en 2020 y el cambio de pendiente posterior; (ii) un "
              "<b>contrafactual</b> que proyecta la tendencia previa con banda de 95%; y (iii) un "
              "<b>grupo de control</b> —el resto del sistema hospitalario, no psiquiátrico— para una "
              "lectura de diferencias en diferencias. Adicionalmente se desglosa el cambio por <b>grupo "
              "diagnóstico</b>, algo que la Capa 1 no permitía."),
        ("fig", "01_serie_anual_sm.png",
         "Figura 1. Egresos por trastorno mental (F00–F99), 2001–2025. A la izquierda, valores "
         "absolutos; a la derecha, su peso sobre el total hospitalario (por 10.000 egresos). Ambos "
         "estables hasta 2019 y con un quiebre al alza tras 2020."),

        ("h1", "3. Resultado: la patología estuvo plana dos décadas y se quiebra al alza tras 2020"),
        ("p", "A diferencia de las camas, las hospitalizaciones <b>por diagnóstico</b> psiquiátrico "
              "<b>no</b> mostraban una tendencia significativa antes de la pandemia: la pendiente "
              "pre-COVID (2001–2019) fue de apenas <b>+22,8 egresos por año</b> y <b>no significativa</b> "
              "(p=0,77). Durante casi dos décadas, los egresos con diagnóstico F oscilaron sin rumbo "
              "claro en torno a 27.000–32.000 al año."),
        ("p", "El modelo detecta un <b>quiebre estructural fuerte y altamente significativo</b> coincidente "
              "con la pandemia (test F de quiebre = <b>211,7</b>; p&lt;0,001). Como en la Capa 1, 2020 "
              "trae primero una <b>caída</b> —cambio de nivel de <b>−3.177 egresos</b> (p=0,014), el "
              "colapso de la actividad hospitalaria electiva—, pero a continuación la pendiente cambia en "
              "<b>+4.009 egresos por año</b> (p&lt;0,001): un cambio de régimen, no la continuación de una "
              "tendencia previa. En cifras crudas, los egresos por trastorno mental pasan de "
              "<b>32.695 en 2019 a 45.372 en 2025 (+38,8%)</b>."),
        ("fig", "02_quiebre_tendencia_sm.png",
         "Figura 2. Egresos reales por trastorno mental frente a la tendencia pre-COVID extendida. La "
         "trayectoria previa era esencialmente plana; el alza posterior a 2020 se despega con claridad."),

        ("h1", "4. El quiebre es específico de salud mental"),
        ("p", "El contrafactual cuantifica la magnitud. Tras descontar la caída de la fase aguda "
              "—brecha media de <b>−1.702 egresos/año</b> en 2020–2021—, el período post-COVID (2022 en "
              "adelante) se ubica <b>+37,5% sobre lo esperado</b> por la tendencia previa, una brecha "
              "media de <b>+11.119 egresos por año</b>. Medido como peso sobre el total hospitalario, el "
              "exceso es aún mayor: <b>+41,4%</b> sobre lo esperado, porque el total de egresos del país "
              "no creció igual."),
        ("p", "El grupo de control confirma que el fenómeno es <b>diferencial de salud mental</b> y no un "
              "movimiento general del sistema: mientras la patología psiquiátrica quedó <b>+37,5%</b> "
              "sobre lo esperado, el resto del sistema hospitalario quedó <b>−3,6%</b>. La diferencia en "
              "diferencias es de <b>+41,1 puntos porcentuales</b> a favor de salud mental — una brecha "
              "mucho mayor que los +9,2 pp observados en la Capa 1 con datos de camas."),
        ("fig", "05_control_did_sm.png",
         "Figura 3. Egresos normalizados (base 100 = media pre-COVID): salud mental vs. resto del "
         "sistema. La divergencia tras 2020 es pronunciada y sostenida."),

        ("h1", "5. Qué patologías explican el alza"),
        ("p", "El desglose por diagnóstico —ventaja exclusiva de esta capa— muestra que el aumento no es "
              "homogéneo. En términos <b>absolutos</b>, el mayor motor son los <b>trastornos afectivos</b> "
              "(F30–F39, depresión y bipolaridad): de 8.330 egresos anuales promedio en 2015–2019 a "
              "12.898 en 2022–2024 (<b>+54,8%</b>, +4.568 egresos). Les siguen los <b>trastornos de "
              "ansiedad y estrés</b> (F40–F48, <b>+52,3%</b>)."),
        ("p", "En términos <b>relativos</b>, los mayores crecimientos están en población joven y en cuadros "
              "del desarrollo y la personalidad: trastornos del <b>desarrollo</b> (F80–F89, <b>+105,4%</b>), "
              "de la <b>personalidad</b> (F60–F69, <b>+78,0%</b>) y de <b>inicio en la infancia y "
              "adolescencia</b> (F90–F99, <b>+76,5%</b>). En contraste, dos grupos <b>cayeron</b>: los "
              "trastornos por <b>consumo de sustancias</b> (F10–F19, <b>−10,2%</b>) y la <b>discapacidad "
              "intelectual</b> (F70–F79, <b>−24,3%</b>). El patrón es coherente con un aumento de la carga "
              "de depresión, ansiedad y salud mental infanto-juvenil tras la pandemia."),
        ("fig", "06_desglose_dx.png",
         "Figura 4. Cambio porcentual en egresos por grupo diagnóstico: post-COVID (2022–2024) frente a "
         "pre-COVID (2015–2019). En rojo los que aumentan; en azul los que disminuyen."),

        ("h1", "6. Síntesis de las dos capas"),
        ("p", "Las dos capas miden cosas distintas y, juntas, dan una respuesta más honesta que cualquiera "
              "por separado. <b>Hospitalización (camas, REM20):</b> el uso de camas psiquiátricas ya "
              "crecía desde 2014; el COVID no lo causó (Capa 1). <b>Patología (diagnóstico, DEIS):</b> las "
              "hospitalizaciones con diagnóstico de trastorno mental estuvieron planas durante dos décadas "
              "y se <b>quiebran al alza justo después de 2020</b>, de forma específica de salud mental y "
              "concentrada en depresión, ansiedad y población infanto-juvenil (Capa 2)."),
        ("p", "La reconciliación es coherente: el alza de patología se expresa más en <b>flujo</b> "
              "—egresos, casos atendidos, alta rotación— que en <b>stock</b> de camas ocupadas, tal como "
              "ya anticipaba la Capa 1. Es decir, el sistema absorbió más hospitalizaciones psiquiátricas "
              "sin una expansión equivalente de camas, probablemente vía estadías más cortas y atención en "
              "hospitales generales."),
        ("p", "Respuesta a la pregunta original — <b>¿fue el COVID?</b> Depende de qué se mida. La "
              "<b>necesidad de camas</b> psiquiátricas no la creó la pandemia: es una tendencia "
              "estructural previa. Pero la <b>patología psiquiátrica hospitalizada</b> sí muestra un "
              "quiebre fuerte, significativo y específico que <b>coincide con el COVID</b> y no existía "
              "antes — la señal más sólida de un cambio asociado a la pandemia que arroja todo el estudio."),

        ("h1", "7. Salvedades y honestidad del dato"),
        ("p", "El quiebre de la Capa 2 es una <b>asociación</b> temporal fuerte, no una prueba de "
              "causalidad. La fuente mide <b>hospitalización por diagnóstico</b>, no incidencia "
              "poblacional: parte del alza podría reflejar mayor búsqueda de atención, menor estigma, "
              "cambios en los criterios de codificación o de admisión, o la expansión de programas de "
              "salud mental, además de un aumento real de la enfermedad. Distinguir estos componentes "
              "exigiría datos ambulatorios (REM serie A), licencias médicas (SUSESO) o encuestas "
              "poblacionales (ENS)."),
        ("p", "Limitaciones técnicas: la serie es <b>anual</b> (punto de interrupción fijo en 2020, sin "
              "resolución intra-anual), el contrafactual asume continuidad lineal de la tendencia previa, "
              "y la comparación se hace sobre promedios de período. Aun con esas cautelas, la magnitud del "
              "quiebre (F=211,7; +37,5% sobre lo esperado; +41,1 pp frente al control) es lo bastante "
              "grande y consistente como para tratarse de un hallazgo robusto dentro de su marco: un "
              "cambio real en las hospitalizaciones por diagnóstico psiquiátrico, coincidente con la "
              "pandemia y concentrado en cuadros específicos."),
    ]


def main() -> None:
    register_fonts()
    styles = build_styles()
    root = project_root()
    graph_dir = root / "data" / "processed" / "graficos_patologias"
    out_path = root / "data" / "processed" / "Sub-estudio_Patologia_Psiquiatrica_COVID.pdf"

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
        title="Sub-estudio Capa 2: COVID y patología psiquiátrica",
        author="Matías Durán",
    )
    max_width = A4[0] - doc.leftMargin - doc.rightMargin

    story: list = []
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph("Sub-estudio · Capa 2: COVID y patología psiquiátrica", styles["cover_title"]))
    story.append(Paragraph("¿Aumentó la enfermedad mental, o solo el uso de camas? Quiebre de tendencia "
                           "en las hospitalizaciones por diagnóstico CIE-10 (F00–F99), 2001–2025",
                           styles["cover_subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Análisis de Indicadores Hospitalarios · DEIS/MINSAL<br/>"
                           "Matías Durán · Data &amp; Business Analyst", styles["cover_meta"]))
    story.append(PageBreak())

    for block in content_blocks():
        if block[0] == "h1":
            story.append(Paragraph(block[1], styles["h1"]))
        elif block[0] == "p":
            story.append(Paragraph(block[1], styles["body"]))
        elif block[0] == "fig":
            story.append(Spacer(1, 0.2 * cm))
            story.append(scaled_image(graph_dir / block[1], max_width))
            story.append(Paragraph(block[2], styles["caption"]))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"PDF generado: {out_path}")


if __name__ == "__main__":
    main()
