"""
Domain Service: Distribución de Cuotas

Calcula y distribuye las cuotas de guardias entre profesores
considerando múltiples factores de equidad.

Factores considerados:
- Turno (mañana, tarde, mixto) según recreos disponibles
- Horas de contrato (proporción respecto a 30h jornada completa)
- Factor de tutoría (ajuste_tutores / ajuste_no_tutores de configuración)
- Fechas de inicio/fin de guardias (proporción de días disponibles)
- Total de slots disponibles

Fórmula de cálculo:
    factor_total = factor_turno × factor_horas × factor_tutoria × proporcion_tiempo
    cuota = round(total_slots × factor_profesor / suma_todos_factores)

Este servicio implementa el mismo algoritmo que calculador_guardias.py
pero siguiendo principios de Clean Architecture (Domain Service).
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from models.models import Configuracion, Profesor, Zona
from services.calculador_guardias import (
    _parse_recreos_config,
    listar_dias_lectivos,
)
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class CuotaInfo:
    """Información detallada de una cuota calculada."""

    profesor_id: int
    nombre_profesor: str
    cuota: int
    porcentaje_jornada: float
    turno: str
    factor_participacion: float
    slots_disponibles: int
    fecha_inicio_guardias: Optional[date]
    observaciones: List[str]


class DistribucionCuotasService:
    """
    Servicio de dominio para calcular y distribuir cuotas de guardias.

    Algoritmo de distribución:
    1. Calcular slots totales (días × recreos × zonas)
    2. Calcular factor de participación por profesor:
       - Factor turno: proporción de recreos según turno (mañana/tarde/mixto)
       - Factor horas: horas_contrato / 30h (jornada completa)
       - Factor tutoría: ajuste_tutores o ajuste_no_tutores (de configuración)
       - Proporción tiempo: días disponibles según fechas inicio/fin
    3. Factor total = turno × horas × tutoría × tiempo
    4. Distribuir slots proporcionalmente según factor total
    5. Redondear y compensar diferencias

    Principios:
    - Equidad: Mismas condiciones → misma cuota (aproximadamente)
    - Precisión: Considera todas las restricciones reales
    - Transparencia: Explica cómo se calculó cada cuota
    - Equivalencia: Produce resultados idénticos a calculador_guardias.py
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.logger = logger

    def calcular_cuotas(
        self, profesores: Optional[List[Profesor]] = None
    ) -> Dict[int, int]:
        """
        Calcula cuotas para todos los profesores activos.

        Args:
            profesores: Lista de profesores (si None, consulta todos los activos)

        Returns:
            Dict[profesor_id, cuota]

        Examples:
            >>> service = DistribucionCuotasService(session)
            >>> cuotas = service.calcular_cuotas()
            >>> print(f"Profesor 1: {cuotas[1]} guardias")
        """
        if profesores is None:
            profesores = (
                self.session.query(Profesor).filter(Profesor.activo).all()
            )

        if not profesores:
            self.logger.warning("No hay profesores activos para calcular cuotas")
            return {}

        # Obtener configuración
        config = self.session.query(Configuracion).first()
        if not config:
            raise ValueError("No se encontró configuración activa")

        # Calcular total de slots
        total_slots = self._calcular_total_slots(config)
        self.logger.info(f"Total de slots a distribuir: {total_slots}")

        # Calcular factores de participación
        factores = self._calcular_factores_participacion(profesores, config)

        # Distribuir cuotas
        cuotas = self._distribuir_slots(profesores, factores, total_slots)

        # Log de resumen
        self._log_resumen_distribucion(profesores, cuotas, total_slots)

        return cuotas

    def calcular_cuota_profesor(
        self, profesor: Profesor, total_slots: int, profesores_activos: List[Profesor]
    ) -> int:
        """
        Calcula la cuota para un profesor específico.

        Args:
            profesor: Profesor para calcular cuota
            total_slots: Total de slots disponibles
            profesores_activos: Todos los profesores activos

        Returns:
            Cuota calculada (número de guardias)
        """
        config = self.session.query(Configuracion).first()
        if not config:
            raise ValueError("No se encontró configuración activa")

        factores = self._calcular_factores_participacion(profesores_activos, config)
        factor_profesor = factores.get(profesor.id, 0.0)

        # Calcular cuota proporcional
        suma_factores = sum(factores.values())
        if suma_factores == 0:
            return 0

        cuota = int(round(total_slots * factor_profesor / suma_factores))

        return max(0, cuota)

    def obtener_info_cuota(self, profesor: Profesor) -> CuotaInfo:
        """
        Obtiene información detallada sobre la cuota de un profesor.

        Args:
            profesor: Profesor a analizar

        Returns:
            CuotaInfo con detalles de la cuota
        """
        config = self.session.query(Configuracion).first()
        if not config:
            raise ValueError("No se encontró configuración activa")

        profesores = (
            self.session.query(Profesor).filter(Profesor.activo).all()
        )
        total_slots = self._calcular_total_slots(config)
        factores = self._calcular_factores_participacion(profesores, config)

        cuota = self.calcular_cuota_profesor(profesor, total_slots, profesores)

        observaciones = []
        if profesor.fecha_inicio_guardias:
            observaciones.append(
                f"Fecha inicio: {profesor.fecha_inicio_guardias}"
            )
        if profesor.turno != "mixto":
            observaciones.append(f"Turno restringido: {profesor.turno}")

        return CuotaInfo(
            profesor_id=profesor.id,
            nombre_profesor=profesor.nombre_completo,
            cuota=cuota,
            porcentaje_jornada=profesor.porcentaje_jornada,
            turno=profesor.turno,
            factor_participacion=factores.get(profesor.id, 0.0),
            slots_disponibles=total_slots,
            fecha_inicio_guardias=profesor.fecha_inicio_guardias,
            observaciones=observaciones,
        )

    # Métodos privados auxiliares

    def _calcular_total_slots(self, config: Configuracion) -> int:
        """Calcula el total de slots a distribuir."""
        dias_lectivos = listar_dias_lectivos(config)
        recreos = _parse_recreos_config(config)
        zonas = self.session.query(Zona).all()

        total = len(dias_lectivos) * len(recreos) * len(zonas)
        return total

    def _calcular_factores_participacion(
        self, profesores: List[Profesor], config: Configuracion
    ) -> Dict[int, float]:
        """
        Calcula el factor de participación de cada profesor.

        Factor completo = factor_turno × factor_horas × factor_tutoria × proporcion_tiempo

        Considera:
        - Turno (mañana/tarde/mixto) según recreos disponibles
        - Horas de contrato (proporción respecto a 30h jornada completa)
        - Factor de tutoría (ajuste_tutores / ajuste_no_tutores)
        - Fechas de inicio/fin de guardias
        """
        factores = {}
        recreos = _parse_recreos_config(config)
        dias_lectivos = listar_dias_lectivos(config)

        # Contar recreos por turno
        recreos_manana = sum(1 for r in recreos if r["turno"] == "mañana")
        recreos_tarde = sum(1 for r in recreos if r["turno"] == "tarde")
        total_recreos = len(recreos)

        for profesor in profesores:
            if not profesor.activo:
                factores[profesor.id] = 0.0
                continue

            # 1. Factor por turno (proporción de recreos disponibles)
            if profesor.turno == "mañana":
                factor_turno = (
                    recreos_manana / total_recreos if total_recreos > 0 else 0.5
                )
            elif profesor.turno == "tarde":
                factor_turno = (
                    recreos_tarde / total_recreos if total_recreos > 0 else 0.5
                )
            else:  # mixto
                factor_turno = 1.0

            # 2. Factor por porcentaje de jornada (ya normalizado 0-100%)
            # Usar porcentaje_jornada en lugar de horas_contrato para evitar
            # problemas con datos incorrectos (ej: 60h cuando máximo es 30h)
            factor_horas = profesor.porcentaje_jornada / 100.0

            # 3. Factor de tutoría (desde configuración)
            factor_tutoria = (
                getattr(config, 'ajuste_tutores', 1.0)
                if getattr(profesor, 'tutor', False)
                else getattr(config, 'ajuste_no_tutores', 1.0)
            )

            # 4. Proporción de tiempo disponible (fechas inicio/fin)
            proporcion_tiempo = 1.0
            if len(dias_lectivos) > 0:
                if profesor.fecha_inicio_guardias or profesor.fecha_fin_guardias:
                    inicio_efectivo = (
                        profesor.fecha_inicio_guardias
                        if profesor.fecha_inicio_guardias
                        else config.fecha_inicio_curso
                    )
                    fin_efectivo = (
                        profesor.fecha_fin_guardias
                        if profesor.fecha_fin_guardias
                        else config.fecha_fin_curso
                    )

                    # Contar días lectivos disponibles para este profesor
                    dias_disponibles = len(
                        [d for d in dias_lectivos if inicio_efectivo <= d <= fin_efectivo]
                    )
                    proporcion_tiempo = dias_disponibles / len(dias_lectivos)

                    self.logger.info(
                        f"{profesor.nombre_completo}: disponible {dias_disponibles}/"
                        f"{len(dias_lectivos)} días (factor: {proporcion_tiempo:.2f})"
                    )

            # Factor total combinado
            factor = factor_turno * factor_horas * factor_tutoria * proporcion_tiempo
            factores[profesor.id] = factor

            self.logger.debug(
                f"{profesor.nombre_completo}: turno={factor_turno:.2f}, "
                f"jornada={factor_horas:.2f} ({profesor.porcentaje_jornada}%), "
                f"tutoria={factor_tutoria:.2f}, tiempo={proporcion_tiempo:.2f} → "
                f"factor={factor:.4f}"
            )

        return factores

    def _distribuir_slots(
        self, profesores: List[Profesor], factores: Dict[int, float], total_slots: int
    ) -> Dict[int, int]:
        """Distribuye slots entre profesores según factores."""
        suma_factores = sum(factores.values())
        if suma_factores == 0:
            self.logger.warning("Suma de factores es 0, no se pueden distribuir slots")
            return {p.id: 0 for p in profesores}

        cuotas = {}
        slots_asignados = 0

        # Primera pasada: asignar proporcional redondeado
        for profesor in profesores:
            factor = factores[profesor.id]
            cuota = int(round(total_slots * factor / suma_factores))
            cuotas[profesor.id] = cuota
            slots_asignados += cuota

        # Ajustar diferencia por redondeo
        diferencia = total_slots - slots_asignados
        if diferencia != 0:
            self.logger.info(
                f"Ajustando {abs(diferencia)} slots por redondeo"
            )
            # Distribuir diferencia entre profesores con mayor factor
            profesores_ordenados = sorted(
                profesores, key=lambda p: factores[p.id], reverse=True
            )

            for i in range(abs(diferencia)):
                profesor = profesores_ordenados[i % len(profesores_ordenados)]
                if diferencia > 0:
                    cuotas[profesor.id] += 1
                else:
                    cuotas[profesor.id] = max(0, cuotas[profesor.id] - 1)

        return cuotas

    # NOTA: Método obsoleto - el ajuste por fechas ahora se hace en _calcular_factores_participacion
    # def _ajustar_por_fechas_inicio(...) - ELIMINADO

    def _log_resumen_distribucion(
        self, profesores: List[Profesor], cuotas: Dict[int, int], total_slots: int
    ):
        """Registra resumen de la distribución en el log."""
        total_cuotas = sum(cuotas.values())
        self.logger.info("")
        self.logger.info("=" * 70)
        self.logger.info("RESUMEN DE DISTRIBUCIÓN DE CUOTAS")
        self.logger.info("=" * 70)
        self.logger.info(f"Total slots: {total_slots}")
        self.logger.info(f"Total cuotas asignadas: {total_cuotas}")
        self.logger.info(f"Diferencia: {total_slots - total_cuotas}")
        self.logger.info("")

        # Agrupar por % jornada
        grupos = defaultdict(list)
        for profesor in profesores:
            cuota = cuotas.get(profesor.id, 0)
            grupos[profesor.porcentaje_jornada].append((profesor, cuota))

        for jornada in sorted(grupos.keys(), reverse=True):
            self.logger.info(f"Jornada {jornada}%:")
            for profesor, cuota in sorted(
                grupos[jornada], key=lambda x: x[1], reverse=True
            ):
                self.logger.info(
                    f"  • {profesor.nombre_completo:30} {cuota:3} guardias "
                    f"(turno: {profesor.turno})"
                )

        self.logger.info("=" * 70)
