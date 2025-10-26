"""
Formulario de gestión de zonas de recreo.

Permite realizar operaciones CRUD sobre las zonas usando patrón MVP.
"""

from pydantic import ValidationError
from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

import ui_styles as styles
from application.dtos.zona_dto import ActualizarZonaDTO, CrearZonaDTO
from application.use_cases.zona import (
    ActualizarZonaUseCase,
    CrearZonaUseCase,
    EliminarZonaUseCase,
    ListarZonasUseCase,
)
from presentation.forms.base_form import BaseForm
from utils.exceptions import BusinessLogicError, NotFoundError


class ZonaForm(BaseForm):
    """
    Formulario para gestionar zonas de recreo.

    Permite crear, listar y eliminar zonas siguiendo el patrón MVP.
    """

    # Señal que se emite cuando se modifican los datos de zonas
    datos_modificados = pyqtSignal()

    def __init__(self, session: Session):
        """
        Inicializar el formulario de zonas.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        super().__init__(session)

        # Inicializar Use Cases
        self.crear_zona_uc = CrearZonaUseCase(session)
        self.actualizar_zona_uc = ActualizarZonaUseCase(session)
        self.listar_zonas_uc = ListarZonasUseCase(session)
        self.eliminar_zona_uc = EliminarZonaUseCase(session)

        # Control de modo edición
        self.zona_editando_id = None

        self.setWindowTitle("Gestión de Zonas")
        self.setup_ui()
        self._setup_shortcuts()
        self.cargar_zonas()

    def _setup_shortcuts(self):
        """Configurar atajos de teclado"""
        QShortcut(QKeySequence("Del"), self).activated.connect(self.eliminar_zona)
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(self.seleccionar_todas)

    def seleccionar_todas(self):
        """Seleccionar todas las zonas de la tabla."""
        if self.tabla_zonas.rowCount() > 0:
            self.tabla_zonas.selectAll()

    def setup_ui(self):
        """Configurar la interfaz de usuario del formulario"""
        # Layout principal vertical
        main_layout = QVBoxLayout()

        # Crear splitter horizontal para permitir redimensionamiento
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Widget izquierdo: Lista de zonas
        left_widget = self._crear_widget_lista()

        # Widget derecho: Formulario de alta
        right_widget = self._crear_widget_formulario()

        # Agregar widgets al splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Configurar proporciones del splitter (60% lista, 40% formulario)
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        # Agregar splitter al layout principal
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def _crear_widget_lista(self) -> QWidget:
        """
        Crear el widget de la sección de lista de zonas.

        Returns:
            Widget contenedor con la lista y botones de gestión
        """
        widget = QWidget()
        layout = self._crear_seccion_lista()
        widget.setLayout(layout)
        return widget

    def _crear_widget_formulario(self) -> QWidget:
        """
        Crear el widget de la sección de formulario.

        Returns:
            Widget contenedor con el formulario de alta
        """
        widget = QWidget()
        layout = self._crear_seccion_formulario()
        widget.setLayout(layout)
        return widget

    def _crear_seccion_lista(self) -> QVBoxLayout:
        """
        Crear la sección de lista de zonas.

        Returns:
            Layout con la lista y botones de gestión
        """
        left_section = QVBoxLayout()
        left_section.setContentsMargins(10, 0, 10, 10)
        left_section.setSpacing(10)

        # Título con contador
        self.titulo_lista_zonas = QLabel("🏫 ZONAS REGISTRADAS (0)")
        self.titulo_lista_zonas.setStyleSheet(styles.STYLE_TITLE_MAIN)
        left_section.addWidget(self.titulo_lista_zonas)

        # Tabla de zonas
        self.tabla_zonas = QTableWidget()
        self.tabla_zonas.setColumnCount(5)
        self.tabla_zonas.setHorizontalHeaderLabels([
            "ID", "Nombre", "Descripción", "Fecha Inicio", "Fecha Fin"
        ])

        # Ocultar columna ID
        self.tabla_zonas.setColumnHidden(0, True)

        # Configurar el ancho de las columnas
        self.tabla_zonas.horizontalHeader().setStretchLastSection(False)
        self.tabla_zonas.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents  # Nombre (ajustado al contenido)
        )
        self.tabla_zonas.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch  # Descripción (expandible)
        )
        self.tabla_zonas.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents  # Fecha Inicio
        )
        self.tabla_zonas.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.ResizeToContents  # Fecha Fin
        )

        self.tabla_zonas.setSortingEnabled(True)
        self.tabla_zonas.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        # Permitir selección múltiple (Ctrl+clic o Shift+clic)
        self.tabla_zonas.setSelectionMode(
            QTableWidget.SelectionMode.ExtendedSelection
        )
        self.tabla_zonas.doubleClicked.connect(self.editar_zona)
        left_section.addWidget(self.tabla_zonas)

        # Label informativo de multiselección
        from presentation.themes.ccleaner_theme import (
            CONTENT_BG_ALT,
            FONT_SIZE_SMALL,
            PRIMARY_BLUE,
            RADIUS_SMALL,
            SPACING_MD,
            SPACING_SM,
            TEXT_SECONDARY,
        )
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
        left_section.addWidget(info_label)

        # Botones de gestión
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_zonas)

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.editar_zona)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_zona)
        self.delete_btn.setToolTip(
            "Eliminar las zonas seleccionadas (Supr)\n\n"
            "💡 Ctrl+clic: selección múltiple individual\n"
            "💡 Shift+clic: selección de rango\n"
            "💡 Ctrl+A: seleccionar todas"
        )

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.editar_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        left_section.addLayout(btn_layout)

        return left_section

    def _crear_seccion_formulario(self) -> QVBoxLayout:
        """
        Crear la sección de formulario de alta.

        Returns:
            Layout con el formulario y botón de guardar
        """
        right_section = QVBoxLayout()
        right_section.setContentsMargins(10, 0, 10, 10)
        right_section.setSpacing(12)

        # Título del formulario
        self.titulo_form = QLabel("✏️ NUEVA ZONA")
        self.titulo_form.setStyleSheet(styles.STYLE_TITLE_MAIN)
        right_section.addWidget(self.titulo_form)

        # Grupo de datos
        grupo_datos = QGroupBox("📋 Datos de la Zona")
        grupo_datos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_datos = QVBoxLayout()
        layout_datos.setSpacing(8)

        # Campo: Nombre de la zona
        label_nombre = QLabel("Nombre de la zona:")
        label_nombre.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_nombre)

        self.nombre_zona_input = QLineEdit()
        self.nombre_zona_input.setPlaceholderText("Ej: Patio Principal, Porche, etc.")
        self.nombre_zona_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_zona_input.setMaximumWidth(350)
        layout_datos.addWidget(self.nombre_zona_input)

        # Campo: Descripción
        label_desc = QLabel("Descripción (opcional):")
        label_desc.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_desc)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Detalles adicionales sobre la zona")
        self.descripcion_input.setStyleSheet(styles.STYLE_INPUT)
        self.descripcion_input.setMaximumWidth(350)
        layout_datos.addWidget(self.descripcion_input)

        # Campo: Fecha de inicio (opcional)
        self.usar_fecha_inicio_check = QCheckBox("Especificar fecha de inicio")
        self.usar_fecha_inicio_check.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_fecha_inicio_check.toggled.connect(self._toggle_fecha_inicio)
        layout_datos.addWidget(self.usar_fecha_inicio_check)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_input.setMaximumWidth(200)
        self.fecha_inicio_input.setEnabled(False)
        layout_datos.addWidget(self.fecha_inicio_input)

        # Campo: Fecha de fin (opcional)
        self.usar_fecha_fin_check = QCheckBox("Especificar fecha de fin")
        self.usar_fecha_fin_check.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_fecha_fin_check.toggled.connect(self._toggle_fecha_fin)
        layout_datos.addWidget(self.usar_fecha_fin_check)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_input.setMaximumWidth(200)
        self.fecha_fin_input.setEnabled(False)
        layout_datos.addWidget(self.fecha_fin_input)

        grupo_datos.setLayout(layout_datos)
        right_section.addWidget(grupo_datos)

        # Botones de acción
        btn_action_layout = QHBoxLayout()
        btn_action_layout.setSpacing(8)

        self.submit_btn = QPushButton("💾 Guardar Zona")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_zona)
        btn_action_layout.addWidget(self.submit_btn)

        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        self.cancelar_btn.clicked.connect(self.cancelar_edicion)
        self.cancelar_btn.setVisible(False)  # Oculto por defecto
        btn_action_layout.addWidget(self.cancelar_btn)

        right_section.addLayout(btn_action_layout)

        # Espacio flexible
        right_section.addStretch()

        return right_section

    def _toggle_fecha_inicio(self, checked: bool):
        """Habilitar/deshabilitar campo de fecha de inicio"""
        self.fecha_inicio_input.setEnabled(checked)

    def _toggle_fecha_fin(self, checked: bool):
        """Habilitar/deshabilitar campo de fecha de fin"""
        self.fecha_fin_input.setEnabled(checked)

    def guardar_zona(self):
        """Guardar o actualizar una zona usando el Use Case correspondiente"""
        try:
            nombre = self.nombre_zona_input.text().strip()
            descripcion = self.descripcion_input.text().strip() or None

            # Obtener fechas opcionales
            fecha_inicio = None
            if self.usar_fecha_inicio_check.isChecked():
                fecha_inicio = self.fecha_inicio_input.date().toPyDate()

            fecha_fin = None
            if self.usar_fecha_fin_check.isChecked():
                fecha_fin = self.fecha_fin_input.date().toPyDate()

            if self.zona_editando_id is not None:
                # Modo actualización
                zona_dto = ActualizarZonaDTO(
                    nombre_zona=nombre,
                    descripcion=descripcion,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )

                # Ejecutar Use Case de actualización
                zona_actualizada = self.actualizar_zona_uc.execute(
                    self.zona_editando_id, zona_dto
                )

                # Mostrar mensaje de éxito
                self.mostrar_exito(
                    "Zona actualizada",
                    f"Zona '{zona_actualizada.nombre_zona}' actualizada correctamente."
                )

                # Salir del modo edición
                self.cancelar_edicion()

            else:
                # Modo creación
                zona_dto = CrearZonaDTO(
                    nombre_zona=nombre,
                    descripcion=descripcion,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )

                # Ejecutar Use Case de creación
                zona_creada = self.crear_zona_uc.execute(zona_dto)

                # Mostrar mensaje de éxito
                self.mostrar_exito(
                    "Zona guardada",
                    f"Zona '{zona_creada.nombre_zona}' guardada correctamente."
                )

                # Limpiar formulario
                self.limpiar_formulario()

            # Recargar lista
            self.cargar_zonas()

            # Emitir señal de modificación de datos
            self.datos_modificados.emit()

        except ValidationError as e:
            # Errores de validación de Pydantic
            errores = "; ".join([error["msg"] for error in e.errors()])
            self.mostrar_error("Datos inválidos", errores)

        except BusinessLogicError as e:
            # Errores de lógica de negocio (zona duplicada, etc.)
            self.mostrar_error("Error de lógica de negocio", str(e))

        except Exception as e:
            # Otros errores inesperados
            self.manejar_excepcion(e, "guardar la zona")

    def editar_zona(self):
        """Cargar zona seleccionada en formulario para edición."""
        fila_actual = self.tabla_zonas.currentRow()
        if fila_actual == -1:
            self.mostrar_advertencia(
                "Selección requerida",
                "Selecciona una zona para editar."
            )
            return

        # Obtener el ID de la primera columna
        item_id = self.tabla_zonas.item(fila_actual, 0)
        if not item_id:
            return

        id_zona = int(item_id.text())

        try:
            from models.models import Zona

            zona = self.session.query(Zona).filter(Zona.id == id_zona).first()
            if not zona:
                self.mostrar_advertencia(
                    "Error de edición",
                    "Zona no encontrada."
                )
                return

            # Cargar datos en el formulario
            self.nombre_zona_input.setText(zona.nombre_zona or "")
            self.descripcion_input.setText(zona.descripcion or "")

            # Cargar fechas si existen
            if zona.fecha_inicio:
                self.usar_fecha_inicio_check.setChecked(True)
                qdate_inicio = QDate(zona.fecha_inicio.year, zona.fecha_inicio.month, zona.fecha_inicio.day)
                self.fecha_inicio_input.setDate(qdate_inicio)
            else:
                self.usar_fecha_inicio_check.setChecked(False)

            if zona.fecha_fin:
                self.usar_fecha_fin_check.setChecked(True)
                qdate_fin = QDate(zona.fecha_fin.year, zona.fecha_fin.month, zona.fecha_fin.day)
                self.fecha_fin_input.setDate(qdate_fin)
            else:
                self.usar_fecha_fin_check.setChecked(False)

            # Activar modo edición
            self.zona_editando_id = id_zona
            self.titulo_form.setText(f"✏️ EDITAR ZONA [ID: {id_zona}]")
            self.submit_btn.setText("💾 Actualizar Zona")
            self.cancelar_btn.setVisible(True)

        except Exception as e:
            self.manejar_excepcion(e, "editar zona")

    def cancelar_edicion(self):
        """Cancelar el modo edición y volver al modo creación."""
        self.zona_editando_id = None
        self.titulo_form.setText("✏️ NUEVA ZONA")
        self.submit_btn.setText("💾 Guardar Zona")
        self.cancelar_btn.setVisible(False)
        self.limpiar_formulario()

    def cargar_zonas(self):
        """Cargar la lista de zonas desde la base de datos usando el Use Case"""
        try:
            # Ejecutar Use Case (ya viene ordenado por nombre_zona)
            zonas = self.listar_zonas_uc.execute()

            # Limpiar tabla actual
            self.tabla_zonas.setRowCount(0)

            # Actualizar contador en el título
            total_zonas = len(zonas)
            self.titulo_lista_zonas.setText(f"🏫 ZONAS REGISTRADAS ({total_zonas})")

            # Agregar zonas a la tabla
            for row, zona in enumerate(zonas):
                self.tabla_zonas.insertRow(row)

                # ID
                item_id = QTableWidgetItem(str(zona.id))
                item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_zonas.setItem(row, 0, item_id)

                # Nombre
                item_nombre = QTableWidgetItem(zona.nombre_zona)
                self.tabla_zonas.setItem(row, 1, item_nombre)

                # Descripción
                desc = zona.descripcion if zona.descripcion else "Sin descripción"
                item_desc = QTableWidgetItem(desc)
                self.tabla_zonas.setItem(row, 2, item_desc)

                # Fecha Inicio
                if zona.fecha_inicio:
                    fecha_inicio_texto = zona.fecha_inicio.strftime('%d/%m/%Y')
                else:
                    fecha_inicio_texto = "-"
                item_fecha_inicio = QTableWidgetItem(fecha_inicio_texto)
                item_fecha_inicio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_zonas.setItem(row, 3, item_fecha_inicio)

                # Fecha Fin
                if zona.fecha_fin:
                    fecha_fin_texto = zona.fecha_fin.strftime('%d/%m/%Y')
                else:
                    fecha_fin_texto = "-"
                item_fecha_fin = QTableWidgetItem(fecha_fin_texto)
                item_fecha_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_zonas.setItem(row, 4, item_fecha_fin)

        except Exception as e:
            self.manejar_excepcion(e, "cargar las zonas")

    def eliminar_zona(self):
        """Eliminar las zonas seleccionadas usando el Use Case"""
        # Obtener filas seleccionadas
        filas_seleccionadas = self.tabla_zonas.selectionModel().selectedRows()

        if not filas_seleccionadas:
            self.mostrar_advertencia(
                "Selección requerida",
                "Selecciona una o más zonas para eliminar.\n\n"
                "💡 Usa Ctrl+clic para seleccionar varias zonas individuales\n"
                "💡 Usa Shift+clic para seleccionar un rango\n"
                "💡 Usa Ctrl+A para seleccionar todas"
            )
            return

        # Recopilar información de las zonas a eliminar
        zonas_a_eliminar = []
        for index in filas_seleccionadas:
            fila = index.row()
            item_id = self.tabla_zonas.item(fila, 0)
            item_nombre = self.tabla_zonas.item(fila, 1)

            if item_id:
                id_zona = int(item_id.text())
                nombre_zona = item_nombre.text() if item_nombre else f"ID {id_zona}"
                zonas_a_eliminar.append((id_zona, nombre_zona))

        if not zonas_a_eliminar:
            return

        # Preparar mensaje de confirmación
        cantidad = len(zonas_a_eliminar)
        if cantidad == 1:
            mensaje = f"¿Eliminar la zona '{zonas_a_eliminar[0][1]}'?"
        else:
            nombres = "\n• ".join([nombre for _, nombre in zonas_a_eliminar])
            mensaje = f"¿Eliminar {cantidad} zonas?\n\n• {nombres}"

        # Confirmar eliminación
        if not self.confirmar_accion("Confirmar eliminación", mensaje):
            return

        # Eliminar zonas
        eliminadas = 0
        errores = []

        for id_zona, nombre_zona in zonas_a_eliminar:
            try:
                self.eliminar_zona_uc.execute(id_zona)
                eliminadas += 1
            except NotFoundError as e:
                errores.append(f"{nombre_zona}: {str(e)}")
            except BusinessLogicError as e:
                errores.append(f"{nombre_zona}: {str(e)}")
            except Exception as e:
                errores.append(f"{nombre_zona}: Error inesperado - {str(e)}")

        # Recargar lista
        self.cargar_zonas()

        # Emitir señal de modificación de datos
        if eliminadas > 0:
            self.datos_modificados.emit()

        # Mostrar resultado
        if eliminadas > 0 and not errores:
            mensaje_exito = f"Se {'eliminó' if eliminadas == 1 else 'eliminaron'} {eliminadas} zona(s) correctamente."
            self.mostrar_exito("Zonas eliminadas", mensaje_exito)
        elif eliminadas > 0 and errores:
            mensaje_parcial = f"Se eliminaron {eliminadas} zona(s).\n\nErrores en {len(errores)} zona(s):\n" + "\n".join(errores)
            self.mostrar_advertencia("Eliminación parcial", mensaje_parcial)
        else:
            mensaje_error = "No se pudo eliminar ninguna zona:\n\n" + "\n".join(errores)
            self.mostrar_error("Error al eliminar", mensaje_error)

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.nombre_zona_input.clear()
        self.descripcion_input.clear()
        self.usar_fecha_inicio_check.setChecked(False)
        self.usar_fecha_fin_check.setChecked(False)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setDate(QDate.currentDate())

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, Pydantic lo hace en el DTO).

        Returns:
            True siempre, la validación real ocurre en CrearZonaDTO
        """
        return True
