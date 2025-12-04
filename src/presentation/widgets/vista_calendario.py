"""
Vista de calendario mejorada para visualizar guardias asignadas.

Características:
- Vistas: Mensual, Semanal, Anual
- Navegación intuitiva con controles claros
- Celdas con scroll para mostrar todas las guardias (hasta 16+)
- Indicadores visuales de ausencias y sustituciones
- Diseño optimizado para aprovechamiento de espacio
"""

import json
from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from core.logging import get_logger
from infrastructure.database.models import Ausencia, Configuracion, Guardia, Zona
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from services.calculador_guardias import listar_dias_lectivos

from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog
from presentation.forms.base_form import BaseForm


class CeldaDia(QGroupBox):
    """Celda individual para un día del calendario con scroll interno."""

    dia_clicked = pyqtSignal(date)  # Señal cuando se hace click en el día

    def __init__(
        self,
        fecha: date,
        guardias: List[Guardia],
        ausencias: List[Ausencia],
        sustituciones: List[Guardia],
        zonas_esperadas_por_recreo: Dict[Tuple[str, int], List[Zona]] = None,
        es_dia_lectivo: bool = True,
        es_hoy: bool = False,
    ):
        """
        Inicializar celda de día.

        Args:
            fecha: Fecha del día
            guardias: Lista de guardias del día
            ausencias: Lista de ausencias del día
            sustituciones: Lista de sustituciones del día
            zonas_esperadas_por_recreo: Dict con zonas esperadas por (turno, recreo)
            es_dia_lectivo: Si el día es lectivo (no festivo, no fin de semana)
            es_hoy: Si es el día actual
        """
        super().__init__()
        self.fecha = fecha
        self.guardias = guardias
        self.ausencias = ausencias
        self.sustituciones = sustituciones
        self.zonas_esperadas_por_recreo = zonas_esperadas_por_recreo or {}
        self.es_dia_lectivo = es_dia_lectivo
        self.es_hoy = es_hoy

        self.setup_ui()

    def setup_ui(self):
        """Construir interfaz de la celda."""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(4, 4, 4, 4)
        layout_principal.setSpacing(2)

        # Encabezado con número del día e indicadores
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        # Número del día
        label_dia = QLabel(str(self.fecha.day))
        font_dia = QFont()
        font_dia.setBold(True)
        font_dia.setPointSize(11)
        label_dia.setFont(font_dia)
        header_layout.addWidget(label_dia)

        # Indicadores de estado
        indicadores = []
        if self.ausencias:
            indicadores.append(f"🏥{len(self.ausencias)}")
        if self.sustituciones:
            indicadores.append(f"🔄{len(self.sustituciones)}")

        if indicadores:
            label_indicadores = QLabel(" ".join(indicadores))
            label_indicadores.setStyleSheet("font-size: 9px; color: #666;")
            header_layout.addWidget(label_indicadores)

        header_layout.addStretch()
        layout_principal.addLayout(header_layout)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #ccc; max-height: 1px;")
        layout_principal.addWidget(separador)

        # Área de scroll para guardias
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(600)  # Aumentado para vista semanal

        # Contenedor de guardias
        guardias_widget = QWidget()
        guardias_layout = QVBoxLayout()
        guardias_layout.setContentsMargins(2, 2, 2, 2)
        guardias_layout.setSpacing(3)

        # Mostrar todas las guardias agrupadas por turno y recreo
        self._agregar_guardias_agrupadas(guardias_layout)

        # Mostrar ausencias si hay
        if self.ausencias:
            self._agregar_ausencias(guardias_layout)

        guardias_layout.addStretch()
        guardias_widget.setLayout(guardias_layout)
        scroll_area.setWidget(guardias_widget)

        layout_principal.addWidget(scroll_area, 1)

        # Contador total al final
        total_guardias = len(self.guardias)
        if total_guardias > 0:
            label_total = QLabel(f"Total: {total_guardias} guardias")
            label_total.setStyleSheet("font-size: 8px; color: #999; font-weight: bold;")
            label_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_principal.addWidget(label_total)

        self.setLayout(layout_principal)

        # Aplicar estilo según estado
        self._aplicar_estilo()

    def _agregar_guardias_agrupadas(self, layout: QVBoxLayout):
        """Agregar guardias agrupadas por turno y recreo, ordenadas por zona."""
        # No mostrar nada en días no lectivos (festivos, fines de semana)
        if not self.es_dia_lectivo:
            return

        # Agrupar guardias por turno y recreo
        grupos = defaultdict(list)
        for guardia in self.guardias:
            clave = (guardia.turno, guardia.recreo)
            grupos[clave].append(guardia)

        # Ordenar por turno (mañana primero) y recreo
        orden_turno = {"mañana": 0, "tarde": 1}
        claves_ordenadas = sorted(grupos.keys(), key=lambda x: (orden_turno.get(x[0], 2), x[1]))

        # Si tenemos zonas esperadas, agregar también los grupos sin guardias
        if self.zonas_esperadas_por_recreo:
            for clave in self.zonas_esperadas_por_recreo.keys():
                if clave not in claves_ordenadas:
                    claves_ordenadas.append(clave)
            # Re-ordenar
            claves_ordenadas = sorted(
                claves_ordenadas, key=lambda x: (orden_turno.get(x[0], 2), x[1])
            )

        for turno, recreo in claves_ordenadas:
            guardias_grupo = grupos.get((turno, recreo), [])

            # Ordenar guardias del grupo por zona (Z1, Z2, Z3, Z4)
            guardias_ordenadas = sorted(
                guardias_grupo,
                key=lambda g: (
                    int(g.zona.nombre_zona[1])
                    if g.zona and g.zona.nombre_zona.startswith("Z")
                    else 999
                ),
            )

            # Encabezado del grupo
            icono_turno = "☀" if turno == "mañana" else "🌙"
            label_grupo = QLabel(f"{icono_turno} Recreo {recreo} ({turno})")
            label_grupo.setStyleSheet(
                "font-size: 9px; font-weight: bold; color: #1565C0; "
                "background-color: #E3F2FD; padding: 3px 5px; border-radius: 2px;"
            )
            layout.addWidget(label_grupo)

            # Detectar zonas faltantes
            zonas_con_guardia = {g.zona_id for g in guardias_ordenadas if g.zona_id}
            zonas_esperadas = self.zonas_esperadas_por_recreo.get((turno, recreo), [])
            zonas_faltantes = [z for z in zonas_esperadas if z.id not in zonas_con_guardia]

            # Guardias del grupo ordenadas por zona
            for guardia in guardias_ordenadas:
                self._agregar_guardia_individual(layout, guardia)

            # Mostrar zonas faltantes solo en días lectivos
            if self.es_dia_lectivo:
                for zona in zonas_faltantes:
                    self._agregar_zona_sin_guardia(layout, zona)

    def _agregar_guardia_individual(self, layout: QVBoxLayout, guardia: Guardia):
        """Agregar una guardia individual con mejor diseño."""
        # Obtener información
        profesor_nombre = guardia.profesor.nombre_completo if guardia.profesor else "Sin asignar"
        zona_nombre = guardia.zona.nombre_zona if guardia.zona else "??"

        # Formatear nombre: "Apellido, Nombre" completo
        nombre_mostrar = profesor_nombre

        # Determinar si es sustitución
        es_sustitucion = guardia in self.sustituciones

        # Crear widget contenedor con layout horizontal
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(3, 2, 3, 2)
        h_layout.setSpacing(5)

        # Badge de zona (más compacto y visible)
        zona_label = QLabel(zona_nombre)
        zona_label.setStyleSheet("""
            background-color: #1976D2;
            color: white;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 2px;
            min-width: 18px;
        """)
        zona_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(zona_label)

        # Nombre del profesor completo
        nombre_label = QLabel(nombre_mostrar)
        nombre_label.setStyleSheet("font-size: 8px; color: #333;")
        h_layout.addWidget(nombre_label, 1)

        if es_sustitucion:
            # Indicador de sustitución
            sust_label = QLabel("🔄")
            sust_label.setStyleSheet("font-size: 8px;")
            sust_label.setToolTip("Sustitución")
            h_layout.addWidget(sust_label)

        # Estilo del widget según sea sustitución o no
        if es_sustitucion:
            widget.setStyleSheet("""
                QWidget {
                    background-color: #FFF3E0;
                    border-left: 3px solid #FF9800;
                    border-radius: 3px;
                    margin: 1px 0px;
                }
            """)
            widget.setToolTip(f"SUSTITUCIÓN: {profesor_nombre} en {zona_nombre}")
        else:
            widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-left: 2px solid #4CAF50;
                    border-radius: 2px;
                    margin: 1px 0px;
                }
            """)
            widget.setToolTip(f"{profesor_nombre} en {zona_nombre}")

        layout.addWidget(widget)

    def _agregar_zona_sin_guardia(self, layout: QVBoxLayout, zona: Zona):
        """Agregar un indicador visual de zona sin guardia asignada."""
        # Crear widget contenedor con layout horizontal
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(3, 2, 3, 2)
        h_layout.setSpacing(5)

        # Badge de zona con color de advertencia
        zona_label = QLabel(zona.nombre_zona)
        zona_label.setStyleSheet("""
            background-color: #D32F2F;
            color: white;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 2px;
            min-width: 18px;
        """)
        zona_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(zona_label)

        # Texto indicando falta de guardia
        texto_label = QLabel("⚠️ SIN GUARDIA ASIGNADA")
        texto_label.setStyleSheet("font-size: 8px; color: #B71C1C; font-weight: bold;")
        h_layout.addWidget(texto_label, 1)

        # Estilo del widget con color de alerta
        widget.setStyleSheet("""
            QWidget {
                background-color: #FFEBEE;
                border-left: 3px solid #D32F2F;
                border-radius: 3px;
                margin: 1px 0px;
            }
        """)
        widget.setToolTip(f"ALERTA: La zona {zona.nombre_zona} no tiene guardia asignada")

        layout.addWidget(widget)

    def _agregar_ausencias(self, layout: QVBoxLayout):
        """Agregar información de ausencias."""
        label_titulo = QLabel("🏥 Ausencias:")
        label_titulo.setStyleSheet(
            "font-size: 9px; font-weight: bold; color: #C62828; "
            "background-color: #FFEBEE; padding: 2px; border-radius: 2px; margin-top: 4px;"
        )
        layout.addWidget(label_titulo)

        for ausencia in self.ausencias[:5]:  # Máximo 5 ausencias mostradas
            profesor = ausencia.profesor.nombre_completo if ausencia.profesor else "Desconocido"
            if "," in profesor:
                apellido = profesor.split(",")[0].strip()
            else:
                partes = profesor.split()
                apellido = partes[-1] if partes else profesor

            motivo = ausencia.motivo[:15] if ausencia.motivo else "Sin motivo"
            texto = f"  • {apellido}: {motivo}"

            label = QLabel(texto)
            label.setStyleSheet(
                "font-size: 8px; padding: 1px 3px; margin-left: 5px; "
                "background-color: #FFCDD2; border-left: 2px solid #F44336; color: #B71C1C;"
            )
            label.setToolTip(f"Ausencia: {profesor} - {ausencia.motivo}")
            layout.addWidget(label)

        if len(self.ausencias) > 5:
            label_mas = QLabel(f"  ... y {len(self.ausencias) - 5} más")
            label_mas.setStyleSheet("font-size: 7px; color: #999; font-style: italic;")
            layout.addWidget(label_mas)

    def _aplicar_estilo(self):
        """Aplicar estilo CSS a la celda según su estado."""
        tiene_guardias = len(self.guardias) > 0
        tiene_ausencias = len(self.ausencias) > 0
        tiene_sustituciones = len(self.sustituciones) > 0

        # Días no lectivos (festivos/fines de semana) tienen prioridad visual
        if not self.es_dia_lectivo:
            # Estilo para días no lectivos (sombreado gris)
            estilo = """
                QGroupBox {
                    background-color: #F5F5F5;
                    border: 1px solid #BDBDBD;
                    border-radius: 6px;
                    opacity: 0.7;
                }
                QLabel {
                    color: #757575;
                }
            """
        elif self.es_hoy:
            # Estilo para hoy
            estilo = """
                QGroupBox {
                    background-color: #FFF9C4;
                    border: 3px solid #FBC02D;
                    border-radius: 6px;
                }
            """
        elif tiene_sustituciones:
            # Estilo para días con sustituciones
            estilo = """
                QGroupBox {
                    background-color: #FFF3E0;
                    border: 2px solid #FF9800;
                    border-radius: 6px;
                }
            """
        elif tiene_ausencias and tiene_guardias:
            # Estilo para días con ausencias y guardias
            estilo = """
                QGroupBox {
                    background-color: #FCE4EC;
                    border: 2px solid #E91E63;
                    border-radius: 6px;
                }
            """
        elif tiene_guardias:
            # Estilo para días con guardias
            estilo = """
                QGroupBox {
                    background-color: #E3F2FD;
                    border: 1px solid #90CAF9;
                    border-radius: 6px;
                }
            """
        else:
            # Estilo para días sin actividad
            estilo = """
                QGroupBox {
                    background-color: #FAFAFA;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                }
            """

        self.setStyleSheet(estilo)

    def mousePressEvent(self, event):
        """Emitir señal cuando se hace click en el día."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dia_clicked.emit(self.fecha)
        super().mousePressEvent(event)


class VistaCalendario(BaseForm):
    """Vista de calendario mejorada con múltiples vistas y controles."""

    VISTA_MENSUAL = "Mensual"
    VISTA_SEMANAL = "Semanal"
    VISTA_ANUAL = "Anual"

    def __init__(self, session):
        """
        Inicializar vista de calendario.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.logger = get_logger(__name__)
        self.fecha_actual = datetime.now().date()
        self.mes_mostrado = self.fecha_actual.month
        self.anio_mostrado = self.fecha_actual.year
        self.semana_mostrada = self.fecha_actual.isocalendar()[1]
        self.vista_actual = self.VISTA_MENSUAL

        # Cache de días lectivos
        self._dias_lectivos_cache = None

        self.setWindowTitle("📅 Calendario de Guardias")
        self.resize(1400, 900)
        self.setup_ui()

    def showEvent(self, event):
        """
        Sobrescribe showEvent para refrescar el calendario cuando se muestra la vista.

        Esto garantiza que el calendario se actualice automáticamente al:
        - Cambiar de curso escolar en el selector
        - Volver a esta pestaña después de estar en otra vista
        """
        super().showEvent(event)
        # Limpiar caché de días lectivos para forzar recarga
        self._dias_lectivos_cache = None
        # Refrescar calendario con datos del curso activo
        self.actualizar_calendario()

    def cargar_datos(self):
        """Alias de refrescar() para compatibilidad con otras vistas."""
        self.logger.info("🔄 VistaCalendario.cargar_datos() llamado - iniciando refresco")
        self.refrescar()

    def _obtener_dias_lectivos(self) -> set:
        """
        Obtiene el conjunto de días lectivos de la configuración (con caché).

        Returns:
            Set de fechas que son días lectivos
        """
        if self._dias_lectivos_cache is None:
            config = self.session.query(Configuracion).first()
            if config:
                dias_list = listar_dias_lectivos(config)
                self._dias_lectivos_cache = set(dias_list)
            else:
                self._dias_lectivos_cache = set()
        return self._dias_lectivos_cache

    def _es_dia_lectivo(self, fecha: date) -> bool:
        """
        Verifica si una fecha es un día lectivo.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si es día lectivo, False si es festivo o fin de semana
        """
        return fecha in self._obtener_dias_lectivos()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout()
        layout_principal.setSpacing(10)

        # Barra de controles superior
        layout_principal.addLayout(self._crear_barra_controles())

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #2196F3; max-height: 2px;")
        layout_principal.addWidget(separador)

        # Área de calendario (scroll)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)

        self.calendario_widget = QWidget()
        self.calendario_layout = QVBoxLayout()
        self.calendario_widget.setLayout(self.calendario_layout)
        self.scroll_area.setWidget(self.calendario_widget)

        layout_principal.addWidget(self.scroll_area, 1)

        # Leyenda inferior
        layout_principal.addLayout(self._crear_leyenda())

        self.setLayout(layout_principal)
        self.actualizar_calendario()

    def _crear_barra_controles(self) -> QHBoxLayout:
        """Crear barra de controles de navegación y vista."""
        barra_layout = QHBoxLayout()
        barra_layout.setSpacing(10)

        # Grupo: Selector de vista
        label_vista = QLabel("Vista:")
        label_vista.setStyleSheet("font-weight: bold; font-size: 11px;")
        barra_layout.addWidget(label_vista)

        self.combo_vista = QComboBox()
        self.combo_vista.addItems([self.VISTA_MENSUAL, self.VISTA_SEMANAL, self.VISTA_ANUAL])
        self.combo_vista.setCurrentText(self.vista_actual)
        self.combo_vista.currentTextChanged.connect(self.cambiar_vista)
        self.combo_vista.setMinimumWidth(120)
        self.combo_vista.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
            QComboBox:hover {
                background-color: #E3F2FD;
            }
        """)
        barra_layout.addWidget(self.combo_vista)

        barra_layout.addSpacing(20)

        # Grupo: Navegación
        self.btn_anterior = QPushButton("◀ Anterior")
        self.btn_anterior.clicked.connect(self.periodo_anterior)
        self.btn_anterior.setStyleSheet(self._estilo_boton_navegacion())
        barra_layout.addWidget(self.btn_anterior)

        # Etiqueta de periodo actual
        self.label_periodo = QLabel()
        self.label_periodo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_periodo.setMinimumWidth(250)
        font_periodo = QFont()
        font_periodo.setPointSize(14)
        font_periodo.setBold(True)
        self.label_periodo.setFont(font_periodo)
        self.label_periodo.setStyleSheet("""
            QLabel {
                color: #1976D2;
                padding: 8px 16px;
                background-color: #E3F2FD;
                border-radius: 6px;
            }
        """)
        barra_layout.addWidget(self.label_periodo)

        self.btn_siguiente = QPushButton("Siguiente ▶")
        self.btn_siguiente.clicked.connect(self.periodo_siguiente)
        self.btn_siguiente.setStyleSheet(self._estilo_boton_navegacion())
        barra_layout.addWidget(self.btn_siguiente)

        barra_layout.addSpacing(20)

        # Botón Hoy
        self.btn_hoy = QPushButton("📅 Hoy")
        self.btn_hoy.clicked.connect(self.ir_a_hoy)
        self.btn_hoy.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
        """)
        barra_layout.addWidget(self.btn_hoy)

        # Selector de año (para vista anual)
        self.spin_anio = QSpinBox()
        self.spin_anio.setMinimum(2020)
        self.spin_anio.setMaximum(2030)
        self.spin_anio.setValue(self.anio_mostrado)
        self.spin_anio.valueChanged.connect(self.cambiar_anio)
        self.spin_anio.setVisible(False)  # Solo visible en vista anual
        self.spin_anio.setStyleSheet("""
            QSpinBox {
                padding: 5px 10px;
                border: 2px solid #2196F3;
                border-radius: 4px;
                background-color: white;
                font-size: 11px;
            }
        """)
        barra_layout.addWidget(self.spin_anio)

        barra_layout.addStretch()

        # Botón refrescar
        btn_refrescar = QPushButton("🔄 Refrescar")
        btn_refrescar.clicked.connect(self.refrescar)
        btn_refrescar.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        barra_layout.addWidget(btn_refrescar)

        return barra_layout

    def _estilo_boton_navegacion(self) -> str:
        """Estilo CSS para botones de navegación."""
        return """
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """

    def _crear_leyenda(self) -> QHBoxLayout:
        """Crear leyenda del calendario."""
        leyenda_layout = QHBoxLayout()
        leyenda_layout.setSpacing(15)

        label_titulo = QLabel("📋 LEYENDA:")
        label_titulo.setStyleSheet("font-weight: bold; font-size: 10px; color: #1976D2;")
        leyenda_layout.addWidget(label_titulo)

        # Items de leyenda con colores
        items = [
            ("🟨", "Hoy", "#FFF9C4", "#FBC02D"),
            ("🟦", "Con guardias", "#E3F2FD", "#90CAF9"),
            ("🟧", "Con sustituciones", "#FFF3E0", "#FF9800"),
            ("🟥", "Con ausencias", "#FCE4EC", "#E91E63"),
            ("⬜", "Sin actividad", "#FAFAFA", "#E0E0E0"),
            ("⬛", "No lectivo", "#F5F5F5", "#BDBDBD"),
            ("⚠️", "Zona sin guardia", "#FFEBEE", "#D32F2F"),
        ]

        for emoji, texto, bg_color, border_color in items:
            label = QLabel(f"{emoji} {texto}")
            label.setStyleSheet(f"""
                padding: 4px 8px;
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 3px;
                font-size: 9px;
            """)
            leyenda_layout.addWidget(label)

        leyenda_layout.addStretch()

        return leyenda_layout

    def cambiar_vista(self, vista: str):
        """Cambiar el tipo de vista."""
        self.vista_actual = vista

        # Mostrar/ocultar controles según la vista
        if vista == self.VISTA_ANUAL:
            self.spin_anio.setVisible(True)
            self.btn_anterior.setText("◀ Año Anterior")
            self.btn_siguiente.setText("Año Siguiente ▶")
        else:
            self.spin_anio.setVisible(False)
            if vista == self.VISTA_MENSUAL:
                self.btn_anterior.setText("◀ Mes Anterior")
                self.btn_siguiente.setText("Mes Siguiente ▶")
            else:  # SEMANAL
                self.btn_anterior.setText("◀ Semana Anterior")
                self.btn_siguiente.setText("Semana Siguiente ▶")

        self.actualizar_calendario()

    def _obtener_zonas_esperadas_por_recreo(self, fecha: date) -> Dict[Tuple[str, int], List[Zona]]:
        """
        Determina qué zonas deberían tener guardia para cada recreo/turno en una fecha.

        Args:
            fecha: Fecha para la cual calcular las zonas esperadas

        Returns:
            Diccionario con clave (turno, recreo) y valor lista de zonas esperadas
        """
        zonas_por_recreo = {}

        # Obtener configuración
        config = self.session.query(Configuracion).first()
        if not config:
            return zonas_por_recreo

        # Obtener todas las zonas activas en esta fecha
        zonas = self.session.query(Zona).all()
        zonas_activas = []
        for zona in zonas:
            # Verificar si la zona está activa en esta fecha
            zona_activa = True
            if zona.fecha_inicio and fecha < zona.fecha_inicio:
                zona_activa = False
            if zona.fecha_fin and fecha > zona.fecha_fin:
                zona_activa = False
            if zona_activa:
                zonas_activas.append(zona)

        # Ordenar zonas por nombre (Z1, Z2, Z3, Z4)
        zonas_activas = sorted(
            zonas_activas,
            key=lambda z: (
                int(z.nombre_zona[1]) if z.nombre_zona and z.nombre_zona.startswith("Z") else 999
            ),
        )

        # Parse recreos_config
        recreos_list = self._parse_recreos_config(config)

        # Para cada recreo, agregar las zonas que deberían tener guardia
        for recreo_data in recreos_list:
            recreo_id = recreo_data["id"]
            turno = recreo_data.get("turno", "mañana")
            num_zonas = recreo_data.get("zonas", len(zonas_activas))

            # Limitar al número de zonas activas disponibles
            zonas_para_recreo = zonas_activas[: min(num_zonas, len(zonas_activas))]
            zonas_por_recreo[(turno, recreo_id)] = zonas_para_recreo

        return zonas_por_recreo

    def _parse_recreos_config(self, config: Configuracion) -> List[Dict]:
        """Parse la configuración de recreos desde JSON."""
        if config.recreos_config:
            try:
                return json.loads(config.recreos_config)
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback: deducir de campos individuales
        recreos = []
        recreo_id = 0

        if config.hora_recreo1_manana:
            recreo_id += 1
            recreos.append(
                {
                    "id": recreo_id,
                    "turno": "mañana",
                    "etiqueta": f"Recreo {recreo_id}",
                }
            )

        if config.hora_recreo2_manana:
            recreo_id += 1
            recreos.append(
                {
                    "id": recreo_id,
                    "turno": "mañana",
                    "etiqueta": f"Recreo {recreo_id}",
                }
            )

        if config.hora_recreo1_tarde:
            recreo_id += 1
            recreos.append(
                {
                    "id": recreo_id,
                    "turno": "tarde",
                    "etiqueta": f"Recreo {recreo_id}",
                }
            )

        if config.hora_recreo2_tarde:
            recreo_id += 1
            recreos.append(
                {
                    "id": recreo_id,
                    "turno": "tarde",
                    "etiqueta": f"Recreo {recreo_id}",
                }
            )

        return recreos

    def actualizar_calendario(self):
        """Actualizar el calendario según la vista actual."""
        self.logger.info(f"📅 Actualizando calendario - Vista: {self.vista_actual}")

        # Limpiar calendario anterior
        while self.calendario_layout.count():
            item = self.calendario_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Renderizar según vista
        if self.vista_actual == self.VISTA_MENSUAL:
            self._renderizar_vista_mensual()
        elif self.vista_actual == self.VISTA_SEMANAL:
            self._renderizar_vista_semanal()
        else:  # ANUAL
            self._renderizar_vista_anual()

        self.logger.info("✅ Calendario actualizado correctamente")

    def _renderizar_vista_mensual(self):
        """Renderizar vista mensual."""
        # Actualizar etiqueta de periodo
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
        self.label_periodo.setText(f"{meses[self.mes_mostrado]} {self.anio_mostrado}")

        # Crear grid del calendario
        grid_calendario = QGridLayout()
        grid_calendario.setSpacing(5)
        grid_calendario.setContentsMargins(10, 10, 10, 10)

        # Encabezados de días de la semana
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, dia in enumerate(dias_semana):
            label = QLabel(dia)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            label.setFont(font)
            label.setStyleSheet("""
                QLabel {
                    background-color: #2196F3;
                    color: white;
                    padding: 12px;
                    border-radius: 4px;
                }
            """)
            grid_calendario.addWidget(label, 0, i)

        # Cargar datos del mes
        primer_dia = date(self.anio_mostrado, self.mes_mostrado, 1)
        dias_en_mes = monthrange(self.anio_mostrado, self.mes_mostrado)[1]
        ultimo_dia = date(self.anio_mostrado, self.mes_mostrado, dias_en_mes)

        (
            guardias_por_fecha,
            ausencias_por_fecha,
            sustituciones_por_fecha,
        ) = self._cargar_datos_periodo(primer_dia, ultimo_dia)

        # Renderizar días del mes
        dia_semana_inicio = primer_dia.weekday()  # 0=Lunes, 6=Domingo
        fila = 1
        columna = dia_semana_inicio

        for dia_num in range(1, dias_en_mes + 1):
            fecha_dia = date(self.anio_mostrado, self.mes_mostrado, dia_num)

            celda = CeldaDia(
                fecha=fecha_dia,
                guardias=guardias_por_fecha.get(fecha_dia, []),
                ausencias=ausencias_por_fecha.get(fecha_dia, []),
                sustituciones=sustituciones_por_fecha.get(fecha_dia, []),
                zonas_esperadas_por_recreo=self._obtener_zonas_esperadas_por_recreo(fecha_dia),
                es_dia_lectivo=self._es_dia_lectivo(fecha_dia),
                es_hoy=(fecha_dia == self.fecha_actual),
            )
            celda.dia_clicked.connect(self._dia_seleccionado)

            grid_calendario.addWidget(celda, fila, columna)

            columna += 1
            if columna > 6:  # Nueva fila después del domingo
                columna = 0
                fila += 1

        # Añadir grid al layout principal
        widget_grid = QWidget()
        widget_grid.setLayout(grid_calendario)
        self.calendario_layout.addWidget(widget_grid)
        self.calendario_layout.addStretch()

    def _renderizar_vista_semanal(self):
        """Renderizar vista semanal."""
        # Calcular primer y último día de la semana
        # Encontrar el lunes de la semana actual
        date(self.anio_mostrado, self.mes_mostrado, 1)
        # Buscar una fecha en la semana deseada
        primer_dia_anio = date(self.anio_mostrado, 1, 1)
        dias_desde_inicio = (self.semana_mostrada - 1) * 7
        fecha_semana = primer_dia_anio + timedelta(days=dias_desde_inicio)

        # Ajustar al lunes
        primer_dia_semana = fecha_semana - timedelta(days=fecha_semana.weekday())
        ultimo_dia_semana = primer_dia_semana + timedelta(days=6)

        # Actualizar etiqueta
        self.label_periodo.setText(
            f"Semana {self.semana_mostrada} - {primer_dia_semana.strftime('%d/%m')} "
            f"al {ultimo_dia_semana.strftime('%d/%m/%Y')}"
        )

        # Crear grid
        grid_calendario = QGridLayout()
        grid_calendario.setSpacing(5)
        grid_calendario.setContentsMargins(10, 10, 10, 10)

        # Encabezados
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, dia in enumerate(dias_semana):
            label = QLabel(dia)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setBold(True)
            font.setPointSize(10)
            label.setFont(font)
            label.setStyleSheet("""
                QLabel {
                    background-color: #2196F3;
                    color: white;
                    padding: 12px;
                    border-radius: 4px;
                }
            """)
            grid_calendario.addWidget(label, 0, i)

        # Cargar datos
        (
            guardias_por_fecha,
            ausencias_por_fecha,
            sustituciones_por_fecha,
        ) = self._cargar_datos_periodo(primer_dia_semana, ultimo_dia_semana)

        # Renderizar días de la semana
        for i in range(7):
            fecha_dia = primer_dia_semana + timedelta(days=i)

            celda = CeldaDia(
                fecha=fecha_dia,
                guardias=guardias_por_fecha.get(fecha_dia, []),
                ausencias=ausencias_por_fecha.get(fecha_dia, []),
                sustituciones=sustituciones_por_fecha.get(fecha_dia, []),
                zonas_esperadas_por_recreo=self._obtener_zonas_esperadas_por_recreo(fecha_dia),
                es_dia_lectivo=self._es_dia_lectivo(fecha_dia),
                es_hoy=(fecha_dia == self.fecha_actual),
            )
            celda.dia_clicked.connect(self._dia_seleccionado)
            celda.setMinimumHeight(600)  # Altura aumentada para ver más guardias

            grid_calendario.addWidget(celda, 1, i)

        widget_grid = QWidget()
        widget_grid.setLayout(grid_calendario)
        self.calendario_layout.addWidget(widget_grid)
        self.calendario_layout.addStretch()

    def _renderizar_vista_anual(self):
        """Renderizar vista anual (12 meses en miniatura)."""
        self.label_periodo.setText(f"Año {self.anio_mostrado}")

        # Grid de 3x4 para 12 meses
        grid_anual = QGridLayout()
        grid_anual.setSpacing(15)
        grid_anual.setContentsMargins(10, 10, 10, 10)

        meses = [
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

        for mes_num in range(1, 13):
            fila = (mes_num - 1) // 4
            columna = (mes_num - 1) % 4

            mes_widget = self._crear_mes_miniatura(mes_num, meses[mes_num - 1])
            grid_anual.addWidget(mes_widget, fila, columna)

        widget_grid = QWidget()
        widget_grid.setLayout(grid_anual)
        self.calendario_layout.addWidget(widget_grid)
        self.calendario_layout.addStretch()

    def _crear_mes_miniatura(self, mes: int, nombre_mes: str) -> QGroupBox:
        """Crear widget de mes miniatura para vista anual."""
        grupo = QGroupBox(nombre_mes)
        grupo.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2196F3;
                border-radius: 6px;
                margin-top: 10px;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #1976D2;
            }
        """)

        layout = QVBoxLayout()

        # Mini calendario
        grid = QGridLayout()
        grid.setSpacing(2)

        # Encabezados (abreviados)
        dias_semana_cortos = ["L", "M", "X", "J", "V", "S", "D"]
        for i, dia in enumerate(dias_semana_cortos):
            label = QLabel(dia)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 8px; font-weight: bold; color: #666;")
            grid.addWidget(label, 0, i)

        # Días del mes
        primer_dia = date(self.anio_mostrado, mes, 1)
        dias_en_mes = monthrange(self.anio_mostrado, mes)[1]
        ultimo_dia = date(self.anio_mostrado, mes, dias_en_mes)

        # Cargar datos (solo guardias para simplificar)
        guardias = (
            self.session.query(Guardia)
            .filter(Guardia.fecha >= primer_dia, Guardia.fecha <= ultimo_dia)
            .all()
        )

        guardias_por_fecha = defaultdict(int)
        for g in guardias:
            guardias_por_fecha[g.fecha] += 1

        dia_semana_inicio = primer_dia.weekday()
        fila = 1
        columna = dia_semana_inicio

        for dia_num in range(1, dias_en_mes + 1):
            fecha_dia = date(self.anio_mostrado, mes, dia_num)
            num_guardias = guardias_por_fecha.get(fecha_dia, 0)

            label = QLabel(str(dia_num))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(self._estilo_dia_miniatura(fecha_dia, num_guardias))
            label.setMinimumSize(25, 25)
            label.setMaximumSize(25, 25)

            if num_guardias > 0:
                label.setToolTip(f"{num_guardias} guardias")

            grid.addWidget(label, fila, columna)

            columna += 1
            if columna > 6:
                columna = 0
                fila += 1

        layout.addLayout(grid)
        grupo.setLayout(layout)

        # Click en mes para ir a vista mensual
        grupo.mousePressEvent = lambda event: self._seleccionar_mes(mes)
        grupo.setCursor(Qt.CursorShape.PointingHandCursor)

        return grupo

    def _estilo_dia_miniatura(self, fecha: date, num_guardias: int) -> str:
        """Obtener estilo para día en vista anual miniatura."""
        es_hoy = fecha == self.fecha_actual

        if es_hoy:
            return """
                QLabel {
                    background-color: #FBC02D;
                    color: white;
                    border-radius: 3px;
                    font-size: 9px;
                    font-weight: bold;
                }
            """
        elif num_guardias > 0:
            intensidad = min(num_guardias * 20, 200)  # Más oscuro = más guardias
            return f"""
                QLabel {{
                    background-color: rgb({255 - intensidad}, {242 - intensidad // 2}, 253);
                    border: 1px solid #90CAF9;
                    border-radius: 3px;
                    font-size: 8px;
                }}
            """
        else:
            return """
                QLabel {
                    background-color: #FAFAFA;
                    border: 1px solid #E0E0E0;
                    border-radius: 3px;
                    font-size: 8px;
                }
            """

    def _cargar_datos_periodo(self, fecha_inicio: date, fecha_fin: date) -> tuple:
        """
        Cargar guardias, ausencias y sustituciones de un periodo.

        Returns:
            Tupla de (guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha)
        """
        # Obtener configuración activa para filtrar por curso
        from infrastructure.database.models import CursoEscolar

        curso_activo = self.session.query(CursoEscolar).filter_by(activo=True).first()

        if not curso_activo:
            # Si no hay curso activo, retornar datos vacíos
            return defaultdict(list), defaultdict(list), defaultdict(list)

        # Guardias del curso activo
        guardias = (
            self.session.query(Guardia)
            .filter(
                Guardia.curso_id == curso_activo.id,
                Guardia.fecha >= fecha_inicio,
                Guardia.fecha <= fecha_fin,
            )
            .all()
        )

        guardias_por_fecha = defaultdict(list)
        sustituciones_por_fecha = defaultdict(list)

        for g in guardias:
            guardias_por_fecha[g.fecha].append(g)
            # Detectar sustituciones (tiene profesor_sustituido_id)
            if hasattr(g, "profesor_sustituido_id") and g.profesor_sustituido_id:
                sustituciones_por_fecha[g.fecha].append(g)

        # Ausencias
        ausencias = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.activa == True,  # noqa: E712
                Ausencia.fecha_inicio <= fecha_fin,
                Ausencia.fecha_fin >= fecha_inicio,
            )
            .all()
        )

        ausencias_por_fecha = defaultdict(list)
        for ausencia in ausencias:
            fecha_actual = max(ausencia.fecha_inicio, fecha_inicio)
            fecha_fin_ausencia = min(ausencia.fecha_fin, fecha_fin)

            while fecha_actual <= fecha_fin_ausencia:
                ausencias_por_fecha[fecha_actual].append(ausencia)
                fecha_actual += timedelta(days=1)

        return guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha

    def _dia_seleccionado(self, fecha: date):
        """Abrir ventana de detalle del día seleccionado."""
        # Obtener datos del día
        guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha = (
            self._cargar_datos_periodo(fecha, fecha)
        )

        guardias = guardias_por_fecha.get(fecha, [])
        ausencias = ausencias_por_fecha.get(fecha, [])
        sustituciones = sustituciones_por_fecha.get(fecha, [])

        # Abrir diálogo con detalles
        dialog = DiaDetalleDialog(
            fecha=fecha,
            guardias=guardias,
            ausencias=ausencias,
            sustituciones=sustituciones,
            zonas_esperadas_por_recreo=self._obtener_zonas_esperadas_por_recreo(fecha),
            es_dia_lectivo=self._es_dia_lectivo(fecha),
            parent=self,
        )
        dialog.exec()

    def _seleccionar_mes(self, mes: int):
        """Cambiar a vista mensual del mes seleccionado."""
        self.mes_mostrado = mes
        self.vista_actual = self.VISTA_MENSUAL
        self.combo_vista.setCurrentText(self.VISTA_MENSUAL)
        self.actualizar_calendario()

    def periodo_anterior(self):
        """Navegar al periodo anterior según la vista."""
        if self.vista_actual == self.VISTA_MENSUAL:
            self.mes_anterior()
        elif self.vista_actual == self.VISTA_SEMANAL:
            self.semana_anterior()
        else:  # ANUAL
            self.anio_anterior()

    def periodo_siguiente(self):
        """Navegar al periodo siguiente según la vista."""
        if self.vista_actual == self.VISTA_MENSUAL:
            self.mes_siguiente()
        elif self.vista_actual == self.VISTA_SEMANAL:
            self.semana_siguiente()
        else:  # ANUAL
            self.anio_siguiente()

    def mes_anterior(self):
        """Ir al mes anterior."""
        if self.mes_mostrado == 1:
            self.mes_mostrado = 12
            self.anio_mostrado -= 1
        else:
            self.mes_mostrado -= 1
        self.actualizar_calendario()

    def mes_siguiente(self):
        """Ir al mes siguiente."""
        if self.mes_mostrado == 12:
            self.mes_mostrado = 1
            self.anio_mostrado += 1
        else:
            self.mes_mostrado += 1
        self.actualizar_calendario()

    def semana_anterior(self):
        """Ir a la semana anterior."""
        if self.semana_mostrada == 1:
            self.semana_mostrada = 52
            self.anio_mostrado -= 1
        else:
            self.semana_mostrada -= 1
        self.actualizar_calendario()

    def semana_siguiente(self):
        """Ir a la semana siguiente."""
        if self.semana_mostrada >= 52:
            self.semana_mostrada = 1
            self.anio_mostrado += 1
        else:
            self.semana_mostrada += 1
        self.actualizar_calendario()

    def anio_anterior(self):
        """Ir al año anterior."""
        self.anio_mostrado -= 1
        self.spin_anio.setValue(self.anio_mostrado)
        self.actualizar_calendario()

    def anio_siguiente(self):
        """Ir al año siguiente."""
        self.anio_mostrado += 1
        self.spin_anio.setValue(self.anio_mostrado)
        self.actualizar_calendario()

    def cambiar_anio(self, anio: int):
        """Cambiar el año mostrado (desde el spinner)."""
        self.anio_mostrado = anio
        self.actualizar_calendario()

    def ir_a_hoy(self):
        """Volver a la fecha actual."""
        self.fecha_actual = datetime.now().date()
        self.mes_mostrado = self.fecha_actual.month
        self.anio_mostrado = self.fecha_actual.year
        self.semana_mostrada = self.fecha_actual.isocalendar()[1]
        self.actualizar_calendario()

    def refrescar(self):
        """Refrescar el calendario."""
        self.logger.info("🔄 VistaCalendario.refrescar() llamado - limpiando caché y actualizando")
        self.session.expire_all()  # Limpiar caché de SQLAlchemy
        self._dias_lectivos_cache = None  # Limpiar caché de días lectivos
        self.actualizar_calendario()
