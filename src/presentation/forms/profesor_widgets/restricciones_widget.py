"""
Widget profesional de restricciones y preferencias del profesor - VERSIÓN 2.

Diseño CRUD profesional con tabla y formulario lateral:
- Tabla de restricciones de horario con columnas: Día, Recreos disponibles
- Formulario lateral para crear/editar restricciones por día
- Botones: Nuevo, Editar, Eliminar, Guardar, Cancelar
- Experiencia de usuario intuitiva y clara
"""

import json
from datetime import date
from typing import Dict, List, Optional, Tuple

from presentation.theme import legacy_styles as styles
from core.logging import get_logger
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from presentation.themes.ccleaner_theme import TEXT_SECONDARY

logger = get_logger(__name__)


class RestriccionesWidget(QGroupBox):
    """
    Widget CRUD profesional para gestionar restricciones y preferencias del profesor.

    Características:
    - Tabla con restricciones por día de la semana
    - Formulario lateral para editar recreos disponibles
    - Botones de acción: Editar, Aplicar a todos, Limpiar todo
    - Validación automática
    """

    # Señales
    restricciones_changed = pyqtSignal()
    preseleccionar_turno_request = pyqtSignal(str)

    # Constantes
    DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    RECREOS = [1, 2, 3, 4]  # R1, R2, R3, R4

    def __init__(self, parent=None):
        """Inicializar widget de restricciones."""
        super().__init__("⚙️ Restricciones y Preferencias", parent)

        # Estado interno: {día_index: [recreos_permitidos]}
        self.restricciones_dias: Dict[int, List[int]] = {}

        # Referencias a widgets
        self.tabla_restricciones: Optional[QTableWidget] = None
        self.recreos_checks: Dict[int, QCheckBox] = {}
        self.form_panel: Optional[QWidget] = None
        self.dia_editando: Optional[int] = None

        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Construir la interfaz de usuario."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)  # Reducido de 12 a 8

        # Sección de fechas
        main_layout.addLayout(self._crear_seccion_fechas())

        # Sección de zona preferida
        main_layout.addLayout(self._crear_seccion_zona_preferida())

        # Separador
        main_layout.addWidget(self._crear_separador())

        # Layout horizontal: Tabla + Panel de edición (SIEMPRE VISIBLE)
        panel_restricciones = QHBoxLayout()
        panel_restricciones.setSpacing(6)  # Reducido de 10 a 6

        # Tabla de restricciones (70%)
        panel_restricciones.addWidget(self._crear_tabla_restricciones(), 70)

        # Panel de edición lateral (30%)
        self.form_panel = self._crear_panel_edicion()
        panel_restricciones.addWidget(self.form_panel, 30)

        # Contenedor para el panel de restricciones (siempre habilitado en modo solo lectura)
        self.panel_restricciones_widget = QWidget()
        self.panel_restricciones_widget.setLayout(panel_restricciones)
        main_layout.addWidget(self.panel_restricciones_widget)

        # Checkbox principal - AL FINAL, después de la matriz
        self.usar_restricciones_checkbox = QCheckBox(
            "☑️ Personalizar disponibilidad (modificar matriz anterior)"
        )
        self.usar_restricciones_checkbox.setStyleSheet(
            styles.STYLE_LABEL_FIELD + " font-weight: bold;"
        )
        self.usar_restricciones_checkbox.setChecked(False)  # Desactivado por defecto
        main_layout.addWidget(self.usar_restricciones_checkbox)

        self.setLayout(main_layout)

    def _crear_separador(self) -> QWidget:
        """Crear línea separadora visual."""
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet(f"background-color: {TEXT_SECONDARY};")
        return separator

    def _crear_seccion_fechas(self) -> QVBoxLayout:
        """Crear sección de fechas mutuamente excluyentes."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Label de sección
        label_seccion = QLabel("📅 <b>Periodo de Guardias:</b>")
        label_seccion.setObjectName("fieldLabel")
        layout.addWidget(label_seccion)

        # Fecha de inicio
        layout_fecha_inicio = QHBoxLayout()
        self.usar_fecha_inicio_checkbox = QCheckBox("Desde:")
        self.usar_fecha_inicio_checkbox.setObjectName("fieldLabel")
        self.usar_fecha_inicio_checkbox.setFixedWidth(80)
        layout_fecha_inicio.addWidget(self.usar_fecha_inicio_checkbox)

        self.fecha_inicio_guardias_input = QDateEdit()
        self.fecha_inicio_guardias_input.setCalendarPopup(True)
        self.fecha_inicio_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_guardias_input.setMaximumWidth(150)
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_inicio_guardias_input.setEnabled(False)
        layout_fecha_inicio.addWidget(self.fecha_inicio_guardias_input)
        layout_fecha_inicio.addStretch()
        layout.addLayout(layout_fecha_inicio)

        # Fecha de fin
        layout_fecha_fin = QHBoxLayout()
        self.usar_fecha_fin_checkbox = QCheckBox("Hasta:")
        self.usar_fecha_fin_checkbox.setObjectName("fieldLabel")
        self.usar_fecha_fin_checkbox.setFixedWidth(80)
        layout_fecha_fin.addWidget(self.usar_fecha_fin_checkbox)

        self.fecha_fin_guardias_input = QDateEdit()
        self.fecha_fin_guardias_input.setCalendarPopup(True)
        self.fecha_fin_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_guardias_input.setMaximumWidth(150)
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setEnabled(False)
        layout_fecha_fin.addWidget(self.fecha_fin_guardias_input)
        layout_fecha_fin.addStretch()
        layout.addLayout(layout_fecha_fin)

        return layout

    def _crear_seccion_zona_preferida(self) -> QVBoxLayout:
        """Crear sección de zona preferida."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Label de sección
        label_seccion = QLabel("🏫 <b>Zona Preferida:</b>")
        label_seccion.setObjectName("fieldLabel")
        layout.addWidget(label_seccion)

        # Combo de zonas
        self.zona_preferida_combo = QComboBox()
        self.zona_preferida_combo.setToolTip(
            "Selecciona la zona preferida del profesor para asignar guardias"
        )
        layout.addWidget(self.zona_preferida_combo)

        return layout

    def _crear_tabla_restricciones(self) -> QWidget:
        """Crear tabla de restricciones por día."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Título
        titulo = QLabel("<b>Disponibilidad por Día</b>")
        titulo.setObjectName("fieldLabel")
        layout.addWidget(titulo)

        # Tabla
        self.tabla_restricciones = QTableWidget()
        self.tabla_restricciones.setColumnCount(2)
        self.tabla_restricciones.setHorizontalHeaderLabels(["Día", "Recreos"])
        self.tabla_restricciones.horizontalHeader().setStretchLastSection(True)
        self.tabla_restricciones.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        self.tabla_restricciones.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_restricciones.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_restricciones.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_restricciones.setAlternatingRowColors(True)
        self.tabla_restricciones.clicked.connect(self._cargar_dia_en_formulario)

        # Poblar tabla con los 5 días
        self._poblar_tabla()

        layout.addWidget(self.tabla_restricciones)

        container.setLayout(layout)
        return container

    def _poblar_tabla(self):
        """Poblar tabla con los 5 días de la semana."""
        self.tabla_restricciones.setRowCount(5)

        for i in range(5):
            # Día de la semana
            dia_item = QTableWidgetItem(self.DIAS_SEMANA[i])
            dia_item.setData(Qt.ItemDataRole.UserRole, i)  # Guardar índice del día
            self.tabla_restricciones.setItem(i, 0, dia_item)

            # Recreos (inicialmente vacío)
            recreos_item = QTableWidgetItem("—")
            recreos_item.setForeground(Qt.GlobalColor.gray)
            self.tabla_restricciones.setItem(i, 1, recreos_item)

    def _crear_panel_edicion(self) -> QWidget:
        """Crear panel lateral de edición de recreos (SIEMPRE visible)."""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Label del día seleccionado
        self.label_dia_editando = QLabel("Selecciona un día de la tabla")
        self.label_dia_editando.setStyleSheet("font-weight: bold; font-size: 13px; color: #007ACC;")
        self.label_dia_editando.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_dia_editando)

        # Checkboxes de recreos
        recreos_group = QGroupBox("Recreos disponibles:")
        recreos_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        recreos_layout = QVBoxLayout()
        recreos_layout.setSpacing(6)

        for recreo in self.RECREOS:
            check = QCheckBox(f"Recreo {recreo} (R{recreo})")
            check.setObjectName("fieldLabel")
            check.setEnabled(False)
            recreos_layout.addWidget(check)
            self.recreos_checks[recreo] = check

        recreos_group.setLayout(recreos_layout)
        layout.addWidget(recreos_group)

        # Botones de acción - SIMPLIFICADOS
        layout.addWidget(self._crear_separador())

        # Solo 2 botones: aplicar a todos y restaurar defecto
        btn_aplicar_todos = QPushButton("Aplicar a todos")
        btn_aplicar_todos.clicked.connect(self._aplicar_recreos_a_todos)
        btn_aplicar_todos.setToolTip(
            "Copia la configuración de recreos actual a todos los días de la semana"
        )
        layout.addWidget(btn_aplicar_todos)

        btn_limpiar_todo = QPushButton("Restaurar defecto")
        btn_limpiar_todo.setProperty("warning", True)
        btn_limpiar_todo.clicked.connect(self._restaurar_por_turno)
        btn_limpiar_todo.setToolTip("Restaura los recreos por defecto según el turno del profesor")
        layout.addWidget(btn_limpiar_todo)

        layout.addStretch()

        panel.setLayout(layout)
        return panel

    def _conectar_senales(self):
        """Conectar señales de los campos."""
        self.usar_fecha_inicio_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_fecha_fin_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_restricciones_checkbox.stateChanged.connect(self._toggle_panel_restricciones)

        # Señales de cambio
        self.fecha_inicio_guardias_input.dateChanged.connect(self.restricciones_changed.emit)
        self.fecha_fin_guardias_input.dateChanged.connect(self.restricciones_changed.emit)

        # Auto-guardar cambios en recreos cuando se modifican los checkboxes
        for check in self.recreos_checks.values():
            check.stateChanged.connect(self._auto_guardar_recreos_dia_actual)
            check.stateChanged.connect(self.restricciones_changed.emit)

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

    def _toggle_panel_restricciones(self):
        """Activar/desactivar EDICIÓN del panel de restricciones."""
        is_checked = self.usar_restricciones_checkbox.isChecked()

        # Habilitar/deshabilitar EDICIÓN de los checkboxes en el panel lateral
        for check in self.recreos_checks.values():
            check.setEnabled(is_checked)

        # Habilitar/deshabilitar botones de edición del panel lateral
        if self.form_panel:
            for widget in self.form_panel.findChildren(QPushButton):
                widget.setEnabled(is_checked)

        # Si se activa, seleccionar el primer día automáticamente
        if is_checked and self.tabla_restricciones.rowCount() > 0:
            self.tabla_restricciones.selectRow(0)
            self._cargar_dia_en_formulario()

        self.restricciones_changed.emit()

    def _cargar_dia_en_formulario(self):
        """
        Cargar el día seleccionado en el formulario.

        Siempre se puede ver, solo lectura si no está activado.
        """
        fila_actual = self.tabla_restricciones.currentRow()
        if fila_actual < 0:
            return

        dia_item = self.tabla_restricciones.item(fila_actual, 0)
        if not dia_item:
            return

        dia_index = dia_item.data(Qt.ItemDataRole.UserRole)
        dia_nombre = dia_item.text()

        self.dia_editando = dia_index
        self.label_dia_editando.setText(dia_nombre)

        # Cargar recreos del día (siempre se muestran)
        recreos_actuales = self.restricciones_dias.get(dia_index, [])
        for recreo, check in self.recreos_checks.items():
            check.setChecked(recreo in recreos_actuales)

        # Los checkboxes solo se habilitan si el checkbox principal está activado
        is_restricciones_activas = self.usar_restricciones_checkbox.isChecked()
        for check in self.recreos_checks.values():
            check.setEnabled(is_restricciones_activas)

    def _auto_guardar_recreos_dia_actual(self):
        """
        Auto-guardar cambios de recreos del día actual cuando se modifican checkboxes.

        Este método se llama automáticamente cuando cambia cualquier checkbox de recreo.
        """
        if self.dia_editando is None:
            return

        # No auto-guardar si el checkbox de restricciones no está activo
        if not self.usar_restricciones_checkbox.isChecked():
            return

        # Obtener recreos seleccionados
        recreos_seleccionados = [
            recreo for recreo, check in self.recreos_checks.items() if check.isChecked()
        ]

        # Actualizar estado interno
        if recreos_seleccionados:
            self.restricciones_dias[self.dia_editando] = recreos_seleccionados
        else:
            # Si no hay recreos, eliminar el día del diccionario
            self.restricciones_dias.pop(self.dia_editando, None)

        # Actualizar tabla
        self._actualizar_tabla()

    def _aplicar_recreos_a_dia(self):
        """
        Aplicar los recreos seleccionados al día actual.

        NOTA: Este método ya NO es necesario con el auto-guardado,
        pero se mantiene por compatibilidad.
        """
        self._auto_guardar_recreos_dia_actual()
        self.restricciones_changed.emit()

    def _aplicar_recreos_a_todos(self):
        """Aplicar los recreos seleccionados actualmente a todos los días de la semana."""
        # Obtener recreos seleccionados
        recreos_seleccionados = [
            recreo for recreo, check in self.recreos_checks.items() if check.isChecked()
        ]

        if not recreos_seleccionados:
            return

        # Aplicar a todos los días
        for i in range(5):
            self.restricciones_dias[i] = recreos_seleccionados.copy()

        # Actualizar tabla
        self._actualizar_tabla()

        self.restricciones_changed.emit()

    def _restaurar_por_turno(self):
        """
        Restaurar restricciones a los valores por defecto según el turno del profesor.

        Este método obtiene el turno actual del widget de horario y recarga
        la matriz con los valores predeterminados.
        """
        # Obtener el turno del widget de horario (padre)
        turno_actual = "Mañana"  # Por defecto
        try:
            # Intentar obtener el turno del formulario padre
            if hasattr(self.parent(), "horario_widget"):
                turno_widget = self.parent().horario_widget
                turno_actual = turno_widget.turno_input.currentText()
        except (ValueError, TypeError, OSError) as e:
            logger.debug(f"No se pudo obtener turno del widget padre: {e}")

        # Preseleccionar según turno
        self.preseleccionar_segun_turno(turno_actual)

        # Si hay un día seleccionado, recargar su formulario
        if self.dia_editando is not None:
            self._cargar_dia_en_formulario()

        self.restricciones_changed.emit()

    def _actualizar_tabla(self):
        """Actualizar la tabla con el estado actual de restricciones."""
        for i in range(5):
            recreos = self.restricciones_dias.get(i, [])

            if recreos:
                # Formatear como "R1, R2, R4"
                recreos_texto = ", ".join([f"R{r}" for r in sorted(recreos)])
                recreos_item = QTableWidgetItem(recreos_texto)
                recreos_item.setForeground(Qt.GlobalColor.black)
            else:
                recreos_item = QTableWidgetItem("—")
                recreos_item.setForeground(Qt.GlobalColor.gray)

            self.tabla_restricciones.setItem(i, 1, recreos_item)

    def _obtener_recreos_por_defecto(self, turno: str) -> Dict[int, List[int]]:
        """
        Obtener la configuración de recreos por defecto según el turno.

        Args:
            turno: Turno del profesor ('Mañana', 'Tarde', 'Mixto')

        Returns:
            Diccionario con los recreos por defecto para cada día
        """
        turno_lower = turno.lower()
        recreos_defecto = {}

        for dia in range(5):
            if turno_lower == "mañana":
                recreos_defecto[dia] = [1, 2]
            elif turno_lower == "tarde":
                recreos_defecto[dia] = [3, 4]
            elif turno_lower == "mixto":
                recreos_defecto[dia] = [1, 2, 3, 4]
            else:
                recreos_defecto[dia] = []

        return recreos_defecto

    def _son_restricciones_personalizadas(
        self, restricciones: Dict[int, List[int]], recreos_defecto: Dict[int, List[int]]
    ) -> bool:
        """
        Verificar si las restricciones son diferentes a las del turno por defecto.

        Args:
            restricciones: Restricciones actuales del profesor
            recreos_defecto: Recreos por defecto según turno

        Returns:
            True si hay diferencias (personalizadas), False si son iguales al defecto
        """
        # Si no hay restricciones, no es personalizado
        if not restricciones:
            return False

        # Si no tienen el mismo número de días, es personalizado
        if len(restricciones) != len(recreos_defecto):
            return True

        # Comparar día por día
        for dia in range(5):
            restriccion_dia = sorted(restricciones.get(dia, []))
            defecto_dia = sorted(recreos_defecto.get(dia, []))

            if restriccion_dia != defecto_dia:
                return True  # Hay diferencias

        return False  # Son iguales

    def preseleccionar_segun_turno(self, turno: str):
        """Pre-seleccionar recreos según el turno del profesor."""
        turno_lower = turno.lower()

        # Limpiar primero
        self.restricciones_dias.clear()

        # Pre-seleccionar según turno
        for dia in range(5):
            if turno_lower == "mañana":
                self.restricciones_dias[dia] = [1, 2]
            elif turno_lower == "tarde":
                self.restricciones_dias[dia] = [3, 4]
            elif turno_lower == "mixto":
                self.restricciones_dias[dia] = [1, 2, 3, 4]

        # Actualizar tabla y formulario
        self._actualizar_tabla()

        # Si hay un día seleccionado, recargar
        if self.dia_editando is not None:
            self._cargar_dia_en_formulario()

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
        return self.usar_restricciones_checkbox.isChecked()

    def set_usar_restricciones(self, usar: bool):
        """Establecer si se usan restricciones personalizadas."""
        self.usar_restricciones_checkbox.setChecked(usar)

    def get_recreos_permitidos_json(self) -> str:
        """
        Obtener recreos permitidos como JSON.

        Returns:
            JSON string con formato {"0": [1, 2], "1": [1, 2, 4]}
        """
        if not self.restricciones_dias:
            return ""

        # Convertir claves a string para JSON
        resultado = {str(dia): recreos for dia, recreos in self.restricciones_dias.items()}
        return json.dumps(resultado)

    def set_recreos_permitidos_json(self, json_str):
        """
        Cargar recreos permitidos desde JSON.

        Args:
            json_str: JSON string con formato {"0": [1, 2]} o diccionario
        """
        self.restricciones_dias.clear()

        # Solo retornar si es None o string vacía (dict vacío {} es válido)
        if json_str is None or (isinstance(json_str, str) and not json_str):
            self._actualizar_tabla()
            return

        try:
            # Si ya es un diccionario, usarlo directamente (incluso si está vacío {})
            if isinstance(json_str, dict):
                datos = json_str
            # Si ya es una lista plana [1,2,3], convertir a dict aplicando a todos los días
            elif isinstance(json_str, list):
                datos = {str(d): json_str for d in range(5)}
            # Si es string, parsearlo
            elif isinstance(json_str, str):
                datos = json.loads(json_str)
                # El JSON puede haberse decodificado como lista plana
                if isinstance(datos, list):
                    datos = {str(d): datos for d in range(5)}
            else:
                self._actualizar_tabla()
                return

            # Cargar datos (si datos está vacío {}, no entra al loop pero es válido)
            for dia_str, recreos in datos.items():
                try:
                    dia_int = int(dia_str)
                    if 0 <= dia_int < 5 and isinstance(recreos, list):
                        self.restricciones_dias[dia_int] = recreos
                except (ValueError, TypeError):
                    continue

            # ✅ IMPORTANTE: Actualizar tabla SIEMPRE después de cargar datos
            self._actualizar_tabla()

            # ✅ Si hay un día seleccionado en la tabla, recargar su formulario
            if self.dia_editando is not None:
                self._cargar_dia_en_formulario()
            # ✅ Si no hay día seleccionado pero hay datos, seleccionar el primer día
            elif self.restricciones_dias and self.tabla_restricciones.rowCount() > 0:
                self.tabla_restricciones.selectRow(0)
                self._cargar_dia_en_formulario()

        except (json.JSONDecodeError, TypeError, ValueError):
            pass  # Ignorar errores de formato

    def get_zona_preferida_id(self) -> Optional[int]:
        """Obtener ID de zona preferida seleccionada."""
        zona_id = self.zona_preferida_combo.currentData()
        return zona_id if zona_id and zona_id > 0 else None

    def set_zona_preferida_id(self, zona_id: Optional[int]):
        """Establecer zona preferida por ID."""
        if zona_id is None:
            self.zona_preferida_combo.setCurrentIndex(0)
        else:
            for i in range(self.zona_preferida_combo.count()):
                if self.zona_preferida_combo.itemData(i) == zona_id:
                    self.zona_preferida_combo.setCurrentIndex(i)
                    break

    def cargar_zonas(self, zonas: list):
        """Cargar lista de zonas en el combo."""
        self.zona_preferida_combo.clear()
        self.zona_preferida_combo.addItem("Sin preferencia", 0)
        for zona_id, nombre in zonas:
            self.zona_preferida_combo.addItem(nombre, zona_id)

    def get_dias_permitidos(self) -> Optional[List[int]]:
        """
        Obtener lista de días permitidos.

        Returns:
            Lista con índices de días (0-4) que tienen restricciones, o None si no hay
        """
        if not self.restricciones_dias:
            return None
        return list(self.restricciones_dias.keys())

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        IMPORTANTE: Solo devuelve recreos_permitidos si el checkbox está ACTIVADO.
        Si está desactivado, la matriz es solo visual (según turno por defecto).
        """
        # Determinar días permitidos y recreos
        dias_permitidos = None
        recreos_json = ""

        # SOLO guardar restricciones si el checkbox está activado
        if self.get_usar_restricciones() and self.restricciones_dias:
            dias_permitidos = sorted(self.restricciones_dias.keys())
            recreos_json = self.get_recreos_permitidos_json()

        return {
            "fecha_inicio": self.get_fecha_inicio(),
            "fecha_fin": self.get_fecha_fin(),
            "zona_preferida_id": self.get_zona_preferida_id(),
            "usar_restricciones": self.get_usar_restricciones(),
            "recreos_permitidos": recreos_json,
            "dias_permitidos": dias_permitidos,
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Siempre carga la matriz desde la BD. Solo activa el checkbox si las restricciones
        guardadas SON DIFERENTES al turno por defecto actual.
        """
        if "fecha_inicio" in datos:
            self.set_fecha_inicio(datos["fecha_inicio"])
        if "fecha_fin" in datos:
            self.set_fecha_fin(datos["fecha_fin"])
        if "zona_preferida_id" in datos:
            self.set_zona_preferida_id(datos["zona_preferida_id"])

        # Obtener turno actual
        turno_actual = datos.get("turno", "Mañana")

        # Calcular recreos por defecto según turno
        recreos_por_defecto = self._obtener_recreos_por_defecto(turno_actual)

        # ✅ SIEMPRE cargar las restricciones guardadas en la BD
        if "recreos_permitidos" in datos and datos["recreos_permitidos"] is not None:
            # Cargar restricciones desde BD (aunque sea dict vacío {})
            self.set_recreos_permitidos_json(datos["recreos_permitidos"])

            # ✅ Verificar si son DIFERENTES al turno por defecto
            son_personalizadas = self._son_restricciones_personalizadas(
                self.restricciones_dias, recreos_por_defecto
            )

            # ✅ Solo activar checkbox si fueron EDITADAS (diferentes al defecto)
            self.set_usar_restricciones(son_personalizadas)
        else:
            # ✅ Si no hay datos en BD (None), usar valores por defecto según turno
            self.set_usar_restricciones(False)
            self.preseleccionar_segun_turno(turno_actual)

    def limpiar(self):
        """Limpiar todos los campos del widget (estado inicial)."""
        self.usar_fecha_inicio_checkbox.setChecked(False)
        self.usar_fecha_fin_checkbox.setChecked(False)
        self.usar_restricciones_checkbox.setChecked(False)  # Desactivado por defecto
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.zona_preferida_combo.setCurrentIndex(0)
        self.restricciones_dias.clear()
        self._actualizar_tabla()

        for check in self.recreos_checks.values():
            check.setChecked(False)
            check.setEnabled(False)  # Deshabilitado por defecto

        self.dia_editando = None
        self.label_dia_editando.setText("Selecciona un día de la tabla")

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        SOLO valida restricciones si el checkbox está activado.
        """
        # Validar exclusividad de fechas
        if self.usar_fecha_inicio_checkbox.isChecked() and self.usar_fecha_fin_checkbox.isChecked():
            return False, "No se pueden usar fecha de inicio y fin simultáneamente"

        # Validar restricciones SOLO si el checkbox está activo
        if self.get_usar_restricciones():
            if not self.restricciones_dias:
                return (
                    False,
                    "Si activa restricciones de horario, debe configurar al menos un día",
                )

            # Verificar que cada día tenga al menos un recreo
            for dia, recreos in self.restricciones_dias.items():
                if not recreos:
                    dia_nombre = self.DIAS_SEMANA[dia]
                    return (False, f"El {dia_nombre} debe tener al menos un recreo disponible")

        return True, ""
