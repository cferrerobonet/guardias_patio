PASO 5: Interfaz de Usuario - Gestión de Datos
Objetivo: Crear la interfaz gráfica para gestionar profesores, zonas y configuración.
Tareas:

Elige framework (recomendado: PyQt6) y crea src/ui/main_window.py
Implementa la ventana principal con menú:

Profesores
Zonas
Configuración
Guardias
Generar Calendario


Crea src/ui/profesor_dialog.py:

Formulario para añadir/editar profesores
Campos: nombre, apellidos, horas de contrato, % jornada, turno (dropdown)
Tabla para listar profesores existentes
Botones: Nuevo, Editar, Eliminar


Crea src/ui/zona_dialog.py:

Formulario para añadir/editar zonas
Tabla de zonas existentes


Crea src/ui/configuracion_dialog.py:

Selectores de fecha para inicio/fin de curso
Campos de hora para los recreos de mañana y tarde



Criterio de verificación:

Puedes añadir, editar y eliminar profesores desde la interfaz
Los datos se guardan correctamente en la base de datos
La interfaz valida los datos (no permite % jornada > 100, fechas inválidas, etc.)