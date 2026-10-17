"""
Estilos corporativos para PDFs del Sistema de Guardias de Patio.

Este módulo centraliza todos los estilos, colores y configuraciones
para garantizar consistencia visual en todos los documentos PDF generados.

Author: Sistema de Guardias de Patio
Version: 1.0
"""

from functools import lru_cache

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader, simpleSplit
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen.canvas import Canvas


def _registrar_fuentes() -> tuple[str, str, str]:
    """Registra Barlow en ReportLab; si no están los archivos, Helvetica.

    Son las tipografías de la aplicación (`imagenes/fuentes`, OFL), compartidas con
    Partes de salida. Devuelve los nombres para texto, negrita y títulos.
    """
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFError, TTFont

    try:
        from core.paths import get_resources_directory

        carpeta = get_resources_directory() / "fuentes"
        for nombre, archivo in (
            ("Barlow", "Barlow-Regular.ttf"),
            ("Barlow-Bold", "Barlow-Bold.ttf"),
            ("Barlow-SemiBold", "Barlow-SemiBold.ttf"),
            ("BarlowCondensed-Bold", "BarlowCondensed-Bold.ttf"),
            ("BarlowCondensed-SemiBold", "BarlowCondensed-SemiBold.ttf"),
            ("BarlowCondensed-ExtraBold", "BarlowCondensed-ExtraBold.ttf"),
            ("Barlow-Medium", "Barlow-Medium.ttf"),
        ):
            if nombre not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(nombre, str(carpeta / archivo)))
        if "Barlow-Italic" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("Barlow-Italic", str(carpeta / "Barlow-Italic.ttf")))
        # Sin la familia, el <b> de los párrafos no encuentra la negrita.
        pdfmetrics.registerFontFamily(
            "Barlow",
            normal="Barlow",
            bold="Barlow-Bold",
            italic="Barlow-Italic",
            boldItalic="Barlow-Bold",
        )
        return "Barlow", "Barlow-Bold", "BarlowCondensed-Bold"
    except (OSError, ImportError, TTFError):  # sin las fuentes, el PDF sale con Helvetica
        return "Helvetica", "Helvetica-Bold", "Helvetica-Bold"


_NORMAL, _NEGRITA, _TITULO = _registrar_fuentes()


