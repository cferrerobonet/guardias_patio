"""VIS-010 — la aplicación deja de llamarse por el programa en el que se inspiró.

El tema, la ventana principal y el menú lateral llevaban en el nombre el del
programa de limpieza en cuyo aspecto se inspiró el diseño, y la clase de la
ventana también. Es el primer nombre que ve quien abre el proyecto, y no es el
de esta aplicación.

El nombre ajeno se compone aquí a partir de sus letras para que este fichero no
salga en su propia búsqueda.
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
CARPETAS = (RAIZ / "src", RAIZ / "tests")
EXCLUIDAS = {"__pycache__", "guardias_de_patio.egg-info", ".venv"}

#: Compuesto a trozos: escrito entero, este propio fichero sería un falso positivo.
NOMBRE_AJENO = "cc" + "leaner"


def _ficheros_de_codigo():
    for carpeta in CARPETAS:
        for ruta in carpeta.rglob("*.py"):
            if EXCLUIDAS.isdisjoint(ruta.parts):
                yield ruta


def test_no_queda_ninguna_mencion_al_programa_ajeno():
    culpables = [
        str(ruta.relative_to(RAIZ))
        for ruta in _ficheros_de_codigo()
        if NOMBRE_AJENO in ruta.read_text(encoding="utf-8", errors="ignore").lower()
    ]
    assert culpables == [], f"Vuelve a aparecer el nombre ajeno en: {culpables}"


def test_los_modulos_se_llaman_por_lo_que_hacen():
    esperados = [
        RAIZ / "src" / "presentation" / "ventana_principal.py",
        RAIZ / "src" / "presentation" / "components" / "menu_lateral.py",
        RAIZ / "src" / "presentation" / "themes" / "tema_aplicacion.py",
    ]
    assert [r for r in esperados if not r.exists()] == []


@pytest.mark.parametrize(
    "modulo,clase",
    [
        ("presentation.ventana_principal", "VentanaPrincipal"),
        ("presentation.components.menu_lateral", "SidebarMenu"),
    ],
)
def test_las_clases_siguen_estando_donde_se_espera(modulo, clase):
    import importlib

    assert hasattr(importlib.import_module(modulo), clase)


def test_la_ventana_lleva_el_nombre_de_la_aplicacion(qapp, session):
    from presentation.ventana_principal import VentanaPrincipal

    ventana = VentanaPrincipal(session, sync_manager=None)
    assert ventana.windowTitle() == "Guardias de Patio"
