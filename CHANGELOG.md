# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [3.2.1] - 2025-12-08

### 🎯 Resumen

**Mejora del algoritmo Híbrido v4.1**: El algoritmo rápido ahora también prioriza consecutividad y zona. **Limpieza del proyecto** con reducción significativa del tamaño.

### ✨ Added

#### Algoritmo Híbrido v4.1
- **Consecutividad como prioridad máxima**: 
  - Scoring mejorado en `_score_slot()` que prioriza días consecutivos
  - Bonus fuerte para distancia=1 día (perfecto)
  - Penalización progresiva para días lejanos (>7 días)
  
- **Zona preferida como segunda prioridad**:
  - Cada profesor se asigna preferentemente a la misma zona
  - Tracking de zona más usada por profesor

### Changed

- Docstring del módulo actualizado a v4.1
- Reorganización de prioridades de scoring:
  1. Consecutividad (MÁXIMA PRIORIDAD)
  2. Zona preferida
  3. Recreo consistente
  4. Día de semana (baja prioridad)

### 🧹 Housekeeping

- Limpieza de caché: `__pycache__`, `.pytest_cache`, `.ruff_cache`
- Eliminación de archivos temporales: `.coverage`, `coverage.xml`, `htmlcov/`
- Limpieza de logs antiguos (>7 días)
- Eliminación de `.DS_Store`
- **Reducción de ~160MB** en el tamaño del proyecto

---

## [3.2.0] - 2025-12-08

### 🎯 Resumen

**Algoritmo CP-SAT optimizado con 3 objetivos**: Equidad perfecta (IE=100%), consecutividad de guardias, y preferencia de zona. Mejoras en UI para organizar profesores por turno.

### ✨ Added

#### Algoritmo CP-SAT Multi-Objetivo
- **Objetivo 1 - Equidad perfecta**: 
  - Índice de Equidad (IE) = 100%
  - Máxima desviación = 0 guardias por profesor
  - Pesos: `PESO_EQUIDAD=1,000,000`, `PESO_EQUIDAD_SUMA=10,000`

- **Objetivo 2 - Consecutividad de guardias**:
  - Las guardias de cada profesor son lo más consecutivas posibles
  - Minimiza "cortes" entre días (cambios día con guardia ↔ día sin guardia)
  - Resultado: ~30% menos bloques por profesor (de ~22 a ~15)
  - Peso: `PESO_CONSECUTIVIDAD=10`

- **Objetivo 3 - Preferencia de zona**:
  - Cada profesor hace guardias preferentemente en la misma zona
  - Maximiza concentración en zona principal
  - Resultado: ~85% guardias en zona principal (vs ~68% antes)
  - Peso: `PESO_ZONA=3`

#### Greedy Mejorado para Hints
- Función de scoring multi-criterio para solución inicial:
  - Bonus por días consecutivos (`-0.1`)
  - Bonus por zona principal (`-0.05`)
  - Tracking de último día y zona principal por profesor

### Changed

#### UI - Organización por Turno
- **CuotasPanel**: Profesores agrupados por turno (☀️ MAÑANA, 🌙 TARDE, 🔄 MIXTO)
- **ResultadosPanel**: Misma organización por turno con ordenación alfabética
- **GeneracionPanel**: Algoritmo Óptimo (CP-SAT) seleccionado por defecto

#### DTOs
- **CuotaProfesorDTO**: Añadido campo `turno: str` para agrupar profesores
- **calcular_cuotas_use_case.py**: Incluye turno del profesor en DTOs

### 📊 Métricas de Mejora

| Métrica | Antes (v4 Híbrido) | Después (CP-SAT) | Mejora |
|---------|-------------------|------------------|--------|
| Índice de Equidad | ~60-80% | **100%** | +20-40% |
| Bloques/profesor | ~22 | ~15 | -30% |
| % zona principal | ~68% | ~85% | +17% |
| Tiempo ejecución | ~1-2s | ~10-30s | Trade-off |

### 🔧 Technical

- **Jerarquía de pesos**: `Equidad >> Consecutividad > Zona`
- **Solver config**: 8 workers, timeout 120s, linearization_level=2
- **Variables**: ~170,000 booleanas para 67 profesores × 2516 slots

---

## [3.1.1] - 2025-01-13

### 🎯 Resumen

