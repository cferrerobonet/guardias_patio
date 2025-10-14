PASO 6: Interfaz de Usuario - Visualización de Guardias
Objetivo: Mostrar el calendario de guardias generado de forma clara y permitir exportación.
Tareas:

Crea src/ui/calendario_guardias.py:

Vista de calendario mensual o tabla
Filtros: por profesor, por zona, por turno, por mes
Colores diferentes para turnos de mañana/tarde


Implementa src/ui/vista_profesor.py:

Muestra todas las guardias asignadas a un profesor específico
Lista cronológica con fecha, hora, recreo y zona


Implementa src/ui/vista_zona.py:

Muestra qué profesores vigilan cada zona cada día


Crea botón "Generar Guardias" en la ventana principal:

Ejecuta el algoritmo de asignación
Muestra progreso con barra de carga
Al finalizar, abre automáticamente la vista del calendario


Añade funcionalidad de regeneración:

Botón "Borrar y Regenerar" que elimina guardias existentes y genera nuevas



Criterio de verificación:

El calendario se muestra correctamente
Los filtros funcionan
Puedes ver las guardias desde diferentes perspectivas (por profesor, por zona, por fecha)