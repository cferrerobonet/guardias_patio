# Guardias de Patio

![Version](https://img.shields.io/badge/Version-2.9.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-orange.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)
![Pydantic](https://img.shields.io/badge/Pydantic-2.0-purple.svg)
![Arquitectura](https://img.shields.io/badge/Arquitectura-Clean-brightgreen.svg)
![Status](https://img.shields.io/badge/Status-Stable-success.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Aplicación de escritorio profesional** para la gestión integral de guardias de patio en centros educativos. Asignación automática equitativa, gestión de ausencias y sustituciones, exportación de calendarios, y sistema completo de observabilidad.

> 🎉 **v2.9.0 Released** - Fix crítico de compilación: app ahora funciona perfectamente compilada con DMG instalable  
> 📚 [Ver Changelog v2.9](documentacion/CHANGELOG_v2.9.md) | [Changelog v2.8](documentacion/CHANGELOG_v2.8.md)

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
./build_simple.sh
```

**¿Problemas al compilar?** → Lee [`COMPILACION_RAPIDA.md`](./COMPILACION_RAPIDA.md)

**Documentación completa de compilación:**
- [`documentacion/SOLUCION_COMPILACION.md`](./documentacion/SOLUCION_COMPILACION.md) - Solución de todos los problemas conocidos
- [`documentacion/COMPILACION_Y_DISTRIBUCION.md`](./documentacion/COMPILACION_Y_DISTRIBUCION.md) - Guía completa

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

### Documentación Principal

- **[README de Documentación](documentacion/README.md)** - Índice completo de toda la documentación
- **[CHANGELOG_v2.8.md](documentacion/CHANGELOG_v2.8.md)** - Cambios de la versión 2.8.0
- **[Requisitos del Sistema](documentacion/REQUISITOS_SISTEMA.md)** - Requisitos mínimos y recomendados

### Guías Específicas

- **[Configuración SMTP](documentacion/CONFIGURACION_EMAIL.md)** - Configurar recuperación de contraseña por email
- **[Sincronización SFTP](documentacion/sftp/)** - Documentación completa de sincronización cloud
- **[Build y Distribución](documentacion/build/)** - Guías para crear ejecutables

### Documentación Técnica

- **[Patrones de Arquitectura](documentacion/ARCHITECTURE_PATTERNS.md)** - Patrones utilizados
- **[Schemas Pydantic](documentacion/SCHEMAS_USAGE_GUIDE.md)** - Guía de validación de datos
- **[Historia de Sprints](documentacion/HISTORIA_SPRINTS.md)** - Evolución del proyecto

---

## 🗺️ Roadmap

### ✅ Características Principales (v2.8+)

- ✅ **Sistema Multi-usuario**: Gestión de múltiples usuarios con recuperación de contraseña por email
- ✅ **Sincronización Cloud**: Soporte SFTP para sincronización entre dispositivos
- ✅ **CRUD completo**: Profesores, Zonas, Guardias, Configuración
- ✅ **Generación automática de guardias**: Asignación equitativa según % jornada
- ✅ **Vista de calendario interactiva**: Visualización mensual con filtros
- ✅ **Gestión de ausencias y sustituciones**: Sistema completo
- ✅ **Panel de estadísticas**: Métricas en tiempo real
- ✅ **Importar/Exportar JSON**: Portabilidad completa
- ✅ **Dashboard de observabilidad**: Métricas, health checks y logs
- ✅ **Logo corporativo**: Branding consistente
- ✅ **Validaciones robustas**: Mensajes claros y contextuales

### 🔄 En Desarrollo (Sprint 9)

- 🔄 Exportación a Excel
- 🔄 Exportación a PDF por profesor
- 🔄 Gráficos de estadísticas
- 🔄 Filtros avanzados

### 🔜 Planificado (Sprint 10+)

- 📋 Preferencias de zonas por profesor
- 📋 Sistema de notificaciones
- 📋 Historial de cambios
- 📋 Reportes personalizados
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

- **Líneas de código**: ~15,000+
- **Tests**: 124+ unitarios
- **Archivos Python**: 80+
- **Sprints completados**: 8
- **Versión actual**: 2.9.0

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
