"""
Validador de Guardias - Sistema de Validación Post-Asignación
==============================================================

Valida que las guardias asignadas cumplan todas las restricciones:
- Todos los profesores activos tienen guardias
- Fechas de inicio/fin respetadas al 100%
- Distribución equilibrada según jornada
- Sin guardias durante ausencias
- Sin múltiples guardias por día para un profesor
"""

from collections import defaultdict
from typing import Dict, List

from infrastructure.database.models import Ausencia, Guardia, Profesor
from infrastructure.repositories.repository_factory import RepositoryFactory
from utils import get_logger

logger = get_logger(__name__)


class ResultadoValidacion:
    """Resultado de la validación con métricas y errores."""

    def __init__(self):
        self.errores_criticos: List[str] = []
        self.warnings: List[str] = []
        self.metricas: Dict[str, float] = {}
        self.estado: str = "DESCONOCIDO"  # ÓPTIMO, ACEPTABLE, CRÍTICO

    def es_valido(self) -> bool:
        """Retorna True si no hay errores críticos."""
        return len(self.errores_criticos) == 0

    def agregar_error(self, mensaje: str):
        """Agrega un error crítico."""
        self.errores_criticos.append(mensaje)

    def agregar_warning(self, mensaje: str):
        """Agrega un warning."""
        self.warnings.append(mensaje)

    def calcular_estado(self):
        """Calcula el estado general basado en errores y métricas."""
        if len(self.errores_criticos) > 0:
            self.estado = "CRÍTICO"
        elif len(self.warnings) > 5:
            self.estado = "ACEPTABLE"
        else:
            self.estado = "ÓPTIMO"

    def generar_reporte(self) -> str:
        """Genera un reporte legible."""
        lineas = []
        lineas.append("=" * 80)
        lineas.append("📋 REPORTE DE VALIDACIÓN DE GUARDIAS")
        lineas.append("=" * 80)
        lineas.append("")

        # Métricas
        if self.metricas:
            lineas.append("📊 MÉTRICAS:")
            for key, valor in self.metricas.items():
                if isinstance(valor, float):
                    lineas.append(f"  • {key}: {valor:.2f}")
                else:
                    lineas.append(f"  • {key}: {valor}")
            lineas.append("")

        # Errores críticos
        if self.errores_criticos:
            lineas.append(f"🔴 ERRORES CRÍTICOS ({len(self.errores_criticos)}):")
            for error in self.errores_criticos[:10]:  # Limitar a 10
                lineas.append(f"  ❌ {error}")
            if len(self.errores_criticos) > 10:
                lineas.append(f"  ... y {len(self.errores_criticos) - 10} errores más")
            lineas.append("")

        # Warnings
        if self.warnings:
            lineas.append(f"⚠️  WARNINGS ({len(self.warnings)}):")
            for warning in self.warnings[:10]:  # Limitar a 10
                lineas.append(f"  ⚠️  {warning}")
            if len(self.warnings) > 10:
                lineas.append(f"  ... y {len(self.warnings) - 10} warnings más")
            lineas.append("")

        # Estado
        if self.estado == "ÓPTIMO":
            lineas.append("✅ ESTADO: ÓPTIMO - Todas las restricciones cumplidas")
        elif self.estado == "ACEPTABLE":
            lineas.append("⚠️  ESTADO: ACEPTABLE - Algunos warnings detectados")
        else:
            lineas.append("❌ ESTADO: CRÍTICO - Errores que requieren corrección")

        lineas.append("=" * 80)
        return "\n".join(lineas)


