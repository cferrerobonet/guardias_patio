"""Vista previa y envío de los avisos de guardias (FUN-006).

Antes se pulsaba «Enviar emails a profesores» y salían, sin ver qué decían ni a
quién iban, con la ventana congelada mientras tanto y un resumen final que
recortaba los errores a los cinco primeros.

Aquí se ve la lista de destinatarios, el mensaje tal cual le llegará a cada uno,
y al terminar qué pasó con cada envío.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QLabel,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
)

from core.logging import get_logger
from services import notificador_guardias

logger = get_logger(__name__)

COL_NOMBRE, COL_CORREO, COL_GUARDIAS, COL_ESTADO = range(4)


class EnvioDeEmailsDialog(QDialog):
    """Lista de destinatarios, vista previa del mensaje y resultado de cada envío."""

    def __init__(self, session, parent=None, mes_anio: Optional[str] = None):
        super().__init__(parent)
        self.session = session
        self.preparacion = notificador_guardias.preparar_envios(session, mes_anio)
        self.resultados: list = []
        self._construir()
        self._rellenar_tabla()

    def _construir(self) -> None:
        self.setWindowTitle("Enviar avisos de guardias")
        self.setMinimumSize(900, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.label_resumen = QLabel()
        self.label_resumen.setWordWrap(True)
        self.label_resumen.setAccessibleName("Resumen del envío")
        layout.addWidget(self.label_resumen)

        divisor = QSplitter(Qt.Orientation.Horizontal)

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Profesor", "Correo", "Guardias", "Estado"])
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAccessibleName("Destinatarios")
        self.tabla.setAccessibleDescription(
            "Profesores que recibirán el aviso, con su correo, cuántas guardias "
            "se les comunican y el resultado del envío"
        )
        self.tabla.horizontalHeader().setSectionResizeMode(
            COL_NOMBRE, QHeaderView.ResizeMode.Stretch
        )
        self.tabla.itemSelectionChanged.connect(self._mostrar_vista_previa)
        divisor.addWidget(self.tabla)

        self.vista_previa = QTextBrowser()
        self.vista_previa.setAccessibleName("Vista previa del mensaje")
        self.vista_previa.setOpenExternalLinks(False)
        divisor.addWidget(self.vista_previa)
        divisor.setSizes([420, 480])
        layout.addWidget(divisor, 1)

        self.label_excluidos = QLabel()
        self.label_excluidos.setWordWrap(True)
        layout.addWidget(self.label_excluidos)

        botones = QDialogButtonBox()
        self.boton_enviar = botones.addButton(
            "Enviar", QDialogButtonBox.ButtonRole.AcceptRole
        )
        self.boton_cerrar = botones.addButton(
            "Cerrar", QDialogButtonBox.ButtonRole.RejectRole
        )
        self.boton_enviar.clicked.connect(self._enviar)
        self.boton_cerrar.clicked.connect(self.reject)
        layout.addWidget(botones)

    def _rellenar_tabla(self) -> None:
        envios = self.preparacion.envios
        self.tabla.setRowCount(len(envios))
        for fila, envio in enumerate(envios):
            self.tabla.setItem(fila, COL_NOMBRE, QTableWidgetItem(envio.nombre))
            self.tabla.setItem(fila, COL_CORREO, QTableWidgetItem(envio.email))
            self.tabla.setItem(fila, COL_GUARDIAS, QTableWidgetItem(str(envio.guardias)))
            self.tabla.setItem(fila, COL_ESTADO, QTableWidgetItem("Sin enviar"))

        self.label_resumen.setText(
            f"Se enviará el aviso a {len(envios)} profesores. "
            "Selecciona uno para ver el mensaje que recibirá."
        )
        self.boton_enviar.setEnabled(bool(envios))

        excluidos = self.preparacion.excluidos
        if excluidos:
            detalle = ", ".join(f"{e.nombre} ({e.motivo})" for e in excluidos[:6])
            if len(excluidos) > 6:
                detalle += f" y {len(excluidos) - 6} más"
            self.label_excluidos.setText(f"Fuera del envío: {detalle}")
        else:
            self.label_excluidos.setVisible(False)

        if envios:
            self.tabla.selectRow(0)

    def _mostrar_vista_previa(self) -> None:
        envio = self._envio_seleccionado()
        if envio is None:
            self.vista_previa.clear()
            return
        self.vista_previa.setHtml(
            f"<p style='font-family:sans-serif'><b>Para:</b> {envio.email}<br>"
            f"<b>Asunto:</b> {envio.asunto}</p><hr>{envio.html}"
        )

    def _envio_seleccionado(self):
        fila = self.tabla.currentRow()
        if fila < 0 or fila >= len(self.preparacion.envios):
            return None
        return self.preparacion.envios[fila]

    def _enviar(self) -> None:
        from presentation.widgets.progress_indicators import ejecutar_con_progreso

        envios = self.preparacion.envios
        if not envios:
            return

        def tarea(callback_progreso, cancelacion=None):
            def avisar(numero, total, nombre):
                callback_progreso(numero, total, f"Enviando a {nombre}...")

            return notificador_guardias.enviar(
                envios, progreso=avisar, cancelacion=cancelacion
            )

        self.boton_enviar.setEnabled(False)
        resultados = ejecutar_con_progreso(
            self,
            tarea,
            titulo="Enviando avisos",
            mensaje=f"Enviando {len(envios)} avisos...",
            cerrar_al_terminar=True,
        )
        self.boton_enviar.setEnabled(True)

        if resultados is None:
            return
        self.resultados = resultados
        self._pintar_resultados(resultados)

    def _pintar_resultados(self, resultados: list) -> None:
        por_profesor = {r.profesor_id: r for r in resultados}
        for fila, envio in enumerate(self.preparacion.envios):
            resultado = por_profesor.get(envio.profesor_id)
            if resultado is None:
                self.tabla.setItem(fila, COL_ESTADO, QTableWidgetItem("Cancelado"))
                continue
            celda = QTableWidgetItem(resultado.detalle)
            celda.setToolTip(resultado.detalle)
            self.tabla.setItem(fila, COL_ESTADO, celda)

        enviados = sum(1 for r in resultados if r.enviado)
        fallidos = len(resultados) - enviados
        cancelados = len(self.preparacion.envios) - len(resultados)
        texto = f"Enviados {enviados} de {len(self.preparacion.envios)}."
        if fallidos:
            texto += f" {fallidos} con error: el motivo está en su fila."
        if cancelados:
            texto += f" {cancelados} sin enviar por cancelación."
        self.label_resumen.setText(texto)
