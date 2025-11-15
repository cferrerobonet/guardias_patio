# 🔄 REINICIO PLAN DE REFACTORIZACIÓN ORIGINAL

## Aplicación: Guardias de Patio (Python + SQLite + PyQt6)

---

## 📋 CONTEXTO

### Plan V2 (Multicurso) - COMPLETADO ✅

**Duración**: 8 horas efectivas (2 días)  
**Commits**: 6 totales (c35ea8a → ced677d)  
**Tests**: 23/24 pasando (95.8%)  
**Estado**: Production-ready

El Plan V2 cumplió exitosamente sus objetivos específicos de implementación multicurso:
- ✅ Database setup con `cursos_escolares` table
- ✅ Curso_id field en todas las guardias
- ✅ Filtrado por curso activo en todos los queries
- ✅ UI selector de curso en sidebar
- ✅ Bug crítico resuelto: `Configuracion.curso_id` no existe
- ✅ Bug resuelto: QMessageBox visibility
- ✅ Suite de 24 tests automatizados
- ✅ Documentación completa (reporte validación, plan completado)

**Decisión Estratégica**: Cerrar V2 y retomar plan original desde el principio.

---

## 🎯 PLAN ORIGINAL: ANÁLISIS DE ESTADO

### Documento Base
**Archivo**: `documentacion/PLAN_REFACTORIZACION.md`  
**Longitud**: 4,787 líneas  
**Fases Totales**: 8 fases principales (ajustadas de 13 originales)  
**Duración Estimada**: 10 semanas (2.5 meses) → Optimizado a 4 semanas

### Fases Eliminadas (Ya Implementadas)
- ~~Fase 2 original: Arquitectura~~ → Clean Architecture ya existe
- ~~Fase 3 original: Herramientas~~ → ruff, mypy, pytest ya configurados
- ~~Fase 4 original: Base de datos~~ → Alembic + SQLAlchemy 2.0 OK
- ~~Fase 5 original: Tipado y Logging~~ → structlog implementado
- ~~Fase 8 original: Configuración~~ → Pydantic Settings funciona
- ~~Fase 12 original: Rendimiento~~ → Métricas y monitoring existe

### Fases del Plan Ajustado

#### ✅ FASE 3 – Tests: Arreglar y Medir (COMPLETADA)
**Estado**: ✅ **COMPLETADA** (8 nov 2025)  
**Resultados**:
- Tests totales: 843 → 976 (+133, +15.8%)
- Tests pasando: 717 → 789 (+72, ahora 81%)
- Coverage: 44.63% → 46.31% (+1.68%)
- Domain entities: 87-96% coverage ⭐
- Value objects: 62-74% coverage
- `TESTING.md` completamente actualizado

**Decisión**: Pausar mejoras de coverage (ROI decreciente), retomar después.

#### ✅ FASE 7 – Experiencia de Usuario (UX) (COMPLETADA)
**Estado**: ✅ **COMPLETADA** (mencionado en línea 4300)  
*Nota: Requiere verificación en archivo para confirmar alcance exacto*

#### ⏳ FASE 1 – Diagnóstico y Limpieza Inicial (PENDIENTE)
**Objetivo**: Identificar y eliminar archivos obsoletos, duplicados y tests rotos.  
**Estimación**: 1 día (4-6 horas efectivas)

**Tareas**:
- [ ] Eliminar `src/presentation/forms/profesor_widgets/restricciones_widget_old.py` (517 líneas)
- [ ] Consolidar carpeta `/ui` en `/presentation` (2 archivos: session_locked_dialog, sync_progress_dialog)
- [ ] Arreglar o eliminar `tests/test_calendario_guardias_form.py` (test roto, módulo inexistente)
- [ ] Auditar documentación (30+ archivos → consolidar)
- [ ] Generar `documentacion/auditoria/limpieza_fase1.md`

**Valor**: Alto – Limpieza rápida sin riesgo, reduce deuda técnica.

#### ⏳ FASE 2 – Consolidación de Código (PENDIENTE)
**Objetivo**: Verificar arquitectura, documentar estructura real.  
**Estimación**: 1 día

**Tareas**:
- [ ] Verificar violaciones arquitectónicas (domain→infrastructure, domain→presentation)
- [ ] Analizar carpeta `/services` (¿pertenece a application?)
- [ ] Generar diagrama con pyreverse
- [ ] Crear `documentacion/ARCHITECTURE.md` con estructura real
- [ ] Documentar dependencias entre capas

**Valor**: Medio-Alto – Consolida conocimiento existente, baseline para futuro.

#### ⏳ FASE 4 – Documentación: Consolidar y Simplificar (PENDIENTE)
**Objetivo**: Reducir de 30+ archivos markdown a 12-15 principales.  
**Estimación**: 2 días

