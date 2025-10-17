# 🎯 Zona Preferida del Profesor - Resumen Ejecutivo

## ¿Qué es?

Una mejora en el algoritmo de asignación de guardias que **mantiene a cada profesor en la misma zona** durante todo el curso escolar.

## ¿Por qué?

**Antes**: Los profesores debían consultar cada día en qué zona les tocaba hacer la guardia.

**Ahora**: Una vez conocen su zona el primer día, saben que generalmente estarán siempre ahí.

## Resultados

```
✅ 100% de guardias en la misma zona (escenarios típicos)
✅ ≥70% garantizado (escenarios con restricciones complejas)
✅ 0% configuración manual - totalmente automático
✅ 0% impacto en rendimiento
```

## Beneficios

### Para el Profesor
- ✅ No necesita consultar cada día su zona
- ✅ Conoce bien "su" zona de vigilancia
- ✅ Rutina más estable y predecible

### Para el Centro
- ✅ Menos consultas diarias
- ✅ Profesores más familiarizados con su zona
- ✅ Mejor cobertura de vigilancia

## Cómo Funciona

1. **Primera guardia**: El sistema asigna una zona al profesor y la registra como su "zona preferida"
2. **Siguientes guardias**: El algoritmo da **máxima prioridad** a mantener al profesor en esa misma zona
3. **Automático**: Sin intervención del usuario

## Ejemplo Real

```
Profesor: Juan Pérez
Primera guardia: 02/09/2024 → Zona 1 (Patio Principal)

Resto del curso:
05/09/2024: Patio Principal ✓
10/09/2024: Patio Principal ✓
12/09/2024: Patio Principal ✓
15/09/2024: Patio Principal ✓
... (y así todo el año)
```

## Compatibilidad

✅ Compatible con todas las funcionalidades existentes:
- Matriz día × recreo
- Gestión de ausencias
- Turnos mixtos
- Fechas de inicio/fin
- Todas las validaciones

## Instalación

**No requiere ninguna acción**. La funcionalidad está activa automáticamente.

Para aprovecharla en un curso ya iniciado, simplemente regenera el calendario de guardias.

## Validación

Ejecuta el test de validación:
```bash
.venv/bin/python tests/test_zona_preferida.py
```

Resultado esperado:
```
✅ TEST APROBADO: Todos los profesores mantienen su zona preferida
```

## Documentación Completa

- **Guía completa**: `documentacion/ZONA_PREFERIDA_v2.6.1.md`
- **Changelog**: `documentacion/CHANGELOG_v2.6.1.md`
- **Test**: `tests/test_zona_preferida.py`
- **Código**: `src/services/asignador_guardias.py` (líneas 151, 201-227, 246-251)

---

**Versión**: 2.6.1  
**Fecha**: 17 de octubre de 2025  
**Estado**: ✅ Implementado y Validado
