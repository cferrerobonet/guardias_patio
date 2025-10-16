"""
Widget para gestionar ausencias de profesores.
Permite registrar, editar, eliminar y visualizar ausencias.
"""

from datetime import date

import ui_styles as styles
from database.db_manager import SessionLocal
from models.models import Ausencia, Profesor
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
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
from utils import get_logger

logger = get_logger(__name__)


class GestionarAusenciasForm(QWidget):
    """Formulario para gestionar ausencias de profesores."""

    def __init__(self):
        super().__init__()
        self.ausencia_actual = None  # Para edición
        self.init_ui()
        self.cargar_ausencias()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout_principal = QVBoxLayout(self)

        # Título
        titulo = QLabel("🏥 GESTIÓN DE AUSENCIAS")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout_principal.addWidget(titulo)

        # Layout horizontal: Lista + Formulario
        layout_horizontal = QHBoxLayout()

        # === PANEL IZQUIERDO: Lista de ausencias ===
        panel_izquierdo = QVBoxLayout()

        titulo_lista = QLabel("📋 AUSENCIAS REGISTRADAS")
        titulo_lista.setStyleSheet(styles.STYLE_TITLE_MAIN)
        panel_izquierdo.addWidget(titulo_lista)

        # Tabla de ausencias
        self.tabla_ausencias = QTableWidget()
        self.tabla_ausencias.setColumnCount(7)
        self.tabla_ausencias.setHorizontalHeaderLabels(
            ["ID", "Profesor", "Tipo", "Fecha Inicio", "Fecha Fin", "Días", "Estado"]
        )
        self.tabla_ausencias.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_ausencias.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_ausencias.itemDoubleClicked.connect(self.cargar_ausencia_seleccionada)
        self.tabla_ausencias.setColumnWidth(0, 50)
        self.tabla_ausencias.setColumnWidth(1, 200)
        self.tabla_ausencias.setColumnWidth(2, 120)
        self.tabla_ausencias.setColumnWidth(3, 100)
        self.tabla_ausencias.setColumnWidth(4, 100)
        self.tabla_ausencias.setColumnWidth(5, 60)
        self.tabla_ausencias.setColumnWidth(6, 80)
        panel_izquierdo.addWidget(self.tabla_ausencias)

        # Botones de acción para la lista
        botones_lista = QHBoxLayout()

        self.refresh_btn = QPushButton("🔄 Refrescar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_ausencias)
        self.refresh_btn.setToolTip("Recargar la lista de ausencias desde la base de datos (F5)")
        botones_lista.addWidget(self.refresh_btn)

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.cargar_ausencia_seleccionada)
        self.editar_btn.setToolTip("Editar la ausencia seleccionada")
        botones_lista.addWidget(self.editar_btn)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_ausencia_seleccionada)
        self.delete_btn.setToolTip("Eliminar la ausencia seleccionada (Del)")
        botones_lista.addWidget(self.delete_btn)

        self.desactivar_btn = QPushButton("⏸️ Desactivar")
        self.desactivar_btn.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        self.desactivar_btn.clicked.connect(self.desactivar_ausencia_seleccionada)
        self.desactivar_btn.setToolTip("Desactivar la ausencia sin eliminarla")
        botones_lista.addWidget(self.desactivar_btn)

        panel_izquierdo.addLayout(botones_lista)

        layout_horizontal.addLayout(panel_izquierdo, 2)

        # === PANEL DERECHO: Formulario ===
        panel_derecho = QVBoxLayout()

        self.titulo_form = QLabel("✏️ NUEVA AUSENCIA")
        self.titulo_form.setStyleSheet(styles.STYLE_TITLE_MAIN)
        panel_derecho.addWidget(self.titulo_form)

        # Grupo: Datos de la ausencia
        grupo_datos = QGroupBox("📝 Datos de la Ausencia")
        grupo_datos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_datos = QVBoxLayout()
        layout_datos.setSpacing(8)

        # Profesor
        label_profesor = QLabel("Profesor:")
        label_profesor.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_profesor)
        self.profesor_combo = QComboBox()
        self.profesor_combo.setStyleSheet(styles.STYLE_INPUT)
        self.profesor_combo.setMaximumWidth(400)
        layout_datos.addWidget(self.profesor_combo)

        # Tipo de ausencia
        label_tipo = QLabel("Tipo de ausencia:")
        label_tipo.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_tipo)
        self.tipo_combo = QComboBox()
        self.tipo_combo.addItems(["baja_medica", "permiso", "vacaciones", "otros"])
        self.tipo_combo.setStyleSheet(styles.STYLE_INPUT)
        self.tipo_combo.setMaximumWidth(200)
        layout_datos.addWidget(self.tipo_combo)

        # Fechas en horizontal
        layout_fechas = QHBoxLayout()

        layout_fecha_inicio = QVBoxLayout()
        label_fecha_inicio = QLabel("Fecha de inicio:")
        label_fecha_inicio.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fecha_inicio.addWidget(label_fecha_inicio)
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_input.setMaximumWidth(150)
        self.fecha_inicio_input.dateChanged.connect(self.actualizar_preview_guardias)
        layout_fecha_inicio.addWidget(self.fecha_inicio_input)
        layout_fechas.addLayout(layout_fecha_inicio)

        layout_fecha_fin = QVBoxLayout()
        label_fecha_fin = QLabel("Fecha de fin:")
        label_fecha_fin.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fecha_fin.addWidget(label_fecha_fin)
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_input.setMaximumWidth(150)
        self.fecha_fin_input.dateChanged.connect(self.actualizar_preview_guardias)
        layout_fecha_fin.addWidget(self.fecha_fin_input)
        layout_fechas.addLayout(layout_fecha_fin)

        layout_fechas.addStretch()
        layout_datos.addLayout(layout_fechas)

        # Motivo
        label_motivo = QLabel("Motivo (opcional):")
        label_motivo.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_motivo)
        self.motivo_input = QTextEdit()
        self.motivo_input.setPlaceholderText("Descripción del motivo de la ausencia...")
        self.motivo_input.setStyleSheet(styles.STYLE_INPUT)
        self.motivo_input.setMaximumHeight(80)
        self.motivo_input.setMaximumWidth(400)
        layout_datos.addWidget(self.motivo_input)

        grupo_datos.setLayout(layout_datos)
        panel_derecho.addWidget(grupo_datos)

        # Preview de guardias afectadas
        grupo_preview = QGroupBox("📊 Guardias Afectadas (Preview)")
        grupo_preview.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_preview = QVBoxLayout()

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setStyleSheet(
            "background-color: #fafafa; border: 1px solid #bdbdbd; border-radius: 4px;"
        )
        layout_preview.addWidget(self.preview_text)

        grupo_preview.setLayout(layout_preview)
        panel_derecho.addWidget(grupo_preview)

        # Botones de acción del formulario
        botones_form = QHBoxLayout()

        self.guardar_btn = QPushButton("💾 Guardar Ausencia")
        self.guardar_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.guardar_btn.clicked.connect(self.guardar_ausencia)
        self.guardar_btn.setToolTip("Guardar la ausencia (Ctrl+S)")
        botones_form.addWidget(self.guardar_btn)

        self.ver_guardias_btn = QPushButton("👁️ Ver Guardias Afectadas")
        self.ver_guardias_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.ver_guardias_btn.clicked.connect(self.mostrar_guardias_afectadas)
        self.ver_guardias_btn.setToolTip("Ver y reasignar guardias afectadas")
        self.ver_guardias_btn.setEnabled(False)
        botones_form.addWidget(self.ver_guardias_btn)

        self.cancelar_btn = QPushButton("❌ Cancelar")
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        self.cancelar_btn.clicked.connect(self.limpiar_formulario)
        self.cancelar_btn.setToolTip("Cancelar y limpiar formulario (Esc)")
        botones_form.addWidget(self.cancelar_btn)

        panel_derecho.addLayout(botones_form)
        panel_derecho.addStretch()

        layout_horizontal.addLayout(panel_derecho, 1)

        layout_principal.addLayout(layout_horizontal)

        # Cargar profesores en el combo
        self.cargar_profesores()

        # Conectar cambio de profesor con preview
        self.profesor_combo.currentIndexChanged.connect(self.actualizar_preview_guardias)

    def cargar_profesores(self):
        """Carga la lista de profesores en el combo."""
        self.profesor_combo.clear()
        with SessionLocal() as session:
            profesores = session.query(Profesor).order_by(Profesor.nombre_completo).all()
            for p in profesores:
                self.profesor_combo.addItem(p.nombre_completo, p.id)

    def cargar_ausencias(self):
        """Carga todas las ausencias en la tabla."""
        self.tabla_ausencias.setRowCount(0)

        with SessionLocal() as session:
            ausencias = session.query(Ausencia).order_by(Ausencia.fecha_inicio.desc()).all()

            for ausencia in ausencias:
                row = self.tabla_ausencias.rowCount()
                self.tabla_ausencias.insertRow(row)

                # ID
                self.tabla_ausencias.setItem(row, 0, QTableWidgetItem(str(ausencia.id)))

                # Profesor
                profesor_nombre = ausencia.profesor.nombre_completo if ausencia.profesor else "N/A"
                self.tabla_ausencias.setItem(row, 1, QTableWidgetItem(profesor_nombre))

                # Tipo
                self.tabla_ausencias.setItem(row, 2, QTableWidgetItem(ausencia.tipo))

                # Fecha Inicio
                self.tabla_ausencias.setItem(
                    row, 3, QTableWidgetItem(ausencia.fecha_inicio.strftime("%d/%m/%Y"))
                )

                # Fecha Fin
                self.tabla_ausencias.setItem(
                    row, 4, QTableWidgetItem(ausencia.fecha_fin.strftime("%d/%m/%Y"))
                )

                # Días
                dias = (ausencia.fecha_fin - ausencia.fecha_inicio).days + 1
                self.tabla_ausencias.setItem(row, 5, QTableWidgetItem(str(dias)))

                # Estado con color
                estado_item = QTableWidgetItem("Activa" if ausencia.activa else "Inactiva")
                if ausencia.activa:
                    if ausencia.fecha_fin < date.today():
                        estado_item.setBackground(Qt.GlobalColor.lightGray)  # Pasada
                    elif ausencia.fecha_inicio <= date.today() <= ausencia.fecha_fin:
                        estado_item.setBackground(Qt.GlobalColor.yellow)  # En curso
                    else:
                        estado_item.setBackground(Qt.GlobalColor.cyan)  # Futura
                else:
                    estado_item.setBackground(Qt.GlobalColor.red)  # Inactiva

                self.tabla_ausencias.setItem(row, 6, estado_item)

        logger.info(f"Cargadas {self.tabla_ausencias.rowCount()} ausencias")

    def cargar_ausencia_seleccionada(self):
        """Carga la ausencia seleccionada en el formulario para edición."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        row = selected_rows[0].row()
        ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

        with SessionLocal() as session:
            ausencia = session.query(Ausencia).get(ausencia_id)
            if not ausencia:
                QMessageBox.critical(self, "Error", "No se encontró la ausencia")
                return

            # Guardar referencia para edición
            self.ausencia_actual = ausencia_id

            # Cambiar título
            self.titulo_form.setText("✏️ EDITAR AUSENCIA")

            # Cargar datos en formulario
            # Buscar índice del profesor en el combo
            for i in range(self.profesor_combo.count()):
                if self.profesor_combo.itemData(i) == ausencia.profesor_id:
                    self.profesor_combo.setCurrentIndex(i)
                    break

            # Tipo
            tipo_index = self.tipo_combo.findText(ausencia.tipo)
            if tipo_index >= 0:
                self.tipo_combo.setCurrentIndex(tipo_index)

            # Fechas
            self.fecha_inicio_input.setDate(
                QDate(
                    ausencia.fecha_inicio.year,
                    ausencia.fecha_inicio.month,
                    ausencia.fecha_inicio.day,
                )
            )
            self.fecha_fin_input.setDate(
                QDate(ausencia.fecha_fin.year, ausencia.fecha_fin.month, ausencia.fecha_fin.day)
            )

            # Motivo
            self.motivo_input.setPlainText(ausencia.motivo or "")

            # Habilitar botón de ver guardias
            self.ver_guardias_btn.setEnabled(True)

            # Actualizar preview
            self.actualizar_preview_guardias()

        logger.info(f"Ausencia {ausencia_id} cargada para edición")

    def guardar_ausencia(self):
        """Guarda o actualiza la ausencia."""
        # Validar datos
        if self.profesor_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Error", "Por favor selecciona un profesor")
            return

        profesor_id = self.profesor_combo.currentData()
        tipo = self.tipo_combo.currentText()
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()
        motivo = self.motivo_input.toPlainText().strip() or None

        if fecha_fin < fecha_inicio:
            QMessageBox.warning(
                self, "Error", "La fecha de fin debe ser posterior o igual a la fecha de inicio"
            )
            return

        try:
            with SessionLocal() as session:
                if self.ausencia_actual:
                    # Editar ausencia existente
                    editar_ausencia(
                        session,
                        self.ausencia_actual,
                        fecha_inicio=fecha_inicio,
                        fecha_fin=fecha_fin,
                        tipo=tipo,
                        motivo=motivo,
                    )
                    QMessageBox.information(self, "Éxito", "Ausencia actualizada correctamente")
                else:
                    # Crear nueva ausencia
                    registrar_ausencia(
                        session,
                        profesor_id,
                        fecha_inicio,
                        fecha_fin,
                        tipo,
                        motivo,
                    )
                    QMessageBox.information(self, "Éxito", "Ausencia registrada correctamente")

            self.limpiar_formulario()
            self.cargar_ausencias()

        except Exception as e:
            logger.error(f"Error al guardar ausencia: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al guardar ausencia:\n{str(e)}")

    def eliminar_ausencia_seleccionada(self):
        """Elimina la ausencia seleccionada."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        row = selected_rows[0].row()
        ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

        # Confirmar eliminación
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de que quieres eliminar esta ausencia?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as session:
                    eliminar_ausencia(session, ausencia_id)
                QMessageBox.information(self, "Éxito", "Ausencia eliminada correctamente")
                self.cargar_ausencias()
                self.limpiar_formulario()
            except Exception as e:
                logger.error(f"Error al eliminar ausencia: {str(e)}")
                QMessageBox.critical(self, "Error", f"Error al eliminar ausencia:\n{str(e)}")

    def desactivar_ausencia_seleccionada(self):
        """Desactiva la ausencia seleccionada sin eliminarla."""
        selected_rows = self.tabla_ausencias.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self, "Sin selección", "Por favor selecciona una ausencia de la tabla"
            )
            return

        row = selected_rows[0].row()
        ausencia_id = int(self.tabla_ausencias.item(row, 0).text())

        try:
            with SessionLocal() as session:
                desactivar_ausencia(session, ausencia_id)
            QMessageBox.information(self, "Éxito", "Ausencia desactivada correctamente")
            self.cargar_ausencias()
        except Exception as e:
            logger.error(f"Error al desactivar ausencia: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error al desactivar ausencia:\n{str(e)}")

    def actualizar_preview_guardias(self):
        """Actualiza el preview de guardias afectadas."""
        if self.profesor_combo.currentIndex() < 0:
            self.preview_text.setPlainText("Selecciona un profesor para ver las guardias afectadas")
            return

        profesor_id = self.profesor_combo.currentData()
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()

        if fecha_fin < fecha_inicio:
            self.preview_text.setPlainText("⚠️ Fecha de fin anterior a fecha de inicio")
            return

        try:
            with SessionLocal() as session:
                guardias = obtener_guardias_afectadas_por_periodo(
                    session, profesor_id, fecha_inicio, fecha_fin
                )

                if not guardias:
                    self.preview_text.setPlainText(
                        "✅ No hay guardias asignadas en este periodo"
                    )
                else:
                    texto = f"⚠️ {len(guardias)} guardias afectadas:\n\n"
                    for g in guardias[:10]:  # Mostrar máximo 10
                        zona_nombre = g.zona.nombre_zona if g.zona else "N/A"
                        texto += f"• {g.fecha.strftime('%d/%m/%Y')} - {g.turno} - Recreo {g.recreo} - {zona_nombre}\n"  # noqa: E501

                    if len(guardias) > 10:
                        texto += f"\n... y {len(guardias) - 10} más"

                    self.preview_text.setPlainText(texto)

        except Exception as e:
            logger.error(f"Error al obtener preview: {str(e)}")
            self.preview_text.setPlainText(f"Error al cargar guardias: {str(e)}")

    def mostrar_guardias_afectadas(self):
        """Muestra diálogo con guardias afectadas y opción de reasignación."""
        if not self.ausencia_actual:
            QMessageBox.warning(
                self, "Error", "Primero debes seleccionar o guardar una ausencia"
            )
            return

        try:
            with SessionLocal() as session:
                guardias = obtener_guardias_afectadas(session, self.ausencia_actual)

                if not guardias:
                    QMessageBox.information(
                        self, "Sin guardias", "No hay guardias afectadas por esta ausencia"
                    )
                    return

                # Crear diálogo de reasignación
                dialogo = DialogoReasignacion(guardias, self.ausencia_actual, self)
                dialogo.exec()

                # Actualizar tabla si hubo cambios
                self.cargar_ausencias()

        except Exception as e:
            logger.error(f"Error al mostrar guardias afectadas: {str(e)}")
            QMessageBox.critical(
                self, "Error", f"Error al cargar guardias afectadas:\n{str(e)}"
            )

    def limpiar_formulario(self):
        """Limpia el formulario y resetea el modo de edición."""
        self.ausencia_actual = None
        self.titulo_form.setText("✏️ NUEVA AUSENCIA")
        self.profesor_combo.setCurrentIndex(-1)
        self.tipo_combo.setCurrentIndex(0)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.motivo_input.clear()
        self.preview_text.clear()
        self.ver_guardias_btn.setEnabled(False)
        logger.info("Formulario limpiado")


