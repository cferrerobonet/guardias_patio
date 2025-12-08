"""
Diálogo Acerca de
=================
Muestra información sobre la aplicación: versión, autor, licencia, etc.
"""

import platform
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from utils.constants import APP_AUTHOR, APP_LAST_UPDATE, APP_NAME, APP_VERSION


class DialogoAcercaDe(QDialog):
    """Diálogo con información completa de la aplicación"""

    def __init__(self, parent=None, session=None):
        super().__init__(parent)
        self.session = session
        self.setWindowTitle("Acerca de")
        self.setMinimumSize(500, 450)
        self.setMaximumSize(600, 550)
        self.setup_ui()

    def setup_ui(self):
        """Configurar la interfaz del diálogo"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # ========== HEADER ==========
        header = self._create_header()
        layout.addWidget(header)

        # ========== TABS ==========
        tabs = QTabWidget()
        tabs.addTab(self._create_info_tab(), "📋 Información")
        tabs.addTab(self._create_tech_tab(), "🔧 Técnico")
        tabs.addTab(self._create_stats_tab(), "📊 Estadísticas")
        tabs.addTab(self._create_license_tab(), "📜 Licencia")
        layout.addWidget(tabs)

        # ========== BOTÓN CERRAR ==========
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setFixedWidth(100)
        btn_cerrar.clicked.connect(self.accept)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignCenter)

    def _create_header(self) -> QWidget:
        """Crear header con logo y nombre de la app"""
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Icono de la app
        from utils.icon_manager import get_icon

        icon_label = QLabel()
        icon = get_icon("school", "#3498db", 64)
        icon_label.setPixmap(icon.pixmap(64, 64))
        header_layout.addWidget(icon_label)

        # Nombre y versión
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(10, 0, 0, 0)
        info_layout.setSpacing(2)

        name_label = QLabel(APP_NAME)
        name_label.setFont(QFont("", 18, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50;")
        info_layout.addWidget(name_label)

        version_label = QLabel(f"Versión {APP_VERSION}")
        version_label.setStyleSheet("color: #7f8c8d; font-size: 14px;")
        info_layout.addWidget(version_label)

        header_layout.addWidget(info_widget)
        header_layout.addStretch()

        return header

    def _create_info_tab(self) -> QWidget:
        """Tab con información general"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(12)

        # Información básica
        info_items = [
            ("👤 Autor:", APP_AUTHOR),
            ("📧 Contacto:", "cferrerobonet@gmail.com"),
            ("🔄 Última actualización:", APP_LAST_UPDATE),
            ("🌐 Repositorio:", "github.com/cferrerobonet/guardias_patio"),
        ]

        for label_text, value in info_items:
            row = self._create_info_row(label_text, value)
            layout.addWidget(row)

        # Descripción
        layout.addSpacing(10)
        desc_label = QLabel(
            "Sistema de gestión de guardias de patio para centros educativos. "
            "Permite la asignación automática y equitativa de guardias de recreo "
            "entre el profesorado, con algoritmos optimizados (CP-SAT) que garantizan "
            "equidad perfecta, consecutividad de guardias y preferencia de zona."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("""
            QLabel {
                color: #555;
                font-size: 12px;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
        """)
        layout.addWidget(desc_label)

        layout.addStretch()
        return widget

    def _create_tech_tab(self) -> QWidget:
        """Tab con información técnica"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        # Info del sistema
        tech_items = [
            ("🐍 Python:", platform.python_version()),
            ("💻 Sistema:", f"{platform.system()} {platform.release()}"),
            ("🖥️ Arquitectura:", platform.machine()),
            ("📦 PyQt6:", self._get_pyqt_version()),
            ("🗄️ SQLAlchemy:", self._get_sqlalchemy_version()),
            ("🧮 OR-Tools:", self._get_ortools_version()),
        ]

        for label_text, value in tech_items:
            row = self._create_info_row(label_text, value)
            layout.addWidget(row)

        # Separador
        layout.addSpacing(10)
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        layout.addWidget(separator)
        layout.addSpacing(5)

        # Info de la base de datos
        db_info = self._get_db_info()
        for label_text, value in db_info:
            row = self._create_info_row(label_text, value)
            layout.addWidget(row)

        layout.addStretch()
        return widget

    def _create_stats_tab(self) -> QWidget:
        """Tab con estadísticas del sistema"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(8)

        stats = self._get_stats()
        for label_text, value in stats:
            row = self._create_info_row(label_text, value)
            layout.addWidget(row)

        layout.addStretch()
        return widget

    def _create_license_tab(self) -> QWidget:
        """Tab con información de licencia"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        license_text = QLabel(
            "MIT License\n\n"
            f"Copyright (c) {datetime.now().year} {APP_AUTHOR}\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all "
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR "
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
            "SOFTWARE."
        )
        license_text.setWordWrap(True)
        license_text.setStyleSheet("""
            QLabel {
                font-family: monospace;
                font-size: 11px;
                color: #555;
                padding: 10px;
            }
        """)
        scroll.setWidget(license_text)
        layout.addWidget(scroll)

        return widget

    def _create_info_row(self, label: str, value: str) -> QWidget:
        """Crear una fila de información label: valor"""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(10)

        label_widget = QLabel(label)
        label_widget.setStyleSheet("font-weight: bold; color: #2c3e50;")
        label_widget.setFixedWidth(160)
        row_layout.addWidget(label_widget)

        value_widget = QLabel(str(value))
        value_widget.setStyleSheet("color: #555;")
        value_widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row_layout.addWidget(value_widget)
        row_layout.addStretch()

        return row

    def _get_pyqt_version(self) -> str:
        """Obtener versión de PyQt6"""
        try:
            from PyQt6.QtCore import PYQT_VERSION_STR

            return PYQT_VERSION_STR
        except Exception:
            return "No disponible"

    def _get_sqlalchemy_version(self) -> str:
        """Obtener versión de SQLAlchemy"""
        try:
            import sqlalchemy

            return sqlalchemy.__version__
        except Exception:
            return "No disponible"

    def _get_ortools_version(self) -> str:
        """Obtener versión de OR-Tools"""
        try:
            from ortools import __version__

            return __version__
        except Exception:
            return "No disponible"

    def _get_db_info(self) -> list:
        """Obtener información de la base de datos"""
        info = []
        try:
            from pathlib import Path

            from utils.constants import DB_FILE

            db_path = Path(DB_FILE)
            if db_path.exists():
                size_mb = db_path.stat().st_size / (1024 * 1024)
                info.append(("🗄️ Base de datos:", DB_FILE))
                info.append(("📁 Tamaño:", f"{size_mb:.2f} MB"))
            else:
                info.append(("🗄️ Base de datos:", "No encontrada"))
        except Exception as e:
            info.append(("🗄️ Base de datos:", f"Error: {e}"))
        return info

    def _get_stats(self) -> list:
        """Obtener estadísticas del sistema"""
        stats = []
        try:
            if self.session:
                from infrastructure.database.models import Guardia, Profesor, Zona

                # Contar profesores activos
                n_profesores = (
                    self.session.query(Profesor).filter(Profesor.activo.is_(True)).count()
                )
                stats.append(("👥 Profesores activos:", str(n_profesores)))

                # Contar profesores inactivos
                n_inactivos = (
                    self.session.query(Profesor).filter(Profesor.activo.is_(False)).count()
                )
                stats.append(("👤 Profesores inactivos:", str(n_inactivos)))

                # Contar zonas
                n_zonas = self.session.query(Zona).count()
                stats.append(("📍 Zonas:", str(n_zonas)))

                # Contar guardias
                n_guardias = self.session.query(Guardia).count()
                stats.append(("🛡️ Guardias generadas:", str(n_guardias)))

                # Rango de fechas de guardias
                from sqlalchemy import func

                fecha_min = self.session.query(func.min(Guardia.fecha)).scalar()
                fecha_max = self.session.query(func.max(Guardia.fecha)).scalar()
                if fecha_min and fecha_max:
                    stats.append(("📅 Período guardias:", f"{fecha_min} → {fecha_max}"))
            else:
                stats.append(("⚠️ Sesión:", "No disponible"))
        except Exception as e:
            stats.append(("❌ Error:", str(e)))
        return stats
