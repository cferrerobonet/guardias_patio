"""Widgets de configuración reutilizables."""

from presentation.forms.config_widgets.ajustes_widget import AjustesWidget
from presentation.forms.config_widgets.fechas_recreos_widget import (
    FechasRecreosWidget,
)
from presentation.forms.config_widgets.festivos_widget import FestivosWidget
from presentation.forms.config_widgets.perfil_usuario_widget import (
    PerfilUsuarioWidget,
)
from presentation.forms.config_widgets.sftp_widget import SFTPConfigWidget
from presentation.forms.config_widgets.smtp_widget import SMTPConfigWidget

__all__ = [
    "SMTPConfigWidget",
    "SFTPConfigWidget",
    "FechasRecreosWidget",
    "AjustesWidget",
    "FestivosWidget",
    "PerfilUsuarioWidget",
]
