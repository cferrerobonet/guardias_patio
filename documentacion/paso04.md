PASO 4: Algoritmo de Asignación de Guardias
Objetivo: Crear el sistema que asigna guardias específicas (fecha, recreo, zona) a cada profesor.
Tareas:

Crea src/services/asignador_guardias.py
Implementa la función generar_calendario_guardias():

Obtiene la lista de días lectivos del curso
Para cada día:

Para cada recreo (1 y 2):

Para cada turno (mañana/tarde):

Asigna profesores a cada zona según su disponibilidad








Implementa estrategia de distribución equitativa:

Mantén un contador de guardias asignadas por profesor
Prioriza asignar a quien tenga menos guardias acumuladas
Respeta el turno del profesor
Evita asignar la misma zona consecutivamente al mismo profesor (si es posible)
Evita asignar dos guardias el mismo día al mismo profesor (si es posible)


Implementa validar_asignacion(guardia, profesor):

Verifica que el profesor trabaje en ese turno
Verifica que no tenga ya una guardia ese día en ese recreo
Verifica que no supere su cuota de guardias


Implementa guardar_guardias_en_bd(calendario):

Guarda todas las guardias generadas en la tabla Guardias



Criterio de verificación:

Genera el calendario completo
Verifica que cada profesor tenga aproximadamente el número de guardias calculado (±2 de diferencia)
Verifica que todos los slots de guardias estén cubiertos
Verifica que no haya conflictos (mismo profesor, mismo día, mismo recreo)