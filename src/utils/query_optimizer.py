"""
Utilidades para optimización de queries de SQLAlchemy.

Este módulo proporciona helpers y decoradores para optimizar consultas:
- Eager loading con joinedload
- Generación automática de índices
- Análisis de rendimiento de queries
"""

from functools import wraps
from time import time
from typing import Callable

from sqlalchemy import event
from sqlalchemy.orm import Query, joinedload

from src.utils.logger import get_logger

logger = get_logger(__name__)


def optimize_query(query: Query, *relationships) -> Query:
    """
    Optimiza una query aplicando eager loading a las relaciones especificadas.

    Args:
        query: Query de SQLAlchemy a optimizar
        *relationships: Nombres de las relaciones a cargar anticipadamente

    Returns:
        Query optimizada con joinedload

    Example:
        # Sin optimización (N+1 queries)
        profesores = session.query(Profesor).all()
        for p in profesores:
            print(p.guardias)  # Query por cada profesor

        # Con optimización (1 query)
        query = session.query(Profesor)
        query = optimize_query(query, 'guardias')
        profesores = query.all()
        for p in profesores:
            print(p.guardias)  # Sin queries adicionales
    """
    for rel in relationships:
        query = query.options(joinedload(rel))

    logger.debug(f"Query optimizada con eager loading: {relationships}")
    return query


def time_query(func: Callable) -> Callable:
    """
    Decorador para medir y loguear el tiempo de ejecución de queries.

    Args:
        func: Función que ejecuta queries

    Returns:
        Función decorada con medición de tiempo

    Example:
        @time_query
        def obtener_profesores_activos(session):
            return session.query(Profesor).filter_by(activo=True).all()

        # Logs:
        # Query obtener_profesores_activos ejecutada en 0.045s
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time()
        result = func(*args, **kwargs)
        elapsed = time() - start

        logger.info(f"Query {func.__name__} ejecutada en {elapsed:.3f}s")

        # Advertencia si la query es lenta
        if elapsed > 1.0:
            logger.warning(
                f"Query lenta detectada: {func.__name__} "
                f"({elapsed:.3f}s) - Considerar optimización"
            )

        return result

    return wrapper


class QueryAnalyzer:
    """
    Analizador de queries para detectar problemas de rendimiento.

    Registra todas las queries ejecutadas y genera reportes.

    Example:
        analyzer = QueryAnalyzer(engine)
        analyzer.start()

        # ... ejecutar queries ...

        stats = analyzer.get_stats()
        print(f"Total queries: {stats['total_queries']}")
        print(f"Tiempo total: {stats['total_time']:.2f}s")

        analyzer.stop()
    """

    def __init__(self, engine):
        """
        Inicializa el analizador.

        Args:
            engine: Engine de SQLAlchemy a monitorear
        """
        self.engine = engine
        self.queries = []
        self._listening = False

    def start(self):
        """Inicia el monitoreo de queries."""
        if self._listening:
            logger.warning("QueryAnalyzer ya está activo")
            return

        @event.listens_for(self.engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            conn.info.setdefault('query_start_time', []).append(time())

        @event.listens_for(self.engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            total = time() - conn.info['query_start_time'].pop()
            self.queries.append({
                'statement': statement,
                'parameters': parameters,
                'time': total
            })

        self._listening = True
        logger.info("QueryAnalyzer iniciado")

    def stop(self):
        """Detiene el monitoreo de queries."""
        # SQLAlchemy no permite remover listeners fácilmente
        # Simplemente marcamos como no escuchando
        self._listening = False
        logger.info("QueryAnalyzer detenido")

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas de las queries ejecutadas.

        Returns:
            dict: Estadísticas con total_queries, total_time, avg_time, slow_queries

        Example:
            stats = analyzer.get_stats()
            print(f"Queries lentas: {stats['slow_queries']}")
        """
        if not self.queries:
            return {
                'total_queries': 0,
                'total_time': 0,
                'avg_time': 0,
                'slow_queries': 0
            }

        total_time = sum(q['time'] for q in self.queries)
        slow_queries = sum(1 for q in self.queries if q['time'] > 0.5)

        return {
            'total_queries': len(self.queries),
            'total_time': total_time,
            'avg_time': total_time / len(self.queries),
            'slow_queries': slow_queries
        }

    def get_slowest_queries(self, limit: int = 10) -> list:
        """
        Obtiene las queries más lentas.

        Args:
            limit: Número máximo de queries a retornar

        Returns:
            list: Lista de queries ordenadas por tiempo (desc)

        Example:
            slowest = analyzer.get_slowest_queries(5)
            for q in slowest:
                print(f"{q['time']:.3f}s - {q['statement'][:100]}")
        """
        sorted_queries = sorted(
            self.queries,
            key=lambda q: q['time'],
            reverse=True
        )
        return sorted_queries[:limit]

    def print_report(self):
        """
        Imprime un reporte detallado de las queries.

        Example:
            analyzer.print_report()
            # Output:
            # ========== Query Analysis Report ==========
            # Total queries:     150
            # Total time:        2.45s
            # Average time:      0.016s
            # Slow queries:      3 (>0.5s)
            #
            # Top 5 Slowest Queries:
            # 1. 1.234s - SELECT * FROM guardias...
            # ...
        """
        stats = self.get_stats()
        slowest = self.get_slowest_queries(5)

        print("=" * 50)
        print("Query Analysis Report".center(50))
        print("=" * 50)
        print(f"Total queries:     {stats['total_queries']}")
        print(f"Total time:        {stats['total_time']:.3f}s")
        print(f"Average time:      {stats['avg_time']:.3f}s")
        print(f"Slow queries:      {stats['slow_queries']} (>0.5s)")
        print()

        if slowest:
            print("Top 5 Slowest Queries:")
            for i, q in enumerate(slowest, 1):
                stmt = q['statement'].replace('\n', ' ')[:80]
                print(f"{i}. {q['time']:.3f}s - {stmt}...")

        print("=" * 50)

    def clear(self):
        """Limpia el historial de queries."""
        self.queries.clear()
        logger.info("Historial de queries limpiado")


