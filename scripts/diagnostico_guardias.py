#!/usr/bin/env python3
"""
Script de Diagnóstico Completo del Sistema de Guardias

Analiza en profundidad por qué hay profesores sin guardias y slots vacíos.
Genera un reporte detallado con:
- Validación de configuración
- Análisis de elegibilidad por profesor
- Matriz de compatibilidad profesor-slot
- Identificación de cuellos de botella
- Sugerencias de corrección

Uso:
    python scripts/diagnostico_guardias.py [--html] [--json] [--verbose]
"""

import sys
from pathlib import Path

# Añadir src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import argparse
import json
from collections import defaultdict
from datetime import timedelta

from database.db_manager import SessionLocal
from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona


class DiagnosticoGuardias:
    """Analizador completo del sistema de guardias."""

    def __init__(self, session):
        self.session = session
        self.config = None
        self.profesores = []
        self.zonas = []
        self.guardias = []
        self.recreos_config = []
        self.problemas = []
        self.advertencias = []
        self.sugerencias = []

    def ejecutar(self, verbose=False):
        """Ejecuta el diagnóstico completo."""
        print("🔍 DIAGNÓSTICO COMPLETO DEL SISTEMA DE GUARDIAS")
        print("=" * 80)
        print()

        # 1. Cargar datos
        self._cargar_datos()

        # 2. Validar configuración
        print("\n1️⃣ VALIDACIÓN DE CONFIGURACIÓN")
        print("-" * 80)
        self._validar_configuracion()

        # 3. Analizar profesores
        print("\n2️⃣ ANÁLISIS DE PROFESORES")
        print("-" * 80)
        self._analizar_profesores(verbose)

        # 4. Analizar zonas
        print("\n3️⃣ ANÁLISIS DE ZONAS")
        print("-" * 80)
        self._analizar_zonas(verbose)

        # 5. Analizar guardias generadas
        print("\n4️⃣ ANÁLISIS DE GUARDIAS GENERADAS")
        print("-" * 80)
        self._analizar_guardias(verbose)

        # 6. Matriz de elegibilidad
        print("\n5️⃣ MATRIZ DE ELEGIBILIDAD")
        print("-" * 80)
        self._analizar_elegibilidad(verbose)

        # 7. Ausencias
        print("\n6️⃣ ANÁLISIS DE AUSENCIAS")
        print("-" * 80)
        self._analizar_ausencias(verbose)

        # 8. Resumen y sugerencias
        print("\n7️⃣ RESUMEN Y SUGERENCIAS")
        print("-" * 80)
        self._generar_resumen()

        print("\n" + "=" * 80)

    def _cargar_datos(self):
        """Carga todos los datos necesarios."""
        self.config = self.session.query(Configuracion).first()
        self.profesores = self.session.query(Profesor).all()
        self.zonas = self.session.query(Zona).all()
        self.guardias = self.session.query(Guardia).all()

        if self.config and self.config.recreos_config:
            try:
                self.recreos_config = json.loads(self.config.recreos_config)
            except:
                self.recreos_config = []

    def _validar_configuracion(self):
        """Valida la configuración del curso."""
        if not self.config:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Configuración',
                'mensaje': 'No existe configuración del curso',
                'impacto': 'No se pueden generar guardias sin configuración',
                'solucion': 'Crear configuración desde la UI: Configuración > Curso Escolar'
            })
            print("❌ CRÍTICO: No existe configuración del curso")
            print("   → Sin configuración no se pueden generar guardias")
            print("   → SOLUCIÓN: Crear configuración desde la UI\n")
            return

        print("✅ Configuración encontrada")
        print(f"   • ID: {self.config.id}")
        print(f"   • Curso: {self.config.fecha_inicio_curso} a {self.config.fecha_fin_curso}")

        # Validar fechas
        if self.config.fecha_inicio_curso >= self.config.fecha_fin_curso:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Configuración',
                'mensaje': 'Fecha de inicio >= fecha de fin',
                'impacto': 'Rango de fechas inválido',
                'solucion': 'Corregir fechas en configuración'
            })
            print("   ❌ Fecha inicio >= fecha fin (INVÁLIDO)")
        else:
            dias_curso = (self.config.fecha_fin_curso - self.config.fecha_inicio_curso).days
            print(f"   ✅ Rango válido: {dias_curso} días")

        # Validar recreos
        if not self.recreos_config:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Configuración',
                'mensaje': 'No hay recreos configurados',
                'impacto': 'Sin recreos no hay slots para asignar',
                'solucion': 'Configurar al menos 1 recreo en la configuración'
            })
            print("   ❌ No hay recreos configurados")
        else:
            print(f"   ✅ Recreos configurados: {len(self.recreos_config)}")
            for r in self.recreos_config:
                print(f"      • {r.get('etiqueta', 'Sin nombre')}: {r.get('turno', 'N/A')}, {r.get('zonas', 0)} zona(s)")

                # Validar que tenga al menos 1 zona
                if r.get('zonas', 0) == 0:
                    self.advertencias.append({
                        'categoria': 'Configuración',
                        'mensaje': f"Recreo '{r.get('etiqueta')}' tiene 0 zonas",
                        'solucion': 'Asignar al menos 1 zona al recreo'
                    })

        # Validar ajustes de tutores
        ajuste_tutores = getattr(self.config, 'ajuste_tutores', 1.0)
        ajuste_no_tutores = getattr(self.config, 'ajuste_no_tutores', 1.0)
        print(f"   • Ajuste tutores: {ajuste_tutores:.2f}")
        print(f"   • Ajuste no tutores: {ajuste_no_tutores:.2f}")

        if ajuste_tutores == 0 or ajuste_no_tutores == 0:
            self.advertencias.append({
                'categoria': 'Configuración',
                'mensaje': 'Ajuste de tutores o no tutores es 0',
                'solucion': 'Revisar valores de ajuste (normalmente entre 0.8 y 1.2)'
            })

    def _analizar_profesores(self, verbose=False):
        """Analiza profesores y sus restricciones."""
        if not self.profesores:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Profesores',
                'mensaje': 'No hay profesores registrados',
                'impacto': 'Sin profesores no se pueden generar guardias',
                'solucion': 'Registrar profesores desde la UI'
            })
            print("❌ No hay profesores registrados\n")
            return

        print(f"Total profesores: {len(self.profesores)}")

        # Clasificar profesores
        profes_ids_con_guardias = {g.profesor_id for g in self.guardias}
        profes_con_guardias = [p for p in self.profesores if p.id in profes_ids_con_guardias]
        profes_sin_guardias = [p for p in self.profesores if p.id not in profes_ids_con_guardias]

        pct_con = len(profes_con_guardias) / len(self.profesores) * 100
        pct_sin = len(profes_sin_guardias) / len(self.profesores) * 100

        print(f"   ✅ CON guardias: {len(profes_con_guardias)} ({pct_con:.1f}%)")
        print(f"   ❌ SIN guardias: {len(profes_sin_guardias)} ({pct_sin:.1f}%)")

        # Estadísticas por turno
        turnos_con = defaultdict(int)
        turnos_sin = defaultdict(int)

        for p in profes_con_guardias:
            turnos_con[p.turno] += 1
        for p in profes_sin_guardias:
            turnos_sin[p.turno] += 1

        print("\n   Distribución por turno:")
        for turno in set(list(turnos_con.keys()) + list(turnos_sin.keys())):
            con = turnos_con.get(turno, 0)
            sin = turnos_sin.get(turno, 0)
            total = con + sin
            print(f"      {turno.capitalize():10s}: {con:2d} con guardias, {sin:2d} sin guardias (total: {total})")

        # Analizar profesores sin guardias
        if profes_sin_guardias:
            if pct_sin > 20:
                self.problemas.append({
                    'tipo': 'ALTO',
                    'categoria': 'Profesores',
                    'mensaje': f'{pct_sin:.1f}% de profesores sin guardias',
                    'impacto': 'Distribución muy desigual',
                    'solucion': 'Revisar restricciones de profesores sin guardias'
                })

            print("\n   📋 ANÁLISIS DETALLADO DE PROFESORES SIN GUARDIAS:")

            for p in profes_sin_guardias[:10 if not verbose else None]:
                print(f"\n      👤 {p.nombre_completo}")
                print(f"         • Turno: {p.turno}")
                print(f"         • Horas: {p.horas_contrato}h ({p.porcentaje_jornada*100:.0f}% jornada)")
                print(f"         • Tutor: {'Sí' if p.tutor else 'No'}")

                # Analizar restricciones
                restricciones = []

                # Fechas
                if p.fecha_inicio_guardias or p.fecha_fin_guardias:
                    inicio = p.fecha_inicio_guardias or "Sin límite"
                    fin = p.fecha_fin_guardias or "Sin límite"
                    print(f"         • Fechas guardias: {inicio} a {fin}")

                    if self.config:
                        if p.fecha_inicio_guardias and p.fecha_inicio_guardias > self.config.fecha_fin_curso:
                            restricciones.append("Fecha inicio posterior al fin del curso")
                        if p.fecha_fin_guardias and p.fecha_fin_guardias < self.config.fecha_inicio_curso:
                            restricciones.append("Fecha fin anterior al inicio del curso")

                # Recreos permitidos
                if p.recreos_permitidos:
                    print(f"         • Recreos permitidos: {p.recreos_permitidos}")
                    try:
                        recreos_prof = json.loads(p.recreos_permitidos)
                        if self.recreos_config:
                            recreos_config_ids = [r['id'] for r in self.recreos_config]

                            # Verificar compatibilidad
                            if isinstance(recreos_prof, list):
                                compatible = any(r in recreos_config_ids for r in recreos_prof)
                                if not compatible:
                                    restricciones.append(f"Recreos permitidos {recreos_prof} incompatibles con config {recreos_config_ids}")
                            elif isinstance(recreos_prof, dict):
                                # Formato matriz: verificar que al menos un día tenga recreos compatibles
                                tiene_algun_recreo = False
                                for dia, recreos_dia in recreos_prof.items():
                                    if any(r in recreos_config_ids for r in recreos_dia):
                                        tiene_algun_recreo = True
                                        break
                                if not tiene_algun_recreo:
                                    restricciones.append("Matriz de recreos no coincide con ningún recreo configurado")
                    except:
                        restricciones.append("Formato de recreos_permitidos inválido")

                # Turno vs recreos configurados
                if self.recreos_config:
                    recreos_turnos = [r['turno'] for r in self.recreos_config]
                    if p.turno == 'mañana' and 'mañana' not in recreos_turnos:
                        restricciones.append("Turno mañana pero no hay recreos de mañana")
                    elif p.turno == 'tarde' and 'tarde' not in recreos_turnos:
                        restricciones.append("Turno tarde pero no hay recreos de tarde")

                # Ausencias
                ausencias_activas = self.session.query(Ausencia).filter(
                    Ausencia.profesor_id == p.id,
                    Ausencia.activa == True
                ).count()

                if ausencias_activas > 0:
                    print(f"         • Ausencias activas: {ausencias_activas}")
                    if ausencias_activas > 5:
                        restricciones.append(f"{ausencias_activas} ausencias activas (muchas)")

                # Mostrar diagnóstico
                if restricciones:
                    print("         🔍 POSIBLES RAZONES:")
                    for r in restricciones:
                        print(f"            ⚠️ {r}")
                else:
                    print("         ⚠️ NO SE DETECTÓ RAZÓN EVIDENTE - Problema del algoritmo")
                    self.problemas.append({
                        'tipo': 'ALTO',
                        'categoria': 'Algoritmo',
                        'mensaje': f'Profesor {p.nombre_completo} sin razón evidente para no tener guardias',
                        'impacto': 'Posible bug en el algoritmo de asignación',
                        'solucion': 'Revisar lógica de elegibilidad y scoring'
                    })

            if len(profes_sin_guardias) > 10 and not verbose:
                print(f"\n      ... y {len(profes_sin_guardias) - 10} más (usa --verbose para ver todos)")

    def _analizar_zonas(self, verbose=False):
        """Analiza zonas y su uso."""
        if not self.zonas:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Zonas',
                'mensaje': 'No hay zonas registradas',
                'impacto': 'Sin zonas no se pueden generar guardias',
                'solucion': 'Registrar zonas desde la UI'
            })
            print("❌ No hay zonas registradas\n")
            return

        print(f"Total zonas: {len(self.zonas)}")

        zonas_ids_con_guardias = {g.zona_id for g in self.guardias}
        zonas_con_guardias = [z for z in self.zonas if z.id in zonas_ids_con_guardias]
        zonas_sin_guardias = [z for z in self.zonas if z.id not in zonas_ids_con_guardias]

        pct_con = len(zonas_con_guardias) / len(self.zonas) * 100
        pct_sin = len(zonas_sin_guardias) / len(self.zonas) * 100

        print(f"   ✅ CON guardias: {len(zonas_con_guardias)} ({pct_con:.1f}%)")
        print(f"   ❌ SIN guardias: {len(zonas_sin_guardias)} ({pct_sin:.1f}%)")

        # Analizar zonas sin guardias
        if zonas_sin_guardias:
            if pct_sin > 30:
                self.advertencias.append({
                    'categoria': 'Zonas',
                    'mensaje': f'{pct_sin:.1f}% de zonas sin guardias',
                    'solucion': 'Revisar fechas de activación de zonas o configuración de recreos'
                })

            print("\n   📋 ZONAS SIN GUARDIAS:")
            for z in zonas_sin_guardias[:10 if not verbose else None]:
                print(f"      • {z.nombre_zona}")

                # Analizar fechas
                if z.fecha_inicio or z.fecha_fin:
                    inicio = z.fecha_inicio or "Sin límite"
                    fin = z.fecha_fin or "Sin límite"
                    print(f"        Activa: {inicio} a {fin}")

                    if self.config:
                        # Verificar si está fuera del rango del curso
                        if z.fecha_inicio and z.fecha_inicio > self.config.fecha_fin_curso:
                            print("        ⚠️ Fecha inicio posterior al fin del curso")
                        if z.fecha_fin and z.fecha_fin < self.config.fecha_inicio_curso:
                            print("        ⚠️ Fecha fin anterior al inicio del curso")

                        # Verificar solapamiento parcial
                        if z.fecha_inicio and z.fecha_fin:
                            if z.fecha_inicio <= self.config.fecha_fin_curso and z.fecha_fin >= self.config.fecha_inicio_curso:
                                # Hay solapamiento - debería tener algunas guardias
                                print("        ⚠️ Tiene solapamiento con el curso pero sin guardias")

            if len(zonas_sin_guardias) > 10 and not verbose:
                print(f"      ... y {len(zonas_sin_guardias) - 10} más")

    def _analizar_guardias(self, verbose=False):
        """Analiza las guardias generadas."""
        if not self.guardias:
            self.problemas.append({
                'tipo': 'CRÍTICO',
                'categoria': 'Guardias',
                'mensaje': 'No hay guardias generadas',
                'impacto': 'Sistema sin datos',
                'solucion': 'Generar guardias desde: Guardias > Generar Calendario'
            })
            print("❌ No hay guardias generadas")
            print("   → SOLUCIÓN: Generar guardias desde la UI\n")
            return

        print(f"Total guardias: {len(self.guardias)}")

        # Calcular slots esperados
        if self.config and self.recreos_config:
            primera_guardia = min(g.fecha for g in self.guardias)
            ultima_guardia = max(g.fecha for g in self.guardias)

            print(f"   • Rango: {primera_guardia} a {ultima_guardia}")

            # Calcular días laborables
            dias_laborables = 0
            current = primera_guardia
            while current <= ultima_guardia:
                if current.weekday() < 5:
                    dias_laborables += 1
                current += timedelta(days=1)

            # Calcular slots esperados por día
            slots_por_recreo = sum(r.get('zonas', 0) for r in self.recreos_config)
            slots_esperados_total = dias_laborables * slots_por_recreo

            print(f"   • Días laborables: {dias_laborables}")
            print(f"   • Slots/día: {slots_por_recreo} ({len(self.recreos_config)} recreos)")
            print(f"   • Slots esperados: {slots_esperados_total}")
            print(f"   • Slots generados: {len(self.guardias)}")

            cobertura = len(self.guardias) / slots_esperados_total * 100 if slots_esperados_total > 0 else 0
            print(f"   • Cobertura: {cobertura:.1f}%")

            if cobertura < 80:
                self.problemas.append({
                    'tipo': 'ALTO',
                    'categoria': 'Guardias',
                    'mensaje': f'Cobertura muy baja: {cobertura:.1f}%',
                    'impacto': 'Muchos slots sin cubrir',
                    'solucion': 'Revisar restricciones de profesores y mejorar algoritmo'
                })
            elif cobertura < 95:
                self.advertencias.append({
                    'categoria': 'Guardias',
                    'mensaje': f'Cobertura sub-óptima: {cobertura:.1f}%',
                    'solucion': 'Intentar mejorar distribución'
                })

            # Analizar distribución por día
            guardias_por_dia = defaultdict(int)
            for g in self.guardias:
                guardias_por_dia[g.fecha] += 1

            dias_completos = sum(1 for count in guardias_por_dia.values() if count == slots_por_recreo)
            dias_parciales = sum(1 for count in guardias_por_dia.values() if 0 < count < slots_por_recreo)
            dias_vacios = dias_laborables - len(guardias_por_dia)

            print("\n   Distribución por día:")
            print(f"      Completos (100%): {dias_completos} días")
            print(f"      Parciales: {dias_parciales} días")
            print(f"      Vacíos: {dias_vacios} días")

            if dias_vacios > 0:
                self.advertencias.append({
                    'categoria': 'Guardias',
                    'mensaje': f'{dias_vacios} días sin ninguna guardia',
                    'solucion': 'Revisar si hay ausencias masivas o problemas de elegibilidad'
                })

            # Mostrar días con slots vacíos
            if dias_parciales > 0 and verbose:
                print("\n   Días con cobertura parcial:")
                dias_parciales_lista = [(fecha, count) for fecha, count in guardias_por_dia.items()
                                       if 0 < count < slots_por_recreo]
                dias_parciales_lista.sort()

                for fecha, count in dias_parciales_lista[:10]:
                    vacios = slots_por_recreo - count
                    print(f"      {fecha.strftime('%Y-%m-%d %A')}: {count}/{slots_por_recreo} ({vacios} vacío(s))")

        # Distribución por profesor
        guardias_por_profesor = defaultdict(int)
        for g in self.guardias:
            guardias_por_profesor[g.profesor_id] += 1

        if guardias_por_profesor:
            valores = list(guardias_por_profesor.values())
            promedio = sum(valores) / len(valores)
            maximo = max(valores)
            minimo = min(valores)

            print("\n   Distribución por profesor:")
            print(f"      Promedio: {promedio:.1f} guardias")
            print(f"      Máximo: {maximo} | Mínimo: {minimo}")
            print(f"      Rango: {maximo - minimo}")

            if maximo - minimo > promedio * 0.5:
                self.advertencias.append({
                    'categoria': 'Guardias',
                    'mensaje': f'Gran desigualdad en distribución (rango: {maximo - minimo})',
                    'solucion': 'Mejorar balanceo del algoritmo'
                })

    def _analizar_elegibilidad(self, verbose=False):
        """Analiza la elegibilidad de profesores para slots."""
        if not self.config or not self.profesores or not self.recreos_config:
            print("⚠️ Faltan datos para analizar elegibilidad\n")
            return

        print("Calculando matriz de elegibilidad...")

        # Simular creación de slots
        from services.calculador_guardias import listar_dias_lectivos

        try:
            dias_lectivos = listar_dias_lectivos(self.config)
            if not dias_lectivos:
                print("⚠️ No hay días lectivos calculados\n")
                return

            # Calcular slots totales
            total_slots = 0
            for dia in dias_lectivos[:30]:  # Solo primeros 30 días para no saturar
                for recreo in self.recreos_config:
                    total_slots += recreo.get('zonas', 0)

            print("   • Analizando primeros 30 días lectivos")
            print(f"   • Slots a analizar: ~{total_slots}")

            # Matriz de elegibilidad
            matriz_elegibilidad = defaultdict(int)

            for prof in self.profesores:
                slots_compatibles = 0

                for dia in dias_lectivos[:30]:
                    for recreo in self.recreos_config:
                        # Verificar turno
                        if prof.turno != 'completo' and prof.turno != recreo.get('turno'):
                            continue

                        # Verificar fechas
                        if prof.fecha_inicio_guardias and dia < prof.fecha_inicio_guardias:
                            continue
                        if prof.fecha_fin_guardias and dia > prof.fecha_fin_guardias:
                            continue

                        # Verificar recreos permitidos
                        if prof.recreos_permitidos:
                            try:
                                recreos_prof = json.loads(prof.recreos_permitidos)
                                if isinstance(recreos_prof, list):
                                    if recreo['id'] not in recreos_prof:
                                        continue
                                elif isinstance(recreos_prof, dict):
                                    dia_semana = str(dia.weekday())
                                    if dia_semana not in recreos_prof or recreo['id'] not in recreos_prof[dia_semana]:
                                        continue
                            except:
                                pass

                        # Si llegamos aquí, el profesor es compatible
                        slots_compatibles += recreo.get('zonas', 0)

                matriz_elegibilidad[prof.id] = slots_compatibles

            # Analizar resultados
            profesores_bloqueados = []
            profesores_baja_elegibilidad = []

            for prof in self.profesores:
                slots = matriz_elegibilidad[prof.id]
                tasa = (slots / total_slots * 100) if total_slots > 0 else 0

                if slots == 0:
                    profesores_bloqueados.append(prof)
                elif tasa < 30:
                    profesores_baja_elegibilidad.append((prof, slots, tasa))

            print("\n   Resultados:")
            print(f"      Profesores totalmente bloqueados: {len(profesores_bloqueados)}")
            print(f"      Profesores con baja elegibilidad (<30%): {len(profesores_baja_elegibilidad)}")

            if profesores_bloqueados:
                self.problemas.append({
                    'tipo': 'ALTO',
                    'categoria': 'Elegibilidad',
                    'mensaje': f'{len(profesores_bloqueados)} profesores no pueden hacer ninguna guardia',
                    'impacto': 'Estos profesores NUNCA recibirán guardias',
                    'solucion': 'Revisar restricciones de turnos, fechas y recreos permitidos'
                })

                print("\n      🚫 PROFESORES BLOQUEADOS (0 slots compatibles):")
                for prof in profesores_bloqueados[:5]:
                    print(f"         • {prof.nombre_completo}")
                    print(f"           Turno: {prof.turno}, Recreos: {prof.recreos_permitidos or 'Todos'}")

                if len(profesores_bloqueados) > 5:
                    print(f"         ... y {len(profesores_bloqueados) - 5} más")

            if profesores_baja_elegibilidad and verbose:
                print("\n      ⚠️ PROFESORES CON BAJA ELEGIBILIDAD:")
                profesores_baja_elegibilidad.sort(key=lambda x: x[2])

                for prof, slots, tasa in profesores_baja_elegibilidad[:5]:
                    print(f"         • {prof.nombre_completo}: {slots} slots ({tasa:.1f}%)")

                if len(profesores_baja_elegibilidad) > 5:
                    print(f"         ... y {len(profesores_baja_elegibilidad) - 5} más")

        except Exception as e:
            print(f"⚠️ Error al calcular elegibilidad: {e}\n")

    def _analizar_ausencias(self, verbose=False):
        """Analiza las ausencias activas."""
        ausencias_activas = self.session.query(Ausencia).filter(Ausencia.activa == True).all()

        print(f"Total ausencias activas: {len(ausencias_activas)}")

        if not ausencias_activas:
            print("   ✅ No hay ausencias activas\n")
            return

        # Agrupar por profesor
        ausencias_por_profesor = defaultdict(list)
        for aus in ausencias_activas:
            ausencias_por_profesor[aus.profesor_id].append(aus)

        print(f"   Profesores con ausencias: {len(ausencias_por_profesor)}")

        # Calcular días totales de ausencia
        dias_ausencia_totales = 0
        for aus in ausencias_activas:
            dias = (aus.fecha_fin - aus.fecha_inicio).days + 1
            dias_ausencia_totales += dias

        print(f"   Días totales de ausencia: {dias_ausencia_totales}")

        # Mostrar top profesores con más ausencias
        if verbose:
            print("\n   Top profesores con más ausencias:")
            profesores_ordenados = sorted(
                ausencias_por_profesor.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )[:5]

            for prof_id, ausencias in profesores_ordenados:
                profesor = self.session.query(Profesor).filter(Profesor.id == prof_id).first()
                if profesor:
                    print(f"      • {profesor.nombre_completo}: {len(ausencias)} ausencia(s)")
                    for aus in ausencias[:2]:
                        print(f"        - {aus.tipo}: {aus.fecha_inicio} a {aus.fecha_fin}")

    def _generar_resumen(self):
        """Genera resumen final con problemas y sugerencias."""
        print("\n📊 RESUMEN EJECUTIVO\n")

        # Problemas críticos
        if self.problemas:
            problemas_criticos = [p for p in self.problemas if p['tipo'] == 'CRÍTICO']
            problemas_altos = [p for p in self.problemas if p['tipo'] == 'ALTO']

            if problemas_criticos:
                print(f"❌ PROBLEMAS CRÍTICOS: {len(problemas_criticos)}")
                for p in problemas_criticos:
                    print(f"\n   • {p['mensaje']}")
                    print(f"     Categoría: {p['categoria']}")
                    print(f"     Impacto: {p['impacto']}")
                    print(f"     💡 SOLUCIÓN: {p['solucion']}")

            if problemas_altos:
                print(f"\n⚠️ PROBLEMAS DE ALTA PRIORIDAD: {len(problemas_altos)}")
                for p in problemas_altos[:3]:
                    print(f"\n   • {p['mensaje']}")
                    print(f"     💡 SOLUCIÓN: {p['solucion']}")

                if len(problemas_altos) > 3:
                    print(f"\n   ... y {len(problemas_altos) - 3} problemas más")
        else:
            print("✅ No se detectaron problemas críticos")

        # Advertencias
        if self.advertencias:
            print(f"\n⚡ ADVERTENCIAS: {len(self.advertencias)}")
            for adv in self.advertencias[:3]:
                print(f"   • {adv['mensaje']}")

        # Métricas clave
        print("\n📈 MÉTRICAS CLAVE:")

        if self.profesores:
            profes_con_guardias = len({g.profesor_id for g in self.guardias})
            pct_participacion = profes_con_guardias / len(self.profesores) * 100
            print(f"   • Participación: {pct_participacion:.1f}% ({profes_con_guardias}/{len(self.profesores)} profesores)")

            if pct_participacion < 80:
                print("     ❌ OBJETIVO: ≥95%")
            elif pct_participacion < 95:
                print("     ⚠️ OBJETIVO: ≥95%")
            else:
                print("     ✅ OBJETIVO CUMPLIDO")

        if self.guardias and self.config and self.recreos_config:
            # Calcular cobertura estimada
            primera = min(g.fecha for g in self.guardias)
            ultima = max(g.fecha for g in self.guardias)
            dias_laborables = sum(1 for d in range((ultima - primera).days + 1)
                                 if (primera + timedelta(days=d)).weekday() < 5)
            slots_estimados = dias_laborables * sum(r.get('zonas', 0) for r in self.recreos_config)
            cobertura = len(self.guardias) / slots_estimados * 100 if slots_estimados > 0 else 0

            print(f"   • Cobertura: {cobertura:.1f}% ({len(self.guardias)}/{slots_estimados} slots)")

            if cobertura < 80:
                print("     ❌ OBJETIVO: ≥95%")
            elif cobertura < 95:
                print("     ⚠️ OBJETIVO: ≥95%")
            else:
                print("     ✅ OBJETIVO CUMPLIDO")

        # Sugerencias finales
        print("\n💡 PRÓXIMOS PASOS RECOMENDADOS:\n")

        if not self.config:
            print("   1. URGENTE: Crear configuración del curso desde la UI")
            print("      → Ir a: Configuración > Curso Escolar")
        elif not self.guardias:
            print("   1. Generar guardias desde la UI")
            print("      → Ir a: Guardias > Generar Calendario")
        else:
            if self.problemas:
                print("   1. Corregir problemas críticos detectados (ver arriba)")

            profes_sin = len([p for p in self.profesores if p.id not in {g.profesor_id for g in self.guardias}])
            if profes_sin > 0:
                print(f"   2. Revisar restricciones de los {profes_sin} profesores sin guardias")
                print("      → Verificar turnos, recreos permitidos, fechas")

            print("   3. Re-generar guardias con restricciones corregidas")
            print("   4. Validar cobertura ≥95% y participación ≥95%")


def main():
    """Función principal."""
    parser = argparse.ArgumentParser(
        description='Diagnóstico completo del sistema de guardias'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    parser.add_argument(
        '--html',
        action='store_true',
        help='Generar reporte HTML (próximamente)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Exportar resultados a JSON (próximamente)'
    )

    args = parser.parse_args()

    # Ejecutar diagnóstico
    session = SessionLocal()
    try:
        diagnostico = DiagnosticoGuardias(session)
        diagnostico.ejecutar(verbose=args.verbose)

        if args.html:
            print("\n⚠️ Exportación HTML no implementada aún")

        if args.json:
            print("\n⚠️ Exportación JSON no implementada aún")

    finally:
        session.close()


if __name__ == "__main__":
    main()
