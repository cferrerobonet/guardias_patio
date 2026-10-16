"""
Exportación PDF individual de profesor: «mis guardias».

A4 vertical con la identidad de Partes de salida: cabecera con los dos logos, ficha
del destinatario (nombre en grande y su resumen), calendario de cada mes con lo que
toca cada día escrito con palabras, leyenda y detalle. Se lee igual en blanco y negro.
"""

from collections import Counter, defaultdict
from datetime import date, datetime
from typing import Callable, Optional

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    CondPageBreak,
    Flowable,
    KeepTogether,
    Paragraph,
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
    obtener_hora_recreo,
    texto_horarios,
)
from services.gestor_cursos import GestorCursos
from services.pdf_styles import Papel, PDFStyles, ajustar, construir_documento
from utils import get_logger

logger = get_logger(__name__)

ANCHO = Papel.PAGINA[0] - 2 * Papel.MARGEN_X


def _decimal(valor: float) -> str:
    return f"{valor:.1f}".replace(".", ",")


def _plural(n: int, uno: str, varios: str) -> str:
    return f"{n} {uno if n == 1 else varios}"


class FichaProfesor(Flowable):
    """Recuadro del destinatario: su nombre en grande, sus datos y el total de guardias."""

    def __init__(self, ancho, nombre, linea_datos, linea_resumen, total, dias):
        super().__init__()
        self.ancho = ancho
        self.linea_datos, self.linea_resumen = linea_datos, linea_resumen
        self.total, self.dias = total, dias
        self.ancho_caja = 42 * mm
        self.ancho_izq = ancho - self.ancho_caja - 11 * mm
        self.nombre, self.tam = ajustar(nombre.upper(), Papel.TITULAR, 23, 13, self.ancho_izq, 2)
        self.datos, self.tam_datos = ajustar(linea_datos, Papel.MEDIA, 9, 7, self.ancho_izq, 2)
        self.resumen, self.tam_res = ajustar(linea_resumen, Papel.TEXTO, 8.3, 6.8,
                                             self.ancho_izq, 2)
        pt = 0.3528 * mm
        self.alto = max(
            33 * mm,
            (8.5 * mm + len(self.nombre) * self.tam * 1.02 * pt + 2.2 * mm
             + len(self.datos) * self.tam_datos * 1.25 * pt
             + len(self.resumen) * self.tam_res * 1.25 * pt + 4.5 * mm),
        )

    def wrap(self, *_):
        return self.ancho, self.alto

    def draw(self):
        c = self.canv
        pt = 0.3528 * mm
        w, h = self.ancho, self.alto
        c.setStrokeColor(Papel.TINTA)
        c.setLineWidth(1.2)
        c.roundRect(0.6, 0.6, w - 1.2, h - 1.2, 2.2 * mm, stroke=1, fill=0)
        x = 5.5 * mm
        y = h - 6.4 * mm
        c.setFillColor(Papel.TINTA_SUAVE)
        rotulo = c.beginText(x, y)
        rotulo.setFont(Papel.NEGRITA, 7)
        rotulo.setCharSpace(0.9)
        rotulo.textOut("PROFESOR/A")
        rotulo.setCharSpace(0)  # Tc se queda en el estado gráfico: hay que devolverlo a 0
        c.drawText(rotulo)
        y -= 1.2 * mm
        c.setFillColor(Papel.TINTA)
        c.setFont(Papel.TITULAR, self.tam)
        for linea in self.nombre:
            y -= self.tam * 1.0 * pt
            c.drawString(x, y, linea)
        y -= 2.6 * mm
        c.setFont(Papel.MEDIA, self.tam_datos)
        for linea in self.datos:
            y -= self.tam_datos * 1.05 * pt
            c.drawString(x, y, linea)
            y -= self.tam_datos * 0.2 * pt
        c.setFillColor(Papel.TINTA_SUAVE)
        c.setFont(Papel.TEXTO, self.tam_res)
        for linea in self.resumen:
            y -= self.tam_res * 1.05 * pt + 0.6 * mm
            c.drawString(x, y, linea)

        # Caja del total, como la «hora de salida» del parte
        xc = w - self.ancho_caja - 3.2 * mm
        c.setStrokeColor(Papel.TINTA)
        c.setLineWidth(1.6)
        c.roundRect(xc, 3.2 * mm, self.ancho_caja, h - 6.4 * mm, 1.8 * mm, stroke=1, fill=0)
        cx = xc + self.ancho_caja / 2
        mitad = h / 2
        c.setFillColor(Papel.TINTA)
        c.setFont(Papel.NEGRITA, 7)
        c.drawCentredString(cx, mitad + 7.8 * mm, "GUARDIAS")
        c.setFont(Papel.TITULAR, 34)
        c.drawCentredString(cx, mitad - 4.6 * mm, str(self.total))
        c.setFillColor(Papel.TINTA_SUAVE)
        c.setFont(Papel.TEXTO, 8)
        c.drawCentredString(cx, mitad - 9.6 * mm, f"en {_plural(self.dias, 'día', 'días')}")