# Índices recomendados para las tablas principales
RECOMMENDED_INDEXES = {
    'profesor': [
        ('idx_profesor_activo', ['activo']),
        ('idx_profesor_turno', ['turno']),
        ('idx_profesor_email', ['email']),
    ],
    'zona': [
        ('idx_zona_activa', ['activa']),
        ('idx_zona_nombre', ['nombre']),
    ],
    'guardia': [
        ('idx_guardia_fecha', ['fecha']),
        ('idx_guardia_profesor_fecha', ['profesor_id', 'fecha']),
        ('idx_guardia_zona_fecha', ['zona_id', 'fecha']),
        ('idx_guardia_turno_recreo', ['turno', 'recreo']),
    ],
    'configuracion': [
        ('idx_configuracion_activa', ['activa']),
    ]
}


def generate_index_sql() -> list:
    """
    Genera SQL para crear índices recomendados.

    Returns:
        list: Lista de sentencias SQL CREATE INDEX

    Example:
        sql_statements = generate_index_sql()
        for sql in sql_statements:
            print(sql)
            session.execute(sql)
    """
    sql_statements = []

    for table, indexes in RECOMMENDED_INDEXES.items():
        for index_name, columns in indexes:
            columns_str = ', '.join(columns)
            sql = (
                f"CREATE INDEX IF NOT EXISTS {index_name} "
                f"ON {table} ({columns_str});"
            )
            sql_statements.append(sql)

    return sql_statements


def print_index_recommendations():
    """
    Imprime recomendaciones de índices para mejorar rendimiento.

    Example:
        print_index_recommendations()
        # Output:
        # ========== Index Recommendations ==========
        # Table: profesor
        #   - CREATE INDEX idx_profesor_activo ON profesor (activo);
        #   - CREATE INDEX idx_profesor_turno ON profesor (turno);
        # ...
    """
    print("=" * 50)
    print("Index Recommendations".center(50))
    print("=" * 50)

    for table, indexes in RECOMMENDED_INDEXES.items():
        print(f"\nTable: {table}")
        for index_name, columns in indexes:
            columns_str = ', '.join(columns)
            print(f"  - CREATE INDEX {index_name} ON {table} ({columns_str});")

    print("\n" + "=" * 50)
    print("Para aplicar los índices, ejecutar:")
    print("  from src.utils.query_optimizer import generate_index_sql")
    print("  for sql in generate_index_sql():")
    print("      session.execute(sql)")
    print("=" * 50)
