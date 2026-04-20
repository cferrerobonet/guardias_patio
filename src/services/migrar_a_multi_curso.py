"""
Script de migración para el sistema Multi-Curso.

Este script detecta guardias sin curso_id asignado y las migra automáticamente
al curso escolar correspondiente según su fecha.

Se ejecuta automáticamente al iniciar la aplicación si detecta datos huérfanos.
"""

from datetime import date
from typing import Optional

from core.logging import get_logger
from infrastructure.database.models import CursoEscolar, Guardia
from services.gestor_cursos import GestorCursos
from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = get_logger(__name__)


class MigradorMultiCurso:
    """Gestor de migración de datos al sistema Multi-Curso."""

    @staticmethod
    def necesita_migracion(session: Session) -> bool:
        """
        Verifica si hay guardias sin curso_id asignado.

        Args:
            session: Sesión de SQLAlchemy

        Returns:
            True si hay guardias huérfanas que necesitan migración
        """
        count = session.query(Guardia).filter(Guardia.curso_id.is_(None)).count()

        if count > 0:
            logger.warning(f"Detectadas {count} guardias sin curso asignado")
            return True

        logger.info("No hay guardias pendientes de migración")
        return False

    @staticmethod
    def detectar_anio_curso_desde_guardias(session: Session) -> Optional[int]:
        """
        Detecta el año de inicio del curso escolar basándose en las fechas
        de las guardias existentes.

        Lógica:
        - Si hay guardias entre Sep-Dic → año de inicio es ese año
        - Si hay guardias entre Ene-Ago → año de inicio es año anterior

        Args:
            session: Sesión de SQLAlchemy

        Returns:
            Año de inicio detectado o None si no hay guardias
        """
        # Obtener la fecha más temprana y más tardía
        stats = (
            session.query(
                func.min(Guardia.fecha).label("primera"),
                func.max(Guardia.fecha).label("ultima"),
            )
            .filter(Guardia.curso_id.is_(None))
            .first()
        )

        if not stats or not stats.primera:
            logger.warning("No hay guardias para detectar año del curso")
            return None

        primera_fecha: date = stats.primera
        ultima_fecha: date = stats.ultima

        logger.info(f"Rango de guardias detectado: {primera_fecha} - {ultima_fecha}")

        # Determinar año de inicio basándose en la distribución de fechas
        # Si la mayoría están en Sep-Dic, el curso empieza ese año
        # Si la mayoría están en Ene-Ago, el curso empezó el año anterior

        guardias_septiembre_diciembre = (
            session.query(func.count(Guardia.id))
            .filter(
                Guardia.curso_id.is_(None),
                func.extract("month", Guardia.fecha) >= 9,
            )
            .scalar()
        )

        guardias_enero_agosto = (
            session.query(func.count(Guardia.id))
            .filter(
                Guardia.curso_id.is_(None),
                func.extract("month", Guardia.fecha) <= 8,
            )
            .scalar()
        )

        logger.info(
            f"Distribución: Sep-Dic: {guardias_septiembre_diciembre}, "
            f"Ene-Ago: {guardias_enero_agosto}"
        )

        # Si hay más guardias en la segunda mitad del año, el curso empieza ese año
        if guardias_septiembre_diciembre > guardias_enero_agosto:
            anio_inicio = primera_fecha.year
        else:
            # Si hay más en la primera mitad, el curso empezó el año anterior
            anio_inicio = primera_fecha.year - 1

        logger.info(f"Año de inicio detectado: {anio_inicio}")
        return anio_inicio

    @staticmethod
    def crear_curso_desde_guardias(
        session: Session,
        anio_inicio: Optional[int] = None,
    ) -> CursoEscolar:
        """
        Crea un curso escolar basándose en las guardias existentes.

        Args:
            session: Sesión de SQLAlchemy
            anio_inicio: Año de inicio del curso (si None, se detecta automáticamente)

        Returns:
            CursoEscolar creado

        Raises:
            ValueError: Si no se puede determinar el año o ya existe el curso
        """
        # Detectar año si no se proporciona
        if anio_inicio is None:
            anio_inicio = MigradorMultiCurso.detectar_anio_curso_desde_guardias(session)
            if anio_inicio is None:
                raise ValueError(
                    "No se pudo determinar el año del curso. "
                    "No hay guardias o especifica el año manualmente."
                )

        # Verificar si ya existe
        curso_existente = GestorCursos.from_session(session).obtener_curso_por_anio(anio_inicio)
        if curso_existente:
            logger.info(f"Ya existe el curso {anio_inicio}/{anio_inicio + 1}. Usando el existente.")
            return curso_existente

        # Crear nuevo curso
        logger.info(f"Creando curso {anio_inicio}/{anio_inicio + 1}...")
        curso = GestorCursos.from_session(session).crear_nuevo_curso(
            anio_inicio=anio_inicio,
            activar=True,
            copiar_profesores=False,
        )

        logger.info(f"Curso creado y activado: {curso.nombre} (ID: {curso.id})")
        return curso

    @staticmethod
    def asignar_guardias_a_curso(
        session: Session,
        curso_id: int,
        anio_inicio: Optional[int] = None,
    ) -> int:
        """
        Asigna las guardias huérfanas al curso especificado.

        Args:
            session: Sesión de SQLAlchemy
            curso_id: ID del curso al que asignar las guardias
            anio_inicio: Si se proporciona, solo asigna guardias de ese año escolar

        Returns:
            Número de guardias actualizadas
        """
        query = session.query(Guardia).filter(Guardia.curso_id.is_(None))

        # Filtrar por año si se especifica
        if anio_inicio is not None:
            # Guardias entre Sep del año_inicio y Ago del año_fin
            fecha_inicio = date(anio_inicio, 9, 1)
            fecha_fin = date(anio_inicio + 1, 8, 31)
            query = query.filter(
                Guardia.fecha >= fecha_inicio,
                Guardia.fecha <= fecha_fin,
            )

        # Contar antes de actualizar
        total = query.count()

        # Actualizar todas las guardias
        query.update({Guardia.curso_id: curso_id})
        session.commit()

        logger.info(f"Asignadas {total} guardias al curso ID {curso_id}")
        return total

    @staticmethod
    def migrar_automaticamente(session: Session) -> dict:
        """
        Ejecuta la migración completa automáticamente.

        Detecta guardias huérfanas, crea el curso correspondiente y asigna.

        Args:
            session: Sesión de SQLAlchemy

        Returns:
            Diccionario con resultado de la migración:
            {
                'necesitaba_migracion': bool,
                'curso_creado': bool,
                'curso_id': int,
                'curso_nombre': str,
                'guardias_migradas': int
            }
        """
        resultado = {
            "necesitaba_migracion": False,
            "curso_creado": False,
            "curso_id": None,
            "curso_nombre": None,
            "guardias_migradas": 0,
        }

        # Verificar si necesita migración
        if not MigradorMultiCurso.necesita_migracion(session):
            logger.info("✅ Sistema Multi-Curso: No requiere migración")
            return resultado

        resultado["necesitaba_migracion"] = True
        logger.info("🔄 Iniciando migración automática al sistema Multi-Curso...")

        try:
            # Detectar año del curso
            anio_inicio = MigradorMultiCurso.detectar_anio_curso_desde_guardias(session)
            if anio_inicio is None:
                logger.error("No se pudo detectar el año del curso desde las guardias")
                return resultado

            # Crear o obtener curso
            curso_existente = GestorCursos.from_session(session).obtener_curso_por_anio(anio_inicio)
            if curso_existente:
                curso = curso_existente
                resultado["curso_creado"] = False
                logger.info(f"Usando curso existente: {curso.nombre}")
            else:
                curso = MigradorMultiCurso.crear_curso_desde_guardias(session, anio_inicio)
                resultado["curso_creado"] = True
                logger.info(f"Curso nuevo creado: {curso.nombre}")

            resultado["curso_id"] = curso.id
            resultado["curso_nombre"] = curso.nombre

            # Asignar guardias al curso
            guardias_migradas = MigradorMultiCurso.asignar_guardias_a_curso(
                session, curso.id, anio_inicio
            )
            resultado["guardias_migradas"] = guardias_migradas

            logger.info(
                f"✅ Migración completada: {guardias_migradas} guardias "
                f"asignadas al curso {curso.nombre}"
            )

        except (ValueError, TypeError, OSError) as e:
            logger.error(f"❌ Error durante la migración: {e}")
            session.rollback()
            raise

        return resultado

    @staticmethod
    def migrar_interactivo(
        session: Session,
        anio_inicio: int,
        crear_si_no_existe: bool = True,
    ) -> dict:
        """
        Ejecuta migración con parámetros específicos del usuario.

        Args:
            session: Sesión de SQLAlchemy
            anio_inicio: Año de inicio del curso escolar
            crear_si_no_existe: Si True, crea el curso si no existe

        Returns:
            Diccionario con resultado de la migración
        """
        resultado = {
            "curso_creado": False,
            "curso_id": None,
            "curso_nombre": None,
            "guardias_migradas": 0,
        }

        # Obtener o crear curso
        curso = GestorCursos.from_session(session).obtener_curso_por_anio(anio_inicio)

        if not curso and crear_si_no_existe:
            curso = GestorCursos.from_session(session).crear_nuevo_curso(
                anio_inicio=anio_inicio,
                activar=True,
                copiar_profesores=False,
            )
            resultado["curso_creado"] = True
        elif not curso:
            raise ValueError(
                f"No existe el curso {anio_inicio}/{anio_inicio + 1} "
                "y no se permite crear automáticamente"
            )

        resultado["curso_id"] = curso.id
        resultado["curso_nombre"] = curso.nombre

        # Asignar guardias
        guardias_migradas = MigradorMultiCurso.asignar_guardias_a_curso(
            session, curso.id, anio_inicio
        )
        resultado["guardias_migradas"] = guardias_migradas

        logger.info(
            f"✅ Migración manual completada: {guardias_migradas} guardias al curso {curso.nombre}"
        )

        return resultado


def ejecutar_migracion_si_necesario(session: Session) -> bool:
    """
    Función helper para ejecutar desde app_initializer.

    Args:
        session: Sesión de SQLAlchemy

    Returns:
        True si se ejecutó migración, False si no fue necesario
    """
    if MigradorMultiCurso.necesita_migracion(session):
        resultado = MigradorMultiCurso.migrar_automaticamente(session)
        return resultado["guardias_migradas"] > 0
    return False
