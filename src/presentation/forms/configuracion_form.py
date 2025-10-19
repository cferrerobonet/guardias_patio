"""
Configuración Form - Refactorizado.

Form para gestionar la configuración del curso escolar.
Sigue el patrón MVP usando Use Cases.
"""

from PyQt6.QtCore import QDate, QTime
from PyQt6.QtWidgets import (
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
)
from sqlalchemy.orm import Session

import ui_styles as styles
from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
from application.use_cases.configuracion import (
    ActualizarConfiguracionUseCase,
    ObtenerConfiguracionUseCase,
)
from core.exceptions import NotFoundError
from presentation.forms.base_form import BaseForm


class ConfiguracionForm(BaseForm):
    """
    Formulario para gestionar la configuración del curso.

    Permite configurar:
    - Fechas del curso
    - Horarios de recreos
    - Ajustes de tutores/no tutores
    - Festivos y días no lectivos
    - Configuración avanzada
    """

    def __init__(self, session: Session, parent=None):
        """
        Inicializa el formulario de configuración.

        Args:
            session: Sesión de SQLAlchemy
            parent: Widget padre
        """
        super().__init__(session, parent)

        # Inicializar Use Cases
        self.obtener_config_uc = ObtenerConfiguracionUseCase(session)
        self.actualizar_config_uc = ActualizarConfiguracionUseCase(session)

        # Configurar UI
        self.setup_ui()

        # Cargar configuración existente si hay
        self.cargar_configuracion()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Configuración del Curso")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título principal
        titulo = QLabel("⚙️ CONFIGURACIÓN DEL CURSO ESCOLAR")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        layout.addWidget(titulo)

        # ===== GRUPO: Fechas del Curso =====
        grupo_fechas = self._crear_grupo_fechas()
        layout.addWidget(grupo_fechas)

        # ===== GRUPO: Recreos de Mañana =====
        grupo_manana = self._crear_grupo_recreos_manana()
        layout.addWidget(grupo_manana)

        # ===== GRUPO: Recreos de Tarde =====
        grupo_tarde = self._crear_grupo_recreos_tarde()
        layout.addWidget(grupo_tarde)

        # ===== GRUPO: Ajustes Adicionales =====
        grupo_ajustes = self._crear_grupo_ajustes()
        layout.addWidget(grupo_ajustes)

        # ===== GRUPO: Festivos =====
        grupo_festivos = self._crear_grupo_festivos()
        layout.addWidget(grupo_festivos)

        # ===== GRUPO: Avanzado =====
        grupo_avanzado = self._crear_grupo_avanzado()
        layout.addWidget(grupo_avanzado)

        # Botones
        btn_layout = self._crear_botones()
        layout.addLayout(btn_layout)

        # Espacio flexible
        layout.addStretch()

        self.setLayout(layout)

    def _crear_grupo_fechas(self) -> QGroupBox:
        """Crea el grupo de fechas del curso."""
        grupo = QGroupBox("📅 Fechas del Curso")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Fecha inicio
        label_inicio = QLabel("Fecha de inicio del curso:")
        label_inicio.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_inicio)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_input.setMaximumWidth(200)
        layout.addWidget(self.fecha_inicio_input)

        # Fecha fin
        label_fin = QLabel("Fecha de fin del curso:")
        label_fin.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_fin)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_input.setMaximumWidth(200)
        layout.addWidget(self.fecha_fin_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_manana(self) -> QGroupBox:
        """Crea el grupo de recreos de mañana."""
        grupo = QGroupBox("☀️ Recreos de Mañana")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(5)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col1.addWidget(label_r1)

        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.recreo1_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo1_manana_input.setMaximumWidth(120)
        col1.addWidget(self.recreo1_manana_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(5)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col2.addWidget(label_r2)

        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.recreo2_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo2_manana_input.setMaximumWidth(120)
        col2.addWidget(self.recreo2_manana_input)
        layout.addLayout(col2)

        layout.addStretch()
        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_recreos_tarde(self) -> QGroupBox:
        """Crea el grupo de recreos de tarde."""
        grupo = QGroupBox("🌙 Recreos de Tarde (opcional)")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Recreo 1
        col1 = QVBoxLayout()
        col1.setSpacing(5)
        label_r1 = QLabel("Recreo 1:")
        label_r1.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col1.addWidget(label_r1)

        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.recreo1_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo1_tarde_input.setMaximumWidth(120)
        col1.addWidget(self.recreo1_tarde_input)
        layout.addLayout(col1)

        # Recreo 2
        col2 = QVBoxLayout()
        col2.setSpacing(5)
        label_r2 = QLabel("Recreo 2:")
        label_r2.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col2.addWidget(label_r2)

        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setTime(QTime(17, 0))
        self.recreo2_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo2_tarde_input.setMaximumWidth(120)
        col2.addWidget(self.recreo2_tarde_input)
        layout.addLayout(col2)

        layout.addStretch()
        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_ajustes(self) -> QGroupBox:
        """Crea el grupo de ajustes adicionales."""
        grupo = QGroupBox("🔧 Ajustes Adicionales")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # Multiplicador tutores
        col1 = QVBoxLayout()
        col1.setSpacing(5)
        label_tutores = QLabel("Multiplicador tutores:")
        label_tutores.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col1.addWidget(label_tutores)

        self.ajuste_tutores_input = QLineEdit()
        self.ajuste_tutores_input.setPlaceholderText("0.90")
        self.ajuste_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        self.ajuste_tutores_input.setMaximumWidth(100)
        col1.addWidget(self.ajuste_tutores_input)
        layout.addLayout(col1)

        # Multiplicador no tutores
        col2 = QVBoxLayout()
        col2.setSpacing(5)
        label_no_tutores = QLabel("Multiplicador no tutores:")
        label_no_tutores.setStyleSheet(styles.STYLE_LABEL_FIELD)
        col2.addWidget(label_no_tutores)

        self.ajuste_no_tutores_input = QLineEdit()
        self.ajuste_no_tutores_input.setPlaceholderText("1.00")
        self.ajuste_no_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        self.ajuste_no_tutores_input.setMaximumWidth(100)
        col2.addWidget(self.ajuste_no_tutores_input)
        layout.addLayout(col2)

        layout.addStretch()
        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_festivos(self) -> QGroupBox:
        """Crea el grupo de festivos."""
        grupo = QGroupBox("🎉 Festivos y Días No Lectivos")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        label_auto = QLabel("Aplicar festivos automáticos (1 sí / 0 no):")
        label_auto.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_auto)

        self.festivos_auto_input = QLineEdit()
        self.festivos_auto_input.setPlaceholderText("1")
        self.festivos_auto_input.setStyleSheet(styles.STYLE_INPUT)
        self.festivos_auto_input.setMaximumWidth(100)
        layout.addWidget(self.festivos_auto_input)

        label_custom = QLabel("Días no lectivos personalizados (YYYY-MM-DD, separados por coma):")
        label_custom.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_custom)

        self.no_lectivos_input = QLineEdit()
        self.no_lectivos_input.setPlaceholderText("2025-10-09, 2025-10-12")
        self.no_lectivos_input.setStyleSheet(styles.STYLE_INPUT)
        self.no_lectivos_input.setMaximumWidth(500)
        layout.addWidget(self.no_lectivos_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_grupo_avanzado(self) -> QGroupBox:
        """Crea el grupo de configuración avanzada."""
        grupo = QGroupBox("🔬 Configuración Avanzada (opcional)")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        label_recreos = QLabel("Recreos configurables JSON (lista de objetos):")
        label_recreos.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout.addWidget(label_recreos)

        self.recreos_config_input = QLineEdit()
        self.recreos_config_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreos_config_input.setMaximumWidth(500)
        layout.addWidget(self.recreos_config_input)

        grupo.setLayout(layout)
        return grupo

    def _crear_botones(self) -> QHBoxLayout:
        """Crea los botones de acción."""
        layout = QHBoxLayout()
        layout.setSpacing(10)

        self.save_btn = QPushButton("💾 Guardar Configuración")
        self.save_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.save_btn.clicked.connect(self.guardar_configuracion)

        self.load_btn = QPushButton("🔄 Cargar Actual")
        self.load_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.load_btn.clicked.connect(self.cargar_configuracion)

        layout.addWidget(self.save_btn)
        layout.addWidget(self.load_btn)
        layout.addStretch()

        return layout

    def guardar_configuracion(self) -> None:
        """
        Guarda la configuración usando el Use Case.

        Valida los datos y ejecuta ActualizarConfiguracionUseCase.
        """
        try:
            # Validar formulario
            es_valido, mensaje = self.validar_formulario()
            if not es_valido:
                self.mostrar_advertencia("Validación", mensaje)
                return

            # Crear DTO
            dto = ActualizarConfiguracionDTO(
                fecha_inicio_curso=self.fecha_inicio_input.date().toPyDate(),
                fecha_fin_curso=self.fecha_fin_input.date().toPyDate(),
                hora_recreo1_manana=self.recreo1_manana_input.time().toPyTime(),
                hora_recreo2_manana=self.recreo2_manana_input.time().toPyTime(),
                hora_recreo1_tarde=self.recreo1_tarde_input.time().toPyTime(),
                hora_recreo2_tarde=self.recreo2_tarde_input.time().toPyTime(),
                ajuste_tutores=float(self.ajuste_tutores_input.text() or 1.0),
                ajuste_no_tutores=float(self.ajuste_no_tutores_input.text() or 1.0),
                activar_festivos_automaticos=(
                    (self.festivos_auto_input.text() or "1").strip() in ("1", "true", "True")
                ),
                dias_no_lectivos_personalizados=(self.no_lectivos_input.text() or "").strip(),
                recreos_config=(self.recreos_config_input.text() or "").strip()
            )

            # Ejecutar Use Case
            config = self.actualizar_config_uc.execute(dto)

            # Mostrar éxito
            self.mostrar_exito(
                "Configuración Guardada",
                f"La configuración del curso {config.fecha_inicio_curso} - "
                f"{config.fecha_fin_curso} ha sido guardada correctamente."
            )

        except Exception as e:
            self.manejar_excepcion(e, "guardar configuración")

    def cargar_configuracion(self) -> None:
        """
        Carga la configuración actual usando el Use Case.

        Si no existe configuración, muestra valores por defecto.
        """
        try:
            # Ejecutar Use Case
            config = self.obtener_config_uc.execute()

            # Cargar datos en el formulario
            self.fecha_inicio_input.setDate(QDate(config.fecha_inicio_curso))
            self.fecha_fin_input.setDate(QDate(config.fecha_fin_curso))
            self.recreo1_manana_input.setTime(QTime(config.hora_recreo1_manana))
            self.recreo2_manana_input.setTime(QTime(config.hora_recreo2_manana))

            if config.hora_recreo1_tarde:
                self.recreo1_tarde_input.setTime(QTime(config.hora_recreo1_tarde))
            if config.hora_recreo2_tarde:
                self.recreo2_tarde_input.setTime(QTime(config.hora_recreo2_tarde))

            self.ajuste_tutores_input.setText(str(config.ajuste_tutores))
            self.ajuste_no_tutores_input.setText(str(config.ajuste_no_tutores))
            self.festivos_auto_input.setText("1" if config.activar_festivos_automaticos else "0")
            self.no_lectivos_input.setText(config.dias_no_lectivos_personalizados or "")
            self.recreos_config_input.setText(config.recreos_config or "")

            self.logger.info("Configuración cargada correctamente")

        except NotFoundError:
            # No hay configuración, usar valores por defecto
            self.logger.info("No hay configuración guardada, usando valores por defecto")
        except Exception as e:
            self.manejar_excepcion(e, "cargar configuración")

    def limpiar_formulario(self) -> None:
        """Limpia el formulario (no usado en configuración)."""
        # No aplica para configuración ya que solo hay un registro
        pass

    def validar_formulario(self) -> tuple[bool, str]:
        """
        Valida los datos del formulario.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        # Validar fechas
        fecha_inicio = self.fecha_inicio_input.date().toPyDate()
        fecha_fin = self.fecha_fin_input.date().toPyDate()

        if fecha_fin <= fecha_inicio:
            return False, "La fecha de fin debe ser posterior a la fecha de inicio"

        # Validar ajustes
        try:
            ajuste_tutores = float(self.ajuste_tutores_input.text() or 1.0)
            ajuste_no_tutores = float(self.ajuste_no_tutores_input.text() or 1.0)

            if ajuste_tutores <= 0 or ajuste_tutores > 2:
                return False, "El ajuste de tutores debe estar entre 0 y 2"

            if ajuste_no_tutores <= 0 or ajuste_no_tutores > 2:
                return False, "El ajuste de no tutores debe estar entre 0 y 2"

        except ValueError:
            return False, "Los ajustes deben ser números válidos"

        return True, ""
