"""
Gráficos nativos con QPainter — sin dependencias externas.
Reemplazan matplotlib para histogramas y pie charts simples.
"""

import math

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget


class BarChartWidget(QWidget):
    """Gráfico de barras verticales u horizontales con QPainter."""

    def __init__(
        self,
        datos: list[tuple[str, float, str]] | None = None,
        titulo: str = "",
        horizontal: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self._datos: list[tuple[str, float, str]] = datos or []
        self._titulo = titulo
        self._horizontal = horizontal
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_datos(self, datos: list[tuple[str, float, str]], titulo: str = ""):
        self._datos = datos
        if titulo:
            self._titulo = titulo
        self.update()

    def paintEvent(self, event):
        if not self._datos:
            self._paint_empty()
            return
        if self._horizontal:
            self._paint_horizontal()
        else:
            self._paint_vertical()

    def _paint_empty(self):
        p = QPainter(self)
        p.setPen(QColor("#9CA3AF"))
        p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos")

    def _paint_vertical(self):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_top = 30 if self._titulo else 10
        pad_bot = 50
        pad_left = 40
        pad_right = 10

        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bot

        max_val = max(v for _, v, _ in self._datos) or 1
        n = len(self._datos)
        bar_w = max(4, chart_w / n - 4)

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 4, w, 22), Qt.AlignmentFlag.AlignCenter, self._titulo)

        # Y-axis gridlines
        p.setPen(QPen(QColor("#E5E7EB"), 1))
        for i in range(5):
            y = pad_top + chart_h - int(chart_h * i / 4)
            p.drawLine(pad_left, y, w - pad_right, y)
            val = max_val * i / 4
            p.setPen(QColor("#9CA3AF"))
            p.setFont(QFont("Arial", 7))
            p.drawText(QRect(0, y - 8, pad_left - 2, 16), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(int(val)))
            p.setPen(QPen(QColor("#E5E7EB"), 1))

        for i, (label, valor, color) in enumerate(self._datos):
            x = pad_left + i * (chart_w / n) + (chart_w / n - bar_w) / 2
            bar_h_px = int((valor / max_val) * chart_h)
            y = pad_top + chart_h - bar_h_px

            p.fillRect(int(x), y, int(bar_w), bar_h_px, QColor(color))

            # Valor sobre la barra
            p.setFont(QFont("Arial", 7))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(int(x), y - 14, int(bar_w), 14), Qt.AlignmentFlag.AlignCenter, str(int(valor)))

            # Etiqueta bajo la barra
            label_short = label[:10] if len(label) > 10 else label
            p.setFont(QFont("Arial", 7))
            p.setPen(QColor("#6B7280"))
            p.save()
            p.translate(int(x + bar_w / 2), h - pad_bot + 4)
            p.rotate(45)
            p.drawText(0, 0, label_short)
            p.restore()

    def _paint_horizontal(self):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_top = 30 if self._titulo else 10
        pad_bot = 10
        pad_left = 100
        pad_right = 40

        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bot

        max_val = max(v for _, v, _ in self._datos) or 1
        n = len(self._datos)
        bar_h_px = max(8, chart_h / n - 4)

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 4, w, 22), Qt.AlignmentFlag.AlignCenter, self._titulo)

        for i, (label, valor, color) in enumerate(self._datos):
            y = pad_top + i * (chart_h / n) + (chart_h / n - bar_h_px) / 2
            bar_w_px = int((valor / max_val) * chart_w)

            p.fillRect(pad_left, int(y), bar_w_px, int(bar_h_px), QColor(color))

            p.setFont(QFont("Arial", 8))
            p.setPen(QColor("#374151"))
            label_short = label.split(",")[0][:18]
            p.drawText(QRect(0, int(y), pad_left - 4, int(bar_h_px)), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, label_short)

            p.setPen(QColor("#374151"))
            p.setFont(QFont("Arial", 7))
            p.drawText(QRect(pad_left + bar_w_px + 2, int(y), 35, int(bar_h_px)), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(int(valor)))


class PieChartWidget(QWidget):
    """Gráfico de tarta (pie/donut) nativo con QPainter."""

    COLORS = [
        "#007ACC", "#10B981", "#F59E0B", "#EF4444", "#8B5CF6",
        "#06B6D4", "#84CC16", "#F97316", "#EC4899", "#6B7280",
    ]

    def __init__(
        self,
        datos: list[tuple[str, float]] | None = None,
        titulo: str = "",
        donut: bool = True,
        parent=None,
    ):
        super().__init__(parent)
        self._datos: list[tuple[str, float]] = datos or []
        self._titulo = titulo
        self._donut = donut
        self.setMinimumHeight(200)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_datos(self, datos: list[tuple[str, float]], titulo: str = ""):
        self._datos = datos
        if titulo:
            self._titulo = titulo
        self.update()

    def paintEvent(self, event):
        if not self._datos:
            p = QPainter(self)
            p.setPen(QColor("#9CA3AF"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos")
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad = 10
        legend_h = 20 * len(self._datos)
        title_h = 24 if self._titulo else 0

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 4, w, 20), Qt.AlignmentFlag.AlignCenter, self._titulo)

        chart_area_h = h - title_h - legend_h - pad * 2
        diameter = min(w - 2 * pad, chart_area_h)
        if diameter < 20:
            return

        cx = w // 2
        cy = title_h + pad + diameter // 2
        r = diameter // 2
        total = sum(v for _, v in self._datos) or 1

        start_angle = 90 * 16
        for i, (label, valor) in enumerate(self._datos):
            span = int((valor / total) * 360 * 16)
            color = QColor(self.COLORS[i % len(self.COLORS)])
            p.setBrush(color)
            p.setPen(QPen(QColor("white"), 2))
            p.drawPie(cx - r, cy - r, diameter, diameter, start_angle, -span)
            start_angle -= span

        if self._donut:
            inner_r = int(r * 0.55)
            p.setBrush(QColor("white"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)

        # Leyenda
        legend_y = title_h + pad + diameter + pad
        for i, (label, valor) in enumerate(self._datos):
            color = QColor(self.COLORS[i % len(self.COLORS)])
            p.fillRect(pad, legend_y + i * 20, 12, 12, color)
            pct = f"{valor / total * 100:.1f}%"
            p.setFont(QFont("Arial", 8))
            p.setPen(QColor("#374151"))
            p.drawText(pad + 16, legend_y + i * 20, w - pad - 16, 16, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, f"{label} ({int(valor)}) — {pct}")
