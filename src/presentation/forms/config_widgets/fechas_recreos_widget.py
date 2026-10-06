"""
Widget para configuración de fechas y recreos.

Encapsula la lógica de configuración de:
- Fechas del curso (inicio/fin) e inicio del reparto oficial de guardias
- Recreos de mañana (2 recreos) y de tarde (2 recreos). Cada turno se puede
  quitar entero con la casilla de su grupo: hay centros sin guardias de mañana
  o sin guardias de tarde, y sus recreos dejaban la mitad de los huecos sin
  nadie que pudiera cubrirlos (2026-10-06).
"""

from datetime import date

from PyQt6.QtCore import QDate, QTime, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QTimeEdit,
    QVBoxLayout,
)

from presentation.theme import legacy_styles as styles
from presentation.theme.tokens import Spacing
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
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Configura la interfaz del widget."""
        # Layout horizontal para fechas y recreos
        main_layout = QHBoxLayout()
        main_layout.setSpacing(Spacing.SM)
        main_layout.setContentsMargins(Spacing.SM, Spacing.SM, Spacing.SM, Spacing.SM)

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
        layout = QVBoxLayout()
        layout.setSpacing(1)
        layout.setContentsMargins(6, 6, 6, 6)

        # Fecha inicio
        label_inicio = QLabel("Inicio:")
        label_inicio.setObjectName("smallFieldLabel")
        layout.addWidget(label_inicio)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setAccessibleName("Campo fecha de inicio del curso")
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.dateChanged.connect(self.config_changed.emit)
        layout.addWidget(self.fecha_inicio_input)

        # Fecha fin
        label_fin = QLabel("Fin:")
        label_fin.setObjectName("smallFieldLabel")
        layout.addWidget(label_fin)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setAccessibleName("Campo fecha de fin del curso")
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.fecha_fin_input.dateChanged.connect(self.config_changed.emit)
        layout.addWidget(self.fecha_fin_input)

        # Inicio del reparto oficial (antes sólo hay guardias voluntarias)
        label_reparto = QLabel("Inicio del reparto oficial de guardias:")
        label_reparto.setObjectName("smallFieldLabel")
        layout.addWidget(label_reparto)

        self.reparto_igual_inicio_check = QCheckBox("Igual que el inicio de curso")
        self.reparto_igual_inicio_check.setAccessibleName(
            "Reparto oficial desde el inicio de curso"
        )
        self.reparto_igual_inicio_check.setChecked(True)
        self.reparto_igual_inicio_check.setToolTip(
            "Desmárcala si las primeras semanas las cubren voluntarios: las guardias\n"
            "se generan y se cuentan desde la fecha indicada, y las voluntarias de cada\n"
            "profesor se descuentan de su parte del curso."
        )
        fila_reparto = QHBoxLayout()
        fila_reparto.setSpacing(Spacing.SM)
        fila_reparto.addWidget(self.reparto_igual_inicio_check)

        self.fecha_reparto_input = QDateEdit()
        self.fecha_reparto_input.setAccessibleName("Campo fecha de inicio del reparto oficial")
        self.fecha_reparto_input.setCalendarPopup(True)
        self.fecha_reparto_input.setDate(self.fecha_inicio_input.date())
        self.fecha_reparto_input.setEnabled(False)
        self.fecha_reparto_input.dateChanged.connect(self.config_changed.emit)
        fila_reparto.addWidget(self.fecha_reparto_input)
        layout.addLayout(fila_reparto)

        self.reparto_igual_inicio_check.toggled.connect(self._on_reparto_igual_toggled)

        # Las tres fechas con el mismo estilo
        estilo_fecha = styles.STYLE_INPUT + "padding: 4px;"
        for campo in (self.fecha_inicio_input, self.fecha_fin_input, self.fecha_reparto_input):
            campo.setStyleSheet(estilo_fecha)

        grupo.setLayout(layout)
        return grupo

    def _on_reparto_igual_toggled(self, igual: bool) -> None:
        self.fecha_reparto_input.setEnabled(not igual)
        if not igual and self.fecha_reparto_input.date() < self.fecha_inicio_input.date():
            self.fecha_reparto_input.setDate(self.fecha_inicio_input.date())
        self.config_changed.emit()

    def get_fecha_reparto_oficial(self):
        """Inicio del reparto oficial, o None si es igual que el inicio de curso."""
        if self.reparto_igual_inicio_check.isChecked():
            return None
        return self.fecha_reparto_input.date().toPyDate()

    def set_fecha_reparto_oficial(self, fecha) -> None:
        """Carga el inicio del reparto oficial (None = igual que el inicio de curso)."""
        if not isinstance(fecha, date):
            fecha = None
        self.reparto_igual_inicio_check.blockSignals(True)
        self.reparto_igual_inicio_check.setChecked(fecha is None)
        self.reparto_igual_inicio_check.blockSignals(False)
        self.fecha_reparto_input.setEnabled(fecha is not None)
        destino = fecha if fecha is not None else self.fecha_inicio_input.date().toPyDate()
        self.fecha_reparto_input.setDate(QDate(destino.year, destino.month, destino.day))

    def _crear_grupo_recreos_manana(self) -> QGroupBox:
        """Crea el grupo de recreos de mañana; desmarcado, no hay guardias de mañana."""
        grupo = QGroupBox("Hay guardias de mañana")
        grupo.setCheckable(True)
        grupo.setChecked(True)
        grupo.setAccessibleName("Hay guardias de mañana")
        grupo.setToolTip("Desmárcalo si en el centro no hay guardias de patio por la mañana")
        grupo.toggled.connect(self.config_changed.emit)
        self.grupo_manana = grupo
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setObjectName("smallFieldLabel")
        col1.addWidget(label_r1)

        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setAccessibleName("Campo hora recreo 1 de mañana")
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.recreo1_manana_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo1_manana_input.timeChanged.connect(self.config_changed.emit)
        col1.addWidget(self.recreo1_manana_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setObjectName("smallFieldLabel")
        col2.addWidget(label_r2)

        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setAccessibleName("Campo hora recreo 2 de mañana")
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.recreo2_manana_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo2_manana_input.timeChanged.connect(self.config_changed.emit)
        col2.addWidget(self.recreo2_manana_input)
        layout.addLayout(col2)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_tarde(self) -> QGroupBox:
        """Crea el grupo de recreos de tarde; desmarcado, no hay guardias de tarde."""
        grupo = QGroupBox("Hay guardias de tarde")
        grupo.setCheckable(True)
        grupo.setChecked(True)
        grupo.setAccessibleName("Hay guardias de tarde")
        grupo.setToolTip("Desmárcalo si en el centro no hay guardias de patio por la tarde")
        grupo.toggled.connect(self.config_changed.emit)
        self.grupo_tarde = grupo
        layout = QHBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(6, 6, 6, 6)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(2)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setObjectName("smallFieldLabel")
        col1.addWidget(label_r1)

        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setAccessibleName("Campo hora recreo 1 de tarde")
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.recreo1_tarde_input.setStyleSheet(styles.STYLE_INPUT + "padding: 4px;")
        self.recreo1_tarde_input.timeChanged.connect(self.config_changed.emit)
        col1.addWidget(self.recreo1_tarde_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(2)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setObjectName("smallFieldLabel")
        col2.addWidget(label_r2)

        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setAccessibleName("Campo hora recreo 2 de tarde")
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

    def hay_recreos_manana(self) -> bool:
        """Si el centro tiene guardias de mañana (casilla del grupo)."""
        return self.grupo_manana.isChecked()

    def hay_recreos_tarde(self) -> bool:
        """Si el centro tiene guardias de tarde (casilla del grupo)."""
        return self.grupo_tarde.isChecked()

    def set_turnos_con_recreos(self, manana: bool, tarde: bool) -> None:
        """Marca qué turnos tienen recreos, sin avisar de cambios pendientes."""
        for grupo, valor in ((self.grupo_manana, manana), (self.grupo_tarde, tarde)):
            grupo.blockSignals(True)
            grupo.setChecked(bool(valor))
            grupo.blockSignals(False)

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

        if not self.reparto_igual_inicio_check.isChecked():
            fecha_reparto = self.fecha_reparto_input.date()
            if fecha_reparto < fecha_inicio:
                return (
                    False,
                    "El inicio del reparto oficial no puede ser anterior al inicio de curso",
                )
            if fecha_reparto > fecha_fin:
                return (
                    False,
                    "El inicio del reparto oficial no puede ser posterior al fin de curso",
                )

        manana = self.hay_recreos_manana()
        tarde = self.hay_recreos_tarde()
        if not manana and not tarde:
            return (
                False,
                "Marca al menos un turno con guardias (mañana o tarde): "
                "sin recreos no hay guardias que repartir",
            )

        # Las horas solo se comprueban en los turnos que tienen guardias.
        recreo1_manana = self.recreo1_manana_input.time()
        recreo2_manana = self.recreo2_manana_input.time()
        if manana and recreo1_manana >= recreo2_manana:
            return (
                False,
                "El recreo 1 de mañana debe ser anterior al recreo 2 de mañana",
            )

        recreo1_tarde = self.recreo1_tarde_input.time()
        recreo2_tarde = self.recreo2_tarde_input.time()
        if tarde and recreo1_tarde >= recreo2_tarde:
            return (
                False,
                "El recreo 1 de tarde debe ser anterior al recreo 2 de tarde",
            )

        if manana and tarde and recreo1_tarde <= recreo2_manana:
            return (
                False,
                "Los recreos de tarde deben ser posteriores a los de mañana",
            )

        return True, ""