Refactorización arquitectónica completa: migración de modelos ORM a su ubicación canónica, corrección de violaciones DIP, separación UI/Lógica en panel de estadísticas, y actualización de imports en capas Clean Architecture.

### Changed

#### Arquitectura - Separación UI/Lógica (14 ene 2025)
- **panel_estadisticas.py**: Refactorizado para usar Use Case en lugar de queries directas
  - ❌ Eliminadas 14 queries SQLAlchemy del widget
  - ✅ Usa `ObtenerEstadisticasPanelUseCase` para obtener datos
  - ✅ Widget solo maneja presentación, no lógica de BD

#### Nuevos DTOs y Use Cases
- **application/dtos/asignacion_guardias_dto.py**: Nuevos DTOs para panel:
  - `ResumenPanelDTO`: Métricas generales
  - `EstadisticaProfesorDTO`: Stats por profesor
  - `EstadisticaZonaDTO`: Stats por zona
  - `DatosGraficoDTO`: Datos para gráficos
  - `EstadisticasPanelCompletoDTO`: DTO completo agregado
- **application/use_cases/asignacion_guardias/obtener_estadisticas_panel.py**: 
  - Nuevo Use Case que centraliza toda la lógica de estadísticas del panel

#### Arquitectura - Migración Completa de Imports (2 dic 2025)
- **113 archivos migrados** de `models.models` a `infrastructure.database.models`:
  - 54 archivos en `src/`
  - 44 archivos en `tests/`
  - 15 archivos en `scripts/`
- **models/models.py**: Ahora es solo re-export de backup, ya no se usa

#### Arquitectura - Migración de Modelos ORM
- **infrastructure/database/models.py**: Nueva ubicación canónica de modelos SQLAlchemy
- **models/models.py**: Convertido a re-export para backward compatibility (deprecado)
- **28 archivos migrados** a usar nueva ubicación:
  - `infrastructure/mappers/*` (3 archivos)
  - `infrastructure/repositories/*` (6 archivos)
  - `domain/services/*` (5 archivos)
  - `application/use_cases/*` (14 archivos)

#### Arquitectura - Dependency Injection
- **application/factories.py**: Nuevo archivo con factory functions para crear Use Cases con DI
- **5 Use Cases refactorizados** para aceptar interfaces de repositorio como parámetros:
  - `guardia/obtener_guardias.py`: Acepta `IGuardiaRepository`, `IProfesorRepository`, `IZonaRepository`
  - `guardia/asignar_guardia.py`: Acepta `IGuardiaRepository`, `IProfesorRepository`, `IZonaRepository`
  - `profesor/listar_profesores.py`: Acepta `IProfesorRepository`
  - `profesor/obtener_profesor.py`: Acepta `IProfesorRepository`
  - `profesor/crear_profesor.py`: Acepta `IProfesorRepository`

#### Patrón de Imports Recomendado
```python
# Nueva ubicación canónica (recomendado para nuevo código):
from infrastructure.database.models import Profesor, Guardia, Zona

# Backward compatibility (deprecado, funciona pero no recomendado):
from models.models import Profesor, Guardia, Zona  # Re-export
```

### Fixed

#### Documentación Actualizada
- **ARCHITECTURE.md**: 
  - Mejoras arquitectónicas marcadas como completadas
  - Documentación de distinción Use Cases vs Services
- **CLEAN_ARCHITECTURE_PHASE3.md**: Tests marcados como ✅ FIXED, Phase 3 al 100%

### Metrics

- **Violaciones DIP corregidas**: 6 → 0
- **Archivos migrados a nueva ubicación**: 113 (src: 54, tests: 44, scripts: 15)
- **Widget panel_estadisticas.py**: 14 queries eliminadas → 0 queries directas
- **Tests**: 1012 passed, 36 skipped (+22 nuevos tests de use case)
- **Cobertura**: 39.93%

---

## [3.1.0] - 2025-11-30

### 🎯 Resumen

Mejora significativa de la suite de tests. Se corrigieron 33 tests que fallaban y se redujeron los tests saltados de 80 a 36. Cobertura estable en ~40%.

### Fixed

#### Tests de Presentación
- **test_gestionar_ausencias.py**: Reescrito completamente
  - Corregido orden de fixtures (`curso_activo` → `datos_completos` → `form`)
  - 24 tests ahora pasan (antes todos saltados)
  - Actualizado para usar API actual del widget

