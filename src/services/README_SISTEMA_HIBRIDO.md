# Sistema Híbrido de Asignación de Guardias

## 📋 Descripción General

Sistema inteligente de asignación de guardias que combina dos algoritmos complementarios:

1. **Algoritmo Iterativo (Opción A)**: Rápido, construye sobre el código actual, múltiples intentos con relajación progresiva
2. **Algoritmo ILP (Opción B)**: Óptimo matemáticamente garantizado usando Programación Lineal Entera

El sistema intenta primero el **algoritmo iterativo** (rápido) y si no logra una solución aceptable:
- Muestra **diagnóstico detallado** al usuario
- Ofrece **opciones**: ajustar manualmente o continuar con ILP
- Si el usuario elige ILP, ejecuta el **algoritmo avanzado**

## 🎯 Flujo de Operación

```
┌─────────────────────────────────────┐
│  1. ALGORITMO ITERATIVO (Rápido)   │
│     • 5 iteraciones progresivas     │
│     • Recalculación de cuotas       │
│     • Relajación automática         │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  2. VALIDACIÓN DEL RESULTADO        │
│     • Cobertura ≥ 95%?              │
│     • Problemas críticos = 0?       │
└──────────────┬──────────────────────┘
               │
        ┌──────┴──────┐
        │             │
    ✅ SÍ          ❌ NO
        │             │
        │             ▼
        │   ┌──────────────────────────┐
        │   │ 3. DIAGNÓSTICO DETALLADO │
        │   │   • Profesores faltantes │
        │   │   • Slots vacíos         │
        │   │   • Causas raíz          │
        │   │   • Sugerencias          │
        │   └──────────┬───────────────┘
        │              │
        │              ▼
        │   ┌──────────────────────────┐
        │   │ 4. DECISIÓN USUARIO      │
        │   │   [Ajustar Manual]       │
        │   │   [Continuar con ILP] ─┐ │
        │   │   [Cancelar]           │ │
        │   └────────────────────────┼─┘
        │                            │
        │                            ▼
        │              ┌─────────────────────────┐
        │              │ 5. ALGORITMO ILP        │
        │              │    • Solución óptima    │
        │              │    • Garantías matemát. │
        │              │    • Diagnóstico infac. │
        │              └─────────┬───────────────┘
        │                        │
        └────────────────────────┘
                       │
                       ▼
            ┌─────────────────┐
            │ RESULTADO FINAL │
            └─────────────────┘
```

## 🗂️ Arquitectura del Sistema

### Componentes Principales

```
src/services/
├── orquestador_asignacion_guardias.py    # Coordinador principal
├── asignador_iterativo.py                # Algoritmo iterativo (Opción A)
├── asignador_ilp.py                      # Algoritmo ILP (Opción B)
├── diagnosticador_guardias.py            # Análisis de problemas
├── validador_guardias.py                 # Validación post-asignación
└── integrador_orquestador_ui.py          # Integración con UI

src/presentation/dialogs/
└── dialogo_diagnostico_guardias.py       # Diálogo para decisión usuario
```

### Clases Principales

#### 1. `OrquestadorAsignacionGuardias`

**Responsabilidad**: Coordinar todo el flujo de asignación con fallback automático.

**Métodos**:
- `generar_guardias_con_fallback()`: Método principal, ejecuta todo el flujo
- `_ejecutar_fase_ilp()`: Ejecuta algoritmo ILP si es necesario

**Retorna**: `ResultadoOrquestacion` con:
- `exitoso`: bool
- `guardias`: List[Guardia]
- `estrategia_usada`: EstrategiaUsada (ITERATIVO, ILP, NINGUNA)
- `diagnostico`: DiagnosticoCompleto
- `requiere_intervencion_usuario`: bool
- `mensaje_usuario`: str

#### 2. `AsignadorIterativo`

**Responsabilidad**: Algoritmo rápido con múltiples intentos y ajustes automáticos.

**Estrategias** (de más estricta a más permisiva):
1. **Estricta**: 10% desbalance, 14 días retraso, 2 días consecutivos
2. **Moderada**: 20% desbalance, 30 días retraso, 3 días consecutivos
3. **Prioridad Cobertura**: 30% desbalance, 45 días retraso, 4 días consecutivos
4. **Permisiva**: 40% desbalance, 60 días retraso, 5 días consecutivos
5. **Máxima Flexibilidad**: 50% desbalance, 90 días retraso, 7 días consecutivos

**Características**:
- Recalculación automática de cuotas basada en capacidad real
- Detección de profesores con déficit sistemático
- Redistribución inteligente de carga

#### 3. `AsignadorILP`

**Responsabilidad**: Solución óptima garantizada usando OR-Tools.

**Variables de Decisión**:
```python
x[profesor_id][fecha][recreo][zona] ∈ {0, 1}
```

