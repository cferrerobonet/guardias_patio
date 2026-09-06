"""Pantalla de arranque con los pasos a la vista (ESC-006).

Entre el login y la ventana principal hay tres pasos que hablan con la red o con
el disco: la migración de datos, comprobar que la cuenta no esté abierta en otro
equipo y traerse los datos de la nube. Todos corren en el hilo de la interfaz,
así que durante esos segundos no había nada en pantalla: ni ventana, ni aviso,
ni forma de saber si la aplicación estaba haciendo algo o se había colgado.

Esto no cambia dónde corren los pasos —moverlos a un hilo aparte obligaría a
sacar de ahí los diálogos que algunos abren—, pero sí los cuenta mientras pasan.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import QApplication, QSplashScreen

from core.logging import get_logger

logger = get_logger(__name__)

ANCHO, ALTO = 460, 260


class PantallaDeArranque(QSplashScreen):
    """Un rótulo con el logo que va diciendo por qué paso va el arranque."""

    def __init__(self, parent=None):
        super().__init__(parent, self._fondo(), Qt.WindowType.WindowStaysOnTopHint)
        self.setEnabled(False)  # decorativa: no debe robar clics ni foco

    @staticmethod
    def _fondo() -> QPixmap:
        from utils.ui_helpers import get_corporate_pixmap

        lienzo = QPixmap(ANCHO, ALTO)
        lienzo.fill(QColor("#3E4857"))

        logo = get_corporate_pixmap(120)
        if logo is not None and not logo.isNull():
            from PyQt6.QtGui import QPainter

            pintor = QPainter(lienzo)
            pintor.drawPixmap((ANCHO - logo.width()) // 2, 40, logo)
            pintor.end()
        return lienzo

    def paso(self, mensaje: str) -> None:
        """Escribe el paso en marcha y deja que la pantalla se repinte."""
        logger.info(f"Arranque: {mensaje}")
        self.showMessage(
            mensaje,
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            QColor("#FFFFFF"),
        )
        aplicacion = QApplication.instance()
        if aplicacion is not None:
            # Sin esto el texto no llega a verse: el hilo entra en el paso
            # siguiente antes de que Qt haya pintado nada.
            aplicacion.processEvents()

    def terminar(self, ventana=None) -> None:
        if ventana is not None:
            self.finish(ventana)
        else:
            self.close()


def abrir_pantalla_de_arranque() -> Optional[PantallaDeArranque]:
    """Crea y muestra la pantalla, o devuelve None si no hay interfaz gráfica."""
    if QApplication.instance() is None:
        return None
    pantalla = PantallaDeArranque()
    pantalla.show()
    QApplication.instance().processEvents()
    return pantalla
