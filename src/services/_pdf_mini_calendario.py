"""
Piezas comunes de los PDF de guardias: calendario mensual, leyenda y muestras.

Antes era el mini calendario de figuras de colores (círculo = R1, cuadrado = R2) que
se solapaban con el número del día. Ahora cada día dice con palabras qué hay: recreo,
hora, turno y zona; festivos con trama y fines de semana en gris. Se lee igual en
blanco y negro.
"""

from calendar import monthcalendar
from dataclasses import dataclass, field

from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

from infrastructure.database.models import Configuracion
from services.pdf_styles import Papel, ajustar, trama
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class Bloque:
    """Lo que se escribe en un día: una guardia (individual) o un recuento (general)."""

    titulo: str
    detalle: str = ""
    etiqueta: str = ""  # a la derecha del título, p. ej. «MAÑANA»
    etiqueta_corta: str = ""  # si la larga no cabe, p. ej. «M»
    color: object = None  # color de la zona (barrita a la izquierda)


@dataclass
class DiaCalendario:
    bloques: list = field(default_factory=list)
    resaltado: bool = False  # día con guardia del destinatario


class CalendarioMes(Flowable):
    """Mes completo en rejilla L-D, con título opcional y celdas que se adaptan al tamaño."""

    def __init__(self, anio: int, mes: int, ancho: float, alto_fila: float, dias: dict,
                 no_lectivos: set, titulo: str = "", titulo_derecha: str = ""):
        super().__init__()
        self.anio, self.mes = anio, mes
        self.ancho, self.alto_fila = ancho, alto_fila
        self.dias = dias  # {dia: DiaCalendario}
        self.no_lectivos = no_lectivos  # {dia} laborables sin clase (festivos)
        self.titulo, self.titulo_derecha = titulo, titulo_derecha
        self.semanas = monthcalendar(anio, mes)
        self.col = ancho / 7
        self.escala = min(1.0, self.col / (25 * mm))
        self.grande = self.escala > 0.7
        self.alto_titulo = (9 * mm if self.grande else 7 * mm) if titulo else 0
        self.alto_cabecera = 5.5 * mm if self.grande else 4.4 * mm
        self.alto = self.alto_titulo + self.alto_cabecera + len(self.semanas) * alto_fila

    def wrap(self, *_):
        return self.ancho, self.alto

    def draw(self):
        c = self.canv
        y = self.alto
        if self.titulo:
            c.setFillColor(Papel.VERDE_OSCURO)
            c.setFont(Papel.CONDENSADA, 15 if self.grande else 11.5)
            c.drawString(0, y - self.alto_titulo + 2.6 * mm, self.titulo)
            if self.titulo_derecha:
                c.setFillColor(Papel.TINTA_SUAVE)
                c.setFont(Papel.SEMI, 8.5 if self.grande else 7)
                c.drawRightString(self.ancho, y - self.alto_titulo + 2.8 * mm,
                                  self.titulo_derecha)
            y -= self.alto_titulo

        largos = self.col >= 20 * mm
        for i, nombre in enumerate(Papel.DIAS):
            texto = nombre.upper() if largos else ("X" if i == 2 else nombre[0])
            c.setFillColor(Papel.TINTA_SUAVE if i >= 5 else Papel.TINTA)
            c.setFont(Papel.NEGRITA, 7 if largos else 6.5)
            c.drawCentredString(i * self.col + self.col / 2, y - self.alto_cabecera + 1.5 * mm,
                                texto)
        y -= self.alto_cabecera
        c.setStrokeColor(Papel.TINTA)
        c.setLineWidth(0.9)
        c.line(0, y, self.ancho, y)

        resaltados = []
        for fila, semana in enumerate(self.semanas):
            yf = y - (fila + 1) * self.alto_fila
            for i, dia in enumerate(semana):
                if dia == 0:
                    continue
                x = i * self.col
                info = self.dias.get(dia)
                self._celda(c, x, yf, dia, i, info)
                if info and info.resaltado:
                    resaltados.append((x, yf))
        # El borde grueso se pinta al final para que ninguna celda vecina lo tape
        c.setStrokeColor(Papel.VERDE_OSCURO)
        c.setLineWidth(1.7 if self.grande else 1.2)
        for x, yf in resaltados:
            c.rect(x + 0.7, yf + 0.7, self.col - 1.4, self.alto_fila - 1.4, stroke=1, fill=0)

    def _celda(self, c, x, y, dia, dia_semana, info):
        w, h, s = self.col, self.alto_fila, self.escala
        finde = dia_semana >= 5
        festivo = (not finde) and dia in self.no_lectivos
        resaltado = bool(info and info.resaltado)
        if finde:
            c.setFillColor(Papel.FINDE)
            c.rect(x, y, w, h, stroke=0, fill=1)
        elif resaltado:
            c.setFillColor(Papel.VERDE_CELDA)
            c.rect(x, y, w, h, stroke=0, fill=1)
        if festivo:
            trama(c, x, y, w, h, paso=(1.7 if self.grande else 1.3) * mm)
        c.setStrokeColor(Papel.LINEA)
        c.setLineWidth(0.5)
        c.rect(x, y, w, h, stroke=1, fill=0)

        # Número del día: en guardia, blanco sobre etiqueta oscura
        tam = 9.5 if self.grande else 7
        pad = 1.4 * mm if self.grande else 0.9 * mm
        arriba = y + h - pad
        if resaltado:
            texto = str(dia)
            bw = max(stringWidth(texto, Papel.NEGRITA, tam) + 2.2 * mm, 5.0 * mm * max(s, 0.8))
            bh = tam * 1.3
            c.setFillColor(Papel.VERDE_OSCURO)
            c.roundRect(x + pad - 0.5, arriba - bh, bw, bh, 0.9 * mm, stroke=0, fill=1)
            c.setFillColor(Papel.BLANCO)
            c.setFont(Papel.NEGRITA, tam)
            c.drawCentredString(x + pad - 0.5 + bw / 2, arriba - bh + bh * 0.27, texto)
        else:
            if festivo:  # el número no se pierde en la trama
                c.setFillColor(Papel.BLANCO)
                ancho_num = stringWidth(str(dia), Papel.SEMI, tam) + 1.2 * mm
                c.rect(x + pad - 0.6 * mm, arriba - tam * 1.2, ancho_num, tam * 1.25, stroke=0,
                       fill=1)
            c.setFillColor(Papel.TINTA_SUAVE if (finde or festivo) else Papel.TINTA)
            c.setFont(Papel.SEMI, tam)
            c.drawString(x + pad, arriba - tam * 0.95, str(dia))
        cab = tam * 1.3 + pad + 0.6 * mm

        if festivo:
            etiqueta = "No lectivo" if w >= 16 * mm else "NL"
            ft = 7 if self.grande else 5.4
            ancho_t = stringWidth(etiqueta, Papel.SEMI, ft) + 1.6 * mm
            cx, cy = x + w / 2, y + max((h - cab) / 2 - ft * 0.2, 0.8 * mm)
            c.setFillColor(Papel.BLANCO)
            c.rect(cx - ancho_t / 2, cy - ft * 0.32, ancho_t, ft * 1.22, stroke=0, fill=1)
            c.setFillColor(Papel.TINTA)
            c.setFont(Papel.SEMI, ft)
            c.drawCentredString(cx, cy, etiqueta)
            return
        if info and info.bloques:
            self._bloques(c, x, y, w, h - cab, info.bloques)

    def _bloques(self, c, x, y, w, h, bloques):
        g = self.grande
        n = len(bloques)
        hb = (h - (0.8 if g else 0.4) * mm) / n
        barra = 0.9 * mm if g else 0.6 * mm
        x_barra = x + (1.3 if g else 0.8) * mm
        x_texto = x_barra + barra + (1.0 if g else 0.6) * mm
        ancho = x + w - (1.1 if g else 0.6) * mm - x_texto
        con_detalle = bool(bloques[0].detalle)
        pt = 0.3528 * mm  # 1 pt
        # Cuerpo del título según el hueco: título (+ detalle de hasta dos líneas)
        ft = (8.4 if g else 6.4)
        necesita = (1.15 + (1.0 * 1.1 if con_detalle else 0)) * pt
        ft = max(min(ft, hb / necesita), 4.4)
        for k, b in enumerate(bloques):
            techo = y + h - k * hb
            etiqueta = b.etiqueta
            fe = max(ft * 0.7, 4.4)
            if etiqueta:
                ancho_e = stringWidth(etiqueta, Papel.NEGRITA, fe)
                if stringWidth(b.titulo, Papel.CONDENSADA, ft) + ancho_e + 1.2 * mm > ancho:
                    etiqueta = b.etiqueta_corta
                    ancho_e = stringWidth(etiqueta, Papel.NEGRITA, fe)
            else:
                ancho_e = 0
            hueco = ancho - (ancho_e + 0.9 * mm if etiqueta else 0)
            lineas, t = ajustar(b.titulo, Papel.CONDENSADA, ft, 4.4, hueco)
            base = techo - t * 0.92
            c.setFillColor(Papel.TINTA)
            c.setFont(Papel.CONDENSADA, t)
            c.drawString(x_texto, base, lineas[0])
            if etiqueta:
                c.setFillColor(Papel.TINTA_SUAVE)
                c.setFont(Papel.NEGRITA, fe)
                c.drawRightString(x_texto + ancho, base + 0.2, etiqueta)
            fondo = base
            if b.detalle:
                fd = max(ft * 0.9, 4.4)
                resto = (hb - t * 1.12 * pt) / pt
                max_lineas = max(1, min(2, int(resto / (fd * 1.12))))
                det, td = ajustar(b.detalle, Papel.MEDIA, fd, 4.4, ancho, max_lineas)
                c.setFillColor(Papel.TINTA)
                c.setFont(Papel.MEDIA, td)
                for j, linea in enumerate(det):
                    fondo = base - (j + 1) * td * 1.1
                    c.drawString(x_texto, fondo, linea)
            if b.color is not None:
                c.setFillColor(b.color)
                c.rect(x_barra, fondo - 0.5 * mm, barra, techo - fondo + 0.2 * mm, stroke=0,
                       fill=1)


