"""
Gestión de conexión a la base de datos con optimizaciones de rendimiento.

Características:
- Connection pooling para reutilización de conexiones
- Configuración optimizada para SQLite y PostgreSQL
- Control de timeout y reintentos
- Logging de conexiones
- Soporte multi-usuario con bases de datos aisladas
"""

import hashlib
import os
from contextlib import contextmanager
from pathlib import Path

from core.paths import get_user_data_directory
from sqlalchemy import create_engine, event, pool
from sqlalchemy.orm import sessionmaker
from utils.constants import TIMEOUT_DB
from utils.logger import get_logger

logger = get_logger(__name__)

# Directorio base para bases de datos de usuarios
USER_DATA_DIR = get_user_data_directory()

# Variable global para el usuario activo
_current_user_id = None
_current_engine = None
_current_session_factory = None


def _hash_user_id(user_id: str) -> str:
    """Genera un hash del user_id para usar como nombre de carpeta."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def _run_alembic_migrations(engine, db_path: Path):
    """
    Ejecuta migraciones de Alembic para inicializar/actualizar el esquema.

    Args:
        engine: SQLAlchemy engine
        db_path: Ruta al archivo de base de datos
    """
    try:
        from sqlalchemy import inspect

        from alembic import command
        from alembic.config import Config

        # Verificar si la base de datos ya tiene tablas
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # Configurar Alembic
        import sys
        from pathlib import Path

        # Obtener ruta al alembic.ini
        if getattr(sys, 'frozen', False):
            # Aplicación empaquetada
            if hasattr(sys, '_MEIPASS'):
                alembic_ini_path = Path(sys._MEIPASS) / 'alembic.ini'
            else:
                alembic_ini_path = Path(sys.executable).parent / 'alembic.ini'
        else:
            # Modo desarrollo
            alembic_ini_path = Path(__file__).parent.parent.parent / 'alembic.ini'

        if not alembic_ini_path.exists():
            logger.warning(f"alembic.ini no encontrado en {alembic_ini_path}")
            logger.info("Usando create_all() para inicializar esquema")
            return

        # Configurar Alembic
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option('sqlalchemy.url', str(engine.url))

        if not existing_tables:
            logger.info("Base de datos nueva detectada. Inicializando esquema completo...")
            # Marcar la base de datos en la versión head sin ejecutar migraciones
            # ya que vamos a crear todo desde cero con create_all()
            command.stamp(alembic_cfg, 'head')
            logger.info("✓ Base de datos marcada con la versión actual del esquema")
        else:
            logger.info(
                f"Base de datos existente con {len(existing_tables)} tablas. "
                "Verificando migraciones..."
            )
            # Intentar aplicar migraciones pendientes
            command.upgrade(alembic_cfg, 'head')
            logger.info("✓ Migraciones de Alembic aplicadas/verificadas correctamente")

    except Exception as e:
        logger.warning(f"No se pudieron ejecutar migraciones de Alembic: {e}")
        logger.info("La aplicación continuará usando create_all() para el esquema")



def initialize_user_database(user_id: str):
    """
    Inicializa la base de datos para un usuario específico.

    Args:
        user_id: Identificador único del usuario

    Returns:
        tuple: (engine, SessionLocal) para el usuario
    """
    global _current_user_id, _current_engine, _current_session_factory

    # Crear hash del usuario
    user_hash = _hash_user_id(user_id)

    # Crear directorio del usuario
    user_dir = USER_DATA_DIR / user_hash
    user_dir.mkdir(parents=True, exist_ok=True)

    # Path de la base de datos del usuario
    db_path = user_dir / "guardias_patio.db"
    database_url = f"sqlite:///{db_path}"

    logger.info(f"Inicializando BD para usuario: {user_id} (hash: {user_hash})")
    logger.info(f"Database path: {db_path}")

    # Crear engine específico para este usuario
    engine = create_engine(
        database_url,
        echo=False,
        future=True,
        poolclass=pool.NullPool,
        connect_args={
            'check_same_thread': False,
            'timeout': TIMEOUT_DB,
        }
    )

    # Pragmas de optimización para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configura pragmas de optimización para SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

    # Primero ejecutar migraciones de Alembic (esto manejará la creación/actualización del esquema)
    _run_alembic_migrations(engine, db_path)

    # Como fallback, crear tablas con SQLAlchemy si Alembic falló
    from models.models import Base
    Base.metadata.create_all(bind=engine)

    # Session factory para este usuario
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )

    # Guardar referencias globales
    _current_user_id = user_id
    _current_engine = engine
    _current_session_factory = session_factory

    logger.info(f"Base de datos inicializada para usuario: {user_id}")

    return engine, session_factory


def get_current_user_id() -> str:
    """Obtiene el ID del usuario activo."""
    return _current_user_id


def get_user_database_path(user_id: str) -> Path:
    """Obtiene el path de la base de datos de un usuario."""
    user_hash = _hash_user_id(user_id)
    return USER_DATA_DIR / user_hash / "guardias_patio.db"


def user_has_database(user_id: str) -> bool:
    """Verifica si un usuario tiene una base de datos creada."""
    db_path = get_user_database_path(user_id)
    return db_path.exists()


def delete_user_database(user_id: str) -> bool:
    """
    Elimina completamente la base de datos y archivos de un usuario.

    Args:
        user_id: Identificador del usuario

    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        user_hash = _hash_user_id(user_id)
        user_dir = USER_DATA_DIR / user_hash

        if user_dir.exists():
            import shutil
            shutil.rmtree(user_dir)
            logger.info(f"Base de datos eliminada para usuario: {user_id}")
            return True
        else:
            logger.warning(f"No existe base de datos para usuario: {user_id}")
            return False
    except Exception as e:
        logger.error(f"Error eliminando base de datos de usuario {user_id}: {e}")
        return False


# URL de la base de datos (fallback para compatibilidad)
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///guardias_patio.db')

# Detectar tipo de base de datos
IS_SQLITE = DATABASE_URL.startswith('sqlite')
IS_POSTGRESQL = DATABASE_URL.startswith('postgresql')

# Engine y SessionLocal por defecto (se sobrescribirán al iniciar sesión)
if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=pool.NullPool,
        connect_args={
            'check_same_thread': False,
            'timeout': TIMEOUT_DB,
        }
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configura pragmas de optimización para SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()
        logger.debug("SQLite pragmas configurados")

elif IS_POSTGRESQL:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=pool.QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_timeout=30,
        pool_recycle=3600,
        pool_pre_ping=True,
    )

    logger.info(
        "Engine PostgreSQL creado: "
        "pool_size=10, max_overflow=20, timeout=30s"
    )

else:
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
    expire_on_commit=False
)

logger.info(f"Database manager inicializado: {DATABASE_URL[:50]}")


def get_session():
    """
    Generador de sesión de base de datos.
    Usa la base de datos del usuario activo si está configurada.

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
    # Usar session factory del usuario activo si existe
    session_factory = _current_session_factory if _current_session_factory else SessionLocal

    db = session_factory()
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
    Usa la base de datos del usuario activo si está configurada.

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
    # Usar session factory del usuario activo si existe
    session_factory = _current_session_factory if _current_session_factory else SessionLocal

    session = session_factory()
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
