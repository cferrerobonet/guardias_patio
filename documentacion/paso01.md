# PASO 1: Configuración del Proyecto y Base de Datos

## 🎯 Objetivo
Establecer la estructura inicial del proyecto y la base de datos usando SQLAlchemy y Alembic.

## 🧰 Alcance
En este paso solo se prepara la infraestructura: carpetas, dependencias, modelos base y primera migración.

## 📁 Estructura de Carpetas Propuesta
```text
guardias-patio/
├── src/
│   ├── models/
│   ├── database/
│   ├── services/
│   └── ui/
├── alembic/
├── tests/
└── requirements.txt
```

## 📦 Dependencias Iniciales (requirements.txt)
Obligatorias para este paso:
```
SQLAlchemy
alembic
python-dateutil
```
Pendientes de fases posteriores (no instalar aún si no se necesitan):
```
PyQt6       # Interfaz gráfica
reportlab   # Exportación PDF
openpyxl    # Exportación Excel
pandas      # Transformaciones y estadísticas
matplotlib  # Gráficos
```

## 🗄️ Modelo de Datos (Versión Base)
| Tabla | Campos |
|-------|--------|
| Profesores | id, nombre, apellidos, horas_contrato, porcentaje_jornada, turno (mañana/tarde/completo) |
| Zonas | id, nombre_zona, descripcion |
| Configuracion | id, fecha_inicio_curso, fecha_fin_curso, hora_recreo1_manana, hora_recreo2_manana, hora_recreo1_tarde, hora_recreo2_tarde |
| Guardias | id, profesor_id, fecha, turno, recreo (1/2), zona_id |

## 🛠️ Pasos Detallados
1. Crear entorno virtual y archivo `requirements.txt`.
2. Instalar dependencias mínimas.
3. Crear estructura de carpetas.
4. Definir `Base` de SQLAlchemy y los modelos en `src/models/models.py`.
5. Inicializar Alembic: `alembic init alembic`.
6. Configurar cadena de conexión (SQLite inicial) en `alembic.ini` y/o `env.py`.
7. Generar primera revisión: `alembic revision --autogenerate -m "crear tablas base"`.
8. Aplicar migraciones: `alembic upgrade head`.
9. Probar inserción manual (script o shell) de un profesor y una zona.

## ✅ Criterios de Verificación
- [ ] La base de datos se genera sin errores
- [ ] Existen las tablas definidas
- [ ] Inserción y consulta de un profesor funciona
- [ ] Inserción y consulta de una zona funciona
- [ ] Migración reproducible en un entorno limpio

## 🧪 Comprobación Rápida (Ejemplo SQLAlchemy Shell)
```python
from src.database.session import SessionLocal
from src.models.models import Profesor, Zona
db = SessionLocal()
db.add(Profesor(nombre="Ana", apellidos="García", horas_contrato=25, porcentaje_jornada=100, turno="mañana"))
db.add(Zona(nombre_zona="Patio Norte", descripcion="Zona principal"))
db.commit()
print(db.query(Profesor).all())
```

## 📌 Notas
- Empezar con SQLite facilita el arranque; más adelante se puede migrar a PostgreSQL.
- Añade índices después cuando se identifiquen consultas frecuentes.
- Mantén los modelos simples; relaciones adicionales vendrán en pasos posteriores.

---
Continúa con el PASO 2 para implementar los servicios CRUD básicos.