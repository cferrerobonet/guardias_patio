---
paths:
  - "src/sync/**"
  - "src/services/exportador.py"
  - "src/services/_exportador_import.py"
  - "src/services/_exportador_formatos.py"
  - "src/infrastructure/database/models.py"
  - "alembic/versions/**"
  - "tests/test_ida_y_vuelta_completa.py"
---

# Sincronización e importación/exportación: no pueden fallar

CarlosFB (2026-10-03): la sincronización en la nube y la importación/exportación «no pueden fallar bajo ningún concepto». La última copia subida al SFTP con una versión anterior debe cargar al abrir la app nueva; importan las copias del SFTP (hay cuentas de otros usuarios), no las locales.

- La descarga de arranque reconstruye la base desde cero (`clear_existing=True`): lo que no viaja se pierde sin aviso.
- **Columna nueva en un modelo** → añadirla a `sync/dtos.py`, `sync/data_exporter.py`, `services/exportador.py` y `services/_exportador_import.py`, y a las filas de `tests/test_ida_y_vuelta_completa.py` (el test falla si falta).
- **El importador nuevo acepta todo lo que aceptaba el anterior**: `.get()` con valor por defecto y referencias huérfanas a `None`.
- Bajar copias del SFTP de otras cuentas lo bloquea el clasificador de permisos (datos personales): la comprobación la decide y ejecuta CarlosFB. Mismo host IONOS que AutoExam: no sondear ni abrir conexiones de más (puerto 22).
- `sync/sync_manager.py` tiene techo de líneas (`tests/audit/test_modulos_grandes.py`): lo nuevo de sync va a módulos aparte. `tests/audit/test_manejo_de_errores.py` tiene un techo de `except Exception` que solo puede bajar.
