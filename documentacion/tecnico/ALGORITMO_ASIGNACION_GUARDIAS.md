# 🧮 Algoritmo de Asignación de Guardias - Documentación Completa

![Status](https://img.shields.io/badge/Status-Consolidado-success.svg)
![Versión](https://img.shields.io/badge/Versión-Pasada_6-blue.svg)
![Tipo](https://img.shields.io/badge/Tipo-Documentación_Técnica-orange.svg)
![Última Actualización](https://img.shields.io/badge/Última_Actualización-Nov_2025-green.svg)

> 📦 **Documento Consolidado**: Este archivo reemplaza 4 documentos sobre algoritmos

Este documento consolida toda la información sobre el algoritmo de asignación de guardias del proyecto.

**Documentos originales archivados:**
- `ALGORITMO_PASADA_6.md`
- `INTEGRACION_ALGORITMO_V3.md`
- `RESUMEN_EJECUTIVO_ALGORITMO_V3.md`
- `PROPUESTA_ALGORITMO_SIMPLE.md`

---

## 📋 Índice

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Algoritmo Pasada 6 (Implementación Actual)](#algoritmo-pasada-6)
3. [Integración en la Aplicación](#integración-en-la-aplicación)
4. [Propuestas Alternativas](#propuestas-alternativas)

---

## 1. Resumen Ejecutivo

### Estado Actual
- **Versión:** v3.0 (Algoritmo Pasada 6)
- **Implementación:** `src/services/asignador_guardias.py`
- **Estado:** ✅ En producción y funcionando
- **Rendimiento:** ~2.5 segundos para 169 días con 67 profesores

### Características Principales
✅ Distribución equitativa de guardias  
✅ Respeto de disponibilidad de profesores  
✅ Balance entre turnos (mañana/tarde)  
✅ Gestión de ausencias y sustituciones  
✅ Optimización de rendimiento con caché  
✅ Validaciones de negocio completas  

---

## 2. Algoritmo Pasada 6 (Implementación Actual)

### Descripción General

El Algoritmo Pasada 6 es un sistema de asignación iterativo que realiza múltiples pasadas sobre los días lectivos para distribuir las guardias de forma equitativa.

### Flujo Principal

```
1. PREPARACIÓN
   ├── Cargar configuración (fechas, recreos, zonas)
   ├── Identificar días lectivos (excluir festivos)
   ├── Cargar profesores activos
   └── Calcular cuotas ideales por profesor

2. PASADAS ITERATIVAS (1-6)
   ├── Pasada 1: Asignación inicial greedy
   ├── Pasada 2: Balance de carga básico
   ├── Pasada 3: Ajuste de turnos
   ├── Pasada 4: Relleno de huecos
   ├── Pasada 5: Optimización de equidad
   └── Pasada 6: Refinamiento final

3. VALIDACIÓN
   ├── Verificar cobertura (>95%)
   ├── Validar equidad (desviación <15%)
   ├── Comprobar restricciones de negocio
   └── Generar informe de resultados
```

### Pasadas Detalladas

#### Pasada 1: Asignación Inicial Greedy
```python
Para cada día lectivo:
    Para cada recreo del día:
        Para cada zona del recreo:
            # Seleccionar profesor con menos guardias asignadas
            profesor = obtener_profesor_con_menos_guardias(
                turno=recreo.turno,
                disponible_en=día,
                zona=zona
            )
            asignar_guardia(profesor, día, recreo, zona)
```

**Criterios de selección:**
- Menor número de guardias asignadas
- Disponibilidad en el turno (mañana/tarde)
- No tiene ausencia en la fecha
- No ha alcanzado el límite diario (8 guardias)

#### Pasada 2: Balance de Carga
```python
# Identificar profesores sobrecargados (>110% cuota)
profesores_sobrecargados = []
for profesor in profesores:
    if profesor.guardias_asignadas > cuota_ideal * 1.1:
        profesores_sobrecargados.append(profesor)

# Redistribuir guardias
for profesor in profesores_sobrecargados:
    guardias_a_reubicar = seleccionar_guardias_menos_conflictivas(profesor)
    for guardia in guardias_a_reubicar:
        profesor_alternativo = encontrar_profesor_con_menos_carga(
            mismo_turno=guardia.turno,
            misma_zona=guardia.zona,
            disponible=guardia.fecha
        )
        reasignar_guardia(guardia, profesor_alternativo)
```

#### Pasada 3: Ajuste de Turnos
```python
# Balancear guardias entre mañana y tarde
for profesor in profesores_mixto:  # Profesores con turno "mixto"
    ratio_manana = profesor.guardias_manana / profesor.total_guardias
    ratio_tarde = profesor.guardias_tarde / profesor.total_guardias
    
    if abs(ratio_manana - 0.5) > 0.15:  # Desbalance >15%
        # Reubicar guardias del turno excedente al deficitario
        balancear_turnos(profesor)
```

#### Pasada 4: Relleno de Huecos
```python
# Rellenar slots sin asignar
slots_vacios = obtener_slots_sin_profesor()
for slot in slots_vacios:
    candidatos = obtener_profesores_disponibles(
        turno=slot.turno,
        fecha=slot.fecha,
        zona=slot.zona,
        con_cuota_disponible=True
    )
    
    if candidatos:
        # Priorizar profesor con menos guardias
        profesor = min(candidatos, key=lambda p: p.guardias_asignadas)
        asignar_guardia(profesor, slot)
    else:
        # Marcar como no cubierto (warning)
        slots_sin_cubrir.append(slot)
```

#### Pasada 5: Optimización de Equidad
```python
# Minimizar desviación estándar de guardias asignadas
objetivo_desviacion = 0.15  # Máximo 15% de desviación

while desviacion_actual > objetivo_desviacion and iteraciones < max_iter:
    # Identificar extremos
    profesor_max = profesor_con_mas_guardias()
    profesor_min = profesor_con_menos_guardias()
    
    # Buscar intercambio factible
    guardia_candidata = seleccionar_guardia_intercambiable(
        desde=profesor_max,
        hacia=profesor_min
    )
    
    if guardia_candidata and es_intercambio_valido(guardia_candidata):
        intercambiar_guardia(profesor_max, profesor_min, guardia_candidata)
        desviacion_actual = calcular_desviacion()
    
    iteraciones += 1
```

#### Pasada 6: Refinamiento Final
```python
# Aplicar heurísticas finales
for profesor in profesores:
    # Evitar guardias consecutivas en el mismo día
    for dia in dias_lectivos:
        guardias_dia = profesor.guardias_en(dia)
        if len(guardias_dia) > 1:
            # Intentar distribuir entre profesores sin guardias ese día
            intentar_redistribuir_guardias_dia(profesor, dia)
    
    # Distribuir guardias uniformemente en el periodo
    densidad_guardias = analizar_densidad_temporal(profesor)
    if densidad_guardias.tiene_clusters:
        suavizar_distribucion(profesor)
```

### Cálculo de Cuota Ideal

```python
def calcular_cuota_ideal(profesor, config):
    """
    Calcula guardias ideales que debería tener un profesor.
    
    Fórmula:
        cuota = (total_slots_periodo / suma_horas_contrato) * horas_profesor
    
    Donde:
        - total_slots_periodo = días_lectivos * recreos_por_día * zonas
        - suma_horas_contrato = sum(p.horas_contrato for p in profesores_activos)
        - horas_profesor = profesor.horas_contrato
    """
    dias_lectivos = config.calcular_dias_lectivos()
    recreos_por_dia = len(config.recreos_mañana) + len(config.recreos_tarde)
    zonas = session.query(Zona).filter(Zona.activa == True).count()
    
    total_slots = dias_lectivos * recreos_por_dia * zonas
    
    profesores_activos = session.query(Profesor).filter(
        Profesor.activo == True
    ).all()
    suma_horas = sum(p.horas_contrato for p in profesores_activos)
    
    cuota = (total_slots / suma_horas) * profesor.horas_contrato
    
    return round(cuota, 2)
```

### Validaciones de Negocio

```python
class ValidadorGuardias:
    """Valida restricciones de negocio en asignaciones."""
    
    def validar_asignacion(self, guardia):
        """Valida una asignación antes de confirmarla."""
        errores = []
        
        # 1. Profesor activo
        if not guardia.profesor.activo:
            errores.append("Profesor inactivo")
        
        # 2. Sin ausencias
        if tiene_ausencia(guardia.profesor, guardia.fecha):
            errores.append("Profesor ausente en la fecha")
        
        # 3. Disponibilidad de turno
        if not es_turno_compatible(guardia.profesor.turno, guardia.turno):
            errores.append("Turno incompatible")
        
        # 4. Límite diario (máx 8 guardias/día)
        guardias_dia = contar_guardias_dia(guardia.profesor, guardia.fecha)
        if guardias_dia >= 8:
            errores.append("Límite diario excedido (8)")
        
        # 5. No duplicados
        if existe_guardia_igual(guardia):
            errores.append("Guardia duplicada")
        
        return len(errores) == 0, errores
```

### Optimizaciones de Rendimiento

1. **Caché de Consultas**
   ```python
   # Cache de profesores activos (evita 169 queries)
   profesores_cache = {p.id: p for p in profesores_activos}
   
   # Cache de días con ausencias (evita N+1)
   ausencias_por_profesor = defaultdict(set)
   for ausencia in ausencias:
       fechas = generar_fechas_entre(ausencia.inicio, ausencia.fin)
       ausencias_por_profesor[ausencia.profesor_id].update(fechas)
   ```

2. **Bulk Inserts**
   ```python
   # En lugar de session.add() por cada guardia
   guardias_batch = []
   for dia in dias:
       for recreo in recreos:
           for zona in zonas:
               guardia = crear_guardia(...)
               guardias_batch.append(guardia)
   
   session.bulk_save_objects(guardias_batch)
   session.commit()  # Una sola transacción
   ```

3. **Índices de BD**
   ```sql
   CREATE INDEX idx_guardia_profesor ON guardias(profesor_id);
   CREATE INDEX idx_guardia_fecha ON guardias(fecha);
   CREATE INDEX idx_guardia_config ON guardias(configuracion_id);
   CREATE INDEX idx_ausencia_profesor ON ausencias(profesor_id);
   ```

### Métricas de Calidad

```python
def calcular_metricas(guardias):
    """Calcula métricas de calidad de la asignación."""
    return {
        'cobertura': (slots_cubiertos / total_slots) * 100,
        'equidad': 1 - desviacion_estandar(guardias_por_profesor),
        'balance_turnos': ratio_manana / ratio_tarde,  # Ideal: ~1.0
        'profesores_sin_guardias': count(prof.guardias == 0),
        'desviacion_cuota': max(abs(real - ideal) / ideal * 100),
    }
```

**Objetivos:**
- Cobertura: ≥ 95%
- Equidad: ≥ 0.85 (desviación ≤ 15%)
- Balance turnos: 0.9 - 1.1
- Sin guardias: 0 profesores
- Desviación cuota: ≤ 20%

---

## 3. Integración en la Aplicación

### Ubicación del Código

```
src/services/
├── asignador_guardias.py       # Algoritmo principal
├── generador_guardias.py       # Lógica de negocio
└── validators/
    └── guardia_validator.py    # Validaciones
```

### Punto de Entrada

```python
# src/services/asignador_guardias.py
def generar_guardias(session, configuracion_id):
    """
    Genera guardias para una configuración.
    
    Args:
        session: Sesión de SQLAlchemy
        configuracion_id: ID de la configuración
    
    Returns:
        dict: {
            'exito': bool,
            'cobertura': float,
            'equidad': float,
            'guardias_generadas': int,
            'errores': list
        }
    """
```

### Uso desde UI

```python
# src/presentation/forms/asignacion_guardias_form.py
class AsignacionGuardiasForm(BaseForm):
    def generar_guardias_action(self):
        """Ejecuta generación de guardias."""
        try:
            config = self.obtener_configuracion()
            
            # Ejecutar con indicador de progreso
            resultado = ejecutar_con_progreso(
                funcion=generar_guardias,
                args=(self.session, config.id),
                mensaje="Generando guardias..."
            )
            
            if resultado['exito']:
                self.mostrar_resultado_exitoso(resultado)
            else:
                self.mostrar_errores(resultado['errores'])
        
        except Exception as e:
            self.manejar_excepcion(e, "generar guardias")
```

---

## 4. Propuestas Alternativas

### Algoritmo Simple (Propuesta Archivada)

**Concepto:** Asignación greedy en una sola pasada.

```python
def asignar_simple(dias, profesores, zonas):
    """Asignación greedy simple."""
    for dia in dias:
        for recreo in dia.recreos:
            for zona in zonas:
                # Seleccionar profesor con menos guardias
                profesor = min(profesores, key=lambda p: p.guardias)
                asignar(profesor, dia, recreo, zona)
```

**Ventajas:**
- Muy rápido (~0.5 segundos)
- Código simple y fácil de entender

**Desventajas:**
- Equidad pobre (~60%)
- No respeta disponibilidad de turnos
- No maneja ausencias
- Distribución temporal irregular

**Estado:** ❌ Archivada (ver `documentacion/archivo/PROPUESTA_ALGORITMO_SIMPLE.md`)

---

## 📊 Comparativa de Rendimiento

| Métrica | Pasada 6 | Simple |
|---------|----------|--------|
| Tiempo ejecución | 2.5s | 0.5s |
| Cobertura | 98% | 100% |
| Equidad | 92% | 60% |
| Respeta turnos | ✅ | ❌ |
| Gestiona ausencias | ✅ | ❌ |
| Balance temporal | ✅ | ❌ |

---

## 🔧 Mantenimiento y Mejoras Futuras

### Posibles Optimizaciones
1. Paralelizar pasadas independientes
2. Usar algoritmos genéticos para Pasada 5
3. Machine Learning para predecir mejores asignaciones
4. Cache persistente de cuotas calculadas

### Puntos de Mejora Identificados
- [ ] Reducir tiempo de ejecución a <1 segundo
- [ ] Mejorar equidad al 95%+
- [ ] Soportar zonas con diferente prioridad
- [ ] Añadir preferencias de profesores (opcional)

---

**Última actualización:** 1 de Noviembre de 2025  
**Versión del algoritmo:** v3.0 (Pasada 6)  
**Estado:** ✅ En producción
