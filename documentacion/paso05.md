# PASO 5: Interfaz de Usuario – Gestión de Datos

## 🎯 Objetivo
Proveer pantallas CRUD para profesores, zonas y configuración del curso usando PyQt6 (recomendado).

## 📄 Archivos Principales
```
src/ui/
 ├── main_window.py
 ├── profesor_dialog.py
 ├── zona_dialog.py
 └── configuracion_dialog.py
```

## 🪟 Ventana Principal (`main_window.py`)
Menú / navegación:
- Profesores
- Zonas
- Configuración
- Guardias (vista – pasos posteriores)
- Generar Calendario

## 👤 Diálogo de Profesores
Campos:
- Nombre
- Apellidos
- Horas de contrato (horas_contrato)
- % Jornada (porcentaje_jornada)
- Turno (Combo: mañana / tarde / completo)

Funciones:
- Listado en tabla (sortable)
- Botones: Nuevo / Editar / Eliminar
- Validaciones inline

## 📍 Diálogo de Zonas
Campos:
- Nombre de zona
- Descripción

Funciones:
- Tabla de zonas
- CRUD básico

## 🗓️ Diálogo de Configuración
Elementos:
- Fecha inicio / fin curso (DateEdit)
- Horarios recreos (TimeEdit) mañana y tarde (dos cada uno si aplica)
- Botón Guardar / Cancelar

## ✅ Validaciones UI
- % jornada: 0 < valor ≤ 100
- Fechas: fin > inicio
- Turno obligatorio
- Nombres no vacíos

## 🧪 Criterios de Verificación
- [ ] Alta / edición / eliminación de profesor refleja cambios en BD
- [ ] CRUD zonas funcional
- [ ] Configuración persiste y se recupera al reabrir
- [ ] Errores muestran diálogos claros

## 🔍 Mejores Prácticas
- Desacoplar: UI llama a servicios, no a modelos directamente
- Uso de `QAbstractTableModel` para escalabilidad

---
Siguiente: PASO 6 (vista de calendario y visualización).