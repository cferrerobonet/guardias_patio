"""Caso de uso: comprobar los prerrequisitos para generar guardias.

El guardarraíl "no se puede generar sin cuotas" vivía como un booleano de la
interfaz: se perdía al cambiar de vista o de curso y no comprobaba nada real
(UXF-002). Aquí se calcula desde los datos, que es lo único que sobrevive a la
navegación, y sirve tanto para habilitar el botón de generar como para pintar el
panel de estado del curso (UXF-001, FUN-001).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
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
    #: Aviso sin bloqueo: se puede generar, pero quedarán huecos. El reparto
    #: cubre todo lo que puede (v6.7.0); esto dice antes qué no podrá cubrir.
    aviso: bool = False


@dataclass(frozen=True)
class ResultadoPreflight:
    """Estado del curso de cara a generar guardias."""

    requisitos: List[Requisito] = field(default_factory=list)

    @property
    def faltantes(self) -> List[Requisito]:
        return [r for r in self.requisitos if not r.cumplido and not r.aviso]

    @property
    def avisos(self) -> List[Requisito]:
        """Lo que no impide generar pero dejará huecos sin cubrir."""
        return [r for r in self.requisitos if not r.cumplido and r.aviso]

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
        yield self._profesorado_por_turno(config)

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
            oficial = getattr(config, "fecha_inicio_reparto_oficial", None)
            if isinstance(oficial, date) and oficial > config.fecha_inicio_curso:
                detalle += f" · reparto oficial desde el {oficial}"
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
        # Un recreo guardado con menos zonas de las que hay dejaría alguna zona sin
        # guardias sin decir nada (2026-10-03).
        total_zonas = self.session.query(Zona).filter(Zona.activa.is_(True)).count()
        cortos = [
            r.get("etiqueta") or f"Recreo {r.get('id')}"
            for r in self._recreos_guardados(config)
            if isinstance(r.get("zonas"), int) and r["zonas"] < total_zonas
        ]
        if cortos:
            return Requisito(
                clave="recreos",
                titulo="Recreos configurados",
                cumplido=False,
                detalle=(
                    f"{', '.join(cortos)} cubre{'n' if len(cortos) > 1 else ''} menos zonas "
                    f"de las {total_zonas} que hay. Guarda Ajustes para incluirlas todas."
                ),
                seccion="ajustes",
            )
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

    @staticmethod
    def _recreos_guardados(config) -> list:
        """Los recreos tal cual: sin «zonas» los repartos cubren todas las zonas."""
        import json

        try:
            datos = json.loads(getattr(config, "recreos_config", None) or "[]")
        except ValueError:
            return []
        return [r for r in datos if isinstance(r, dict)] if isinstance(datos, list) else []

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

    #: Turnos que pueden cubrir los recreos de cualquier turno (como al repartir).
    _TURNOS_COMODIN = ("completo", "mixto", "ambos", "", None)

    def _profesorado_por_turno(self, config) -> Requisito:
        """Cada turno con recreos necesita profesorado suficiente para cubrirlos.

        Un centro con todo el profesorado de tarde y recreos de mañana generaba
        con la mitad de los huecos sin nadie elegible (2026-10-06). Y con pocos
        mixtos pasa lo mismo a menor escala: cada profesor hace como mucho una
        guardia al día, así que si un turno pide cada día más guardias que
        profesores pueden cubrirlo, quedan huecos todos los días. No bloquea: se
        reparte lo posible y aquí se dice antes qué no.
        """
        from services.calculador_guardias import _parse_recreos_config, turnos_con_recreos

        ok = Requisito(
            clave="turnos",
            titulo="Profesorado para cada turno",
            cumplido=True,
            detalle="Cada turno con recreos tiene profesorado suficiente para cubrirlos.",
            seccion="ajustes",
            aviso=True,
        )
        if config is None:
            return ok
        manana, tarde = turnos_con_recreos(config)
        recreos = _parse_recreos_config(config)
        zonas = self.session.query(Zona).filter(Zona.activa.is_(True)).count()
        activos = [
            (t or "").strip().lower()
            for (t,) in self.session.query(Profesor.turno).filter(Profesor.activo.is_(True))
        ]
        if not activos or not zonas:
            return ok

        problemas = []
        for turno, hay in (("mañana", manana), ("tarde", tarde)):
            if not hay:
                continue
            # Como en turnos_con_recreos: lo que no es de tarde es de mañana.
            del_turno = [
                r for r in recreos
                if (str(r.get("turno") or "").strip().lower() == "tarde") == (turno == "tarde")
            ]
            por_dia = (
                sum(min(int(r.get("zonas") or zonas), zonas) for r in del_turno)
                if del_turno
                else 2 * zonas
            )
            pueden = sum(1 for a in activos if a == turno or a in self._TURNOS_COMODIN)
            if pueden == 0:
                problemas.append(
                    f"Hay recreos de {turno} pero ningún profesor de {turno} ni mixto: "
                    f"todos sus huecos se quedarán sin cubrir. Si el centro no tiene guardias "
                    f"de {turno}, desmarca «Hay guardias de {turno}» en Ajustes; si las tiene, "
                    f"da de alta a su profesorado."
                )
            elif pueden < por_dia:
                problemas.append(
                    f"Cada día de {turno} hay {por_dia} guardias y solo {pueden} profesores "
                    f"pueden hacerlas (de {turno} o mixtos), y cada uno hace como mucho una al "
                    f"día: quedarán huecos de {turno} todos los días. Da de alta profesorado, "
                    f"pon a alguien como mixto o reduce zonas o recreos de {turno}."
                )
        if not problemas:
            return ok
        return Requisito(
            clave="turnos",
            titulo="Profesorado para cada turno",
            cumplido=False,
            detalle=" ".join(problemas),
            seccion="ajustes",
            aviso=True,
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
