import os
import sys

import ui_styles as styles
from database.db_manager import SessionLocal
from models.models import Configuracion, Guardia, Profesor, Zona

# Importar forms refactorizados (Sprint 4)
from presentation.forms import AsignacionGuardiasForm as AsignacionGuardiasFormRefactorizado
from presentation.forms import ConfiguracionForm as ConfiguracionFormRefactorizado
from presentation.forms import ProfesorForm as ProfesorFormRefactorizado
from presentation.forms import ZonaForm as ZonaFormRefactorizado
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from utils import setup_logging
from widgets.gestionar_ausencias import GestionarAusenciasForm
from widgets.gestionar_sustituciones import GestorSustituciones
from widgets.panel_estadisticas import PanelEstadisticas
from widgets.vista_calendario import VistaCalendario

# Configurar logging al inicio
setup_logging()

GUI_AVAILABLE = True
try:
    from PyQt6.QtCore import QDate, QTime
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QApplication,
        QCalendarWidget,
        QCheckBox,
        QComboBox,
        QDateEdit,
        QFileDialog,
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


# ==============================================================================
# ProfesorForm - Movida a src/presentation/forms/profesor_form.py
# La clase antigua ha sido eliminada y reemplazada por versión refactorizada
# que sigue el patrón MVP (Sprint 4)
# ==============================================================================

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
        # Usar ProfesorForm refactorizado (Sprint 4)
        self.tabs.addTab(ProfesorFormRefactorizado(self.session), "👨‍🏫 Profesores")
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