class Muestra(Flowable):
    """Cuadradito de la leyenda: el mismo dibujo que la celda que explica."""

    def __init__(self, tipo: str, ancho=8 * mm, alto=5.5 * mm):
        super().__init__()
        self.tipo, self.w, self.h = tipo, ancho, alto

    def wrap(self, *_):
        return self.w, self.h

    def draw(self):
        c = self.canv
        if self.tipo == "finde":
            c.setFillColor(Papel.FINDE)
            c.rect(0, 0, self.w, self.h, stroke=0, fill=1)
        elif self.tipo == "guardia":
            c.setFillColor(Papel.VERDE_CELDA)
            c.rect(0, 0, self.w, self.h, stroke=0, fill=1)
        elif self.tipo == "festivo":
            trama(c, 0, 0, self.w, self.h, paso=1.3 * mm)
        c.setStrokeColor(Papel.LINEA)
        c.setLineWidth(0.5)
        c.rect(0, 0, self.w, self.h, stroke=1, fill=0)
        if self.tipo == "guardia":
            c.setStrokeColor(Papel.VERDE_OSCURO)
            c.setLineWidth(1.5)
            c.rect(0.7, 0.7, self.w - 1.4, self.h - 1.4, stroke=1, fill=0)
            c.setFillColor(Papel.VERDE_OSCURO)
            c.roundRect(1.3 * mm, self.h - 3.5 * mm, 3.2 * mm, 2.4 * mm, 0.5 * mm, stroke=0,
                        fill=1)


