"""
Use Case: Generar calendario de guardias.

Genera todas las guardias del curso y las guarda en la base de datos.
"""

from typing import Callable, Optional

from models.models import Guardia
from services.asignador_guardias import (
    generar_calendario_guardias,
    guardar_guardias_en_bd,
)
from services.calculador_guardias import obtener_estadisticas
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError
from utils.logger import get_logger

from application.dtos.asignacion_guardias_dto import ResumenGeneracionDTO

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

    def execute(
        self,
        eliminar_existentes: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> ResumenGeneracionDTO:
        """
        Ejecutar la generación de guardias.

        Args:
            eliminar_existentes: Si True, elimina las guardias existentes antes
            progress_callback: Función opcional para reportar progreso
                              Recibe (mensaje: str, porcentaje: int)

        Returns:
            ResumenGeneracionDTO con el resultado de la generación

        Raises:
            BusinessLogicError: Si hay errores en la generación
        """
        try:
            # Verificar guardias existentes
            count_guardias = self.session.query(Guardia).count()

            if count_guardias > 0 and eliminar_existentes:
                if progress_callback:
                    progress_callback("Eliminando guardias existentes...", 10)

                self.session.query(Guardia).delete()
                self.session.commit()
                logger.info(f"Eliminadas {count_guardias} guardias existentes")

            # Obtener estadísticas
            if progress_callback:
                progress_callback("Calculando distribución...", 30)

            stats = obtener_estadisticas(self.session) or {}
            esperado = stats.get("slots_totales", 0)

            # Generar calendario
            if progress_callback:
                progress_callback("Generando calendario de guardias...", 50)

            calendario, resumen = generar_calendario_guardias(self.session)

            # Guardar en base de datos
            if progress_callback:
                progress_callback("Guardando guardias en base de datos...", 80)

            guardar_guardias_en_bd(self.session, calendario)

            if progress_callback:
                progress_callback("Proceso completado", 100)

            # Preparar resumen
            total_generado = len(calendario)
            diff = esperado - total_generado if esperado else 0

            mensaje = self._generar_mensaje(total_generado, esperado, diff)

            logger.info(f"Guardias generadas: {total_generado} de {esperado} esperados")

            return ResumenGeneracionDTO(
                guardias_generadas=total_generado,
                slots_esperados=esperado,
                slots_sin_cubrir=max(0, diff),
                resumen_por_profesor=resumen,
                mensaje=mensaje,
            )

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error al generar guardias: {str(e)}")
            raise BusinessLogicError(f"No se pudo generar: {str(e)}") from e

    def _generar_mensaje(
        self, total_generado: int, esperado: int, diff: int
    ) -> str:
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
                f"⚠️ {diff} slots sin cubrir "
                f"(puede deberse a falta de elegibilidad de profesores)"
            )
        else:
            return f"✅ {total_generado} guardias generadas de {esperado} esperados"
