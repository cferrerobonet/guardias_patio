"""
Asignador de guardias usando Integer Linear Programming (ILP) con OR-Tools.
Implementa la Opción B: solución matemáticamente óptima garantizada.
"""

import logging
import os
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional

# Domain Services (Phase 2.4)
from domain.services.distribucion_cuotas_service import DistribucionCuotasService
from domain.services.equidad_guardias_service import EquidadGuardiasService
from infrastructure.database.models import Configuracion, Guardia, Profesor
from services.validators import TurnoValidator
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Instancia del validador de turnos
_turno_validator = TurnoValidator()

# Importación condicional de OR-Tools
try:
    from ortools.sat.python import cp_model

    ORTOOLS_DISPONIBLE = True
except ImportError:
    ORTOOLS_DISPONIBLE = False
    logger.warning(
        "OR-Tools no está instalado. El asignador ILP no estará disponible. "
        "Instalar con: pip install ortools"
    )


@dataclass
class ResultadoILP:
    """Resultado de la asignación ILP."""

    exitoso: bool
    guardias: List[Guardia]
    estadisticas: Dict
    diagnostico_infactibilidad: Optional[str] = None
    tiempo_solucion_segundos: float = 0.0


class AsignadorILP:
    """
    Asignador de guardias usando Integer Linear Programming.
    Garantiza la solución óptima si existe, o diagnostica por qué no hay solución.
    """

    def __init__(self, db: Session, config: Configuracion, dias_lectivos: List[date]):
        if not ORTOOLS_DISPONIBLE:
            raise ImportError("OR-Tools no está instalado. Instalar con: pip install ortools")

        self.db = db
        self.config = config
        self.dias_lectivos = dias_lectivos

        # Para el modelo
        self.model = None
        self.solver = None
        self.variables = {}

    def generar_guardias_ilp(
        self,
        limite_tiempo_segundos: int = 300,  # 5 minutos por defecto
        priorizar_fecha_inicio: bool = True,
        priorizar_equidad: bool = True,
    ) -> ResultadoILP:
        """
        Genera guardias usando ILP con CP-SAT solver de OR-Tools.

        Args:
            limite_tiempo_segundos: Tiempo máximo de búsqueda
            priorizar_fecha_inicio: Dar peso a cumplir fechas de inicio
            priorizar_equidad: Dar peso a la equidad en la distribución

        Returns:
            ResultadoILP con el resultado de la asignación
        """
        logger.info("=" * 70)
        logger.info("INICIANDO ASIGNACIÓN ILP (Programación Lineal Entera)")
        logger.info("=" * 70)

        import time

        tiempo_inicio = time.time()

        # Crear modelo
        self.model = cp_model.CpModel()

        # Obtener datos
        profesores = self.db.query(Profesor).filter(Profesor.activo.is_(True)).all()
        recreos = self.config.recreos
        zonas = self.config.zonas

        # Calcular cuotas usando Domain Service
        try:
            distribucion_service = DistribucionCuotasService(self.db)
            cuotas = distribucion_service.calcular_cuotas(profesores)
            logger.info("✓ Cuotas calculadas con DistribucionCuotasService (Domain Service)")
        except Exception as e:
            logger.warning(f"⚠️ Error con DistribucionCuotasService: {e}. Usando método legacy.")
            from services.calculador_guardias import calcular_guardias_por_profesor

            cuotas = calcular_guardias_por_profesor(self.db)

        logger.info(f"Profesores activos: {len(profesores)}")
        logger.info(f"Días lectivos: {len(self.dias_lectivos)}")
        logger.info(f"Recreos: {len(recreos)}")
        logger.info(f"Zonas: {len(zonas)}")
        logger.info(f"Slots totales: {len(self.dias_lectivos) * len(recreos) * len(zonas)}")

        # 1. Crear variables de decisión
        logger.info("\n📝 Creando variables de decisión...")
        self._crear_variables_decision(profesores, recreos, zonas)

        # 2. Restricciones DURAS (deben cumplirse siempre)
        logger.info("🔒 Agregando restricciones duras...")
        self._agregar_restricciones_duras(profesores, recreos, zonas)

        # 3. Restricciones SUAVES (preferencias, se optimizan)
        logger.info("⚙️  Agregando restricciones suaves y función objetivo...")
        self._agregar_funcion_objetivo(
            profesores, recreos, zonas, cuotas, priorizar_fecha_inicio, priorizar_equidad
        )

        # 4. Resolver
        logger.info(f"\n🔍 Resolviendo modelo ILP (límite: {limite_tiempo_segundos}s)...")
        self.solver = cp_model.CpSolver()
        self.solver.parameters.max_time_in_seconds = limite_tiempo_segundos
        self.solver.parameters.log_search_progress = True

        # Configurar paralelización para usar todos los cores disponibles
        num_cores = os.cpu_count() or 1
        self.solver.parameters.num_search_workers = num_cores
        logger.info(f"⚡ Usando {num_cores} cores para la búsqueda paralela")

        status = self.solver.Solve(self.model)

        tiempo_total = time.time() - tiempo_inicio

        # 5. Procesar resultado
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            logger.info("✅ Solución encontrada!")
            guardias = self._extraer_guardias_de_solucion(profesores, recreos, zonas)
            estadisticas = self._calcular_estadisticas_solucion(guardias, cuotas)

            if status == cp_model.OPTIMAL:
                logger.info("⭐ Solución ÓPTIMA")
            else:
                logger.info("✔️  Solución FACTIBLE (puede no ser óptima)")

            # Reporte de Equidad usando Domain Service
            logger.info("")
            logger.info("ANÁLISIS DE EQUIDAD (Domain Service)")
            logger.info("=" * 70)

            try:
                equidad_service = EquidadGuardiasService(self.db)

                # Log reporte completo de equidad
                equidad_service.log_reporte_equidad(guardias, cuotas)

                # Calcular índice de equidad
                indice_equidad = equidad_service.calcular_indice_equidad(guardias, cuotas)
                logger.info(f"📊 Índice de Equidad Global: {indice_equidad:.2%}")

                # Identificar desbalances
                desbalances = equidad_service.identificar_desbalances(guardias, cuotas)
                if desbalances:
                    logger.warning(f"⚠️  Desbalances detectados: {len(desbalances)}")
                else:
                    logger.info("✅ Sin desbalances significativos")

            except Exception as e:
                logger.warning(f"⚠️  Error en análisis de equidad: {e}")

            logger.info("=" * 70)

            return ResultadoILP(
                exitoso=True,
                guardias=guardias,
                estadisticas=estadisticas,
                tiempo_solucion_segundos=tiempo_total,
            )

        else:
            # No hay solución
            logger.error("❌ No se encontró solución")
            diagnostico = self._diagnosticar_infactibilidad(status, profesores, recreos, zonas)

            return ResultadoILP(
                exitoso=False,
                guardias=[],
                estadisticas={},
                diagnostico_infactibilidad=diagnostico,
                tiempo_solucion_segundos=tiempo_total,
            )

    def _crear_variables_decision(self, profesores: List[Profesor], recreos, zonas):
        """
        Crea variables de decisión x[p][d][r][z] que vale 1 si el profesor p
        está asignado al día d, recreo r, zona z.
        """
        self.variables = {}

        for profesor in profesores:
            self.variables[profesor.id] = {}
            for dia in self.dias_lectivos:
                self.variables[profesor.id][dia] = {}
                for recreo in recreos:
                    self.variables[profesor.id][dia][recreo.numero] = {}
                    for zona in zonas:
                        # Variable booleana
                        var = self.model.NewBoolVar(
                            f"x_p{profesor.id}_d{dia}_r{recreo.numero}_z{zona.id}"
                        )
                        self.variables[profesor.id][dia][recreo.numero][zona.id] = var

        logger.info(
            f"Variables creadas: {len(profesores)} × {len(self.dias_lectivos)} × {len(recreos)} × {len(zonas)}"
        )

    def _agregar_restricciones_duras(self, profesores: List[Profesor], recreos, zonas):
        """Agrega restricciones que DEBEN cumplirse."""

        # R1: Cada slot (día, recreo, zona) debe tener exactamente 1 profesor
        logger.info("  • R1: Cobertura 100% (1 profesor por slot)")
        for dia in self.dias_lectivos:
            for recreo in recreos:
                for zona in zonas:
                    # Suma de todos los profesores en este slot = 1
                    self.model.Add(
                        sum(
                            self.variables[p.id][dia][recreo.numero][zona.id]
                            for p in profesores
                            if self._profesor_compatible_slot(p, dia, recreo, zona)
                        )
                        == 1
                    )

        # R2: Un profesor no puede estar en dos zonas el mismo recreo del mismo día
        logger.info("  • R2: Máximo 1 guardia por profesor por recreo")
        for profesor in profesores:
            for dia in self.dias_lectivos:
                for recreo in recreos:
                    self.model.Add(
                        sum(
                            self.variables[profesor.id][dia][recreo.numero][zona.id]
                            for zona in zonas
                        )
                        <= 1
                    )

        # R3: Respetar ausencias
        logger.info("  • R3: Respeto de ausencias")
        for profesor in profesores:
            if hasattr(profesor, "ausencias") and profesor.ausencias:
                for ausencia in profesor.ausencias:
                    # Iterar sobre todas las fechas en el rango de la ausencia
                    for dia in self.dias_lectivos:
                        # Verificar si el día cae dentro del rango de ausencia
                        if ausencia.fecha_inicio <= dia <= ausencia.fecha_fin:
                            for recreo in recreos:
                                for zona in zonas:
                                    self.model.Add(
                                        self.variables[profesor.id][dia][recreo.numero][zona.id]
                                        == 0
                                    )

        # R4: Respetar incompatibilidades de turno
        logger.info("  • R4: Compatibilidad de turnos")
        for profesor in profesores:
            # Un profesor puede hacer guardias de un turno si:
            # - su turno es "completo" o "mixto" (pueden ambos turnos)
            # - su turno coincide con el turno del recreo
            for dia in self.dias_lectivos:
                for recreo in recreos:
                    puede_hacer_turno = (
                        profesor.turno in ("completo", "mixto") or profesor.turno == recreo.turno
                    )
                    if not puede_hacer_turno:
                        for zona in zonas:
                            self.model.Add(
                                self.variables[profesor.id][dia][recreo.numero][zona.id] == 0
                            )

        # R5: Priorizar zona preferida (los profesores pueden trabajar en todas las zonas)
        logger.info("  • R5: Priorización de zona preferida")
        # NOTA: Los profesores pueden trabajar en TODAS las zonas activas
        # Solo tienen una zona_preferida_id que el sistema debería priorizar
        # pero NO es una restricción obligatoria
        # Por ahora, no añadimos restricciones de zona incompatible
        # TODO: Implementar soft constraint para priorizar zona preferida

        # Placeholder: anteriormente se aplicaba restricción incorrecta
        # que bloqueaba zonas, pero profesor.zonas no existe en el modelo

        # R6: No exceder guardias máximas por día (si está configurado)
        max_guardias_dia = getattr(self.config, "max_guardias_por_dia", 2)
        logger.info(f"  • R6: Máximo {max_guardias_dia} guardias por profesor por día")
        for profesor in profesores:
            for dia in self.dias_lectivos:
                self.model.Add(
                    sum(
                        self.variables[profesor.id][dia][recreo.numero][zona.id]
                        for recreo in recreos
                        for zona in zonas
                    )
                    <= max_guardias_dia
                )

    def _agregar_funcion_objetivo(
        self,
        profesores: List[Profesor],
        recreos,
        zonas,
        cuotas: Dict[int, int],
        priorizar_fecha_inicio: bool,
        priorizar_equidad: bool,
    ):
        """
        Define la función objetivo que se maximiza.
        Combina múltiples objetivos con pesos.
        """
        objetivo_terminos = []

        # Objetivo 1: Minimizar desviación de cuotas (EQUIDAD)
        if priorizar_equidad:
            logger.info("  • Objetivo: Minimizar desviación de cuotas")
            for profesor in profesores:
                cuota_esperada = cuotas.get(profesor.id, 0)
                guardias_asignadas = sum(
                    self.variables[profesor.id][dia][recreo.numero][zona.id]
                    for dia in self.dias_lectivos
                    for recreo in recreos
                    for zona in zonas
                )

                # Variable auxiliar para la desviación absoluta
                desviacion_pos = self.model.NewIntVar(0, 1000, f"dev_pos_p{profesor.id}")
                desviacion_neg = self.model.NewIntVar(0, 1000, f"dev_neg_p{profesor.id}")

                self.model.Add(
                    guardias_asignadas - cuota_esperada == desviacion_pos - desviacion_neg
                )

                # Penalizar desviación (peso negativo = minimizar)
                objetivo_terminos.append(-10 * desviacion_pos)
                objetivo_terminos.append(-10 * desviacion_neg)

        # Objetivo 2: Priorizar cumplimiento de fecha_inicio
        if priorizar_fecha_inicio:
            logger.info("  • Objetivo: Priorizar fechas de inicio tempranas")
            for profesor in profesores:
                if (
                    profesor.fecha_inicio_guardias
                    and profesor.fecha_inicio_guardias in self.dias_lectivos
                ):
                    idx_inicio = self.dias_lectivos.index(profesor.fecha_inicio_guardias)

                    # Premiar guardias cercanas a la fecha de inicio
                    for i, dia in enumerate(self.dias_lectivos):
                        if i >= idx_inicio:
                            dias_desde_inicio = i - idx_inicio
                            peso = max(0, 50 - dias_desde_inicio)  # Más peso cuanto más cerca

                            for recreo in recreos:
                                for zona in zonas:
                                    objetivo_terminos.append(
                                        peso
                                        * self.variables[profesor.id][dia][recreo.numero][zona.id]
                                    )

        # Objetivo 3: Favorecer fechas consecutivas (agrupamiento)
        logger.info("  • Objetivo: Favorecer guardias consecutivas")
        for profesor in profesores:
            for i in range(len(self.dias_lectivos) - 1):
                dia_actual = self.dias_lectivos[i]
                dia_siguiente = self.dias_lectivos[i + 1]

                # Si hay guardia hoy Y mañana, sumar bonus
                for recreo in recreos:
                    tiene_hoy = sum(
                        self.variables[profesor.id][dia_actual][recreo.numero][zona.id]
                        for zona in zonas
                    )
                    tiene_manana = sum(
                        self.variables[profesor.id][dia_siguiente][recreo.numero][zona.id]
                        for zona in zonas
                    )

                    # Variable para detectar ambos días
                    ambos_dias = self.model.NewBoolVar(
                        f"consec_p{profesor.id}_d{i}_r{recreo.numero}"
                    )
                    self.model.AddMultiplicationEquality(ambos_dias, [tiene_hoy, tiene_manana])

                    # Bonus por consecutivos
                    objetivo_terminos.append(5 * ambos_dias)

        # Maximizar objetivo total
        if objetivo_terminos:
            self.model.Maximize(sum(objetivo_terminos))

    def _profesor_compatible_slot(self, profesor: Profesor, dia: date, recreo, zona) -> bool:
        """Verifica si un profesor es compatible con un slot."""
        # Verificar ausencias (chequear si el día cae en el rango de alguna ausencia)
        if hasattr(profesor, "ausencias") and profesor.ausencias:
            for ausencia in profesor.ausencias:
                if ausencia.fecha_inicio <= dia <= ausencia.fecha_fin:
                    return False

        # Verificar turno
        puede_hacer_turno = (
            profesor.turno in ("completo", "mixto") or profesor.turno == recreo.turno
        )
        if not puede_hacer_turno:
            return False

        # Verificar zona: Los profesores pueden trabajar en TODAS las zonas
        # No hay restricción de zona (profesor.zonas no existe en el modelo)
        # Solo hay zona_preferida que es una preferencia suave

        return True

    def _extraer_guardias_de_solucion(
        self, profesores: List[Profesor], recreos, zonas
    ) -> List[Guardia]:
        """Extrae las guardias de la solución del solver."""
        guardias = []

        for profesor in profesores:
            for dia in self.dias_lectivos:
                for recreo in recreos:
                    for zona in zonas:
                        var = self.variables[profesor.id][dia][recreo.numero][zona.id]
                        if self.solver.Value(var) == 1:
                            guardia = Guardia(
                                profesor_id=profesor.id,
                                fecha=dia,
                                recreo=recreo.numero,
                                zona=zona.id,
                                turno=recreo.turno,
                            )
                            guardias.append(guardia)

        logger.info(f"✅ Extraídas {len(guardias)} guardias de la solución")
        return guardias

    def _calcular_estadisticas_solucion(
        self, guardias: List[Guardia], cuotas: Dict[int, int]
    ) -> Dict:
        """Calcula estadísticas de la solución."""
        total_slots = len(self.dias_lectivos) * len(self.config.recreos) * len(self.config.zonas)

        guardias_por_profesor = {}
        for guardia in guardias:
            guardias_por_profesor[guardia.profesor_id] = (
                guardias_por_profesor.get(guardia.profesor_id, 0) + 1
            )

        # Desviaciones de cuota
        desviaciones = []
        for prof_id, cuota_esperada in cuotas.items():
            guardias_reales = guardias_por_profesor.get(prof_id, 0)
            if cuota_esperada > 0:
                desv = abs(guardias_reales - cuota_esperada) / cuota_esperada
                desviaciones.append(desv)

        return {
            "total_guardias": len(guardias),
            "total_slots": total_slots,
            "cobertura": len(guardias) / total_slots if total_slots > 0 else 0,
            "profesores_con_guardias": len(guardias_por_profesor),
            "desviacion_cuota_promedio": sum(desviaciones) / len(desviaciones)
            if desviaciones
            else 0,
            "desviacion_cuota_maxima": max(desviaciones) if desviaciones else 0,
            "tiempo_solucion": self.solver.WallTime(),
        }

    def _diagnosticar_infactibilidad(
        self, status, profesores: List[Profesor], recreos, zonas
    ) -> str:
        """
        Intenta diagnosticar por qué el modelo es infactible.
        """
        lineas = []
        lineas.append("=" * 70)
        lineas.append("DIAGNÓSTICO DE INFACTIBILIDAD")
        lineas.append("=" * 70)

        if status == cp_model.INFEASIBLE:
            lineas.append("\n❌ El problema es INFACTIBLE")
            lineas.append("   No existe ninguna asignación que cumpla TODAS las restricciones.")
        elif status == cp_model.MODEL_INVALID:
            lineas.append("\n⚠️  El modelo tiene errores")
        else:
            lineas.append(f"\n⏱️  Tiempo agotado (status: {status})")
            lineas.append("   No se pudo encontrar solución en el tiempo límite.")

        lineas.append("\nPosibles causas:")

        # Analizar capacidad
        total_slots = len(self.dias_lectivos) * len(recreos) * len(zonas)
        slots_por_turno = {}
        for dia in self.dias_lectivos:
            for recreo in recreos:
                turno = recreo.turno
                slots_por_turno[turno] = slots_por_turno.get(turno, 0) + len(zonas)

        lineas.append(f"\n1. Capacidad total necesaria: {total_slots} slots")

        for turno, slots in slots_por_turno.items():
            # Contar profesores disponibles en este turno usando el validador
            profs_disponibles = _turno_validator.contar_profesores_por_turno(profesores, turno)

            lineas.append(
                f"   • Turno '{turno}': {slots} slots, {profs_disponibles} profesores disponibles"
            )

            if profs_disponibles == 0:
                lineas.append(f"     ❌ CRÍTICO: No hay profesores para turno '{turno}'")

        # Analizar zonas (NOTA: Todos los profesores pueden trabajar en todas las zonas)
        lineas.append("\n2. Análisis de zonas:")
        total_profesores_activos = len([p for p in profesores if p.activo])
        lineas.append(f"   • Total de zonas: {len(zonas)}")
        lineas.append(f"   • Profesores activos: {total_profesores_activos}")
        lineas.append("   • Nota: Los profesores pueden trabajar en TODAS las zonas activas")

        if total_profesores_activos == 0:
            lineas.append("     ❌ CRÍTICO: No hay profesores activos en el sistema")

        lineas.append("\n3. Causas más comunes:")
        lineas.append("   • Profesores insuficientes para cubrir todos los slots")
        lineas.append("   • Mismatch entre turnos de profesores y recreos")
        lineas.append("   • Demasiadas ausencias que impiden cobertura completa")
        lineas.append("   • Max guardias/día muy restrictivo")
        lineas.append("\n4. Sugerencias:")
        lineas.append("   ✓ Verificar que hay suficientes profesores activos")
        lineas.append("   ✓ Revisar que los turnos de profesores coinciden con los de recreos")
        lineas.append(
            "   ✓ Verificar ausencias (especialmente si muchos profesores ausentes el mismo día)"
        )
        lineas.append("   ✓ Considerar aumentar max_guardias_por_dia en configuración")
        lineas.append("   ✓ Como última opción: reducir número de zonas por recreo")

        lineas.append("=" * 70)

        return "\n".join(lineas)