class PDFStyles:
    """Estilos corporativos estandarizados para PDFs."""

    # ==========================================
    # PALETA DE COLORES CORPORATIVA
    # ==========================================
    # La de la aplicación (y de Partes de salida): verde EPLA, dorado y neutros que
    # tiran al verde. Los nombres AZUL_* se conservan porque los usan los generadores.

    VERDE = colors.HexColor("#2C7A3A")
    VERDE_OSCURO = colors.HexColor("#1C5226")
    VERDE_SUAVE = colors.HexColor("#E2F0E3")
    DORADO = colors.HexColor("#B97A12")
    DORADO_SUAVE = colors.HexColor("#FBF0D9")
    LINEA = colors.HexColor("#D9E0D5")

    AZUL_PRINCIPAL = VERDE  # cabeceras y banda del título
    AZUL_OSCURO = VERDE_OSCURO  # filete inferior de la banda
    AZUL_CLARO = VERDE_SUAVE

    # Datos destacados sobre la banda verde: dorado claro (4,6:1 sobre el verde)
    COLOR_DATO_PRINCIPAL = colors.HexColor("#F5D58A")
    COLOR_DATO_SECUNDARIO = colors.HexColor("#F8E2AE")
    COLOR_DATO_TERCIARIO = colors.HexColor("#FBF0D9")

    # Colores para zonas (hasta 10): distintos entre sí, pero de la misma familia
    # apagada que la aplicación, y oscuros para leerse como texto sobre fondo claro.
    COLORES_ZONAS = {
        1: colors.HexColor("#A32D2D"),  # Rojo
        2: colors.HexColor("#2E6B8A"),  # Azul
        3: colors.HexColor("#2C7A3A"),  # Verde
        4: colors.HexColor("#B97A12"),  # Dorado
        5: colors.HexColor("#6B4E8A"),  # Morado
        6: colors.HexColor("#2E6B73"),  # Verde azulado
        7: colors.HexColor("#B4561C"),  # Terracota
        8: colors.HexColor("#46524A"),  # Gris verdoso
        9: colors.HexColor("#B0456E"),  # Rosa
        10: colors.HexColor("#3F8FA6"),  # Cian
    }

    # Colores para recreos (diferenciación visual)
    COLORES_RECREOS = {
        1: colors.HexColor("#2C7A3A"),  # Verde
        2: colors.HexColor("#B97A12"),  # Dorado
        3: colors.HexColor("#6B4E8A"),  # Morado
        4: colors.HexColor("#A32D2D"),  # Rojo
    }

    # Colores para separación de meses: tintes muy suaves de la paleta
    COLORES_MESES_ALTERNOS = [
        colors.HexColor("#E2F0E3"),  # Verde
        colors.HexColor("#FBF0D9"),  # Crema
        colors.HexColor("#E3EDF2"),  # Azul
        colors.HexColor("#F6E3EA"),  # Rosa
        colors.HexColor("#EEF2EC"),  # Gris verdoso
    ]

    # Colores de texto
    TEXTO_OSCURO = colors.HexColor("#1D2A20")
    TEXTO_MEDIO = colors.HexColor("#2F3B32")
    TEXTO_GRIS = colors.HexColor("#5D6B60")
    TEXTO_AVISO = colors.HexColor("#A32D2D")

    # Fondos
    FONDO_CLARO = colors.HexColor("#F3F5F1")
    FONDO_TABLA_HEADER = AZUL_PRINCIPAL
    FONDO_TABLA_ALTERNADO_1 = colors.white
    FONDO_TABLA_ALTERNADO_2 = colors.HexColor("#F3F5F1")

    # ==========================================
    # DIMENSIONES Y MÁRGENES
    # ==========================================

    PAGESIZE = landscape(A4)
    MARGEN_SUPERIOR = 1 * cm
    MARGEN_INFERIOR = 1 * cm
    MARGEN_IZQUIERDO = 1 * cm
    MARGEN_DERECHO = 1 * cm

    # ==========================================
    # TIPOGRAFÍA
    # ==========================================

    FUENTE_TITULO = _TITULO
    FUENTE_SUBTITULO = _TITULO
    FUENTE_NORMAL = _NORMAL
    FUENTE_NEGRITA = _NEGRITA

    TAMANO_TITULO_PRINCIPAL = 18
    TAMANO_SUBTITULO = 14
    TAMANO_TEXTO_NORMAL = 10
    TAMANO_TEXTO_PEQUENO = 8
    TAMANO_ENCABEZADO_TABLA = 10
    TAMANO_CUERPO_TABLA = 9

    @classmethod
    def pie_de_pagina(cls, canvas, doc):
        """Pie común: filete dorado, nombre de la aplicación y número de página."""
        ancho, _ = doc.pagesize
        y = doc.bottomMargin * 0.55
        canvas.saveState()
        canvas.setStrokeColor(cls.DORADO)
        canvas.setLineWidth(0.8)
        canvas.line(doc.leftMargin, y + 9, ancho - doc.rightMargin, y + 9)
        canvas.setFillColor(cls.TEXTO_GRIS)
        canvas.setFont(cls.FUENTE_NORMAL, 7.5)
        canvas.drawString(doc.leftMargin, y, "Guardias de Patio · EPLA")
        canvas.drawRightString(ancho - doc.rightMargin, y, f"Página {canvas.getPageNumber()}")
        canvas.restoreState()

    @classmethod
    def tabla_estandar(cls, cabecera_filas: int = 1) -> list:
        """Estilo de tabla común: cabecera verde, filas alternas y líneas finas."""
        return [
            ("BACKGROUND", (0, 0), (-1, cabecera_filas - 1), cls.FONDO_TABLA_HEADER),
            ("TEXTCOLOR", (0, 0), (-1, cabecera_filas - 1), colors.white),
            ("FONTNAME", (0, 0), (-1, cabecera_filas - 1), cls.FUENTE_NEGRITA),
            ("TEXTCOLOR", (0, cabecera_filas), (-1, -1), cls.TEXTO_OSCURO),
            ("FONTNAME", (0, cabecera_filas), (-1, -1), cls.FUENTE_NORMAL),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, cls.LINEA),
            ("BOX", (0, 0), (-1, -1), 0.6, cls.LINEA),
            (
                "ROWBACKGROUNDS",
                (0, cabecera_filas),
                (-1, -1),
                [cls.FONDO_TABLA_ALTERNADO_1, cls.FONDO_TABLA_ALTERNADO_2],
            ),
        ]

    @classmethod
    def get_base_styles(cls):
        """
        Retorna estilos base de reportlab configurados.

        Returns:
            StyleSheet con estilos predefinidos
        """
        return getSampleStyleSheet()

    @classmethod
    def get_titulo_principal(cls, texto_color=None):
        """
        Estilo para título principal del documento.

        Args:
            texto_color: Color del texto (opcional, por defecto blanco)

        Returns:
            ParagraphStyle configurado
        """
        styles = cls.get_base_styles()
        return ParagraphStyle(
            "TituloPrincipal",
            parent=styles["Heading1"],
            fontSize=cls.TAMANO_TITULO_PRINCIPAL,
            textColor=texto_color or colors.white,
            fontName=cls.FUENTE_TITULO,
            spaceAfter=12,
            alignment=1,  # Centrado
        )

    @classmethod
    def get_subtitulo(cls, texto_color=None):
        """
        Estilo para subtítulos.

        Args:
            texto_color: Color del texto (opcional)

        Returns:
            ParagraphStyle configurado
        """
        styles = cls.get_base_styles()
        return ParagraphStyle(
            "Subtitulo",
            parent=styles["Heading2"],
            fontSize=cls.TAMANO_SUBTITULO,
            textColor=texto_color or cls.TEXTO_OSCURO,
            fontName=cls.FUENTE_SUBTITULO,
            spaceAfter=10,
            alignment=1,
        )

    @classmethod
    def get_texto_normal(cls, texto_color=None, alineacion=0):
        """
        Estilo para texto normal.

        Args:
            texto_color: Color del texto (opcional)
            alineacion: 0=izquierda, 1=centro, 2=derecha

        Returns:
            ParagraphStyle configurado
        """
        styles = cls.get_base_styles()
        return ParagraphStyle(
            "TextoNormal",
            parent=styles["Normal"],
            fontSize=cls.TAMANO_TEXTO_NORMAL,
            textColor=texto_color or cls.TEXTO_OSCURO,
            fontName=cls.FUENTE_NORMAL,
            alignment=alineacion,
        )

    @classmethod
    def get_texto_pequeno(cls, texto_color=None, alineacion=0):
        """
        Estilo para texto pequeño (pies de página, notas).

        Args:
            texto_color: Color del texto (opcional)
            alineacion: 0=izquierda, 1=centro, 2=derecha

        Returns:
            ParagraphStyle configurado
        """
        styles = cls.get_base_styles()
        return ParagraphStyle(
            "TextoPequeno",
            parent=styles["Normal"],
            fontSize=cls.TAMANO_TEXTO_PEQUENO,
            textColor=texto_color or cls.TEXTO_GRIS,
            fontName=cls.FUENTE_NORMAL,
            alignment=alineacion,
        )

    @classmethod
    def get_color_zona(cls, zona_id):
        """
        Obtiene el color para una zona específica.

        Args:
            zona_id: ID de la zona

        Returns:
            Color asignado a la zona
        """
        if zona_id is None:
            return colors.grey

        # Si hay más de 10 zonas, reciclar colores
        zona_num = ((zona_id - 1) % 10) + 1
        return cls.COLORES_ZONAS.get(zona_num, colors.grey)

    @classmethod
    def get_color_recreo(cls, recreo):
        """
        Obtiene el color para un recreo específico.

        Args:
            recreo: Número de recreo (1, 2, 3, 4)

        Returns:
            Color asignado al recreo
        """
        return cls.COLORES_RECREOS.get(recreo, colors.grey)

    @classmethod
    def get_color_mes(cls, mes_index):
        """
        Obtiene el color de fondo para un mes específico.

        Args:
            mes_index: Índice del mes (0, 1, 2, ...)

        Returns:
            Color de fondo para el mes
        """
        return cls.COLORES_MESES_ALTERNOS[mes_index % len(cls.COLORES_MESES_ALTERNOS)]

    @classmethod
    def get_meses_nombres(cls):
        """
        Retorna lista con nombres de meses en español.

        Returns:
            Lista de strings con nombres de meses
        """
        return [
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

    @classmethod
    def get_dias_semana_completos(cls):
        """
        Retorna lista con nombres completos de días de la semana.

        Returns:
            Lista de strings con días de la semana
        """
        return ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    @classmethod
    def get_dias_semana_cortos(cls):
        """
        Retorna lista con nombres cortos de días de la semana.

        Returns:
            Lista de strings con días de la semana abreviados
        """
        return ["L", "M", "X", "J", "V", "S", "D"]


# ==========================================
# DOCUMENTO IMPRESO (A4 vertical, estilo Partes de salida)
# ==========================================
# El papel no sigue el tema: tinta oscura sobre blanco. Todo lo que distingue algo
# (guardia, festivo, fin de semana, recreo, zona) lleva también texto, borde o trama,
# para que se lea igual impreso en blanco y negro.

_CONDENSADA = "BarlowCondensed-Bold" if _NORMAL == "Barlow" else "Helvetica-Bold"


class Papel:
    """Tintas y medidas del documento impreso."""

    TINTA = colors.HexColor("#1b1f1c")
    TINTA_SUAVE = colors.HexColor("#5a625c")
    LINEA = colors.HexColor("#c9d1c5")
    LINEA_SUAVE = colors.HexColor("#e1e6dd")
    FONDO = colors.HexColor("#f3f5f1")
    FINDE = colors.HexColor("#e4e7e1")
    TRAMA = colors.HexColor("#8f988f")
    VERDE = colors.HexColor("#2c7a3a")
    VERDE_OSCURO = colors.HexColor("#1c5226")
    VERDE_SUAVE = colors.HexColor("#e2f0e3")
    VERDE_CELDA = colors.HexColor("#eef6ee")  # día con guardia: en gris queda casi blanco
    DORADO = colors.HexColor("#b97a12")
    DORADO_SUAVE = colors.HexColor("#fbf0d9")
    BLANCO = colors.white

    TEXTO = _NORMAL
    MEDIA = "Barlow-Medium" if _NORMAL == "Barlow" else _NORMAL
    SEMI = "Barlow-SemiBold" if _NORMAL == "Barlow" else _NEGRITA
    NEGRITA = _NEGRITA
    CONDENSADA = _CONDENSADA
    CONDENSADA_SEMI = "BarlowCondensed-SemiBold" if _NORMAL == "Barlow" else _NEGRITA
    TITULAR = "BarlowCondensed-ExtraBold" if _NORMAL == "Barlow" else _NEGRITA

    PAGINA = A4
    MARGEN_X = 15 * mm
    MARGEN_ARRIBA = 14 * mm
    MARGEN_ARRIBA_RESTO = 24 * mm
    MARGEN_ABAJO = 19 * mm
    AUTOR = "EPLA · Guardias de patio"

    MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
             "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def ajustar(texto: str, fuente: str, tam: float, tam_min: float, ancho: float,
            lineas: int = 1) -> tuple[list[str], float]:
    """Parte y encoge el texto hasta que cabe en `lineas` de `ancho`; nunca lo recorta
    salvo que ni al cuerpo mínimo quepa (entonces la última línea acaba en «…»)."""
    t = tam
    while True:
        partes = simpleSplit(texto, fuente, t, ancho)
        if len(partes) <= lineas and all(stringWidth(p, fuente, t) <= ancho for p in partes):
            return partes, t
        if t - 0.25 < tam_min:
            break
        t -= 0.25
    partes = simpleSplit(texto, fuente, tam_min, ancho)[:lineas]
    ultima = partes[-1]
    while ultima and stringWidth(ultima + "…", fuente, tam_min) > ancho:
        ultima = ultima[:-1]
    partes[-1] = ultima.rstrip() + "…"
    return partes, tam_min


