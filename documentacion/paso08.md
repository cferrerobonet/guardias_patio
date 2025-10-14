# PASO 8: Validaciones y Manejo de Errores

## 🎯 Objetivo
Fortalecer la aplicación añadiendo validaciones de negocio y tratamiento consistente de errores.

## ✅ Validaciones en Servicios
- Porcentaje jornada: 0 < valor ≤ 100
- Fechas curso: `fin > inicio`
- No eliminar profesor con guardias asignadas
- No eliminar zona en uso
- Configuración única activa (si aplica)

## ⚠️ Asignador
Errores a detectar:
- Falta de profesores en un turno requerido
- Zonas > profesores disponibles en un recreo
- Distribución imposible (lanzar excepción especializada)

## 🪵 Logging
Archivo: `src/utils/logger.py`
Sugerido:
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s"
)
logger = logging.getLogger("guardias")
```
Registrar:
- Operaciones CRUD
- Inicio/fin de generación de calendario
- Errores con `logger.exception`

## 💬 Interfaz (Confirmaciones)
- Eliminar profesor/zona: diálogo sí/no
- Regenerar guardias: advertir pérdida de datos previos

## 🧪 Criterios de Verificación
- [ ] Operaciones inválidas muestran mensaje claro
- [ ] No hay excepciones sin capturar en consola
- [ ] Logs contienen trazas de eventos clave

## 🔄 Estrategia de Errores
Crear excepciones personalizadas (`exceptions.py`):
- `TurnoInsuficienteError`
- `DistribucionImposibleError`
- `EntidadEnUsoError`

---
Siguiente: PASO 9 (funcionalidades avanzadas).
