"""Prueba de humo del arranque, para el ejecutable congelado (BLD-020).

No hay PC con Windows: la única forma de saber si el `.exe` llega al login es
arrancarlo en el Windows de GitHub, y ahí nadie pulsa botones. Con
`GUARDIAS_PRUEBA_DE_ARRANQUE` en el entorno, un temporizador hace de usuario:

- acepta cada aviso por su botón por defecto y rechaza cualquier otro diálogo
  (el de configuración inicial, la huella del servidor…), dejando su texto en el
  registro;
- ``login``: al ver el login lo apunta y lo cierra; la aplicación sale con 0;
- ``ventana``: entra con una cuenta de prueba de este equipo y, cuando la ventana
  principal está a la vista, lo apunta y cierra la aplicación.

Sin la variable no hace nada. Nunca toca el servidor real: el flujo de CI arranca
sin configuración o contra un servidor falso.
"""

import logging
import os

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QDialog, QMessageBox

logger = logging.getLogger(__name__)

VARIABLE = "GUARDIAS_PRUEBA_DE_ARRANQUE"
MARCA_LOGIN = "PRUEBA DE ARRANQUE: login a la vista"
MARCA_VENTANA = "PRUEBA DE ARRANQUE: ventana principal a la vista"

USUARIO = "prueba.arranque"
CONTRASENA = "Prueba-Arranque-2026!"

#: Vueltas del temporizador que una ventana debe llevar a la vista antes de
#: tocarla: así queda pintada de verdad, que es lo que se quiere comprobar.
VUELTAS_A_LA_VISTA = 2


def modo() -> str:
    """``login``, ``ventana`` o cadena vacía si la prueba no está pedida."""
    valor = os.getenv(VARIABLE, "").strip().lower()
    if valor in ("1", "login"):
        return "login"
    if valor == "ventana":
        return "ventana"
    return ""


def _describir(ventana) -> str:
    texto = f"{type(ventana).__name__} «{ventana.windowTitle()}»"
    if isinstance(ventana, QMessageBox):
        texto += f": {ventana.text()} | {ventana.informativeText()}"
    return texto


def _entrar(login) -> None:
    """Crea la cuenta de prueba si no existe y entra con ella."""
    if USUARIO not in login.user_auth.users:
        if not login.user_auth.register_user(USUARIO, CONTRASENA, "prueba@ejemplo.invalid"):
            logger.error(f"PRUEBA DE ARRANQUE: no se pudo crear la cuenta de prueba: "
                         f"{login.user_auth.ultimo_motivo_registro}")
            login.reject()
            return
        login.username_combo.addItem(USUARIO)
    login.username_combo.setCurrentText(USUARIO)
    login.password_input.setText(CONTRASENA)
    login.login()


class _Vigia:
    """Mira las ventanas de primer nivel y hace lo que haría quien está delante."""

    def __init__(self, app: QApplication, que: str):
        self.app = app
        self.modo = que
        self.vueltas: dict[int, int] = {}
        self.vistas: set[str] = set()
        self.intentos_de_entrar = 0

    def revisar(self) -> None:
        visibles = [w for w in QApplication.topLevelWidgets() if w.isVisible()]
        for ventana in visibles:
            descripcion = _describir(ventana)
            if descripcion not in self.vistas:
                self.vistas.add(descripcion)
                logger.info(f"PRUEBA DE ARRANQUE: a la vista {descripcion}")
            clave = id(ventana)
            self.vueltas[clave] = self.vueltas.get(clave, 0) + 1
            if self.vueltas[clave] < VUELTAS_A_LA_VISTA:
                continue
            self._actuar(ventana)

    def _actuar(self, ventana) -> None:
        nombre = type(ventana).__name__
        if nombre == "PantallaDeArranque":
            return
        if nombre == "LoginDialog":
            logger.info(MARCA_LOGIN)
            if self.modo == "ventana" and self.intentos_de_entrar == 0:
                self.intentos_de_entrar += 1
                _entrar(ventana)
            else:
                ventana.reject()
            return
        if nombre == "VentanaPrincipal":
            logger.info(MARCA_VENTANA)
            self.app.quit()
            return
        if isinstance(ventana, QMessageBox):
            boton = ventana.defaultButton()
            logger.info(f"PRUEBA DE ARRANQUE: se acepta {_describir(ventana)}")
            if boton is not None:
                boton.click()
            else:
                ventana.accept()
            return
        if isinstance(ventana, QDialog):
            logger.info(f"PRUEBA DE ARRANQUE: se rechaza {_describir(ventana)}")
            ventana.reject()


def vigilar_si_se_pide(app: QApplication):
    """Arranca el temporizador si la prueba está pedida; devuelve el temporizador o None."""
    que = modo()
    if not que:
        return None
    logger.info(f"PRUEBA DE ARRANQUE: activa, modo {que}")
    vigia = _Vigia(app, que)
    temporizador = QTimer(app)
    temporizador.setInterval(400)
    temporizador.timeout.connect(vigia.revisar)
    temporizador.start()
    app._prueba_de_arranque = (vigia, temporizador)  # que no se los lleve el recolector
    return temporizador
