---
name: auditoria-desktop
description: Re-ejecutar los gates de la auditoría integral de Guardias de Patio (colección, lint, seguridad, suite de auditoría) y actualizar el registro de hallazgos y el plan de ataque. Usar al cerrar un lote de remediación o al reauditar.
---

# Auditoría: gates y actualización del registro

Documentos: `auditoria/00_INDICE.md` (mapa), `auditoria/30_REGISTRO_HALLAZGOS.md` (estado único), `auditoria/17_PLAN_DE_ATAQUE.md` (backlog único). No crear informes paralelos. No leer entero `.agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md`: usar `auditoria/02_PLAN_MAESTRO_AUDITORIA.md`.

## Gates reproducibles

```bash
PY=/opt/homebrew/bin/python3.11; export QT_QPA_PLATFORM=offscreen
$PY -m pytest --co -q --no-cov -p no:cacheprovider | tail -3        # 0 errores
$PY -m ruff check src --statistics                                    # objetivo: 0
$PY -m ruff check src --select F821                                   # obligatorio 0
$PY -m bandit -r src -q -f txt | tail -12                             # sin medios/altos nuevos
$PY -m pytest tests/audit -q --no-cov                                 # xfail estrictos coherentes
$PY -m pytest tests/ -q --no-cov --timeout=120 -p no:cacheprovider    # suite completa
```

Métricas visuales (para ratchets):

```bash
grep -rn 'setStyleSheet' src/presentation | wc -l
grep -rhoE '#[0-9A-Fa-f]{6}\b' src/presentation | wc -l
grep -rhoE 'font-size: ?[0-9]+px' src/presentation | grep -oE '[0-9]+' | awk '$1<12' | wc -l
```

## Al cerrar un ítem

1. Test de regresión verde (retirar `xfail` si existía).
2. En `30_REGISTRO_HALLAZGOS.md`: estado `RESUELTO VERIFICADO vX.Y.Z` + test citado.
3. En `17_PLAN_DE_ATAQUE.md`: tachar y marcar `✅ RESUELTO vX.Y.Z`.
4. Recuentos de `00_INDICE.md` recalculados desde el registro.
5. Mismo commit que el código (regla del fichero de instrucciones).

## Al reauditar (delta)

- Cambió código de hilos/solver/sesión → repetir 06 §5 en Windows.
- Cambió estilo → ratchets y snapshots.
- Cambió build → compilar en ambas plataformas y arrancar el artefacto.
- Registrar commit, fecha y limitaciones en `01_BASELINE_Y_ADAPTADOR.md`.
