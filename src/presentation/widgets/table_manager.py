"""
Table Manager - Helper para mejorar la UX de tablas CRUD.

Este módulo centraliza la lógica común de gestión de tablas para formularios CRUD,
mejorando la experiencia de usuario con feedback visual y navegación mejorada.
"""

from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QPushButton, QTableWidget


class TableManager:
    """
    Gestor de tabla para mejorar la UX en formularios CRUD.

    Funcionalidades:
    - Habilitar/deshabilitar botones según selección
    - Feedback visual mejorado
    - Navegación con teclado
    - Mantener selección tras operaciones
    """

    def __init__(
        self,
        table: QTableWidget,
        edit_btn: Optional[QPushButton] = None,
        delete_btn: Optional[QPushButton] = None,
    ):
        """
        Inicializar el gestor de tabla.

        Args:
            table: Tabla a gestionar
            edit_btn: Botón de edición (opcional)
            delete_btn: Botón de eliminación (opcional)
        """
        self.table = table
        self.edit_btn = edit_btn
        self.delete_btn = delete_btn
        self._last_selected_id = None

        self._setup_table()
        self._connect_signals()

    def _setup_table(self):
        """Configurar mejoras de la tabla."""
        # Habilitar navegación con flechas
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Mejorar feedback visual
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            """
            QTableWidget {
                gridline-color: #e0e0e0;
                selection-background-color: #0E5FA8;
                selection-color: white;
            }
            QTableWidget::item:hover {
                background-color: #e8f4ff;
            }
            QTableWidget::item:selected {
                background-color: #0E5FA8;
                color: white;
            }
            QTableWidget QHeaderView::section {
                background-color: #f5f5f5;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #0E5FA8;
                font-weight: bold;
            }
        """
        )

    def _connect_signals(self):
        """Conectar señales para actualizar estado de botones."""
        self.table.itemSelectionChanged.connect(self._update_button_states)

        # Habilitar Enter para editar
        if self.edit_btn:
            self.table.itemActivated.connect(lambda: self.edit_btn.click())

    def _update_button_states(self):
        """Actualizar estado de botones según selección."""
        has_selection = len(self.table.selectedItems()) > 0
        single_selection = len(self.table.selectionModel().selectedRows()) == 1

        if self.edit_btn:
            # Editar solo con selección única
            self.edit_btn.setEnabled(single_selection)

        if self.delete_btn:
            # Eliminar con cualquier selección
            self.delete_btn.setEnabled(has_selection)

    def save_selection(self):
        """Guardar ID del elemento seleccionado para restaurarlo después."""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # Guardar ID de la primera columna (normalmente oculta)
            id_item = self.table.item(current_row, 0)
            if id_item:
                # Intentar obtener UserRole, sino usar el texto
                self._last_selected_id = id_item.data(Qt.ItemDataRole.UserRole)
                if self._last_selected_id is None:
                    self._last_selected_id = id_item.text()

    def restore_selection(self):
        """Restaurar selección guardada tras recargar tabla."""
        if self._last_selected_id is None:
            return

        # Buscar la fila con el ID guardado
        for row in range(self.table.rowCount()):
            id_item = self.table.item(row, 0)
            if id_item:
                item_id = id_item.data(Qt.ItemDataRole.UserRole)
                if item_id is None:
                    item_id = id_item.text()

                if str(item_id) == str(self._last_selected_id):
                    self.table.selectRow(row)
                    self.table.scrollToItem(id_item)
                    break

        # Limpiar selección guardada
        self._last_selected_id = None

    def clear_selection(self):
        """Limpiar selección guardada."""
        self._last_selected_id = None

    def get_selected_ids(self) -> list:
        """
        Obtener lista de IDs seleccionados.

        Returns:
            Lista de IDs de elementos seleccionados
        """
        selected_rows = self.table.selectionModel().selectedRows()
        ids = []

        for index in selected_rows:
            row = index.row()
            id_item = self.table.item(row, 0)
            if id_item:
                item_id = id_item.data(Qt.ItemDataRole.UserRole)
                if item_id is None:
                    item_id = id_item.text()
                ids.append(item_id)

        return ids

    def highlight_row(self, row_index: int, duration_ms: int = 2000):
        """
        Destacar visualmente una fila temporalmente.

        Args:
            row_index: Índice de la fila a destacar
            duration_ms: Duración del highlight en milisegundos
        """
        if 0 <= row_index < self.table.rowCount():
            self.table.selectRow(row_index)
            self.table.scrollToItem(self.table.item(row_index, 0))

            # El highlight se mantiene por la selección
            # Podríamos agregar un timer para quitar la selección después
            # pero es mejor mantenerla para que el usuario vea qué modificó

    def enable_table_interactions(self, enabled: bool = True):
        """
        Habilitar/deshabilitar interacciones con la tabla.

        Args:
            enabled: True para habilitar, False para deshabilitar
        """
        self.table.setEnabled(enabled)
        if self.edit_btn:
            self.edit_btn.setEnabled(
                enabled and len(self.table.selectionModel().selectedRows()) == 1
            )
        if self.delete_btn:
            self.delete_btn.setEnabled(enabled and len(self.table.selectedItems()) > 0)

    def get_current_row_data(self, column: int = 0) -> Optional[str]:
        """
        Obtener datos de la fila actual.

        Args:
            column: Columna de donde obtener datos

        Returns:
            Texto del item o None si no hay selección
        """
        current_row = self.table.currentRow()
        if current_row >= 0:
            item = self.table.item(current_row, column)
            if item:
                return item.text()
        return None