def leyenda(ancho: float, horarios: str, zonas: list | None = None,
            guardia: str = "Día con guardia") -> Table:
    """Leyenda en tabla: se parte en líneas sola, así nada se solapa."""
    texto = ParagraphStyle("ley", fontName=Papel.TEXTO, fontSize=8, leading=10.5,
                           textColor=Papel.TINTA)
    rotulo = ParagraphStyle("leyR", parent=texto, fontName=Papel.NEGRITA, fontSize=6.8,
                            textColor=Papel.TINTA_SUAVE)
    resto = ancho - 16 * mm - 3 * 10 * mm
    primera = [Paragraph("LEYENDA", rotulo)]
    if guardia:
        primera += [Muestra("guardia"), Paragraph(guardia, texto)]
    primera += [Muestra("festivo"), Paragraph("Festivo o no lectivo", texto),
                Muestra("finde"), Paragraph("Sábado y domingo", texto)]
    if not guardia:
        primera += ["", ""]
    filas = [primera]
    estilos = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("LINEABOVE", (0, 0), (-1, 0), 0.5, Papel.LINEA),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, Papel.LINEA),
    ]
    filas.append([Paragraph("RECREOS", rotulo), Paragraph(horarios, texto), "", "", "", "", ""])
    estilos.append(("SPAN", (1, 1), (-1, 1)))
    if zonas:
        partes = " &nbsp;&nbsp; ".join(
            f"<font name='ZapfDingbats' size='7' color='#{col.hexval()[2:]}'>n</font> "
            f"<b>{cod}</b> {nom}"
            for cod, nom, col in zonas
        )
        filas.append([Paragraph("ZONAS", rotulo), Paragraph(partes, texto), "", "", "", "", ""])
        estilos.append(("SPAN", (1, 2), (-1, 2)))
    tabla = Table(filas, colWidths=[16 * mm, 10 * mm, resto / 3, 10 * mm, resto / 3, 10 * mm,
                                    resto / 3])
    tabla.setStyle(TableStyle(estilos))
    return tabla


