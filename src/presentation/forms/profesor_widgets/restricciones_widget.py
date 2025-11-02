"""
Widget de restricciones y preferencias del profesor.

Este widget encapsula:
- Fechas de guardias (inicio/fin mutuamente excluyentes)
- Restricciones personalizadas de horario
- Matriz de disponibilidad día × recreo (Lun-Vie × R1-R4)
"""

import ast
import json
from datetime import date
from typing import Dict, Optional, Tuple

import ui_styles as styles
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class RestriccionesWidget(QGroupBox):
    """
    Widget para gestionar restricciones y preferencias del profesor.

    Señales:
        restricciones_changed: Se emite cuando cambian las restricciones
        turno_changed_request: Se emite para solicitar pre-selección según turno
    """

    # Señales
    restricciones_changed = pyqtSignal()
    preseleccionar_turno_request = pyqtSignal(str)  # Solicitar pre-selección

    def __init__(self, parent=None):
        """
        Inicializar widget de restricciones.

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__("⚙️ Restricciones y Preferencias", parent)
        self.setStyleSheet(styles.STYLE_GROUPBOX)

        # Matriz de checkboxes
        self.matriz_checks: Dict[int, Dict[int, QCheckBox]] = {}

        # Widgets de botones (referencias para habilitar/deshabilitar)
        self.btn_marcar_todos: Optional[QPushButton] = None
        self.btn_desmarcar_todos: Optional[QPushButton] = None
        self.matriz_horario_widget: Optional[QWidget] = None

        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Crear la interfaz de usuario del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Sección de fechas
        layout.addLayout(self._crear_seccion_fechas())

        # Sección de zona preferida
        layout.addLayout(self._crear_seccion_zona_preferida())

        # Checkbox para restricciones de horario
        self.usar_restricciones_horario_checkbox = QCheckBox(
            "☑️ Usar restricciones personalizadas de horario"
        )
        self.usar_restricciones_horario_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(self.usar_restricciones_horario_checkbox)

        # Label de la matriz
        label_matriz = QLabel("📅 Disponibilidad por día y recreo:")
        label_matriz.setStyleSheet(styles.STYLE_LABEL_FIELD + " font-weight: bold;")
        layout.addWidget(label_matriz)

        # Matriz de horario
        self.matriz_horario_widget = self._crear_matriz_horario()
        layout.addWidget(self.matriz_horario_widget)

        self.setLayout(layout)

    def _crear_seccion_fechas(self) -> QVBoxLayout:
        """Crear sección de fechas mutuamente excluyentes."""
        layout = QVBoxLayout()

        # Fecha de inicio
        layout_fecha_inicio = QHBoxLayout()
        self.usar_fecha_inicio_checkbox = QCheckBox("Usar fecha de inicio:")
        self.usar_fecha_inicio_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fecha_inicio.addWidget(self.usar_fecha_inicio_checkbox)

        self.fecha_inicio_guardias_input = QDateEdit()
        self.fecha_inicio_guardias_input.setCalendarPopup(True)
        self.fecha_inicio_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_guardias_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_guardias_input.setMaximumWidth(200)
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_inicio_guardias_input.setEnabled(False)
        layout_fecha_inicio.addWidget(self.fecha_inicio_guardias_input)
        layout_fecha_inicio.addStretch()
        layout.addLayout(layout_fecha_inicio)

        # Fecha de fin
        layout_fecha_fin = QHBoxLayout()
        self.usar_fecha_fin_checkbox = QCheckBox("Usar fecha de fin:")
        self.usar_fecha_fin_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fecha_fin.addWidget(self.usar_fecha_fin_checkbox)

        self.fecha_fin_guardias_input = QDateEdit()
        self.fecha_fin_guardias_input.setCalendarPopup(True)
        self.fecha_fin_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_guardias_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_guardias_input.setMaximumWidth(200)
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setEnabled(False)
        layout_fecha_fin.addWidget(self.fecha_fin_guardias_input)
        layout_fecha_fin.addStretch()
        layout.addLayout(layout_fecha_fin)

        return layout

    def _crear_seccion_zona_preferida(self) -> QHBoxLayout:
        """Crear sección de zona preferida."""
        layout = QHBoxLayout()

        label = QLabel("🎯 Zona preferida:")
        label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label)

        self.zona_preferida_combo = QComboBox()
        self.zona_preferida_combo.setStyleSheet(styles.STYLE_INPUT)
        self.zona_preferida_combo.setMaximumWidth(300)
        # Se cargará dinámicamente en el formulario principal
        layout.addWidget(self.zona_preferida_combo)

        layout.addStretch()

        return layout

    def _crear_matriz_horario(self) -> QWidget:
        """Crear widget con matriz de disponibilidad día × recreo."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Grid de checkboxes
        grid_matriz = QGridLayout()
        grid_matriz.setSpacing(8)

        # Encabezados (solo días laborables: Lunes a Viernes)
        dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie"]
        grid_matriz.addWidget(QLabel(""), 0, 0)
        for col in range(4):
            label_recreo = QLabel(f"<b>R{col + 1}</b>")
            label_recreo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_matriz.addWidget(label_recreo, 0, col + 1)

        # Crear matriz de checkboxes (solo días laborables: 0-4)
        for fila, dia_idx in enumerate(range(5)):  # Solo 5 días: Lunes a Viernes
            label_dia = QLabel(f"<b>{dias_nombres[dia_idx]}</b>")
            label_dia.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            grid_matriz.addWidget(label_dia, fila + 1, 0)

            self.matriz_checks[dia_idx] = {}
            for col, recreo_id in enumerate(range(1, 5)):
                checkbox = QCheckBox()
                checkbox.setEnabled(False)
                grid_matriz.addWidget(checkbox, fila + 1, col + 1)
                self.matriz_checks[dia_idx][recreo_id] = checkbox

        layout.addLayout(grid_matriz)

        # Botones de acción rápida
        botones_matriz = QHBoxLayout()
        botones_matriz.setSpacing(10)

        self.btn_marcar_todos = QPushButton("✓ Marcar todos")
        self.btn_marcar_todos.setEnabled(False)
        self.btn_marcar_todos.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.btn_marcar_todos.clicked.connect(lambda: self._marcar_todos_matriz(True))
        botones_matriz.addWidget(self.btn_marcar_todos)

        self.btn_desmarcar_todos = QPushButton("✗ Desmarcar todos")
        self.btn_desmarcar_todos.setEnabled(False)
        self.btn_desmarcar_todos.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.btn_desmarcar_todos.clicked.connect(lambda: self._marcar_todos_matriz(False))
        botones_matriz.addWidget(self.btn_desmarcar_todos)

        botones_matriz.addStretch()
        layout.addLayout(botones_matriz)

        widget.setLayout(layout)
        widget.setEnabled(False)
        return widget

    def _conectar_senales(self):
        """Conectar señales de los campos."""
        self.usar_fecha_inicio_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_fecha_fin_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_restricciones_horario_checkbox.stateChanged.connect(
            self._toggle_restricciones_horario
        )

        # Emitir señal de cambio en fechas
        self.fecha_inicio_guardias_input.dateChanged.connect(self.restricciones_changed.emit)
        self.fecha_fin_guardias_input.dateChanged.connect(self.restricciones_changed.emit)

        # Emitir señal de cambio en checkboxes de matriz
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].stateChanged.connect(
                    self.restricciones_changed.emit
                )

    def _toggle_fechas_guardias(self):
        """Controlar exclusividad mutua entre fecha inicio y fin."""
        sender = self.sender()

        if sender == self.usar_fecha_inicio_checkbox:
            if self.usar_fecha_inicio_checkbox.isChecked():
                self.fecha_inicio_guardias_input.setEnabled(True)
                self.usar_fecha_fin_checkbox.blockSignals(True)
                self.usar_fecha_fin_checkbox.setChecked(False)
                self.usar_fecha_fin_checkbox.blockSignals(False)
                self.fecha_fin_guardias_input.setEnabled(False)
            else:
                self.fecha_inicio_guardias_input.setEnabled(False)

        elif sender == self.usar_fecha_fin_checkbox:
            if self.usar_fecha_fin_checkbox.isChecked():
                self.fecha_fin_guardias_input.setEnabled(True)
                self.usar_fecha_inicio_checkbox.blockSignals(True)
                self.usar_fecha_inicio_checkbox.setChecked(False)
                self.usar_fecha_inicio_checkbox.blockSignals(False)
                self.fecha_inicio_guardias_input.setEnabled(False)
            else:
                self.fecha_fin_guardias_input.setEnabled(False)

        self.restricciones_changed.emit()

    def _toggle_restricciones_horario(self):
        """Activar/desactivar matriz de disponibilidad."""
        is_checked = self.usar_restricciones_horario_checkbox.isChecked()
        if self.matriz_horario_widget:
            self.matriz_horario_widget.setEnabled(is_checked)
        if self.btn_marcar_todos:
            self.btn_marcar_todos.setEnabled(is_checked)
        if self.btn_desmarcar_todos:
            self.btn_desmarcar_todos.setEnabled(is_checked)

        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setEnabled(is_checked)

        self.restricciones_changed.emit()

    def _marcar_todos_matriz(self, estado: bool):
        """Marcar/desmarcar todos los checkboxes de la matriz."""
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setChecked(estado)

    def preseleccionar_segun_turno(self, turno: str):
        """
        Pre-seleccionar recreos en la matriz según el turno del profesor.

        Args:
            turno: Turno del profesor ("mañana", "tarde" o "mixto")
        """
        # Limpiar matriz primero
        self._marcar_todos_matriz(False)

        turno_lower = turno.lower()

        # Pre-seleccionar todos los días
        for dia in self.matriz_checks:
            if turno_lower == "mañana":
                # R1 y R2 (recreos de mañana)
                self.matriz_checks[dia][1].setChecked(True)
                self.matriz_checks[dia][2].setChecked(True)
            elif turno_lower == "tarde":
                # R3 y R4 (recreos de tarde)
                self.matriz_checks[dia][3].setChecked(True)
                self.matriz_checks[dia][4].setChecked(True)
            elif turno_lower == "mixto":
                # Todos los recreos R1, R2, R3, R4
                for recreo in [1, 2, 3, 4]:
                    self.matriz_checks[dia][recreo].setChecked(True)

    # ========== Getters / Setters ==========

    def get_fecha_inicio(self) -> Optional[date]:
        """Obtener fecha de inicio de guardias."""
        if self.usar_fecha_inicio_checkbox.isChecked():
            qdate = self.fecha_inicio_guardias_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_inicio(self, fecha: Optional[date]):
        """Establecer fecha de inicio de guardias."""
        if fecha:
            self.usar_fecha_inicio_checkbox.setChecked(True)
            self.fecha_inicio_guardias_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_inicio_checkbox.setChecked(False)

    def get_fecha_fin(self) -> Optional[date]:
        """Obtener fecha de fin de guardias."""
        if self.usar_fecha_fin_checkbox.isChecked():
            qdate = self.fecha_fin_guardias_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_fin(self, fecha: Optional[date]):
        """Establecer fecha de fin de guardias."""
        if fecha:
            self.usar_fecha_fin_checkbox.setChecked(True)
            self.fecha_fin_guardias_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_fin_checkbox.setChecked(False)

    def get_usar_restricciones(self) -> bool:
        """Verificar si se usan restricciones personalizadas."""
        return self.usar_restricciones_horario_checkbox.isChecked()

    def set_usar_restricciones(self, usar: bool):
        """Establecer si se usan restricciones personalizadas."""
        self.usar_restricciones_horario_checkbox.setChecked(usar)

    def get_recreos_permitidos_json(self) -> str:
        """
        Obtener recreos permitidos como JSON.

        Returns:
            JSON string con formato {"0": [1, 2], "2": [1, 3, 4]}
        """
        resultado = {}
        for dia in self.matriz_checks:
            recreos_activos = []
            for recreo in self.matriz_checks[dia]:
                if self.matriz_checks[dia][recreo].isChecked():
                    recreos_activos.append(recreo)
            if recreos_activos:
                resultado[str(dia)] = recreos_activos
        return json.dumps(resultado) if resultado else ""

    def set_recreos_permitidos_json(self, json_str):
        """
        Cargar recreos permitidos desde JSON o lista.

        Args:
            json_str: JSON string con formato {"0": [1, 2]} o lista [1, 2, 3, 4]
                     También acepta directamente una lista de Python
        """
        self._marcar_todos_matriz(False)

        if not json_str:
            return

        try:
            # Si ya es una lista, usarla directamente
            if isinstance(json_str, list):
                datos = json_str
            # Si es string, parsearlo
            elif isinstance(json_str, str):
                # Intentar JSON primero
                try:
                    datos = json.loads(json_str)
                except json.JSONDecodeError:
                    # Si falla JSON, intentar Python literal
                    try:
                        datos = ast.literal_eval(json_str)
                    except (ValueError, SyntaxError):
                        return
            else:
                return

            # Si es una lista simple (formato nuevo)
            if isinstance(datos, list):
                # Marcar esos recreos en todos los días
                for dia in self.matriz_checks:
                    for recreo in datos:
                        if recreo in self.matriz_checks[dia]:
                            self.matriz_checks[dia][recreo].setChecked(True)

            # Si es un diccionario (formato viejo)
            elif isinstance(datos, dict):
                for dia_str, recreos in datos.items():
                    try:
                        dia_int = int(dia_str)
                        if dia_int in self.matriz_checks:
                            for recreo in recreos:
                                if recreo in self.matriz_checks[dia_int]:
                                    self.matriz_checks[dia_int][recreo].setChecked(True)
                    except (ValueError, KeyError):
                        continue

        except Exception:
            pass  # Ignorar errores de formato

    def get_zona_preferida_id(self) -> Optional[int]:
        """Obtener ID de zona preferida seleccionada."""
        zona_id = self.zona_preferida_combo.currentData()
        return zona_id if zona_id and zona_id > 0 else None

    def set_zona_preferida_id(self, zona_id: Optional[int]):
        """Establecer zona preferida por ID."""
        if zona_id is None:
            # Seleccionar "Sin preferencia" (índice 0)
            self.zona_preferida_combo.setCurrentIndex(0)
        else:
            # Buscar el índice por data
            for i in range(self.zona_preferida_combo.count()):
                if self.zona_preferida_combo.itemData(i) == zona_id:
                    self.zona_preferida_combo.setCurrentIndex(i)
                    break

    def cargar_zonas(self, zonas: list):
        """
        Cargar lista de zonas en el combo.

        Args:
            zonas: Lista de tuplas (id, nombre_zona)
        """
        self.zona_preferida_combo.clear()
        self.zona_preferida_combo.addItem("Sin preferencia", 0)
        for zona_id, nombre in zonas:
            self.zona_preferida_combo.addItem(nombre, zona_id)

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        Returns:
            Diccionario con fecha_inicio, fecha_fin, zona_preferida_id,
            usar_restricciones, recreos_permitidos
        """
        return {
            "fecha_inicio": self.get_fecha_inicio(),
            "fecha_fin": self.get_fecha_fin(),
            "zona_preferida_id": self.get_zona_preferida_id(),
            "usar_restricciones": self.get_usar_restricciones(),
            "recreos_permitidos": self.get_recreos_permitidos_json(),
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Args:
            datos: Diccionario con fecha_inicio, fecha_fin, zona_preferida_id,
            usar_restricciones, recreos_permitidos
        """
        if "fecha_inicio" in datos:
            self.set_fecha_inicio(datos["fecha_inicio"])
        if "fecha_fin" in datos:
            self.set_fecha_fin(datos["fecha_fin"])
        if "zona_preferida_id" in datos:
            self.set_zona_preferida_id(datos["zona_preferida_id"])
        if "usar_restricciones" in datos:
            self.set_usar_restricciones(datos["usar_restricciones"])
        if "recreos_permitidos" in datos:
            self.set_recreos_permitidos_json(datos["recreos_permitidos"])

    def limpiar(self):
        """Limpiar todos los campos del widget."""
        self.usar_fecha_inicio_checkbox.setChecked(False)
        self.usar_fecha_fin_checkbox.setChecked(False)
        self.usar_restricciones_horario_checkbox.setChecked(False)
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.zona_preferida_combo.setCurrentIndex(0)  # Sin preferencia
        self._marcar_todos_matriz(False)

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Validar que no estén ambas fechas activas (ya manejado por UI, pero por seguridad)
        if self.usar_fecha_inicio_checkbox.isChecked() and self.usar_fecha_fin_checkbox.isChecked():
            return False, "No se pueden usar fecha de inicio y fin simultáneamente"

        # Validar que si se usan restricciones, haya al menos un recreo seleccionado
        if self.get_usar_restricciones():
            tiene_recreos = False
            for dia in self.matriz_checks:
                for recreo in self.matriz_checks[dia]:
                    if self.matriz_checks[dia][recreo].isChecked():
                        tiene_recreos = True
                        break
                if tiene_recreos:
                    break

            if not tiene_recreos:
                return (
                    False,
                    "Si usa restricciones de horario, debe seleccionar al menos un recreo",
                )

        return True, ""
