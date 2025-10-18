import os
import sys

from database.db_manager import SessionLocal

# Importar forms refactorizados (Sprint 4)
from presentation.forms import AsignacionGuardiasForm as AsignacionGuardiasFormRefactorizado
from presentation.forms import CalendarioGuardiasForm as CalendarioGuardiasFormRefactorizado
from presentation.forms import ConfiguracionForm as ConfiguracionFormRefactorizado
from presentation.forms import ImportExportForm as ImportExportFormRefactorizado
from presentation.forms import ProfesorForm as ProfesorFormRefactorizado
from presentation.forms import ZonaForm as ZonaFormRefactorizado

# Importar widgets refactorizados (Sprint 5)
from presentation.widgets import (
    GestionarAusenciasForm as GestionarAusenciasRefactorizado,
)
from presentation.widgets import (
    GestorSustituciones as GestorSustitucionesRefactorizado,
)
from presentation.widgets import (
    PanelEstadisticas as PanelEstadisticasRefactorizado,
)
from presentation.widgets import (
    VistaCalendario as VistaCalendarioRefactorizada,
)
from utils import setup_logging

# Configurar logging al inicio
setup_logging()

GUI_AVAILABLE = True
try:
    from PyQt6.QtCore import QDate, QTime
    from PyQt6.QtGui import QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QApplication,
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


# ==============================================================================
# CalendarioGuardiasForm - Movida a src/presentation/forms/calendario_guardias_form.py
# La clase antigua ha sido eliminada y reemplazada por versión refactorizada
# que sigue el patrón MVP (Sprint 4)
# ==============================================================================
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

        # Usar widgets refactorizados (Sprint 5)
        self.vista_calendario = VistaCalendarioRefactorizada(self.session)
        self.gestionar_ausencias = GestionarAusenciasRefactorizado(self.session)
        self.tabs.addTab(self.gestionar_ausencias, "🏥 Ausencias")
        self.tabs.addTab(self.vista_calendario, "📅 Vista Calendario")

        # Usar PanelEstadisticas refactorizado (Sprint 5)
        self.panel_estadisticas = PanelEstadisticasRefactorizado(self.session)
        self.tabs.addTab(self.panel_estadisticas, "📊 Estadísticas")

        # Usar GestorSustituciones refactorizado (Sprint 5)
        self.gestor_sustituciones = GestorSustitucionesRefactorizado(self.session)
        self.tabs.addTab(self.gestor_sustituciones, "🔄 Sustituciones")

        # Usar CalendarioGuardiasForm refactorizado (Sprint 4)
        self.tabs.addTab(CalendarioGuardiasFormRefactorizado(self.session), "📆 Calendario")
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
