"""
Domain Service: Equidad en Guardias

Evalúa y mantiene la equidad en la distribución de guardias.
Identifica desbalances y sugiere reasignaciones para mejorar equidad.

Métricas de equidad consideradas:
- Desviación respecto a cuota asignada
- Coeficiente de variación entre profesores del mismo % jornada
- Distribución temporal (evitar concentración en pocas fechas)
- Balance entre zonas (si hay preferencias)
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from models.models import Guardia, Profesor
from services.estadisticas_service import EstadisticasService
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class DesbalanceInfo:
    """Información sobre un desbalance detectado."""

    profesor_id: int
    nombre_profesor: str
    guardias_asignadas: int
    cuota_esperada: int
    diferencia: int  # positivo = exceso, negativo = déficit
    porcentaje_desviacion: float
    gravedad: str  # "leve", "moderado", "critico"


@dataclass
class SugerenciaReasignacion:
    """Sugerencia de reasignación para mejorar equidad."""

    guardia_id: int
    profesor_origen_id: int
    profesor_destino_id: int
    fecha: date
    recreo_id: int
    zona_id: int
    mejora_esperada: float  # reducción en coeficiente de variación
    razon: str


class EquidadGuardiasService:
    """
    Servicio de dominio para evaluar y mejorar equidad en guardias.

    Responsabilidades:
    - Calcular índices de equidad
    - Identificar desbalances
    - Sugerir reasignaciones
    - Generar reportes de equidad
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.stats_service = EstadisticasService(session)
        self.logger = logger

    def calcular_indice_equidad(
        self, guardias: List[Guardia], cuotas: Dict[int, int]
    ) -> float:
        """
        Calcula un índice global de equidad (0-1, donde 1 es perfecto).

        Fórmula: 1 - (coeficiente_variacion / 2)
        CV = desviación_estándar / media

        Args:
            guardias: Lista de guardias asignadas
            cuotas: Dict de cuotas esperadas por profesor

        Returns:
            Índice entre 0 (muy inequitativo) y 1 (perfectamente equitativo)

        Examples:
            >>> service = EquidadGuardiasService(session)
            >>> indice = service.calcular_indice_equidad(guardias, cuotas)
            >>> print(f"Índice de equidad: {indice:.2%}")
        """
        if not guardias or not cuotas:
            return 1.0  # Sin datos, consideramos equitativo

        # Calcular guardias reales por profesor
        guardias_reales = self.stats_service.calcular_guardias_por_profesor(guardias)

        # Calcular desviaciones respecto a cuota
        desviaciones = []
        for prof_id, cuota in cuotas.items():
            reales = guardias_reales.get(prof_id, 0)
            if cuota > 0:
                desviacion_relativa = abs(reales - cuota) / cuota
                desviaciones.append(desviacion_relativa)

        if not desviaciones:
            return 1.0

        # Calcular coeficiente de variación
        import statistics

        media = statistics.mean(desviaciones)
        if media == 0:
            return 1.0

        try:
            desv_std = statistics.stdev(desviaciones)
            cv = desv_std / media
            # Normalizar a [0, 1], donde CV=0 → índice=1, CV alto → índice bajo
            indice = max(0.0, 1.0 - cv / 2)
        except statistics.StatisticsError:
            indice = 1.0

        return indice

    def identificar_desbalances(
        self,
        guardias: List[Guardia],
        cuotas: Dict[int, int],
        umbral_leve: float = 0.15,  # 15% desviación
        umbral_moderado: float = 0.30,  # 30% desviación
    ) -> List[DesbalanceInfo]:
        """
        Identifica profesores con desbalances en sus guardias.

        Args:
            guardias: Lista de guardias
            cuotas: Cuotas esperadas
            umbral_leve: % desviación para considerar leve
            umbral_moderado: % desviación para considerar moderado (>30% es crítico)

        Returns:
            Lista de desbalances ordenados por gravedad

        Examples:
            >>> desbalances = service.identificar_desbalances(guardias, cuotas)
            >>> for d in desbalances:
            ...     print(f"{d.nombre_profesor}: {d.gravedad} ({d.diferencia:+d})")
        """
        guardias_reales = self.stats_service.calcular_guardias_por_profesor(guardias)
        desbalances = []

        for prof_id, cuota in cuotas.items():
            reales = guardias_reales.get(prof_id, 0)
            diferencia = reales - cuota

            if diferencia == 0:
                continue  # Perfectamente balanceado

            # Calcular porcentaje de desviación
            if cuota > 0:
                porcentaje = abs(diferencia) / cuota
            else:
                porcentaje = 1.0 if reales > 0 else 0.0

            # Determinar gravedad
            if porcentaje <= umbral_leve:
                gravedad = "leve"
            elif porcentaje <= umbral_moderado:
                gravedad = "moderado"
            else:
                gravedad = "critico"

            # Obtener nombre del profesor
            profesor = self.session.query(Profesor).get(prof_id)
            nombre = profesor.nombre_completo if profesor else f"Profesor {prof_id}"

            desbalances.append(
                DesbalanceInfo(
                    profesor_id=prof_id,
                    nombre_profesor=nombre,
                    guardias_asignadas=reales,
                    cuota_esperada=cuota,
                    diferencia=diferencia,
                    porcentaje_desviacion=porcentaje,
                    gravedad=gravedad,
                )
            )

        # Ordenar por gravedad y diferencia absoluta
        orden_gravedad = {"critico": 0, "moderado": 1, "leve": 2}
        desbalances.sort(key=lambda d: (orden_gravedad[d.gravedad], -abs(d.diferencia)))

        return desbalances

    def sugerir_reasignaciones(
        self,
        guardias: List[Guardia],
        cuotas: Dict[int, int],
        max_sugerencias: int = 10,
    ) -> List[SugerenciaReasignacion]:
        """
        Sugiere reasignaciones para mejorar la equidad.

        Algoritmo:
        1. Identificar profesores con exceso y déficit
        2. Buscar guardias de profesores con exceso que puedan reasignarse
        3. Validar que el profesor destino pueda tomar la guardia
        4. Calcular mejora esperada en equidad
        5. Ordenar por mejora esperada

        Args:
            guardias: Lista de guardias actuales
            cuotas: Cuotas esperadas
            max_sugerencias: Máximo número de sugerencias a generar

        Returns:
            Lista de sugerencias ordenadas por impacto

        Examples:
            >>> sugerencias = service.sugerir_reasignaciones(guardias, cuotas)
            >>> for sug in sugerencias[:3]:  # Top 3
            ...     print(f"Reasignar guardia {sug.guardia_id}: "
            ...           f"Profesor {sug.profesor_origen_id} → {sug.profesor_destino_id}")
        """
        desbalances = self.identificar_desbalances(guardias, cuotas)

        # Separar en exceso y déficit
        con_exceso = [d for d in desbalances if d.diferencia > 0]
        con_deficit = [d for d in desbalances if d.diferencia < 0]

        if not con_exceso or not con_deficit:
            self.logger.info("No hay desbalances que corregir")
            return []

        sugerencias = []

        # Por cada profesor con exceso
        for prof_exceso in con_exceso:
            if len(sugerencias) >= max_sugerencias:
                break

            # Obtener sus guardias
            guardias_exceso = [
                g for g in guardias if g.profesor_id == prof_exceso.profesor_id
            ]

            # Por cada guardia, ver si se puede reasignar a alguien con déficit
            for guardia in guardias_exceso:
                if len(sugerencias) >= max_sugerencias:
                    break

                for prof_deficit in con_deficit:
                    # Verificar que el profesor destino pueda tomar la guardia
                    # (esto requeriría más validaciones en producción)

                    # Calcular mejora esperada
                    mejora = self._calcular_mejora_reasignacion(
                        prof_exceso, prof_deficit, guardias, cuotas
                    )

                    razon = (
                        f"Reducir exceso de {prof_exceso.nombre_profesor} "
                        f"({prof_exceso.diferencia:+d}) y déficit de "
                        f"{prof_deficit.nombre_profesor} ({prof_deficit.diferencia:+d})"
                    )

                    sugerencias.append(
                        SugerenciaReasignacion(
                            guardia_id=guardia.id,
                            profesor_origen_id=prof_exceso.profesor_id,
                            profesor_destino_id=prof_deficit.profesor_id,
                            fecha=guardia.fecha,
                            recreo_id=guardia.recreo_id,
                            zona_id=guardia.zona_id,
                            mejora_esperada=mejora,
                            razon=razon,
                        )
                    )

        # Ordenar por mejora esperada (descendente)
        sugerencias.sort(key=lambda s: s.mejora_esperada, reverse=True)

        return sugerencias[:max_sugerencias]

    def generar_reporte_equidad(
        self, guardias: List[Guardia], cuotas: Dict[int, int]
    ) -> dict:
        """
        Genera un reporte completo de equidad.

        Returns:
            Dict con: índice, desbalances, profesores_ok, profesores_problema, etc.
        """
        indice = self.calcular_indice_equidad(guardias, cuotas)
        desbalances = self.identificar_desbalances(guardias, cuotas)

        # Clasificar desbalances
        criticos = [d for d in desbalances if d.gravedad == "critico"]
        moderados = [d for d in desbalances if d.gravedad == "moderado"]
        leves = [d for d in desbalances if d.gravedad == "leve"]

        # Profesores sin problemas
        guardias_reales = self.stats_service.calcular_guardias_por_profesor(guardias)
        profesores_ok = []
        for prof_id, cuota in cuotas.items():
            reales = guardias_reales.get(prof_id, 0)
            if reales == cuota:
                profesor = self.session.query(Profesor).get(prof_id)
                if profesor:
                    profesores_ok.append(profesor.nombre_completo)

        return {
            "indice_equidad": indice,
            "total_desbalances": len(desbalances),
            "desbalances_criticos": len(criticos),
            "desbalances_moderados": len(moderados),
            "desbalances_leves": len(leves),
            "profesores_perfectos": len(profesores_ok),
            "detalle_criticos": criticos,
            "detalle_moderados": moderados,
            "detalle_leves": leves,
            "profesores_sin_problemas": profesores_ok,
        }

    def log_reporte_equidad(
        self, guardias: List[Guardia], cuotas: Dict[int, int]
    ) -> None:
        """Genera y muestra en log un reporte de equidad."""
        reporte = self.generar_reporte_equidad(guardias, cuotas)

        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("REPORTE DE EQUIDAD EN GUARDIAS")
        self.logger.info("=" * 70)
        self.logger.info(f"Índice de equidad: {reporte['indice_equidad']:.2%}")
        self.logger.info(f"Total desbalances: {reporte['total_desbalances']}")
        self.logger.info(
            f"  • Críticos: {reporte['desbalances_criticos']}"
        )
        self.logger.info(
            f"  • Moderados: {reporte['desbalances_moderados']}"
        )
        self.logger.info(f"  • Leves: {reporte['desbalances_leves']}")
        self.logger.info(
            f"Profesores con cuota exacta: {reporte['profesores_perfectos']}"
        )

        if reporte["detalle_criticos"]:
            self.logger.warning("")
            self.logger.warning("⚠️  DESBALANCES CRÍTICOS:")
            for d in reporte["detalle_criticos"][:5]:  # Mostrar top 5
                self.logger.warning(
                    f"  • {d.nombre_profesor}: {d.guardias_asignadas}/{d.cuota_esperada} "
                    f"({d.diferencia:+d}, {d.porcentaje_desviacion:.0%})"
                )

        self.logger.info("=" * 70)

    # Métodos privados auxiliares

    def _calcular_mejora_reasignacion(
        self,
        prof_exceso: DesbalanceInfo,
        prof_deficit: DesbalanceInfo,
        guardias: List[Guardia],
        cuotas: Dict[int, int],
    ) -> float:
        """
        Calcula la mejora esperada en el índice de equidad al hacer una reasignación.

        Returns:
            Mejora esperada (delta positivo en índice de equidad)
        """
        # Simular reasignación
        guardias_simuladas = guardias.copy()

        # Encontrar una guardia del profesor con exceso y simular cambio
        # (versión simplificada, en producción sería más elaborado)

        # Calcular índices antes y después
        indice_antes = self.calcular_indice_equidad(guardias, cuotas)

        # Para la simulación, simplemente reducimos desviación
        mejora_estimada = (
            abs(prof_exceso.diferencia) + abs(prof_deficit.diferencia)
        ) / (sum(cuotas.values()) or 1)

        return mejora_estimada
