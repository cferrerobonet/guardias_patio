"""
Servicio para gestión de cursos escolares.

Este módulo proporciona la lógica de negocio para:
- Obtener el curso activo
- Crear nuevos cursos
- Activar/desactivar cursos
- Cerrar cursos
- Copiar profesores entre cursos
"""

from datetime import date, datetime
from typing import Optional

from core.logging import get_logger
from infrastructure.repositories.repository_factory import RepositoryFactory
from models.models import CursoEscolar, Profesor
from sqlalchemy.orm import Session

logger = get_logger(__name__)


class GestorCursos:
    """Gestor para operaciones con cursos escolares."""

    def __init__(self, session: Session):
        """
        Inicializa el gestor con los repositorios necesarios.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        factory = RepositoryFactory(session)
        self.curso_repo = factory.create_curso_escolar_repository()
        self.profesor_repo = factory.create_profesor_repository()

    def obtener_curso_activo(self) -> Optional[CursoEscolar]:
        """
        Obtiene el curso escolar actualmente activo.

        Returns:
            CursoEscolar activo o None si no hay ninguno
        """
        curso = self.curso_repo.find_active()

        if curso:
            logger.info(
                f"Curso activo encontrado: {curso.nombre} ({curso.anio_inicio}/{curso.anio_fin})"
            )
        else:
            logger.warning("No hay ningún curso escolar activo")

        return curso

    @staticmethod
    def crear_nuevo_curso(
        session: Session,
        anio_inicio: int,
        anio_fin: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        nombre: Optional[str] = None,
        activar: bool = False,
        copiar_profesores: bool = False,
    ) -> CursoEscolar:
        """
        Crea un nuevo curso escolar.

        Args:
            session: Sesión de SQLAlchemy
            anio_inicio: Año de inicio del curso (ej: 2025)
            anio_fin: Año de fin del curso (por defecto: anio_inicio + 1)
            fecha_inicio: Fecha de inicio (por defecto: 1 de septiembre)
            fecha_fin: Fecha de fin (por defecto: 30 de junio siguiente)
            nombre: Nombre descriptivo (por defecto: "YYYY/YYYY")
            activar: Si True, desactiva otros cursos y activa este
            copiar_profesores: Si True, copia profesores del curso anterior

        Returns:
            CursoEscolar creado

        Raises:
            ValueError: Si ya existe un curso con esos años
        """
        # Valores por defecto
        if anio_fin is None:
            anio_fin = anio_inicio + 1
        if fecha_inicio is None:
            fecha_inicio = date(anio_inicio, 9, 1)
        if fecha_fin is None:
            fecha_fin = date(anio_fin, 6, 30)
        if nombre is None:
            nombre = f"{anio_inicio}/{anio_fin}"

        # Validar que no exista ya
        existente = (
            session.query(CursoEscolar)
            .filter_by(anio_inicio=anio_inicio, anio_fin=anio_fin)
            .first()
        )
        if existente:
            raise ValueError(
                f"Ya existe un curso {anio_inicio}/{anio_fin}. "
                f"ID: {existente.id}, Estado: "
                f"{'Activo' if existente.activo else 'Inactivo'}"
            )

        # Crear nuevo curso
        nuevo_curso = CursoEscolar(
            anio_inicio=anio_inicio,
            anio_fin=anio_fin,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            nombre=nombre,
            activo=False,  # Se activará después si es necesario
            cerrado=False,
            created_at=datetime.utcnow(),
        )

        session.add(nuevo_curso)
        session.flush()  # Para obtener el ID

        logger.info(f"Curso creado: {nombre} (ID: {nuevo_curso.id}, {fecha_inicio} - {fecha_fin})")

        # Copiar profesores del curso anterior si se solicita
        if copiar_profesores:
            curso_anterior = (
                session.query(CursoEscolar)
                .filter(CursoEscolar.anio_inicio < anio_inicio)
                .order_by(CursoEscolar.anio_inicio.desc())
                .first()
            )
            if curso_anterior:
                GestorCursos.copiar_profesores_curso_anterior(
                    session, nuevo_curso.id, curso_anterior.id
                )
            else:
                logger.warning("No se encontró curso anterior para copiar profesores")

        # Activar si se solicita
        if activar:
            GestorCursos.activar_curso(session, nuevo_curso.id)

        session.commit()
        return nuevo_curso

    @staticmethod
    def activar_curso(session: Session, curso_id: int) -> CursoEscolar:
        """
        Activa un curso y desactiva todos los demás.

        Solo puede haber un curso activo a la vez.

        Args:
            session: Sesión de SQLAlchemy
            curso_id: ID del curso a activar

        Returns:
            CursoEscolar activado

        Raises:
            ValueError: Si el curso no existe o está cerrado
        """
        curso = session.query(CursoEscolar).filter_by(id=curso_id).first()

        if not curso:
            raise ValueError(f"No existe el curso con ID {curso_id}")

        if curso.cerrado:
            raise ValueError(
                f"No se puede activar el curso {curso.nombre} porque está cerrado. "
                "Debes reabrirlo primero."
            )

        # Desactivar todos los cursos
        session.query(CursoEscolar).update({CursoEscolar.activo: False})

        # Activar el seleccionado
        curso.activo = True
        session.commit()

        logger.info(f"Curso activado: {curso.nombre} (ID: {curso_id})")
        return curso

    @staticmethod
    def cerrar_curso(session: Session, curso_id: int) -> CursoEscolar:
        """
        Marca un curso como cerrado.

        Los cursos cerrados no se pueden modificar ni activar.

        Args:
            session: Sesión de SQLAlchemy
            curso_id: ID del curso a cerrar

        Returns:
            CursoEscolar cerrado

        Raises:
            ValueError: Si el curso no existe
        """
        curso = session.query(CursoEscolar).filter_by(id=curso_id).first()

        if not curso:
            raise ValueError(f"No existe el curso con ID {curso_id}")

        curso.cerrado = True

        # Si era el activo, desactivarlo
        if curso.activo:
            curso.activo = False
            logger.info(f"Curso {curso.nombre} desactivado al cerrarse")

        session.commit()
        logger.info(f"Curso cerrado: {curso.nombre} (ID: {curso_id})")
        return curso

    @staticmethod
    def reabrir_curso(session: Session, curso_id: int) -> CursoEscolar:
        """
        Reabre un curso previamente cerrado.

        Args:
            session: Sesión de SQLAlchemy
            curso_id: ID del curso a reabrir

        Returns:
            CursoEscolar reabierto

        Raises:
            ValueError: Si el curso no existe
        """
        curso = session.query(CursoEscolar).filter_by(id=curso_id).first()

        if not curso:
            raise ValueError(f"No existe el curso con ID {curso_id}")

        curso.cerrado = False
        session.commit()

        logger.info(f"Curso reabierto: {curso.nombre} (ID: {curso_id})")
        return curso

    @staticmethod
    def copiar_profesores_curso_anterior(
        session: Session,
        curso_nuevo_id: int,
        curso_anterior_id: Optional[int] = None,
    ) -> int:
        """
        Copia los profesores de un curso anterior al nuevo curso.

        IMPORTANTE: Solo copia los datos básicos (nombre, apellidos, email).
        Las guardias NO se copian.

        Args:
            session: Sesión de SQLAlchemy
            curso_nuevo_id: ID del curso destino
            curso_anterior_id: ID del curso origen (si None, usa el más reciente)

        Returns:
            Número de profesores copiados

        Raises:
            ValueError: Si no se encuentra el curso origen o destino
        """
        # Validar curso nuevo
        curso_nuevo = session.query(CursoEscolar).filter_by(id=curso_nuevo_id).first()
        if not curso_nuevo:
            raise ValueError(f"No existe el curso con ID {curso_nuevo_id}")

        # Obtener curso anterior
        if curso_anterior_id is None:
            curso_anterior = (
                session.query(CursoEscolar)
                .filter(CursoEscolar.anio_inicio < curso_nuevo.anio_inicio)
                .order_by(CursoEscolar.anio_inicio.desc())
                .first()
            )
        else:
            curso_anterior = session.query(CursoEscolar).filter_by(id=curso_anterior_id).first()

        if not curso_anterior:
            raise ValueError("No se encontró curso anterior para copiar")

        # Obtener profesores del curso anterior
        # NOTA: Esta lógica asume que tienes una relación curso_id en Profesor
        # Si no la tienes, tendrás que ajustar esto
        profesores_antiguos = (
            session.query(Profesor)
            # TODO: Filtrar por curso_id cuando se añada a Profesor
            .all()
        )

        contador = 0
        for prof_viejo in profesores_antiguos:
            # Verificar si ya existe un profesor con ese email en el nuevo curso
            # TODO: Cuando Profesor tenga curso_id, filtrar por curso también
            existe = session.query(Profesor).filter_by(email=prof_viejo.email).first()

            if not existe:
                # Crear copia del profesor
                nuevo_prof = Profesor(
                    nombre=prof_viejo.nombre,
                    apellidos=prof_viejo.apellidos,
                    email=prof_viejo.email,
                    # TODO: curso_id=curso_nuevo_id cuando se añada
                )
                session.add(nuevo_prof)
                contador += 1

        session.commit()

        logger.info(
            f"Copiados {contador} profesores de {curso_anterior.nombre} a {curso_nuevo.nombre}"
        )

        return contador

    @staticmethod
    def listar_todos_cursos(session: Session, incluir_cerrados: bool = True) -> list[CursoEscolar]:
        """
        Lista todos los cursos escolares.

        Args:
            session: Sesión de SQLAlchemy
            incluir_cerrados: Si False, excluye cursos cerrados

        Returns:
            Lista de cursos ordenados por año de inicio (más reciente primero)
        """
        query = session.query(CursoEscolar)

        if not incluir_cerrados:
            query = query.filter_by(cerrado=False)

        cursos = query.order_by(CursoEscolar.anio_inicio.desc()).all()

        logger.info(
            f"Listados {len(cursos)} cursos ({'con' if incluir_cerrados else 'sin'} cerrados)"
        )

        return cursos

    @staticmethod
    def obtener_curso_por_anio(session: Session, anio_inicio: int) -> Optional[CursoEscolar]:
        """
        Busca un curso por su año de inicio.

        Args:
            session: Sesión de SQLAlchemy
            anio_inicio: Año de inicio (ej: 2025)

        Returns:
            CursoEscolar o None si no existe
        """
        curso = session.query(CursoEscolar).filter_by(anio_inicio=anio_inicio).first()
        return curso
