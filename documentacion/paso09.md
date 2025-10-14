# PASO 9: Funcionalidades Avanzadas

## 🎯 Objetivo
Ampliar la utilidad y flexibilidad del sistema con exclusiones, preferencias, histórico y estadísticas.

## 🗄️ Nuevas Tablas
| Tabla | Campos |
|-------|--------|
| Exclusiones | id, profesor_id, fecha_inicio, fecha_fin, motivo |
| Preferencias | id, profesor_id, zona_id, preferencia (int: -1/0/+1) |
| Calendarios | id, curso, fecha_generacion, metadatos |

## 🧩 Exclusiones
- Aplicar filtro antes de asignar.
- Opción visual de "periodos no asignables" en vista profesor.

## 🎚️ Preferencias
- Ajustar heurística de asignación: sumar/restar peso.
- Evitar violar preferencias negativas salvo necesidad.

## 🔁 Ajustes Manuales
- Intercambiar guardias (validación de cuotas y turnos).
- Registrar auditoría de cambios (tabla changes_log opcional).

## 🗂️ Histórico
- Guardar snapshot de guardias por curso.
- Permitir consultar cursos anteriores sin mezclar datos.

## 📊 Estadísticas
- Guardias por profesor (total, mañana, tarde).
- Uso de zonas.
- Distribución mensual.
- Visualización con matplotlib (barras, pastel, heatmap simple).

## ✅ Criterios de Verificación
- [ ] Exclusiones respetadas (ninguna guardia dentro del rango excluido)
- [ ] Ajuste manual no rompe integridad
- [ ] Preferencias influyen en asignaciones (analizar % cumplimiento)
- [ ] Estadísticas coinciden con consultas SQL directas

## 🔮 Futuro
- Sistema de notificaciones / recordatorios
- Exportación de cambios auditados

---
Pasar al PASO 10: testing y documentación final.


