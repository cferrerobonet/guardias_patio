"""
Formulario de gestión de profesores.

Este módulo implementa la UI para crear, editar, eliminar y buscar profesores.
Incluye una tabla con búsqueda y un formulario detallado con validaciones.
"""

import json
from typing import Dict, Optional

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import ui_styles as styles
from application.dtos.profesor_dto import ActualizarProfesorDTO, CrearProfesorDTO
from application.use_cases.profesor import (
    ActualizarProfesorUseCase,
    BuscarProfesoresUseCase,
    CrearProfesorUseCase,
    EliminarProfesorUseCase,
    ListarProfesoresUseCase,
)
from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import (
    CONTENT_BG_ALT,
    FONT_SIZE_SMALL,
    PRIMARY_BLUE,
    RADIUS_SMALL,
    SPACING_MD,
    SPACING_SM,
    TEXT_SECONDARY,
)
from utils.validators import validar_email, validar_horas_contrato, validar_nombre_completo


class ProfesorForm(BaseForm):
    """Formulario para gestión completa de profesores."""

    # Señal que se emite cuando se modifican los datos de profesores
    datos_modificados = pyqtSignal()

    def __init__(self, session):
        """
        Inicializar formulario de profesores.

        Args:
            session: Sesión de base de datos para operaciones CRUD
        """
        super().__init__(session)
        self.setWindowTitle("Gestión de Profesores")

        # Variable para trackear modo edición
        self.profesor_editando_id: Optional[int] = None

        # Inicializar Use Cases
        self.crear_use_case = CrearProfesorUseCase(session)
        self.actualizar_use_case = ActualizarProfesorUseCase(session)
        self.eliminar_use_case = EliminarProfesorUseCase(session)
        self.listar_use_case = ListarProfesoresUseCase(session)
        self.buscar_use_case = BuscarProfesoresUseCase(session)

        # Configurar atajos
        self._configurar_atajos()

        # Construir UI
        self.setup_ui()

        # Cargar datos iniciales
        self.cargar_profesores()

    def setup_ui(self):
        """Construir la interfaz del formulario con diseño responsivo."""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # ========== CREAR SPLITTER HORIZONTAL ==========
        # Permite redimensionar manualmente tabla vs formulario
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ========== SECCIÓN IZQUIERDA: TABLA ==========
        left_widget = self._crear_widget_tabla()
        splitter.addWidget(left_widget)

        # ========== SECCIÓN DERECHA: FORMULARIO CON SCROLL ==========
        right_widget = self._crear_widget_formulario_con_scroll()
        splitter.addWidget(right_widget)

        # Establecer proporciones iniciales: 60% tabla, 40% formulario
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _crear_widget_tabla(self) -> QWidget:
        """Crear widget contenedor para la sección de tabla."""
        widget = QWidget()
        layout = self._crear_seccion_tabla()
        widget.setLayout(layout)
        return widget

    def _crear_widget_formulario_con_scroll(self) -> QWidget:
        """Crear widget con scroll para el formulario."""
        # Crear contenedor del formulario
        form_container = QWidget()
        form_layout = self._crear_seccion_formulario()
        form_container.setLayout(form_layout)

        # Envolver en QScrollArea
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # CRÍTICO: permite que el widget se ajuste
        scroll_area.setWidget(form_container)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Crear widget contenedor para el scroll
        container = QWidget()
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(scroll_area)
        container.setLayout(container_layout)

        return container

    def _crear_seccion_tabla(self) -> QVBoxLayout:
        """Crear sección izquierda con tabla de profesores."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Título con contador
        self.titulo_lista_profesores = QLabel("📋 PROFESORES REGISTRADOS (0)")
        self.titulo_lista_profesores.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(self.titulo_lista_profesores)

        # Campo de búsqueda
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setSpacing(8)

        busqueda_label = QLabel("🔍 Buscar:")
        busqueda_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        busqueda_layout.addWidget(busqueda_label)

        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("Buscar por nombre o email...")
        self.busqueda_input.setStyleSheet(styles.STYLE_INPUT)
        self.busqueda_input.textChanged.connect(self.filtrar_profesores)
        busqueda_layout.addWidget(self.busqueda_input)

        self.limpiar_busqueda_btn = QPushButton("✖")
        self.limpiar_busqueda_btn.setFixedWidth(30)
        self.limpiar_busqueda_btn.setToolTip("Limpiar búsqueda")
        self.limpiar_busqueda_btn.clicked.connect(self.limpiar_busqueda)
        self.limpiar_busqueda_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        busqueda_layout.addWidget(self.limpiar_busqueda_btn)

        layout.addLayout(busqueda_layout)

        # Tabla de profesores
        self.tabla_profesores = QTableWidget()
        self.tabla_profesores.setColumnCount(5)
        self.tabla_profesores.setHorizontalHeaderLabels([
            "Nombre Completo", "Email", "Horas", "Turno", "Tutor"
        ])
        self.tabla_profesores.horizontalHeader().setStretchLastSection(False)
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for i in [1, 2, 3, 4]:
            self.tabla_profesores.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla_profesores.setSortingEnabled(True)
        self.tabla_profesores.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        # Permitir selección múltiple (Ctrl+clic o Shift+clic)
        self.tabla_profesores.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )
        self.tabla_profesores.doubleClicked.connect(self.editar_profesor)

        layout.addWidget(self.tabla_profesores)
        
        # Label informativo de multiselección
        info_label = QLabel("💡 <b>Selección múltiple:</b> Ctrl+clic (individual) | Shift+clic (rango) | Ctrl+A (todos) | Supr (eliminar)")
        info_label.setStyleSheet(f"""
            QLabel {{
                background-color: {CONTENT_BG_ALT};
                color: {TEXT_SECONDARY};
                font-size: {FONT_SIZE_SMALL}px;
                padding: {SPACING_SM}px {SPACING_MD}px;
                border-left: 3px solid {PRIMARY_BLUE};
                border-radius: {RADIUS_SMALL}px;
            }}
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Botones de gestión
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_profesores)
        self.refresh_btn.setToolTip("Recargar la lista de profesores (F5)")

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.editar_profesor)
        self.editar_btn.setToolTip("Editar el profesor seleccionado")

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_profesor)
        self.delete_btn.setToolTip(
            "Eliminar profesor(es) seleccionado(s)\n"
            "💡 Ctrl+clic: selección múltiple\n"
            "💡 Shift+clic: rango de selección"
        )

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.editar_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        return layout

    def _crear_seccion_formulario(self) -> QVBoxLayout:
        """Crear sección derecha con formulario de alta/edición."""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Cambiado de (10, 0, 10, 10) a (10, 10, 10, 10)
        layout.setSpacing(12)

        self.titulo_seccion = QLabel("✏️ ALTA DE PROFESOR")
        self.titulo_seccion.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(self.titulo_seccion)

        # Grupos del formulario
        layout.addWidget(self._crear_grupo_basicos())
        layout.addWidget(self._crear_grupo_horario())
        layout.addWidget(self._crear_grupo_restricciones())

        # Botones de acción
        botones_accion = QHBoxLayout()
        botones_accion.setSpacing(10)

        self.submit_btn = QPushButton("💾 Guardar nuevo profesor")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_profesor)

        self.cancelar_btn = QPushButton("❌ Cancelar Edición")
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.cancelar_btn.clicked.connect(self.cancelar_edicion)
        self.cancelar_btn.setVisible(False)

        botones_accion.addWidget(self.submit_btn)
        botones_accion.addWidget(self.cancelar_btn)
        layout.addLayout(botones_accion)

        layout.addStretch()

        return layout

    def _crear_grupo_basicos(self) -> QGroupBox:
        """Crear grupo de datos básicos."""
        grupo = QGroupBox("📋 Datos Básicos")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Nombre completo
        label_nombre = QLabel("Nombre completo (formato: APELLIDOS, NOMBRE):")
        label_nombre.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_nombre)

        self.nombre_completo_input = QLineEdit()
        self.nombre_completo_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")
        self.nombre_completo_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_completo_input.setMaximumWidth(350)
        self.nombre_completo_input.setToolTip(
            "Formato requerido: APELLIDOS, NOMBRE\n"
            "Ejemplo: GARCÍA LÓPEZ, JUAN\n"
            "Debe contener una coma separando apellidos y nombre"
        )
        layout.addWidget(self.nombre_completo_input)

        # Email
        label_email = QLabel("Email corporativo:")
        label_email.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_email)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("profesor@colegio.edu")
        self.email_input.setStyleSheet(styles.STYLE_INPUT)
        self.email_input.setMaximumWidth(350)
        self.email_input.setToolTip(
            "Email corporativo del profesor (opcional)\n"
            "Se usará para enviar calendarios y notificaciones"
        )
        layout.addWidget(self.email_input)

        # Tutor
        self.tutor_checkbox = QCheckBox("✓ Es tutor/a")
        self.tutor_checkbox.setStyleSheet("font-size: 13px; margin-top: 5px;")
        self.tutor_checkbox.setToolTip(
            "Marca si el profesor es tutor de un grupo\n"
            "Los tutores pueden tener un ajuste de carga diferente"
        )
        layout.addWidget(self.tutor_checkbox)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_horario(self) -> QGroupBox:
        """Crear grupo de configuración de horario."""
        grupo = QGroupBox("🕐 Configuración de Horario")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Primera fila: Horas y Turno
        layout_fila1 = QHBoxLayout()
        layout_fila1.setSpacing(15)

        label_horas = QLabel("Horas de contrato:")
        label_horas.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fila1.addWidget(label_horas)

        self.horas_input = QLineEdit()
        self.horas_input.setPlaceholderText("Ej: 30.0")
        self.horas_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_input.setMaximumWidth(100)
        self.horas_input.setToolTip(
            "Horas totales de contrato del profesor\n"
            "Debe ser un número positivo (ej: 30.0)"
        )
        layout_fila1.addWidget(self.horas_input)

        layout_fila1.addSpacing(20)

        label_turno = QLabel("Turno:")
        label_turno.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fila1.addWidget(label_turno)

        self.turno_input = QComboBox()
        self.turno_input.addItems(["Mañana", "Tarde", "Mixto"])
        self.turno_input.setStyleSheet(styles.STYLE_INPUT)
        self.turno_input.setMaximumWidth(120)
        layout_fila1.addWidget(self.turno_input)

        layout_fila1.addStretch()
        layout.addLayout(layout_fila1)

        layout.addSpacing(15)

        # Segunda fila: Campos mixto (ocultos por defecto)
        layout_mixto = QHBoxLayout()
        layout_mixto.setSpacing(10)

        self.label_horas_manana = QLabel("  🌅 Horas mañana:")
        self.label_horas_manana.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_mixto.addWidget(self.label_horas_manana)

        self.horas_manana_input = QLineEdit()
        self.horas_manana_input.setPlaceholderText("Ej: 15.0")
        self.horas_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_manana_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_manana_input)

        layout_mixto.addSpacing(20)

        self.label_horas_tarde = QLabel("🌆 Horas tarde:")
        self.label_horas_tarde.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_mixto.addWidget(self.label_horas_tarde)

        self.horas_tarde_input = QLineEdit()
        self.horas_tarde_input.setPlaceholderText("Ej: 15.0")
        self.horas_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_tarde_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_tarde_input)

        layout_mixto.addStretch()
        layout.addLayout(layout_mixto)

        grupo.setLayout(layout)

        # Conectar señal para mostrar/ocultar campos mixto
        self._toggle_mixto_fields(False)
        self.turno_input.currentTextChanged.connect(self._on_turno_changed)

        return grupo

    def _crear_grupo_restricciones(self) -> QGroupBox:
        """Crear grupo de restricciones y preferencias."""
        grupo = QGroupBox("⚙️ Restricciones y Preferencias")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Fechas de guardias
        layout.addLayout(self._crear_seccion_fechas())

        # Matriz de disponibilidad
        self.usar_restricciones_horario_checkbox = QCheckBox(
            "☑️ Usar restricciones personalizadas de horario"
        )
        self.usar_restricciones_horario_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_restricciones_horario_checkbox.stateChanged.connect(
            self._toggle_matriz_horario
        )
        layout.addWidget(self.usar_restricciones_horario_checkbox)

        label_matriz = QLabel("📅 Disponibilidad por día y recreo:")
        label_matriz.setStyleSheet(styles.STYLE_LABEL_FIELD + " font-weight: bold;")
        layout.addWidget(label_matriz)

        # Widget contenedor de la matriz
        self.matriz_horario_widget = self._crear_matriz_horario()
        layout.addWidget(self.matriz_horario_widget)

        grupo.setLayout(layout)
        return grupo

    def _crear_seccion_fechas(self) -> QVBoxLayout:
        """Crear sección de fechas mutuamente excluyentes."""
        layout = QVBoxLayout()

        # Fecha de inicio
        layout_fecha_inicio = QHBoxLayout()
        self.usar_fecha_inicio_checkbox = QCheckBox("Usar fecha de inicio:")
        self.usar_fecha_inicio_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_fecha_inicio_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
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
        self.usar_fecha_fin_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
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

    def _crear_matriz_horario(self) -> QWidget:
        """Crear widget con matriz de disponibilidad día × recreo."""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Grid de checkboxes
        grid_matriz = QGridLayout()
        grid_matriz.setSpacing(8)

        # Encabezados
        dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        grid_matriz.addWidget(QLabel(""), 0, 0)
        for col in range(4):
            label_recreo = QLabel(f"<b>R{col+1}</b>")
            label_recreo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_matriz.addWidget(label_recreo, 0, col + 1)

        # Crear matriz de checkboxes
        self.matriz_checks: Dict[int, Dict[int, QCheckBox]] = {}
        for fila, dia_idx in enumerate(range(7)):
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

    def _configurar_atajos(self):
        """Configurar atajos de teclado."""
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.guardar_profesor)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(
            lambda: self.busqueda_input.setFocus()
        )
        QShortcut(QKeySequence("F5"), self).activated.connect(self.cargar_profesores)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.cancelar_edicion)
        QShortcut(QKeySequence("Del"), self).activated.connect(self.eliminar_profesor)
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.seleccionar_todos)

    def seleccionar_todos(self):
        """Seleccionar todos los profesores de la tabla."""
        if self.tabla_profesores.rowCount() > 0:
            self.tabla_profesores.selectAll()
            
    def _toggle_mixto_fields(self, visible: bool):
        """Mostrar/ocultar campos de turno mixto."""
        for w in [
            self.label_horas_manana,
            self.horas_manana_input,
            self.label_horas_tarde,
            self.horas_tarde_input,
        ]:
            w.setVisible(visible)

    def _on_turno_changed(self, value: str):
        """Manejar cambio en selector de turno."""
        self._toggle_mixto_fields(value.lower() == "mixto")

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

    def _toggle_matriz_horario(self):
        """Activar/desactivar matriz de disponibilidad."""
        is_checked = self.usar_restricciones_horario_checkbox.isChecked()
        self.matriz_horario_widget.setEnabled(is_checked)
        self.btn_marcar_todos.setEnabled(is_checked)
        self.btn_desmarcar_todos.setEnabled(is_checked)

        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setEnabled(is_checked)

    def _marcar_todos_matriz(self, estado: bool):
        """Marcar/desmarcar todos los checkboxes de la matriz."""
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setChecked(estado)

    def _matriz_a_json(self) -> str:
        """
        Convertir matriz de checkboxes a JSON.

        Returns:
            JSON string con formato {"0": [1, 2], "2": [1, 3, 4]}
            donde clave = día (0-6) y valor = lista de recreos (1-4)
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

    def _json_a_matriz(self, json_str: str):
        """
        Cargar datos JSON en matriz de checkboxes.

        Args:
            json_str: JSON string con formato {"0": [1, 2], "2": [1, 3, 4]}
                     o lista simple [1, 2, 3, 4] (formato nuevo)
        """
        self._marcar_todos_matriz(False)

        if not json_str:
            return

        try:
            datos = json.loads(json_str)

            # Si es una lista simple (formato nuevo), marcar todos los días con esos recreos
            if isinstance(datos, list):
                # Formato nuevo: lista de recreos [1, 2, 3, 4]
                # Marcar esos recreos en todos los días
                for dia in self.matriz_checks:
                    for recreo in datos:
                        if recreo in self.matriz_checks[dia]:
                            self.matriz_checks[dia][recreo].setChecked(True)

            # Si es un diccionario (formato viejo), usar el método original
            elif isinstance(datos, dict):
                # Formato viejo: {"0": [1, 2], "1": [1]}
                for dia_str, recreos in datos.items():
                    dia = int(dia_str)
                    if dia in self.matriz_checks:
                        for recreo in recreos:
                            if recreo in self.matriz_checks[dia]:
                                self.matriz_checks[dia][recreo].setChecked(True)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            self.mostrar_error("Error al cargar matriz", f"Error al cargar matriz de horario: {e}")

    def _extraer_listas_desde_matriz(self) -> tuple[list[int], list[int]]:
        """
        Extrae listas simples desde la matriz de checkboxes.

        Si no hay restricciones personalizadas, retorna valores por defecto.

        Returns:
            tuple: (dias_permitidos, recreos_permitidos)
                - dias_permitidos: lista de días (0-6) donde hay al menos un recreo marcado
                - recreos_permitidos: lista de recreos (1-4) marcados en cualquier día
        """
        if not self.usar_restricciones_horario_checkbox.isChecked():
            # Sin restricciones: todos los días y recreos
            return list(range(7)), [1, 2, 3, 4]

        dias_con_checkmarks = set()
        recreos_con_checkmarks = set()

        # Recorrer toda la matriz
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                if self.matriz_checks[dia][recreo].isChecked():
                    dias_con_checkmarks.add(dia)
                    recreos_con_checkmarks.add(recreo)

        # Convertir sets a listas ordenadas
        dias_permitidos = (
            sorted(list(dias_con_checkmarks))
            if dias_con_checkmarks
            else list(range(7))
        )
        recreos_permitidos = (
            sorted(list(recreos_con_checkmarks))
            if recreos_con_checkmarks
            else [1, 2, 3, 4]
        )

        return dias_permitidos, recreos_permitidos

    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario."""
        self.nombre_completo_input.clear()
        self.email_input.clear()
        self.horas_input.clear()
        self.horas_manana_input.clear()
        self.horas_tarde_input.clear()
        self.tutor_checkbox.setChecked(False)
        self.usar_fecha_inicio_checkbox.setChecked(False)
        self.usar_fecha_fin_checkbox.setChecked(False)
        self.fecha_inicio_guardias_input.clear()
        self.fecha_inicio_guardias_input.setEnabled(False)
        self.fecha_fin_guardias_input.clear()
        self.fecha_fin_guardias_input.setEnabled(False)
        self.usar_restricciones_horario_checkbox.setChecked(False)
        self._marcar_todos_matriz(False)
        self.turno_input.setCurrentIndex(0)
        self.profesor_editando_id = None
        self.titulo_seccion.setText("✏️ ALTA DE PROFESOR")
        self.submit_btn.setText("💾 Guardar nuevo profesor")
        self.cancelar_btn.setVisible(False)

    def cancelar_edicion(self):
        """Cancelar edición y volver a modo creación."""
        self._limpiar_formulario()
        self.mostrar_exito("Cancelado", "Edición cancelada.")

    def guardar_profesor(self):
        """Crear o actualizar profesor según el modo actual."""
        try:
            # Validar nombre
            nombre_completo = self.nombre_completo_input.text().strip()
            valido, error_msg = validar_nombre_completo(nombre_completo)
            if not valido:
                self.mostrar_advertencia("Validación de nombre", error_msg)
                return

            # Validar horas
            try:
                horas = float(self.horas_input.text())
            except ValueError:
                self.mostrar_advertencia(
                    "Validación de horas",
                    "Las horas de contrato deben ser un número válido."
                )
                return

            valido, error_msg = validar_horas_contrato(horas)
            if not valido:
                self.mostrar_advertencia("Validación de horas", error_msg)
                return

            # Obtener turno
            turno = self.turno_input.currentText().lower()

            # Validar turno mixto
            horas_manana = horas_tarde = None
            if turno == "mixto":
                if not self.horas_manana_input.text() or not self.horas_tarde_input.text():
                    self.mostrar_advertencia(
                        "Validación de turno mixto",
                        "Debes indicar horas de mañana y tarde para turno mixto."
                    )
                    return
                try:
                    horas_manana = float(self.horas_manana_input.text())
                    horas_tarde = float(self.horas_tarde_input.text())
                except ValueError:
                    self.mostrar_advertencia(
                        "Validación de turno mixto",
                        "Horas de mañana y tarde deben ser numéricas."
                    )
                    return

                if abs((horas_manana + horas_tarde) - horas) > 1e-6:
                    self.mostrar_advertencia(
                        "Validación de turno mixto",
                        "La suma de horas de mañana y tarde debe coincidir con las horas totales."
                    )
                    return

            # Validar email
            email_corporativo = self.email_input.text().strip() or None
            if email_corporativo:
                valido, error_msg = validar_email(email_corporativo)
                if not valido:
                    self.mostrar_advertencia("Validación de email", error_msg)
                    return

            # Obtener valores de fechas
            fecha_inicio_guardias = None
            fecha_fin_guardias = None

            if self.usar_fecha_inicio_checkbox.isChecked():
                if self.fecha_inicio_guardias_input.date().isValid():
                    fecha_inicio_guardias = self.fecha_inicio_guardias_input.date().toPyDate()
            elif self.usar_fecha_fin_checkbox.isChecked():
                if self.fecha_fin_guardias_input.date().isValid():
                    fecha_fin_guardias = self.fecha_fin_guardias_input.date().toPyDate()

            # Obtener restricciones de horario
            # Guardar la matriz completa como dict para que se serialice correctamente
            dias_permitidos = None
            recreos_dict = {}

            if self.usar_restricciones_horario_checkbox.isChecked():
                # Obtener la matriz como JSON y convertir a dict
                matriz_json = self._matriz_a_json()
                if matriz_json:
                    recreos_dict = json.loads(matriz_json)
                    # Convertir keys de str a int
                    recreos_dict = {int(k): v for k, v in recreos_dict.items()}
                # También extraer las listas para días_semana_permitidos
                dias_permitidos, _ = self._extraer_listas_desde_matriz()

            # Guardar profesor
            # NOTA: Actualizaremos directamente el modelo después para guardar el JSON
            if self.profesor_editando_id:
                # Modo edición
                dto = ActualizarProfesorDTO(
                    nombre_completo=nombre_completo,
                    email_corporativo=email_corporativo,
                    horas_contrato=horas,
                    turno=turno,
                    horas_manana=horas_manana,
                    horas_tarde=horas_tarde,
                    tutor=self.tutor_checkbox.isChecked(),
                    fecha_inicio_guardias=fecha_inicio_guardias,
                    fecha_fin_guardias=fecha_fin_guardias,
                    recreos_permitidos=None,  # Lo actualizaremos después
                    dias_semana_permitidos=dias_permitidos,
                )
                self.actualizar_use_case.execute(self.profesor_editando_id, dto)

                # Actualizar el campo recreos_permitidos manualmente con el JSON
                if recreos_dict:
                    from models.models import Profesor
                    profesor = self.session.query(Profesor).filter(
                        Profesor.id == self.profesor_editando_id
                    ).first()
                    if profesor:
                        profesor.recreos_permitidos = json.dumps(recreos_dict)
                        self.session.commit()
            else:
                # Modo creación
                dto = CrearProfesorDTO(
                    nombre_completo=nombre_completo,
                    email_corporativo=email_corporativo,
                    horas_contrato=horas,
                    turno=turno,
                    horas_manana=horas_manana,
                    horas_tarde=horas_tarde,
                    tutor=self.tutor_checkbox.isChecked(),
                    fecha_inicio_guardias=fecha_inicio_guardias,
                    fecha_fin_guardias=fecha_fin_guardias,
                    recreos_permitidos=None,  # Lo actualizaremos después
                    dias_semana_permitidos=dias_permitidos,
                )
                profesor_creado = self.crear_use_case.execute(dto)

                # Actualizar el campo recreos_permitidos manualmente con el JSON
                if recreos_dict and profesor_creado:
                    from models.models import Profesor
                    profesor = self.session.query(Profesor).filter(
                        Profesor.id == profesor_creado.id
                    ).first()
                    if profesor:
                        profesor.recreos_permitidos = json.dumps(recreos_dict)
                        self.session.commit()

            # Limpiar y recargar
            self._limpiar_formulario()
            self.cargar_profesores()

            # Emitir señal de modificación de datos
            self.datos_modificados.emit()

        except Exception as e:
            self.manejar_excepcion(e, "guardar profesor")

    def cargar_profesores(self):
        """Cargar tabla de profesores desde la base de datos."""
        try:
            from models.models import Profesor

            self.tabla_profesores.setSortingEnabled(False)
            self.tabla_profesores.setRowCount(0)

            # Ordenar por nombre completo (alfabéticamente)
            profesores = self.session.query(Profesor).order_by(
                Profesor.nombre_completo
            ).all()
            total_profesores = len(profesores)
            self.tabla_profesores.setRowCount(total_profesores)

            self.titulo_lista_profesores.setText(
                f"📋 PROFESORES REGISTRADOS ({total_profesores})"
            )

            for i, prof in enumerate(profesores):
                # Nombre (con ID oculto)
                nombre_item = QTableWidgetItem(prof.nombre_completo or "")
                nombre_item.setData(Qt.ItemDataRole.UserRole, prof.id)
                self.tabla_profesores.setItem(i, 0, nombre_item)

                # Email
                self.tabla_profesores.setItem(
                    i, 1, QTableWidgetItem(prof.email_corporativo or "-")
                )

                # Horas
                self.tabla_profesores.setItem(
                    i, 2, QTableWidgetItem(f"{prof.horas_contrato:.1f}h")
                )

                # Turno
                self.tabla_profesores.setItem(
                    i, 3, QTableWidgetItem(prof.turno.capitalize())
                )

                # Tutor
                tutor_text = "Sí" if prof.tutor else "No"
                self.tabla_profesores.setItem(i, 4, QTableWidgetItem(tutor_text))

            # Habilitar ordenación manual (el usuario puede hacer clic en las columnas)
            self.tabla_profesores.setSortingEnabled(True)

            # Ordenar por columna de nombre (columna 0) ascendentemente
            self.tabla_profesores.sortItems(0, Qt.SortOrder.AscendingOrder)

        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def filtrar_profesores(self):
        """Filtrar profesores en la tabla según búsqueda."""
        texto_busqueda = self.busqueda_input.text().lower().strip()

        if not texto_busqueda:
            for i in range(self.tabla_profesores.rowCount()):
                self.tabla_profesores.setRowHidden(i, False)
            return

        for i in range(self.tabla_profesores.rowCount()):
            nombre_item = self.tabla_profesores.item(i, 0)
            email_item = self.tabla_profesores.item(i, 1)

            nombre = nombre_item.text().lower() if nombre_item else ""
            email = email_item.text().lower() if email_item else ""

            coincide = texto_busqueda in nombre or texto_busqueda in email
            self.tabla_profesores.setRowHidden(i, not coincide)

    def limpiar_busqueda(self):
        """Limpiar campo de búsqueda."""
        self.busqueda_input.clear()

    def editar_profesor(self):
        """Cargar profesor seleccionado en formulario para edición."""
        fila_actual = self.tabla_profesores.currentRow()
        if fila_actual < 0:
            self.mostrar_advertencia(
                "Selección requerida",
                "Selecciona un profesor para editar."
            )
            return

        id_item = self.tabla_profesores.item(fila_actual, 0)
        if not id_item:
            return

        id_profesor = id_item.data(Qt.ItemDataRole.UserRole)

        try:
            from models.models import Profesor

            profesor = self.session.query(Profesor).filter(
                Profesor.id == id_profesor
            ).first()
            if not profesor:
                self.mostrar_advertencia(
                    "Error de edición",
                    "Profesor no encontrado."
                )
                return

            # Cargar datos básicos
            self.nombre_completo_input.setText(profesor.nombre_completo or "")
            self.email_input.setText(profesor.email_corporativo or "")
            self.horas_input.setText(str(profesor.horas_contrato))

            # Seleccionar turno
            index = self.turno_input.findText(profesor.turno.capitalize())
            if index >= 0:
                self.turno_input.setCurrentIndex(index)

            # Cargar horas mixto
            if profesor.turno == "mixto":
                if profesor.horas_manana is not None:
                    self.horas_manana_input.setText(str(profesor.horas_manana))
                if profesor.horas_tarde is not None:
                    self.horas_tarde_input.setText(str(profesor.horas_tarde))

            # Tutor
            self.tutor_checkbox.setChecked(profesor.tutor or False)

            # Resetear fechas
            self.usar_fecha_inicio_checkbox.setChecked(False)
            self.usar_fecha_fin_checkbox.setChecked(False)
            self.fecha_inicio_guardias_input.setEnabled(False)
            self.fecha_fin_guardias_input.setEnabled(False)

            # Cargar fecha inicio
            if profesor.fecha_inicio_guardias:
                self.usar_fecha_inicio_checkbox.setChecked(True)
                self.fecha_inicio_guardias_input.setEnabled(True)
                self.fecha_inicio_guardias_input.setDate(
                    QDate(
                        profesor.fecha_inicio_guardias.year,
                        profesor.fecha_inicio_guardias.month,
                        profesor.fecha_inicio_guardias.day,
                    )
                )
            # Cargar fecha fin
            elif profesor.fecha_fin_guardias:
                self.usar_fecha_fin_checkbox.setChecked(True)
                self.fecha_fin_guardias_input.setEnabled(True)
                self.fecha_fin_guardias_input.setDate(
                    QDate(
                        profesor.fecha_fin_guardias.year,
                        profesor.fecha_fin_guardias.month,
                        profesor.fecha_fin_guardias.day,
                    )
                )

            # Cargar matriz horario
            if profesor.recreos_permitidos:
                self.usar_restricciones_horario_checkbox.setChecked(True)
                self._json_a_matriz(profesor.recreos_permitidos)
            else:
                self.usar_restricciones_horario_checkbox.setChecked(False)
                self._marcar_todos_matriz(False)

            # Activar modo edición
            self.profesor_editando_id = id_profesor
            self.titulo_seccion.setText(f"✏️ EDITAR PROFESOR [ID: {id_profesor}]")
            self.submit_btn.setText("💾 Actualizar Profesor")
            self.cancelar_btn.setVisible(True)

        except Exception as e:
            self.manejar_excepcion(e, "editar profesor")

    def eliminar_profesor(self):
        """Eliminar profesor(es) seleccionado(s)."""
        filas_seleccionadas = self.tabla_profesores.selectionModel().selectedRows()
        
        if not filas_seleccionadas:
            self.mostrar_advertencia(
                "Selección requerida",
                "Selecciona uno o más profesores para eliminar.\n\n"
                "💡 Usa Ctrl+clic para seleccionar múltiples profesores\n"
                "💡 Usa Shift+clic para seleccionar un rango"
            )
            return

        # Recopilar información de los profesores seleccionados
        profesores_a_eliminar = []
        for index in filas_seleccionadas:
            fila = index.row()
            nombre_item = self.tabla_profesores.item(fila, 0)
            if nombre_item:
                id_profesor = nombre_item.data(Qt.ItemDataRole.UserRole)
                nombre_profesor = nombre_item.text()
                profesores_a_eliminar.append((id_profesor, nombre_profesor))

        if not profesores_a_eliminar:
            return

        # Confirmar eliminación
        if len(profesores_a_eliminar) == 1:
            mensaje = f"¿Eliminar al profesor '{profesores_a_eliminar[0][1]}'?"
        else:
            nombres = "\n• ".join([nombre for _, nombre in profesores_a_eliminar])
            mensaje = (
                f"¿Eliminar {len(profesores_a_eliminar)} profesores?\n\n"
                f"• {nombres}"
            )

        respuesta = self.mostrar_pregunta(
            "Confirmar eliminación",
            mensaje
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                eliminados = 0
                errores = []
                
                for id_profesor, nombre_profesor in profesores_a_eliminar:
                    try:
                        self.eliminar_use_case.execute(id_profesor)
                        eliminados += 1
                    except Exception as e:
                        errores.append(f"{nombre_profesor}: {str(e)}")
                
                # Mostrar resultado
                if eliminados > 0:
                    if errores:
                        self.mostrar_advertencia(
                            "Eliminación parcial",
                            f"Se eliminaron {eliminados} profesor(es).\n\n"
                            f"Errores:\n• " + "\n• ".join(errores)
                        )
                    else:
                        self.mostrar_exito(
                            "Profesores eliminados",
                            f"Se eliminaron {eliminados} profesor(es) correctamente."
                        )
                    
                    self.cargar_profesores()
                    # Emitir señal de modificación de datos
                    self.datos_modificados.emit()
                else:
                    self.mostrar_error(
                        "Error",
                        "No se pudo eliminar ningún profesor:\n• " + "\n• ".join(errores)
                    )
                    
            except Exception as e:
                self.manejar_excepcion(e, "eliminar profesores")

