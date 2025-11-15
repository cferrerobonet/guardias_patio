# 🔄 PLAN DE REFACTORIZACIÓN V2 - VALIDACIÓN INTEGRAL

**Fecha inicio:** 10 de noviembre de 2025  
**Estado:** 🟢 EN EJECUCIÓN  
**Objetivo:** Validar funcionamiento completo tras implementación de nuevas funcionalidades

---

## 📊 CONTEXTO DEL REINICIO

### ¿Por qué reiniciar el plan?

Durante la ejecución del plan original se implementaron múltiples funcionalidades nuevas y mejoras de UX que **NO** estaban contempladas:

- ✅ Sistema multi-curso completo
- ✅ Indicadores visuales de zonas sin guardia
- ✅ Sombreado de días no lectivos
- ✅ Gestión de cursos con 11 columnas estadísticas
- ✅ Refrescado automático de datos
- ✅ Migraciones de BD para multi-curso
- ✅ Filtrado por curso activo en calendario

**Resultado:** Necesitamos validar SISTEMÁTICAMENTE que todo funciona correctamente juntos.

---

## 🔍 PROBLEMAS DETECTADOS QUE MOTIVARON EL REINICIO

### 1. ⚠️ Estadísticas en Gestión de Cursos
- **Problema:** Tabla mostraba valores incorrectos/cacheados
- **Causa:** Configuración no vinculada correctamente, sesión no refrescada
- **Estado:** 🟡 PARCIALMENTE RESUELTO
- **Pendiente:** Validar tras generar guardias reales

### 2. ⚠️ Base de Datos sin Guardias
- **Problema:** BD tiene 0 guardias (limpiadas y no regeneradas)
- **Esperado:** 2400+ guardias con 67 profesores y 4 zonas
- **Estado:** 🔴 BLOQUEANTE para validación

### 3. ⚠️ Relación Configuración-Curso
- **Problema:** Código buscaba `curso_id` pero debe ser `curso_activo_id`
- **Estado:** ✅ RESUELTO

### 4. ⚠️ Columna `cerrado` faltante
- **Problema:** Migración no la creó inicialmente
- **Estado:** ✅ RESUELTO (agregada manualmente)

---

## 🎯 OBJETIVOS DE ESTA VERSIÓN

### Objetivo Principal
**Validar que TODAS las funcionalidades (viejas y nuevas) funcionan correctamente juntas**

### Objetivos Secundarios
1. ✅ Documentar cambios no planificados
2. ✅ Detectar bugs de integración
3. ✅ Asegurar calidad del código
4. ✅ Verificar migraciones de BD
5. ✅ Validar UX completa

---

## 📋 INVENTARIO DE FUNCIONALIDADES A VALIDAR

### 🆕 Funcionalidades Nuevas (Implementadas durante refactorización)

#### Sistema Multi-Curso
- [ ] Crear curso escolar
- [ ] Activar/desactivar cursos
- [ ] Cerrar cursos
- [ ] Eliminar cursos
- [ ] Migración automática de datos entre cursos
- [ ] Filtrado de guardias por curso activo
- [ ] Estadísticas por curso

#### Gestión de Cursos (11 columnas)
- [ ] Columna: Días Lectivos (calculados)
- [ ] Columna: Guardias Calculadas
- [ ] Columna: Guardias Asignadas
- [ ] Columna: Guardias Sin Asignar (rojo si > 0)
- [ ] Columna: Profesores (únicos con guardias)
- [ ] Columna: Zonas (únicas con guardias)
- [ ] Refrescado automático al mostrar widget
- [ ] Encabezados abreviados legibles

#### Calendario con Indicadores Visuales
- [ ] Mostrar zonas sin guardia (fondo rojo, ⚠️)
- [ ] Solo en días lectivos (no festivos/fines de semana)
- [ ] Sombreado gris para días no lectivos
- [ ] Leyenda actualizada
- [ ] Modal de detalle con mismo sistema
- [ ] Filtrado por curso activo

#### Ajustes de Configuración
- [ ] Algoritmo v3.0 como solo lectura (sin selector)
- [ ] Estilo visual actualizado

#### UX Mejorada
- [ ] Botones CRUD alineados a la derecha
- [ ] Tabla responsive (stretch columns)
- [ ] Tooltips informativos

### 🔧 Funcionalidades Existentes (A revalidar)

#### Core - Asignación de Guardias
- [ ] Calcular distribución de guardias
- [ ] Generar guardias (algoritmo v3.0)
- [ ] Limpieza de guardias
- [ ] Cálculo de estadísticas
- [ ] Detección de incidencias
- [ ] Guardias sin cubrir