**Tareas**:
- [ ] Consolidar `desarrollo/`, `guias/`, `tecnico/` en `DEVELOPMENT.md`
- [ ] Consolidar `build/`, `BUILD_WINDOWS.md` en `DEPLOYMENT.md`
- [ ] Actualizar `CHANGELOG.md` consolidando versiones
- [ ] Consolidar funcionalidades en `USER_GUIDE.md`
- [ ] Archivar `archivo/`, `roadmap/`, `LIMPIEZA_NOV_2025.md` fuera de Git
- [ ] Generar documentación API con pdoc
- [ ] Actualizar `README.md` principal con índice claro

**Valor**: Alto – Mejora mantenibilidad, onboarding, usabilidad.

#### ⏳ FASE 5 – CI/CD Básico (PENDIENTE)
**Objetivo**: Automatizar tests, linting, coverage.  
**Estimación**: 1 día

**Tareas**:
- [ ] Crear `.github/workflows/tests.yml` (Ubuntu + macOS, Python 3.11-3.12)
- [ ] Crear `.github/workflows/lint.yml` (ruff + mypy)
- [ ] Integrar Codecov (opcional)
- [ ] Añadir badges al README
- [ ] Configurar branch protection en GitHub

**Valor**: Muy Alto – Automatiza validación, previene regresiones.

#### ⏳ FASE 6 – Seguridad y Cumplimiento (PENDIENTE)
**Objetivo**: Auditorías de seguridad, protección de datos sensibles.  
**Estimación**: Variable (detalle no revisado en full)

**Tareas (estimadas)**:
- [ ] Ejecutar `pip-audit`, `bandit`, `safety`
- [ ] Verificar `.gitignore` (no .env, no .db en Git)
- [ ] Crear `SECURITY.md` con políticas
- [ ] GitHub Actions para auditoría semanal

**Valor**: Medio – Importante pero no bloqueante para funcionalidad.

#### ⏳ FASE 8 – Mantenimiento Continuo (PENDIENTE)
**Objetivo**: Scripts automatizados, checklists, cron jobs.  
**Estimación**: 2 días

**Tareas (estimadas)**:
- [ ] Script `scripts/weekly_maintenance.sh` (VACUUM, ANALYZE, logs)
- [ ] Script `scripts/monthly_audit.sh` (dependencias, seguridad)
- [ ] Crear `documentacion/MAINTENANCE.md`
- [ ] Configurar cron jobs
- [ ] Definir métricas y umbrales

**Valor**: Medio – Sostenibilidad a largo plazo.

---

## 📊 RESUMEN DE ESTADO ACTUAL

### Fases Completadas: 2/8 (25%)
- ✅ **Fase 3**: Tests (46.31% coverage, 789/976 pasando)
- ✅ **Fase 7**: UX (requiere verificación de alcance)

### Fases Pendientes: 6/8 (75%)
- ⏳ **Fase 1**: Diagnóstico y Limpieza (1 día)
- ⏳ **Fase 2**: Consolidación de Código (1 día)
- ⏳ **Fase 4**: Documentación (2 días)
- ⏳ **Fase 5**: CI/CD (1 día)
- ⏳ **Fase 6**: Seguridad (variable)
- ⏳ **Fase 8**: Mantenimiento (2 días)

**Estimación Total Pendiente**: ~7-10 días (1.5-2 semanas)

### Métricas Clave del Plan Original

#### Código
| Métrica | Objetivo | Actual | Gap |
|---------|----------|--------|-----|
| Cobertura Global | ≥85% | 46.31% | -38.69% |
| Cobertura Domain | ≥95% | 87-96% | ✅ Alcanzado |
| CC Máxima | ≤10 | ? | ❓ Sin medir |
| Warnings MyPy | 0 | ? | ❓ Sin auditar |
| Errores Ruff | 0 | ? | ❓ Sin auditar |

#### Seguridad
| Métrica | Objetivo | Actual | Gap |
|---------|----------|--------|-----|
| Vulnerabilidades | 0 | ? | ❓ Sin auditar |
| Secretos en Git | 0 | ? | ❓ Sin verificar |
| Warnings Bandit | ≤5 | ? | ❓ Sin ejecutar |

#### Documentación
| Métrica | Objetivo | Actual | Gap |
|---------|----------|--------|-----|
| Docs actualizados | 100% | ~50% | -50% |
| Archivos `.md` principales | ≤15 | 30+ | +15+ |
| Archivos obsoletos | 0 | ~3+ | +3 |
| Diagramas | ≥3 | 0 | -3 |

---

## 🚀 ESTRATEGIA DE REINICIO

