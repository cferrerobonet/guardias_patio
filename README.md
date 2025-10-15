# Guardias de Patio

![MIT License](https://img.shields.io/badge/License-MIT-green.svg)

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

## 🖥️ Interfaz de Usuario
Módulos implementados:
- ✅ **Gestión de profesores**: Alta, visualización y eliminación
- ✅ **Gestión de zonas**: Creación y gestión de zonas de vigilancia
- ✅ **Configuración de curso**: Fechas, horarios de recreos, festivos automáticos, multiplicadores
- ✅ **Generación de calendario**: Cálculo automático de guardias con distribución equitativa
- ✅ **Vista de Calendario**: Visualización interactiva de guardias asignadas con filtros por profesor, zona y turno
- ✅ **Importar/Exportar datos**: Portabilidad completa de datos entre equipos (ver [documentación](documentacion/importar_exportar.md))

Módulos previstos:
- Vista detalle por profesor y por zona
- Regeneración controlada
- Exportación avanzada (Excel / PDF)

## 📤 Exportación e Importación

### ✅ Importar/Exportar Datos (Implementado)
La aplicación permite exportar e importar **todos los datos** (profesores, zonas, configuración, guardias) en formato JSON para:
- **Portabilidad**: Transferir datos entre diferentes equipos
- **Respaldo**: Hacer copias de seguridad completas
- **Migración**: Facilitar actualizaciones de la aplicación

**Características**:
- Exportación completa a archivo JSON con un clic
- Importación con opción de limpieza de datos existentes
- Preservación de todas las relaciones (profesores ↔ guardias, zonas ↔ guardias)
- Formato legible y editable manualmente si es necesario

**Documentación completa**: Ver [documentacion/importar_exportar.md](documentacion/importar_exportar.md)

### 🔜 Exportación Avanzada (Roadmap)
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

## 📦 Instalación

### Requisitos Previos
- Python 3.9 o superior
- pip
- macOS, Linux o Windows

### Pasos de Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone https://github.com/cferrerobonet/guardias_patio.git
   cd guardias_patio
   ```

2. **Crear y activar entorno virtual**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

   **⚠️ Nota para macOS**: Si encuentras errores con PyQt6, ejecuta:
   ```bash
   ./fix_pyqt6.sh
   ```
   O consulta `documentacion/solucion_pyqt6.md` para más detalles.

4. **Configurar la base de datos**:
   ```bash
   alembic upgrade head
   ```

5. **Ejecutar la aplicación**:
   ```bash
   ./run_app.sh  # En macOS/Linux
   python src/main.py  # En Windows
   ```

### Solución de Problemas
- **Error de importación de PyQt6**: Ver `documentacion/solucion_pyqt6.md`
- **Error de base de datos**: Asegúrate de ejecutar `alembic upgrade head`
- **Otros errores**: Revisa los logs y reporta issues en GitHub

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

## 📂 Estructura de Servicios
```
services/
 ├── calculador_guardias.py   # Cálculo de cargas y generación de calendario
 ├── exportador.py            # Exportación e importación de datos JSON
```

Servicios previstos:
```
 ├── profesor_service.py      # CRUD profesores (futuro)
 ├── zona_service.py          # CRUD zonas (futuro)
 ├── configuracion_service.py # Configuración curso (futuro)
 ├── exportador_excel.py      # Exportaciones Excel (roadmap)
 ├── exportador_pdf.py        # Exportaciones PDF (roadmap)
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

## � Documentación

### Guías de Usuario
- [Vista de Calendario](documentacion/vista_calendario.md) - Visualización interactiva de guardias asignadas
- [Tutorial de Importación/Exportación](documentacion/TUTORIAL_IMPORTAR_EXPORTAR.md) - Guía paso a paso para transferir datos
- [Importar/Exportar Datos](documentacion/importar_exportar.md) - Documentación técnica de portabilidad

### Documentación Técnica
- [Validaciones de Asignación](documentacion/validaciones_asignacion.md) - **[NUEVO]** Guía completa de todas las validaciones del sistema
- [Condiciones Generales de Asignación](documentacion/condiciones_generales_asignacion.md) - Reglas globales de asignación
- [Condiciones Particulares por Profesor](documentacion/condiciones_particulares_profesores.md) - Restricciones individuales

### Guías de Desarrollo
- Pasos de implementación: [paso01](documentacion/paso01.md) a [paso10](documentacion/paso10.md)
- [Solución PyQt6 en macOS](documentacion/solucion_pyqt6.md) - Resolución de problemas de instalación

### Notas de Versión
- [Versión 1.2.0](documentacion/RESUMEN_VALIDACION_NO_SIMULTANEIDAD.md) - Validación de no simultaneidad de zonas
- [Versión 1.1.0](documentacion/NOTAS_VERSION_1_1_0.md) - Sistema de importación/exportación
- [Resumen Importación/Exportación](documentacion/RESUMEN_IMPORTACION_EXPORTACION.md)

## �📄 Licencia
(Define la licencia: MIT / GPL / privativa según corresponda.)

---
Si necesitas guías más detalladas de cada fase, consulta la carpeta `documentacion/` o solicita un desglose adicional.
