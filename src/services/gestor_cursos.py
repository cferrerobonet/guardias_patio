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
from infrastructure.database.models import Configuracion, Profesor
from infrastructure.repositories.repository_factory import RepositoryFactory

logger = get_logger(__name__)


def _vaciar_las_caches(motivo: str) -> None:
    """Tira lo cacheado al cambiar de curso (ESC-005).

    Se hace aquí y no sólo en la ventana porque a `activar_curso` se llega desde
    tres sitios —el selector, la gestión de cursos y la creación— y sólo uno de
    ellos avisaba a la interfaz. Un resultado cacheado del curso anterior es un
    dato equivocado, no un dato viejo.
    """
    try:
        from utils.cache import clear_all_cache

        clear_all_cache()
    except Exception as e:  # noqa: BLE001
        logger.warning(f"No se pudo vaciar la caché al {motivo}: {e}")


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
        trasladar_no_lectivos: bool = False,
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

        if copiar_profesores or trasladar_no_lectivos:
            resumen = self.preparar_curso_nuevo(
                nuevo_entity.id,
                copiar_profesores=copiar_profesores,
                trasladar_no_lectivos=trasladar_no_lectivos,
            )
            if not resumen["hubo_anterior"]:
                logger.warning("No se encontró curso anterior del que partir")

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
        self._sincronizar_configuracion_con(entity)
        self.session.commit()
        _vaciar_las_caches("activar curso")
        logger.info(f"Curso activado: {entity.nombre} (ID: {curso_id})")
        return result

    def _sincronizar_configuracion_con(self, curso) -> None:
        """Apunta la configuración global al curso indicado y copia su rango de fechas.

        Sin esto, al cambiar de curso la generación seguiría usando las fechas del
        anterior y ``curso_activo_id`` nunca llegaría a apuntar a ningún curso.
        """
        config = self.session.query(Configuracion).first()
        if config is None:
            return
        config.curso_activo_id = curso.id
        config.anio_inicio_curso = curso.anio_inicio
        config.fecha_inicio_curso = curso.fecha_inicio
        config.fecha_fin_curso = curso.fecha_fin
        logger.info(
            f"Configuración sincronizada con {curso.nombre}: "
            f"{curso.fecha_inicio} - {curso.fecha_fin}"
        )

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
            # Sin correo, filtrar por él agruparía a todos los que no lo tienen en uno
            # solo y sólo se copiaría el primero: el nombre es el segundo criterio.
            criterio = {"curso_id": curso_nuevo_id}
            if prof_viejo.email_corporativo:
                criterio["email_corporativo"] = prof_viejo.email_corporativo
            else:
                criterio["nombre_completo"] = prof_viejo.nombre_completo
            existe = self.session.query(Profesor).filter_by(**criterio).first()
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

    def trasladar_dias_no_lectivos(self, curso_nuevo_id: int, curso_anterior_id: int) -> dict:
        """Lleva los días no lectivos personalizados de un curso al siguiente.

        Los desplaza tantos años como separen a los dos cursos y descarta los que
        se salgan del rango del curso nuevo. Las fechas fijas (Navidad, Fallas)
        caen donde deben; las que dependen del día de la semana hay que revisarlas.
        """
        curso_nuevo = self.curso_repo.get_by_id(curso_nuevo_id)
        curso_anterior = self.curso_repo.get_by_id(curso_anterior_id)
        if not curso_nuevo or not curso_anterior:
            raise ValueError("No se encontraron los dos cursos para trasladar los días no lectivos")

        config = self.session.query(Configuracion).first()
        if config is None:
            return {"trasladados": 0, "descartados": 0}

        desplazamiento = curso_nuevo.anio_inicio - curso_anterior.anio_inicio
        trasladadas: list[date] = []
        descartados = 0
        for original in _leer_dias_no_lectivos(config.dias_no_lectivos_personalizados):
            movida = _desplazar_anios(original, desplazamiento)
            if movida is None or not (curso_nuevo.fecha_inicio <= movida <= curso_nuevo.fecha_fin):
                descartados += 1
                continue
            trasladadas.append(movida)

        config.dias_no_lectivos_personalizados = ",".join(
            f.isoformat() for f in sorted(set(trasladadas))
        )
        self.session.commit()
        logger.info(
            f"Trasladados {len(trasladadas)} días no lectivos a {curso_nuevo.nombre} "
            f"({descartados} descartados por quedar fuera del curso)"
        )
        return {"trasladados": len(trasladadas), "descartados": descartados}

    def preparar_curso_nuevo(
        self,
        curso_nuevo_id: int,
        curso_anterior_id: Optional[int] = None,
        copiar_profesores: bool = True,
        trasladar_no_lectivos: bool = True,
    ) -> dict:
        """Deja un curso recién creado listo para trabajar a partir del anterior.

        Las zonas, los recreos y los ajustes de reparto son únicos para toda la
        aplicación, así que ya están disponibles sin copiar nada. Lo que sí hay
        que arrastrar es el claustro y el calendario de días no lectivos.
        """
        curso_anterior_id = curso_anterior_id or self._id_del_curso_anterior_a(curso_nuevo_id)
        resumen = {"profesores": 0, "trasladados": 0, "descartados": 0, "hubo_anterior": False}
        if curso_anterior_id is None:
            return resumen

        resumen["hubo_anterior"] = True
        if copiar_profesores:
            resumen["profesores"] = self.copiar_profesores_curso_anterior(
                curso_nuevo_id, curso_anterior_id
            )
        if trasladar_no_lectivos:
            resumen.update(self.trasladar_dias_no_lectivos(curso_nuevo_id, curso_anterior_id))
        return resumen

    def _id_del_curso_anterior_a(self, curso_id: int) -> Optional[int]:
        curso = self.curso_repo.get_by_id(curso_id)
        if not curso:
            return None
        anteriores = sorted(
            [c for c in self.curso_repo.get_all() if c.anio_inicio < curso.anio_inicio],
            key=lambda c: c.anio_inicio,
            reverse=True,
        )
        return anteriores[0].id if anteriores else None

    def listar_todos_cursos(self, incluir_cerrados: bool = True) -> list[CursoEscolarEntity]:
        todos = self.curso_repo.get_all()
        if not incluir_cerrados:
            todos = [c for c in todos if not c.cerrado]
        cursos = sorted(todos, key=lambda c: c.anio_inicio, reverse=True)
        logger.info(f"Listados {len(cursos)} cursos ({'con' if incluir_cerrados else 'sin'} cerrados)")
        return cursos

    def obtener_curso_por_anio(self, anio_inicio: int) -> Optional[CursoEscolarEntity]:
        return self.curso_repo.find_by_year(anio_inicio)


def _leer_dias_no_lectivos(texto: Optional[str]) -> list[date]:
    fechas: list[date] = []
    for token in (texto or "").split(","):
        limpio = token.strip()
        if not limpio:
            continue
        try:
            fechas.append(date.fromisoformat(limpio))
        except ValueError:
            continue
    return fechas


def _desplazar_anios(fecha: date, anios: int) -> Optional[date]:
    try:
        return fecha.replace(year=fecha.year + anios)
    except ValueError:
        return None
