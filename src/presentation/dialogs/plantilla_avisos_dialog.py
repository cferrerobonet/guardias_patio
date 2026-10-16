"""Editor de la plantilla de los avisos de guardias (GUA-CON-002)."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from services import plantilla_avisos
from utils.ui_helpers import aplicar_caja


class PlantillaAvisosDialog(QDialog):
    """Asunto, mensaje y adjuntos de los avisos. Se guarda al aceptar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plantilla de los avisos")
        self.resize(640, 520)
        self.plantilla = plantilla_avisos.cargar()

        capa = QVBoxLayout(self)
        capa.setSpacing(10)

        ayuda = QLabel(
            "Marcadores: "
            + " · ".join(f"{{{m}}} {texto.lower()}" for m, texto in plantilla_avisos.MARCADORES.items())
        )
        ayuda.setWordWrap(True)
        aplicar_caja(ayuda, "info")
        capa.addWidget(ayuda)

        formulario = QFormLayout()
        self.asunto = QLineEdit(self.plantilla.asunto)
        self.asunto.setAccessibleName("Asunto del aviso")
        formulario.addRow("Asunto:", self.asunto)
        self.cuerpo = QPlainTextEdit(self.plantilla.cuerpo)
        self.cuerpo.setAccessibleName("Mensaje del aviso")
        formulario.addRow("Mensaje:", self.cuerpo)
        capa.addLayout(formulario, 1)

        self.adjuntar_pdf = QCheckBox("Adjuntar su calendario individual en PDF")
        self.adjuntar_pdf.setChecked(self.plantilla.adjuntar_pdf)
        capa.addWidget(self.adjuntar_pdf)
        self.adjuntar_ical = QCheckBox("Adjuntar el archivo iCal (.ics) para su calendario")
        self.adjuntar_ical.setChecked(self.plantilla.adjuntar_ical)
        capa.addWidget(self.adjuntar_ical)

        self.aviso = QLabel("")
        self.aviso.setWordWrap(True)
        self.aviso.setVisible(False)
        capa.addWidget(self.aviso)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        botones.button(QDialogButtonBox.StandardButton.Save).setText("Guardar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.restablecer = QPushButton("Volver a la de serie")
        self.restablecer.setProperty("secondary", "true")
        botones.addButton(self.restablecer, QDialogButtonBox.ButtonRole.ResetRole)
        self.restablecer.clicked.connect(self._de_serie)
        botones.accepted.connect(self._guardar)
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)

    def leida(self) -> plantilla_avisos.Plantilla:
        return plantilla_avisos.Plantilla(
            asunto=self.asunto.text(),
            cuerpo=self.cuerpo.toPlainText(),
            adjuntar_pdf=self.adjuntar_pdf.isChecked(),
            adjuntar_ical=self.adjuntar_ical.isChecked(),
        )

    def _de_serie(self) -> None:
        serie = plantilla_avisos.Plantilla()
        self.asunto.setText(serie.asunto)
        self.cuerpo.setPlainText(serie.cuerpo)
        self.adjuntar_pdf.setChecked(serie.adjuntar_pdf)
        self.adjuntar_ical.setChecked(serie.adjuntar_ical)

    def _guardar(self) -> None:
        plantilla = self.leida()
        errores = plantilla.errores()
        if errores:
            self.aviso.setText("\n".join(errores))
            aplicar_caja(self.aviso, "error")
            self.aviso.setVisible(True)
            return
        try:
            plantilla_avisos.guardar(plantilla)
        except OSError as e:
            self.aviso.setText(f"No se pudo guardar la plantilla: {e}")
            aplicar_caja(self.aviso, "error")
            self.aviso.setVisible(True)
            return
        self.plantilla = plantilla
        self.accept()
