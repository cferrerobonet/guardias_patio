"""
DTOs específicos para Domain Services Integration (Phase 3)

DTOs para operaciones que usan los Domain Services de Phase 2.4:
- DisponibilidadProfesorService
- DistribucionCuotasService
- AsignacionGuardiaService
- EquidadGuardiasService
"""

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional


class AlgoritmoAsignacion(str, Enum):
    """Tipos de algoritmos de asignación disponibles."""

    V2_9_LEGACY = "v2.9"
    V3_SIMPLE = "v3_simple"
    V4_MODULAR = "v4"
    ITERATIVO = "iterativo"
    ILP = "ilp"


@dataclass(frozen=True)
class CuotaProfesorDTO:
    """DTO para cuota de guardias de un profesor."""

    profesor_id: int
    profesor_nombre: str
    cuota_esperada: int
    porcentaje_jornada: float = 100.0
    cuota_asignada: int = 0
    turno: str = "mixto"  # mañana, tarde, mixto

    @property
    def porcentaje_cumplimiento(self) -> float:
        """Porcentaje de cuota cumplida."""
        if self.cuota_esperada == 0:
            return 100.0
        return (self.cuota_asignada / self.cuota_esperada) * 100

    @property
    def deficit(self) -> int:
        """Déficit de guardias (negativo si hay exceso)."""
        return self.cuota_esperada - self.cuota_asignada


@dataclass(frozen=True)
class EquidadMetricasDTO:
    """DTO para métricas de equidad."""

    indice_equidad: float  # 0.0 a 1.0 (1.0 = perfecta equidad)
    coeficiente_variacion: float
    desviacion_estandar: float
    desbalances_detectados: int
    profesores_con_deficit: int
    profesores_con_exceso: int

    @property
    def nivel_equidad(self) -> str:
        """Clasificación del nivel de equidad."""
        if self.indice_equidad >= 0.95:
            return "EXCELENTE"
        elif self.indice_equidad >= 0.85:
            return "BUENO"
        elif self.indice_equidad >= 0.70:
            return "ACEPTABLE"
        else:
            return "DEFICIENTE"


@dataclass(frozen=True)
class DisponibilidadDTO:
    """DTO para disponibilidad de un profesor."""

    profesor_id: int
    fecha: date
    recreo_id: int
    disponible: bool
    razon_no_disponible: Optional[str] = None


# Request/Response DTOs para Use Cases


@dataclass(frozen=True)
class CalcularCuotasRequest:
    """Request para calcular cuotas de profesores."""

    configuracion_id: int
    solo_activos: bool = True


@dataclass(frozen=True)
class CalcularCuotasResponse:
    """Response de cálculo de cuotas."""

    exitoso: bool
    cuotas: Dict[int, int]  # profesor_id -> cuota
    cuotas_detalle: List[CuotaProfesorDTO]
    total_guardias: int
    mensaje: str


@dataclass(frozen=True)
class AnalisisEquidadRequest:
    """Request para analizar equidad de guardias."""

    configuracion_id: Optional[int] = None
    incluir_detalle: bool = True
    umbral_desbalance: float = 0.15  # 15% de desviación


@dataclass(frozen=True)
class AnalisisEquidadResponse:
    """Response de análisis de equidad."""

    exitoso: bool
    metricas: EquidadMetricasDTO
    cuotas: List[CuotaProfesorDTO]
    recomendaciones: List[str]
    mensaje: str


@dataclass(frozen=True)
class ValidarDisponibilidadRequest:
    """Request para validar disponibilidad de profesores."""

    profesor_id: int
    fecha: date
    recreo_id: int


@dataclass(frozen=True)
class ValidarDisponibilidadResponse:
    """Response de validación de disponibilidad."""

    disponible: bool
    profesor_nombre: str
    razon_no_disponible: Optional[str] = None


@dataclass(frozen=True)
class GenerarGuardiasConDomainServicesRequest:
    """Request mejorado para generar guardias usando Domain Services."""

    configuracion_id: int
    algoritmo: AlgoritmoAsignacion = AlgoritmoAsignacion.V4_MODULAR
    forzar_regeneracion: bool = False
    validar_antes: bool = True
    calcular_equidad_despues: bool = True


@dataclass(frozen=True)
class GenerarGuardiasConDomainServicesResponse:
    """Response mejorado con información de Domain Services."""

    exitoso: bool
    total_guardias: int
    cobertura_porcentaje: float
    cuotas: List[CuotaProfesorDTO]
    equidad: Optional[EquidadMetricasDTO]
    algoritmo_usado: AlgoritmoAsignacion
    tiempo_ejecucion_segundos: float
    mensaje: str
    warnings: List[str] = field(default_factory=list)
    errores: List[str] = field(default_factory=list)
