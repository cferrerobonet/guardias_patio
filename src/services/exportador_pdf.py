"""
Exportador de calendarios de guardias a formato PDF.
Genera PDFs individuales por profesor con su calendario mensual.
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Callable, Optional

from models.models import Guardia, Profesor
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.orm import Session, joinedload
from utils import get_logger

logger = get_logger(__name__)


class ExportadorPDF:
    """Exporta calendarios de guardias a PDF."""

    @staticmethod
    def exportar_calendario_profesor(
        session: Session, profesor_id: int, mes: int, anio: int, ruta_salida: str
    ) -> bool:
        """
        Exporta el calendario de un profesor para un mes específico.

        Args:
            session: Sesión de base de datos
            profesor_id: ID del profesor
            mes: Mes (1-12)
            anio: Año
            ruta_salida: Ruta del archivo PDF a generar

        Returns:
            True si se generó correctamente, False en caso contrario
        """
        try:
            profesor = session.query(Profesor).get(profesor_id)
            if not profesor:
                return False

            # Obtener guardias del mes
            primer_dia = date(anio, mes, 1)
            dias_en_mes = monthrange(anio, mes)[1]
            ultimo_dia = date(anio, mes, dias_en_mes)

            guardias = (
                session.query(Guardia)
                .options(joinedload(Guardia.zona))
                .filter(
                    Guardia.profesor_id == profesor_id,
                    Guardia.fecha >= primer_dia,
                    Guardia.fecha <= ultimo_dia,
                )
                .order_by(Guardia.fecha, Guardia.recreo)
                .all()
            )

            # Crear PDF
            doc = SimpleDocTemplate(
                ruta_salida,
                pagesize=landscape(A4),
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            elements = []
            styles = getSampleStyleSheet()

            # Título
            titulo_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                alignment=1,  # Centrado
            )

            meses = [
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

            titulo = Paragraph(
                f"Calendario de Guardias - {meses[mes]} {anio}",
                titulo_style
            )
            elements.append(titulo)

            # Información del profesor
            info_style = ParagraphStyle(
                'InfoStyle',
                parent=styles['Normal'],
                fontSize=12,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=20,
                alignment=1,
            )

            info = Paragraph(
                f"<b>Profesor/a:</b> {profesor.nombre_completo}",
                info_style
            )
            elements.append(info)

            # Tabla de guardias
            if guardias:
                # Agrupar guardias por fecha
                guardias_por_fecha = defaultdict(list)
                for g in guardias:
                    guardias_por_fecha[g.fecha].append(g)

                # Crear datos de la tabla
                data = [['Fecha', 'Día', 'Turno', 'Recreo', 'Zona', 'Observaciones']]

                dias_semana = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

                for fecha, guardias_dia in sorted(guardias_por_fecha.items()):
                    for i, guardia in enumerate(guardias_dia):
                        zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"

                        fecha_str = fecha.strftime("%d/%m/%Y") if i == 0 else ""
                        dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""

                        data.append([
                            fecha_str,
                            dia_semana,
                            guardia.turno.capitalize(),
                            f"Recreo {guardia.recreo}",
                            zona_nombre,
                            ""  # Observaciones vacías
                        ])

                # Crear tabla
                tabla = Table(data, colWidths=[3*cm, 1.5*cm, 2.5*cm, 2.5*cm, 5*cm, 5*cm])

                # Estilo de tabla
                tabla.setStyle(TableStyle([
                    # Encabezado
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                    # Cuerpo
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ]))

                elements.append(tabla)

                # Resumen
                elements.append(Spacer(1, 1*cm))

                resumen_style = ParagraphStyle(
                    'ResumenStyle',
                    parent=styles['Normal'],
                    fontSize=11,
                    textColor=colors.HexColor('#2c3e50'),
                )

                total_guardias = len(guardias)
                guardias_manana = len([g for g in guardias if g.turno == "mañana"])
                guardias_tarde = len([g for g in guardias if g.turno == "tarde"])

                resumen_text = f"""
                <b>Resumen:</b><br/>
                • Total de guardias en {meses[mes]}: {total_guardias}<br/>
                • Guardias de mañana: {guardias_manana}<br/>
                • Guardias de tarde: {guardias_tarde}
                """

                resumen = Paragraph(resumen_text, resumen_style)
                elements.append(resumen)

            else:
                # No hay guardias
                no_guardias_style = ParagraphStyle(
                    'NoGuardiasStyle',
                    parent=styles['Normal'],
                    fontSize=12,
                    textColor=colors.HexColor('#e74c3c'),
                    alignment=1,
                )

                no_guardias = Paragraph(
                    f"No hay guardias asignadas para {meses[mes]} {anio}",
                    no_guardias_style
                )
                elements.append(Spacer(1, 2*cm))
                elements.append(no_guardias)

            # Pie de página con fecha de generación
            elements.append(Spacer(1, 2*cm))

            footer_style = ParagraphStyle(
                'FooterStyle',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=2,  # Derecha
            )

            from datetime import datetime
            fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            footer = Paragraph(
                f"Documento generado el {fecha_generacion}",
                footer_style
            )
            elements.append(footer)

            # Construir PDF
            doc.build(elements)
            return True

        except Exception as e:
            print(f"Error al exportar PDF: {e}")
            return False

    @staticmethod
    def exportar_todos_los_profesores(
        session: Session,
        mes: int,
        anio: int,
        carpeta_salida: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> int:
        """
        Exporta calendarios PDF para todos los profesores con guardias.

        Args:
            session: Sesión de base de datos
            mes: Mes (1-12)
            anio: Año
            carpeta_salida: Carpeta donde guardar los PDFs
            progress_callback: Función opcional para reportar progreso.
                              Recibe (porcentaje, mensaje_detalle)

        Returns:
            Número de PDFs generados exitosamente
        """
        def reportar_progreso(porcentaje: int, mensaje: str = ""):
            """Helper para reportar progreso de forma segura."""
            if progress_callback:
                try:
                    progress_callback(porcentaje, mensaje)
                except Exception as e:
                    logger.warning(f"Error al reportar progreso: {e}")

        reportar_progreso(0, "Preparando exportación de PDFs...")

        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)

        reportar_progreso(10, "Carpeta de salida creada")

        # Obtener profesores con guardias en ese mes
        primer_dia = date(anio, mes, 1)
        dias_en_mes = monthrange(anio, mes)[1]
        ultimo_dia = date(anio, mes, dias_en_mes)

        reportar_progreso(15, "Consultando profesores con guardias...")

        # Obtener IDs de profesores con guardias
        profesor_ids = (
            session.query(Guardia.profesor_id)
            .filter(Guardia.fecha >= primer_dia, Guardia.fecha <= ultimo_dia)
            .distinct()
            .all()
        )

        # Cargar todos los profesores de una vez
        profesores_dict = {}
        if profesor_ids:
            ids_list = [pid for (pid,) in profesor_ids]
            profesores = session.query(Profesor).filter(Profesor.id.in_(ids_list)).all()
            profesores_dict = {p.id: p for p in profesores}

        total_profesores = len(profesores_dict)
        reportar_progreso(20, f"{total_profesores} profesores con guardias encontrados")

        if total_profesores == 0:
            reportar_progreso(100, "No hay profesores con guardias en este mes")
            return 0

        exitos = 0
        # Progreso de 20% a 95% (75% del rango total)
        for idx, profesor_id in enumerate(profesores_dict.keys()):
            profesor = profesores_dict[profesor_id]
            # Calcular porcentaje (20% - 95%)
            porcentaje = 20 + int((idx / total_profesores) * 75)
            mensaje = f"Generando PDF {idx + 1}/{total_profesores}: {profesor.nombre_completo}"
            reportar_progreso(porcentaje, mensaje)

            # Crear nombre de archivo seguro
            nombre_completo = profesor.nombre_completo.replace(" ", "_")
            nombre_completo = nombre_completo.replace(",", "")
            nombre_archivo = f"Guardias_{nombre_completo}_{mes:02d}_{anio}.pdf"
            ruta_archivo = carpeta / nombre_archivo

            if ExportadorPDF.exportar_calendario_profesor(
                session, profesor_id, mes, anio, str(ruta_archivo)
            ):
                exitos += 1

        reportar_progreso(95, f"{exitos} PDFs generados exitosamente")
        reportar_progreso(100, "Exportación completada")

        return exitos

    @staticmethod
    def exportar_curso_completo(
        session: Session,
        anio_inicio: int,
        carpeta_salida: str,
        profesor_ids: Optional[list[int]] = None,
        progress_callback: Optional[Callable[[int, str], None]] = None
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

            carpeta = Path(carpeta_salida)
            carpeta.mkdir(parents=True, exist_ok=True)

            # Definir meses del curso escolar: Septiembre a Junio
            meses_curso = [
                (9, anio_inicio),    # Septiembre
                (10, anio_inicio),   # Octubre
                (11, anio_inicio),   # Noviembre
                (12, anio_inicio),   # Diciembre
                (1, anio_inicio + 1), # Enero
                (2, anio_inicio + 1), # Febrero
                (3, anio_inicio + 1), # Marzo
                (4, anio_inicio + 1), # Abril
                (5, anio_inicio + 1), # Mayo
                (6, anio_inicio + 1), # Junio
            ]

            # Obtener profesores con guardias
            if profesor_ids is None:
                # Obtener todos los profesores con guardias en el curso
                primer_dia_curso = date(anio_inicio, 9, 1)
                ultimo_dia_curso = date(anio_inicio + 1, 6, 30)

                prof_ids_query = (
                    session.query(Guardia.profesor_id)
                    .filter(
                        Guardia.fecha >= primer_dia_curso,
                        Guardia.fecha <= ultimo_dia_curso
                    )
                    .distinct()
                    .all()
                )
                profesor_ids = [pid for (pid,) in prof_ids_query]

            if not profesor_ids:
                reportar_progreso(100, "No hay profesores con guardias en este curso")
                return False

            # Cargar profesores
            profesores = session.query(Profesor).filter(Profesor.id.in_(profesor_ids)).all()

            reportar_progreso(10, f"Generando PDF para {len(profesores)} profesores...")

            # Crear nombre de archivo
            nombre_archivo = f"Guardias_Curso_{anio_inicio}_{anio_inicio + 1}_Completo.pdf"
            ruta_archivo = carpeta / nombre_archivo

            # Crear PDF
            doc = SimpleDocTemplate(
                str(ruta_archivo),
                pagesize=landscape(A4),
                rightMargin=1.5*cm,
                leftMargin=1.5*cm,
                topMargin=1.5*cm,
                bottomMargin=1.5*cm,
            )

            elements = []
            styles = getSampleStyleSheet()

            # Título principal del curso
            titulo_style = ParagraphStyle(
                'CursoTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=20,
                alignment=1,
            )

            titulo = Paragraph(
                f"📚 Guardias de Patio - Curso Escolar {anio_inicio}/{anio_inicio + 1}",
                titulo_style
            )
            elements.append(titulo)
            elements.append(Spacer(1, 0.5*cm))

            # Procesar cada mes del curso
            total_meses = len(meses_curso)
            for idx_mes, (mes, anio) in enumerate(meses_curso):
                porcentaje = 10 + int((idx_mes / total_meses) * 80)
                meses_nombres = [
                    "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
                ]
                reportar_progreso(porcentaje, f"Procesando {meses_nombres[mes]} {anio}...")

                # Título del mes
                mes_style = ParagraphStyle(
                    'MesTitle',
                    parent=styles['Heading2'],
                    fontSize=16,
                    textColor=colors.HexColor('#2196F3'),
                    spaceAfter=12,
                    spaceBefore=12,
                )

                mes_titulo = Paragraph(
                    f"📅 {meses_nombres[mes]} {anio}",
                    mes_style
                )
                elements.append(mes_titulo)

                # Obtener todas las guardias del mes para los profesores seleccionados
                primer_dia = date(anio, mes, 1)
                dias_en_mes = monthrange(anio, mes)[1]
                ultimo_dia = date(anio, mes, dias_en_mes)

                guardias_mes = (
                    session.query(Guardia)
                    .options(joinedload(Guardia.zona), joinedload(Guardia.profesor))
                    .filter(
                        Guardia.profesor_id.in_(profesor_ids),
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
                    data = [['Fecha', 'Día', 'Turno', 'Recreo', 'Profesor', 'Zona']]
                    dias_semana = ['L', 'M', 'X', 'J', 'V', 'S', 'D']

                    for fecha, guardias_dia in sorted(guardias_por_fecha.items()):
                        for i, guardia in enumerate(guardias_dia):
                            fecha_str = fecha.strftime("%d/%m") if i == 0 else ""
                            dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""
                            profesor_nombre = guardia.profesor.nombre if guardia.profesor else "N/A"
                            zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"

                            data.append([
                                fecha_str,
                                dia_semana,
                                guardia.turno.capitalize(),
                                f"R{guardia.recreo}",
                                profesor_nombre,
                                zona_nombre,
                            ])

                    # Crear tabla con columnas más compactas
                    tabla = Table(data, colWidths=[2*cm, 1.2*cm, 2.2*cm, 1.8*cm, 6*cm, 4*cm])

                    tabla.setStyle(TableStyle([
                        # Encabezado
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

                        # Cuerpo
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                    ]))

                    elements.append(tabla)
                    elements.append(Spacer(1, 0.5*cm))
                else:
                    # No hay guardias este mes
                    no_guardias_style = ParagraphStyle(
                        'NoGuardiasMes',
                        parent=styles['Normal'],
                        fontSize=10,
                        textColor=colors.grey,
                        alignment=1,
                    )
                    elements.append(Paragraph("Sin guardias asignadas", no_guardias_style))
                    elements.append(Spacer(1, 0.3*cm))

            # Pie de página
            reportar_progreso(95, "Generando documento final...")

            from datetime import datetime
            footer_style = ParagraphStyle(
                'FooterCurso',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=2,
            )

            fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            footer = Paragraph(
                f"Documento generado el {fecha_generacion} | "
                f"Profesores incluidos: {len(profesores)}",
                footer_style
            )
            elements.append(Spacer(1, 1*cm))
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

    @staticmethod
    def exportar_profesor_individual_optimizado(
        session: Session,
        profesor_id: int,
        fecha_inicio: date,
        fecha_fin: date,
        ruta_salida: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> bool:
        """
        Exporta calendario individual de un profesor mostrando SOLO días con guardias.

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
                except Exception as e:
                    logger.warning(f"Error al reportar progreso: {e}")

        try:
            reportar_progreso(0, "Preparando exportación individual...")

            # Obtener profesor
            profesor = session.query(Profesor).get(profesor_id)
            if not profesor:
                return False

            reportar_progreso(10, f"Consultando guardias de {profesor.nombre_completo}...")

            # Obtener SOLO días con guardias
            guardias = (
                session.query(Guardia)
                .options(joinedload(Guardia.zona))
                .filter(
                    Guardia.profesor_id == profesor_id,
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

            # Crear PDF
            doc = SimpleDocTemplate(
                ruta_salida,
                pagesize=landscape(A4),
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm,
            )

            elements = []
            styles = getSampleStyleSheet()

            # Título
            titulo_style = ParagraphStyle(
                'TituloIndividual',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#1976D2'),
                spaceAfter=12,
                alignment=1,
            )

            titulo = Paragraph(
                "📋 Calendario Personal de Guardias",
                titulo_style
            )
            elements.append(titulo)

            # Información del profesor
            info_style = ParagraphStyle(
                'InfoProfesor',
                parent=styles['Normal'],
                fontSize=13,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=10,
                alignment=1,
            )

            info = Paragraph(
                f"<b>{profesor.nombre_completo}</b><br/>"
                f"Turno: {profesor.turno.capitalize()} | "
                f"Tutor: {'Sí' if profesor.tutor else 'No'}",
                info_style
            )
            elements.append(info)

            # Periodo
            periodo_style = ParagraphStyle(
                'Periodo',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.grey,
                spaceAfter=20,
                alignment=1,
            )

            periodo = Paragraph(
                f"Periodo: {primera_guardia.strftime('%d/%m/%Y')} - "
                f"{ultima_guardia.strftime('%d/%m/%Y')}",
                periodo_style
            )
            elements.append(periodo)

            reportar_progreso(50, "Generando tabla de guardias...")

            # Agrupar por fecha
            guardias_por_fecha = defaultdict(list)
            for g in guardias:
                guardias_por_fecha[g.fecha].append(g)

            # Crear tabla
            data = [['Fecha', 'Día', 'Turno', 'Recreo', 'Zona']]
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

            for fecha in fechas_guardias:
                guardias_dia = guardias_por_fecha[fecha]
                for i, guardia in enumerate(guardias_dia):
                    fecha_str = fecha.strftime("%d/%m/%Y") if i == 0 else ""
                    dia_semana = dias_semana[fecha.weekday()] if i == 0 else ""
                    zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"

                    data.append([
                        fecha_str,
                        dia_semana,
                        guardia.turno.capitalize(),
                        f"Recreo {guardia.recreo}",
                        zona_nombre,
                    ])

            # Tabla con columnas ajustadas
            tabla = Table(data, colWidths=[3.5*cm, 3.5*cm, 3*cm, 3*cm, 6*cm])

            tabla.setStyle(TableStyle([
                # Encabezado
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976D2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                # Cuerpo
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))

            elements.append(tabla)

            reportar_progreso(80, "Generando estadísticas...")

            # Resumen estadístico
            elements.append(Spacer(1, 1*cm))

            resumen_style = ParagraphStyle(
                'ResumenIndividual',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#2c3e50'),
            )

            total_guardias = len(guardias)
            dias_con_guardias = len(fechas_guardias)
            guardias_manana = len([g for g in guardias if g.turno == "mañana"])
            guardias_tarde = len([g for g in guardias if g.turno == "tarde"])

            # Calcular zonas más frecuentes
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

            # Pie de página
            elements.append(Spacer(1, 1*cm))

            from datetime import datetime
            footer_style = ParagraphStyle(
                'FooterIndividual',
                parent=styles['Normal'],
                fontSize=8,
                textColor=colors.grey,
                alignment=2,
            )

            fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
            footer = Paragraph(
                f"Documento generado el {fecha_generacion}",
                footer_style
            )
            elements.append(footer)

            reportar_progreso(95, "Construyendo PDF...")

            # Construir PDF
            doc.build(elements)

            reportar_progreso(100, "PDF generado exitosamente")
            return True

        except Exception as e:
            logger.error(f"Error al exportar profesor individual: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return False

    @staticmethod
    def exportar_profesores_seleccionados(
        session: Session,
        profesor_ids: list[int],
        mes: int,
        anio: int,
        carpeta_salida: str,
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> int:
        """
        Exporta PDFs individuales solo para profesores seleccionados.

        Args:
            session: Sesión de base de datos
            profesor_ids: Lista de IDs de profesores a exportar
            mes: Mes (1-12)
            anio: Año
            carpeta_salida: Carpeta donde guardar PDFs
            progress_callback: Función opcional para reportar progreso

        Returns:
            Número de PDFs generados exitosamente
        """
        def reportar_progreso(porcentaje: int, mensaje: str = ""):
            if progress_callback:
                try:
                    progress_callback(porcentaje, mensaje)
                except Exception as e:
                    logger.warning(f"Error al reportar progreso: {e}")

        try:
            reportar_progreso(0, "Preparando exportación de profesores seleccionados...")

            carpeta = Path(carpeta_salida)
            carpeta.mkdir(parents=True, exist_ok=True)

            # Cargar profesores seleccionados
            profesores = session.query(Profesor).filter(Profesor.id.in_(profesor_ids)).all()
            total_profesores = len(profesores)

            if total_profesores == 0:
                reportar_progreso(100, "No se seleccionaron profesores")
                return 0

            reportar_progreso(10, f"Exportando {total_profesores} profesores seleccionados...")

            exitos = 0
            for idx, profesor in enumerate(profesores):
                # Calcular porcentaje (10% - 95%)
                porcentaje = 10 + int((idx / total_profesores) * 85)
                mensaje = f"Generando PDF {idx + 1}/{total_profesores}: {profesor.nombre_completo}"
                reportar_progreso(porcentaje, mensaje)

                # Crear nombre de archivo seguro
                nombre_completo = profesor.nombre_completo.replace(" ", "_").replace(",", "")
                nombre_archivo = f"Guardias_{nombre_completo}_{mes:02d}_{anio}.pdf"
                ruta_archivo = carpeta / nombre_archivo

                if ExportadorPDF.exportar_calendario_profesor(
                    session, profesor.id, mes, anio, str(ruta_archivo)
                ):
                    exitos += 1

            reportar_progreso(95, f"{exitos}/{total_profesores} PDFs generados")
            reportar_progreso(100, "Exportación completada")

            return exitos

        except Exception as e:
            logger.error(f"Error al exportar profesores seleccionados: {e}")
            if progress_callback:
                progress_callback(0, f"Error: {str(e)}")
            return 0
