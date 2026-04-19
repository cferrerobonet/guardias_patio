"""
Diálogo para crear un nuevo curso escolar.

Permite al usuario configurar un curso y opcionalmente copiar profesores.
"""

from datetime import date
from typing import Optional

from core.logging import get_logger
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)
from services.gestor_cursos import GestorCursos
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class DialogoCrearCurso(QDialog):
    """Diálogo para crear un nuevo curso escolar."""

    def __init__(self, session: Session, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.session = session  # Guardamos referencia pero usaremos una nueva sesión
        self.curso_creado_id: Optional[int] = None
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Crea la interfaz del diálogo."""
        self.setWindowTitle("Crear Nuevo Curso Escolar")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)  # Asegurar altura suficiente para ver todo

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Información
        info_label = QLabel(
            "Crea un nuevo curso escolar para trabajar con datos independientes.\n"
            "Los cursos te permiten preparar el año siguiente sin perder el actual."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Grupo de configuración del curso
        grupo_curso = QGroupBox("Datos del Curso")
        form_layout = QFormLayout()

        # Año de inicio
        self.spin_anio_inicio = QSpinBox()
        self.spin_anio_inicio.setRange(2020, 2050)
        self.spin_anio_inicio.setValue(date.today().year)
        self.spin_anio_inicio.valueChanged.connect(self._actualizar_preview)
        form_layout.addRow("Año de inicio:", self.spin_anio_inicio)

        # Preview del curso - Crear los labels ANTES de actualizar
        self.label_preview = QLabel()
        form_layout.addRow("Nombre del curso:", self.label_preview)

        # Fechas automáticas - Crear el label ANTES de actualizar
        self.label_fechas = QLabel()
        form_layout.addRow("Rango de fechas:", self.label_fechas)

        # Ahora SÍ actualizar los previews (después de crear los widgets)
        self._actualizar_preview()

        grupo_curso.setLayout(form_layout)
        layout.addWidget(grupo_curso)

        # Grupo de opciones avanzadas
        grupo_opciones = QGroupBox("Opciones Avanzadas")
        opciones_layout = QVBoxLayout()

        self.check_activar = QCheckBox("Activar este curso automáticamente al crearlo")
        self.check_activar.setChecked(True)
        self.check_activar.setToolTip(
            "Si está marcado, cambiarás inmediatamente a trabajar con este curso"
        )
        opciones_layout.addWidget(self.check_activar)

        self.check_copiar_profesores = QCheckBox("Copiar profesores del curso anterior")
        self.check_copiar_profesores.setChecked(False)
        self.check_copiar_profesores.setEnabled(False)  # Deshabilitado temporalmente
        self.check_copiar_profesores.setToolTip(
            "⚠️ Función deshabilitada temporalmente.\n"
            "Los profesores aún no tienen relación con cursos específicos.\n"
            "Debes agregar/gestionar los profesores manualmente para cada curso."
        )
        opciones_layout.addWidget(self.check_copiar_profesores)

        grupo_opciones.setLayout(opciones_layout)
        layout.addWidget(grupo_opciones)

        # Spacer para empujar botones hacia abajo
        layout.addStretch()

        # Botones - Asegurar que sean visibles
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._crear_curso)
        botones.rejected.connect(self.reject)

        # Forzar tamaño mínimo de los botones
        botones.setMinimumHeight(50)

        layout.addWidget(botones)

    def _actualizar_preview(self) -> None:
        """Actualiza el preview del nombre del curso."""
        anio_inicio = self.spin_anio_inicio.value()
        anio_fin = anio_inicio + 1
        self.label_preview.setText(f"Curso {anio_inicio}/{anio_fin}")
        self._actualizar_fechas_preview()

    def _actualizar_fechas_preview(self) -> None:
        """Actualiza el preview de las fechas del curso."""
        anio_inicio = self.spin_anio_inicio.value()
        anio_fin = anio_inicio + 1
        self.label_fechas.setText(f"01/09/{anio_inicio} - 30/06/{anio_fin}")

    def _crear_curso(self) -> None:
        """Crea el curso con los datos introducidos."""
        anio_inicio = self.spin_anio_inicio.value()
        activar = self.check_activar.isChecked()

        try:
            logger.info(f"Iniciando creación de curso {anio_inicio}/{anio_inicio + 1}")

            # Confirmar creación con QMessageBox explícito para control de tamaño
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Confirmar Creación")

            mensaje = f"¿Crear el curso {anio_inicio}/{anio_inicio + 1}?\n\n"
            if activar:
                mensaje += "✓ Se activará automáticamente\n"

            msg_box.setText(mensaje)
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

            # FORZAR tamaño fijo para que se vean los botones en macOS
            msg_box.setFixedSize(450, 220)

            respuesta = msg_box.exec()

            if respuesta != QMessageBox.StandardButton.Yes:
                logger.info("Creación de curso cancelada por el usuario")
                return

            logger.info("Usuario confirmó creación, llamando a GestorCursos...")

            # Crear curso SIN activar para evitar problemas de transacción
            # Lo activaremos después si es necesario
            curso = GestorCursos.crear_nuevo_curso(
                session=self.session,
                anio_inicio=anio_inicio,
                activar=False,  # SIEMPRE False primero
                copiar_profesores=False,  # Deshabilitado
            )

            logger.info(f"Curso creado exitosamente: {curso.nombre} (ID: {curso.id})")
            self.curso_creado_id = curso.id

            # Si se solicitó activar, hacerlo en un paso separado
            if activar:
                logger.info(f"Activando curso {curso.id}...")
                GestorCursos.activar_curso(self.session, curso.id)
                logger.info("Curso activado correctamente")

            # Mensaje de éxito
            msg_success = QMessageBox(self)
            msg_success.setIcon(QMessageBox.Icon.Information)
            msg_success.setWindowTitle("Curso Creado")

            mensaje_exito = f"✅ Curso {curso.nombre} creado correctamente"
            if activar:
                mensaje_exito += "\n\nAhora estás trabajando con este curso."

            msg_success.setText(mensaje_exito)
            msg_success.setStandardButtons(QMessageBox.StandardButton.Ok)

            # FORZAR tamaño fijo para que se vean los botones en macOS
            msg_success.setFixedSize(450, 200)

            msg_success.exec()

            self.accept()

        except ValueError as e:
            # Error de validación (ej: curso ya existe)
            logger.warning(f"Error de validación al crear curso: {e}")
            msg_warning = QMessageBox(self)
            msg_warning.setIcon(QMessageBox.Icon.Warning)
            msg_warning.setWindowTitle("Error de Validación")
            msg_warning.setText(str(e))
            msg_warning.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_warning.setFixedSize(450, 200)
            msg_warning.exec()
        except (ValueError, TypeError) as e:
            # Error inesperado
            logger.error(f"Error inesperado al crear curso: {type(e).__name__}: {e}", exc_info=True)
            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo crear el curso:\n{type(e).__name__}: {e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.setFixedSize(450, 220)
            msg_error.exec()

    def obtener_curso_creado_id(self) -> Optional[int]:
        """
        Obtiene el ID del curso creado.

        Returns:
            ID del curso o None si no se creó
        """
        return self.curso_creado_id
