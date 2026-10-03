import json
import logging
import platform
import ssl
import urllib.request
from threading import Thread
from typing import Callable

logger = logging.getLogger(__name__)

RELEASES_URL = "https://api.github.com/repos/cferrerobonet/guardias_patio/releases/latest"

#: Plan B sin API. La API sin autenticar admite 60 consultas por hora y por IP
#: pública: en el centro todos los equipos salen por la misma y cada arranque
#: gasta dos, así que se agotaba, GitHub respondía 403 y el aviso de versión
#: nueva no salía (2026-10-03). Esta página redirige a `.../tag/vX.Y.Z`.
RELEASES_WEB = "https://github.com/cferrerobonet/guardias_patio/releases/latest"
DESCARGAS_WEB = "https://github.com/cferrerobonet/guardias_patio/releases/download"

#: Nombre fijo del instalador de cada sistema (Makefile e `installer_windows.iss`).
_INSTALADOR_POR_SISTEMA = {
    "Darwin": "GuardiasPatio_v{v}_macOS.dmg",
    "Windows": "GuardiasDePatio-{v}-Windows-Setup.exe",
}

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


def contexto_ssl() -> ssl.SSLContext:
    """Contexto TLS que verifica con los certificados raíz de `certifi`.

    El OpenSSL que viaja en el DMG busca los certificados en la carpeta del
    Python con el que se compiló (`/Library/Frameworks/Python.framework/…`),
    que no existe en el Mac del usuario: la petición a GitHub moría con
    «CERTIFICATE_VERIFY_FAILED», se tragaba en silencio y nadie se enteraba de
    que había versión nueva. `certifi` ya va dentro del paquete (BLD-018).
    """
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:  # sin certifi, lo que sepa el sistema
        return ssl.create_default_context()


def check_for_updates(current_version: str, callback: Callable[[str, str, str], None]) -> None:
    """Avisa de una versión nueva con `(version, url_de_descarga, notas)`.

    Las notas son el cuerpo del release: sin ellas el aviso pide instalar algo
    sin decir qué cambia (FUN-011).
    """

    def _check():
        try:
            latest, download_url, notas, fuente = _ultima_version()
        except Exception as e:  # noqa: BLE001 - nunca debe tumbar la interfaz
            # Antes se tragaba sin más y un fallo de certificado era invisible.
            logger.warning("No se pudo comprobar si hay versión nueva: %s", e)
            return
        # El éxito también se anota: sin esto no había forma de saber, mirando
        # el registro de un equipo, si la comprobación funcionaba.
        logger.info(
            "Versión instalada %s, última publicada %s (vía %s)", current_version, latest, fuente
        )
        if _is_newer(latest, current_version):
            callback(latest, download_url, notas)

    Thread(target=_check, daemon=True).start()


#: Extensión del instalador de cada sistema, para no ofrecer a Windows un DMG.
_EXTENSION_POR_SISTEMA = {"Darwin": ".dmg", "Windows": ".exe"}


def _abrir(url: str):
    if not url_de_confianza(url):
        raise ValueError(f"URL no permitida: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "guardias-patio"})
    # nosec B310 - la URL se valida en url_de_confianza(): sólo https a GitHub
    return urllib.request.urlopen(req, timeout=5, context=contexto_ssl())  # nosec B310


def _ultima_version() -> tuple[str, str, str, str]:
    """`(versión, url del instalador, notas, fuente)`: la API y, si falla, la web."""
    try:
        with _abrir(RELEASES_URL) as r:
            data = json.loads(r.read())
        return (
            data["tag_name"].lstrip("v"),
            _find_download_url(data.get("assets", [])),
            (data.get("body") or "").strip(),
            "api",
        )
    except Exception as e:  # noqa: BLE001 - límite de la API, red o respuesta rara
        logger.info("La API de GitHub no respondió (%s); se pregunta a la web", e)
    with _abrir(RELEASES_WEB) as r:
        destino = r.geturl()
    if "/tag/" not in destino:
        raise ValueError(f"La web no redirigió a una versión: {destino}")
    version = destino.rsplit("/tag/", 1)[1].lstrip("v")
    plantilla = _INSTALADOR_POR_SISTEMA.get(platform.system())
    url = f"{DESCARGAS_WEB}/v{version}/{plantilla.format(v=version)}" if plantilla else ""
    return version, url, "", "web"


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
