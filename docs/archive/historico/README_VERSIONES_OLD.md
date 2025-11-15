# Historial de Versiones

Documentación de todas las versiones del sistema con sus cambios, mejoras y características.

## 📦 Versión Actual: v2.6.1

### [v2.6 - Zona Preferida](v2.6/)

**Fecha**: Diciembre 2024

**Características Principales**:
- ✨ **Zona Preferida**: Sistema inteligente que mantiene a cada profesor en su zona asignada
- 🎯 Algoritmo de scoring mejorado (5-tuplas con prioridad de zona)
- 📊 100% de consistencia en zona (test validado)
- 🐛 Fix: Campos de turno mixto no se mostraban correctamente

**Documentación**:
- [Changelog v2.6](v2.6/changelog.md) - Lista completa de cambios
- [Zona Preferida](v2.6/zona-preferida.md) - Documentación técnica de la feature
- [Ejemplos](v2.6/ejemplos-zona-preferida.md) - Casos de uso y escenarios
- [Resumen de Implementación](v2.6/resumen-implementacion.md) - Detalles técnicos

**Impacto**:
- 👨‍🏫 Los profesores ya no necesitan consultar su zona cada día
- 📈 Mejora la organización y predictibilidad
- ⚡ Reduce tiempo de coordinación

---

### [v2.5 - Gestión de Ausencias](v2.5/)

**Fecha**: Octubre 2024

**Características Principales**:
- 📅 Sistema completo de gestión de ausencias
- 🔄 Sustituciones automáticas y manuales
- 📊 Vista de calendario mensual mejorada
- 📤 Mejoras en importación/exportación

**Documentación**:
- [Changelog v2.5](v2.5/changelog.md)

**Impacto**:
- 🏥 Control centralizado de bajas y permisos
- ⚡ Sustituciones más rápidas y organizadas
- 📈 Visibilidad completa del mes

---

## 📊 Línea Temporal

```
v2.6.1 (Dic 2024)  ● Zona Preferida + Reorganización docs
                   │
v2.6.0 (Dic 2024)  ● Zona Preferida feature
                   │
v2.5.0 (Oct 2024)  ● Gestión de Ausencias + Vista Calendario
                   │
v2.4.0 (Sep 2024)  ● Importación/Exportación JSON
                   │
v2.3.0 (Ago 2024)  ● Optimizaciones de rendimiento
                   │
v2.2.0 (Jul 2024)  ● Refactorización major
                   │
v2.1.0 (Jun 2024)  ● Nuevas funcionalidades base
                   │
v2.0.0 (May 2024)  ● Reescritura PyQt6
                   │
v1.1.0 (Abr 2024)  ● Mejoras UI iniciales
                   │
v1.0.0 (Mar 2024)  ● Release inicial
```

## 🔍 Buscar por Característica

| Característica | Versión Introducida | Documentación |
|----------------|---------------------|---------------|
| Zona Preferida | v2.6.0 | [Docs](v2.6/zona-preferida.md) |
| Gestión de Ausencias | v2.5.0 | [Docs](../funcionalidades/ausencias/gestion.md) |
| Vista Calendario | v2.5.0 | [Docs](../funcionalidades/calendario/vista-mensual.md) |
| Importar/Exportar | v2.4.0 | [Docs](../funcionalidades/importar-exportar/README.md) |
| Turno Mixto | v2.6.0 | [Changelog](v2.6/changelog.md) |
| Algoritmo de Scoring | v2.6.0 | [Zona Preferida](v2.6/zona-preferida.md) |

## 📈 Evolución de Features

### Sistema de Asignación
- v1.0: Asignación básica aleatoria
- v2.0: Algoritmo con restricciones
- v2.2: Refactorización con scoring
- v2.6: **Zona preferida con prioridad alta**

### Gestión de Profesores
- v1.0: CRUD básico
- v2.0: Condiciones avanzadas (turnos, días, recreos)
- v2.6: **Turno mixto con horas específicas**

