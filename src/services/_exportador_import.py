"""
Implementación de las funciones de importación de datos.
Extraído de exportador.py para reducir el tamaño del módulo principal.
No importa desde exportador.py (evita importaciones circulares).
"""

import base64
import json
import os
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.exc import SQLAlchemyError

from core.logging import get_logger
from infrastructure.database.models import Ausencia, Configuracion, Guardia, Profesor, Zona

logger = get_logger(__name__)

_FERNET_KEY_ENV = "GUARDIAS_FERNET_KEY"


# ---------------------------------------------------------------------------
# Helpers (independientes de ExportadorDatos)
# ---------------------------------------------------------------------------


def _get_fernet() -> Fernet:
    key = os.environ.get(_FERNET_KEY_ENV)
    if not key:
        key_path = Path.home() / ".guardias_patio_key"
        if key_path.exists():
            key = key_path.read_text().strip()
        else:
            key = Fernet.generate_key().decode()
            key_path.write_text(key)
            key_path.chmod(0o600)
    return Fernet(key.encode() if isinstance(key, str) else key)


def _desencriptar_password(encrypted_password: str) -> str:
    if not encrypted_password:
        return ""
    try:
        return _get_fernet().decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        try:
            return base64.b64decode(encrypted_password.encode("utf-8")).decode("utf-8")
        except (ValueError, TypeError, OSError, UnicodeDecodeError):
            return encrypted_password


def _deserializar_fecha(fecha_str: Optional[str]) -> Optional[date]:
    return date.fromisoformat(fecha_str) if fecha_str else None


def _deserializar_hora(hora_str: Optional[str]) -> Optional[time]:
    if not hora_str:
        return None
    h, m = hora_str.split(":")
    return time(int(h), int(m))


# ---------------------------------------------------------------------------
# Funciones de importación
# ---------------------------------------------------------------------------


def importar_profesores(
    session, profesores_data: list[dict[str, Any]], limpiar: bool = False
) -> int:
    if limpiar:
        session.query(Guardia).delete()
        session.query(Ausencia).delete()
        session.flush()
        session.query(Profesor).delete()
        session.commit()
        session.expunge_all()

    count = 0
    for p_data in profesores_data:
        if "nombre_completo" in p_data:
            nombre_completo = p_data["nombre_completo"]
        elif "nombre" in p_data and "apellidos" in p_data:
            nombre_completo = f"{p_data['apellidos']}, {p_data['nombre']}"
        else:
            continue

        if "id" in p_data:
            existing = session.query(Profesor).filter_by(id=p_data["id"]).first()
            if existing:
                existing.nombre_completo = nombre_completo
                existing.email_corporativo = p_data.get("email_corporativo")
                existing.horas_contrato = p_data["horas_contrato"]
                existing.porcentaje_jornada = p_data["porcentaje_jornada"]
                existing.turno = p_data["turno"]
                existing.horas_manana = p_data.get("horas_manana")
                existing.horas_tarde = p_data.get("horas_tarde")
                existing.tutor = p_data.get("tutor", False)
                existing.activo = p_data.get("activo", True)
                existing.fecha_inicio_guardias = _deserializar_fecha(
                    p_data.get("fecha_inicio_guardias")
                )
                existing.fecha_fin_guardias = _deserializar_fecha(
                    p_data.get("fecha_fin_guardias")
                )
                existing.zona_preferida_id = p_data.get("zona_preferida_id")
                existing.dias_semana_permitidos = p_data.get("dias_semana_permitidos")
                existing.recreos_permitidos = p_data.get("recreos_permitidos")
            else:
                profesor = Profesor(
                    id=p_data["id"],
                    nombre_completo=nombre_completo,
                    email_corporativo=p_data.get("email_corporativo"),
                    horas_contrato=p_data["horas_contrato"],
                    porcentaje_jornada=p_data["porcentaje_jornada"],
                    turno=p_data["turno"],
                    horas_manana=p_data.get("horas_manana"),
                    horas_tarde=p_data.get("horas_tarde"),
                    tutor=p_data.get("tutor", False),
                    activo=p_data.get("activo", True),
                    fecha_inicio_guardias=_deserializar_fecha(p_data.get("fecha_inicio_guardias")),
                    fecha_fin_guardias=_deserializar_fecha(p_data.get("fecha_fin_guardias")),
                    zona_preferida_id=p_data.get("zona_preferida_id"),
                    dias_semana_permitidos=p_data.get("dias_semana_permitidos"),
                    recreos_permitidos=p_data.get("recreos_permitidos"),
                )
                session.add(profesor)
        else:
            profesor = Profesor(
                nombre_completo=nombre_completo,
                email_corporativo=p_data.get("email_corporativo"),
                horas_contrato=p_data["horas_contrato"],
                porcentaje_jornada=p_data["porcentaje_jornada"],
                turno=p_data["turno"],
                horas_manana=p_data.get("horas_manana"),
                horas_tarde=p_data.get("horas_tarde"),
                tutor=p_data.get("tutor", False),
                activo=p_data.get("activo", True),
                fecha_inicio_guardias=_deserializar_fecha(p_data.get("fecha_inicio_guardias")),
                fecha_fin_guardias=_deserializar_fecha(p_data.get("fecha_fin_guardias")),
                zona_preferida_id=p_data.get("zona_preferida_id"),
                dias_semana_permitidos=p_data.get("dias_semana_permitidos"),
                recreos_permitidos=p_data.get("recreos_permitidos"),
            )
            session.add(profesor)
        count += 1

    session.commit()
    return count


