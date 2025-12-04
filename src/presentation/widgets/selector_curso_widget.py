"""
Widget selector de curso escolar para la barra de herramientas.

Permite cambiar entre cursos escolares de forma rápida desde la UI principal.
"""

from typing import Optional

from core.logging import get_logger
from infrastructure.database.models import CursoEscolar
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QWidget
from services.gestor_cursos import GestorCursos
from sqlalchemy.orm import Session

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

        # Label (oculto para diseño limpio en sidebar)
        label = QLabel("Curso Escolar:")
        label.setVisible(False)
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
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"No se pudieron cargar los cursos:\n{e}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)
            msg_box.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            msg_box.setFixedSize(480, 220)
            msg_box.exec()

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

            msg_confirmar = QMessageBox(self)
            msg_confirmar.setIcon(QMessageBox.Icon.Question)
            msg_confirmar.setWindowTitle("Cambiar Curso Escolar")
            msg_confirmar.setText(
                f"¿Cambiar al curso {curso.nombre}?\n\n"
                "Las vistas se actualizarán para mostrar los datos de este curso."
            )
            msg_confirmar.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_confirmar.setDefaultButton(QMessageBox.StandardButton.No)
            msg_confirmar.setStyleSheet("""
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:default {
                    background-color: #e74c3c;
                }
                QPushButton:default:hover {
                    background-color: #c0392b;
                }
            """)
            msg_confirmar.setFixedSize(550, 320)
            respuesta = msg_confirmar.exec()

            if respuesta == QMessageBox.StandardButton.Yes:
                # Activar curso
                GestorCursos.activar_curso(self.session, curso_id)
                logger.info(f"Curso cambiado a: {curso.nombre}")

                # Actualizar UI - IMPORTANTE: bloquear señales durante recarga
                self.combo_cursos.blockSignals(True)
                self._cargar_cursos()
                self.combo_cursos.blockSignals(False)

                # Emitir señal DESPUÉS de actualizar UI
                logger.info(f"🔔 Emitiendo señal curso_cambiado con ID: {curso_id}")
                self.curso_cambiado.emit(curso_id)
                logger.info("✅ Señal curso_cambiado emitida correctamente")

                msg_success = QMessageBox(self)
                msg_success.setIcon(QMessageBox.Icon.Information)
                msg_success.setWindowTitle("Curso Cambiado")
                msg_success.setText(f"Ahora estás trabajando con el curso {curso.nombre}")
                msg_success.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_success.setDefaultButton(QMessageBox.StandardButton.Ok)
                msg_success.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        padding: 8px 16px;
                        border-radius: 4px;
                        font-weight: bold;
                        min-width: 80px;
                    }
                    QPushButton:hover {
                        background-color: #229954;
                    }
                """)
                msg_success.setFixedSize(480, 220)
                msg_success.exec()
            else:
                # Restaurar selección anterior
                self._cargar_cursos()

        except Exception as e:
            logger.error(f"Error al cambiar curso: {e}")
            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo cambiar de curso:\n{e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.setDefaultButton(QMessageBox.StandardButton.Ok)
            msg_error.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: bold;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            msg_error.setFixedSize(480, 220)
            msg_error.exec()
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
