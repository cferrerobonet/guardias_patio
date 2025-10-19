# Integración de Decoradores de Observabilidad

## Resumen

Este documento detalla la integración de decoradores de observabilidad en los casos de uso principales del sistema.

## Use Cases Modificados

### ✅ Profesores

1. **CrearProfesorUseCase** - `@with_metrics("crear_profesor")`
   - Tracking de tiempo de creación
   - Conteo de profesores creados
   - Manejo de errores

2. **ListarProfesoresUseCase** - `@with_metrics("listar_profesores")`
   - Tracking de consultas
   - Tiempo de respuesta
   - Cantidad de registros retornados

### 📋 Pendientes de Integración

**Profesores:**
- ActualizarProfesorUseCase → `@with_metrics("actualizar_profesor")`
- EliminarProfesorUseCase → `@with_metrics("eliminar_profesor")`
- ObtenerProfesorUseCase → `@with_metrics("obtener_profesor")`
- BuscarProfesoresUseCase → `@with_metrics("buscar_profesores")`

**Zonas:**
- CrearZonaUseCase → `@with_metrics("crear_zona")`
- ActualizarZonaUseCase → `@with_metrics("actualizar_zona")`
- EliminarZonaUseCase → `@with_metrics("eliminar_zona")`
- ListarZonasUseCase → `@with_metrics("listar_zonas")`

**Configuración:**
- ObtenerConfiguracionUseCase → `@with_metrics("obtener_configuracion")`
- ActualizarConfiguracionUseCase → `@with_metrics("actualizar_configuracion")`

**Asignación de Guardias:**
- GenerarGuardiasUseCase → `@with_metrics("generar_guardias")` + `@track_time`
- CalcularDistribucionUseCase → `@with_metrics("calcular_distribucion")`
- ObtenerEstadisticasUseCase → `@with_metrics("obtener_estadisticas")`

## Métricas Generadas

Para cada use case decorado, se generan automáticamente:

1. **Contador de Llamadas**: `operation_calls_total{operation="nombre_operacion"}`
2. **Tiempo de Ejecución**: `operation_duration_seconds{operation="nombre_operacion"}`
3. **Contador de Errores**: `operation_errors_total{operation="nombre_operacion"}`

## Ejemplo de Uso

```python
from core.observability import with_metrics

class CrearProfesorUseCase:
    @with_metrics("crear_profesor")
    def execute(self, dto: CrearProfesorDTO) -> ProfesorDTO:
        # Lógica del caso de uso
        pass
```

## Visualización

Las métricas pueden visualizarse:

1. **Dashboard UI**: Botón "📊 Observabilidad" en la aplicación
2. **Terminal**: `python scripts/ver_metricas.py --metrics`
3. **Prometheus**: Endpoint `/metrics` (si está configurado)

## Próximos Pasos

1. ✅ Completar integración en todos los use cases
2. ⏳ Agregar métricas de negocio específicas
3. ⏳ Configurar alertas para operaciones lentas
4. ⏳ Implementar dashboards de visualización avanzados

## Estado Actual

- **Use Cases Totales**: ~15
- **Use Cases con Decoradores**: 2
- **Progreso**: 13% ✨
- **Objetivo**: 100% para Sprint 7.5

---

*Documento generado: 19 de octubre de 2025*