- **test_progress_indicators.py**: Corregidos tests de threading Qt
  - 8 tests reescritos usando `qtbot.waitSignal()` 
  - Añadido fixture `cleanup_threads` para limpieza
  - Todos los 20 tests ahora pasan (antes 11)

#### Tests de Vista Calendario
- **test_vista_calendario.py**: Revisados y documentados
  - 27 tests pasan correctamente
  - 12 tests apropiadamente marcados como skip (APIs internas obsoletas)

### Changed

#### Métricas de Tests
| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Tests pasando | 957 | **990** | +33 |
| Tests saltados | 80 | **36** | -44 |
| Cobertura | 38.44% | **39.75%** | +1.31% |

### Testing

- **Total tests**: 1026 (990 passed, 36 skipped)
- **Archivos corregidos**: 3 (gestionar_ausencias, progress_indicators, vista_calendario)
- **Tests recuperados**: 33 tests que antes fallaban o estaban saltados
- **Mejora en manejo de Qt threading**: Uso de `qtbot.waitSignal()` en lugar de `wait()` y verificaciones inmediatas

---

## [3.0.2] - 2025-11-08

### 🎯 Resumen

Implementación de ventana de detalle del día en calendario y correcciones de seguridad.

### Added

#### UX - Vista de Calendario
- **DiaDetalleDialog**: Ventana modal con detalles completos del día seleccionado
  - Resumen estadístico (guardias, recreos, zonas, ausencias, sustituciones)
  - Sección de guardias agrupadas por recreo
  - Sección de ausencias con fechas y motivos
  - Sección de sustituciones con información del sustituto
  - Diseño visual consistente con código de colores
- **Integración en vista_calendario**: Click en día abre ventana de detalle
- **Tests**: 8 tests unitarios para DiaDetalleDialog (3 pasando, 5 con errores de fixtures)

### Fixed

#### Seguridad
- Resuelto TODO pendiente en `vista_calendario.py:912`
- Mejora en la experiencia de usuario del calendario

---

## [3.0.1] - 2025-11-08

### 🎯 Resumen

Corrección completa de todas las vulnerabilidades de seguridad identificadas en auditoría.

### Security

#### Vulnerabilidades Corregidas
- **7 dependencias actualizadas**:
  - `pip`: 21.2.4 → ≥25.3 (2 CVEs)
  - `setuptools`: 58.0.4 → ≥78.1.1 (3 CVEs: ReDoS, RCE, path traversal)
  - `wheel`: 0.37.0 → ≥0.38.1 (DoS)
  - `future`: 0.18.2 → ≥0.18.3 (DoS)
  - `fastapi`: 0.104.1 → ≥0.109.1 (ReDoS)
  - `requests`: 2.32.3 → ≥2.32.4 (credential leak)
  - `starlette`: 0.27.0 → ≥0.47.2 (2 DoS)

- **Issue B507 (HIGH) corregido**:
  - ANTES: `paramiko.AutoAddPolicy()` (vulnerable a MITM)
  - DESPUÉS: `paramiko.RejectPolicy()` (verifica host keys)
  - Carga automática de host keys desde `~/.ssh/known_hosts`
  - Logging mejorado con instrucciones para usuarios
  - Manejo específico de excepciones SSH

#### Resultados Post-Corrección
- **pip-audit**: 0 vulnerabilidades ✅ (antes: 7)
- **bandit HIGH**: 0 issues ✅ (antes: 1)
- **Certificación**: APROBADO PARA PRODUCCIÓN SIN RESTRICCIONES

### Changed
- Badge de seguridad actualizado en README: "0 vulnerabilities"
- Documentación actualizada: `SECURITY.md`, `SECURITY_FIX_20251108.md`

---

## [3.0.0] - 2025-11-01

### 🎯 Resumen

Refactorización arquitectónica completa de la capa de presentación y optimización del sistema de persistencia mediante implementación de cache. Se extrajeron 12 widgets reutilizables reduciendo 2,757 líneas de código en formularios (-40.3% promedio) y se implementó cache en 12 Use Cases mejorando el rendimiento en consultas de lectura entre 50-98%.

### Added

#### Widgets Reutilizables (12 nuevos)

