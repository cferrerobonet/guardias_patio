"""
Exportador de calendarios de guardias a formato PDF.
Genera PDFs individuales por profesor con su calendario mensual.
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date
from pathlib import Path

from models.models import Guardia, Profesor, Zona
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
from sqlalchemy.orm import Session


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
                        zona = session.query(Zona).get(guardia.zona_id)
                        zona_nombre = zona.nombre_zona if zona else "N/A"

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
        session: Session, mes: int, anio: int, carpeta_salida: str
    ) -> int:
        """
        Exporta calendarios PDF para todos los profesores con guardias.

        Args:
            session: Sesión de base de datos
            mes: Mes (1-12)
            anio: Año
            carpeta_salida: Carpeta donde guardar los PDFs

        Returns:
            Número de PDFs generados exitosamente
        """
        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)

        # Obtener profesores con guardias en ese mes
        primer_dia = date(anio, mes, 1)
        dias_en_mes = monthrange(anio, mes)[1]
        ultimo_dia = date(anio, mes, dias_en_mes)

        profesores_con_guardias = (
            session.query(Guardia.profesor_id)
            .filter(Guardia.fecha >= primer_dia, Guardia.fecha <= ultimo_dia)
            .distinct()
            .all()
        )

        exitos = 0
        for (profesor_id,) in profesores_con_guardias:
            profesor = session.query(Profesor).get(profesor_id)
            if profesor:
                # Crear nombre de archivo seguro
                nombre_completo = profesor.nombre_completo.replace(" ", "_")
                nombre_completo = nombre_completo.replace(",", "")
                nombre_archivo = f"Guardias_{nombre_completo}_{mes:02d}_{anio}.pdf"
                ruta_archivo = carpeta / nombre_archivo

                if ExportadorPDF.exportar_calendario_profesor(
                    session, profesor_id, mes, anio, str(ruta_archivo)
                ):
                    exitos += 1

        return exitos
