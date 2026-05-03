import json
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
                    download_url = _find_dmg_url(data.get("assets", []))
                    callback(latest, download_url)
        except Exception:
            pass

    Thread(target=_check, daemon=True).start()


def _find_dmg_url(assets: list) -> str:
    for asset in assets:
        name = asset.get("name", "")
        if name.endswith(".dmg"):
            return asset.get("browser_download_url", "")
    return ""


def _is_newer(latest: str, current: str) -> bool:
    try:
        return tuple(int(x) for x in latest.split(".")) > tuple(int(x) for x in current.split("."))
    except ValueError:
        return False
