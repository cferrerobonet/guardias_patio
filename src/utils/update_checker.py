import json
import platform
import urllib.request
from threading import Thread
from typing import Callable

RELEASES_URL = "https://api.github.com/repos/cferrerobonet/guardias_patio/releases/latest"


def check_for_updates(current_version: str, callback: Callable[[str, str], None]) -> None:
    def _check():
        try:
            req = urllib.request.Request(RELEASES_URL, headers={"User-Agent": "guardias-patio"})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = json.loads(r.read())
                latest = data["tag_name"].lstrip("v")
                if _is_newer(latest, current_version):
                    download_url = _find_download_url(data.get("assets", []))
                    callback(latest, download_url)
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
            return asset.get("browser_download_url", "")
    return ""


#: Nombre anterior, por si alguien lo importaba.
_find_dmg_url = _find_download_url


def _is_newer(latest: str, current: str) -> bool:
    try:
        return tuple(int(x) for x in latest.split(".")) > tuple(int(x) for x in current.split("."))
    except ValueError:
        return False