def importar_zonas(
    session, zonas_data: list[dict[str, Any]], limpiar: bool = False
) -> int:
    if limpiar:
        session.query(Zona).delete()
        session.flush()
        session.expire_all()

    count = 0
    for z_data in zonas_data:
        if "id" in z_data:
            existing = session.query(Zona).filter_by(id=z_data["id"]).first()
            if existing:
                existing.nombre_zona = z_data["nombre_zona"]
                existing.descripcion = z_data.get("descripcion")
                existing.fecha_inicio = _deserializar_fecha(z_data.get("fecha_inicio"))
                existing.fecha_fin = _deserializar_fecha(z_data.get("fecha_fin"))
            else:
                zona = Zona(
                    id=z_data["id"],
                    nombre_zona=z_data["nombre_zona"],
                    descripcion=z_data.get("descripcion"),
                    fecha_inicio=_deserializar_fecha(z_data.get("fecha_inicio")),
                    fecha_fin=_deserializar_fecha(z_data.get("fecha_fin")),
                )
                session.add(zona)
        else:
            zona = Zona(
                nombre_zona=z_data["nombre_zona"],
                descripcion=z_data.get("descripcion"),
                fecha_inicio=_deserializar_fecha(z_data.get("fecha_inicio")),
                fecha_fin=_deserializar_fecha(z_data.get("fecha_fin")),
            )
            session.add(zona)
        count += 1

    session.commit()
    return count


