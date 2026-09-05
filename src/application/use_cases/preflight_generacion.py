"""Caso de uso: comprobar los prerrequisitos para generar guardias.

El guardarraíl "no se puede generar sin cuotas" vivía como un booleano de la
interfaz: se perdía al cambiar de vista o de curso y no comprobaba nada real
(UXF-002). Aquí se calcula desde los datos, que es lo único que sobrevive a la
navegación, y sirve tanto para habilitar el botón de generar como para pintar el
panel de estado del curso (UXF-001, FUN-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from infrastructure.database.models import Configuracion, Profesor, Zona
from utils import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class Requisito:
    """Un prerrequisito de la generación y dónde se resuelve."""

    clave: str
    titulo: str
    cumplido: bool
    detalle: str = ""
    #: Sección del menú lateral que permite resolverlo.
    seccion: str = ""


@dataclass(frozen=True)
class ResultadoPreflight:
    """Estado del curso de cara a generar guardias."""

    requisitos: List[Requisito] = field(default_factory=list)

    @property
    def faltantes(self) -> List[Requisito]:
        return [r for r in self.requisitos if not r.cumplido]

    @property
    def listo(self) -> bool:
        return not self.faltantes

    @property
    def motivo(self) -> str:
        """Frase corta para tooltips y etiquetas de bloqueo."""
        pendientes = self.faltantes
        if not pendientes:
            return ""
        if len(pendientes) == 1:
            return f"Falta: {pendientes[0].titulo.lower()}"
        titulos = ", ".join(r.titulo.lower() for r in pendientes)
        return f"Faltan {len(pendientes)} pasos: {titulos}"


class PreflightGeneracionUseCase:
    """Responde a "¿se puede generar ya?" mirando los datos, no la sesión de UI."""

    def __init__(self, session):
        self.session = session

    def execute(self) -> ResultadoPreflight:
        return ResultadoPreflight(requisitos=list(self._comprobar()))

    def _comprobar(self):
        yield self._curso_activo()

        config = self.session.query(Configuracion).first()
        yield self._fechas_del_curso(config)
        yield self._recreos(config)
        yield self._zonas()
        yield self._profesores()

    # -- comprobaciones ------------------------------------------------------

    def _curso_activo(self) -> Requisito:
        curso = None
        try:
            from services.gestor_cursos import GestorCursos

            curso = GestorCursos.from_session(self.session).obtener_curso_activo()
        except Exception as e:  # noqa: BLE001 - sin curso el resto se explica solo
            logger.debug(f"No se pudo leer el curso activo: {e}")
        return Requisito(
            clave="curso",
            titulo="Curso escolar activo",
            cumplido=curso is not None,
            detalle=(
                f"Curso {curso.nombre}" if curso else "Crea o activa un curso escolar en Ajustes."
            ),
            seccion="ajustes",
        )

    def _fechas_del_curso(self, config) -> Requisito:
        completo = bool(
            config
            and getattr(config, "fecha_inicio_curso", None)
            and getattr(config, "fecha_fin_curso", None)
        )
        if completo:
            detalle = f"Del {config.fecha_inicio_curso} al {config.fecha_fin_curso}"
        else:
            detalle = "Indica las fechas de inicio y fin del curso en Ajustes."
        return Requisito(
            clave="fechas",
            titulo="Fechas del curso",
            cumplido=completo,
            detalle=detalle,
            seccion="ajustes",
        )

    def _recreos(self, config) -> Requisito:
        recreos = []
        if config is not None:
            try:
                from services.calculador_guardias import _parse_recreos_config

                recreos = _parse_recreos_config(config)
            except Exception as e:  # noqa: BLE001
                logger.debug(f"No se pudieron leer los recreos: {e}")
        return Requisito(
            clave="recreos",
            titulo="Recreos configurados",
            cumplido=bool(recreos),
            detalle=(
                f"{len(recreos)} recreos definidos"
                if recreos
                else "Define al menos un recreo en Ajustes."
            ),
            seccion="ajustes",
        )

    def _zonas(self) -> Requisito:
        total = self.session.query(Zona).filter(Zona.activa.is_(True)).count()
        return Requisito(
            clave="zonas",
            titulo="Zonas de patio",
            cumplido=total > 0,
            detalle=(
                f"{total} zonas activas" if total else "Crea al menos una zona de patio."
            ),
            seccion="zonas",
        )

    def _profesores(self) -> Requisito:
        total = self.session.query(Profesor).filter(Profesor.activo.is_(True)).count()
        return Requisito(
            clave="profesores",
            titulo="Profesores activos",
            cumplido=total > 0,
            detalle=(
                f"{total} profesores activos"
                if total
                else "Da de alta o importa profesores."
            ),
            seccion="profesores",
        )
