"""Diálogo para intercambiar una guardia con la de otro profesor.

No es una sustitución: nadie falta. Dos personas se ponen de acuerdo y cambian
sus guardias, así que cada una cede una y coge otra y **los totales del curso no
varían**. Por eso no toca cuotas ni se marca como sustitución (FUN-003b).
"""

from datetime import date

from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from infrastructure.database.models import Guardia, Profesor
from utils import get_logger
from utils.ui_helpers import aplicar_caja

logger = get_logger(__name__)


class PermutarGuardiaDialog(QDialog):
    """Elige con qué profesor y con cuál de sus guardias se intercambia."""

    def __init__(self, session, guardia: Guardia, parent=None):
        super().__init__(parent)
        self.session = session
        self.guardia = guardia

        self.setWindowTitle("Permutar guardia")
        self.setMinimumWidth(520)
        self._setup_ui()
        self._cargar_profesores()

    # -- interfaz ------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        cede = self.guardia.profesor.nombre_completo if self.guardia.profesor else "?"
        zona = self.guardia.zona.nombre_zona if self.guardia.zona else "?"
        cabecera = QLabel(
            f"<b>{cede}</b> cede su guardia del "
            f"<b>{self.guardia.fecha:%d/%m/%Y}</b>, recreo {self.guardia.recreo} ({zona})."
        )
        cabecera.setWordWrap(True)
        layout.addWidget(cabecera)

        fila_profesor = QHBoxLayout()
        etiqueta_profesor = QLabel("Permutar con:")
        fila_profesor.addWidget(etiqueta_profesor)
        self.combo_profesor = QComboBox()
        self.combo_profesor.setAccessibleName("Profesor con el que permutar")
        self.combo_profesor.currentIndexChanged.connect(self._cargar_guardias_del_otro)
        etiqueta_profesor.setBuddy(self.combo_profesor)
        fila_profesor.addWidget(self.combo_profesor, 1)
        layout.addLayout(fila_profesor)

        fila_guardia = QHBoxLayout()
        etiqueta_guardia = QLabel("Guardia que cede a cambio:")
        fila_guardia.addWidget(etiqueta_guardia)
        self.combo_guardia = QComboBox()
        self.combo_guardia.setAccessibleName("Guardia que se recibe a cambio")
        etiqueta_guardia.setBuddy(self.combo_guardia)
        fila_guardia.addWidget(self.combo_guardia, 1)
        layout.addLayout(fila_guardia)

        self.aviso = QLabel("")
        self.aviso.setWordWrap(True)
        aplicar_caja(self.aviso, "info")
        self.aviso.setText(
            "Es un intercambio: cada uno hace una guardia distinta, pero el número "
            "total de guardias de cada profesor en el curso no cambia."
        )
        layout.addWidget(self.aviso)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setText("Permutar")
        self.botones.accepted.connect(self._aceptar)
        self.botones.rejected.connect(self.reject)
        layout.addWidget(self.botones)

    # -- datos ---------------------------------------------------------------

    def _cargar_profesores(self) -> None:
        """Todos los activos menos quien ya tiene esta guardia."""
        profesores = (
            self.session.query(Profesor)
            .filter(Profesor.activo.is_(True), Profesor.id != self.guardia.profesor_id)
            .order_by(Profesor.nombre_completo)
            .all()
        )
        self.combo_profesor.clear()
        for profesor in profesores:
            self.combo_profesor.addItem(profesor.nombre_completo, profesor.id)

        if not profesores:
            self._bloquear("No hay otros profesores activos con los que permutar.")

    def _cargar_guardias_del_otro(self) -> None:
        """Sus guardias futuras, que son las que tiene sentido intercambiar."""
        self.combo_guardia.clear()
        profesor_id = self.combo_profesor.currentData()
        if profesor_id is None:
            return

        guardias = (
            self.session.query(Guardia)
            .filter(
                Guardia.profesor_id == profesor_id,
                Guardia.fecha >= date.today(),
                Guardia.id != self.guardia.id,
            )
            .order_by(Guardia.fecha, Guardia.recreo)
            .all()
        )

        for otra in guardias:
            zona = otra.zona.nombre_zona if otra.zona else "?"
            self.combo_guardia.addItem(
                f"{otra.fecha:%d/%m/%Y} · recreo {otra.recreo} · {zona}", otra.id
            )

        hay = bool(guardias)
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setEnabled(hay)
        if not hay:
            self.aviso.setText(
                "Ese profesor no tiene ninguna guardia futura que ofrecer a cambio. "
                "Elige otro."
            )
            aplicar_caja(self.aviso, "aviso")
        else:
            self.aviso.setText(
                "Es un intercambio: cada uno hace una guardia distinta, pero el número "
                "total de guardias de cada profesor en el curso no cambia."
            )
            aplicar_caja(self.aviso, "info")
        self.aviso.style().unpolish(self.aviso)
        self.aviso.style().polish(self.aviso)

    def _bloquear(self, motivo: str) -> None:
        self.aviso.setText(motivo)
        aplicar_caja(self.aviso, "aviso")
        self.botones.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

    # -- acción --------------------------------------------------------------

    def _aceptar(self) -> None:
        otra_id = self.combo_guardia.currentData()
        if otra_id is None:
            return

        from services.gestor_ausencias import permutar_guardias

        try:
            permutar_guardias(self.session, self.guardia.id, otra_id)
        except ValueError as e:
            # El servicio comprueba ausencias y que nadie acabe con dos el mismo día.
            QMessageBox.warning(self, "No se puede permutar", str(e))
            return
        except Exception as e:  # noqa: BLE001
            logger.exception("Error al permutar guardias")
            QMessageBox.critical(self, "Error al permutar", f"{type(e).__name__}: {e}")
            return

        self.accept()
