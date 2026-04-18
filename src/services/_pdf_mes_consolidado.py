"""
Exportación PDF consolidada: vista mensual y curso completo.
Extraído de exportador_pdf.py para reducir tamaño de archivo.
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Optional

from infrastructure.database.models import Guardia, Profesor
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from services.gestor_cursos import GestorCursos
from sqlalchemy.orm import Session, joinedload
from utils import get_logger

logger = get_logger(__name__)


def exportar_mes_consolidado(
    session: Session,
    mes: int,
    anio: int,
    ruta_salida: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> bool:
    """
    Exporta un PDF consolidado con todas las guardias del mes.
    Muestra todos los profesores que tienen guardia cada día, organizados por fecha.

    Args:
        session: Sesión de base de datos
        mes: Mes (1-12)
        anio: Año
        ruta_salida: Ruta del archivo PDF a generar
        progress_callback: Función opcional para reportar progreso

    Returns:
        True si se generó correctamente, False en caso contrario
    """

    def reportar_progreso(porcentaje: int, mensaje: str = ""):
        """Helper para reportar progreso de forma segura."""
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error al reportar progreso: {e}")

    try:
        reportar_progreso(0, "Preparando exportación consolidada del mes...")

        # Obtener curso activo
        curso_activo = GestorCursos.obtener_curso_activo(session)
        if not curso_activo:
            logger.warning("No hay curso activo para exportar PDF consolidado")
            return False

        # Obtener guardias del mes
        primer_dia = date(anio, mes, 1)
        dias_en_mes = monthrange(anio, mes)[1]
        ultimo_dia = date(anio, mes, dias_en_mes)

        reportar_progreso(20, "Consultando guardias del mes...")

        guardias = (
            session.query(Guardia)
            .options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
            .filter(
                Guardia.curso_id == curso_activo.id,
                Guardia.fecha >= primer_dia,
                Guardia.fecha <= ultimo_dia,
            )
            .order_by(Guardia.fecha, Guardia.turno, Guardia.recreo, Guardia.profesor_id)
            .all()
        )

        if not guardias:
            reportar_progreso(100, "No hay guardias en este mes")
            return False

        reportar_progreso(40, f"Procesando {len(guardias)} guardias...")

        # Agrupar por fecha
        guardias_por_fecha = defaultdict(list)
        for g in guardias:
            guardias_por_fecha[g.fecha].append(g)

        # Crear PDF
        doc = SimpleDocTemplate(
            ruta_salida,
            pagesize=landscape(A4),
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements = []
        styles_doc = getSampleStyleSheet()

        reportar_progreso(50, "Generando documento PDF...")

        # Título
        meses = [
            "ENERO",
            "FEBRERO",
            "MARZO",
            "ABRIL",
            "MAYO",
            "JUNIO",
            "JULIO",
            "AGOSTO",
            "SEPTIEMBRE",
            "OCTUBRE",
            "NOVIEMBRE",
            "DICIEMBRE",
        ]

        titulo_style = ParagraphStyle(
            "CustomTitle",
            parent=styles_doc["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=10,
            alignment=1,
            fontName="Helvetica-Bold",
        )

        titulo = Paragraph(f"📅 CALENDARIO DE GUARDIAS - {meses[mes - 1]} {anio}", titulo_style)
        elements.append(titulo)
        elements.append(Spacer(1, 0.5 * cm))

        # Subtítulo con resumen
        subtitulo_style = ParagraphStyle(
            "Subtitulo",
            parent=styles_doc["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#7f8c8d"),
            alignment=1,
            spaceAfter=15,
        )

        profesores_unicos = len(set(g.profesor_id for g in guardias if g.profesor_id))
        dias_con_guardias = len(guardias_por_fecha)

        subtitulo = Paragraph(
            f"Total: {len(guardias)} guardias | {profesores_unicos} profesores | "
            f"{dias_con_guardias} días con guardias",
            subtitulo_style,
        )
        elements.append(subtitulo)
        elements.append(Spacer(1, 0.3 * cm))

        # Crear tabla consolidada
        data = [["Fecha", "Día", "Turno", "Recreo", "Profesor", "Zona"]]
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        total_fechas = len(guardias_por_fecha)
        for idx_fecha, (fecha, guardias_dia) in enumerate(sorted(guardias_por_fecha.items())):
            # Actualizar progreso (50% a 90%)
            porcentaje = 50 + int((idx_fecha / total_fechas) * 40)
            reportar_progreso(porcentaje, f"Procesando {fecha.strftime('%d/%m/%Y')}...")

            for i, guardia in enumerate(guardias_dia):
                fecha_str = fecha.strftime("%d/%m/%Y") if i == 0 else ""
                dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""

                # Nombre del profesor
                if guardia.profesor:
                    profesor_nombre = guardia.profesor.nombre_completo
                else:
                    profesor_nombre = "Sin asignar"

                # Zona
                zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"

                data.append(
                    [
                        fecha_str,
                        dia_semana,
                        guardia.turno.capitalize(),
                        f"Recreo {guardia.recreo}",
                        profesor_nombre,
                        zona_nombre,
                    ]
                )

        reportar_progreso(90, "Aplicando estilos a la tabla...")

        # Crear tabla con columnas ajustadas
        tabla = Table(data, colWidths=[2.5 * cm, 2.5 * cm, 2 * cm, 2 * cm, 7 * cm, 4.5 * cm])

        # Estilos de la tabla
        estilos_tabla = [
            # Encabezado
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            # Cuerpo
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#2c3e50")),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 1), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
        ]

        # Alternar colores de fondo por día
        fila_actual = 1
        color_actual = 0
        fecha_anterior = None

        for fecha in sorted(guardias_por_fecha.keys()):
            num_guardias = len(guardias_por_fecha[fecha])

            if fecha != fecha_anterior:
                if color_actual % 2 == 0:
                    color_fondo = colors.white
                else:
                    color_fondo = colors.HexColor("#ecf0f1")
                color_actual += 1
                fecha_anterior = fecha

            fila_fin = fila_actual + num_guardias - 1
            estilos_tabla.append(("BACKGROUND", (0, fila_actual), (-1, fila_fin), color_fondo))

            fila_actual += num_guardias

        tabla.setStyle(TableStyle(estilos_tabla))
        elements.append(tabla)
        elements.append(Spacer(1, 0.5 * cm))

        # Pie de página con fecha de generación
        reportar_progreso(95, "Finalizando documento...")

        footer_style = ParagraphStyle(
            "FooterStyle",
            parent=styles_doc["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#7f8c8d"),
            alignment=2,
        )

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        footer = Paragraph(f"Documento generado el {fecha_generacion}", footer_style)
        elements.append(footer)

        # Generar PDF
        doc.build(elements)

        reportar_progreso(100, "PDF consolidado generado exitosamente")
        logger.info(f"PDF consolidado generado: {ruta_salida}")
        return True

    except Exception as e:
        logger.error(f"Error al exportar mes consolidado: {e}", exc_info=True)
        reportar_progreso(100, f"Error: {str(e)}")
        return False


def exportar_curso_completo(
    session: Session,
    anio_inicio: int,
    carpeta_salida: str,
    profesor_ids: Optional[list[int]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> bool:
    """
    Exporta un PDF con el curso escolar completo (Septiembre-Junio).

    Args:
        session: Sesión de base de datos
        anio_inicio: Año de inicio del curso (ej: 2024 para curso 2024-2025)
        carpeta_salida: Carpeta donde guardar el PDF
        profesor_ids: Lista opcional de IDs de profesores. Si es None, exporta todos.
        progress_callback: Función opcional para reportar progreso

    Returns:
        True si se generó correctamente, False en caso contrario
    """

    def reportar_progreso(porcentaje: int, mensaje: str = ""):
        """Helper para reportar progreso de forma segura."""
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error al reportar progreso: {e}")

    try:
        reportar_progreso(0, "Preparando exportación de curso completo...")

        logger.info(f"Iniciando exportación curso completo. Año inicio: {anio_inicio}")
        logger.info(f"Carpeta salida: {carpeta_salida}")
        logger.info(f"Profesor IDs: {profesor_ids}")

        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)

        # Definir meses del curso escolar: Septiembre a Junio
        meses_curso = [
            (9, anio_inicio),   # Septiembre
            (10, anio_inicio),  # Octubre
            (11, anio_inicio),  # Noviembre
            (12, anio_inicio),  # Diciembre
            (1, anio_inicio + 1),   # Enero
            (2, anio_inicio + 1),   # Febrero
            (3, anio_inicio + 1),   # Marzo
            (4, anio_inicio + 1),   # Abril
            (5, anio_inicio + 1),   # Mayo
            (6, anio_inicio + 1),   # Junio
        ]

        # Obtener profesores con guardias
        if profesor_ids is None:
            primer_dia_curso = date(anio_inicio, 1, 1)
            ultimo_dia_curso = date(anio_inicio + 1, 12, 31)

            logger.info(
                f"Buscando profesores con guardias entre "
                f"{primer_dia_curso} y {ultimo_dia_curso}"
            )

            prof_ids_query = (
                session.query(Guardia.profesor_id)
                .filter(Guardia.fecha >= primer_dia_curso, Guardia.fecha <= ultimo_dia_curso)
                .distinct()
                .all()
            )
            profesor_ids = [pid for (pid,) in prof_ids_query]
            logger.info(f"Profesores encontrados: {len(profesor_ids)}")

        if not profesor_ids:
            logger.warning("No hay profesores con guardias en este curso")
            reportar_progreso(100, "No hay profesores con guardias en este curso")
            return False

        # Cargar profesores
        profesores = session.query(Profesor).filter(Profesor.id.in_(profesor_ids)).all()
        logger.info(f"Profesores cargados: {len(profesores)}")

        reportar_progreso(10, f"Generando PDF para {len(profesores)} profesores...")

        # Crear nombre de archivo
        nombre_archivo = f"Guardias_Curso_{anio_inicio}_{anio_inicio + 1}_Completo.pdf"
        ruta_archivo = carpeta / nombre_archivo

        # Crear PDF
        doc = SimpleDocTemplate(
            str(ruta_archivo),
            pagesize=landscape(A4),
            rightMargin=1.5 * cm,
            leftMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )

        elements = []
        styles = getSampleStyleSheet()

        # Título principal del curso
        titulo_style = ParagraphStyle(
            "CursoTitle",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=colors.HexColor("#1976D2"),
            spaceAfter=20,
            alignment=1,
        )

        titulo = Paragraph(
            f"📚 Guardias de Patio - Curso Escolar {anio_inicio}/{anio_inicio + 1}",
            titulo_style,
        )
        elements.append(titulo)
        elements.append(Spacer(1, 0.5 * cm))

        # Procesar cada mes del curso
        total_meses = len(meses_curso)
        meses_nombres = [
            "",
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        for idx_mes, (mes, anio) in enumerate(meses_curso):
            porcentaje = 10 + int((idx_mes / total_meses) * 80)
            reportar_progreso(porcentaje, f"Procesando {meses_nombres[mes]} {anio}...")

            # Título del mes
            mes_style = ParagraphStyle(
                "MesTitle",
                parent=styles["Heading2"],
                fontSize=16,
                textColor=colors.HexColor("#2196F3"),
                spaceAfter=12,
                spaceBefore=12,
            )

            mes_titulo = Paragraph(f"📅 {meses_nombres[mes]} {anio}", mes_style)
            elements.append(mes_titulo)

            # Obtener curso activo
            curso_activo = GestorCursos.obtener_curso_activo(session)
            if not curso_activo:
                logger.warning("No hay curso activo para exportar PDFs múltiples")
                return False

            # Obtener todas las guardias del mes para los profesores seleccionados
            primer_dia = date(anio, mes, 1)
            dias_en_mes = monthrange(anio, mes)[1]
            ultimo_dia = date(anio, mes, dias_en_mes)

            guardias_mes = (
                session.query(Guardia)
                .options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
                .filter(
                    Guardia.profesor_id.in_(profesor_ids),
                    Guardia.curso_id == curso_activo.id,
                    Guardia.fecha >= primer_dia,
                    Guardia.fecha <= ultimo_dia,
                )
                .order_by(Guardia.fecha, Guardia.recreo, Guardia.profesor_id)
                .all()
            )

            if guardias_mes:
                # Agrupar por fecha
                guardias_por_fecha = defaultdict(list)
                for g in guardias_mes:
                    guardias_por_fecha[g.fecha].append(g)

                # Crear tabla
                data = [["Fecha", "Día", "Turno", "Recreo", "Profesor", "Zona"]]
                dias_semana = ["L", "M", "X", "J", "V", "S", "D"]

                for fecha, guardias_dia in sorted(guardias_por_fecha.items()):
                    for i, guardia in enumerate(guardias_dia):
                        fecha_str = fecha.strftime("%d/%m") if i == 0 else ""
                        dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""
                        profesor_nombre = (
                            guardia.profesor.nombre_completo if guardia.profesor else "N/A"
                        )
                        zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"

                        data.append(
                            [
                                fecha_str,
                                dia_semana,
                                guardia.turno.capitalize(),
                                f"R{guardia.recreo}",
                                profesor_nombre,
                                zona_nombre,
                            ]
                        )

                # Crear tabla con columnas más compactas
                tabla = Table(
                    data, colWidths=[2 * cm, 1.2 * cm, 2.2 * cm, 1.8 * cm, 6 * cm, 4 * cm]
                )

                tabla.setStyle(
                    TableStyle(
                        [
                            # Encabezado
                            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#3498db")),
                            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                            # Cuerpo
                            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                            ("TEXTCOLOR", (0, 1), (-1, -1), colors.black),
                            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            (
                                "ROWBACKGROUNDS",
                                (0, 1),
                                (-1, -1),
                                [colors.white, colors.lightgrey],
                            ),
                        ]
                    )
                )

                elements.append(tabla)
                elements.append(Spacer(1, 0.5 * cm))
            else:
                # No hay guardias este mes
                no_guardias_style = ParagraphStyle(
                    "NoGuardiasMes",
                    parent=styles["Normal"],
                    fontSize=10,
                    textColor=colors.grey,
                    alignment=1,
                )
                elements.append(Paragraph("Sin guardias asignadas", no_guardias_style))
                elements.append(Spacer(1, 0.3 * cm))

        # Pie de página
        reportar_progreso(95, "Generando documento final...")

        footer_style = ParagraphStyle(
            "FooterCurso",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=2,
        )

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        footer = Paragraph(
            f"Documento generado el {fecha_generacion} | "
            f"Profesores incluidos: {len(profesores)}",
            footer_style,
        )
        elements.append(Spacer(1, 1 * cm))
        elements.append(footer)

        # Construir PDF
        doc.build(elements)

        reportar_progreso(100, f"PDF generado: {nombre_archivo}")
        return True

    except Exception as e:
        logger.error(f"Error al exportar curso completo: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return False
