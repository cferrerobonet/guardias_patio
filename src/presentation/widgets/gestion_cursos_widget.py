"""
Widget de gestión de cursos escolares para la sección de Configuración.

Permite visualizar todos los cursos y realizar operaciones de gestión.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

import ui_styles as styles
from core.logging import get_logger
from models.models import CursoEscolar, Guardia
from presentation.dialogs.dialogo_crear_curso import DialogoCrearCurso
from services.gestor_cursos import GestorCursos

logger = get_logger(__name__)


class GestionCursosWidget(QWidget):
    """Widget para gestionar cursos escolares."""

    curso_modificado = pyqtSignal()  # Emitido cuando cambia algún curso

    def __init__(self, session: Session, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self._inicializar_ui()
        self._cargar_cursos()

    def _inicializar_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # GroupBox con estilo - Se expandirá verticalmente
        grupo = QGroupBox("📚 Gestión de Cursos Escolares")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        grupo_layout = QVBoxLayout()
        grupo_layout.setSpacing(12)
        grupo_layout.setContentsMargins(20, 20, 20, 20)

        # Descripción
        descripcion = QLabel(
            "Administra los cursos escolares. Cada curso es independiente "
            "y tiene sus propias guardias y datos."
        )
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        grupo_layout.addWidget(descripcion)

        # Botones de acción con estilos consistentes
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        self.btn_crear = QPushButton("➕ Crear Nuevo Curso")
        self.btn_crear.setStyleSheet(
            styles.STYLE_BUTTON_SUCCESS + "font-size: 12px; padding: 8px 16px; font-weight: bold;"
        )
        self.btn_crear.setToolTip("Crear un nuevo curso escolar")
        self.btn_crear.clicked.connect(self._crear_curso)
        botones_layout.addWidget(self.btn_crear)

        self.btn_activar = QPushButton("⭐ Activar")
        self.btn_activar.setStyleSheet(
            styles.STYLE_BUTTON_PRIMARY + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_activar.setToolTip("Activar el curso seleccionado (incluso si está cerrado)")
        self.btn_activar.clicked.connect(self._activar_curso_seleccionado)
        self.btn_activar.setEnabled(False)
        botones_layout.addWidget(self.btn_activar)

        self.btn_cerrar = QPushButton("🔒 Cerrar")
        self.btn_cerrar.setStyleSheet(
            styles.STYLE_BUTTON_WARNING + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_cerrar.setToolTip("Cerrar el curso seleccionado (no se podrán añadir más guardias)")
        self.btn_cerrar.clicked.connect(self._cerrar_curso_seleccionado)
        self.btn_cerrar.setEnabled(False)
        botones_layout.addWidget(self.btn_cerrar)

        self.btn_eliminar = QPushButton("🗑️ Eliminar")
        self.btn_eliminar.setStyleSheet(
            styles.STYLE_BUTTON_DANGER + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_eliminar.setToolTip("Eliminar el curso seleccionado y todas sus guardias")
        self.btn_eliminar.clicked.connect(self._eliminar_curso_seleccionado)
        self.btn_eliminar.setEnabled(False)
        botones_layout.addWidget(self.btn_eliminar)

        botones_layout.addStretch()
        grupo_layout.addLayout(botones_layout)

        # Espaciado entre botones y tabla
        grupo_layout.addSpacing(15)

        # Tabla de cursos con scroll automático
        self.tabla_cursos = QTableWidget()
        self.tabla_cursos.setColumnCount(6)
        self.tabla_cursos.setHorizontalHeaderLabels(
            ["Curso", "Fecha Inicio", "Fecha Fin", "Estado", "Guardias", "Creado"]
        )

        # Ajustar columnas
        header = self.tabla_cursos.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Curso
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Fecha Inicio
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Fecha Fin
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Estado
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Guardias
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Creado

        self.tabla_cursos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_cursos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_cursos.setAlternatingRowColors(True)

        # Eliminar altura mínima fija para que sea flexible
        # El scroll aparecerá automáticamente cuando haya muchas filas
        self.tabla_cursos.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_cursos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.tabla_cursos.itemSelectionChanged.connect(self._on_seleccion_cambiada)

        # Añadir tabla con stretch=1 para que ocupe el espacio disponible
        grupo_layout.addWidget(self.tabla_cursos, 1)

        grupo.setLayout(grupo_layout)

        # Añadir GroupBox con stretch=1 para que se expanda verticalmente
        layout.addWidget(grupo, 1)

    def _cargar_cursos(self) -> None:
        """Carga todos los cursos en la tabla."""
        try:
            cursos = GestorCursos.listar_todos_cursos(self.session, incluir_cerrados=True)

            self.tabla_cursos.setRowCount(len(cursos))

            for i, curso in enumerate(cursos):
                # Nombre del curso
                item_nombre = QTableWidgetItem(curso.nombre)
                item_nombre.setData(Qt.ItemDataRole.UserRole, curso.id)

                # Resaltar curso activo
                if curso.activo:
                    item_nombre.setBackground(Qt.GlobalColor.yellow)
                    item_nombre.setText(f"⭐ {curso.nombre}")

                self.tabla_cursos.setItem(i, 0, item_nombre)

                # Fecha inicio
                self.tabla_cursos.setItem(
                    i, 1, QTableWidgetItem(curso.fecha_inicio.strftime("%d/%m/%Y"))
                )

                # Fecha fin
                self.tabla_cursos.setItem(
                    i, 2, QTableWidgetItem(curso.fecha_fin.strftime("%d/%m/%Y"))
                )

                # Estado
                estado = []
                if curso.activo:
                    estado.append("Activo")
                if curso.cerrado:
                    estado.append("Cerrado")
                if not curso.activo and not curso.cerrado:
                    estado.append("Inactivo")

                self.tabla_cursos.setItem(i, 3, QTableWidgetItem(" | ".join(estado)))

                # Número de guardias
                num_guardias = self.session.query(Guardia).filter_by(curso_id=curso.id).count()
                self.tabla_cursos.setItem(i, 4, QTableWidgetItem(str(num_guardias)))

                # Fecha creación
                self.tabla_cursos.setItem(
                    i, 5, QTableWidgetItem(curso.created_at.strftime("%d/%m/%Y %H:%M"))
                )

            logger.info(f"Cargados {len(cursos)} cursos en tabla de gestión")

        except Exception as e:
            logger.error(f"Error al cargar cursos: {e}")
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los cursos:\n{e}")

    def _on_seleccion_cambiada(self) -> None:
        """Actualiza el estado de los botones según la selección."""
        items = self.tabla_cursos.selectedItems()
        hay_seleccion = len(items) > 0

        if not hay_seleccion:
            self.btn_activar.setEnabled(False)
            self.btn_cerrar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            return

        # Obtener curso seleccionado
        curso_id = items[0].data(Qt.ItemDataRole.UserRole)
        curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

        if curso:
            # Activar: solo si no está activo (puede estar cerrado o no)
            # El botón "Activar" también reabre cursos cerrados
            self.btn_activar.setEnabled(not curso.activo)

            # Cerrar: solo si no está cerrado y está activo
            self.btn_cerrar.setEnabled(not curso.cerrado and curso.activo)

            # Eliminar: solo si no está activo
            self.btn_eliminar.setEnabled(not curso.activo)

    def _crear_curso(self) -> None:
        """Abre el diálogo de creación de curso."""
        dialogo = DialogoCrearCurso(self.session, self)
        if dialogo.exec():
            self._cargar_cursos()
            self.curso_modificado.emit()

    def _activar_curso_seleccionado(self) -> None:
        """Activa el curso seleccionado (incluso si está cerrado)."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

            # Mensaje diferente si el curso está cerrado
            if curso.cerrado:
                mensaje = (
                    f"¿Activar el curso {curso.nombre}?\n\n"
                    "Este curso está cerrado. Se reabrirá automáticamente.\n"
                    "El curso activo actual se desactivará."
                )
            else:
                mensaje = (
                    f"¿Activar el curso {curso.nombre}?\n\n"
                    "El curso activo actual se desactivará."
                )

            respuesta = QMessageBox.question(
                self,
                "Activar Curso",
                mensaje,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Si está cerrado, reabrirlo primero
                if curso.cerrado:
                    GestorCursos.reabrir_curso(self.session, curso_id)

                # Luego activarlo
                GestorCursos.activar_curso(self.session, curso_id)

                QMessageBox.information(
                    self, "Curso Activado", f"El curso {curso.nombre} está ahora activo."
                )
                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al activar curso: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo activar el curso:\n{e}")

    def _cerrar_curso_seleccionado(self) -> None:
        """Cierra el curso seleccionado."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

            respuesta = QMessageBox.question(
                self,
                "Cerrar Curso",
                f"¿Cerrar el curso {curso.nombre}?\n\n"
                "Un curso cerrado no se puede modificar ni activar.\n"
                "Podrás reabrirlo más tarde si es necesario.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                GestorCursos.cerrar_curso(self.session, curso_id)
                QMessageBox.information(
                    self, "Curso Cerrado", f"El curso {curso.nombre} ha sido cerrado."
                )
                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al cerrar curso: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo cerrar el curso:\n{e}")

    def _eliminar_curso_seleccionado(self) -> None:
        """Elimina el curso seleccionado (con confirmación fuerte)."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

            # Contar guardias
            num_guardias = self.session.query(Guardia).filter_by(curso_id=curso_id).count()

            # Confirmación doble
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("⚠️ Eliminar Curso")
            msg_box.setText(f"¿ELIMINAR el curso {curso.nombre}?")
            msg_box.setInformativeText(
                f"⚠️ Esta acción eliminará:\n"
                f"   • {num_guardias} guardias asignadas\n"
                f"   • Todos los datos asociados al curso\n\n"
                "Esta acción NO se puede deshacer."
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            # Ajustar tamaño mínimo para que se vean los botones
            msg_box.setMinimumWidth(500)
            msg_box.setMinimumHeight(250)

            respuesta1 = msg_box.exec()

            if respuesta1 != QMessageBox.StandardButton.Yes:
                return

            # Segunda confirmación
            msg_box2 = QMessageBox(self)
            msg_box2.setIcon(QMessageBox.Icon.Critical)
            msg_box2.setWindowTitle("⚠️ CONFIRMACIÓN FINAL")
            msg_box2.setText(f"¿Estás COMPLETAMENTE SEGURO de eliminar {curso.nombre}?")
            msg_box2.setInformativeText("Se perderán todos los datos permanentemente.")
            msg_box2.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            )
            msg_box2.setDefaultButton(QMessageBox.StandardButton.Cancel)

            # Ajustar tamaño mínimo
            msg_box2.setMinimumWidth(450)
            msg_box2.setMinimumHeight(200)

            respuesta2 = msg_box2.exec()

            if respuesta2 == QMessageBox.StandardButton.Yes:
                # Eliminar curso (cascade eliminará guardias)
                self.session.delete(curso)
                self.session.commit()

                QMessageBox.information(
                    self, "Curso Eliminado", f"El curso {curso.nombre} ha sido eliminado."
                )
                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al eliminar curso: {e}")
            self.session.rollback()
            QMessageBox.critical(self, "Error", f"No se pudo eliminar el curso:\n{e}")

    def _obtener_curso_seleccionado_id(self) -> Optional[int]:
        """Obtiene el ID del curso seleccionado en la tabla."""
        items = self.tabla_cursos.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def refrescar(self) -> None:
        """Recarga la tabla de cursos."""
        self._cargar_cursos()
