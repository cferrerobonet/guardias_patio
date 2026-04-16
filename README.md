# Guardias de Patio

![Version](https://img.shields.io/badge/Version-3.2.1-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.7.0-orange.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Aplicación de escritorio** para la gestión de guardias de patio en centros educativos. Asignación automática con equidad perfecta (IE=100%) usando Google OR-Tools CP-SAT, calendario interactivo, gestión de ausencias/sustituciones, y exportación PDF/iCal.

---

## Características Principales

- **Algoritmo CP-SAT**: Equidad perfecta, minimización de consecutividad, preferencia de zona
- **Calendario interactivo**: Vista mensual con filtros por profesor, zona y turno
- **Gestión de ausencias**: Sistema de sustituciones con búsqueda automática
- **Exportación múltiple**: PDF corporativo, iCalendar (.ics), JSON
- **API REST**: Endpoints FastAPI para integraciones externas
- **Dashboard de equidad**: Visualización con gráficos en tiempo real
- **Multi-usuario**: BD SQLite aislada por usuario con sync SFTP
- **Observabilidad**: Métricas Prometheus, logging estructurado (structlog)

---

## Quick Start

```bash
# Crear entorno virtual (Python 3.11+ requerido)
python3.11 -m venv .venv
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python src/main.py
```

### Primer Uso

1. **Configurar Curso** → Definir fechas, recreos y festivos
2. **Crear Zonas** → Establecer áreas de vigilancia
3. **Alta de Profesores** → Añadir profesorado con restricciones
4. **Generar Guardias** → Ejecutar algoritmo de asignación
5. **Visualizar** → Ver calendario y exportar PDFs

---

## Stack Tecnológico

| Categoría | Tecnología |
|-----------|------------|
| GUI | PyQt6 6.7.0 |
| ORM | SQLAlchemy 2.0 + Alembic |
| BD | SQLite (per-user) |
| API | FastAPI + Uvicorn |
| Optimización | Google OR-Tools (CP-SAT) |
| Validación | Pydantic 2.x |
| Testing | pytest + pytest-qt (990 tests) |
| Logging | structlog + prometheus_client |
| Linting | Ruff + mypy |

**Compatibilidad**: macOS 11+, Windows 10+, Linux (Ubuntu 20.04+)

---

## Arquitectura

Clean Architecture con separación en capas:

```
src/
├── domain/          Entidades, value objects, interfaces de repositorio
├── application/     Use cases, DTOs, factories DI
├── infrastructure/  Repositorios SQLAlchemy, mappers, modelos BD
├── presentation/    GUI PyQt6 (forms, widgets, dialogs, themes)
├── services/        Algoritmos de asignación, exportadores, email, iCal
├── api/             REST API FastAPI
├── core/            Excepciones, logging, observabilidad
├── sync/            Sincronización SFTP, bloqueo de sesión
├── config/          Settings (Pydantic BaseSettings)
├── database/        Gestión de conexiones y migraciones
└── utils/           Cache, constantes, helpers
```

---

## Compilación

```bash
# macOS
make app && make dmg

# Windows
powershell scripts/build_windows.ps1
```

---

## Documentación

| Documento | Descripción |
|-----------|-------------|
| [docs/AUDITORIA_INTEGRAL_2026.md](docs/AUDITORIA_INTEGRAL_2026.md) | Auditoría completa: seguridad, performance, arquitectura, roadmap |
| [CHANGELOG.md](CHANGELOG.md) | Historial de versiones |
| [tests/README.md](tests/README.md) | Guía de testing y buenas prácticas |
| [scripts/README.md](scripts/README.md) | Documentación de scripts |

---

## Contribución

1. Fork el repositorio
2. Crea rama: `git checkout -b feature/mi-feature`
3. Tests: `pytest` (asegura que todo pasa)
4. Commit: `git commit -m "feat: descripción"` (Conventional Commits)
5. Pull Request con descripción detallada

**Convenciones**: PEP 8, type hints, tests obligatorios para features nuevas.

---

## Licencia

MIT License — Copyright (c) 2024-2026 Carlos Ferrero Bonet. Ver [LICENSE](LICENSE).

**Carlos Ferrero Bonet** — [@cferrerobonet](https://github.com/cferrerobonet)
