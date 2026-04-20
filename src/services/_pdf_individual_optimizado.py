"""
Exportación PDF individual de profesor (versión optimizada con mini calendarios).
Extraído de exportador_pdf.py para reducir tamaño de archivo.
"""

from calendar import monthcalendar
from collections import defaultdict
from datetime import date, datetime
from typing import Callable, Optional

from infrastructure.database.models import Configuracion, Guardia, Profesor
from reportlab.graphics.shapes import Circle, Drawing, Polygon, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from services.gestor_cursos import GestorCursos
from services.pdf_styles import PDFStyles
from sqlalchemy.orm import Session, joinedload
from utils import get_logger
from services._pdf_mini_calendario import crear_mini_calendario, obtener_hora_recreo

logger = get_logger(__name__)


def exportar_profesor_individual_optimizado(
    session: Session,
    profesor_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    ruta_salida: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> bool:
    """
    Exporta calendario individual de un profesor mostrando SOLO días con guardias.
    Incluye mini calendarios mensuales con días de guardia marcados.

    Args:
        session: Sesión de base de datos
        profesor_id: ID del profesor
        fecha_inicio: Fecha inicial del periodo
        fecha_fin: Fecha final del periodo
        ruta_salida: Ruta del archivo PDF
        progress_callback: Función opcional para reportar progreso

    Returns:
        True si se generó correctamente, False en caso contrario
    """

    def reportar_progreso(porcentaje: int, mensaje: str = ""):
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Error al reportar progreso: {e}")

    try:
        reportar_progreso(0, "Preparando exportación individual...")

        # Obtener curso activo
        curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
        if not curso_activo:
            logger.warning("No hay curso activo para exportar PDF individual")
            return False

        # Obtener profesor y configuración global
        profesor = session.query(Profesor).get(profesor_id)
        config = session.query(Configuracion).first()

        if not profesor:
            return False

        reportar_progreso(10, f"Consultando guardias de {profesor.nombre_completo}...")

        # Obtener SOLO días con guardias
        guardias = (
            session.query(Guardia)
            .options(joinedload(Guardia.zona))
            .filter(
                Guardia.profesor_id == profesor_id,
                Guardia.curso_id == curso_activo.id,
                Guardia.fecha >= fecha_inicio,
                Guardia.fecha <= fecha_fin,
            )
            .order_by(Guardia.fecha, Guardia.recreo)
            .all()
        )

        if not guardias:
            reportar_progreso(100, "No hay guardias en este periodo")
            return False

        reportar_progreso(30, f"Encontradas {len(guardias)} guardias...")

        # Obtener rango real de fechas (primera y última guardia)
        fechas_guardias = sorted(set(g.fecha for g in guardias))
        primera_guardia = min(fechas_guardias)
        ultima_guardia = max(fechas_guardias)

        # Agrupar guardias por mes para mini calendarios
        # Estructura: {(año, mes): {dia: [(zona_id, recreo), ...]}}
        guardias_por_mes = defaultdict(lambda: defaultdict(list))
        zonas_usadas = set()
        recreos_usados = set()

        for guardia in guardias:
            año_mes = (guardia.fecha.year, guardia.fecha.month)
            dia = guardia.fecha.day
            zona_id = guardia.zona.id if guardia.zona else None

            guardias_por_mes[año_mes][dia].append((zona_id, guardia.recreo))

            if zona_id:
                zonas_usadas.add(zona_id)
            recreos_usados.add(guardia.recreo)

        # Crear PDF con márgenes reducidos para aprovechar espacio
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=landscape(A4),
            rightMargin=1 * cm,
            leftMargin=1 * cm,
            topMargin=1 * cm,
            bottomMargin=1 * cm,
        )

        elements = []
        styles = getSampleStyleSheet()

        # ===== ENCABEZADO VISUAL MEJORADO =====
        ancho_pagina = landscape(A4)[0] - 2 * cm
        altura_banner = 2.5 * cm

        banner = Drawing(ancho_pagina, altura_banner)

        fondo = Rect(
            0,
            0,
            ancho_pagina,
            altura_banner,
            fillColor=PDFStyles.AZUL_PRINCIPAL,
            strokeColor=None,
        )
        banner.add(fondo)

        borde = Rect(
            0, 0, ancho_pagina, 0.3 * cm, fillColor=PDFStyles.AZUL_OSCURO, strokeColor=None
        )
        banner.add(borde)

        titulo_texto = String(
            ancho_pagina / 2,
            altura_banner - 0.8 * cm,
            "CALENDARIO PERSONAL DE GUARDIAS",
            fontSize=PDFStyles.TAMANO_TITULO_PRINCIPAL,
            fontName=PDFStyles.FUENTE_TITULO,
            textAnchor="middle",
            fillColor=colors.whitesmoke,
        )
        banner.add(titulo_texto)

        nombre_texto = String(
            ancho_pagina / 2,
            altura_banner - 1.5 * cm,
            profesor.nombre_completo.upper(),
            fontSize=PDFStyles.TAMANO_SUBTITULO,
            fontName=PDFStyles.FUENTE_TITULO,
            textAnchor="middle",
            fillColor=PDFStyles.COLOR_DATO_PRINCIPAL,
        )
        banner.add(nombre_texto)

        turno_valor = profesor.turno.capitalize()
        tutor_valor = "Si" if profesor.tutor else "No"
        periodo_inicio = primera_guardia.strftime("%d/%m/%Y")
        periodo_fin = ultima_guardia.strftime("%d/%m/%Y")

        linea_info = String(
            ancho_pagina / 2,
            altura_banner - 2.1 * cm,
            f"Turno: {turno_valor}     Tutor: {tutor_valor}     "
            f"Periodo: {periodo_inicio} - {periodo_fin}",
            fontSize=9,
            fontName="Helvetica",
            textAnchor="middle",
            fillColor=colors.whitesmoke,
        )
        banner.add(linea_info)

        elements.append(banner)
        elements.append(Spacer(1, 0.8 * cm))

        reportar_progreso(40, "Generando mini calendarios...")

        # Mini calendarios mensuales - PÁGINA DEDICADA
        meses_ordenados = sorted(guardias_por_mes.keys())
        if meses_ordenados:
            num_meses = len(meses_ordenados)

            if num_meses <= 6:
                cal_por_fila = 3
                ancho_cal = 8 * cm
                alto_cal = 6.5 * cm
            elif num_meses <= 10:
                cal_por_fila = 5
                ancho_cal = 5 * cm
                alto_cal = 4.2 * cm
            else:
                cal_por_fila = 4
                ancho_cal = 6.5 * cm
                alto_cal = 5 * cm

            calendarios = []
            for anio, mes in meses_ordenados:
                guardias_del_mes = guardias_por_mes[(anio, mes)]
                mini_cal = crear_mini_calendario(
                    mes, anio, guardias_del_mes, ancho=ancho_cal, alto=alto_cal
                )
                calendarios.append(mini_cal)

            filas_calendarios = []
            for i in range(0, len(calendarios), cal_por_fila):
                fila = calendarios[i : i + cal_por_fila]
                while len(fila) < cal_por_fila:
                    fila.append(Spacer(ancho_cal, alto_cal))
                filas_calendarios.append(fila)

            if filas_calendarios:
                ancho_columna = ancho_cal + 0.4 * cm
                tabla_calendarios = Table(
                    filas_calendarios, colWidths=[ancho_columna] * cal_por_fila
                )
                tabla_calendarios.setStyle(
                    TableStyle(
                        [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 4),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                            ("TOPPADDING", (0, 0), (-1, -1), 4),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    )
                )
                elements.append(tabla_calendarios)
                elements.append(Spacer(1, 0.3 * cm))

            # Crear leyenda compacta
            reportar_progreso(45, "Generando leyenda...")

            def crear_leyenda():
                """Crea la leyenda de colores y formas de forma compacta."""
                leyenda_ancho = 27 * cm
                leyenda_alto = 0.9 * cm
                leyenda_drawing = Drawing(leyenda_ancho, leyenda_alto)

                marco = Rect(
                    0,
                    0,
                    leyenda_ancho,
                    leyenda_alto,
                    fillColor=PDFStyles.FONDO_CLARO,
                    strokeColor=colors.HexColor("#dee2e6"),
                    strokeWidth=1,
                )
                leyenda_drawing.add(marco)

                y_pos = leyenda_alto / 2 - 0.05 * cm

                x_pos = 0.3 * cm
                texto = String(
                    x_pos,
                    y_pos,
                    "Recreos:",
                    fontSize=7,
                    fontName="Helvetica-Bold",
                    textAnchor="start",
                )
                leyenda_drawing.add(texto)

                x_pos = 1.5 * cm
                recreos_ordenados = sorted(recreos_usados)
                for recreo in recreos_ordenados:
                    if recreo == 1:
                        circulo = Circle(
                            x_pos,
                            y_pos + 0.08 * cm,
                            0.08 * cm,
                            fillColor=colors.grey,
                            strokeColor=colors.grey,
                        )
                        leyenda_drawing.add(circulo)
                        forma_nombre = "●=R1"
                    elif recreo == 2:
                        cuadrado = Rect(
                            x_pos - 0.08 * cm,
                            y_pos,
                            0.16 * cm,
                            0.16 * cm,
                            fillColor=colors.grey,
                            strokeColor=colors.grey,
                        )
                        leyenda_drawing.add(cuadrado)
                        forma_nombre = "■=R2"
                    elif recreo == 3:
                        puntos = [
                            x_pos,
                            y_pos + 0.18 * cm,
                            x_pos - 0.08 * cm,
                            y_pos,
                            x_pos + 0.08 * cm,
                            y_pos,
                        ]
                        triangulo = Polygon(
                            puntos, fillColor=colors.grey, strokeColor=colors.grey
                        )
                        leyenda_drawing.add(triangulo)
                        forma_nombre = "▲=R3"
                    else:
                        puntos = [
                            x_pos,
                            y_pos + 0.12 * cm,
                            x_pos + 0.08 * cm,
                            y_pos + 0.04 * cm,
                            x_pos,
                            y_pos - 0.04 * cm,
                            x_pos - 0.08 * cm,
                            y_pos + 0.04 * cm,
                        ]
                        rombo = Polygon(puntos, fillColor=colors.grey, strokeColor=colors.grey)
                        leyenda_drawing.add(rombo)
                        forma_nombre = f"◆=R{recreo}"

                    texto = String(
                        x_pos + 0.22 * cm,
                        y_pos,
                        forma_nombre,
                        fontSize=6,
                        fontName="Helvetica",
                        textAnchor="start",
                    )
                    leyenda_drawing.add(texto)
                    x_pos += 1.2 * cm

                x_pos += 0.3 * cm
                sep = Rect(
                    x_pos,
                    0.1 * cm,
                    0.02 * cm,
                    leyenda_alto - 0.2 * cm,
                    fillColor=colors.HexColor("#dee2e6"),
                    strokeColor=None,
                )
                leyenda_drawing.add(sep)
                x_pos += 0.3 * cm

                texto = String(
                    x_pos,
                    y_pos,
                    "Zonas:",
                    fontSize=7,
                    fontName="Helvetica-Bold",
                    textAnchor="start",
                )
                leyenda_drawing.add(texto)
                x_pos += 1.2 * cm

                zonas_info = {}
                for zona_id in sorted(zonas_usadas):
                    for g in guardias:
                        if g.zona and g.zona.id == zona_id:
                            zonas_info[zona_id] = g.zona.nombre_zona
                            break

                for zona_id in sorted(zonas_usadas)[:10]:
                    color = PDFStyles.get_color_zona(zona_id)

                    cuadrado = Rect(
                        x_pos - 0.06 * cm,
                        y_pos,
                        0.16 * cm,
                        0.16 * cm,
                        fillColor=color,
                        strokeColor=color,
                    )
                    leyenda_drawing.add(cuadrado)

                    zona_nombre = zonas_info.get(zona_id, f"Z{zona_id}")
                    texto = String(
                        x_pos + 0.15 * cm,
                        y_pos,
                        zona_nombre,
                        fontSize=6,
                        fontName="Helvetica",
                        textAnchor="start",
                    )
                    leyenda_drawing.add(texto)
                    x_pos += 1.8 * cm

                return leyenda_drawing

            leyenda = crear_leyenda()
            elements.append(leyenda)

            elements.append(PageBreak())

        reportar_progreso(50, "Generando tabla de guardias...")

        # Agrupar por fecha Y por mes
        guardias_por_fecha = defaultdict(list)
        guardias_por_mes = defaultdict(list)
        for g in guardias:
            guardias_por_fecha[g.fecha].append(g)
            mes_anio = (g.fecha.year, g.fecha.month)
            guardias_por_mes[mes_anio].append(g)

        data = [["Fecha", "Día", "Turno", "Recreo - Hora", "Zona - Descripción"]]
        dias_semana = PDFStyles.get_dias_semana_completos()

        estilos_filas = []
        fila_actual = 1

        meses_ordenados = sorted(guardias_por_mes.keys())

        for idx_mes, (anio, mes) in enumerate(meses_ordenados):
            fechas_del_mes = sorted(
                [f for f in fechas_guardias if f.year == anio and f.month == mes]
            )

            color_fondo_mes = PDFStyles.get_color_mes(idx_mes)

            for fecha in fechas_del_mes:
                guardias_dia = guardias_por_fecha[fecha]

                for i, guardia in enumerate(guardias_dia):
                    fecha_str = fecha.strftime("%d/%m/%Y") if i == 0 else ""
                    dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""

                    if guardia.zona:
                        if guardia.zona.descripcion:
                            zona_nombre = guardia.zona.nombre_zona
                            zona_desc = guardia.zona.descripcion
                            zona_info = f"{zona_nombre} - {zona_desc}"
                        else:
                            zona_info = guardia.zona.nombre_zona
                    else:
                        zona_info = "N/A"

                    if config:
                        hora = obtener_hora_recreo(config, guardia.turno, guardia.recreo)
                    else:
                        hora = ""
                    if hora:
                        recreo_info = f"Recreo {guardia.recreo} ({hora})"
                    else:
                        recreo_info = f"Recreo {guardia.recreo}"

                    data.append(
                        [
                            fecha_str,
                            dia_semana,
                            guardia.turno.capitalize(),
                            recreo_info,
                            zona_info,
                        ]
                    )

                    estilos_filas.append(
                        ("BACKGROUND", (0, fila_actual), (-1, fila_actual), color_fondo_mes)
                    )

                    color_recreo = PDFStyles.get_color_recreo(guardia.recreo)
                    estilos_filas.append(
                        ("TEXTCOLOR", (3, fila_actual), (3, fila_actual), color_recreo)
                    )
                    estilos_filas.append(
                        ("FONTNAME", (3, fila_actual), (3, fila_actual), "Helvetica-Bold")
                    )

                    if guardia.zona:
                        color_zona = PDFStyles.get_color_zona(guardia.zona.id)
                        estilos_filas.append(
                            ("TEXTCOLOR", (4, fila_actual), (4, fila_actual), color_zona)
                        )
                        estilos_filas.append(
                            ("FONTNAME", (4, fila_actual), (4, fila_actual), "Helvetica-Bold")
                        )

                    fila_actual += 1

            if idx_mes < len(meses_ordenados) - 1:
                estilos_filas.append(
                    (
                        "LINEBELOW",
                        (0, fila_actual - 1),
                        (-1, fila_actual - 1),
                        3,
                        PDFStyles.AZUL_PRINCIPAL,
                    )
                )

        tabla = Table(data, colWidths=[3 * cm, 3 * cm, 2.5 * cm, 4 * cm, 9 * cm])

        estilos_base = [
            ("BACKGROUND", (0, 0), (-1, 0), PDFStyles.FONDO_TABLA_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), PDFStyles.FUENTE_NEGRITA),
            ("FONTSIZE", (0, 0), (-1, 0), PDFStyles.TAMANO_ENCABEZADO_TABLA),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
            ("TEXTCOLOR", (0, 1), (2, -1), PDFStyles.TEXTO_OSCURO),
            ("FONTNAME", (0, 1), (-1, -1), PDFStyles.FUENTE_NORMAL),
            ("FONTSIZE", (0, 1), (-1, -1), PDFStyles.TAMANO_CUERPO_TABLA),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ]

        tabla.setStyle(TableStyle(estilos_base + estilos_filas))

        elements.append(tabla)

        reportar_progreso(80, "Generando estadísticas...")

        elements.append(Spacer(1, 1 * cm))

        resumen_style = ParagraphStyle(
            "ResumenIndividual",
            parent=styles["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#2c3e50"),
        )

        total_guardias = len(guardias)
        dias_con_guardias = len(fechas_guardias)
        guardias_manana = len([g for g in guardias if g.turno == "mañana"])
        guardias_tarde = len([g for g in guardias if g.turno == "tarde"])

        zonas_contador = defaultdict(int)
        for g in guardias:
            if g.zona:
                zonas_contador[g.zona.nombre_zona] += 1

        if zonas_contador:
            zona_mas_frecuente = max(zonas_contador.items(), key=lambda x: x[1])
        else:
            zona_mas_frecuente = ("N/A", 0)

        resumen_text = f"""
        <b>📊 Resumen Estadístico:</b><br/>
        • Total de guardias: {total_guardias}<br/>
        • Días con guardias: {dias_con_guardias}<br/>
        • Guardias de mañana: {guardias_manana}<br/>
        • Guardias de tarde: {guardias_tarde}<br/>
        • Zona más frecuente: {zona_mas_frecuente[0]} ({zona_mas_frecuente[1]} guardias)<br/>
        • Promedio de guardias por día: {total_guardias / dias_con_guardias:.1f}
        """

        resumen = Paragraph(resumen_text, resumen_style)
        elements.append(resumen)

        elements.append(Spacer(1, 1 * cm))

        footer_style = ParagraphStyle(
            "FooterIndividual",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=2,
        )

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        footer = Paragraph(f"Documento generado el {fecha_generacion}", footer_style)
        elements.append(footer)

        reportar_progreso(95, "Construyendo PDF...")

        doc.build(elements)

        reportar_progreso(100, "PDF generado exitosamente")
        return True

    except (ValueError, TypeError, OSError) as e:
        logger.error(f"Error al exportar profesor individual: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return False