# Logos ya reducidos y sobre blanco (JPEG): ReportLab los lee sin Pillow y el adjunto
# no lleva los originales de varios MB. El escudo grande (`logo.png`) es el de la app.
LOGO_IZQUIERDO = "escudo_epla_documentos.jpg"
LOGO_DERECHO = "logo_colegios_amigo.jpg"


@lru_cache(maxsize=4)
def logo(nombre: str):
    """Logo de `imagenes/` listo para dibujar, o None si falta (el PDF sale sin él)."""
    try:
        from core.paths import get_resources_directory

        ruta = get_resources_directory() / nombre
        return ImageReader(str(ruta)) if ruta.is_file() else None
    except OSError:
        return None


def dibujar_logo(c, nombre: str, x: float, y: float, ancho: float, alto: float,
                 alinear: str = "izquierda") -> None:
    img = logo(nombre)
    if img is None:
        return
    iw, ih = img.getSize()
    escala = min(ancho / iw, alto / ih)
    w, h = iw * escala, ih * escala
    dx = 0 if alinear == "izquierda" else (ancho - w if alinear == "derecha" else (ancho - w) / 2)
    c.drawImage(img, x + dx, y + (alto - h) / 2, w, h)


def trama(c, x: float, y: float, w: float, h: float, paso: float = 1.7 * mm) -> None:
    """Rayado diagonal (festivos y días no lectivos): se distingue sin color."""
    c.saveState()
    p = c.beginPath()
    p.rect(x, y, w, h)
    c.clipPath(p, stroke=0, fill=0)
    c.setStrokeColor(Papel.TRAMA)
    c.setLineWidth(0.45)
    d = -h
    while d < w:
        c.line(x + d, y, x + d + h, y + h)
        d += paso
    c.restoreState()


