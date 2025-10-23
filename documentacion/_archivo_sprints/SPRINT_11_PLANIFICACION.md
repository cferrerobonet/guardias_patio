# 🎯 SPRINT 11: CONSOLIDACIÓN Y LIMPIEZA

**Fecha de planificación**: 23 de octubre de 2025  
**Objetivo**: Consolidar el código, eliminar archivos obsoletos y optimizar la arquitectura  
**Duración estimada**: 1-2 semanas  
**Prioridad**: Alta (Deuda técnica acumulada)

---

## 📋 CONTEXTO

Después de 10 sprints intensivos de desarrollo, testing y observabilidad, el proyecto ha acumulado:
- ✅ Arquitectura hexagonal completa y funcional
- ✅ Coverage de testing significativo (services 93%, use_cases 93%, repositories 59%)
- ✅ Sistema de observabilidad y métricas
- ⚠️ Archivos legacy sin eliminar desde Sprint 5
- ⚠️ Código potencialmente duplicado o sin uso
- ⚠️ Documentación parcialmente desactualizada

Sprint 11 se enfoca en **consolidar, limpiar y optimizar** antes de nuevas features.

---

## 🎯 OBJETIVOS PRINCIPALES

1. **Eliminar archivos obsoletos** identificados desde Sprint 5
2. **Migrar archivos nuevos** a la estructura correcta
3. **Limpiar código muerto** (imports, funciones, clases sin uso)
4. **Consolidar documentación** (eliminar redundancias, actualizar)
5. **Optimizar imports** y dependencias
6. **Validar integridad** del sistema después de limpieza

---

## 📦 TAREAS DEL SPRINT

### Task 11.1: Limpieza de Archivos Legacy ⚠️ CRÍTICO

**Prioridad**: Alta  
**Tiempo estimado**: 2-3 horas  
**Complejidad**: Media

#### 11.1.1: Analizar Dependencias de Archivos Legacy

**Objetivo**: Verificar que ningún archivo activo importa desde `src/widgets/` legacy

**Acciones**:
```bash
# Buscar imports de widgets legacy
grep -r "from src.widgets" --include="*.py" src/
grep -r "import src.widgets" --include="*.py" src/
```

**Resultado esperado**: Lista completa de archivos que importan desde legacy

---

#### 11.1.2: Migrar Archivos Nuevos a Presentation Layer

**Archivos a migrar** (creados en Sprint 7-8, ubicados incorrectamente):

1. **`src/widgets/dashboard_observabilidad.py`** → `src/presentation/widgets/observability_dashboard.py`
   - Creado en Sprint 7
   - Dashboard de métricas y observabilidad
   - Actualizar imports en `main.py` y otros archivos

2. **`src/widgets/progress_indicators.py`** → `src/presentation/widgets/progress_indicators.py`
   - Creado en Sprint 8
   - Componentes de indicadores de progreso
   - Actualizar imports en forms que lo usan

3. **`src/widgets/validadores_ui.py`** → `src/presentation/widgets/validadores_ui.py`
   - Creado en Sprint 8
   - Validaciones de UI
   - Actualizar imports en forms que lo usan

**Proceso por archivo**:
1. Crear archivo en nueva ubicación
2. Copiar contenido
3. Actualizar imports internos si es necesario
4. Buscar y actualizar todos los imports externos
5. Ejecutar tests para validar
6. Eliminar archivo legacy

---

#### 11.1.3: Eliminar Archivos Duplicados Obsoletos

**Archivos a ELIMINAR** (migrados en Sprint 5, duplicados en presentation/):

```
src/widgets/
├── gestionar_ausencias.py        ❌ ELIMINAR (duplicado)
├── gestor_sustituciones.py       ❌ ELIMINAR (duplicado)
├── panel_estadisticas.py         ❌ ELIMINAR (duplicado)
└── vista_calendario.py           ❌ ELIMINAR (duplicado)
```

**Validación previa**:
```bash
# Verificar que existen las versiones migradas
ls -la src/presentation/widgets/gestionar_ausencias.py
ls -la src/presentation/widgets/gestor_sustituciones.py
ls -la src/presentation/widgets/panel_estadisticas.py
ls -la src/presentation/widgets/vista_calendario.py
```

