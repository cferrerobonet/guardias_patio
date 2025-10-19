"""
Performance Monitoring

Sistema de monitoreo de performance para detectar operaciones lentas,
N+1 queries, y degradación del sistema.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceRecord:
    """Registro de una operación de performance."""

    operation: str
    duration_ms: float
    timestamp: datetime
    metadata: Dict[str, any] = field(default_factory=dict)
    is_slow: bool = False


@dataclass
class PerformanceStats:
    """Estadísticas de performance de una operación."""

    operation: str
    count: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    slow_operations: int


class PerformanceMonitor:
    """
    Monitor de performance que rastrea operaciones lentas y detecta degradación.

    Características:
    - Detección automática de operaciones lentas
    - Estadísticas por operación
    - Detección de N+1 queries
    - Alertas de degradación
    """

    def __init__(
        self,
        slow_threshold_ms: float = 1000,
        very_slow_threshold_ms: float = 5000,
        max_records: int = 1000,
    ):
        """
        Inicializa el monitor de performance.

        Args:
            slow_threshold_ms: Umbral para operaciones lentas (ms)
            very_slow_threshold_ms: Umbral para operaciones muy lentas (ms)
            max_records: Máximo de registros a mantener en memoria
        """
        self.slow_threshold_ms = slow_threshold_ms
        self.very_slow_threshold_ms = very_slow_threshold_ms
        self.max_records = max_records

        # Almacenamiento de registros
        self._records: List[PerformanceRecord] = []

        # Estadísticas por operación
        self._operation_stats: Dict[str, List[float]] = defaultdict(list)

        # Detección de N+1
        self._query_patterns: Dict[str, int] = defaultdict(int)
        self._query_window_start = datetime.now()

        # Alertas
        self._alerts: List[str] = []

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, any]] = None,
    ):
        """
        Registra una operación y su duración.

        Args:
            operation: Nombre de la operación
            duration_ms: Duración en milisegundos
            metadata: Metadata adicional
        """
        is_slow = duration_ms >= self.slow_threshold_ms

        record = PerformanceRecord(
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            metadata=metadata or {},
            is_slow=is_slow,
        )

        # Agregar a registros
        self._records.append(record)

        # Limitar tamaño
        if len(self._records) > self.max_records:
            self._records = self._records[-self.max_records :]

        # Actualizar estadísticas
        self._operation_stats[operation].append(duration_ms)

        # Detectar operaciones muy lentas
        if duration_ms >= self.very_slow_threshold_ms:
            alert = (
                f"⚠️  Operación muy lenta: {operation} "
                f"tomó {duration_ms:.2f}ms (umbral: {self.very_slow_threshold_ms}ms)"
            )
            self._alerts.append(alert)
            logger.warning(alert, extra={"operation": operation, "duration_ms": duration_ms})

        # Log de operaciones lentas
        if is_slow:
            logger.warning(
                f"Operación lenta detectada: {operation}",
                extra={
                    "operation": operation,
                    "duration_ms": duration_ms,
                    "threshold_ms": self.slow_threshold_ms,
                },
            )

    def record_query(self, query_type: str, table: str, duration_ms: float):
        """
        Registra una query a la base de datos.

        Args:
            query_type: Tipo de query (select, insert, update, delete)
            table: Tabla afectada
            duration_ms: Duración en ms
        """
        # Registrar como operación normal
        self.record_operation(
            f"db_{query_type}_{table}",
            duration_ms,
            {"query_type": query_type, "table": table},
        )

        # Detectar posible N+1
        pattern = f"{query_type}_{table}"
        self._query_patterns[pattern] += 1

        # Resetear ventana cada minuto
        if (datetime.now() - self._query_window_start).total_seconds() > 60:
            self._check_n_plus_one()
            self._query_patterns.clear()
            self._query_window_start = datetime.now()

    def _check_n_plus_one(self):
        """Detecta posibles problemas de N+1 queries."""
        for pattern, count in self._query_patterns.items():
            if count > 50:  # Más de 50 queries similares en 1 minuto
                alert = (
                    f"⚠️  Posible N+1 query detectado: {pattern} "
                    f"ejecutado {count} veces en 1 minuto"
                )
                self._alerts.append(alert)
                logger.warning(
                    "Posible N+1 query detectado",
                    extra={"pattern": pattern, "count": count},
                )

    def get_slow_operations(
        self, limit: int = 10, minutes: int = 60
    ) -> List[PerformanceRecord]:
        """
        Obtiene las operaciones más lentas recientes.

        Args:
            limit: Número máximo de resultados
            minutes: Ventana de tiempo en minutos

        Returns:
            Lista de operaciones lentas
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)

        slow_ops = [
            record
            for record in self._records
            if record.is_slow and record.timestamp >= cutoff
        ]

        # Ordenar por duración descendente
        slow_ops.sort(key=lambda x: x.duration_ms, reverse=True)

        return slow_ops[:limit]

    def get_operation_stats(self, operation: str) -> Optional[PerformanceStats]:
        """
        Obtiene estadísticas de una operación específica.

        Args:
            operation: Nombre de la operación

        Returns:
            Estadísticas de la operación o None si no existe
        """
        if operation not in self._operation_stats:
            return None

        durations = self._operation_stats[operation]
        if not durations:
            return None

        sorted_durations = sorted(durations)
        count = len(sorted_durations)

        return PerformanceStats(
            operation=operation,
            count=count,
            total_duration_ms=sum(durations),
            avg_duration_ms=sum(durations) / count,
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            p50_duration_ms=sorted_durations[int(count * 0.50)],
            p95_duration_ms=sorted_durations[int(count * 0.95)],
            p99_duration_ms=sorted_durations[int(count * 0.99)],
            slow_operations=sum(
                1 for d in durations if d >= self.slow_threshold_ms
            ),
        )

    def get_all_operations_stats(self) -> List[PerformanceStats]:
        """
        Obtiene estadísticas de todas las operaciones.

        Returns:
            Lista de estadísticas por operación
        """
        stats = []
        for operation in self._operation_stats.keys():
            op_stats = self.get_operation_stats(operation)
            if op_stats:
                stats.append(op_stats)

        # Ordenar por duración promedio descendente
        stats.sort(key=lambda x: x.avg_duration_ms, reverse=True)

        return stats

    def get_alerts(self, clear: bool = False) -> List[str]:
        """
        Obtiene alertas de performance.

        Args:
            clear: Si True, limpia las alertas después de obtenerlas

        Returns:
            Lista de mensajes de alerta
        """
        alerts = self._alerts.copy()
        if clear:
            self._alerts.clear()
        return alerts

    def check_degradation(
        self, operation: str, current_duration_ms: float
    ) -> bool:
        """
        Verifica si hay degradación de performance en una operación.

        Args:
            operation: Nombre de la operación
            current_duration_ms: Duración actual en ms

        Returns:
            True si hay degradación (>50% más lenta que el promedio)
        """
        stats = self.get_operation_stats(operation)
        if not stats or stats.count < 10:  # Necesitamos suficientes datos
            return False

        # Degradación si es >50% más lenta que el promedio
        threshold = stats.avg_duration_ms * 1.5
        is_degraded = current_duration_ms > threshold

        if is_degraded:
            alert = (
                f"⚠️  Degradación detectada en {operation}: "
                f"{current_duration_ms:.2f}ms vs {stats.avg_duration_ms:.2f}ms promedio "
                f"({((current_duration_ms / stats.avg_duration_ms - 1) * 100):.1f}% más lento)"
            )
            self._alerts.append(alert)
            logger.warning(
                "Degradación de performance detectada",
                extra={
                    "operation": operation,
                    "current_ms": current_duration_ms,
                    "avg_ms": stats.avg_duration_ms,
                    "degradation_pct": (
                        (current_duration_ms / stats.avg_duration_ms - 1) * 100
                    ),
                },
            )

        return is_degraded

    def get_summary(self) -> Dict[str, any]:
        """
        Obtiene un resumen del estado de performance.

        Returns:
            Diccionario con resumen
        """
        total_records = len(self._records)
        slow_records = sum(1 for r in self._records if r.is_slow)

        recent_records = [
            r
            for r in self._records
            if (datetime.now() - r.timestamp).total_seconds() < 300
        ]  # Últimos 5 min

        return {
            "total_operations": total_records,
            "slow_operations": slow_records,
            "slow_percentage": (
                (slow_records / total_records * 100) if total_records > 0 else 0
            ),
            "recent_operations_5min": len(recent_records),
            "tracked_operation_types": len(self._operation_stats),
            "active_alerts": len(self._alerts),
            "slow_threshold_ms": self.slow_threshold_ms,
        }

    def reset_stats(self):
        """Resetea todas las estadísticas."""
        self._records.clear()
        self._operation_stats.clear()
        self._query_patterns.clear()
        self._alerts.clear()
        logger.info("Estadísticas de performance reseteadas")


# Instancia global
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Obtiene la instancia global del monitor de performance.

    Returns:
        Instancia del PerformanceMonitor
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor
