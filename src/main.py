import os
import sys

import ui_styles as styles
from database.db_manager import SessionLocal
from models.models import Configuracion, Guardia, Profesor, Zona
from services.calculador_guardias import (
    calcular_guardias_por_profesor,
    obtener_estadisticas,
)
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from utils import constants, setup_logging
from utils.validators import (
    validar_email,
    validar_horas_contrato,
    validar_nombre_completo,
)
from widgets.gestionar_sustituciones import GestorSustituciones
from widgets.panel_estadisticas import PanelEstadisticas
from widgets.vista_calendario import VistaCalendario

# Configurar logging al inicio
setup_logging()

GUI_AVAILABLE = True
try:
    from PyQt6.QtCore import QDate, Qt, QTime
    from PyQt6.QtWidgets import (
        QApplication,
        QCalendarWidget,
        QCheckBox,
        QComboBox,
        QDateEdit,
        QFileDialog,
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

        # Layout principal horizontal: Tabla a la izquierda, Formulario a la derecha
        main_layout = QHBoxLayout()

        # ========== SECCIÓN IZQUIERDA: LISTA DE PROFESORES ==========
        left_section = QVBoxLayout()
        left_section.setContentsMargins(10, 10, 10, 10)
        left_section.setSpacing(10)

        titulo_lista = QLabel("📋 PROFESORES REGISTRADOS")
        titulo_lista.setStyleSheet(styles.STYLE_TITLE_MAIN)
        left_section.addWidget(titulo_lista)        # Tabla de profesores con columnas
        self.tabla_profesores = QTableWidget()
        self.tabla_profesores.setColumnCount(6)
        self.tabla_profesores.setHorizontalHeaderLabels([
            "ID", "Nombre Completo", "Email", "Horas", "Turno", "Tutor"
        ])
        # Hacer que la columna de nombre se estire para ocupar espacio disponible
        self.tabla_profesores.horizontalHeader().setStretchLastSection(False)
        self.tabla_profesores.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        # Hacer las demás columnas ajustables al contenido
        for i in [0, 2, 3, 4, 5]:
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

        self.editar_btn = QPushButton("✏️ Editar")
        self.editar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        self.editar_btn.clicked.connect(self.editar_profesor)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_profesor)

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
        label_nombre.setStyleSheet("font-size: 12px; color: #555;")
        layout_basicos.addWidget(label_nombre)
        self.nombre_completo_input = QLineEdit()
        self.nombre_completo_input.setPlaceholderText("GARCÍA LÓPEZ, JUAN")
        self.nombre_completo_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_completo_input.setMaximumWidth(350)
        layout_basicos.addWidget(self.nombre_completo_input)

        label_email = QLabel("Email corporativo:")
        label_email.setStyleSheet("font-size: 12px; color: #555;")
        layout_basicos.addWidget(label_email)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("profesor@colegio.edu")
        self.email_input.setStyleSheet(styles.STYLE_INPUT)
        self.email_input.setMaximumWidth(350)
        layout_basicos.addWidget(self.email_input)

        self.tutor_checkbox = QCheckBox("✓ Es tutor/a")
        self.tutor_checkbox.setStyleSheet("font-size: 13px; margin-top: 5px;")
        layout_basicos.addWidget(self.tutor_checkbox)

        grupo_basicos.setLayout(layout_basicos)
        right_section.addWidget(grupo_basicos)

        # ===== GRUPO: Configuración de Horario =====
        grupo_horario = QGroupBox("🕐 Configuración de Horario")
        grupo_horario.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_horario = QVBoxLayout()
        layout_horario.setSpacing(8)

        label_horas = QLabel("Horas de contrato (total):")
        label_horas.setStyleSheet("font-size: 12px; color: #555;")
        layout_horario.addWidget(label_horas)
        self.horas_input = QLineEdit()
        self.horas_input.setPlaceholderText("Ej: 30.0")
        self.horas_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_input.setMaximumWidth(150)
        layout_horario.addWidget(self.horas_input)

        label_turno = QLabel("Turno:")
        label_turno.setStyleSheet("font-size: 12px; color: #555;")
        layout_horario.addWidget(label_turno)
        self.turno_input = QComboBox()
        self.turno_input.addItems(["mañana", "tarde", "mixto"])
        self.turno_input.setStyleSheet(styles.STYLE_INPUT)
        self.turno_input.setMaximumWidth(200)
        layout_horario.addWidget(self.turno_input)

        # Campos para turno mixto (inicialmente ocultos)
        self.label_horas_manana = QLabel("Horas de mañana:")
        self.label_horas_manana.setStyleSheet("font-size: 12px; color: #555;")
        self.horas_manana_input = QLineEdit()
        self.horas_manana_input.setPlaceholderText("Ej: 15.0")
        self.horas_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_manana_input.setMaximumWidth(150)
        layout_horario.addWidget(self.label_horas_manana)
        layout_horario.addWidget(self.horas_manana_input)

        self.label_horas_tarde = QLabel("Horas de tarde:")
        self.label_horas_tarde.setStyleSheet("font-size: 12px; color: #555;")
        self.horas_tarde_input = QLineEdit()
        self.horas_tarde_input.setPlaceholderText("Ej: 15.0")
        self.horas_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.horas_tarde_input.setMaximumWidth(150)
        layout_horario.addWidget(self.label_horas_tarde)
        layout_horario.addWidget(self.horas_tarde_input)

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

        label_fecha = QLabel("Fecha de inicio de guardias (opcional):")
        label_fecha.setStyleSheet("font-size: 12px; color: #555;")
        layout_restricciones.addWidget(label_fecha)
        self.fecha_inicio_guardias_input = QDateEdit()
        self.fecha_inicio_guardias_input.setCalendarPopup(True)
        self.fecha_inicio_guardias_input.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio_guardias_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_guardias_input.setMaximumWidth(200)
        layout_restricciones.addWidget(self.fecha_inicio_guardias_input)

        label_dias = QLabel("Días de la semana permitidos (opcional):")
        label_dias.setStyleSheet("font-size: 12px; color: #555;")
        layout_restricciones.addWidget(label_dias)
        self.dias_semana_input = QLineEdit()
        self.dias_semana_input.setPlaceholderText("Ej: 0,1,2,3,4 (0=Lun, 6=Dom)")
        self.dias_semana_input.setStyleSheet(styles.STYLE_INPUT)
        self.dias_semana_input.setMaximumWidth(250)
        layout_restricciones.addWidget(self.dias_semana_input)

        label_recreos = QLabel("Recreos permitidos (opcional):")
        label_recreos.setStyleSheet("font-size: 12px; color: #555;")
        layout_restricciones.addWidget(label_recreos)
        self.recreos_permitidos_input = QLineEdit()
        self.recreos_permitidos_input.setPlaceholderText("Ej: 1,2 (IDs de recreo)")
        self.recreos_permitidos_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreos_permitidos_input.setMaximumWidth(250)
        layout_restricciones.addWidget(self.recreos_permitidos_input)

        grupo_restricciones.setLayout(layout_restricciones)
        right_section.addWidget(grupo_restricciones)

        # Botones de acción con estilos
        botones_accion = QHBoxLayout()
        botones_accion.setSpacing(10)

        self.submit_btn = QPushButton("💾 Guardar Profesor")
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
        self._toggle_mixto_fields(value == "mixto")

    def _limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.nombre_completo_input.clear()
        self.email_input.clear()
        self.horas_input.clear()
        self.horas_manana_input.clear()
        self.horas_tarde_input.clear()
        self.tutor_checkbox.setChecked(False)
        self.fecha_inicio_guardias_input.clear()
        self.dias_semana_input.clear()
        self.recreos_permitidos_input.clear()
        self.turno_input.setCurrentIndex(0)
        # Resetear modo edición
        self.profesor_editando_id = None
        self.titulo_seccion.setText("✏️ ALTA DE PROFESOR")
        self.submit_btn.setText("💾 Guardar Profesor")
        self.cancelar_btn.setVisible(False)

    def cancelar_edicion(self):
        """Cancelar la edición actual y volver a modo creación"""
        self._limpiar_formulario()
        QMessageBox.information(self, "Cancelado", "Edición cancelada.")

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

            turno = self.turno_input.currentText()
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
            fecha_inicio_guardias = (
                self.fecha_inicio_guardias_input.date().toPyDate()
                if self.fecha_inicio_guardias_input.date().isValid() else None
            )
            dias_semana_permitidos = self.dias_semana_input.text().strip()
            recreos_permitidos = self.recreos_permitidos_input.text().strip()

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
                    profesor.tutor = tutor
                    profesor.fecha_inicio_guardias = fecha_inicio_guardias
                    profesor.dias_semana_permitidos = dias_semana_permitidos or None
                    profesor.recreos_permitidos = recreos_permitidos or None
                    session.commit()
                    QMessageBox.information(
                        self,
                        "Éxito",
                        f"Profesor actualizado correctamente. Porcentaje jornada: {porcentaje:.2f}",
                    )
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
                    tutor=tutor,
                    fecha_inicio_guardias=fecha_inicio_guardias,
                    dias_semana_permitidos=dias_semana_permitidos or None,
                    recreos_permitidos=recreos_permitidos or None,
                )
                session.add(nuevo_profesor)
                session.commit()
                QMessageBox.information(
                    self,
                    "Éxito",
                    f"Profesor guardado correctamente. Porcentaje jornada: {porcentaje:.2f}",
                )

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
            self.tabla_profesores.setRowCount(len(profesores))

            for i, prof in enumerate(profesores):
                # ID
                id_item = QTableWidgetItem(str(prof.id))
                id_item.setData(Qt.ItemDataRole.UserRole, prof.id)  # Guardar ID
                self.tabla_profesores.setItem(i, 0, id_item)

                # Nombre completo
                self.tabla_profesores.setItem(
                    i, 1, QTableWidgetItem(prof.nombre_completo or "")
                )

                # Email
                self.tabla_profesores.setItem(
                    i, 2, QTableWidgetItem(prof.email_corporativo or "-")
                )

                # Horas
                self.tabla_profesores.setItem(
                    i, 3, QTableWidgetItem(f"{prof.horas_contrato:.1f}h")
                )

                # Turno
                self.tabla_profesores.setItem(
                    i, 4, QTableWidgetItem(prof.turno.capitalize())
                )

                # Tutor
                tutor_text = "Sí" if prof.tutor else "No"
                self.tabla_profesores.setItem(i, 5, QTableWidgetItem(tutor_text))

            # Reactivar ordenación
            self.tabla_profesores.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar profesores: {e}")
        finally:
            session.close()

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

            # Seleccionar turno
            index = self.turno_input.findText(profesor.turno)
            if index >= 0:
                self.turno_input.setCurrentIndex(index)

            # Cargar checkbox tutor
            self.tutor_checkbox.setChecked(profesor.tutor or False)

            # Cargar fecha inicio guardias
            if profesor.fecha_inicio_guardias:
                self.fecha_inicio_guardias_input.setDate(
                    QDate(
                        profesor.fecha_inicio_guardias.year,
                        profesor.fecha_inicio_guardias.month,
                        profesor.fecha_inicio_guardias.day,
                    )
                )
            else:
                self.fecha_inicio_guardias_input.clear()

            # Cargar restricciones
            self.dias_semana_input.setText(profesor.dias_semana_permitidos or "")
            self.recreos_permitidos_input.setText(profesor.recreos_permitidos or "")

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

        # Extraer ID y nombre del profesor
        id_item = self.tabla_profesores.item(fila_actual, 0)
        nombre_item = self.tabla_profesores.item(fila_actual, 1)
        if not id_item or not nombre_item:
            return

        id_profesor = id_item.data(Qt.ItemDataRole.UserRole)
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

class ZonaForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Zonas")

        # Layout principal horizontal
        main_layout = QHBoxLayout()

        # ========== SECCIÓN IZQUIERDA: LISTA DE ZONAS ==========
        left_section = QVBoxLayout()
        left_section.setContentsMargins(10, 10, 10, 10)
        left_section.setSpacing(10)

        titulo_lista = QLabel("🏫 ZONAS REGISTRADAS")
        titulo_lista.setStyleSheet(styles.STYLE_TITLE_MAIN)
        left_section.addWidget(titulo_lista)

        self.lista_zonas = QListWidget()
        self.lista_zonas.setStyleSheet("""
            QListWidget {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        left_section.addWidget(self.lista_zonas)

        # Botones de gestión
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_zonas)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_zona)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        left_section.addLayout(btn_layout)

        # ========== SECCIÓN DERECHA: FORMULARIO DE ALTA ==========
        right_section = QVBoxLayout()
        right_section.setContentsMargins(10, 0, 10, 10)
        right_section.setSpacing(12)

        titulo_form = QLabel("✏️ NUEVA ZONA")
        titulo_form.setStyleSheet(styles.STYLE_TITLE_MAIN)
        right_section.addWidget(titulo_form)

        # Grupo de datos
        grupo_datos = QGroupBox("📋 Datos de la Zona")
        grupo_datos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_datos = QVBoxLayout()
        layout_datos.setSpacing(8)

        label_nombre = QLabel("Nombre de la zona:")
        label_nombre.setStyleSheet("font-size: 12px; color: #555;")
        layout_datos.addWidget(label_nombre)
        self.nombre_zona_input = QLineEdit()
        self.nombre_zona_input.setPlaceholderText("Ej: Patio Principal, Porche, etc.")
        self.nombre_zona_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_zona_input.setMaximumWidth(350)
        layout_datos.addWidget(self.nombre_zona_input)

        label_desc = QLabel("Descripción (opcional):")
        label_desc.setStyleSheet("font-size: 12px; color: #555;")
        layout_datos.addWidget(label_desc)
        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Detalles adicionales sobre la zona")
        self.descripcion_input.setStyleSheet(styles.STYLE_INPUT)
        self.descripcion_input.setMaximumWidth(350)
        layout_datos.addWidget(self.descripcion_input)

        grupo_datos.setLayout(layout_datos)
        right_section.addWidget(grupo_datos)

        # Botón de guardar
        self.submit_btn = QPushButton("💾 Guardar Zona")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_zona)
        right_section.addWidget(self.submit_btn)

        # Espacio flexible
        right_section.addStretch()

        # ========== ENSAMBLAR LAYOUT PRINCIPAL ==========
        main_layout.addLayout(left_section, 60)
        main_layout.addLayout(right_section, 40)

        self.setLayout(main_layout)
        self.cargar_zonas()  # Cargar al inicio

    def guardar_zona(self):
        session = SessionLocal()
        try:
            nombre_zona = self.nombre_zona_input.text()
            descripcion = self.descripcion_input.text()

            if not nombre_zona:
                QMessageBox.warning(self, "Falta nombre", "Debes indicar el nombre de la zona.")
                return

            nueva_zona = Zona(nombre_zona=nombre_zona, descripcion=descripcion)
            session.add(nueva_zona)
            session.commit()
            QMessageBox.information(self, "Éxito", f"Zona '{nombre_zona}' guardada correctamente.")
            self.nombre_zona_input.clear()
            self.descripcion_input.clear()
            self.cargar_zonas()  # Actualizar lista tras guardar
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

    def cargar_zonas(self):
        """Cargar la lista de zonas desde la base de datos"""
        self.lista_zonas.clear()
        session = SessionLocal()
        try:
            zonas = session.query(Zona).all()
            for zona in zonas:
                desc = zona.descripcion if zona.descripcion else "Sin descripción"
                texto = f"[{zona.id}] {zona.nombre_zona} - {desc}"
                self.lista_zonas.addItem(texto)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar zonas: {e}")
        finally:
            session.close()

    def eliminar_zona(self):
        """Eliminar la zona seleccionada"""
        item_actual = self.lista_zonas.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Sin selección", "Selecciona una zona para eliminar.")
            return

        # Extraer ID del texto [ID] nombre...
        texto = item_actual.text()
        id_zona = int(texto.split("]")[0].replace("[", ""))

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar zona con ID {id_zona}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                zona = session.query(Zona).filter(Zona.id == id_zona).first()
                if zona:
                    session.delete(zona)
                    session.commit()
                    QMessageBox.information(self, "Éxito", "Zona eliminada correctamente.")
                    self.cargar_zonas()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {e}")
            finally:
                session.close()


class ConfiguracionForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuración del Curso")
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # Título principal
        titulo = QLabel("⚙️ CONFIGURACIÓN DEL CURSO ESCOLAR")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        self.layout.addWidget(titulo)

        # ===== GRUPO: Fechas del Curso =====
        grupo_fechas = QGroupBox("📅 Fechas del Curso")
        grupo_fechas.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_fechas = QVBoxLayout()
        layout_fechas.setSpacing(8)

        # Fecha inicio
        label_inicio = QLabel("Fecha de inicio del curso:")
        label_inicio.setStyleSheet("font-size: 12px; color: #555;")
        layout_fechas.addWidget(label_inicio)
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.fecha_inicio_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_inicio_input.setMaximumWidth(200)
        layout_fechas.addWidget(self.fecha_inicio_input)

        # Fecha fin
        label_fin = QLabel("Fecha de fin del curso:")
        label_fin.setStyleSheet("font-size: 12px; color: #555;")
        layout_fechas.addWidget(label_fin)
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.fecha_fin_input.setStyleSheet(styles.STYLE_INPUT)
        self.fecha_fin_input.setMaximumWidth(200)
        layout_fechas.addWidget(self.fecha_fin_input)

        grupo_fechas.setLayout(layout_fechas)
        self.layout.addWidget(grupo_fechas)

        # ===== GRUPO: Recreos de Mañana =====
        grupo_manana = QGroupBox("☀️ Recreos de Mañana")
        grupo_manana.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_manana = QHBoxLayout()
        layout_manana.setSpacing(15)

        # Recreo 1 mañana
        col1 = QVBoxLayout()
        col1.setSpacing(5)
        label_r1m = QLabel("Recreo 1:")
        label_r1m.setStyleSheet("font-size: 12px; color: #555;")
        col1.addWidget(label_r1m)
        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.recreo1_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo1_manana_input.setMaximumWidth(120)
        col1.addWidget(self.recreo1_manana_input)
        layout_manana.addLayout(col1)

        # Recreo 2 mañana
        col2 = QVBoxLayout()
        col2.setSpacing(5)
        label_r2m = QLabel("Recreo 2:")
        label_r2m.setStyleSheet("font-size: 12px; color: #555;")
        col2.addWidget(label_r2m)
        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.recreo2_manana_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo2_manana_input.setMaximumWidth(120)
        col2.addWidget(self.recreo2_manana_input)
        layout_manana.addLayout(col2)

        layout_manana.addStretch()
        grupo_manana.setLayout(layout_manana)
        self.layout.addWidget(grupo_manana)

        # ===== GRUPO: Recreos de Tarde =====
        grupo_tarde = QGroupBox("🌙 Recreos de Tarde (opcional)")
        grupo_tarde.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_tarde = QHBoxLayout()
        layout_tarde.setSpacing(15)

        # Recreo 1 tarde
        col3 = QVBoxLayout()
        col3.setSpacing(5)
        label_r1t = QLabel("Recreo 1:")
        label_r1t.setStyleSheet("font-size: 12px; color: #555;")
        col3.addWidget(label_r1t)
        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.recreo1_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo1_tarde_input.setMaximumWidth(120)
        col3.addWidget(self.recreo1_tarde_input)
        layout_tarde.addLayout(col3)

        # Recreo 2 tarde
        col4 = QVBoxLayout()
        col4.setSpacing(5)
        label_r2t = QLabel("Recreo 2:")
        label_r2t.setStyleSheet("font-size: 12px; color: #555;")
        col4.addWidget(label_r2t)
        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setTime(QTime(17, 0))
        self.recreo2_tarde_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreo2_tarde_input.setMaximumWidth(120)
        col4.addWidget(self.recreo2_tarde_input)
        layout_tarde.addLayout(col4)

        layout_tarde.addStretch()
        grupo_tarde.setLayout(layout_tarde)
        self.layout.addWidget(grupo_tarde)

        # ===== GRUPO: Ajustes Adicionales =====
        grupo_ajustes = QGroupBox("🔧 Ajustes Adicionales")
        grupo_ajustes.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_ajustes = QHBoxLayout()
        layout_ajustes.setSpacing(15)

        # Multiplicador tutores
        col5 = QVBoxLayout()
        col5.setSpacing(5)
        label_tutores = QLabel("Multiplicador tutores:")
        label_tutores.setStyleSheet("font-size: 12px; color: #555;")
        col5.addWidget(label_tutores)
        self.ajuste_tutores_input = QLineEdit()
        self.ajuste_tutores_input.setPlaceholderText("0.90")
        self.ajuste_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        self.ajuste_tutores_input.setMaximumWidth(100)
        col5.addWidget(self.ajuste_tutores_input)
        layout_ajustes.addLayout(col5)

        # Multiplicador no tutores
        col6 = QVBoxLayout()
        col6.setSpacing(5)
        label_no_tutores = QLabel("Multiplicador no tutores:")
        label_no_tutores.setStyleSheet("font-size: 12px; color: #555;")
        col6.addWidget(label_no_tutores)
        self.ajuste_no_tutores_input = QLineEdit()
        self.ajuste_no_tutores_input.setPlaceholderText("1.00")
        self.ajuste_no_tutores_input.setStyleSheet(styles.STYLE_INPUT)
        self.ajuste_no_tutores_input.setMaximumWidth(100)
        col6.addWidget(self.ajuste_no_tutores_input)
        layout_ajustes.addLayout(col6)

        layout_ajustes.addStretch()
        grupo_ajustes.setLayout(layout_ajustes)
        self.layout.addWidget(grupo_ajustes)

        # ===== GRUPO: Festivos =====
        grupo_festivos = QGroupBox("🎉 Festivos y Días No Lectivos")
        grupo_festivos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_festivos = QVBoxLayout()
        layout_festivos.setSpacing(8)

        label_auto = QLabel("Aplicar festivos automáticos (1 sí / 0 no):")
        label_auto.setStyleSheet("font-size: 12px; color: #555;")
        layout_festivos.addWidget(label_auto)
        self.festivos_auto_input = QLineEdit()
        self.festivos_auto_input.setPlaceholderText("1")
        self.festivos_auto_input.setStyleSheet(styles.STYLE_INPUT)
        self.festivos_auto_input.setMaximumWidth(100)
        layout_festivos.addWidget(self.festivos_auto_input)

        label_custom = QLabel("Días no lectivos personalizados (YYYY-MM-DD, separados por coma):")
        label_custom.setStyleSheet("font-size: 12px; color: #555;")
        layout_festivos.addWidget(label_custom)
        self.no_lectivos_input = QLineEdit()
        self.no_lectivos_input.setPlaceholderText("2025-10-09, 2025-10-12")
        self.no_lectivos_input.setStyleSheet(styles.STYLE_INPUT)
        self.no_lectivos_input.setMaximumWidth(500)
        layout_festivos.addWidget(self.no_lectivos_input)

        grupo_festivos.setLayout(layout_festivos)
        self.layout.addWidget(grupo_festivos)

        # ===== GRUPO: Avanzado =====
        grupo_avanzado = QGroupBox("🔬 Configuración Avanzada (opcional)")
        grupo_avanzado.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_avanzado = QVBoxLayout()
        layout_avanzado.setSpacing(8)

        label_recreos = QLabel("Recreos configurables JSON (lista de objetos):")
        label_recreos.setStyleSheet("font-size: 12px; color: #555;")
        layout_avanzado.addWidget(label_recreos)
        self.recreos_config_input = QLineEdit()
        self.recreos_config_input.setStyleSheet(styles.STYLE_INPUT)
        self.recreos_config_input.setMaximumWidth(500)
        layout_avanzado.addWidget(self.recreos_config_input)

        grupo_avanzado.setLayout(layout_avanzado)
        self.layout.addWidget(grupo_avanzado)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.save_btn = QPushButton("💾 Guardar Configuración")
        self.save_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.save_btn.clicked.connect(self.guardar_configuracion)

        self.load_btn = QPushButton("🔄 Cargar Actual")
        self.load_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.load_btn.clicked.connect(self.cargar_configuracion)

        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        btn_layout.addStretch()
        self.layout.addLayout(btn_layout)

        # Espacio flexible
        self.layout.addStretch()

        self.setLayout(self.layout)
        self.cargar_configuracion()  # Cargar al inicio si existe

    def guardar_configuracion(self):
        session = SessionLocal()
        try:
            # Solo debe haber una configuración
            config_existente = session.query(Configuracion).first()

            fecha_inicio = self.fecha_inicio_input.date().toPyDate()
            fecha_fin = self.fecha_fin_input.date().toPyDate()
            recreo1_manana = self.recreo1_manana_input.time().toPyTime()
            recreo2_manana = self.recreo2_manana_input.time().toPyTime()
            recreo1_tarde = self.recreo1_tarde_input.time().toPyTime()
            recreo2_tarde = self.recreo2_tarde_input.time().toPyTime()

            # Campos nuevos (con valores por defecto si vacío)
            ajuste_tutores = float(self.ajuste_tutores_input.text() or 1.0)
            ajuste_no_tutores = float(self.ajuste_no_tutores_input.text() or 1.0)
            activar_festivos_automaticos = (
                (self.festivos_auto_input.text() or "1").strip() in ("1", "true", "True")
            )
            dias_no_lectivos_personalizados = (self.no_lectivos_input.text() or "").strip()
            recreos_config = (self.recreos_config_input.text() or "").strip()

            if config_existente:
                # Actualizar configuración existente
                config_existente.fecha_inicio_curso = fecha_inicio
                config_existente.fecha_fin_curso = fecha_fin
                config_existente.hora_recreo1_manana = recreo1_manana
                config_existente.hora_recreo2_manana = recreo2_manana
                config_existente.hora_recreo1_tarde = recreo1_tarde
                config_existente.hora_recreo2_tarde = recreo2_tarde
                config_existente.ajuste_tutores = ajuste_tutores
                config_existente.ajuste_no_tutores = ajuste_no_tutores
                config_existente.activar_festivos_automaticos = activar_festivos_automaticos
                config_existente.dias_no_lectivos_personalizados = dias_no_lectivos_personalizados
                config_existente.recreos_config = recreos_config
                mensaje = "Configuración actualizada correctamente."
            else:
                # Crear nueva configuración
                nueva_config = Configuracion(
                    fecha_inicio_curso=fecha_inicio,
                    fecha_fin_curso=fecha_fin,
                    hora_recreo1_manana=recreo1_manana,
                    hora_recreo2_manana=recreo2_manana,
                    hora_recreo1_tarde=recreo1_tarde,
                    hora_recreo2_tarde=recreo2_tarde,
                    ajuste_tutores=ajuste_tutores,
                    ajuste_no_tutores=ajuste_no_tutores,
                    activar_festivos_automaticos=activar_festivos_automaticos,
                    dias_no_lectivos_personalizados=dias_no_lectivos_personalizados,
                    recreos_config=recreos_config
                )
                session.add(nueva_config)
                mensaje = "Configuración guardada correctamente."

            session.commit()
            QMessageBox.information(self, "Éxito", mensaje)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

    def cargar_configuracion(self):
        """Cargar la configuración desde la base de datos"""
        session = SessionLocal()
        try:
            config = session.query(Configuracion).first()
            if config:
                self.fecha_inicio_input.setDate(QDate(config.fecha_inicio_curso))
                self.fecha_fin_input.setDate(QDate(config.fecha_fin_curso))
                self.recreo1_manana_input.setTime(QTime(config.hora_recreo1_manana))
                self.recreo2_manana_input.setTime(QTime(config.hora_recreo2_manana))
                if config.hora_recreo1_tarde:
                    self.recreo1_tarde_input.setTime(QTime(config.hora_recreo1_tarde))
                if config.hora_recreo2_tarde:
                    self.recreo2_tarde_input.setTime(QTime(config.hora_recreo2_tarde))
                # Nuevos campos
                self.ajuste_tutores_input.setText(str(config.ajuste_tutores))
                self.ajuste_no_tutores_input.setText(str(config.ajuste_no_tutores))
                self.festivos_auto_input.setText(
                    "1" if config.activar_festivos_automaticos else "0"
                )
                self.no_lectivos_input.setText(config.dias_no_lectivos_personalizados or "")
                self.recreos_config_input.setText(config.recreos_config or "")
        except Exception as e:
            QMessageBox.warning(self, "Info", f"No hay configuración guardada: {e}")
        finally:
            session.close()


class AsignacionGuardiasForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Asignación de Guardias")
        self.layout = QVBoxLayout()

        # Título
        self.layout.addWidget(QLabel("=== CÁLCULO Y ASIGNACIÓN DE GUARDIAS ==="))

        # Área de estadísticas
        self.layout.addWidget(QLabel("\n📊 ESTADÍSTICAS DEL CURSO:"))
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        self.layout.addWidget(self.stats_text)

        # Botón para calcular distribución
        calc_button = QPushButton("📊 Calcular Distribución")
        calc_button.clicked.connect(self.calcular_distribucion)
        self.layout.addWidget(calc_button)

        # Área de resultados de distribución
        self.layout.addWidget(QLabel("\n📋 DISTRIBUCIÓN DE GUARDIAS POR PROFESOR:"))
        self.distribucion_text = QTextEdit()
        self.distribucion_text.setReadOnly(True)
        self.distribucion_text.setMaximumHeight(250)
        self.layout.addWidget(self.distribucion_text)

        # Botón para generar guardias (deshabilitado inicialmente)
        self.generar_button = QPushButton("🎯 Generar Asignación de Guardias")
        self.generar_button.setEnabled(False)
        self.generar_button.clicked.connect(self.generar_guardias)
        self.layout.addWidget(self.generar_button)

        # Área de resultados de generación
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(150)
        self.layout.addWidget(self.resultado_text)

        self.setLayout(self.layout)

        # Cargar estadísticas al inicio
        self.cargar_estadisticas()

    def cargar_estadisticas(self):
        """Muestra las estadísticas del curso"""
        session = SessionLocal()
        try:
            stats = obtener_estadisticas(session)

            if not stats:
                self.stats_text.setText(
                    "⚠️  No hay configuración del curso.\n"
                    "Por favor, configure primero las fechas y recreos."
                )
                return

            texto = f"""
Días lectivos: {stats.get('dias_lectivos', 0)} días (L-V)
Recreos mañana: {stats.get('recreos_manana', 0)}
Recreos tarde: {stats.get('recreos_tarde', 0)}
Total recreos/día: {stats.get('recreos_manana', 0) + stats.get('recreos_tarde', 0)}
Número de zonas: {stats.get('num_zonas', 0)}
Número de profesores: {stats.get('num_profesores', 0)}

📌 SLOTS TOTALES: {stats.get('slots_totales', 0)} guardias
   (días × recreos × zonas = {stats.get('dias_lectivos', 0)} ×
   {stats.get('recreos_manana', 0) + stats.get('recreos_tarde', 0)} ×
   {stats.get('num_zonas', 0)})
            """
            self.stats_text.setText(texto.strip())

        except ValueError as e:
            self.stats_text.setText(f"⚠️  {str(e)}")
        finally:
            session.close()

    def calcular_distribucion(self):
        """Calcula y muestra la distribución de guardias"""
        session = SessionLocal()
        try:
            # Validar que hay datos
            stats = obtener_estadisticas(session)
            if not stats or stats.get('slots_totales', 0) == 0:
                QMessageBox.warning(
                    self,
                    "Datos incompletos",
                    "Debe configurar el curso, profesores y zonas antes de calcular."
                )
                return

            # Calcular distribución
            distribucion = calcular_guardias_por_profesor(session)

            # Obtener nombres de profesores
            texto = "Distribución calculada:\n\n"
            total = 0

            profesores_ordenados = sorted(
                distribucion.items(),
                key=lambda x: x[1],
                reverse=True
            )

            for profesor_id, guardias in profesores_ordenados:
                profesor = session.query(Profesor).get(profesor_id)
                if profesor:
                    texto += (
                        f"• {profesor.nombre_completo} "
                        f"({profesor.turno}, {profesor.porcentaje_jornada*100:.0f}%): "
                        f"{guardias} guardias\n"
                    )
                    total += guardias

            texto += f"\n✅ TOTAL: {total} guardias"
            texto += f"\n📌 Slots disponibles: {stats.get('slots_totales', 0)}"

            if total == stats.get('slots_totales', 0):
                texto += "\n\n✅ La distribución es exacta"
            else:
                diff = abs(total - stats.get('slots_totales', 0))
                texto += f"\n\n⚠️  Diferencia: {diff}"

            self.distribucion_text.setText(texto)

            # Habilitar botón de generación
            self.generar_button.setEnabled(True)

        except ValueError as e:
            QMessageBox.critical(self, "Error", str(e))
            self.distribucion_text.setText(f"❌ Error: {str(e)}")
        finally:
            session.close()

    def generar_guardias(self):
        session = SessionLocal()
        try:
            # Verificar si ya existen guardias
            count_guardias = session.query(Guardia).count()

            if count_guardias > 0:
                respuesta = QMessageBox.question(
                    self,
                    "⚠️ Guardias Existentes",
                    f"Ya existen {count_guardias} guardias en la base de datos.\n\n"
                    f"¿Deseas ELIMINAR todas las guardias existentes antes de generar nuevas?\n\n"
                    f"• SÍ: Eliminará todas y generará desde cero (recomendado)\n"
                    f"• NO: Agregará nuevas guardias a las existentes (puede crear duplicados)",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No |
                    QMessageBox.StandardButton.Cancel
                )

                if respuesta == QMessageBox.StandardButton.Cancel:
                    return

                if respuesta == QMessageBox.StandardButton.Yes:
                    # Eliminar todas las guardias existentes
                    session.query(Guardia).delete()
                    session.commit()
                    QMessageBox.information(
                        self,
                        "Limpieza completada",
                        f"{count_guardias} guardias eliminadas. Generando calendario nuevo..."
                    )

            # Importación local para evitar lint de imports no usados
            from services.asignador_guardias import (
                generar_calendario_guardias,
                guardar_guardias_en_bd,
            )
            from services.calculador_guardias import obtener_estadisticas

            stats = obtener_estadisticas(session) or {}
            esperado = stats.get('slots_totales', 0)

            calendario, resumen = generar_calendario_guardias(session)
            guardar_guardias_en_bd(session, calendario)

            total_generado = len(calendario)
            diff = esperado - total_generado if esperado else 0

            # Mostrar resumen
            lineas = [
                f"Guardias generadas: {total_generado}",
            ]
            if esperado:
                lineas.append(f"Slots esperados: {esperado}")
                if diff == 0:
                    lineas.append("✅ Cobertura completa")
                elif diff > 0:
                    lineas.append(f"⚠️ {diff} slots sin cubrir (falta elegibilidad)")

            # Top profesores (opc)
            if resumen:
                top = sorted(resumen.items(), key=lambda x: x[1], reverse=True)[:10]
                lineas.append("\nPor profesor (top):")
                for pid, cnt in top:
                    prof = session.query(Profesor).get(pid)
                    if prof:
                        lineas.append(f"• {prof.nombre_completo}: {cnt}")

            self.resultado_text.setText("\n".join(lineas))

            QMessageBox.information(
                self,
                "Asignación generada",
                "Guardias generadas y guardadas en la base de datos.",
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo generar: {e}")
        finally:
            session.close()


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
        calendar_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
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
        filtros_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        right_panel.addWidget(filtros_label)

        # Filtro por profesor
        right_panel.addWidget(QLabel("Profesor:"))
        self.filtro_profesor = QComboBox()
        self.filtro_profesor.addItem("Todos los profesores", None)
        self.filtro_profesor.currentIndexChanged.connect(self.aplicar_filtros)
        right_panel.addWidget(self.filtro_profesor)

        # Filtro por zona
        right_panel.addWidget(QLabel("Zona:"))
        self.filtro_zona = QComboBox()
        self.filtro_zona.addItem("Todas las zonas", None)
        self.filtro_zona.currentIndexChanged.connect(self.aplicar_filtros)
        right_panel.addWidget(self.filtro_zona)

        # Filtro por turno
        right_panel.addWidget(QLabel("Turno:"))
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
        detalles_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        right_panel.addWidget(detalles_label)

        self.guardias_dia_text = QTextEdit()
        self.guardias_dia_text.setReadOnly(True)
        self.guardias_dia_text.setMaximumHeight(400)
        right_panel.addWidget(self.guardias_dia_text)

        # Estadísticas
        stats_label = QLabel("Estadísticas:")
        stats_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
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

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()
        self.tabs.addTab(ProfesorForm(), "👨‍🏫 Profesores")
        self.tabs.addTab(ZonaForm(), "🏫 Zonas")
        self.tabs.addTab(ConfiguracionForm(), "⚙️ Configuración")
        self.tabs.addTab(AsignacionGuardiasForm(), "📋 Asignación de Guardias")

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
