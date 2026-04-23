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
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from presentation.theme.tokens import FontSize
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
from utils.icons import icon_for_button

from presentation.dialogs.dia_detalle_dialog import DiaDetalleDialog
from presentation.forms.base_form import BaseForm
from presentation.widgets.vista_calendario_helpers import (
    cargar_datos_periodo,
    estilo_dia_miniatura,
    obtener_zonas_esperadas_por_recreo,
    parse_recreos_config,
)
from presentation.widgets._celda_dia import CeldaDia  # noqa: F401 (re-exportado)

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
        self.modo_compacto = False

        # Cache de días lectivos por mes (PERF-04)
        self._dias_lectivos_cache: dict = {}
        # Pool de CeldaDia reutilizables (PERF-01)
        self._celda_pool: list = []

        self.setWindowTitle("Calendario de Guardias")
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
        self._dias_lectivos_cache = {}
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
        key = (self.anio_mostrado, self.mes_mostrado)
        if key not in self._dias_lectivos_cache:
            from application.app_services import AppServices
            config = AppServices(self.session).configuracion_repo.get_first()
            if config:
                self._dias_lectivos_cache[key] = set(listar_dias_lectivos(config))
            else:
                self._dias_lectivos_cache[key] = set()
        return self._dias_lectivos_cache[key]

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
        separador.setObjectName("separator")
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
        font_periodo.setPointSize(FontSize.BODY)
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
        self.btn_hoy = QPushButton("Hoy")
        self.btn_hoy.setIcon(icon_for_button("calendar"))
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
        btn_refrescar = QPushButton("Refrescar")
        btn_refrescar.setIcon(icon_for_button("refresh"))
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

        # Botón modo compacto
        self.btn_compacto = QPushButton("Compacto" if not self.modo_compacto else "Detalle")
        self.btn_compacto.setIcon(icon_for_button("view-compact"))
        self.btn_compacto.setCheckable(True)
        self.btn_compacto.setChecked(self.modo_compacto)
        self.btn_compacto.clicked.connect(self.toggle_modo_compacto)
        self.btn_compacto.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #546E7A; }
            QPushButton:checked { background-color: #37474F; }
        """)
        barra_layout.addWidget(self.btn_compacto)

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

        label_titulo = QLabel("LEYENDA:")
        label_titulo.setStyleSheet("font-weight: bold; font-size: 10px; color: #1976D2;")
        leyenda_layout.addWidget(label_titulo)

        # Items de leyenda con colores
        items = [
            ("🟨", "Hoy", "#FFF9C4", "#FBC02D"),
            ("🟦", "Con guardias", "#E3F2FD", "#90CAF9"),
            ("🟧", "Con sustituciones", "#FFF3E0", "#FF9800"),
            ("■", "Con ausencias", "#FCE4EC", "#E91E63"),
            ("□", "Sin actividad", "#FAFAFA", "#E0E0E0"),
            ("■", "No lectivo", "#F5F5F5", "#BDBDBD"),
            ("!", "Zona sin guardia", "#FFEBEE", "#D32F2F"),
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


    def actualizar_calendario(self):
        """Actualizar el calendario según la vista actual."""
        self.logger.info(f"📅 Actualizando calendario - Vista: {self.vista_actual}")

        # Invalidar pool: las celdas son hijos del widget_grid que se va a destruir
        self._celda_pool.clear()

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
            font.setPointSize(FontSize.CAPTION)
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
        ) = cargar_datos_periodo(self.session, primer_dia, ultimo_dia)

        # Renderizar días del mes
        dia_semana_inicio = primer_dia.weekday()  # 0=Lunes, 6=Domingo
        fila = 1
        columna = dia_semana_inicio

        pool_idx = 0
        for dia_num in range(1, dias_en_mes + 1):
            fecha_dia = date(self.anio_mostrado, self.mes_mostrado, dia_num)

            kwargs = dict(
                fecha=fecha_dia,
                guardias=guardias_por_fecha.get(fecha_dia, []),
                ausencias=ausencias_por_fecha.get(fecha_dia, []),
                sustituciones=sustituciones_por_fecha.get(fecha_dia, []),
                zonas_esperadas_por_recreo=obtener_zonas_esperadas_por_recreo(self.session, fecha_dia),
                es_dia_lectivo=self._es_dia_lectivo(fecha_dia),
                es_hoy=(fecha_dia == self.fecha_actual),
                modo_compacto=self.modo_compacto,
            )
            if pool_idx < len(self._celda_pool):
                celda = self._celda_pool[pool_idx]
                celda.actualizar(**kwargs)
            else:
                celda = CeldaDia(**kwargs)
                celda.dia_clicked.connect(self._dia_seleccionado)
                self._celda_pool.append(celda)
            pool_idx += 1

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
            font.setPointSize(FontSize.CAPTION)
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
        ) = cargar_datos_periodo(self.session, primer_dia_semana, ultimo_dia_semana)

        # Renderizar días de la semana
        for i in range(7):
            fecha_dia = primer_dia_semana + timedelta(days=i)

            celda = CeldaDia(
                fecha=fecha_dia,
                guardias=guardias_por_fecha.get(fecha_dia, []),
                ausencias=ausencias_por_fecha.get(fecha_dia, []),
                sustituciones=sustituciones_por_fecha.get(fecha_dia, []),
                zonas_esperadas_por_recreo=obtener_zonas_esperadas_por_recreo(self.session, fecha_dia),
                es_dia_lectivo=self._es_dia_lectivo(fecha_dia),
                es_hoy=(fecha_dia == self.fecha_actual),
                modo_compacto=self.modo_compacto,
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
        from application.app_services import AppServices
        guardias = AppServices(self.session).guardias.find_by_rango_fechas(primer_dia, ultimo_dia)

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
            label.setStyleSheet(estilo_dia_miniatura(fecha_dia, num_guardias, self.fecha_actual))
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


    def _dia_seleccionado(self, fecha: date):
        """Abrir ventana de detalle del día seleccionado."""
        # Obtener datos del día
        guardias_por_fecha, ausencias_por_fecha, sustituciones_por_fecha = (
            cargar_datos_periodo(self.session, fecha, fecha)
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
            zonas_esperadas_por_recreo=obtener_zonas_esperadas_por_recreo(self.session, fecha),
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

    def toggle_modo_compacto(self):
        """Alterna entre modo detalle y modo compacto en la vista mensual."""
        self.modo_compacto = not self.modo_compacto
        self.btn_compacto.setChecked(self.modo_compacto)
        self.btn_compacto.setText("Detalle" if self.modo_compacto else "Compacto")
        self.actualizar_calendario()

    def refrescar(self):
        """Refrescar el calendario."""
        self.logger.info("🔄 VistaCalendario.refrescar() llamado - limpiando caché y actualizando")
        self.session.expire_all()  # Limpiar caché de SQLAlchemy
        self._dias_lectivos_cache = {}  # Limpiar caché de días lectivos
        self.actualizar_calendario()
