"""Calendarios de guardias para consultar desde el navegador (FUN-009).

Decisión de producto de CarlosFB (2026-09-06): **páginas estáticas**, no una
aplicación web. No hace falta servidor, ni base de datos compartida, ni
contraseñas que mantener; basta con subir una carpeta al hosting del centro.

Cada profesor recibe una dirección propia con un identificador largo. El
identificador se calcula con una clave secreta que se guarda junto a los datos
del usuario, así que **no cambia** entre publicaciones: quien se suscriba al
calendario una vez lo tiene para todo el curso.

Esto protege de que alguien adivine la dirección de otro, no de que alguien
reenvíe la suya. Para un horario de guardias es suficiente; no lo sería para
datos personales de más peso.
"""

import hashlib
import hmac
import html
import secrets
from collections import defaultdict
from pathlib import Path
from typing import Optional

from core.logging import get_logger
from infrastructure.database.models import Guardia, Profesor

logger = get_logger(__name__)

NOMBRE_DE_LA_CLAVE = "clave_publicacion_web.txt"

#: Longitud del identificador de cada dirección. Con 32 caracteres hexadecimales
#: hay 16 bytes de entropía: probar direcciones al azar no lleva a ningún sitio.
LARGO_DEL_ENLACE = 32

DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
MESES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


def clave_de_publicacion(session) -> Optional[bytes]:
    """Secreto del que salen las direcciones, guardado junto a la base de datos.

    Se crea la primera vez y no se vuelve a tocar: si cambiara, cambiarían todas
    las direcciones y las suscripciones al calendario dejarían de funcionar.
    """
    from services.papelera_guardias import ruta_de_la_papelera

    referencia = ruta_de_la_papelera(session)
    if referencia is None:
        return None
    ruta = referencia.parent / NOMBRE_DE_LA_CLAVE
    try:
        if ruta.exists():
            return ruta.read_text(encoding="utf-8").strip().encode("utf-8")
        clave = secrets.token_hex(32)
        ruta.write_text(clave, encoding="utf-8")
        from core.paths import proteger_fichero_de_credenciales

        proteger_fichero_de_credenciales(ruta)
        logger.info("Creada la clave de publicación web")
        return clave.encode("utf-8")
    except OSError as e:
        logger.warning(f"No se pudo leer ni crear la clave de publicación: {e}")
        return None


def enlace_de(profesor_id: int, clave: bytes) -> str:
    """Identificador estable y no adivinable de la página de un profesor."""
    firma = hmac.new(clave, str(profesor_id).encode("utf-8"), hashlib.sha256)
    return firma.hexdigest()[:LARGO_DEL_ENLACE]


def publicar(session, destino, nombre_centro: str = "EPLA") -> dict:
    """Escribe en `destino` una página y un calendario por profesor.

    Devuelve `{"publicados": n, "sin_guardias": n, "enlaces": [(nombre, correo,
    fichero)], "carpeta": ruta}`. La lista de enlaces es lo que hace falta para
    avisar a cada uno; no se escribe ninguna página índice, porque enumerar las
    direcciones de todos anularía el motivo de que sean secretas.
    """
    from services.icalendar_service import ICalendarService

    carpeta = Path(destino)
    carpeta.mkdir(parents=True, exist_ok=True)

    clave = clave_de_publicacion(session)
    if clave is None:
        raise ValueError(
            "No se puede publicar sin una clave estable: las direcciones cambiarían "
            "en cada publicación y las suscripciones dejarían de funcionar."
        )

    resumen = {"publicados": 0, "sin_guardias": 0, "enlaces": [], "carpeta": carpeta}
    profesores = (
        session.query(Profesor)
        .filter(Profesor.activo.is_(True))
        .order_by(Profesor.nombre_completo)
        .all()
    )

    for profesor in profesores:
        guardias = (
            session.query(Guardia)
            .filter(Guardia.profesor_id == profesor.id)
            .order_by(Guardia.fecha, Guardia.recreo)
            .all()
        )
        if not guardias:
            resumen["sin_guardias"] += 1
            continue

        enlace = enlace_de(profesor.id, clave)
        (carpeta / f"{enlace}.html").write_text(
            _pagina(profesor, guardias, enlace, nombre_centro), encoding="utf-8"
        )
        ICalendarService.generar_icalendar_profesor(
            session, profesor.id, str(carpeta / f"{enlace}.ics"), nombre_centro
        )
        resumen["publicados"] += 1
        resumen["enlaces"].append(
            (profesor.nombre_completo, profesor.email_corporativo or "", f"{enlace}.html")
        )

    logger.info(
        f"Publicados {resumen['publicados']} calendarios en {carpeta} "
        f"({resumen['sin_guardias']} profesores sin guardias)"
    )
    return resumen


