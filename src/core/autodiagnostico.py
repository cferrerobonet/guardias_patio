"""Comprobación de arranque de la aplicación empaquetada.

PyInstaller no ve los imports que se resuelven en tiempo de ejecución ni los
recursos que no son `.py`, así que lo que falta no rompe el arranque: desactiva
una funcionalidad **en silencio** y sólo se descubre en el equipo del usuario,
donde no hay forma de depurar. Ya pasó con el llavero (SEC-001), con la hoja de
estilos (VIS-010) y con las migraciones de Alembic (BLD-010).

Cada comprobación devuelve `None` si todo está en su sitio, o el motivo del
fallo en una frase. Ninguna puede tumbar el arranque: si la propia comprobación
revienta, eso también se cuenta como fallo y la aplicación sigue (BLD-012).
"""

import logging
import os
import sys
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


def _comprobar_llavero() -> Optional[str]:
    """Sin backend de llavero no hay dónde guardar las contraseñas (SEC-001)."""
    from core import credenciales

    if not credenciales.disponible():
        return "no hay almacén de credenciales; las contraseñas no se pueden guardar"
    return None


def _comprobar_hoja_de_estilos() -> Optional[str]:
    """La hoja se empaqueta aparte de los `.py` y se quedó fuera una vez (VIS-010)."""
    from presentation.theme.hoja_de_estilos import RUTA_QSS

    if not RUTA_QSS.exists():
        return f"falta la hoja de estilos ({RUTA_QSS}); la aplicación se vería sin tema"
    return None


def _comprobar_solver() -> Optional[str]:
    """OR-Tools lleva librerías nativas: importar no basta, hay que resolver algo."""
    from ortools.sat.python import cp_model

    modelo = cp_model.CpModel()
    x = modelo.NewBoolVar("x")
    modelo.Add(x == 1)
    solucionador = cp_model.CpSolver()
    solucionador.parameters.max_time_in_seconds = 10.0
    estado = solucionador.Solve(modelo)
    if estado not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return "el motor de asignación no resuelve un modelo trivial"
    return None


def _comprobar_graficas() -> Optional[str]:
    """El backend de matplotlib se elige en tiempo de ejecución, no se ve al importar."""
    import matplotlib.backends.backend_qtagg  # noqa: F401

    return None


def _comprobar_informes() -> Optional[str]:
    """Sin reportlab no hay PDF, y eso no se nota hasta pulsar el botón."""
    import reportlab  # noqa: F401

    return None


def _comprobar_migraciones() -> Optional[str]:
    """`db_manager` busca `alembic.ini` junto al paquete; sin él la BD no migra."""
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    else:
        base = Path(__file__).parent.parent.parent

    if not (base / "alembic.ini").exists():
        return f"falta alembic.ini en {base}; la base de datos no se puede migrar"
    if not (base / "alembic" / "versions").is_dir():
        return f"falta alembic/versions en {base}; la base de datos no se puede migrar"
    return None


def _comprobar_iconos() -> Optional[str]:
    """Las imágenes van como datos del paquete y no las ve ningún import."""
    from core.paths import get_resources_directory

    recursos = get_resources_directory()
    if not recursos.is_dir():
        return f"falta la carpeta de imágenes ({recursos})"
    return None


COMPROBACIONES: tuple[tuple[str, Callable[[], Optional[str]]], ...] = (
    ("Llavero del sistema", _comprobar_llavero),
    ("Hoja de estilos", _comprobar_hoja_de_estilos),
    ("Motor de asignación", _comprobar_solver),
    ("Gráficas", _comprobar_graficas),
    ("Informes PDF", _comprobar_informes),
    ("Migraciones de base de datos", _comprobar_migraciones),
    ("Imágenes e iconos", _comprobar_iconos),
)


def revisar_entorno() -> list[str]:
    """Ejecuta todas las comprobaciones y devuelve los fallos como frases legibles.

    Deja constancia de cada una en el registro, también de las que pasan: cuando
    un usuario manda su log, la lista completa dice de un vistazo qué se cargó y
    qué no en **su** equipo.
    """
    fallos: list[str] = []

    for nombre, comprobar in COMPROBACIONES:
        try:
            motivo = comprobar()
        except Exception as e:  # una comprobación rota no puede impedir el arranque
            motivo = f"{type(e).__name__}: {e}"

        if motivo is None:
            logger.info(f"✓ {nombre}")
        else:
            logger.error(f"✗ {nombre}: {motivo}")
            fallos.append(f"{nombre}: {motivo}")

    if fallos:
        logger.error(f"Autodiagnóstico: {len(fallos)} funcionalidad(es) no disponibles")
    else:
        logger.info("Autodiagnóstico: todo en su sitio")

    return fallos


def debe_avisar_al_usuario() -> bool:
    """Sólo molesta en la aplicación empaquetada, que es donde esto falla.

    En desarrollo todo está en su sitio por definición, así que el aviso sería
    ruido. `GUARDIAS_AUTODIAGNOSTICO=1` lo fuerza para poder probarlo.
    """
    if os.getenv("GUARDIAS_AUTODIAGNOSTICO") == "1":
        return True
    return bool(getattr(sys, "frozen", False))
