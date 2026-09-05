"""
Servicio de exportación e importación de datos de la aplicación.
Permite exportar/importar todos los datos (profesores, zonas, configuración, guardias)
en formato JSON para portabilidad entre equipos.
"""

import base64
import json
import os
from datetime import date, time
from pathlib import Path
from typing import Any, Optional, Union

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload

from core.logging import get_logger
from infrastructure.database.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from services._exportador_import import (
    _importar_sftp_config as _importar_sftp_config_impl,
)
from services._exportador_import import (
    _importar_smtp_config as _importar_smtp_config_impl,
)
from services._exportador_import import (
    importar_ausencias as _importar_ausencias_impl,
)
from services._exportador_import import (
    importar_configuracion as _importar_configuracion_impl,
)
from services._exportador_import import (
    importar_cursos_escolares as _importar_cursos_escolares_impl,
)
from services._exportador_import import (
    importar_guardias as _importar_guardias_impl,
)
from services._exportador_import import (
    importar_profesores as _importar_profesores_impl,
)
from services._exportador_import import (
    importar_todo as _importar_todo_impl,
)
from services._exportador_import import (
    importar_usuarios as _importar_usuarios_impl,
)
from services._exportador_import import (
    importar_zonas as _importar_zonas_impl,
)

logger = get_logger(__name__)