**Restricciones Duras** (deben cumplirse):
- R1: Cada slot tiene exactamente 1 profesor (100% cobertura)
- R2: Máximo 1 guardia por profesor por recreo
- R3: Respeto de ausencias
- R4: Compatibilidad de turnos
- R5: Compatibilidad de zonas
- R6: Máximo guardias por día

**Función Objetivo** (se maximiza):
- Minimizar desviación de cuotas (equidad)
- Priorizar fechas de inicio tempranas
- Favorecer guardias consecutivas (agrupamiento)

**Diagnóstico de Infactibilidad**: Si no hay solución, explica por qué:
- Análisis de capacidad por turno
- Profesores disponibles por zona
- Sugerencias específicas

#### 4. `DiagnosticadorGuardias`

**Responsabilidad**: Analizar resultados y generar diagnósticos detallados.

**Tipos de Problemas Detectados**:
- 🔴 **CRÍTICOS**: Profesores sin guardias, slots vacíos
- 🟠 **ALTOS**: Fechas de inicio incumplidas, cuotas incompletas
- 🟡 **MEDIOS**: Desbalances significativos

**Para Cada Problema**:
- Descripción clara
- Causas raíz específicas
- Sugerencias accionables

**Ejemplo de Diagnóstico**:
```
🔴 PROBLEMA CRÍTICO:
3 profesor(es) sin guardias en turno 'tarde'

CAUSAS:
• ⚠️  CRÍTICO: No hay suficientes slots en turno 'tarde'
• 2 profesores con excesivas ausencias

SUGERENCIAS:
• Añadir más recreos en turno tarde
• Reducir ausencias de profesores específicos
• Desactivar profesores innecesarios en este turno
```

#### 5. `DialogoDiagnosticoGuardias`

**Responsabilidad**: Interfaz gráfica para mostrar diagnóstico y obtener decisión.

**Elementos UI**:
- Título con resumen de estadísticas
- Secciones por gravedad (críticos, altos, medios)
- Sugerencias específicas por problema
- Botones de acción:
  - 📝 **Ajustar Manualmente**: Volver a configuración
  - 🎯 **Continuar con ILP**: Usar algoritmo avanzado
  - ❌ **Cancelar**: Abortar operación

## 🚀 Uso del Sistema

### Desde la UI (PyQt6)

```python
from src.services.integrador_orquestador_ui import IntegradorOrquestadorUI

# En tu formulario o ventana
integrador = IntegradorOrquestadorUI(db, self)
resultado = integrador.generar_guardias_inteligente()

if resultado.exitoso:
    # Guardar guardias
    db.query(Guardia).delete()
    db.add_all(resultado.guardias)
    db.commit()
    
    QMessageBox.information(self, "Éxito", resultado.mensaje_usuario)
else:
    QMessageBox.warning(self, "Atención", resultado.mensaje_usuario)
```

### Desde CLI (Script)

```python
from src.services.orquestador_asignacion_guardias import OrquestadorAsignacionGuardias

orquestador = OrquestadorAsignacionGuardias(db, config, dias_lectivos)

def decision_usuario(diagnostico):
    print(diagnostico.mensaje_resumen)
    opcion = input("¿Ajustar (1), ILP (2), o Cancelar (3)? ")
    return {'1': 'ajustar', '2': 'continuar_ilp', '3': 'cancelar'}[opcion]

resultado = orquestador.generar_guardias_con_fallback(
    callback_decision_usuario=decision_usuario
)

if resultado.exitoso:
    db.add_all(resultado.guardias)
    db.commit()
```

### Personalización de Umbrales

```python
resultado = orquestador.generar_guardias_con_fallback(
    umbral_cobertura_minima=0.98,      # 98% mínimo
    umbral_problemas_criticos=0,       # Cero problemas críticos
    callback_decision_usuario=mi_callback
)
```

## 📊 Métricas y Estadísticas

El sistema retorna estadísticas completas:

```python
{
    'total_guardias_asignadas': 2423,
    'total_slots_esperados': 2516,
    'cobertura_porcentaje': 96.3,
    'profesores_con_guardias': 64,
    'profesores_activos_totales': 67,
    'participacion_porcentaje': 95.5,
    
    # Si se usó ILP:
    'tiempo_solucion': 12.3,  # segundos
    'desviacion_cuota_promedio': 0.05,
    'desviacion_cuota_maxima': 0.15
}
```

## 🔧 Instalación y Configuración

### Dependencias

```bash
# Básico (solo algoritmo iterativo)
pip install sqlalchemy pyqt6

# Completo (con ILP)
pip install sqlalchemy pyqt6 ortools
```

### Configuración en `requirements.txt`

```text
# Añadir al final:
ortools>=9.7.0  # Para algoritmo ILP
```

### Verificar Instalación

