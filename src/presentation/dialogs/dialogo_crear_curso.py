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

from core.logging import get_logger
from services.gestor_cursos import GestorCursos

logger = get_logger(__name__)


class DialogoCrearCurso(QDialog):
    """Diálogo para crear un nuevo curso escolar."""

    def __init__(self, session, parent: Optional[QDialog] = None):
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

        self.check_copiar_profesores = QCheckBox("Copiar el claustro del curso anterior")
        self.check_copiar_profesores.setChecked(True)
        self.check_copiar_profesores.setToolTip(
            "Trae los profesores del último curso con sus horas, turno, zona preferida\n"
            "y restricciones de días y recreos. Después podrás dar de baja a quien no siga."
        )
        opciones_layout.addWidget(self.check_copiar_profesores)

        self.check_trasladar_festivos = QCheckBox(
            "Trasladar los días no lectivos del curso anterior"
        )
        self.check_trasladar_festivos.setChecked(True)
        self.check_trasladar_festivos.setToolTip(
            "Desplaza un año las fechas que marcaste a mano. Las de fecha fija caen\n"
            "donde deben; las que dependían del día de la semana hay que revisarlas\n"
            "en Ajustes."
        )
        opciones_layout.addWidget(self.check_trasladar_festivos)

        nota = QLabel(
            "Las zonas, los recreos y los ajustes de reparto son comunes a toda la "
            "aplicación: el curso nuevo los hereda sin copiar nada."
        )
        nota.setWordWrap(True)
        opciones_layout.addWidget(nota)

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
                mensaje += "· Se activará automáticamente\n"
            if self.check_copiar_profesores.isChecked():
                mensaje += "· Se copiará el claustro del curso anterior\n"
            if self.check_trasladar_festivos.isChecked():
                mensaje += "· Se trasladarán los días no lectivos marcados a mano\n"

            msg_box.setText(mensaje)
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

            # FORZAR tamaño fijo para que se vean los botones en macOS
            respuesta = msg_box.exec()

            if respuesta != QMessageBox.StandardButton.Yes:
                logger.info("Creación de curso cancelada por el usuario")
                return

            logger.info("Usuario confirmó creación, llamando a GestorCursos...")

            # Crear curso SIN activar para evitar problemas de transacción
            # Lo activaremos después si es necesario
            gestor = GestorCursos.from_session(self.session)
            curso = gestor.crear_nuevo_curso(
                anio_inicio=anio_inicio,
                activar=False,  # SIEMPRE False primero
                copiar_profesores=False,  # se hace abajo, para poder informar del resultado
            )

            logger.info(f"Curso creado exitosamente: {curso.nombre} (ID: {curso.id})")
            self.curso_creado_id = curso.id

            resumen = gestor.preparar_curso_nuevo(
                curso.id,
                copiar_profesores=self.check_copiar_profesores.isChecked(),
                trasladar_no_lectivos=self.check_trasladar_festivos.isChecked(),
            )

            # Si se solicitó activar, hacerlo en un paso separado
            if activar:
                logger.info(f"Activando curso {curso.id}...")
                gestor.activar_curso(curso.id)
                logger.info("Curso activado correctamente")

            texto = f"Curso {curso.nombre} creado"
            if activar:
                texto += " y activado"
            texto += self._resumen_de_lo_heredado(resumen)
            from presentation.widgets.toast_notification import ToastNotification
            ToastNotification(self.window(), texto, "success")
            self.accept()

        except ValueError as e:
            # Error de validación (ej: curso ya existe)
            logger.warning(f"Error de validación al crear curso: {e}")
            msg_warning = QMessageBox(self)
            msg_warning.setIcon(QMessageBox.Icon.Warning)
            msg_warning.setWindowTitle("Error de Validación")
            msg_warning.setText(str(e))
            msg_warning.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_warning.exec()
        except (ValueError, TypeError) as e:
            # Error inesperado
            logger.error(f"Error inesperado al crear curso: {type(e).__name__}: {e}", exc_info=True)
            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo crear el curso:\n{type(e).__name__}: {e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.exec()

    @staticmethod
    def _resumen_de_lo_heredado(resumen: dict) -> str:
        """Frase con lo que se ha traído del curso anterior, para el aviso final."""
        partes = []
        if resumen.get("profesores"):
            partes.append(f"{resumen['profesores']} profesores")
        if resumen.get("trasladados"):
            partes.append(f"{resumen['trasladados']} días no lectivos")
        if not partes:
            return ""
        return " con " + " y ".join(partes) + " del curso anterior"

    def obtener_curso_creado_id(self) -> Optional[int]:
        """
        Obtiene el ID del curso creado.

        Returns:
            ID del curso o None si no se creó
        """
        return self.curso_creado_id
