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
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from models.models import Guardia, Profesor, Zona


class GestorSustituciones(QWidget):
    """Widget para gestionar sustituciones de guardias."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout_principal = QVBoxLayout()

        # Título
        titulo = QLabel("🔄 Gestión de Sustituciones")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_principal.addWidget(titulo)

        # Sección: Buscar Guardia Original
        grupo_buscar = QGroupBox("1️⃣ Buscar Guardia a Sustituir")
        layout_buscar = QFormLayout()

        self.fecha_buscar = QDateEdit()
        self.fecha_buscar.setDate(date.today())
        self.fecha_buscar.setCalendarPopup(True)
        layout_buscar.addRow("Fecha:", self.fecha_buscar)

        self.combo_profesor_original = QComboBox()
        layout_buscar.addRow("Profesor Original:", self.combo_profesor_original)

        self.btn_buscar = QPushButton("🔍 Buscar Guardias")
        self.btn_buscar.clicked.connect(self.buscar_guardias)
        self.btn_buscar.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            """
        )
        layout_buscar.addRow("", self.btn_buscar)

        grupo_buscar.setLayout(layout_buscar)
        layout_principal.addWidget(grupo_buscar)

        # Tabla de guardias encontradas
        self.tabla_guardias = QTableWidget()
        self.tabla_guardias.setColumnCount(5)
        self.tabla_guardias.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Turno", "Recreo", "Zona"]
        )
        self.tabla_guardias.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.tabla_guardias.selectionModel().selectionChanged.connect(
            self.guardia_seleccionada_cambio
        )
        layout_principal.addWidget(self.tabla_guardias)

        # Sección: Asignar Sustituto
        grupo_sustituir = QGroupBox("2️⃣ Asignar Sustituto")
        layout_sustituir = QFormLayout()

        self.combo_profesor_sustituto = QComboBox()
        layout_sustituir.addRow("Profesor Sustituto:", self.combo_profesor_sustituto)

        self.btn_buscar_disponibles = QPushButton("👥 Ver Disponibles")
        self.btn_buscar_disponibles.clicked.connect(self.buscar_profesores_disponibles)
        layout_sustituir.addRow("", self.btn_buscar_disponibles)

        self.text_observaciones = QTextEdit()
        self.text_observaciones.setMaximumHeight(60)
        self.text_observaciones.setPlaceholderText(
            "Observaciones sobre la sustitución (opcional)..."
        )
        layout_sustituir.addRow("Observaciones:", self.text_observaciones)

        botones_layout = QHBoxLayout()

        self.btn_confirmar_sustitucion = QPushButton("✅ Confirmar Sustitución")
        self.btn_confirmar_sustitucion.clicked.connect(self.confirmar_sustitucion)
        self.btn_confirmar_sustitucion.setStyleSheet(
            """
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
            """
        )
        self.btn_confirmar_sustitucion.setEnabled(False)
        botones_layout.addWidget(self.btn_confirmar_sustitucion)

        self.btn_cancelar = QPushButton("❌ Cancelar")
        self.btn_cancelar.clicked.connect(self.limpiar_formulario)
        botones_layout.addWidget(self.btn_cancelar)

        layout_sustituir.addRow("", botones_layout)

        grupo_sustituir.setLayout(layout_sustituir)
        layout_principal.addWidget(grupo_sustituir)

        # Historial de sustituciones
        grupo_historial = QGroupBox("📜 Historial Reciente")
        layout_historial = QVBoxLayout()

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(5)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha", "Profesor Original", "Profesor Sustituto", "Turno/Recreo", "Zona"]
        )
        self.tabla_historial.setMaximumHeight(150)
        layout_historial.addWidget(self.tabla_historial)

        grupo_historial.setLayout(layout_historial)
        layout_principal.addWidget(grupo_historial)

        self.setLayout(layout_principal)

        # Cargar datos iniciales
        self.cargar_profesores()

    def cargar_profesores(self):
        """Carga la lista de profesores en los combos."""
        profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()

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

    def buscar_guardias(self):
        """Busca las guardias del profesor en la fecha seleccionada."""
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
                i, 1,
                QTableWidgetItem(f"{profesor.nombre_completo if profesor else 'N/A'}")
            )
            self.tabla_guardias.setItem(i, 2, QTableWidgetItem(guardia.turno))
            self.tabla_guardias.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
            self.tabla_guardias.setItem(
                i, 4,
                QTableWidgetItem(zona.nombre_zona if zona else "N/A")
            )

            # Guardar el objeto guardia en la fila
            self.tabla_guardias.item(i, 0).setData(Qt.ItemDataRole.UserRole, guardia)

    def guardia_seleccionada_cambio(self):
        """Maneja el cambio de selección en la tabla de guardias."""
        self.btn_confirmar_sustitucion.setEnabled(
            len(self.tabla_guardias.selectedItems()) > 0
        )

    def buscar_profesores_disponibles(self):
        """Muestra los profesores disponibles para el slot seleccionado."""
        if not self.tabla_guardias.selectedItems():
            QMessageBox.warning(
                self,
                "Selección Requerida",
                "Por favor, selecciona primero una guardia a sustituir."
            )
            return

        fila = self.tabla_guardias.currentRow()
        guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)

        # Buscar profesores que NO tengan guardia ese día
        # (cumpliendo la regla de máximo 1 guardia por día)
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

            QMessageBox.information(
                self,
                "Profesores Disponibles",
                mensaje
            )
        else:
            QMessageBox.warning(
                self,
                "Sin Disponibles",
                "No hay profesores disponibles ese día (todos tienen al menos 1 guardia)."
            )

    def confirmar_sustitucion(self):
        """Confirma la sustitución de guardia."""
        if not self.tabla_guardias.selectedItems():
            return

        fila = self.tabla_guardias.currentRow()
        guardia = self.tabla_guardias.item(fila, 0).data(Qt.ItemDataRole.UserRole)
        nuevo_profesor_id = self.combo_profesor_sustituto.currentData()

        if nuevo_profesor_id is None:
            QMessageBox.warning(
                self,
                "Profesor Requerido",
                "Por favor, selecciona un profesor sustituto."
            )
            return

        # Verificar que el sustituto no tenga guardia ese día
        guardia_existente = (
            self.session.query(Guardia)
            .filter(
                Guardia.profesor_id == nuevo_profesor_id,
                Guardia.fecha == guardia.fecha
            )
            .first()
        )

        if guardia_existente:
            QMessageBox.warning(
                self,
                "Profesor Ocupado",
                "El profesor seleccionado ya tiene una guardia ese día.\n"
                "Recuerda: máximo 1 guardia por día por profesor."
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
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            # Realizar sustitución
            guardia.profesor_id = nuevo_profesor_id
            self.session.commit()

            QMessageBox.information(
                self,
                "Sustitución Completada",
                "La guardia ha sido reasignada exitosamente."
            )

            # Limpiar y refrescar
            self.limpiar_formulario()
            self.buscar_guardias()

    def limpiar_formulario(self):
        """Limpia el formulario de sustitución."""
        self.tabla_guardias.clearSelection()
        self.combo_profesor_sustituto.setCurrentIndex(0)
        self.text_observaciones.clear()
        self.btn_confirmar_sustitucion.setEnabled(False)

    def refrescar(self):
        """Refresca los datos."""
        self.cargar_profesores()
        self.tabla_guardias.setRowCount(0)
