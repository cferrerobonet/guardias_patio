"""
Diagnosticador de problemas en la asignación de guardias.
Analiza las causas raíz de fallos y genera reportes detallados para el usuario.
"""

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from infrastructure.database.models import Configuracion, Guardia, Profesor
from infrastructure.repositories.repository_factory import RepositoryFactory
from services.validators import TurnoValidator
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

# Instancia del validador de turnos
_turno_validator = TurnoValidator()


@dataclass
class ProblemaDetectado:
    """Representa un problema específico detectado."""

    tipo: str  # 'profesor_sin_guardias', 'fecha_inicio_incumplida', 'slot_vacio', etc.
    gravedad: str  # 'CRITICA', 'ALTA', 'MEDIA', 'BAJA'
    descripcion: str  # Descripción clara para el usuario
    detalles: Dict  # Datos específicos del problema
    sugerencias: List[str]  # Acciones que el usuario puede tomar


@dataclass
class DiagnosticoCompleto:
    """Resultado completo del diagnóstico."""

    problemas_criticos: List[ProblemaDetectado]
    problemas_altos: List[ProblemaDetectado]
    problemas_medios: List[ProblemaDetectado]
    estadisticas: Dict
    puede_continuar_ilp: bool
    mensaje_resumen: str


class DiagnosticadorGuardias:
    """Analiza problemas en la asignación y genera diagnósticos detallados."""

    def __init__(self, db, config: Configuracion, dias_lectivos: List[date]):
        self.db = (
            db.session
            if isinstance(db, RepositoryFactory)
            else db
        )
        self.config = config
        self.dias_lectivos = dias_lectivos

    def diagnosticar_resultado(self, guardias_asignadas: List[Guardia]) -> DiagnosticoCompleto:
        """
        Analiza el resultado de una asignación y genera diagnóstico completo.
        """
        problemas_criticos = []
        problemas_altos = []
        problemas_medios = []

        # 1. Profesores sin guardias
        problemas_criticos.extend(self._diagnosticar_profesores_sin_guardias(guardias_asignadas))

        # 2. Slots vacíos por turno/zona/día
        problemas_criticos.extend(self._diagnosticar_slots_vacios(guardias_asignadas))

        # 3. Fechas de inicio incumplidas
        problemas_altos.extend(self._diagnosticar_fechas_inicio(guardias_asignadas))

        # 4. Cuotas incompletas
        problemas_altos.extend(self._diagnosticar_cuotas_incompletas(guardias_asignadas))

        # 5. Desbalances significativos
        problemas_medios.extend(self._diagnosticar_desbalances(guardias_asignadas))

        # Estadísticas generales
        estadisticas = self._calcular_estadisticas(guardias_asignadas)

        # Decidir si puede continuar con ILP
        puede_continuar_ilp = len(problemas_criticos) > 0 or len(problemas_altos) > 3

        # Mensaje resumen
        mensaje_resumen = self._generar_mensaje_resumen(
            problemas_criticos, problemas_altos, problemas_medios, estadisticas
        )

        return DiagnosticoCompleto(
            problemas_criticos=problemas_criticos,
            problemas_altos=problemas_altos,
            problemas_medios=problemas_medios,
            estadisticas=estadisticas,
            puede_continuar_ilp=puede_continuar_ilp,
            mensaje_resumen=mensaje_resumen,
        )

    def _diagnosticar_profesores_sin_guardias(
        self, guardias: List[Guardia]
    ) -> List[ProblemaDetectado]:
        """Detecta profesores activos sin guardias asignadas."""
        problemas = []

        profesores_activos = (
            self.db.query(Profesor)
            .options(joinedload(Profesor.zona_preferida))
            .filter(Profesor.activo)
            .all()
        )

        profesores_con_guardias = {g.profesor_id for g in guardias}
        profesores_sin_guardias = [
            p for p in profesores_activos if p.id not in profesores_con_guardias
        ]

        if profesores_sin_guardias:
            # Agrupar por turno para diagnóstico más específico
            por_turno = {}
            for prof in profesores_sin_guardias:
                # Determinar qué turnos puede hacer el profesor
                if prof.turno in ("completo", "mixto"):
                    turnos = ["mañana", "tarde"]
                else:
                    turnos = [prof.turno]
                for turno in turnos:
                    por_turno.setdefault(turno, []).append(prof)

            for turno, profs in por_turno.items():
                # Analizar causas: ¿faltan slots? ¿incompatibilidades?
                causas = self._analizar_causas_sin_guardias(profs, turno)

                problema = ProblemaDetectado(
                    tipo="profesor_sin_guardias",
                    gravedad="CRITICA",
                    descripcion=f"{len(profs)} profesor(es) sin guardias en turno '{turno}'",
                    detalles={
                        "turno": turno,
                        "profesores": [{"nombre": p.nombre_completo, "id": p.id} for p in profs],
                        "causas": causas,
                    },
                    sugerencias=self._generar_sugerencias_profesores_sin_guardias(causas, turno),
                )
                problemas.append(problema)

        return problemas

    def _diagnosticar_slots_vacios(self, guardias: List[Guardia]) -> List[ProblemaDetectado]:
        """Detecta slots sin cubrir por día/recreo/zona."""
        problemas = []

        # Calcular slots totales esperados
        total_dias = len(self.dias_lectivos)
        recreos = self.config.recreos
        zonas = self.config.zonas

        slots_esperados = total_dias * len(recreos) * len(zonas)
        slots_cubiertos = len(guardias)
        slots_vacios = slots_esperados - slots_cubiertos

        if slots_vacios > 0:
            # Análisis detallado: ¿dónde están los huecos?
            huecos_detallados = self._analizar_slots_vacios_detalle(guardias)

            problema = ProblemaDetectado(
                tipo="slots_vacios",
                gravedad="CRITICA",
                descripcion=f"{slots_vacios} slots sin cubrir ({(slots_vacios / slots_esperados) * 100:.1f}% del total)",
                detalles={
                    "slots_vacios": slots_vacios,
                    "slots_esperados": slots_esperados,
                    "cobertura_porcentaje": (slots_cubiertos / slots_esperados) * 100,
                    "huecos_por_turno": huecos_detallados["por_turno"],
                    "huecos_por_zona": huecos_detallados["por_zona"],
                    "dias_problematicos": huecos_detallados["dias_criticos"],
                },
                sugerencias=self._generar_sugerencias_slots_vacios(huecos_detallados),
            )
            problemas.append(problema)

        return problemas

    def _diagnosticar_fechas_inicio(self, guardias: List[Guardia]) -> List[ProblemaDetectado]:
        """Detecta profesores con retraso en fecha_inicio."""
        problemas = []

        profesores_con_guardias = {}
        for guardia in guardias:
            if guardia.profesor_id not in profesores_con_guardias:
                profesores_con_guardias[guardia.profesor_id] = []
            profesores_con_guardias[guardia.profesor_id].append(guardia.fecha)

        profesores_retrasados = []
        for profesor_id, fechas in profesores_con_guardias.items():
            profesor = self.db.query(Profesor).get(profesor_id)
            if profesor and profesor.fecha_inicio_guardias:
                primera_guardia = min(fechas)
                if primera_guardia > profesor.fecha_inicio_guardias:
                    dias_retraso = (primera_guardia - profesor.fecha_inicio_guardias).days
                    profesores_retrasados.append(
                        {
                            "profesor": profesor,
                            "fecha_inicio_esperada": profesor.fecha_inicio_guardias,
                            "primera_guardia": primera_guardia,
                            "dias_retraso": dias_retraso,
                        }
                    )

        if profesores_retrasados:
            # Agrupar por nivel de retraso
            retrasos_criticos = [p for p in profesores_retrasados if p["dias_retraso"] > 60]
            [p for p in profesores_retrasados if 30 < p["dias_retraso"] <= 60]

            if retrasos_criticos:
                problema = ProblemaDetectado(
                    tipo="fecha_inicio_incumplida",
                    gravedad="ALTA",
                    descripcion=f"{len(retrasos_criticos)} profesor(es) con retraso >60 días en fecha inicio",
                    detalles={
                        "profesores_retrasados": [
                            {
                                "nombre": p["profesor"].nombre_completo,
                                "fecha_inicio": p["fecha_inicio_esperada"].isoformat(),
                                "primera_guardia": p["primera_guardia"].isoformat(),
                                "dias_retraso": p["dias_retraso"],
                            }
                            for p in retrasos_criticos
                        ],
                        "retraso_promedio": sum(p["dias_retraso"] for p in retrasos_criticos)
                        / len(retrasos_criticos),
                    },
                    sugerencias=[
                        "Revisar si hay suficientes slots disponibles en las primeras semanas del curso",
                        "Verificar disponibilidades de profesores en fechas tempranas",
                        "Considerar aumentar prioridad de profesores con fecha_inicio temprana",
                    ],
                )
                problemas.append(problema)

        return problemas

    def _diagnosticar_cuotas_incompletas(self, guardias: List[Guardia]) -> List[ProblemaDetectado]:
        """Detecta profesores que no alcanzan su cuota mínima."""
        problemas = []

        # Calcular cuotas esperadas
        # Importar función de calculador
        from services.calculador_guardias import calcular_guardias_por_profesor

        cuotas = calcular_guardias_por_profesor(self.db)

        # Contar guardias reales por profesor
        guardias_reales = {}
        for guardia in guardias:
            guardias_reales[guardia.profesor_id] = guardias_reales.get(guardia.profesor_id, 0) + 1

        profesores_deficit = []
        for profesor_id, cuota_esperada in cuotas.items():
            guardias_asignadas = guardias_reales.get(profesor_id, 0)
            deficit = cuota_esperada - guardias_asignadas

            if deficit > cuota_esperada * 0.2:  # Más de 20% de déficit
                profesor = self.db.query(Profesor).get(profesor_id)
                profesores_deficit.append(
                    {
                        "profesor": profesor,
                        "esperadas": cuota_esperada,
                        "asignadas": guardias_asignadas,
                        "deficit": deficit,
                        "deficit_porcentaje": (deficit / cuota_esperada) * 100,
                    }
                )

        if profesores_deficit:
            problema = ProblemaDetectado(
                tipo="cuota_incompleta",
                gravedad="ALTA",
                descripcion=f"{len(profesores_deficit)} profesor(es) con déficit >20% en su cuota",
                detalles={
                    "profesores": [
                        {
                            "nombre": p["profesor"].nombre_completo,
                            "esperadas": p["esperadas"],
                            "asignadas": p["asignadas"],
                            "deficit": p["deficit"],
                            "deficit_porcentaje": p["deficit_porcentaje"],
                        }
                        for p in profesores_deficit[:10]  # Mostrar solo los 10 primeros
                    ],
                    "total_afectados": len(profesores_deficit),
                },
                sugerencias=[
                    "Verificar disponibilidades de estos profesores (pueden tener muchas ausencias)",
                    "Revisar si hay incompatibilidades de zonas o turnos",
                    "Considerar si las restricciones son demasiado estrictas",
                ],
            )
            problemas.append(problema)

        return problemas

    def _diagnosticar_desbalances(self, guardias: List[Guardia]) -> List[ProblemaDetectado]:
        """Detecta desbalances significativos en la distribución."""
        problemas = []

        # Analizar distribución por zona
        guardias_por_zona = {}
        for guardia in guardias:
            guardias_por_zona[guardia.zona] = guardias_por_zona.get(guardia.zona, 0) + 1

        if guardias_por_zona:
            promedio = sum(guardias_por_zona.values()) / len(guardias_por_zona)
            zonas_desbalanceadas = []

            for zona, cantidad in guardias_por_zona.items():
                desviacion = abs(cantidad - promedio) / promedio
                if desviacion > 0.3:  # Más de 30% de desviación
                    zonas_desbalanceadas.append(
                        {
                            "zona": zona,
                            "cantidad": cantidad,
                            "promedio": promedio,
                            "desviacion_porcentaje": desviacion * 100,
                        }
                    )

            if zonas_desbalanceadas:
                problema = ProblemaDetectado(
                    tipo="desbalance_zonas",
                    gravedad="MEDIA",
                    descripcion=f"{len(zonas_desbalanceadas)} zona(s) con desbalance >30%",
                    detalles={"zonas": zonas_desbalanceadas},
                    sugerencias=[
                        "Revisar disponibilidad de profesores por zona",
                        "Verificar si algunas zonas tienen restricciones muy estrictas",
                    ],
                )
                problemas.append(problema)

        return problemas

    def _analizar_causas_sin_guardias(self, profesores: List[Profesor], turno: str) -> Dict:
        """Analiza por qué un grupo de profesores no tiene guardias."""
        causas = {
            "slots_insuficientes": False,
            "ausencias_excesivas": [],
            "incompatibilidades_zona": [],
            "sin_disponibilidad_turno": [],
        }

        # Calcular slots disponibles en ese turno
        recreos_turno = [r for r in self.config.recreos if r.turno == turno]
        slots_disponibles = len(self.dias_lectivos) * len(recreos_turno) * len(self.config.zonas)

        profesores_turno = (
            self.db.query(Profesor)
            .filter(
                Profesor.activo,
                # Filtrar profesores que pueden hacer este turno
                # (turno completo/mixto pueden ambos, o turno específico coincide)
                or_(Profesor.turno.in_(["completo", "mixto"]), Profesor.turno == turno),
            )
            .count()
        )

        if slots_disponibles < profesores_turno:
            causas["slots_insuficientes"] = True

        # Analizar cada profesor
        for prof in profesores:
            # Verificar ausencias
            if hasattr(prof, "ausencias") and prof.ausencias:
                ausencias_count = len(prof.ausencias)
                if ausencias_count > len(self.dias_lectivos) * 0.5:
                    causas["ausencias_excesivas"].append(
                        {
                            "nombre": prof.nombre_completo,
                            "ausencias": ausencias_count,
                            "dias_totales": len(self.dias_lectivos),
                        }
                    )

            # Verificar zonas: Los profesores pueden trabajar en TODAS las zonas
            # No hay restricción (profesor.zonas no existe)
            # Solo hay zona_preferida que es preferencia, no restricción

            # Verificar turno
            # Verificar si el profesor puede hacer este turno
            puede_turno = prof.turno in ("completo", "mixto") or prof.turno == turno
            if not puede_turno:
                causas["sin_disponibilidad_turno"].append(prof.nombre_completo)

        return causas

    def _analizar_slots_vacios_detalle(self, guardias: List[Guardia]) -> Dict:
        """Análisis detallado de dónde están los slots vacíos."""
        # Crear estructura de slots esperados
        slots_esperados = set()
        for dia in self.dias_lectivos:
            for recreo in self.config.recreos:
                for zona in self.config.zonas:
                    slots_esperados.add((dia, recreo.numero, zona.id))

        # Marcar slots cubiertos
        slots_cubiertos = set()
        for guardia in guardias:
            slots_cubiertos.add((guardia.fecha, guardia.recreo, guardia.zona))

        # Calcular vacíos
        slots_vacios = slots_esperados - slots_cubiertos

        # Agrupar por turno
        huecos_por_turno = {}
        for dia, recreo_num, zona_id in slots_vacios:
            recreo = next(r for r in self.config.recreos if r.numero == recreo_num)
            turno = recreo.turno
            huecos_por_turno[turno] = huecos_por_turno.get(turno, 0) + 1

        # Agrupar por zona
        huecos_por_zona = {}
        for dia, recreo_num, zona_id in slots_vacios:
            zona = next(z for z in self.config.zonas if z.id == zona_id)
            huecos_por_zona[zona.nombre] = huecos_por_zona.get(zona.nombre, 0) + 1

        # Identificar días críticos (con muchos huecos)
        huecos_por_dia = {}
        for dia, recreo_num, zona_id in slots_vacios:
            huecos_por_dia[dia] = huecos_por_dia.get(dia, 0) + 1

        dias_criticos = sorted(
            [(dia, count) for dia, count in huecos_por_dia.items()],
            key=lambda x: x[1],
            reverse=True,
        )[:5]  # Top 5 días con más huecos

        return {
            "por_turno": huecos_por_turno,
            "por_zona": huecos_por_zona,
            "dias_criticos": [(dia.isoformat(), count) for dia, count in dias_criticos],
        }

    def _generar_sugerencias_profesores_sin_guardias(self, causas: Dict, turno: str) -> List[str]:
        """Genera sugerencias específicas basadas en las causas detectadas."""
        sugerencias = []

        if causas["slots_insuficientes"]:
            sugerencias.append(
                f"⚠️ CRÍTICO: No hay suficientes slots en turno '{turno}' para todos los profesores. "
                "Opciones: a) Añadir más recreos en este turno, b) Reducir número de zonas, "
                "c) Desactivar algunos profesores de este turno"
            )

        if causas["ausencias_excesivas"]:
            nombres = [a["nombre"] for a in causas["ausencias_excesivas"][:3]]
            sugerencias.append(
                f"Profesores con excesivas ausencias: {', '.join(nombres)}. "
                "Revisar y reducir sus ausencias en el calendario si es posible."
            )

        if causas["incompatibilidades_zona"]:
            sugerencias.append(
                f"{len(causas['incompatibilidades_zona'])} profesor(es) sin zonas asignadas. "
                "Asignar al menos una zona a cada profesor activo."
            )

        if causas["sin_disponibilidad_turno"]:
            sugerencias.append(
                f"{len(causas['sin_disponibilidad_turno'])} profesor(es) marcados como activos "
                f"pero sin disponibilidad en turno '{turno}'. Revisar configuración de turnos."
            )

        if not sugerencias:
            sugerencias.append(
                "No se detectaron causas obvias. Revisar manualmente disponibilidades, "
                "ausencias y compatibilidades de estos profesores."
            )

        return sugerencias

    def _generar_sugerencias_slots_vacios(self, huecos: Dict) -> List[str]:
        """Genera sugerencias para cubrir slots vacíos."""
        sugerencias = []

        # Identificar turno más problemático
        if huecos["por_turno"]:
            turno_peor = max(huecos["por_turno"].items(), key=lambda x: x[1])
            sugerencias.append(
                f"Turno '{turno_peor[0]}' tiene {turno_peor[1]} slots vacíos. "
                "Verificar que hay suficientes profesores activos y disponibles en este turno."
            )

        # Identificar zona más problemática
        if huecos["por_zona"]:
            zona_peor = max(huecos["por_zona"].items(), key=lambda x: x[1])
            sugerencias.append(
                f"Zona '{zona_peor[0]}' tiene {zona_peor[1]} slots vacíos. "
                "Asignar más profesores compatibles con esta zona."
            )

        # Días críticos
        if huecos["dias_criticos"]:
            sugerencias.append(
                f"Días con más huecos: {', '.join(str(d[0]) for d in huecos['dias_criticos'][:3])}. "
                "Revisar si hay eventos especiales o ausencias masivas en estas fechas."
            )

        return sugerencias

    def _calcular_estadisticas(self, guardias: List[Guardia]) -> Dict:
        """Calcula estadísticas generales del resultado."""
        total_dias = len(self.dias_lectivos)
        total_slots = total_dias * len(self.config.recreos) * len(self.config.zonas)

        profesores_con_guardias = len(set(g.profesor_id for g in guardias))
        profesores_activos = self.db.query(Profesor).filter(Profesor.activo).count()

        return {
            "total_guardias_asignadas": len(guardias),
            "total_slots_esperados": total_slots,
            "cobertura_porcentaje": (len(guardias) / total_slots * 100) if total_slots > 0 else 0,
            "profesores_con_guardias": profesores_con_guardias,
            "profesores_activos_totales": profesores_activos,
            "participacion_porcentaje": (profesores_con_guardias / profesores_activos * 100)
            if profesores_activos > 0
            else 0,
        }

    def _generar_mensaje_resumen(
        self,
        criticos: List[ProblemaDetectado],
        altos: List[ProblemaDetectado],
        medios: List[ProblemaDetectado],
        stats: Dict,
    ) -> str:
        """Genera mensaje resumen para el usuario."""
        lineas = []

        lineas.append("=" * 70)
        lineas.append("DIAGNÓSTICO DE ASIGNACIÓN DE GUARDIAS")
        lineas.append("=" * 70)
        lineas.append("")

        # Estadísticas
        lineas.append("📊 ESTADÍSTICAS GENERALES:")
        lineas.append(
            f"  • Guardias asignadas: {stats['total_guardias_asignadas']} de {stats['total_slots_esperados']}"
        )
        lineas.append(f"  • Cobertura: {stats['cobertura_porcentaje']:.1f}%")
        lineas.append(
            f"  • Profesores participantes: {stats['profesores_con_guardias']} de {stats['profesores_activos_totales']}"
        )
        lineas.append("")

        # Problemas críticos
        if criticos:
            lineas.append("🔴 PROBLEMAS CRÍTICOS:")
            for p in criticos:
                lineas.append(f"  • {p.descripcion}")
            lineas.append("")

        # Problemas altos
        if altos:
            lineas.append("🟠 PROBLEMAS IMPORTANTES:")
            for p in altos:
                lineas.append(f"  • {p.descripcion}")
            lineas.append("")

        # Problemas medios
        if medios:
            lineas.append("🟡 PROBLEMAS MENORES:")
            for p in medios:
                lineas.append(f"  • {p.descripcion}")
            lineas.append("")

        # Conclusión
        if not criticos and not altos:
            lineas.append("✅ La asignación es aceptable. Solo problemas menores detectados.")
        elif criticos:
            lineas.append("⚠️ Se detectaron problemas críticos que impiden una asignación válida.")
            lineas.append("   Recomendación: Revisar y ajustar configuración manualmente,")
            lineas.append("   o continuar con el algoritmo ILP avanzado.")
        else:
            lineas.append("⚠️ La asignación tiene problemas importantes.")
            lineas.append("   Puede continuar con ILP para obtener mejor resultado.")

        lineas.append("=" * 70)

        return "\n".join(lineas)