**Proceso de eliminación**:
1. Backup del directorio (git stash)
2. Eliminar archivo legacy
3. Ejecutar suite completa de tests
4. Si falla, revertir; si pasa, confirmar eliminación

---

#### 11.1.4: Eliminar Directorio `src/widgets/` Vacío

**Después de migrar/eliminar todos los archivos**:

```bash
# Verificar que solo queda __init__.py y __pycache__
ls -la src/widgets/

# Eliminar directorio completo
rm -rf src/widgets/
```

**Actualizar imports globales**:
- Buscar en `src/main.py`
- Buscar en tests
- Actualizar `__init__.py` files si es necesario

---

### Task 11.2: Limpieza de Código Muerto 🧹

**Prioridad**: Media  
**Tiempo estimado**: 3-4 horas  
**Complejidad**: Media-Alta

#### 11.2.1: Identificar Imports sin Uso

**Herramientas**:
```bash
# Instalar autoflake para detectar imports sin uso
pip install autoflake

# Analizar imports sin uso (dry-run)
autoflake --remove-all-unused-imports --recursive --check src/

# Ver reporte detallado
autoflake --remove-all-unused-imports --recursive src/ > unused_imports_report.txt
```

**Proceso**:
1. Revisar reporte manualmente
2. Eliminar imports obviamente sin uso
3. Validar con tests después de cada cambio
4. NO eliminar imports que puedan ser indirectos o de tipo hints

---

#### 11.2.2: Identificar Funciones/Clases sin Uso

**Herramientas**:
```bash
# Instalar vulture para detectar código muerto
pip install vulture

# Analizar código muerto
vulture src/ --min-confidence 80 > dead_code_report.txt
```

**Criterios para eliminar**:
- ✅ Funciones privadas sin llamadas (confianza > 90%)
- ✅ Clases sin instancias (confianza > 80%)
- ⚠️ Revisar manualmente funciones públicas
- ❌ NO eliminar métodos de interfaces/protocolos

**Proceso**:
1. Revisar reporte de vulture
2. Validar manualmente cada caso
3. Eliminar solo con alta confianza
4. Ejecutar tests después de cada eliminación

---

#### 11.2.3: Consolidar Código Duplicado

**Áreas a revisar**:

1. **Validaciones duplicadas**:
   - `src/presentation/widgets/validadores_ui.py`
   - Validaciones en DTOs
   - Validaciones en Value Objects
   - → Consolidar en un solo lugar (preferiblemente domain)

2. **Mappers similares**:
   - Revisar `src/infrastructure/mappers/`
   - Buscar patrones repetidos
   - → Extraer a funciones helper si aplica

3. **Configuración duplicada**:
   - Settings en múltiples lugares
   - → Centralizar en `src/config/`

**Herramientas**:
```bash
# Detectar código duplicado con PMD CPD
pip install pmd-python

# O usar jscpd
npm install -g jscpd
jscpd src/ --min-lines 10
```

---

### Task 11.3: Optimización de Imports y Dependencias 📦

**Prioridad**: Media  
**Tiempo estimado**: 2-3 horas  
**Complejidad**: Baja-Media

#### 11.3.1: Analizar Dependencias Instaladas vs Usadas

**Objetivo**: Identificar paquetes instalados que no se usan

```bash
# Instalar pip-check-reqs
pip install pip-check-reqs

# Verificar dependencias extra
pip-extra-reqs src/

# Verificar dependencias faltantes
pip-missing-reqs src/
```

**Proceso**:
1. Revisar lista de paquetes en `requirements.txt`
2. Verificar cuáles se usan realmente
3. Comentar/eliminar los que no se usan
4. Mantener solo los necesarios

---

#### 11.3.2: Optimizar Estructura de Imports

**Estándares a aplicar**:
```python
# ✅ Orden correcto de imports
# 1. Standard library
import os
import sys
from datetime import datetime

# 2. Third-party
from sqlalchemy import Column, Integer
from PyQt6.QtWidgets import QWidget

# 3. Local application
from src.domain.entities import Profesor
from src.infrastructure.repositories import ProfesorRepository
```

**Herramientas**:
```bash
# isort para ordenar imports automáticamente
pip install isort

# Configurar isort
cat > .isort.cfg << EOF
[settings]
profile = black
line_length = 100
EOF

# Aplicar a todo el proyecto (dry-run)
isort --check-only --diff src/

# Aplicar cambios
isort src/
```

