# Guardias de Patio

![Version](https://img.shields.io/badge/Version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-orange.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-2.0-purple.svg)
![Arquitectura](https://img.shields.io/badge/Arquitectura-Clean-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Stable-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Aplicación de escritorio profesional** para la gestión integral de guardias de patio en centros educativos. Asignación automática equitativa, gestión de ausencias y sustituciones, exportación de calendarios, y sistema completo de observabilidad.

> 🚀 **v3.0.0 Released** - Refactorización arquitectónica: -40% código en formularios, cache en 12 Use Cases, +12 widgets reutilizables  
> 📚 [Ver Changelog v3.0](documentacion/versiones/CHANGELOG_v3.0.md) | [Changelog v2.9.1](documentacion/versiones/CHANGELOG_v2.9.1.md)

---

## 📋 Tabla de Contenidos

- [Características Principales](#-características-principales)
- [Stack Tecnológico](#️-stack-tecnológico)
- [Arquitectura](#️-arquitectura)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Compilación](#-compilación)
- [Documentación](#-documentación)
- [Roadmap](#️-roadmap)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## 🚀 Compilación Rápida

Para compilar la aplicación en macOS:

```bash
./scripts/build/build_simple.sh
```

Para crear el instalador DMG:

```bash
./scripts/build/create_dmg.sh
```

**¿Problemas al compilar?** → Lee [`documentacion/build/GUIA_COMPILACION.md`](./documentacion/build/GUIA_COMPILACION.md)

**Documentación completa de compilación:**
- [`documentacion/build/GUIA_COMPILACION.md`](./documentacion/build/GUIA_COMPILACION.md) - Guía consolidada de compilación y distribución
- [`documentacion/build/BUILD_DMG.md`](./documentacion/build/BUILD_DMG.md) - Crear instalador DMG para macOS
- [`documentacion/build/BUILD_WINDOWS.md`](./documentacion/build/BUILD_WINDOWS.md) - Crear instalador para Windows

---

## 📋 Tabla de Contenidos (Original)

- [Características Principales](#-características-principales)
- [Stack Tecnológico](#️-stack-tecnológico)
- [Arquitectura](#️-arquitectura)
- [Instalación](#-instalación)
- [Uso](#-uso)
- [Documentación](#-documentación)
- [Roadmap](#️-roadmap)
- [Contribución](#-contribución)
- [Licencia](#-licencia)

---

## ✨ Características Principales

### 🎯 Gestión Completa de Guardias
- ✅ **Asignación Automática Equitativa**: Algoritmo que distribuye guardias proporcionalmente según porcentaje de jornada
- ✅ **Gestión de Ausencias y Sustituciones**: Sistema completo para manejar profesores ausentes
- ✅ **Vista de Calendario Interactiva**: Visualización mensual con filtros por profesor, zona y turno
- ✅ **Estadísticas en Tiempo Real**: Panel con métricas de carga, balance y cobertura
- ✅ **Importar/Exportar Datos**: Portabilidad completa en JSON para backup y migración

### 🏗️ Arquitectura y Calidad
- ✅ **Clean Architecture**: Separación en capas (Domain, Application, Infrastructure, Presentation)
- ✅ **Patrón de Widgets**: 12 widgets reutilizables extraídos, -40.3% código en formularios
- ✅ **Sistema de Cache**: Cache inteligente en 12 Use Cases (90-98% menos queries)
- ✅ **Type Safety con Pydantic**: Validación automática de datos en todas las capas
- ✅ **Sistema de Observabilidad**: Dashboard con métricas, health checks y logs
- ✅ **Inyección de Dependencias**: Acoplamiento débil entre componentes
- ✅ **Performance Optimizado**: Eager loading, caching inteligente, eliminación de N+1 queries

### 🎨 UX Profesional
- ✅ **Logo Corporativo**: Branding consistente en todos los diálogos
- ✅ **Actualización Automática**: Sistema de señales Qt para refresh de listas
- ✅ **Indicadores de Progreso**: Feedback visual en operaciones largas
- ✅ **Validaciones en Tiempo Real**: Mensajes claros y contextuales
- ✅ **Ventana Maximizada por Defecto**: Aprovecha todo el espacio disponible

---

## 🛠️ Stack Tecnológico

### Core
- **Python 3.11+**: Lenguaje principal con type hints y pattern matching
- **PyQt6 6.7.0**: Framework GUI multiplataforma
- **SQLAlchemy 2.0**: ORM con soporte async y relationship eager loading
- **Alembic**: Migraciones de base de datos versionadas
- **Pydantic 2.0**: Validación de datos y schemas

### Utilidades
- **python-dateutil**: Manejo avanzado de fechas
- **structlog**: Logging estructurado
- **pytest**: Framework de testing
- **ruff**: Linter y formatter ultra-rápido

### Base de Datos
- **SQLite**: Base de datos embebida (default)
- Compatible con PostgreSQL y MySQL

---

## 🏛️ Arquitectura

Sistema basado en **Clean Architecture** con separación clara de responsabilidades en 4 capas:

```
src/
├── presentation/          # 🟪 CAPA DE PRESENTACIÓN (PyQt6)
│   ├── forms/            # Formularios CRUD
│   ├── widgets/          # Widgets especializados
│   └── main_window.py    # Ventana principal
│
├── application/          # 🟩 CAPA DE APLICACIÓN
│   ├── use_cases/       # Casos de uso del negocio
│   └── dtos/            # Data Transfer Objects
│
├── infrastructure/       # 🟨 CAPA DE INFRAESTRUCTURA
│   ├── repositories/    # Implementaciones de repositorios
│   ├── mappers/         # Conversión Modelo ↔ Entidad
│   └── database/        # Configuración de BD
│
├── models/              # 📦 MODELOS (SQLAlchemy)
│   └── models.py        # Profesor, Zona, Guardia, etc.
│
├── services/            # 🔧 SERVICIOS DE NEGOCIO
│   ├── asignador_guardias.py
│   ├── calculador_guardias.py
│   └── gestor_ausencias.py
│
└── utils/               # 🛠️ UTILIDADES
    ├── validators.py
    ├── exceptions.py
    └── ui_helpers.py
```

### Flujo de Datos
```
UI → Use Cases → Services → Repositories → Database
 ↓       ↓          ↓           ↓            ↓
Forms   DTOs    Business    Mappers      Models
```

📚 **Documentación completa**: [ARQUITECTURA.md](documentacion/ARQUITECTURA.md)

---

## 📦 Instalación

### Requisitos Previos

> ⚠️ **IMPORTANTE:** Verifica que tu sistema cumple con los [**requisitos mínimos del sistema**](documentacion/REQUISITOS_SISTEMA.md) antes de instalar.

**Requisitos de Hardware:**
- **Resolución de pantalla:** 1280x720 píxeles (mínimo), 1920x1080 recomendado
- **RAM:** 4 GB mínimo, 8 GB recomendado
- **Espacio en disco:** 500 MB libres

**Requisitos de Software:**
- **Python 3.11+** (obligatorio)
- **pip** actualizado
- **Git**

📋 Ver [**Requisitos Completos del Sistema**](documentacion/REQUISITOS_SISTEMA.md) para detalles sobre:
- Sistemas operativos soportados (macOS, Windows, Linux)
- Validación automática de resolución de pantalla
- Solución de problemas comunes
- Tabla comparativa de configuraciones

### Pasos de Instalación

#### 1. Clonar el Repositorio

```bash
git clone https://github.com/cferrerobonet/guardias_patio.git
cd guardias_patio
```

#### 2. Crear Entorno Virtual

```bash
# macOS/Linux
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

#### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

#### 4. Configurar Base de Datos

```bash
alembic upgrade head
```

#### 5. Ejecutar la Aplicación

```bash
python src/main.py
```

O usar el script incluido:

```bash
# macOS/Linux
chmod +x run_app.sh
./run_app.sh
```

### Verificación

```bash
# Verificar versión de Python
python --version  # Debe ser 3.11+

# Verificar dependencias
pip list | grep -E 'PyQt6|SQLAlchemy|pydantic'
```

---

## 🚀 Uso

### Primer Uso

1. **Configurar Curso** → Fechas, horarios de recreos, festivos
2. **Crear Zonas** → Áreas de vigilancia del patio
3. **Dar de Alta Profesores** → Nombre, email, horas, turno, restricciones
4. **Generar Guardias** → Asignación automática equitativa
5. **Visualizar Calendario** → Ver guardias con filtros

### Operaciones Comunes

#### Gestión de Profesores
- **Alta**: Formulario con validación en tiempo real
- **Edición**: Actualización automática de listas
- **Restricciones**: Personalizar días y recreos no permitidos

#### Generación de Guardias
- **Algoritmo inteligente** que respeta:
  - Turno del profesor
  - Restricciones de horario
  - Distribución equitativa según % jornada
  - Evita 2+ guardias el mismo día

#### Gestión de Ausencias
- Registrar ausencias con fechas y motivo
- Buscar sustituto compatible automáticamente
- Historial de sustituciones

#### Importar/Exportar
- **Exportar**: Backup completo a JSON
- **Importar**: Restaurar datos desde JSON
- **Portabilidad**: Transferir entre equipos

---

## 📚 Documentación

### 📖 Índice Principal

🗂️ **[Documentación Completa](documentacion/README.md)** - Tabla de contenidos organizada por categorías

La documentación está organizada en las siguientes categorías:

#### 🔧 Desarrollo
- [**HISTORIAL_LIMPIEZAS.md**](documentacion/desarrollo/HISTORIAL_LIMPIEZAS.md) 📦 - Historial consolidado de limpiezas del proyecto
- [Resumen Ejecutivo Refactorización](documentacion/desarrollo/RESUMEN_EJECUTIVO_REFACTORIZACION.md)
- [Sprint 1.2 - Plan Detallado](documentacion/desarrollo/SPRINT_1.2_PLAN_DETALLADO.md)
- [Guía para Contribuir](documentacion/desarrollo/CONTRIBUIR.md)
- [Historia de Sprints](documentacion/desarrollo/HISTORIA_SPRINTS.md)

#### ⚙️ Técnico
- [**ALGORITMO_ASIGNACION_GUARDIAS.md**](documentacion/tecnico/ALGORITMO_ASIGNACION_GUARDIAS.md) 📦 - Documentación consolidada del algoritmo
- [Patrón de Widgets](documentacion/tecnico/PATRON_WIDGETS.md)
- [Mejoras UX Tablas v3.0](documentacion/tecnico/MEJORAS_UX_TABLAS_v3.0.md)
- [Patrones de Arquitectura](documentacion/tecnico/ARCHITECTURE_PATTERNS.md)
- [Configuración Email SMTP](documentacion/tecnico/CONFIGURACION_EMAIL_SMTP.md)
- [Validaciones de Negocio](documentacion/tecnico/VALIDACIONES_NEGOCIO.md)

#### 🏗️ Build y Distribución
- [**GUIA_COMPILACION.md**](documentacion/build/GUIA_COMPILACION.md) 📦 - Guía consolidada de compilación
- [Build DMG (macOS)](documentacion/build/BUILD_DMG.md)
- [Build Windows](documentacion/build/BUILD_WINDOWS.md)
- [Instrucciones GitHub Release](documentacion/build/GITHUB_RELEASE_INSTRUCTIONS.md)

#### 🎯 Funcionalidades
- [Funcionalidades Completas](documentacion/funcionalidades/FUNCIONALIDADES_COMPLETAS.md)

#### 📖 Guías de Uso
- [Guía UI Features](documentacion/guias/GUIA_UI_FEATURES.md)
- [Atajos de Teclado](documentacion/guias/atajos-teclado.md)

#### 📋 Versiones y Changelogs
- [CHANGELOG v3.0](documentacion/versiones/CHANGELOG_v3.0.md)
- [CHANGELOG v2.9.1](documentacion/versiones/CHANGELOG_v2.9.1.md)
- [CHANGELOG v2.9](documentacion/versiones/CHANGELOG_v2.9.md)
- [Release Notes v2.9.1](documentacion/versiones/RELEASE_NOTES_v2.9.1.md)

#### 🗺️ Roadmap
- [Roadmap v3.0](documentacion/roadmap/roadmap-v3.0.md)

#### 📦 Archivo Histórico
- [Documentos Archivados](documentacion/archivo/) - Planes completados y documentos históricos

> 📦 **Nota**: Los archivos marcados con 📦 son documentos consolidados que reemplazan múltiples archivos anteriores.

### Documentación de Referencia Rápida

- **[INDICE_RAPIDO.md](documentacion/INDICE_RAPIDO.md)** - Acceso rápido a documentos por tema
- **[Requisitos del Sistema](documentacion/tecnico/REQUISITOS_SISTEMA.md)** - Requisitos mínimos y recomendados

---

## 🗺️ Roadmap

### ✅ v3.0 - Refactorización Arquitectónica (Completado)

- ✅ **Patrón de Widgets**: 12 widgets reutilizables extraídos
- ✅ **Reducción de código**: -2,757 líneas (-40.3% en formularios)
- ✅ **Sistema de Cache**: Cache en 12 Use Cases (90-98% menos queries)
- ✅ **TTL diferenciado**: Configuración (10min), Zonas (5min), Profesores (3min)
- ✅ **Compatibilidad retroactiva**: 100% sin breaking changes
- ✅ **Documentación**: Patrón documentado para futuros desarrollos

### ✅ v2.9 - Sistema Multi-usuario y Cloud (Completado)

- ✅ **Sistema Multi-usuario**: Gestión de múltiples usuarios con recuperación de contraseña por email
- ✅ **Sincronización Cloud**: Soporte SFTP para sincronización entre dispositivos
- ✅ **Dashboard de observabilidad**: Métricas, health checks y logs
- ✅ **Logo corporativo**: Branding consistente
- ✅ **Performance**: Eager loading, eliminación N+1 queries

### ✅ v2.8 - Features Principales (Completado)

- ✅ **CRUD completo**: Profesores, Zonas, Guardias, Configuración
- ✅ **Generación automática de guardias**: Asignación equitativa según % jornada
- ✅ **Vista de calendario interactiva**: Visualización mensual con filtros
- ✅ **Gestión de ausencias y sustituciones**: Sistema completo
- ✅ **Panel de estadísticas**: Métricas en tiempo real
- ✅ **Importar/Exportar JSON**: Portabilidad completa

### 🔄 v3.1 - Refactorización Avanzada (En Desarrollo)

- 🔄 Refactorizar `asignacion_guardias_form.py` (794 líneas)
- 🔄 Refactorizar `calendario_guardias_form.py` (790 líneas)
- 🔄 Tests unitarios para widgets
- 🔄 Benchmarks de rendimiento del cache

### � v3.2+ - Planificado

- � Exportación a Excel mejorada
- � Exportación a PDF por profesor
- � Gráficos de estadísticas interactivos
- 📋 Preferencias de zonas por profesor
- 📋 Sistema de notificaciones
- 📋 API REST

---

## 🤝 Contribución

¡Las contribuciones son bienvenidas!

### Proceso

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -m 'feat: descripción'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

### Convenciones

**Commits**:
- `feat:` nueva funcionalidad
- `fix:` corrección de bug
- `docs:` cambios en documentación
- `refactor:` refactorización
- `test:` tests

**Código**:
- Python 3.11+ con type hints
- Seguir PEP 8 (usar `ruff`)
- Documentar con docstrings
- Tests para nueva funcionalidad

Ver [CONTRIBUIR.md](documentacion/CONTRIBUIR.md) para más detalles.

---

## 📄 Licencia

Este proyecto está bajo la **Licencia MIT**. Ver archivo [LICENSE](LICENSE) para más detalles.

---

## 👤 Autor

**Carlos Ferrero Bonet**

- GitHub: [@cferrerobonet](https://github.com/cferrerobonet)
- Email: cferrerobonet@gmail.com

---

## 🙏 Agradecimientos

- **PyQt6**: Framework UI multiplataforma
- **SQLAlchemy**: ORM robusto y flexible
- **Pydantic**: Validación de datos elegante
- **Alembic**: Migraciones de base de datos sencillas

---

## 📊 Estadísticas del Proyecto

### Métricas de Código (v3.0)
- **Líneas de código**: ~12,250 (-2,757 desde v2.9)
- **Reducción en formularios**: -40.3% promedio
- **Widgets reutilizables**: 12
- **Tests**: 124+ unitarios
- **Archivos Python**: 93 (80 + 13 nuevos widgets)
- **Cobertura de código**: ~75%

### Performance (v3.0)
- **Cache implementado**: 12 Use Cases
- **Reducción de queries**: 90-98%
- **Carga de formularios**: 50-70% más rápido
- **Navegación UI**: Experiencia fluida

### Desarrollo
- **Sprints completados**: 11 (Sprint 1.1 completo)
- **Versión actual**: 3.0.0
- **Última actualización**: 1 de noviembre de 2025

---

## �� Enlaces Útiles

- **Repositorio**: https://github.com/cferrerobonet/guardias_patio
- **Releases**: https://github.com/cferrerobonet/guardias_patio/releases
- **Release v2.8.0**: https://github.com/cferrerobonet/guardias_patio/releases/tag/v2.8.0
- **Issues**: https://github.com/cferrerobonet/guardias_patio/issues
- **Documentación**: [INDEX.md](documentacion/INDEX.md)

---

<div align="center">

**⭐ Si este proyecto te resulta útil, no olvides darle una estrella en GitHub ⭐**

Made with ❤️ by [Carlos Ferrero Bonet](https://github.com/cferrerobonet)

</div>