def dibujar_cabecera(c, titulo: str, subtitulo: str, x0: float, x1: float, arriba: float) -> float:
    """Cabecera de la primera página: escudo, título, subtítulo y Colegios Amigó.

    Devuelve la altura ocupada (para el marco de la página).
    """
    alto_logo = 17 * mm
    y = arriba - alto_logo
    dibujar_logo(c, LOGO_IZQUIERDO, x0, y, alto_logo, alto_logo)
    dibujar_logo(c, LOGO_DERECHO, x1 - 31 * mm, y + 1.5 * mm, 31 * mm, 14 * mm,
                 "derecha")
    centro = (x0 + x1) / 2
    ancho = (x1 - x0) - 2 * 36 * mm
    lineas, t = ajustar(titulo, Papel.TITULAR, 22, 14, ancho)
    c.setFillColor(Papel.TINTA)
    c.setFont(Papel.TITULAR, t)
    c.drawCentredString(centro, arriba - 9.2 * mm, lineas[0])
    c.setFont(Papel.TEXTO, 8.6)
    c.setFillColor(Papel.TINTA_SUAVE)
    c.drawCentredString(centro, arriba - 14.6 * mm, subtitulo)
    base = y - 3 * mm
    c.setFillColor(Papel.VERDE)
    c.rect(x0, base, x1 - x0, 1.1 * mm, stroke=0, fill=1)
    c.setFillColor(Papel.DORADO)
    c.rect(x0, base - 0.9 * mm, x1 - x0, 0.45 * mm, stroke=0, fill=1)
    return arriba - (base - 0.9 * mm)