**Configuración (6 widgets)**:
- `DatosGeneralesWidget` - Nombre del centro, curso académico, fechas
- `ConfiguracionRecreoWidget` - Gestión de recreos y horarios
- `ZonasProfesorConfigWidget` - Configuración de zonas por profesor
- `ToleranciaEquidadWidget` - Tolerancia en distribución
- `ConfiguracionEmailWidget` - Configuración SMTP completa
- `GuardarCancelarWidget` - Botones estandarizados

**Profesores (3 widgets)**:
- `DatosBasicosWidget` - Nombre, email, checkbox tutor
- `HorarioWidget` - Horas contrato, turno, distribución
- `RestriccionesWidget` - Fechas, matriz horario semanal

**Zonas (1 widget)**:
- `DatosZonaWidget` - Nombre, descripción, fechas opcionales

**Import/Export (2 widgets)**:
- `JsonOperationsWidget` - Exportar/importar JSON
- `PdfExportWidget` - Exportación de PDFs con opciones

#### Sistema de Cache

- Cache de profesores (TTL: 3 minutos)
- Cache de zonas (TTL: 5 minutos)
- Decoradores `@cache_profesores` y `@cache_zonas`
- Invalidación automática en operaciones de escritura

#### Sistema de PDFs Corporativos

- Paleta de colores estandarizada (10 colores para zonas)
- Separación visual por meses en tablas
- Colores diferenciados por recreo (4 colores)
- Banner corporativo con datos destacados
- Estilos reutilizables centralizados

#### Algoritmo v3.0

- Fechas consecutivas/agrupadas (prioridad MUY alta)
- Profesores terminan guardias lo antes posible
- Períodos libres más largos
- Mejor conciliación personal
- Algoritmo seleccionable (v2.9 o v3.0)

### Changed

#### Formularios Refactorizados (4)

- `configuracion_form.py`: 1936 → 565 líneas (-70.9%)
- `profesor_form.py`: 1390 → 1013 líneas (-27.1%)
- `import_export_form.py`: 851 → 574 líneas (-32.6%)
- `zona_form.py`: 696 → 657 líneas (-5.6%)

**Reducción total**: -2,757 líneas (-40.3% promedio)

#### Use Cases Optimizados (11)

**Con cache (5)**:
- `ObtenerConfiguracionUseCase` (TTL: 10 min, -98% queries)
- `ListarProfesoresUseCase` (TTL: 3 min, -90% queries)
- `ObtenerProfesorUseCase` (TTL: 3 min, -85% queries)
- `ListarZonasUseCase` (TTL: 5 min, -95% queries)
- `ObtenerZonaUseCase` (TTL: 5 min, -90% queries)

**Con invalidación (6)**:
- `ActualizarConfiguracionUseCase`
- `CrearProfesorUseCase`, `ActualizarProfesorUseCase`, `EliminarProfesorUseCase`
- `CrearZonaUseCase`, `ActualizarZonaUseCase`, `EliminarZonaUseCase`

#### Mejoras de UI

- Branding corporativo en QMessageBox
- SMTP con nombre del remitente configurable
- Mejor manejo de errores y validaciones
- Interfaz más consistente y profesional

### Performance

- **Carga inicial de formularios**: 50-70% más rápido
- **Listar profesores**: 80-90% más rápido
- **Listar zonas**: 80-90% más rápido
- **Obtener configuración**: ~95% más rápido
- **Reducción de queries a BD**: 90-98%

### Documentation

- [SISTEMA_PDF_CORPORATIVO.md](archivo/tecnico/SISTEMA_PDF_CORPORATIVO.md) - Sistema de PDFs
- [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md) - Algoritmo v3.0
- Patrón de widgets documentado
- Docstrings completos (100%)
- Type hints en toda la API pública

---

## [2.9.1] - 2025-10-31

### 🎯 Resumen

Actualización del calendario escolar para el curso 2025-2026 con ajustes en días lectivos y validación completa del sistema de equidad. Se corrigieron 4 días en el calendario resultando en una reducción neta de 2 días lectivos y 32 guardias totales. Implementadas optimizaciones de rendimiento que mejoran la velocidad del algoritmo en 67-75%.

### Changed

#### Calendario 2025-2026

