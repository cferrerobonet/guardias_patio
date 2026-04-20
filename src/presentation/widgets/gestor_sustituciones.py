"""
Gestión de sustituciones de guardias.

Permite registrar ausencias y reasignar guardias automáticamente.
"""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import TEXT_SECONDARY, get_table_style
from utils.icons import icon_for_button, icon_for_form
from core.observability import business_metrics


class GestorSustituciones(BaseForm):
    """Widget para gestionar sustituciones de guardias."""

    def __init__(self, session):
        """
        Inicializar gestor de sustituciones.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setWindowTitle("Gestión de Sustituciones")
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        # Título
        titulo = QLabel("GESTIÓN DE SUSTITUCIONES")
        titulo.setObjectName("titleMain")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Busca una guardia asignada a un profesor y reasígnala a otro profesor disponible"
        )
        descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descripcion.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            margin-bottom: 10px;
        """)
        layout_principal.addWidget(descripcion)

        # Layout en 2 columnas para las secciones principales
        layout_columnas = QHBoxLayout()
        layout_columnas.setSpacing(15)

        # Columna izquierda: Buscar guardia
        columna_izq = QVBoxLayout()
        columna_izq.addWidget(self._crear_seccion_buscar())
        columna_izq.addStretch()
        layout_columnas.addLayout(columna_izq, 1)

        # Columna derecha: Asignar sustituto
        columna_der = QVBoxLayout()
        columna_der.addWidget(self._crear_seccion_sustituir())
        columna_der.addStretch()
        layout_columnas.addLayout(columna_der, 1)

        layout_principal.addLayout(layout_columnas)

        # Tabla de guardias encontradas (ancho completo)
        tabla_group = QGroupBox("Guardias Encontradas")
        tabla_layout = QVBoxLayout()
        self.tabla_guardias = self._crear_tabla_guardias()
        tabla_layout.addWidget(self.tabla_guardias)
        tabla_group.setLayout(tabla_layout)
        layout_principal.addWidget(tabla_group)

        # Historial (ancho completo, colapsable)
        layout_principal.addWidget(self._crear_seccion_historial())

        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.cargar_profesores()

        # A11Y: Tab order
        QWidget.setTabOrder(self.combo_profesor_original, self.fecha_buscar)
        QWidget.setTabOrder(self.fecha_buscar, self.btn_buscar)
        QWidget.setTabOrder(self.btn_buscar, self.combo_profesor_sustituto)
        QWidget.setTabOrder(self.combo_profesor_sustituto, self.btn_buscar_disponibles)
        QWidget.setTabOrder(self.btn_buscar_disponibles, self.text_observaciones)
        QWidget.setTabOrder(self.text_observaciones, self.btn_confirmar_sustitucion)
        QWidget.setTabOrder(self.btn_confirmar_sustitucion, self.btn_cancelar)

    def _crear_seccion_buscar(self) -> QGroupBox:
        """Crear sección de búsqueda de guardia."""
        grupo_buscar = QGroupBox("1. Buscar Guardia")
        layout_buscar = QVBoxLayout()
        layout_buscar.setSpacing(12)
        layout_buscar.setContentsMargins(15, 20, 15, 15)

        # Fecha
        fecha_label = QLabel("Fecha de la guardia:")
        fecha_label.setObjectName("fieldLabel")
        layout_buscar.addWidget(fecha_label)

        self.fecha_buscar = QDateEdit()
        self.fecha_buscar.setDate(date.today())
        self.fecha_buscar.setCalendarPopup(True)
        self.fecha_buscar.setAccessibleName("Fecha de la guardia a sustituir")
        layout_buscar.addWidget(self.fecha_buscar)

        # Profesor
        profesor_label = QLabel("Profesor original:")
        profesor_label.setObjectName("fieldLabel")
        layout_buscar.addWidget(profesor_label)

        self.combo_profesor_original = QComboBox()
        self.combo_profesor_original.setAccessibleName("Profesor original de la guardia")
        layout_buscar.addWidget(self.combo_profesor_original)

        # Botón buscar
        self.btn_buscar = QPushButton("Buscar Guardias")
        self.btn_buscar.setIcon(icon_for_button("search"))
        self.btn_buscar.clicked.connect(self.buscar_guardias)
        self.btn_buscar.setMinimumHeight(40)
        self.btn_buscar.setAccessibleName("Botón buscar guardias del profesor")
        layout_buscar.addWidget(self.btn_buscar)

        grupo_buscar.setLayout(layout_buscar)
        return grupo_buscar

    def _crear_tabla_guardias(self) -> QTableWidget:
        """Crear tabla de guardias encontradas."""
        tabla = QTableWidget()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["ID", "Profesor", "Turno", "Recreo", "Zona"])
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet(get_table_style())

        # Configurar columnas para ajustarse al contenido
        header = tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Profesor
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Turno
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Recreo
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Zona

        tabla.setMinimumHeight(150)
        tabla.selectionModel().selectionChanged.connect(self.guardia_seleccionada_cambio)
        return tabla

    def _crear_seccion_sustituir(self) -> QGroupBox:
        """Crear sección de asignación de sustituto."""
        grupo_sustituir = QGroupBox("2. Asignar Sustituto")
        layout_sustituir = QVBoxLayout()
        layout_sustituir.setSpacing(12)
        layout_sustituir.setContentsMargins(15, 20, 15, 15)

        # Profesor sustituto
        sustituto_label = QLabel("Profesor sustituto:")
        sustituto_label.setObjectName("fieldLabel")
        layout_sustituir.addWidget(sustituto_label)

        self.combo_profesor_sustituto = QComboBox()
        self.combo_profesor_sustituto.setAccessibleName("Profesor sustituto")
        layout_sustituir.addWidget(self.combo_profesor_sustituto)

        # Botón ver disponibles
        self.btn_buscar_disponibles = QPushButton("Ver Profesores Disponibles")
        self.btn_buscar_disponibles.setIcon(icon_for_form("users"))
        self.btn_buscar_disponibles.clicked.connect(self.buscar_profesores_disponibles)
        self.btn_buscar_disponibles.setMinimumHeight(35)
        self.btn_buscar_disponibles.setObjectName("secondaryButton")
        self.btn_buscar_disponibles.setAccessibleName("Botón ver profesores disponibles")
        layout_sustituir.addWidget(self.btn_buscar_disponibles)

        # Observaciones
        obs_label = QLabel("Observaciones (opcional):")
        obs_label.setObjectName("fieldLabel")
        layout_sustituir.addWidget(obs_label)

        self.text_observaciones = QTextEdit()
        self.text_observaciones.setMaximumHeight(70)
        self.text_observaciones.setPlaceholderText("Añade observaciones sobre la sustitución...")
        self.text_observaciones.setAccessibleName("Observaciones sobre la sustitución")
        layout_sustituir.addWidget(self.text_observaciones)

        # Botones de acción
        botones_layout = self._crear_botones_accion()
        layout_sustituir.addLayout(botones_layout)

        grupo_sustituir.setLayout(layout_sustituir)
        return grupo_sustituir

    def _crear_botones_accion(self) -> QHBoxLayout:
        """Crear botones de acción."""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)
        botones_layout.setContentsMargins(0, 15, 0, 0)

        self.btn_confirmar_sustitucion = QPushButton("Confirmar Sustitución")
        self.btn_confirmar_sustitucion.setIcon(icon_for_button("check"))
        self.btn_confirmar_sustitucion.clicked.connect(self.confirmar_sustitucion)
        self.btn_confirmar_sustitucion.setMinimumHeight(45)
        self.btn_confirmar_sustitucion.setProperty("success", "true")
        self.btn_confirmar_sustitucion.setEnabled(False)
        self.btn_confirmar_sustitucion.setAccessibleName("Botón confirmar sustitución")
        botones_layout.addWidget(self.btn_confirmar_sustitucion, 2)

        self.btn_cancelar = QPushButton("Limpiar")
        self.btn_cancelar.setIcon(icon_for_button("close"))
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
        self.btn_cancelar.setMinimumHeight(45)
        self.btn_cancelar.setProperty("danger", "true")
        self.btn_cancelar.setAccessibleName("Botón limpiar formulario")
        botones_layout.addWidget(self.btn_cancelar, 1)

        return botones_layout

    def _crear_seccion_historial(self) -> QGroupBox:
        """Crear sección de historial."""
        grupo_historial = QGroupBox("Historial Reciente de Sustituciones")
        layout_historial = QVBoxLayout()
        layout_historial.setContentsMargins(15, 20, 15, 15)

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha", "Profesor Original", "Profesor Sustituto", "Turno/Recreo", "Zona"]
        )
        self.tabla_historial.setMaximumHeight(180)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.setStyleSheet(get_table_style())

        # Configurar columnas para ajustarse al contenido
        header_hist = self.tabla_historial.horizontalHeader()
        header_hist.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Fecha
        header_hist.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Prof. Original
        header_hist.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Prof. Sustituto
        header_hist.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Turno/Recreo
        header_hist.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Zona

        layout_historial.addWidget(self.tabla_historial)

        grupo_historial.setLayout(layout_historial)
        return grupo_historial

    def cargar_profesores(self):
        """Cargar la lista de profesores en los combos."""
        try:
            from application.app_services import AppServices
            profesores = sorted(
                AppServices(self.session).profesores.get_all(),
                key=lambda p: p.nombre_completo,
            )

            self.combo_profesor_original.clear()
            self.combo_profesor_sustituto.clear()

            self.combo_profesor_original.addItem("-- Todos --", None)

            for profesor in profesores:
                self.combo_profesor_original.addItem(profesor.nombre_completo, profesor.id)
                self.combo_profesor_sustituto.addItem(profesor.nombre_completo, profesor.id)

        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def buscar_guardias(self):
        """Buscar las guardias del profesor en la fecha seleccionada."""
        try:
            fecha = self.fecha_buscar.date().toPyDate()
            profesor_id = self.combo_profesor_original.currentData()

            # Consultar guardias
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            guardias_fecha = _svc.guardias.find_by_fecha(fecha)
            guardias = [
                g for g in guardias_fecha
                if profesor_id is None or g.profesor_id == profesor_id
            ]

            # Llenar tabla
            self.tabla_guardias.setRowCount(len(guardias))

            for i, guardia in enumerate(guardias):
                from application.app_services import AppServices
                _svc = AppServices(self.session)
                profesor = _svc.profesores.get_by_id(guardia.profesor_id)
                zona = _svc.zonas.get_by_id(guardia.zona_id)

                self.tabla_guardias.setItem(i, 0, QTableWidgetItem(str(guardia.id)))
                self.tabla_guardias.setItem(
                    i,
                    1,
                    QTableWidgetItem(f"{profesor.nombre_completo if profesor else 'N/A'}"),
                )
                self.tabla_guardias.setItem(i, 2, QTableWidgetItem(guardia.turno))
                self.tabla_guardias.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
                self.tabla_guardias.setItem(
                    i, 4, QTableWidgetItem(zona.nombre_zona if zona else "N/A")
                )

                # Guardar el objeto guardia en la fila
                self.tabla_guardias.item(i, 0).setData(Qt.ItemDataRole.UserRole, guardia)

            # Mensaje si no hay resultados
            if len(guardias) == 0:
                self.mostrar_informacion(
                    "Sin resultados",
                    f"No se encontraron guardias para la fecha {fecha.strftime('%d/%m/%Y')}",
                )

        except Exception as e:
            self.manejar_excepcion(e, "buscar guardias")

    def guardia_seleccionada_cambio(self):
        """Manejar el cambio de selección en la tabla de guardias."""
        self.btn_confirmar_sustitucion.setEnabled(len(self.tabla_guardias.selectedItems()) > 0)

    def buscar_profesores_disponibles(self):
        """Mostrar los profesores disponibles para el slot seleccionado."""
        if not self.tabla_guardias.selectedItems():
            self.mostrar_advertencia(
                "Selección Requerida",
                "Por favor, selecciona primero una guardia a sustituir.",
            )
            return

        try:
            fila = self.tabla_guardias.currentRow()
            guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)

            # Buscar profesores que NO tengan guardia ese día
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            guardias_ese_dia = _svc.guardias.find_by_fecha(guardia.fecha)
            profesores_ocupados = {g.profesor_id for g in guardias_ese_dia}

            todos_profesores = _svc.profesores.get_all()
            disponibles = [p for p in todos_profesores if p.id not in profesores_ocupados]

            if disponibles:
                mensaje = "Profesores disponibles (sin guardias ese día):\n\n"
                for profesor in disponibles[:10]:  # Mostrar máximo 10
                    mensaje += f"• {profesor.nombre_completo}\n"

                if len(disponibles) > 10:
                    mensaje += f"\n... y {len(disponibles) - 10} más"

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Profesores Disponibles")
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setText(mensaje)
                msg.exec()
            else:
                self.mostrar_advertencia(
                    "Sin Disponibles",
                    "No hay profesores disponibles ese día (todos tienen al menos 1 guardia).",
                )

        except Exception as e:
            self.manejar_excepcion(e, "buscar profesores disponibles")

    def confirmar_sustitucion(self):
        """Confirmar la sustitución de guardia."""
        if not self.tabla_guardias.selectedItems():
            return

        try:
            fila = self.tabla_guardias.currentRow()
            guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)
            nuevo_profesor_id = self.combo_profesor_sustituto.currentData()

            if nuevo_profesor_id is None:
                self.mostrar_advertencia(
                    "Profesor Requerido", "Por favor, selecciona un profesor sustituto."
                )
                return

            # Verificar que el sustituto no tenga guardia ese día
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            tiene_guardia = _svc.guardias.contar_guardias_profesor_en_fecha(
                nuevo_profesor_id, guardia.fecha
            ) > 0

            if tiene_guardia:
                self.mostrar_advertencia(
                    "Profesor Ocupado",
                    "El profesor seleccionado ya tiene una guardia ese día.\n"
                    "Recuerda: máximo 1 guardia por día por profesor.",
                )
                return

            # Confirmar con el usuario
            from application.app_services import AppServices
            _svc2 = AppServices(self.session)
            profesor_original = _svc2.profesores.get_by_id(guardia.profesor_id)
            profesor_nuevo = _svc2.profesores.get_by_id(nuevo_profesor_id)

            respuesta = QMessageBox.question(
                self,
                "Confirmar Sustitución",
                f"¿Confirmas la sustitución?\n\n"
                f"Profesor Original: {profesor_original.nombre_completo}\n"
                f"Profesor Sustituto: {profesor_nuevo.nombre_completo}\n"
                f"Fecha: {guardia.fecha}\n"
                f"Turno: {guardia.turno} - Recreo {guardia.recreo}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Realizar sustitución a través del repositorio (sin query directa a ORM)
                from application.app_services import AppServices
                _svc_sust = AppServices(self.session)
                guardia_entity = _svc_sust.guardias.get_by_id(guardia.id)
                if guardia_entity:
                    guardia_entity.marcar_como_sustitucion(guardia.profesor_id)
                    guardia_entity.profesor_id = nuevo_profesor_id
                    notas_texto = self.text_observaciones.toPlainText().strip()
                    if notas_texto:
                        guardia_entity.notas = notas_texto
                    _svc_sust.guardias.save(guardia_entity)
                    self.session.commit()
                    business_metrics.sustitucion_confirmada(
                        guardia_id=guardia.id,
                        profesor_original_id=guardia.profesor_id,
                        profesor_sustituto_id=nuevo_profesor_id,
                        fecha=guardia.fecha,
                    )

                self.mostrar_exito(
                    "Sustitución Completada",
                    "La guardia ha sido reasignada exitosamente.",
                )

                # Limpiar y refrescar
                self.limpiar_formulario()
                self.buscar_guardias()

        except Exception as e:
            self.manejar_excepcion(e, "confirmar sustitución")

    def limpiar_formulario(self):
        """Limpiar el formulario de sustitución."""
        self.tabla_guardias.clearSelection()
        self.combo_profesor_sustituto.setCurrentIndex(0)
        self.text_observaciones.clear()
        self.btn_confirmar_sustitucion.setEnabled(False)

    def refrescar(self):
        """Refrescar los datos."""
        self.cargar_profesores()
        self.tabla_guardias.setRowCount(0)