### Interfaz de Usuario
- v1.0: Formularios básicos
- v2.0: PyQt6 modernizado
- v2.5: **Vista de calendario mensual**
- v2.6: **Mejoras UX en turno mixto**

### Datos y Persistencia
- v1.0: SQLite básico
- v2.2: SQLAlchemy ORM
- v2.4: **Sistema de importación/exportación**

## 🐛 Bugs Importantes Resueltos

| Bug | Versión Afectada | Fix en Versión | Descripción |
|-----|------------------|----------------|-------------|
| Duplicados en guardias | v2.2.0 - v2.2.1 | v2.3.0 | Guardias se duplicaban al regenerar calendario |
| Turno mixto invisible | v2.5.0 | v2.6.0 | Campos horas_manana/tarde no se mostraban |
| Memoria en calendario | v2.4.0 | v2.5.0 | Memory leak en vista calendario |
| PyQt6 incompatibilidades | v2.0.0 - v2.1.0 | v2.2.0 | Problemas con Python 3.11+ |

## 🔮 Próximas Versiones

Ver [Roadmap v3.0](../roadmap/roadmap-v3.0.md) para planificación de futuras versiones.

**Adelanto v2.7** (Q1 2025):
- 🎨 Mejoras visuales en UI
- ⚡ Optimizaciones de rendimiento
- 📊 Estadísticas avanzadas
- 🔔 Sistema de notificaciones

**Adelanto v3.0** (Q2 2025):
- 🌐 Versión web/multi-plataforma
- 👥 Multi-usuario con roles
- 🔄 Sincronización en tiempo real
- 📱 App móvil companion

## 📦 Notas de Migración

### Migrando de v2.5 a v2.6
1. **Backup**: Exporta tus datos actuales
2. **Actualizar**: Instala v2.6
3. **Base de datos**: Se actualiza automáticamente (Alembic)
4. **Revisar**: Zonas preferidas se asignarán en primera guardia
5. **Regenerar**: Opcional - regenerar calendario para aplicar zona preferida

### Migrando de v2.4 a v2.5
1. **Backup**: Exporta datos
2. **Actualizar**: Instala v2.5
3. **Nueva tabla**: Alembic crea tabla `ausencias`
4. **Configurar**: Define ausencias existentes si las hay

### Migrando de v1.x a v2.x
⚠️ **Migración major**: Requiere exportación e importación manual
1. Exportar datos en v1.x (si disponible función)
2. Instalar v2.x en nuevo entorno
3. Importar datos manualmente
4. Ver guía de migración específica v1→v2

## 🧪 Testing por Versión

| Versión | Tests | Cobertura | Estado |
|---------|-------|-----------|--------|
| v2.6.1  | 43    | ~85%      | ✅ Passing |
| v2.6.0  | 40    | ~83%      | ✅ Passing |
| v2.5.0  | 35    | ~80%      | ✅ Passing |
| v2.4.0  | 28    | ~75%      | ✅ Passing |

## 📝 Convenciones de Versionado

Seguimos [Semantic Versioning](https://semver.org/):

- **MAJOR** (v1 → v2): Cambios incompatibles, breaking changes
- **MINOR** (v2.5 → v2.6): Nuevas features, compatible hacia atrás
- **PATCH** (v2.6.0 → v2.6.1): Bug fixes, mejoras menores

## 🔗 Ver También

- [Roadmap](../roadmap/roadmap-v3.0.md) - Planificación futura
- [Desarrollo](../desarrollo/guia-desarrollo.md) - Cómo contribuir
- [Características](../tecnico/caracteristicas-sistema.md) - Specs técnicas

## 📞 Reportar Issues

Si encuentras un bug o tienes una sugerencia:

1. Verifica si ya está reportado: [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues)
2. Si es nuevo, crea un issue con:
   - Versión afectada
   - Descripción del problema
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Screenshots si aplica

---

[← Volver al índice principal](../README.md)
