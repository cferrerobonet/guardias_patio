"""
Widget para configurar y generar calendarios PDF.

Permite configurar opciones de generación de PDFs con diferentes modos:
- Mes específico o curso completo
- Todos los profesores o selección personalizada
"""

from datetime import datetime
from typing import List

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

from presentation.theme.tokens import Spacing
from presentation.themes.tema_aplicacion import TEXT_SECONDARY


class CalendariosPdfWidget(QGroupBox):
    """Widget para configurar la exportación de calendarios PDF."""

    # Señal cuando se solicita generar PDFs
    generar_pdfs_solicitado = pyqtSignal()

    def __init__(self, session, parent=None):
        """
        Inicializar el widget de exportación PDF.

        Args:
            session: Sesión de base de datos para cargar profesores
            parent: Widget padre
        """
        super().__init__("📅 CALENDARIOS PDF", parent)
        self.session = session
        self.profesor_checkboxes: List[QCheckBox] = []

        self._setup_ui()
        self._conectar_senales()

    def _setup_ui(self):
        """Construir la interfaz del widget."""
        layout = QVBoxLayout()
        layout.setSpacing(Spacing.MD)
        layout.setContentsMargins(15, 20, 15, 15)

        # Información
        info = QLabel(
            "Genera calendarios individuales en PDF. Puedes exportar por mes, curso completo "
            "o calendario individual optimizado (desde la primera hasta la última guardia "
            "del profesor)."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
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

        # Opción de envío por email (solo para calendarios individuales)
        self.email_container = self._crear_opcion_email()
        layout.addWidget(self.email_container)
        self.email_container.hide()

        # Botón de exportación
        self.exportar_pdf_btn = QPushButton("Generar PDFs")
        self.exportar_pdf_btn.setMinimumHeight(40)
        self.exportar_pdf_btn.setProperty("success", "true")
        self.exportar_pdf_btn.setAccessibleName("Botón generar calendarios PDF")
        layout.addWidget(self.exportar_pdf_btn)

        self.setLayout(layout)

    def _crear_tipo_exportacion(self) -> QVBoxLayout:
        """Crear controles para tipo de exportación."""
        tipo_layout = QVBoxLayout()
        tipo_layout.setSpacing(5)

        tipo_label = QLabel("Tipo de exportación:")
        tipo_label.setObjectName("fieldLabel")
        tipo_layout.addWidget(tipo_label)

        self.pdf_tipo_combo = QComboBox()
        self.pdf_tipo_combo.addItem(
            "👤 Mes específico - Profesores seleccionados", "mes_seleccionados"
        )
        self.pdf_tipo_combo.addItem(
            "🗓️ Calendario individual - Profesores seleccionados", "individual_seleccionados"
        )
        self.pdf_tipo_combo.setAccessibleName("Tipo de exportación de calendario PDF")
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
        mes_label.setObjectName("fieldLabel")
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
        self.pdf_mes_combo.setAccessibleName("Mes para exportación de calendario")
        mes_container.addWidget(self.pdf_mes_combo)
        fecha_layout.addLayout(mes_container, 2)

        # Año
        anio_container = QVBoxLayout()
        anio_container.setSpacing(5)
        anio_label = QLabel("📆 Año:")
        anio_label.setObjectName("fieldLabel")
        anio_container.addWidget(anio_label)

        self.pdf_anio_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_anio_combo.addItem(str(anio))
        self.pdf_anio_combo.setCurrentIndex(1)  # Año actual
        self.pdf_anio_combo.setAccessibleName("Año para exportación de calendario")
        anio_container.addWidget(self.pdf_anio_combo)
        fecha_layout.addLayout(anio_container, 1)

        return container

    def _crear_controles_curso(self) -> QWidget:
        """Crear controles para curso completo."""
        container = QWidget()
        curso_layout = QVBoxLayout(container)
        curso_layout.setContentsMargins(0, 0, 0, 0)
        curso_layout.setSpacing(5)

        curso_label = QLabel("📚 Curso escolar:")
        curso_label.setObjectName("fieldLabel")
        curso_layout.addWidget(curso_label)

        # Mostrar el curso activo (sin selector - se usa automáticamente)
        self.curso_activo_label = QLabel()
        self.curso_activo_label.setStyleSheet(
            """
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196f3;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                font-weight: bold;
                color: #1976d2;
            }
        """
        )
        curso_layout.addWidget(self.curso_activo_label)

        curso_info = QLabel(
            "ℹ️ Se exportará el curso activo completo.\n"
            "Para cambiar de curso, usa el selector en la barra superior."
        )
        curso_info.setWordWrap(True)
        curso_info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            font-style: italic;
        """
        )
        curso_layout.addWidget(curso_info)

        # Actualizar el label con el curso activo
        self._actualizar_curso_activo_label()

        return container

    def _crear_seleccion_profesores(self) -> QWidget:
        """Crear widget de selección de profesores."""
        container = QWidget()
        profesores_layout = QVBoxLayout(container)
        profesores_layout.setContentsMargins(0, 0, 0, 0)
        profesores_layout.setSpacing(5)

        prof_label = QLabel("👥 Seleccionar profesores:")
        prof_label.setObjectName("fieldLabel")
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
        self.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)
        self.seleccionar_todos_check.setAccessibleName(
            "Seleccionar todos los profesores para exportación"
        )
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
        separator.setObjectName("separator")
        self.profesores_checks_layout.addWidget(separator)

        # Lista dinámica de checkboxes (se carga después)
        self.cargar_profesores_checkboxes()

        scroll_area.setWidget(scroll_widget)
        profesores_layout.addWidget(scroll_area)

        return container

    def _crear_opcion_email(self) -> QWidget:
        """Crear widget de opción de envío por email."""
        container = QWidget()
        email_layout = QVBoxLayout(container)
        email_layout.setContentsMargins(0, 10, 0, 0)
        email_layout.setSpacing(5)

        # Checkbox de envío por email
        self.enviar_email_check = QCheckBox("📧 Enviar calendario por email a cada profesor")
        self.enviar_email_check.setChecked(False)
        self.enviar_email_check.setAccessibleName(
            "Activar envío de calendario por email a profesores"
        )
        self.enviar_email_check.setStyleSheet(
            """
            QCheckBox {
                font-weight: bold;
                color: #166529;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """
        )
        email_layout.addWidget(self.enviar_email_check)

        # Información sobre el envío
        email_info = QLabel(
            "ℹ️ Se enviará un email personalizado con el PDF adjunto a la dirección "
            "de correo de cada profesor seleccionado."
        )
        email_info.setWordWrap(True)
        email_info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            font-style: italic;
            margin-left: 24px;
        """
        )
        email_layout.addWidget(email_info)

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
        if tipo == "mes_seleccionados":
            self.fecha_container.show()
            self.curso_container.hide()
        else:  # individual_seleccionados
            self.fecha_container.hide()
            self.curso_container.hide()

        self.profesores_container.show()

        # Mostrar opción de email solo para calendarios individuales
        if tipo == "individual_seleccionados":
            self.email_container.show()
        else:
            self.email_container.hide()

        # Actualizar texto del botón
        if tipo == "mes_seleccionados":
            self.exportar_pdf_btn.setText("Generar PDFs Seleccionados (Mes)")
        else:  # individual_seleccionados
            self.exportar_pdf_btn.setText("Generar Calendarios Individuales")

    def _on_seleccionar_todos_changed(self, state):
        """Manejar cambio en el checkbox de seleccionar todos."""
        seleccionado = int(state) == Qt.CheckState.Checked.value

        # Bloquear señales temporalmente para evitar bucles
        for checkbox in self.profesor_checkboxes:
            checkbox.blockSignals(True)
            checkbox.setChecked(seleccionado)
            checkbox.blockSignals(False)

    def _on_profesor_checkbox_changed(self):
        """Manejar cambio en checkbox individual de profesor."""
        if not self.profesor_checkboxes:
            return

        # Actualizar estado de "Seleccionar todos"
        todos_seleccionados = all(cb.isChecked() for cb in self.profesor_checkboxes)
        ninguno_seleccionado = not any(cb.isChecked() for cb in self.profesor_checkboxes)

        # Bloquear señales para evitar bucle infinito
        self.seleccionar_todos_check.blockSignals(True)

        if todos_seleccionados:
            self.seleccionar_todos_check.setTristate(False)
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)
        elif ninguno_seleccionado:
            self.seleccionar_todos_check.setTristate(False)
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.Unchecked)
        else:
            # Activar tristate solo para mostrar estado parcial
            self.seleccionar_todos_check.setTristate(True)
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.PartiallyChecked)
            self.seleccionar_todos_check.setTristate(False)

        self.seleccionar_todos_check.blockSignals(False)

    # ========== API PÚBLICA ==========

    def _actualizar_curso_activo_label(self):
        """Actualiza el label del curso activo desde la base de datos."""
        try:
            from services.gestor_cursos import GestorCursos

            curso_activo = GestorCursos.from_session(self.session).obtener_curso_activo()
            if curso_activo:
                self.curso_activo_label.setText(
                    f"⭐ {curso_activo.nombre}\n"
                    f"📅 {curso_activo.fecha_inicio.strftime('%d/%m/%Y')} - "
                    f"{curso_activo.fecha_fin.strftime('%d/%m/%Y')}"
                )
            else:
                self.curso_activo_label.setText(
                    "⚠️ No hay curso activo.\nCrea un curso desde Configuración → Gestión de Cursos"
                )
                self.curso_activo_label.setStyleSheet(
                    """
                    QLabel {
                        background-color: #fff3cd;
                        border: 2px solid #ffc107;
                        border-radius: 4px;
                        padding: 8px;
                        font-size: 12px;
                        font-weight: bold;
                        color: #856404;
                    }
                """
                )
        except (ValueError, TypeError, OSError) as e:
            self.curso_activo_label.setText(f"Error al obtener curso: {e}")

    def refrescar_curso_activo(self):
        """Método público para refrescar el curso activo desde la UI principal."""
        self._actualizar_curso_activo_label()

    def cargar_profesores_checkboxes(self):
        """Cargar checkboxes de profesores desde la base de datos."""
        try:
            # Limpiar checkboxes anteriores
            for checkbox in self.profesor_checkboxes:
                checkbox.deleteLater()
            self.profesor_checkboxes.clear()

            # Obtener profesores
            from application.app_services import AppServices

            profesores = AppServices(self.session).profesores.get_all()
            profesores = sorted(profesores, key=lambda p: p.nombre_completo)

            for profesor in profesores:
                checkbox = QCheckBox(f"{profesor.nombre_completo} ({profesor.turno})")
                checkbox.setChecked(True)  # Seleccionados por defecto
                checkbox.setProperty("profesor_id", profesor.id)
                checkbox.setStyleSheet(
                    """
                    QCheckBox {
                        font-size: 12px;
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

        except (ValueError, TypeError, OSError):
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
            - enviar_email: bool (solo si tipo es 'individual_seleccionados')
        """
        tipo = self.pdf_tipo_combo.currentData()
        config = {"tipo": tipo}

        if "mes" in tipo:
            config["mes"] = self.pdf_mes_combo.currentIndex() + 1
            config["anio"] = int(self.pdf_anio_combo.currentText())
        elif "curso" in tipo:
            # Obtener año de inicio del curso activo
            from services.gestor_cursos import GestorCursos

            curso_activo = GestorCursos.from_session(self.session).obtener_curso_activo()
            if curso_activo:
                config["anio_inicio_curso"] = curso_activo.anio_inicio
                config["curso_id"] = curso_activo.id
            else:
                # Si no hay curso activo, retornar None para que el formulario lo maneje
                config["anio_inicio_curso"] = None
                config["curso_id"] = None

        if "seleccionados" in tipo:
            config["profesores_ids"] = self.get_profesores_seleccionados()

        # Agregar opción de email para calendarios individuales
        if tipo == "individual_seleccionados":
            config["enviar_email"] = self.enviar_email_check.isChecked()

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
