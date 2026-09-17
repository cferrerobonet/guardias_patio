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
from PyQt6.QtWidgets import QApplication, QMessageBox, QProgressDialog

from utils.update_checker import abrir_instalador, contexto_ssl, url_de_confianza

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
            # `urlretrieve` no admite contexto TLS y fallaría igual que la
            # comprobación de versión en un Mac sin los certificados del
            # Python de compilación (BLD-018).
            # nosec B310 - validada justo encima con url_de_confianza()
            with urllib.request.urlopen(self._url, context=contexto_ssl()) as r:  # nosec B310
                total = int(r.headers.get("Content-Length") or 0)
                bloque = 64 * 1024
                with open(self._destino, "wb") as f:
                    for n in range(1, 10**9):
                        trozo = r.read(bloque)
                        if not trozo:
                            break
                        f.write(trozo)
                        _reporthook(n, bloque, total)
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
    hilo.listo_signal.connect(lambda ruta: (progreso.close(), instalar_y_salir(parent, ruta)))
    hilo.error_signal.connect(
        lambda err: (
            progreso.close(),
            QMessageBox.critical(
                parent, "Error de descarga", f"No se pudo descargar la actualización:\n{err}"
            ),
        )
    )
    hilo.start()


def instalar_y_salir(parent, ruta: str) -> None:
    """Lanza el instalador y cierra la aplicación.

    Mientras la aplicación corre, su ejecutable está en uso y el instalador no
    puede reemplazarlo: en Windows se quedaba en «DeleteFile falló; código 5» y
    la instalación se abortaba a medias. Se cierra todo antes de que el
    instalador llegue a copiar nada.
    """
    app = QApplication.instance()
    if app is not None:
        app.closeAllWindows()
        # Si algo se niega a cerrarse (cambios sin sincronizar, por ejemplo) no
        # se lanza el instalador: fallaría igual y dejaría la copia a medias.
        if any(v.isVisible() for v in app.topLevelWidgets()):
            QMessageBox.information(
                parent,
                "Actualización pendiente",
                "Cierra Guardias de Patio y vuelve a pulsar Actualizar para instalar "
                "la versión nueva.",
            )
            return

    abrir_instalador(ruta)

    if app is not None:
        app.quit()


def ofrecer(parent, version: str, url: str = "", notas: str = "") -> None:
    """Pregunta y, si se acepta, actualiza. Sin instalador para este sistema,
    abre la página de descargas en el navegador."""
    if not confirmar(parent, version, notas):
        return
    if url:
        descargar_e_instalar(parent, url, version)
    else:
        webbrowser.open(PAGINA_DE_RELEASES)
