"""
Diálogo de mapeo de columnas para importación de Excel/CSV (FUNC-03).
Permite al usuario asignar columnas del archivo a los campos de la app.
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

try:
    from PyQt6.QtCore import QSettings
except ImportError:
    QSettings = None

# Campos que la app necesita con su etiqueta y si son obligatorios
CAMPOS_APP = {
    "nombre": ("Nombre completo", True),
    "email": ("Email corporativo", False),
}

SETTINGS_KEY = "import/column_mapping"


class ColumnMappingDialog(QDialog):
    """
    Paso previo a la importación: el usuario elige qué columna del archivo
    corresponde a cada campo de la app y cuántas filas saltar.
    Guarda el último mapeo en QSettings.
    """

    def __init__(self, archivo_path: str, parent=None):
        super().__init__(parent)
        self.archivo_path = archivo_path
        self.columnas_archivo: list[str] = []
        self.preview_data: list[list] = []
        self._mapping: dict[str, str] = {}
        self._combos: dict[str, QComboBox] = {}

        self.setWindowTitle("Mapear columnas del archivo")
        self.setMinimumWidth(620)
        self.setMinimumHeight(500)

        self._load_file_columns()
        self._setup_ui()
        self._restore_settings()

    # ------------------------------------------------------------------
    def _load_file_columns(self):
        try:
            import pandas as pd
            ext = self.archivo_path.lower()
            if ext.endswith(".csv"):
                df = pd.read_csv(self.archivo_path, nrows=6)
            else:
                df = pd.read_excel(self.archivo_path, nrows=6)
            self.columnas_archivo = [str(c) for c in df.columns.tolist()]
            self.preview_data = df.head(5).astype(str).values.tolist()
        except Exception:
            self.columnas_archivo = []
            self.preview_data = []

    # ------------------------------------------------------------------
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- Filas a saltar ---
        skip_group = QGroupBox("Opciones de lectura")
        skip_form = QFormLayout(skip_group)
        self.skip_spin = QSpinBox()
        self.skip_spin.setRange(0, 50)
        self.skip_spin.setValue(0)
        self.skip_spin.setToolTip(
            "Número de filas iniciales a ignorar antes de la cabecera de columnas"
        )
        skip_form.addRow("Filas a saltar (antes de cabecera):", self.skip_spin)
        self.skip_spin.valueChanged.connect(self._on_skip_changed)
        layout.addWidget(skip_group)

        # --- Mapeo de campos ---
        map_group = QGroupBox("Mapeo de columnas")
        map_form = QFormLayout(map_group)

        opciones = ["— sin asignar —"] + self.columnas_archivo
        for campo, (etiqueta, obligatorio) in CAMPOS_APP.items():
            combo = QComboBox()
            combo.addItems(opciones)
            label_txt = f"{etiqueta} {'*' if obligatorio else ''}"
            map_form.addRow(label_txt, combo)
            self._combos[campo] = combo

        layout.addWidget(map_group)

        # --- Previsualización ---
        prev_group = QGroupBox("Previsualización (primeras 5 filas)")
        prev_layout = QVBoxLayout(prev_group)
        self.tabla_preview = QTableWidget()
        self.tabla_preview.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_preview.setMaximumHeight(160)
        self._refresh_preview()
        prev_layout.addWidget(self.tabla_preview)
        layout.addWidget(prev_group)

        # --- Botones ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------
    def _refresh_preview(self):
        if not self.columnas_archivo:
            self.tabla_preview.setRowCount(1)
            self.tabla_preview.setColumnCount(1)
            self.tabla_preview.setItem(0, 0, QTableWidgetItem("No se pudo leer el archivo"))
            return

        self.tabla_preview.setColumnCount(len(self.columnas_archivo))
        self.tabla_preview.setHorizontalHeaderLabels(self.columnas_archivo)
        self.tabla_preview.setRowCount(len(self.preview_data))
        for r, row in enumerate(self.preview_data):
            for c, val in enumerate(row):
                self.tabla_preview.setItem(r, c, QTableWidgetItem(str(val)))
        self.tabla_preview.resizeColumnsToContents()

    def _on_skip_changed(self, value: int):
        try:
            import pandas as pd
            ext = self.archivo_path.lower()
            if ext.endswith(".csv"):
                df = pd.read_csv(self.archivo_path, skiprows=value, nrows=6)
            else:
                df = pd.read_excel(self.archivo_path, skiprows=value, nrows=6)
            self.columnas_archivo = [str(c) for c in df.columns.tolist()]
            self.preview_data = df.head(5).astype(str).values.tolist()
        except Exception:
            pass
        opciones = ["— sin asignar —"] + self.columnas_archivo
        for combo in self._combos.values():
            current = combo.currentText()
            combo.clear()
            combo.addItems(opciones)
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        self._refresh_preview()

    # ------------------------------------------------------------------
    def _restore_settings(self):
        if QSettings is None:
            return
        try:
            s = QSettings("GuardiasPatio", "ColumnMapping")
            for campo, combo in self._combos.items():
                saved = s.value(f"import/{campo}", "")
                idx = combo.findText(str(saved))
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            skip = s.value("import/skip_rows", 0, type=int)
            self.skip_spin.setValue(skip)
        except Exception:
            pass

    def _save_settings(self):
        if QSettings is None:
            return
        try:
            s = QSettings("GuardiasPatio", "ColumnMapping")
            for campo, combo in self._combos.items():
                s.setValue(f"import/{campo}", combo.currentText())
            s.setValue("import/skip_rows", self.skip_spin.value())
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _on_accept(self):
        # Validar campos obligatorios
        for campo, (etiqueta, obligatorio) in CAMPOS_APP.items():
            if obligatorio and self._combos[campo].currentIndex() == 0:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Campo obligatorio",
                    f"El campo '{etiqueta}' es obligatorio — selecciona una columna.",
                )
                return
        self._save_settings()
        self._mapping = {
            campo: combo.currentText()
            for campo, combo in self._combos.items()
            if combo.currentIndex() > 0
        }
        self.accept()

    # ------------------------------------------------------------------
    @property
    def mapping(self) -> dict[str, str]:
        """Devuelve {campo_app: columna_archivo} para los campos asignados."""
        return self._mapping

    @property
    def skip_rows(self) -> int:
        return self.skip_spin.value()
