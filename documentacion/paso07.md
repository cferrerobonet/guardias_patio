# PASO 7: Exportación e Informes

## 🎯 Objetivo
Generar representaciones externas del calendario en formatos Excel y PDF.

## 📦 Dependencias
```
reportlab
openpyxl
pandas
```

## 📄 Archivo Principal
`src/services/exportador.py`

## 📊 Excel (`exportar_a_excel`)
Hojas sugeridas:
1. Calendario completo: Fecha | Día semana | Turno | Recreo | Zona | Profesor
2. Resumen por profesor: Profesor | Total | Mañana | Tarde | % Distribución
3. Distribución por zona: Zona | Total guardias | % sobre total

## 📄 PDF por Profesor (`exportar_a_pdf_profesor(profesor_id)`)
Contenido:
- Encabezado con nombre y total
- Tabla cronológica
- Totales por turno

## 📘 PDF Calendario Completo (`exportar_calendario_completo_pdf`)
Formato:
- Una página por mes
- Tabla (día vs recreo/zonas)
- Leyenda colores turno

## 🧪 Criterios de Verificación
- [ ] Archivos se abren sin errores
- [ ] Totales coinciden con base de datos
- [ ] Formato legible y ordenado

## 🔍 Notas
- Considerar exportación CSV simple como fallback
- Para grandes volúmenes, generar en hilo separado

---
Siguiente: PASO 8 (validaciones y manejo de errores).