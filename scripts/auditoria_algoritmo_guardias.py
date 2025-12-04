#!/usr/bin/env python3
"""
Script de auditoría exhaustiva del algoritmo de asignación de guardias.

Analiza:
1. Cumplimiento de fechas de inicio/fin de profesores
2. Equilibrio en la distribución de guardias
3. Cobertura temporal (por qué hay "agujeros" en marzo)
4. Profesores sin guardias asignadas
5. Zonas sin asignar
6. Validación de todas las restricciones

Autor: Carlos Ferrero Bonet
Fecha: 14 de noviembre de 2025
"""

import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import sqlite3


class AuditoriaAlgoritmoGuardias:
    """Auditoría exhaustiva del algoritmo de asignación de guardias."""

    def __init__(self, db_path: str):
        """Inicializar auditoría."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

        # Resultados de la auditoría
        self.problemas = []
        self.warnings = []
        self.stats = {}

    def run(self):
        """Ejecutar auditoría completa."""
        print("=" * 100)
        print("🔍 AUDITORÍA EXHAUSTIVA DEL ALGORITMO DE ASIGNACIÓN DE GUARDIAS")
        print("=" * 100)
        print()

        # 1. Análisis de configuración básica
        self.analizar_configuracion()

        # 2. Análisis de profesores sin guardias
        self.analizar_profesores_sin_guardias()

        # 3. Análisis de cumplimiento de fechas de inicio/fin
        self.analizar_cumplimiento_fechas()

        # 4. Análisis de equilibrio de guardias
        self.analizar_equilibrio_guardias()

        # 5. Análisis de cobertura temporal
        self.analizar_cobertura_temporal()

        # 6. Análisis de zonas sin cubrir
        self.analizar_zonas_sin_cubrir()

        # 7. Análisis de restricciones (turnos, días, recreos)
        self.analizar_restricciones()

        # 8. Análisis de ausencias vs guardias
        self.analizar_ausencias()

        # 9. Resumen y conclusiones
        self.generar_resumen()

        # 10. Recomendaciones y plan de acción
        self.generar_plan_accion()

    def analizar_configuracion(self):
        """Analizar configuración básica del sistema."""
        print("📋 1. ANÁLISIS DE CONFIGURACIÓN BÁSICA")
        print("-" * 100)

        # Obtener configuración
        self.cursor.execute("SELECT * FROM configuracion LIMIT 1")
        config = self.cursor.fetchone()

        if not config:
            self.problemas.append("CRÍTICO: No existe configuración del sistema")
            print("❌ No existe configuración del sistema")
            return

        # Mapeo manual de columnas (ajustar según tu esquema)
        config_dict = {
            "id": config[0],
            "fecha_inicio": config[1],
            "fecha_fin": config[2],
        }

        print(f"✓ Curso: {config_dict['fecha_inicio']} a {config_dict['fecha_fin']}")

        # Calcular días lectivos
        fecha_inicio = datetime.strptime(config_dict["fecha_inicio"], "%Y-%m-%d")
        fecha_fin = datetime.strptime(config_dict["fecha_fin"], "%Y-%m-%d")
        dias_totales = (fecha_fin - fecha_inicio).days + 1

        print(f"✓ Duración: {dias_totales} días")

        # Estadísticas básicas
        self.cursor.execute("SELECT COUNT(*) FROM profesores WHERE activo = 1")
        total_profes = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM zonas")
        total_zonas = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT COUNT(*) FROM guardias")
        total_guardias = self.cursor.fetchone()[0]

        print(f"✓ Profesores activos: {total_profes}")
        print(f"✓ Zonas: {total_zonas}")
        print(f"✓ Guardias asignadas: {total_guardias}")

        self.stats["total_profesores"] = total_profes
        self.stats["total_zonas"] = total_zonas
        self.stats["total_guardias"] = total_guardias
        self.stats["dias_lectivos"] = dias_totales
        self.stats["fecha_inicio"] = config_dict["fecha_inicio"]
        self.stats["fecha_fin"] = config_dict["fecha_fin"]

        print()

    def analizar_profesores_sin_guardias(self):
        """Analizar profesores sin guardias asignadas."""
        print("👥 2. ANÁLISIS DE PROFESORES SIN GUARDIAS")
        print("-" * 100)

        self.cursor.execute("""
            SELECT p.id, p.nombre_completo, p.turno, p.porcentaje_jornada, p.tutor,
                   p.fecha_inicio_guardias, p.fecha_fin_guardias
            FROM profesores p
            LEFT JOIN guardias g ON p.id = g.profesor_id
            WHERE p.activo = 1
            GROUP BY p.id
            HAVING COUNT(g.id) = 0
            ORDER BY p.nombre_completo
        """)

        sin_guardias = self.cursor.fetchall()

        if sin_guardias:
            print(f"❌ PROBLEMA: {len(sin_guardias)} profesores activos SIN guardias asignadas:")
            print()
            for prof in sin_guardias:
                prof_id, nombre, turno, jornada, tutor, fecha_ini, fecha_fin = prof
                tutor_mark = "👨‍🏫" if tutor else "  "
                fecha_info = f"Inicio: {fecha_ini or 'N/A':10}" if fecha_ini else ""
                print(f"  {tutor_mark} {nombre:45} | {turno:8} | {jornada:3.0f}% | {fecha_info}")

                self.problemas.append(f"Profesor sin guardias: {nombre} (ID: {prof_id})")

            self.stats["profesores_sin_guardias"] = len(sin_guardias)
        else:
            print("✅ Todos los profesores activos tienen guardias asignadas")
            self.stats["profesores_sin_guardias"] = 0

        print()

    def analizar_cumplimiento_fechas(self):
        """Analizar cumplimiento de fechas de inicio/fin."""
        print("📅 3. ANÁLISIS DE CUMPLIMIENTO DE FECHAS DE INICIO/FIN")
        print("-" * 100)

        # Profesores con fecha_inicio configurada
        self.cursor.execute("""
            SELECT p.id, p.nombre_completo, p.fecha_inicio_guardias,
                   MIN(g.fecha) as primera_guardia,
                   COUNT(g.id) as total_guardias
            FROM profesores p
            LEFT JOIN guardias g ON p.id = g.profesor_id
            WHERE p.activo = 1 AND p.fecha_inicio_guardias IS NOT NULL
            GROUP BY p.id, p.nombre_completo, p.fecha_inicio_guardias
        """)

        profesores_con_fecha = self.cursor.fetchall()

        violaciones_inicio = []
        retrasos = []
        sin_guardias_con_fecha = []

        for prof in profesores_con_fecha:
            prof_id, nombre, fecha_inicio, primera_guardia, total = prof

            if primera_guardia is None:
                sin_guardias_con_fecha.append((nombre, fecha_inicio))
                self.problemas.append(
                    f"Profesor con fecha_inicio pero sin guardias: {nombre} (Inicio: {fecha_inicio})"
                )
            elif primera_guardia < fecha_inicio:
                violaciones_inicio.append((nombre, fecha_inicio, primera_guardia))
                self.problemas.append(
                    f"VIOLACIÓN: {nombre} tiene guardias ANTES de fecha_inicio "
                    f"(Config: {fecha_inicio}, Primera: {primera_guardia})"
                )
            elif primera_guardia > fecha_inicio:
                dias_retraso = (
                    datetime.strptime(primera_guardia, "%Y-%m-%d")
                    - datetime.strptime(fecha_inicio, "%Y-%m-%d")
                ).days
                retrasos.append((nombre, fecha_inicio, primera_guardia, dias_retraso))
                if dias_retraso > 30:  # Más de 1 mes
                    self.problemas.append(
                        f"RETRASO EXCESIVO: {nombre} empieza {dias_retraso} días después "
                        f"(Config: {fecha_inicio}, Primera: {primera_guardia})"
                    )
                else:
                    self.warnings.append(
                        f"Retraso aceptable: {nombre} empieza {dias_retraso} días después"
                    )

        print(f"Profesores con fecha_inicio configurada: {len(profesores_con_fecha)}")
        print(
            f"  ✅ Cumplen exactamente: {len(profesores_con_fecha) - len(violaciones_inicio) - len(retrasos) - len(sin_guardias_con_fecha)}"
        )
        print(f"  ❌ Violaciones (antes de fecha): {len(violaciones_inicio)}")
        print(f"  ⚠️  Retrasos: {len(retrasos)}")
        print(f"  ❌ Sin guardias: {len(sin_guardias_con_fecha)}")

        if retrasos:
            retraso_promedio = sum(r[3] for r in retrasos) / len(retrasos)
            retraso_max = max(r[3] for r in retrasos)
            print(f"\n  📊 Retraso promedio: {retraso_promedio:.1f} días")
            print(f"  📊 Retraso máximo: {retraso_max} días")

        # Análisis de fecha_fin
        self.cursor.execute("""
            SELECT p.id, p.nombre_completo, p.fecha_fin_guardias,
                   MAX(g.fecha) as ultima_guardia
            FROM profesores p
            LEFT JOIN guardias g ON p.id = g.profesor_id
            WHERE p.activo = 1 AND p.fecha_fin_guardias IS NOT NULL
            GROUP BY p.id, p.nombre_completo, p.fecha_fin_guardias
        """)

        profesores_con_fecha_fin = self.cursor.fetchall()

        violaciones_fin = []
        for prof in profesores_con_fecha_fin:
            prof_id, nombre, fecha_fin, ultima_guardia = prof
            if ultima_guardia and ultima_guardia > fecha_fin:
                violaciones_fin.append((nombre, fecha_fin, ultima_guardia))
                self.problemas.append(
                    f"VIOLACIÓN: {nombre} tiene guardias DESPUÉS de fecha_fin "
                    f"(Config: {fecha_fin}, Última: {ultima_guardia})"
                )

        if violaciones_fin:
            print(f"\n  ❌ Violaciones fecha_fin: {len(violaciones_fin)}")

        self.stats["violaciones_fecha_inicio"] = len(violaciones_inicio)
        self.stats["retrasos_fecha_inicio"] = len(retrasos)
        self.stats["violaciones_fecha_fin"] = len(violaciones_fin)

        print()

    def analizar_equilibrio_guardias(self):
        """Analizar equilibrio en la distribución de guardias."""
        print("⚖️  4. ANÁLISIS DE EQUILIBRIO DE GUARDIAS")
        print("-" * 100)

        self.cursor.execute("""
            SELECT p.id, p.nombre_completo, p.porcentaje_jornada, p.tutor,
                   COUNT(g.id) as total_guardias
            FROM profesores p
            LEFT JOIN guardias g ON p.id = g.profesor_id
            WHERE p.activo = 1
            GROUP BY p.id, p.nombre_completo, p.porcentaje_jornada, p.tutor
            ORDER BY total_guardias DESC
        """)

        distribucion = self.cursor.fetchall()

        guardias_por_profesor = [d[4] for d in distribucion if d[4] > 0]

        if not guardias_por_profesor:
            print("❌ No hay guardias asignadas")
            return

        promedio = sum(guardias_por_profesor) / len(guardias_por_profesor)
        minimo = min(guardias_por_profesor)
        maximo = max(guardias_por_profesor)

        # Calcular desviación estándar
        varianza = sum((x - promedio) ** 2 for x in guardias_por_profesor) / len(
            guardias_por_profesor
        )
        desv_std = varianza**0.5

        print("📊 Estadísticas de distribución:")
        print(f"  Promedio: {promedio:.1f} guardias por profesor")
        print(f"  Mínimo: {minimo} guardias")
        print(f"  Máximo: {maximo} guardias")
        print(f"  Desviación estándar: {desv_std:.2f}")
        print(f"  Rango: {maximo - minimo} guardias")

        # Analizar desequilibrios
        desequilibrios = []
        for prof in distribucion:
            prof_id, nombre, jornada, tutor, total = prof
            if total > 0:
                diferencia_abs = abs(total - promedio)
                diferencia_pct = (diferencia_abs / promedio) * 100

                if diferencia_pct > 20:  # Más del 20% de desviación
                    desequilibrios.append((nombre, total, promedio, diferencia_pct))
                    if diferencia_pct > 50:
                        self.problemas.append(
                            f"DESEQUILIBRIO CRÍTICO: {nombre} tiene {total} guardias "
                            f"(promedio: {promedio:.1f}, desviación: {diferencia_pct:.1f}%)"
                        )
                    else:
                        self.warnings.append(
                            f"Desequilibrio: {nombre} tiene {total} guardias "
                            f"(desviación: {diferencia_pct:.1f}%)"
                        )

        if desequilibrios:
            print(f"\n⚠️  Profesores con desequilibrio (>{20}% desviación): {len(desequilibrios)}")
            print("\nTop 10 mayores desequilibrios:")
            for nombre, total, prom, pct in sorted(
                desequilibrios, key=lambda x: x[3], reverse=True
            )[:10]:
                print(f"  - {nombre:45} | {total:3} guardias | Desv: {pct:5.1f}%")
        else:
            print("\n✅ Distribución equilibrada (desviaciones <20%)")

        self.stats["promedio_guardias"] = promedio
        self.stats["desviacion_std"] = desv_std
        self.stats["desequilibrios"] = len(desequilibrios)

        print()

    def analizar_cobertura_temporal(self):
        """Analizar cobertura temporal - detectar 'agujeros'."""
        print("📆 5. ANÁLISIS DE COBERTURA TEMPORAL")
        print("-" * 100)

        # Obtener rango de fechas
        fecha_inicio = datetime.strptime(self.stats["fecha_inicio"], "%Y-%m-%d")
        fecha_fin = datetime.strptime(self.stats["fecha_fin"], "%Y-%m-%d")

        # Obtener fechas con guardias
        self.cursor.execute("""
            SELECT DISTINCT fecha, COUNT(*) as num_guardias
            FROM guardias
            GROUP BY fecha
            ORDER BY fecha
        """)

        fechas_con_guardias = {row[0]: row[1] for row in self.cursor.fetchall()}

        # Analizar agujeros (días sin guardias)
        dias_sin_guardias = []
        fecha_actual = fecha_inicio

        while fecha_actual <= fecha_fin:
            fecha_str = fecha_actual.strftime("%Y-%m-%d")
            dia_semana = fecha_actual.weekday()

            # Ignorar fines de semana
            if dia_semana < 5:  # Lunes a viernes
                if fecha_str not in fechas_con_guardias:
                    dias_sin_guardias.append((fecha_str, dia_semana))

            fecha_actual += timedelta(days=1)

        print(
            f"Total días lectivos esperados (L-V): ~{len([d for d in range((fecha_fin - fecha_inicio).days + 1) if (fecha_inicio + timedelta(days=d)).weekday() < 5])}"
        )
        print(f"Días con guardias: {len(fechas_con_guardias)}")
        print(f"❌ Días sin guardias (L-V): {len(dias_sin_guardias)}")

        if dias_sin_guardias:
            # Agrupar por meses
            por_mes = defaultdict(list)
            for fecha, dia in dias_sin_guardias:
                mes = fecha[:7]  # YYYY-MM
                por_mes[mes].append(fecha)

            print("\n📅 Distribución de días sin guardias por mes:")
            for mes in sorted(por_mes.keys()):
                print(f"  {mes}: {len(por_mes[mes])} días sin guardias")
                if len(por_mes[mes]) > 5:  # Más de 5 días en un mes
                    self.problemas.append(
                        f"AGUJERO TEMPORAL: {mes} tiene {len(por_mes[mes])} días sin guardias"
                    )

            # Detectar períodos largos sin guardias
            periodos_largos = []
            periodo_actual = [dias_sin_guardias[0][0]]

            for i in range(1, len(dias_sin_guardias)):
                fecha_ant = datetime.strptime(dias_sin_guardias[i - 1][0], "%Y-%m-%d")
                fecha_act = datetime.strptime(dias_sin_guardias[i][0], "%Y-%m-%d")

                if (fecha_act - fecha_ant).days <= 3:  # Consecutivos o casi
                    periodo_actual.append(dias_sin_guardias[i][0])
                else:
                    if len(periodo_actual) >= 5:
                        periodos_largos.append(periodo_actual)
                    periodo_actual = [dias_sin_guardias[i][0]]

            if len(periodo_actual) >= 5:
                periodos_largos.append(periodo_actual)

            if periodos_largos:
                print(f"\n⚠️  Períodos largos sin guardias (≥5 días): {len(periodos_largos)}")
                for periodo in periodos_largos:
                    print(f"  - Del {periodo[0]} al {periodo[-1]} ({len(periodo)} días)")
                    self.problemas.append(
                        f"PERÍODO SIN COBERTURA: {periodo[0]} a {periodo[-1]} ({len(periodo)} días)"
                    )

        # Analizar caída en marzo
        guardias_por_mes = defaultdict(int)
        for fecha, num in fechas_con_guardias.items():
            mes = fecha[:7]
            guardias_por_mes[mes] += num

        print("\n📊 Guardias por mes:")
        meses_ordenados = sorted(guardias_por_mes.keys())
        for mes in meses_ordenados:
            print(f"  {mes}: {guardias_por_mes[mes]:4} guardias")

        # Detectar caídas significativas
        if len(meses_ordenados) > 1:
            for i in range(1, len(meses_ordenados)):
                mes_ant = meses_ordenados[i - 1]
                mes_act = meses_ordenados[i]

                caida_pct = (
                    (guardias_por_mes[mes_ant] - guardias_por_mes[mes_act])
                    / guardias_por_mes[mes_ant]
                    * 100
                )

                if caida_pct > 30:  # Caída > 30%
                    self.problemas.append(
                        f"CAÍDA SIGNIFICATIVA: {mes_act} tiene {caida_pct:.1f}% menos guardias que {mes_ant}"
                    )

        self.stats["dias_sin_guardias"] = len(dias_sin_guardias)

        print()

    def analizar_zonas_sin_cubrir(self):
        """Analizar zonas sin cubrir por períodos."""
        print("🗺️  6. ANÁLISIS DE ZONAS SIN CUBRIR")
        print("-" * 100)

        # Obtener todas las zonas
        self.cursor.execute("SELECT id, nombre_zona FROM zonas")
        zonas = self.cursor.fetchall()

        print(f"Total zonas: {len(zonas)}")

        # Para cada zona, analizar cobertura temporal
        zonas_problematicas = []

        for zona_id, nombre_zona in zonas:
            self.cursor.execute(
                """
                SELECT COUNT(DISTINCT fecha) as dias_cubiertos
                FROM guardias
                WHERE zona_id = ?
            """,
                (zona_id,),
            )

            dias_cubiertos = self.cursor.fetchone()[0]

            # Calcular días esperados (aproximado)
            dias_esperados = len(
                [
                    d
                    for d in range(
                        (
                            datetime.strptime(self.stats["fecha_fin"], "%Y-%m-%d")
                            - datetime.strptime(self.stats["fecha_inicio"], "%Y-%m-%d")
                        ).days
                        + 1
                    )
                    if (
                        datetime.strptime(self.stats["fecha_inicio"], "%Y-%m-%d")
                        + timedelta(days=d)
                    ).weekday()
                    < 5
                ]
            )

            cobertura_pct = (dias_cubiertos / dias_esperados * 100) if dias_esperados > 0 else 0

            if cobertura_pct < 80:
                zonas_problematicas.append(
                    (nombre_zona, dias_cubiertos, dias_esperados, cobertura_pct)
                )
                if cobertura_pct < 50:
                    self.problemas.append(
                        f"ZONA CRÍTICA: {nombre_zona} solo cubierta {cobertura_pct:.1f}% del tiempo"
                    )

        if zonas_problematicas:
            print(f"\n⚠️  Zonas con baja cobertura (<80%): {len(zonas_problematicas)}")
            for nombre, dias_cub, dias_esp, pct in sorted(zonas_problematicas, key=lambda x: x[3]):
                print(f"  - {nombre:30} | {dias_cub:3}/{dias_esp:3} días | {pct:5.1f}%")
        else:
            print("✅ Todas las zonas tienen cobertura >80%")

        self.stats["zonas_baja_cobertura"] = len(zonas_problematicas)

        print()

    def analizar_restricciones(self):
        """Analizar cumplimiento de restricciones (turnos, días, recreos)."""
        print("🔒 7. ANÁLISIS DE CUMPLIMIENTO DE RESTRICCIONES")
        print("-" * 100)

        # Verificar turnos
        self.cursor.execute("""
            SELECT p.nombre_completo, p.turno, g.turno, COUNT(*) as violaciones
            FROM profesores p
            INNER JOIN guardias g ON p.id = g.profesor_id
            WHERE p.turno != 'mixto' AND p.turno != g.turno
            GROUP BY p.id, p.nombre_completo, p.turno, g.turno
        """)

        violaciones_turno = self.cursor.fetchall()

        if violaciones_turno:
            print(f"❌ Violaciones de turno: {len(violaciones_turno)} casos")
            for nombre, turno_prof, turno_guard, count in violaciones_turno[:10]:
                print(
                    f"  - {nombre}: asignado a turno '{turno_guard}' (debe ser '{turno_prof}') - {count} veces"
                )
                self.problemas.append(
                    f"VIOLACIÓN TURNO: {nombre} tiene guardias en turno incorrecto"
                )
        else:
            print("✅ Turnos: Sin violaciones detectadas")

        # Verificar días permitidos
        self.cursor.execute("""
            SELECT p.nombre_completo, p.dias_semana_permitidos, COUNT(*) as guardias
            FROM profesores p
            INNER JOIN guardias g ON p.id = g.profesor_id
            WHERE p.dias_semana_permitidos IS NOT NULL
            GROUP BY p.id, p.nombre_completo, p.dias_semana_permitidos
        """)

        profes_con_restriccion_dias = self.cursor.fetchall()
        print(f"\nProfesores con restricción de días: {len(profes_con_restriccion_dias)}")

        # Verificar recreos permitidos
        self.cursor.execute("""
            SELECT p.nombre_completo, p.recreos_permitidos, COUNT(*) as guardias
            FROM profesores p
            INNER JOIN guardias g ON p.id = g.profesor_id
            WHERE p.recreos_permitidos IS NOT NULL
            GROUP BY p.id, p.nombre_completo, p.recreos_permitidos
        """)

        profes_con_restriccion_recreos = self.cursor.fetchall()
        print(f"Profesores con restricción de recreos: {len(profes_con_restriccion_recreos)}")

        self.stats["violaciones_turno"] = len(violaciones_turno)

        print()

    def analizar_ausencias(self):
        """Analizar relación entre ausencias y guardias."""
        print("🏥 8. ANÁLISIS DE AUSENCIAS VS GUARDIAS")
        print("-" * 100)

        # Contar ausencias
        self.cursor.execute("SELECT COUNT(*) FROM ausencias WHERE activa = 1")
        ausencias_activas = self.cursor.fetchone()[0]

        print(f"Ausencias activas: {ausencias_activas}")

        # Verificar si hay guardias asignadas durante ausencias
        self.cursor.execute("""
            SELECT p.nombre_completo, a.fecha_inicio, a.fecha_fin, a.tipo, COUNT(g.id) as guardias
            FROM ausencias a
            INNER JOIN profesores p ON a.profesor_id = p.id
            LEFT JOIN guardias g ON g.profesor_id = p.id
                AND g.fecha >= a.fecha_inicio
                AND g.fecha <= a.fecha_fin
            WHERE a.activa = 1
            GROUP BY a.id, p.nombre_completo, a.fecha_inicio, a.fecha_fin, a.tipo
            HAVING COUNT(g.id) > 0
        """)

        guardias_durante_ausencia = self.cursor.fetchall()

        if guardias_durante_ausencia:
            print(
                f"\n❌ PROBLEMA: {len(guardias_durante_ausencia)} profesores con guardias durante ausencia:"
            )
            for nombre, inicio, fin, tipo, num_guardias in guardias_durante_ausencia[:10]:
                print(f"  - {nombre}: {num_guardias} guardias del {inicio} al {fin} ({tipo})")
                self.problemas.append(
                    f"GUARDIAS DURANTE AUSENCIA: {nombre} tiene {num_guardias} guardias durante ausencia"
                )
        else:
            print("✅ No hay guardias asignadas durante ausencias")

        self.stats["guardias_durante_ausencia"] = len(guardias_durante_ausencia)

        print()

    def generar_resumen(self):
        """Generar resumen de la auditoría."""
        print("=" * 100)
        print("📊 RESUMEN DE LA AUDITORÍA")
        print("=" * 100)
        print()

        print(f"🔴 PROBLEMAS CRÍTICOS: {len(self.problemas)}")
        if self.problemas:
            print("\nTop 10 problemas más críticos:")
            for i, problema in enumerate(self.problemas[:10], 1):
                print(f"  {i}. {problema}")
            if len(self.problemas) > 10:
                print(f"  ... y {len(self.problemas) - 10} problemas más")

        print(f"\n⚠️  WARNINGS: {len(self.warnings)}")
        if self.warnings and len(self.warnings) <= 10:
            for warning in self.warnings:
                print(f"  - {warning}")
        elif self.warnings:
            print("  (Ver log completo para detalles)")

        print("\n📈 ESTADÍSTICAS CLAVE:")
        print(f"  - Profesores sin guardias: {self.stats.get('profesores_sin_guardias', 0)}")
        print(f"  - Violaciones fecha_inicio: {self.stats.get('violaciones_fecha_inicio', 0)}")
        print(f"  - Retrasos fecha_inicio: {self.stats.get('retrasos_fecha_inicio', 0)}")
        print(f"  - Desequilibrios (>20%): {self.stats.get('desequilibrios', 0)}")
        print(f"  - Días sin guardias: {self.stats.get('dias_sin_guardias', 0)}")
        print(f"  - Zonas con baja cobertura: {self.stats.get('zonas_baja_cobertura', 0)}")
        print(f"  - Guardias durante ausencia: {self.stats.get('guardias_durante_ausencia', 0)}")

        # Score de salud del sistema
        problemas_criticos = len([p for p in self.problemas if "CRÍTICO" in p or "VIOLACIÓN" in p])

        if problemas_criticos == 0 and len(self.problemas) < 5:
            print("\n✅ ESTADO DEL SISTEMA: SALUDABLE")
        elif problemas_criticos < 5 and len(self.problemas) < 20:
            print("\n⚠️  ESTADO DEL SISTEMA: REQUIERE ATENCIÓN")
        else:
            print("\n❌ ESTADO DEL SISTEMA: CRÍTICO - REQUIERE ACCIÓN INMEDIATA")

        print()

    def generar_plan_accion(self):
        """Generar plan de acción basado en problemas detectados."""
        print("=" * 100)
        print("🎯 PLAN DE ACCIÓN RECOMENDADO")
        print("=" * 100)
        print()

        acciones = []

        # Acción 1: Profesores sin guardias
        if self.stats.get("profesores_sin_guardias", 0) > 0:
            acciones.append(
                {
                    "prioridad": "CRÍTICA",
                    "accion": "Asignar guardias a profesores sin asignación",
                    "pasos": [
                        "1. Identificar por qué no se les asignó (¿restricciones? ¿turnos?)",
                        "2. Verificar que tienen horario compatible",
                        "3. Redistribuir guardias para incluirlos",
                        "4. Ejecutar algoritmo con parámetro force_include_all=True",
                    ],
                }
            )

        # Acción 2: Violaciones de fechas
        if self.stats.get("violaciones_fecha_inicio", 0) > 0:
            acciones.append(
                {
                    "prioridad": "CRÍTICA",
                    "accion": "Corregir violaciones de fecha_inicio",
                    "pasos": [
                        "1. Reasignar guardias que violan fecha_inicio",
                        "2. Verificar lógica de validación en asignador",
                        "3. Añadir test unitario para esta restricción",
                    ],
                }
            )

        # Acción 3: Retrasos excesivos
        if self.stats.get("retrasos_fecha_inicio", 0) > 5:
            acciones.append(
                {
                    "prioridad": "ALTA",
                    "accion": "Reducir retrasos en fecha_inicio",
                    "pasos": [
                        "1. Implementar priorización de profesores con fecha_inicio",
                        "2. Alternar asignaciones: día sí, día no hasta cubrir todos",
                        "3. Calcular guardias necesarias considerando fecha_inicio",
                    ],
                }
            )

        # Acción 4: Desequilibrios
        if self.stats.get("desequilibrios", 0) > 10:
            acciones.append(
                {
                    "prioridad": "ALTA",
                    "accion": "Mejorar equilibrio de guardias",
                    "pasos": [
                        "1. Revisar cálculo de guardias esperadas por profesor",
                        "2. Implementar iteraciones de balanceo post-asignación",
                        "3. Verificar que jornada reducida se considera correctamente",
                    ],
                }
            )

        # Acción 5: Agujeros temporales
        if self.stats.get("dias_sin_guardias", 0) > 20:
            acciones.append(
                {
                    "prioridad": "CRÍTICA",
                    "accion": "Cubrir días sin guardias",
                    "pasos": [
                        "1. Identificar causa (¿festivos mal marcados? ¿bug en generación?)",
                        "2. Revisar configuración de días lectivos",
                        "3. Regenerar guardias para períodos sin cobertura",
                        "4. Verificar que no hay límite artificial de guardias",
                    ],
                }
            )

        # Acción 6: Zonas sin cubrir
        if self.stats.get("zonas_baja_cobertura", 0) > 0:
            acciones.append(
                {
                    "prioridad": "ALTA",
                    "accion": "Mejorar cobertura de zonas",
                    "pasos": [
                        "1. Verificar si zonas tienen fecha_inicio/fin configuradas",
                        "2. Asegurar que hay suficientes profesores para cubrir",
                        "3. Implementar rotación equitativa de zonas",
                    ],
                }
            )

        # Acción 7: Algoritmo general
        acciones.append(
            {
                "prioridad": "FUNDAMENTAL",
                "accion": "Mejorar algoritmo de asignación",
                "pasos": [
                    "1. Implementar asignación en múltiples pasadas:",
                    "   - Pasada 1: Profesores con fecha_inicio urgente",
                    "   - Pasada 2: Profesores normales",
                    "   - Pasada 3: Balanceo y corrección",
                    "2. Añadir validación post-asignación con métricas",
                    "3. Implementar backtracking si no se cumplen restricciones",
                    "4. Añadir parámetro max_iteraciones para ajustar hasta cumplir",
                    "5. Generar reporte de cumplimiento al finalizar",
                ],
            }
        )

        # Mostrar plan
        for i, accion in enumerate(acciones, 1):
            print(f"{i}. [{accion['prioridad']}] {accion['accion']}")
            for paso in accion["pasos"]:
                print(f"   {paso}")
            print()

        print("=" * 100)
        print()
        print("💡 SIGUIENTES PASOS INMEDIATOS:")
        print()
        print("1. Revisar este informe completo")
        print("2. Priorizar acciones por criticidad")
        print("3. Implementar mejoras en el algoritmo (asignador_guardias_v3_simple.py)")
        print("4. Ejecutar tests de validación")
        print("5. Regenerar guardias con algoritmo mejorado")
        print("6. Re-ejecutar esta auditoría para verificar mejoras")
        print()
        print("=" * 100)

    def close(self):
        """Cerrar conexión."""
        self.conn.close()


def main():
    """Ejecutar auditoría."""

    # Determinar ruta de BD
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent

    # Buscar BD activa
    db_path = project_dir / "data/users/0db13e2857239ed8/guardias_patio.db"

    if not db_path.exists():
        print(f"❌ No se encuentra la base de datos en: {db_path}")
        print("\nBuscando bases de datos disponibles...")
        data_dir = project_dir / "data"
        for db_file in data_dir.rglob("*.db"):
            print(f"  Encontrada: {db_file.relative_to(project_dir)}")
        sys.exit(1)

    print(f"📂 Base de datos: {db_path.relative_to(project_dir)}")
    print()

    # Ejecutar auditoría
    auditoria = AuditoriaAlgoritmoGuardias(str(db_path))

    try:
        auditoria.run()
    finally:
        auditoria.close()

    print("\n✅ Auditoría completada")


if __name__ == "__main__":
    main()