class ValidadorGuardias:
    """Validador completo de guardias asignadas."""

    def __init__(self, session_or_factory):
        self.session = (
            session_or_factory.session
            if isinstance(session_or_factory, RepositoryFactory)
            else session_or_factory
        )

    def validar_todo(
        self, profesores: List[Profesor], cuotas_esperadas: Dict[int, int]
    ) -> ResultadoValidacion:
        """
        Ejecuta todas las validaciones.

        Args:
            profesores: Lista de profesores activos
            cuotas_esperadas: Dict[profesor_id, cuota] con guardias esperadas

        Returns:
            ResultadoValidacion con errores, warnings y métricas
        """
        resultado = ResultadoValidacion()

        logger.info("")
        logger.info("🔍 EJECUTANDO VALIDACIÓN COMPLETA DE GUARDIAS")
        logger.info("=" * 80)

        # 1. Profesores sin guardias
        self._validar_profesores_sin_guardias(profesores, resultado)

        # 2. Cumplimiento de fechas inicio/fin
        self._validar_fechas_inicio_fin(profesores, resultado)

        # 3. Equilibrio de distribución
        self._validar_equilibrio_distribucion(profesores, cuotas_esperadas, resultado)

        # 4. Guardias durante ausencias
        self._validar_ausencias(resultado)

        # 5. Múltiples guardias por día
        self._validar_guardias_por_dia(profesores, resultado)

        # Calcular estado final
        resultado.calcular_estado()

        logger.info("")
        logger.info(resultado.generar_reporte())

        return resultado

    def _validar_profesores_sin_guardias(
        self, profesores: List[Profesor], resultado: ResultadoValidacion
    ):
        """Valida que todos los profesores activos tengan al menos 1 guardia."""
        logger.info("\n1️⃣ Validando profesores sin guardias...")

        guardias_por_profesor = defaultdict(int)
        for guardia in self.session.query(Guardia).all():
            guardias_por_profesor[guardia.profesor_id] += 1

        profesores_sin_guardias = []
        for profesor in profesores:
            if guardias_por_profesor[profesor.id] == 0:
                profesores_sin_guardias.append(profesor)
                resultado.agregar_error(
                    f"Profesor sin guardias: {profesor.nombre_completo} "
                    f"(ID: {profesor.id}, turno: {profesor.turno}, "
                    f"jornada: {profesor.porcentaje_jornada}%)"
                )

        resultado.metricas["profesores_sin_guardias"] = len(profesores_sin_guardias)
        resultado.metricas["profesores_con_guardias"] = len(profesores) - len(
            profesores_sin_guardias
        )

        if profesores_sin_guardias:
            logger.warning(f"  ❌ {len(profesores_sin_guardias)} profesores sin guardias")
        else:
            logger.info("  ✅ Todos los profesores tienen guardias")

    def _validar_fechas_inicio_fin(
        self, profesores: List[Profesor], resultado: ResultadoValidacion
    ):
        """Valida que las guardias respeten fecha_inicio_guardias y fecha_fin_guardias."""
        logger.info("\n2️⃣ Validando cumplimiento de fechas inicio/fin...")

        profesores_con_fecha_inicio = [p for p in profesores if p.fecha_inicio_guardias]

        if not profesores_con_fecha_inicio:
            logger.info("  ℹ️  Ningún profesor tiene fecha_inicio configurada")
            resultado.metricas["cumplimiento_fecha_inicio"] = 100.0
            return

        violaciones_inicio = []
        profesores_sin_guardias_con_fecha = []
        retrasos = []

        for profesor in profesores_con_fecha_inicio:
            guardias = (
                self.session.query(Guardia)
                .filter(Guardia.profesor_id == profesor.id)
                .order_by(Guardia.fecha)
                .all()
            )

            if not guardias:
                profesores_sin_guardias_con_fecha.append(profesor)
                resultado.agregar_error(
                    f"Profesor con fecha_inicio sin guardias: {profesor.nombre_completo} "
                    f"(fecha_inicio: {profesor.fecha_inicio_guardias})"
                )
                continue

            primera_guardia = guardias[0]

            # Verificar si la primera guardia es ANTES de fecha_inicio
            if primera_guardia.fecha < profesor.fecha_inicio_guardias:
                violaciones_inicio.append((profesor, primera_guardia.fecha))
                resultado.agregar_error(
                    f"Guardia ANTES de fecha_inicio: {profesor.nombre_completo} "
                    f"(config: {profesor.fecha_inicio_guardias}, "
                    f"primera: {primera_guardia.fecha})"
                )

            # Verificar si la primera guardia es DESPUÉS de fecha_inicio
            elif primera_guardia.fecha > profesor.fecha_inicio_guardias:
                dias_retraso = (primera_guardia.fecha - profesor.fecha_inicio_guardias).days
                retrasos.append((profesor, primera_guardia.fecha, dias_retraso))
                resultado.agregar_warning(
                    f"Retraso en fecha_inicio: {profesor.nombre_completo} "
                    f"(config: {profesor.fecha_inicio_guardias}, "
                    f"primera: {primera_guardia.fecha}, retraso: {dias_retraso} días)"
                )

            # Verificar fecha_fin si existe
            if profesor.fecha_fin_guardias:
                ultima_guardia = guardias[-1]
                if ultima_guardia.fecha > profesor.fecha_fin_guardias:
                    resultado.agregar_error(
                        f"Guardia DESPUÉS de fecha_fin: {profesor.nombre_completo} "
                        f"(config: {profesor.fecha_fin_guardias}, "
                        f"última: {ultima_guardia.fecha})"
                    )

        # Calcular métricas
        total_con_fecha = len(profesores_con_fecha_inicio)
        cumplen_exactamente = (
            total_con_fecha
            - len(violaciones_inicio)
            - len(retrasos)
            - len(profesores_sin_guardias_con_fecha)
        )

        cumplimiento = (cumplen_exactamente / total_con_fecha * 100) if total_con_fecha > 0 else 100

        resultado.metricas["profesores_con_fecha_inicio"] = total_con_fecha
        resultado.metricas["cumplimiento_fecha_inicio"] = cumplimiento
        resultado.metricas["violaciones_fecha_inicio"] = len(violaciones_inicio)
        resultado.metricas["retrasos_fecha_inicio"] = len(retrasos)

        if retrasos:
            retraso_promedio = sum(r[2] for r in retrasos) / len(retrasos)
            resultado.metricas["retraso_promedio_dias"] = retraso_promedio

        if violaciones_inicio:
            logger.error(f"  ❌ {len(violaciones_inicio)} violaciones de fecha_inicio")
        if retrasos:
            logger.warning(f"  ⚠️  {len(retrasos)} profesores con retraso en fecha_inicio")
        if cumplimiento == 100:
            logger.info("  ✅ 100% cumplimiento de fecha_inicio")
        else:
            logger.warning(f"  ⚠️  {cumplimiento:.1f}% cumplimiento de fecha_inicio")

    def _validar_equilibrio_distribucion(
        self,
        profesores: List[Profesor],
        cuotas_esperadas: Dict[int, int],
        resultado: ResultadoValidacion,
    ):
        """Valida que la distribución sea equilibrada."""
        logger.info("\n3️⃣ Validando equilibrio de distribución...")

        guardias_por_profesor = defaultdict(int)
        for guardia in self.session.query(Guardia).all():
            guardias_por_profesor[guardia.profesor_id] += 1

        desviaciones = []
        profesores_con_desequilibrio = []

        for profesor in profesores:
            cuota_esperada = cuotas_esperadas.get(profesor.id, 0)
            guardias_reales = guardias_por_profesor[profesor.id]

            if cuota_esperada > 0:
                desviacion_pct = abs(guardias_reales - cuota_esperada) / cuota_esperada * 100
                desviaciones.append(desviacion_pct)

                # Desequilibrio >20% es problema
                if desviacion_pct > 20:
                    profesores_con_desequilibrio.append((profesor, guardias_reales, cuota_esperada))
                    resultado.agregar_warning(
                        f"Desequilibrio >20%: {profesor.nombre_completo} "
                        f"(real: {guardias_reales}, esperado: {cuota_esperada}, "
                        f"desv: {desviacion_pct:.1f}%)"
                    )

        # Calcular desviación estándar
        if desviaciones:
            promedio_desv = sum(desviaciones) / len(desviaciones)
            varianza = sum((d - promedio_desv) ** 2 for d in desviaciones) / len(desviaciones)
            desviacion_std = varianza**0.5

            resultado.metricas["desviacion_promedio_pct"] = promedio_desv
            resultado.metricas["desviacion_std_pct"] = desviacion_std
            resultado.metricas["profesores_desequilibrio"] = len(profesores_con_desequilibrio)

            if desviacion_std < 10:
                logger.info(f"  ✅ Buen equilibrio (desv. std: {desviacion_std:.1f}%)")
            elif desviacion_std < 20:
                logger.warning(f"  ⚠️  Equilibrio aceptable (desv. std: {desviacion_std:.1f}%)")
            else:
                logger.error(f"  ❌ Mal equilibrio (desv. std: {desviacion_std:.1f}%)")

    def _validar_ausencias(self, resultado: ResultadoValidacion):
        """Valida que no haya guardias durante ausencias."""
        logger.info("\n4️⃣ Validando guardias durante ausencias...")

        guardias_con_ausencia = []

        for guardia in self.session.query(Guardia).all():
            ausencia = (
                self.session.query(Ausencia)
                .filter(
                    Ausencia.profesor_id == guardia.profesor_id,
                    Ausencia.fecha_inicio <= guardia.fecha,
                    Ausencia.fecha_fin >= guardia.fecha,
                    Ausencia.activa == True,  # noqa: E712
                )
                .first()
            )

            if ausencia:
                profesor = self.session.query(Profesor).get(guardia.profesor_id)
                guardias_con_ausencia.append((profesor, guardia, ausencia))
                resultado.agregar_error(
                    f"Guardia durante ausencia: {profesor.nombre_completo} "
                    f"el {guardia.fecha} (ausencia: {ausencia.tipo}, "
                    f"{ausencia.fecha_inicio} a {ausencia.fecha_fin})"
                )

        resultado.metricas["guardias_durante_ausencia"] = len(guardias_con_ausencia)

        if guardias_con_ausencia:
            logger.error(f"  ❌ {len(guardias_con_ausencia)} guardias durante ausencias")
        else:
            logger.info("  ✅ Sin guardias durante ausencias")

    def _validar_guardias_por_dia(self, profesores: List[Profesor], resultado: ResultadoValidacion):
        """Valida que ningún profesor tenga >1 guardia por día."""
        logger.info("\n5️⃣ Validando múltiples guardias por día...")

        guardias_por_profesor_fecha = defaultdict(int)
        for guardia in self.session.query(Guardia).all():
            key = (guardia.profesor_id, guardia.fecha)
            guardias_por_profesor_fecha[key] += 1

        dias_multiples = []
        for (profesor_id, fecha), count in guardias_por_profesor_fecha.items():
            if count > 1:
                profesor = self.session.query(Profesor).get(profesor_id)
                dias_multiples.append((profesor, fecha, count))
                resultado.agregar_error(
                    f"Múltiples guardias por día: {profesor.nombre_completo} "
                    f"el {fecha} tiene {count} guardias"
                )

        resultado.metricas["dias_multiples_guardias"] = len(dias_multiples)

        if dias_multiples:
            logger.error(f"  ❌ {len(dias_multiples)} días con múltiples guardias")
        else:
            logger.info("  ✅ Sin múltiples guardias por día")


def validar_guardias_completo(
    session_or_factory, profesores: List[Profesor], cuotas_esperadas: Dict[int, int]
) -> ResultadoValidacion:
    """
    Función helper para validar guardias.

    Args:
        session: Sesión de base de datos
        profesores: Lista de profesores activos
        cuotas_esperadas: Dict[profesor_id, cuota] con guardias esperadas

    Returns:
        ResultadoValidacion con estado, errores y métricas
    """
    validador = ValidadorGuardias(session_or_factory)
    return validador.validar_todo(profesores, cuotas_esperadas)
