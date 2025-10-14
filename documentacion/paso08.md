PASO 8: Validaciones y Manejo de Errores
Objetivo: Asegurar robustez de la aplicación con validaciones y mensajes de error claros.
Tareas:

Implementa validaciones en los servicios:

No permitir porcentajes de jornada > 100% o < 0%
No permitir fechas de fin de curso anteriores a inicio
No permitir eliminar profesores con guardias asignadas
No permitir eliminar zonas en uso


Implementa manejo de errores en el asignador:

Si no hay suficientes profesores para cubrir todas las zonas, mostrar error claro
Si la distribución es imposible (ej: solo profesores de mañana pero hay guardias de tarde), avisar


Añade logs del sistema:

Implementa logging en src/utils/logger.py
Registra todas las operaciones importantes
Registra errores con stack trace


Implementa ventanas de diálogo de confirmación:

Confirmar antes de eliminar datos
Confirmar antes de regenerar guardias (se perderán las existentes)



Criterio de verificación:

Intenta operaciones inválidas y verifica que se manejan correctamente
Los mensajes de error son claros y útiles
No hay crashes sin capturar
