"""
Servicio para gestión de cursos escolares.

Este módulo proporciona la lógica de negocio para:
- Obtener el curso activo
- Crear nuevos cursos
- Activar/desactivar cursos
- Cerrar cursos
- Copiar profesores entre cursos
"""

from datetime import date, datetime, timezone
from typing import Optional

from core.logging import get_logger
from domain.entities.curso_escolar_entity import CursoEscolarEntity
from infrastructure.database.models import Profesor
from infrastructure.repositories.repository_factory import RepositoryFactory

logger = get_logger(__name__)


class GestorCursos:
    """Gestor para operaciones con cursos escolares."""

    def __init__(self, session_or_factory):
        if isinstance(session_or_factory, RepositoryFactory):
            factory = session_or_factory
        else:
            factory = RepositoryFactory(session_or_factory)
        self.session = factory.session
        self.curso_repo = factory.create_curso_escolar_repository()
        self.profesor_repo = factory.create_profesor_repository()

    @classmethod
    def from_session(cls, session) -> "GestorCursos":
        return cls(session)

    def obtener_curso_activo(self) -> Optional[CursoEscolarEntity]:
        curso = self.curso_repo.find_active()
        if curso:
            logger.info(f"Curso activo encontrado: {curso.nombre} ({curso.anio_inicio}/{curso.anio_fin})")
        else:
            logger.warning("No hay ningún curso escolar activo")
        return curso

    def crear_nuevo_curso(
        self,
        anio_inicio: int,
        anio_fin: Optional[int] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        nombre: Optional[str] = None,
        activar: bool = False,
        copiar_profesores: bool = False,
    ) -> CursoEscolarEntity:
        if anio_fin is None:
            anio_fin = anio_inicio + 1
        if fecha_inicio is None:
            fecha_inicio = date(anio_inicio, 9, 1)
        if fecha_fin is None:
            fecha_fin = date(anio_fin, 6, 30)
        if nombre is None:
            nombre = f"{anio_inicio}/{anio_fin}"

        existente = self.curso_repo.find_by_year(anio_inicio)
        if existente and existente.anio_fin == anio_fin:
            raise ValueError(
                f"Ya existe un curso {anio_inicio}/{anio_fin}. "
                f"ID: {existente.id}, Estado: {'Activo' if existente.activo else 'Inactivo'}"
            )

        nuevo_entity = CursoEscolarEntity(
            anio_inicio=anio_inicio,
            anio_fin=anio_fin,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            nombre=nombre,
            activo=False,
            cerrado=False,
            created_at=datetime.now(timezone.utc),
        )
        nuevo_entity = self.curso_repo.save(nuevo_entity)

        logger.info(f"Curso creado: {nombre} (ID: {nuevo_entity.id}, {fecha_inicio} - {fecha_fin})")

        if copiar_profesores:
            todos = self.curso_repo.get_all()
            anteriores = sorted(
                [c for c in todos if c.anio_inicio < anio_inicio],
                key=lambda c: c.anio_inicio,
                reverse=True,
            )
            if anteriores:
                self.copiar_profesores_curso_anterior(nuevo_entity.id, anteriores[0].id)
            else:
                logger.warning("No se encontró curso anterior para copiar profesores")

        if activar:
            self.activar_curso(nuevo_entity.id)

        self.session.commit()
        return nuevo_entity

    def activar_curso(self, curso_id: int) -> CursoEscolarEntity:
        entity = self.curso_repo.get_by_id(curso_id)
        if not entity:
            raise ValueError(f"No existe el curso con ID {curso_id}")
        if entity.cerrado:
            raise ValueError(
                f"No se puede activar el curso {entity.nombre} porque está cerrado. "
                "Debes reabrirlo primero."
            )
        self.curso_repo.deactivate_all()
        entity.activo = True
        result = self.curso_repo.save(entity)
        self.session.commit()
        logger.info(f"Curso activado: {entity.nombre} (ID: {curso_id})")
        return result

    def cerrar_curso(self, curso_id: int) -> CursoEscolarEntity:
        entity = self.curso_repo.get_by_id(curso_id)
        if not entity:
            raise ValueError(f"No existe el curso con ID {curso_id}")
        entity.cerrado = True
        if entity.activo:
            entity.activo = False
            logger.info(f"Curso {entity.nombre} desactivado al cerrarse")
        result = self.curso_repo.save(entity)
        self.session.commit()
        logger.info(f"Curso cerrado: {entity.nombre} (ID: {curso_id})")
        return result

    def reabrir_curso(self, curso_id: int) -> CursoEscolarEntity:
        entity = self.curso_repo.get_by_id(curso_id)
        if not entity:
            raise ValueError(f"No existe el curso con ID {curso_id}")
        entity.cerrado = False
        result = self.curso_repo.save(entity)
        self.session.commit()
        logger.info(f"Curso reabierto: {entity.nombre} (ID: {curso_id})")
        return result

    def copiar_profesores_curso_anterior(
        self,
        curso_nuevo_id: int,
        curso_anterior_id: Optional[int] = None,
    ) -> int:
        curso_nuevo = self.curso_repo.get_by_id(curso_nuevo_id)
        if not curso_nuevo:
            raise ValueError(f"No existe el curso con ID {curso_nuevo_id}")

        if curso_anterior_id is None:
            todos = self.curso_repo.get_all()
            anteriores = sorted(
                [c for c in todos if c.anio_inicio < curso_nuevo.anio_inicio],
                key=lambda c: c.anio_inicio,
                reverse=True,
            )
            curso_anterior = anteriores[0] if anteriores else None
        else:
            curso_anterior = self.curso_repo.get_by_id(curso_anterior_id)

        if not curso_anterior:
            raise ValueError("No se encontró curso anterior para copiar")

        profesores_antiguos = (
            self.session.query(Profesor)
            .filter(Profesor.curso_id == curso_anterior.id)
            .all()
        )

        contador = 0
        for prof_viejo in profesores_antiguos:
            existe = (
                self.session.query(Profesor)
                .filter_by(email_corporativo=prof_viejo.email_corporativo, curso_id=curso_nuevo_id)
                .first()
            )
            if not existe:
                nuevo_prof = Profesor(
                    nombre_completo=prof_viejo.nombre_completo,
                    email_corporativo=prof_viejo.email_corporativo,
                    horas_contrato=prof_viejo.horas_contrato,
                    porcentaje_jornada=prof_viejo.porcentaje_jornada,
                    turno=prof_viejo.turno,
                    horas_manana=prof_viejo.horas_manana,
                    horas_tarde=prof_viejo.horas_tarde,
                    tutor=prof_viejo.tutor,
                    activo=prof_viejo.activo,
                    zona_preferida_id=prof_viejo.zona_preferida_id,
                    dias_semana_permitidos=prof_viejo.dias_semana_permitidos,
                    recreos_permitidos=prof_viejo.recreos_permitidos,
                    curso_id=curso_nuevo_id,
                )
                self.session.add(nuevo_prof)
                contador += 1

        self.session.commit()
        logger.info(f"Copiados {contador} profesores de {curso_anterior.nombre} a {curso_nuevo.nombre}")
        return contador

    def listar_todos_cursos(self, incluir_cerrados: bool = True) -> list[CursoEscolarEntity]:
        todos = self.curso_repo.get_all()
        if not incluir_cerrados:
            todos = [c for c in todos if not c.cerrado]
        cursos = sorted(todos, key=lambda c: c.anio_inicio, reverse=True)
        logger.info(f"Listados {len(cursos)} cursos ({'con' if incluir_cerrados else 'sin'} cerrados)")
        return cursos

    def obtener_curso_por_anio(self, anio_inicio: int) -> Optional[CursoEscolarEntity]:
        return self.curso_repo.find_by_year(anio_inicio)