#### Gestión de Profesores
- [ ] CRUD completo de profesores
- [ ] Marcar como tutores
- [ ] Horas mañana/tarde
- [ ] Zona preferida
- [ ] Email corporativo
- [ ] Activar/desactivar profesores

#### Gestión de Zonas
- [ ] CRUD completo de zonas
- [ ] Fechas inicio/fin
- [ ] Activar/desactivar zonas

#### Ausencias y Sustituciones
- [ ] Crear ausencias
- [ ] Gestionar ausencias
- [ ] Sustituciones automáticas
- [ ] Calendario de ausencias

#### Configuración
- [ ] Fechas del curso
- [ ] Recreos (mañana/tarde)
- [ ] Festivos automáticos/personalizados
- [ ] Ajustes tutores/no tutores
- [ ] Días lectivos calculados

#### Exportación
- [ ] Exportar a Excel
- [ ] Exportar a PDF
- [ ] Exportar calendario ICS
- [ ] Imprimir calendario

#### Perfiles Multi-Usuario
- [ ] Login de usuarios
- [ ] BD independiente por usuario
- [ ] Logos corporativos
- [ ] Cambio de contraseña

---

## 🚀 PLAN DE EJECUCIÓN

### FASE 1: PREPARACIÓN (30 min)
**Objetivo:** Dejar sistema listo para validación completa

#### 1.1 Verificar Migraciones
```bash
cd alembic
alembic current
alembic upgrade head
```
- [ ] Verificar migración `d1e2f3a4b5c6` aplicada
- [ ] Confirmar columna `curso_id` en guardias
- [ ] Confirmar columna `cerrado` en cursos_escolares

#### 1.2 Generar Datos de Prueba
- [ ] Verificar que hay 67 profesores
- [ ] Verificar que hay 4 zonas
- [ ] Verificar que hay 2 cursos (2025/2026 activo, 2024/2025 cerrado)
- [ ] Verificar configuración asociada al curso activo

#### 1.3 Generar Guardias Completas
- [ ] Ir a "Asignación de Guardias"
- [ ] Calcular Distribución
- [ ] Generar Asignación (eliminar existentes: SÍ)
- [ ] Verificar ~2400 guardias generadas
- [ ] Verificar 0 slots sin cubrir

**Criterio de éxito:** BD con guardias reales para validar todo el sistema

---

### FASE 2: VALIDACIÓN DE FUNCIONALIDADES NUEVAS (1 hora)

#### 2.1 Sistema Multi-Curso

**Test 1: Gestión de Cursos**
- [ ] Abrir "Configuración" → "Gestión de Cursos"
- [ ] Verificar tabla con 11 columnas
- [ ] Verificar datos del curso activo (2025/2026):
  - Días Lect. = 195
  - G. Calc. ≈ 2400
  - G. Asig. ≈ 2400
  - G. Sin Asig. = 0
  - Profs. ≈ 64-67
  - Zonas = 4
- [ ] Verificar curso cerrado muestra todo en 0

**Test 2: Crear Nuevo Curso**
- [ ] Click "➕ Crear Nuevo Curso"
- [ ] Rellenar: 2026/2027, fechas futuras
- [ ] Guardar
- [ ] Verificar aparece en tabla
- [ ] Verificar NO está activo

**Test 3: Activar Curso Diferente**
- [ ] Seleccionar curso 2024/2025
- [ ] Click "⭐ Activar"
- [ ] Confirmar desactivación del actual
- [ ] Verificar ⭐ cambia de curso
- [ ] Ir a Calendario → debe estar VACÍO
- [ ] Volver a activar 2025/2026

**Test 4: Cerrar Curso**
- [ ] Seleccionar curso 2026/2027
- [ ] Click "🔒 Cerrar"
- [ ] Confirmar
- [ ] Verificar estado = "Cerrado"

**Test 5: Eliminar Curso**
- [ ] Seleccionar curso cerrado
- [ ] Click "🗑️ Eliminar"
- [ ] Confirmar doble confirmación
- [ ] Verificar desaparece de tabla

#### 2.2 Calendario con Indicadores Visuales

**Test 6: Zonas Sin Guardia**
- [ ] Ir a "Calendario"
- [ ] Vista Mensual, navegar a Marzo 2026
- [ ] Verificar días con zonas sin guardia muestran:
  - Fondo rojo
  - Texto "⚠️ Zona X - SIN GUARDIA"
- [ ] Verificar NO aparece en festivos/fines de semana

