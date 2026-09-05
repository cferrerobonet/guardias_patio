"""Vista de inicio: qué falta para poder generar las guardias.

La aplicación abría en Profesores, una rejilla sin contexto: nada indicaba por
dónde empezar ni por qué el botón de generar estaba apagado (UXF-001). Esta vista
pinta la lista de prerrequisitos calculada por `PreflightGeneracionUseCase` y
lleva de un clic a la pantalla que resuelve cada uno (FUN-001).
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from application.use_cases.preflight_generacion import PreflightGeneracionUseCase
from presentation.theme.tokens import FontSize, Spacing
from utils import get_logger

logger = get_logger(__name__)

#: Nombre legible de la sección de destino de cada requisito.
NOMBRE_DE_SECCION = {
    "ajustes": "Ajustes",
    "zonas": "Zonas",
    "profesores": "Profesores",
    "asignacion_calculo": "Cálculo y Asignación",
}


class EstadoCursoForm(QWidget):
    """Checklist de lo que hace falta antes de generar guardias."""

    #: Pide a la ventana principal que navegue a una sección.
    ir_a_seccion = pyqtSignal(str)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self._filas = []
        self._setup_ui()
        self.cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Spacing.LG, Spacing.LG, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)

        self.titulo = QLabel("Estado del curso")
        fuente = self.titulo.font()
        fuente.setPointSize(FontSize.TITLE)
        fuente.setBold(True)
        self.titulo.setFont(fuente)
        layout.addWidget(self.titulo)

        self.resumen = QLabel("")
        self.resumen.setWordWrap(True)
        layout.addWidget(self.resumen)

        self.contenedor = QVBoxLayout()
        self.contenedor.setSpacing(Spacing.SM)
        layout.addLayout(self.contenedor)

        self.boton_generar = QPushButton("Ir a Cálculo y Asignación")
        self.boton_generar.clicked.connect(
            lambda: self.ir_a_seccion.emit("asignacion_calculo")
        )
        layout.addWidget(self.boton_generar)

        layout.addStretch()

    def _limpiar_filas(self):
        for fila in self._filas:
            self.contenedor.removeWidget(fila)
            fila.deleteLater()
        self._filas = []

    def _crear_fila(self, requisito):
        fila = QFrame()
        fila.setFrameShape(QFrame.Shape.StyledPanel)
        color = "#059669" if requisito.cumplido else "#b45309"
        fondo = "#ecfdf5" if requisito.cumplido else "#fffbeb"
        fila.setStyleSheet(
            f"QFrame {{ background: {fondo}; border: 1px solid {color};"
            f" border-radius: 6px; padding: 8px; }}"
        )

        caja = QHBoxLayout(fila)
        caja.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

        marca = "✓" if requisito.cumplido else "!"
        texto = QLabel(
            f"<span style='color:{color};font-weight:700'>{marca}</span>&nbsp;&nbsp;"
            f"<b>{requisito.titulo}</b><br>{requisito.detalle}"
        )
        texto.setWordWrap(True)
        texto.setTextFormat(Qt.TextFormat.RichText)
        caja.addWidget(texto, 1)

        if not requisito.cumplido and requisito.seccion:
            destino = NOMBRE_DE_SECCION.get(requisito.seccion, requisito.seccion)
            boton = QPushButton(f"Ir a {destino}")
            boton.clicked.connect(
                lambda _=False, s=requisito.seccion: self.ir_a_seccion.emit(s)
            )
            caja.addWidget(boton)

        return fila

    def cargar_datos(self):
        """Recalcula el estado. Se llama al abrir y en cada recarga de vistas."""
        try:
            estado = PreflightGeneracionUseCase(self.session).execute()
        except Exception as e:  # noqa: BLE001 - la vista nunca debe reventar
            logger.warning(f"No se pudo calcular el estado del curso: {e}")
            self.resumen.setText("No se ha podido comprobar el estado del curso.")
            return

        self._limpiar_filas()
        for requisito in estado.requisitos:
            fila = self._crear_fila(requisito)
            self.contenedor.addWidget(fila)
            self._filas.append(fila)

        if estado.listo:
            self.resumen.setText(
                "Todo listo. Ya puedes calcular las cuotas y generar el calendario."
            )
            self.boton_generar.setEnabled(True)
        else:
            pendientes = len(estado.faltantes)
            plural = "paso" if pendientes == 1 else "pasos"
            self.resumen.setText(
                f"Quedan {pendientes} {plural} antes de poder generar las guardias."
            )
            self.boton_generar.setEnabled(False)

    # Alias para el mecanismo de recarga de la ventana principal.
    def cargar_estadisticas(self):
        self.cargar_datos()
