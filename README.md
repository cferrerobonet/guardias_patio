# Guardias de Patio

<!-- Build & Quality Badges -->
[![CI/CD Pipeline](https://github.com/cferrerobonet/guardias_patio/actions/workflows/ci.yml/badge.svg)](https://github.com/cferrerobonet/guardias_patio/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/cferrerobonet/guardias_patio/branch/main/graph/badge.svg)](https://codecov.io/gh/cferrerobonet/guardias_patio)
![Tests](https://img.shields.io/badge/Tests-994_total-success.svg)
![Coverage](https://img.shields.io/badge/Coverage-46.31%25-yellow.svg)

<!-- Security & Release -->
[![Security](https://img.shields.io/badge/Security-✅_0_vulnerabilities-success.svg)](documentacion/auditoria/SECURITY_FIX_20251108.md)
[![Release](https://img.shields.io/github/v/release/cferrerobonet/guardias_patio)](https://github.com/cferrerobonet/guardias_patio/releases/latest)
![Version](https://img.shields.io/badge/Version-3.0.2-blue.svg)

<!-- Tech Stack -->
![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-orange.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)

<!-- Architecture & Standards -->
![Arquitectura](https://img.shields.io/badge/Arquitectura-Clean-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-blueviolet.svg)](https://github.com/astral-sh/ruff)

**Aplicación de escritorio profesional** para la gestión integral de guardias de patio en centros educativos. Asignación automática equitativa con algoritmo optimizado, gestión completa de ausencias y sustituciones, calendario interactivo, y arquitectura limpia con 46% de cobertura de tests.

> � **v3.0.2 Released** - Ventana de detalle del día implementada: resumen completo de guardias, ausencias y sustituciones  
> �🔒 **v3.0.1 Security Update** - Todas las vulnerabilidades corregidas: 0 issues críticos, SFTP seguro  
> 🚀 **v3.0.0 Released** - Refactorización arquitectónica completa: Clean Architecture, -40% código, cache inteligente  
> 📚 [Ver Changelog](documentacion/CHANGELOG.md) | [Guía de Usuario](documentacion/USER_GUIDE.md) | [Guía Técnica](documentacion/TECHNICAL_GUIDE.md)

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Quick Start](#-quick-start)
- [Stack Tecnológico](#-stack-tecnológico)
- [Arquitectura](#-arquitectura)
- [Documentación](#-documentación)
- [Compilación y Distribución](#-compilación-y-distribución)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## ✨ Características Principales

### 🎯 Gestión Completa
- ✅ **Asignación Automática Inteligente**: Algoritmo v3.0 con distribución equitativa según % de jornada
- ✅ **Gestión de Ausencias**: Sistema completo de sustituciones con búsqueda automática de compatibles
- ✅ **Calendario Interactivo**: Vista mensual con filtros por profesor, zona y turno
- ✅ **Dashboard de Equidad**: Visualización con gráficos en tiempo real (matplotlib)
- ✅ **API REST**: Endpoints FastAPI para integraciones externas y mobile
- ✅ **Panel de Estadísticas**: Métricas en tiempo real de carga, balance y cobertura
- ✅ **Exportación Múltiple**: PDF corporativo, iCalendar (.ics), JSON para backup

### 🏗️ Arquitectura Profesional
- ✅ **Clean Architecture**: 4 capas bien separadas (Domain, Application, Infrastructure, Presentation)
- ✅ **976 Tests**: 46.31% cobertura con tests unitarios y de integración
- ✅ **Type Safety**: Validación automática con Pydantic en todas las capas
- ✅ **Cache Inteligente**: 90-98% reducción de queries en operaciones frecuentes
- ✅ **12 Widgets Reutilizables**: -40% código en formularios
- ✅ **Logging Estructurado**: Trazabilidad completa con structlog

### 🎨 UX/UI Moderna
- ✅ **Fluent Design**: Interfaz moderna inspirada en Windows 11
- ✅ **Responsive**: Validación automática de resolución (mínimo 1280x720)
- ✅ **Feedback Visual**: Indicadores de progreso y confirmaciones contextuales
- ✅ **Tooltips Intuitivos**: ~85% de campos con ayuda contextual ([Auditoría UX](documentacion/UX_AUDIT.md))
- ✅ **Confirmaciones Inteligentes**: Solo en acciones destructivas (100% apropiadas)
- ✅ **Atajos de Teclado**: 50+ shortcuts documentados ([Guía completa](documentacion/guias/KEYBOARD_SHORTCUTS.md))
- ✅ **Patrones UX Consistentes**: [Guía de patrones](documentacion/guias/UX_PATTERNS.md) para desarrollo
- ✅ **Puntuación UX**: 8.2/10 según auditoría independiente

---

## 🚀 Quick Start

### Instalación Rápida

```bash
# 1. Clonar repositorio
git clone https://github.com/cferrerobonet/guardias_patio.git
cd guardias_patio

# 2. Crear entorno virtual (Python 3.11+ requerido)
python3.11 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate    # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Inicializar base de datos
alembic upgrade head

# 5. Ejecutar aplicación
python src/main.py
```

### Primer Uso

1. **Configurar Curso** → Definir fechas, recreos y festivos
2. **Crear Zonas** → Establecer áreas de vigilancia
3. **Alta de Profesores** → Añadir profesorado con restricciones
4. **Generar Guardias** → Ejecutar algoritmo de asignación
5. **Visualizar** → Ver calendario y exportar PDFs

📖 **Guía completa**: [USER_GUIDE.md](documentacion/USER_GUIDE.md)

---

## 💻 Stack Tecnológico

| Categoría | Tecnología | Versión | Propósito |
|-----------|------------|---------|-----------|
| **Lenguaje** | Python | 3.11+ | Type hints, pattern matching |
| **GUI** | PyQt6 | 6.7.0 | Framework multiplataforma |
| **ORM** | SQLAlchemy | 2.0.31 | Gestión de base de datos |
| **Validación** | Pydantic | 2.8.2 | Type safety y schemas |
| **Migraciones** | Alembic | 1.13.2 | Control de versiones BD |
| **Testing** | Pytest | 8.3.2 | Framework de tests |
| **Linter** | Ruff | 0.5.5 | Linting ultra-rápido |
| **Logging** | Structlog | 24.4.0 | Logs estructurados |
| **BD** | SQLite | 3.x | Base de datos embebida |

**Compatibilidad**: macOS 11+, Windows 10+, Linux (Ubuntu 20.04+)

---

## 🏛️ Arquitectura

**Clean Architecture** con separación clara en 4 capas:

```
┌─────────────────────────────────────────────────────┐
│  🟪 PRESENTATION (PyQt6)                            │
│  ├─ forms/          Formularios CRUD                │
│  ├─ widgets/        12 widgets reutilizables        │
│  └─ dialogs/        Diálogos y confirmaciones       │
├─────────────────────────────────────────────────────┤
│  🟩 APPLICATION                                     │
│  ├─ use_cases/      Lógica de negocio              │
│  ├─ dtos/           Data Transfer Objects           │
│  └─ cache/          Sistema de caché TTL           │
├─────────────────────────────────────────────────────┤
│  🟨 INFRASTRUCTURE                                  │
│  ├─ repositories/   Persistencia de datos          │
│  ├─ mappers/        Conversión Modelo ↔ Entidad   │
│  └─ services/       Servicios externos             │
├─────────────────────────────────────────────────────┤
│  🟦 DOMAIN                                          │
│  ├─ entities/       Entidades de negocio           │
│  ├─ value_objects/  Objetos de valor               │
│  └─ interfaces/     Contratos de repositorios      │
└─────────────────────────────────────────────────────┘
```

**Flujo de Datos**: `UI → Use Cases → Services → Repositories → Database`

**Beneficios**:
- ✅ Testabilidad: 976 tests, 46.31% cobertura
- ✅ Mantenibilidad: Cambios aislados por capa
- ✅ Escalabilidad: Fácil añadir features
- ✅ Independencia: Domain sin dependencias externas

📚 **Documentación completa**: [TECHNICAL_GUIDE.md](documentacion/TECHNICAL_GUIDE.md)

---

## 📚 Documentación

### 📖 Para Usuarios

| Documento | Descripción |
|-----------|-------------|
| **[USER_GUIDE.md](documentacion/USER_GUIDE.md)** | Tutorial completo paso a paso |
| **[KEYBOARD_SHORTCUTS.md](documentacion/guias/KEYBOARD_SHORTCUTS.md)** | 50+ atajos de teclado documentados |

### �‍💻 Para Desarrolladores

| Documento | Descripción |
|-----------|-------------|
| **[ARCHITECTURE.md](documentacion/ARCHITECTURE.md)** | Clean Architecture - 4 capas, dependencias, patrones ⭐⭐⭐⭐ |
| **[TECHNICAL_GUIDE.md](documentacion/TECHNICAL_GUIDE.md)** | Algoritmos, validaciones, cache, logging |
| **[TESTING.md](documentacion/TESTING.md)** | 976 tests, 46% coverage, guía completa pytest |
| **[CONTRIBUTING.md](documentacion/CONTRIBUTING.md)** | Workflow, estándares de código, PR guidelines |
| **[UX_PATTERNS.md](documentacion/guias/UX_PATTERNS.md)** | Patrones UI/UX para desarrollo consistente |

### 🚀 Para DevOps / Mantenedores

| Documento | Descripción |
|-----------|-------------|
| **[DEPLOYMENT.md](documentacion/DEPLOYMENT.md)** | Build macOS/Windows, PyInstaller, DMG |
| **[CI_CD.md](documentacion/CI_CD.md)** | GitHub Actions, workflows automáticos |
| **[BRANCH_PROTECTION.md](documentacion/guias/BRANCH_PROTECTION_SETUP.md)** | Setup protección rama main |
| **[MAINTENANCE.md](documentacion/MAINTENANCE.md)** | Backups, limpieza BD, checklists |
| **[SECURITY.md](documentacion/SECURITY.md)** | Política seguridad, reporte vulnerabilidades |

### 📊 Referencia

| Documento | Descripción |
|-----------|-------------|
| **[CHANGELOG.md](documentacion/CHANGELOG.md)** | Historial completo de versiones |
| **[PREMISAS_ASIGNACION.md](documentacion/PREMISAS_ASIGNACION_GUARDIAS.md)** | Reglas de negocio asignación |
| **[UX_AUDIT.md](documentacion/UX_AUDIT.md)** | Auditoría UX completa (8.2/10) |
| **[API Reference](documentacion/api/)** | Documentación técnica de la API |

### 🎯 Por Caso de Uso

**¿Quieres empezar a usar la app?**  
→ [USER_GUIDE.md](documentacion/USER_GUIDE.md)

**¿Vas a desarrollar o contribuir?**  
→ [ARCHITECTURE.md](documentacion/ARCHITECTURE.md) + [CONTRIBUTING.md](documentacion/CONTRIBUTING.md)

**¿Necesitas compilar/desplegar?**  
→ [DEPLOYMENT.md](documentacion/DEPLOYMENT.md)

**¿Configurar CI/CD?**  
→ [CI_CD.md](documentacion/CI_CD.md) + [BRANCH_PROTECTION](documentacion/guias/BRANCH_PROTECTION_SETUP.md)

### 📝 Índice Completo

Ver [documentacion/README.md](documentacion/README.md) para el índice completo de toda la documentación.

**Resultados de auditoría UX:**
- ✅ 85% de campos con tooltip/placeholder (objetivo: ≥80%)
- ✅ 100% de confirmaciones apropiadas
- ✅ 8.2/10 puntuación global (MUY BUENO)
- ✅ Patrones documentados para desarrollo consistente

### �🎯 Por Tema

**Instalación y Uso**
- [Guía de Usuario](documentacion/USER_GUIDE.md) - Tutorial completo paso a paso
- Requisitos del sistema y resolución de problemas

**Desarrollo**
- [Guía Técnica](documentacion/TECHNICAL_GUIDE.md) - Arquitectura, algoritmos, validaciones
- [Guía de Contribución](documentacion/CONTRIBUTING.md) - Workflow, estándares, testing

**Despliegue**
- [Guía de Despliegue](documentacion/DEPLOYMENT.md) - Build macOS/Windows, distribución
- Troubleshooting de compilación

**Mantenimiento**
- [Seguridad](documentacion/SECURITY.md) - Reporte vulnerabilidades, buenas prácticas
- [Mantenimiento](documentacion/MAINTENANCE.md) - Backups, limpieza, actualizaciones

### 📝 Índice Completo

Ver [documentacion/README.md](documentacion/README.md) para el índice completo de toda la documentación.

---

## 🔨 Compilación y Distribución

### Compilación Rápida

```bash
# macOS - Ejecutable + DMG
./scripts/build/build_simple.sh
./scripts/build/create_dmg.sh

# Windows - Ejecutable + Instalador
python -m PyInstaller GuardiasDePatio.spec
```

### Documentación Completa

📚 **[DEPLOYMENT.md](documentacion/DEPLOYMENT.md)** - Guía completa de despliegue

**Incluye:**
- ✅ Requisitos de compilación (macOS/Windows)
- ✅ Configuración del entorno de build
- ✅ Proceso paso a paso con PyInstaller
- ✅ Creación de instaladores (DMG/InnoSetup)
- ✅ Testing de ejecutables
- ✅ Distribución y release en GitHub
- ✅ Troubleshooting completo
- ✅ Checklist de distribución

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas! Lee nuestra [**Guía de Contribución**](documentacion/CONTRIBUTING.md) completa.

### Quick Start para Contribuir

1. **Fork** el repositorio
2. **Crea rama**: `git checkout -b feature/mi-feature`
3. **Configura entorno**: `python3.11 -m venv venv && pip install -r requirements.txt`
4. **Haz cambios** siguiendo estándares de código
5. **Tests**: `pytest` (asegura que todo pasa)
6. **Commit**: `git commit -m "feat: descripción"` (Conventional Commits)
7. **Push**: `git push origin feature/mi-feature`
8. **Pull Request** con descripción detallada

### Convenciones

- **Commits**: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- **Código**: PEP 8, type hints, docstrings Google Style
- **Tests**: Obligatorios para features nuevas
- **Cobertura**: Mínimo 70% en código nuevo

📖 **Documentación completa**: [CONTRIBUTING.md](documentacion/CONTRIBUTING.md)

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver [LICENSE](LICENSE) para detalles completos.

```
MIT License - Copyright (c) 2024-2025 Carlos Ferrero Bonet
```

---

## 👤 Autor

**Carlos Ferrero Bonet**

- 💼 GitHub: [@cferrerobonet](https://github.com/cferrerobonet)
- 📧 Email: cferrerobonet@gmail.com
- 🔗 Proyecto: [github.com/cferrerobonet/guardias_patio](https://github.com/cferrerobonet/guardias_patio)

---

## 📊 Estadísticas del Proyecto

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| **Versión** | 3.0.0 | Release actual |
| **Tests** | 976 | Tests pasando |
| **Cobertura** | 46.31% | Cobertura de código |
| **Líneas de código** | ~12,250 | Total líneas Python |
| **Archivos Python** | 93 | Módulos del proyecto |
| **Widgets** | 12 | Componentes reutilizables |
| **Reducción código** | -40% | En formularios (v3.0) |
| **Última actualización** | 8 nov 2025 | Fecha release |

---

## 🔗 Enlaces Útiles

- 📦 **[Releases](https://github.com/cferrerobonet/guardias_patio/releases)** - Descargas y changelog
- 🐛 **[Issues](https://github.com/cferrerobonet/guardias_patio/issues)** - Reportar bugs o sugerir features
- 📚 **[Documentación](documentacion/README.md)** - Índice completo de docs
- 🔒 **[Seguridad](documentacion/SECURITY.md)** - Reportar vulnerabilidades
- 🛠️ **[Mantenimiento](documentacion/MAINTENANCE.md)** - Guía de mantenimiento

---

<div align="center">

### ⭐ Si este proyecto te resulta útil, dale una estrella en GitHub ⭐

**Made with ❤️ by [Carlos Ferrero Bonet](https://github.com/cferrerobonet)**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

</div>