def importar_configuracion(
    session, config_data: dict[str, Any], limpiar: bool = False
) -> bool:
    if not config_data:
        return False

    if limpiar:
        session.query(Configuracion).delete()
        session.flush()
        session.expire_all()

    if "id" in config_data:
        existing = session.query(Configuracion).filter_by(id=config_data["id"]).first()
        if existing:
            existing.fecha_inicio_curso = _deserializar_fecha(config_data["fecha_inicio_curso"])
            existing.fecha_fin_curso = _deserializar_fecha(config_data["fecha_fin_curso"])
            existing.hora_recreo1_manana = _deserializar_hora(config_data["hora_recreo1_manana"])
            existing.hora_recreo2_manana = _deserializar_hora(config_data["hora_recreo2_manana"])
            existing.hora_recreo1_tarde = _deserializar_hora(config_data.get("hora_recreo1_tarde"))
            existing.hora_recreo2_tarde = _deserializar_hora(config_data.get("hora_recreo2_tarde"))
            existing.activar_festivos_automaticos = config_data.get(
                "activar_festivos_automaticos", True
            )
            existing.dias_no_lectivos_personalizados = config_data.get(
                "dias_no_lectivos_personalizados"
            )
            existing.recreos_config = config_data.get("recreos_config")
            existing.ajuste_tutores = config_data.get("ajuste_tutores", 1.0)
            existing.ajuste_no_tutores = config_data.get("ajuste_no_tutores", 1.0)
            existing.algoritmo_asignacion = config_data.get("algoritmo_asignacion", "v2.9")
        else:
            fecha_inicio = _deserializar_fecha(config_data["fecha_inicio_curso"])
            anio_inicio = config_data.get("anio_inicio_curso")
            if anio_inicio is None and fecha_inicio:
                anio_inicio = fecha_inicio.year

            config = Configuracion(
                id=config_data["id"],
                anio_inicio_curso=anio_inicio,
                fecha_inicio_curso=fecha_inicio,
                fecha_fin_curso=_deserializar_fecha(config_data["fecha_fin_curso"]),
                hora_recreo1_manana=_deserializar_hora(config_data["hora_recreo1_manana"]),
                hora_recreo2_manana=_deserializar_hora(config_data["hora_recreo2_manana"]),
                hora_recreo1_tarde=_deserializar_hora(config_data.get("hora_recreo1_tarde")),
                hora_recreo2_tarde=_deserializar_hora(config_data.get("hora_recreo2_tarde")),
                activar_festivos_automaticos=config_data.get("activar_festivos_automaticos", True),
                dias_no_lectivos_personalizados=config_data.get("dias_no_lectivos_personalizados"),
                recreos_config=config_data.get("recreos_config"),
                ajuste_tutores=config_data.get("ajuste_tutores", 1.0),
                ajuste_no_tutores=config_data.get("ajuste_no_tutores", 1.0),
                algoritmo_asignacion=config_data.get("algoritmo_asignacion", "v2.9"),
            )
            session.add(config)
    else:
        fecha_inicio = _deserializar_fecha(config_data["fecha_inicio_curso"])
        anio_inicio = config_data.get("anio_inicio_curso")
        if anio_inicio is None and fecha_inicio:
            anio_inicio = fecha_inicio.year

        config = Configuracion(
            anio_inicio_curso=anio_inicio,
            fecha_inicio_curso=fecha_inicio,
            fecha_fin_curso=_deserializar_fecha(config_data["fecha_fin_curso"]),
            hora_recreo1_manana=_deserializar_hora(config_data["hora_recreo1_manana"]),
            hora_recreo2_manana=_deserializar_hora(config_data["hora_recreo2_manana"]),
            hora_recreo1_tarde=_deserializar_hora(config_data.get("hora_recreo1_tarde")),
            hora_recreo2_tarde=_deserializar_hora(config_data.get("hora_recreo2_tarde")),
            activar_festivos_automaticos=config_data.get("activar_festivos_automaticos", True),
            dias_no_lectivos_personalizados=config_data.get("dias_no_lectivos_personalizados"),
            recreos_config=config_data.get("recreos_config"),
            ajuste_tutores=config_data.get("ajuste_tutores", 1.0),
            ajuste_no_tutores=config_data.get("ajuste_no_tutores", 1.0),
            algoritmo_asignacion=config_data.get("algoritmo_asignacion", "v2.9"),
        )
        session.add(config)
    session.commit()
    return True