def obtener_hora_recreo(config: Configuracion, turno: str, recreo: int) -> str:
    """Hora «HH:MM» del recreo con ese id global (`services.recreos`)."""
    from services.recreos import resolver

    return resolver(config, recreo, turno).hora_texto


def texto_horarios(config) -> str:
    """«Mañana: R1 10:30 · R2 12:20   Tarde: …» con las horas que haya configuradas.

    Sale de la misma lista que resuelve cada guardia: lo que dice la leyenda es lo
    que se pinta en el calendario y en la tabla.
    """
    from services.recreos import recreos_de

    partes = []
    for turno in ("mañana", "tarde"):
        horas = [f"{r.corta} {r.hora_texto}" for r in recreos_de(config)
                 if r.turno == turno and r.hora]
        if horas:
            partes.append(f"<b>{turno.capitalize()}:</b> " + " · ".join(horas))
    return " &nbsp;&nbsp;&nbsp; ".join(partes) or "Sin horas configuradas"


def no_lectivos_del_mes(config, anio: int, mes: int) -> set:
    """Días laborables del mes, dentro del curso, que no son lectivos (festivos y puentes)."""
    from calendar import monthrange
    from datetime import date

    from services.calculador_guardias import listar_dias_lectivos

    if config is None:
        return set()
    lectivos = set(listar_dias_lectivos(config))
    dias = set()
    for d in range(1, monthrange(anio, mes)[1] + 1):
        f = date(anio, mes, d)
        if (f.weekday() < 5 and config.fecha_inicio_curso <= f <= config.fecha_fin_curso
                and f not in lectivos):
            dias.add(d)
    return dias
