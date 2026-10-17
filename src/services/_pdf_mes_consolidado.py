"""
Exportación PDF consolidada: vista mensual (rediseñada) y curso completo.

La vista mensual es el cuadrante del mes para el tablón y para el correo: cabecera
con los logos, cifras, calendario del mes con las guardias de cada día y, día a día,
una rejilla recreo × zona con quién está en cada sitio. Se lee igual en blanco y negro.
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Optional

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from infrastructure.database.models import Configuracion, Guardia, Profesor
from services._pdf_mini_calendario import (
    Bloque,
    CalendarioMes,
    DiaCalendario,
    leyenda,
    no_lectivos_del_mes,
    texto_horarios,
)
from services.gestor_cursos import GestorCursos
from services.pdf_styles import Papel, PDFStyles, construir_documento, trama
from services.recreos import resolver
from utils import get_logger

logger = get_logger(__name__)


class Cifras(Flowable):
    """Fila de cifras grandes (como las tarjetas de Partes de salida)."""

    def __init__(self, ancho, cifras):
        super().__init__()
        self.ancho, self.cifras = ancho, cifras
        self.alto = 17 * mm

    def wrap(self, *_):
        return self.ancho, self.alto

    def draw(self):
        c = self.canv
        n = len(self.cifras)
        hueco = 4 * mm
        w = (self.ancho - hueco * (n - 1)) / n
        for i, (valor, texto) in enumerate(self.cifras):
            x = i * (w + hueco)
            c.setStrokeColor(Papel.TINTA)
            c.setLineWidth(1.1)
            c.roundRect(x + 0.5, 0.5, w - 1, self.alto - 1, 1.8 * mm, stroke=1, fill=0)
            c.setFillColor(Papel.TINTA)
            c.setFont(Papel.TITULAR, 24)
            c.drawString(x + 4.5 * mm, 5.2 * mm, str(valor))
            from reportlab.pdfbase.pdfmetrics import stringWidth

            ancho_num = stringWidth(str(valor), Papel.TITULAR, 24)
            c.setFillColor(Papel.TINTA_SUAVE)
            c.setFont(Papel.SEMI, 9)
            c.drawString(x + 4.5 * mm + ancho_num + 2.2 * mm, 5.9 * mm, texto)


class FranjaNoLectiva(Flowable):
    """Un laborable sin clase dentro del listado día a día: la secuencia de días no salta."""

    def __init__(self, ancho, texto):
        super().__init__()
        self.ancho, self.texto, self.alto = ancho, texto, 7.5 * mm

    def wrap(self, *_):
        return self.ancho, self.alto

    def draw(self):
        c = self.canv
        trama(c, 0, 0, self.ancho, self.alto, paso=1.6 * mm)
        c.setStrokeColor(Papel.TINTA)
        c.setLineWidth(0.8)
        c.rect(0, 0, self.ancho, self.alto, stroke=1, fill=0)
        from reportlab.pdfbase.pdfmetrics import stringWidth

        c.setFont(Papel.CONDENSADA, 10.5)
        w = stringWidth(self.texto, Papel.CONDENSADA, 10.5) + 4 * mm
        c.setFillColor(Papel.BLANCO)
        c.rect(2 * mm, 1.4 * mm, w, self.alto - 2.8 * mm, stroke=0, fill=1)
        c.setFillColor(Papel.TINTA)
        c.drawString(4 * mm, 2.6 * mm, self.texto)


def _fecha_larga(f: date) -> str:
    return f"{Papel.DIAS[f.weekday()]} {f.day} de {Papel.MESES[f.month].lower()}"


def exportar_mes_consolidado(
    session,
    mes: int,
    anio: int,
    ruta_salida: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> bool:
    """
    Exporta un PDF consolidado con todas las guardias del mes.

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
        reportar_progreso(0, "Preparando exportación consolidada del mes...")
        curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
        if not curso_activo:
            logger.warning("No hay curso activo para exportar PDF consolidado")
            return False

        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, monthrange(anio, mes)[1])
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
        config = session.query(Configuracion).first()

        # Id global del recreo (3 y 4 de tarde) → «Tarde · R1 · 16:30» (`services.recreos`)
        def hora(turno, recreo):
            return resolver(config, recreo, turno).hora_texto

        por_fecha = defaultdict(list)
        for g in guardias:
            por_fecha[g.fecha].append(g)
        zonas = sorted({g.zona for g in guardias if g.zona}, key=lambda z: z.id)
        franjas = sorted({(g.turno, g.recreo) for g in guardias},
                         key=lambda tr: (hora(*tr) or "99", tr[1]))
        no_lectivos = no_lectivos_del_mes(config, anio, mes)
        nombre_mes = f"{Papel.MESES[mes]} {anio}"

        apaisado = len(zonas) > 6
        pagina = landscape(A4) if apaisado else A4
        ancho = pagina[0] - 2 * Papel.MARGEN_X

        piezas = [
            Cifras(ancho, [
                (len(guardias), "guardias"),
                (len({g.profesor_id for g in guardias if g.profesor_id}), "profesores"),
                (len(por_fecha), "días con guardias"),
            ]),
            Spacer(1, 5 * mm),
        ]

        # Calendario del mes: cuántas guardias hay cada día, y de qué turno
        dias = {}
        for f, lista in por_fecha.items():
            m = sum(1 for g in lista if g.turno == "mañana")
            t = len(lista) - m
            partes = [p for p in (f"{m} mañana" if m else "", f"{t} tarde" if t else "") if p]
            dias[f.day] = DiaCalendario(
                [Bloque(f"{len(lista)} guardias", detalle=" · ".join(partes))]
            )
        semanas = 6 if len(__import__("calendar").monthcalendar(anio, mes)) > 5 else 5
        fila = (17 if apaisado else 13.5) * mm if semanas == 5 else (14 if apaisado else 11.5) * mm
        piezas.append(CalendarioMes(anio, mes, ancho, fila, dias, no_lectivos,
                                    titulo=nombre_mes, titulo_derecha="Guardias de cada día"))
        piezas.append(Spacer(1, 2 * mm))
        piezas.append(leyenda(ancho, texto_horarios(config), None, guardia=None))

        # Día a día: rejilla recreo × zona
        reportar_progreso(60, "Generando el cuadrante día a día...")
        titulo_sec = ParagraphStyle("h", fontName=Papel.CONDENSADA, fontSize=14, leading=17,
                                    textColor=Papel.VERDE_OSCURO, spaceBefore=5 * mm,
                                    spaceAfter=2 * mm)
        dia_st = ParagraphStyle("dia", fontName=Papel.CONDENSADA, fontSize=11.5, leading=13,
                                textColor=Papel.BLANCO)
        dia_n = ParagraphStyle("dian", parent=dia_st, fontName=Papel.SEMI, fontSize=8.5,
                               leading=10, alignment=2)
        cab = ParagraphStyle("cab", fontName=Papel.NEGRITA, fontSize=7.6, leading=9,
                             textColor=Papel.TINTA)
        franja_st = ParagraphStyle("fr", fontName=Papel.NEGRITA, fontSize=8.2, leading=9.8,
                                   textColor=Papel.TINTA)
        nombre_st = ParagraphStyle("nom", fontName=Papel.TEXTO, fontSize=8.2, leading=9.8,
                                   textColor=Papel.TINTA)
        vacio_st = ParagraphStyle("vac", parent=nombre_st, textColor=Papel.TINTA_SUAVE,
                                  alignment=1)

        col_franja = 31 * mm
        col_zona = (ancho - col_franja) / max(len(zonas), 1)
        piezas += [CondPageBreak(60 * mm), Paragraph("Guardias día a día", titulo_sec)]

        laborables = [date(anio, mes, d) for d in range(1, ultimo_dia.day + 1)
                      if date(anio, mes, d).weekday() < 5]
        total_dias = len(laborables)
        for i, f in enumerate(laborables):
            reportar_progreso(60 + int(i / total_dias * 30), f"Procesando {f:%d/%m/%Y}...")
            lista = por_fecha.get(f)
            if not lista:
                if f.day in no_lectivos:
                    piezas += [FranjaNoLectiva(ancho, f"{_fecha_larga(f)} · festivo o no lectivo"),
                               Spacer(1, 3 * mm)]
                continue
            celdas = defaultdict(list)
            for g in lista:
                nombre = g.profesor.nombre_completo if g.profesor else "Sin asignar"
                celdas[(g.turno, g.recreo, g.zona.id if g.zona else None)].append(nombre)
            data = [
                [Paragraph(_fecha_larga(f), dia_st)] + [""] * (len(zonas) - 1)
                + [Paragraph(f"{len(lista)} guardias", dia_n)],
                [Paragraph("RECREO", cab)] + [Paragraph(z.nombre_zona, cab) for z in zonas],
            ]
            estilos = [
                ("SPAN", (0, 0), (-2, 0)),
                ("VALIGN", (0, 0), (-1, 0), "BOTTOM"),
                ("BACKGROUND", (0, 0), (-1, 0), Papel.VERDE_OSCURO),
                ("BACKGROUND", (0, 1), (-1, 1), Papel.FONDO),
                ("VALIGN", (0, 1), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1.6 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 1.0 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.3 * mm),
                ("BOX", (0, 0), (-1, -1), 0.8, Papel.TINTA),
                ("INNERGRID", (0, 1), (-1, -1), 0.4, Papel.LINEA),
                ("LINEBELOW", (0, 1), (-1, 1), 0.8, Papel.TINTA),
            ]
            for j, z in enumerate(zonas, start=1):
                estilos.append(("LINEABOVE", (j, 1), (j, 1), 2.4, PDFStyles.get_color_zona(z.id)))
            for turno, recreo in franjas:
                h = hora(turno, recreo)
                fila_datos = [Paragraph(f"{turno.capitalize()} · "
                                        f"{resolver(config, recreo, turno).corta}"
                                        + (f" · <font name='{Papel.TEXTO}'>{h}</font>" if h
                                           else ""), franja_st)]
                for z in zonas:
                    nombres = sorted(celdas.get((turno, recreo, z.id), []))
                    if len(nombres) > 1:  # dos personas en el mismo sitio: que se vea que son dos
                        nombres = [f"• {n}" for n in nombres]
                    fila_datos.append(Paragraph("<br/>".join(nombres), nombre_st) if nombres
                                      else Paragraph("—", vacio_st))
                data.append(fila_datos)
            tabla = Table(data, colWidths=[col_franja] + [col_zona] * len(zonas))
            tabla.setStyle(TableStyle(estilos))
            piezas += [KeepTogether([tabla]), Spacer(1, 3 * mm)]

        reportar_progreso(95, "Finalizando documento...")
        generado = datetime.now()
        curso = getattr(curso_activo, "nombre", "") or ""
        construir_documento(
            ruta_salida, piezas,
            titulo=f"CALENDARIO DE GUARDIAS · {nombre_mes.upper()}",
            subtitulo="Escuelas Profesionales Luis Amigó · Godella"
            + (f" · {curso}" if curso else ""),
            resto_izquierda=f"Guardias de patio · {nombre_mes}",
            resto_derecha=curso,
            pie=f"EPLA · Guardias de patio · Generado el {generado:%d/%m/%Y} "
            f"a las {generado:%H:%M}",
            titulo_pdf=f"Guardias de patio · {nombre_mes}",
            asunto="Calendario de guardias de patio del mes",
            pagesize=pagina,
        )
        reportar_progreso(100, "PDF consolidado generado exitosamente")
        logger.info(f"PDF consolidado generado: {ruta_salida}")
        return True

    except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
        logger.error(f"Error al exportar mes consolidado: {e}", exc_info=True)
        reportar_progreso(100, f"Error: {str(e)}")
        return False


