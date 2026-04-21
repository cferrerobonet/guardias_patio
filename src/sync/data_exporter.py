"""
Exportador/Importador de Datos a JSON
======================================

Convierte toda la base de datos SQLite a formato JSON para sincronización.
Incluye: Profesores, Zonas, Configuración, Guardias y Ausencias.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from infrastructure.database.models import (
    Ausencia,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)
from sync.data_exporter_helpers import (
    desencriptar_password,
    encriptar_password,
    export_sftp_config,
    export_smtp_config,
    import_sftp_config,
    import_smtp_config,
    parse_date,
    parse_time,
    serialize_date,
)
from sync.dtos import (
    AusenciaSyncDTO,
    ConfiguracionSyncDTO,
    CursoEscolarSyncDTO,
    GuardiaSyncDTO,
    ProfesorSyncDTO,
    ZonaSyncDTO,
)

logger = logging.getLogger(__name__)


class DataExporter:
    """Exporta e importa datos de la base de datos a/desde JSON."""

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
                "smtp_config": export_smtp_config(),  # Config global SMTP
                "sftp_config": export_sftp_config(),  # Config global SFTP
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
                data["cursos_escolares"].append(CursoEscolarSyncDTO.from_orm(c).to_dict())
            logger.info(f"✓ {len(cursos)} cursos escolares exportados")

            # Exportar Profesores
            profesores = session.query(Profesor).all()
            for p in profesores:
                data["profesores"].append(ProfesorSyncDTO.from_orm(p).to_dict())
            logger.info(f"✓ {len(profesores)} profesores exportados")

            # Exportar Zonas
            zonas = session.query(Zona).all()
            for z in zonas:
                data["zonas"].append(ZonaSyncDTO.from_orm(z).to_dict())
            logger.info(f"✓ {len(zonas)} zonas exportadas")

            # Exportar Configuración
            configs = session.query(Configuracion).all()
            for c in configs:
                data["configuracion"].append(ConfiguracionSyncDTO.from_orm(c).to_dict())
            logger.info(f"✓ {len(configs)} configuraciones exportadas")

            # Exportar Guardias
            guardias = session.query(Guardia).all()
            for g in guardias:
                data["guardias"].append(GuardiaSyncDTO.from_orm(g).to_dict())
            logger.info(f"✓ {len(guardias)} guardias exportadas")

            # Exportar Ausencias
            ausencias = session.query(Ausencia).all()
            for a in ausencias:
                data["ausencias"].append(AusenciaSyncDTO.from_orm(a).to_dict())
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

        except (OSError, ValueError) as e:
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
                import_smtp_config(data["smtp_config"])
                logger.info("✓ Configuración SMTP global importada")

            # Importar configuración SFTP GLOBAL si existe en el JSON
            if "sftp_config" in data and data["sftp_config"]:
                import_sftp_config(data["sftp_config"])
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
                    existing.fecha_inicio = parse_date(c_data["fecha_inicio"])
                    existing.fecha_fin = parse_date(c_data["fecha_fin"])
                    existing.nombre = c_data["nombre"]
                    existing.activo = c_data["activo"]
                    existing.cerrado = c_data["cerrado"]
                    existing.created_at = parse_date(c_data["created_at"])
                else:
                    # Crear nuevo
                    curso = CursoEscolar(
                        id=c_data["id"],
                        anio_inicio=c_data["anio_inicio"],
                        anio_fin=c_data["anio_fin"],
                        fecha_inicio=parse_date(c_data["fecha_inicio"]),
                        fecha_fin=parse_date(c_data["fecha_fin"]),
                        nombre=c_data["nombre"],
                        activo=c_data["activo"],
                        cerrado=c_data["cerrado"],
                        created_at=parse_date(c_data["created_at"]),
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
                    existing.fecha_inicio = parse_date(z_data.get("fecha_inicio"))
                    existing.fecha_fin = parse_date(z_data.get("fecha_fin"))
                else:
                    # Crear nueva
                    zona = Zona(
                        id=z_data["id"],
                        nombre_zona=z_data["nombre_zona"],
                        descripcion=z_data.get("descripcion"),
                        fecha_inicio=parse_date(z_data.get("fecha_inicio")),
                        fecha_fin=parse_date(z_data.get("fecha_fin")),
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
                    existing.fecha_inicio_guardias = parse_date(p_data.get("fecha_inicio_guardias"))
                    existing.fecha_fin_guardias = parse_date(p_data.get("fecha_fin_guardias"))
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
                        fecha_inicio_guardias=parse_date(p_data.get("fecha_inicio_guardias")),
                        fecha_fin_guardias=parse_date(p_data.get("fecha_fin_guardias")),
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
                    existing.fecha_inicio_curso = parse_date(c_data["fecha_inicio_curso"])
                    existing.fecha_fin_curso = parse_date(c_data["fecha_fin_curso"])
                    existing.hora_recreo1_manana = parse_time(c_data.get("hora_recreo1_manana"))
                    existing.hora_recreo2_manana = parse_time(c_data.get("hora_recreo2_manana"))
                    existing.hora_recreo1_tarde = parse_time(c_data.get("hora_recreo1_tarde"))
                    existing.hora_recreo2_tarde = parse_time(c_data.get("hora_recreo2_tarde"))
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
                        anio_inicio_curso=c_data.get("anio_inicio_curso"),
                        fecha_inicio_curso=parse_date(c_data["fecha_inicio_curso"]),
                        fecha_fin_curso=parse_date(c_data["fecha_fin_curso"]),
                        hora_recreo1_manana=parse_time(c_data.get("hora_recreo1_manana")),
                        hora_recreo2_manana=parse_time(c_data.get("hora_recreo2_manana")),
                        hora_recreo1_tarde=parse_time(c_data.get("hora_recreo1_tarde")),
                        hora_recreo2_tarde=parse_time(c_data.get("hora_recreo2_tarde")),
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
                        fecha=parse_date(g_data["fecha"]),
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
                    existing.fecha_inicio = parse_date(a_data["fecha_inicio"])
                    existing.fecha_fin = parse_date(a_data["fecha_fin"])
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
                        fecha_inicio=parse_date(a_data["fecha_inicio"]),
                        fecha_fin=parse_date(a_data["fecha_fin"]),
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
                ausencias_importadas += 1
            session.commit()
            logger.info(f"✓ {ausencias_importadas} ausencias importadas/actualizadas")

            logger.info("✅ Importación completada exitosamente")
            return True

        except SQLAlchemyError as e:
            logger.error(f"❌ Error importando datos desde JSON: {e}", exc_info=True)
            session.rollback()
            return False

    # ------------------------------------------------------------------
    # Alias de helpers — expuestos como métodos estáticos para compatibilidad
    # ------------------------------------------------------------------
    _serialize_date = staticmethod(serialize_date)
    _parse_date = staticmethod(parse_date)
    _parse_time = staticmethod(parse_time)
    _encriptar_password = staticmethod(encriptar_password)
    _desencriptar_password = staticmethod(desencriptar_password)
    _export_smtp_config = staticmethod(export_smtp_config)
    _import_smtp_config = staticmethod(import_smtp_config)
    _export_sftp_config = staticmethod(export_sftp_config)
    _import_sftp_config = staticmethod(import_sftp_config)
