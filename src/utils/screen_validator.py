"""
Validador de Resolución de Pantalla.

Valida que la resolución de pantalla cumpla con los requisitos mínimos
para una correcta visualización de la aplicación.
"""

from typing import Tuple

from core.qt_imports import QApplication, QMessageBox, QScreen


class ScreenValidator:
    """Validador de requisitos de resolución de pantalla."""

    # Requisitos mínimos de resolución
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720
    RECOMMENDED_WIDTH = 1920
    RECOMMENDED_HEIGHT = 1080

    @staticmethod
    def get_screen_resolution() -> Tuple[int, int]:
        """
        Obtiene la resolución de la pantalla principal.

        Returns:
            Tuple[int, int]: Tupla con (ancho, alto) en píxeles.
        """
        screen: QScreen = QApplication.primaryScreen()
        geometry = screen.geometry()
        return geometry.width(), geometry.height()

    @classmethod
    def validate_resolution(cls) -> bool:
        """
        Valida que la resolución cumpla con los requisitos mínimos.

        Returns:
            bool: True si la resolución es adecuada, False en caso contrario.
        """
        width, height = cls.get_screen_resolution()
        return width >= cls.MIN_WIDTH and height >= cls.MIN_HEIGHT

    @classmethod
    def show_resolution_warning(cls) -> None:
        """
        Muestra un diálogo de advertencia si la resolución no es adecuada.

        Este método bloquea la ejecución de la aplicación si no se cumplen
        los requisitos mínimos de resolución.
        """
        width, height = cls.get_screen_resolution()

        if not cls.validate_resolution():
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Resolución Insuficiente")
            msg_box.setText("<h3>⚠️ Resolución de Pantalla Insuficiente</h3>")
            msg_box.setInformativeText(
                f"<p>La resolución actual de tu pantalla es "
                f"<b>{width}x{height}</b> píxeles.</p>"
                f"<p>Para una correcta visualización de la aplicación, "
                f"se requiere una resolución mínima de:</p>"
                f"<ul>"
                f"<li><b>Mínimo requerido:</b> "
                f"{cls.MIN_WIDTH}x{cls.MIN_HEIGHT} píxeles</li>"
                f"<li><b>Recomendado:</b> "
                f"{cls.RECOMMENDED_WIDTH}x{cls.RECOMMENDED_HEIGHT} "
                f"píxeles o superior</li>"
                f"</ul>"
                f"<p><b>La aplicación no se ejecutará</b> para evitar "
                f"una mala experiencia de usuario con campos y textos "
                f"que no se visualizan correctamente.</p>"
                f"<p>Por favor, ajusta la resolución de tu pantalla "
                f"e intenta de nuevo.</p>"
            )
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setDefaultButton(QMessageBox.StandardButton.Ok)

            # Aplicar estilo corporativo
            from utils.ui_helpers import get_corporate_icon

            msg_box.setWindowIcon(get_corporate_icon())

            msg_box.exec()
            return False

        # Mostrar advertencia informativa si está por debajo de lo recomendado
        elif width < cls.RECOMMENDED_WIDTH or height < cls.RECOMMENDED_HEIGHT:
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Resolución por debajo de lo recomendado")
            msg_box.setText("<h3>ℹ️ Resolución por debajo de lo recomendado</h3>")
            msg_box.setInformativeText(
                f"<p>Tu resolución actual es "
                f"<b>{width}x{height}</b> píxeles.</p>"
                f"<p>Aunque cumples con el mínimo requerido de "
                f"{cls.MIN_WIDTH}x{cls.MIN_HEIGHT}, "
                f"se recomienda una resolución de <b>"
                f"{cls.RECOMMENDED_WIDTH}x{cls.RECOMMENDED_HEIGHT}</b> "
                f"o superior para una mejor experiencia.</p>"
                f"<p>Algunos elementos de la interfaz podrían verse "
                f"reducidos o apretados.</p>"
                f"<p>¿Deseas continuar de todos modos?</p>"
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

            # Aplicar estilo corporativo
            from utils.ui_helpers import get_corporate_icon

            msg_box.setWindowIcon(get_corporate_icon())

            result = msg_box.exec()
            return result == QMessageBox.StandardButton.Yes

        return True

    @classmethod
    def get_resolution_info(cls) -> str:
        """
        Obtiene información legible sobre la resolución actual.

        Returns:
            str: Información de la resolución con indicación de si es adecuada.
        """
        width, height = cls.get_screen_resolution()
        status = "✅ Adecuada" if cls.validate_resolution() else "❌ Insuficiente"

        return (
            f"Resolución actual: {width}x{height} - {status}\n"
            f"Mínimo requerido: {cls.MIN_WIDTH}x{cls.MIN_HEIGHT}\n"
            f"Recomendado: {cls.RECOMMENDED_WIDTH}x{cls.RECOMMENDED_HEIGHT}"
        )