### Principios
1. **Empezar desde el principio**: Fase 1 → Fase 2 → ...
2. **No reabrir V2**: Multicurso está completado y cerrado
3. **Iteración rápida**: Fases cortas (1-2 días), commits frecuentes
4. **Test-driven**: Validar con tests cuando aplique
5. **Documentar todo**: Cada fase genera documentación

### Propuesta de Arranque

#### Opción A: Secuencial Estricto (Conservador)
1. Comenzar FASE 1 (Diagnóstico y Limpieza)
2. Al completar → FASE 2 (Consolidación)
3. Al completar → FASE 4 (Documentación)
4. Al completar → FASE 5 (CI/CD)
5. Continuar secuencialmente

**Ventajas**: Orden lógico, minimiza riesgo  
**Duración**: 10-14 días consecutivos

#### Opción B: Priorizado por Valor (Recomendado)
1. **FASE 1** (Limpieza) → 1 día ⚡ Rápido, alto valor
2. **FASE 5** (CI/CD) → 1 día 🎯 Automatiza validaciones desde ya
3. **FASE 2** (Consolidación Código) → 1 día 📐 Baseline arquitectura
4. **FASE 4** (Documentación) → 2 días 📚 Mejora mantenibilidad
5. **FASE 6** (Seguridad) → variable 🔒 Importante, no bloqueante
6. **FASE 8** (Mantenimiento) → 2 días 🔄 Sostenibilidad

**Ventajas**: CI/CD temprano detecta problemas antes, iteración rápida  
**Duración**: 7-10 días (más eficiente)

#### Opción C: Híbrido Iterativo (Ágil)
1. **Sprint 1 (Semana 1)**:
   - Día 1-2: FASE 1 (Limpieza)
   - Día 3-4: FASE 5 (CI/CD)
   - Día 5: FASE 2 (Consolidación Código)

2. **Sprint 2 (Semana 2)**:
   - Día 1-3: FASE 4 (Documentación)
   - Día 4-5: FASE 6 (Seguridad - inicio)

3. **Sprint 3 (Semana 3)**:
   - Día 1-2: FASE 6 (Seguridad - completar)
   - Día 3-5: FASE 8 (Mantenimiento)

**Ventajas**: Flexibilidad, entregas incrementales, ajustes en cada sprint  
**Duración**: 3 semanas con buffer

---

## 🎯 RECOMENDACIÓN: OPCIÓN B (Priorizado por Valor)

### Justificación
1. **FASE 1 primero**: Limpieza rápida, bajo riesgo, reduce fricción futura
2. **FASE 5 segundo**: CI/CD temprano → automatiza validaciones para Fases 2, 4, 6, 8
3. **Feedback loop rápido**: Cada commit validado automáticamente desde Día 2
4. **ROI máximo**: Fases cortas (1-2 días) con valor tangible

### Primer Paso Inmediato: FASE 1 (Diagnóstico y Limpieza)

**Tareas del Día 1:**

#### 1.1 Auditoría de Archivos Obsoletos
```bash
# Buscar archivos con sufijos obsoletos
find src/ -name "*_old.py" -o -name "*_backup.py" -o -name "*_test.py"

# Resultado esperado:
# src/presentation/forms/profesor_widgets/restricciones_widget_old.py (517 líneas)
```

**Acción**: Verificar que existe versión actualizada → Eliminar archivo.

#### 1.2 Consolidar Carpeta `/ui`
```bash
# Verificar contenido de src/ui
ls -R src/ui/

# Resultado esperado:
# dialogs/session_locked_dialog.py
# widgets/sync_progress_dialog.py

# Mover a ubicación correcta
mv src/ui/dialogs/session_locked_dialog.py src/presentation/dialogs/
mv src/ui/widgets/sync_progress_dialog.py src/presentation/widgets/

# Actualizar imports en archivos que los usen
rg "from ui.dialogs" src/
rg "from ui.widgets" src/

# Actualizar imports encontrados (si existen)
# Eliminar carpeta vacía
rm -rf src/ui/
```

#### 1.3 Arreglar Test Roto
```bash
# Verificar test que falla
pytest tests/test_calendario_guardias_form.py -v

# Error esperado:
# ModuleNotFoundError: No module named 'presentation.forms.calendario_guardias_form'

# Opciones:
# A) Si formulario existe con otro nombre → actualizar import
# B) Si formulario no existe → eliminar test obsoleto
```

**Acción**: Investigar si `calendario_guardias_form.py` existe, decidir fix o delete.

#### 1.4 Auditar Documentación
```bash
# Contar archivos markdown
find documentacion/ -name "*.md" | wc -l
# Resultado esperado: ~30+ archivos

# Listar estructura
tree documentacion/ -L 2

# Identificar candidatos a consolidar
ls -lh documentacion/desarrollo/
ls -lh documentacion/guias/
ls -lh documentacion/tecnico/
ls -lh documentacion/build/
```

