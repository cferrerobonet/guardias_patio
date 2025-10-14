# Guardias de Patio

Aplicación de escritorio para planificar, asignar, visualizar y exportar las guardias de patio de un centro educativo de forma equitativa y transparente.

## 🚀 Objetivo
Automatizar el cálculo y la asignación de guardias (recreos) entre el profesorado según:
- Porcentaje de jornada
- Turno (mañana / tarde / completo)
- Zonas del patio
- Periodo lectivo del curso
- Preferencias y exclusiones (futuro)

## 🏗️ Arquitectura General
Estructura en capas separando datos, servicios, lógica de negocio, interfaz y utilidades.

```
src/
 ├── models/                # Modelos SQLAlchemy
 ├── database/              # Gestión de conexión y migraciones
 ├── services/              # Lógica de negocio (CRUD, cálculo, asignación, exportación)
 ├── ui/                    # Interfaz gráfica (PyQt6 recomendado)
 ├── utils/                 # Logging, helpers
 └── tests/                 # Pruebas unitarias e integración
alembic/                    # Migraciones de base de datos
requirements.txt            # Dependencias
```

## 🗄️ Modelo de Datos (Base inicial)
Tablas principales:
- Profesores: id, nombre, apellidos, horas_contrato, porcentaje_jornada, turno
- Zonas: id, nombre_zona, descripcion
- Configuracion: fechas de curso y horarios de recreos
- Guardias: asignaciones concretas (profesor, fecha, turno, recreo, zona)

Futuro:
- Exclusiones (ausencias temporales)
- Preferencias (afinidad o evitación de zonas)
- Histórico de calendarios

## 🔢 Algoritmos Clave
1. Cálculo de cargas: determina cuántas guardias debe asumir cada profesor proporcionalmente a su porcentaje de jornada y turno.
2. Asignación: distribuye slots (fecha × recreo × zona × turno) minimizando desequilibrios y evitando conflictos.
3. Reglas de asignación:
   - Prioriza profesor con menor número acumulado de guardias
   - Respeta turno
   - Evita dos guardias el mismo día para la misma persona (si es posible)
   - Evita repetir zona consecutiva (si es posible)

## 🖥️ Interfaz de Usuario (Prevista)
Módulos previstos:
- Gestión de profesores
- Gestión de zonas
- Configuración de curso y horarios de recreos
- Generación de calendario
- Vista calendario (filtros por profesor / zona / turno / mes)
- Vista detalle por profesor y por zona
- Regeneración controlada
- Exportación (Excel / PDF)

## 📤 Exportación (Roadmap)
- Excel (openpyxl, pandas): calendario completo + resumen por profesor + distribución por zona
- PDF (reportlab): calendario completo y PDFs individuales por profesor

## ✅ Validaciones & Robustez
- Porcentajes de jornada 0–100
- Fechas válidas (fin > inicio)
- No eliminar entidades en uso (profesores con guardias, zonas asignadas)
- Detección de imposibilidad de cubrir turnos
- Logging centralizado (`utils/logger.py`)

## 🧪 Testing
Pruebas previstas:
- Unitarias: cálculo de guardias, asignador, servicios CRUD
- Integración: flujo completo (crear datos → configurar → generar → validar)
- Futuro: pruebas sobre ajustes manuales y preferencias

## 🧱 Migraciones
Se gestionan con Alembic. Flujo típico:
```
alembic revision -m "crear tablas base"
alembic upgrade head
```

## 📦 Empaquetado (Futuro)
Generación de ejecutable standalone con PyInstaller + base de datos SQLite inicial.

## 🔮 Funcionalidades Avanzadas (Roadmap)
- Exclusiones (vacaciones / bajas)
- Preferencias de zonas
- Ajustes manuales e intercambios
- Histórico multi-curso
- Dashboard de estadísticas (matplotlib)
- Multiidioma

## 📁 requirements.txt (Inicial sugerido)
```
SQLAlchemy
alembic
PyQt6
python-dateutil
reportlab        # (fase exportación PDF)
openpyxl         # (fase exportación Excel)
pandas           # (fase exportación / estadísticas)
matplotlib       # (fase estadísticas)
```
(Instala solo lo necesario según la fase.)

## ▶️ Ejecución (Esquema preliminar)
```
python -m venv .venv
source .venv/bin/activate  # macOS / Linux
pip install -r requirements.txt
alembic upgrade head
python src/ui/main_window.py
```

## 🤝 Convenciones
Commits (Conventional Commits):
- feat:, fix:, docs:, refactor:, test:, chore:
Ramas: `feat/`, `fix/`, `chore/`, `refactor/`

## 📂 Estructura de Servicios (Ejemplo)
```
services/
 ├── profesor_service.py      # CRUD profesores
 ├── zona_service.py          # CRUD zonas
 ├── configuracion_service.py # Configuración curso
 ├── calculo_guardias.py      # Cálculo de cargas
 ├── asignador_guardias.py    # Generación de calendario
 ├── exportador.py            # Exportaciones (roadmap)
```

## 🧠 Diseño y Patrones
- Repository / DAO para acceso a datos
- Strategy para variantes de asignación futura
- Separación estricta UI ↔ lógica

## 🛡️ Calidad
- Docstrings en funciones públicas
- Tipado opcional (PEP 484) recomendado
- Linter: `ruff` o `flake8` (a incorporar)

## 🗓️ Ejemplo de Cálculo (Escenario base)
Con 180 días lectivos, 4 zonas, 2 recreos/día, turnos completos:
- Slots totales = 180 × 2 × 4 = 1440
- Profesor 100% ≈ 144 guardias si hay 10 profesores equivalentes a jornada completa
- Profesor 50% ≈ 72 guardias

## 🔍 Próximos Pasos Inmediatos
1. Crear `requirements.txt` mínimo e instalar dependencias base
2. Definir modelos SQLAlchemy
3. Inicializar Alembic y primera migración
4. Implementar servicios CRUD
5. Desarrollar algoritmo de cálculo y asignación
6. Conectar con interfaz (PyQt6)

## 📄 Licencia
(Define la licencia: MIT / GPL / privativa según corresponda.)

---
Si necesitas guías más detalladas de cada fase, consulta la carpeta `documentacion/` o solicita un desglose adicional.
