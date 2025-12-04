"""
Script para aplicar manualmente la migración del sistema Multi-Curso.

Ejecutar desde la raíz del proyecto:
python scripts/migrate_multi_curso.py
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

"""Script para aplicar la migración del sistema Multi-Curso manualmente."""

import logging
import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text

# Configurar logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def aplicar_migracion_multi_curso():
    """Aplica la migración del sistema Multi-Curso a la base de datos."""

    # Usar la ruta directa a la base de datos existente
    db_path = (
        Path(__file__).parent.parent / "data" / "users" / "0db13e2857239ed8" / "guardias_patio.db"
    )

    logger.info(f"Conectando a base de datos: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")

    with engine.begin() as conn:
        logger.info("Iniciando migración Multi-Curso...")

        try:
            # 1. Crear tabla cursos_escolares
            logger.info("1. Creando tabla cursos_escolares...")
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS cursos_escolares (
                    id INTEGER PRIMARY KEY,
                    anio_inicio INTEGER NOT NULL,
                    anio_fin INTEGER NOT NULL,
                    fecha_inicio DATE NOT NULL,
                    fecha_fin DATE NOT NULL,
                    nombre VARCHAR NOT NULL,
                    activo BOOLEAN NOT NULL DEFAULT 0,
                    cerrado BOOLEAN NOT NULL DEFAULT 0,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(anio_inicio, anio_fin)
                )
            """)
            )
            logger.info("   ✓ Tabla cursos_escolares creada")

            # 2. Añadir curso_activo_id a configuracion
            logger.info("2. Añadiendo curso_activo_id a configuracion...")
            try:
                conn.execute(
                    text("""
                    ALTER TABLE configuracion
                    ADD COLUMN curso_activo_id INTEGER
                    REFERENCES cursos_escolares(id)
                """)
                )
                logger.info("   ✓ Columna curso_activo_id añadida")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    logger.info("   ⚠ Columna curso_activo_id ya existe")
                else:
                    raise

            # 3. Añadir curso_id a guardias
            logger.info("3. Añadiendo curso_id a guardias...")
            try:
                conn.execute(
                    text("""
                    ALTER TABLE guardias
                    ADD COLUMN curso_id INTEGER
                    REFERENCES cursos_escolares(id)
                """)
                )
                logger.info("   ✓ Columna curso_id añadida a guardias")
            except Exception as e:
                if "duplicate column" in str(e).lower():
                    logger.info("   ⚠ Columna curso_id ya existe en guardias")
                else:
                    raise

            logger.info("✅ Migración Multi-Curso completada exitosamente")

        except Exception as e:
            logger.error(f"❌ Error durante la migración: {e}")
            raise

    engine.dispose()


if __name__ == "__main__":
    try:
        aplicar_migracion_multi_curso()
        print("\n✅ Migración aplicada correctamente")
        print("Ahora puedes ejecutar la aplicación normalmente")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
