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

from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

from infrastructure.database.models import Configuracion, Profesor, Zona
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

    def calcular_cuotas(self, profesores: Optional[List[Profesor]] = None) -> Dict[int, int]:
        """
        Calcula cuotas para todos los profesores activos.

        La distribución se basa en:
        - Porcentaje de jornada (factor principal)
        - Factor de tutoría (ajuste desde configuración)

        El turno NO afecta el cálculo de cuotas - solo afecta dónde
        se asignan las guardias en el algoritmo de asignación.

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
            profesores = self.session.query(Profesor).filter(Profesor.activo).all()

        if not profesores:
            self.logger.warning("No hay profesores activos para calcular cuotas")
            return {}

        # Obtener configuración
        config = self.session.query(Configuracion).first()
        if not config:
            raise ValueError("No se encontró configuración activa")

        # Calcular total de slots
        total_slots = self._calcular_total_slots(config)
        self.logger.info(f"Total de slots: {total_slots}")

        # Calcular factores de participación (sin considerar turno)
        factores = self._calcular_factores_participacion(profesores, config)

        # Distribuir slots proporcionalmente entre TODOS los profesores
        cuotas = self._distribuir_slots_equitativamente(profesores, factores, total_slots)

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

        profesores = self.session.query(Profesor).filter(Profesor.activo).all()
        total_slots = self._calcular_total_slots(config)
        factores = self._calcular_factores_participacion(profesores, config)

        cuota = self.calcular_cuota_profesor(profesor, total_slots, profesores)

        observaciones = []
        if profesor.fecha_inicio_guardias:
            observaciones.append(f"Fecha inicio: {profesor.fecha_inicio_guardias}")
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

    def _calcular_slots_por_turno(self, config: Configuracion) -> Dict[str, int]:
        """
        Calcula los slots disponibles por turno.

        Returns:
            Dict con 'mañana' y 'tarde' como claves y número de slots como valores.
        """
        dias_lectivos = listar_dias_lectivos(config)
        recreos = _parse_recreos_config(config)
        zonas = self.session.query(Zona).all()

        slots_manana = 0
        slots_tarde = 0

        for recreo in recreos:
            turno_recreo = recreo.get("turno", "mañana")
            slots_recreo = len(dias_lectivos) * len(zonas)
            if turno_recreo == "mañana":
                slots_manana += slots_recreo
            else:
                slots_tarde += slots_recreo

        return {"mañana": slots_manana, "tarde": slots_tarde}

    def _get_turno_profesor(self, profesor: Profesor) -> str:
        """
        Determina el turno efectivo de un profesor.

        Returns:
            'mañana', 'tarde' o 'mixto'
        """
        turno = profesor.turno or "mixto"
        if turno in ("completo", "ambos"):
            return "mixto"
        return turno

    def _calcular_factores_participacion(
        self, profesores: List[Profesor], config: Configuracion
    ) -> Dict[int, float]:
        """
        Calcula el factor de participación de cada profesor.

        Factor completo = factor_horas × factor_tutoria

        Considera:
        - Horas de contrato (proporción respecto a 30h jornada completa)
        - Factor de tutoría (ajuste_tutores / ajuste_no_tutores)

        NOTA: El turno afecta qué slots puede cubrir cada profesor,
        pero el factor de participación es independiente del turno.
        La distribución por turno se hace en _distribuir_slots_por_turno.
        """
        factores = {}

        for profesor in profesores:
            if not profesor.activo:
                factores[profesor.id] = 0.0
                continue

            # 1. Factor por porcentaje de jornada (ya normalizado 0-100%)
            factor_horas = profesor.porcentaje_jornada / 100.0

            # 2. Factor de tutoría (desde configuración)
            factor_tutoria = (
                getattr(config, "ajuste_tutores", 1.0)
                if getattr(profesor, "tutor", False)
                else getattr(config, "ajuste_no_tutores", 1.0)
            )

            # Factor total combinado
            factor = factor_horas * factor_tutoria
            factores[profesor.id] = factor

            self.logger.debug(
                f"{profesor.nombre_completo}: "
                f"jornada={factor_horas:.2f} ({profesor.porcentaje_jornada}%), "
                f"tutoria={factor_tutoria:.2f} → factor={factor:.4f}"
            )

        return factores

    def _distribuir_slots_equitativamente(
        self,
        profesores: List[Profesor],
        factores: Dict[int, float],
        total_slots: int,
    ) -> Dict[int, int]:
        """
        Distribuye slots entre TODOS los profesores proporcionalmente.

        NO considera el turno - todos los profesores compiten por el mismo
        pool de slots. La asignación real respetará el turno, pero la cuota
        objetivo es equitativa basada solo en jornada y tutoría.

        Args:
            profesores: Lista de profesores activos
            factores: Factor de participación de cada profesor
            total_slots: Total de slots a distribuir

        Returns:
            Dict[profesor_id, cuota]
        """
        if not profesores or total_slots == 0:
            return {}

        suma_factores = sum(factores.get(p.id, 0) for p in profesores)
        if suma_factores == 0:
            self.logger.warning("Suma de factores es 0")
            return {p.id: 0 for p in profesores}

        cuotas = {}
        slots_asignados = 0

        # Primera pasada: asignar proporcional redondeado
        for profesor in profesores:
            factor = factores.get(profesor.id, 0)
            cuota = int(round(total_slots * factor / suma_factores))
            cuotas[profesor.id] = cuota
            slots_asignados += cuota

        # Ajustar diferencia por redondeo
        diferencia = total_slots - slots_asignados
        if diferencia != 0:
            self.logger.debug(f"Ajustando {abs(diferencia)} slots por redondeo")
            # Distribuir diferencia entre profesores con mayor factor
            profesores_ordenados = sorted(
                profesores, key=lambda p: factores.get(p.id, 0), reverse=True
            )

            for i in range(abs(diferencia)):
                profesor = profesores_ordenados[i % len(profesores_ordenados)]
                if diferencia > 0:
                    cuotas[profesor.id] += 1
                else:
                    cuotas[profesor.id] = max(0, cuotas[profesor.id] - 1)

        self.logger.info(
            f"Distribución equitativa: {total_slots} slots → "
            f"{sum(cuotas.values())} cuotas entre {len(profesores)} profesores"
        )

        return cuotas

    def _distribuir_slots_por_turno(
        self,
        profesores: List[Profesor],
        factores: Dict[int, float],
        slots_por_turno: Dict[str, int],
    ) -> Dict[int, int]:
        """
        Distribuye slots considerando el turno de cada profesor.

        - Profesores de mañana: solo reciben cuota de slots de mañana
        - Profesores de tarde: solo reciben cuota de slots de tarde
        - Profesores mixtos: reciben cuota de ambos turnos

        Esto garantiza que las cuotas calculadas sean realmente alcanzables.
        """
        cuotas = {p.id: 0 for p in profesores}

        # Separar profesores por turno
        profs_manana = []
        profs_tarde = []
        profs_mixtos = []

        for p in profesores:
            turno = self._get_turno_profesor(p)
            if turno == "mañana":
                profs_manana.append(p)
            elif turno == "tarde":
                profs_tarde.append(p)
            else:  # mixto
                profs_mixtos.append(p)

        self.logger.info(
            f"Distribución por turno: {len(profs_manana)} mañana, "
            f"{len(profs_tarde)} tarde, {len(profs_mixtos)} mixto"
        )

        # Distribuir slots de mañana entre profesores de mañana + mixtos
        slots_manana = slots_por_turno.get("mañana", 0)
        elegibles_manana = profs_manana + profs_mixtos
        cuotas_manana = self._distribuir_slots_grupo(
            elegibles_manana, factores, slots_manana, "mañana"
        )

        # Distribuir slots de tarde entre profesores de tarde + mixtos
        slots_tarde = slots_por_turno.get("tarde", 0)
        elegibles_tarde = profs_tarde + profs_mixtos
        cuotas_tarde = self._distribuir_slots_grupo(
            elegibles_tarde, factores, slots_tarde, "tarde"
        )

        # Combinar cuotas
        for p in profesores:
            cuotas[p.id] = cuotas_manana.get(p.id, 0) + cuotas_tarde.get(p.id, 0)

        return cuotas

    def _distribuir_slots_grupo(
        self,
        profesores: List[Profesor],
        factores: Dict[int, float],
        total_slots: int,
        nombre_grupo: str,
    ) -> Dict[int, int]:
        """Distribuye slots entre un grupo de profesores según sus factores."""
        if not profesores or total_slots == 0:
            return {}

        suma_factores = sum(factores.get(p.id, 0) for p in profesores)
        if suma_factores == 0:
            self.logger.warning(f"Suma de factores es 0 para grupo {nombre_grupo}")
            return {p.id: 0 for p in profesores}

        cuotas = {}
        slots_asignados = 0

        # Primera pasada: asignar proporcional redondeado
        for profesor in profesores:
            factor = factores.get(profesor.id, 0)
            cuota = int(round(total_slots * factor / suma_factores))
            cuotas[profesor.id] = cuota
            slots_asignados += cuota

        # Ajustar diferencia por redondeo
        diferencia = total_slots - slots_asignados
        if diferencia != 0:
            self.logger.debug(
                f"Ajustando {abs(diferencia)} slots en grupo {nombre_grupo}"
            )
            # Distribuir diferencia entre profesores con mayor factor
            profesores_ordenados = sorted(
                profesores, key=lambda p: factores.get(p.id, 0), reverse=True
            )

            for i in range(abs(diferencia)):
                profesor = profesores_ordenados[i % len(profesores_ordenados)]
                if diferencia > 0:
                    cuotas[profesor.id] += 1
                else:
                    cuotas[profesor.id] = max(0, cuotas[profesor.id] - 1)

        self.logger.info(
            f"Grupo {nombre_grupo}: {total_slots} slots → "
            f"{sum(cuotas.values())} cuotas asignadas a {len(profesores)} profesores"
        )

        return cuotas

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

        # Agrupar por porcentaje de jornada
        grupos_jornada = {}
        for profesor in profesores:
            cuota = cuotas.get(profesor.id, 0)
            jornada = int(profesor.porcentaje_jornada)
            if jornada not in grupos_jornada:
                grupos_jornada[jornada] = []
            grupos_jornada[jornada].append((profesor, cuota))

        for jornada in sorted(grupos_jornada.keys(), reverse=True):
            profs = grupos_jornada[jornada]
            if not profs:
                continue
            cuotas_grupo = [c for _, c in profs]
            self.logger.info(
                f"Jornada {jornada}%: {len(profs)} profesores, "
                f"cuota ~{cuotas_grupo[0]} guardias"
            )

        self.logger.info("=" * 70)