```python
from src.services.asignador_ilp import ORTOOLS_DISPONIBLE

if ORTOOLS_DISPONIBLE:
    print("✅ ILP disponible")
else:
    print("⚠️  Solo algoritmo iterativo disponible")
    print("   Instalar: pip install ortools")
```

## 🎨 Ejemplos de Salida

### Mensaje de Éxito (Iterativo)

```
✅ ASIGNACIÓN COMPLETADA CON ÉXITO

🚀 Estrategia: Algoritmo Iterativo (Rápido)
   Iteración exitosa: 2

📊 Resultado:
   • Guardias asignadas: 2450 de 2516
   • Cobertura: 97.4%
   • Participación: 66/67 profesores

ℹ️  Se detectaron 3 problema(s) menor(es)
   (no afectan la validez de la asignación)
```

### Mensaje de Éxito (ILP)

```
✅ ASIGNACIÓN COMPLETADA CON ÉXITO

🎯 Estrategia: ILP - Solución Óptima Matemática
   Tiempo de cálculo: 18.3s

📊 Resultado:
   • Guardias asignadas: 2516 de 2516
   • Cobertura: 100.0%
   • Participación: 67/67 profesores
```

### Diagnóstico de Problemas

```
⚠️  LA ASIGNACIÓN REQUIERE SU ATENCIÓN

🔴 2 problema(s) crítico(s) detectado(s)
🟠 5 problema(s) importante(s) detectado(s)

Opciones:
  1. Revisar y ajustar configuración manualmente
     (disponibilidades, zonas, recreos, ausencias)
  2. Continuar con algoritmo ILP avanzado
     (garantiza solución óptima si existe)
```

## 🧪 Testing

```bash
# Test completo del sistema
python -m pytest tests/test_orquestador_asignacion.py -v

# Test solo algoritmo iterativo
python -m pytest tests/test_asignador_iterativo.py -v

# Test solo ILP (requiere ortools)
python -m pytest tests/test_asignador_ilp.py -v

# Test diagnóstico
python -m pytest tests/test_diagnosticador_guardias.py -v
```

## 📝 Logs y Debugging

El sistema genera logs detallados:

```python
import logging

# Configurar nivel de detalle
logging.basicConfig(level=logging.INFO)

# Para debug completo
logging.getLogger('src.services.orquestador_asignacion_guardias').setLevel(logging.DEBUG)
logging.getLogger('src.services.asignador_ilp').setLevel(logging.DEBUG)
```

## ⚡ Performance

| Algoritmo  | Tiempo Típico | Cobertura     | Equidad       |
|------------|---------------|---------------|---------------|
| Iterativo  | 5-15 seg      | 95-98%        | Buena         |
| ILP        | 30-300 seg    | 100% (si hay) | Óptima        |

**Recomendación**: El sistema automático es la mejor opción:
- Intenta iterativo primero (rápido)
- Solo usa ILP cuando es necesario
- Ofrece diagnóstico claro al usuario

## 🐛 Solución de Problemas

### ILP no encuentra solución

**Causa**: El problema es matemáticamente infactible.

**Solución**: El sistema muestra diagnóstico específico:
```
❌ DIAGNÓSTICO DE INFACTIBILIDAD

1. Capacidad total necesaria: 2516 slots
   • Turno 'tarde': 800 slots, 12 profesores disponibles
     ❌ CRÍTICO: Insuficientes profesores en turno 'tarde'

Sugerencias:
   • Aumentar número de profesores activos en turno 'tarde'
   • Ampliar disponibilidad de turnos
   • Reducir número de recreos en tarde
```

### Iterativo da baja cobertura

**Causa**: Restricciones muy estrictas.

**Solución**: El sistema intenta 5 iteraciones con relajación progresiva.
Si no mejora, muestra diagnóstico detallado y ofrece usar ILP.

### Performance lenta en ILP

**Causa**: Problema muy grande (muchos días/profesores/zonas).

**Solución**:
- Aumentar `limite_tiempo_segundos` (por defecto 300s)
- El solver puede dar solución "factible" antes de "óptima"
- Considerar reducir días/zonas si es posible

## 📚 Documentación Adicional

- [PREMISAS_ASIGNACION_GUARDIAS_ACTUAL.md](../documentacion/PREMISAS_ASIGNACION_GUARDIAS_ACTUAL.md): Premisas exactas del algoritmo
- [TECHNICAL_GUIDE.md](../documentacion/TECHNICAL_GUIDE.md): Guía técnica general
- [API ILP](./asignador_ilp.py): Documentación del modelado matemático

## 🤝 Contribuir

Al modificar el sistema, asegúrate de:
1. Mantener compatibilidad con ambos algoritmos
2. Actualizar tests correspondientes
3. Documentar cambios en premisas si aplica
4. Probar con datos reales del colegio

## 📄 Licencia

Ver [LICENSE](../../LICENSE)