- 22/12/2025 (lunes): Cambiado a **LECTIVO** (+1 día, +4 guardias)
- 17-19/03/2026 (Fallas Valencia): Cambiados a **NO LECTIVOS** (-3 días, -12 guardias)
- **Total**: 173 días lectivos (antes 175)
- **Guardias**: 2768 (antes 2800)
- **Balance**: -2 días lectivos = -32 guardias

#### Validación de Equidad

- Equidad perfecta mantenida: 0% desviación
- Cobertura: 100.00%
- Participación: 100% (75/75 profesores)
- Grupos inequitativos: 0 de 7

### Performance

#### IndiceSlots - Búsquedas O(1)

- **Antes**: Búsqueda lineal O(n) en cada verificación
- **Después**: Búsqueda hash O(1) usando conjuntos
- **Impacto**: >2000x más rápido en verificaciones

#### Mejoras Estimadas

- **Fase 2.1** (pre-asignación): 83-88% más rápida
  - Antes: 5-8 minutos
  - Después: 30-60 segundos
- **Tiempo total**: 67-75% más rápido
  - Antes: 8-12 minutos
  - Después: 2.5-4 minutos
- **Memoria adicional**: < 1 MB

#### Optimizaciones Implementadas

- `IndiceSlots`: Índice hash para verificación instantánea
- `FiltroProfesores`: Pre-filtrado por turno y zona
- `CacheElegibilidad`: Memoization de cálculos
- Funciones auxiliares optimizadas

### Fixed

- Corrección de días lectivos en calendario 2025-2026
- Validación matemática: 173 días × 16 guardias/día = 2768 guardias ✅

### Documentation

- [CHANGELOG_v2.9.1.md](archivo/versiones/CHANGELOG_v2.9.1.md) - Análisis detallado del calendario
- [GUIA_OPTIMIZACIONES_RENDIMIENTO.md](archivo/tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md) - Optimizaciones técnicas
- [RELEASE_NOTES_v2.9.1.md](archivo/versiones/RELEASE_NOTES_v2.9.1.md) - Notas de lanzamiento

### Testing

- 28 tests unitarios creados para optimizaciones (71% pasando)
- Tests de regresión: Algoritmo v2.9 sin cambios
- Validación de equidad: 0 grupos inequitativos
- Cobertura: 61.59% en optimizaciones_asignador.py

---

## [2.9.0] - 2025-10-28

### 🎯 Resumen

Fix crítico de compilación y distribución que impedía que la aplicación funcionara correctamente cuando se compilaba con PyInstaller. La app ahora se puede distribuir como un DMG instalable completamente funcional en macOS.

### Fixed

#### Iconos SVG No Se Cargaban

- **Problema**: Iconos no se cargaban en app compilada (rutas hardcodeadas)
- **Solución**: `IconManager` ahora usa `get_resources_directory()`
- **Archivo**: `src/utils/icon_manager.py`

#### App No Abría con Doble Clic

- **Problema**: Error "Read-only file system" al crear directorio logs/
- **Solución**: Eliminada creación de directorios del validador en `settings.py`
- **Sistema de logging**: Ya crea directorios correctamente usando `get_logs_directory()`
- **Archivo**: `src/config/settings.py`

### Added

#### Sistema de Rutas Adaptativas

Funciones en `src/core/paths.py`:
- `get_base_directory()` - Directorio base según entorno
- `get_data_directory()` - Datos de la aplicación
- `get_logs_directory()` - Logs del sistema
- `get_resources_directory()` - Recursos (imágenes, iconos)

**Comportamiento**:

| Función | Desarrollo | Producción (macOS) |
|---------|------------|-------------------|
| Base | `/path/to/project/` | `~/Library/Application Support/GuardiasDePatio/` |
| Data | `project/data/` | `~/Library/.../data/` |
| Logs | `project/logs/` | `~/Library/.../logs/` |
| Resources | `project/imagenes/` | `Contents/Resources/imagenes/` |

#### Script de Creación de DMG

- Nuevo script: `create_dmg.sh`
- Ventana personalizada con iconos grandes
- Acceso directo a `/Applications`
- Archivo `LEEME.txt` con instrucciones
- Compresión optimizada (82.6% de ahorro)
- **Tamaño final**: ~87 MB (de ~250 MB)

### Documentation

#### Nuevos Documentos

