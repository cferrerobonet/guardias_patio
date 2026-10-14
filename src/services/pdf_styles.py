"""
Estilos corporativos para PDFs del Sistema de Guardias de Patio.

Este módulo centraliza todos los estilos, colores y configuraciones
para garantizar consistencia visual en todos los documentos PDF generados.

Author: Sistema de Guardias de Patio
Version: 1.0
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm


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
