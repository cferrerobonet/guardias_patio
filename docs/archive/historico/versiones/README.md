# 📜 Historial de Versiones - Guardias de Patio# Historial de Versiones



Documentación de todas las versiones del sistema con sus cambios, mejoras y características.Documentación de todas las versiones del sistema con sus cambios, mejoras y características.



---## 📦 Versión Actual: v2.6.1



## 📦 Versión Actual: v3.0.0 ⭐### [v2.6 - Zona Preferida](v2.6/)



**Fecha de lanzamiento:** Noviembre 2025**Fecha**: Diciembre 2024



### Características Principales**Características Principales**:

- ✨ **Zona Preferida**: Sistema inteligente que mantiene a cada profesor en su zona asignada

#### 🏗️ Refactorización Arquitectónica Completa- 🎯 Algoritmo de scoring mejorado (5-tuplas con prioridad de zona)

- ✨ Homogeneización de formularios (patrón unificado)- 📊 100% de consistencia en zona (test validado)

- ✨ Widgets modernizados con estilos corporativos- 🐛 Fix: Campos de turno mixto no se mostraban correctamente

- ✨ Eliminación de dashboards redundantes

- ✨ Mejor organización del código**Documentación**:

- [Changelog v2.6](v2.6/changelog.md) - Lista completa de cambios

#### 🎨 Sistema de PDFs Corporativos- [Zona Preferida](v2.6/zona-preferida.md) - Documentación técnica de la feature

- ✨ Paleta de colores estandarizada (10 colores para zonas)- [Ejemplos](v2.6/ejemplos-zona-preferida.md) - Casos de uso y escenarios

- ✨ Separación visual por meses en tablas- [Resumen de Implementación](v2.6/resumen-implementacion.md) - Detalles técnicos

- ✨ Colores diferenciados por recreo (4 colores)

- ✨ Banner corporativo con datos destacados en amarillo**Impacto**:

- ✨ Estilos reutilizables centralizados- 👨‍🏫 Los profesores ya no necesitan consultar su zona cada día

- 📄 **Documentación**: [SISTEMA_PDF_CORPORATIVO.md](../tecnico/SISTEMA_PDF_CORPORATIVO.md)- 📈 Mejora la organización y predictibilidad

- ⚡ Reduce tiempo de coordinación

#### 🧮 Algoritmo Mejorado v3.0

- ⭐ **Fechas consecutivas/agrupadas** (prioridad MUY alta)---

  - Profesores terminan sus guardias lo antes posible

  - Períodos libres de guardias más largos### [v2.5 - Gestión de Ausencias](v2.5/)

  - Mejor conciliación personal

- ✅ Zona consistente (máxima prioridad)**Fecha**: Octubre 2024

- ✅ Recreo consistente

- ✅ Día de semana consistente (menor prioridad que fechas)**Características Principales**:

- 📄 **Documentación**: [PREMISAS_ASIGNACION_GUARDIAS.md](../PREMISAS_ASIGNACION_GUARDIAS.md)- 📅 Sistema completo de gestión de ausencias

- 🔄 Sustituciones automáticas y manuales

#### 🔧 Mejoras Técnicas- 📊 Vista de calendario mensual mejorada

- ✅ Branding corporativo en QMessageBox- 📤 Mejoras en importación/exportación

- ✅ SMTP con nombre del remitente configurable

- ✅ Algoritmos v2.9 y v3.0 coexistiendo (seleccionable)**Documentación**:

- ✅ Mejor manejo de errores y validaciones- [Changelog v2.5](v2.5/changelog.md)



### Documentación**Impacto**:

- [CHANGELOG v3.0](CHANGELOG_v3.0.md) - Lista completa de cambios- 🏥 Control centralizado de bajas y permisos

- [SISTEMA_PDF_CORPORATIVO.md](../tecnico/SISTEMA_PDF_CORPORATIVO.md) - Sistema de PDFs- ⚡ Sustituciones más rápidas y organizadas

- [PREMISAS_ASIGNACION_GUARDIAS.md](../PREMISAS_ASIGNACION_GUARDIAS.md) - Algoritmo actualizado- 📈 Visibilidad completa del mes



------



## 📊 Versiones Anteriores## 📊 Línea Temporal



### [v2.9.1 - Calendario 2025-2026](CHANGELOG_v2.9.1.md)```

v2.6.1 (Dic 2024)  ● Zona Preferida + Reorganización docs

**Fecha**: Noviembre 2024                   │

v2.6.0 (Dic 2024)  ● Zona Preferida feature

**Características Principales**:                   │

