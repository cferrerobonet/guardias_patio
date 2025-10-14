# Gestión de Profesores y Turnos

## 🎯 Objetivo
Permitir la introducción de profesores desde la interfaz gráfica, calculando automáticamente el porcentaje de jornada y gestionando correctamente los turnos (mañana, tarde, mixto).

## 🧮 Cálculo del porcentaje de jornada
- El porcentaje de jornada se calcula automáticamente: **porcentaje = horas_contrato / 30**
- 30 horas semanales equivalen al 100% de la jornada.
- El usuario solo introduce las horas de contrato.

## 🕑 Turnos disponibles
- **mañana**: Todas las horas en turno de mañana.
- **tarde**: Todas las horas en turno de tarde.
- **mixto**: El usuario debe indicar cuántas horas son de mañana y cuántas de tarde. La suma debe coincidir con las horas de contrato.

## ⚖️ Reparto de guardias en turno mixto
- Si el turno es mixto, las guardias asignadas se repartirán de forma proporcional al número de horas trabajadas en cada turno.
- Ejemplo: Si un profesor tiene 18h de mañana y 12h de tarde (total 30h), el 60% de sus guardias serán de mañana y el 40% de tarde.

## 🖥️ Interfaz gráfica
- El formulario de alta de profesor solicita:
  - Nombre
  - Apellidos
  - Horas de contrato (total)
  - Turno (mañana/tarde/mixto)
  - **Si es mixto**: horas de mañana y horas de tarde (campos visibles solo al seleccionar "mixto")
- El porcentaje de jornada se calcula automáticamente y se muestra en el mensaje de confirmación.
- Si la suma de horas de mañana y tarde no coincide con el total, se muestra una advertencia.
- Los campos adicionales de distribución horaria se ocultan automáticamente si el turno no es mixto.

## ✅ Criterios de verificación
- [ ] El usuario no introduce el porcentaje de jornada manualmente.
- [ ] El reparto de guardias en turno mixto es proporcional a las horas de cada turno.
- [ ] El formulario valida la suma de horas en turno mixto.
- [ ] Los campos de horas mañana/tarde solo son visibles y requeridos cuando el turno es mixto.## 🏗️ Gestión de Zonas

### Objetivo
Permitir la introducción de zonas de patio desde la interfaz gráfica.

### Modelo de datos
- **nombre_zona**: Nombre identificativo de la zona (obligatorio)
- **descripcion**: Descripción opcional de la zona

### Interfaz gráfica
- Formulario simple con dos campos:
  - Nombre de la zona (obligatorio)
  - Descripción (opcional)
- Validación: el nombre de la zona no puede estar vacío
- Al guardar, se muestra confirmación con el nombre de la zona creada

## 📑 Estructura de la interfaz principal

La aplicación utiliza un sistema de **pestañas (QTabWidget)** para organizar las diferentes funcionalidades:

### Pestañas disponibles:
1. **Profesores**: Formulario de alta de profesores con gestión de turnos
2. **Zonas**: Formulario de alta de zonas del patio

### Ventana principal
- Clase: `MainWindow`
- Contiene el widget de pestañas que agrupa los formularios
- Permite navegación sencilla entre las diferentes secciones de gestión

## 📦 Dependencias de interfaz gráfica

La aplicación utiliza **PyQt6 versión 6.7.0** (versión estable para macOS):
- PyQt6==6.7.0
- PyQt6-Qt6 (instalado automáticamente)
- PyQt6-sip (instalado automáticamente)

### Nota sobre versiones
- La versión 6.7.0 ha demostrado mejor compatibilidad con macOS que versiones más recientes
- Si encuentras problemas con el plugin "cocoa", reinstala con: `pip install PyQt6==6.7.0`

---
Continúa con el PASO 3 para la lógica de cálculo de guardias y configuración de curso.
# PASO 2: Capa de Servicios – CRUD Básico

## 🎯 Objetivo
Implementar servicios para gestionar profesores, zonas y configuración del curso (crear, leer, actualizar, eliminar).

## 🧩 Componentes a Crear
```text
src/
 ├── database/
 │   └── db_manager.py
 └── services/
	 ├── profesor_service.py
	 ├── zona_service.py
	 └── configuracion_service.py
```

## ⚙️ `db_manager.py`
Responsabilidades:
- Crear motor (`create_engine`)
- Proveer `SessionLocal`
- Context manager: `with get_session() as session:`

## 🧪 Servicios
### Profesor
- `crear_profesor(nombre, apellidos, horas_contrato, porcentaje_jornada, turno)`
- `listar_profesores()`
- `actualizar_profesor(id, datos_dict)`
- `eliminar_profesor(id)` (validar futuras dependencias)
- `obtener_profesor_por_id(id)`

### Zona
- `crear_zona(nombre, descripcion)`
- `listar_zonas()`
- `actualizar_zona(id, datos_dict)`
- `eliminar_zona(id)`

### Configuración
- `guardar_configuracion_curso(fecha_inicio, fecha_fin, horarios_recreos)`
- `obtener_configuracion_actual()` (último registro o uno activo)

## 🧪 Script de Prueba Rápida (Ejemplo)
```python
from datetime import date, time
from src.services import profesor_service, zona_service, configuracion_service

profesores_demo = [
	("Ana", "García", 25, 100, "mañana"),
	("Luis", "Pérez", 20, 80, "tarde"),
	("Marta", "López", 15, 60, "completo"),
	("Juan", "Ruiz", 12, 50, "mañana"),
	("Sara", "Díaz", 10, 40, "tarde"),
]
for p in profesores_demo:
	profesor_service.crear_profesor(*p)

for nombre in ["Patio Norte", "Patio Sur", "Pista", "Biblioteca"]:
	zona_service.crear_zona(nombre, f"Zona {nombre}")

configuracion_service.guardar_configuracion_curso(
	date(2025, 9, 10), date(2026, 6, 20),
	dict(
		hora_recreo1_manana=time(10,30),
		hora_recreo2_manana=time(12,0),
		hora_recreo1_tarde=time(16,30),
		hora_recreo2_tarde=time(18,0)
	)
)

print(profesor_service.listar_profesores())
print(zona_service.listar_zonas())
print(configuracion_service.obtener_configuracion_actual())
```

## ✅ Criterios de Verificación
- [ ] Inserta 5 profesores con distintos turnos/porcentajes
- [ ] Inserta 4 zonas
- [ ] Guarda configuración de curso
- [ ] Listar devuelve los datos correctos
- [ ] Actualizar modifica campos esperados

## 🔍 Notas
- Validaciones avanzadas se añaden en pasos posteriores.
- Mantener transacciones cortas.

---
Siguiente: PASO 3 (cálculo de cargas de guardias).