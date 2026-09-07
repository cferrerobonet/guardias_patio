"""Ofrecer la versión nueva: preguntar qué trae, bajarla e instalarla.

Esto vivía dentro del menú lateral, así que sólo se podía actualizar con la
sesión ya abierta. La pantalla de login lo ofrece también, y quien no puede
entrar —porque su versión no conecta con el servidor— es justo quien más
necesita actualizarse. Una sola copia para las dos pantallas.
"""

import logging
import tempfile
import urllib.request
import webbrowser
from pathlib import Path

from PyQt6.QtCore import QThread
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtWidgets import QMessageBox, QProgressDialog

from utils.update_checker import abrir_instalador, url_de_confianza

logger = logging.getLogger(__name__)

PAGINA_DE_RELEASES = "https://github.com/cferrerobonet/guardias_patio/releases/latest"


def confirmar(parent, version: str, notas: str = "") -> bool:
    """Enseña qué trae la versión nueva antes de bajar nada (FUN-011)."""
    caja = QMessageBox(parent)
    caja.setIcon(QMessageBox.Icon.Question)
    caja.setWindowTitle(f"Guardias de Patio {version}")
    caja.setText(f"Hay una versión nueva: {version}. ¿Descargarla e instalarla?")
    notas = (notas or "").strip()
    if notas:
        caja.setDetailedText(notas)
    else:
        caja.setInformativeText("Esta versión no trae notas publicadas.")
    caja.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    caja.setDefaultButton(QMessageBox.StandardButton.Yes)
    return caja.exec() == QMessageBox.StandardButton.Yes


class _Descargador(QThread):
    progreso_signal = Signal(int)
    error_signal = Signal(str)
    listo_signal = Signal(str)

    def __init__(self, url, destino):
        super().__init__()
        self._url = url
        self._destino = destino

    def run(self):
        try:

            def _reporthook(count, block_size, total):
                if total > 0:
                    pct = min(int(count * block_size * 100 / total), 100)
                    self.progreso_signal.emit(pct)

            # La URL viene de una respuesta remota: se comprueba antes de bajar
            # nada, porque lo que se descarga es un instalador (SEC-003).
            if not url_de_confianza(self._url):
                self.error_signal.emit("La dirección de descarga no es de confianza; se cancela.")
                return
            # nosec B310 - validada justo encima con url_de_confianza()
            urllib.request.urlretrieve(self._url, self._destino, _reporthook)  # nosec B310
            self.listo_signal.emit(str(self._destino))
        except Exception as e:  # noqa: BLE001 - nada puede escapar de run() (CRW-005)
            self.error_signal.emit(str(e))


def descargar_e_instalar(parent, url: str, version: str = "") -> None:
    """Baja el instalador con una barra de progreso y lo lanza al terminar."""
    nombre = url.split("/")[-1]
    destino = Path(tempfile.gettempdir()) / nombre

    progreso = QProgressDialog(
        f"Descargando Guardias de Patio v{version}…", "Cancelar", 0, 100, parent
    )
    progreso.setWindowTitle("Actualización")
    progreso.setMinimumDuration(0)
    progreso.setValue(0)

    cancelado = [False]
    progreso.canceled.connect(lambda: cancelado.__setitem__(0, True))

    hilo = _Descargador(url, destino)
    # El hilo se guarda en el diálogo de progreso para que no lo recoja el
    # recolector de basura a mitad de descarga.
    progreso._hilo_de_descarga = hilo
    hilo.progreso_signal.connect(
        lambda v: progreso.setValue(v) if not cancelado[0] else hilo.terminate()
    )
    hilo.listo_signal.connect(lambda ruta: (progreso.close(), abrir_instalador(ruta)))
    hilo.error_signal.connect(
        lambda err: (
            progreso.close(),
            QMessageBox.critical(
                parent, "Error de descarga", f"No se pudo descargar la actualización:\n{err}"
            ),
        )
    )
    hilo.start()


def ofrecer(parent, version: str, url: str = "", notas: str = "") -> None:
    """Pregunta y, si se acepta, actualiza. Sin instalador para este sistema,
    abre la página de descargas en el navegador."""
    if not confirmar(parent, version, notas):
        return
    if url:
        descargar_e_instalar(parent, url, version)
    else:
        webbrowser.open(PAGINA_DE_RELEASES)
