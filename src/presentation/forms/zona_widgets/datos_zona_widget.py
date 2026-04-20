"""
Widget de datos de zona.

Este widget encapsula los campos de información de la zona:
- Nombre
- Descripción
- Fecha inicio (opcional)
- Fecha fin (opcional)
"""

from datetime import date
from typing import Optional, Tuple

from PyQt6.QtCore import QDate, QRegularExpression, pyqtSignal
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

from presentation.theme import legacy_styles as styles


class DatosZonaWidget(QGroupBox):
    """
    Widget para gestionar datos de la zona.

    Señales:
        datos_changed: Se emite cuando cambian los datos del widget
    """

    # Señales
    datos_changed = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializar widget de datos de zona.

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__("📋 Datos de la Zona", parent)
        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Crear la interfaz de usuario del widget."""
        layout_datos = QVBoxLayout()
        layout_datos.setSpacing(8)

        # Campo: Nombre de la zona
        label_nombre = QLabel("Nombre de la zona:")
        label_nombre.setObjectName("fieldLabel")
        layout_datos.addWidget(label_nombre)

        self.nombre_zona_input = QLineEdit()
        self.nombre_zona_input.setPlaceholderText("Ej: Patio Principal, Porche, etc.")
        self.nombre_zona_input.setMaximumWidth(350)
        self.nombre_zona_input.setValidator(
            QRegularExpressionValidator(QRegularExpression(r".{2,80}"))
        )
        layout_datos.addWidget(self.nombre_zona_input)

        # Campo: Descripción
        label_desc = QLabel("Descripción (opcional):")
        label_desc.setObjectName("fieldLabel")
        layout_datos.addWidget(label_desc)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Detalles adicionales sobre la zona")
        self.descripcion_input.setMaximumWidth(350)
        layout_datos.addWidget(self.descripcion_input)

        # Campo: Fecha de inicio (opcional)
        self.usar_fecha_inicio_check = QCheckBox("Especificar fecha de inicio")
        self.usar_fecha_inicio_check.setObjectName("fieldLabel")
        layout_datos.addWidget(self.usar_fecha_inicio_check)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setMaximumWidth(200)
        self.fecha_inicio_input.setEnabled(False)
        layout_datos.addWidget(self.fecha_inicio_input)

        # Campo: Fecha de fin (opcional)
        self.usar_fecha_fin_check = QCheckBox("Especificar fecha de fin")
        self.usar_fecha_fin_check.setObjectName("fieldLabel")
        layout_datos.addWidget(self.usar_fecha_fin_check)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setMaximumWidth(200)
        self.fecha_fin_input.setEnabled(False)
        layout_datos.addWidget(self.fecha_fin_input)

        self.setLayout(layout_datos)

    def _conectar_senales(self):
        """Conectar señales de los campos."""
        self.nombre_zona_input.textChanged.connect(self.datos_changed.emit)
        self.descripcion_input.textChanged.connect(self.datos_changed.emit)
        self.usar_fecha_inicio_check.toggled.connect(self._toggle_fecha_inicio)
        self.usar_fecha_fin_check.toggled.connect(self._toggle_fecha_fin)
        self.fecha_inicio_input.dateChanged.connect(self.datos_changed.emit)
        self.fecha_fin_input.dateChanged.connect(self.datos_changed.emit)

    def _toggle_fecha_inicio(self, checked: bool):
        """Habilitar/deshabilitar campo de fecha de inicio."""
        self.fecha_inicio_input.setEnabled(checked)
        self.datos_changed.emit()

    def _toggle_fecha_fin(self, checked: bool):
        """Habilitar/deshabilitar campo de fecha de fin."""
        self.fecha_fin_input.setEnabled(checked)
        self.datos_changed.emit()

    def get_nombre(self) -> str:
        """Obtener el nombre de la zona."""
        return self.nombre_zona_input.text().strip()

    def set_nombre(self, nombre: str):
        """Establecer el nombre de la zona."""
        self.nombre_zona_input.setText(nombre if nombre else "")

    def get_descripcion(self) -> str:
        """Obtener la descripción de la zona."""
        return self.descripcion_input.text().strip()

    def set_descripcion(self, descripcion: str):
        """Establecer la descripción de la zona."""
        self.descripcion_input.setText(descripcion if descripcion else "")

    def get_fecha_inicio(self) -> Optional[date]:
        """Obtener fecha de inicio si está habilitada."""
        if self.usar_fecha_inicio_check.isChecked():
            qdate = self.fecha_inicio_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_inicio(self, fecha: Optional[date]):
        """Establecer fecha de inicio."""
        if fecha:
            self.usar_fecha_inicio_check.setChecked(True)
            self.fecha_inicio_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_inicio_check.setChecked(False)

    def get_fecha_fin(self) -> Optional[date]:
        """Obtener fecha de fin si está habilitada."""
        if self.usar_fecha_fin_check.isChecked():
            qdate = self.fecha_fin_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_fin(self, fecha: Optional[date]):
        """Establecer fecha de fin."""
        if fecha:
            self.usar_fecha_fin_check.setChecked(True)
            self.fecha_fin_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_fin_check.setChecked(False)

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        Returns:
            Diccionario con nombre, descripcion, fecha_inicio, fecha_fin
        """
        return {
            "nombre": self.get_nombre(),
            "descripcion": self.get_descripcion(),
            "fecha_inicio": self.get_fecha_inicio(),
            "fecha_fin": self.get_fecha_fin(),
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Args:
            datos: Diccionario con nombre, descripcion, fecha_inicio, fecha_fin
        """
        if "nombre" in datos:
            self.set_nombre(datos["nombre"])
        if "descripcion" in datos:
            self.set_descripcion(datos["descripcion"])
        if "fecha_inicio" in datos:
            self.set_fecha_inicio(datos["fecha_inicio"])
        if "fecha_fin" in datos:
            self.set_fecha_fin(datos["fecha_fin"])

    def limpiar(self):
        """Limpiar todos los campos del widget."""
        self.nombre_zona_input.clear()
        self.descripcion_input.clear()
        self.usar_fecha_inicio_check.setChecked(False)
        self.usar_fecha_fin_check.setChecked(False)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_fin_input.setDate(QDate.currentDate())

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        nombre = self.get_nombre()

        # Validar nombre (obligatorio)
        if not nombre:
            return False, "El nombre de la zona es obligatorio"

        if len(nombre) < 2:
            return False, "El nombre debe tener al menos 2 caracteres"

        # Validar fechas si ambas están activas
        fecha_inicio = self.get_fecha_inicio()
        fecha_fin = self.get_fecha_fin()

        if fecha_inicio and fecha_fin:
            if fecha_inicio > fecha_fin:
                return (
                    False,
                    "La fecha de inicio no puede ser posterior a la fecha de fin",
                )

        return True, ""

    def enfocar_primer_campo(self):
        """Poner el foco en el primer campo del widget."""
        self.nombre_zona_input.setFocus()
        self.nombre_zona_input.selectAll()