def importar_guardias(
    session, guardias_data: list[dict[str, Any]], limpiar: bool = False
) -> int:
    if limpiar:
        session.query(Guardia).delete()

    count = 0
    for g_data in guardias_data:
        profesor_id = g_data.get("profesor_id")
        zona_id = g_data.get("zona_id")

        if not profesor_id:
            if g_data.get("profesor_nombre_completo"):
                profesor = (
                    session.query(Profesor)
                    .filter_by(nombre_completo=g_data["profesor_nombre_completo"])
                    .first()
                )
                profesor_id = profesor.id if profesor else None
            elif g_data.get("profesor_nombre") and g_data.get("profesor_apellidos"):
                nombre_completo = f"{g_data['profesor_apellidos']}, {g_data['profesor_nombre']}"
                profesor = (
                    session.query(Profesor).filter_by(nombre_completo=nombre_completo).first()
                )
                profesor_id = profesor.id if profesor else None

        if not zona_id and g_data.get("zona_nombre"):
            zona = session.query(Zona).filter_by(nombre_zona=g_data["zona_nombre"]).first()
            zona_id = zona.id if zona else None

        if profesor_id and zona_id:
            curso_id = g_data.get("curso_id")

            if "id" in g_data:
                existing = session.query(Guardia).filter_by(id=g_data["id"]).first()
                if existing:
                    existing.profesor_id = profesor_id
                    existing.fecha = _deserializar_fecha(g_data["fecha"])
                    existing.turno = g_data["turno"]
                    existing.recreo = g_data["recreo"]
                    existing.zona_id = zona_id
                    existing.curso_id = curso_id
                else:
                    guardia = Guardia(
                        id=g_data["id"],
                        profesor_id=profesor_id,
                        fecha=_deserializar_fecha(g_data["fecha"]),
                        turno=g_data["turno"],
                        recreo=g_data["recreo"],
                        zona_id=zona_id,
                        curso_id=curso_id,
                    )
                    session.add(guardia)
            else:
                guardia = Guardia(
                    profesor_id=profesor_id,
                    fecha=_deserializar_fecha(g_data["fecha"]),
                    turno=g_data["turno"],
                    recreo=g_data["recreo"],
                    zona_id=zona_id,
                    curso_id=curso_id,
                )
                session.add(guardia)
            count += 1

    session.commit()
    return count


def importar_ausencias(
    session, ausencias_data: list[dict[str, Any]], limpiar: bool = False
) -> int:
    if limpiar:
        session.query(Ausencia).delete()

    count = 0
    for a_data in ausencias_data:
        profesor_id = a_data.get("profesor_id")

        if not profesor_id and a_data.get("profesor_nombre_completo"):
            profesor = (
                session.query(Profesor)
                .filter_by(nombre_completo=a_data["profesor_nombre_completo"])
                .first()
            )
            profesor_id = profesor.id if profesor else None

        if profesor_id:
            if "id" in a_data:
                existing = session.query(Ausencia).filter_by(id=a_data["id"]).first()
                if existing:
                    existing.profesor_id = profesor_id
                    existing.fecha_inicio = _deserializar_fecha(a_data["fecha_inicio"])
                    existing.fecha_fin = _deserializar_fecha(a_data["fecha_fin"])
                    existing.tipo = a_data["tipo"]
                    existing.motivo = a_data.get("motivo")
                    existing.documento_path = a_data.get("documento_path")
                    existing.activa = a_data.get("activa", True)
                    if a_data.get("created_at"):
                        existing.created_at = datetime.fromisoformat(a_data["created_at"])
                    if a_data.get("updated_at"):
                        existing.updated_at = datetime.fromisoformat(a_data["updated_at"])
                else:
                    ausencia = Ausencia(
                        id=a_data["id"],
                        profesor_id=profesor_id,
                        fecha_inicio=_deserializar_fecha(a_data["fecha_inicio"]),
                        fecha_fin=_deserializar_fecha(a_data["fecha_fin"]),
                        tipo=a_data["tipo"],
                        motivo=a_data.get("motivo"),
                        documento_path=a_data.get("documento_path"),
                        activa=a_data.get("activa", True),
                        created_at=(
                            datetime.fromisoformat(a_data["created_at"])
                            if a_data.get("created_at")
                            else datetime.now(timezone.utc)
                        ),
                        updated_at=(
                            datetime.fromisoformat(a_data["updated_at"])
                            if a_data.get("updated_at")
                            else datetime.now(timezone.utc)
                        ),
                    )
                    session.add(ausencia)
            else:
                ausencia = Ausencia(
                    profesor_id=profesor_id,
                    fecha_inicio=_deserializar_fecha(a_data["fecha_inicio"]),
                    fecha_fin=_deserializar_fecha(a_data["fecha_fin"]),
                    tipo=a_data["tipo"],
                    motivo=a_data.get("motivo"),
                    documento_path=a_data.get("documento_path"),
                    activa=a_data.get("activa", True),
                    created_at=(
                        datetime.fromisoformat(a_data["created_at"])
                        if a_data.get("created_at")
                        else datetime.now(timezone.utc)
                    ),
                    updated_at=(
                        datetime.fromisoformat(a_data["updated_at"])
                        if a_data.get("updated_at")
                        else datetime.now(timezone.utc)
                    ),
                )
                session.add(ausencia)
            count += 1
            count += 1  # preservado del original

    session.commit()
    return count


