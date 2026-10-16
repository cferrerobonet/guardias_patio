"""Límite de intentos de conexión con el servidor de sincronización.

El servidor corta el acceso por el puerto 22 a quien encadena conexiones. Tras un
rechazo o un fallo, volver a intentarlo en bucle —el latido de la sesión cada 30 s,
cada fichero de una sincronización, «Probar conexión» pulsado varias veces— es justo
lo que dispara ese bloqueo, y entonces deja de funcionar también en los demás equipos
del centro.

Aquí se lleva la cuenta de los fallos seguidos: tras cada uno, la espera antes del
siguiente intento se dobla (30 s, 1 min, 2 min… hasta 15 min) y, tras cinco en la
misma sesión, la aplicación deja de intentarlo por su cuenta hasta el próximo
arranque; solo lo vuelve a intentar quien lo pide, y respetando la espera. Una
conexión buena pone la cuenta a cero. Se guarda en disco para que cerrar y abrir la
aplicación no la reinicie.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

#: Espera tras el primer fallo, en segundos; se dobla con cada fallo seguido.
ESPERA_INICIAL = 30
#: Tope de la espera entre dos intentos.
ESPERA_MAXIMA = 15 * 60
#: Fallos seguidos en una sesión tras los que la app deja de intentarlo sola.
TOPE_AUTOMATICO = 5


def espera_tras(fallos: int) -> int:
    """Segundos que hay que esperar después de `fallos` fallos seguidos."""
    if fallos <= 0:
        return 0
    return min(ESPERA_INICIAL * 2 ** (fallos - 1), ESPERA_MAXIMA)


def _texto_de_espera(segundos: float) -> str:
    segundos = max(1, int(round(segundos)))
    if segundos < 60:
        return f"{segundos} s"
    minutos = (segundos + 59) // 60
    return f"{minutos} min"


class LimiteDeConexiones:
    """Cuenta de fallos seguidos y espera creciente antes de volver a conectar."""

    def __init__(
        self,
        ruta: Optional[Path] = None,
        reloj: Callable[[], float] = time.time,
    ):
        self._ruta = ruta
        self._reloj = reloj
        self._cerrojo = threading.Lock()
        self._cargado = False
        self._fallos = 0
        self._ultimo_fallo = 0.0
        self._fallos_en_sesion = 0

    # --- Estado en disco ---------------------------------------------------

    def _ruta_del_estado(self) -> Path:
        if self._ruta is None:
            from core.paths import get_data_directory

            self._ruta = get_data_directory() / "limite_conexiones.json"
        return self._ruta

    def _cargar(self) -> None:
        if self._cargado:
            return
        self._cargado = True
        try:
            datos = json.loads(self._ruta_del_estado().read_text(encoding="utf-8"))
            self._fallos = max(0, int(datos.get("fallos", 0)))
            self._ultimo_fallo = float(datos.get("ultimo_fallo", 0.0))
        except FileNotFoundError:
            return
        except (OSError, ValueError, TypeError, AttributeError) as e:
            logger.warning(f"No se pudo leer el límite de conexiones; se empieza de cero: {e}")
            self._fallos, self._ultimo_fallo = 0, 0.0

    def _guardar(self) -> None:
        try:
            ruta = self._ruta_del_estado()
            ruta.parent.mkdir(parents=True, exist_ok=True)
            ruta.write_text(
                json.dumps({"fallos": self._fallos, "ultimo_fallo": self._ultimo_fallo}),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning(f"No se pudo guardar el límite de conexiones: {e}")

    # --- Consulta ----------------------------------------------------------

    @property
    def fallos_seguidos(self) -> int:
        with self._cerrojo:
            self._cargar()
            return self._fallos

    def segundos_de_espera(self) -> float:
        """Lo que falta para poder volver a intentarlo (0 si ya se puede)."""
        with self._cerrojo:
            self._cargar()
            return self._segundos_de_espera()

    def _segundos_de_espera(self) -> float:
        if self._fallos <= 0:
            return 0.0
        ahora = self._reloj()
        if ahora < self._ultimo_fallo:
            # Reloj atrasado desde el último fallo: se cuenta desde ahora.
            self._ultimo_fallo = ahora
        return max(0.0, self._ultimo_fallo + espera_tras(self._fallos) - ahora)

    def puede_intentar(self, automatico: bool = True) -> bool:
        """¿Se puede abrir ya una conexión?

        `automatico` es lo que la app hace sola (latido, subidas, reconexiones);
        tras `TOPE_AUTOMATICO` fallos seguidos en la sesión se le dice que no
        hasta el próximo arranque. Lo que pide una persona solo espera.
        """
        with self._cerrojo:
            self._cargar()
            if automatico and self._fallos_en_sesion >= TOPE_AUTOMATICO:
                return False
            return self._segundos_de_espera() <= 0

    def motivo(self, automatico: bool = True) -> str:
        """Por qué no se conecta ahora, en palabras para quien usa la app."""
        with self._cerrojo:
            self._cargar()
            if automatico and self._fallos_en_sesion >= TOPE_AUTOMATICO:
                return (
                    f"La conexión con el servidor ha fallado {self._fallos_en_sesion} veces "
                    "seguidas y no se volverá a intentar sola hasta que se abra de nuevo la "
                    "aplicación, para que el servidor no bloquee el acceso."
                )
            espera = self._segundos_de_espera()
            if espera <= 0:
                return ""
            return (
                "La última conexión con el servidor falló. Para que el servidor no bloquee "
                f"el acceso, no se volverá a intentar hasta dentro de {_texto_de_espera(espera)}."
            )

    # --- Resultado de un intento -------------------------------------------

    def registrar_fallo(self) -> None:
        with self._cerrojo:
            self._cargar()
            self._fallos += 1
            self._fallos_en_sesion += 1
            self._ultimo_fallo = self._reloj()
            self._guardar()
            logger.warning(
                f"Conexión con el servidor fallida ({self._fallos} seguidas): "
                f"próximo intento dentro de {espera_tras(self._fallos)} s como pronto"
            )

    def registrar_exito(self) -> None:
        with self._cerrojo:
            self._cargar()
            if self._fallos == 0 and self._fallos_en_sesion == 0:
                return
            self._fallos = 0
            self._fallos_en_sesion = 0
            self._ultimo_fallo = 0.0
            self._guardar()


_limite: Optional[LimiteDeConexiones] = None
_cerrojo_global = threading.Lock()


def limite_sftp() -> LimiteDeConexiones:
    """El límite común a todas las conexiones SFTP del proceso."""
    global _limite
    with _cerrojo_global:
        if _limite is None:
            _limite = LimiteDeConexiones()
        return _limite


def usar_limite(limite: Optional[LimiteDeConexiones]) -> None:
    """Sustituye el límite común (las pruebas usan uno con su propia ruta y reloj)."""
    global _limite
    with _cerrojo_global:
        _limite = limite
