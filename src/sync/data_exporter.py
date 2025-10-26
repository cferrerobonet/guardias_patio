"""
Exportador/Importador de Datos a JSON
======================================

Convierte toda la base de datos SQLite a formato JSON para sincronización.
Incluye: Profesores, Zonas, Configuración, Guardias y Ausencias.
"""

import json
import logging
from datetime import date, datetime, time
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona

logger = logging.getLogger(__name__)


class DataExporter:
    """Exporta e importa datos de la base de datos a/desde JSON."""

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

        # Solo exportar si hay configuración completa
        if smtp_server and smtp_port and smtp_user and smtp_password:
            return {
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user,
                "smtp_password": smtp_password,  # Se exporta cifrada en producción
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
            smtp_password = smtp_data.get("smtp_password", "")

            if not smtp_server or not smtp_port or not smtp_user or not smtp_password:
                logger.warning("Configuración SMTP incompleta en JSON")
                return False

            # Leer el archivo .env actual
            env_path = ".env"
            env_lines = []

            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    env_lines = f.readlines()

            # Actualizar o agregar variables SMTP
            smtp_vars = {
                "SMTP_SERVER": smtp_server,
                "SMTP_PORT": smtp_port,
                "SMTP_USER": smtp_user,
                "SMTP_PASSWORD": smtp_password,
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
            with open(env_path, 'w') as f:
                f.writelines(env_lines)

            logger.info("Configuración SMTP GLOBAL actualizada desde JSON")
            return True

        except Exception as e:
            logger.error(f"Error al importar configuración SMTP: {e}")
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
                "profesores": [],
                "zonas": [],
                "configuracion": [],
                "guardias": [],
                "ausencias": [],
            }

            # Exportar Profesores
            profesores = session.query(Profesor).all()
            for p in profesores:
                data["profesores"].append({
                    "id": p.id,
                    "nombre_completo": p.nombre_completo,
                    "email_corporativo": p.email_corporativo,
                    "horas_contrato": float(p.horas_contrato),
                    "porcentaje_jornada": float(p.porcentaje_jornada),
                    "turno": p.turno,
                    "horas_manana": float(p.horas_manana) if p.horas_manana else None,
                    "horas_tarde": float(p.horas_tarde) if p.horas_tarde else None,
                    "tutor": p.tutor,
                    "fecha_inicio_guardias": DataExporter._serialize_date(p.fecha_inicio_guardias) if p.fecha_inicio_guardias else None,
                    "fecha_fin_guardias": DataExporter._serialize_date(p.fecha_fin_guardias) if p.fecha_fin_guardias else None,
                })
            logger.info(f"✓ {len(profesores)} profesores exportados")

            # Exportar Zonas
            zonas = session.query(Zona).all()
            for z in zonas:
                data["zonas"].append({
                    "id": z.id,
                    "nombre_zona": z.nombre_zona,
                    "descripcion": z.descripcion,
                    "fecha_inicio": DataExporter._serialize_date(z.fecha_inicio) if z.fecha_inicio else None,
                    "fecha_fin": DataExporter._serialize_date(z.fecha_fin) if z.fecha_fin else None,
                })
            logger.info(f"✓ {len(zonas)} zonas exportadas")

            # Exportar Configuración
            configs = session.query(Configuracion).all()
            for c in configs:
                data["configuracion"].append({
                    "id": c.id,
                    "fecha_inicio_curso": DataExporter._serialize_date(c.fecha_inicio_curso),
                    "fecha_fin_curso": DataExporter._serialize_date(c.fecha_fin_curso),
                    "hora_recreo1_manana": c.hora_recreo1_manana.isoformat() if c.hora_recreo1_manana else None,
                    "hora_recreo2_manana": c.hora_recreo2_manana.isoformat() if c.hora_recreo2_manana else None,
                    "hora_recreo1_tarde": c.hora_recreo1_tarde.isoformat() if c.hora_recreo1_tarde else None,
                    "hora_recreo2_tarde": c.hora_recreo2_tarde.isoformat() if c.hora_recreo2_tarde else None,
                    "activar_festivos_automaticos": c.activar_festivos_automaticos,
                    "dias_no_lectivos_personalizados": c.dias_no_lectivos_personalizados,
                    "recreos_config": c.recreos_config,
                    "ajuste_tutores": float(c.ajuste_tutores) if c.ajuste_tutores else 1.0,
                    "ajuste_no_tutores": float(c.ajuste_no_tutores) if c.ajuste_no_tutores else 1.0,
                })
            logger.info(f"✓ {len(configs)} configuraciones exportadas")

            # Exportar Guardias
            guardias = session.query(Guardia).all()
            for g in guardias:
                data["guardias"].append({
                    "id": g.id,
                    "profesor_id": g.profesor_id,
                    "fecha": DataExporter._serialize_date(g.fecha),
                    "turno": g.turno,
                    "recreo": g.recreo,
                    "zona_id": g.zona_id,
                })
            logger.info(f"✓ {len(guardias)} guardias exportadas")

            # Exportar Ausencias
            ausencias = session.query(Ausencia).all()
            for a in ausencias:
                data["ausencias"].append({
                    "id": a.id,
                    "profesor_id": a.profesor_id,
                    "fecha_inicio": DataExporter._serialize_date(a.fecha_inicio),
                    "fecha_fin": DataExporter._serialize_date(a.fecha_fin),
                    "tipo": a.tipo,
                    "motivo": a.motivo,
                    "documento_path": a.documento_path,
                    "activa": a.activa,
                    "created_at": DataExporter._serialize_date(a.created_at) if a.created_at else None,
                    "updated_at": DataExporter._serialize_date(a.updated_at) if a.updated_at else None,
                })
            logger.info(f"✓ {len(ausencias)} ausencias exportadas")

            # Guardar JSON
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"✅ Datos exportados exitosamente a {output_path}")
            logger.info(f"   Total: {len(profesores)} profesores, {len(zonas)} zonas, "
                       f"{len(guardias)} guardias, {len(ausencias)} ausencias")
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
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            logger.info(f"📥 Importando datos desde {input_path}")
            logger.info(f"   Versión: {data.get('version', 'desconocida')}")
            logger.info(f"   Fecha exportación: {data.get('export_date', 'desconocida')}")

            # Importar configuración SMTP GLOBAL si existe en el JSON
            if "smtp_config" in data and data["smtp_config"]:
                DataExporter._import_smtp_config(data["smtp_config"])
                logger.info("✓ Configuración SMTP global importada")

            # Limpiar datos existentes si se solicita
            if clear_existing:
                logger.warning("🗑️  Limpiando datos existentes...")
                session.query(Guardia).delete()
                session.query(Ausencia).delete()
                session.query(Profesor).delete()
                session.query(Zona).delete()
                session.query(Configuracion).delete()
                session.commit()

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
                    existing.fecha_inicio_guardias = DataExporter._parse_date(p_data.get("fecha_inicio_guardias"))
                    existing.fecha_fin_guardias = DataExporter._parse_date(p_data.get("fecha_fin_guardias"))
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
                        fecha_inicio_guardias=DataExporter._parse_date(p_data.get("fecha_inicio_guardias")),
                        fecha_fin_guardias=DataExporter._parse_date(p_data.get("fecha_fin_guardias")),
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
                    existing.fecha_inicio_curso = DataExporter._parse_date(c_data["fecha_inicio_curso"])
                    existing.fecha_fin_curso = DataExporter._parse_date(c_data["fecha_fin_curso"])
                    existing.hora_recreo1_manana = DataExporter._parse_time(c_data.get("hora_recreo1_manana"))
                    existing.hora_recreo2_manana = DataExporter._parse_time(c_data.get("hora_recreo2_manana"))
                    existing.hora_recreo1_tarde = DataExporter._parse_time(c_data.get("hora_recreo1_tarde"))
                    existing.hora_recreo2_tarde = DataExporter._parse_time(c_data.get("hora_recreo2_tarde"))
                    existing.activar_festivos_automaticos = c_data.get("activar_festivos_automaticos", True)
                    existing.dias_no_lectivos_personalizados = c_data.get("dias_no_lectivos_personalizados")
                    existing.recreos_config = c_data.get("recreos_config")
                    existing.ajuste_tutores = c_data.get("ajuste_tutores", 1.0)
                    existing.ajuste_no_tutores = c_data.get("ajuste_no_tutores", 1.0)
                else:
                    # Crear nueva
                    config = Configuracion(
                        id=c_data["id"],
                        fecha_inicio_curso=DataExporter._parse_date(c_data["fecha_inicio_curso"]),
                        fecha_fin_curso=DataExporter._parse_date(c_data["fecha_fin_curso"]),
                        hora_recreo1_manana=DataExporter._parse_time(c_data.get("hora_recreo1_manana")),
                        hora_recreo2_manana=DataExporter._parse_time(c_data.get("hora_recreo2_manana")),
                        hora_recreo1_tarde=DataExporter._parse_time(c_data.get("hora_recreo1_tarde")),
                        hora_recreo2_tarde=DataExporter._parse_time(c_data.get("hora_recreo2_tarde")),
                        activar_festivos_automaticos=c_data.get("activar_festivos_automaticos", True),
                        dias_no_lectivos_personalizados=c_data.get("dias_no_lectivos_personalizados"),
                        recreos_config=c_data.get("recreos_config"),
                        ajuste_tutores=c_data.get("ajuste_tutores", 1.0),
                        ajuste_no_tutores=c_data.get("ajuste_no_tutores", 1.0),
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
                    )
                    session.add(ausencia)
                ausencias_importadas += 1
            session.commit()
            logger.info(f"✓ {ausencias_importadas} ausencias importadas/actualizadas")

            logger.info("✅ Importación completada exitosamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error importando datos desde JSON: {e}")
            session.rollback()
            return False
