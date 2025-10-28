"""
Servicio de exportación e importación de datos de la aplicación.
Permite exportar/importar todos los datos (profesores, zonas, configuración, guardias)
en formato JSON para portabilidad entre equipos.
"""
import base64
import json
from datetime import date, time
from pathlib import Path
from typing import Any, Optional, Union

from sqlalchemy.orm import Session, joinedload

from models.models import Configuracion, Guardia, Profesor, Zona


class ExportadorDatos:
    """Servicio para exportar e importar datos de la aplicación."""

    @staticmethod
    def _encriptar_password(password: str) -> str:
        """
        Encripta una contraseña usando base64.

        Args:
            password: Contraseña en texto plano

        Returns:
            Contraseña encriptada en base64
        """
        if not password:
            return ""
        return base64.b64encode(password.encode('utf-8')).decode('utf-8')

    @staticmethod
    def _desencriptar_password(encrypted_password: str) -> str:
        """
        Desencripta una contraseña desde base64.

        Args:
            encrypted_password: Contraseña encriptada en base64

        Returns:
            Contraseña en texto plano
        """
        if not encrypted_password:
            return ""
        try:
            return base64.b64decode(encrypted_password.encode('utf-8')).decode('utf-8')
        except Exception:
            # Si falla, asumir que ya está desencriptada (compatibilidad con exports antiguos)
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
    def exportar_profesores(session: Session) -> list[dict[str, Any]]:
        """Exporta todos los profesores a diccionario."""
        profesores = session.query(Profesor).all()
        return [
            {
                "nombre_completo": p.nombre_completo,
                "email_corporativo": p.email_corporativo,
                "horas_contrato": p.horas_contrato,
                "porcentaje_jornada": p.porcentaje_jornada,
                "turno": p.turno,
                "tutor": p.tutor,
                "fecha_inicio_guardias": ExportadorDatos._serializar_fecha(
                    p.fecha_inicio_guardias
                ),
                "dias_semana_permitidos": p.dias_semana_permitidos,
                "recreos_permitidos": p.recreos_permitidos,
            }
            for p in profesores
        ]

    @staticmethod
    def exportar_zonas(session: Session) -> list[dict[str, Any]]:
        """Exporta todas las zonas a diccionario."""
        zonas = session.query(Zona).all()
        return [
            {
                "nombre_zona": z.nombre_zona,
                "descripcion": z.descripcion,
            }
            for z in zonas
        ]

    @staticmethod
    def exportar_configuracion(session: Session) -> Optional[dict[str, Any]]:
        """Exporta la configuración a diccionario."""
        config = session.query(Configuracion).first()
        if not config:
            return None

        return {
            "fecha_inicio_curso": ExportadorDatos._serializar_fecha(
                config.fecha_inicio_curso
            ),
            "fecha_fin_curso": ExportadorDatos._serializar_fecha(config.fecha_fin_curso),
            "hora_recreo1_manana": ExportadorDatos._serializar_hora(
                config.hora_recreo1_manana
            ),
            "hora_recreo2_manana": ExportadorDatos._serializar_hora(
                config.hora_recreo2_manana
            ),
            "hora_recreo1_tarde": ExportadorDatos._serializar_hora(
                config.hora_recreo1_tarde
            ),
            "hora_recreo2_tarde": ExportadorDatos._serializar_hora(
                config.hora_recreo2_tarde
            ),
            "activar_festivos_automaticos": config.activar_festivos_automaticos,
            "dias_no_lectivos_personalizados": config.dias_no_lectivos_personalizados,
            "recreos_config": config.recreos_config,
            "ajuste_tutores": config.ajuste_tutores,
            "ajuste_no_tutores": config.ajuste_no_tutores,
        }

    @staticmethod
    def exportar_guardias(session: Session) -> list[dict[str, Any]]:
        """Exporta todas las guardias a diccionario."""
        guardias = session.query(Guardia).options(
            joinedload(Guardia.profesor),
            joinedload(Guardia.zona)
        ).all()
        return [
            {
                "profesor_nombre_completo": g.profesor.nombre_completo if g.profesor else None,
                "fecha": ExportadorDatos._serializar_fecha(g.fecha),
                "turno": g.turno,
                "recreo": g.recreo,
                "zona_nombre": g.zona.nombre_zona if g.zona else None,
            }
            for g in guardias
        ]

    @staticmethod
    def exportar_todo(session: Session, ruta_archivo: Union[str, Path]) -> None:
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

        if smtp_server and smtp_port and smtp_user and smtp_password:
            smtp_config = {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user,
                "smtp_password": ExportadorDatos._encriptar_password(smtp_password),  # Encriptada
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
        }

        ruta = Path(ruta_archivo)
        with ruta.open("w", encoding="utf-8") as f:
            json.dump(datos_completos, f, ensure_ascii=False, indent=2)

    @staticmethod
    def importar_profesores(
        session: Session, profesores_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        """
        Importa profesores desde diccionario.

        Args:
            session: Sesión de SQLAlchemy
            profesores_data: Lista de diccionarios con datos de profesores
            limpiar: Si True, elimina profesores existentes antes de importar

        Returns:
            Número de profesores importados
        """
        if limpiar:
            # Eliminar guardias primero por FOREIGN KEY constraint
            session.query(Guardia).delete()
            session.flush()
            # Ahora eliminar profesores
            session.query(Profesor).delete()
            session.flush()
            session.expire_all()

        count = 0
        for p_data in profesores_data:
            # Soportar tanto el formato antiguo (nombre/apellidos) como el nuevo (nombre_completo)
            if "nombre_completo" in p_data:
                nombre_completo = p_data["nombre_completo"]
            elif "nombre" in p_data and "apellidos" in p_data:
                # Compatibilidad con exportaciones antiguas
                nombre_completo = f"{p_data['apellidos']}, {p_data['nombre']}"
            else:
                continue  # Skip si no tiene datos de nombre

            profesor = Profesor(
                nombre_completo=nombre_completo,
                email_corporativo=p_data.get("email_corporativo"),
                horas_contrato=p_data["horas_contrato"],
                porcentaje_jornada=p_data["porcentaje_jornada"],
                turno=p_data["turno"],
                tutor=p_data.get("tutor", False),
                fecha_inicio_guardias=ExportadorDatos._deserializar_fecha(
                    p_data.get("fecha_inicio_guardias")
                ),
                dias_semana_permitidos=p_data.get("dias_semana_permitidos"),
                recreos_permitidos=p_data.get("recreos_permitidos"),
            )
            session.add(profesor)
            count += 1

        session.commit()
        return count

    @staticmethod
    def importar_zonas(
        session: Session, zonas_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        """
        Importa zonas desde diccionario.

        Args:
            session: Sesión de SQLAlchemy
            zonas_data: Lista de diccionarios con datos de zonas
            limpiar: Si True, elimina zonas existentes antes de importar

        Returns:
            Número de zonas importadas
        """
        if limpiar:
            session.query(Zona).delete()
            session.flush()
            session.expire_all()

        count = 0
        for z_data in zonas_data:
            zona = Zona(
                nombre_zona=z_data["nombre_zona"],
                descripcion=z_data.get("descripcion"),
            )
            session.add(zona)
            count += 1

        session.commit()
        return count

    @staticmethod
    def importar_configuracion(
        session: Session, config_data: dict[str, Any], limpiar: bool = False
    ) -> bool:
        """
        Importa configuración desde diccionario.

        Args:
            session: Sesión de SQLAlchemy
            config_data: Diccionario con datos de configuración
            limpiar: Si True, elimina configuración existente antes de importar

        Returns:
            True si se importó correctamente
        """
        if not config_data:
            return False

        if limpiar:
            session.query(Configuracion).delete()
            session.flush()
            session.expire_all()

        config = Configuracion(
            fecha_inicio_curso=ExportadorDatos._deserializar_fecha(
                config_data["fecha_inicio_curso"]
            ),
            fecha_fin_curso=ExportadorDatos._deserializar_fecha(
                config_data["fecha_fin_curso"]
            ),
            hora_recreo1_manana=ExportadorDatos._deserializar_hora(
                config_data["hora_recreo1_manana"]
            ),
            hora_recreo2_manana=ExportadorDatos._deserializar_hora(
                config_data["hora_recreo2_manana"]
            ),
            hora_recreo1_tarde=ExportadorDatos._deserializar_hora(
                config_data.get("hora_recreo1_tarde")
            ),
            hora_recreo2_tarde=ExportadorDatos._deserializar_hora(
                config_data.get("hora_recreo2_tarde")
            ),
            activar_festivos_automaticos=config_data.get(
                "activar_festivos_automaticos", True
            ),
            dias_no_lectivos_personalizados=config_data.get(
                "dias_no_lectivos_personalizados"
            ),
            recreos_config=config_data.get("recreos_config"),
            ajuste_tutores=config_data.get("ajuste_tutores", 1.0),
            ajuste_no_tutores=config_data.get("ajuste_no_tutores", 1.0),
        )
        session.add(config)
        session.commit()
        return True

    @staticmethod
    def importar_guardias(
        session: Session, guardias_data: list[dict[str, Any]], limpiar: bool = False
    ) -> int:
        """
        Importa guardias desde diccionario.

        Args:
            session: Sesión de SQLAlchemy
            guardias_data: Lista de diccionarios con datos de guardias
            limpiar: Si True, elimina guardias existentes antes de importar

        Returns:
            Número de guardias importadas
        """
        if limpiar:
            session.query(Guardia).delete()

        count = 0
        for g_data in guardias_data:
            # Buscar profesor por nombre_completo (nuevo formato) o nombre+apellidos (antiguo)
            profesor = None
            if g_data.get("profesor_nombre_completo"):
                profesor = (
                    session.query(Profesor)
                    .filter_by(nombre_completo=g_data["profesor_nombre_completo"])
                    .first()
                )
            elif g_data.get("profesor_nombre") and g_data.get("profesor_apellidos"):
                # Compatibilidad con formato antiguo
                nombre_completo = f"{g_data['profesor_apellidos']}, {g_data['profesor_nombre']}"
                profesor = (
                    session.query(Profesor)
                    .filter_by(nombre_completo=nombre_completo)
                    .first()
                )

            # Buscar zona por nombre
            zona = None
            if g_data.get("zona_nombre"):
                zona = (
                    session.query(Zona)
                    .filter_by(nombre_zona=g_data["zona_nombre"])
                    .first()
                )

            if profesor and zona:  # Solo crear si encontramos profesor y zona
                guardia = Guardia(
                    profesor_id=profesor.id,
                    fecha=ExportadorDatos._deserializar_fecha(g_data["fecha"]),
                    turno=g_data["turno"],
                    recreo=g_data["recreo"],
                    zona_id=zona.id,
                )
                session.add(guardia)
                count += 1

        session.commit()
        return count

    @staticmethod
    def _importar_smtp_config(smtp_data: dict[str, str]) -> bool:
        """
        Importa la configuración SMTP GLOBAL al archivo .env.

        Esta configuración es compartida entre todos los usuarios.
        Si se modifica, afectará a todos los usuarios del sistema.

        Args:
            smtp_data: Dict con configuración SMTP

        Returns:
            True si se importó correctamente
        """
        import os

        try:
            smtp_server = smtp_data.get("smtp_server", "")
            smtp_port = smtp_data.get("smtp_port", "")
            smtp_user = smtp_data.get("smtp_user", "")
            smtp_password_encrypted = smtp_data.get("smtp_password", "")

            if not smtp_server or not smtp_port or not smtp_user or not smtp_password_encrypted:
                return False

            # Desencriptar contraseña
            smtp_password = ExportadorDatos._desencriptar_password(smtp_password_encrypted)

            # Leer el archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SMTP
            smtp_vars = {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": smtp_port,
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": smtp_password,  # Guardamos desencriptada
            }

            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var_name, var_value in smtp_vars.items():
                    if line.startswith(f"{var_name}="):
                        env_lines[i] = f"{var_name}={var_value}\n"
                        updated_vars.add(var_name)

            # Agregar variables que no existían
            for var_name, var_value in smtp_vars.items():
                if var_name not in updated_vars:
                    env_lines.append(f"{var_name}={var_value}\n")

            # Guardar archivo .env
            with open(env_path, "w") as f:
                f.writelines(env_lines)

            return True

        except Exception as e:
            print(f"Error al importar configuración SMTP: {e}")
            return False

    @staticmethod
    def _importar_sftp_config(sftp_data: dict[str, str]) -> bool:
        """
        Importa la configuración SFTP GLOBAL al archivo .env.

        Esta configuración es compartida entre todos los usuarios.
        Si se modifica, afectará a todos los usuarios del sistema.

        Args:
            sftp_data: Dict con configuración SFTP

        Returns:
            True si se importó correctamente
        """
        import os

        try:
            sftp_host = sftp_data.get("sftp_host", "")
            sftp_port = sftp_data.get("sftp_port", "")
            sftp_basedir = sftp_data.get("sftp_base_dir", "")
            sftp_user = sftp_data.get("sftp_username", "")
            sftp_password_encrypted = sftp_data.get("sftp_password", "")

            if not sftp_host or not sftp_port or not sftp_user or not sftp_password_encrypted:
                return False

            # Desencriptar contraseña
            sftp_password = ExportadorDatos._desencriptar_password(sftp_password_encrypted)

            # Leer el archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SFTP
            sftp_vars = {
                "SFTP_HOST": sftp_host,
                "SFTP_PORT": sftp_port,
                "SFTP_BASE_DIR": sftp_basedir,
                "SFTP_USERNAME": sftp_user,
                "SFTP_PASSWORD": sftp_password,  # Guardamos desencriptada
            }

            updated_vars = set()
            for i, line in enumerate(env_lines):
                for var_name, var_value in sftp_vars.items():
                    if line.startswith(f"{var_name}="):
                        env_lines[i] = f"{var_name}={var_value}\n"
                        updated_vars.add(var_name)

            # Agregar variables que no existían
            for var_name, var_value in sftp_vars.items():
                if var_name not in updated_vars:
                    env_lines.append(f"{var_name}={var_value}\n")

            # Guardar archivo .env
            with open(env_path, "w") as f:
                f.writelines(env_lines)

            return True

        except Exception as e:
            print(f"Error al importar configuración SFTP: {e}")
            return False

    @staticmethod
    def importar_todo(
        session: Session, ruta_archivo: Union[str, Path], limpiar: bool = False
    ) -> dict[str, int]:
        """
        Importa todos los datos desde un archivo JSON.

        Args:
            session: Sesión de SQLAlchemy
            ruta_archivo: Ruta del archivo JSON a importar
            limpiar: Si True, elimina datos existentes antes de importar

        Returns:
            Diccionario con contadores de elementos importados
        """
        ruta = Path(ruta_archivo)
        with ruta.open("r", encoding="utf-8") as f:
            datos = json.load(f)

        resultado = {
            "profesores": 0,
            "zonas": 0,
            "configuracion": 0,
            "guardias": 0,
            "smtp_config": 0,
            "sftp_config": 0,
        }

        # Importar configuración SMTP GLOBAL si existe en el JSON
        if "smtp_config" in datos and datos["smtp_config"]:
            if ExportadorDatos._importar_smtp_config(datos["smtp_config"]):
                resultado["smtp_config"] = 1

        # Importar configuración SFTP GLOBAL si existe en el JSON
        if "sftp_config" in datos and datos["sftp_config"]:
            if ExportadorDatos._importar_sftp_config(datos["sftp_config"]):
                resultado["sftp_config"] = 1

        # Orden importante: primero profesores y zonas (para claves foráneas)
        if "profesores" in datos:
            resultado["profesores"] = ExportadorDatos.importar_profesores(
                session, datos["profesores"], limpiar
            )

        if "zonas" in datos:
            resultado["zonas"] = ExportadorDatos.importar_zonas(
                session, datos["zonas"], limpiar
            )

        if "configuracion" in datos:
            resultado["configuracion"] = (
                1
                if ExportadorDatos.importar_configuracion(
                    session, datos["configuracion"], limpiar
                )
                else 0
            )

        # Guardias al final (depende de profesores y zonas)
        if "guardias" in datos:
            resultado["guardias"] = ExportadorDatos.importar_guardias(
                session, datos["guardias"], limpiar
            )

        return resultado
