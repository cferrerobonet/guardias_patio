"""
Widget de gestión de cursos escolares para la sección de Configuración.

Permite visualizar todos los cursos y realizar operaciones de gestión.
"""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
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

from src.core.logging import logger
from src.models.models import CursoEscolar, Guardia
from src.presentation.dialogs.dialogo_crear_curso import DialogoCrearCurso
from src.services.gestor_cursos import GestorCursos


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

        # Título
        titulo = QLabel("Gestión de Cursos Escolares")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Administra los cursos escolares. Cada curso es independiente "
            "y tiene sus propias guardias y datos."
        )
        descripcion.setWordWrap(True)
        layout.addWidget(descripcion)

        # Botones de acción
        botones_layout = QHBoxLayout()

        self.btn_crear = QPushButton("➕ Crear Nuevo Curso")
        self.btn_crear.clicked.connect(self._crear_curso)
        botones_layout.addWidget(self.btn_crear)

        self.btn_activar = QPushButton("⭐ Activar Curso")
        self.btn_activar.clicked.connect(self._activar_curso_seleccionado)
        self.btn_activar.setEnabled(False)
        botones_layout.addWidget(self.btn_activar)

        self.btn_cerrar = QPushButton("🔒 Cerrar Curso")
        self.btn_cerrar.clicked.connect(self._cerrar_curso_seleccionado)
        self.btn_cerrar.setEnabled(False)
        botones_layout.addWidget(self.btn_cerrar)

        self.btn_reabrir = QPushButton("🔓 Reabrir Curso")
        self.btn_reabrir.clicked.connect(self._reabrir_curso_seleccionado)
        self.btn_reabrir.setEnabled(False)
        botones_layout.addWidget(self.btn_reabrir)

        self.btn_eliminar = QPushButton("🗑️ Eliminar Curso")
        self.btn_eliminar.clicked.connect(self._eliminar_curso_seleccionado)
        self.btn_eliminar.setEnabled(False)
        self.btn_eliminar.setStyleSheet("QPushButton { color: red; }")
        botones_layout.addWidget(self.btn_eliminar)

        botones_layout.addStretch()
        layout.addLayout(botones_layout)

        # Tabla de cursos
        self.tabla_cursos = QTableWidget()
        self.tabla_cursos.setColumnCount(6)
        self.tabla_cursos.setHorizontalHeaderLabels(
            ["Curso", "Fecha Inicio", "Fecha Fin", "Estado", "Guardias", "Creado"]
        )
        self.tabla_cursos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_cursos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_cursos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_cursos.itemSelectionChanged.connect(self._on_seleccion_cambiada)
        layout.addWidget(self.tabla_cursos)

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
            self.btn_reabrir.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            return

        # Obtener curso seleccionado
        curso_id = items[0].data(Qt.ItemDataRole.UserRole)
        curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

        if curso:
            # Activar: solo si no está activo y no está cerrado
            self.btn_activar.setEnabled(not curso.activo and not curso.cerrado)

            # Cerrar: solo si no está cerrado
            self.btn_cerrar.setEnabled(not curso.cerrado)

            # Reabrir: solo si está cerrado
            self.btn_reabrir.setEnabled(curso.cerrado)

            # Eliminar: solo si no está activo
            self.btn_eliminar.setEnabled(not curso.activo)

    def _crear_curso(self) -> None:
        """Abre el diálogo de creación de curso."""
        dialogo = DialogoCrearCurso(self.session, self)
        if dialogo.exec():
            self._cargar_cursos()
            self.curso_modificado.emit()

    def _activar_curso_seleccionado(self) -> None:
        """Activa el curso seleccionado."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

            respuesta = QMessageBox.question(
                self,
                "Activar Curso",
                f"¿Activar el curso {curso.nombre}?\n\nEl curso activo actual se desactivará.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
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

    def _reabrir_curso_seleccionado(self) -> None:
        """Reabre un curso previamente cerrado."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()

            respuesta = QMessageBox.question(
                self,
                "Reabrir Curso",
                f"¿Reabrir el curso {curso.nombre}?\n\n"
                "El curso volverá a estar disponible para modificaciones.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                GestorCursos.reabrir_curso(self.session, curso_id)
                QMessageBox.information(
                    self, "Curso Reabierto", f"El curso {curso.nombre} ha sido reabierto."
                )
                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al reabrir curso: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo reabrir el curso:\n{e}")

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
            respuesta1 = QMessageBox.warning(
                self,
                "⚠️ Eliminar Curso",
                f"¿ELIMINAR el curso {curso.nombre}?\n\n"
                f"⚠️ Esta acción eliminará:\n"
                f"   • {num_guardias} guardias asignadas\n"
                f"   • Todos los datos asociados al curso\n\n"
                "Esta acción NO se puede deshacer.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if respuesta1 != QMessageBox.StandardButton.Yes:
                return

            # Segunda confirmación
            respuesta2 = QMessageBox.critical(
                self,
                "⚠️ CONFIRMACIÓN FINAL",
                f"¿Estás COMPLETAMENTE SEGURO de eliminar {curso.nombre}?\n\n"
                "Se perderán todos los datos permanentemente.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )

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
