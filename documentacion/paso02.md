PASO 2: Capa de Servicios - CRUD Básico
Objetivo: Implementar las operaciones básicas de creación, lectura, actualización y eliminación para profesores y zonas.
Tareas:

Crea src/database/db_manager.py con:

Clase para gestionar la conexión a la base de datos
Context manager para sesiones


Implementa src/services/profesor_service.py:

crear_profesor(nombre, apellidos, horas_contrato, porcentaje_jornada, turno)
listar_profesores()
actualizar_profesor(id, datos)
eliminar_profesor(id)
obtener_profesor_por_id(id)


Implementa src/services/zona_service.py:

crear_zona(nombre, descripcion)
listar_zonas()
actualizar_zona(id, datos)
eliminar_zona(id)


Implementa src/services/configuracion_service.py:

guardar_configuracion_curso(fecha_inicio, fecha_fin, horarios_recreos)
obtener_configuracion_actual()



Criterio de verificación:

Crea un script de prueba que inserte 5 profesores con diferentes turnos y porcentajes
Inserta 4 zonas del patio
Configura las fechas del curso
Verifica que puedes listar y modificar los datos correctamente