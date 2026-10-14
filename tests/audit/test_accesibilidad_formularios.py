"""Accesibilidad de formularios y tablas (UXA-002/005/006/008/012).

El 63% de los controles de las pantallas principales no tenía nombre accesible:
un lector de pantalla anunciaba «cuadro de edición» veinte veces seguidas. Estos
tests fijan el contrato y sirven de ratchet.
"""

import pytest
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTimeEdit,
)

pytestmark = pytest.mark.ui

TIPOS_INTERACTIVOS = (
    QLineEdit,
    QComboBox,
    QCheckBox,
    QDateEdit,
    QTimeEdit,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
    QTableWidget,
)


def _construir(nombre, session):
    from presentation.forms.ajustes_form import AjustesForm
    from presentation.forms.profesor_form import ProfesorForm
    from presentation.forms.zona_form import ZonaForm

    clases = {"ProfesorForm": ProfesorForm, "ZonaForm": ZonaForm, "AjustesForm": AjustesForm}
    vista = clases[nombre](session)
    QApplication.processEvents()
    return vista


def _sin_nombre(vista):
    return [
        f"{type(w).__name__}(objectName={w.objectName()!r})"
        for tipo in TIPOS_INTERACTIVOS
        for w in vista.findChildren(tipo)
        if not w.accessibleName()
    ]


# ---------------------------------------------------------------------------
# UXA-005: todo control anunciable tiene nombre
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("nombre", ["ProfesorForm", "ZonaForm", "AjustesForm"])
def test_ningun_control_se_queda_sin_nombre_accesible(qapp, session, nombre):
    vista = _construir(nombre, session)
    try:
        huerfanos = _sin_nombre(vista)
        assert not huerfanos, f"{nombre}: {len(huerfanos)} controles sin nombre: {huerfanos}"
    finally:
        vista.close()


def test_los_nombres_no_llevan_marcado_ni_emojis(qapp, session):
    """El nombre lo pronuncia una voz: nada de HTML, emojis ni dos puntos."""
    import re

    vista = _construir("AjustesForm", session)
    try:
        for tipo in TIPOS_INTERACTIVOS:
            for w in vista.findChildren(tipo):
                nombre = w.accessibleName()
                if not nombre:
                    continue
                assert "<" not in nombre, f"marcado en {nombre!r}"
                assert not re.search("[\U0001f300-\U0001faff☀-➿]", nombre), nombre
                assert not nombre.endswith(":"), nombre
    finally:
        vista.close()


def test_la_matriz_de_restricciones_distingue_cada_casilla(qapp, session):
    """UXA-005: veinte botones con el mismo '✓' son indistinguibles al oído."""
    vista = _construir("ProfesorForm", session)
    try:
        casillas = [
            b
            for b in vista.findChildren(QPushButton)
            if b.accessibleName().startswith("Recreo ")
        ]
        assert len(casillas) >= 20, f"sólo {len(casillas)} casillas con nombre"
        assert len({b.accessibleName() for b in casillas}) == len(casillas), (
            "hay casillas con el mismo nombre accesible"
        )
        # Y su estado también se anuncia.
        assert all(b.accessibleDescription() for b in casillas)
    finally:
        vista.close()


# ---------------------------------------------------------------------------
# UXA-008: tablas con nombre y descripción
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("nombre", "atributo"),
    [("ProfesorForm", "tabla_profesores"), ("ZonaForm", "tabla_zonas")],
)
def test_las_tablas_principales_se_presentan(qapp, session, nombre, atributo):
    vista = _construir(nombre, session)
    try:
        tabla = getattr(vista, atributo)
        assert tabla.accessibleName()
        assert tabla.accessibleDescription(), "la tabla no explica qué se puede hacer con ella"
    finally:
        vista.close()


# ---------------------------------------------------------------------------
# UXA-002: foco visible
# ---------------------------------------------------------------------------
def test_la_hoja_de_estilos_marca_el_foco_en_todo_control():
    """Sin anillo de foco, moverse con el tabulador es moverse a ciegas."""
    import sys
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(raiz / "src"))
    from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos

    hoja = construir_hoja_de_estilos()

    for control in (
        "QPushButton:focus",
        "QCheckBox:focus",
        "QRadioButton:focus",
        "QDateEdit:focus",
        "QTableWidget:focus",
        "QLineEdit:focus",
        "QComboBox:focus",
    ):
        assert control in hoja, f"sin regla de foco para {control}"

    # Y el anillo se ve: 2 px, no el punteado por defecto de Qt.
    assert "2px solid" in hoja.replace("2px  solid", "2px solid")


# ---------------------------------------------------------------------------
# UXA-006: el error señala el campo
# ---------------------------------------------------------------------------
def test_un_error_de_validacion_marca_el_campo_y_le_lleva_el_foco(qapp, session):
    vista = _construir("ZonaForm", session)
    try:
        # Un widget que no se muestra no puede recibir el foco de teclado.
        vista.show()
        QApplication.processEvents()

        vista.datos_zona_widget.nombre_zona_input.setText("")  # nombre obligatorio
        vista.guardar_zona()
        QApplication.processEvents()

        campo = vista.datos_zona_widget.nombre_zona_input
        assert campo.property("error") == "true", "el campo no queda marcado"
        assert campo.accessibleDescription(), "el campo no dice cuál es el problema"
        assert campo.hasFocus(), "el foco no fue al campo que falla"
    finally:
        vista.close()


def test_los_errores_se_limpian_al_reintentar(qapp, session):
    vista = _construir("ZonaForm", session)
    try:
        campo = vista.datos_zona_widget.nombre_zona_input
        vista.marcar_error_en_campo(campo, "prueba")
        assert campo.property("error") == "true"

        vista.limpiar_errores()
        assert campo.property("error") == "false"
        assert not campo.accessibleDescription()
    finally:
        vista.close()


def test_el_validador_de_zona_dice_que_campo_falla(qapp, session):
    vista = _construir("ZonaForm", session)
    try:
        widget = vista.datos_zona_widget
        widget.nombre_zona_input.setText("")
        valido, mensaje, campo = widget.validar_con_campo()

        assert not valido
        assert mensaje
        assert campo is widget.nombre_zona_input
    finally:
        vista.close()
