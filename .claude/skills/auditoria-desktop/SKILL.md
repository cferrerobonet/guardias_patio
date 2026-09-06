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

## Gates ampliados (desde v5.97.0, dimensiones H–O de `auditoria/21_PLAN_DE_AUDITORIA_AMPLIADO.md`)

Ejecutar desde la raíz con `PY=~/.venvs/guardias-patio/bin/python` y `export QT_QPA_PLATFORM=offscreen`. Cada línea es un gate: si falla, ficha en `30_REGISTRO_HALLAZGOS.md` con la familia indicada.

```bash
$PY -m pytest tests/audit/test_credenciales_no_van_en_el_codigo.py tests/audit/test_sin_datos_reales_en_el_repositorio.py tests/audit/test_credenciales_en_el_llavero.py tests/audit/test_limpieza_de_rastros.py -q --no-cov   # H · SEC
$PY -m bandit -r src -q -ll                                    # H · SEC: salida vacía
$PY -m pip_audit --progress-spinner off                        # J · SUP: sin filas
$PY -m pytest tests/audit/test_un_solo_spec.py tests/audit/test_publicacion_web.py -q --no-cov   # J/I
grep -rnE "logger\.\w+\(.*(to_email|nombre_completo)" src     # I · PRIV: vacío o enmascarado
grep -rnE "\bopen\([^)]*\)" src | grep -v encoding             # K · COD-010: vacío
$PY -m radon cc src -s -n D                                    # E · COD-009: que no crezca
$PY -m vulture src --min-confidence 80                         # E: ≤ 5 líneas
grep -cE "ruff|bandit|pip_audit" .github/workflows/*.yml       # J · SEC-007: > 0 cuando se cierre el lote 19
```

Reglas de la sesión de auditoría: una dimensión por sesión; leer sólo `20`, `21` y `30`; **auditar no es arreglar**; barrera antes que test; nunca escribir la palabra prohibida por la bóveda.
