
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import SessionLocal
from models.models import Configuracion, Profesor, Zona
from PyQt6.QtCore import QDate, QTime
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from services.calculador_guardias import (
    calcular_guardias_por_profesor,
    obtener_estadisticas,
)


class ProfesorForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Profesores")
        self.layout = QVBoxLayout()

        # Sección de alta
        self.layout.addWidget(QLabel("=== ALTA DE PROFESOR ==="))

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

        # Sección de listado
        self.layout.addWidget(QLabel("=== PROFESORES REGISTRADOS ==="))
        self.lista_profesores = QListWidget()
        self.layout.addWidget(self.lista_profesores)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar lista")
        self.refresh_btn.clicked.connect(self.cargar_profesores)
        self.delete_btn = QPushButton("Eliminar seleccionado")
        self.delete_btn.clicked.connect(self.eliminar_profesor)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)
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
            self.cargar_profesores()  # Actualizar lista tras guardar
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al guardar: {e}")
        finally:
            session.close()

    def cargar_profesores(self):
        """Cargar la lista de profesores desde la base de datos"""
        self.lista_profesores.clear()
        session = SessionLocal()
        try:
            profesores = session.query(Profesor).all()
            for prof in profesores:
                texto = (
                    f"[{prof.id}] {prof.nombre} {prof.apellidos} - "
                    f"{prof.horas_contrato}h ({prof.turno})"
                )
                self.lista_profesores.addItem(texto)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cargar profesores: {e}")
        finally:
            session.close()

    def eliminar_profesor(self):
        """Eliminar el profesor seleccionado"""
        item_actual = self.lista_profesores.currentItem()
        if not item_actual:
            QMessageBox.warning(self, "Sin selección", "Selecciona un profesor para eliminar.")
            return

        # Extraer ID del texto [ID] nombre...
        texto = item_actual.text()
        id_profesor = int(texto.split("]")[0].replace("[", ""))

        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Eliminar profesor con ID {id_profesor}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            session = SessionLocal()
            try:
                profesor = session.query(Profesor).filter(Profesor.id == id_profesor).first()
                if profesor:
                    session.delete(profesor)
                    session.commit()
                    QMessageBox.information(self, "Éxito", "Profesor eliminado correctamente.")
                    self.cargar_profesores()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar: {e}")
            finally:
                session.close()

class ZonaForm(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Zonas")
        self.layout = QVBoxLayout()

        # Sección de alta
        self.layout.addWidget(QLabel("=== ALTA DE ZONA ==="))

        self.nombre_zona_input = QLineEdit()
        self.descripcion_input = QLineEdit()

        self.layout.addWidget(QLabel("Nombre de la zona:"))
        self.layout.addWidget(self.nombre_zona_input)
        self.layout.addWidget(QLabel("Descripción:"))
        self.layout.addWidget(self.descripcion_input)

        self.submit_btn = QPushButton("Guardar zona")
        self.submit_btn.clicked.connect(self.guardar_zona)
        self.layout.addWidget(self.submit_btn)

        # Sección de listado
        self.layout.addWidget(QLabel("=== ZONAS REGISTRADAS ==="))
        self.lista_zonas = QListWidget()
        self.layout.addWidget(self.lista_zonas)

        btn_layout = QHBoxLayout()
        self.refresh_btn = QPushButton("Actualizar lista")
        self.refresh_btn.clicked.connect(self.cargar_zonas)
        self.delete_btn = QPushButton("Eliminar seleccionada")
        self.delete_btn.clicked.connect(self.eliminar_zona)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        self.layout.addLayout(btn_layout)

        self.setLayout(self.layout)
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

        self.layout.addWidget(QLabel("=== CONFIGURACIÓN DEL CURSO ESCOLAR ==="))

        # Fechas del curso
        self.layout.addWidget(QLabel("Fecha de inicio del curso:"))
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate())
        self.layout.addWidget(self.fecha_inicio_input)

        self.layout.addWidget(QLabel("Fecha de fin del curso:"))
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addMonths(9))
        self.layout.addWidget(self.fecha_fin_input)

        # Horarios de recreos mañana
        self.layout.addWidget(QLabel("=== RECREOS DE MAÑANA ==="))

        self.layout.addWidget(QLabel("Hora recreo 1 mañana:"))
        self.recreo1_manana_input = QTimeEdit()
        self.recreo1_manana_input.setTime(QTime(10, 30))
        self.layout.addWidget(self.recreo1_manana_input)

        self.layout.addWidget(QLabel("Hora recreo 2 mañana:"))
        self.recreo2_manana_input = QTimeEdit()
        self.recreo2_manana_input.setTime(QTime(12, 0))
        self.layout.addWidget(self.recreo2_manana_input)

        # Horarios de recreos tarde (opcionales)
        self.layout.addWidget(QLabel("=== RECREOS DE TARDE (opcional) ==="))

        self.layout.addWidget(QLabel("Hora recreo 1 tarde (opcional):"))
        self.recreo1_tarde_input = QTimeEdit()
        self.recreo1_tarde_input.setTime(QTime(15, 30))
        self.layout.addWidget(self.recreo1_tarde_input)

        self.layout.addWidget(QLabel("Hora recreo 2 tarde (opcional):"))
        self.recreo2_tarde_input = QTimeEdit()
        self.recreo2_tarde_input.setTime(QTime(17, 0))
        self.layout.addWidget(self.recreo2_tarde_input)

        # Botones
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Guardar configuración")
        self.save_btn.clicked.connect(self.guardar_configuracion)
        self.load_btn = QPushButton("Cargar configuración actual")
        self.load_btn.clicked.connect(self.cargar_configuracion)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        self.layout.addLayout(btn_layout)

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

            if config_existente:
                # Actualizar configuración existente
                config_existente.fecha_inicio_curso = fecha_inicio
                config_existente.fecha_fin_curso = fecha_fin
                config_existente.hora_recreo1_manana = recreo1_manana
                config_existente.hora_recreo2_manana = recreo2_manana
                config_existente.hora_recreo1_tarde = recreo1_tarde
                config_existente.hora_recreo2_tarde = recreo2_tarde
                mensaje = "Configuración actualizada correctamente."
            else:
                # Crear nueva configuración
                nueva_config = Configuracion(
                    fecha_inicio_curso=fecha_inicio,
                    fecha_fin_curso=fecha_fin,
                    hora_recreo1_manana=recreo1_manana,
                    hora_recreo2_manana=recreo2_manana,
                    hora_recreo1_tarde=recreo1_tarde,
                    hora_recreo2_tarde=recreo2_tarde
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
                        f"• {profesor.nombre} {profesor.apellidos} "
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
        """Genera la asignación concreta de guardias (próximamente)"""
        QMessageBox.information(
            self,
            "Próximamente",
            "La función de generación de guardias se implementará en el siguiente paso.\n\n"
            "Por ahora puedes ver la distribución calculada de guardias por profesor."
        )


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Guardias de Patio - Gestión")
        self.layout = QVBoxLayout()

        # Pestañas para profesores y zonas
        self.tabs = QTabWidget()
        self.tabs.addTab(ProfesorForm(), "Profesores")
        self.tabs.addTab(ZonaForm(), "Zonas")
        self.tabs.addTab(ConfiguracionForm(), "Configuración")
        self.tabs.addTab(AsignacionGuardiasForm(), "Asignación de Guardias")

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
