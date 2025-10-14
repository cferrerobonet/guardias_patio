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