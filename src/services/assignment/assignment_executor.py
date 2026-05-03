"""
AssignmentExecutor - Ejecución de asignaciones

Responsabilidad: Orquestar el proceso de asignación completo,
coordinando SlotBuilder, ProfesorFilter y ScoreCalculator.
"""

from collections import defaultdict
from datetime import date
from typing import Callable, Dict, List, Optional, Set, Tuple

from services.asignacion_guardia_service import AsignacionGuardiaService
from services.disponibilidad_profesor_service import DisponibilidadProfesorService
from services.distribucion_cuotas_service import DistribucionCuotasService
from services.equidad_guardias_service import EquidadGuardiasService
from infrastructure.database.models import Ausencia, Configuracion, Guardia, Profesor
from services.assignment.profesor_filter import ProfesorFilter, _limpiar_cache_elegibilidad
from services.assignment.score_calculator import ScoreCalculator
from services.assignment.slot_builder import SlotBuilder
from services.estadisticas_service import EstadisticasService
from infrastructure.repositories.repository_factory import RepositoryFactory
from utils import get_logger

logger = get_logger(__name__)


class AssignmentExecutor:
    """
    Ejecutor del proceso de asignación de guardias.

    Coordina todos los componentes para generar un calendario
    completo de guardias.
    """

    def __init__(self, session_or_factory):
        self.session = (
            session_or_factory.session
            if isinstance(session_or_factory, RepositoryFactory)
            else session_or_factory
        )
        session = self.session
        self.slot_builder = SlotBuilder(session)
        self.profesor_filter = ProfesorFilter(session)
        self.score_calculator = ScoreCalculator()
        self.stats_service = EstadisticasService()

        # Domain Services (DDD)
        self.disponibilidad_service = DisponibilidadProfesorService(session)
        self.distribucion_service = DistribucionCuotasService(session)
        self.asignacion_service = AsignacionGuardiaService(session)
        self.equidad_service = EquidadGuardiasService(session)

    def ejecutar_asignacion(
        self,
        config: Configuracion,
        profesores: List[Profesor],
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Tuple[List[Guardia], List[str]]:
        """
        Ejecuta la asignación completa de guardias.

        Args:
            config: Configuración del periodo
            profesores: Lista de profesores activos
            progress_callback: Callback para reportar progreso

        Returns:
            Tupla (calendario_guardias, incidencias)
        """
        # Limpiar cachés
        _limpiar_cache_elegibilidad()

        # Paso 1: Construir slots
        logger.info("Construyendo slots...")
        slots = self.slot_builder.build_slots(config)

        if not slots:
            logger.error("No se generaron slots")
            return [], ["No se generaron slots"]

        total_slots = len(slots)
        logger.info(f"Total de slots a asignar: {total_slots}")

        # Paso 2: Calcular cuotas usando Domain Service
        logger.info("Calculando cuotas por profesor...")
        cuotas = self.distribucion_service.calcular_cuotas(profesores)
        logger.info(f"Cuotas calculadas: {len(cuotas)} profesores")

        # Paso 3: Inicializar estructuras
        calendario: List[Guardia] = []
        incidencias: List[str] = []
        asignaciones_profesor: Dict[int, int] = defaultdict(int)
        guardias_en_fecha: Dict[Tuple[date, int], Set[int]] = defaultdict(set)

        # Paso 4: Asignar slot por slot
        for idx, slot in enumerate(slots):
            if progress_callback:
                porcentaje = int((idx / total_slots) * 100)
                progress_callback(
                    porcentaje,
                    total_slots,
                    f"Asignando guardia {idx + 1}/{total_slots}",
                )

            # Filtrar profesores elegibles
            elegibles = self.profesor_filter.obtener_profesores_elegibles(
                profesores=profesores,
                slot=slot,
                asignaciones_profesor=asignaciones_profesor,
                cuotas=cuotas,
                guardias_en_fecha=guardias_en_fecha,
            )

            if not elegibles:
                msg = (
                    f"No hay profesores elegibles para "
                    f"{slot.fecha} recreo {slot.recreo_id} zona {slot.zona_id}"
                )
                incidencias.append(msg)
                logger.warning(msg)
                continue

            # Seleccionar mejor profesor
            try:
                mejor = self.score_calculator.seleccionar_mejor(
                    candidatos=elegibles,
                    slot=slot,
                    asignaciones_profesor=asignaciones_profesor,
                    cuotas=cuotas,
                    guardias_en_fecha=guardias_en_fecha,
                    profesores=profesores,
                )
            except ValueError as e:
                incidencias.append(f"Error seleccionando profesor: {e}")
                continue

            # Crear guardia
            guardia = Guardia(
                fecha=slot.fecha,
                recreo=slot.recreo_id,
                zona_id=slot.zona_id,
                profesor_id=mejor.id,
            )
            calendario.append(guardia)

            # Actualizar contadores
            asignaciones_profesor[mejor.id] += 1
            guardias_en_fecha[(slot.fecha, slot.recreo_id)].add(mejor.id)

        # Paso 5: Reportar estadísticas
        if progress_callback:
            progress_callback(100, total_slots, "Asignación completada")

        logger.info(f"Calendario generado: {len(calendario)} guardias asignadas")
        logger.info(f"Incidencias: {len(incidencias)}")

        # Generar y mostrar estadísticas usando el servicio
        stats = self.stats_service.generar_resumen_completo(
            guardias=calendario,
            profesores=profesores,
            cuotas=cuotas,
            total_slots=total_slots,
        )
        self.stats_service.log_resumen(stats)

        # Estadísticas de filtrado
        filter_stats = self.profesor_filter.get_estadisticas()
        logger.info(f"Estadísticas de filtrado: {filter_stats}")

        # Evaluar equidad usando Domain Service
        if calendario:
            logger.info("\n" + "=" * 60)
            logger.info("ANÁLISIS DE EQUIDAD")
            logger.info("=" * 60)
            self.equidad_service.log_reporte_equidad(calendario, cuotas)
            indice_equidad = self.equidad_service.calcular_indice_equidad(calendario, cuotas)
            logger.info(f"\n📊 Índice de Equidad Global: {indice_equidad:.2%}")

            # Identificar desbalances
            desbalances = self.equidad_service.identificar_desbalances(calendario, cuotas)
            if desbalances:
                logger.warning(f"⚠️  Se identificaron {len(desbalances)} desbalances")
            logger.info("=" * 60 + "\n")

        return calendario, incidencias

    def guardar_guardias(self, calendario: List[Guardia]) -> None:
        """
        Guarda las guardias en la base de datos.

        Args:
            calendario: Lista de guardias a guardar
        """
        if not calendario:
            logger.warning("No hay guardias para guardar")
            return

        # Limpiar guardias existentes
        self.session.query(Ausencia).delete()
        self.session.query(Guardia).delete()

        # Insertar nuevas guardias
        for guardia in calendario:
            self.session.add(guardia)

        self.session.flush()
        logger.info(f"{len(calendario)} guardias guardadas en BD")
