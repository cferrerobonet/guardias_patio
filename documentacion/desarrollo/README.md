# 🔧 Documentación para Desarrolladores

Esta carpeta contiene documentación técnica dirigida a desarrolladores que trabajan en el proyecto **Guardias de Patio**.

**Versión:** 3.0.0  
**Última actualización:** 2 de Noviembre de 2025

---

## 📚 Contenido

### 📖 Guías de Desarrollo

- **[CONTRIBUIR.md](CONTRIBUIR.md)** - Cómo contribuir al proyecto
  - Estándares de código
  - Proceso de desarrollo
  - Guía de commits
  - Pull requests

- **[HISTORIA_SPRINTS.md](HISTORIA_SPRINTS.md)** - Historial de sprints de desarrollo
  - Evolución del proyecto
  - Decisiones técnicas
  - Lecciones aprendidas

- **[HISTORIAL_LIMPIEZAS.md](HISTORIAL_LIMPIEZAS.md)** ✨ - Historial de reorganizaciones
  - Limpieza Nov 2025 (Post-refactorización)
  - Limpieza Nov 2025 (Usuarios y BD)
  - Reorganización Oct 2025
  - Métricas y resultados

### 📦 Archivo Histórico

- **[ARCHIVO_HISTORICO_INFO.md](ARCHIVO_HISTORICO_INFO.md)** - Información sobre sprints archivados
  - Sprints 1-12 comprimidos
  - Ubicación: `ARCHIVO_HISTORICO_SPRINTS.tar.gz` (raíz del proyecto)
  - Razones del archivado

---

## 🏗️ Arquitectura

Para información sobre la arquitectura del proyecto, consulta:
- `../tecnico/ARCHITECTURE_PATTERNS.md` - Patrones arquitectónicos
- `../tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md` - Algoritmo completo de asignación
- `../PREMISAS_ASIGNACION_GUARDIAS.md` - Premisas y reglas del algoritmo

---

## 🧪 Testing

Para documentación sobre pruebas y validaciones:
- `../tecnico/VALIDACIONES_NEGOCIO.md` - Validaciones de negocio
- `../../tests/` - Tests del proyecto (873+ tests, ~85% cobertura)

---

## 🔧 Herramientas de Desarrollo

### Scripts Útiles

Ver `../../scripts/` para scripts de desarrollo y análisis:
- `scripts/build/` - Compilación y distribución
- `scripts/dev/` - Desarrollo y debugging
- Profiling de rendimiento
- Análisis de queries
- Generación de reportes

### Compilación y Distribución

Ver `../build/` para:
- [GUIA_COMPILACION.md](../build/GUIA_COMPILACION.md) - Guía consolidada
- [BUILD_DMG.md](../build/BUILD_DMG.md) - macOS DMG
- [BUILD_WINDOWS.md](../build/BUILD_WINDOWS.md) - Windows Setup
- Solución de problemas

---

## 📝 Estándares de Código

### Python

- **Versión:** Python 3.11+
- **Estilo:** PEP 8
- **Linter:** Ruff
- **Type checking:** MyPy
- **Imports:** isort
- **Formateo:** Black (opcional)

### Commits

Seguir **Conventional Commits**:
```
<tipo>(<alcance>): <descripción>

[cuerpo opcional]

[footer opcional]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formateo de código
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Tareas de mantenimiento
- `perf`: Mejoras de rendimiento

**Ejemplos:**
```
feat(algoritmo): añadir prioridad de fechas consecutivas
fix(pdf): corregir colores de zona en mini-calendarios
docs(premisas): actualizar documentación algoritmo v3.0
refactor(widgets): consolidar dashboard duplicado
```

---

## 🚀 Flujo de Desarrollo

1. **Crear rama** desde `main`:
   ```bash
   git checkout -b feature/nombre-funcionalidad
   # o
   git checkout -b fix/nombre-bug
   ```

2. **Desarrollar** siguiendo estándares

3. **Tests**: Verificar que los tests pasan
   ```bash
   pytest
   # o específicos
   pytest tests/test_algoritmo.py
   ```

4. **Linting**: Verificar código
   ```bash
   ruff check src/
   mypy src/
   ```

5. **Commit** con mensaje descriptivo siguiendo Conventional Commits

6. **Push** y crear **Pull Request**

7. **Review** y merge a `main`

---

## 📦 Estructura del Proyecto

```
guardias_patio/
├── src/                    # Código fuente
│   ├── application/        # Casos de uso
│   ├── core/               # Núcleo del sistema (observability)
│   ├── database/           # Gestión de BD
│   ├── infrastructure/     # Repositorios y servicios externos
│   ├── models/             # Modelos de datos (SQLAlchemy)
│   ├── presentation/       # UI (PyQt6)
│   │   ├── components/     # Componentes reutilizables
│   │   ├── dialogs/        # Diálogos y modales
│   │   ├── forms/          # Formularios principales
│   │   ├── themes/         # Temas y estilos
│   │   └── widgets/        # Widgets personalizados
│   ├── services/           # Servicios de negocio
│   ├── sync/               # Sincronización SFTP
│   └── utils/              # Utilidades
├── tests/                  # Tests (873+ tests)
├── scripts/                # Scripts de utilidad
│   ├── build/              # Scripts de compilación
│   └── dev/                # Scripts de desarrollo
├── documentacion/          # Documentación
├── alembic/                # Migraciones de BD
└── ...
```

---

## 🎯 Versión Actual: 3.0.0

### Novedades

- ✨ **Sistema de PDFs Corporativos** - Ver `../tecnico/SISTEMA_PDF_CORPORATIVO.md`
- ✨ **Algoritmo v3.0 con fechas consecutivas** - Ver `../PREMISAS_ASIGNACION_GUARDIAS.md`
- ✨ **Refactorización arquitectónica** - Formularios homogeneizados
- ✅ **Dashboard eliminado** - Eliminada redundancia en UI

Ver [CHANGELOG v3.0](../versiones/CHANGELOG_v3.0.md) para detalles completos.

---

## 🔗 Enlaces Útiles

- **Repositorio:** https://github.com/cferrerobonet/guardias_patio
- **Issues:** https://github.com/cferrerobonet/guardias_patio/issues
- **Releases:** https://github.com/cferrerobonet/guardias_patio/releases
- **Documentación Principal:** [../README.md](../README.md)
- **Changelog Actual:** [../versiones/CHANGELOG_v3.0.md](../versiones/CHANGELOG_v3.0.md)

---

**Proyecto:** Guardias de Patio  
**Versión:** 3.0.0  
**Última actualización:** 2 de Noviembre de 2025
