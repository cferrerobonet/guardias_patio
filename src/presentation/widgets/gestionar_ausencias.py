"""
Widget para gestionar ausencias de profesores.

Permite registrar, editar, eliminar y visualizar ausencias.
"""

from datetime import date

from presentation.theme import legacy_styles as styles
from infrastructure.database.models import Ausencia, Guardia, Profesor
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from services.gestor_ausencias import GestorAusencias
from presentation.widgets.dialogo_reasignacion import DialogoReasignacion
from services.gestor_cursos import GestorCursos
from utils.icons import icon_for_button
from utils.ui_helpers import get_corporate_icon

from presentation.forms.base_form import BaseForm


class GestionarAusenciasForm(BaseForm):
    """Formulario para gestionar ausencias de profesores."""

    def __init__(self, session):
        """
        Inicializar formulario de gestión de ausencias.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.ausencia_actual = None  # Para edición
        self.setWindowTitle("Gestión de Ausencias")
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout(self)

        # Título
        titulo = QLabel("🏥 GESTIÓN DE AUSENCIAS")
        titulo.setObjectName("titleMain")
        layout_principal.addWidget(titulo)

        # Layout horizontal: Lista + Formulario
        layout_horizontal = QHBoxLayout()
        layout_horizontal.addLayout(self._crear_panel_lista(), 2)
        layout_horizontal.addLayout(self._crear_panel_formulario(), 1)

        layout_principal.addLayout(layout_horizontal)

        # Cargar datos iniciales
        self.cargar_profesores()
        self.cargar_ausencias()

        # A11Y: Orden de tabulación (de arriba abajo, izquierda a derecha)
        QWidget.setTabOrder(self.profesor_combo, self.tipo_combo)
        QWidget.setTabOrder(self.tipo_combo, self.fecha_inicio_input)
        QWidget.setTabOrder(self.fecha_inicio_input, self.fecha_fin_input)
        QWidget.setTabOrder(self.fecha_fin_input, self.motivo_input)
        QWidget.setTabOrder(self.motivo_input, self.guardar_btn)
        QWidget.setTabOrder(self.guardar_btn, self.ver_guardias_btn)
        QWidget.setTabOrder(self.ver_guardias_btn, self.cancelar_btn)

    def cargar_datos(self):
        """
        Recargar datos cuando cambia el curso activo.

        Este método es llamado automáticamente por el sistema de señales
        cuando el usuario cambia de curso escolar.
        """
        self.logger.info("🔄 Recargando ausencias para el curso activo")
        self.session.expire_all()  # Limpiar caché de SQLAlchemy
        self.cargar_profesores()
        self.cargar_ausencias()

    def _crear_panel_lista(self) -> QVBoxLayout:
        """Crear panel izquierdo con lista de ausencias."""
        panel = QVBoxLayout()

        titulo_lista = QLabel("AUSENCIAS REGISTRADAS")
        titulo_lista.setObjectName("titleMain")
        panel.addWidget(titulo_lista)

        # Tabla de ausencias
        self.tabla_ausencias = self._crear_tabla_ausencias()
        panel.addWidget(self.tabla_ausencias)

        # Botones de acción
        panel.addLayout(self._crear_botones_lista())

        return panel

    def _crear_tabla_ausencias(self) -> QTableWidget:
        """Crear tabla de ausencias."""
        tabla = QTableWidget()
        tabla.setColumnCount(7)
        tabla.setHorizontalHeaderLabels(
            ["ID", "Profesor", "Tipo", "Fecha Inicio", "Fecha Fin", "Días", "Estado"]
        )
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tabla.itemDoubleClicked.connect(self.cargar_ausencia_seleccionada)
        tabla.setColumnWidth(0, 50)
        tabla.setColumnWidth(1, 200)
        tabla.setColumnWidth(2, 120)
        tabla.setColumnWidth(3, 100)
        tabla.setColumnWidth(4, 100)
        tabla.setColumnWidth(5, 60)
        tabla.setColumnWidth(6, 80)
        return tabla

    def _crear_botones_lista(self) -> QHBoxLayout:
        """Crear botones de acción para la lista."""
        botones = QHBoxLayout()

        # El botón de refrescar fue eliminado porque la tabla se actualiza
        # automáticamente después de cada operación (crear, editar, eliminar, desactivar)

        self.editar_btn = QPushButton("Editar")
        self.editar_btn.setIcon(icon_for_button("edit"))
        self.editar_btn.setProperty("warning", True)
        self.editar_btn.clicked.connect(self.cargar_ausencia_seleccionada)
        self.editar_btn.setToolTip("Editar la ausencia seleccionada")
        botones.addWidget(self.editar_btn)

        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setIcon(icon_for_button("delete"))
        self.delete_btn.setProperty("danger", True)
        self.delete_btn.clicked.connect(self.eliminar_ausencia_seleccionada)
        self.delete_btn.setToolTip("Eliminar la ausencia seleccionada (Del)")
        botones.addWidget(self.delete_btn)

        self.desactivar_btn = QPushButton("Desactivar")
        self.desactivar_btn.setIcon(icon_for_button("pause"))
        self.desactivar_btn.setObjectName("secondaryButton")
        self.desactivar_btn.clicked.connect(self.desactivar_ausencia_seleccionada)
        self.desactivar_btn.setToolTip("Desactivar la ausencia sin eliminarla")
        botones.addWidget(self.desactivar_btn)

        return botones

    def _crear_panel_formulario(self) -> QVBoxLayout:
        """Crear panel derecho con formulario."""
        panel = QVBoxLayout()

        self.titulo_form = QLabel("NUEVA AUSENCIA")
        self.titulo_form.setObjectName("titleMain")
        panel.addWidget(self.titulo_form)

        # Grupo de datos
        panel.addWidget(self._crear_grupo_datos())

        # Preview de guardias
        panel.addWidget(self._crear_grupo_preview())

        # Botones de acción
        panel.addLayout(self._crear_botones_formulario())

        panel.addStretch()

        return panel

    def _crear_grupo_datos(self) -> QGroupBox:
        """Crear grupo de datos de la ausencia."""
        grupo = QGroupBox("Datos de la Ausencia")
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Profesor
        label_profesor = QLabel("Profesor:")
        label_profesor.setObjectName("fieldLabel")
        layout.addWidget(label_profesor)
        self.profesor_combo = QComboBox()
        self.profesor_combo.setMaximumWidth(400)
        self.profesor_combo.currentIndexChanged.connect(self.actualizar_preview_guardias)
        self.profesor_combo.setAccessibleName("Selector de profesor ausente")
        layout.addWidget(self.profesor_combo)

        # Tipo de ausencia
        label_tipo = QLabel("Tipo de ausencia:")
        label_tipo.setObjectName("fieldLabel")
        layout.addWidget(label_tipo)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["baja_medica", "permiso", "vacaciones", "otros"])
        self.tipo_combo.setMaximumWidth(200)
        self.tipo_combo.setAccessibleName("Tipo de ausencia")
        layout.addWidget(self.tipo_combo)

        # Fechas
        layout.addLayout(self._crear_layout_fechas())

        # Motivo
        label_motivo = QLabel("Motivo (opcional):")
        label_motivo.setObjectName("fieldLabel")
        layout.addWidget(label_motivo)
        self.motivo_input = QTextEdit()
        self.motivo_input.setPlaceholderText("Descripción del motivo de la ausencia...")
        self.motivo_input.setMaximumHeight(80)
        self.motivo_input.setMaximumWidth(400)
        self.motivo_input.setAccessibleName("Motivo de la ausencia")
        layout.addWidget(self.motivo_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_layout_fechas(self) -> QHBoxLayout:
        """Crear layout de fechas en horizontal."""
        layout_fechas = QHBoxLayout()

        # Fecha inicio
        layout_inicio = QVBoxLayout()
        label_inicio = QLabel("Fecha de inicio:")
        label_inicio.setObjectName("fieldLabel")
        layout_inicio.addWidget(label_inicio)
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setMaximumWidth(150)
        self.fecha_inicio_input.dateChanged.connect(self.actualizar_preview_guardias)
        self.fecha_inicio_input.setAccessibleName("Fecha de inicio de la ausencia")
        layout_inicio.addWidget(self.fecha_inicio_input)
        layout_fechas.addLayout(layout_inicio)

        # Fecha fin
        layout_fin = QVBoxLayout()
        label_fin = QLabel("Fecha de fin:")
        label_fin.setObjectName("fieldLabel")
        layout_fin.addWidget(label_fin)
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setMaximumWidth(150)
        self.fecha_fin_input.dateChanged.connect(self.actualizar_preview_guardias)
        self.fecha_fin_input.setAccessibleName("Fecha de fin de la ausencia")
        layout_fin.addWidget(self.fecha_fin_input)
        layout_fechas.addLayout(layout_fin)

        layout_fechas.addStretch()
        return layout_fechas

    def _crear_grupo_preview(self) -> QGroupBox:
        """Crear grupo de preview de guardias afectadas."""
        grupo = QGroupBox("Guardias Afectadas (Preview)")
        layout = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet(
            "background-color: #fafafa; border: 1px solid #bdbdbd; border-radius: 4px;"
        )
        layout.addWidget(self.preview_text)

        grupo.setLayout(layout)
        return grupo

    def _crear_botones_formulario(self) -> QHBoxLayout:
        """Crear botones de acción del formulario."""
        botones = QHBoxLayout()

        self.guardar_btn = QPushButton("Guardar Ausencia")
        self.guardar_btn.setIcon(icon_for_button("save"))
        self.guardar_btn.setProperty("success", True)
        self.guardar_btn.clicked.connect(self.guardar_ausencia)
        self.guardar_btn.setToolTip("Guardar la ausencia (Ctrl+S)")
        self.guardar_btn.setAccessibleName("Botón guardar ausencia")
        botones.addWidget(self.guardar_btn)

        self.ver_guardias_btn = QPushButton("Ver Guardias Afectadas")
        self.ver_guardias_btn.setIcon(icon_for_button("view"))
        self.ver_guardias_btn.clicked.connect(self.mostrar_guardias_afectadas)
        self.ver_guardias_btn.setToolTip("Ver y reasignar guardias afectadas")
        self.ver_guardias_btn.setEnabled(False)
        self.ver_guardias_btn.setAccessibleName("Botón ver guardias afectadas")
        botones.addWidget(self.ver_guardias_btn)

        self.cancelar_btn = QPushButton("Cancelar")
        self.cancelar_btn.setIcon(icon_for_button("close"))
        self.cancelar_btn.setObjectName("secondaryButton")
        self.cancelar_btn.clicked.connect(self.limpiar_formulario)
        self.cancelar_btn.setToolTip("Cancelar y limpiar formulario (Esc)")
        self.cancelar_btn.setAccessibleName("Botón cancelar y limpiar formulario")
        botones.addWidget(self.cancelar_btn)

        return botones

    def cargar_profesores(self):
        """Cargar la lista de profesores del curso activo en el combo."""
        try:
            self.profesor_combo.clear()

            # Obtener curso activo
            curso_activo = GestorCursos.from_session(self.session).obtener_curso_activo()
            if not curso_activo:
                self.logger.warning("No hay curso activo, no se cargan profesores")
                return

            # Solo profesores con guardias en el curso activo
            from application.app_services import AppServices
            profesores = AppServices(self.session).profesores_con_guardias_en_curso(curso_activo.id)

            for p in profesores:
                self.profesor_combo.addItem(p.nombre_completo, p.id)

            self.logger.info(
                f"Cargados {len(profesores)} profesores del curso {curso_activo.nombre}"
            )
        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "cargar profesores")

    def cargar_ausencias(self):
        """Cargar todas las ausencias en la tabla filtradas por curso activo."""
        try:
            self.tabla_ausencias.setRowCount(0)

            # Obtener curso activo
            curso_activo = GestorCursos.from_session(self.session).obtener_curso_activo()
            if not curso_activo:
                self.logger.warning("No hay curso activo, no se cargan ausencias")
                return

            # Ausencias de profesores con guardias en el curso activo
            from application.app_services import AppServices
            ausencias = AppServices(self.session).ausencias_de_profesores_en_curso(curso_activo.id)

            for ausencia in ausencias:
                row = self.tabla_ausencias.rowCount()
                self.tabla_ausencias.insertRow(row)

                # Llenar datos
                self.tabla_ausencias.setItem(row, 0, QTableWidgetItem(str(ausencia.id)))

                from application.app_services import AppServices
                _prof = AppServices(self.session).profesores.get_by_id(ausencia.profesor_id) if ausencia.profesor_id else None
                profesor_nombre = _prof.nombre_completo if _prof else "N/A"
                self.tabla_ausencias.setItem(row, 1, QTableWidgetItem(profesor_nombre))

                self.tabla_ausencias.setItem(row, 2, QTableWidgetItem(ausencia.tipo))

                self.tabla_ausencias.setItem(
                    row, 3, QTableWidgetItem(ausencia.fecha_inicio.strftime("%d/%m/%Y"))
                )

                self.tabla_ausencias.setItem(
                    row, 4, QTableWidgetItem(ausencia.fecha_fin.strftime("%d/%m/%Y"))
                )

                dias = (ausencia.fecha_fin - ausencia.fecha_inicio).days + 1
                self.tabla_ausencias.setItem(row, 5, QTableWidgetItem(str(dias)))

                # Estado con color
                estado_item = QTableWidgetItem("Activa" if ausencia.activa else "Inactiva")
                if ausencia.activa:
                    if ausencia.fecha_fin < date.today():
                        estado_item.setBackground(Qt.GlobalColor.lightGray)
                    elif ausencia.fecha_inicio <= date.today() <= ausencia.fecha_fin:
                        estado_item.setBackground(Qt.GlobalColor.yellow)
                    else:
                        estado_item.setBackground(Qt.GlobalColor.cyan)
                else:
                    estado_item.setBackground(Qt.GlobalColor.red)

                self.tabla_ausencias.setItem(row, 6, estado_item)

            self.logger.info(
                f"Cargadas {self.tabla_ausencias.rowCount()} ausencias "
                f"del curso {curso_activo.nombre}"
            )

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "cargar ausencias")

    def cargar_ausencia_seleccionada(self):
        """Cargar la ausencia seleccionada en el formulario para edición."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            self.mostrar_advertencia(
                "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        try:
            row = selected_rows[0].row()
            ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

            from application.app_services import AppServices
            ausencia = AppServices(self.session).ausencias.get_by_id(ausencia_id)
            if not ausencia:
                self.mostrar_error("Error", "No se encontró la ausencia")
                return

            # Guardar referencia para edición
            self.ausencia_actual = ausencia_id
            self.titulo_form.setText("EDITAR AUSENCIA")

            # Cargar datos
            for i in range(self.profesor_combo.count()):
                if self.profesor_combo.itemData(i) == ausencia.profesor_id:
                    self.profesor_combo.setCurrentIndex(i)
                    break

            tipo_index = self.tipo_combo.findText(ausencia.tipo)
            if tipo_index >= 0:
                self.tipo_combo.setCurrentIndex(tipo_index)

            self.fecha_inicio_input.setDate(
                QDate(
                    ausencia.fecha_inicio.year,
                    ausencia.fecha_inicio.month,
                    ausencia.fecha_inicio.day,
                )
            )
            self.fecha_fin_input.setDate(
                QDate(
                    ausencia.fecha_fin.year,
                    ausencia.fecha_fin.month,
                    ausencia.fecha_fin.day,
                )
            )

            self.motivo_input.setPlainText(ausencia.motivo or "")
            self.ver_guardias_btn.setEnabled(True)
            self.actualizar_preview_guardias()

            self.logger.info(f"Ausencia {ausencia_id} cargada para edición")

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "cargar ausencia seleccionada")

    def guardar_ausencia(self):
        """Guardar o actualizar la ausencia."""
        if self.profesor_combo.currentIndex() < 0:
            self.mostrar_advertencia("Error", "Por favor selecciona un profesor")
            return

        profesor_id = self.profesor_combo.currentData()
        tipo = self.tipo_combo.currentText()
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()
        motivo = self.motivo_input.toPlainText().strip() or None

        if fecha_fin < fecha_inicio:
            self.mostrar_advertencia(
                "Error",
                "La fecha de fin debe ser posterior o igual a la fecha de inicio",
            )
            return

        try:
            if self.ausencia_actual:
                GestorAusencias.editar_ausencia(
                    self.session,
                    self.ausencia_actual,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    tipo=tipo,
                    motivo=motivo,
                )
                self.mostrar_exito("Éxito", "Ausencia actualizada correctamente")
            else:
                GestorAusencias.registrar_ausencia(
                    self.session,
                    profesor_id,
                    fecha_inicio,
                    fecha_fin,
                    tipo,
                    motivo,
                )
                self.mostrar_exito("Éxito", "Ausencia registrada correctamente")

            self.limpiar_formulario()
            self.cargar_ausencias()

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "guardar ausencia")

    def eliminar_ausencia_seleccionada(self):
        """Eliminar la ausencia seleccionada."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            self.mostrar_advertencia(
                "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        row = selected_rows[0].row()
        ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

        from utils.ui_helpers import show_confirmation

        confirmado = show_confirmation(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de que quieres eliminar esta ausencia?\n"
            "Esta acción no se puede deshacer.",
            default_button="No",
        )

        if confirmado:
            try:
                GestorAusencias.eliminar_ausencia(self.session, ausencia_id)
                self.mostrar_exito("Éxito", "Ausencia eliminada correctamente")
                self.cargar_ausencias()
                self.limpiar_formulario()
            except (ValueError, TypeError, OSError) as e:
                self.manejar_excepcion(e, "eliminar ausencia")

    def desactivar_ausencia_seleccionada(self):
        """Desactivar la ausencia seleccionada sin eliminarla."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            self.mostrar_advertencia(
                "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        try:
            row = selected_rows[0].row()
            ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

            GestorAusencias.desactivar_ausencia(self.session, ausencia_id)
            self.mostrar_exito("Éxito", "Ausencia desactivada correctamente")
            self.cargar_ausencias()

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "desactivar ausencia")

    def actualizar_preview_guardias(self):
        """Actualizar el preview de guardias afectadas."""
        if self.profesor_combo.currentIndex() < 0:
            self.preview_text.setPlainText("Selecciona un profesor para ver las guardias afectadas")
            return

        try:
            profesor_id = self.profesor_combo.currentData()
            fecha_inicio = self.fecha_inicio_input.date().toPyDate()
            fecha_fin = self.fecha_fin_input.date().toPyDate()

            if fecha_fin < fecha_inicio:
                self.preview_text.setPlainText("Fecha de fin anterior a fecha de inicio")
                return

            guardias = GestorAusencias.obtener_guardias_afectadas_por_periodo(
                self.session, profesor_id, fecha_inicio, fecha_fin
            )

            if not guardias:
                self.preview_text.setPlainText("No hay guardias asignadas en este periodo")
            else:
                texto = f"{len(guardias)} guardias afectadas:\n\n"
                for g in guardias[:10]:  # Mostrar máximo 10
                    zona_nombre = g.zona.nombre_zona if g.zona else "N/A"
                    texto += f"• {g.fecha.strftime('%d/%m/%Y')} - {g.turno} - Recreo {g.recreo} - {zona_nombre}\n"  # noqa: E501

                if len(guardias) > 10:
                    texto += f"\n... y {len(guardias) - 10} más"

                self.preview_text.setPlainText(texto)

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "actualizar preview guardias")
            self.preview_text.setPlainText(f"Error al cargar guardias: {str(e)}")

    def mostrar_guardias_afectadas(self):
        """Mostrar diálogo con guardias afectadas y opción de reasignación."""
        if not self.ausencia_actual:
            self.mostrar_advertencia("Error", "Primero debes seleccionar o guardar una ausencia")
            return

        try:
            guardias = GestorAusencias.obtener_guardias_afectadas(self.session, self.ausencia_actual)

            if not guardias:
                self.mostrar_informacion(
                    "Sin guardias", "No hay guardias afectadas por esta ausencia"
                )
                return

            # Crear diálogo de reasignación
            dialogo = DialogoReasignacion(guardias, self.ausencia_actual, self.session, self)
            dialogo.exec()

            # Actualizar tabla si hubo cambios
            self.cargar_ausencias()

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "mostrar guardias afectadas")

    def limpiar_formulario(self):
        """Limpiar el formulario y resetear el modo de edición."""
        self.ausencia_actual = None
        self.titulo_form.setText("NUEVA AUSENCIA")
        self.profesor_combo.setCurrentIndex(-1)
        self.tipo_combo.setCurrentIndex(0)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.motivo_input.clear()
        self.preview_text.clear()
        self.ver_guardias_btn.setEnabled(False)
        self.logger.info("Formulario limpiado")

