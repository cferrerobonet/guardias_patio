import os
import sys

import ui_styles as styles
from database.db_manager import SessionLocal
from models.models import Configuracion, Guardia, Profesor, Zona

# Importar forms refactorizados (Sprint 4)
from presentation.forms import AsignacionGuardiasForm as AsignacionGuardiasFormRefactorizado
from presentation.forms import ConfiguracionForm as ConfiguracionFormRefactorizado
from presentation.forms import ZonaForm as ZonaFormRefactorizado
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from utils import constants, setup_logging
from utils.validators import (
    validar_email,
    validar_horas_contrato,
    validar_nombre_completo,
)
from widgets.gestionar_ausencias import GestionarAusenciasForm
from widgets.gestionar_sustituciones import GestorSustituciones
from widgets.panel_estadisticas import PanelEstadisticas
from widgets.vista_calendario import VistaCalendario

# Configurar logging al inicio
setup_logging()

GUI_AVAILABLE = True
try:
    from PyQt6.QtCore import QDate, Qt, QTime
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QApplication,
        QCalendarWidget,
        QCheckBox,
        QComboBox,
        QDateEdit,
        QFileDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QListWidget,
        QMessageBox,
        QPushButton,
        QTableWidget,
        QTableWidgetItem,
        QTabWidget,
        QTextEdit,
        QTimeEdit,
        QVBoxLayout,
        QWidget,
    )
except Exception:  # pragma: no cover - ruta de pruebas/CI sin PyQt
    GUI_AVAILABLE = False

    class _Stub:
        def __init__(self, *args, **kwargs):
            pass

        def __getattr__(self, name):
            return _Stub()

        def setCalendarPopup(self, *a, **k):
            pass

        def setDate(self, *a, **k):
            pass

        def setTime(self, *a, **k):
            pass

        def addItems(self, *a, **k):
            pass

        def setPlaceholderText(self, *a, **k):
            pass

        def setVisible(self, *a, **k):
            pass

        def setReadOnly(self, *a, **k):
            pass

        def setMaximumHeight(self, *a, **k):
            pass

        def addWidget(self, *a, **k):
            pass

        def addLayout(self, *a, **k):
            pass

        def clicked(self, *a, **k):
            return _Stub()

        def connect(self, *a, **k):
            pass

        def currentText(self):
            return ""

        def text(self):
            return ""

        def clear(self):
            pass

        def setChecked(self, *a, **k):
            pass

        def date(self):
            return _Stub()

        def time(self):
            return _Stub()

        def toPyDate(self):
            return None

        def toPyTime(self):
            return None

        def isValid(self):
            return False

        def setWindowTitle(self, *a, **k):
            pass

        def show(self):
            pass

        def exec(self):
            return 0

        def setText(self, *a, **k):
            pass

        def currentTextChanged(self, *a, **k):
            return _Stub()

    # Stubs de widgets
    QApplication = QWidget = QLabel = QLineEdit = QComboBox = QDateEdit = QTimeEdit = QCheckBox = (
        QListWidget
    ) = QPushButton = QHBoxLayout = QVBoxLayout = QTabWidget = QTextEdit = _Stub

    # Stub de QMessageBox
    class QMessageBox(_Stub):
        class StandardButton:
            Yes = 1
            No = 0

        @staticmethod
        def information(*a, **k):
            pass

        @staticmethod
        def warning(*a, **k):
            pass

        @staticmethod
        def critical(*a, **k):
            pass

        @staticmethod
        def question(*a, **k):
            return 0

    # Stubs de QDate/QTime
    class QDate:
        @staticmethod
        def currentDate():
            return QDate()

        def addMonths(self, n):
            return self

        def __call__(self, *a, **k):
            return self

    class QTime:
        def __init__(self, *a, **k):
            pass

"""Aplicación de gestión de guardias de patio con GUI PyQt6.

Este archivo define la GUI principal. Para permitir la ejecución de tests en entornos
sin PyQt6 (CI), se inyectan stubs si la importación de PyQt6 falla.
"""

# Se importarán funciones del asignador al conectar la generación


class ProfesorForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Profesores")

        # Variable para trackear si estamos editando
        self.profesor_editando_id = None

        # Configurar atajos de teclado
        self._configurar_atajos()

        # Layout principal horizontal: Tabla a la izquierda, Formulario a la derecha
        main_layout = QHBoxLayout()

        # ========== SECCIÓN IZQUIERDA: LISTA DE PROFESORES ==========
        left_section = QVBoxLayout()
        left_section.setContentsMargins(10, 10, 10, 10)
        left_section.setSpacing(10)

        self.titulo_lista_profesores = QLabel("📋 PROFESORES REGISTRADOS (0)")
        self.titulo_lista_profesores.setStyleSheet(styles.STYLE_TITLE_MAIN)
        left_section.addWidget(self.titulo_lista_profesores)

        # Campo de búsqueda
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setSpacing(8)

        busqueda_label = QLabel("🔍 Buscar:")
        busqueda_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        busqueda_layout.addWidget(busqueda_label)

        self.busqueda_input = QLineEdit()
        self.busqueda_input.setPlaceholderText("Buscar por nombre o email...")
        self.busqueda_input.setStyleSheet(styles.STYLE_INPUT)
        self.busqueda_input.textChanged.connect(self.filtrar_profesores)
        busqueda_layout.addWidget(self.busqueda_input)

        self.limpiar_busqueda_btn = QPushButton("✖")
        self.limpiar_busqueda_btn.setFixedWidth(30)
        self.limpiar_busqueda_btn.setToolTip("Limpiar búsqueda")
        self.limpiar_busqueda_btn.clicked.connect(self.limpiar_busqueda)
        self.limpiar_busqueda_btn.setStyleSheet("""
            QPushButton {
                background-color: #e0e0e0;
                border: none;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d0d0d0;
            }
        """)
        busqueda_layout.addWidget(self.limpiar_busqueda_btn)

        left_section.addLayout(busqueda_layout)

        # Tabla de profesores con columnas
        self.tabla_profesores = QTableWidget()
        self.tabla_profesores.setColumnCount(5)
        self.tabla_profesores.setHorizontalHeaderLabels([
            "Nombre Completo", "Email", "Horas", "Turno", "Tutor"
        ])
        # Hacer que la columna de nombre se estire para ocupar espacio disponible
        self.tabla_profesores.horizontalHeader().setStretchLastSection(False)
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        # Hacer las demás columnas ajustables al contenido
        for i in [1, 2, 3, 4]:
            self.tabla_profesores.horizontalHeader().setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents
            )
        # Habilitar ordenación
        self.tabla_profesores.setSortingEnabled(True)
        # Selección de fila completa
        self.tabla_profesores.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_profesores.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        # Doble clic para editar
        self.tabla_profesores.doubleClicked.connect(self.editar_profesor)

        left_section.addWidget(self.tabla_profesores)

        # Botones de gestión de tabla
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_profesores)
        self.refresh_btn.setToolTip("Recargar la lista de profesores desde la base de datos (F5)")

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.editar_profesor)
        self.editar_btn.setToolTip("Editar el profesor seleccionado en la tabla")

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_profesor)
        self.delete_btn.setToolTip("Eliminar el profesor seleccionado (Del)")

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.editar_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        left_section.addLayout(btn_layout)

        # ========== SECCIÓN DERECHA: FORMULARIO DE ALTA/EDICIÓN ==========
        right_section = QVBoxLayout()
        right_section.setContentsMargins(10, 0, 10, 10)
        right_section.setSpacing(12)

        self.titulo_seccion = QLabel("✏️ ALTA DE PROFESOR")
        self.titulo_seccion.setStyleSheet(styles.STYLE_TITLE_MAIN)
        right_section.addWidget(self.titulo_seccion)

        # ===== GRUPO: Datos Básicos =====
        grupo_basicos = QGroupBox("📋 Datos Básicos")
        grupo_basicos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_basicos = QVBoxLayout()
        layout_basicos.setSpacing(8)

        label_nombre = QLabel("Nombre completo (formato: APELLIDOS, NOMBRE):")
        label_nombre.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_basicos.addWidget(label_nombre)
        self.nombre_completo_input = QLineEdit()
        self.nombre_completo_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")
        self.nombre_completo_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_completo_input.setMaximumWidth(350)
        self.nombre_completo_input.setToolTip(
            "Formato requerido: APELLIDOS, NOMBRE\n"
            "Ejemplo: GARCÍA LÓPEZ, JUAN\n"
            "Debe contener una coma separando apellidos y nombre"
        )
        layout_basicos.addWidget(self.nombre_completo_input)

        label_email = QLabel("Email corporativo:")
        label_email.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_basicos.addWidget(label_email)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("profesor@colegio.edu")
        self.email_input.setStyleSheet(styles.STYLE_INPUT)
        self.email_input.setMaximumWidth(350)
        self.email_input.setToolTip(
            "Email corporativo del profesor (opcional)\n"
            "Se usará para enviar calendarios y notificaciones\n"
            "Debe ser una dirección de email válida"
        )
        layout_basicos.addWidget(self.email_input)

        self.tutor_checkbox = QCheckBox("✓ Es tutor/a")
        self.tutor_checkbox.setStyleSheet("font-size: 13px; margin-top: 5px;")
        self.tutor_checkbox.setToolTip(
            "Marca si el profesor es tutor de un grupo\n"
            "Los tutores pueden tener un ajuste de carga diferente\n"
            "configurado en la sección de Configuración"
        )
        layout_basicos.addWidget(self.tutor_checkbox)

        grupo_basicos.setLayout(layout_basicos)
        right_section.addWidget(grupo_basicos)

        # ===== GRUPO: Configuración de Horario =====
        grupo_horario = QGroupBox("🕐 Configuración de Horario")
        grupo_horario.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_horario = QVBoxLayout()
        layout_horario.setSpacing(8)

        # Primera fila: Horas de contrato y Turno en horizontal
        layout_fila1 = QHBoxLayout()
        layout_fila1.setSpacing(15)

        # Horas de contrato
        label_horas = QLabel("Horas de contrato:")
        label_horas.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fila1.addWidget(label_horas)

        self.horas_input = QLineEdit()
        self.horas_input.setPlaceholderText("Ej: 30.0")
        self.horas_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_input.setMaximumWidth(100)
        self.horas_input.setToolTip(
            "Horas totales de contrato del profesor\n"
            "Debe ser un número positivo (ej: 30.0)\n"
            "Se usará para calcular el porcentaje de jornada\n"
            "y la distribución proporcional de guardias"
        )
        layout_fila1.addWidget(self.horas_input)

        layout_fila1.addSpacing(20)

        # Turno
        label_turno = QLabel("Turno:")
        label_turno.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_fila1.addWidget(label_turno)

        self.turno_input = QComboBox()
        self.turno_input.addItems(["Mañana", "Tarde", "Mixto"])
        self.turno_input.setStyleSheet(styles.STYLE_INPUT)
        self.turno_input.setMaximumWidth(120)
        layout_fila1.addWidget(self.turno_input)

        layout_fila1.addStretch()
        layout_horario.addLayout(layout_fila1)

        # Añadir espaciado vertical
        layout_horario.addSpacing(15)

        # Segunda fila: Campos para turno mixto (inicialmente ocultos)
        layout_mixto = QHBoxLayout()
        layout_mixto.setSpacing(10)

        self.label_horas_manana = QLabel("  🌅 Horas mañana:")
        self.label_horas_manana.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_mixto.addWidget(self.label_horas_manana)

        self.horas_manana_input = QLineEdit()
        self.horas_manana_input.setPlaceholderText("Ej: 15.0")
        self.horas_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_manana_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_manana_input)

        layout_mixto.addSpacing(20)

        self.label_horas_tarde = QLabel("🌆 Horas tarde:")
        self.label_horas_tarde.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_mixto.addWidget(self.label_horas_tarde)

        self.horas_tarde_input = QLineEdit()
        self.horas_tarde_input.setPlaceholderText("Ej: 15.0")
        self.horas_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_tarde_input.setMaximumWidth(100)
        layout_mixto.addWidget(self.horas_tarde_input)

        layout_mixto.addStretch()
        layout_horario.addLayout(layout_mixto)

        grupo_horario.setLayout(layout_horario)
        right_section.addWidget(grupo_horario)

        # Inicialmente ocultar campos mixto
        self._toggle_mixto_fields(False)
        self.turno_input.currentTextChanged.connect(self._on_turno_changed)

        # ===== GRUPO: Restricciones y Preferencias =====
        grupo_restricciones = QGroupBox("⚙️ Restricciones y Preferencias")
        grupo_restricciones.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_restricciones = QVBoxLayout()
        layout_restricciones.setSpacing(8)

        # Fecha de inicio de guardias (mutuamente excluyente con fecha fin)
        layout_fecha_inicio = QHBoxLayout()
        self.usar_fecha_inicio_checkbox = QCheckBox("Usar fecha de inicio:")
        self.usar_fecha_inicio_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_fecha_inicio_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        layout_fecha_inicio.addWidget(self.usar_fecha_inicio_checkbox)

        self.fecha_inicio_guardias_input = QDateEdit()
        self.fecha_inicio_guardias_input.setCalendarPopup(True)
        self.fecha_inicio_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_guardias_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_guardias_input.setMaximumWidth(200)
        # Establecer fecha actual por defecto
        from PyQt6.QtCore import QDate
        self.fecha_inicio_guardias_input.setDate(QDate.currentDate())
        self.fecha_inicio_guardias_input.setEnabled(False)  # Deshabilitado por defecto
        layout_fecha_inicio.addWidget(self.fecha_inicio_guardias_input)
        layout_fecha_inicio.addStretch()
        layout_restricciones.addLayout(layout_fecha_inicio)

        # Fecha de fin de guardias (mutuamente excluyente con fecha inicio)
        layout_fecha_fin = QHBoxLayout()
        self.usar_fecha_fin_checkbox = QCheckBox("Usar fecha de fin:")
        self.usar_fecha_fin_checkbox.setStyleSheet(styles.STYLE_LABEL_FIELD)
        self.usar_fecha_fin_checkbox.stateChanged.connect(self._toggle_fechas_guardias)
        layout_fecha_fin.addWidget(self.usar_fecha_fin_checkbox)

        self.fecha_fin_guardias_input = QDateEdit()
        self.fecha_fin_guardias_input.setCalendarPopup(True)
        self.fecha_fin_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin_guardias_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_guardias_input.setMaximumWidth(200)
        # Establecer fecha actual por defecto
        self.fecha_fin_guardias_input.setDate(QDate.currentDate())
        self.fecha_fin_guardias_input.setEnabled(False)  # Deshabilitado por defecto
        layout_fecha_fin.addWidget(self.fecha_fin_guardias_input)
        layout_fecha_fin.addStretch()
        layout_restricciones.addLayout(layout_fecha_fin)

        # Nueva matriz de disponibilidad día × recreo
        self.usar_restricciones_horario_checkbox = QCheckBox(
            "☑️ Usar restricciones personalizadas de horario"
        )
        self.usar_restricciones_horario_checkbox.setStyleSheet(
            styles.STYLE_LABEL_FIELD
        )
        self.usar_restricciones_horario_checkbox.stateChanged.connect(
            self._toggle_matriz_horario
        )
        layout_restricciones.addWidget(self.usar_restricciones_horario_checkbox)

        label_matriz = QLabel("📅 Disponibilidad por día y recreo:")
        label_matriz.setStyleSheet(styles.STYLE_LABEL_FIELD + " font-weight: bold;")
        layout_restricciones.addWidget(label_matriz)

        # Contenedor para la matriz
        self.matriz_horario_widget = QWidget()
        layout_matriz = QVBoxLayout()
        layout_matriz.setContentsMargins(10, 10, 10, 10)
        layout_matriz.setSpacing(5)

        # Grid de checkboxes
        grid_matriz = QGridLayout()
        grid_matriz.setSpacing(8)

        # Encabezados de columnas (recreos)
        dias_nombres = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
        grid_matriz.addWidget(QLabel(""), 0, 0)  # Esquina superior izquierda vacía
        for col in range(4):
            label_recreo = QLabel(f"<b>R{col+1}</b>")
            label_recreo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid_matriz.addWidget(label_recreo, 0, col + 1)

        # Crear matriz de checkboxes: self.matriz_checks[dia][recreo]
        self.matriz_checks = {}
        for fila, dia_idx in enumerate(range(7)):
            # Etiqueta del día
            label_dia = QLabel(f"<b>{dias_nombres[dia_idx]}</b>")
            label_dia.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            grid_matriz.addWidget(label_dia, fila + 1, 0)

            self.matriz_checks[dia_idx] = {}
            for col, recreo_id in enumerate(range(1, 5)):
                checkbox = QCheckBox()
                checkbox.setEnabled(False)  # Deshabilitado por defecto
                grid_matriz.addWidget(checkbox, fila + 1, col + 1)
                self.matriz_checks[dia_idx][recreo_id] = checkbox

        layout_matriz.addLayout(grid_matriz)

        # Botones de acción rápida
        botones_matriz = QHBoxLayout()
        botones_matriz.setSpacing(10)

        self.btn_marcar_todos = QPushButton("✓ Marcar todos")
        self.btn_marcar_todos.setEnabled(False)
        self.btn_marcar_todos.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.btn_marcar_todos.clicked.connect(lambda: self._marcar_todos_matriz(True))
        botones_matriz.addWidget(self.btn_marcar_todos)

        self.btn_desmarcar_todos = QPushButton("✗ Desmarcar todos")
        self.btn_desmarcar_todos.setEnabled(False)
        self.btn_desmarcar_todos.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.btn_desmarcar_todos.clicked.connect(lambda: self._marcar_todos_matriz(False))
        botones_matriz.addWidget(self.btn_desmarcar_todos)

        botones_matriz.addStretch()
        layout_matriz.addLayout(botones_matriz)

        self.matriz_horario_widget.setLayout(layout_matriz)
        self.matriz_horario_widget.setEnabled(False)  # Deshabilitado por defecto
        layout_restricciones.addWidget(self.matriz_horario_widget)

        grupo_restricciones.setLayout(layout_restricciones)
        right_section.addWidget(grupo_restricciones)

        # Botones de acción con estilos
        botones_accion = QHBoxLayout()
        botones_accion.setSpacing(10)

        self.submit_btn = QPushButton("💾 Guardar nuevo profesor")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_profesor)

        self.cancelar_btn = QPushButton("❌ Cancelar Edición")
        self.cancelar_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.cancelar_btn.clicked.connect(self.cancelar_edicion)
        self.cancelar_btn.setVisible(False)  # Oculto por defecto

        botones_accion.addWidget(self.submit_btn)
        botones_accion.addWidget(self.cancelar_btn)
        right_section.addLayout(botones_accion)

        # Añadir espacio flexible al final del formulario
        right_section.addStretch()

        # ========== ENSAMBLAR LAYOUT PRINCIPAL ==========
        # Tabla ocupa 60% del espacio, formulario 40%
        main_layout.addLayout(left_section, 60)
        main_layout.addLayout(right_section, 40)

        self.setLayout(main_layout)
        self.cargar_profesores()  # Cargar al inicio

    def _toggle_mixto_fields(self, visible: bool):
        for w in [
            self.label_horas_manana,
            self.horas_manana_input,
            self.label_horas_tarde,
            self.horas_tarde_input,
        ]:
            w.setVisible(visible)

    def _on_turno_changed(self, value: str):
        # Comparar en minúsculas para ser insensible a mayúsculas
        self._toggle_mixto_fields(value.lower() == "mixto")

    def _configurar_atajos(self):
        """Configurar atajos de teclado para el formulario"""
        # Ctrl+S: Guardar profesor
        atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        atajo_guardar.activated.connect(self.guardar_profesor)

        # Ctrl+F: Enfocar búsqueda
        atajo_buscar = QShortcut(QKeySequence("Ctrl+F"), self)
        atajo_buscar.activated.connect(lambda: self.busqueda_input.setFocus())

        # F5: Refrescar lista
        atajo_refrescar = QShortcut(QKeySequence("F5"), self)
        atajo_refrescar.activated.connect(self.cargar_profesores)

        # Esc: Cancelar edición
        atajo_cancelar = QShortcut(QKeySequence("Esc"), self)
        atajo_cancelar.activated.connect(self.cancelar_edicion)

        # Del: Eliminar profesor seleccionado
        atajo_eliminar = QShortcut(QKeySequence("Del"), self)
        atajo_eliminar.activated.connect(self.eliminar_profesor)

    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.nombre_completo_input.clear()
        self.email_input.clear()
        self.horas_input.clear()
        self.horas_manana_input.clear()
        self.horas_tarde_input.clear()
        self.tutor_checkbox.setChecked(False)
        # Resetear fechas y sus checkboxes
        self.usar_fecha_inicio_checkbox.setChecked(False)
        self.usar_fecha_fin_checkbox.setChecked(False)
        self.fecha_inicio_guardias_input.clear()
        self.fecha_inicio_guardias_input.setEnabled(False)
        self.fecha_fin_guardias_input.clear()
        self.fecha_fin_guardias_input.setEnabled(False)
        # Resetear matriz de horario
        self.usar_restricciones_horario_checkbox.setChecked(False)
        self._marcar_todos_matriz(False)
        self.turno_input.setCurrentIndex(0)
        # Resetear modo edición
        self.profesor_editando_id = None
        self.titulo_seccion.setText("✏️ ALTA DE PROFESOR")
        self.submit_btn.setText("💾 Guardar nuevo profesor")
        self.cancelar_btn.setVisible(False)

    def cancelar_edicion(self):
        """Cancelar la edición actual y volver a modo creación"""
        self._limpiar_formulario()
        QMessageBox.information(self, "Cancelado", "Edición cancelada.")

    def _toggle_fechas_guardias(self):
        """
        Controla la exclusividad mutua entre fecha de inicio y fecha de fin.
        Solo una puede estar activa a la vez.
        """
        # Identificar quién disparó el evento
        sender = self.sender()

        # Si fue el checkbox de fecha de inicio
        if sender == self.usar_fecha_inicio_checkbox:
            if self.usar_fecha_inicio_checkbox.isChecked():
                # Activar fecha de inicio
                self.fecha_inicio_guardias_input.setEnabled(True)
                # Desactivar fecha fin (sin disparar eventos adicionales)
                self.usar_fecha_fin_checkbox.blockSignals(True)
                self.usar_fecha_fin_checkbox.setChecked(False)
                self.usar_fecha_fin_checkbox.blockSignals(False)
                self.fecha_fin_guardias_input.setEnabled(False)
            else:
                # Solo desactivar fecha de inicio
                self.fecha_inicio_guardias_input.setEnabled(False)

        # Si fue el checkbox de fecha de fin
        elif sender == self.usar_fecha_fin_checkbox:
            if self.usar_fecha_fin_checkbox.isChecked():
                # Activar fecha de fin
                self.fecha_fin_guardias_input.setEnabled(True)
                # Desactivar fecha inicio (sin disparar eventos adicionales)
                self.usar_fecha_inicio_checkbox.blockSignals(True)
                self.usar_fecha_inicio_checkbox.setChecked(False)
                self.usar_fecha_inicio_checkbox.blockSignals(False)
                self.fecha_inicio_guardias_input.setEnabled(False)
            else:
                # Solo desactivar fecha de fin
                self.fecha_fin_guardias_input.setEnabled(False)

    def _toggle_matriz_horario(self):
        """Activa/desactiva la matriz de disponibilidad por día y recreo."""
        is_checked = self.usar_restricciones_horario_checkbox.isChecked()
        self.matriz_horario_widget.setEnabled(is_checked)
        self.btn_marcar_todos.setEnabled(is_checked)
        self.btn_desmarcar_todos.setEnabled(is_checked)

        # Habilitar/deshabilitar todos los checkboxes individuales
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setEnabled(is_checked)

    def _marcar_todos_matriz(self, estado: bool):
        """Marca o desmarca todos los checkboxes de la matriz."""
        for dia in self.matriz_checks:
            for recreo in self.matriz_checks[dia]:
                self.matriz_checks[dia][recreo].setChecked(estado)

    def _matriz_a_json(self) -> str:
        """
        Convierte la matriz de checkboxes a formato JSON.
        Retorna: JSON string tipo '{"0": [1, 2], "2": [1, 3, 4]}'
        donde clave = día (0-6) y valor = lista de recreos (1-4).
        """
        import json
        resultado = {}
        for dia in self.matriz_checks:
            recreos_activos = []
            for recreo in self.matriz_checks[dia]:
                if self.matriz_checks[dia][recreo].isChecked():
                    recreos_activos.append(recreo)
            if recreos_activos:  # Solo incluir días con al menos un recreo
                resultado[str(dia)] = recreos_activos
        return json.dumps(resultado) if resultado else ""

    def _json_a_matriz(self, json_str: str):
        """
        Carga datos JSON en la matriz de checkboxes.
        Espera: JSON string tipo '{"0": [1, 2], "2": [1, 3, 4]}'
        """
        import json
        # Primero desmarcar todo
        self._marcar_todos_matriz(False)

        if not json_str:
            return

        try:
            datos = json.loads(json_str)
            for dia_str, recreos in datos.items():
                dia = int(dia_str)
                if dia in self.matriz_checks:
                    for recreo in recreos:
                        if recreo in self.matriz_checks[dia]:
                            self.matriz_checks[dia][recreo].setChecked(True)
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error al cargar matriz de horario: {e}")

    def guardar_profesor(self):
        session = SessionLocal()
        try:
            # Validar nombre completo
            nombre_completo = self.nombre_completo_input.text().strip()
            valido, error_msg = validar_nombre_completo(nombre_completo)
            if not valido:
                QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
                return

            # Validar horas de contrato
            try:
                horas = float(self.horas_input.text())
            except ValueError:
                QMessageBox.warning(
                    self,
                    constants.MSG_ERROR_TITULO,
                    "Las horas de contrato deben ser un número válido.",
                )
                return

            valido, error_msg = validar_horas_contrato(horas)
            if not valido:
                QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
                return

            turno = self.turno_input.currentText().lower()  # Convertir a minúsculas para BD
            porcentaje = horas / 30.0
            # Si turno mixto, calcular proporciones
            horas_manana = horas_tarde = 0.0
            if turno == "mixto":
                if not self.horas_manana_input.text() or not self.horas_tarde_input.text():
                    QMessageBox.warning(
                        self,
                        "Faltan datos",
                        "Debes indicar horas de mañana y tarde para turno mixto.",
                    )
                    return
                try:
                    horas_manana = float(self.horas_manana_input.text())
                    horas_tarde = float(self.horas_tarde_input.text())
                except ValueError:
                    QMessageBox.warning(
                        self,
                        "Formato",
                        "Horas de mañana y tarde deben ser numéricas.",
                    )
                    return
                if abs((horas_manana + horas_tarde) - horas) > 1e-6:
                    QMessageBox.warning(
                        self,
                        "Inconsistencia",
                        "La suma de horas de mañana y tarde debe coincidir con las horas totales.",
                    )
                    return
                # Aquí podrías guardar la proporción en la base de datos si el modelo lo permite
            # Validar email corporativo si se proporciona
            email_corporativo = self.email_input.text().strip() or None
            if email_corporativo:
                valido, error_msg = validar_email(email_corporativo)
                if not valido:
                    QMessageBox.warning(self, constants.MSG_ERROR_TITULO, error_msg)
                    return

            # Campos nuevos opcionales
            tutor = self.tutor_checkbox.isChecked()

            # Fechas de guardias (mutuamente excluyentes)
            fecha_inicio_guardias = None
            fecha_fin_guardias = None

            if self.usar_fecha_inicio_checkbox.isChecked():
                fecha_inicio_guardias = (
                    self.fecha_inicio_guardias_input.date().toPyDate()
                    if self.fecha_inicio_guardias_input.date().isValid() else None
                )
            elif self.usar_fecha_fin_checkbox.isChecked():
                fecha_fin_guardias = (
                    self.fecha_fin_guardias_input.date().toPyDate()
                    if self.fecha_fin_guardias_input.date().isValid() else None
                )

            # Obtener restricciones de horario desde la matriz (si está activada)
            recreos_permitidos_horario = None
            if self.usar_restricciones_horario_checkbox.isChecked():
                recreos_permitidos_horario = self._matriz_a_json()

            # Verificar si estamos editando o creando
            if self.profesor_editando_id is not None:
                # MODO EDICIÓN: Actualizar profesor existente
                profesor = session.query(Profesor).filter(
                    Profesor.id == self.profesor_editando_id
                ).first()
                if profesor:
                    profesor.nombre_completo = nombre_completo
                    profesor.email_corporativo = email_corporativo
                    profesor.horas_contrato = horas
                    profesor.porcentaje_jornada = porcentaje
                    profesor.turno = turno
                    profesor.horas_manana = horas_manana if turno == "mixto" else None
                    profesor.horas_tarde = horas_tarde if turno == "mixto" else None
                    profesor.tutor = tutor
                    profesor.fecha_inicio_guardias = fecha_inicio_guardias
                    profesor.fecha_fin_guardias = fecha_fin_guardias
                    # Guardar nueva matriz de horario (combina días y recreos)
                    profesor.recreos_permitidos = recreos_permitidos_horario or None
                    profesor.dias_semana_permitidos = None  # Ya no se usa por separado
                    session.commit()
                    # Mensaje de confirmación eliminado para mejor UX
                else:
                    QMessageBox.warning(self, "Error", "Profesor no encontrado.")
            else:
                # MODO CREACIÓN: Crear nuevo profesor
                nuevo_profesor = Profesor(
                    nombre_completo=nombre_completo,
                    email_corporativo=email_corporativo,
                    horas_contrato=horas,
                    porcentaje_jornada=porcentaje,
                    turno=turno,
                    horas_manana=horas_manana if turno == "mixto" else None,
                    horas_tarde=horas_tarde if turno == "mixto" else None,
                    tutor=tutor,
                    fecha_inicio_guardias=fecha_inicio_guardias,
                    fecha_fin_guardias=fecha_fin_guardias,
                    # Guardar nueva matriz de horario (combina días y recreos)
                    recreos_permitidos=recreos_permitidos_horario or None,
                    dias_semana_permitidos=None,  # Ya no se usa por separado
                )
                session.add(nuevo_profesor)
                session.commit()
                # Mensaje de confirmación eliminado para mejor UX

            # Limpiar formulario y actualizar lista
            self._limpiar_formulario()
            self.cargar_profesores()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

    def cargar_profesores(self):
        """Cargar la tabla de profesores desde la base de datos"""
        # Deshabilitar ordenación temporalmente para mejor rendimiento
        self.tabla_profesores.setSortingEnabled(False)
        self.tabla_profesores.setRowCount(0)

        session = SessionLocal()
        try:
            profesores = session.query(Profesor).order_by(Profesor.id).all()
            total_profesores = len(profesores)
            self.tabla_profesores.setRowCount(total_profesores)

            # Actualizar el título con el conteo en tiempo real
            self.titulo_lista_profesores.setText(f"📋 PROFESORES REGISTRADOS ({total_profesores})")

            for i, prof in enumerate(profesores):
                # Nombre completo (guardamos el ID aquí oculto)
                nombre_item = QTableWidgetItem(prof.nombre_completo or "")
                nombre_item.setData(Qt.ItemDataRole.UserRole, prof.id)  # Guardar ID oculto
                self.tabla_profesores.setItem(i, 0, nombre_item)

                # Email
                self.tabla_profesores.setItem(
                    i, 1, QTableWidgetItem(prof.email_corporativo or "-")
                )

                # Horas
                self.tabla_profesores.setItem(
                    i, 2, QTableWidgetItem(f"{prof.horas_contrato:.1f}h")
                )

                # Turno
                self.tabla_profesores.setItem(
                    i, 3, QTableWidgetItem(prof.turno.capitalize())
                )

                # Tutor
                tutor_text = "Sí" if prof.tutor else "No"
                self.tabla_profesores.setItem(i, 4, QTableWidgetItem(tutor_text))

            # Reactivar ordenación
            self.tabla_profesores.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar profesores: {e}")
        finally:
            session.close()

    def filtrar_profesores(self):
        """Filtrar profesores en la tabla según el texto de búsqueda"""
        texto_busqueda = self.busqueda_input.text().lower().strip()

        # Si no hay texto de búsqueda, mostrar todas las filas
        if not texto_busqueda:
            for i in range(self.tabla_profesores.rowCount()):
                self.tabla_profesores.setRowHidden(i, False)
            return

        # Filtrar filas según el texto de búsqueda
        for i in range(self.tabla_profesores.rowCount()):
            # Obtener nombre y email de la fila (ahora en columnas 0 y 1)
            nombre_item = self.tabla_profesores.item(i, 0)
            email_item = self.tabla_profesores.item(i, 1)

            nombre = nombre_item.text().lower() if nombre_item else ""
            email = email_item.text().lower() if email_item else ""

            # Mostrar fila si el texto está en nombre o email
            coincide = texto_busqueda in nombre or texto_busqueda in email
            self.tabla_profesores.setRowHidden(i, not coincide)

    def limpiar_busqueda(self):
        """Limpiar el campo de búsqueda y mostrar todos los profesores"""
        self.busqueda_input.clear()
        # filtrar_profesores se llamará automáticamente por textChanged

    def editar_profesor(self):
        """Cargar los datos del profesor seleccionado en el formulario para edición"""
        # Obtener la fila seleccionada
        fila_actual = self.tabla_profesores.currentRow()
        if fila_actual < 0:
            QMessageBox.warning(
                self, "Sin selección", "Selecciona un profesor para editar."
            )
            return

        # Extraer ID del item de la primera columna
        id_item = self.tabla_profesores.item(fila_actual, 0)
        if not id_item:
            return

        id_profesor = id_item.data(Qt.ItemDataRole.UserRole)

        session = SessionLocal()
        try:
            profesor = session.query(Profesor).filter(
                Profesor.id == id_profesor
            ).first()
            if not profesor:
                QMessageBox.warning(self, "Error", "Profesor no encontrado.")
                return

            # Cargar datos en el formulario
            self.nombre_completo_input.setText(profesor.nombre_completo or "")
            self.email_input.setText(profesor.email_corporativo or "")
            self.horas_input.setText(str(profesor.horas_contrato))

            # Seleccionar turno (capitalizar para que coincida con el ComboBox)
            index = self.turno_input.findText(profesor.turno.capitalize())
            if index >= 0:
                self.turno_input.setCurrentIndex(index)

            # Cargar horas de mañana y tarde si es turno mixto
            if profesor.turno == "mixto":
                if profesor.horas_manana is not None:
                    self.horas_manana_input.setText(str(profesor.horas_manana))
                if profesor.horas_tarde is not None:
                    self.horas_tarde_input.setText(str(profesor.horas_tarde))

            # Cargar checkbox tutor
            self.tutor_checkbox.setChecked(profesor.tutor or False)

            # Cargar fechas de guardias (mutuamente excluyentes)
            # Resetear primero
            self.usar_fecha_inicio_checkbox.setChecked(False)
            self.usar_fecha_fin_checkbox.setChecked(False)
            self.fecha_inicio_guardias_input.setEnabled(False)
            self.fecha_fin_guardias_input.setEnabled(False)

            # Cargar fecha inicio si existe
            if profesor.fecha_inicio_guardias:
                self.usar_fecha_inicio_checkbox.setChecked(True)
                self.fecha_inicio_guardias_input.setEnabled(True)
                self.fecha_inicio_guardias_input.setDate(
                    QDate(
                        profesor.fecha_inicio_guardias.year,
                        profesor.fecha_inicio_guardias.month,
                        profesor.fecha_inicio_guardias.day,
                    )
                )
            # Si no hay inicio, cargar fecha fin si existe
            elif profesor.fecha_fin_guardias:
                self.usar_fecha_fin_checkbox.setChecked(True)
                self.fecha_fin_guardias_input.setEnabled(True)
                self.fecha_fin_guardias_input.setDate(
                    QDate(
                        profesor.fecha_fin_guardias.year,
                        profesor.fecha_fin_guardias.month,
                        profesor.fecha_fin_guardias.day,
                    )
                )

            # Cargar restricciones de horario (matriz día × recreo)
            if profesor.recreos_permitidos:
                # Si tiene datos en recreos_permitidos, asumimos formato JSON nuevo
                self.usar_restricciones_horario_checkbox.setChecked(True)
                self._json_a_matriz(profesor.recreos_permitidos)
            else:
                # Si no hay datos, dejar desactivado
                self.usar_restricciones_horario_checkbox.setChecked(False)
                self._marcar_todos_matriz(False)

            # Activar modo edición
            self.profesor_editando_id = id_profesor
            self.titulo_seccion.setText(f"✏️ EDITAR PROFESOR [ID: {id_profesor}]")
            self.submit_btn.setText("💾 Actualizar Profesor")
            self.cancelar_btn.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar profesor: {e}")
        finally:
            session.close()

    def eliminar_profesor(self):
        """Eliminar el profesor seleccionado"""
        # Obtener la fila seleccionada
        fila_actual = self.tabla_profesores.currentRow()
        if fila_actual < 0:
            QMessageBox.warning(
                self, "Sin selección", "Selecciona un profesor para eliminar."
            )
            return

        # Extraer ID y nombre del profesor (el ID está guardado en la columna 0)
        nombre_item = self.tabla_profesores.item(fila_actual, 0)
        if not nombre_item:
            return

        id_profesor = nombre_item.data(Qt.ItemDataRole.UserRole)
        nombre_profesor = nombre_item.text()

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar profesor '{nombre_profesor}' (ID {id_profesor})?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                profesor = session.query(Profesor).filter(
                    Profesor.id == id_profesor
                ).first()
                if profesor:
                    session.delete(profesor)
                    session.commit()
                    QMessageBox.information(
                        self, "Éxito", "Profesor eliminado correctamente."
                    )
                    self.cargar_profesores()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {e}")
            finally:
                session.close()


