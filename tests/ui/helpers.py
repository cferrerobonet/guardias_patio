"""Helpers para tests de UI: mocks de diálogos Qt y utilidades de interacción."""

from contextlib import contextmanager
from unittest.mock import patch

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QTableWidget


@contextmanager
def confirm_yes(form):
    """Mock confirmar_accion -> True (el usuario acepta)."""
    with patch.object(form, "confirmar_accion", return_value=True):
        yield


@contextmanager
def confirm_no(form):
    """Mock confirmar_accion -> False (el usuario cancela)."""
    with patch.object(form, "confirmar_accion", return_value=False):
        yield


@contextmanager
def mock_file_save(target_module: str, path: str = "/tmp/test_output.pdf"):
    """Mock QFileDialog.getSaveFileName en el módulo indicado."""
    with patch(f"{target_module}.QFileDialog.getSaveFileName", return_value=(path, "")):
        yield


@contextmanager
def mock_file_open(target_module: str, path: str = "/tmp/test_input.json"):
    """Mock QFileDialog.getOpenFileName en el módulo indicado."""
    with patch(f"{target_module}.QFileDialog.getOpenFileName", return_value=(path, "")):
        yield


@contextmanager
def mock_file_cancelled(target_module: str):
    """Mock QFileDialog que simula cancelación del usuario."""
    with patch(f"{target_module}.QFileDialog.getSaveFileName", return_value=("", "")):
        with patch(f"{target_module}.QFileDialog.getOpenFileName", return_value=("", "")):
            yield


def select_row(table: QTableWidget, row: int):
    """Seleccionar una fila en una QTableWidget."""
    table.setCurrentCell(row, 0)
    table.selectRow(row)


def row_center(table: QTableWidget, row: int) -> QPoint:
    """Devolver el centro de la celda (row, 0) para simular clicks."""
    item = table.item(row, 0)
    if item:
        return table.visualItemRect(item).center()
    return QPoint(10, table.rowHeight(row) * row + table.rowHeight(row) // 2)


def dbl_click_row(qtbot, table: QTableWidget, row: int):
    """Doble-click en la primera celda de la fila indicada."""
    select_row(table, row)
    center = row_center(table, row)
    qtbot.mouseDblClick(table.viewport(), Qt.MouseButton.LeftButton, pos=center)
