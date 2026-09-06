"""Informe previo de una importación de profesores (FUN-007).

Antes se elegía el fichero, se mapeaban las columnas y se escribía en la base de
datos de una vez: el usuario se enteraba de lo que había pasado al terminar, con
un recuento. Si el mapeo estaba mal o el fichero traía nombres repetidos, ya era
tarde.

Esta ventana enseña, fila a fila, qué va a ocurrir antes de escribir nada.
"""

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from core.logging import get_logger

logger = get_logger(__name__)

COL_FILA, COL_NOMBRE, COL_CORREO, COL_QUE_PASA = range(4)

QUE_PASA = {
    "nuevo": "Se dará de alta",
    "existente": "Ya está: no se toca",
    "repetido": "Repetido en el fichero: se ignora",
}


class InformeImportacionDialog(QDialog):
    """Muestra el resultado del análisis y pregunta si seguir adelante."""

    def __init__(self, informe: dict, parent=None):
        super().__init__(parent)
        self.informe = informe
        self._construir()

    def _construir(self) -> None:
        self.setWindowTitle("Antes de importar")
        self.setMinimumSize(720, 480)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.label_resumen = QLabel(self._resumen())
        self.label_resumen.setWordWrap(True)
        self.label_resumen.setAccessibleName("Resumen de la importación")
        layout.addWidget(self.label_resumen)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Fila", "Nombre", "Correo", "Qué pasará"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAccessibleName("Filas del fichero")
        self.tabla.setAccessibleDescription(
            "Cada fila del fichero con lo que ocurrirá al importarla"
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            COL_NOMBRE, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.tabla, 1)
        self._rellenar()

        botones = QDialogButtonBox()
        self.boton_importar = botones.addButton(
            "Importar", QDialogButtonBox.ButtonRole.AcceptRole
        )
        botones.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.boton_importar.setEnabled(bool(self.informe.get("nuevos")))

    def _resumen(self) -> str:
        if self.informe.get("error"):
            return f"No se puede leer el fichero: {self.informe['error']}"
        nuevos = self.informe.get("nuevos", 0)
        existentes = self.informe.get("existentes", 0)
        repetidos = self.informe.get("repetidos", 0)
        partes = [f"{nuevos} profesores nuevos"]
        if existentes:
            partes.append(f"{existentes} que ya estaban")
        if repetidos:
            partes.append(f"{repetidos} repetidos dentro del propio fichero")
        if not nuevos:
            return (
                f"{self.informe.get('archivo', 'El fichero')}: no hay nada que dar de alta "
                f"({', '.join(partes[1:]) or 'ninguna fila válida'})."
            )
        return f"{self.informe.get('archivo', 'El fichero')} traerá {', '.join(partes)}."

    def _rellenar(self) -> None:
        filas = self.informe.get("filas", [])
        self.tabla.setRowCount(len(filas))
        for indice, fila in enumerate(filas):
            self.tabla.setItem(indice, COL_FILA, QTableWidgetItem(str(fila["fila"])))
            self.tabla.setItem(indice, COL_NOMBRE, QTableWidgetItem(fila["nombre"]))
            self.tabla.setItem(indice, COL_CORREO, QTableWidgetItem(fila["email"] or "—"))
            self.tabla.setItem(
                indice, COL_QUE_PASA, QTableWidgetItem(QUE_PASA.get(fila["estado"], fila["estado"]))
            )
