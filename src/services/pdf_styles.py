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


class PDFStyles:
    """Estilos corporativos estandarizados para PDFs."""

    # ==========================================
    # PALETA DE COLORES CORPORATIVA
    # ==========================================

    # Azules principales (fondo de encabezados)
    AZUL_PRINCIPAL = colors.HexColor('#1976D2')      # Azul primario
    AZUL_OSCURO = colors.HexColor('#0D47A1')         # Azul oscuro para bordes
    AZUL_CLARO = colors.HexColor('#E3F2FD')          # Azul muy claro para texto sobre azul

    # Colores para datos dinámicos (compatibles con fondo azul)
    COLOR_DATO_PRINCIPAL = colors.HexColor('#FFD54F')   # Amarillo/dorado (destaca mucho)
    COLOR_DATO_SECUNDARIO = colors.HexColor('#FFE082')  # Amarillo más claro
    COLOR_DATO_TERCIARIO = colors.HexColor('#FFF59D')   # Amarillo pastel

    # Colores para zonas (hasta 10 zonas diferentes)
    COLORES_ZONAS = {
        1: colors.HexColor('#e74c3c'),   # Rojo
        2: colors.HexColor('#3498db'),   # Azul
        3: colors.HexColor('#2ecc71'),   # Verde
        4: colors.HexColor('#f39c12'),   # Naranja
        5: colors.HexColor('#9b59b6'),   # Morado
        6: colors.HexColor('#1abc9c'),   # Turquesa
        7: colors.HexColor('#e67e22'),   # Naranja oscuro
        8: colors.HexColor('#34495e'),   # Gris oscuro
        9: colors.HexColor('#e91e63'),   # Rosa
        10: colors.HexColor('#00bcd4'),  # Cian
    }

    # Colores para recreos (diferenciación visual)
    COLORES_RECREOS = {
        1: colors.HexColor('#4CAF50'),   # Verde
        2: colors.HexColor('#FF9800'),   # Naranja
        3: colors.HexColor('#9C27B0'),   # Morado
        4: colors.HexColor('#F44336'),   # Rojo
    }

    # Colores para separación de meses
    COLORES_MESES_ALTERNOS = [
        colors.HexColor('#E8F5E9'),  # Verde muy claro
        colors.HexColor('#E3F2FD'),  # Azul muy claro
        colors.HexColor('#FFF3E0'),  # Naranja muy claro
        colors.HexColor('#F3E5F5'),  # Morado muy claro
        colors.HexColor('#E0F2F1'),  # Turquesa muy claro
    ]

    # Colores de texto
    TEXTO_OSCURO = colors.HexColor('#2c3e50')
    TEXTO_MEDIO = colors.HexColor('#34495e')
    TEXTO_GRIS = colors.grey

    # Fondos
    FONDO_CLARO = colors.HexColor('#f8f9fa')
    FONDO_TABLA_HEADER = AZUL_PRINCIPAL
    FONDO_TABLA_ALTERNADO_1 = colors.white
    FONDO_TABLA_ALTERNADO_2 = colors.HexColor('#f5f5f5')

    # ==========================================
    # DIMENSIONES Y MÁRGENES
    # ==========================================

    PAGESIZE = landscape(A4)
    MARGEN_SUPERIOR = 1*cm
    MARGEN_INFERIOR = 1*cm
    MARGEN_IZQUIERDO = 1*cm
    MARGEN_DERECHO = 1*cm

    # ==========================================
    # TIPOGRAFÍA
    # ==========================================

    FUENTE_TITULO = 'Helvetica-Bold'
    FUENTE_SUBTITULO = 'Helvetica-Bold'
    FUENTE_NORMAL = 'Helvetica'
    FUENTE_NEGRITA = 'Helvetica-Bold'

    TAMANO_TITULO_PRINCIPAL = 18
    TAMANO_SUBTITULO = 14
    TAMANO_TEXTO_NORMAL = 10
    TAMANO_TEXTO_PEQUENO = 8
    TAMANO_ENCABEZADO_TABLA = 10
    TAMANO_CUERPO_TABLA = 9

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
            'TituloPrincipal',
            parent=styles['Heading1'],
            fontSize=cls.TAMANO_TITULO_PRINCIPAL,
            textColor=texto_color or colors.whitesmoke,
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
            'Subtitulo',
            parent=styles['Heading2'],
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
            'TextoNormal',
            parent=styles['Normal'],
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
            'TextoPequeno',
            parent=styles['Normal'],
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
        return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

    @classmethod
    def get_dias_semana_cortos(cls):
        """
        Retorna lista con nombres cortos de días de la semana.

        Returns:
            Lista de strings con días de la semana abreviados
        """
        return ['L', 'M', 'X', 'J', 'V', 'S', 'D']
