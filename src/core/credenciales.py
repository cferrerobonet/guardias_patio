"""Contraseñas en el llavero del sistema, no en un fichero de texto (SEC-001).

El `.env` guardaba las contraseñas de SFTP y de correo en claro, sobrevivía a
desinstalar la aplicación y en Windows no tenía más protección que el perfil de
usuario: `os.chmod` no aplica permisos POSIX ahí.

Aquí las contraseñas van al llavero del sistema —Keychain en macOS, Administrador
de credenciales en Windows, Secret Service en Linux— y el `.env` se queda solo
con lo que no es secreto: servidor, puerto, usuario y carpeta.

Si no hay llavero disponible (un Linux sin escritorio, por ejemplo) se sigue
usando el `.env`, porque quedarse sin poder sincronizar es peor que guardar la
contraseña como se guardaba hasta ahora. Eso sí, se dice en el registro.
"""

import os
from pathlib import Path
from typing import List, Optional

from core.logging import get_logger

logger = get_logger(__name__)

#: Nombre con el que la aplicación aparece en el llavero del sistema.
SERVICIO = "GuardiasDePatio"

#: Lo que nunca debe acabar escrito en el `.env`.
CLAVES_SECRETAS = ("SFTP_PASSWORD", "SMTP_PASSWORD")


def _llavero():
    """El módulo `keyring` si hay un almacén utilizable, o None."""
    try:
        import keyring
        from keyring.backends.fail import Keyring as SinLlavero
    except ImportError:
        return None
    try:
        if isinstance(keyring.get_keyring(), SinLlavero):
            return None
    except Exception as e:  # noqa: BLE001 - el backend puede fallar de mil formas
        logger.warning(f"No hay llavero del sistema utilizable: {e}")
        return None
    return keyring


def disponible() -> bool:
    """True si el equipo tiene un llavero donde guardar contraseñas."""
    return _llavero() is not None


def _errores_del_llavero() -> tuple:
    """Lo que puede fallar al hablar con el almacén: llavero bloqueado, permiso
    denegado, entrada inexistente. Cada sistema lanza los suyos, todos bajo
    `KeyringError`."""
    try:
        from keyring.errors import KeyringError

        return (KeyringError, OSError)
    except ImportError:
        return (OSError,)


def guardar(nombre: str, valor: str) -> bool:
    """Guarda un secreto en el llavero. False si no se ha podido."""
    llavero = _llavero()
    if llavero is None:
        return False
    try:
        if valor:
            llavero.set_password(SERVICIO, nombre, valor)
        else:
            borrar(nombre)
        return True
    except _errores_del_llavero() as e:
        logger.warning(f"No se pudo guardar {nombre} en el llavero: {e}")
        return False


def leer(nombre: str) -> Optional[str]:
    """Devuelve el secreto guardado, o None si no está o no hay llavero."""
    llavero = _llavero()
    if llavero is None:
        return None
    try:
        guardado: Optional[str] = llavero.get_password(SERVICIO, nombre)
        return guardado
    except _errores_del_llavero() as e:
        logger.warning(f"No se pudo leer {nombre} del llavero: {e}")
        return None


def borrar(nombre: str) -> None:
    llavero = _llavero()
    if llavero is None:
        return
    try:
        llavero.delete_password(SERVICIO, nombre)
    except _errores_del_llavero():
        pass  # no estar guardado no es un error


def obtener(nombre: str, por_defecto: str = "") -> str:
    """El secreto, mirando primero el llavero y después el entorno.

    El orden importa: un `.env` viejo puede seguir teniendo la contraseña
    antigua después de haberla cambiado desde Ajustes.
    """
    del_llavero = leer(nombre)
    if del_llavero:
        return del_llavero
    return os.getenv(nombre, por_defecto)


def migrar_desde_env(ruta_env: Path) -> List[str]:
    """Lleva al llavero las contraseñas que aún estén en el `.env`.

    Devuelve los nombres migrados. La línea se deja vacía en vez de borrarla,
    para que se vea que esa clave ya no vive ahí.
    """
    if not ruta_env.exists() or not disponible():
        return []

    try:
        lineas = ruta_env.read_text(encoding="utf-8").splitlines(keepends=True)
    except OSError as e:
        logger.warning(f"No se pudo leer {ruta_env.name} para migrar: {e}")
        return []

    migradas = []
    for i, linea in enumerate(lineas):
        for clave in CLAVES_SECRETAS:
            if not linea.startswith(f"{clave}="):
                continue
            valor = linea.split("=", 1)[1].strip()
            if valor and guardar(clave, valor):
                lineas[i] = f"{clave}=\n"
                migradas.append(clave)

    if migradas:
        try:
            ruta_env.write_text("".join(lineas), encoding="utf-8")
            from core.paths import proteger_fichero_de_credenciales

            proteger_fichero_de_credenciales(ruta_env)
            logger.info(f"Contraseñas llevadas al llavero del sistema: {', '.join(migradas)}")
        except OSError as e:
            logger.warning(f"No se pudo limpiar {ruta_env.name} tras migrar: {e}")
    return migradas


def guardar_configuracion(variables: dict) -> None:
    """Punto único para guardar la configuración de servidor y correo.

    Las contraseñas van al llavero; el resto, al `.env` de la carpeta de datos
    del usuario. Antes había tres sitios escribiendo el fichero y dos de ellos
    usaban la ruta relativa `".env"`, que en la aplicación instalada apunta al
    directorio de trabajo y no a donde de verdad se lee la configuración.
    """
    from core.paths import get_base_directory, proteger_fichero_de_credenciales

    al_fichero = {}
    for clave, valor in variables.items():
        if clave in CLAVES_SECRETAS and guardar(clave, valor):
            # Se escribe vacía para que un `.env` anterior no siga mandando.
            al_fichero[clave] = ""
        else:
            al_fichero[clave] = valor
            if clave in CLAVES_SECRETAS:
                logger.warning(
                    f"{clave} se guarda en el fichero: este equipo no tiene llavero"
                )

    ruta = get_base_directory() / ".env"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    lineas = ruta.read_text(encoding="utf-8").splitlines(keepends=True) if ruta.exists() else []

    puestas = set()
    for i, linea in enumerate(lineas):
        for clave, valor in al_fichero.items():
            if linea.startswith(f"{clave}="):
                lineas[i] = f"{clave}={valor}\n"
                puestas.add(clave)
                break
    for clave, valor in al_fichero.items():
        if clave not in puestas:
            lineas.append(f"{clave}={valor}\n")

    ruta.write_text("".join(lineas), encoding="utf-8")
    proteger_fichero_de_credenciales(ruta)

    # El proceso ya en marcha tiene que ver los valores nuevos sin reiniciar.
    for clave, valor in variables.items():
        if valor:
            os.environ[clave] = valor
    logger.info(f"Configuración guardada ({len(variables)} valores)")