- 📅 Calendario actualizado curso 2025-2026v2.5.0 (Oct 2024)  ● Gestión de Ausencias + Vista Calendario

- 🐛 Correcciones menores de bugs                   │

- 📊 Mejoras en validacionesv2.4.0 (Sep 2024)  ● Importación/Exportación JSON

                   │

**Documentación**:v2.3.0 (Ago 2024)  ● Optimizaciones de rendimiento

- [CHANGELOG v2.9.1](CHANGELOG_v2.9.1.md)                   │

- [Release Notes v2.9.1](RELEASE_NOTES_v2.9.1.md)v2.2.0 (Jul 2024)  ● Refactorización major

                   │

---v2.1.0 (Jun 2024)  ● Nuevas funcionalidades base

                   │

### [v2.9 - Mejoras de Calendario y Equidad](CHANGELOG_v2.9.md)v2.0.0 (May 2024)  ● Reescritura PyQt6

                   │

**Fecha**: Octubre 2024v1.1.0 (Abr 2024)  ● Mejoras UI iniciales

                   │

**Características Principales**:v1.0.0 (Mar 2024)  ● Release inicial

- 🧮 **Algoritmo de Equidad Mejorado** (v2.9 Determinista)```

  - Profesores con mismas características reciben mismas guardias (±1)

  - Eliminada aleatoriedad## 🔍 Buscar por Característica

  - Mayor consistencia en zonas y recreos

- 📅 **Calendario Mejorado**| Característica | Versión Introducida | Documentación |

  - Mejoras visuales|----------------|---------------------|---------------|

  - Mejor rendimiento| Zona Preferida | v2.6.0 | [Docs](v2.6/zona-preferida.md) |

- 📊 **Validaciones Mejoradas**| Gestión de Ausencias | v2.5.0 | [Docs](../funcionalidades/ausencias/gestion.md) |

| Vista Calendario | v2.5.0 | [Docs](../funcionalidades/calendario/vista-mensual.md) |

**Documentación**:| Importar/Exportar | v2.4.0 | [Docs](../funcionalidades/importar-exportar/README.md) |

- [CHANGELOG v2.9](CHANGELOG_v2.9.md)| Turno Mixto | v2.6.0 | [Changelog](v2.6/changelog.md) |

- [Corrección de Equidad v2.9](../archivo/CORRECCION_EQUIDAD_v2.9.md) 📦| Algoritmo de Scoring | v2.6.0 | [Zona Preferida](v2.6/zona-preferida.md) |

- [Resumen Corrección v2.9](../archivo/RESUMEN_CORRECCION_v2.9.md) 📦

- [Mejoras Calendario v2.9](../archivo/MEJORAS_CALENDARIO_v2.9.md) 📦## 📈 Evolución de Features



---### Sistema de Asignación

- v1.0: Asignación básica aleatoria

## 📈 Línea Temporal- v2.0: Algoritmo con restricciones

- v2.2: Refactorización con scoring

```- v2.6: **Zona preferida con prioridad alta**

v3.0.0 (Nov 2025)  ⭐ Refactorización + PDFs + Algoritmo v3.0

                   │### Gestión de Profesores

v2.9.1 (Nov 2024)  ● Calendario 2025-2026- v1.0: CRUD básico

                   │- v2.0: Condiciones avanzadas (turnos, días, recreos)

v2.9.0 (Oct 2024)  ● Equidad Determinista + Calendario Mejorado- v2.6: **Turno mixto con horas específicas**

                   │

v2.6.1 (Dic 2024)  ● Zona Preferida + Reorganización docs### Interfaz de Usuario

                   │- v1.0: Formularios básicos

v2.6.0 (Dic 2024)  ● Zona Preferida feature- v2.0: PyQt6 modernizado

                   │- v2.5: **Vista de calendario mensual**

v2.5.0 (Oct 2024)  ● Gestión de Ausencias + Vista Calendario- v2.6: **Mejoras UX en turno mixto**

                   │

v2.4.0 (Sep 2024)  ● Importación/Exportación JSON### Datos y Persistencia

                   │- v1.0: SQLite básico

v2.3.0 (Ago 2024)  ● Optimizaciones de rendimiento- v2.2: SQLAlchemy ORM

                   │- v2.4: **Sistema de importación/exportación**

v2.2.0 (Jul 2024)  ● Refactorización major

                   │## 🐛 Bugs Importantes Resueltos

v2.0.0 (May 2024)  ● Reescritura PyQt6

                   │| Bug | Versión Afectada | Fix en Versión | Descripción |

v1.0.0 (Mar 2024)  ● Release inicial|-----|------------------|----------------|-------------|