class ExportadorDatos:
    """Servicio para exportar e importar datos de la aplicación."""

    _fernet_key_env = "GUARDIAS_FERNET_KEY"

    @classmethod
    def _get_fernet(cls) -> Fernet:
        key = os.environ.get(cls._fernet_key_env)
        if not key:
            key_path = Path.home() / ".guardias_patio_key"
            if key_path.exists():
                key = key_path.read_text().strip()
            else:
                key = Fernet.generate_key().decode()
                key_path.write_text(key)
                key_path.chmod(0o600)
        return Fernet(key.encode() if isinstance(key, str) else key)

    @classmethod
    def _encriptar_password(cls, password: str) -> str:
        if not password:
            return ""
        return cls._get_fernet().encrypt(password.encode("utf-8")).decode("utf-8")

    @classmethod
    def _desencriptar_password(cls, encrypted_password: str) -> str:
        if not encrypted_password:
            return ""
        try:
            return cls._get_fernet().decrypt(encrypted_password.encode("utf-8")).decode("utf-8")
        except InvalidToken:
            try:
                return base64.b64decode(encrypted_password.encode("utf-8")).decode("utf-8")
            except (ValueError, TypeError, OSError):
                return encrypted_password

    @staticmethod
    def _serializar_fecha(obj: date) -> Optional[str]:
        """Convierte fecha a string ISO."""
        return obj.isoformat() if obj else None

    @staticmethod
    def _serializar_hora(obj: time) -> Optional[str]:
        """Convierte hora a string HH:MM."""
        return obj.strftime("%H:%M") if obj else None

    @staticmethod
    def _deserializar_fecha(fecha_str: Optional[str]) -> Optional[date]:
        """Convierte string ISO a fecha."""
        return date.fromisoformat(fecha_str) if fecha_str else None

    @staticmethod
    def _deserializar_hora(hora_str: Optional[str]) -> Optional[time]:
        """Convierte string HH:MM a hora."""
        if not hora_str:
            return None
        h, m = hora_str.split(":")
        return time(int(h), int(m))

    @staticmethod
    def exportar_profesores(session) -> list[dict[str, Any]]:
        """Exporta todos los profesores a diccionario."""
        profesores = session.query(Profesor).all()
        return [
            {
                "id": p.id,  # ID necesario para restauración completa
                "nombre_completo": p.nombre_completo,
                "email_corporativo": p.email_corporativo,
                "horas_contrato": p.horas_contrato,
                "porcentaje_jornada": p.porcentaje_jornada,
                "turno": p.turno,
                "horas_manana": p.horas_manana,  # Campo añadido
                "horas_tarde": p.horas_tarde,  # Campo añadido
                "tutor": p.tutor,
                "activo": p.activo,  # Campo añadido
                "fecha_inicio_guardias": ExportadorDatos._serializar_fecha(p.fecha_inicio_guardias),
                "fecha_fin_guardias": ExportadorDatos._serializar_fecha(
                    p.fecha_fin_guardias
                ),  # Campo añadido
                "zona_preferida_id": p.zona_preferida_id,  # Campo añadido
                "dias_semana_permitidos": p.dias_semana_permitidos,
                "recreos_permitidos": p.recreos_permitidos,
            }
            for p in profesores
        ]

    @staticmethod
    def exportar_zonas(session) -> list[dict[str, Any]]:
        """Exporta todas las zonas a diccionario."""
        zonas = session.query(Zona).all()
        return [
            {
                "id": z.id,  # ID necesario para restauración completa
                "nombre_zona": z.nombre_zona,
                "descripcion": z.descripcion,
                "fecha_inicio": ExportadorDatos._serializar_fecha(z.fecha_inicio),  # Campo añadido
                "fecha_fin": ExportadorDatos._serializar_fecha(z.fecha_fin),  # Campo añadido
            }
            for z in zonas
        ]

    @staticmethod
    def exportar_configuracion(session) -> Optional[dict[str, Any]]:
        """Exporta la configuración a diccionario."""
        config = session.query(Configuracion).first()
        if not config:
            return None

        return {
            "id": config.id,  # ID necesario para restauración completa
            "fecha_inicio_curso": ExportadorDatos._serializar_fecha(config.fecha_inicio_curso),
            "fecha_fin_curso": ExportadorDatos._serializar_fecha(config.fecha_fin_curso),
            "hora_recreo1_manana": ExportadorDatos._serializar_hora(config.hora_recreo1_manana),
            "hora_recreo2_manana": ExportadorDatos._serializar_hora(config.hora_recreo2_manana),
            "hora_recreo1_tarde": ExportadorDatos._serializar_hora(config.hora_recreo1_tarde),
            "hora_recreo2_tarde": ExportadorDatos._serializar_hora(config.hora_recreo2_tarde),
            "activar_festivos_automaticos": config.activar_festivos_automaticos,
            "dias_no_lectivos_personalizados": config.dias_no_lectivos_personalizados,
            "recreos_config": config.recreos_config,
            "ajuste_tutores": config.ajuste_tutores,
            "ajuste_no_tutores": config.ajuste_no_tutores,
            "algoritmo_asignacion": config.algoritmo_asignacion,  # Campo añadido
        }

    @staticmethod
    def exportar_guardias(session) -> list[dict[str, Any]]:
        """Exporta todas las guardias a diccionario."""
        guardias = (
            session.query(Guardia)
            .options(joinedload(Guardia.profesor), joinedload(Guardia.zona))
            .all()
        )
        return [
            {
                "id": g.id,  # ID necesario para restauración completa
                "profesor_id": g.profesor_id,  # FK necesario para relaciones
                "profesor_nombre_completo": g.profesor.nombre_completo if g.profesor else None,
                "fecha": ExportadorDatos._serializar_fecha(g.fecha),
                "turno": g.turno,
                "recreo": g.recreo,
                "zona_id": g.zona_id,  # FK necesario para relaciones
                "zona_nombre": g.zona.nombre_zona if g.zona else None,
                "curso_id": g.curso_id,  # Curso escolar asociado
            }
            for g in guardias
        ]

    @staticmethod
    def exportar_ausencias(session) -> list[dict[str, Any]]:
        """Exporta todas las ausencias a diccionario."""
        ausencias = session.query(Ausencia).options(joinedload(Ausencia.profesor)).all()
        return [
            {
                "id": a.id,  # ID necesario para restauración completa
                "profesor_id": a.profesor_id,  # FK necesario para relaciones
                "profesor_nombre_completo": a.profesor.nombre_completo if a.profesor else None,
                "fecha_inicio": ExportadorDatos._serializar_fecha(a.fecha_inicio),
                "fecha_fin": ExportadorDatos._serializar_fecha(a.fecha_fin),
                "tipo": a.tipo,
                "motivo": a.motivo,
                "documento_path": a.documento_path,
                "activa": a.activa,
                "created_at": a.created_at.isoformat() if a.created_at else None,
                "updated_at": a.updated_at.isoformat() if a.updated_at else None,
            }
            for a in ausencias
        ]

    @staticmethod
    def exportar_usuarios() -> Optional[dict[str, Any]]:
        """
        Exporta todos los usuarios (perfiles) del sistema.

        Returns:
            Diccionario con datos de usuarios o None si no hay archivo
        """
        from sync.sync_manager import UserAuth

        try:
            user_auth = UserAuth()
            usuarios_export = []

            for username, user_data in user_auth.users.items():
                usuarios_export.append(
                    {
                        "username": username,
                        "email": user_data.get("email", ""),
                        "password_hash": user_data.get("password_hash", ""),
                        "created_at": user_data.get("created_at", ""),
                    }
                )

            return {"count": len(usuarios_export), "usuarios": usuarios_export}
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Error al exportar usuarios: {e}")
            return None

    @staticmethod
    def exportar_cursos_escolares(session) -> Optional[dict[str, Any]]:
        """
        Exporta todos los cursos escolares del sistema.

        Args:
            session: Sesión de SQLAlchemy

        Returns:
            Diccionario con datos de cursos o None si hay error
        """
        from infrastructure.database.models import CursoEscolar

        try:
            cursos = session.query(CursoEscolar).all()

            cursos_export = []
            curso_actual = None

            for curso in cursos:
                if curso.activo and not curso.cerrado:
                    curso_actual = curso.nombre

                cursos_export.append(
                    {
                        "nombre": curso.nombre,
                        "activo": curso.activo,
                        "cerrado": curso.cerrado,
                        "fecha_creacion": (
                            curso.created_at.isoformat() if curso.created_at else None
                        ),
                        "fecha_cierre": None,
                    }
                )

            return {
                "count": len(cursos_export),
                "curso_actual": curso_actual,
                "cursos": cursos_export,
            }
        except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
            logger.warning(f"Error al exportar cursos escolares: {e}")
            return None

    @staticmethod
    def exportar_todo(session, ruta_archivo: Union[str, Path]) -> None:
        """
        Exporta todos los datos de la aplicación a un archivo JSON.

        Args:
            session: Sesión de SQLAlchemy
            ruta_archivo: Ruta donde guardar el archivo JSON
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        # Exportar configuración SMTP GLOBAL (compartida entre todos los usuarios)
        smtp_config = None
        smtp_server = os.getenv("SMTP_SERVER", "")
        smtp_port = os.getenv("SMTP_PORT", "")
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from_name = os.getenv("SMTP_FROM_NAME", "Guardias de Patio")

        if smtp_server and smtp_port and smtp_user and smtp_password:
            smtp_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user,
                "smtp_password": ExportadorDatos._encriptar_password(smtp_password),  # Encriptada
                "smtp_from_name": smtp_from_name,  # Nombre del remitente
            }

        # Exportar configuración SFTP GLOBAL (compartida entre todos los usuarios)
        sftp_config = None
        sftp_host = os.getenv("SFTP_HOST", "")
        sftp_port = os.getenv("SFTP_PORT", "")
        sftp_basedir = os.getenv("SFTP_BASE_DIR", "")
        sftp_user = os.getenv("SFTP_USERNAME", "")
        sftp_password = os.getenv("SFTP_PASSWORD", "")

        if sftp_host and sftp_port and sftp_user and sftp_password:
            sftp_config = {
                "sftp_host": sftp_host,
                "sftp_port": sftp_port,
                "sftp_base_dir": sftp_basedir,
                "sftp_username": sftp_user,
                "sftp_password": ExportadorDatos._encriptar_password(sftp_password),  # Encriptada
            }

        datos_completos = {
            "version": "1.0",
            "fecha_exportacion": date.today().isoformat(),
            "smtp_config": smtp_config,  # Configuración SMTP global
            "sftp_config": sftp_config,  # Configuración SFTP global
            "profesores": ExportadorDatos.exportar_profesores(session),
            "zonas": ExportadorDatos.exportar_zonas(session),
            "configuracion": ExportadorDatos.exportar_configuracion(session),
            "guardias": ExportadorDatos.exportar_guardias(session),
            "ausencias": ExportadorDatos.exportar_ausencias(session),
            "usuarios": ExportadorDatos.exportar_usuarios(),  # Perfiles de usuario
            "cursos_escolares": ExportadorDatos.exportar_cursos_escolares(session),  # Cursos
        }

        ruta = Path(ruta_archivo)
        with ruta.open("w", encoding="utf-8") as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=2)

    @staticmethod
    def importar_profesores(
        session, profesores_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_profesores_impl(session, profesores_data, limpiar)

    @staticmethod
    def importar_zonas(
        session, zonas_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_zonas_impl(session, zonas_data, limpiar)

    @staticmethod
    def importar_configuracion(
        session, config_data: dict[str, Any], limpiar: bool = False
    ) -> bool:
        return _importar_configuracion_impl(session, config_data, limpiar)

    @staticmethod
    def importar_guardias(
        session, guardias_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_guardias_impl(session, guardias_data, limpiar)

    @staticmethod
    def importar_ausencias(
        session, ausencias_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_ausencias_impl(session, ausencias_data, limpiar)

    @staticmethod
    def _importar_smtp_config(smtp_data: dict[str, str]) -> bool:
        return _importar_smtp_config_impl(smtp_data)

    @staticmethod
    def _importar_sftp_config(sftp_data: dict[str, str]) -> bool:
        return _importar_sftp_config_impl(sftp_data)

    @staticmethod
    def importar_usuarios(
        usuarios_data: Optional[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_usuarios_impl(usuarios_data, limpiar)

    @staticmethod
    def importar_cursos_escolares(
        session, cursos_data: Optional[dict[str, Any]], limpiar: bool = False
    ) -> int:
        return _importar_cursos_escolares_impl(session, cursos_data, limpiar)

    @staticmethod
    def importar_todo(
        session, ruta_archivo: Union[str, Path], limpiar: bool = False
    ) -> dict[str, int]:
        return _importar_todo_impl(session, ruta_archivo, limpiar)
