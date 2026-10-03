"""
Use Case: Generar calendario de guardias.

Genera todas las guardias del curso y las guarda en la base de datos.
"""

import json
import json as _json
import threading
from datetime import date, datetime
from typing import Callable, Optional

from sqlalchemy.orm import Session

from application.dtos.asignacion_guardias_dto import ResumenGeneracionDTO
from core.exceptions import BusinessLogicError
from core.observability import with_metrics
from core.usage_logger import usage_log
from infrastructure.database.models import Configuracion, Guardia, GuardiaAuditLog, Profesor
from services.asignador_guardias_cpsat import (
    generar_guardias_cpsat,
    guardar_guardias_cpsat_en_bd,
)
from services.calculador_guardias import obtener_estadisticas
from utils.logger import get_logger

logger = get_logger(__name__)


class GenerarGuardiasUseCase:
    """
    Caso de uso para generar el calendario completo de guardias.

    Genera todas las asignaciones de guardias para el curso escolar
    y las persiste en la base de datos.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    def _guardias_del_curso_activo(self):
        from infrastructure.database.models import CursoEscolar

        curso = self.session.query(CursoEscolar).filter_by(activo=True).first()
        consulta = self.session.query(Guardia)
        if curso is None:
            return consulta.filter(Guardia.curso_id.is_(None))
        return consulta.filter(Guardia.curso_id == curso.id)

    @with_metrics("generar_guardias")
    def execute(
        self,
        eliminar_existentes: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancelacion: Optional[threading.Event] = None,
        desde: Optional["date"] = None,
    ) -> ResumenGeneracionDTO:
        """
        Ejecutar la generación de guardias.

        Args:
            eliminar_existentes: Si True, elimina las guardias existentes antes
            progress_callback: Función opcional para reportar progreso
                              Recibe (mensaje: str, porcentaje: int)
            cancelacion: Evento que, al activarse, detiene la generación
            desde: Si se indica, sólo se recalcula desde esa fecha; lo anterior y las
                sustituciones posteriores se conservan (FUN-002)

        Returns:
            ResumenGeneracionDTO con el resultado de la generación

        Raises:
            BusinessLogicError: Si hay errores en la generación
        """
        try:
            # Sólo las guardias del curso activo: antes se borraban las de todos
            # los cursos y generar el nuevo se llevaba el historial (2026-10-03).
            del_curso = self._guardias_del_curso_activo()
            count_guardias = del_curso.count()

            if count_guardias > 0 and eliminar_existentes:
                if progress_callback:
                    progress_callback("Eliminando guardias existentes...", 10)

                if desde is None:
                    borradas = del_curso.delete(synchronize_session=False)
                else:
                    # Incremental: sólo se borra lo recalculable. Lo anterior a la
                    # fecha y las sustituciones se quedan como están (FUN-002).
                    borradas = del_curso.filter(
                        Guardia.fecha >= desde, Guardia.es_sustitucion.is_(False)
                    ).delete(synchronize_session=False)
                logger.info(f"Eliminadas {borradas} guardias existentes (pendiente commit)")

            # Obtener estadísticas
            if progress_callback:
                progress_callback("Calculando distribución...", 30)

            stats = obtener_estadisticas(self.session) or {}
            esperado = stats.get("slots_totales", 0)

            if not self.session.query(Configuracion).first():
                raise BusinessLogicError("No existe configuración del curso")

            # Un solo algoritmo: el «Rápido» (v4) se retiró en la v6.7.0 porque ponía
            # dos guardias el mismo día y dejaba profesores lejos de su cuota.
            algoritmo = "cpsat"
            if progress_callback:
                progress_callback("Generando guardias...", 50)

            # Crear wrapper para adaptar callback (porcentaje, mensaje) -> (mensaje, porcentaje)
            def adapter_callback(porcentaje: int, mensaje: str = ""):
                if progress_callback:
                    # Escalar porcentaje de 0-100 a 50-80 (30% del rango total)
                    porcentaje_escalado = 50 + int(porcentaje * 0.30)
                    progress_callback(mensaje or "Generando guardias...", porcentaje_escalado)

            calendario, resumen = generar_guardias_cpsat(
                self.session, adapter_callback, cancelacion=cancelacion, desde=desde
            )
            if progress_callback:
                progress_callback("Guardando guardias en base de datos...", 80)
            guardar_guardias_cpsat_en_bd(self.session, calendario)

            if progress_callback:
                progress_callback("Proceso completado", 100)

            # Registrar en audit log. El commit es propio: las guardias ya se
            # guardaron dentro de guardar_*_en_bd, y sin esto el registro sólo
            # sobrevivía si otro flujo hacía commit más tarde (CRW-009).
            self.session.add(GuardiaAuditLog(
                accion="GENERADA_BULK",
                detalle=_json.dumps(
                    {
                        "total": len(calendario),
                        "algoritmo": algoritmo,
                        "desde": desde.isoformat() if desde else None,
                    }
                ),
            ))
            self.session.commit()

            # Preparar resumen
            total_generado = len(calendario)
            diff = esperado - total_generado if esperado else 0

            mensaje = self._generar_mensaje(total_generado, esperado, diff)

            logger.info(f"Guardias generadas: {total_generado} de {esperado} esperados")
            usage_log("GEN_CPSAT", algoritmo=algoritmo, guardias=total_generado, esperado=esperado)

            # Exportar comparación cuotas vs asignaciones para análisis
            self._exportar_comparacion_cuotas(resumen)

            return ResumenGeneracionDTO(
                guardias_generadas=total_generado,
                slots_esperados=esperado,
                slots_sin_cubrir=max(0, diff),
                resumen_por_profesor=resumen,
                mensaje=mensaje,
            )
        except InterruptedError:
            # Cancelación del usuario: no es un error que anunciar como tal.
            self.session.rollback()
            logger.info("Generación cancelada por el usuario")
            raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al generar guardias: {str(e)}")
            raise BusinessLogicError(f"No se pudo generar: {str(e)}") from e

    def _generar_mensaje(self, total_generado: int, esperado: int, diff: int) -> str:
        """
        Generar mensaje de resultado.

        Args:
            total_generado: Guardias generadas
            esperado: Slots esperados
            diff: Diferencia

        Returns:
            Mensaje descriptivo del resultado
        """
        if diff == 0:
            return "✅ Cobertura completa - Todas las guardias asignadas"
        elif diff > 0:
            return (
                f"⚠️ {diff} slots sin cubrir (puede deberse a falta de elegibilidad de profesores)"
            )
        else:
            return f"✅ {total_generado} guardias generadas de {esperado} esperados"

    def _exportar_comparacion_cuotas(self, asignaciones: dict) -> None:
        """
        Exporta la comparación entre cuotas calculadas y guardias asignadas.

        Genera un archivo JSON con:
        - Cuotas ideales calculadas por el servicio de distribución
        - Guardias realmente asignadas por el algoritmo
        - Diferencia (delta) entre ambos
        - Timestamp de generación

        El archivo se guarda en: logs/comparacion_cuotas_YYYYMMDD_HHMMSS.json
        """
        try:
            from services.distribucion_cuotas_service import DistribucionCuotasService

            # Calcular cuotas ideales
            cuotas_service = DistribucionCuotasService(self.session)
            profesores = self.session.query(Profesor).filter(Profesor.activo.is_(True)).all()
            cuotas_ideales = cuotas_service.calcular_cuotas(profesores)

            # Construir comparación
            comparacion = {
                "timestamp": datetime.now().isoformat(),
                "resumen": {
                    "total_cuotas_ideales": sum(cuotas_ideales.values()),
                    "total_asignadas": sum(asignaciones.values()),
                    "diferencia_global": sum(asignaciones.values()) - sum(cuotas_ideales.values()),
                },
                "profesores": [],
            }

            # Añadir detalle por profesor
            for profesor in profesores:
                cuota = cuotas_ideales.get(profesor.id, 0)
                asignada = asignaciones.get(profesor.id, 0)
                delta = asignada - cuota

                comparacion["profesores"].append(
                    {
                        "id": profesor.id,
                        "nombre": profesor.nombre_completo,
                        "porcentaje_jornada": profesor.porcentaje_jornada or 100,
                        "turno": profesor.turno or "mixto",
                        "cuota_ideal": cuota,
                        "guardias_asignadas": asignada,
                        "diferencia": delta,
                        "cumple_cuota": abs(delta) <= 1,
                    }
                )

            # Ordenar por diferencia (mayor discrepancia primero)
            comparacion["profesores"].sort(key=lambda x: abs(x["diferencia"]), reverse=True)

            # Añadir estadísticas de discrepancias
            discrepancias = [p for p in comparacion["profesores"] if abs(p["diferencia"]) > 1]
            comparacion["resumen"]["profesores_con_discrepancia"] = len(discrepancias)
            comparacion["resumen"]["max_discrepancia"] = (
                max(abs(p["diferencia"]) for p in comparacion["profesores"])
                if comparacion["profesores"]
                else 0
            )

            # Guardar archivo en el directorio de logs
            from core.paths import get_logs_directory

            logs_dir = get_logs_directory()

            filename = f"comparacion_cuotas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = logs_dir / filename

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(comparacion, f, ensure_ascii=False, indent=2)

            logger.info(f"📊 Comparación exportada a: {filepath}")
            self._podar_comparaciones_antiguas(logs_dir)

        except (OSError, ValueError) as e:
            logger.warning(f"No se pudo exportar comparación: {e}")

    @staticmethod
    def _podar_comparaciones_antiguas(logs_dir, conservar: int = 20) -> None:
        """Deja sólo las últimas comparaciones y borra el resto.

        Cada generación escribía un JSON con fecha en el nombre y nadie los
        borraba nunca: se acumulaban cientos en la carpeta de registros del
        usuario (COD-005).
        """
        try:
            archivos = sorted(
                logs_dir.glob("comparacion_cuotas_*.json"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            for sobrante in archivos[conservar:]:
                sobrante.unlink(missing_ok=True)
        except OSError as e:
            logger.debug(f"No se pudieron podar las comparaciones antiguas: {e}")
