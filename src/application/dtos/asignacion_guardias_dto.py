"""
DTOs para Asignación de Guardias.

Permite transferir datos relacionados con estadísticas y generación de guardias.
"""

from typing import Dict, Optional

from pydantic import BaseModel, Field


class EstadisticasDTO(BaseModel):
    """DTO para estadísticas del curso"""

    dias_lectivos: int = Field(..., ge=0)
    recreos_manana: int = Field(..., ge=0)
    recreos_tarde: int = Field(..., ge=0)
    num_zonas: int = Field(..., ge=0)
    num_profesores: int = Field(..., ge=0)
    slots_totales: int = Field(..., ge=0)

    model_config = {"from_attributes": True}


class DistribucionDTO(BaseModel):
    """DTO para distribución de guardias por profesor"""

    distribucion: Dict[int, int]  # profesor_id -> número de guardias
    total_guardias: int = Field(..., ge=0)
    slots_totales: int = Field(..., ge=0)

    @property
    def diferencia(self) -> int:
        """Diferencia entre guardias calculadas y slots disponibles"""
        return self.slots_totales - self.total_guardias

    @property
    def es_exacta(self) -> bool:
        """True si la distribución cubre exactamente todos los slots"""
        return self.diferencia == 0

    model_config = {"from_attributes": True}


class ResumenGeneracionDTO(BaseModel):
    """DTO para resumen de generación de guardias"""

    guardias_generadas: int = Field(..., ge=0)
    slots_esperados: int = Field(..., ge=0)
    slots_sin_cubrir: int = Field(..., ge=0)
    resumen_por_profesor: Dict[int, int]  # profesor_id -> count
    mensaje: Optional[str] = None

    @property
    def cobertura_completa(self) -> bool:
        """True si se cubrieron todos los slots"""
        return self.slots_sin_cubrir == 0

    model_config = {"from_attributes": True}
