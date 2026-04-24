"""
Gráficos nativos con QPainter — sin dependencias externas.
Reemplazan matplotlib para histogramas y pie charts simples.
"""

import math

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

BAR_HEIGHT = 26        # px por barra en modo horizontal
BAR_GAP = 4            # px de separación entre barras
PAD_LEFT = 210         # espacio para etiquetas de nombre
PAD_RIGHT = 55         # espacio para valor numérico
PAD_TOP_TITLE = 32
PAD_BOT = 12


def _color_por_valor(valor, media, max_val):
    """Devuelve color según desviación respecto a la media."""
    if media <= 0:
        return QColor("#007ACC")
    ratio = valor / media
    if ratio <= 0.85:
        return QColor("#60A5FA")   # azul claro — bajo
    elif ratio <= 1.15:
        return QColor("#22C55E")   # verde — en media
    elif ratio <= 1.40:
        return QColor("#F59E0B")   # ámbar — algo alto
    else:
        return QColor("#EF4444")   # rojo — muy alto


class BarChartWidget(QWidget):
    """Gráfico de barras horizontales con QPainter, altura dinámica."""

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
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self._actualizar_altura_minima()

    def set_datos(self, datos: list[tuple[str, float, str]], titulo: str = ""):
        self._datos = datos
        if titulo:
            self._titulo = titulo
        self._actualizar_altura_minima()
        self.update()

    def _actualizar_altura_minima(self):
        n = len(self._datos)
        if n == 0:
            self.setMinimumHeight(60)
            return
        title_h = PAD_TOP_TITLE if self._titulo else 12
        altura = title_h + PAD_BOT + n * (BAR_HEIGHT + BAR_GAP) + 20
        self.setMinimumHeight(altura)

    def paintEvent(self, event):
        if not self._datos:
            p = QPainter(self)
            p.setPen(QColor("#9CA3AF"))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sin datos")
            return
        if self._horizontal:
            self._paint_horizontal()
        else:
            self._paint_vertical()

    def _paint_vertical(self):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        pad_top = PAD_TOP_TITLE if self._titulo else 12
        pad_bot, pad_left, pad_right = 50, 40, 10
        chart_w = w - pad_left - pad_right
        chart_h = h - pad_top - pad_bot
        max_val = max(v for _, v, _ in self._datos) or 1
        n = len(self._datos)
        bar_w = max(4, chart_w / n - 4)

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 4, w, 22), Qt.AlignmentFlag.AlignCenter, self._titulo)

        p.setPen(QPen(QColor("#E5E7EB"), 1))
        for i in range(5):
            y = pad_top + chart_h - int(chart_h * i / 4)
            p.drawLine(pad_left, y, w - pad_right, y)
            val = max_val * i / 4
            p.setPen(QColor("#9CA3AF"))
            p.setFont(QFont("Arial", 7))
            p.drawText(QRect(0, y - 8, pad_left - 2, 16),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, str(int(val)))
            p.setPen(QPen(QColor("#E5E7EB"), 1))

        media = sum(v for _, v, _ in self._datos) / n if n else 1
        for i, (label, valor, _) in enumerate(self._datos):
            x = pad_left + i * (chart_w / n) + (chart_w / n - bar_w) / 2
            bar_h_px = int((valor / max_val) * chart_h)
            y = pad_top + chart_h - bar_h_px
            color = _color_por_valor(valor, media, max_val)
            p.fillRect(int(x), y, int(bar_w), bar_h_px, color)
            p.setFont(QFont("Arial", 7))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(int(x), y - 14, int(bar_w), 14), Qt.AlignmentFlag.AlignCenter, str(int(valor)))
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
        title_h = PAD_TOP_TITLE if self._titulo else 12
        chart_w = w - PAD_LEFT - PAD_RIGHT
        n = len(self._datos)
        if chart_w <= 0 or n == 0:
            return

        max_val = max(v for _, v, _ in self._datos) or 1
        media = sum(v for _, v, _ in self._datos) / n

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 6, w, 22), Qt.AlignmentFlag.AlignCenter, self._titulo)

        # Línea de referencia (media)
        media_x = PAD_LEFT + int((media / max_val) * chart_w)
        p.setPen(QPen(QColor("#9CA3AF"), 1, Qt.PenStyle.DashLine))
        p.drawLine(media_x, title_h, media_x, h - PAD_BOT)
        p.setFont(QFont("Arial", 7))
        p.setPen(QColor("#9CA3AF"))
        p.drawText(media_x - 20, title_h - 2, 40, 12, Qt.AlignmentFlag.AlignCenter, f"μ={int(media)}")

        for i, (label, valor, _) in enumerate(self._datos):
            y = title_h + i * (BAR_HEIGHT + BAR_GAP)
            bar_w_px = max(2, int((valor / max_val) * chart_w))
            color = _color_por_valor(valor, media, max_val)

            # Fondo alterno
            if i % 2 == 0:
                p.fillRect(0, y - 1, w, BAR_HEIGHT + 2, QColor("#F9FAFB"))

            # Barra
            p.fillRect(PAD_LEFT, y + 2, bar_w_px, BAR_HEIGHT - 4, color)

            # Etiqueta nombre (apellidos)
            apellidos = label.split(",")[0].strip()
            if len(apellidos) > 26:
                apellidos = apellidos[:24] + "…"
            p.setFont(QFont("Arial", 8))
            p.setPen(QColor("#111827"))
            p.drawText(QRect(4, y, PAD_LEFT - 8, BAR_HEIGHT),
                       Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, apellidos)

            # Valor numérico a la derecha
            p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(PAD_LEFT + bar_w_px + 4, y, PAD_RIGHT - 4, BAR_HEIGHT),
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, str(int(valor)))

        # Eje base
        p.setPen(QPen(QColor("#D1D5DB"), 1))
        p.drawLine(PAD_LEFT, title_h, PAD_LEFT, h - PAD_BOT)

        # Leyenda de colores
        legend_y = h - PAD_BOT + 2
        items = [
            ("#60A5FA", "Bajo"),
            ("#22C55E", "En media"),
            ("#F59E0B", "+15%"),
            ("#EF4444", "+40%"),
        ]
        lx = PAD_LEFT
        p.setFont(QFont("Arial", 7))
        for color_hex, text in items:
            p.fillRect(lx, legend_y, 10, 10, QColor(color_hex))
            p.setPen(QColor("#6B7280"))
            p.drawText(lx + 13, legend_y, 55, 10,
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, text)
            lx += 72


