"""
PROPUESTA: Algoritmo Simple Determinista para Asignación de Guardias
====================================================================

ANÁLISIS DEL PROBLEMA ACTUAL:
- 7 FASES complejas (Ordenamiento, Scoring, CSP, Simulated Annealing, etc.)
- >2000 líneas de código
- Puede dejar slots vacíos y profesores sin guardias
- Difícil de debuggear y mantener

SOLUCIÓN PROPUESTA: Algoritmo en 1 FASE
========================================

Principio: "Asignar profesor por profesor su cuota EXACTA hasta agotar todos"

PSEUDOCÓDIGO:

1. CALCULAR CUOTAS
   ─────────────────
   Para cada profesor:
     cuota = (total_slots / total_profesores) * (jornada_profesor / 100)
   
   Ejemplo: 2768 slots, 75 profesores
     - Profesor jornada 100%: 2768/75 = 37 guardias
     - Profesor jornada 50%: 37 * 0.5 = 18 guardias

2. ORDENAR PROFESORES (por prioridad de asignación)
   ──────────────────────────────────────────────────
   Criterios de ordenación:
   a) Profesores CON restricciones primero (más difíciles)
   b) Menor disponibilidad de slots
   c) Mayor cuota pendiente
   
   Razón: Los profesores más restrictivos deben elegir primero,
          los flexibles pueden adaptarse a los huecos que quedan

3. ASIGNAR PROFESOR POR PROFESOR
   ──────────────────────────────
   Para cada profesor en orden:
     
     slots_disponibles = filtrar_slots_validos(
       - No ocupados aún
       - Cumple horario permitido del profesor
       - No tiene ausencias
       - Cumple restricciones de turno/zona
     )
     
     ordenar_slots_disponibles_por(
       - Fecha (cronológico)
       - Equidad temporal (no saturar días)
       - Preferencia de zona
     )
     
     MIENTRAS (asignadas < cuota_profesor) Y (hay slots disponibles):
       slot = siguiente_slot_optimo(
         que no sature días consecutivos,
         que distribuya por semanas,
         que respete preferencias
       )
       
       asignar_guardia(profesor, slot)
       marcar_slot_ocupado(slot)
       asignadas += 1
     
     SI asignadas < cuota_profesor:
       LOG WARNING: Profesor {nombre} solo {asignadas}/{cuota}
       (Significa restricciones muy severas)

4. VALIDACIÓN FINAL
   ─────────────────
   total_asignadas = contar_guardias()
   slots_vacios = total_slots - total_asignadas
   
   SI slots_vacios > 0:
     LOG ERROR: {slots_vacios} slots sin cubrir
     INTENTAR relajar restricciones o distribuir entre flexibles

VENTAJAS DE ESTE ALGORITMO:
===========================

✅ SIMPLE: 1 fase vs 7 fases
✅ PREDECIBLE: Resultado determinista
✅ COMPLETO: Garantiza intentar llenar todos los slots
✅ EQUITATIVO: Cada profesor recibe su cuota exacta
✅ RÁPIDO: O(P × S) donde P=profesores, S=slots
✅ DEBUGGEABLE: Fácil rastrear por qué X profesor tiene Y guardias
✅ MANTENIBLE: ~200-300 líneas vs ~2000 líneas

EJEMPLO CONCRETO:
================

BD: 66f06c9433d74e80
Total slots: 2768 (173 días × 4 zonas × 4 recreos)
Total profesores: 75

Cuota base: 2768 / 75 = 36.9 guardias/profesor

Profesores:
  1. Ana (100% jornada, solo mañanas, solo zona A)
     Cuota: 37 guardias
     Slots válidos: ~173 × 4 recreos = 692 slots mañana zona A
     
  2. Pedro (50% jornada, sin restricciones)
     Cuota: 18 guardias
     Slots válidos: 2768 slots (cualquiera)

EJECUCIÓN:

1. Ordenar: Ana primero (más restrictiva), Pedro después
   
2. Asignar Ana:
   - Filtrar 692 slots válidos (mañana, zona A)
   - Ordenar cronológicamente
   - Tomar primeros 37 slots
   - Marcar ocupados
   
3. Asignar Pedro:
   - Filtrar 2768 - 37 = 2731 slots libres
   - Ordenar
   - Tomar primeros 18 slots
   - Marcar ocupados

4. ... (continuar con resto de profesores)

RESULTADO ESPERADO:
- 2768 / 2768 slots cubiertos (100%)
- 0 profesores sin guardias
- Distribución exacta según jornada

CASOS EXTREMOS:
==============

1. Profesor con restricciones IMPOSIBLES de cumplir:
   - Ejemplo: Solo trabaja lunes + cuota de 50 guardias
   - Solución: Asignar lo máximo posible, LOG warning

2. Último profesor encuentra todos los slots ocupados:
   - No debería pasar si cuotas suman = total_slots
   - Si pasa: ERROR en cálculo de cuotas

3. Quedan slots sin asignar:
   - Redistribuir entre profesores con más flexibilidad
   - Priorizar profesores con cuota incompleta

IMPLEMENTACIÓN SUGERIDA:
=======================

def generar_guardias_simple(session, config_id):
    # 1. Calcular cuotas
    cuotas = calcular_cuotas_exactas(session, config_id)
    
    # 2. Ordenar profesores
    profesores = ordenar_por_restricciones(session)
    
    # 3. Preparar slots
    todos_slots = generar_todos_slots(config)
    slots_ocupados = set()
    
    # 4. Asignar profesor por profesor
    for profesor in profesores:
        cuota = cuotas[profesor.id]
        
        # Filtrar slots válidos para este profesor
        slots_validos = [
            slot for slot in todos_slots
            if slot not in slots_ocupados
            and cumple_restricciones(profesor, slot)
        ]
        
        # Ordenar por optimalidad
        slots_validos = ordenar_slots_optimos(slots_validos, profesor)
        
        # Tomar exactamente la cuota
        slots_asignar = slots_validos[:cuota]
        
        # Asignar guardias
        for slot in slots_asignar:
            crear_guardia(session, profesor, slot)
            slots_ocupados.add(slot)
    
    # 5. Validar cobertura
    validar_cobertura_completa(session, config_id)

COMPLEJIDAD:
- Tiempo: O(P × S × log S) donde P=profesores, S=slots
  - Ordenar slots: O(S × log S)
  - Para cada profesor: O(S) filtrado
  - Total: O(P × S × log S) = O(75 × 2768 × 11) ≈ 2.2M ops
  - Vs algoritmo actual: 7 fases × múltiples iteraciones

- Espacio: O(S) para índice de slots ocupados
  - 2768 slots = ~11 KB

CONCLUSIÓN:
==========

El algoritmo actual usa técnicas avanzadas (CSP, Simulated Annealing)
que son INNECESARIAS para este problema.

El problema es esencialmente:
"Distribuir N guardias entre P profesores con restricciones"

Esto NO requiere:
❌ Optimización heurística (Simulated Annealing)
❌ Constraint Satisfaction Problem solver
❌ Múltiples fases de refinamiento
❌ Scoring multi-criterio complejo

SÍ requiere:
✅ Cálculo exacto de cuotas
✅ Ordenamiento inteligente de profesores
✅ Asignación determinista
✅ Validación de restricciones

RECOMENDACIÓN: Implementar este algoritmo simple como v3.0
y comparar resultados con v2.9.1

Expected outcome:
- Mismo o mejor equidad
- 100% cobertura garantizada
- Código 10x más simple
- Ejecución más rápida
- Más fácil de entender y mantener
"""
