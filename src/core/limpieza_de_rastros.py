"""Borra lo que dejaron por el equipo las versiones anteriores (SEC-001).

Hasta la 5.95.0 la aplicación guardaba las contraseñas en el `.env`, a veces con
permisos de lectura para todo el mundo, y los volcados que subía al servidor
llevaban dentro un bloque con las credenciales —en las versiones más antiguas
codificadas en base64, que no es cifrado—. Actualizar no quita nada de eso: los
ficheros siguen ahí.

Esto los busca y los limpia, en macOS y en Windows, **sólo si las contraseñas ya
están a salvo en el llavero**. Si la migración no ha podido hacerse, no se toca
nada: sería cambiar un riesgo por una pérdida.

Regla que no se salta nunca: no se borra ninguna carpeta que pueda contener
datos. Una carpeta heredada con una base de datos que no esté vacía se deja
donde está y se avisa.
"""

import json
import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from core.logging import get_logger

logger = get_logger(__name__)

#: Nombre de las carpetas por usuario: 16 caracteres hexadecimales.
CARPETA_DE_USUARIO = re.compile(r"^[0-9a-f]{16}$")

BLOQUES_DE_CREDENCIALES = ("sftp_config", "smtp_config")

VOLCADO = "guardias_patio_data.json"


@dataclass
class Informe:
    """Qué se ha hecho, o qué se haría. Todo en frases para el registro."""

    hecho: List[str] = field(default_factory=list)
    pendiente: List[str] = field(default_factory=list)
    motivo_de_no_actuar: Optional[str] = None

    @property
    def hubo_cambios(self) -> bool:
        return bool(self.hecho)


def _permisos_abiertos(ruta: Path) -> bool:
    """True si alguien que no sea el dueño puede leer el fichero.

    En Windows los bits POSIX no significan nada, así que allí no se comprueba:
    la protección la da el perfil de usuario.
    """
    if os.name == "nt":
        return False
    try:
        return bool(stat.S_IMODE(ruta.stat().st_mode) & 0o077)
    except OSError:
        return False


def _es_seguro_limpiar() -> tuple:
    """¿Están ya las contraseñas en el llavero? Devuelve `(sí, motivo)`."""
    from core.credenciales import CLAVES_SECRETAS, disponible, leer

    if not disponible():
        return False, "este equipo no tiene llavero donde guardar las contraseñas"
    if not any(leer(clave) for clave in CLAVES_SECRETAS):
        return False, "todavía no hay ninguna contraseña en el llavero"
    return True, None


def _carpetas_heredadas(datos: Path) -> List[Path]:
    """Carpetas por usuario colgando de `data/` en vez de `data/users/`.

    Es el esquema de antes de la 5.x: quedaron ahí con el volcado dentro.
    """
    if not datos.is_dir():
        return []
    return [
        hijo
        for hijo in datos.iterdir()
        if hijo.is_dir() and CARPETA_DE_USUARIO.match(hijo.name)
    ]


def _tiene_datos(carpeta: Path) -> bool:
    """True si la carpeta guarda una base de datos con algo dentro."""
    base = carpeta / "guardias_patio.db"
    try:
        return base.exists() and base.stat().st_size > 0
    except OSError:
        return True  # ante la duda, se conserva


def _quitar_credenciales_del_volcado(ruta: Path) -> List[str]:
    """Saca los bloques de credenciales de un volcado, dejando los datos."""
    try:
        contenido = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudo leer {ruta.name}: {e}")
        return []
    if not isinstance(contenido, dict):
        return []

    quitados = [b for b in BLOQUES_DE_CREDENCIALES if contenido.get(b)]
    if not quitados:
        return []
    for bloque in quitados:
        contenido.pop(bloque, None)
    try:
        ruta.write_text(json.dumps(contenido, ensure_ascii=False, indent=2), encoding="utf-8")
        _proteger(ruta)
    except OSError as e:
        logger.warning(f"No se pudo reescribir {ruta.name}: {e}")
        return []
    return quitados


def _proteger(ruta: Path) -> None:
    from core.paths import proteger_fichero_de_credenciales

    proteger_fichero_de_credenciales(ruta)


def revisar_y_limpiar(base: Optional[Path] = None, solo_mirar: bool = False) -> Informe:
    """Recorre la carpeta de datos y quita los rastros que dejaron atrás.

    Con `solo_mirar` no cambia nada: sirve para poder enseñar antes qué se va a
    tocar. Devuelve un `Informe` con lo hecho y lo que se ha dejado a propósito.
    """
    from core.credenciales import migrar_desde_env
    from core.paths import get_base_directory

    base = Path(base) if base else get_base_directory()
    informe = Informe()

    # 1. Las contraseñas del `.env`, al llavero. Es lo que habilita el resto.
    env = base / ".env"
    if env.exists() and not solo_mirar:
        migradas = migrar_desde_env(env)
        if migradas:
            informe.hecho.append(
                f"contraseñas llevadas al llavero: {', '.join(migradas)}"
            )

    seguro, motivo = _es_seguro_limpiar()
    if not seguro:
        informe.motivo_de_no_actuar = motivo
        logger.info(f"Limpieza de rastros omitida: {motivo}")
        return informe

    # 2. El `.env` no puede quedar legible por otras cuentas del equipo.
    if env.exists() and _permisos_abiertos(env):
        if solo_mirar:
            informe.pendiente.append(".env con permisos de lectura para otras cuentas")
        else:
            _proteger(env)
            informe.hecho.append("permisos del .env restringidos a tu usuario")

    datos = base / "data"

    # 3. Carpetas del esquema antiguo. Sólo las que no guardan nada.
    for carpeta in _carpetas_heredadas(datos):
        if _tiene_datos(carpeta):
            informe.pendiente.append(
                f"carpeta heredada {carpeta.name} con base de datos: se conserva, revísala a mano"
            )
            continue
        if solo_mirar:
            informe.pendiente.append(f"carpeta heredada vacía {carpeta.name}")
            continue
        try:
            import shutil

            shutil.rmtree(carpeta)
            informe.hecho.append(f"carpeta heredada vacía eliminada: {carpeta.name}")
        except OSError as e:
            logger.warning(f"No se pudo eliminar {carpeta}: {e}")

    # 4. Volcados con el bloque de credenciales dentro, estén donde estén.
    if datos.is_dir():
        for volcado in datos.rglob(VOLCADO):
            if solo_mirar:
                try:
                    contenido = json.loads(volcado.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                if isinstance(contenido, dict) and any(
                    contenido.get(b) for b in BLOQUES_DE_CREDENCIALES
                ):
                    informe.pendiente.append(f"credenciales dentro de {volcado.parent.name}")
                continue
            quitados = _quitar_credenciales_del_volcado(volcado)
            if quitados:
                informe.hecho.append(
                    f"credenciales quitadas del volcado de {volcado.parent.name} "
                    f"({', '.join(quitados)})"
                )

    if informe.hecho:
        logger.info("Limpieza de rastros: " + "; ".join(informe.hecho))
    for aviso in informe.pendiente:
        logger.warning(f"Limpieza de rastros, sin tocar: {aviso}")
    return informe
