PASO 1: Configuración del Proyecto y Base de Datos
Objetivo: Establecer la estructura básica del proyecto con gestión de base de datos usando SQLAlchemy y Alembic.
Tareas:

Crea la estructura de carpetas del proyecto:

   guardias-patio/
   ├── src/
   │   ├── models/
   │   ├── database/
   │   ├── services/
   │   └── ui/
   ├── alembic/
   ├── tests/
   └── requirements.txt

Configura el archivo requirements.txt con las dependencias:

SQLAlchemy
Alembic
PyQt6 o Tkinter (para la interfaz)
python-dateutil


Inicializa Alembic para migraciones de base de datos
Define el modelo de datos en src/models/models.py:

Tabla Profesores: id, nombre, apellidos, horas_contrato, porcentaje_jornada, turno (mañana/tarde/completo)
Tabla Zonas: id, nombre_zona, descripcion
Tabla Configuracion: id, fecha_inicio_curso, fecha_fin_curso, hora_recreo1_manana, hora_recreo2_manana, hora_recreo1_tarde, hora_recreo2_tarde
Tabla Guardias: id, profesor_id, fecha, turno, recreo (1 o 2), zona_id


Crea la primera migración con Alembic y genera la base de datos

Criterio de verificación:

La base de datos se crea correctamente
Puedes insertar manualmente un profesor y una zona de prueba
Las migraciones funcionan sin errores