def _fecha_larga(fecha) -> str:
    return f"{DIAS[fecha.weekday()]} {fecha.day} de {MESES[fecha.month - 1]}"


def _pagina(profesor, guardias, enlace: str, nombre_centro: str) -> str:
    """Una página por profesor, sin scripts ni recursos externos.

    Se abre igual desde el móvil que desde un ordenador y no depende de que el
    hosting sirva nada más que ficheros.
    """
    por_mes = defaultdict(list)
    for guardia in guardias:
        por_mes[(guardia.fecha.year, guardia.fecha.month)].append(guardia)

    bloques = []
    for (anio, mes), guardias_del_mes in sorted(por_mes.items()):
        filas = "".join(
            "<tr>"
            f"<td>{html.escape(_fecha_larga(g.fecha))}</td>"
            f"<td>{html.escape(str(g.turno))}</td>"
            f"<td>Recreo {g.recreo}</td>"
            f"<td>{html.escape(getattr(g.zona, 'nombre_zona', None) or '—')}</td>"
            "</tr>"
            for g in guardias_del_mes
        )
        bloques.append(
            f"<h2>{MESES[mes - 1].capitalize()} {anio}</h2>"
            "<table><thead><tr><th>Día</th><th>Turno</th><th>Recreo</th>"
            f"<th>Zona</th></tr></thead><tbody>{filas}</tbody></table>"
        )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Guardias de patio — {html.escape(profesor.nombre_completo)}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
         margin: 0 auto; max-width: 46rem; padding: 1.5rem; line-height: 1.5; }}
  h1 {{ font-size: 1.35rem; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.05rem; margin-top: 2rem; }}
  p.centro {{ color: #6B7280; margin-top: 0; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.95rem; }}
  th {{ background: #0E5FA8; color: #fff; text-align: left; padding: 0.5rem 0.6rem; }}
  td {{ padding: 0.45rem 0.6rem; border-bottom: 1px solid #E1E4E8; }}
  tr:nth-child(even) td {{ background: rgba(0,0,0,0.03); }}
  .suscribir {{ display: inline-block; margin: 1.5rem 0; padding: 0.6rem 1rem;
                background: #0E5FA8; color: #fff; text-decoration: none;
                border-radius: 4px; }}
  footer {{ margin-top: 2.5rem; font-size: 0.85rem; color: #6B7280; }}
  @media (max-width: 30rem) {{ body {{ padding: 1rem; }} table {{ font-size: 0.85rem; }} }}
</style>
</head>
<body>
<h1>Guardias de patio de {html.escape(profesor.nombre_completo)}</h1>
<p class="centro">{html.escape(nombre_centro)} · {len(guardias)} guardias en el curso</p>
<a class="suscribir" href="{enlace}.ics">Añadir a mi calendario</a>
{"".join(bloques)}
<footer>
  <p>Esta dirección es solo tuya: no la compartas si no quieres que otros vean
  tus guardias.</p>
  <p>Si algo no cuadra, habla con jefatura: esta página es una copia de consulta
  y no se puede editar desde aquí.</p>
</footer>
</body>
</html>
"""
