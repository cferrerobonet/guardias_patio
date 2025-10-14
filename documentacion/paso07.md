PASO 7: Exportación e Informes
Objetivo: Permitir exportar los calendarios a formatos útiles (PDF, Excel, CSV).
Tareas:

Instala dependencias adicionales:

reportlab (para PDF)
openpyxl (para Excel)
pandas (para manipulación de datos)


Crea src/services/exportador.py:
Implementa exportar_a_excel():

Hoja 1: Calendario completo (columnas: Fecha, Día semana, Turno, Recreo, Zona, Profesor)
Hoja 2: Resumen por profesor (Profesor, Total guardias, Guardias mañana, Guardias tarde)
Hoja 3: Distribución por zona


Implementa exportar_a_pdf_profesor(profesor_id):

Genera PDF individual para cada profesor con su calendario personal
Incluye: nombre, total de guardias, listado de fechas con zona asignada


Implementa exportar_calendario_completo_pdf():

Genera PDF con calendario mensual visual
Una página por mes
Tabla con días del mes y asignaciones


Añade botones de exportación en la interfaz

Criterio de verificación:

Los archivos Excel se generan correctamente y se pueden abrir
Los PDF se generan con formato legible
Los datos exportados coinciden con los de la base de datos