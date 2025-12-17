"""
Widget para gestionar ausencias de profesores.

Permite registrar, editar, eliminar y visualizar ausencias.
"""

from datetime import date

import ui_styles as styles
from infrastructure.database.models import Ausencia, Guardia, Profesor
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)
from services.gestor_ausencias import (
    desactivar_ausencia,
    editar_ausencia,
    eliminar_ausencia,
    obtener_guardias_afectadas,
    obtener_guardias_afectadas_por_periodo,
    obtener_profesores_disponibles,
    reasignar_guardia,
    reasignar_guardias_automaticamente,
    registrar_ausencia,
)
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
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout_principal.addWidget(titulo)

        # Layout horizontal: Lista + Formulario
        layout_horizontal = QHBoxLayout()
        layout_horizontal.addLayout(self._crear_panel_lista(), 2)
        layout_horizontal.addLayout(self._crear_panel_formulario(), 1)

        layout_principal.addLayout(layout_horizontal)

        # Cargar datos iniciales
        self.cargar_profesores()
        self.cargar_ausencias()

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
        titulo_lista.setStyleSheet(styles.STYLE_TITLE_MAIN)
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
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.cargar_ausencia_seleccionada)
        self.editar_btn.setToolTip("Editar la ausencia seleccionada")
        botones.addWidget(self.editar_btn)

        self.delete_btn = QPushButton("Eliminar")
        self.delete_btn.setIcon(icon_for_button("delete"))
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_ausencia_seleccionada)
        self.delete_btn.setToolTip("Eliminar la ausencia seleccionada (Del)")
        botones.addWidget(self.delete_btn)

        self.desactivar_btn = QPushButton("Desactivar")
        self.desactivar_btn.setIcon(icon_for_button("pause"))
        self.desactivar_btn.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        self.desactivar_btn.clicked.connect(self.desactivar_ausencia_seleccionada)
        self.desactivar_btn.setToolTip("Desactivar la ausencia sin eliminarla")
        botones.addWidget(self.desactivar_btn)

        return botones

    def _crear_panel_formulario(self) -> QVBoxLayout:
        """Crear panel derecho con formulario."""
        panel = QVBoxLayout()

        self.titulo_form = QLabel("NUEVA AUSENCIA")
        self.titulo_form.setStyleSheet(styles.STYLE_TITLE_MAIN)
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
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Profesor
        label_profesor = QLabel("Profesor:")
        label_profesor.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_profesor)
        self.profesor_combo = QComboBox()
        self.profesor_combo.setStyleSheet(styles.STYLE_INPUT)
        self.profesor_combo.setMaximumWidth(400)
        self.profesor_combo.currentIndexChanged.connect(self.actualizar_preview_guardias)
        layout.addWidget(self.profesor_combo)

        # Tipo de ausencia
        label_tipo = QLabel("Tipo de ausencia:")
        label_tipo.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_tipo)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["baja_medica", "permiso", "vacaciones", "otros"])
        self.tipo_combo.setStyleSheet(styles.STYLE_INPUT)
        self.tipo_combo.setMaximumWidth(200)
        layout.addWidget(self.tipo_combo)

        # Fechas
        layout.addLayout(self._crear_layout_fechas())

        # Motivo
        label_motivo = QLabel("Motivo (opcional):")
        label_motivo.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_motivo)
        self.motivo_input = QTextEdit()
        self.motivo_input.setPlaceholderText("Descripción del motivo de la ausencia...")
        self.motivo_input.setStyleSheet(styles.STYLE_INPUT)
        self.motivo_input.setMaximumHeight(80)
        self.motivo_input.setMaximumWidth(400)
        layout.addWidget(self.motivo_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_layout_fechas(self) -> QHBoxLayout:
        """Crear layout de fechas en horizontal."""
        layout_fechas = QHBoxLayout()

        # Fecha inicio
        layout_inicio = QVBoxLayout()
        label_inicio = QLabel("Fecha de inicio:")
        label_inicio.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_inicio.addWidget(label_inicio)
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_input.setMaximumWidth(150)
        self.fecha_inicio_input.dateChanged.connect(self.actualizar_preview_guardias)
        layout_inicio.addWidget(self.fecha_inicio_input)
        layout_fechas.addLayout(layout_inicio)

        # Fecha fin
        layout_fin = QVBoxLayout()
        label_fin = QLabel("Fecha de fin:")
        label_fin.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fin.addWidget(label_fin)
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_input.setMaximumWidth(150)
        self.fecha_fin_input.dateChanged.connect(self.actualizar_preview_guardias)
        layout_fin.addWidget(self.fecha_fin_input)
        layout_fechas.addLayout(layout_fin)

        layout_fechas.addStretch()
        return layout_fechas

    def _crear_grupo_preview(self) -> QGroupBox:
        """Crear grupo de preview de guardias afectadas."""
        grupo = QGroupBox("Guardias Afectadas (Preview)")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
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
        self.guardar_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.guardar_btn.clicked.connect(self.guardar_ausencia)
        self.guardar_btn.setToolTip("Guardar la ausencia (Ctrl+S)")
        botones.addWidget(self.guardar_btn)

        self.ver_guardias_btn = QPushButton("Ver Guardias Afectadas")
        self.ver_guardias_btn.setIcon(icon_for_button("view"))
        self.ver_guardias_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.ver_guardias_btn.clicked.connect(self.mostrar_guardias_afectadas)
        self.ver_guardias_btn.setToolTip("Ver y reasignar guardias afectadas")
        self.ver_guardias_btn.setEnabled(False)
        botones.addWidget(self.ver_guardias_btn)

        self.cancelar_btn = QPushButton("Cancelar")
        self.cancelar_btn.setIcon(icon_for_button("close"))
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        self.cancelar_btn.clicked.connect(self.limpiar_formulario)
        self.cancelar_btn.setToolTip("Cancelar y limpiar formulario (Esc)")
        botones.addWidget(self.cancelar_btn)

        return botones

    def cargar_profesores(self):
        """Cargar la lista de profesores del curso activo en el combo."""
        try:
            self.profesor_combo.clear()

            # Obtener curso activo
            curso_activo = GestorCursos.obtener_curso_activo(self.session)
            if not curso_activo:
                self.logger.warning("No hay curso activo, no se cargan profesores")
                return

            # Solo profesores con guardias en el curso activo
            profesores = (
                self.session.query(Profesor)
                .join(Guardia, Profesor.id == Guardia.profesor_id)
                .filter(Guardia.curso_id == curso_activo.id)
                .distinct()
                .order_by(Profesor.nombre_completo)
                .all()
            )

            for p in profesores:
                self.profesor_combo.addItem(p.nombre_completo, p.id)

            self.logger.info(
                f"Cargados {len(profesores)} profesores del curso {curso_activo.nombre}"
            )
        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def cargar_ausencias(self):
        """Cargar todas las ausencias en la tabla filtradas por curso activo."""
        try:
            self.tabla_ausencias.setRowCount(0)

            # Obtener curso activo
            curso_activo = GestorCursos.obtener_curso_activo(self.session)
            if not curso_activo:
                self.logger.warning("No hay curso activo, no se cargan ausencias")
                return

            # Filtrar ausencias de profesores que tienen guardias en el curso activo
            # Subconsulta: IDs de profesores con guardias en el curso activo
            # Obtener IDs de profesores con guardias
            profesores_con_guardias = (
                self.session.query(Guardia.profesor_id)
                .filter(Guardia.curso_id == curso_activo.id)
                .distinct()
            )

            # Ausencias de esos profesores
            ausencias = (
                self.session.query(Ausencia)
                .filter(Ausencia.profesor_id.in_(profesores_con_guardias))
                .order_by(Ausencia.fecha_inicio.desc())
                .all()
            )

            for ausencia in ausencias:
                row = self.tabla_ausencias.rowCount()
                self.tabla_ausencias.insertRow(row)

                # Llenar datos
                self.tabla_ausencias.setItem(row, 0, QTableWidgetItem(str(ausencia.id)))

                profesor_nombre = ausencia.profesor.nombre_completo if ausencia.profesor else "N/A"
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

        except Exception as e:
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

            ausencia = self.session.query(Ausencia).get(ausencia_id)
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

        except Exception as e:
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
                editar_ausencia(
                    self.session,
                    self.ausencia_actual,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    tipo=tipo,
                    motivo=motivo,
                )
                self.mostrar_exito("Éxito", "Ausencia actualizada correctamente")
            else:
                registrar_ausencia(
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

        except Exception as e:
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
                eliminar_ausencia(self.session, ausencia_id)
                self.mostrar_exito("Éxito", "Ausencia eliminada correctamente")
                self.cargar_ausencias()
                self.limpiar_formulario()
            except Exception as e:
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

            desactivar_ausencia(self.session, ausencia_id)
            self.mostrar_exito("Éxito", "Ausencia desactivada correctamente")
            self.cargar_ausencias()

        except Exception as e:
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

            guardias = obtener_guardias_afectadas_por_periodo(
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

        except Exception as e:
            self.manejar_excepcion(e, "actualizar preview guardias")
            self.preview_text.setPlainText(f"Error al cargar guardias: {str(e)}")

    def mostrar_guardias_afectadas(self):
        """Mostrar diálogo con guardias afectadas y opción de reasignación."""
        if not self.ausencia_actual:
            self.mostrar_advertencia("Error", "Primero debes seleccionar o guardar una ausencia")
            return

        try:
            guardias = obtener_guardias_afectadas(self.session, self.ausencia_actual)

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

        except Exception as e:
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


class DialogoReasignacion(QDialog):
    """Diálogo para reasignar guardias afectadas por una ausencia."""

    def __init__(self, guardias, ausencia_id, session, parent=None):
        """
        Inicializar diálogo de reasignación.

        Args:
            guardias: Lista de guardias afectadas
            ausencia_id: ID de la ausencia
            session: Sesión de base de datos
            parent: Widget padre
        """
        super().__init__(parent)
        self.guardias = guardias
        self.ausencia_id = ausencia_id
        self.session = session
        self.setWindowTitle("Reasignación de Guardias")
        self.setWindowIcon(get_corporate_icon())
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        """Inicializar la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel(f"Guardias Afectadas ({len(self.guardias)} guardias)")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(titulo)

        # Tabla de guardias
        self.tabla = self._crear_tabla()
        layout.addWidget(self.tabla)

        # Botones de acción
        layout.addLayout(self._crear_botones())

    def _crear_tabla(self) -> QTableWidget:
        """Crear tabla de guardias."""
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Turno", "Recreo", "Zona", "Profesor Actual"]
        )
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setColumnWidth(0, 50)
        tabla.setColumnWidth(1, 100)
        tabla.setColumnWidth(2, 80)
        tabla.setColumnWidth(3, 80)
        tabla.setColumnWidth(4, 150)
        tabla.setColumnWidth(5, 200)

        for i, guardia in enumerate(self.guardias):
            tabla.insertRow(i)
            tabla.setItem(i, 0, QTableWidgetItem(str(guardia.id)))
            tabla.setItem(i, 1, QTableWidgetItem(guardia.fecha.strftime("%d/%m/%Y")))
            tabla.setItem(i, 2, QTableWidgetItem(guardia.turno))
            tabla.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
            zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"
            tabla.setItem(i, 4, QTableWidgetItem(zona_nombre))
            profesor_nombre = guardia.profesor.nombre_completo if guardia.profesor else "N/A"
            tabla.setItem(i, 5, QTableWidgetItem(profesor_nombre))

        return tabla

    def _crear_botones(self) -> QHBoxLayout:
        """Crear botones de acción."""
        botones = QHBoxLayout()

        btn_auto = QPushButton("Reasignar Automáticamente")
        btn_auto.setIcon(icon_for_button("refresh"))
        btn_auto.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        btn_auto.clicked.connect(self.reasignar_automaticamente)
        botones.addWidget(btn_auto)

        btn_manual = QPushButton("Reasignar Seleccionada")
        btn_manual.setIcon(icon_for_button("user"))
        btn_manual.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        btn_manual.clicked.connect(self.reasignar_manual)
        botones.addWidget(btn_manual)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setIcon(icon_for_button("close"))
        btn_cerrar.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        btn_cerrar.clicked.connect(self.close)
        botones.addWidget(btn_cerrar)

        return botones

    def reasignar_automaticamente(self):
        """Reasignar todas las guardias automáticamente."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar reasignación",
            f"¿Reasignar automáticamente {len(self.guardias)} guardias?\n"
            "El sistema buscará los mejores sustitutos disponibles.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultados = reasignar_guardias_automaticamente(self.session, self.guardias)

                mensaje = (
                    f"Reasignación completada:\n\n"
                    f"Reasignadas: {resultados['reasignadas']}\n"
                    f"Fallidas: {resultados['fallidas']}"
                )

                if resultados["fallidas"] > 0:
                    mensaje += "\n\nVer detalles en el log para más información."

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Resultado")
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setText(mensaje)
                msg.exec()

                if resultados["reasignadas"] > 0:
                    self.close()

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")

    def reasignar_manual(self):
        """Permitir seleccionar manualmente un sustituto."""
        selected_rows = self.tabla.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Por favor selecciona una guardia")
            return

        try:
            row = selected_rows[0].row()
            guardia_id = int(self.tabla.item(row, 0).text())

            guardia = next((g for g in self.guardias if g.id == guardia_id), None)
            if not guardia:
                return

            disponibles = obtener_profesores_disponibles(
                self.session,
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
                excluir_profesor_id=guardia.profesor_id,
            )

            if not disponibles:
                QMessageBox.warning(
                    self,
                    "Sin disponibles",
                    "No hay profesores disponibles para esta guardia",
                )
                return

            nombres = [f"{p.nombre_completo} ({count} guardias hoy)" for p, count in disponibles]

            nombre_seleccionado, ok = QInputDialog.getItem(
                self, "Seleccionar Sustituto", "Profesor:", nombres, 0, False
            )

            if ok and nombre_seleccionado:
                index = nombres.index(nombre_seleccionado)
                nuevo_profesor, _ = disponibles[index]

                reasignar_guardia(self.session, guardia_id, nuevo_profesor.id)

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Éxito")
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setText(
                    f"Guardia reasignada a "
                    f"<span style='color: #007ACC; "
                    f"font-style: italic;'>{nuevo_profesor.nombre_completo}</span>"
                )
                msg.exec()

                self.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")
