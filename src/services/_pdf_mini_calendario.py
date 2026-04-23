"""
Helpers de generación de PDF individual para VistaCalendario.

Extraído de _pdf_individual_optimizado.py para reducir su tamaño (ARQ-05).
"""

from calendar import monthcalendar

from reportlab.graphics.shapes import Circle, Drawing, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph

from infrastructure.database.models import Configuracion
from services.pdf_styles import PDFStyles
from utils import get_logger

logger = get_logger(__name__)

def crear_mini_calendario(
    mes: int, anio: int, guardias_del_mes: dict, ancho=4 * cm, alto=3.5 * cm
):
    """
    Crea un mini calendario mensual con días marcados según zona y recreo.

    Args:
        mes: Número del mes (1-12)
        anio: Año
        guardias_del_mes: Dict con estructura {dia: [(zona_id, recreo), ...]}
        ancho: Ancho del calendario
        alto: Alto del calendario

    Returns:
        Drawing con el calendario
    """
    drawing = Drawing(ancho, alto)

    # Marco del calendario
    marco = Rect(
        0,
        0,
        ancho,
        alto,
        fillColor=None,
        strokeColor=colors.HexColor("#2c3e50"),
        strokeWidth=1.5,
    )
    drawing.add(marco)

    # Calcular proporciones en base al tamaño
    header_height = alto * 0.16  # 16% del alto para encabezado

    # Fondo del encabezado
    fondo_encabezado = Rect(
        0,
        alto - header_height,
        ancho,
        header_height,
        fillColor=colors.HexColor("#ecf0f1"),
        strokeColor=None,
    )
    drawing.add(fondo_encabezado)

    # Título del mes (tamaño de fuente proporcional)
    meses_nombres = [
        "",
        "Enero",
        "Feb",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Sept",
        "Oct",
        "Nov",
        "Dic",
    ]
    font_size_titulo = max(8, min(14, int(ancho / cm * 1.8)))  # Escala: ~7-14pt
    titulo = String(
        ancho / 2,
        alto - header_height * 0.6,
        f"{meses_nombres[mes]} {anio}",
        fontSize=font_size_titulo,
        fontName="Helvetica-Bold",
        textAnchor="middle",
    )
    drawing.add(titulo)

    # Encabezados de días
    dias_sem = ["L", "M", "X", "J", "V", "S", "D"]
    celda_ancho = ancho / 7
    celda_alto = (alto - header_height * 1.1) / 7  # 6 semanas + encabezado

    font_size_dias = max(6, min(10, int(ancho / cm * 1.4)))  # Escala: ~6-10pt
    y = alto - header_height - celda_alto * 0.3
    for i, dia in enumerate(dias_sem):
        x = i * celda_ancho + celda_ancho / 2
        texto = String(
            x,
            y,
            dia,
            fontSize=font_size_dias,
            fontName="Helvetica-Bold",
            textAnchor="middle",
        )
        drawing.add(texto)

    def obtener_color_zona(zona_id):
        """Obtiene el color para una zona específica."""
        return PDFStyles.get_color_zona(zona_id)

    def dibujar_forma_recreo(x_centro, y_centro, recreo, color, tamano=None):
        """Dibuja la forma correspondiente al recreo con tamaño proporcional."""
        if tamano is None:
            tamano = min(celda_ancho, celda_alto) * 0.25  # 25% del tamaño de celda

        if recreo == 1:
            circulo = Circle(x_centro, y_centro, tamano, fillColor=color, strokeColor=color)
            drawing.add(circulo)
        elif recreo == 2:
            cuadrado = Rect(
                x_centro - tamano,
                y_centro - tamano,
                tamano * 2,
                tamano * 2,
                fillColor=color,
                strokeColor=color,
            )
            drawing.add(cuadrado)
        elif recreo == 3:
            puntos = [
                x_centro,
                y_centro + tamano * 1.2,
                x_centro - tamano,
                y_centro - tamano * 0.6,
                x_centro + tamano,
                y_centro - tamano * 0.6,
            ]
            triangulo = Polygon(puntos, fillColor=color, strokeColor=color)
            drawing.add(triangulo)
        else:
            puntos = [
                x_centro,
                y_centro + tamano,
                x_centro + tamano,
                y_centro,
                x_centro,
                y_centro - tamano,
                x_centro - tamano,
                y_centro,
            ]
            rombo = Polygon(puntos, fillColor=color, strokeColor=color)
            drawing.add(rombo)

    # Días del mes
    calendario = monthcalendar(anio, mes)
    font_size_numeros = max(6, min(12, int(ancho / cm * 2)))  # Escala: ~6-12pt
    y = alto - header_height - celda_alto * 0.7

    for semana in calendario:
        y -= celda_alto
        for i, dia in enumerate(semana):
            if dia == 0:
                continue

            x = i * celda_ancho

            # Si el día tiene guardias
            if dia in guardias_del_mes:
                guardias_dia = guardias_del_mes[dia]

                num_guardias = len(guardias_dia)

                if num_guardias == 1:
                    zona_id, recreo = guardias_dia[0]
                    color = obtener_color_zona(zona_id)
                    dibujar_forma_recreo(x + celda_ancho / 2, y + celda_alto / 2, recreo, color)

                elif num_guardias == 2:
                    for idx, (zona_id, recreo) in enumerate(guardias_dia):
                        color = obtener_color_zona(zona_id)
                        x_pos = x + celda_ancho / 3 if idx == 0 else x + 2 * celda_ancho / 3
                        dibujar_forma_recreo(x_pos, y + celda_alto / 2, recreo, color)

                elif num_guardias == 3:
                    tamano_reducido = min(celda_ancho, celda_alto) * 0.20
                    for idx, (zona_id, recreo) in enumerate(guardias_dia):
                        color = obtener_color_zona(zona_id)
                        if idx == 0:
                            x_pos, y_pos = x + celda_ancho / 2, y + celda_alto * 0.7
                        elif idx == 1:
                            x_pos, y_pos = x + celda_ancho / 3, y + celda_alto * 0.3
                        else:
                            x_pos, y_pos = x + 2 * celda_ancho / 3, y + celda_alto * 0.3
                        dibujar_forma_recreo(
                            x_pos, y_pos, recreo, color, tamano=tamano_reducido
                        )

                else:
                    tamano_mini = min(celda_ancho, celda_alto) * 0.15
                    for idx, (zona_id, recreo) in enumerate(guardias_dia[:4]):
                        color = obtener_color_zona(zona_id)
                        if idx == 0:
                            x_pos, y_pos = x + celda_ancho / 3, y + celda_alto * 0.7
                        elif idx == 1:
                            x_pos, y_pos = x + 2 * celda_ancho / 3, y + celda_alto * 0.7
                        elif idx == 2:
                            x_pos, y_pos = x + celda_ancho / 3, y + celda_alto * 0.3
                        else:
                            x_pos, y_pos = x + 2 * celda_ancho / 3, y + celda_alto * 0.3
                        dibujar_forma_recreo(
                            x_pos, y_pos, recreo, color, tamano=tamano_mini
                        )

                # Número del día en negro y más pequeño
                texto = String(
                    x + celda_ancho / 2,
                    y + celda_alto / 8,
                    str(dia),
                    fontSize=font_size_numeros - 1,
                    fontName="Helvetica-Bold",
                    textAnchor="middle",
                    fillColor=colors.black,
                )
            else:
                # Número normal para días sin guardias
                texto = String(
                    x + celda_ancho / 2,
                    y + celda_alto / 3,
                    str(dia),
                    fontSize=font_size_numeros,
                    fontName="Helvetica",
                    textAnchor="middle",
                )

            drawing.add(texto)

    return drawing





def obtener_hora_recreo(config: Configuracion, turno: str, recreo: int) -> str:
    """Obtiene la hora formateada del recreo."""
    try:
        if turno == "mañana":
            if recreo == 1 and config.hora_recreo1_manana:
                return config.hora_recreo1_manana.strftime("%H:%M")
            elif recreo == 2 and config.hora_recreo2_manana:
                return config.hora_recreo2_manana.strftime("%H:%M")
        elif turno == "tarde":
            if recreo == 1 and config.hora_recreo1_tarde:
                return config.hora_recreo1_tarde.strftime("%H:%M")
            elif recreo == 2 and config.hora_recreo2_tarde:
                return config.hora_recreo2_tarde.strftime("%H:%M")
    except (ValueError, TypeError, OSError) as e:
        logger.debug(f"No se pudo obtener hora de recreo ({turno}, recreo {recreo}): {e}")
    return ""



