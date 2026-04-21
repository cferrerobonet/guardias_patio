---
description: Workflow post-modificaciones (OBLIGATORIO)
---

Después de CADA conjunto de modificaciones, ejecutar en este orden:

1. **Tests** — `pytest tests/ --tb=no -q`. Si hay fallos nuevos, corregirlos antes de continuar.
2. **Bump versión** — Editar `app_version` en `src/config/settings.py` según SemVer:
   - fix → patch (+0.0.1)
   - feat → minor (+0.1.0)
   - breaking change → major (+1.0.0)
3. **CHANGELOG.md** — Añadir entrada con fecha actual bajo la nueva versión.
4. **Commit + tag + push** (sin pedir confirmación al usuario):
   ```bash
   git add -A
   git commit -m "tipo(scope): descripción"
   git tag v{nueva_versión}
   git push && git push --tags
   ```

## Seguimiento de auditorías/guiones (OBLIGATORIO)

Cuando se implementen cambios a partir de un documento de auditoría, guion técnico o lista de tareas estructurada:

- Al completar cada ítem, actualizar el documento fuente marcándolo como resuelto (`~~texto~~` + `✅ RESUELTO vX.Y.Z`) antes de pasar al siguiente.
- Hacer commit del documento actualizado junto con los cambios de código (o inmediatamente después).

## Archivos protegidos (NO MODIFICAR)

- `sftp_config.json`, `smtp_config.json` — credenciales, gitignored
- `data/` — datos de usuario, gitignored
- `alembic/versions/` — migraciones existentes (solo crear nuevas)