# ==============================================================================
# ZonaForm - Movida a src/presentation/forms/zona_form.py
# La clase antigua ha sido eliminada y reemplazada por versión refactorizada
# que sigue el patrón MVP (Sprint 4)
# ==============================================================================

# ==============================================================================
# AsignacionGuardiasForm - Movida a src/presentation/forms/asignacion_guardias_form.py
# La clase antigua ha sido eliminada y reemplazada por versión refactorizada
# que sigue el patrón MVP (Sprint 4)
# ==============================================================================


class ImportExportForm(QWidget):
    """Formulario para importar y exportar datos de la aplicación."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Importar / Exportar Datos")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Exporta todos los datos de la aplicación (profesores, zonas, "
            "configuración, guardias)\n"
            "a un archivo JSON para copiar a otro equipo o hacer respaldo.\n\n"
            "También puedes importar datos desde un archivo JSON exportado previamente."
        )
        layout.addWidget(desc)

        # Sección de exportación
        export_label = QLabel("EXPORTAR DATOS")
        export_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(export_label)

        export_info = QLabel(
            "Exporta todos los datos actuales de la base de datos a un archivo JSON."
        )
        layout.addWidget(export_info)

        self.exportar_btn = QPushButton("Exportar a JSON...")
        self.exportar_btn.clicked.connect(self.exportar_datos)
        layout.addWidget(self.exportar_btn)

        # Sección de importación
        import_label = QLabel("IMPORTAR DATOS")
        import_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(import_label)

        import_info = QLabel(
            "Importa datos desde un archivo JSON.\n"
            "⚠️ ATENCIÓN: Esto ELIMINARÁ todos los datos actuales y los reemplazará "
            "con los del archivo."
        )
        import_info.setStyleSheet("color: #d63031;")
        layout.addWidget(import_info)

        self.limpiar_checkbox = QCheckBox(
            "Eliminar datos existentes antes de importar (recomendado)"
        )
        self.limpiar_checkbox.setChecked(True)
        layout.addWidget(self.limpiar_checkbox)

        self.importar_btn = QPushButton("Importar desde JSON...")
        self.importar_btn.clicked.connect(self.importar_datos)
        layout.addWidget(self.importar_btn)

        # Sección de exportación a PDF
        pdf_label = QLabel("EXPORTAR A PDF")
        pdf_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        layout.addWidget(pdf_label)

        pdf_info = QLabel(
            "Genera calendarios individuales en PDF para cada profesor con sus guardias."
        )
        layout.addWidget(pdf_info)

        pdf_form_layout = QHBoxLayout()

        pdf_mes_label = QLabel("Mes:")
        pdf_mes_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        pdf_form_layout.addWidget(pdf_mes_label)

        self.pdf_mes_combo = QComboBox()
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.pdf_mes_combo.addItems(meses)
        # Seleccionar mes actual
        from datetime import datetime
        self.pdf_mes_combo.setCurrentIndex(datetime.now().month - 1)
        pdf_form_layout.addWidget(self.pdf_mes_combo)

        pdf_anio_label = QLabel("Año:")
        pdf_anio_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        pdf_form_layout.addWidget(pdf_anio_label)

        self.pdf_anio_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_anio_combo.addItem(str(anio))
        self.pdf_anio_combo.setCurrentIndex(1)  # Año actual
        pdf_form_layout.addWidget(self.pdf_anio_combo)

        layout.addLayout(pdf_form_layout)

        self.exportar_pdf_btn = QPushButton("📄 Generar PDFs para todos los profesores...")
        self.exportar_pdf_btn.clicked.connect(self.exportar_pdfs)
        self.exportar_pdf_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            """
        )
        layout.addWidget(self.exportar_pdf_btn)

        # Resultado
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(200)
        layout.addWidget(self.resultado_text)

        layout.addStretch()
        self.setLayout(layout)

    def exportar_datos(self):
        """Exporta todos los datos a un archivo JSON."""
        try:
            # Diálogo para seleccionar archivo de destino
            archivo, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar datos",
                "guardias_patio_export.json",
                "Archivos JSON (*.json)",
            )

            if not archivo:
                return  # Usuario canceló

            session = SessionLocal()
            try:
                ExportadorDatos.exportar_todo(session, archivo)

                # Mostrar resumen
                prof_count = session.query(Profesor).count()
                zona_count = session.query(Zona).count()
                config_count = session.query(Configuracion).count()

                mensaje = (
                    f"✅ Datos exportados exitosamente a:\n{archivo}\n\n"
                    f"Datos exportados:\n"
                    f"• Profesores: {prof_count}\n"
                    f"• Zonas: {zona_count}\n"
                    f"• Configuración: {config_count}\n"
                )

                self.resultado_text.setText(mensaje)
                QMessageBox.information(self, "Éxito", "Datos exportados correctamente.")

            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar: {e}")
            self.resultado_text.setText(f"❌ Error al exportar: {e}")

    def importar_datos(self):
        """Importa datos desde un archivo JSON."""
        try:
            # Confirmación previa
            limpiar = self.limpiar_checkbox.isChecked()
            if limpiar:
                respuesta = QMessageBox.question(
                    self,
                    "Confirmar importación",
                    "⚠️ ATENCIÓN: Se eliminarán TODOS los datos actuales.\n\n"
                    "¿Está seguro de que desea continuar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if respuesta != QMessageBox.StandardButton.Yes:
                    return

            # Diálogo para seleccionar archivo
            archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Importar datos",
                "",
                "Archivos JSON (*.json)",
            )

            if not archivo:
                return  # Usuario canceló

            session = SessionLocal()
            try:
                resultado = ExportadorDatos.importar_todo(session, archivo, limpiar)

                mensaje = (
                    f"✅ Datos importados exitosamente desde:\n{archivo}\n\n"
                    f"Datos importados:\n"
                    f"• Profesores: {resultado['profesores']}\n"
                    f"• Zonas: {resultado['zonas']}\n"
                    f"• Configuración: {resultado['configuracion']}\n"
                    f"• Guardias: {resultado['guardias']}\n"
                )

                self.resultado_text.setText(mensaje)
                QMessageBox.information(
                    self,
                    "Éxito",
                    "Datos importados correctamente.\n\n"
                    "Se recomienda reiniciar la aplicación para ver los cambios.",
                )

            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al importar: {e}")
            self.resultado_text.setText(f"❌ Error al importar: {e}")

    def exportar_pdfs(self):
        """Exporta calendarios PDF para todos los profesores."""
        try:
            # Obtener mes y año seleccionados
            mes = self.pdf_mes_combo.currentIndex() + 1
            anio = int(self.pdf_anio_combo.currentText())

            # Diálogo para seleccionar carpeta de destino
            carpeta = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta para guardar PDFs",
                "",
                QFileDialog.Option.ShowDirsOnly
            )

            if not carpeta:
                return  # Usuario canceló

            session = SessionLocal()
            try:
                # Generar PDFs
                exitos = ExportadorPDF.exportar_todos_los_profesores(
                    session, mes, anio, carpeta
                )

                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

                mensaje = (
                    f"✅ PDFs generados exitosamente\n\n"
                    f"Mes: {meses[mes]} {anio}\n"
                    f"Carpeta: {carpeta}\n"
                    f"PDFs generados: {exitos}\n"
                )

                self.resultado_text.setText(mensaje)
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Se generaron {exitos} calendarios PDF correctamente."
                )

            finally:
                session.close()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al generar PDFs: {e}")
            self.resultado_text.setText(f"❌ Error al generar PDFs: {e}")