---

#### 11.3.3: Actualizar `requirements.txt`

**Proceso**:
1. Congelar versiones actuales funcionales
2. Actualizar solo patches de seguridad
3. Validar que todo funciona después
4. Documentar cambios en CHANGELOG

```bash
# Generar requirements actualizado
pip freeze > requirements_new.txt

# Comparar con actual
diff requirements.txt requirements_new.txt

# Actualizar si es necesario
mv requirements_new.txt requirements.txt
```

---

### Task 11.4: Consolidación de Documentación 📚

**Prioridad**: Media  
**Tiempo estimado**: 2-3 horas  
**Complejidad**: Baja

#### 11.4.1: Identificar Documentación Obsoleta

**Archivos a revisar**:
```bash
documentacion/
├── desarrollo/          # Planes antiguos de refactorización
├── versiones/           # Changelogs antiguos
├── CHANGELOG_*.md       # Múltiples changelogs
└── RESUMEN_*.md         # Múltiples resúmenes
```

**Criterios para consolidar/eliminar**:
- ✅ Mantener: Documentos de sprints completos (5, 6, 7, 8, 9, 10)
- ✅ Mantener: Arquitectura actual (v2.6, v2.7)
- ⚠️ Archivar: Versiones anteriores a v2.5
- ❌ Eliminar: Documentos duplicados o muy similares
- ❌ Eliminar: TODOs completados hace más de 1 sprint

---

#### 11.4.2: Crear Índice Maestro de Documentación

**Archivo nuevo**: `documentacion/INDEX.md`

**Estructura**:
```markdown
# 📚 Índice de Documentación

## 🏗️ Arquitectura
- [Arquitectura v2.6](RESUMEN_ARQUITECTURA_v2.6.md)
- [Branding Corporativo](BRANDING_CORPORATIVO.md)

## 📖 Sprints
- [Sprint 5: Widgets](SPRINT_5_WIDGETS.md)
- [Sprint 6: Testing](RESUMEN_FINAL_SPRINT_6.md)
- [Sprint 7: Observabilidad](SPRINT_7_COMPLETO.md)
- [Sprint 8: Validaciones](SPRINT_8_PLANIFICACION.md)
- [Sprint 9: Integración](RESUMEN_SPRINT_9.md)
- [Sprint 10: Testing Exhaustivo](SPRINT_10_PLANIFICACION.md)
- [Sprint 11: Consolidación](SPRINT_11_PLANIFICACION.md)

## 🔧 Guías Técnicas
- [Contribuir](CONTRIBUIR.md)
- [Checklist de Proyecto](Checklist_proyecto.md)

## 📝 Changelogs
- [v2.7](CHANGELOG_v2.7.md)
- [v2.6](CHANGELOG_v2.6.md)
```

---

#### 11.4.3: Actualizar README Principal

**Archivo**: `README.md` (raíz del proyecto)

**Secciones a actualizar**:
1. Estado del proyecto (Sprint 11)
2. Coverage actual (~75% general)
3. Arquitectura consolidada
4. Guía de inicio rápido
5. Links a documentación principal

---

### Task 11.5: Validación Post-Limpieza ✅

**Prioridad**: Alta (CRÍTICO)  
**Tiempo estimado**: 1-2 horas  
**Complejidad**: Media

#### 11.5.1: Suite Completa de Tests

**Ejecutar TODOS los tests**:
```bash
# Tests unitarios + integración + E2E
pytest tests/ -v --tb=short

# Con coverage completo
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Solo tests críticos (smoke test)
pytest tests/test_e2e_flujo_completo.py -v
```

**Criterio de éxito**:
- ✅ 0 tests fallando
- ✅ Coverage no debe bajar del actual
- ✅ Tiempo de ejecución similar o mejor

---

#### 11.5.2: Validación de Aplicación

**Tests manuales**:
1. Iniciar aplicación: `python src/main.py`
2. Verificar todas las ventanas se abren
3. Crear un profesor nuevo
4. Generar guardias para un mes
5. Exportar a JSON y PDF
6. Verificar calendario se muestra correctamente
7. Ver dashboard de observabilidad

