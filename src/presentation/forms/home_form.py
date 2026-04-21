"""
Panel de inicio — estado del día, alertas y accesos rápidos.
"""

from datetime import date

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from infrastructure.database.models import Ausencia, Guardia, Profesor, Zona
from presentation.forms.base_form import BaseForm
from presentation.theme.tokens import Spacing
from utils import get_logger

logger = get_logger(__name__)


class _StatCard(QWidget):
    """Card de métrica compacta."""

    def __init__(self, label: str, value: str, color: str, parent=None):
        super().__init__(parent)
        self.setMinimumSize(140, 100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet(
            f"QWidget {{ background: white; border: 2px solid {color};"
            f" border-radius: 8px; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("statValue")
        val_lbl.setStyleSheet(
            f"QLabel {{ font-size: 30px; font-weight: 700; color: {color};"
            f" background: transparent; border: none; }}"
        )
        layout.addWidget(val_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet(
            "QLabel { font-size: 11px; color: #6B7280; background: transparent; border: none; }"
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

        self._val_lbl = val_lbl

    def set_value(self, value: str):
        self._val_lbl.setText(value)


class _AlertItem(QWidget):
    """Fila de alerta con icono de color."""

    def __init__(self, texto: str, nivel: str = "warning", parent=None):
        super().__init__(parent)
        colores = {"warning": "#F59E0B", "error": "#EF4444", "info": "#3B82F6", "ok": "#10B981"}
        color = colores.get(nivel, "#F59E0B")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        dot = QLabel("●")
        dot.setStyleSheet(
            f"QLabel {{ color: {color}; font-size: 10px; background: transparent; }}"
        )
        dot.setFixedWidth(14)
        layout.addWidget(dot)

        msg = QLabel(texto)
        msg.setStyleSheet("QLabel { font-size: 12px; color: #374151; background: transparent; }")
        msg.setWordWrap(True)
        layout.addWidget(msg)


class HomeForm(BaseForm):
    """Dashboard de inicio: estado del día y alertas del sistema."""

    def __init__(self, session):
        super().__init__(session)
        self.setup_ui()
        self.cargar_datos()

    def setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        root.setSpacing(20)

        # Cabecera
        header = QHBoxLayout()
        today_str = date.today().strftime("%A, %d de %B de %Y").capitalize()
        title = QLabel(f"Inicio  ·  {today_str}")
        title.setObjectName("titleMain")
        header.addWidget(title)
        header.addStretch()

        refresh_btn = QPushButton("Actualizar")
        refresh_btn.setMinimumHeight(32)
        refresh_btn.setProperty("secondary", "true")
        refresh_btn.clicked.connect(self.cargar_datos)
        header.addWidget(refresh_btn)
        root.addLayout(header)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFixedHeight(1)
        root.addWidget(sep)

        # Layout principal 2 columnas
        cols = QHBoxLayout()
        cols.setSpacing(20)

        # ── Columna izquierda: estado del día ──
        left = QVBoxLayout()
        left.setSpacing(16)

        lbl_hoy = QLabel("Estado del día")
        lbl_hoy.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 600; color: #374151; }"
        )
        left.addWidget(lbl_hoy)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(12)
        self._card_guardias = _StatCard("Guardias hoy", "—", "#007ACC")
        self._card_ausencias = _StatCard("Ausencias activas", "—", "#EF4444")
        self._card_sustituciones = _StatCard("Sustituciones hoy", "—", "#F59E0B")
        self._card_total = _StatCard("Guardias totales", "—", "#10B981")
        for card in (self._card_guardias, self._card_ausencias,
                     self._card_sustituciones, self._card_total):
            cards_row.addWidget(card)
        left.addLayout(cards_row)

        # Próximos días
        lbl_proximos = QLabel("Resumen del sistema")
        lbl_proximos.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 600; color: #374151; margin-top: 4px; }"
        )
        left.addWidget(lbl_proximos)

        self._summary_lbl = QLabel("Cargando...")
        self._summary_lbl.setStyleSheet(
            "QLabel { font-size: 12px; color: #6B7280; padding: 8px;"
            " background: #F9FAFB; border-radius: 6px; }"
        )
        self._summary_lbl.setWordWrap(True)
        left.addWidget(self._summary_lbl)

        left.addStretch()
        cols.addLayout(left, 3)

        # ── Columna derecha: alertas ──
        right_widget = QWidget()
        right_widget.setStyleSheet(
            "QWidget { background: #F9FAFB; border-radius: 8px; border: 1px solid #E5E7EB; }"
        )
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(8)

        lbl_alertas = QLabel("Alertas del sistema")
        lbl_alertas.setStyleSheet(
            "QLabel { font-size: 13px; font-weight: 600; color: #374151;"
            " background: transparent; border: none; }"
        )
        right_layout.addWidget(lbl_alertas)

        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedHeight(1)
        right_layout.addWidget(sep2)

        self._alerts_scroll = QScrollArea()
        self._alerts_scroll.setWidgetResizable(True)
        self._alerts_scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
        )
        self._alerts_container = QWidget()
        self._alerts_container.setStyleSheet("QWidget { background: transparent; }")
        self._alerts_layout = QVBoxLayout(self._alerts_container)
        self._alerts_layout.setContentsMargins(0, 0, 0, 0)
        self._alerts_layout.setSpacing(4)
        self._alerts_layout.addStretch()
        self._alerts_scroll.setWidget(self._alerts_container)
        right_layout.addWidget(self._alerts_scroll)

        cols.addWidget(right_widget, 2)
        root.addLayout(cols)

    def cargar_datos(self):
        """Carga métricas y alertas desde la BD."""
        try:
            hoy = date.today()

            # Guardias hoy
            guardias_hoy = (
                self.session.query(Guardia)
                .filter(Guardia.fecha == hoy, Guardia.es_sustitucion == False)  # noqa: E712
                .count()
            )
            self._card_guardias.set_value(str(guardias_hoy))

            # Ausencias activas hoy
            ausencias_hoy = (
                self.session.query(Ausencia)
                .filter(
                    Ausencia.activa == True,  # noqa: E712
                    Ausencia.fecha_inicio <= hoy,
                    Ausencia.fecha_fin >= hoy,
                )
                .count()
            )
            self._card_ausencias.set_value(str(ausencias_hoy))

            # Sustituciones hoy
            susts_hoy = (
                self.session.query(Guardia)
                .filter(Guardia.fecha == hoy, Guardia.es_sustitucion == True)  # noqa: E712
                .count()
            )
            self._card_sustituciones.set_value(str(susts_hoy))

            # Total guardias en BD
            total_guardias = self.session.query(Guardia).count()
            self._card_total.set_value(str(total_guardias))

            # Resumen
            n_prof = self.session.query(Profesor).filter(Profesor.activo == True).count()  # noqa: E712
            n_zonas = self.session.query(Zona).count()
            self._summary_lbl.setText(
                f"Profesores activos: {n_prof}  ·  Zonas configuradas: {n_zonas}  ·  "
                f"Guardias en total: {total_guardias}"
            )

            # Alertas
            self._rebuild_alertas(n_prof, n_zonas, total_guardias, ausencias_hoy)

        except Exception as e:
            logger.warning(f"HomeForm.cargar_datos error: {e}")

    def _rebuild_alertas(self, n_prof: int, n_zonas: int, total_guardias: int, ausencias_hoy: int):
        """Reconstruye la lista de alertas."""
        # Limpiar
        while self._alerts_layout.count() > 1:
            item = self._alerts_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        alertas = []

        if total_guardias == 0:
            alertas.append(("No hay guardias generadas — ve a Cálculo y Asignación", "warning"))
        if n_prof == 0:
            alertas.append(("No hay profesores activos configurados", "error"))
        if n_zonas == 0:
            alertas.append(("No hay zonas configuradas", "error"))
        if ausencias_hoy > 0:
            alertas.append((f"{ausencias_hoy} profesor{'es' if ausencias_hoy > 1 else ''} ausente{'s' if ausencias_hoy > 1 else ''} hoy", "warning"))
        if not alertas:
            alertas.append(("Sistema operativo — sin alertas pendientes", "ok"))

        for texto, nivel in alertas:
            item = _AlertItem(texto, nivel)
            self._alerts_layout.insertWidget(self._alerts_layout.count() - 1, item)
