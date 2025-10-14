
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import SessionLocal
from models.models import Profesor, Zona
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ProfesorForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alta de Profesor")
        self.layout = QVBoxLayout()

        self.nombre_input = QLineEdit()
        self.apellidos_input = QLineEdit()
        self.horas_input = QLineEdit()
        self.turno_input = QComboBox()
        self.turno_input.addItems(["mañana", "tarde", "mixto"])
        self.horas_manana_input = QLineEdit()
        self.horas_tarde_input = QLineEdit()
        self.horas_manana_input.setPlaceholderText("Horas mañana si mixto")
        self.horas_tarde_input.setPlaceholderText("Horas tarde si mixto")

        self.layout.addWidget(QLabel("Nombre:"))
        self.layout.addWidget(self.nombre_input)
        self.layout.addWidget(QLabel("Apellidos:"))
        self.layout.addWidget(self.apellidos_input)
        self.layout.addWidget(QLabel("Horas de contrato (total):"))
        self.layout.addWidget(self.horas_input)
        self.layout.addWidget(QLabel("Turno:"))
        self.layout.addWidget(self.turno_input)
        self.label_horas_manana = QLabel("Horas de mañana (solo mixto):")
        self.label_horas_tarde = QLabel("Horas de tarde (solo mixto):")
        self.layout.addWidget(self.label_horas_manana)
        self.layout.addWidget(self.horas_manana_input)
        self.layout.addWidget(self.label_horas_tarde)
        self.layout.addWidget(self.horas_tarde_input)

        # Inicialmente ocultar campos mixto
        self._toggle_mixto_fields(False)
        self.turno_input.currentTextChanged.connect(self._on_turno_changed)

        self.submit_btn = QPushButton("Guardar profesor")
        self.submit_btn.clicked.connect(self.guardar_profesor)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

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

    def guardar_profesor(self):
        session = SessionLocal()
        try:
            nombre = self.nombre_input.text()
            apellidos = self.apellidos_input.text()
            horas = float(self.horas_input.text())
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
            nuevo_profesor = Profesor(
                nombre=nombre,
                apellidos=apellidos,
                horas_contrato=horas,
                porcentaje_jornada=porcentaje,
                turno=turno
            )
            session.add(nuevo_profesor)
            session.commit()
            QMessageBox.information(
                self,
                "Éxito",
                f"Profesor guardado correctamente. Porcentaje jornada: {porcentaje:.2f}",
            )
            self.nombre_input.clear()
            self.apellidos_input.clear()
            self.horas_input.clear()
            self.horas_manana_input.clear()
            self.horas_tarde_input.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

class ZonaForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Alta de Zona")
        self.layout = QVBoxLayout()

        self.nombre_zona_input = QLineEdit()
        self.descripcion_input = QLineEdit()

        self.layout.addWidget(QLabel("Nombre de la zona:"))
        self.layout.addWidget(self.nombre_zona_input)
        self.layout.addWidget(QLabel("Descripción:"))
        self.layout.addWidget(self.descripcion_input)

        self.submit_btn = QPushButton("Guardar zona")
        self.submit_btn.clicked.connect(self.guardar_zona)
        self.layout.addWidget(self.submit_btn)

        self.setLayout(self.layout)

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
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guardias de Patio - Gestión")
        self.layout = QVBoxLayout()

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()
        self.tabs.addTab(ProfesorForm(), "Profesores")
        self.tabs.addTab(ZonaForm(), "Zonas")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