**Criterio de éxito**:
- ✅ Aplicación inicia sin errores
- ✅ Todas las funcionalidades principales funcionan
- ✅ No hay excepciones en logs

---

#### 11.5.3: Análisis Estático de Código

**Herramientas**:
```bash
# mypy para type checking
mypy src/ --ignore-missing-imports

# pylint para análisis estático
pylint src/ --disable=C0111,R0903

# flake8 para style checking
flake8 src/ --max-line-length=100 --ignore=E203,W503
```

**Criterio de éxito**:
- ✅ mypy: 0 errores críticos (warnings ok)
- ✅ pylint: score > 8.0
- ✅ flake8: 0 errores críticos

---

### Task 11.6: Optimizaciones de Rendimiento (Opcional) ⚡

**Prioridad**: Baja (bonus)  
**Tiempo estimado**: 2-3 horas  
**Complejidad**: Alta

#### 11.6.1: Profiling de Operaciones Lentas

**Herramientas**:
```bash
# cProfile para profiling
python -m cProfile -o profile.stats src/main.py

# Analizar resultados
python -m pstats profile.stats
```

**Áreas a revisar**:
1. Generación de guardias (asignador)
2. Cálculo de distribución (calculador)
3. Queries de base de datos (repositories)
4. Renderizado de UI (widgets)

---

#### 11.6.2: Optimización de Queries SQL

**Proceso**:
1. Activar logging SQL en SQLAlchemy
2. Identificar N+1 queries
3. Agregar `joinedload()` o `selectinload()` donde sea necesario
4. Medir mejora de performance

**Ejemplo**:
```python
# ❌ Antes (N+1)
profesores = session.query(Profesor).all()
for prof in profesores:
    guardias = prof.guardias  # Query por cada profesor

# ✅ Después
profesores = session.query(Profesor).options(
    joinedload(Profesor.guardias)
).all()
```

---

#### 11.6.3: Caché de Resultados Frecuentes

**Implementar caché para**:
1. Configuración global (ya se recarga poco)
2. Lista de profesores (cambia poco)
3. Festivos del año (calculado una vez por año)
4. Estadísticas del dashboard

**Herramienta**: `functools.lru_cache` o Redis si se necesita

---

## 📊 MÉTRICAS DE ÉXITO

### Archivos Eliminados
- ✅ Al menos 4 archivos legacy eliminados
- ✅ Directorio `src/widgets/` eliminado
- ✅ Reducción de 200-300 líneas de código duplicado

### Código Limpio
- ✅ 0 imports sin uso (verificado con autoflake)
- ✅ 0 funciones privadas sin llamadas (vulture > 90% confianza)
- ✅ Imports ordenados según estándar (isort)

### Tests
- ✅ 100% de tests pasando después de limpieza
- ✅ Coverage >= actual (no debe bajar)
- ✅ Aplicación funcional al 100%

### Documentación
- ✅ Índice maestro creado
- ✅ README actualizado
- ✅ Al menos 3 docs obsoletos archivados/eliminados

### Rendimiento (Opcional)
- ✅ Tiempo de inicio < 2 segundos
- ✅ Generación de guardias < 5 segundos (mes completo)
- ✅ Queries SQL < 50ms promedio

---

## 🗓️ CRONOGRAMA PROPUESTO

### Semana 1: Limpieza Core
- **Día 1-2**: Task 11.1 (Archivos legacy)
- **Día 3**: Task 11.2 (Código muerto)
- **Día 4**: Task 11.3 (Imports y dependencias)
- **Día 5**: Task 11.5 (Validación)

### Semana 2: Consolidación (Opcional)
- **Día 1-2**: Task 11.4 (Documentación)
- **Día 3-4**: Task 11.6 (Optimizaciones)
- **Día 5**: Buffer para imprevistos

---

## 🚨 RIESGOS Y MITIGACIONES

### Riesgo 1: Eliminar código que se usa indirectamente
**Mitigación**: 
- Siempre ejecutar tests después de cada eliminación
- Git commit frecuente para poder revertir
- Backup antes de empezar

### Riesgo 2: Romper imports al mover archivos
**Mitigación**:
- Usar grep para encontrar TODOS los imports antes de mover
- Actualizar imports uno por uno
- Validar con mypy/pylint después de cada cambio

