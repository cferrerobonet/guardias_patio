"""
Sistema de Health Checks

Verifica el estado de salud de los componentes críticos de la aplicación:
- Conectividad a base de datos
- Estado del cache
- Disponibilidad de configuración
- Recursos del sistema
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from utils.logger import get_logger

logger = get_logger(__name__)


class HealthState(Enum):
    """Estados posibles de salud de un componente."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Estado de salud de un componente individual."""

    name: str
    state: HealthState
    message: str = ""
    details: Dict[str, any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    response_time_ms: Optional[float] = None

    @property
    def is_healthy(self) -> bool:
        """Retorna True si el componente está saludable."""
        return self.state == HealthState.HEALTHY

    @property
    def is_degraded(self) -> bool:
        """Retorna True si el componente está degradado."""
        return self.state == HealthState.DEGRADED

    @property
    def is_unhealthy(self) -> bool:
        """Retorna True si el componente no está saludable."""
        return self.state == HealthState.UNHEALTHY


@dataclass
class HealthStatus:
    """Estado de salud general del sistema."""

    components: List[ComponentHealth] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_healthy(self) -> bool:
        """Retorna True si todos los componentes están saludables."""
        return all(c.is_healthy for c in self.components)

    @property
    def is_degraded(self) -> bool:
        """Retorna True si algún componente está degradado."""
        return any(c.is_degraded for c in self.components) and not any(
            c.is_unhealthy for c in self.components
        )

    @property
    def is_unhealthy(self) -> bool:
        """Retorna True si algún componente no está saludable."""
        return any(c.is_unhealthy for c in self.components)

    @property
    def overall_state(self) -> HealthState:
        """Retorna el estado general del sistema."""
        if self.is_unhealthy:
            return HealthState.UNHEALTHY
        elif self.is_degraded:
            return HealthState.DEGRADED
        elif self.is_healthy:
            return HealthState.HEALTHY
        return HealthState.UNKNOWN

    def get_component(self, name: str) -> Optional[ComponentHealth]:
        """Obtiene el estado de un componente específico."""
        for component in self.components:
            if component.name == name:
                return component
        return None

    def to_dict(self) -> Dict[str, any]:
        """Convierte el estado a diccionario."""
        return {
            "status": self.overall_state.value,
            "timestamp": self.timestamp.isoformat(),
            "components": [
                {
                    "name": c.name,
                    "status": c.state.value,
                    "message": c.message,
                    "details": c.details,
                    "response_time_ms": c.response_time_ms,
                }
                for c in self.components
            ],
        }


class HealthChecker:
    """
    Verificador de salud de la aplicación.

    Ejecuta health checks en todos los componentes críticos y
    proporciona un estado general del sistema.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Inicializa el health checker.

        Args:
            session: Sesión de SQLAlchemy (opcional)
        """
        self.session = session

    def check_database(self) -> ComponentHealth:
        """
        Verifica la salud de la base de datos.

        Returns:
            ComponentHealth con el estado de la BD
        """
        start_time = datetime.now()

        try:
            if self.session is None:
                from database.db_manager import SessionLocal

                self.session = SessionLocal()
                close_session = True
            else:
                close_session = False

            # Test simple query
            self.session.execute(text("SELECT 1"))
            self.session.commit()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if close_session:
                self.session.close()

            # Determinar estado basado en tiempo de respuesta
            if response_time < 50:
                state = HealthState.HEALTHY
                message = "Base de datos funcionando correctamente"
            elif response_time < 200:
                state = HealthState.DEGRADED
                message = f"Base de datos respondiendo lentamente ({response_time:.1f}ms)"
            else:
                state = HealthState.DEGRADED
                message = f"Base de datos muy lenta ({response_time:.1f}ms)"

            return ComponentHealth(
                name="database",
                state=state,
                message=message,
                details={"response_time_ms": round(response_time, 2)},
                response_time_ms=round(response_time, 2),
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error("Health check de database falló", exc_info=e)

            return ComponentHealth(
                name="database",
                state=HealthState.UNHEALTHY,
                message=f"Error de conectividad: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                response_time_ms=round(response_time, 2),
            )

    def check_cache(self) -> ComponentHealth:
        """
        Verifica la salud del sistema de cache.

        Returns:
            ComponentHealth con el estado del cache
        """
        start_time = datetime.now()

        try:
            # Importar funciones de cache
            from utils.cache import get_cache_stats

            # Obtener estadísticas del cache
            stats = get_cache_stats()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Cache está siempre operativo (es en memoria)
            state = HealthState.HEALTHY
            message = f"Cache operativo ({stats['size']} entradas)"
            details = {
                "hits": stats["hits"],
                "misses": stats["misses"],
                "hit_rate": round(stats["hit_rate"], 2),
                "size": stats["size"],
            }

            return ComponentHealth(
                name="cache",
                state=state,
                message=message,
                details=details,
                response_time_ms=round(response_time, 2),
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error("Health check de cache falló", exc_info=e)

            return ComponentHealth(
                name="cache",
                state=HealthState.UNHEALTHY,
                message=f"Error en cache: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                response_time_ms=round(response_time, 2),
            )

    def check_configuration(self) -> ComponentHealth:
        """
        Verifica que la configuración esté disponible.

        Returns:
            ComponentHealth con el estado de la configuración
        """
        start_time = datetime.now()

        try:
            from application.use_cases.configuracion import ObtenerConfiguracionUseCase

            use_case = ObtenerConfiguracionUseCase(self.session)
            config = use_case.execute()

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            if config:
                state = HealthState.HEALTHY
                message = "Configuración cargada correctamente"
                details = {
                    "fecha_inicio_curso": config.fecha_inicio_curso.isoformat()
                    if config.fecha_inicio_curso
                    else None,
                    "fecha_fin_curso": config.fecha_fin_curso.isoformat()
                    if config.fecha_fin_curso
                    else None,
                }
            else:
                state = HealthState.DEGRADED
                message = "Configuración no encontrada"
                details = {}

            return ComponentHealth(
                name="configuration",
                state=state,
                message=message,
                details=details,
                response_time_ms=round(response_time, 2),
            )

        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error("Health check de configuración falló", exc_info=e)

            return ComponentHealth(
                name="configuration",
                state=HealthState.UNHEALTHY,
                message=f"Error al obtener configuración: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__},
                response_time_ms=round(response_time, 2),
            )

    def check_system_resources(self) -> ComponentHealth:
        """
        Verifica los recursos del sistema (CPU, memoria).

        Returns:
            ComponentHealth con el estado de los recursos
        """
        start_time = datetime.now()

        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.1)

            response_time = (datetime.now() - start_time).total_seconds() * 1000

            # Umbrales
            memory_warning_mb = 500
            memory_critical_mb = 1000
            cpu_warning = 70
            cpu_critical = 90

            if memory_mb < memory_warning_mb and cpu_percent < cpu_warning:
                state = HealthState.HEALTHY
                message = "Recursos del sistema normales"
            elif memory_mb < memory_critical_mb and cpu_percent < cpu_critical:
                state = HealthState.DEGRADED
                message = "Recursos del sistema bajo presión"
            else:
                state = HealthState.UNHEALTHY
                message = "Recursos del sistema críticos"

            return ComponentHealth(
                name="system_resources",
                state=state,
                message=message,
                details={
                    "memory_mb": round(memory_mb, 2),
                    "cpu_percent": round(cpu_percent, 2),
                },
                response_time_ms=round(response_time, 2),
            )

        except ImportError:
            # psutil no disponible
            return ComponentHealth(
                name="system_resources",
                state=HealthState.UNKNOWN,
                message="psutil no disponible para monitoreo de recursos",
                details={},
            )
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error("Health check de recursos falló", exc_info=e)

            return ComponentHealth(
                name="system_resources",
                state=HealthState.DEGRADED,
                message=f"Error al obtener recursos: {str(e)}",
                details={"error": str(e)},
                response_time_ms=round(response_time, 2),
            )

    def check_all(self) -> HealthStatus:
        """
        Ejecuta todos los health checks.

        Returns:
            HealthStatus con el estado de todos los componentes
        """
        components = [
            self.check_database(),
            self.check_cache(),
            self.check_configuration(),
            self.check_system_resources(),
        ]

        return HealthStatus(components=components)

    def check_component(self, component_name: str) -> Optional[ComponentHealth]:
        """
        Ejecuta health check de un componente específico.

        Args:
            component_name: Nombre del componente (database, cache, etc.)

        Returns:
            ComponentHealth o None si el componente no existe
        """
        checkers = {
            "database": self.check_database,
            "cache": self.check_cache,
            "configuration": self.check_configuration,
            "system_resources": self.check_system_resources,
        }

        checker = checkers.get(component_name)
        if checker:
            return checker()
        return None

    def is_healthy(self) -> bool:
        """Verifica si el sistema está saludable."""
        status = self.check_all()
        return status.is_healthy

    def get_status_summary(self) -> str:
        """
        Obtiene un resumen textual del estado de salud.

        Returns:
            String con resumen del estado
        """
        status = self.check_all()
        lines = [f"🏥 Estado de Salud: {status.overall_state.value.upper()}"]
        lines.append("=" * 50)

        for component in status.components:
            icon = "✅" if component.is_healthy else "⚠️" if component.is_degraded else "❌"
            lines.append(f"{icon} {component.name}: {component.message}")
            if component.response_time_ms:
                lines.append(f"   └─ Tiempo de respuesta: {component.response_time_ms}ms")

        return "\n".join(lines)


# Instancia global del health checker
_health_checker: Optional[HealthChecker] = None


def get_health_checker(session: Optional[Session] = None) -> HealthChecker:
    """
    Obtiene la instancia global del health checker.

    Args:
        session: Sesión de SQLAlchemy (opcional)

    Returns:
        Instancia del HealthChecker
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(session)
    return _health_checker