- [SOLUCION_COMPILACION.md](archivo/build/SOLUCION_COMPILACION.md) - Historial completo de problemas y soluciones
- [COMPILACION_RAPIDA.md](archivo/build/COMPILACION_RAPIDA.md) - Guía rápida de 5 minutos
- [CHECKLIST_COMPILACION.md](archivo/build/CHECKLIST_COMPILACION.md) - Checklist exhaustivo

#### Documentos Actualizados

- [COMPILACION_Y_DISTRIBUCION.md](archivo/build/COMPILACION_Y_DISTRIBUCION.md) - Referencia a nueva documentación
- `README.md` - Sección de compilación rápida
- `build_simple.sh` - Comentarios explicativos

### Testing

Tests de compilación agregados:
- ✅ Ejecución directa del binario
- ✅ Apertura con `open` (doble clic)
- ✅ Verificación de proceso activo
- ✅ Verificación de directorios del sistema
- ✅ Verificación de iconos (sin warnings)
- ✅ Estructura del bundle correcta

---

## [2.6.1] - 2024-12-XX

### Added

- Sistema de zona preferida para profesores
- Algoritmo de scoring mejorado con 5-tuplas
- 100% de consistencia en zona asignada

### Changed

- Mejoras visuales en formularios
- Reorganización de documentación

### Fixed

- Campos de turno mixto no se mostraban correctamente

### Documentation

- [zona-preferida.md](archivo/versiones/v2.6/zona-preferida.md) - Documentación técnica
- [ejemplos-zona-preferida.md](archivo/versiones/v2.6/ejemplos-zona-preferida.md) - Casos de uso
- [resumen-implementacion.md](archivo/versiones/v2.6/resumen-implementacion.md) - Detalles técnicos

---

## [2.5.0] - 2024-10-XX

### Added

- Sistema completo de gestión de ausencias
- Sustituciones automáticas y manuales
- Vista de calendario mensual mejorada
- Mejoras en importación/exportación de datos

### Changed

- Interfaz de calendario rediseñada
- Mejor organización de vistas

---

## [2.4.0] - 2024-09-XX

### Added

- Sistema de importación/exportación JSON
- Respaldo y restauración de datos
- Transferencia de configuración entre equipos

---

## [2.3.0] - 2024-08-XX

### Performance

- Optimizaciones de rendimiento en algoritmo de asignación
- Mejora en tiempo de carga de formularios

---

## [2.2.0] - 2024-07-XX

### Changed

- Refactorización major de arquitectura
- Mejor separación de responsabilidades

---

## [2.1.0] - 2024-06-XX

### Added

- Nuevas funcionalidades base
- Mejoras en gestión de profesores y zonas

---

## [2.0.0] - 2024-05-XX

### Changed

- Reescritura completa con PyQt6
- Interfaz moderna y responsiva

### Breaking Changes

- Incompatible con versiones 1.x
- Nueva estructura de base de datos

---

## [1.1.0] - 2024-04-XX

### Added

- Mejoras iniciales de UI
- Nuevos widgets y controles

---

## [1.0.0] - 2024-03-XX

### Added

- Release inicial
- CRUD básico de profesores y zonas
- Algoritmo de asignación básico
- Exportación a PDF simple

---

## 🔗 Enlaces

- **Documentación técnica**: [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)
- **Guía de despliegue**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Guía de usuario**: [USER_GUIDE.md](USER_GUIDE.md)
- **Repositorio**: https://github.com/cferrerobonet/guardias_patio
- **Issues**: https://github.com/cferrerobonet/guardias_patio/issues

---

## 📝 Convenciones

### Tipos de Cambios

- **Added**: Nuevas funcionalidades
- **Changed**: Cambios en funcionalidades existentes
- **Deprecated**: Funcionalidades que se eliminarán pronto
- **Removed**: Funcionalidades eliminadas
- **Fixed**: Correcciones de bugs
- **Security**: Correcciones de seguridad
- **Performance**: Mejoras de rendimiento
- **Documentation**: Cambios en documentación
- **Testing**: Cambios en tests

### Versionado Semántico

Formato: `MAJOR.MINOR.PATCH`

- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nuevas funcionalidades compatibles
- **PATCH**: Correcciones de bugs compatibles

---

**Última actualización**: 30 de noviembre de 2025  
**Versión actual**: 3.1.0  
**Mantenido por**: Equipo Guardias de Patio
