"""
Widget profesional de restricciones y preferencias del profesor - VERSIÓN 2.

Diseño CRUD profesional con tabla y formulario lateral:
- Tabla de restricciones de horario con columnas: Día, Recreos disponibles
- Formulario lateral para crear/editar restricciones por día
- Botones: Nuevo, Editar, Eliminar, Guardar, Cancelar
- Experiencia de usuario intuitiva y clara
"""

import json
from datetime import date
from typing import Dict, List, Optional, Tuple

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.logging import get_logger
from presentation.theme import legacy_styles as styles
from presentation.themes.ccleaner_theme import TEXT_SECONDARY

logger = get_logger(__name__)

_DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie"]
#: Nombre completo del día, para lo que anuncia el lector de pantalla (UXA-005).
_DIAS_COMPLETOS = ["lunes", "martes", "miércoles", "jueves", "viernes"]
_COLOR_ON = "#4CAF50"
_COLOR_OFF = "#E0E0E0"
_COLOR_ON_TEXT = "white"
_COLOR_OFF_TEXT = "#888"


class SemanaRestriccionesWidget(QWidget):
    """Rejilla visual 5×N de disponibilidad (días × recreos) con botones toggle."""

    changed = pyqtSignal()

    def __init__(self, recreos: List[int], parent=None):
        super().__init__(parent)
        self._recreos = recreos
        self._celdas: Dict[tuple, QPushButton] = {}  # (dia, recreo) -> QPushButton
        self._build()

    def _build(self):
        from PyQt6.QtWidgets import QGridLayout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # Plantillas rápidas
        tpl_layout = QHBoxLayout()
        tpl_layout.setSpacing(6)
        for etiqueta, datos in [
            ("Siempre", {d: list(self._recreos) for d in range(5)}),
            ("Solo mañanas", {d: [r for r in self._recreos if r <= 2] for d in range(5)}),
            ("Solo tardes", {d: [r for r in self._recreos if r > 2] for d in range(5)}),
            ("Lun/Mié/Vie", {d: list(self._recreos) for d in [0, 2, 4]}),
            ("Ninguno", {}),
        ]:
            btn = QPushButton(etiqueta)
            btn.setObjectName("secondaryButton")
            btn.setMaximumHeight(26)
            _datos = datos
            btn.clicked.connect(lambda _=False, d=_datos: self._aplicar_plantilla(d))
            tpl_layout.addWidget(btn)
        tpl_layout.addStretch()
        layout.addLayout(tpl_layout)

        # Rejilla
        grid = QGridLayout()
        grid.setSpacing(4)

        # Cabecera días
        for col, dia in enumerate(_DIAS):
            lbl = QLabel(dia)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-weight: bold; font-size: 12px;")
            grid.addWidget(lbl, 0, col + 1)

        # Filas de recreos
        for row, recreo in enumerate(self._recreos):
            lbl = QLabel(f"R{recreo}")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 12px; color: #555;")
            grid.addWidget(lbl, row + 1, 0)
            for col in range(5):
                btn = QPushButton("✓")
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.setFixedSize(44, 32)
                # Un botón cuyo único texto es la marca de verificación no dice
                # nada por sí solo: sin nombre, el lector de pantalla anuncia
                # veinte casillas idénticas.
                btn.setAccessibleName(f"Recreo {recreo} del {_DIAS_COMPLETOS[col]}")
                btn.setToolTip(
                    f"Puede hacer guardia en el recreo {recreo} del {_DIAS_COMPLETOS[col]}"
                )
                self._actualizar_estado_accesible(btn, True)
                self._aplicar_color(btn, True)
                btn.toggled.connect(lambda checked, b=btn: self._on_toggle(b, checked))
                self._celdas[(col, recreo)] = btn
                grid.addWidget(btn, row + 1, col + 1)

        grid_widget = QWidget()
        grid_widget.setLayout(grid)
        layout.addWidget(grid_widget)

    @staticmethod
    def _actualizar_estado_accesible(btn: QPushButton, activo: bool) -> None:
        """El estado de la casilla también tiene que poder oírse."""
        btn.setAccessibleDescription("Disponible" if activo else "No disponible")

    def _aplicar_color(self, btn: QPushButton, on: bool):
        color = _COLOR_ON if on else _COLOR_OFF
        text_color = _COLOR_ON_TEXT if on else _COLOR_OFF_TEXT
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: {text_color};
                border-radius: 4px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        btn.setText("✓" if on else "")
        self._actualizar_estado_accesible(btn, on)

    def _on_toggle(self, btn: QPushButton, checked: bool):
        self._aplicar_color(btn, checked)
        self.changed.emit()

    def _aplicar_plantilla(self, datos: Dict[int, List[int]]):
        for (dia, recreo), btn in self._celdas.items():
            activo = recreo in datos.get(dia, [])
            btn.blockSignals(True)
            btn.setChecked(activo)
            self._aplicar_color(btn, activo)
            btn.blockSignals(False)
        self.changed.emit()

    def get_restricciones_dias(self) -> Dict[int, List[int]]:
        resultado: Dict[int, List[int]] = {}
        for (dia, recreo), btn in self._celdas.items():
            if btn.isChecked():
                resultado.setdefault(dia, []).append(recreo)
        for dia in resultado:
            resultado[dia] = sorted(resultado[dia])
        return resultado

    def set_restricciones_dias(self, datos: Dict[int, List[int]]):
        for (dia, recreo), btn in self._celdas.items():
            activo = recreo in datos.get(dia, [])
            btn.blockSignals(True)
            btn.setChecked(activo)
            self._aplicar_color(btn, activo)
            btn.blockSignals(False)


