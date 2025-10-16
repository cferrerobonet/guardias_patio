"""
Gestión de conexión a la base de datos con optimizaciones de rendimiento.

Características:
- Connection pooling para reutilización de conexiones
- Configuración optimizada para SQLite y PostgreSQL
- Control de timeout y reintentos
- Logging de conexiones
"""

import os
from contextlib import contextmanager

from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from utils.constants import TIMEOUT_DB
from utils.logger import get_logger

logger = get_logger(__name__)

# URL de la base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///guardias_patio.db')

# Detectar tipo de base de datos
IS_SQLITE = DATABASE_URL.startswith('sqlite')
IS_POSTGRESQL = DATABASE_URL.startswith('postgresql')

# Configuración del engine según el tipo de BD
if IS_SQLITE:
    # SQLite: NullPool (no usa pool) + optimizaciones para SQLite
    engine = create_engine(
        DATABASE_URL,
        echo=False,  # Cambiar a True solo para debug
        future=True,
        poolclass=pool.NullPool,  # SQLite no soporta pool bien
        connect_args={
            'check_same_thread': False,  # Permite uso desde múltiples threads
            'timeout': TIMEOUT_DB,  # Timeout de 30 segundos
        }
    )

    # Pragmas de optimización para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configura pragmas de optimización para SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")  # Activar FK
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        cursor.execute("PRAGMA synchronous=NORMAL")  # Balance rendimiento/seguridad
        cursor.execute("PRAGMA cache_size=10000")  # 10000 páginas (~40MB)
        cursor.execute("PRAGMA temp_store=MEMORY")  # Tablas temp en RAM
        cursor.close()
        logger.debug("SQLite pragmas configurados")

elif IS_POSTGRESQL:
    # PostgreSQL: QueuePool con configuración robusta
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=pool.QueuePool,
        pool_size=10,  # Conexiones permanentes
        max_overflow=20,  # Conexiones adicionales bajo carga
        pool_timeout=30,  # Timeout para obtener conexión del pool
        pool_recycle=3600,  # Reciclar conexiones cada hora
        pool_pre_ping=True,  # Verificar conexión antes de usar
    )

    logger.info(
        "Engine PostgreSQL creado: "
        "pool_size=10, max_overflow=20, timeout=30s"
    )

else:
    # Otras BD: configuración genérica
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=pool.QueuePool,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
    )

    logger.warning(f"Base de datos no reconocida: {DATABASE_URL[:20]}...")

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False  # No refrescar objetos tras commit (mejor rendimiento)
)

logger.info(f"Database manager inicializado: {DATABASE_URL[:50]}")


def get_session():
    """
    Generador de sesión de base de datos.

    Uso en FastAPI/generadores:
        for session in get_session():
            # usar session
            pass

    Yields:
        Session: Sesión de SQLAlchemy

    Example:
        for db in get_session():
            profesores = db.query(Profesor).all()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Error en sesión de BD: {e}", exc_info=True)
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager para sesiones de base de datos.

    Uso recomendado para scripts y servicios:
        with get_db_session() as session:
            profesores = session.query(Profesor).all()

    Yields:
        Session: Sesión de SQLAlchemy

    Example:
        with get_db_session() as db:
            profesor = Profesor(nombre="García, Juan")
            db.add(profesor)
            db.commit()
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Error en sesión de BD: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


def get_pool_status():
    """
    Obtiene estadísticas del connection pool.

    Returns:
        dict: Estadísticas del pool (size, checked_out, overflow, etc.)

    Example:
        status = get_pool_status()
        print(f"Conexiones activas: {status['checked_out']}")
    """
    if IS_SQLITE:
        return {
            'type': 'NullPool',
            'note': 'SQLite no usa connection pool'
        }

    return {
        'type': engine.pool.__class__.__name__,
        'size': engine.pool.size(),
        'checked_out': engine.pool.checkedout(),
        'overflow': engine.pool.overflow(),
        'total': engine.pool.size() + engine.pool.overflow(),
    }


def print_pool_status():
    """
    Imprime estadísticas del connection pool.

    Útil para debugging y análisis de rendimiento.

    Example:
        print_pool_status()
        # Output:
        # ========== Connection Pool Status ==========
        # Type:           QueuePool
        # Size:           10
        # Checked out:    3
        # Overflow:       2
        # Total:          12
        # ===========================================
    """
    status = get_pool_status()

    print("=" * 45)
    print("Connection Pool Status".center(45))
    print("=" * 45)

    if 'note' in status:
        print(f"Type: {status['type']}")
        print(f"Note: {status['note']}")
    else:
        print(f"Type:           {status['type']}")
        print(f"Size:           {status['size']}")
        print(f"Checked out:    {status['checked_out']}")
        print(f"Overflow:       {status['overflow']}")
        print(f"Total:          {status['total']}")

    print("=" * 45)
