# PASO 6: Interfaz – Visualización de Guardias

## 🎯 Objetivo
Ofrecer vistas claras del calendario de guardias con filtros y navegación flexible.

## 🧩 Archivos
```
src/ui/
 ├── calendario_guardias.py
 ├── vista_profesor.py
 └── vista_zona.py
```

## 📅 `calendario_guardias.py`
Funciones:
- Tabla / vista mensual
- Filtros: Profesor | Zona | Turno | Mes
- Colores diferenciados (mañana = azul / tarde = verde, p.ej.)
- Botones: Generar / Regenerar / Exportar (posterior)

## 👤 `vista_profesor.py`
Lista cronológica:
- Fecha
- Turno / recreo
- Zona
- (Opcional) Botón para intercambio manual (futuro)

## 🗺️ `vista_zona.py`
Grid por fecha mostrando profesor asignado por recreo.

## 🔄 Generación desde UI
Botón "Generar Guardias":
1. Muestra `QProgressDialog`
2. Llama a servicio de asignación
3. Refresca vistas

Botón "Borrar y Regenerar": confirmación previa.

## 🧪 Criterios de Verificación
- [ ] Se visualizan todas las guardias
- [ ] Filtros combinados funcionan
- [ ] Vistas profesor/zona coherentes entre sí

## 💡 Mejores Prácticas
- No bloquear UI: usar `QThread` o `QRunnable` para generación si es costosa
- Cachear resultados en memoria para filtros rápidos

---
Siguiente: PASO 7 (exportaciones e informes).