### Riesgo 3: Tiempo mayor al estimado
**Mitigación**:
- Priorizar Task 11.1 y 11.5 (críticas)
- Task 11.4 y 11.6 son opcionales
- Dejar algunas optimizaciones para Sprint 12 si es necesario

---

## 📋 CHECKLIST FINAL

### Pre-Sprint
- [ ] Backup completo del proyecto
- [ ] Git branch nuevo: `feature/sprint-11-consolidacion`
- [ ] Instalar herramientas necesarias (autoflake, vulture, isort)
- [ ] Commit de estado actual como baseline

### Durante Sprint
- [ ] Task 11.1.1: Analizar dependencias legacy
- [ ] Task 11.1.2: Migrar 3 archivos nuevos a presentation/
- [ ] Task 11.1.3: Eliminar 4 archivos duplicados
- [ ] Task 11.1.4: Eliminar directorio src/widgets/
- [ ] Task 11.2.1: Limpiar imports sin uso
- [ ] Task 11.2.2: Eliminar código muerto
- [ ] Task 11.2.3: Consolidar duplicados
- [ ] Task 11.3.1: Analizar dependencias
- [ ] Task 11.3.2: Optimizar imports
- [ ] Task 11.3.3: Actualizar requirements.txt
- [ ] Task 11.4.1: Identificar docs obsoletos
- [ ] Task 11.4.2: Crear índice maestro
- [ ] Task 11.4.3: Actualizar README
- [ ] Task 11.5.1: Suite completa tests
- [ ] Task 11.5.2: Validación manual app
- [ ] Task 11.5.3: Análisis estático
- [ ] Task 11.6.1: Profiling (opcional)
- [ ] Task 11.6.2: Optimizar queries (opcional)
- [ ] Task 11.6.3: Caché (opcional)

### Post-Sprint
- [ ] Crear RESUMEN_SPRINT_11_COMPLETO.md
- [ ] Actualizar CHANGELOG.md
- [ ] Git merge a main
- [ ] Tag de versión: v2.8.0-consolidation
- [ ] Celebrar código limpio 🎉

---

## 🎯 ENTREGABLES

1. **Código limpio**:
   - Directorio `src/widgets/` eliminado
   - 0 archivos legacy
   - Imports ordenados y optimizados
   - 0 código muerto

2. **Documentación consolidada**:
   - `documentacion/INDEX.md` (nuevo)
   - `README.md` actualizado
   - Documentos obsoletos archivados

3. **Validación completa**:
   - Reporte de tests (100% passing)
   - Reporte de coverage (>= actual)
   - Reporte de análisis estático (pylint, mypy, flake8)

4. **Documentación de Sprint**:
   - `RESUMEN_SPRINT_11_COMPLETO.md`
   - Lecciones aprendidas
   - Métricas finales

---

## 💡 LECCIONES ESPERADAS

1. **Prevención de deuda técnica**: Eliminar archivos obsoletos inmediatamente después de migración
2. **Herramientas útiles**: autoflake, vulture, isort para mantener código limpio
3. **Testing crítico**: Suite de tests robusta permite refactoring con confianza
4. **Documentación actualizada**: Índice maestro facilita navegación

---

## 🔗 REFERENCIAS

- [Sprint 5: Migración de Widgets](SPRINT_5_WIDGETS.md)
- [Sprint 10: Testing Exhaustivo](SPRINT_10_PLANIFICACION.md)
- [Arquitectura v2.6](RESUMEN_ARQUITECTURA_v2.6.md)
- [Guía de Contribución](CONTRIBUIR.md)

---

## 📝 NOTAS ADICIONALES

### Consideraciones para Sprint 12 (Post-Consolidación)

Después de consolidar en Sprint 11, Sprint 12 podría enfocarse en:

1. **Async/Await**: Operaciones largas asíncronas
2. **Connection Pooling**: Optimización de DB
3. **Property-Based Testing**: Hypothesis para tests más robustos
4. **Sentry Integration**: Monitoreo de errores en producción
5. **Performance Monitoring**: Métricas de rendimiento en producción

Estas features se postponen de Sprint 11 para mantener el foco en limpieza y no agregar complejidad durante consolidación.

---

**Sprint 11 - Consolidación y Limpieza**  
*"Clean code is simple and direct. Clean code reads like well-written prose."* - Robert C. Martin
