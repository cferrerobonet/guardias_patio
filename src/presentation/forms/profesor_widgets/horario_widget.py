"""
Widget de configuración de horario del profesor.

Este widget encapsula los campos de horario y turno:
- Horas de contrato
- Turno (Mañana/Tarde/Mixto)
- Horas específicas de mañana y tarde (para turno mixto)
- Guardias voluntarias hechas antes del reparto oficial
"""

from typing import Optional, Tuple

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSizePolicy,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from utils.validators import validar_horas_contrato


class HorarioWidget(QGroupBox):
    """
    Widget para gestionar configuración de horario del profesor.

    Señales:
        horario_changed: Se emite cuando cambian los datos de horario
        turno_changed: Se emite cuando cambia el turno seleccionado
        voluntarias_changed: Se emite cuando cambian las guardias voluntarias hechas
    """

    # Señales
    horario_changed = pyqtSignal()
    turno_changed = pyqtSignal(str)  # Emite el turno seleccionado
    voluntarias_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        """
        Inicializar widget de horario.

        Args:
            parent: Widget padre (opcional)
        """
        super().__init__("🕐 Configuración de Horario", parent)
        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Crear la interfaz de usuario del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Primera fila: Horas, Turno y Voluntarias; con la línea de ayuda debajo y sin
        # espacio entre ambas, para que el conjunto mida lo mismo que antes
        bloque_fila1 = QVBoxLayout()
        bloque_fila1.setSpacing(0)
        layout_fila1 = QHBoxLayout()
        layout_fila1.setSpacing(15)

        label_horas = QLabel("Horas de contrato:")
        label_horas.setObjectName("fieldLabel")
        layout_fila1.addWidget(label_horas)

        self.horas_input = QLineEdit()
        self.horas_input.setPlaceholderText("Ej: 30.0")
        self.horas_input.setMaximumWidth(100)
        self.horas_input.setToolTip(
            "Horas totales de contrato del profesor\nDebe ser un número positivo (ej: 30.0)"
        )
        layout_fila1.addWidget(self.horas_input)

        layout_fila1.addSpacing(20)

        label_turno = QLabel("Turno:")
        label_turno.setObjectName("fieldLabel")
        layout_fila1.addWidget(label_turno)

        self.turno_input = QComboBox()
        self.turno_input.addItems(["Mañana", "Tarde", "Mixto"])
        self.turno_input.setMaximumWidth(120)
        layout_fila1.addWidget(self.turno_input)

        layout_fila1.addSpacing(10)

        # Ocupa el hueco que ya quedaba a la derecha del turno. Con la política
        # «Ignored» no cuenta para el ancho del recuadro: el panel no se ensancha.
        contenedor_voluntarias = QWidget()
        politica_voluntarias = contenedor_voluntarias.sizePolicy()
        politica_voluntarias.setHorizontalPolicy(QSizePolicy.Policy.Ignored)
        contenedor_voluntarias.setSizePolicy(politica_voluntarias)
        grupo_voluntarias = QHBoxLayout(contenedor_voluntarias)
        grupo_voluntarias.setContentsMargins(0, 0, 0, 0)
        grupo_voluntarias.setSpacing(6)
        label_voluntarias = QLabel("Guardias voluntarias hechas:")
        label_voluntarias.setObjectName("fieldLabel")
        grupo_voluntarias.addWidget(label_voluntarias)

        self.voluntarias_input = QSpinBox()
        self.voluntarias_input.setRange(0, 500)
        self.voluntarias_input.setValue(0)
        self.voluntarias_input.setMaximumWidth(60)
        self.voluntarias_input.setAccessibleName("Guardias voluntarias hechas")
        self.voluntarias_input.setToolTip(
            "Guardias hechas de forma voluntaria antes del inicio del reparto oficial.\n"
            "Cuentan como hechas: se descuentan de la parte del curso que le toca."
        )
        grupo_voluntarias.addWidget(self.voluntarias_input)
        grupo_voluntarias.addStretch()
        layout_fila1.addWidget(contenedor_voluntarias, 1)

        bloque_fila1.addLayout(layout_fila1)

        # Línea de ayuda de la cuota oficial. Ocupa el hueco de 15 px que separaba
        # las dos filas y lo conserva aunque esté oculta: la altura no cambia.
        self.ayuda_cuota_label = QLabel("")
        self.ayuda_cuota_label.setObjectName("secondary")
        self.ayuda_cuota_label.setContentsMargins(0, 1, 0, 0)
        self.ayuda_cuota_label.setMaximumHeight(15)
        politica = self.ayuda_cuota_label.sizePolicy()
        politica.setRetainSizeWhenHidden(True)
        self.ayuda_cuota_label.setSizePolicy(politica)
        self.ayuda_cuota_label.setVisible(False)
        bloque_fila1.addWidget(self.ayuda_cuota_label)
        layout.addLayout(bloque_fila1)

        # Segunda fila: Campos mixto (ocultos por defecto)
        layout_mixto = QHBoxLayout()
        layout_mixto.setSpacing(10)

        self.label_horas_manana = QLabel("  🌅 Horas mañana:")
        self.label_horas_manana.setObjectName("fieldLabel")
        layout_mixto.addWidget(self.label_horas_manana)

        self.horas_manana_input = QLineEdit()
        self.horas_manana_input.setPlaceholderText("Ej: 15.0")
        self.horas_manana_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_manana_input)

        layout_mixto.addSpacing(20)

        self.label_horas_tarde = QLabel("🌆 Horas tarde:")
        self.label_horas_tarde.setObjectName("fieldLabel")
        layout_mixto.addWidget(self.label_horas_tarde)

        self.horas_tarde_input = QLineEdit()
        self.horas_tarde_input.setPlaceholderText("Ej: 15.0")
        self.horas_tarde_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_tarde_input)

        layout_mixto.addStretch()
        layout.addLayout(layout_mixto)

        self.setLayout(layout)

        # Ocultar campos mixto por defecto
        self._toggle_mixto_fields(False)

    def _conectar_senales(self):
        """Conectar señales de los campos."""
        self.horas_input.textChanged.connect(self.horario_changed.emit)
        self.turno_input.currentTextChanged.connect(self._on_turno_changed)
        self.horas_manana_input.textChanged.connect(self.horario_changed.emit)
        self.horas_tarde_input.textChanged.connect(self.horario_changed.emit)
        self.voluntarias_input.valueChanged.connect(self._on_voluntarias_changed)

    def _on_voluntarias_changed(self, valor: int):
        self.horario_changed.emit()
        self.voluntarias_changed.emit(valor)

    def get_guardias_voluntarias(self) -> int:
        """Guardias voluntarias hechas antes del reparto oficial."""
        return self.voluntarias_input.value()

    def set_guardias_voluntarias(self, valor: Optional[int]):
        """Establecer las guardias voluntarias hechas (None = 0)."""
        self.voluntarias_input.setValue(int(valor or 0))

    def set_ayuda_cuota(self, texto: Optional[str]):
        """Muestra la línea de ayuda de la cuota oficial; None o vacío la oculta."""
        self.ayuda_cuota_label.setText(texto or "")
        self.ayuda_cuota_label.setVisible(bool(texto))

    def _toggle_mixto_fields(self, visible: bool):
        """
        Mostrar/ocultar campos de turno mixto.

        Args:
            visible: True para mostrar, False para ocultar
        """
        for w in [
            self.label_horas_manana,
            self.horas_manana_input,
            self.label_horas_tarde,
            self.horas_tarde_input,
        ]:
            w.setVisible(visible)

    def _on_turno_changed(self, value: str):
        """
        Manejar cambio en selector de turno.

        Args:
            value: Turno seleccionado
        """
        turno_lower = value.lower()

        # Mostrar/ocultar campos de turno mixto
        self._toggle_mixto_fields(turno_lower == "mixto")

        # Emitir señales
        self.horario_changed.emit()
        self.turno_changed.emit(value)

    def get_horas_contrato(self) -> Optional[float]:
        """
        Obtener las horas de contrato.

        Returns:
            Horas de contrato como float, o None si no es válido
        """
        texto = self.horas_input.text().strip()
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def set_horas_contrato(self, horas: Optional[float]):
        """
        Establecer las horas de contrato.

        Args:
            horas: Horas de contrato
        """
        if horas is not None:
            self.horas_input.setText(str(horas))
        else:
            self.horas_input.clear()

    def get_turno(self) -> str:
        """
        Obtener el turno seleccionado.

        Returns:
            Turno seleccionado en minúsculas (mañana/tarde/mixto)
        """
        return self.turno_input.currentText().lower()

    def set_turno(self, turno: str):
        """
        Establecer el turno.

        Args:
            turno: Turno a seleccionar (puede venir en minúsculas: mañana/tarde/mixto)
        """
        # Capitalizar para coincidir con los items del combo (Mañana/Tarde/Mixto)
        turno_capitalizado = turno.capitalize()
        index = self.turno_input.findText(turno_capitalizado)
        if index >= 0:
            self.turno_input.setCurrentIndex(index)

    def get_horas_manana(self) -> Optional[float]:
        """
        Obtener las horas de mañana (solo para turno mixto).

        Returns:
            Horas de mañana como float, o None si no es válido
        """
        texto = self.horas_manana_input.text().strip()
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def set_horas_manana(self, horas: Optional[float]):
        """
        Establecer las horas de mañana.

        Args:
            horas: Horas de mañana
        """
        if horas is not None:
            self.horas_manana_input.setText(str(horas))
        else:
            self.horas_manana_input.clear()

    def get_horas_tarde(self) -> Optional[float]:
        """
        Obtener las horas de tarde (solo para turno mixto).

        Returns:
            Horas de tarde como float, o None si no es válido
        """
        texto = self.horas_tarde_input.text().strip()
        if not texto:
            return None
        try:
            return float(texto)
        except ValueError:
            return None

    def set_horas_tarde(self, horas: Optional[float]):
        """
        Establecer las horas de tarde.

        Args:
            horas: Horas de tarde
        """
        if horas is not None:
            self.horas_tarde_input.setText(str(horas))
        else:
            self.horas_tarde_input.clear()

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        Returns:
            Diccionario con horas_contrato, turno, horas_manana, horas_tarde,
            guardias_voluntarias
        """
        return {
            "horas_contrato": self.get_horas_contrato(),
            "turno": self.get_turno(),
            "horas_manana": self.get_horas_manana(),
            "horas_tarde": self.get_horas_tarde(),
            "guardias_voluntarias": self.get_guardias_voluntarias(),
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Args:
            datos: Diccionario con horas_contrato, turno, horas_manana, horas_tarde
        """
        if "horas_contrato" in datos:
            self.set_horas_contrato(datos["horas_contrato"])
        if "turno" in datos:
            self.set_turno(datos["turno"])
        if "horas_manana" in datos:
            self.set_horas_manana(datos["horas_manana"])
        if "horas_tarde" in datos:
            self.set_horas_tarde(datos["horas_tarde"])
        if "guardias_voluntarias" in datos:
            self.set_guardias_voluntarias(datos["guardias_voluntarias"])

    def limpiar(self):
        """Limpiar todos los campos del widget."""
        self.horas_input.clear()
        self.turno_input.setCurrentIndex(0)
        self.horas_manana_input.clear()
        self.horas_tarde_input.clear()
        self.voluntarias_input.setValue(0)
        self.set_ayuda_cuota(None)

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        horas = self.get_horas_contrato()

        # Validar horas de contrato (obligatorio)
        if horas is None:
            return False, "Las horas de contrato son obligatorias"

        es_valido_horas, mensaje_horas = validar_horas_contrato(horas)
        if not es_valido_horas:
            return False, mensaje_horas

        # Validar campos de turno mixto si aplica
        turno = self.get_turno()
        if turno.lower() == "mixto":
            horas_manana = self.get_horas_manana()
            horas_tarde = self.get_horas_tarde()

            if horas_manana is None or horas_tarde is None:
                return (
                    False,
                    "Para turno mixto debe especificar horas de mañana y tarde",
                )

            if horas_manana < 0 or horas_tarde < 0:
                return False, "Las horas de mañana y tarde deben ser positivas"

            # Verificar que la suma no exceda las horas totales
            if horas_manana + horas_tarde > horas:
                return (
                    False,
                    f"La suma de horas mañana ({horas_manana}) y tarde ({horas_tarde}) "
                    f"excede las horas totales ({horas})",
                )

        return True, ""