def dibujar_cabecera_resto(c, izquierda: str, derecha: str, x0: float, x1: float,
                           arriba: float) -> None:
    """Cabecera corta de las páginas siguientes: quién y de qué, por si la hoja va suelta."""
    dibujar_logo(c, LOGO_IZQUIERDO, x0, arriba - 8 * mm, 8 * mm, 8 * mm)
    ancho = (x1 - x0) - 10 * mm - 45 * mm
    lineas, t = ajustar(izquierda, Papel.CONDENSADA, 11, 7.5, ancho)
    c.setFont(Papel.CONDENSADA, t)
    c.setFillColor(Papel.TINTA)
    c.drawString(x0 + 10 * mm, arriba - 5.4 * mm, lineas[0])
    c.setFont(Papel.TEXTO, 8)
    c.setFillColor(Papel.TINTA_SUAVE)
    c.drawRightString(x1, arriba - 5.4 * mm, derecha)
    c.setStrokeColor(Papel.VERDE)
    c.setLineWidth(0.8)
    c.line(x0, arriba - 10 * mm, x1, arriba - 10 * mm)


class CanvasNumerado(Canvas):
    """Canvas que conoce el total de páginas para el pie «Página n de N»."""

    def __init__(self, *args, pie_izquierda: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._paginas = []
        self.pie_izquierda = pie_izquierda

    def showPage(self):
        self._paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._paginas)
        for estado in self._paginas:
            self.__dict__.update(estado)
            self._pie(total)
            super().showPage()
        super().save()

    def _pie(self, total: int) -> None:
        ancho, _ = self._pagesize
        x0, x1 = Papel.MARGEN_X, ancho - Papel.MARGEN_X
        y = 11 * mm
        self.saveState()
        self.setStrokeColor(Papel.DORADO)
        self.setLineWidth(0.7)
        self.line(x0, y + 3.6 * mm, x1, y + 3.6 * mm)
        self.setFillColor(Papel.TINTA_SUAVE)
        self.setFont(Papel.TEXTO, 7.5)
        self.drawString(x0, y, self.pie_izquierda)
        self.setFont(Papel.SEMI, 7.5)
        self.drawRightString(x1, y, f"Página {self._pageNumber} de {total}")
        self.restoreState()


def canvas_con_pie(pie_izquierda: str):
    def fabrica(*args, **kwargs):
        return CanvasNumerado(*args, pie_izquierda=pie_izquierda, **kwargs)

    return fabrica


