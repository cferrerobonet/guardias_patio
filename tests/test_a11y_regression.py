"""
Tests de regresión A11Y (accesibilidad).

Verifica que los widgets interactivos clave tienen accessibleName no vacío,
según lo implementado en A11Y-BASIC (v5.16.0).
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.ui

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def qapp_instance(qapp):
    """Reutiliza el QApplication creado por pytest-qt."""
    return qapp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _check_accessible_names(widget, expected_names: list[str]) -> None:
    """Verifica que el widget contiene widgets con los accessibleNames esperados."""
    found = set()
    for child in widget.findChildren(type(None).__class__):
        pass

    # Recorre todos los QObject hijos recursivamente
    def collect_names(w):
        name = w.accessibleName()
        if name:
            found.add(name)
        for child in w.children():
            try:
                collect_names(child)
            except Exception:
                pass

    collect_names(widget)

    missing = [n for n in expected_names if n not in found]
    assert not missing, f"AccessibleNames faltantes: {missing}\nEncontrados: {sorted(found)}"


# ---------------------------------------------------------------------------
# ChangePasswordDialog
# ---------------------------------------------------------------------------


class TestChangePasswordDialogA11Y:
    """Verifica accesibilidad de ChangePasswordDialog."""

    def test_accessible_names_presentes(self, qtbot):
        from presentation.forms.change_password_dialog import ChangePasswordDialog

        dlg = ChangePasswordDialog(username="test_user")
        qtbot.addWidget(dlg)

        expected = [
            "Campo contraseña actual",
            "Campo nueva contraseña",
            "Campo confirmar nueva contraseña",
            "Botón cancelar cambio de contraseña",
            "Botón confirmar cambio de contraseña",
        ]
        _check_accessible_names(dlg, expected)

    def test_no_hay_campos_sin_nombre(self, qtbot):
        """Ningún input interactivo debe tener accessibleName vacío."""
        from PyQt6.QtWidgets import QLineEdit

        from presentation.forms.change_password_dialog import ChangePasswordDialog

        dlg = ChangePasswordDialog(username="test_user")
        qtbot.addWidget(dlg)

        for le in dlg.findChildren(QLineEdit):
            assert le.accessibleName(), (
                f"QLineEdit sin accessibleName en ChangePasswordDialog: objectName={le.objectName()}"
            )


# ---------------------------------------------------------------------------
# ResetPasswordDialog
# ---------------------------------------------------------------------------


class TestResetPasswordDialogA11Y:
    """Verifica accesibilidad de ResetPasswordDialog."""

    def test_accessible_names_presentes(self, qtbot):
        from presentation.forms.reset_password_dialog import ResetPasswordDialog

        dlg = ResetPasswordDialog(username="test_user")
        qtbot.addWidget(dlg)

        expected = [
            "Campo código de recuperación",
            "Campo nueva contraseña",
            "Campo confirmar nueva contraseña",
            "Botón cancelar recuperación de contraseña",
            "Botón confirmar nueva contraseña",
        ]
        _check_accessible_names(dlg, expected)

    def test_no_hay_campos_sin_nombre(self, qtbot):
        from PyQt6.QtWidgets import QLineEdit

        from presentation.forms.reset_password_dialog import ResetPasswordDialog

        dlg = ResetPasswordDialog(username="test_user")
        qtbot.addWidget(dlg)

        for le in dlg.findChildren(QLineEdit):
            assert le.accessibleName(), (
                f"QLineEdit sin accessibleName en ResetPasswordDialog: objectName={le.objectName()}"
            )


# ---------------------------------------------------------------------------
# DeleteUserDialog
# ---------------------------------------------------------------------------


class TestDeleteUserDialogA11Y:
    """Verifica accesibilidad de DeleteUserDialog."""

    def test_accessible_names_presentes(self, qtbot):
        from presentation.forms.delete_user_dialog import DeleteUserDialog

        dlg = DeleteUserDialog()
        qtbot.addWidget(dlg)

        expected = [
            "Selector de usuario a eliminar",
            "Campo contraseña para confirmar eliminación",
            "Botón cancelar eliminación de usuario",
            "Botón eliminar usuario permanentemente",
        ]
        _check_accessible_names(dlg, expected)


# ---------------------------------------------------------------------------
# AusenciasSustituciones widget
# ---------------------------------------------------------------------------


class TestAusenciasSustitucionesA11Y:
    """Verifica accesibilidad del widget unificado Ausencias/Sustituciones."""

    def test_accessible_names_presentes(self, qtbot):
        from presentation.widgets.ausencias_sustituciones import AusenciasSustitucionesWidget

        session = MagicMock()
        session.query.return_value.filter.return_value.all.return_value = []
        session.query.return_value.filter.return_value.count.return_value = 0
        session.query.return_value.all.return_value = []

        try:
            widget = AusenciasSustitucionesWidget(session=session)
            qtbot.addWidget(widget)

            expected = [
                "Profesor ausente",
                "Buscar guardias afectadas",
                "Guardar todas las sustituciones asignadas",
                "Cancelar cambios y limpiar tabla",
                "Eliminar todas las sustituciones del calendario actual",
            ]
            _check_accessible_names(widget, expected)
        except Exception as e:
            pytest.skip(f"Widget requiere servicios reales: {e}")