def _importar_smtp_config(smtp_data: dict[str, str]) -> bool:
    try:
        smtp_server = smtp_data.get("smtp_server", "")
        smtp_port = smtp_data.get("smtp_port", "")
        smtp_user = smtp_data.get("smtp_user", "")
        smtp_password_encrypted = smtp_data.get("smtp_password", "")
        smtp_from_name = smtp_data.get("smtp_from_name", "Guardias de Patio")

        if not smtp_server or not smtp_port or not smtp_user or not smtp_password_encrypted:
            return False

        smtp_password = _desencriptar_password(smtp_password_encrypted)

        # Escritor único: la contraseña va al llavero del sistema y el
        # resto al `.env` de la carpeta de datos. Aquí se escribía en la
        # ruta relativa ".env", que no es la que se lee (SEC-001).
        from core.credenciales import guardar_configuracion

        guardar_configuracion(
            {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": smtp_port,
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": smtp_password,
                "SMTP_FROM_NAME": smtp_from_name,
            }
        )

        return True

    except (OSError, ValueError) as e:
        logger.warning(f"Error al importar configuración SMTP: {e}")
        return False


def _importar_sftp_config(sftp_data: dict[str, str]) -> bool:
    try:
        sftp_host = sftp_data.get("sftp_host", "")
        sftp_port = sftp_data.get("sftp_port", "")
        sftp_basedir = sftp_data.get("sftp_base_dir", "")
        sftp_user = sftp_data.get("sftp_username", "")
        sftp_password_encrypted = sftp_data.get("sftp_password", "")

        if not sftp_host or not sftp_port or not sftp_user or not sftp_password_encrypted:
            return False

        sftp_password = _desencriptar_password(sftp_password_encrypted)

        # Escritor único: la contraseña va al llavero del sistema y el
        # resto al `.env` de la carpeta de datos. Aquí se escribía en la
        # ruta relativa ".env", que no es la que se lee (SEC-001).
        from core.credenciales import guardar_configuracion

        guardar_configuracion(
            {
                "SFTP_HOST": sftp_host,
                "SFTP_PORT": sftp_port,
                "SFTP_BASE_DIR": sftp_basedir,
                "SFTP_USERNAME": sftp_user,
                "SFTP_PASSWORD": sftp_password,
            }
        )

        return True

    except (OSError, ValueError) as e:
        logger.warning(f"Error al importar configuración SFTP: {e}")
        return False


