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
from typing import Optional

from core.paths import get_user_data_directory
from infrastructure.database.models import Base
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


def _hash_username(username: str) -> str:
    """Genera un hash del nombre de usuario para usar como nombre de carpeta."""
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def _run_alembic_migrations(engine, db_path: Path) -> bool:
    """
    Ejecuta migraciones de Alembic para inicializar/actualizar el esquema.

    Args:
        engine: SQLAlchemy engine
        db_path: Ruta al archivo de base de datos

    Returns:
        True si Alembic completó correctamente, False en caso de fallo.
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
        if getattr(sys, "frozen", False):
            # Aplicación empaquetada
            if hasattr(sys, "_MEIPASS"):
                alembic_ini_path = Path(sys._MEIPASS) / "alembic.ini"
            else:
                alembic_ini_path = Path(sys.executable).parent / "alembic.ini"
        else:
            # Modo desarrollo
            alembic_ini_path = Path(__file__).parent.parent.parent / "alembic.ini"

        if not alembic_ini_path.exists():
            logger.warning(f"alembic.ini no encontrado en {alembic_ini_path}")
            return False

        # Configurar Alembic
        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", str(engine.url))

        if not existing_tables:
            logger.info("Base de datos nueva detectada. Inicializando esquema completo...")
            command.stamp(alembic_cfg, "head")
            logger.info("✓ Base de datos marcada con la versión actual del esquema")
        else:
            logger.info(
                f"Base de datos existente con {len(existing_tables)} tablas. "
                "Verificando migraciones..."
            )
            command.upgrade(alembic_cfg, "head")
            logger.info("✓ Migraciones de Alembic aplicadas/verificadas correctamente")

        return True

    except Exception as e:
        logger.warning(f"No se pudieron ejecutar migraciones de Alembic: {e}")
        logger.info("Usando create_all() + migraciones directas como fallback")
        return False


def _apply_direct_migrations(engine):
    """
    Aplica migraciones directas con SQL para añadir columnas faltantes.
    Esta función es un fallback cuando Alembic no funciona correctamente.
    """
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        with engine.connect() as conn:
            # ========== TABLA PROFESORES ==========
            if 'profesores' in existing_tables:
                profesores_columns = [col['name'] for col in inspector.get_columns('profesores')]

                # profesores.activo
                if 'activo' not in profesores_columns:
                    logger.info("Añadiendo columna profesores.activo...")
                    sql = "ALTER TABLE profesores ADD COLUMN activo BOOLEAN DEFAULT 1 NOT NULL"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna profesores.activo añadida")

                # profesores.zona_preferida_id
                if 'zona_preferida_id' not in profesores_columns:
                    logger.info("Añadiendo columna profesores.zona_preferida_id...")
                    sql = "ALTER TABLE profesores ADD COLUMN zona_preferida_id INTEGER"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna profesores.zona_preferida_id añadida")

                # profesores.dias_semana_permitidos
                if 'dias_semana_permitidos' not in profesores_columns:
                    logger.info("Añadiendo columna profesores.dias_semana_permitidos...")
                    sql = "ALTER TABLE profesores ADD COLUMN dias_semana_permitidos TEXT"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna profesores.dias_semana_permitidos añadida")

                # profesores.recreos_permitidos
                if 'recreos_permitidos' not in profesores_columns:
                    logger.info("Añadiendo columna profesores.recreos_permitidos...")
                    conn.execute(text("ALTER TABLE profesores ADD COLUMN recreos_permitidos TEXT"))
                    conn.commit()
                    logger.info("✓ Columna profesores.recreos_permitidos añadida")

                # profesores.curso_id
                if 'curso_id' not in profesores_columns:
                    logger.info("Añadiendo columna profesores.curso_id...")
                    conn.execute(text(
                        "ALTER TABLE profesores ADD COLUMN curso_id INTEGER REFERENCES cursos_escolares(id)"
                    ))
                    conn.commit()
                    logger.info("✓ Columna profesores.curso_id añadida")

            # ========== TABLA CONFIGURACION ==========
            if 'configuracion' in existing_tables:
                config_columns = [col['name'] for col in inspector.get_columns('configuracion')]

                # configuracion.anio_inicio_curso
                if 'anio_inicio_curso' not in config_columns:
                    logger.info("Añadiendo columna configuracion.anio_inicio_curso...")
                    sql = "ALTER TABLE configuracion ADD COLUMN anio_inicio_curso INTEGER"
                    conn.execute(text(sql))
                    # Poblar desde fecha_inicio_curso
                    conn.execute(text("""
                        UPDATE configuracion
                        SET anio_inicio_curso = CAST(strftime('%Y', fecha_inicio_curso) AS INTEGER)
                        WHERE anio_inicio_curso IS NULL AND fecha_inicio_curso IS NOT NULL
                    """))
                    conn.commit()
                    logger.info("✓ Columna configuracion.anio_inicio_curso añadida")

                # configuracion.curso_activo_id
                if 'curso_activo_id' not in config_columns:
                    logger.info("Añadiendo columna configuracion.curso_activo_id...")
                    sql = "ALTER TABLE configuracion ADD COLUMN curso_activo_id INTEGER"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna configuracion.curso_activo_id añadida")

                # configuracion.algoritmo_asignacion
                if 'algoritmo_asignacion' not in config_columns:
                    logger.info("Añadiendo columna configuracion.algoritmo_asignacion...")
                    sql = "ALTER TABLE configuracion ADD COLUMN algoritmo_asignacion VARCHAR DEFAULT 'v2.9' NOT NULL"  # noqa: E501
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna configuracion.algoritmo_asignacion añadida")

                # configuracion.recreos_config
                if 'recreos_config' not in config_columns:
                    logger.info("Añadiendo columna configuracion.recreos_config...")
                    conn.execute(text("ALTER TABLE configuracion ADD COLUMN recreos_config TEXT"))
                    conn.commit()
                    logger.info("✓ Columna configuracion.recreos_config añadida")

            # ========== TABLA CURSOS_ESCOLARES ==========
            if 'cursos_escolares' not in existing_tables:
                logger.info("Creando tabla cursos_escolares...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS cursos_escolares (
                        id INTEGER PRIMARY KEY,
                        nombre VARCHAR NOT NULL,
                        anio_inicio INTEGER NOT NULL,
                        anio_fin INTEGER NOT NULL,
                        fecha_inicio DATE NOT NULL,
                        fecha_fin DATE NOT NULL,
                        activo BOOLEAN DEFAULT 0 NOT NULL,
                        cerrado BOOLEAN DEFAULT 0 NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        UNIQUE(anio_inicio, anio_fin)
                    )
                """))
                conn.commit()
                logger.info("✓ Tabla cursos_escolares creada")
            else:
                # Verificar columna cerrado en cursos_escolares
                cursos_columns = [col['name'] for col in inspector.get_columns('cursos_escolares')]
                if 'cerrado' not in cursos_columns:
                    logger.info("Añadiendo columna cursos_escolares.cerrado...")
                    sql = "ALTER TABLE cursos_escolares ADD COLUMN cerrado BOOLEAN DEFAULT 0 NOT NULL"  # noqa: E501
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna cursos_escolares.cerrado añadida")

            # ========== TABLA GUARDIAS ==========
            if 'guardias' in existing_tables:
                guardias_columns = [col['name'] for col in inspector.get_columns('guardias')]

                # guardias.curso_id
                if 'curso_id' not in guardias_columns:
                    logger.info("Añadiendo columna guardias.curso_id...")
                    sql = "ALTER TABLE guardias ADD COLUMN curso_id INTEGER"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info("✓ Columna guardias.curso_id añadida")

            # ========== TABLA AUSENCIAS ==========
            if 'ausencias' not in existing_tables:
                logger.info("Creando tabla ausencias...")
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS ausencias (
                        id INTEGER PRIMARY KEY,
                        profesor_id INTEGER NOT NULL REFERENCES profesores(id),
                        fecha_inicio DATE NOT NULL,
                        fecha_fin DATE NOT NULL,
                        tipo VARCHAR NOT NULL,
                        motivo TEXT,
                        documento_path VARCHAR,
                        activa BOOLEAN DEFAULT 1 NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                logger.info("✓ Tabla ausencias creada")

            logger.info("✓ Migraciones directas completadas")

    except Exception as e:
        logger.error(f"Error aplicando migraciones directas: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # No lanzar excepción, continuar con el flujo normal


def initialize_user_database(username: str):
    """
    Inicializa la base de datos para un usuario específico.

    Args:
        username: Nombre de usuario (ej: 'Jefatura_FpBach')

    Returns:
        tuple: (engine, SessionLocal) para el usuario
    """
    global _current_user_id, _current_engine, _current_session_factory

    # Crear hash del nombre de usuario
    user_hash = _hash_username(username)

    # Crear directorio del usuario
    user_dir = USER_DATA_DIR / user_hash
    user_dir.mkdir(parents=True, exist_ok=True)

    # Path de la base de datos del usuario
    db_path = user_dir / "guardias_patio.db"
    database_url = f"sqlite:///{db_path}"

    logger.info(f"Inicializando BD para usuario: {username} (hash: {user_hash})")
    logger.info(f"Database path: {db_path}")

    # Crear engine específico para este usuario
    engine = create_engine(
        database_url,
        echo=False,
        future=True,
        poolclass=pool.NullPool,
        connect_args={
            "check_same_thread": False,
            "timeout": TIMEOUT_DB,
        },
    )

    # Pragmas de optimización para SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configura pragmas de optimización para SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # Usar DELETE mode en lugar de WAL para evitar problemas con OneDrive
        # WAL crea archivos -wal y -shm que OneDrive puede bloquear
        cursor.execute("PRAGMA journal_mode=DELETE")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=10000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()

    # Ejecutar Alembic como estrategia primaria de init/migración
    alembic_ok = _run_alembic_migrations(engine, db_path)

    if not alembic_ok:
        # Fallback: create_all + migraciones SQL directas para columnas faltantes
        logger.info("Alembic no disponible — usando fallback create_all + direct migrations")
        from infrastructure.database.models import Base

        Base.metadata.create_all(bind=engine)
        _apply_direct_migrations(engine)
    else:
        # Alembic fue exitoso; create_all es idempotente y solo añade tablas nuevas si las hubiera
        from infrastructure.database.models import Base

        Base.metadata.create_all(bind=engine)

    # Session factory para este usuario
    session_factory = sessionmaker(
        autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
    )

    # Guardar referencias globales
    _current_user_id = username
    _current_engine = engine
    _current_session_factory = session_factory

    logger.info(f"Base de datos inicializada para usuario: {username}")

    return engine, session_factory


def get_current_user_id() -> str:
    """Obtiene el ID del usuario activo."""
    return _current_user_id


def get_user_database_path(username: str) -> Path:
    """Obtiene el path de la base de datos de un usuario."""
    user_hash = _hash_username(username)
    return USER_DATA_DIR / user_hash / "guardias_patio.db"


def create_user_database(username: str) -> bool:
    """
    Crea una nueva base de datos para un usuario con la estructura completa.

    Args:
        username: Nombre de usuario

    Returns:
        bool: True si se creó correctamente
    """
    try:
        db_path = get_user_database_path(username)

        # Crear directorio si no existe
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Crear base de datos con todas las tablas
        engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(engine)

        # Marcar como head en Alembic para que migraciones futuras funcionen correctamente
        try:
            from alembic import command as alembic_command
            from alembic.config import Config as AlembicConfig

            alembic_ini = Path(__file__).parent.parent.parent / "alembic.ini"
            if alembic_ini.exists():
                cfg = AlembicConfig(str(alembic_ini))
                cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")
                alembic_command.stamp(cfg, "head")
                logger.info(f"Alembic stamp head aplicado a BD de usuario: {username}")
        except Exception as stamp_err:
            logger.warning(f"No se pudo aplicar alembic stamp: {stamp_err}")

        logger.info(f"Base de datos creada para usuario: {username}")
        return True

    except Exception as e:
        logger.error(f"Error creando base de datos para usuario {username}: {e}")
        return False


def user_has_database(username: str) -> bool:
    """Verifica si un usuario tiene una base de datos creada."""
    db_path = get_user_database_path(username)
    return db_path.exists()


def delete_user_database(username: str) -> bool:
    """
    Elimina completamente la base de datos y archivos de un usuario.

    Args:
        username: Nombre de usuario

    Returns:
        bool: True si se eliminó correctamente
    """
    try:
        user_hash = _hash_username(username)
        user_dir = USER_DATA_DIR / user_hash

        if user_dir.exists():
            import shutil

            shutil.rmtree(user_dir)
            logger.info(f"Base de datos eliminada para usuario: {username}")
            return True
        else:
            logger.warning(f"No existe base de datos para usuario: {username}")
            return False
    except Exception as e:
        logger.error(f"Error eliminando base de datos de usuario {username}: {e}")
        return False


def backup_database(username: str, backup_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Crea una copia de seguridad de la base de datos de un usuario.

    Args:
        username: Nombre de usuario
        backup_dir: Directorio destino del backup. Si None, usa data/backups/

    Returns:
        Path al archivo de backup creado, o None si falla
    """
    import shutil
    from datetime import datetime

    try:
        db_path = get_user_database_path(username)
        if not db_path.exists():
            logger.error(f"No existe BD para usuario: {username}")
            return None

        if backup_dir is None:
            user_hash = _hash_username(username)
            backup_dir = USER_DATA_DIR / user_hash / "backups"

        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"guardias_patio_backup_{timestamp}.db"
        backup_path = backup_dir / backup_filename

        shutil.copy2(db_path, backup_path)
        os.chmod(backup_path, 0o600)

        logger.info(f"Backup creado: {backup_path}")
        return backup_path

    except Exception as e:
        logger.error(f"Error creando backup de usuario {username}: {e}")
        return None


def restore_database(username: str, backup_path: str | Path) -> bool:
    """
    Restaura la base de datos de un usuario desde un backup.
    Crea un backup automático de la BD actual antes de restaurar.

    Args:
        username: Nombre de usuario
        backup_path: Ruta al archivo de backup (.db)

    Returns:
        bool: True si se restauró correctamente
    """
    import shutil
    import sqlite3

    backup_path = Path(backup_path)

    if not backup_path.exists():
        logger.error(f"Archivo de backup no encontrado: {backup_path}")
        return False

    # Validar que sea un SQLite válido
    try:
        conn = sqlite3.connect(str(backup_path))
        conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        conn.close()
    except sqlite3.DatabaseError as e:
        logger.error(f"El archivo de backup no es una BD SQLite válida: {e}")
        return False

    try:
        db_path = get_user_database_path(username)

        # Auto-backup de la BD actual antes de restaurar
        if db_path.exists():
            safety_backup = backup_database(username)
            if safety_backup:
                logger.info(f"Backup de seguridad creado antes de restaurar: {safety_backup}")

        db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, db_path)
        os.chmod(db_path, 0o600)

        logger.info(f"BD restaurada para usuario {username} desde: {backup_path}")
        return True

    except Exception as e:
        logger.error(f"Error restaurando BD de usuario {username}: {e}")
        return False


# URL de la base de datos (fallback para compatibilidad con scripts legacy)
# NOTA: En producción siempre se debe usar initialize_user_database(user_id)
# Este fallback usa ruta absoluta para evitar crear BD en directorios incorrectos
from core.paths import get_database_path  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{get_database_path()}")

# Detectar tipo de base de datos
IS_SQLITE = DATABASE_URL.startswith("sqlite")
IS_POSTGRESQL = DATABASE_URL.startswith("postgresql")

# Engine y SessionLocal por defecto (se sobrescribirán al iniciar sesión)
if IS_SQLITE:
    engine = create_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=pool.NullPool,
        connect_args={
            "check_same_thread": False,
            "timeout": TIMEOUT_DB,
        },
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        """Configura pragmas de optimización para SQLite."""
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        # Usar DELETE mode en lugar de WAL para evitar problemas con OneDrive
        cursor.execute("PRAGMA journal_mode=DELETE")
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

    logger.info("Engine PostgreSQL creado: pool_size=10, max_overflow=20, timeout=30s")

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

# Session factory base (fallback para cuando no hay usuario activo)
_base_session_factory = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


class _SmartSessionLocal:
    """
    Wrapper inteligente que devuelve la sesión del usuario activo
    o la sesión fallback si no hay usuario.

    Esto permite que código legacy que usa SessionLocal() directamente
    funcione correctamente con el sistema multi-usuario.
    """

    def __call__(self):
        """Crea una sesión usando el factory correcto."""
        if _current_session_factory is not None:
            return _current_session_factory()
        else:
            logger.warning(
                "SessionLocal() llamado sin usuario activo. "
                "Usando BD legacy en data/guardias_patio.db. "
                "Considerar usar initialize_user_database(username) primero."
            )
            return _base_session_factory()


# SessionLocal inteligente que usa la BD del usuario activo
SessionLocal = _SmartSessionLocal()

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
    session_factory = (
        _current_session_factory if _current_session_factory else _base_session_factory
    )

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
    session_factory = (
        _current_session_factory if _current_session_factory else _base_session_factory
    )

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
        return {"type": "NullPool", "note": "SQLite no usa connection pool"}

    return {
        "type": engine.pool.__class__.__name__,
        "size": engine.pool.size(),
        "checked_out": engine.pool.checkedout(),
        "overflow": engine.pool.overflow(),
        "total": engine.pool.size() + engine.pool.overflow(),
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

    if "note" in status:
        print(f"Type: {status['type']}")
        print(f"Note: {status['note']}")
    else:
        print(f"Type:           {status['type']}")
        print(f"Size:           {status['size']}")
        print(f"Checked out:    {status['checked_out']}")
        print(f"Overflow:       {status['overflow']}")
        print(f"Total:          {status['total']}")

    print("=" * 45)
