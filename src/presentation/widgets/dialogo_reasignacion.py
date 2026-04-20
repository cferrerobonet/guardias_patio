"""
Diálogo de reasignación de guardias afectadas por ausencias.

Extraído de gestionar_ausencias.py para reducir su tamaño (ARQ-05).
"""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from presentation.theme import legacy_styles as styles
from services.gestor_ausencias import (
    obtener_profesores_disponibles,
    reasignar_guardia,
    reasignar_guardias_automaticamente,
)
from utils.icons import icon_for_button
from utils.ui_helpers import get_corporate_icon


class DialogoReasignacion(QDialog):
    """Diálogo para reasignar guardias afectadas por una ausencia."""

    def __init__(self, guardias, ausencia_id, session, parent=None):
        """
        Inicializar diálogo de reasignación.

        Args:
            guardias: Lista de guardias afectadas
            ausencia_id: ID de la ausencia
            session: Sesión de base de datos
            parent: Widget padre
        """
        super().__init__(parent)
        self.guardias = guardias
        self.ausencia_id = ausencia_id
        self.session = session
        self.setWindowTitle("Reasignación de Guardias")
        self.setWindowIcon(get_corporate_icon())
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.init_ui()

    def init_ui(self):
        """Inicializar la interfaz del diálogo."""
        layout = QVBoxLayout(self)

        # Título
        titulo = QLabel(f"Guardias Afectadas ({len(self.guardias)} guardias)")
        titulo.setObjectName("titleMain")
        layout.addWidget(titulo)

        # Tabla de guardias
        self.tabla = self._crear_tabla()
        layout.addWidget(self.tabla)

        # Botones de acción
        layout.addLayout(self._crear_botones())

    def _crear_tabla(self) -> QTableWidget:
        """Crear tabla de guardias."""
        tabla = QTableWidget()
        tabla.setColumnCount(6)
        tabla.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Turno", "Recreo", "Zona", "Profesor Actual"]
        )
        tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        tabla.setColumnWidth(0, 50)
        tabla.setColumnWidth(1, 100)
        tabla.setColumnWidth(2, 80)
        tabla.setColumnWidth(3, 80)
        tabla.setColumnWidth(4, 150)
        tabla.setColumnWidth(5, 200)

        for i, guardia in enumerate(self.guardias):
            tabla.insertRow(i)
            tabla.setItem(i, 0, QTableWidgetItem(str(guardia.id)))
            tabla.setItem(i, 1, QTableWidgetItem(guardia.fecha.strftime("%d/%m/%Y")))
            tabla.setItem(i, 2, QTableWidgetItem(guardia.turno))
            tabla.setItem(i, 3, QTableWidgetItem(str(guardia.recreo)))
            zona_nombre = guardia.zona.nombre_zona if guardia.zona else "N/A"
            tabla.setItem(i, 4, QTableWidgetItem(zona_nombre))
            profesor_nombre = guardia.profesor.nombre_completo if guardia.profesor else "N/A"
            tabla.setItem(i, 5, QTableWidgetItem(profesor_nombre))

        return tabla

    def _crear_botones(self) -> QHBoxLayout:
        """Crear botones de acción."""
        botones = QHBoxLayout()

        btn_auto = QPushButton("Reasignar Automáticamente")
        btn_auto.setIcon(icon_for_button("refresh"))
        btn_auto.setProperty("success", True)
        btn_auto.clicked.connect(self.reasignar_automaticamente)
        botones.addWidget(btn_auto)

        btn_manual = QPushButton("Reasignar Seleccionada")
        btn_manual.setIcon(icon_for_button("user"))
        btn_manual.clicked.connect(self.reasignar_manual)
        botones.addWidget(btn_manual)

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setIcon(icon_for_button("close"))
        btn_cerrar.setObjectName("secondaryButton")
        btn_cerrar.clicked.connect(self.close)
        botones.addWidget(btn_cerrar)

        return botones

    def reasignar_automaticamente(self):
        """Reasignar todas las guardias automáticamente."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar reasignación",
            f"¿Reasignar automáticamente {len(self.guardias)} guardias?\n"
            "El sistema buscará los mejores sustitutos disponibles.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultados = reasignar_guardias_automaticamente(self.session, self.guardias)

                mensaje = (
                    f"Reasignación completada:\n\n"
                    f"Reasignadas: {resultados['reasignadas']}\n"
                    f"Fallidas: {resultados['fallidas']}"
                )

                if resultados["fallidas"] > 0:
                    mensaje += "\n\nVer detalles en el log para más información."

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Resultado")
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setText(mensaje)
                msg.exec()

                if resultados["reasignadas"] > 0:
                    self.close()

            except (ValueError, TypeError) as e:
                QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")

    def reasignar_manual(self):
        """Permitir seleccionar manualmente un sustituto."""
        selected_rows = self.tabla.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Sin selección", "Por favor selecciona una guardia")
            return

        try:
            row = selected_rows[0].row()
            guardia_id = int(self.tabla.item(row, 0).text())

            guardia = next((g for g in self.guardias if g.id == guardia_id), None)
            if not guardia:
                return

            disponibles = obtener_profesores_disponibles(
                self.session,
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
                excluir_profesor_id=guardia.profesor_id,
            )

            if not disponibles:
                QMessageBox.warning(
                    self,
                    "Sin disponibles",
                    "No hay profesores disponibles para esta guardia",
                )
                return

            nombres = [f"{p.nombre_completo} ({count} guardias hoy)" for p, count in disponibles]

            nombre_seleccionado, ok = QInputDialog.getItem(
                self, "Seleccionar Sustituto", "Profesor:", nombres, 0, False
            )

            if ok and nombre_seleccionado:
                index = nombres.index(nombre_seleccionado)
                nuevo_profesor, _ = disponibles[index]

                reasignar_guardia(self.session, guardia_id, nuevo_profesor.id)

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("Éxito")
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setTextFormat(Qt.TextFormat.RichText)
                msg.setText(
                    f"Guardia reasignada a "
                    f"<span style='color: #007ACC; "
                    f"font-style: italic;'>{nuevo_profesor.nombre_completo}</span>"
                )
                msg.exec()

                self.close()

        except (ValueError, TypeError, OSError) as e:
            QMessageBox.critical(self, "Error", f"Error al reasignar:\n{str(e)}")