```| Duplicados en guardias | v2.2.0 - v2.2.1 | v2.3.0 | Guardias se duplicaban al regenerar calendario |

| Turno mixto invisible | v2.5.0 | v2.6.0 | Campos horas_manana/tarde no se mostraban |

---| Memoria en calendario | v2.4.0 | v2.5.0 | Memory leak en vista calendario |

| PyQt6 incompatibilidades | v2.0.0 - v2.1.0 | v2.2.0 | Problemas con Python 3.11+ |

## 🔍 Buscar por Característica

## 🔮 Próximas Versiones

| Característica | Versión Introducida | Documentación |

|----------------|---------------------|---------------|Ver [Roadmap v3.0](../roadmap/roadmap-v3.0.md) para planificación de futuras versiones.

| **PDFs Corporativos** | v3.0.0 ⭐ | [SISTEMA_PDF_CORPORATIVO.md](../tecnico/SISTEMA_PDF_CORPORATIVO.md) |

| **Fechas Consecutivas** | v3.0.0 ⭐ | [PREMISAS v1.3](../PREMISAS_ASIGNACION_GUARDIAS.md) |**Adelanto v2.7** (Q1 2025):

| **Algoritmo v3.0** | v3.0.0 ⭐ | [PREMISAS](../PREMISAS_ASIGNACION_GUARDIAS.md) |- 🎨 Mejoras visuales en UI

| **Equidad Determinista** | v2.9.0 | [Corrección v2.9](../archivo/CORRECCION_EQUIDAD_v2.9.md) 📦 |- ⚡ Optimizaciones de rendimiento

| Calendario 2025-2026 | v2.9.1 | [CHANGELOG v2.9.1](CHANGELOG_v2.9.1.md) |- 📊 Estadísticas avanzadas

| Zona Preferida | v2.6.0 | [Docs históricas](../archivo/) 📦 |- 🔔 Sistema de notificaciones

| Gestión de Ausencias | v2.5.0 | [Funcionalidades](../funcionalidades/FUNCIONALIDADES_COMPLETAS.md) |

**Adelanto v3.0** (Q2 2025):

---- 🌐 Versión web/multi-plataforma

- 👥 Multi-usuario con roles

## 📈 Evolución de Features- 🔄 Sincronización en tiempo real

- 📱 App móvil companion

### Sistema de Asignación

- **v1.0**: Asignación básica aleatoria## 📦 Notas de Migración

- **v2.0**: Algoritmo con restricciones

- **v2.6**: Zona preferida con prioridad alta### Migrando de v2.5 a v2.6

- **v2.9**: Equidad determinista (sin aleatoriedad)1. **Backup**: Exporta tus datos actuales

- **v3.0**: ⭐ **Fechas consecutivas/agrupadas** (prioridad muy alta)2. **Actualizar**: Instala v2.6

3. **Base de datos**: Se actualiza automáticamente (Alembic)

### Exportación de PDFs4. **Revisar**: Zonas preferidas se asignarán en primera guardia

- **v2.0**: PDFs básicos5. **Regenerar**: Opcional - regenerar calendario para aplicar zona preferida

- **v2.4**: Mejoras en diseño

- **v3.0**: ⭐ **Sistema corporativo con paleta estandarizada**### Migrando de v2.4 a v2.5

1. **Backup**: Exporta datos

### Gestión de Profesores2. **Actualizar**: Instala v2.5

- **v1.0**: CRUD básico3. **Nueva tabla**: Alembic crea tabla `ausencias`

- **v2.0**: Condiciones avanzadas (turnos, días, recreos)4. **Configurar**: Define ausencias existentes si las hay

- **v2.6**: Turno mixto con horas específicas

- **v3.0**: ⭐ **Formularios homogeneizados**### Migrando de v1.x a v2.x

⚠️ **Migración major**: Requiere exportación e importación manual

### Interfaz de Usuario1. Exportar datos en v1.x (si disponible función)

- **v1.0**: Formularios básicos2. Instalar v2.x en nuevo entorno

- **v2.0**: PyQt6 modernizado3. Importar datos manualmente

- **v2.5**: Vista de calendario mensual4. Ver guía de migración específica v1→v2

- **v3.0**: ⭐ **Widgets modernizados + Branding corporativo**

## 🧪 Testing por Versión

---

| Versión | Tests | Cobertura | Estado |

## 🐛 Bugs Importantes Resueltos|---------|-------|-----------|--------|

| v2.6.1  | 43    | ~85%      | ✅ Passing |

| Bug | Versión Afectada | Fix en Versión | Descripción || v2.6.0  | 40    | ~83%      | ✅ Passing |

|-----|------------------|----------------|-------------|| v2.5.0  | 35    | ~80%      | ✅ Passing |

| Inequidad en asignación | v2.0 - v2.8 | v2.9.0 | Profesores similares recibían guardias diferentes || v2.4.0  | 28    | ~75%      | ✅ Passing |

| Dashboard redundante | v2.9.0 | v3.0.0 | Eliminado dashboard con botones duplicados |

| PDFs inconsistentes | v2.0 - v2.9 | v3.0.0 | Sistema de estilos no estandarizado |## 📝 Convenciones de Versionado

| Turno mixto invisible | v2.5.0 | v2.6.0 | Campos horas_manana/tarde no se mostraban |

| Duplicados en guardias | v2.2.0 - v2.2.1 | v2.3.0 | Guardias se duplicaban al regenerar calendario |Seguimos [Semantic Versioning](https://semver.org/):



---- **MAJOR** (v1 → v2): Cambios incompatibles, breaking changes

- **MINOR** (v2.5 → v2.6): Nuevas features, compatible hacia atrás

## 🧪 Testing por Versión- **PATCH** (v2.6.0 → v2.6.1): Bug fixes, mejoras menores



| Versión | Tests | Cobertura | Estado |## 🔗 Ver También

|---------|-------|-----------|--------|

| v3.0.0  | 873+  | ~85%      | ✅ Passing |- [Roadmap](../roadmap/roadmap-v3.0.md) - Planificación futura

| v2.9.1  | 43    | ~85%      | ✅ Passing |- [Desarrollo](../desarrollo/guia-desarrollo.md) - Cómo contribuir

| v2.9.0  | 40    | ~83%      | ✅ Passing |- [Características](../tecnico/caracteristicas-sistema.md) - Specs técnicas

| v2.6.1  | 43    | ~85%      | ✅ Passing |

## 📞 Reportar Issues

---

Si encuentras un bug o tienes una sugerencia:

## 📝 Convenciones de Versionado

1. Verifica si ya está reportado: [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues)

Seguimos [Semantic Versioning](https://semver.org/):2. Si es nuevo, crea un issue con:

   - Versión afectada

- **MAJOR** (v2 → v3): Cambios significativos en arquitectura o funcionalidad   - Descripción del problema

- **MINOR** (v3.0 → v3.1): Nuevas features, compatible hacia atrás   - Pasos para reproducir

- **PATCH** (v3.0.0 → v3.0.1): Bug fixes, mejoras menores   - Comportamiento esperado vs actual

   - Screenshots si aplica

---

---

## 🔮 Próximas Versiones

[← Volver al índice principal](../README.md)

Ver [Roadmap v3.0](../roadmap/roadmap-v3.0.md) para planificación de futuras versiones.

**Posibles mejoras v3.1** (Q1 2026):
- 🎨 Más opciones de personalización de PDFs
- ⚡ Optimizaciones adicionales de rendimiento
- 📊 Estadísticas avanzadas mejoradas
- 🔔 Sistema de notificaciones ampliado

---

## 📦 Notas de Migración

### Migrando de v2.9.x a v3.0

1. **Backup**: Exporta tus datos actuales (JSON)
2. **Actualizar**: Instala v3.0
3. **Base de datos**: Se actualiza automáticamente (Alembic)
4. **Revisar**: 
   - Dashboard eliminado (funciones accesibles desde sidebar)
   - PDFs con nuevo diseño corporativo
   - Algoritmo v3.0 disponible (configurable en Configuración)
5. **Regenerar** (opcional): Regenerar calendario para aplicar algoritmo v3.0

### Migrando de v2.6.x a v2.9.x
1. **Backup**: Exporta datos
2. **Actualizar**: Instala v2.9
3. **Base de datos**: Actualización automática
4. **Regenerar**: Recomendado para aplicar equidad determinista

---

## 🔗 Ver También

- [Documentación Principal](../README.md) - Índice general
- [Roadmap](../roadmap/roadmap-v3.0.md) - Planificación futura
- [Desarrollo](../desarrollo/CONTRIBUIR.md) - Cómo contribuir
- [Archivo Histórico](../archivo/) - Documentos anteriores

---

## 📞 Reportar Issues

Si encuentras un bug o tienes una sugerencia:

1. Verifica si ya está reportado en GitHub Issues
2. Si es nuevo, crea un issue con:
   - **Versión afectada**
   - **Descripción del problema**
   - **Pasos para reproducir**
   - **Comportamiento esperado vs actual**
   - **Screenshots si aplica**

---

**Proyecto:** Guardias de Patio  
**Versión actual:** 3.0.0 ⭐  
**Última actualización:** 2 de Noviembre de 2025