def construir_documento(ruta: str, piezas: list, *, titulo: str, subtitulo: str,
                        resto_izquierda: str, resto_derecha: str, pie: str,
                        titulo_pdf: str, asunto: str, pagesize=A4) -> None:
    """Documento A4 con cabecera completa en la primera página y corta en las demás."""
    from reportlab.platypus import BaseDocTemplate, Frame, NextPageTemplate, PageTemplate

    ancho, alto = pagesize
    x0, x1 = Papel.MARGEN_X, ancho - Papel.MARGEN_X
    alto_cabecera = 26 * mm

    def primera(c, _doc):
        c.saveState()
        dibujar_cabecera(c, titulo, subtitulo, x0, x1, alto - Papel.MARGEN_ARRIBA)
        c.restoreState()

    def resto(c, _doc):
        c.saveState()
        dibujar_cabecera_resto(c, resto_izquierda, resto_derecha, x0, x1,
                               alto - Papel.MARGEN_ARRIBA)
        c.restoreState()

    abajo = Papel.MARGEN_ABAJO
    marco1 = Frame(x0, abajo, x1 - x0, alto - Papel.MARGEN_ARRIBA - alto_cabecera - abajo,
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="primera")
    marco2 = Frame(x0, abajo, x1 - x0, alto - Papel.MARGEN_ARRIBA_RESTO - abajo,
                   leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0, id="resto")
    doc = BaseDocTemplate(
        ruta, pagesize=pagesize, leftMargin=x0, rightMargin=x0,
        topMargin=Papel.MARGEN_ARRIBA, bottomMargin=abajo,
        title=titulo_pdf, author=Papel.AUTOR, subject=asunto, creator=Papel.AUTOR,
        producer=Papel.AUTOR, keywords="",
    )
    doc.addPageTemplates([
        PageTemplate(id="primera", frames=[marco1], onPage=primera),
        PageTemplate(id="resto", frames=[marco2], onPage=resto),
    ])
    doc.build([NextPageTemplate("resto")] + piezas, canvasmaker=canvas_con_pie(pie))


# --- Abreviatura de las zonas ----------------------------------------------------

_PALABRAS_VACIAS = {"de", "del", "la", "el", "los", "las", "y", "e"}


def abreviatura_zona(nombre: str) -> str:
    """La abreviatura de una zona para los calendarios compactos.

    El nombre tal cual si es corto (hasta 4 caracteres: «Z2», «Gim»);
    si no, las iniciales de sus palabras («Patio Norte» → «PN», «Patio 2» → «P2») o
    las tres primeras letras («Gimnasio» → «GIM»). Siempre la misma para el mismo
    nombre, en todos los PDF.
    """
    import re
    import unicodedata

    limpio = " ".join(str(nombre or "").split())
    if 0 < len(limpio) <= 4:
        return limpio
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", limpio) if unicodedata.category(c) != "Mn"
    )
    palabras = re.findall(r"[0-9A-Za-z]+", sin_tildes)
    utiles = [w for w in palabras if w.lower() not in _PALABRAS_VACIAS] or palabras
    if not utiles:
        return "Z"
    if len(utiles) == 1:
        return utiles[0][:3].upper()
    return "".join(w if w.isdigit() else w[0] for w in utiles)[:4].upper()


def abreviaturas_de_zonas(zonas) -> dict:
    """{id de zona: abreviatura}, sin repetidas: si dos coinciden, llevan su id detrás.

    Se calcula sobre todas las zonas del centro, no solo las de un PDF, para que una
    zona se abrevie igual en cualquier documento.
    """
    propuestas = {z.id: abreviatura_zona(z.nombre_zona) for z in zonas}
    cuentas: dict = {}
    for abrev in propuestas.values():
        cuentas[abrev] = cuentas.get(abrev, 0) + 1
    return {
        id_: (abrev if cuentas[abrev] == 1 else f"{abrev}{id_}")
        for id_, abrev in propuestas.items()
    }


def zona_para_leyenda(zona, abrev: str) -> str:
    """Lo que acompaña a la abreviatura en la leyenda: nombre (si no es ella) y descripción."""
    partes = []
    if zona.nombre_zona and zona.nombre_zona.strip() != abrev:
        partes.append(zona.nombre_zona.strip())
    if getattr(zona, "descripcion", None):
        partes.append(zona.descripcion.strip())
    return " — ".join(partes)

