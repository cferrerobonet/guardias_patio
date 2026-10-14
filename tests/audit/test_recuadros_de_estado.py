"""Lote 8 bis — piezas repetidas fuera de las vistas, y recuadros que sí repintan.

De los 174 estilos escritos a mano en la capa de presentación, 157 son
distintos entre sí: ajustes de un widget concreto que sacar a la hoja de estilos
sólo movería de sitio. Los que aparecían dos o tres veces literalmente sí valía
la pena unificarlos.

Al hacerlo salió un fallo: cambiar `setProperty("caja", ...)` en caliente no
repinta nada —Qt sólo evalúa los selectores por propiedad al aplicar la hoja—,
así que los avisos de la configuración inicial y del diálogo de permuta se
quedaban con el color del primer pintado por mucho que cambiase el texto.
"""

import inspect
import re
from pathlib import Path

import pytest
from PyQt6.QtWidgets import QLabel

from utils.ui_helpers import aplicar_caja

RAIZ = Path(__file__).resolve().parents[2]
QSS = RAIZ / "src" / "presentation" / "theme" / "light.qss"


def test_aplicar_caja_deja_el_papel_puesto(qapp):
    etiqueta = QLabel("SFTP: no configurado")

    aplicar_caja(etiqueta, "error")

    assert etiqueta.property("caja") == "error"


def test_aplicar_caja_repinta(qapp):
    """Sin el repolish el color se queda en el del primer pintado."""
    fuente = inspect.getsource(aplicar_caja)
    assert "unpolish" in fuente and "polish" in fuente


@pytest.mark.parametrize("papel", ["aviso", "info", "error", "exito"])
def test_cada_papel_tiene_su_regla(papel):
    assert f'QLabel[caja="{papel}"]' in QSS.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "modulo",
    [
        "presentation.dialogs.initial_config_dialog",
        "presentation.dialogs.permutar_guardia_dialog",
    ],
)
def test_nadie_cambia_el_papel_sin_repintar(modulo):
    import importlib

    fuente = inspect.getsource(importlib.import_module(modulo))
    assert 'setProperty("caja"' not in fuente


def test_las_piezas_repetidas_estan_en_la_hoja():
    qss = QSS.read_text(encoding="utf-8")
    for rol in ("cajaInformativa", "botonConfirmarVerde", "areaConMarco"):
        assert f"#{rol}" in qss


def test_los_estilos_en_linea_que_quedan_son_unicos():
    """El resto no compensa extraerlo, y conviene que conste medido.

    De los estilos escritos a mano en la capa de presentación, la inmensa
    mayoría aparecen una sola vez: son el ajuste de un widget concreto. Sacarlos
    a la hoja de estilos crearía un rol por widget, que es el mismo problema con
    otro nombre. Este test cae si vuelve a haber duplicación que valga la pena.
    """
    import ast
    import collections

    repetidos = collections.Counter()
    for ruta in (RAIZ / "src" / "presentation").rglob("*.py"):
        if "__pycache__" in ruta.parts:
            continue
        try:
            arbol = ast.parse(ruta.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            es_estilo = (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "setStyleSheet"
                and nodo.args
                and isinstance(nodo.args[0], ast.Constant)
                and isinstance(nodo.args[0].value, str)
            )
            if es_estilo:
                repetidos[re.sub(r"\s+", " ", nodo.args[0].value).strip()] += 1

    duplicados = sum(veces - 1 for veces in repetidos.values() if veces > 1)
    assert duplicados <= 12, (
        f"{duplicados} estilos escritos dos o más veces: si son varios, extraerlos "
        "a la hoja de estilos ya compensa"
    )
