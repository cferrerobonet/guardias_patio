"""
Exportador/Importador de Datos a JSON
======================================

Convierte toda la base de datos SQLite a formato JSON para sincronización.
Incluye: Profesores, Zonas, Configuración, Guardias y Ausencias.
"""

import base64
import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Optional

from models.models import Ausencia, Configuracion, CursoEscolar, Guardia, Profesor, Zona
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class DataExporter:
    """Exporta e importa datos de la base de datos a/desde JSON."""

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
        return base64.b64encode(password.encode("utf-8")).decode("utf-8")

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
            return base64.b64decode(encrypted_password.encode("utf-8")).decode("utf-8")
        except Exception as e:
            logger.warning(f"Error al desencriptar contraseña: {e}. Usando valor original.")
            return encrypted_password  # Si falla, asumir que ya está desencriptada

    @staticmethod
    def _serialize_date(obj: Any) -> str:
        """Serializa objetos date/datetime a string ISO."""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return str(obj)

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Optional[date]:
        """Convierte string ISO a objeto date."""
        if not date_str:
            return None
        try:
            if isinstance(date_str, date):
                return date_str
            return datetime.fromisoformat(date_str).date()
        except (ValueError, AttributeError):
            logger.warning(f"No se pudo parsear fecha: {date_str}")
            return None

    @staticmethod
    def _parse_time(time_str: Optional[str]) -> Optional[time]:
        """Convierte string ISO a objeto time."""
        if not time_str:
            return None
        try:
            if isinstance(time_str, time):
                return time_str
            return datetime.fromisoformat(f"2000-01-01T{time_str}").time()
        except (ValueError, AttributeError):
            logger.warning(f"No se pudo parsear hora: {time_str}")
            return None

    @staticmethod
    def _export_smtp_config() -> Optional[Dict[str, str]]:
        """
        Exporta la configuración SMTP desde el archivo .env.

        Esta configuración es GLOBAL y compartida entre todos los usuarios.

        Returns:
            Dict con configuración SMTP o None si no existe
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        smtp_server = os.getenv("SMTP_SERVER", "")
        smtp_port = os.getenv("SMTP_PORT", "")
        smtp_user = os.getenv("SMTP_USER", "")
        smtp_password = os.getenv("SMTP_PASSWORD", "")
        smtp_from_name = os.getenv("SMTP_FROM_NAME", "")

        # Solo exportar si hay configuración completa
        if smtp_server and smtp_port and smtp_user and smtp_password:
            return {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user,
                "smtp_password": DataExporter._encriptar_password(smtp_password),  # Encriptada
                "smtp_from_name": smtp_from_name,  # Nombre del remitente
            }
        return None

    @staticmethod
    def _import_smtp_config(smtp_data: Dict[str, str]) -> bool:
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
            smtp_from_name = smtp_data.get("smtp_from_name", "Guardias de Patio")

            if not smtp_server or not smtp_port or not smtp_user or not smtp_password_encrypted:
                logger.warning("Configuración SMTP incompleta en JSON")
                return False

            # Desencriptar contraseña
            smtp_password = DataExporter._desencriptar_password(smtp_password_encrypted)

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
                "SMTP_FROM_NAME": smtp_from_name,  # Nombre del remitente
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

            logger.info("Configuración SMTP GLOBAL actualizada desde JSON")
            return True

        except Exception as e:
            logger.error(f"Error al importar configuración SMTP: {e}")
            return False

    @staticmethod
    def _export_sftp_config() -> Optional[Dict[str, str]]:
        """
        Exporta la configuración SFTP desde el archivo .env.

        Esta configuración es GLOBAL y compartida entre todos los usuarios.

        Returns:
            Dict con configuración SFTP o None si no existe
        """
        import os

        from dotenv import load_dotenv

        load_dotenv()

        sftp_host = os.getenv("SFTP_HOST", "")
        sftp_port = os.getenv("SFTP_PORT", "")
        sftp_basedir = os.getenv("SFTP_BASE_DIR", "")
        sftp_user = os.getenv("SFTP_USERNAME", "")
        sftp_password = os.getenv("SFTP_PASSWORD", "")

        # Solo exportar si hay configuración completa
        if sftp_host and sftp_port and sftp_user and sftp_password:
            return {
                "sftp_host": sftp_host,
                "sftp_port": sftp_port,
                "sftp_base_dir": sftp_basedir,
                "sftp_username": sftp_user,
                "sftp_password": DataExporter._encriptar_password(sftp_password),  # Encriptada
            }
        return None

    @staticmethod
    def _import_sftp_config(sftp_data: Dict[str, str]) -> bool:
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
                logger.warning("Configuración SFTP incompleta en JSON")
                return False

            # Desencriptar contraseña
            sftp_password = DataExporter._desencriptar_password(sftp_password_encrypted)

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

            logger.info("Configuración SFTP GLOBAL actualizada desde JSON")
            return True

        except Exception as e:
            logger.error(f"Error al importar configuración SFTP: {e}")
            return False

    @staticmethod
    def export_to_json(session: Session, output_path: Path) -> bool:
        """
        Exporta todos los datos de la base de datos a un archivo JSON.

        Args:
            session: Sesión de SQLAlchemy
            output_path: Ruta donde guardar el JSON

        Returns:
            True si la exportación fue exitosa
        """
        try:
            data = {
                "export_date": datetime.now().isoformat(),
                "version": "1.0",
                "smtp_config": DataExporter._export_smtp_config(),  # Config global SMTP
                "sftp_config": DataExporter._export_sftp_config(),  # Config global SFTP
                "cursos_escolares": [],  # NUEVO: Cursos escolares
                "profesores": [],
                "zonas": [],
                "configuracion": [],
                "guardias": [],
                "ausencias": [],
            }

            # Exportar Cursos Escolares (NUEVO)
            cursos = session.query(CursoEscolar).all()
            for c in cursos:
                data["cursos_escolares"].append(
                    {
                        "id": c.id,
                        "anio_inicio": c.anio_inicio,
                        "anio_fin": c.anio_fin,
                        "fecha_inicio": DataExporter._serialize_date(c.fecha_inicio),
                        "fecha_fin": DataExporter._serialize_date(c.fecha_fin),
                        "nombre": c.nombre,
                        "activo": c.activo,
                        "cerrado": c.cerrado,
                        "created_at": DataExporter._serialize_date(c.created_at),
                    }
                )
            logger.info(f"✓ {len(cursos)} cursos escolares exportados")

            # Exportar Profesores
            profesores = session.query(Profesor).all()
            for p in profesores:
                data["profesores"].append(
                    {
                        "id": p.id,
                        "nombre_completo": p.nombre_completo,
                        "email_corporativo": p.email_corporativo,
                        "horas_contrato": float(p.horas_contrato),
                        "porcentaje_jornada": float(p.porcentaje_jornada),
                        "turno": p.turno,
                        "horas_manana": float(p.horas_manana) if p.horas_manana else None,
                        "horas_tarde": float(p.horas_tarde) if p.horas_tarde else None,
                        "tutor": p.tutor,
                        "activo": p.activo,  # Campo añadido
                        "fecha_inicio_guardias": DataExporter._serialize_date(
                            p.fecha_inicio_guardias
                        )
                        if p.fecha_inicio_guardias
                        else None,
                        "fecha_fin_guardias": DataExporter._serialize_date(p.fecha_fin_guardias)
                        if p.fecha_fin_guardias
                        else None,
                        "dias_semana_permitidos": p.dias_semana_permitidos,  # Campo añadido
                        "recreos_permitidos": p.recreos_permitidos,  # Campo añadido
                    }
                )
            logger.info(f"✓ {len(profesores)} profesores exportados")

            # Exportar Zonas
            zonas = session.query(Zona).all()
            for z in zonas:
                data["zonas"].append(
                    {
                        "id": z.id,
                        "nombre_zona": z.nombre_zona,
                        "descripcion": z.descripcion,
                        "fecha_inicio": DataExporter._serialize_date(z.fecha_inicio)
                        if z.fecha_inicio
                        else None,
                        "fecha_fin": DataExporter._serialize_date(z.fecha_fin)
                        if z.fecha_fin
                        else None,
                    }
                )
            logger.info(f"✓ {len(zonas)} zonas exportadas")

            # Exportar Configuración
            configs = session.query(Configuracion).all()
            for c in configs:
                data["configuracion"].append(
                    {
                        "id": c.id,
                        "fecha_inicio_curso": DataExporter._serialize_date(c.fecha_inicio_curso),
                        "fecha_fin_curso": DataExporter._serialize_date(c.fecha_fin_curso),
                        "hora_recreo1_manana": c.hora_recreo1_manana.isoformat()
                        if c.hora_recreo1_manana
                        else None,
                        "hora_recreo2_manana": c.hora_recreo2_manana.isoformat()
                        if c.hora_recreo2_manana
                        else None,
                        "hora_recreo1_tarde": c.hora_recreo1_tarde.isoformat()
                        if c.hora_recreo1_tarde
                        else None,
                        "hora_recreo2_tarde": c.hora_recreo2_tarde.isoformat()
                        if c.hora_recreo2_tarde
                        else None,
                        "activar_festivos_automaticos": c.activar_festivos_automaticos,
                        "dias_no_lectivos_personalizados": c.dias_no_lectivos_personalizados,
                        "recreos_config": c.recreos_config,
                        "ajuste_tutores": float(c.ajuste_tutores) if c.ajuste_tutores else 1.0,
                        "ajuste_no_tutores": float(c.ajuste_no_tutores)
                        if c.ajuste_no_tutores
                        else 1.0,
                        "algoritmo_asignacion": c.algoritmo_asignacion,  # Campo añadido
                    }
                )
            logger.info(f"✓ {len(configs)} configuraciones exportadas")

            # Exportar Guardias
            guardias = session.query(Guardia).all()
            for g in guardias:
                data["guardias"].append(
                    {
                        "id": g.id,
                        "curso_id": g.curso_id,  # NUEVO: FK a cursos_escolares
                        "profesor_id": g.profesor_id,
                        "fecha": DataExporter._serialize_date(g.fecha),
                        "turno": g.turno,
                        "recreo": g.recreo,
                        "zona_id": g.zona_id,
                    }
                )
            logger.info(f"✓ {len(guardias)} guardias exportadas")

            # Exportar Ausencias
            ausencias = session.query(Ausencia).all()
            for a in ausencias:
                data["ausencias"].append(
                    {
                        "id": a.id,
                        "profesor_id": a.profesor_id,
                        "fecha_inicio": DataExporter._serialize_date(a.fecha_inicio),
                        "fecha_fin": DataExporter._serialize_date(a.fecha_fin),
                        "tipo": a.tipo,
                        "motivo": a.motivo,
                        "documento_path": a.documento_path,
                        "activa": a.activa,
                        "created_at": DataExporter._serialize_date(a.created_at)
                        if a.created_at
                        else None,
                        "updated_at": DataExporter._serialize_date(a.updated_at)
                        if a.updated_at
                        else None,
                    }
                )
            logger.info(f"✓ {len(ausencias)} ausencias exportadas")

            # Guardar JSON
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Datos exportados exitosamente a {output_path}")
            logger.info(
                f"   Total: {len(profesores)} profesores, {len(zonas)} zonas, "
                f"{len(guardias)} guardias, {len(ausencias)} ausencias"
            )
            return True

        except Exception as e:
            logger.error(f"❌ Error exportando datos a JSON: {e}")
            return False

    @staticmethod
    def import_from_json(session: Session, input_path: Path, clear_existing: bool = False) -> bool:
        """
        Importa datos desde un archivo JSON a la base de datos.

        Args:
            session: Sesión de SQLAlchemy
            input_path: Ruta del archivo JSON a importar
            clear_existing: Si True, limpia los datos existentes antes de importar

        Returns:
            True si la importación fue exitosa
        """
        try:
            if not input_path.exists():
                logger.warning(f"Archivo {input_path} no existe")
                return False

            # Leer JSON
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"📥 Importando datos desde {input_path}")
            logger.info(f"   Versión: {data.get('version', 'desconocida')}")
            logger.info(f"   Fecha exportación: {data.get('export_date', 'desconocida')}")

            # Verificar que el esquema de la base de datos esté actualizado
            from sqlalchemy import inspect

            inspector = inspect(session.bind)

            # Verificar columnas críticas en la tabla profesores
            profesores_columns = {col["name"] for col in inspector.get_columns("profesores")}
            required_profesor_columns = {
                "activo",
                "zona_preferida_id",
                "dias_semana_permitidos",
                "recreos_permitidos",
                "fecha_inicio_guardias",
                "fecha_fin_guardias",
            }

            missing_profesor_cols = required_profesor_columns - profesores_columns
            if missing_profesor_cols:
                logger.error(
                    f"❌ El esquema de la base de datos está desactualizado. "
                    f"Faltan columnas en profesores: {missing_profesor_cols}"
                )
                logger.error(
                    "Por favor, ejecute las migraciones de Alembic o reinicie la aplicación."
                )
                return False

            # Verificar columnas críticas en la tabla configuracion
            config_columns = {col["name"] for col in inspector.get_columns("configuracion")}
            if "algoritmo_asignacion" not in config_columns:
                logger.error(
                    "❌ El esquema de la base de datos está desactualizado. "
                    "Falta la columna 'algoritmo_asignacion' en configuracion."
                )
                logger.error(
                    "Por favor, ejecute las migraciones de Alembic o reinicie la aplicación."
                )
                return False

            # Importar configuración SMTP GLOBAL si existe en el JSON
            if "smtp_config" in data and data["smtp_config"]:
                DataExporter._import_smtp_config(data["smtp_config"])
                logger.info("✓ Configuración SMTP global importada")

            # Importar configuración SFTP GLOBAL si existe en el JSON
            if "sftp_config" in data and data["sftp_config"]:
                DataExporter._import_sftp_config(data["sftp_config"])
                logger.info("✓ Configuración SFTP global importada")

            # Limpiar datos existentes si se solicita
            if clear_existing:
                logger.warning("🗑️  Limpiando datos existentes...")
                session.query(Guardia).delete()
                session.query(Ausencia).delete()
                session.query(Profesor).delete()
                session.query(Zona).delete()
                session.query(Configuracion).delete()
                session.query(CursoEscolar).delete()  # NUEVO
                session.commit()

            # Importar Cursos Escolares (NUEVO - primero para que existan las FK)
            cursos_importados = 0
            for c_data in data.get("cursos_escolares", []):
                # Verificar si ya existe
                existing = session.query(CursoEscolar).filter_by(id=c_data["id"]).first()
                if existing:
                    # Actualizar
                    existing.anio_inicio = c_data["anio_inicio"]
                    existing.anio_fin = c_data["anio_fin"]
                    existing.fecha_inicio = DataExporter._parse_date(c_data["fecha_inicio"])
                    existing.fecha_fin = DataExporter._parse_date(c_data["fecha_fin"])
                    existing.nombre = c_data["nombre"]
                    existing.activo = c_data["activo"]
                    existing.cerrado = c_data["cerrado"]
                    existing.created_at = DataExporter._parse_date(c_data["created_at"])
                else:
                    # Crear nuevo
                    curso = CursoEscolar(
                        id=c_data["id"],
                        anio_inicio=c_data["anio_inicio"],
                        anio_fin=c_data["anio_fin"],
                        fecha_inicio=DataExporter._parse_date(c_data["fecha_inicio"]),
                        fecha_fin=DataExporter._parse_date(c_data["fecha_fin"]),
                        nombre=c_data["nombre"],
                        activo=c_data["activo"],
                        cerrado=c_data["cerrado"],
                        created_at=DataExporter._parse_date(c_data["created_at"]),
                    )
                    session.add(curso)
                cursos_importados += 1

            session.commit()
            logger.info(f"✓ {cursos_importados} cursos escolares importados")

            # Importar Zonas (primero, porque pueden ser referenciadas)
            zonas_importadas = 0
            for z_data in data.get("zonas", []):
                # Verificar si ya existe
                existing = session.query(Zona).filter_by(id=z_data["id"]).first()
                if existing:
                    # Actualizar
                    existing.nombre_zona = z_data["nombre_zona"]
                    existing.descripcion = z_data.get("descripcion")
                    existing.fecha_inicio = DataExporter._parse_date(z_data.get("fecha_inicio"))
                    existing.fecha_fin = DataExporter._parse_date(z_data.get("fecha_fin"))
                else:
                    # Crear nueva
                    zona = Zona(
                        id=z_data["id"],
                        nombre_zona=z_data["nombre_zona"],
                        descripcion=z_data.get("descripcion"),
                        fecha_inicio=DataExporter._parse_date(z_data.get("fecha_inicio")),
                        fecha_fin=DataExporter._parse_date(z_data.get("fecha_fin")),
                    )
                    session.add(zona)
                zonas_importadas += 1
            session.commit()
            logger.info(f"✓ {zonas_importadas} zonas importadas/actualizadas")

            # Importar Profesores
            profesores_importados = 0
            for p_data in data.get("profesores", []):
                existing = session.query(Profesor).filter_by(id=p_data["id"]).first()
                if existing:
                    # Actualizar
                    existing.nombre_completo = p_data["nombre_completo"]
                    existing.email_corporativo = p_data.get("email_corporativo")
                    existing.horas_contrato = p_data["horas_contrato"]
                    existing.porcentaje_jornada = p_data["porcentaje_jornada"]
                    existing.turno = p_data["turno"]
                    existing.horas_manana = p_data.get("horas_manana")
                    existing.horas_tarde = p_data.get("horas_tarde")
                    existing.tutor = p_data.get("tutor", False)
                    existing.activo = p_data.get("activo", True)  # Campo añadido
                    existing.fecha_inicio_guardias = DataExporter._parse_date(
                        p_data.get("fecha_inicio_guardias")
                    )
                    existing.fecha_fin_guardias = DataExporter._parse_date(
                        p_data.get("fecha_fin_guardias")
                    )
                    existing.dias_semana_permitidos = p_data.get(
                        "dias_semana_permitidos"
                    )  # Campo añadido
                    existing.recreos_permitidos = p_data.get("recreos_permitidos")  # Campo añadido
                else:
                    # Crear nuevo
                    profesor = Profesor(
                        id=p_data["id"],
                        nombre_completo=p_data["nombre_completo"],
                        email_corporativo=p_data.get("email_corporativo"),
                        horas_contrato=p_data["horas_contrato"],
                        porcentaje_jornada=p_data["porcentaje_jornada"],
                        turno=p_data["turno"],
                        horas_manana=p_data.get("horas_manana"),
                        horas_tarde=p_data.get("horas_tarde"),
                        tutor=p_data.get("tutor", False),
                        activo=p_data.get("activo", True),  # Campo añadido
                        fecha_inicio_guardias=DataExporter._parse_date(
                            p_data.get("fecha_inicio_guardias")
                        ),
                        fecha_fin_guardias=DataExporter._parse_date(
                            p_data.get("fecha_fin_guardias")
                        ),
                        dias_semana_permitidos=p_data.get(
                            "dias_semana_permitidos"
                        ),  # Campo añadido
                        recreos_permitidos=p_data.get("recreos_permitidos"),  # Campo añadido
                    )
                    session.add(profesor)
                profesores_importados += 1
            session.commit()
            logger.info(f"✓ {profesores_importados} profesores importados/actualizados")

            # Importar Configuración
            configs_importadas = 0
            for c_data in data.get("configuracion", []):
                existing = session.query(Configuracion).filter_by(id=c_data["id"]).first()
                if existing:
                    # Actualizar
                    existing.fecha_inicio_curso = DataExporter._parse_date(
                        c_data["fecha_inicio_curso"]
                    )
                    existing.fecha_fin_curso = DataExporter._parse_date(c_data["fecha_fin_curso"])
                    existing.hora_recreo1_manana = DataExporter._parse_time(
                        c_data.get("hora_recreo1_manana")
                    )
                    existing.hora_recreo2_manana = DataExporter._parse_time(
                        c_data.get("hora_recreo2_manana")
                    )
                    existing.hora_recreo1_tarde = DataExporter._parse_time(
                        c_data.get("hora_recreo1_tarde")
                    )
                    existing.hora_recreo2_tarde = DataExporter._parse_time(
                        c_data.get("hora_recreo2_tarde")
                    )
                    existing.activar_festivos_automaticos = c_data.get(
                        "activar_festivos_automaticos", True
                    )
                    existing.dias_no_lectivos_personalizados = c_data.get(
                        "dias_no_lectivos_personalizados"
                    )
                    existing.recreos_config = c_data.get("recreos_config")
                    existing.ajuste_tutores = c_data.get("ajuste_tutores", 1.0)
                    existing.ajuste_no_tutores = c_data.get("ajuste_no_tutores", 1.0)
                    existing.algoritmo_asignacion = c_data.get(
                        "algoritmo_asignacion", "v2.9"
                    )  # Campo añadido
                else:
                    # Crear nueva
                    config = Configuracion(
                        id=c_data["id"],
                        fecha_inicio_curso=DataExporter._parse_date(c_data["fecha_inicio_curso"]),
                        fecha_fin_curso=DataExporter._parse_date(c_data["fecha_fin_curso"]),
                        hora_recreo1_manana=DataExporter._parse_time(
                            c_data.get("hora_recreo1_manana")
                        ),
                        hora_recreo2_manana=DataExporter._parse_time(
                            c_data.get("hora_recreo2_manana")
                        ),
                        hora_recreo1_tarde=DataExporter._parse_time(
                            c_data.get("hora_recreo1_tarde")
                        ),
                        hora_recreo2_tarde=DataExporter._parse_time(
                            c_data.get("hora_recreo2_tarde")
                        ),
                        activar_festivos_automaticos=c_data.get(
                            "activar_festivos_automaticos", True
                        ),
                        dias_no_lectivos_personalizados=c_data.get(
                            "dias_no_lectivos_personalizados"
                        ),
                        recreos_config=c_data.get("recreos_config"),
                        ajuste_tutores=c_data.get("ajuste_tutores", 1.0),
                        ajuste_no_tutores=c_data.get("ajuste_no_tutores", 1.0),
                        algoritmo_asignacion=c_data.get(
                            "algoritmo_asignacion", "v2.9"
                        ),  # Campo añadido
                    )
                    session.add(config)
                configs_importadas += 1
            session.commit()
            logger.info(f"✓ {configs_importadas} configuraciones importadas/actualizadas")

            # Importar Guardias
            guardias_importadas = 0
            for g_data in data.get("guardias", []):
                existing = session.query(Guardia).filter_by(id=g_data["id"]).first()
                if not existing:  # Solo crear, no actualizar guardias
                    guardia = Guardia(
                        id=g_data["id"],
                        curso_id=g_data.get("curso_id"),  # NUEVO: puede ser None
                        profesor_id=g_data["profesor_id"],
                        fecha=DataExporter._parse_date(g_data["fecha"]),
                        turno=g_data["turno"],
                        recreo=g_data["recreo"],
                        zona_id=g_data["zona_id"],
                    )
                    session.add(guardia)
                    guardias_importadas += 1
            session.commit()
            logger.info(f"✓ {guardias_importadas} guardias importadas")

            # Importar Ausencias
            ausencias_importadas = 0
            for a_data in data.get("ausencias", []):
                existing = session.query(Ausencia).filter_by(id=a_data["id"]).first()
                if existing:
                    # Actualizar
                    existing.profesor_id = a_data["profesor_id"]
                    existing.fecha_inicio = DataExporter._parse_date(a_data["fecha_inicio"])
                    existing.fecha_fin = DataExporter._parse_date(a_data["fecha_fin"])
                    existing.tipo = a_data["tipo"]
                    existing.motivo = a_data.get("motivo")
                    existing.documento_path = a_data.get("documento_path")
                    existing.activa = a_data.get("activa", True)
                    # Preservar timestamps
                    if a_data.get("created_at"):
                        existing.created_at = datetime.fromisoformat(a_data["created_at"])
                    if a_data.get("updated_at"):
                        existing.updated_at = datetime.fromisoformat(a_data["updated_at"])
                else:
                    # Crear nueva
                    ausencia = Ausencia(
                        id=a_data["id"],
                        profesor_id=a_data["profesor_id"],
                        fecha_inicio=DataExporter._parse_date(a_data["fecha_inicio"]),
                        fecha_fin=DataExporter._parse_date(a_data["fecha_fin"]),
                        tipo=a_data["tipo"],
                        motivo=a_data.get("motivo"),
                        documento_path=a_data.get("documento_path"),
                        activa=a_data.get("activa", True),
                        created_at=(
                            datetime.fromisoformat(a_data["created_at"])
                            if a_data.get("created_at")
                            else datetime.utcnow()
                        ),
                        updated_at=(
                            datetime.fromisoformat(a_data["updated_at"])
                            if a_data.get("updated_at")
                            else datetime.utcnow()
                        ),
                    )
                    session.add(ausencia)
                ausencias_importadas += 1
            session.commit()
            logger.info(f"✓ {ausencias_importadas} ausencias importadas/actualizadas")

            logger.info("✅ Importación completada exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error importando datos desde JSON: {e}", exc_info=True)
            session.rollback()
            return False
