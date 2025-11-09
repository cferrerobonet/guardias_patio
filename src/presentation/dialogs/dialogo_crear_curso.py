"""
Diálogo para crear un nuevo curso escolar.

Permite al usuario configurar un curso y opcionalmente copiar profesores.
"""

from datetime import date
from typing import Optional

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
from sqlalchemy.orm import Session

from core.logging import get_logger
from services.gestor_cursos import GestorCursos

logger = get_logger(__name__)


class DialogoCrearCurso(QDialog):
    """Diálogo para crear un nuevo curso escolar."""

    def __init__(self, session: Session, parent: Optional[QDialog] = None):
        super().__init__(parent)
        self.session = session
        self.curso_creado_id: Optional[int] = None
        self._inicializar_ui()

    def _inicializar_ui(self) -> None:
        """Crea la interfaz del diálogo."""
        self.setWindowTitle("Crear Nuevo Curso Escolar")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

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

        # Preview del curso
        self.label_preview = QLabel()
        self._actualizar_preview()
        form_layout.addRow("Nombre del curso:", self.label_preview)

        # Fechas automáticas
        self.label_fechas = QLabel()
        self._actualizar_fechas_preview()
        form_layout.addRow("Rango de fechas:", self.label_fechas)

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
        self.check_copiar_profesores.setChecked(True)
        self.check_copiar_profesores.setToolTip(
            "Copia los datos básicos de los profesores (sin guardias)"
        )
        opciones_layout.addWidget(self.check_copiar_profesores)

        grupo_opciones.setLayout(opciones_layout)
        layout.addWidget(grupo_opciones)

        # Botones
        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        botones.accepted.connect(self._crear_curso)
        botones.rejected.connect(self.reject)
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
        copiar_profesores = self.check_copiar_profesores.isChecked()

        try:
            # Confirmar creación
            mensaje = f"¿Crear el curso {anio_inicio}/{anio_inicio + 1}?\n\n"
            if activar:
                mensaje += "✓ Se activará automáticamente\n"
            if copiar_profesores:
                mensaje += "✓ Se copiarán los profesores del curso anterior\n"

            respuesta = QMessageBox.question(
                self,
                "Confirmar Creación",
                mensaje,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta != QMessageBox.StandardButton.Yes:
                return

            # Crear curso
            logger.info(
                f"Creando curso {anio_inicio}/{anio_inicio + 1} "
                f"(activar={activar}, copiar={copiar_profesores})"
            )

            curso = GestorCursos.crear_nuevo_curso(
                session=self.session,
                anio_inicio=anio_inicio,
                activar=activar,
                copiar_profesores=copiar_profesores,
            )

            self.curso_creado_id = curso.id

            # Mensaje de éxito
            mensaje_exito = f"✅ Curso {curso.nombre} creado correctamente"
            if activar:
                mensaje_exito += "\n\nAhora estás trabajando con este curso."

            QMessageBox.information(
                self,
                "Curso Creado",
                mensaje_exito,
            )

            self.accept()

        except ValueError as e:
            # Error de validación (ej: curso ya existe)
            logger.warning(f"Error al crear curso: {e}")
            QMessageBox.warning(
                self,
                "Error de Validación",
                str(e),
            )
        except Exception as e:
            # Error inesperado
            logger.error(f"Error inesperado al crear curso: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Error",
                f"No se pudo crear el curso:\n{e}",
            )

    def obtener_curso_creado_id(self) -> Optional[int]:
        """
        Obtiene el ID del curso creado.

        Returns:
            ID del curso o None si no se creó
        """
        return self.curso_creado_id
