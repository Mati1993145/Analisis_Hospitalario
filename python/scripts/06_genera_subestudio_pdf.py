from __future__ import annotations

"""Genera el PDF independiente del sub-estudio 'COVID y hospitalización psiquiátrica'.

Narrativa redactada por Codex y CERTIFICADA número por número contra el notebook
03_covid_psiquiatria_quiebre.ipynb y la sección HALLAZGOS - SALUD MENTAL Y COVID de
BITACORA.md (Fase 9B). Mismo estilo visual que el informe principal.
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
SOURCE_TEXT = "Fuente: MINSAL REM20 · Elaboración propia"
FOOTER_TITLE = "Sub-estudio: Salud Mental y COVID · Chile 2014–2026"
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


# --- Narrativa certificada (Fase 9B). Cada bloque: ("h1"|"p", texto) o ("fig", archivo, pie) ---
def content_blocks() -> list:
    return [
        ("h1", "1. Pregunta de investigación"),
        ("p", "Este sub-estudio evalúa si el aumento observado en los egresos de hospitalización "
              "psiquiátrica clínica puede atribuirse al COVID, o si corresponde a una trayectoria "
              "previa del sistema que ya venía en desarrollo antes de la pandemia. La pregunta no es "
              "si la pandemia afectó la operación hospitalaria —sí lo hizo—, sino si explica "
              "causalmente el alza posterior de hospitalizaciones psiquiátricas."),
        ("p", "La fuente utilizada corresponde a <b>rem20.indicadores</b> del MINSAL REM20, con serie "
              "mensual entre 2014-01 y 2026-05, con 149 meses observados y 0 huecos. En el segmento "
              "psiquiátrico clínico, los egresos presentan una media cercana a 1.143 por mes, con "
              "mínimo de 686 y máximo de 1.652. La ocupación media de camas fue de 87,2%. El año 2026 "
              "debe leerse como año parcial."),
        ("fig", "01_series_egresos_zonas.png",
         "Figura 1. Serie mensual de egresos psiquiátricos: tendencia ascendente previa a marzo de "
         "2020, caída inicial durante el período COVID y recuperación posterior."),

        ("h1", "2. Metodología"),
        ("p", "El análisis utiliza tres aproximaciones complementarias. Primero, una <b>regresión "
              "segmentada de series temporales interrumpidas</b>, que estima la tendencia previa a "
              "marzo de 2020, el cambio inmediato de nivel en ese punto y la pendiente posterior, "
              "controlando la estacionalidad mensual. Para robustecer la inferencia temporal se "
              "usaron errores HAC, adecuados cuando los datos mensuales pueden presentar "
              "autocorrelación o variación no constante."),
        ("p", "Segundo, se construyó un <b>contrafactual</b>: una extensión de la tendencia pre-COVID "
              "con banda de 95%. Esta comparación permite estimar cuánto se apartaron los egresos "
              "reales de lo que se habría esperado si la trayectoria observada hasta febrero de 2020 "
              "hubiese continuado sin interrupción."),
        ("p", "Tercero, se incorporó un <b>grupo de control</b> mediante diferencias en diferencias, "
              "comparando la evolución de psiquiatría clínica con el resto del sistema no "
              "psiquiátrico. Esta lectura no prueba causalidad clínica, pero ayuda a distinguir si el "
              "patrón post-COVID fue general del sistema hospitalario o diferencial del segmento "
              "psiquiátrico."),
        ("fig", "02_quiebre_tendencia.png",
         "Figura 2. Egresos reales frente a la tendencia pre-COVID extendida: el aumento posterior se "
         "monta sobre una trayectoria ascendente ya existente."),

        ("h1", "3. Veredicto: no fue el COVID; la tendencia ya venía desde 2014"),
        ("p", "El veredicto técnico es claro: el COVID no fue la causa del aumento de hospitalización "
              "psiquiátrica. La evidencia principal es que los egresos psiquiátricos ya venían "
              "aumentando antes de la pandemia, con una pendiente pre-COVID de <b>+30 egresos por mes "
              "por año</b> (exactamente +29,97; p&lt;0,0001). Por lo tanto, el crecimiento no comienza "
              "en marzo de 2020."),
        ("p", "Además, el quiebre de marzo de 2020 no produjo un salto positivo en egresos. Por el "
              "contrario, el modelo estima un cambio inmediato de nivel de <b>−310 egresos por mes</b> "
              "(exactamente −309,97; p&lt;0,0001). En términos operacionales, el COVID primero hundió "
              "los egresos psiquiátricos, coherente con una disrupción de la actividad hospitalaria y "
              "no con un aumento inicial de hospitalización."),
        ("p", "La pendiente posterior sí fue más empinada que la tendencia previa: el cambio de "
              "pendiente post-COVID fue de <b>+89 al año</b> (exactamente +88,66; p&lt;0,0001). Sin "
              "embargo, esto debe interpretarse como recuperación y aceleración relativa respecto de "
              "una tendencia que ya existía, no como prueba de que el COVID haya causado el aumento "
              "estructural."),
        ("fig", "03_contrafactual_egresos.png",
         "Figura 3. Contrafactual de egresos: brecha negativa durante 2020-2021 y brecha positiva "
         "moderada desde 2022, sin alterar que la tendencia ascendente era previa."),

        ("h1", "4. Matices"),
        ("p", "El primer matiz es la <b>caída inicial de 2020-2021</b>. Frente al contrafactual "
              "construido desde la tendencia pre-COVID, la brecha media fue de <b>−249 egresos por "
              "mes</b> durante 2020-2021. Este resultado es central: si el COVID hubiese sido el "
              "origen directo del alza, se esperaría un aumento inicial, pero lo observado fue una "
              "contracción importante del flujo de egresos."),
        ("p", "El segundo matiz es el <b>rebote diferencial posterior a 2022</b>. En el período "
              "2022-2026, psiquiatría clínica se ubicó <b>+4,0% sobre lo esperado</b> por la tendencia "
              "previa, equivalente a una brecha media de +51 egresos por mes. En comparación, el resto "
              "del sistema no psiquiátrico quedó −5,2% por debajo de lo esperado. La diferencia en "
              "diferencias fue de <b>+9,2 puntos porcentuales</b> a favor de psiquiatría. Esto indica "
              "un desempeño post-COVID diferencial del segmento, pero no transforma a la pandemia en "
              "causa del aumento de largo plazo."),
        ("fig", "05_control_did.png",
         "Figura 4. Egresos normalizados (base 100 = media pre-COVID): desde 2022 psiquiatría clínica "
         "supera su trayectoria previa mientras el resto del sistema permanece por debajo de lo esperado."),
        ("p", "El tercer matiz es la <b>diferencia entre flujo y stock</b>. Los egresos miden rotación "
              "o volumen de salida hospitalaria; la ocupación de camas mide presión instalada sobre el "
              "stock disponible. En ocupación, la pendiente pre-COVID fue plana y no significativa "
              "(+0,05 puntos por año; p=0,62). En marzo de 2020 cayó −11,7 puntos y, en el período "
              "post-COVID, se mantiene −2,6% por debajo de lo esperado. Por lo tanto, la presión de "
              "camas no muestra un alza sostenida."),
        ("p", "Esta distinción es clave para la gestión: el aumento se observa principalmente en "
              "<b>flujo de egresos</b>, no en camas ocupadas. El patrón es compatible con mayor "
              "rotación o cambios en el funcionamiento de la corta estadía, más que con una expansión "
              "sostenida del stock ocupado."),
        ("fig", "04_contrafactual_ocupacion.png",
         "Figura 5. La ocupación de camas no reproduce el alza de egresos; tras la caída de marzo de "
         "2020 permanece por debajo de lo esperado en el período post-COVID."),

        ("h1", "5. Salvedad metodológica"),
        ("p", "REM20 mide volumen y flujo de actividad hospitalaria, no diagnóstico clínico individual "
              "por patología. Por tanto, este análisis no permite afirmar qué cuadros clínicos "
              "específicos explican los egresos ni establecer causalidad clínica a nivel de paciente."),
        ("p", "El análisis es agregado, con punto de interrupción fijo en marzo de 2020. El "
              "contrafactual utilizado es lineal y proyecta la tendencia pre-COVID bajo ese supuesto. "
              "Además, 2026 corresponde a un año parcial, por lo que debe interpretarse con cautela al "
              "comparar períodos completos y parciales."),
        ("p", "La conclusión debe entenderse en ese marco: el estudio identifica patrones temporales y "
              "diferencias agregadas de flujo hospitalario, pero no afirma causalidad clínica. En "
              "particular, no se sostiene que el COVID haya provocado el aumento de hospitalización "
              "psiquiátrica."),

        ("h1", "6. Lectura de salud pública"),
        ("p", "La necesidad de hospitalización psiquiátrica parece responder a una <b>dinámica "
              "estructural de largo plazo</b>, no a un shock pandémico como origen del aumento. La "
              "tendencia ascendente ya estaba presente desde 2014 y debe ser considerada como base "
              "para la planificación de capacidad."),
        ("p", "La planificación no debería apoyarse exclusivamente en la experiencia del período "
              "COVID, porque ese período incluyó una caída operacional inicial y una recuperación "
              "posterior. Una lectura más estable debe considerar la trayectoria completa 2014-2026, "
              "distinguiendo el efecto de interrupción transitoria de la tendencia de fondo."),
        ("p", "Finalmente, dado que el crecimiento se expresa más claramente en egresos que en "
              "ocupación de camas, la respuesta no debería limitarse a agregar camas. El patrón "
              "sugiere reforzar los dispositivos ambulatorios, la continuidad de cuidados, la "
              "coordinación del egreso y los soportes post-alta, junto con revisar la capacidad "
              "hospitalaria cuando corresponda. El foco técnico no es solo aumentar stock, sino "
              "gestionar mejor el flujo asistencial de corta estadía."),
    ]


def main() -> None:
    register_fonts()
    styles = build_styles()
    root = project_root()
    graph_dir = root / "data" / "processed" / "graficos_salud_mental"
    out_path = root / "data" / "processed" / "Sub-estudio_Salud_Mental_COVID.pdf"

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
        title="Sub-estudio: COVID y hospitalización psiquiátrica",
        author="Matías Durán",
    )
    max_width = A4[0] - doc.leftMargin - doc.rightMargin

    story: list = []
    # Portada
    story.append(Spacer(1, 5 * cm))
    story.append(Paragraph("Sub-estudio: COVID y hospitalización psiquiátrica", styles["cover_title"]))
    story.append(Paragraph("¿Causó la pandemia el aumento? Análisis de quiebre de tendencia "
                           "(2014–2026)", styles["cover_subtitle"]))
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph("Análisis de Indicadores Hospitalarios · MINSAL REM20<br/>"
                           "Matías Durán · Data &amp; Business Analyst", styles["cover_meta"]))
    story.append(PageBreak())

    # Cuerpo
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