def importar_usuarios(
    usuarios_data: Optional[dict[str, Any]], limpiar: bool = False
) -> int:
    if not usuarios_data or "usuarios" not in usuarios_data:
        return 0

    from sync.sync_manager import UserAuth

    try:
        user_auth = UserAuth()

        if limpiar:
            user_auth.users = {}

        count = 0
        for usuario in usuarios_data["usuarios"]:
            username = usuario.get("username")
            if not username:
                continue

            user_auth.users[username] = {
                "password_hash": usuario.get("password_hash", ""),
                "email": usuario.get("email", ""),
                "created_at": usuario.get("created_at", ""),
            }
            count += 1

        user_auth._save_users()
        return count
    except (ValueError, TypeError, OSError) as e:
        logger.warning(f"Error al importar usuarios: {e}")
        return 0


def importar_cursos_escolares(
    session, cursos_data: Optional[dict[str, Any]], limpiar: bool = False
) -> int:
    if not cursos_data or "cursos" not in cursos_data:
        return 0

    from infrastructure.database.models import CursoEscolar

    try:
        if limpiar:
            session.query(CursoEscolar).delete()
            session.flush()

        count = 0
        for curso in cursos_data["cursos"]:
            nombre = curso.get("nombre")
            if not nombre:
                continue

            existe = session.query(CursoEscolar).filter_by(nombre=nombre).first()
            if existe:
                existe.activo = curso.get("activo", False)
                existe.cerrado = curso.get("cerrado", False)
            else:
                anio_inicio = curso.get("anio_inicio")
                anio_fin = curso.get("anio_fin")
                if anio_inicio is None or anio_fin is None:
                    continue

                fecha_inicio = (
                    date.fromisoformat(curso["fecha_inicio"])
                    if curso.get("fecha_inicio")
                    else date(int(anio_inicio), 9, 1)
                )
                fecha_fin = (
                    date.fromisoformat(curso["fecha_fin"])
                    if curso.get("fecha_fin")
                    else date(int(anio_fin), 6, 30)
                )
                nuevo_curso = CursoEscolar(
                    nombre=nombre,
                    anio_inicio=int(anio_inicio),
                    anio_fin=int(anio_fin),
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    activo=curso.get("activo", False),
                    cerrado=curso.get("cerrado", False),
                )
                session.add(nuevo_curso)

            count += 1

        session.commit()
        return count
    except SQLAlchemyError as e:
        logger.warning(f"Error al importar cursos escolares: {e}")
        session.rollback()
        return 0


def importar_todo(
    session, ruta_archivo: Union[str, Path], limpiar: bool = False
) -> dict[str, int]:
    ruta = Path(ruta_archivo)
    with ruta.open("r", encoding="utf-8") as f:
        datos = json.load(f)

    resultado = {
        "profesores": 0,
        "zonas": 0,
        "configuracion": 0,
        "guardias": 0,
        "ausencias": 0,
        "smtp_config": 0,
        "sftp_config": 0,
        "usuarios": 0,
        "cursos_escolares": 0,
    }

    if "smtp_config" in datos and datos["smtp_config"]:
        if _importar_smtp_config(datos["smtp_config"]):
            resultado["smtp_config"] = 1

    if "sftp_config" in datos and datos["sftp_config"]:
        if _importar_sftp_config(datos["sftp_config"]):
            resultado["sftp_config"] = 1

    if "usuarios" in datos:
        resultado["usuarios"] = importar_usuarios(datos["usuarios"], limpiar)

    if "cursos_escolares" in datos:
        resultado["cursos_escolares"] = importar_cursos_escolares(
            session, datos["cursos_escolares"], limpiar
        )

    if "profesores" in datos:
        resultado["profesores"] = importar_profesores(session, datos["profesores"], limpiar)

    if "zonas" in datos:
        resultado["zonas"] = importar_zonas(session, datos["zonas"], limpiar)

    if "configuracion" in datos:
        resultado["configuracion"] = (
            1 if importar_configuracion(session, datos["configuracion"], limpiar) else 0
        )

    if "guardias" in datos:
        resultado["guardias"] = importar_guardias(session, datos["guardias"], limpiar)

    if "ausencias" in datos:
        resultado["ausencias"] = importar_ausencias(session, datos["ausencias"], limpiar)

    return resultado