**Acción**: Generar lista de archivos a consolidar para FASE 4.

#### 1.5 Generar Reporte de Limpieza
```markdown
# documentacion/auditoria/limpieza_fase1.md

## Auditoría de Limpieza - Fase 1

### Archivos Eliminados
- `src/presentation/forms/profesor_widgets/restricciones_widget_old.py` (517 líneas)
  - Razón: Versión actualizada existe en mismo directorio
  - Fecha eliminación: [fecha]

### Carpetas Consolidadas
- `src/ui/` → `src/presentation/`
  - `ui/dialogs/session_locked_dialog.py` → `presentation/dialogs/`
  - `ui/widgets/sync_progress_dialog.py` → `presentation/widgets/`
  - Imports actualizados: [N archivos]

### Tests Arreglados/Eliminados
- `tests/test_calendario_guardias_form.py`
  - Acción: [Arreglado/Eliminado]
  - Razón: [explicación]

### Documentación Auditada
- Total archivos markdown: [N]
- Candidatos a consolidar: [N]
- Carpetas a revisar:
  - `documentacion/desarrollo/` (X archivos)
  - `documentacion/guias/` (Y archivos)
  - `documentacion/tecnico/` (Z archivos)
  - `documentacion/build/` (W archivos)

### Métricas
- Líneas código eliminadas: ~517
- Archivos eliminados: 1
- Carpetas consolidadas: 1
- Tests arreglados: 1
- Tiempo invertido: [horas]

### Próximos Pasos
- FASE 2: Consolidación de Código
- FASE 4: Consolidar documentación identificada
```

#### Entregables Esperados del Día 1
- ✅ `restricciones_widget_old.py` eliminado
- ✅ Carpeta `/ui` consolidada en `/presentation`
- ✅ Test `test_calendario_guardias_form.py` arreglado o eliminado
- ✅ Lista documentación a consolidar generada
- ✅ `documentacion/auditoria/limpieza_fase1.md` creado
- ✅ Commit: "refactor: FASE 1 - Diagnóstico y limpieza inicial"

---

## 📝 CHECKLIST DE INICIO

### Pre-Requisitos
- [x] Plan V2 (Multicurso) cerrado y commiteado
- [x] Plan original leído y analizado
- [x] Documento de reinicio creado (este archivo)
- [ ] Usuario confirma arrancar con FASE 1
- [ ] Crear carpeta `documentacion/auditoria/` si no existe

### Herramientas Necesarias
- [x] pytest instalado
- [x] ruff instalado
- [x] mypy instalado
- [ ] pyreverse instalado (FASE 2: `pip install pylint`)
- [ ] pdoc instalado (FASE 4: `pip install pdoc`)

### Estado del Repositorio
- [x] Branch: `main`
- [x] Sin cambios sin commitear
- [x] Último commit: ced677d (Cierre Plan V2)
- [x] Push exitoso

---

## 🎓 LECCIONES DEL PLAN V2 (Aplicar al Original)

1. **Iteración rápida funciona**: V2 completado en 8 horas con metodología incremental
2. **Tests automatizados son críticos**: 95.8% de éxito validó toda la implementación
3. **Documentación concurrente**: Generar docs durante desarrollo, no al final
4. **Commits frecuentes**: 6 commits en V2 facilitaron trazabilidad
5. **Validar temprano**: Ejecutar tests tras cada cambio previene regresiones
6. **Priorizar valor**: Enfocarse en bugs críticos primero dio máximo impacto

### Aplicación al Plan Original
- **FASE 1-2 rápidas**: 1 día cada una, alta frecuencia de commits
- **FASE 5 temprana**: CI/CD desde Día 2 → validación automática
- **Documentar en tiempo real**: `limpieza_fase1.md`, `ARCHITECTURE.md`, etc.
- **Validación incremental**: Ejecutar pytest, ruff, mypy tras cada fase

---

## 🚦 DECISIÓN PENDIENTE

**¿Comenzamos con FASE 1 (Diagnóstico y Limpieza)?**

**Opción 1**: Sí, arrancar ahora  
→ Ejecutaré tareas 1.1-1.5 documentadas arriba

**Opción 2**: Revisar otra fase primero  
→ Especificar qué deseas revisar/ajustar antes

**Opción 3**: Modificar estrategia  
→ Proponer cambios al orden o enfoque

---

**Última Actualización**: 2025-01-XX  
**Plan Base**: `documentacion/PLAN_REFACTORIZACION.md` (4787 líneas)  
**Plan V2 Completado**: `documentacion/PLAN_REFACTORIZACION_V2_COMPLETADO.md`  
**Commit Actual**: ced677d
