# Reglas para agentes

## Fallos preexistentes en tests

Si durante la ejecución de `pytest` se detectan fallos que ya existían antes de las modificaciones de la sesión actual (verificado con `git stash` o por conocimiento previo), **no intentar corregirlos**. Continuar con el trabajo solicitado sin detenerse en ellos. Solo corregir fallos que hayan sido introducidos por los cambios de la sesión actual.

Fallo preexistente conocido (no corregir):
- `tests/test_widgets_ui.py::TestAjustesWidget::test_info_algoritmos_muestra_solo_opciones_reales`