def exportar_curso_completo(
    session,
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
            except (ValueError, TypeError, OSError) as e:
                logger.warning(f"Error al reportar progreso: {e}")

    try:
        reportar_progreso(0, "Preparando exportación de curso completo...")

        logger.info(f"Iniciando exportación curso completo. Año inicio: {anio_inicio}")
        logger.info(f"Carpeta salida: {carpeta_salida}")
        logger.info(f"Profesor IDs: {profesor_ids}")

        carpeta = Path(carpeta_salida)
        carpeta.mkdir(parents=True, exist_ok=True)
        config = session.query(Configuracion).first()

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
            fontSize=24,
            fontName=PDFStyles.FUENTE_TITULO,
            textColor=PDFStyles.TEXTO_OSCURO,
            spaceAfter=6,
            alignment=1,
        )

        titulo = Paragraph(
            f"GUARDIAS DE PATIO · CURSO {anio_inicio}/{anio_inicio + 1}",
            titulo_style,
        )
        elements.append(titulo)
        elements.append(
            HRFlowable(width="100%", thickness=1.2, color=PDFStyles.DORADO, spaceAfter=8)
        )

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
                fontSize=17,
                fontName=PDFStyles.FUENTE_TITULO,
                textColor=PDFStyles.VERDE_OSCURO,
                spaceAfter=8,
                spaceBefore=12,
            )

            mes_titulo = Paragraph(f"{meses_nombres[mes]} {anio}", mes_style)
            elements.append(mes_titulo)

            # Obtener curso activo
            curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
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
                                resolver(config, guardia.recreo, guardia.turno).corta_con_hora,
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
                        PDFStyles.tabla_estandar()
                        + [
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("FONTSIZE", (0, 0), (-1, 0), 10),
                            ("TOPPADDING", (0, 0), (-1, 0), 6),
                            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                            ("FONTNAME", (0, 1), (1, -1), PDFStyles.FUENTE_NEGRITA),
                            ("FONTSIZE", (0, 1), (-1, -1), 9),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
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
                    fontName=PDFStyles.FUENTE_NORMAL,
                    textColor=PDFStyles.TEXTO_GRIS,
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
            fontName=PDFStyles.FUENTE_NORMAL,
            textColor=PDFStyles.TEXTO_GRIS,
            alignment=2,
        )

        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M")
        footer = Paragraph(
            f"Documento generado el {fecha_generacion} · "
            f"Profesores incluidos: {len(profesores)}",
            footer_style,
        )
        elements.append(Spacer(1, 1 * cm))
        elements.append(footer)

        # Construir PDF
        doc.build(
            elements, onFirstPage=PDFStyles.pie_de_pagina, onLaterPages=PDFStyles.pie_de_pagina
        )

        reportar_progreso(100, f"PDF generado: {nombre_archivo}")
        return True

    except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
        logger.error(f"Error al exportar curso completo: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return False
