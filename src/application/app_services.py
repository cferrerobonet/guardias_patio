"""
AppServices — Facade de servicios de aplicación para la capa de presentación.

Centraliza la instanciación de repositorios y use cases para que los widgets
de presentación no accedan directamente a SQLAlchemy.

Uso:
    services = AppServices(session)
    profesores = services.profesores.get_all()
    config = services.config.execute()
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from application.use_cases.configuracion import (
        ActualizarConfiguracionUseCase,
        ObtenerConfiguracionUseCase,
    )
    from application.use_cases.guardia import (
        AsignarGuardiaUseCase,
        LimpiarGuardiasUseCase,
        ObtenerGuardiasUseCase,
    )
    from application.use_cases.profesor import (
        ActualizarProfesorUseCase,
        BuscarProfesoresUseCase,
        CrearProfesorUseCase,
        EliminarProfesorUseCase,
        ListarProfesoresUseCase,
        ObtenerProfesorUseCase,
    )
    from application.use_cases.zona import (
        ActualizarZonaUseCase,
        CrearZonaUseCase,
        EliminarZonaUseCase,
        ListarZonasUseCase,
        ObtenerZonaUseCase,
    )
    from infrastructure.repositories import (
        SQLAlchemyAusenciaRepository,
        SQLAlchemyConfiguracionRepository,
        SQLAlchemyCursoEscolarRepository,
        SQLAlchemyGuardiaRepository,
        SQLAlchemyProfesorRepository,
        SQLAlchemyZonaRepository,
    )
    from services.gestor_cursos import GestorCursos


class AppServices:
    """
    Facade de servicios de aplicación.

    Instancia bajo demanda repositorios y use cases. Todos los atributos
    son propiedades lazy — solo se crean cuando se accede por primera vez.
    """

    def __init__(self, session: Session) -> None:
        self._session = session
        self._profesor_repo: Optional[SQLAlchemyProfesorRepository] = None
        self._zona_repo: Optional[SQLAlchemyZonaRepository] = None
        self._guardia_repo: Optional[SQLAlchemyGuardiaRepository] = None
        self._ausencia_repo: Optional[SQLAlchemyAusenciaRepository] = None
        self._configuracion_repo: Optional[SQLAlchemyConfiguracionRepository] = None
        self._curso_repo: Optional[SQLAlchemyCursoEscolarRepository] = None
        self._gestor_cursos: Optional[GestorCursos] = None

    # ------------------------------------------------------------------
    # Repositorios
    # ------------------------------------------------------------------

    @property
    def profesores(self) -> SQLAlchemyProfesorRepository:
        if self._profesor_repo is None:
            from infrastructure.repositories import SQLAlchemyProfesorRepository
            self._profesor_repo = SQLAlchemyProfesorRepository(self._session)
        return self._profesor_repo

    @property
    def zonas(self) -> SQLAlchemyZonaRepository:
        if self._zona_repo is None:
            from infrastructure.repositories import SQLAlchemyZonaRepository
            self._zona_repo = SQLAlchemyZonaRepository(self._session)
        return self._zona_repo

    @property
    def guardias(self) -> SQLAlchemyGuardiaRepository:
        if self._guardia_repo is None:
            from infrastructure.repositories import SQLAlchemyGuardiaRepository
            self._guardia_repo = SQLAlchemyGuardiaRepository(self._session)
        return self._guardia_repo

    @property
    def ausencias(self) -> SQLAlchemyAusenciaRepository:
        if self._ausencia_repo is None:
            from infrastructure.repositories import SQLAlchemyAusenciaRepository
            self._ausencia_repo = SQLAlchemyAusenciaRepository(self._session)
        return self._ausencia_repo

    @property
    def configuracion_repo(self) -> SQLAlchemyConfiguracionRepository:
        if self._configuracion_repo is None:
            from infrastructure.repositories import SQLAlchemyConfiguracionRepository
            self._configuracion_repo = SQLAlchemyConfiguracionRepository(self._session)
        return self._configuracion_repo

    @property
    def cursos(self) -> SQLAlchemyCursoEscolarRepository:
        if self._curso_repo is None:
            from infrastructure.repositories import SQLAlchemyCursoEscolarRepository
            self._curso_repo = SQLAlchemyCursoEscolarRepository(self._session)
        return self._curso_repo

    # ------------------------------------------------------------------
    # Use Cases — Configuración
    # ------------------------------------------------------------------

    def obtener_configuracion(self) -> ObtenerConfiguracionUseCase:
        from application.use_cases.configuracion import ObtenerConfiguracionUseCase
        return ObtenerConfiguracionUseCase(self._session)

    def actualizar_configuracion(self) -> ActualizarConfiguracionUseCase:
        from application.use_cases.configuracion import ActualizarConfiguracionUseCase
        return ActualizarConfiguracionUseCase(self._session)

    # ------------------------------------------------------------------
    # Use Cases — Profesor
    # ------------------------------------------------------------------

    def listar_profesores(self) -> ListarProfesoresUseCase:
        from application.use_cases.profesor import ListarProfesoresUseCase
        return ListarProfesoresUseCase(self._session)

    def obtener_profesor(self) -> ObtenerProfesorUseCase:
        from application.use_cases.profesor import ObtenerProfesorUseCase
        return ObtenerProfesorUseCase(self._session)

    def crear_profesor(self) -> CrearProfesorUseCase:
        from application.use_cases.profesor import CrearProfesorUseCase
        return CrearProfesorUseCase(self._session)

    def actualizar_profesor(self) -> ActualizarProfesorUseCase:
        from application.use_cases.profesor import ActualizarProfesorUseCase
        return ActualizarProfesorUseCase(self._session)

    def eliminar_profesor(self) -> EliminarProfesorUseCase:
        from application.use_cases.profesor import EliminarProfesorUseCase
        return EliminarProfesorUseCase(self._session)

    def buscar_profesores(self) -> BuscarProfesoresUseCase:
        from application.use_cases.profesor import BuscarProfesoresUseCase
        return BuscarProfesoresUseCase(self._session)

    # ------------------------------------------------------------------
    # Use Cases — Zona
    # ------------------------------------------------------------------

    def listar_zonas(self) -> ListarZonasUseCase:
        from application.use_cases.zona import ListarZonasUseCase
        return ListarZonasUseCase(self._session)

    def obtener_zona(self) -> ObtenerZonaUseCase:
        from application.use_cases.zona import ObtenerZonaUseCase
        return ObtenerZonaUseCase(self._session)

    def crear_zona(self) -> CrearZonaUseCase:
        from application.use_cases.zona import CrearZonaUseCase
        return CrearZonaUseCase(self._session)

    def actualizar_zona(self) -> ActualizarZonaUseCase:
        from application.use_cases.zona import ActualizarZonaUseCase
        return ActualizarZonaUseCase(self._session)

    def eliminar_zona(self) -> EliminarZonaUseCase:
        from application.use_cases.zona import EliminarZonaUseCase
        return EliminarZonaUseCase(self._session)

    # ------------------------------------------------------------------
    # Use Cases — Guardia
    # ------------------------------------------------------------------

    def obtener_guardias(self) -> ObtenerGuardiasUseCase:
        from application.use_cases.guardia import ObtenerGuardiasUseCase
        return ObtenerGuardiasUseCase(self._session)

    def asignar_guardia(self) -> AsignarGuardiaUseCase:
        from application.use_cases.guardia import AsignarGuardiaUseCase
        return AsignarGuardiaUseCase(self._session)

    def limpiar_guardias(self) -> LimpiarGuardiasUseCase:
        from application.use_cases.guardia import LimpiarGuardiasUseCase
        return LimpiarGuardiasUseCase(self._session)

    # ------------------------------------------------------------------
    # Servicios de aplicación
    # ------------------------------------------------------------------

    @property
    def gestor_cursos(self) -> GestorCursos:
        if self._gestor_cursos is None:
            from services.gestor_cursos import GestorCursos
            self._gestor_cursos = GestorCursos(self._session)
        return self._gestor_cursos

    # ------------------------------------------------------------------
    # Helpers de conteo (muy usados en widgets de estadísticas)
    # ------------------------------------------------------------------

    def contar_profesores_activos(self) -> int:
        return sum(1 for p in self.profesores.get_all() if p.activo)

    def contar_profesores_inactivos(self) -> int:
        return sum(1 for p in self.profesores.get_all() if not p.activo)

    def contar_zonas(self) -> int:
        return self.zonas.count()

    def contar_guardias(self) -> int:
        return self.guardias.count()

    def contar_profesores(self) -> int:
        return self.profesores.count()

    def contar_cursos(self) -> int:
        return self.cursos.count()

    def contar_configuraciones(self) -> int:
        return self.configuracion_repo.count()

    def fecha_min_guardias(self):
        """Fecha más antigua de guardia registrada, o None si no hay guardias."""
        todas = self.guardias.get_all()
        if not todas:
            return None
        return min(g.fecha for g in todas)

    def fecha_max_guardias(self):
        """Fecha más reciente de guardia registrada, o None si no hay guardias."""
        todas = self.guardias.get_all()
        if not todas:
            return None
        return max(g.fecha for g in todas)

    # ------------------------------------------------------------------
    # Helpers cross-aggregate (queries que involucran múltiples modelos)
    # ------------------------------------------------------------------

    def profesores_con_guardias_en_curso(self, curso_id: int):
        """Retorna entidades ProfesorEntity distintas que tienen guardias en el curso dado."""
        from infrastructure.database.models import Guardia as GuardiaModel, Profesor as ProfesorModel
        from infrastructure.mappers.profesor_mapper import ProfesorMapper

        models = (
            self._session.query(ProfesorModel)
            .join(GuardiaModel, ProfesorModel.id == GuardiaModel.profesor_id)
            .filter(GuardiaModel.curso_id == curso_id)
            .distinct()
            .order_by(ProfesorModel.nombre_completo)
            .all()
        )
        return [ProfesorMapper.to_entity(m) for m in models]

    def ausencias_de_profesores_en_curso(self, curso_id: int):
        """Retorna ausencias de profesores que tienen guardias en el curso dado."""
        from infrastructure.database.models import Ausencia as AusenciaModel, Guardia as GuardiaModel
        from infrastructure.mappers.ausencia_mapper import AusenciaMapper

        profesor_ids = [
            row[0]
            for row in self._session.query(GuardiaModel.profesor_id)
            .filter(GuardiaModel.curso_id == curso_id)
            .distinct()
            .all()
        ]
        if not profesor_ids:
            return []
        models = (
            self._session.query(AusenciaModel)
            .filter(AusenciaModel.profesor_id.in_(profesor_ids))
            .order_by(AusenciaModel.fecha_inicio.desc())
            .all()
        )
        return [AusenciaMapper.to_entity(m) for m in models]

    def profesores_activos_con_fechas_especiales(self):
        """Retorna profesores activos que tienen fecha_inicio_guardias o fecha_fin_guardias."""
        from infrastructure.database.models import Profesor as ProfesorModel
        from infrastructure.mappers.profesor_mapper import ProfesorMapper

        models = (
            self._session.query(ProfesorModel)
            .filter(
                ProfesorModel.activo.is_(True),
                (ProfesorModel.fecha_inicio_guardias.isnot(None))
                | (ProfesorModel.fecha_fin_guardias.isnot(None)),
            )
            .all()
        )
        return [ProfesorMapper.to_entity(m) for m in models]
