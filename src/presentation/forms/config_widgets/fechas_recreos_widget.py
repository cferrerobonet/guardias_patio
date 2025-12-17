"""
Widget para configuración de fechas y recreos.

Encapsula la lógica de configuración de:
- Fechas del curso (inicio/fin)
- Recreos de mañana (2 recreos)
- Recreos de tarde (2 recreos opcionales)
"""

import ui_styles as styles
from PyQt6.QtCore import QDate, QTime, pyqtSignal
from PyQt6.QtWidgets import (
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QVBoxLayout,
)
from utils import get_logger


class FechasRecreosWidget(QGroupBox):
    """
    Widget de configuración de fechas y recreos del curso.

    Gestiona las fechas de inicio/fin del curso y los horarios
    de los recreos de mañana y tarde.
    """

    # Señales
    config_changed = pyqtSignal()

    def __init__(self, parent=None):
        """
        Inicializa el widget de fechas y recreos.

        Args:
            parent: Widget padre
        """
        super().__init__("📅 Fechas y Recreos", parent)
        self.logger = get_logger(self.__class__.__name__)
        self.setStyleSheet(styles.STYLE_GROUPBOX)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del widget."""
        # Layout horizontal para fechas y recreos
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(8, 8, 8, 8)

        # GRUPO 1: Fechas del curso
        fechas_grupo = self._crear_grupo_fechas()
        main_layout.addWidget(fechas_grupo)

        # GRUPO 2: Recreos de mañana
        recreos_manana_grupo = self._crear_grupo_recreos_manana()
        main_layout.addWidget(recreos_manana_grupo)

        # GRUPO 3: Recreos de tarde
        recreos_tarde_grupo = self._crear_grupo_recreos_tarde()
        main_layout.addWidget(recreos_tarde_grupo)

        self.setLayout(main_layout)

    def _crear_grupo_fechas(self) -> QGroupBox:
        """Crea el grupo de fechas del curso."""
        grupo = QGroupBox("Fechas del Curso")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(6, 6, 6, 6)

        # Fecha inicio
        label_inicio = QLabel("Inicio:")
        label_inicio.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        layout.addWidget(label_inicio)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.fecha_inicio_input.dateChanged.connect(self.config_changed.emit)
        layout.addWidget(self.fecha_inicio_input)

        # Fecha fin
        label_fin = QLabel("Fin:")
        label_fin.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        layout.addWidget(label_fin)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.fecha_fin_input.dateChanged.connect(self.config_changed.emit)
        layout.addWidget(self.fecha_fin_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_manana(self) -> QGroupBox:
        """Crea el grupo de recreos de mañana."""
        grupo = QGroupBox("Recreos de Mañana")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        col1.addWidget(label_r1)

        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.recreo1_manana_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo1_manana_input.timeChanged.connect(self.config_changed.emit)
        col1.addWidget(self.recreo1_manana_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        col2.addWidget(label_r2)

        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.recreo2_manana_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo2_manana_input.timeChanged.connect(self.config_changed.emit)
        col2.addWidget(self.recreo2_manana_input)
        layout.addLayout(col2)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_tarde(self) -> QGroupBox:
        """Crea el grupo de recreos de tarde."""
        grupo = QGroupBox("🌙 Recreos de Tarde (opcional)")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        col1.addWidget(label_r1)

        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.recreo1_tarde_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo1_tarde_input.timeChanged.connect(self.config_changed.emit)
        col1.addWidget(self.recreo1_tarde_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD + "font-size: 10px;")
        col2.addWidget(label_r2)

        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setTime(QTime(17, 0))
        self.recreo2_tarde_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo2_tarde_input.timeChanged.connect(self.config_changed.emit)
        col2.addWidget(self.recreo2_tarde_input)
        layout.addLayout(col2)

        grupo.setLayout(layout)
        return grupo

    def get_fechas(self) -> dict:
        """
        Obtiene las fechas configuradas.

        Returns:
            dict: Diccionario con fecha_inicio y fecha_fin
        """
        return {
            "fecha_inicio": self.fecha_inicio_input.date().toPyDate(),
            "fecha_fin": self.fecha_fin_input.date().toPyDate(),
        }

    def get_recreos_manana(self) -> dict:
        """
        Obtiene los recreos de mañana configurados.

        Returns:
            dict: Diccionario con recreo1 y recreo2
        """
        return {
            "recreo1": self.recreo1_manana_input.time().toPyTime(),
            "recreo2": self.recreo2_manana_input.time().toPyTime(),
        }

    def get_recreos_tarde(self) -> dict:
        """
        Obtiene los recreos de tarde configurados.

        Returns:
            dict: Diccionario con recreo1 y recreo2
        """
        return {
            "recreo1": self.recreo1_tarde_input.time().toPyTime(),
            "recreo2": self.recreo2_tarde_input.time().toPyTime(),
        }

    def set_fechas(self, fecha_inicio, fecha_fin) -> None:
        """
        Establece las fechas del curso.

        Args:
            fecha_inicio: Fecha de inicio (date o QDate)
            fecha_fin: Fecha de fin (date o QDate)
        """
        if hasattr(fecha_inicio, "year"):  # Es un date de Python
            self.fecha_inicio_input.setDate(
                QDate(fecha_inicio.year, fecha_inicio.month, fecha_inicio.day)
            )
        else:
            self.fecha_inicio_input.setDate(fecha_inicio)

        if hasattr(fecha_fin, "year"):  # Es un date de Python
            self.fecha_fin_input.setDate(QDate(fecha_fin.year, fecha_fin.month, fecha_fin.day))
        else:
            self.fecha_fin_input.setDate(fecha_fin)

    def set_recreos_manana(self, recreo1, recreo2) -> None:
        """
        Establece los recreos de mañana.

        Args:
            recreo1: Hora del recreo 1 (time o QTime)
            recreo2: Hora del recreo 2 (time o QTime)
        """
        if hasattr(recreo1, "hour"):  # Es un time de Python
            self.recreo1_manana_input.setTime(QTime(recreo1.hour, recreo1.minute))
        else:
            self.recreo1_manana_input.setTime(recreo1)

        if hasattr(recreo2, "hour"):  # Es un time de Python
            self.recreo2_manana_input.setTime(QTime(recreo2.hour, recreo2.minute))
        else:
            self.recreo2_manana_input.setTime(recreo2)

    def set_recreos_tarde(self, recreo1, recreo2) -> None:
        """
        Establece los recreos de tarde.

        Args:
            recreo1: Hora del recreo 1 (time o QTime)
            recreo2: Hora del recreo 2 (time o QTime)
        """
        if hasattr(recreo1, "hour"):  # Es un time de Python
            self.recreo1_tarde_input.setTime(QTime(recreo1.hour, recreo1.minute))
        else:
            self.recreo1_tarde_input.setTime(recreo1)

        if hasattr(recreo2, "hour"):  # Es un time de Python
            self.recreo2_tarde_input.setTime(QTime(recreo2.hour, recreo2.minute))
        else:
            self.recreo2_tarde_input.setTime(recreo2)

    def validar(self) -> tuple[bool, str]:
        """
        Valida las fechas y recreos configurados.

        Returns:
            tuple[bool, str]: (es_valido, mensaje_error)
        """
        # Validar fechas
        fecha_inicio = self.fecha_inicio_input.date()
        fecha_fin = self.fecha_fin_input.date()

        if fecha_inicio >= fecha_fin:
            return False, "La fecha de inicio debe ser anterior a la fecha de fin"

        # Validar recreos de mañana
        recreo1_manana = self.recreo1_manana_input.time()
        recreo2_manana = self.recreo2_manana_input.time()

        if recreo1_manana >= recreo2_manana:
            return (
                False,
                "El recreo 1 de mañana debe ser anterior al recreo 2 de mañana",
            )

        # Validar recreos de tarde
        recreo1_tarde = self.recreo1_tarde_input.time()
        recreo2_tarde = self.recreo2_tarde_input.time()

        if recreo1_tarde >= recreo2_tarde:
            return (
                False,
                "El recreo 1 de tarde debe ser anterior al recreo 2 de tarde",
            )

        # Validar que recreos de tarde sean después de mañana
        if recreo1_tarde <= recreo2_manana:
            return (
                False,
                "Los recreos de tarde deben ser posteriores a los de mañana",
            )

        return True, ""
