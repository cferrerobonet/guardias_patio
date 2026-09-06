import json
import platform
import urllib.request
from threading import Thread
from typing import Callable

RELEASES_URL = "https://api.github.com/repos/cferrerobonet/guardias_patio/releases/latest"

#: Sólo se acepta descargar de aquí. `urlopen` admite también `file:` y esquemas
#: propios, así que una respuesta manipulada podría hacer que la aplicación se
#: bajara «la actualización» de cualquier sitio (SEC-003, B310).
ESQUEMA_PERMITIDO = "https"
HOSTS_PERMITIDOS = ("api.github.com", "github.com", "objects.githubusercontent.com")


def url_de_confianza(url: str) -> bool:
    """True si la URL es https y apunta a GitHub."""
    from urllib.parse import urlparse

    partes = urlparse(url or "")
    if partes.scheme != ESQUEMA_PERMITIDO:
        return False
    return partes.hostname in HOSTS_PERMITIDOS


def check_for_updates(current_version: str, callback: Callable[[str, str, str], None]) -> None:
    """Avisa de una versión nueva con `(version, url_de_descarga, notas)`.

    Las notas son el cuerpo del release: sin ellas el aviso pide instalar algo
    sin decir qué cambia (FUN-011).
    """
    def _check():
        try:
            if not url_de_confianza(RELEASES_URL):
                return
            req = urllib.request.Request(RELEASES_URL, headers={"User-Agent": "guardias-patio"})
            # nosec B310 - la URL se valida en url_de_confianza(): sólo https a GitHub
            with urllib.request.urlopen(req, timeout=5) as r:  # nosec B310
                data = json.loads(r.read())
                latest = data["tag_name"].lstrip("v")
                if _is_newer(latest, current_version):
                    download_url = _find_download_url(data.get("assets", []))
                    callback(latest, download_url, (data.get("body") or "").strip())
        except Exception:
            pass

    Thread(target=_check, daemon=True).start()


#: Extensión del instalador de cada sistema, para no ofrecer a Windows un DMG.
_EXTENSION_POR_SISTEMA = {"Darwin": ".dmg", "Windows": ".exe"}


def _find_download_url(assets: list) -> str:
    """
    Busca el instalador que corresponde a este sistema.

    Antes se buscaba siempre un `.dmg`, así que en Windows el aviso de nueva
    versión no llevaba a ninguna descarga y esos equipos nunca se actualizaban.
    """
    extension = _EXTENSION_POR_SISTEMA.get(platform.system())
    if not extension:
        return ""
    for asset in assets:
        if asset.get("name", "").lower().endswith(extension):
            url = asset.get("browser_download_url", "")
            return url if url_de_confianza(url) else ""
    return ""


#: Nombre anterior, por si alguien lo importaba.
_find_dmg_url = _find_download_url


def _is_newer(latest: str, current: str) -> bool:
    try:
        return tuple(int(x) for x in latest.split(".")) > tuple(int(x) for x in current.split("."))
    except ValueError:
        return False


def abrir_instalador(ruta: str) -> None:
    """Lanza el instalador descargado con lo que entiende cada sistema.

    Se usaba `open` siempre, que sólo existe en macOS: en Windows la descarga
    terminaba y no pasaba nada, así que nadie llegaba a actualizarse.
    """
    import os
    import subprocess

    sistema = platform.system()
    if sistema == "Windows":
        os.startfile(ruta)  # noqa: S606  # nosec B606 - ruta creada por nosotros
    elif sistema == "Darwin":
        subprocess.run(["/usr/bin/open", ruta], check=False)  # nosec B603
    else:
        subprocess.run(["/usr/bin/xdg-open", ruta], check=False)  # nosec B603