class DialogoReasignacion(QDialog):
    """Diálogo para reasignar guardias afectadas por una ausencia."""

    def __init__(self, guardias, ausencia_id, parent=None):
        super().__init__(parent)
        self.guardias = guardias
        self.ausencia_id = ausencia_id
        self.setWindowTitle("Reasignación de Guardias")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel(f"📊 Guardias Afectadas ({len(self.guardias)} guardias)")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(titulo)

        # Tabla de guardias
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Turno", "Recreo", "Zona", "Profesor Actual"]
        )
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.setColumnWidth(0, 50)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 80)
        self.tabla.setColumnWidth(3, 80)
        self.tabla.setColumnWidth(4, 150)
        self.tabla.setColumnWidth(5, 200)

        for i, guardia in enumerate(self.guardias):
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(str(guardia.id)))
            self.tabla.setItem(i, 1, QTableWidgetItem(guardia.fecha.strftime("%d/%m/%Y")))
            self.tabla.setItem(i, 2, QTableWidgetItem(guardia.turno))
            self.tabla.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
            zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"
            self.tabla.setItem(i, 4, QTableWidgetItem(zona_nombre))
            profesor_nombre = guardia.profesor.nombre_completo if guardia.profesor else "N/A"
            self.tabla.setItem(i, 5, QTableWidgetItem(profesor_nombre))

        layout.addWidget(self.tabla)

        # Botones de acción
        botones = QHBoxLayout()

        btn_reasignar_auto = QPushButton("🤖 Reasignar Automáticamente")
        btn_reasignar_auto.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        btn_reasignar_auto.clicked.connect(self.reasignar_automaticamente)
        botones.addWidget(btn_reasignar_auto)

        btn_reasignar_manual = QPushButton("👤 Reasignar Seleccionada")
        btn_reasignar_manual.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        btn_reasignar_manual.clicked.connect(self.reasignar_manual)
        botones.addWidget(btn_reasignar_manual)

        btn_cerrar = QPushButton("❌ Cerrar")
        btn_cerrar.setStyleSheet(styles.STYLE_BUTTON_SECONDARY)
        btn_cerrar.clicked.connect(self.close)
        botones.addWidget(btn_cerrar)

        layout.addLayout(botones)

    def reasignar_automaticamente(self):
        """Reasigna todas las guardias automáticamente."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar reasignación",
            f"¿Reasignar automáticamente {len(self.guardias)} guardias?\n"
            "El sistema buscará los mejores sustitutos disponibles.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                with SessionLocal() as session:
                    resultados = reasignar_guardias_automaticamente(session, self.guardias)

                mensaje = (
                    f"Reasignación completada:\n\n"
                    f"✅ Reasignadas: {resultados['reasignadas']}\n"
                    f"❌ Fallidas: {resultados['fallidas']}"
                )

                if resultados["fallidas"] > 0:
                    mensaje += "\n\nVer detalles en el log para más información."

                QMessageBox.information(self, "Resultado", mensaje)

                if resultados["reasignadas"] > 0:
                    self.close()

            except Exception as e:
                logger.error(f"Error en reasignación automática: {str(e)}")
                QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")

    def reasignar_manual(self):
        """Permite seleccionar manualmente un sustituto para la guardia seleccionada."""
        selected_rows = self.tabla.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Por favor selecciona una guardia")
            return

        row = selected_rows[0].row()
        guardia_id = int(self.tabla.item(row, 0).text())

        # Encontrar la guardia
        guardia = next((g for g in self.guardias if g.id == guardia_id), None)
        if not guardia:
            return

        # Obtener profesores disponibles
        with SessionLocal() as session:
            disponibles = obtener_profesores_disponibles(
                session,
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

            # Mostrar diálogo de selección
            nombres = [f"{p.nombre_completo} ({count} guardias hoy)" for p, count in disponibles]

            from PyQt6.QtWidgets import QInputDialog

            nombre_seleccionado, ok = QInputDialog.getItem(
                self, "Seleccionar Sustituto", "Profesor:", nombres, 0, False
            )

            if ok and nombre_seleccionado:
                # Obtener el profesor seleccionado
                index = nombres.index(nombre_seleccionado)
                nuevo_profesor, _ = disponibles[index]

                try:
                    reasignar_guardia(session, guardia_id, nuevo_profesor.id)
                    QMessageBox.information(
                        self,
                        "Éxito",
                        f"Guardia reasignada a {nuevo_profesor.nombre_completo}",
                    )
                    self.close()
                except Exception as e:
                    logger.error(f"Error al reasignar: {str(e)}")
                    QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")
