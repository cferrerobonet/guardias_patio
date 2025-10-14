PASO 3: Lógica de Cálculo de Guardias
Objetivo: Desarrollar el algoritmo que calcula el número de guardias por profesor según su contrato.
Tareas:

Crea src/services/calculo_guardias.py:
Implementa la función calcular_guardias_por_profesor():

Calcula los días lectivos totales entre fecha inicio y fin (excluyendo sábados/domingos)
Calcula el número total de recreos a cubrir (días_lectivos × 2 recreos × número de turnos activos)
Calcula el número total de "slots" de guardia necesarios (recreos × número de zonas)
Distribuye los slots entre profesores según su porcentaje de jornada


Implementa la función calcular_guardias_por_turno(profesor):

Si turno = "mañana": solo recreos de mañana
Si turno = "tarde": solo recreos de tarde
Si turno = "completo": ambos turnos proporcionalmente


Implementa la función calcular_distribucion_base():

Devuelve un diccionario: {profesor_id: número_guardias_a_asignar}



Criterio de verificación:

Con 180 días lectivos, 4 zonas, 2 recreos/día y 10 profesores:

Un profesor a jornada completa (100%) debe tener ~144 guardias
Un profesor al 50% debe tener ~72 guardias


Los números deben sumar exactamente el total de slots disponibles