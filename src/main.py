import os
import sys

import ui_styles as styles
from database.db_manager import SessionLocal
from models.models import Guardia, Profesor, Zona

# Importar forms refactorizados (Sprint 4)
from presentation.forms import AsignacionGuardiasForm as AsignacionGuardiasFormRefactorizado
from presentation.forms import ConfiguracionForm as ConfiguracionFormRefactorizado
from presentation.forms import ImportExportForm as ImportExportFormRefactorizado
from presentation.forms import ProfesorForm as ProfesorFormRefactorizado
from presentation.forms import ZonaForm as ZonaFormRefactorizado
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


# ==============================================================================
# ImportExportForm - Movida a src/presentation/forms/import_export_form.py
# La clase antigua ha sido eliminada y reemplazada por versión refactorizada
# que sigue el patrón MVP (Sprint 4)
# ==============================================================================
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
        # Usar ImportExportForm refactorizado (Sprint 4)
        self.tabs.addTab(ImportExportFormRefactorizado(self.session), "💾 Importar / Exportar")

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