**Test 7: Días No Lectivos**
- [ ] En calendario, verificar fines de semana:
  - Fondo gris (#F5F5F5)
  - Sin indicadores de zonas faltantes
- [ ] Verificar días festivos igual

**Test 8: Modal de Detalle**
- [ ] Click en un día con zona sin guardia
- [ ] Verificar modal muestra badge rojo
- [ ] Verificar texto "⚠️ SIN GUARDIA ASIGNADA"

**Test 9: Filtrado por Curso**
- [ ] Con curso 2025/2026 activo, verificar calendario lleno
- [ ] Activar curso 2024/2025 (sin guardias)
- [ ] Verificar calendario vacío
- [ ] Re-activar 2025/2026, verificar calendario lleno

#### 2.3 UX Mejoradas

**Test 10: Botones CRUD**
- [ ] Gestión de Cursos: botones alineados derecha ✅
- [ ] Gestión de Perfiles: botones alineados derecha ✅
- [ ] Gestión de Profesores: verificar alineación
- [ ] Gestión de Zonas: verificar alineación

**Test 11: Tabla Responsive**
- [ ] Gestión de Cursos: redimensionar ventana
- [ ] Verificar columnas se ajustan proporcionalmente
- [ ] Verificar textos no se cortan

---

### FASE 3: VALIDACIÓN DE FUNCIONALIDADES EXISTENTES (1 hora)

#### 3.1 Asignación de Guardias

**Test 12: Flujo Completo**
- [ ] Limpiar todas las guardias
- [ ] Calcular distribución
- [ ] Verificar estadísticas correctas
- [ ] Generar asignación
- [ ] Verificar progreso funciona
- [ ] Verificar resumen correcto
- [ ] Verificar calendario se actualiza

**Test 13: Incidencias**
- [ ] Después de generar, verificar panel de incidencias
- [ ] Verificar slots sin cubrir = 0
- [ ] Verificar resumen por profesor

#### 3.2 Gestión de Profesores

**Test 14: CRUD Profesores**
- [ ] Crear nuevo profesor
- [ ] Editar profesor existente
- [ ] Marcar como tutor
- [ ] Cambiar zona preferida
- [ ] Desactivar profesor
- [ ] Verificar no aparece en próxima generación

#### 3.3 Ausencias y Sustituciones

**Test 15: Crear Ausencia**
- [ ] Seleccionar profesor con guardias
- [ ] Crear ausencia para fechas futuras
- [ ] Verificar aparece en calendario
- [ ] Verificar genera sustituciones

#### 3.4 Exportación

**Test 16: Exportar**
- [ ] Exportar a Excel
- [ ] Exportar a PDF
- [ ] Exportar ICS
- [ ] Verificar archivos descargados correctamente

---

### FASE 4: TESTING AUTOMATIZADO (30 min)

#### 4.1 Ejecutar Suite de Tests
```bash
pytest tests/ -v --tb=short
```
- [ ] Verificar tests pasan
- [ ] Identificar tests rotos
- [ ] Documentar fallos

#### 4.2 Cobertura de Código
```bash
pytest tests/ --cov=src --cov-report=html
```
- [ ] Generar reporte
- [ ] Verificar cobertura > 70%
- [ ] Identificar áreas sin tests

---

### FASE 5: BUGS Y FIXES (según necesidad)

#### 5.1 Lista de Bugs Encontrados
| # | Descripción | Severidad | Estado |
|---|-------------|-----------|--------|
| 1 | Estadísticas en 0 con datos | 🔴 Alta | ✅ Resuelto |
| 2 | Configuración sin curso_id | 🔴 Alta | ✅ Resuelto |
| 3 | Columna cerrado faltante | 🟡 Media | ✅ Resuelto |
| 4 | App crashea al crear curso con copiar_profesores=True | 🔴 Alta | ✅ Resuelto |
| 5 | AttributeError: 'label_fechas' no existe al crear diálogo | 🔴 Alta | ✅ Resuelto |
| 6 | QMessageBox sin botones visibles en macOS | 🔴 Crítica | ✅ Resuelto |

**Bug #4 - Detalles:**
- **Causa:** Método `copiar_profesores_curso_anterior` intenta filtrar/copiar profesores pero el modelo `Profesor` no tiene relación `curso_id` aún (TODOs pendientes)
- **Solución:** Deshabilitar temporalmente el checkbox "Copiar profesores" hasta que se implemente la relación Profesor-Curso
- **Archivos modificados:** `dialogo_crear_curso.py` (líneas 95-99, 151-154)
- **Impacto:** Usuario debe agregar profesores manualmente a cada curso nuevo

**Bug #5 - Detalles:**
- **Causa:** En `_inicializar_ui()` se llamaba a `_actualizar_preview()` ANTES de crear `self.label_fechas`, causando AttributeError
- **Solución:** Reordenar código para crear todos los widgets (label_preview, label_fechas) ANTES de actualizar sus valores
- **Archivos modificados:** `dialogo_crear_curso.py` (líneas 62-78)
- **Impacto:** Ninguno, fix simple de orden de inicialización

**Bug #6 - Detalles:**
- **Causa:** PyQt6 en macOS tiene problemas de renderizado con QMessageBox usando métodos estáticos (.question(), .information(), etc.). Los botones no se muestran o quedan fuera del área visible
- **Solución:** Reemplazar todos los QMessageBox estáticos por instancias explícitas con `setFixedSize()` para forzar tamaño correcto
- **Archivos modificados:** 
  - `gestion_cursos_widget.py` (confirmaciones de eliminar curso)
  - `dialogo_crear_curso.py` (confirmación y éxito de creación)
- **Impacto:** CRÍTICO - Sin este fix, los diálogos son inutilizables en macOS (no se pueden confirmar/cancelar acciones)

**Agregar aquí bugs encontrados durante validación**

---

### FASE 6: DOCUMENTACIÓN Y CIERRE (30 min)

#### 6.1 Actualizar Documentación
- [ ] CHANGELOG.md con cambios de esta versión
- [ ] README.md con nuevas funcionalidades
- [ ] TECHNICAL_GUIDE.md con arquitectura multi-curso

#### 6.2 Commit y Tag
```bash
git add .
git commit -m "feat: validación completa post-refactorización v2"
git tag v2.0.0-validated
git push origin main --tags
```

---

## 📈 MÉTRICAS DE ÉXITO

### Criterios de Aceptación
- [ ] ✅ Todas las funcionalidades nuevas validadas
- [ ] ✅ Todas las funcionalidades existentes funcionan
- [ ] ✅ 0 bugs críticos pendientes
- [ ] ✅ Cobertura de tests > 70%
- [ ] ✅ Documentación actualizada
- [ ] ✅ BD con datos reales y correctos

### KPIs
- **Funcionalidades validadas:** 0/45
- **Tests pasando:** ?/843
- **Cobertura:** ?%
- **Bugs encontrados:** 3 (resueltos)
- **Tiempo invertido:** 0.5h / estimado 3h

### 📊 Estado de Datos
```
Base de datos: data/users/0db13e2857239ed8/guardias_patio.db
Tamaño: 136 KB
✅ 2,423 guardias generadas
✅ 100% asignadas (0 sin cubrir)
✅ 64/67 profesores con guardias
✅ 4 zonas activas
```

---

## 🔄 ESTADO ACTUAL DEL PLAN

### ✅ Completado
- [x] Problema configuración curso_id → curso_activo_id
- [x] Agregar columna cerrado
- [x] Refrescar sesión en carga de cursos
- [x] Encabezados tabla abreviados
- [x] **FASE 1.1:** Verificar migraciones
- [x] **FASE 1.2:** Verificar datos de prueba
- [x] **FASE 1.3:** Generar guardias completas ✨

**Resumen FASE 1:**
```
✅ 2,423 guardias generadas
✅ 2,423 guardias asignadas (100%)
✅ 0 guardias sin asignar
✅ 64 profesores con guardias
✅ 67 profesores totales
✅ 4 zonas activas
```

### 🟡 En Progreso
- [ ] FASE 2: Validación nuevas funcionalidades

### ⏳ Pendiente
- [ ] FASE 3: Validación funcionalidades existentes
- [ ] FASE 4: Testing automatizado
- [ ] FASE 5: Bugs y fixes
- [ ] FASE 6: Documentación y cierre

---

## 📝 NOTAS Y OBSERVACIONES

### Cambios No Planificados Implementados
1. Sistema multi-curso completo (BD, UI, lógica)
2. Indicadores visuales avanzados en calendario
3. Gestión de cursos con estadísticas detalladas
4. UX mejoradas (alineación, responsive, tooltips)
5. Algoritmo v3.0 como único/solo lectura

### Lecciones Aprendidas
- ⚠️ Implementar funcionalidades durante refactorización requiere re-validación completa
- ✅ Cache de sesión puede ocultar problemas de datos
- ✅ Migraciones de BD deben validarse en todas las BDs de usuario
- ✅ Logs de depuración son críticos para diagnóstico

---

## 🎯 PRÓXIMOS PASOS INMEDIATOS

1. **GENERAR GUARDIAS** en la aplicación para tener datos reales
2. **EJECUTAR FASE 1** de preparación
3. **INICIAR FASE 2** de validación sistemática
4. **DOCUMENTAR** todos los bugs encontrados
5. **RESOLVER** bugs críticos antes de continuar

---

**Última actualización:** 10 nov 2025 - 19:30  
**Responsable:** GitHub Copilot + Usuario  
**Versión del plan:** 2.0