class CalendarioGuardiasForm(QWidget):
    """Formulario para visualizar el calendario de guardias asignadas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Calendario de Guardias")
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Calendario de Guardias")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Visualiza las guardias asignadas por fecha. "
            "Selecciona un día en el calendario para ver los detalles."
        )
        layout.addWidget(desc)

        # Layout horizontal para calendario y filtros
        main_horizontal = QHBoxLayout()

        # Panel izquierdo: Calendario
        calendar_panel = QVBoxLayout()
        calendar_label = QLabel("Selecciona una fecha:")
        calendar_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        calendar_panel.addWidget(calendar_label)

        self.calendario = QCalendarWidget()
        self.calendario.setGridVisible(True)
        self.calendario.clicked.connect(self.actualizar_guardias_dia)
        calendar_panel.addWidget(self.calendario)

        main_horizontal.addLayout(calendar_panel)

        # Panel derecho: Filtros y detalles
        right_panel = QVBoxLayout()

        # Filtros
        filtros_label = QLabel("Filtros:")
        filtros_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        right_panel.addWidget(filtros_label)

        # Filtro por profesor
        label_profesor_filtro = QLabel("Profesor:")
        label_profesor_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        right_panel.addWidget(label_profesor_filtro)
        self.filtro_profesor = QComboBox()
        self.filtro_profesor.addItem("Todos los profesores", None)
        self.filtro_profesor.currentIndexChanged.connect(self.aplicar_filtros)
        right_panel.addWidget(self.filtro_profesor)

        # Filtro por zona
        label_zona_filtro = QLabel("Zona:")
        label_zona_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        right_panel.addWidget(label_zona_filtro)
        self.filtro_zona = QComboBox()
        self.filtro_zona.addItem("Todas las zonas", None)
        self.filtro_zona.currentIndexChanged.connect(self.aplicar_filtros)
        right_panel.addWidget(self.filtro_zona)

        # Filtro por turno
        label_turno_filtro = QLabel("Turno:")
        label_turno_filtro.setStyleSheet(styles.STYLE_LABEL_FIELD)
        right_panel.addWidget(label_turno_filtro)
        self.filtro_turno = QComboBox()
        self.filtro_turno.addItems(["Todos", "mañana", "tarde"])
        self.filtro_turno.currentIndexChanged.connect(self.aplicar_filtros)
        right_panel.addWidget(self.filtro_turno)

        # Botón para limpiar filtros
        self.limpiar_filtros_btn = QPushButton("Limpiar filtros")
        self.limpiar_filtros_btn.clicked.connect(self.limpiar_filtros)
        right_panel.addWidget(self.limpiar_filtros_btn)

        # Detalles del día seleccionado
        detalles_label = QLabel("Guardias del día seleccionado:")
        detalles_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 20px;")
        right_panel.addWidget(detalles_label)

        self.guardias_dia_text = QTextEdit()
        self.guardias_dia_text.setReadOnly(True)
        self.guardias_dia_text.setMaximumHeight(400)
        right_panel.addWidget(self.guardias_dia_text)

        # Estadísticas
        stats_label = QLabel("Estadísticas:")
        stats_label.setStyleSheet(styles.STYLE_LABEL_FIELD + " margin-top: 10px;")
        right_panel.addWidget(stats_label)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(150)
        right_panel.addWidget(self.stats_text)

        main_horizontal.addLayout(right_panel)

        layout.addLayout(main_horizontal)
        self.setLayout(layout)

        # Cargar datos iniciales
        self.cargar_filtros()
        self.actualizar_estadisticas()
        self.actualizar_guardias_dia(self.calendario.selectedDate())

    def cargar_filtros(self):
        """Carga las opciones de los filtros desde la base de datos."""
        session = SessionLocal()
        try:
            # Cargar profesores
            profesores = session.query(Profesor).all()
            self.filtro_profesor.clear()
            self.filtro_profesor.addItem("Todos los profesores", None)
            for prof in profesores:
                self.filtro_profesor.addItem(
                    prof.nombre_completo, prof.id
                )

            # Cargar zonas
            zonas = session.query(Zona).all()
            self.filtro_zona.clear()
            self.filtro_zona.addItem("Todas las zonas", None)
            for zona in zonas:
                self.filtro_zona.addItem(zona.nombre_zona, zona.id)

        finally:
            session.close()

    def limpiar_filtros(self):
        """Limpia todos los filtros y vuelve a mostrar todas las guardias."""
        self.filtro_profesor.setCurrentIndex(0)
        self.filtro_zona.setCurrentIndex(0)
        self.filtro_turno.setCurrentIndex(0)

    def aplicar_filtros(self):
        """Aplica los filtros y actualiza la visualización."""
        self.actualizar_guardias_dia(self.calendario.selectedDate())
        self.actualizar_estadisticas()

    def actualizar_guardias_dia(self, qdate):
        """Actualiza la visualización de guardias para el día seleccionado."""
        fecha = qdate.toPyDate()
        session = SessionLocal()
        try:
            # Construir query base
            query = session.query(Guardia).filter(Guardia.fecha == fecha)

            # Aplicar filtros
            profesor_id = self.filtro_profesor.currentData()
            if profesor_id is not None:
                query = query.filter(Guardia.profesor_id == profesor_id)

            zona_id = self.filtro_zona.currentData()
            if zona_id is not None:
                query = query.filter(Guardia.zona_id == zona_id)

            turno_filtro = self.filtro_turno.currentText()
            if turno_filtro != "Todos":
                query = query.filter(Guardia.turno == turno_filtro)

            guardias = query.all()

            # Formatear y mostrar
            if not guardias:
                self.guardias_dia_text.setText(
                    f"📅 {fecha.strftime('%d/%m/%Y')}\n\n"
                    "No hay guardias asignadas para este día con los filtros aplicados."
                )
            else:
                lineas = [f"📅 {fecha.strftime('%d/%m/%Y')} - {len(guardias)} guardia(s)\n"]

                # Agrupar por turno y recreo
                guardias_por_turno = {}
                for g in guardias:
                    key = (g.turno, g.recreo)
                    if key not in guardias_por_turno:
                        guardias_por_turno[key] = []
                    guardias_por_turno[key].append(g)

                # Mostrar organizadas
                for (turno, recreo), guardias_grupo in sorted(guardias_por_turno.items()):
                    lineas.append(f"\n🕐 {turno.upper()} - Recreo {recreo}")
                    lineas.append("─" * 40)
                    for g in guardias_grupo:
                        prof_nombre = (
                            g.profesor.nombre_completo
                            if g.profesor
                            else "Sin profesor"
                        )
                        zona_nombre = g.zona.nombre_zona if g.zona else "Sin zona"
                        lineas.append(f"  • {prof_nombre} → {zona_nombre}")

                self.guardias_dia_text.setText("\n".join(lineas))

        finally:
            session.close()

    def actualizar_estadisticas(self):
        """Actualiza las estadísticas generales."""
        session = SessionLocal()
        try:
            # Construir query base
            query = session.query(Guardia)

            # Aplicar filtros
            profesor_id = self.filtro_profesor.currentData()
            if profesor_id is not None:
                query = query.filter(Guardia.profesor_id == profesor_id)

            zona_id = self.filtro_zona.currentData()
            if zona_id is not None:
                query = query.filter(Guardia.zona_id == zona_id)

            turno_filtro = self.filtro_turno.currentText()
            if turno_filtro != "Todos":
                query = query.filter(Guardia.turno == turno_filtro)

            total_guardias = query.count()

            # Contar por turno
            guardias_manana = (
                query.filter(Guardia.turno == "mañana").count()
                if turno_filtro == "Todos"
                else (total_guardias if turno_filtro == "mañana" else 0)
            )
            guardias_tarde = (
                query.filter(Guardia.turno == "tarde").count()
                if turno_filtro == "Todos"
                else (total_guardias if turno_filtro == "tarde" else 0)
            )

            lineas = [
                f"📊 Total guardias: {total_guardias}",
                f"🌅 Mañana: {guardias_manana}",
                f"🌆 Tarde: {guardias_tarde}",
            ]

            # Si hay filtro de profesor, mostrar estadísticas personales
            if profesor_id is not None:
                profesor = session.query(Profesor).get(profesor_id)
                if profesor:
                    lineas.append(
                        f"\n👤 {profesor.nombre_completo}"
                    )
                    lineas.append(f"   Turno: {profesor.turno}")
                    lineas.append(f"   Tutor: {'Sí' if profesor.tutor else 'No'}")

            self.stats_text.setText("\n".join(lineas))

        finally:
            session.close()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guardias de Patio - Gestión")
        self.layout = QVBoxLayout()

        # Crear sesión para widgets que la necesiten
        self.session = SessionLocal()

        # Configurar atajos de teclado globales
        self._configurar_atajos_globales()

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()
        self.tabs.addTab(ProfesorForm(), "👨‍🏫 Profesores")
        # Usar ZonaForm refactorizado (Sprint 4)
        self.tabs.addTab(ZonaFormRefactorizado(self.session), "🏫 Zonas")
        # Usar ConfiguracionForm refactorizado (Sprint 4)
        self.tabs.addTab(ConfiguracionFormRefactorizado(self.session), "⚙️ Configuración")
        # Usar AsignacionGuardiasForm refactorizado (Sprint 4)
        self.tabs.addTab(
            AsignacionGuardiasFormRefactorizado(self.session),
            "🎯 Asignación de Guardias",
        )
        self.tabs.addTab(GestionarAusenciasForm(), "🏥 Ausencias")

        # NUEVAS PESTAÑAS
        self.vista_calendario = VistaCalendario(self.session)
        self.tabs.addTab(self.vista_calendario, "📅 Vista Calendario")

        self.panel_estadisticas = PanelEstadisticas(self.session)
        self.tabs.addTab(self.panel_estadisticas, "📊 Estadísticas")

        self.gestor_sustituciones = GestorSustituciones(self.session)
        self.tabs.addTab(self.gestor_sustituciones, "🔄 Sustituciones")

        self.tabs.addTab(CalendarioGuardiasForm(), "📆 Calendario (Antiguo)")
        self.tabs.addTab(ImportExportForm(), "💾 Importar / Exportar")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

        # Conectar señal de cambio de pestaña para refrescar widgets
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def _configurar_atajos_globales(self):
        """Configurar atajos de teclado globales"""
        # Ctrl+Tab: Siguiente pestaña
        atajo_siguiente = QShortcut(QKeySequence("Ctrl+Tab"), self)
        atajo_siguiente.activated.connect(self._siguiente_pestana)

        # Ctrl+Shift+Tab: Pestaña anterior
        atajo_anterior = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        atajo_anterior.activated.connect(self._pestana_anterior)

        # Ctrl+Q: Salir
        atajo_salir = QShortcut(QKeySequence("Ctrl+Q"), self)
        atajo_salir.activated.connect(self.close)

    def _siguiente_pestana(self):
        """Cambiar a la siguiente pestaña"""
        index_actual = self.tabs.currentIndex()
        siguiente = (index_actual + 1) % self.tabs.count()
        self.tabs.setCurrentIndex(siguiente)

    def _pestana_anterior(self):
        """Cambiar a la pestaña anterior"""
        index_actual = self.tabs.currentIndex()
        anterior = (index_actual - 1) % self.tabs.count()
        self.tabs.setCurrentIndex(anterior)

    def on_tab_changed(self, index):
        """Refresca los widgets cuando se cambia de pestaña."""
        # Refrescar calendario si se muestra
        if self.tabs.widget(index) == self.vista_calendario:
            self.vista_calendario.refrescar()
        # Refrescar estadísticas si se muestran
        elif self.tabs.widget(index) == self.panel_estadisticas:
            self.panel_estadisticas.refrescar()
        # Refrescar sustituciones si se muestran
        elif self.tabs.widget(index) == self.gestor_sustituciones:
            self.gestor_sustituciones.refrescar()

    def closeEvent(self, event):
        """Cierra la sesión al cerrar la ventana."""
        self.session.close()
        event.accept()

def main():
    # Mensaje de smoke test siempre visible (usado por tests)
    print("¡Hola mundo desde Guardias de Patio!")

    # Modo prueba: cuando pytest ejecuta este archivo en un subproceso, evitamos levantar la GUI
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return

    # Fix for Qt platform plugin error
    # This sets the correct path for Qt plugins, often an issue in bundled applications
    # or specific environments.
    try:
        import PyQt6
        qt_plugin_path = os.path.join(os.path.dirname(PyQt6.__file__), "Qt", "plugins")
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = qt_plugin_path
        print(f"Setting QT_QPA_PLATFORM_PLUGIN_PATH to: {qt_plugin_path}")
    except Exception as e:
        print(f"Warning: Could not set QT_QPA_PLATFORM_PLUGIN_PATH: {e}")

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