class PieChartWidget(QWidget):
    """Gráfico de tarta (donut) nativo con QPainter."""

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
        self.setMinimumHeight(320)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

    def set_datos(self, datos: list[tuple[str, float]], titulo: str = ""):
        self._datos = datos
        if titulo:
            self._titulo = titulo
        n = len(datos)
        self.setMinimumHeight(max(320, 280 + n * 22))
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
        title_h = 28 if self._titulo else 0
        legend_h = 22 * len(self._datos)
        pad = 12

        if self._titulo:
            p.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(0, 4, w, 22), Qt.AlignmentFlag.AlignCenter, self._titulo)

        chart_area_h = h - title_h - legend_h - pad * 2
        diameter = min(w - 2 * pad, chart_area_h)
        if diameter < 40:
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
            # Etiqueta de porcentaje dentro del sector
            pct = valor / total * 100
            if pct >= 5:
                mid_angle = math.radians(90 - (start_angle / 16) + (span / 16) / 2)
                label_r = r * 0.68
                lx = int(cx + label_r * math.cos(mid_angle))
                ly = int(cy - label_r * math.sin(mid_angle))
                p.setFont(QFont("Arial", 8, QFont.Weight.Bold))
                p.setPen(QColor("white"))
                p.drawText(QRect(lx - 18, ly - 8, 36, 16), Qt.AlignmentFlag.AlignCenter,
                           f"{pct:.0f}%")
            start_angle -= span

        if self._donut:
            inner_r = int(r * 0.52)
            p.setBrush(QColor("white"))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(cx - inner_r, cy - inner_r, inner_r * 2, inner_r * 2)
            # Total en el centro
            p.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            p.setPen(QColor("#374151"))
            p.drawText(QRect(cx - inner_r, cy - 14, inner_r * 2, 28),
                       Qt.AlignmentFlag.AlignCenter, str(int(total)))
            p.setFont(QFont("Arial", 7))
            p.setPen(QColor("#9CA3AF"))
            p.drawText(QRect(cx - inner_r, cy + 10, inner_r * 2, 14),
                       Qt.AlignmentFlag.AlignCenter, "guardias")

        # Leyenda
        legend_y = title_h + pad + diameter + pad
        for i, (label, valor) in enumerate(self._datos):
            row_y = legend_y + i * 22
            color = QColor(self.COLORS[i % len(self.COLORS)])
            p.fillRect(pad, row_y + 4, 14, 14, color)
            pct = f"{valor / total * 100:.1f}%"
            p.setFont(QFont("Arial", 9))
            p.setPen(QColor("#374151"))
            p.drawText(pad + 20, row_y, w - pad - 20, 22,
                       Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                       f"{label}  ·  {int(valor)} guardias  ({pct})")
