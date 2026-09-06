"""Diálogo que enseña la huella del servidor y pide confirmarla una vez (SEC-008)."""

import logging
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

from sync import huella_servidor
from sync.backends import ERRORES_DE_TRANSPORTE

logger = logging.getLogger(__name__)


def _texto(host: str, port: int, tipo: str, huella: str) -> str:
    return (
        f"Es la primera vez que este equipo se conecta a <b>{host}</b>.<br><br>"
        f"Antes de enviar nada hay que comprobar que el servidor es el del centro "
        f"y no otro que se haga pasar por él. Esta es su huella:<br><br>"
        f"<b>Servidor:</b> {host}:{port}<br>"
        f"<b>Tipo de clave:</b> {tipo}<br>"
        f"<b>Huella:</b> <code>{huella}</code><br><br>"
        f"Si coincide con la que ya se aceptó en otro equipo, confírmala. "
        f"Si no la conoces, cancela y pregunta antes de continuar."
    )


def confirmar_huella_si_hace_falta(parent=None, host: Optional[str] = None, port: int = 22) -> bool:
    """Enseña la huella del servidor configurado y la anota si se confirma.

    Devuelve True si al terminar se puede conectar (ya estaba confiado o se acaba
    de confiar) y False si no hay configuración, no se pudo preguntar al servidor
    o la persona canceló.
    """
    if host is None:
        try:
            from config import get_sftp_config, validate_sftp_config

            if not validate_sftp_config():
                return False
            config = get_sftp_config()
            host, port = config["host"], int(config.get("port", 22))
        except (ImportError, ValueError, KeyError, TypeError) as e:
            logger.warning(f"Sin configuración de servidor para comprobar la huella: {e}")
            return False

    if huella_servidor.esta_confiado(host, port):
        return True

    try:
        tipo, clave = huella_servidor.clave_del_servidor(host, port)
    except ERRORES_DE_TRANSPORTE as e:
        logger.error(f"No se pudo obtener la huella de {host}:{port}: {type(e).__name__}: {e}")
        return False

    aviso = QMessageBox(parent)
    aviso.setIcon(QMessageBox.Icon.Warning)
    aviso.setWindowTitle("Servidor desconocido en este equipo")
    aviso.setTextFormat(Qt.TextFormat.RichText)
    aviso.setText(_texto(host, port, tipo, huella_servidor.huella_sha256(clave)))
    confirmar = aviso.addButton("Confiar en este servidor", QMessageBox.ButtonRole.AcceptRole)
    aviso.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
    aviso.setDefaultButton(confirmar)
    aviso.exec()

    if aviso.clickedButton() is not confirmar:
        logger.warning(f"El usuario no confirmó la huella de {host}:{port}")
        return False

    return huella_servidor.confiar(host, port, clave)
