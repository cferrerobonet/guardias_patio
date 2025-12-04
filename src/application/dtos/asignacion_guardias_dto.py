"""
DTOs para Asignación de Guardias.

Permite transferir datos relacionados con estadísticas y generación de guardias.
"""

from datetime import date
from typing import Dict, List, Optional

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


# --- DTOs para Panel de Estadísticas ---


class ResumenPanelDTO(BaseModel):
    """DTO para resumen general del panel de estadísticas."""

    total_guardias: int = Field(default=0, ge=0)
    profesores_con_guardias: int = Field(default=0, ge=0)
    total_profesores: int = Field(default=0, ge=0)
    total_zonas: int = Field(default=0, ge=0)
    guardias_manana: int = Field(default=0, ge=0)
    guardias_tarde: int = Field(default=0, ge=0)
    promedio_por_profesor: float = Field(default=0.0)
    cobertura_estimada: int = Field(default=0, ge=0, le=100)

    model_config = {"from_attributes": True}


class EstadisticaProfesorDTO(BaseModel):
    """DTO para estadísticas de un profesor."""

    profesor_id: int
    nombre_completo: str
    total: int = Field(default=0, ge=0)
    manana: int = Field(default=0, ge=0)
    tarde: int = Field(default=0, ge=0)
    porcentaje: float = Field(default=0.0)
    estado: str = Field(default="❌ Sin guardias")
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None

    model_config = {"from_attributes": True}


class EstadisticaZonaDTO(BaseModel):
    """DTO para estadísticas de una zona."""

    zona_id: int
    nombre_zona: str
    total_guardias: int = Field(default=0, ge=0)
    profesores_diferentes: int = Field(default=0, ge=0)
    porcentaje_cobertura: str = Field(default="N/A")

    model_config = {"from_attributes": True}


class DatosGraficoDTO(BaseModel):
    """DTO para datos de gráficos."""

    nombres: List[str] = Field(default_factory=list)
    cantidades: List[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class EstadisticasPanelCompletoDTO(BaseModel):
    """DTO completo para el panel de estadísticas."""

    resumen: ResumenPanelDTO
    por_profesor: List[EstadisticaProfesorDTO] = Field(default_factory=list)
    por_zona: List[EstadisticaZonaDTO] = Field(default_factory=list)
    grafico_profesores: DatosGraficoDTO = Field(default_factory=DatosGraficoDTO)
    grafico_zonas: DatosGraficoDTO = Field(default_factory=DatosGraficoDTO)

    model_config = {"from_attributes": True}
