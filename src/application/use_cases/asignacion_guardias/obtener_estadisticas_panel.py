"""
Use Case: Obtener estadísticas completas para el panel de UI.

Recupera y calcula todas las estadísticas necesarias para
el widget PanelEstadisticas de forma centralizada.
"""

from collections import Counter, defaultdict
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from application.dtos.asignacion_guardias_dto import (
    DatosGraficoDTO,
    EstadisticaProfesorDTO,
    EstadisticasPanelCompletoDTO,
    EstadisticaZonaDTO,
    ResumenPanelDTO,
)
from core.logging import get_logger
from core.observability import with_metrics
from infrastructure.database.models import Configuracion, CursoEscolar, Guardia, Profesor, Zona
from utils.orden import clave_alfabetica

logger = get_logger(__name__)

#: Hasta ±1 es redondeo del reparto, no una desigualdad.
TOLERANCIA_CUOTA = 1


class ObtenerEstadisticasPanelUseCase:
    """
    Caso de uso para obtener estadísticas completas del panel.

    Encapsula toda la lógica de consultas y cálculos que antes
    estaba dispersa en el widget PanelEstadisticas.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("obtener_estadisticas_panel")
    def execute(self) -> EstadisticasPanelCompletoDTO:
        """
        Ejecutar la obtención de estadísticas completas.

        Returns:
            EstadisticasPanelCompletoDTO con todas las estadísticas
        """
        # Sólo el curso activo, como el calendario: antes se mezclaban todos (2026-10-03).
        consulta = self.session.query(Guardia)
        curso = self.session.query(CursoEscolar).filter_by(activo=True).first()
        if curso is not None:
            consulta = consulta.filter(Guardia.curso_id == curso.id)
        guardias = consulta.all()
        profesores = self.session.query(Profesor).all()
        zonas = self.session.query(Zona).filter(Zona.activa.is_(True)).all()
        cuotas = self._cuotas() if guardias else None

        # Calcular estadísticas
        resumen = self._calcular_resumen(guardias, profesores, zonas)
        por_profesor = self._calcular_por_profesor(guardias, profesores, cuotas)
        self._completar_resumen(resumen, guardias, por_profesor, cuotas)
        por_zona = self._calcular_por_zona(guardias, zonas)
        grafico_profesores = self._preparar_grafico_profesores(guardias, profesores)
        grafico_zonas = self._preparar_grafico_zonas(guardias, zonas)

        return EstadisticasPanelCompletoDTO(
            resumen=resumen,
            por_profesor=por_profesor,
            por_zona=por_zona,
            grafico_profesores=grafico_profesores,
            grafico_zonas=grafico_zonas,
            grafico_diferencias=self._preparar_grafico_diferencias(por_profesor),
            grafico_sustitutos=self._preparar_grafico_sustitutos(por_profesor),
        )

    def _cuotas(self) -> Optional[dict]:
        """La cuota oficial de cada profesor, la misma que usa la generación.

        Sin configuración no hay cuotas: el panel enseña entonces sólo recuentos.
        """
        if self.session.query(Configuracion).first() is None:
            return None
        try:
            from services.distribucion_cuotas_service import DistribucionCuotasService

            return DistribucionCuotasService(self.session).calcular_cuotas()
        except (SQLAlchemyError, ValueError, TypeError, ZeroDivisionError) as e:
            logger.warning(f"No se pudieron calcular las cuotas para las estadísticas: {e}")
            return None

    @staticmethod
    def _completar_resumen(resumen, guardias, por_profesor, cuotas) -> None:
        resumen.sustituciones = sum(1 for g in guardias if g.es_sustitucion)
        if cuotas is None:
            return
        resumen.ranuras_curso = sum(cuotas.values())
        con_cuota = [p for p in por_profesor if p.diferencia is not None]
        resumen.fuera_de_cuota = sum(
            1 for p in con_cuota if abs(p.diferencia) > TOLERANCIA_CUOTA
        )
        if con_cuota:
            peor = max(con_cuota, key=lambda p: abs(p.diferencia))
            resumen.mayor_diferencia = peor.diferencia
            resumen.profesor_mayor_diferencia = peor.nombre_completo

    @staticmethod
    def _preparar_grafico_diferencias(por_profesor) -> DatosGraficoDTO:
        filas = sorted(
            (p for p in por_profesor if p.diferencia is not None),
            key=lambda p: (p.diferencia, clave_alfabetica(p.nombre_completo)),
        )
        return DatosGraficoDTO(
            nombres=[p.nombre_completo for p in filas],
            cantidades=[p.diferencia for p in filas],
        )

    @staticmethod
    def _preparar_grafico_sustitutos(por_profesor) -> DatosGraficoDTO:
        filas = sorted(
            (p for p in por_profesor if p.veces_sustituto),
            key=lambda p: (-p.veces_sustituto, clave_alfabetica(p.nombre_completo)),
        )[:10]
        return DatosGraficoDTO(
            nombres=[p.nombre_completo for p in filas],
            cantidades=[p.veces_sustituto for p in filas],
        )

    def _calcular_resumen(
        self,
        guardias: list,
        profesores: list,
        zonas: list,
    ) -> ResumenPanelDTO:
        """Calcular resumen general."""
        total_guardias = len(guardias)
        total_profesores = len(profesores)
        total_zonas = len(zonas)

        # Profesores con guardias
        profesores_con_guardias = len(set(g.profesor_id for g in guardias))

        # Guardias por turno
        guardias_manana = sum(1 for g in guardias if g.turno == "mañana")
        guardias_tarde = sum(1 for g in guardias if g.turno == "tarde")

        # Cálculos derivados
        promedio = 0.0
        cobertura = 0
        if profesores_con_guardias > 0:
            promedio = total_guardias / profesores_con_guardias
            cobertura = min(100, int((promedio / 50) * 100))

        return ResumenPanelDTO(
            total_guardias=total_guardias,
            profesores_con_guardias=profesores_con_guardias,
            total_profesores=total_profesores,
            total_zonas=total_zonas,
            guardias_manana=guardias_manana,
            guardias_tarde=guardias_tarde,
            promedio_por_profesor=promedio,
            cobertura_estimada=cobertura,
        )

    def _calcular_por_profesor(
        self,
        guardias: list,
        profesores: list,
        cuotas: Optional[dict] = None,
    ) -> list[EstadisticaProfesorDTO]:
        """Calcular estadísticas por profesor."""
        # Agrupar guardias por profesor
        guardias_por_prof = defaultdict(lambda: {"total": 0, "mañana": 0, "tarde": 0})
        for g in guardias:
            guardias_por_prof[g.profesor_id]["total"] += 1
            if g.turno == "mañana":
                guardias_por_prof[g.profesor_id]["mañana"] += 1
            else:
                guardias_por_prof[g.profesor_id]["tarde"] += 1

        total_guardias = len(guardias)
        sustituto = Counter(g.profesor_id for g in guardias if g.es_sustitucion)
        sustituido = Counter(
            g.profesor_sustituido_id
            for g in guardias
            if g.es_sustitucion and g.profesor_sustituido_id is not None
        )
        resultado = []

        for profesor in profesores:
            stats = guardias_por_prof.get(profesor.id, {"total": 0, "mañana": 0, "tarde": 0})

            # Calcular porcentaje
            porcentaje = 0.0
            if total_guardias > 0:
                porcentaje = (stats["total"] / total_guardias) * 100

            cuota = cuotas.get(profesor.id) if cuotas is not None else None
            diferencia = stats["total"] - cuota if cuota is not None else None

            # Con cuota, el estado dice si el reparto es justo para él; sin ella
            # (no hay configuración) sólo cuenta guardias.
            if diferencia is not None:
                if abs(diferencia) <= TOLERANCIA_CUOTA:
                    estado = "✅ En su cuota"
                elif diferencia > 0:
                    estado = f"⚠️ {diferencia} por encima"
                else:
                    estado = f"⚠️ {-diferencia} por debajo"
            elif stats["total"] == 0:
                estado = "❌ Sin guardias"
            elif stats["total"] < 5:
                estado = "⚠️ Pocas guardias"
            else:
                estado = "✅ Asignado"

            resultado.append(
                EstadisticaProfesorDTO(
                    profesor_id=profesor.id,
                    nombre_completo=profesor.nombre_completo,
                    total=stats["total"],
                    manana=stats["mañana"],
                    tarde=stats["tarde"],
                    porcentaje=porcentaje,
                    estado=estado,
                    fecha_inicio_guardias=profesor.fecha_inicio_guardias,
                    fecha_fin_guardias=profesor.fecha_fin_guardias,
                    cuota=cuota,
                    diferencia=diferencia,
                    veces_sustituto=sustituto.get(profesor.id, 0),
                    veces_sustituido=sustituido.get(profesor.id, 0),
                )
            )

        return resultado

    def _calcular_por_zona(
        self,
        guardias: list,
        zonas: list,
    ) -> list[EstadisticaZonaDTO]:
        """Calcular estadísticas por zona."""
        # Agrupar por zona
        guardias_por_zona = defaultdict(list)
        for g in guardias:
            if g.zona_id:
                guardias_por_zona[g.zona_id].append(g)

        resultado = []
        for zona in zonas:
            guardias_zona = guardias_por_zona.get(zona.id, [])
            total = len(guardias_zona)
            profesores_diferentes = len(set(g.profesor_id for g in guardias_zona))

            resultado.append(
                EstadisticaZonaDTO(
                    zona_id=zona.id,
                    nombre_zona=zona.nombre_zona,
                    total_guardias=total,
                    profesores_diferentes=profesores_diferentes,
                    porcentaje_cobertura="N/A",
                )
            )

        return resultado

    def _preparar_grafico_profesores(
        self,
        guardias: list,
        profesores: list,
    ) -> DatosGraficoDTO:
        """Preparar datos para gráfico de profesores."""
        # Contar guardias por profesor
        guardias_por_prof = defaultdict(int)
        for g in guardias:
            guardias_por_prof[g.profesor_id] += 1

        nombres = []
        cantidades = []

        for prof in profesores:
            count = guardias_por_prof.get(prof.id, 0)
            if count > 0:  # Solo profesores con guardias
                nombre = prof.nombre_completo
                if "," in nombre:
                    apellido = nombre.split(",")[0]
                    nombres.append(apellido[:15])
                else:
                    nombres.append(nombre[:15])
                cantidades.append(count)

        return DatosGraficoDTO(nombres=nombres, cantidades=cantidades)

    def _preparar_grafico_zonas(
        self,
        guardias: list,
        zonas: list,
    ) -> DatosGraficoDTO:
        """Preparar datos para gráfico de zonas."""
        # Contar guardias por zona
        guardias_por_zona = defaultdict(int)
        for g in guardias:
            if g.zona_id:
                guardias_por_zona[g.zona_id] += 1

        nombres = []
        cantidades = []

        for zona in zonas:
            count = guardias_por_zona.get(zona.id, 0)
            if count > 0:
                nombres.append(zona.nombre_zona[:20])
                cantidades.append(count)

        return DatosGraficoDTO(nombres=nombres, cantidades=cantidades)