class RestriccionesWidget(QGroupBox):
    """
    Widget CRUD profesional para gestionar restricciones y preferencias del profesor.

    Características:
    - Tabla con restricciones por día de la semana
    - Formulario lateral para editar recreos disponibles
    - Botones de acción: Editar, Aplicar a todos, Limpiar todo
    - Validación automática
    """

    # Señales
    restricciones_changed = pyqtSignal()
    preseleccionar_turno_request = pyqtSignal(str)

    # Constantes
    DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]
    RECREOS = [1, 2, 3, 4]  # R1, R2, R3, R4

    def __init__(self, parent=None):
        """Inicializar widget de restricciones."""
        super().__init__("⚙️ Restricciones y Preferencias", parent)

        # Estado interno: {día_index: [recreos_permitidos]}
        self.restricciones_dias: Dict[int, List[int]] = {}

        # (referencias legacy eliminadas — se usa semana_widget)

        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Construir la interfaz de usuario."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)  # Reducido de 12 a 8

        # Sección de fechas
        main_layout.addLayout(self._crear_seccion_fechas())

        # Sección de zona preferida
        main_layout.addLayout(self._crear_seccion_zona_preferida())

        # Separador
        main_layout.addWidget(self._crear_separador())

        # Rejilla visual de disponibilidad
        self.semana_widget = SemanaRestriccionesWidget(self.RECREOS)
        self.semana_widget.setEnabled(False)  # Se habilita solo cuando el checkbox está activo
        self.semana_widget.changed.connect(self._on_semana_changed)
        self.panel_restricciones_widget = self.semana_widget
        main_layout.addWidget(self.semana_widget)

        # Checkbox principal - AL FINAL, después de la matriz
        self.usar_restricciones_checkbox = QCheckBox(
            "☑️ Personalizar disponibilidad (modificar matriz anterior)"
        )
        self.usar_restricciones_checkbox.setStyleSheet(
            styles.STYLE_LABEL_FIELD + " font-weight: bold;"
        )
        self.usar_restricciones_checkbox.setChecked(False)  # Desactivado por defecto
        self.usar_restricciones_checkbox.setAccessibleName(
            "Activar personalización de disponibilidad del profesor"
        )
        main_layout.addWidget(self.usar_restricciones_checkbox)

        self.setLayout(main_layout)

    def _crear_separador(self) -> QWidget:
        """Crear línea separadora visual."""
        separator = QWidget()
        separator.setFixedHeight(2)
        separator.setStyleSheet(f"background-color: {TEXT_SECONDARY};")
        return separator

    def _crear_seccion_fechas(self) -> QVBoxLayout:
        """Crear sección de fechas mutuamente excluyentes."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Label de sección
        label_seccion = QLabel("📅 <b>Periodo de Guardias:</b>")
        label_seccion.setObjectName("fieldLabel")
        layout.addWidget(label_seccion)

        # Fecha de inicio
        layout_fecha_inicio = QHBoxLayout()
        self.usar_fecha_inicio_checkbox = QCheckBox("Desde:")
        self.usar_fecha_inicio_checkbox.setObjectName("fieldLabel")
        self.usar_fecha_inicio_checkbox.setFixedWidth(80)
        self.usar_fecha_inicio_checkbox.setAccessibleName("Activar fecha de inicio de guardias")
        layout_fecha_inicio.addWidget(self.usar_fecha_inicio_checkbox)

        self.fecha_inicio_guardias_input = QDateEdit()
        self.fecha_inicio_guardias_input.setCalendarPopup(True)
        self.fecha_inicio_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_guardias_input.setMaximumWidth(150)
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_inicio_guardias_input.setEnabled(False)
        self.fecha_inicio_guardias_input.setAccessibleName("Fecha de inicio de disponibilidad para guardias")
        layout_fecha_inicio.addWidget(self.fecha_inicio_guardias_input)
        layout_fecha_inicio.addStretch()
        layout.addLayout(layout_fecha_inicio)

        # Fecha de fin
        layout_fecha_fin = QHBoxLayout()
        self.usar_fecha_fin_checkbox = QCheckBox("Hasta:")
        self.usar_fecha_fin_checkbox.setObjectName("fieldLabel")
        self.usar_fecha_fin_checkbox.setFixedWidth(80)
        self.usar_fecha_fin_checkbox.setAccessibleName("Activar fecha de fin de guardias")
        layout_fecha_fin.addWidget(self.usar_fecha_fin_checkbox)

        self.fecha_fin_guardias_input = QDateEdit()
        self.fecha_fin_guardias_input.setCalendarPopup(True)
        self.fecha_fin_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_guardias_input.setMaximumWidth(150)
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setEnabled(False)
        self.fecha_fin_guardias_input.setAccessibleName("Fecha de fin de disponibilidad para guardias")
        layout_fecha_fin.addWidget(self.fecha_fin_guardias_input)
        layout_fecha_fin.addStretch()
        layout.addLayout(layout_fecha_fin)

        return layout

    def _crear_seccion_zona_preferida(self) -> QVBoxLayout:
        """Crear sección de zona preferida."""
        layout = QVBoxLayout()
        layout.setSpacing(4)  # Reducido de 6 a 4

        # Label de sección
        label_seccion = QLabel("🏫 <b>Zona Preferida:</b>")
        label_seccion.setObjectName("fieldLabel")
        layout.addWidget(label_seccion)

        # Combo de zonas
        self.zona_preferida_combo = QComboBox()
        self.zona_preferida_combo.setToolTip(
            "Selecciona la zona preferida del profesor para asignar guardias"
        )
        self.zona_preferida_combo.setAccessibleName("Zona preferida del profesor para guardias")
        layout.addWidget(self.zona_preferida_combo)

        return layout

    def _on_semana_changed(self):
        """Sincroniza el estado interno desde la rejilla visual."""
        self.restricciones_dias = self.semana_widget.get_restricciones_dias()
        self.restricciones_changed.emit()

    def _conectar_senales(self):
        """Conectar señales de los campos."""
        self.usar_fecha_inicio_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_fecha_fin_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        self.usar_restricciones_checkbox.stateChanged.connect(self._toggle_panel_restricciones)

        # Señales de cambio
        self.fecha_inicio_guardias_input.dateChanged.connect(self.restricciones_changed.emit)
        self.fecha_fin_guardias_input.dateChanged.connect(self.restricciones_changed.emit)

    def _toggle_fechas_guardias(self):
        """Controlar exclusividad mutua entre fecha inicio y fin."""
        sender = self.sender()

        if sender == self.usar_fecha_inicio_checkbox:
            if self.usar_fecha_inicio_checkbox.isChecked():
                self.fecha_inicio_guardias_input.setEnabled(True)
                self.usar_fecha_fin_checkbox.blockSignals(True)
                self.usar_fecha_fin_checkbox.setChecked(False)
                self.usar_fecha_fin_checkbox.blockSignals(False)
                self.fecha_fin_guardias_input.setEnabled(False)
            else:
                self.fecha_inicio_guardias_input.setEnabled(False)

        elif sender == self.usar_fecha_fin_checkbox:
            if self.usar_fecha_fin_checkbox.isChecked():
                self.fecha_fin_guardias_input.setEnabled(True)
                self.usar_fecha_inicio_checkbox.blockSignals(True)
                self.usar_fecha_inicio_checkbox.setChecked(False)
                self.usar_fecha_inicio_checkbox.blockSignals(False)
                self.fecha_inicio_guardias_input.setEnabled(False)
            else:
                self.fecha_fin_guardias_input.setEnabled(False)

        self.restricciones_changed.emit()

    def _toggle_panel_restricciones(self):
        """Activar/desactivar EDICIÓN del panel de restricciones."""
        is_checked = self.usar_restricciones_checkbox.isChecked()
        self.semana_widget.setEnabled(is_checked)
        self.restricciones_changed.emit()


    def _actualizar_tabla(self):
        """Sincronizar la rejilla visual con el estado interno."""
        self.semana_widget.set_restricciones_dias(self.restricciones_dias)

    def _obtener_recreos_por_defecto(self, turno: str) -> Dict[int, List[int]]:
        """
        Obtener la configuración de recreos por defecto según el turno.

        Args:
            turno: Turno del profesor ('Mañana', 'Tarde', 'Mixto')

        Returns:
            Diccionario con los recreos por defecto para cada día
        """
        turno_lower = turno.lower()
        recreos_defecto = {}

        for dia in range(5):
            if turno_lower == "mañana":
                recreos_defecto[dia] = [1, 2]
            elif turno_lower == "tarde":
                recreos_defecto[dia] = [3, 4]
            elif turno_lower == "mixto":
                recreos_defecto[dia] = [1, 2, 3, 4]
            else:
                recreos_defecto[dia] = []

        return recreos_defecto

    def _son_restricciones_personalizadas(
        self, restricciones: Dict[int, List[int]], recreos_defecto: Dict[int, List[int]]
    ) -> bool:
        """
        Verificar si las restricciones son diferentes a las del turno por defecto.

        Args:
            restricciones: Restricciones actuales del profesor
            recreos_defecto: Recreos por defecto según turno

        Returns:
            True si hay diferencias (personalizadas), False si son iguales al defecto
        """
        # Si no hay restricciones, no es personalizado
        if not restricciones:
            return False

        # Si no tienen el mismo número de días, es personalizado
        if len(restricciones) != len(recreos_defecto):
            return True

        # Comparar día por día
        for dia in range(5):
            restriccion_dia = sorted(restricciones.get(dia, []))
            defecto_dia = sorted(recreos_defecto.get(dia, []))

            if restriccion_dia != defecto_dia:
                return True  # Hay diferencias

        return False  # Son iguales

    def preseleccionar_segun_turno(self, turno: str):
        """Pre-seleccionar recreos según el turno del profesor."""
        turno_lower = turno.lower()
        self.restricciones_dias.clear()
        for dia in range(5):
            if turno_lower == "mañana":
                self.restricciones_dias[dia] = [1, 2]
            elif turno_lower == "tarde":
                self.restricciones_dias[dia] = [3, 4]
            elif turno_lower == "mixto":
                self.restricciones_dias[dia] = [1, 2, 3, 4]
        self._actualizar_tabla()

    # ========== Getters / Setters ==========

    def get_fecha_inicio(self) -> Optional[date]:
        """Obtener fecha de inicio de guardias."""
        if self.usar_fecha_inicio_checkbox.isChecked():
            qdate = self.fecha_inicio_guardias_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_inicio(self, fecha: Optional[date]):
        """Establecer fecha de inicio de guardias."""
        if fecha:
            self.usar_fecha_inicio_checkbox.setChecked(True)
            self.fecha_inicio_guardias_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_inicio_checkbox.setChecked(False)

    def get_fecha_fin(self) -> Optional[date]:
        """Obtener fecha de fin de guardias."""
        if self.usar_fecha_fin_checkbox.isChecked():
            qdate = self.fecha_fin_guardias_input.date()
            return date(qdate.year(), qdate.month(), qdate.day())
        return None

    def set_fecha_fin(self, fecha: Optional[date]):
        """Establecer fecha de fin de guardias."""
        if fecha:
            self.usar_fecha_fin_checkbox.setChecked(True)
            self.fecha_fin_guardias_input.setDate(QDate(fecha.year, fecha.month, fecha.day))
        else:
            self.usar_fecha_fin_checkbox.setChecked(False)

    def get_usar_restricciones(self) -> bool:
        """Verificar si se usan restricciones personalizadas."""
        return self.usar_restricciones_checkbox.isChecked()

    def set_usar_restricciones(self, usar: bool):
        """Establecer si se usan restricciones personalizadas."""
        self.usar_restricciones_checkbox.setChecked(usar)

    def get_recreos_permitidos_json(self) -> str:
        """
        Obtener recreos permitidos como JSON.

        Returns:
            JSON string con formato {"0": [1, 2], "1": [1, 2, 4]}
        """
        if not self.restricciones_dias:
            return ""

        # Convertir claves a string para JSON
        resultado = {str(dia): recreos for dia, recreos in self.restricciones_dias.items()}
        return json.dumps(resultado)

    def set_recreos_permitidos_json(self, json_str):
        """
        Cargar recreos permitidos desde JSON.

        Args:
            json_str: JSON string con formato {"0": [1, 2]} o diccionario
        """
        self.restricciones_dias.clear()

        # Solo retornar si es None o string vacía (dict vacío {} es válido)
        if json_str is None or (isinstance(json_str, str) and not json_str):
            self._actualizar_tabla()
            return

        try:
            # Si ya es un diccionario, usarlo directamente (incluso si está vacío {})
            if isinstance(json_str, dict):
                datos = json_str
            # Si ya es una lista plana [1,2,3], convertir a dict aplicando a todos los días
            elif isinstance(json_str, list):
                datos = {str(d): json_str for d in range(5)}
            # Si es string, parsearlo
            elif isinstance(json_str, str):
                datos = json.loads(json_str)
                # El JSON puede haberse decodificado como lista plana
                if isinstance(datos, list):
                    datos = {str(d): datos for d in range(5)}
            else:
                self._actualizar_tabla()
                return

            # Cargar datos (si datos está vacío {}, no entra al loop pero es válido)
            for dia_str, recreos in datos.items():
                try:
                    dia_int = int(dia_str)
                    if 0 <= dia_int < 5 and isinstance(recreos, list):
                        self.restricciones_dias[dia_int] = recreos
                except (ValueError, TypeError):
                    continue

            # ✅ IMPORTANTE: Actualizar tabla SIEMPRE después de cargar datos
            self._actualizar_tabla()

        except (json.JSONDecodeError, TypeError, ValueError):
            pass  # Ignorar errores de formato

    def get_zona_preferida_id(self) -> Optional[int]:
        """Obtener ID de zona preferida seleccionada."""
        zona_id = self.zona_preferida_combo.currentData()
        return zona_id if zona_id and zona_id > 0 else None

    def set_zona_preferida_id(self, zona_id: Optional[int]):
        """Establecer zona preferida por ID."""
        if zona_id is None:
            self.zona_preferida_combo.setCurrentIndex(0)
        else:
            for i in range(self.zona_preferida_combo.count()):
                if self.zona_preferida_combo.itemData(i) == zona_id:
                    self.zona_preferida_combo.setCurrentIndex(i)
                    break

    def cargar_zonas(self, zonas: list):
        """Cargar lista de zonas en el combo."""
        self.zona_preferida_combo.clear()
        self.zona_preferida_combo.addItem("Sin preferencia", 0)
        for zona_id, nombre in zonas:
            self.zona_preferida_combo.addItem(nombre, zona_id)

    def get_dias_permitidos(self) -> Optional[List[int]]:
        """
        Obtener lista de días permitidos.

        Returns:
            Lista con índices de días (0-4) que tienen restricciones, o None si no hay
        """
        if not self.restricciones_dias:
            return None
        return list(self.restricciones_dias.keys())

    def get_datos(self) -> dict:
        """
        Obtener todos los datos del widget.

        IMPORTANTE: Solo devuelve recreos_permitidos si el checkbox está ACTIVADO.
        Si está desactivado, la matriz es solo visual (según turno por defecto).
        """
        # Determinar días permitidos y recreos
        dias_permitidos = None
        recreos_json = ""

        # SOLO guardar restricciones si el checkbox está activado
        if self.get_usar_restricciones() and self.restricciones_dias:
            dias_permitidos = sorted(self.restricciones_dias.keys())
            recreos_json = self.get_recreos_permitidos_json()

        return {
            "fecha_inicio": self.get_fecha_inicio(),
            "fecha_fin": self.get_fecha_fin(),
            "zona_preferida_id": self.get_zona_preferida_id(),
            "usar_restricciones": self.get_usar_restricciones(),
            "recreos_permitidos": recreos_json,
            "dias_permitidos": dias_permitidos,
        }

    def set_datos(self, datos: dict):
        """
        Establecer todos los datos del widget.

        Siempre carga la matriz desde la BD. Solo activa el checkbox si las restricciones
        guardadas SON DIFERENTES al turno por defecto actual.
        """
        if "fecha_inicio" in datos:
            self.set_fecha_inicio(datos["fecha_inicio"])
        if "fecha_fin" in datos:
            self.set_fecha_fin(datos["fecha_fin"])
        if "zona_preferida_id" in datos:
            self.set_zona_preferida_id(datos["zona_preferida_id"])

        # Obtener turno actual
        turno_actual = datos.get("turno", "Mañana")

        # Calcular recreos por defecto según turno
        recreos_por_defecto = self._obtener_recreos_por_defecto(turno_actual)

        # ✅ SIEMPRE cargar las restricciones guardadas en la BD
        if "recreos_permitidos" in datos and datos["recreos_permitidos"] is not None:
            # Cargar restricciones desde BD (aunque sea dict vacío {})
            self.set_recreos_permitidos_json(datos["recreos_permitidos"])

            # ✅ Verificar si son DIFERENTES al turno por defecto
            son_personalizadas = self._son_restricciones_personalizadas(
                self.restricciones_dias, recreos_por_defecto
            )

            # ✅ Solo activar checkbox si fueron EDITADAS (diferentes al defecto)
            self.set_usar_restricciones(son_personalizadas)
        else:
            # ✅ Si no hay datos en BD (None), usar valores por defecto según turno
            self.set_usar_restricciones(False)
            self.preseleccionar_segun_turno(turno_actual)

    def limpiar(self):
        """Limpiar todos los campos del widget (estado inicial)."""
        self.usar_fecha_inicio_checkbox.setChecked(False)
        self.usar_fecha_fin_checkbox.setChecked(False)
        self.usar_restricciones_checkbox.setChecked(False)
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.zona_preferida_combo.setCurrentIndex(0)
        self.restricciones_dias.clear()
        self._actualizar_tabla()

    def validar(self) -> Tuple[bool, str]:
        """
        Validar los datos del widget.

        SOLO valida restricciones si el checkbox está activado.
        """
        # Validar exclusividad de fechas
        if self.usar_fecha_inicio_checkbox.isChecked() and self.usar_fecha_fin_checkbox.isChecked():
            return False, "No se pueden usar fecha de inicio y fin simultáneamente"

        # Validar restricciones SOLO si el checkbox está activo
        if self.get_usar_restricciones():
            if not self.restricciones_dias:
                return (
                    False,
                    "Si activa restricciones de horario, debe configurar al menos un día",
                )

            # Verificar que cada día tenga al menos un recreo
            for dia, recreos in self.restricciones_dias.items():
                if not recreos:
                    dia_nombre = self.DIAS_SEMANA[dia]
                    return (False, f"El {dia_nombre} debe tener al menos un recreo disponible")

        return True, ""
