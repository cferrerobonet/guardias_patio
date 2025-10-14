PASO 9: Funcionalidades Avanzadas
Objetivo: Añadir características que mejoren la usabilidad.
Tareas:

Implementa sistema de exclusiones:

Tabla Exclusiones: profesor_id, fecha_inicio, fecha_fin, motivo
Los profesores con exclusiones no reciben guardias en ese período


Implementa ajustes manuales:

Permitir cambiar una guardia específica de profesor manualmente
Intercambiar guardias entre dos profesores


Implementa preferencias:

Tabla Preferencias: profesor_id, zona_id, preferencia (positiva/negativa)
El algoritmo intenta respetar preferencias si es posible


Implementa histórico:

Permitir guardar múltiples calendarios (por curso escolar)
Selector de curso para ver calendarios anteriores


Implementa estadísticas:

Dashboard con métricas: guardias por profesor, por zona, por mes
Gráficos básicos (matplotlib)



Criterio de verificación:

Las exclusiones funcionan correctamente
Puedes hacer ajustes manuales sin romper el sistema
Las estadísticas reflejan la realidad de las asignaciones


