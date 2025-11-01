"""
Widget para configurar y generar calendarios PDF.

Permite configurar opciones de generación de PDFs con diferentes modos:
- Mes específico o curso completo
- Todos los profesores o selección personalizada
"""

from datetime import datetime
from typing import List

import ui_styles as styles
from models.models import Profesor
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from presentation.themes.ccleaner_theme import TEXT_SECONDARY


class PdfExportWidget(QGroupBox):
    """Widget para configurar la exportación de calendarios PDF."""

    # Señal cuando se solicita generar PDFs
    generar_pdfs_solicitado = pyqtSignal()

    def __init__(self, session: Session, parent=None):
        """
        Inicializar el widget de exportación PDF.

        Args:
            session: Sesión de base de datos para cargar profesores
            parent: Widget padre
        """
        super().__init__("📄 GENERAR CALENDARIOS PDF", parent)
        self.session = session
        self.profesor_checkboxes: List[QCheckBox] = []

        self.setStyleSheet(styles.STYLE_GROUPBOX)
        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 20, 15, 15)

        # Información
        info = QLabel(
            "Genera calendarios individuales en PDF para profesores con sus guardias asignadas."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """
        )
        layout.addWidget(info)

        # Tipo de exportación
        layout.addLayout(self._crear_tipo_exportacion())

        # Controles de mes/año
        self.fecha_container = self._crear_controles_fecha()
        layout.addWidget(self.fecha_container)

        # Controles de curso completo
        self.curso_container = self._crear_controles_curso()
        layout.addWidget(self.curso_container)
        self.curso_container.hide()

        # Selección de profesores
        self.profesores_container = self._crear_seleccion_profesores()
        layout.addWidget(self.profesores_container)
        self.profesores_container.hide()

        # Botón de exportación
        self.exportar_pdf_btn = QPushButton("📄 Generar PDFs")
        self.exportar_pdf_btn.setMinimumHeight(40)
        self.exportar_pdf_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        layout.addWidget(self.exportar_pdf_btn)

        self.setLayout(layout)

    def _crear_tipo_exportacion(self) -> QVBoxLayout:
        """Crear controles para tipo de exportación."""
        tipo_layout = QVBoxLayout()
        tipo_layout.setSpacing(5)

        tipo_label = QLabel("📋 Tipo de exportación:")
        tipo_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        tipo_layout.addWidget(tipo_label)

        self.pdf_tipo_combo = QComboBox()
        self.pdf_tipo_combo.addItem("📅 Mes específico - Todos los profesores", "mes_todos")
        self.pdf_tipo_combo.addItem(
            "👤 Mes específico - Profesores seleccionados", "mes_seleccionados"
        )
        self.pdf_tipo_combo.addItem("📚 Curso completo - Todos los profesores", "curso_todos")
        self.pdf_tipo_combo.addItem(
            "📚 Curso completo - Profesores seleccionados", "curso_seleccionados"
        )
        self.pdf_tipo_combo.setStyleSheet(styles.STYLE_INPUT)
        tipo_layout.addWidget(self.pdf_tipo_combo)

        return tipo_layout

    def _crear_controles_fecha(self) -> QWidget:
        """Crear controles de mes y año."""
        container = QWidget()
        fecha_layout = QHBoxLayout(container)
        fecha_layout.setContentsMargins(0, 0, 0, 0)
        fecha_layout.setSpacing(10)

        # Mes
        mes_container = QVBoxLayout()
        mes_container.setSpacing(5)
        mes_label = QLabel("📅 Mes:")
        mes_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        mes_container.addWidget(mes_label)

        self.pdf_mes_combo = QComboBox()
        meses = [
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        self.pdf_mes_combo.addItems(meses)
        self.pdf_mes_combo.setCurrentIndex(datetime.now().month - 1)
        self.pdf_mes_combo.setStyleSheet(styles.STYLE_INPUT)
        mes_container.addWidget(self.pdf_mes_combo)
        fecha_layout.addLayout(mes_container, 2)

        # Año
        anio_container = QVBoxLayout()
        anio_container.setSpacing(5)
        anio_label = QLabel("📆 Año:")
        anio_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        anio_container.addWidget(anio_label)

        self.pdf_anio_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_anio_combo.addItem(str(anio))
        self.pdf_anio_combo.setCurrentIndex(1)  # Año actual
        self.pdf_anio_combo.setStyleSheet(styles.STYLE_INPUT)
        anio_container.addWidget(self.pdf_anio_combo)
        fecha_layout.addLayout(anio_container, 1)

        return container

    def _crear_controles_curso(self) -> QWidget:
        """Crear controles para curso completo."""
        container = QWidget()
        curso_layout = QVBoxLayout(container)
        curso_layout.setContentsMargins(0, 0, 0, 0)
        curso_layout.setSpacing(5)

        curso_label = QLabel("📚 Año de inicio del curso:")
        curso_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        curso_layout.addWidget(curso_label)

        self.pdf_curso_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_curso_combo.addItem(f"{anio}/{anio + 1}", anio)
        self.pdf_curso_combo.setCurrentIndex(1)
        self.pdf_curso_combo.setStyleSheet(styles.STYLE_INPUT)
        curso_layout.addWidget(self.pdf_curso_combo)

        curso_info = QLabel("ℹ️ Se generarán PDFs de Septiembre a Junio")
        curso_info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 10px;
            font-style: italic;
        """
        )
        curso_layout.addWidget(curso_info)

        return container

    def _crear_seleccion_profesores(self) -> QWidget:
        """Crear widget de selección de profesores."""
        container = QWidget()
        profesores_layout = QVBoxLayout(container)
        profesores_layout.setContentsMargins(0, 0, 0, 0)
        profesores_layout.setSpacing(5)

        prof_label = QLabel("👥 Seleccionar profesores:")
        prof_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        profesores_layout.addWidget(prof_label)

        # Scroll area para checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """
        )

        scroll_widget = QWidget()
        self.profesores_checks_layout = QVBoxLayout(scroll_widget)
        self.profesores_checks_layout.setSpacing(5)
        self.profesores_checks_layout.setContentsMargins(10, 10, 10, 10)

        # Checkbox "Seleccionar todos"
        self.seleccionar_todos_check = QCheckBox("✅ Seleccionar todos")
        self.seleccionar_todos_check.setChecked(True)
        self.seleccionar_todos_check.setStyleSheet(
            """
            QCheckBox {
                font-weight: bold;
                color: #1976D2;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        )
        self.profesores_checks_layout.addWidget(self.seleccionar_todos_check)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc; max-height: 1px;")
        self.profesores_checks_layout.addWidget(separator)

        # Lista dinámica de checkboxes (se carga después)
        self.cargar_profesores_checkboxes()

        scroll_area.setWidget(scroll_widget)
        profesores_layout.addWidget(scroll_area)

        return container

    def _conectar_senales(self):
        """Conectar señales internas."""
        self.pdf_tipo_combo.currentIndexChanged.connect(self._on_tipo_pdf_changed)
        self.seleccionar_todos_check.stateChanged.connect(self._on_seleccionar_todos_changed)
        self.exportar_pdf_btn.clicked.connect(self.generar_pdfs_solicitado.emit)

    def _on_tipo_pdf_changed(self):
        """Manejar cambio en el tipo de exportación PDF."""
        tipo = self.pdf_tipo_combo.currentData()

        # Mostrar/ocultar controles según el tipo
        if tipo in ["mes_todos", "mes_seleccionados"]:
            self.fecha_container.show()
            self.curso_container.hide()
        else:  # curso_todos, curso_seleccionados
            self.fecha_container.hide()
            self.curso_container.show()

        if tipo in ["mes_seleccionados", "curso_seleccionados"]:
            self.profesores_container.show()
        else:
            self.profesores_container.hide()

        # Actualizar texto del botón
        if tipo == "mes_todos":
            self.exportar_pdf_btn.setText("📄 Generar PDFs para Todos (Mes)")
        elif tipo == "mes_seleccionados":
            self.exportar_pdf_btn.setText("📄 Generar PDFs Seleccionados (Mes)")
        elif tipo == "curso_todos":
            self.exportar_pdf_btn.setText("📚 Generar PDF Curso Completo (Todos)")
        else:  # curso_seleccionados
            self.exportar_pdf_btn.setText("📚 Generar PDF Curso Completo (Seleccionados)")

    def _on_seleccionar_todos_changed(self, state):
        """Manejar cambio en el checkbox de seleccionar todos."""
        seleccionado = state == Qt.CheckState.Checked
        for checkbox in self.profesor_checkboxes:
            checkbox.setChecked(seleccionado)

    def _on_profesor_checkbox_changed(self):
        """Manejar cambio en checkbox individual de profesor."""
        # Actualizar estado de "Seleccionar todos"
        todos_seleccionados = all(cb.isChecked() for cb in self.profesor_checkboxes)
        alguno_deseleccionado = any(not cb.isChecked() for cb in self.profesor_checkboxes)

        if todos_seleccionados:
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)
        elif alguno_deseleccionado:
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.PartiallyChecked)

    # ========== API PÚBLICA ==========

    def cargar_profesores_checkboxes(self):
        """Cargar checkboxes de profesores desde la base de datos."""
        try:
            # Limpiar checkboxes anteriores
            for checkbox in self.profesor_checkboxes:
                checkbox.deleteLater()
            self.profesor_checkboxes.clear()

            # Obtener profesores
            profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()

            for profesor in profesores:
                checkbox = QCheckBox(f"{profesor.nombre_completo} ({profesor.turno})")
                checkbox.setChecked(True)  # Seleccionados por defecto
                checkbox.setProperty("profesor_id", profesor.id)
                checkbox.setStyleSheet(
                    """
                    QCheckBox {
                        font-size: 11px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                """
                )
                checkbox.stateChanged.connect(self._on_profesor_checkbox_changed)
                self.profesores_checks_layout.addWidget(checkbox)
                self.profesor_checkboxes.append(checkbox)

        except Exception:
            # No lanzar excepción, solo no cargar profesores
            pass

    def get_configuracion_pdf(self) -> dict:
        """
        Obtener la configuración actual para generación de PDF.

        Returns:
            Diccionario con:
            - tipo: str (mes_todos, mes_seleccionados, curso_todos, curso_seleccionados)
            - mes: int (1-12, solo si tipo incluye 'mes')
            - anio: int (año, solo si tipo incluye 'mes')
            - anio_inicio_curso: int (solo si tipo incluye 'curso')
            - profesores_ids: List[int] (solo si tipo incluye 'seleccionados')
        """
        tipo = self.pdf_tipo_combo.currentData()
        config = {"tipo": tipo}

        if "mes" in tipo:
            config["mes"] = self.pdf_mes_combo.currentIndex() + 1
            config["anio"] = int(self.pdf_anio_combo.currentText())
        else:  # curso
            config["anio_inicio_curso"] = self.pdf_curso_combo.currentData()

        if "seleccionados" in tipo:
            config["profesores_ids"] = self.get_profesores_seleccionados()

        return config

    def get_profesores_seleccionados(self) -> List[int]:
        """
        Obtener IDs de profesores seleccionados.

        Returns:
            Lista de IDs de profesores con checkbox marcado
        """
        return [
            checkbox.property("profesor_id")
            for checkbox in self.profesor_checkboxes
            if checkbox.isChecked()
        ]

    def habilitar_generar(self, habilitado: bool):
        """
        Habilitar/deshabilitar el botón de generar PDF.

        Args:
            habilitado: True para habilitar
        """
        self.exportar_pdf_btn.setEnabled(habilitado)
