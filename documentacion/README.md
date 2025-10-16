# 📚 Documentación del Sistema de Guardias de Patio

Bienvenido a la documentación completa del sistema de gestión de guardias de patio.

## 📖 Documentos Disponibles

### 🎯 Requisitos y Condiciones

| Documento | Descripción | Actualización |
|-----------|-------------|---------------|
| **[REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)** | Documento maestro con todos los requisitos funcionales, validaciones críticas y especificaciones técnicas | 15/10/2025 v2.0 |
| **[REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)** | Especificación detallada del requisito de máximo 1 guardia por día por profesor | 15/10/2025 v2.0 |

### � Nuevas Funcionalidades

| Documento | Descripción | Actualización |
|-----------|-------------|---------------|
| **[NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md)** | 📅 Vista Calendario, 📊 Estadísticas, 📄 Exportación PDF, 🔄 Gestión de Sustituciones | 16/10/2025 v2.1 ✨ **NUEVO** |

### �🐛 Soluciones y Fixes

| Documento | Descripción | Actualización |
|-----------|-------------|---------------|
| **[SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)** | Análisis y solución del problema de guardias duplicadas por ejecución múltiple | 15/10/2025 v1.3 |

---

## 🎯 Guía Rápida por Tema

### Si quieres saber sobre...

#### ✅ **Requisitos del Sistema**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)

**Encontrarás:**
- Requisitos funcionales básicos
- CRUD de profesores
- Gestión de guardias
- Configuración del curso

---

#### 🚀 **Nuevas Funcionalidades v2.1**
👉 Lee: [NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md)

**Las 4 nuevas funcionalidades:**

1. **📅 Vista Calendario Mensual**: Visualización interactiva con colores por día
2. **📊 Panel de Estadísticas**: Dashboard con métricas, tablas y gráficos matplotlib
3. **📄 Exportador PDF**: Genera calendarios individuales por profesor (ReportLab)
4. **🔄 Gestor de Sustituciones**: Sistema para reasignar guardias en ausencias

---

#### ⚠️ **Validaciones Críticas**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 2](REQUISITOS_Y_VALIDACIONES.md#validaciones-críticas-del-algoritmo)

**Las 2 validaciones críticas:**

1. **No Duplicidad de Ubicaciones**: Un profesor NO puede estar en dos zonas al mismo tiempo
   - Clave: mismo (día + turno + recreo)
   - Implementación: `guardias_por_slot_prof`

2. **Máximo 1 Guardia por Día**: Un profesor solo hace 1 guardia al día (mañana + tarde)
   - Clave: mismo día (cualquier turno)
   - Implementación: `guardias_por_dia_prof`
   - Detalle: [REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)

---

#### 👨‍🏫 **Restricciones por Profesor**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 3](REQUISITOS_Y_VALIDACIONES.md#restricciones-por-profesor)

**Configurables por profesor:**
- Turno (mañana/tarde/mixto)
- Fecha inicio guardias
- Días de semana permitidos
- Recreos permitidos

---

#### 🐛 **Problema: Guardias Duplicadas**
👉 Lee: [SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)

**Síntoma:** Al ejecutar "Generar Guardias" varias veces, se acumulan guardias duplicadas

**Solución:** Diálogo de confirmación que pregunta si eliminar guardias existentes antes de generar nuevas

---

#### 📊 **Algoritmo de Asignación**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 8](REQUISITOS_Y_VALIDACIONES.md#algoritmo-de-asignación---flujo-completo)

**Flujo completo:**
1. Construcción de slots (día × turno × recreo × zona)
2. Cálculo de cuotas proporcionales
3. Iteración por slot con filtrado de elegibles
4. Scoring y selección del mejor candidato
5. Asignación y registro en base de datos

---

#### 🧪 **Tests y Validación**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 7](REQUISITOS_Y_VALIDACIONES.md#resumen-de-tests)

**Suite de pruebas:**
- 54 tests en total ✅
- Tests específicos:
  - `test_no_duplicados_profesor_mismo_slot.py` - Validación 1
  - `test_max_una_guardia_dia.py` - Validación 2

---

#### 🔧 **Implementación Técnica**
👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 9](REQUISITOS_Y_VALIDACIONES.md#referencias-técnicas)

**Archivos clave:**
- `src/models/models.py` - Modelos de datos
- `src/services/asignador_guardias.py` - Algoritmo principal
- `src/services/calculador_guardias.py` - Cálculos y distribución
- `src/main.py` - Interfaz gráfica (PyQt6)

---

## 📝 Historial de Requisitos

| Fecha | Versión | Requisito | Estado |
|-------|---------|-----------|--------|
| 14/10/2025 | 1.0 | Unificación nombre/apellidos en `nombre_completo` | ✅ Completado |
| 14/10/2025 | 1.1 | CRUD completo de profesores (con edición) | ✅ Completado |
| 15/10/2025 | 1.2 | UI profesional con QGroupBox y CSS | ✅ Completado |
| 15/10/2025 | 1.3 | Fix: Duplicados en mismo slot (Validación 1) | ✅ Completado |
| **15/10/2025** | **2.0** | **Máximo 1 guardia por día (Validación 2)** | ✅ **Completado** |
| **16/10/2025** | **2.1** | **Vista Calendario + Estadísticas + PDF + Sustituciones** | ✅ **Completado** |

---

## 🚀 Inicio Rápido

### Para Desarrolladores

```bash
# 1. Leer documentación principal
cat documentacion/REQUISITOS_Y_VALIDACIONES.md

# 2. Ejecutar tests
source .venv/bin/activate
pytest tests/ -v

# 3. Ejecutar aplicación
python src/main.py
```

### Para Usuarios

1. **Lee primero**: [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md) para entender las reglas del sistema
2. **Nuevas funcionalidades**: [NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md) para descubrir las últimas mejoras ✨
3. **Problema con duplicados?**: [SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)
4. **Duda sobre límite diario?**: [REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)

---

## 📞 Contacto y Soporte

Para dudas sobre:
- **Requisitos funcionales**: Ver sección correspondiente en [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)
- **Bugs conocidos**: Consultar sección de soluciones
- **Nuevos requisitos**: Documentar en este mismo sistema

---

## 📦 Estructura de Documentación

```
documentacion/
├── README.md                              ← Este archivo (índice)
├── REQUISITOS_Y_VALIDACIONES.md          ← Documento maestro
├── REQUISITO_MAX_UNA_GUARDIA_DIA.md      ← Detalle requisito específico
├── NUEVAS_FUNCIONALIDADES_V2_1.md        ← 4 funcionalidades avanzadas ✨
└── SOLUCION_DUPLICADOS_GUARDIAS.md       ← Fix problema conocido
```

---

**Última actualización:** 16 de octubre de 2025  
**Versión del sistema:** 2.1  
**Estado:** ✅ Documentación completa y actualizada