def exportar_profesor_individual_optimizado(
    session,
    profesor_id: int,
    fecha_inicio: date,
    fecha_fin: date,
    ruta_salida: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> bool:
    """
    Exporta el calendario individual de un profesor con sus guardias del periodo.

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

        curso_activo = GestorCursos.from_session(session).obtener_curso_activo()
        if not curso_activo:
            logger.warning("No hay curso activo para exportar PDF individual")
            return False

        profesor = session.query(Profesor).get(profesor_id)
        config = session.query(Configuracion).first()
        if not profesor:
            return False

        reportar_progreso(10, f"Consultando guardias de {profesor.nombre_completo}...")
        guardias = list(
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

        def hora(g):
            return obtener_hora_recreo(config, g.turno, g.recreo) if config else ""

        # Dentro de cada día, por hora real (la tarde después de la mañana)
        guardias = sorted(guardias, key=lambda g: (g.fecha, hora(g) or "99", g.recreo))
        fechas = sorted({g.fecha for g in guardias})
        meses = sorted({(f.year, f.month) for f in fechas})
        compacto = len(meses) > 2

        zonas = []
        for g in sorted(guardias, key=lambda g: g.zona.id if g.zona else 0):
            if g.zona and g.zona not in zonas:
                zonas.append(g.zona)
        codigo_zona = {z.id: f"Z{i + 1}" for i, z in enumerate(zonas)}

        # ---------------------------------------------------------- ficha
        nombre_mes = Papel.MESES
        if len(meses) == 1:
            periodo_texto = f"{nombre_mes[meses[0][1]]} {meses[0][0]}"
        else:
            (a1, m1), (a2, m2) = meses[0], meses[-1]
            periodo_texto = f"{nombre_mes[m1]} {a1} – {nombre_mes[m2].lower()} {a2}"
        n_manana = sum(1 for g in guardias if g.turno == "mañana")
        n_tarde = sum(1 for g in guardias if g.turno == "tarde")
        zonas_contador = Counter(g.zona.nombre_zona for g in guardias if g.zona)
        zona_top, zona_n = zonas_contador.most_common(1)[0] if zonas_contador else ("—", 0)
        linea_datos = (
            f"Turno {profesor.turno.lower()} · Tutor/a: {'sí' if profesor.tutor else 'no'} · "
            f"Del {fechas[0]:%d/%m/%Y} al {fechas[-1]:%d/%m/%Y}"
        )
        linea_resumen = (
            f"{n_manana} de mañana · {n_tarde} de tarde · Zona más frecuente: {zona_top} "
            f"({zona_n}) · {_decimal(len(guardias) / len(fechas))} guardias por día con guardia"
        )
        piezas = [
            FichaProfesor(ANCHO, profesor.nombre_completo, linea_datos, linea_resumen,
                          len(guardias), len(fechas)),
            Spacer(1, 5 * mm),
        ]

        # ---------------------------------------------------------- calendarios
        reportar_progreso(40, "Generando calendarios...")
        por_mes = defaultdict(lambda: defaultdict(list))
        for g in guardias:
            por_mes[(g.fecha.year, g.fecha.month)][g.fecha.day].append(g)

        def bloque(g):
            color = PDFStyles.get_color_zona(g.zona.id) if g.zona else None
            zona = g.zona.nombre_zona if g.zona else "Sin zona"
            if compacto:
                cod = codigo_zona.get(g.zona.id, "Z?") if g.zona else "Z?"
                return Bloque(f"{g.turno[0].upper()}{g.recreo}·{cod}", color=color)
            h = hora(g)
            return Bloque(
                f"R{g.recreo} · {h}" if h else f"Recreo {g.recreo}",
                detalle=zona, etiqueta=g.turno.upper(), etiqueta_corta=g.turno[0].upper(),
                color=color,
            )

        calendarios = []
        for anio, mes in meses:
            dias = {
                d: DiaCalendario([bloque(g) for g in lista], resaltado=True)
                for d, lista in por_mes[(anio, mes)].items()
            }
            n = sum(len(v) for v in por_mes[(anio, mes)].values())
            calendarios.append(((anio, mes), dias, n))

        if not compacto:
            for (anio, mes), dias, n in calendarios:
                import calendar as _cal

                semanas = len(_cal.monthcalendar(anio, mes))
                fila = 20 * mm if semanas <= 5 else 17 * mm
                piezas.append(CalendarioMes(
                    anio, mes, ANCHO, fila, dias, no_lectivos_del_mes(config, anio, mes),
                    titulo=f"{nombre_mes[mes]} {anio}",
                    titulo_derecha=f"{_plural(n, 'guardia', 'guardias')} este mes",
                ))
                piezas.append(Spacer(1, 3.5 * mm))
        else:
            columnas = 2 if len(meses) <= 4 else 3
            hueco = 6 * mm
            ancho_cal = (ANCHO - hueco * (columnas - 1)) / columnas
            fila = 10.5 * mm if columnas == 2 else 8.2 * mm
            celdas = [
                CalendarioMes(a, m, ancho_cal, fila, dias, no_lectivos_del_mes(config, a, m),
                              titulo=f"{nombre_mes[m]} {a}",
                              titulo_derecha=_plural(n, "guardia", "guardias"))
                for (a, m), dias, n in calendarios
            ]
            filas = [celdas[i:i + columnas] for i in range(0, len(celdas), columnas)]
            filas[-1] += [""] * (columnas - len(filas[-1]))
            anchos = []
            for i in range(columnas):
                anchos.append(ancho_cal + (hueco if i < columnas - 1 else 0))
            t = Table(filas, colWidths=anchos)
            t.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ]))
            piezas.append(t)

        zonas_ley = None
        horarios = texto_horarios(config)
        if compacto:
            zonas_ley = [(codigo_zona[z.id], z.nombre_zona, PDFStyles.get_color_zona(z.id))
                         for z in zonas]
            horarios += (" &nbsp;&nbsp;&nbsp; En el calendario, <b>M1</b> = mañana, recreo 1; "
                         "<b>T2</b> = tarde, recreo 2")
        piezas.append(leyenda(ANCHO, horarios, zonas_ley, "Tienes guardia"))

        # ---------------------------------------------------------- detalle
        reportar_progreso(60, "Generando tabla de guardias...")
        cab = ParagraphStyle("cab", fontName=Papel.NEGRITA, fontSize=7.5, leading=9,
                             textColor=Papel.BLANCO)
        celda = ParagraphStyle("cel", fontName=Papel.TEXTO, fontSize=8.4, leading=10.2,
                               textColor=Papel.TINTA)
        celda_b = ParagraphStyle("celb", parent=celda, fontName=Papel.SEMI)
        zona_st = ParagraphStyle("zon", parent=celda, fontName=Papel.SEMI)
        mes_st = ParagraphStyle("mes", parent=celda, fontName=Papel.NEGRITA, fontSize=7.5,
                                textColor=Papel.VERDE_OSCURO)

        data = [[Paragraph(t, cab) for t in ("FECHA", "DÍA", "TURNO", "RECREO", "ZONA")]]
        estilos = [
            ("BACKGROUND", (0, 0), (-1, 0), Papel.VERDE_OSCURO),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2.2 * mm),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1.8 * mm),
            ("TOPPADDING", (0, 0), (-1, -1), 1.3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5 * mm),
            ("BOX", (0, 0), (-1, -1), 0.8, Papel.TINTA),
            ("LINEBELOW", (0, 1), (-1, -1), 0.4, Papel.LINEA),
        ]
        fila = 1
        zebra = 0
        for anio, mes in meses:
            if len(meses) > 1:
                n = sum(len(v) for v in por_mes[(anio, mes)].values())
                data.append([Paragraph(f"{nombre_mes[mes].upper()} {anio} · "
                                       f"{_plural(n, 'guardia', 'guardias')}", mes_st),
                             "", "", "", ""])
                estilos += [("SPAN", (0, fila), (-1, fila)),
                            ("BACKGROUND", (0, fila), (-1, fila), Papel.VERDE_SUAVE),
                            ("LINEABOVE", (0, fila), (-1, fila), 0.8, Papel.TINTA)]
                fila += 1
            for d in sorted(por_mes[(anio, mes)]):
                lista = por_mes[(anio, mes)][d]
                inicio = fila
                for g in lista:
                    h = hora(g)
                    zona = g.zona.nombre_zona if g.zona else "Sin zona"
                    desc = g.zona.descripcion if g.zona and g.zona.descripcion else ""
                    if compacto and g.zona:
                        zona = f"{codigo_zona[g.zona.id]} · {zona}"
                    texto_zona = f"{zona}"
                    if desc:
                        texto_zona += (f" <font name='{Papel.TEXTO}' size='7.8' "
                                       f"color='#5a625c'>— {desc}</font>")
                    data.append([
                        Paragraph(g.fecha.strftime("%d/%m/%Y"), celda_b),
                        Paragraph(Papel.DIAS[g.fecha.weekday()], celda),
                        Paragraph(g.turno.capitalize(), celda),
                        Paragraph(f"Recreo {g.recreo}" + (f" · <b>{h}</b>" if h else ""), celda),
                        Paragraph(texto_zona, zona_st),
                    ])
                    if g.zona:
                        estilos.append(("LINEBEFORE", (4, fila), (4, fila), 3,
                                        PDFStyles.get_color_zona(g.zona.id)))
                    fila += 1
                if fila - inicio > 1:
                    estilos += [("SPAN", (0, inicio), (0, fila - 1)),
                                ("SPAN", (1, inicio), (1, fila - 1))]
                if zebra % 2:
                    estilos.append(("BACKGROUND", (0, inicio), (-1, fila - 1), Papel.FONDO))
                zebra += 1

        anchos = [24 * mm, 22 * mm, 18 * mm, 28 * mm]
        tabla = Table(data, colWidths=anchos + [ANCHO - sum(anchos)], repeatRows=1)
        tabla.setStyle(TableStyle(estilos))
        titulo = Paragraph(
            "Detalle de las guardias",
            ParagraphStyle("h", fontName=Papel.CONDENSADA, fontSize=14, leading=17,
                           textColor=Papel.VERDE_OSCURO, spaceBefore=4 * mm, spaceAfter=1.5 * mm),
        )
        piezas += [CondPageBreak(40 * mm), KeepTogether([titulo, tabla])]

        reportar_progreso(90, "Construyendo PDF...")
        generado = datetime.now()
        curso = getattr(curso_activo, "nombre", "") or ""
        construir_documento(
            ruta_salida, piezas,
            titulo="CALENDARIO PERSONAL DE GUARDIAS",
            subtitulo="Escuelas Profesionales Luis Amigó · Godella"
            + (f" · {curso}" if curso else ""),
            resto_izquierda=f"Guardias de patio · {profesor.nombre_completo}",
            resto_derecha=periodo_texto,
            pie=f"EPLA · Guardias de patio · Generado el {generado:%d/%m/%Y} "
            f"a las {generado:%H:%M}",
            titulo_pdf=f"Guardias de patio · {profesor.nombre_completo} · {periodo_texto}",
            asunto="Calendario personal de guardias de patio",
        )

        reportar_progreso(100, "PDF generado exitosamente")
        return True

    except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
        logger.error(f"Error al exportar profesor individual: {e}")
        if progress_callback:
            progress_callback(0, f"Error: {str(e)}")
        return False
