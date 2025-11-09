"""
Widget selector de curso escolar para la barra de herramientas.

Permite cambiar entre cursos escolares de forma rápida desde la UI principal.
"""

from typing import Optional

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QWidget
from sqlalchemy.orm import Session

from core.logging import get_logger
from models.models import CursoEscolar
from services.gestor_cursos import GestorCursos

logger = get_logger(__name__)


class SelectorCursoWidget(QWidget):
    """
    Widget para seleccionar el curso escolar activo.

    Emite señal cuando el usuario cambia de curso.
    """

    curso_cambiado = pyqtSignal(int)  # Emite el ID del nuevo curso activo

    def __init__(self, session: Session, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self._inicializar_ui()
        self._cargar_cursos()

    def _inicializar_ui(self) -> None:
        """Crea los widgets de la interfaz."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        label = QLabel("Curso Escolar:")
        layout.addWidget(label)

        # ComboBox
        self.combo_cursos = QComboBox()
        self.combo_cursos.setMinimumWidth(200)
        self.combo_cursos.currentIndexChanged.connect(self._on_curso_seleccionado)
        layout.addWidget(self.combo_cursos)

    def _cargar_cursos(self) -> None:
        """Carga los cursos disponibles en el combo."""
        try:
            # Obtener todos los cursos (excluir cerrados)
            cursos = GestorCursos.listar_todos_cursos(self.session, incluir_cerrados=False)

            # Limpiar combo
            self.combo_cursos.blockSignals(True)
            self.combo_cursos.clear()

            # Añadir cursos
            curso_activo_idx = 0
            for i, curso in enumerate(cursos):
                # Mostrar nombre y estado
                texto = curso.nombre
                if curso.activo:
                    texto += " ⭐"
                    curso_activo_idx = i

                self.combo_cursos.addItem(texto, curso.id)

            # Seleccionar curso activo
            if cursos:
                self.combo_cursos.setCurrentIndex(curso_activo_idx)

            self.combo_cursos.blockSignals(False)

            logger.info(f"Cargados {len(cursos)} cursos en selector")

        except Exception as e:
            logger.error(f"Error al cargar cursos en selector: {e}")
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los cursos:\n{e}")

    def _on_curso_seleccionado(self, index: int) -> None:
        """Maneja el cambio de curso en el combo."""
        if index < 0:
            return

        curso_id = self.combo_cursos.itemData(index)

        try:
            # Confirmar cambio
            curso = self.session.query(CursoEscolar).filter_by(id=curso_id).first()
            if not curso:
                return

            respuesta = QMessageBox.question(
                self,
                "Cambiar Curso Escolar",
                f"¿Cambiar al curso {curso.nombre}?\n\n"
                "Las vistas se actualizarán para mostrar los datos de este curso.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Activar curso
                GestorCursos.activar_curso(self.session, curso_id)
                logger.info(f"Curso cambiado a: {curso.nombre}")

                # Actualizar UI
                self._cargar_cursos()

                # Emitir señal
                self.curso_cambiado.emit(curso_id)

                QMessageBox.information(
                    self, "Curso Cambiado", f"Ahora estás trabajando con el curso {curso.nombre}"
                )
            else:
                # Restaurar selección anterior
                self._cargar_cursos()

        except Exception as e:
            logger.error(f"Error al cambiar curso: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo cambiar de curso:\n{e}")
            self._cargar_cursos()

    def refrescar(self) -> None:
        """Recarga la lista de cursos."""
        self._cargar_cursos()

    def obtener_curso_activo_id(self) -> Optional[int]:
        """
        Obtiene el ID del curso actualmente seleccionado.

        Returns:
            ID del curso o None si no hay selección
        """
        index = self.combo_cursos.currentIndex()
        if index >= 0:
            return self.combo_cursos.itemData(index)
        return None
