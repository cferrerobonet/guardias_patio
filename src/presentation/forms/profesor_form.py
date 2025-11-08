"""
Formulario de gestión de profesores.

Este módulo implementa la UI para crear, editar, eliminar y buscar profesores.
Incluye una tabla con búsqueda y un formulario detallado con validaciones.
"""

import json
from typing import Optional

import ui_styles as styles
from application.dtos.profesor_dto import ActualizarProfesorDTO, CrearProfesorDTO
from application.use_cases.profesor import (
    ActualizarProfesorUseCase,
    BuscarProfesoresUseCase,
    CrearProfesorUseCase,
    EliminarProfesorUseCase,
    ListarProfesoresUseCase,
    ObtenerProfesorUseCase,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from presentation.forms.base_form import BaseForm
from presentation.forms.profesor_widgets import (
    DatosBasicosWidget,
    HorarioWidget,
    RestriccionesWidget,
)
from presentation.themes.ccleaner_theme import (
    CONTENT_BG_ALT,
    FONT_SIZE_SMALL,
    PRIMARY_BLUE,
    RADIUS_SMALL,
    SPACING_MD,
    SPACING_SM,
    TEXT_SECONDARY,
)
from presentation.widgets import TableManager


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
        self.obtener_use_case = ObtenerProfesorUseCase(session)

        # Configurar atajos
        self._configurar_atajos()

        # Construir UI
        self.setup_ui()

        # Inicializar gestor de tabla para mejorar UX
        self.table_manager = None  # Se inicializará después de crear la tabla

        # Cargar datos iniciales
        self.cargar_profesores()
        self.cargar_zonas()

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

        # Establecer proporciones iniciales: 70% tabla, 30% formulario
        # (más espacio para la tabla para no comprimir información)
        splitter.setStretchFactor(0, 70)
        splitter.setStretchFactor(1, 30)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _crear_widget_tabla(self) -> QWidget:
        """Crear widget contenedor para la sección de tabla."""
        widget = QWidget()
        layout = self._crear_seccion_tabla()
        widget.setLayout(layout)
        return widget

    def _crear_widget_formulario_con_scroll(self) -> QWidget:
        """Crear widget para el formulario (sin scroll, optimizado horizontalmente)."""
        # Crear contenedor del formulario sin ScrollArea
        form_container = QWidget()
        form_layout = self._crear_seccion_formulario()
        form_container.setLayout(form_layout)

        return form_container

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
        self.tabla_profesores.setColumnCount(7)
        self.tabla_profesores.setHorizontalHeaderLabels(
            [
                "Nombre Completo",
                "Email",
                "Horas",
                "Turno",
                "Tutor",
                "Inicio Guardias",
                "Fin Guardias",
            ]
        )
        self.tabla_profesores.horizontalHeader().setStretchLastSection(False)
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        for i in [1, 2, 3, 4, 5, 6]:
            self.tabla_profesores.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        self.tabla_profesores.setSortingEnabled(True)
        self.tabla_profesores.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # Permitir selección múltiple (Ctrl+clic o Shift+clic)
        self.tabla_profesores.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        # Doble click: activar modo edición
        self.tabla_profesores.doubleClicked.connect(self.editar_profesor)

        # Hacer la tabla de solo lectura (no editable directamente)
        self.tabla_profesores.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.tabla_profesores)

        # Label informativo de multiselección
        info_label = QLabel(
            "💡 <b>Selección múltiple:</b> Ctrl+clic (individual) | "
            "Shift+clic (rango) | Ctrl+A (todos) | Supr (eliminar)"
        )
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

        # Inicializar TableManager para mejorar UX
        self.table_manager = TableManager(
            table=self.tabla_profesores, edit_btn=self.editar_btn, delete_btn=self.delete_btn
        )

        return layout

    def _crear_seccion_formulario(self) -> QVBoxLayout:
        """Crear sección derecha con formulario de alta/edición optimizado sin scroll."""
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)  # Márgenes mínimos
        layout.setSpacing(4)  # Espaciado mínimo entre elementos

        # Título más compacto
        self.titulo_seccion = QLabel("✏️ ALTA DE PROFESOR")
        self.titulo_seccion.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(self.titulo_seccion)

        # Widgets del formulario (layout vertical simple para no comprimir tabla)
        self.datos_basicos_widget = DatosBasicosWidget(self)
        layout.addWidget(self.datos_basicos_widget)

        self.horario_widget = HorarioWidget(self)
        layout.addWidget(self.horario_widget)

        self.restricciones_widget = RestriccionesWidget(self)
        layout.addWidget(self.restricciones_widget)

        # Conectar señal de cambio de turno para actualizar matriz de restricciones
        self.horario_widget.turno_changed.connect(self._actualizar_matriz_restricciones_por_turno)

        # Botones de acción más compactos
        botones_accion = QHBoxLayout()
        botones_accion.setSpacing(6)

        self.submit_btn = QPushButton("💾 Guardar")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_profesor)
        self.submit_btn.setMaximumHeight(32)  # Altura reducida

        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.cancelar_btn.clicked.connect(self.cancelar_edicion)
        self.cancelar_btn.setVisible(False)
        self.cancelar_btn.setMaximumHeight(32)  # Altura reducida

        botones_accion.addWidget(self.submit_btn)
        botones_accion.addWidget(self.cancelar_btn)
        layout.addLayout(botones_accion)

        layout.addStretch()  # Push todo hacia arriba

        return layout

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

    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario y preseleccionar matriz según turno."""
        # Delegar limpieza a los widgets
        self.datos_basicos_widget.limpiar()
        self.horario_widget.limpiar()
        self.restricciones_widget.limpiar()

        # Preseleccionar matriz de restricciones según el turno por defecto (Mañana)
        turno_por_defecto = self.horario_widget.get_turno()
        if turno_por_defecto:
            self.restricciones_widget.preseleccionar_segun_turno(turno_por_defecto)

        # Actualizar estado del formulario
        self.profesor_editando_id = None
        self.titulo_seccion.setText("✏️ ALTA DE PROFESOR")
        self.submit_btn.setText("💾 Guardar nuevo profesor")
        self.cancelar_btn.setVisible(False)

        # Re-habilitar interacción con la tabla después de cancelar/guardar
        self.tabla_profesores.setEnabled(True)
        self.editar_btn.setEnabled(True)
        self.delete_btn.setEnabled(True)
        self.busqueda_input.setEnabled(True)

    def cancelar_edicion(self):
        """Cancelar edición y volver a modo creación (sin recargar tabla)."""
        self._limpiar_formulario()
        # NO recargar tabla - es más rápido y no se han guardado cambios
        # self.cargar_profesores()  # ELIMINADO - innecesario

    def guardar_profesor(self):
        """Crear o actualizar profesor según el modo actual."""
        try:
            # Validar widgets
            valido_basicos, error_basicos = self.datos_basicos_widget.validar()
            if not valido_basicos:
                self.mostrar_advertencia("Validación", error_basicos)
                return

            valido_horario, error_horario = self.horario_widget.validar()
            if not valido_horario:
                self.mostrar_advertencia("Validación", error_horario)
                return

            valido_restricciones, error_restricciones = self.restricciones_widget.validar()
            if not valido_restricciones:
                self.mostrar_advertencia("Validación", error_restricciones)
                return

            # Obtener datos de los widgets
            datos_basicos = self.datos_basicos_widget.get_datos()
            datos_horario = self.horario_widget.get_datos()
            datos_restricciones = self.restricciones_widget.get_datos()

            # ✅ Obtener restricciones de horario (matriz de recreos)
            matriz_json = datos_restricciones.get("recreos_permitidos", "")
            recreos_dict = {}

            if matriz_json:
                # Hay restricciones personalizadas (checkbox activado)
                try:
                    recreos_dict = json.loads(matriz_json)
                    # Convertir claves a int si es necesario
                    recreos_dict = {int(k): v for k, v in recreos_dict.items()}
                except (json.JSONDecodeError, ValueError):
                    pass
            else:
                # ✅ NO hay restricciones personalizadas (checkbox desactivado)
                # GUARDAR configuración por defecto según turno
                turno = datos_horario["turno"]
                recreos_dict = self.restricciones_widget._obtener_recreos_por_defecto(turno)

            # Guardar profesor
            if self.profesor_editando_id:
                # Modo edición
                dto = ActualizarProfesorDTO(
                    nombre_completo=datos_basicos["nombre_completo"],
                    email_corporativo=datos_basicos["email"] or None,
                    horas_contrato=datos_horario["horas_contrato"],
                    turno=datos_horario["turno"],
                    horas_manana=datos_horario.get("horas_manana"),
                    horas_tarde=datos_horario.get("horas_tarde"),
                    tutor=datos_basicos["es_tutor"],
                    fecha_inicio_guardias=datos_restricciones.get("fecha_inicio"),
                    fecha_fin_guardias=datos_restricciones.get("fecha_fin"),
                    zona_preferida_id=datos_restricciones.get("zona_preferida_id"),
                    # Pasar la matriz completa
                    recreos_permitidos=recreos_dict if recreos_dict else {},
                    dias_semana_permitidos=datos_restricciones.get("dias_permitidos"),
                )
                self.actualizar_use_case.execute(self.profesor_editando_id, dto)
            else:
                # Modo creación
                dto = CrearProfesorDTO(
                    nombre_completo=datos_basicos["nombre_completo"],
                    email_corporativo=datos_basicos["email"] or None,
                    horas_contrato=datos_horario["horas_contrato"],
                    turno=datos_horario["turno"],
                    horas_manana=datos_horario.get("horas_manana"),
                    horas_tarde=datos_horario.get("horas_tarde"),
                    tutor=datos_basicos["es_tutor"],
                    fecha_inicio_guardias=datos_restricciones.get("fecha_inicio"),
                    fecha_fin_guardias=datos_restricciones.get("fecha_fin"),
                    zona_preferida_id=datos_restricciones.get("zona_preferida_id"),
                    recreos_permitidos=recreos_dict if recreos_dict else {},  # Pasar matriz
                    dias_semana_permitidos=datos_restricciones.get("dias_permitidos"),
                )
                profesor_creado = self.crear_use_case.execute(dto)

            # Guardar selección antes de recargar
            if self.table_manager:
                if self.profesor_editando_id:
                    # En modo edición, guardar el ID que estamos editando
                    self.table_manager._last_selected_id = self.profesor_editando_id
                else:
                    # En modo creación, guardar el ID del nuevo profesor si existe
                    if profesor_creado:
                        self.table_manager._last_selected_id = profesor_creado.id

            # Recargar tabla y emitir señal
            self.cargar_profesores()
            self.datos_modificados.emit()

            # Manejar modo edición
            if self.profesor_editando_id:
                self.profesor_editando_id = None
                self.titulo_seccion.setText("✏️ ALTA DE PROFESOR")
                self.submit_btn.setText("💾 Guardar nuevo profesor")
                self.cancelar_btn.setVisible(False)
                # ✅ Limpiar formulario después de actualizar para evitar confusión
                self._limpiar_formulario()
                if self.table_manager:
                    self.table_manager.enable_table_interactions(True)
                self.busqueda_input.setEnabled(True)

                # La selección se restaurará automáticamente en cargar_profesores()
                self.mostrar_exito(
                    "✅ Profesor actualizado",
                    "El profesor ha sido actualizado correctamente.\n\n"
                    "Los datos permanecen visibles en el formulario.",
                )
            else:
                self._limpiar_formulario()
                self.mostrar_exito(
                    "✅ Profesor creado", "El profesor ha sido creado correctamente."
                )

        except Exception as e:
            self.manejar_excepcion(e, "guardar profesor")

    def cargar_profesores(self):
        """Cargar tabla de profesores desde la base de datos."""
        try:
            from models.models import Profesor

            self.tabla_profesores.setSortingEnabled(False)
            self.tabla_profesores.setRowCount(0)

            # Ordenar por nombre completo (alfabéticamente)
            profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()
            total_profesores = len(profesores)
            self.tabla_profesores.setRowCount(total_profesores)

            self.titulo_lista_profesores.setText(f"📋 PROFESORES REGISTRADOS ({total_profesores})")

            for i, prof in enumerate(profesores):
                # Nombre (con ID oculto)
                nombre_item = QTableWidgetItem(prof.nombre_completo or "")
                nombre_item.setData(Qt.ItemDataRole.UserRole, prof.id)
                self.tabla_profesores.setItem(i, 0, nombre_item)

                # Email
                email_item = QTableWidgetItem(prof.email_corporativo or "-")
                self.tabla_profesores.setItem(i, 1, email_item)

                # Horas
                horas_item = QTableWidgetItem(f"{prof.horas_contrato:.1f}h")
                self.tabla_profesores.setItem(i, 2, horas_item)

                # Turno
                turno_item = QTableWidgetItem(prof.turno.capitalize())
                self.tabla_profesores.setItem(i, 3, turno_item)

                # Tutor
                tutor_text = "Sí" if prof.tutor else "No"
                tutor_item = QTableWidgetItem(tutor_text)
                self.tabla_profesores.setItem(i, 4, tutor_item)

                # Fecha Inicio Guardias
                fecha_inicio_text = (
                    prof.fecha_inicio_guardias.strftime("%d/%m/%Y")
                    if prof.fecha_inicio_guardias
                    else "-"
                )
                fecha_inicio_item = QTableWidgetItem(fecha_inicio_text)
                self.tabla_profesores.setItem(i, 5, fecha_inicio_item)

                # Fecha Fin Guardias
                fecha_fin_text = (
                    prof.fecha_fin_guardias.strftime("%d/%m/%Y") if prof.fecha_fin_guardias else "-"
                )
                fecha_fin_item = QTableWidgetItem(fecha_fin_text)
                self.tabla_profesores.setItem(i, 6, fecha_fin_item)

            # Habilitar ordenación manual (el usuario puede hacer clic en las columnas)
            self.tabla_profesores.setSortingEnabled(True)

            # Ordenar por columna de nombre (columna 0) ascendentemente
            self.tabla_profesores.sortItems(0, Qt.SortOrder.AscendingOrder)

            # Restaurar selección si existe
            if self.table_manager:
                self.table_manager.restore_selection()

        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def cargar_zonas(self):
        """Cargar zonas disponibles en el combo del widget de restricciones."""
        try:
            from models.models import Zona

            zonas = self.session.query(Zona).order_by(Zona.nombre_zona).all()
            zonas_list = [(z.id, z.nombre_zona) for z in zonas]
            self.restricciones_widget.cargar_zonas(zonas_list)

        except Exception as e:
            self.manejar_excepcion(e, "cargar zonas")

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

    def mostrar_profesor(self):
        """
        Mostrar datos del profesor seleccionado en modo lectura (sin editar).

        NOTA: Este método ya NO se llama desde click simple de la tabla.
        Solo se usa internamente en editar_profesor().
        """
        if self.profesor_editando_id is not None:
            return

        fila_actual = self.tabla_profesores.currentRow()
        if fila_actual < 0:
            return

        id_item = self.tabla_profesores.item(fila_actual, 0)
        if not id_item:
            return

        id_profesor = id_item.data(Qt.ItemDataRole.UserRole)

        try:
            # Usar Use Case para obtener el profesor
            profesor_dto = self.obtener_use_case.execute(id_profesor)

            # 🔧 OBTENER recreos_permitidos RAW desde la BD (sin procesar)
            # El DTO pierde la estructura por día al convertir dict a lista
            recreos_raw = None
            try:
                from models.models import Profesor

                profesor_model = self.session.query(Profesor).filter_by(id=id_profesor).first()
                if profesor_model and profesor_model.recreos_permitidos:
                    recreos_raw = profesor_model.recreos_permitidos  # String JSON original
            except Exception as e:
                print(f"Warning: No se pudo obtener recreos_permitidos raw: {e}")

            # Limpiar formulario
            self._limpiar_formulario()

            # Cargar datos en widgets desde el DTO
            self.datos_basicos_widget.set_datos(
                {
                    "nombre_completo": profesor_dto.nombre_completo or "",
                    "email": profesor_dto.email_corporativo or "",
                    "es_tutor": profesor_dto.tutor or False,
                }
            )

            self.horario_widget.set_datos(
                {
                    "horas_contrato": profesor_dto.horas_contrato,
                    "turno": profesor_dto.turno,
                    "horas_manana": profesor_dto.horas_manana,
                    "horas_tarde": profesor_dto.horas_tarde,
                }
            )

            self.restricciones_widget.set_datos(
                {
                    "fecha_inicio": profesor_dto.fecha_inicio_guardias,
                    "fecha_fin": profesor_dto.fecha_fin_guardias,
                    "zona_preferida_id": profesor_dto.zona_preferida_id,
                    # ✅ Pasar JSON raw en lugar del DTO procesado
                    "recreos_permitidos": recreos_raw,
                    "turno": profesor_dto.turno,
                }
            )

            # Actualizar título - modo lectura
            self.titulo_seccion.setText("📋 VISTA PREVIA")
            self.submit_btn.setText("💾 Guardar Cambios")
            self.cancelar_btn.setVisible(False)

        except Exception as e:
            self.manejar_excepcion(e, "cargar datos del profesor")

    def editar_profesor(self):
        """Cargar profesor seleccionado en formulario para edición."""
        try:
            fila_actual = self.tabla_profesores.currentRow()
            if fila_actual < 0:
                self.mostrar_advertencia(
                    "Selección requerida", "Selecciona un profesor para editar."
                )
                return

            id_item = self.tabla_profesores.item(fila_actual, 0)
            if not id_item:
                return

            id_profesor = id_item.data(Qt.ItemDataRole.UserRole)

            # Si no está en modo edición, primero mostrar los datos
            if self.profesor_editando_id is None:
                self.mostrar_profesor()

            # Ahora activar modo edición
            self.profesor_editando_id = id_profesor
            self.titulo_seccion.setText(f"✏️ EDITAR PROFESOR [ID: {id_profesor}]")
            self.submit_btn.setText("💾 Actualizar Profesor")
            self.cancelar_btn.setVisible(True)

            # Deshabilitar interacción con la tabla mientras se edita
            if self.table_manager:
                self.table_manager.enable_table_interactions(False)
            self.busqueda_input.setEnabled(False)

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
                "💡 Usa Shift+clic para seleccionar un rango",
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
            nombre_profesor = profesores_a_eliminar[0][1]
            mensaje = (
                f"¿Eliminar al profesor "
                f"<span style='color: #007ACC; font-style: italic;'>{nombre_profesor}</span>?"
            )
        else:
            nombres_html = "<br>• ".join(
                [
                    f"<span style='color: #007ACC; font-style: italic;'>{nombre}</span>"
                    for _, nombre in profesores_a_eliminar
                ]
            )
            mensaje = (
                f"¿Eliminar <b>{len(profesores_a_eliminar)}</b> profesores?<br><br>• {nombres_html}"
            )

        respuesta = self.mostrar_pregunta("Confirmar eliminación", mensaje)

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                eliminados = 0
                errores = []

                # Verificar si algún profesor eliminado está actualmente en edición
                ids_a_eliminar = [id_prof for id_prof, _ in profesores_a_eliminar]
                limpiar_form = self.profesor_editando_id in ids_a_eliminar

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
                            f"Errores:\n• " + "\n• ".join(errores),
                        )
                    else:
                        self.mostrar_exito(
                            "Profesores eliminados",
                            f"Se eliminaron {eliminados} profesor(es) correctamente.",
                        )

                    # Si el profesor eliminado estaba en edición, limpiar formulario
                    if limpiar_form:
                        self._limpiar_formulario()

                    self.cargar_profesores()
                    # Emitir señal de modificación de datos
                    self.datos_modificados.emit()
                else:
                    self.mostrar_error(
                        "Error", "No se pudo eliminar ningún profesor:\n• " + "\n• ".join(errores)
                    )

            except Exception as e:
                self.manejar_excepcion(e, "eliminar profesores")

    def _actualizar_matriz_restricciones_por_turno(self, turno: str):
        """
        Actualizar la matriz de restricciones según el turno seleccionado.

        Solo actualiza si NO hay restricciones personalizadas activas.
        """
        # Solo actualizar si el checkbox de restricciones NO está activado
        if not self.restricciones_widget.get_usar_restricciones():
            self.restricciones_widget.preseleccionar_segun_turno(turno)
