"""
Gestión de sustituciones de guardias.

Permite registrar ausencias y reasignar guardias automáticamente.
"""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from models.models import Guardia, Profesor, Zona
from presentation.forms.base_form import BaseForm


class GestorSustituciones(BaseForm):
    """Widget para gestionar sustituciones de guardias."""

    def __init__(self, session):
        """
        Inicializar gestor de sustituciones.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setWindowTitle("Gestión de Sustituciones")
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del widget."""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(20, 20, 20, 20)
        layout_principal.setSpacing(15)

        # Título
        titulo = QLabel("🔄 Gestión de Sustituciones")
        titulo.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 15px;
                background-color: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout_principal.addWidget(titulo)

        # Descripción
        descripcion = QLabel(
            "Busca una guardia asignada a un profesor y reasígnala a otro profesor disponible"
        )
        descripcion.setAlignment(Qt.AlignmentFlag.AlignCenter)
        descripcion.setStyleSheet("color: #7f8c8d; font-size: 12px; margin-bottom: 10px;")
        layout_principal.addWidget(descripcion)

        # Layout en 2 columnas para las secciones principales
        layout_columnas = QHBoxLayout()
        layout_columnas.setSpacing(15)

        # Columna izquierda: Buscar guardia
        columna_izq = QVBoxLayout()
        columna_izq.addWidget(self._crear_seccion_buscar())
        columna_izq.addStretch()
        layout_columnas.addLayout(columna_izq, 1)

        # Columna derecha: Asignar sustituto
        columna_der = QVBoxLayout()
        columna_der.addWidget(self._crear_seccion_sustituir())
        columna_der.addStretch()
        layout_columnas.addLayout(columna_der, 1)

        layout_principal.addLayout(layout_columnas)

        # Tabla de guardias encontradas (ancho completo)
        tabla_group = QGroupBox("📋 Guardias Encontradas")
        tabla_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        tabla_layout = QVBoxLayout()
        self.tabla_guardias = self._crear_tabla_guardias()
        tabla_layout.addWidget(self.tabla_guardias)
        tabla_group.setLayout(tabla_layout)
        layout_principal.addWidget(tabla_group)

        # Historial (ancho completo, colapsable)
        layout_principal.addWidget(self._crear_seccion_historial())

        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.cargar_profesores()

    def _crear_seccion_buscar(self) -> QGroupBox:
        """Crear sección de búsqueda de guardia."""
        grupo_buscar = QGroupBox("1️⃣ Buscar Guardia")
        grupo_buscar.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #ebf5fb;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2980b9;
            }
        """)
        layout_buscar = QVBoxLayout()
        layout_buscar.setSpacing(12)
        layout_buscar.setContentsMargins(15, 20, 15, 15)

        # Fecha
        fecha_label = QLabel("📅 Fecha de la guardia:")
        fecha_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        layout_buscar.addWidget(fecha_label)

        self.fecha_buscar = QDateEdit()
        self.fecha_buscar.setDate(date.today())
        self.fecha_buscar.setCalendarPopup(True)
        self.fecha_buscar.setStyleSheet("""
            QDateEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QDateEdit:focus {
                border: 2px solid #3498db;
            }
        """)
        layout_buscar.addWidget(self.fecha_buscar)

        # Profesor
        profesor_label = QLabel("👨‍🏫 Profesor original:")
        profesor_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px; margin-top: 5px;")
        layout_buscar.addWidget(profesor_label)

        self.combo_profesor_original = QComboBox()
        self.combo_profesor_original.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #3498db;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        layout_buscar.addWidget(self.combo_profesor_original)

        # Botón buscar
        self.btn_buscar = QPushButton("🔍 Buscar Guardias")
        self.btn_buscar.clicked.connect(self.buscar_guardias)
        self.btn_buscar.setMinimumHeight(40)
        self.btn_buscar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        layout_buscar.addWidget(self.btn_buscar)

        grupo_buscar.setLayout(layout_buscar)
        return grupo_buscar

    def _crear_tabla_guardias(self) -> QTableWidget:
        """Crear tabla de guardias encontradas."""
        tabla = QTableWidget()
        tabla.setColumnCount(5)
        tabla.setHorizontalHeaderLabels(["ID", "Profesor", "Turno", "Recreo", "Zona"])
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        tabla.setAlternatingRowColors(True)
        tabla.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #bdc3c7;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
            }
        """)
        tabla.horizontalHeader().setStretchLastSection(True)
        tabla.setMinimumHeight(150)
        tabla.selectionModel().selectionChanged.connect(
            self.guardia_seleccionada_cambio
        )
        return tabla

    def _crear_seccion_sustituir(self) -> QGroupBox:
        """Crear sección de asignación de sustituto."""
        grupo_sustituir = QGroupBox("2️⃣ Asignar Sustituto")
        grupo_sustituir.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #27ae60;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #eafaf1;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #229954;
            }
        """)
        layout_sustituir = QVBoxLayout()
        layout_sustituir.setSpacing(12)
        layout_sustituir.setContentsMargins(15, 20, 15, 15)

        # Profesor sustituto
        sustituto_label = QLabel("👥 Profesor sustituto:")
        sustituto_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        layout_sustituir.addWidget(sustituto_label)

        self.combo_profesor_sustituto = QComboBox()
        self.combo_profesor_sustituto.setStyleSheet("""
            QComboBox {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 13px;
            }
            QComboBox:focus {
                border: 2px solid #27ae60;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
        """)
        layout_sustituir.addWidget(self.combo_profesor_sustituto)

        # Botón ver disponibles
        self.btn_buscar_disponibles = QPushButton("�️ Ver Profesores Disponibles")
        self.btn_buscar_disponibles.clicked.connect(self.buscar_profesores_disponibles)
        self.btn_buscar_disponibles.setMinimumHeight(35)
        self.btn_buscar_disponibles.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                font-weight: normal;
                font-size: 12px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout_sustituir.addWidget(self.btn_buscar_disponibles)

        # Observaciones
        obs_label = QLabel("📝 Observaciones (opcional):")
        obs_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px; margin-top: 10px;")
        layout_sustituir.addWidget(obs_label)

        self.text_observaciones = QTextEdit()
        self.text_observaciones.setMaximumHeight(70)
        self.text_observaciones.setPlaceholderText(
            "Añade observaciones sobre la sustitución..."
        )
        self.text_observaciones.setStyleSheet("""
            QTextEdit {
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 2px solid #27ae60;
            }
        """)
        layout_sustituir.addWidget(self.text_observaciones)

        # Botones de acción
        botones_layout = self._crear_botones_accion()
        layout_sustituir.addLayout(botones_layout)

        grupo_sustituir.setLayout(layout_sustituir)
        return grupo_sustituir

    def _crear_botones_accion(self) -> QHBoxLayout:
        """Crear botones de acción."""
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)
        botones_layout.setContentsMargins(0, 15, 0, 0)

        self.btn_confirmar_sustitucion = QPushButton("✅ Confirmar Sustitución")
        self.btn_confirmar_sustitucion.clicked.connect(self.confirmar_sustitucion)
        self.btn_confirmar_sustitucion.setMinimumHeight(45)
        self.btn_confirmar_sustitucion.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_confirmar_sustitucion.setEnabled(False)
        botones_layout.addWidget(self.btn_confirmar_sustitucion, 2)

        self.btn_cancelar = QPushButton("❌ Limpiar")
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
        self.btn_cancelar.setMinimumHeight(45)
        self.btn_cancelar.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 20px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """)
        botones_layout.addWidget(self.btn_cancelar, 1)

        return botones_layout

    def _crear_seccion_historial(self) -> QGroupBox:
        """Crear sección de historial."""
        grupo_historial = QGroupBox("📜 Historial Reciente de Sustituciones")
        grupo_historial.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #fdfefe;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #34495e;
            }
        """)
        layout_historial = QVBoxLayout()
        layout_historial.setContentsMargins(15, 20, 15, 15)

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha", "Profesor Original", "Profesor Sustituto", "Turno/Recreo", "Zona"]
        )
        self.tabla_historial.setMaximumHeight(180)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 6px;
                font-size: 12px;
            }
            QHeaderView::section {
                background-color: #95a5a6;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }
        """)
        self.tabla_historial.horizontalHeader().setStretchLastSection(True)
        layout_historial.addWidget(self.tabla_historial)

        grupo_historial.setLayout(layout_historial)
        return grupo_historial

    def cargar_profesores(self):
        """Cargar la lista de profesores en los combos."""
        try:
            profesores = (
                self.session.query(Profesor).order_by(Profesor.nombre_completo).all()
            )

            self.combo_profesor_original.clear()
            self.combo_profesor_sustituto.clear()

            self.combo_profesor_original.addItem("-- Todos --", None)

            for profesor in profesores:
                self.combo_profesor_original.addItem(
                    profesor.nombre_completo, profesor.id
                )
                self.combo_profesor_sustituto.addItem(
                    profesor.nombre_completo, profesor.id
                )

        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def buscar_guardias(self):
        """Buscar las guardias del profesor en la fecha seleccionada."""
        try:
            fecha = self.fecha_buscar.date().toPyDate()
            profesor_id = self.combo_profesor_original.currentData()

            # Consultar guardias
            query = self.session.query(Guardia).filter(Guardia.fecha == fecha)

            if profesor_id is not None:
                query = query.filter(Guardia.profesor_id == profesor_id)

            guardias = query.all()

            # Llenar tabla
            self.tabla_guardias.setRowCount(len(guardias))

            for i, guardia in enumerate(guardias):
                profesor = self.session.query(Profesor).get(guardia.profesor_id)
                zona = self.session.query(Zona).get(guardia.zona_id)

                self.tabla_guardias.setItem(i, 0, QTableWidgetItem(str(guardia.id)))
                self.tabla_guardias.setItem(
                    i,
                    1,
                    QTableWidgetItem(
                        f"{profesor.nombre_completo if profesor else 'N/A'}"
                    ),
                )
                self.tabla_guardias.setItem(i, 2, QTableWidgetItem(guardia.turno))
                self.tabla_guardias.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
                self.tabla_guardias.setItem(
                    i, 4, QTableWidgetItem(zona.nombre_zona if zona else "N/A")
                )

                # Guardar el objeto guardia en la fila
                self.tabla_guardias.item(i, 0).setData(
                    Qt.ItemDataRole.UserRole, guardia
                )

            # Mensaje si no hay resultados
            if len(guardias) == 0:
                self.mostrar_informacion(
                    "Sin resultados",
                    f"No se encontraron guardias para la fecha {fecha.strftime('%d/%m/%Y')}"
                )

        except Exception as e:
            self.manejar_excepcion(e, "buscar guardias")

    def guardia_seleccionada_cambio(self):
        """Manejar el cambio de selección en la tabla de guardias."""
        self.btn_confirmar_sustitucion.setEnabled(
            len(self.tabla_guardias.selectedItems()) > 0
        )

    def buscar_profesores_disponibles(self):
        """Mostrar los profesores disponibles para el slot seleccionado."""
        if not self.tabla_guardias.selectedItems():
            self.mostrar_advertencia(
                "Selección Requerida",
                "Por favor, selecciona primero una guardia a sustituir.",
            )
            return

        try:
            fila = self.tabla_guardias.currentRow()
            guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)

            # Buscar profesores que NO tengan guardia ese día
            guardias_ese_dia = (
                self.session.query(Guardia.profesor_id)
                .filter(Guardia.fecha == guardia.fecha)
                .all()
            )

            profesores_ocupados = {prof_id for (prof_id,) in guardias_ese_dia}

            todos_profesores = self.session.query(Profesor).all()
            disponibles = [
                p for p in todos_profesores if p.id not in profesores_ocupados
            ]

            if disponibles:
                mensaje = "Profesores disponibles (sin guardias ese día):\n\n"
                for profesor in disponibles[:10]:  # Mostrar máximo 10
                    mensaje += f"• {profesor.nombre_completo}\n"

                if len(disponibles) > 10:
                    mensaje += f"\n... y {len(disponibles) - 10} más"

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Profesores Disponibles")
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setWindowFlags(
                    Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                    Qt.WindowType.WindowTitleHint
                )
                msg.setText(mensaje)
                msg.exec()
            else:
                self.mostrar_advertencia(
                    "Sin Disponibles",
                    "No hay profesores disponibles ese día "
                    "(todos tienen al menos 1 guardia).",
                )

        except Exception as e:
            self.manejar_excepcion(e, "buscar profesores disponibles")

    def confirmar_sustitucion(self):
        """Confirmar la sustitución de guardia."""
        if not self.tabla_guardias.selectedItems():
            return

        try:
            fila = self.tabla_guardias.currentRow()
            guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)
            nuevo_profesor_id = self.combo_profesor_sustituto.currentData()

            if nuevo_profesor_id is None:
                self.mostrar_advertencia(
                    "Profesor Requerido", "Por favor, selecciona un profesor sustituto."
                )
                return

            # Verificar que el sustituto no tenga guardia ese día
            guardia_existente = (
                self.session.query(Guardia)
                .filter(
                    Guardia.profesor_id == nuevo_profesor_id,
                    Guardia.fecha == guardia.fecha,
                )
                .first()
            )

            if guardia_existente:
                self.mostrar_advertencia(
                    "Profesor Ocupado",
                    "El profesor seleccionado ya tiene una guardia ese día.\n"
                    "Recuerda: máximo 1 guardia por día por profesor.",
                )
                return

            # Confirmar con el usuario
            profesor_original = self.session.query(Profesor).get(guardia.profesor_id)
            profesor_nuevo = self.session.query(Profesor).get(nuevo_profesor_id)

            respuesta = QMessageBox.question(
                self,
                "Confirmar Sustitución",
                f"¿Confirmas la sustitución?\n\n"
                f"Profesor Original: {profesor_original.nombre_completo}\n"
                f"Profesor Sustituto: {profesor_nuevo.nombre_completo}\n"
                f"Fecha: {guardia.fecha}\n"
                f"Turno: {guardia.turno} - Recreo {guardia.recreo}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if respuesta == QMessageBox.StandardButton.Yes:
                # Realizar sustitución
                guardia.profesor_id = nuevo_profesor_id
                self.session.commit()

                self.mostrar_exito(
                    "Sustitución Completada",
                    "La guardia ha sido reasignada exitosamente.",
                )

                # Limpiar y refrescar
                self.limpiar_formulario()
                self.buscar_guardias()

        except Exception as e:
            self.manejar_excepcion(e, "confirmar sustitución")

    def limpiar_formulario(self):
        """Limpiar el formulario de sustitución."""
        self.tabla_guardias.clearSelection()
        self.combo_profesor_sustituto.setCurrentIndex(0)
        self.text_observaciones.clear()
        self.btn_confirmar_sustitucion.setEnabled(False)

    def refrescar(self):
        """Refrescar los datos."""
        self.cargar_profesores()
        self.tabla_guardias.setRowCount(0)
