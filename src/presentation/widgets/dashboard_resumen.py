"""
Dashboard de Resumen General.

Muestra estadísticas clave y accesos rápidos con ilustraciones vectoriales.
"""

from datetime import datetime
from typing import Optional

from database.db_manager import SessionLocal
from models.models import Ausencia, Guardia, Profesor
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session


class DibujoVectorial(QWidget):
    """Widget que dibuja una ilustración vectorial personalizada."""

    def __init__(self, tipo: str, parent: Optional[QWidget] = None):
        """
        Inicializa dibujo vectorial.

        Args:
            tipo: Tipo de dibujo ('generar', 'calendario', 'ausencias',
                  'profesores', 'exportar', 'reportes')
            parent: Widget padre
        """
        super().__init__(parent)
        self.tipo = tipo
        self.setFixedSize(80, 80)

    def paintEvent(self, event):
        """Dibuja la ilustración vectorial."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.tipo == 'generar':
            self._dibujar_dados_guardias(painter)
        elif self.tipo == 'calendario':
            self._dibujar_calendario(painter)
        elif self.tipo == 'ausencias':
            self._dibujar_cruz_medica(painter)
        elif self.tipo == 'profesores':
            self._dibujar_grupo_personas(painter)
        elif self.tipo == 'exportar':
            self._dibujar_documento_pdf(painter)
        elif self.tipo == 'reportes':
            self._dibujar_graficos_reportes(painter)

    def _dibujar_dados_guardias(self, painter: QPainter):
        """Dibuja dos dados representando generación aleatoria."""
        # Dado 1
        path1 = QPainterPath()
        path1.addRoundedRect(10, 15, 30, 30, 4, 4)

        gradient1 = QLinearGradient(10, 15, 40, 45)
        gradient1.setColorAt(0, QColor('#e74c3c'))
        gradient1.setColorAt(1, QColor('#c0392b'))
        painter.fillPath(path1, QBrush(gradient1))

        painter.setPen(QPen(QColor('#a93226'), 2))
        painter.drawPath(path1)

        # Puntos del dado 1 (número 6)
        painter.setBrush(QBrush(QColor('white')))
        painter.setPen(Qt.PenStyle.NoPen)
        puntos1 = [(15, 20), (15, 30), (15, 40), (35, 20), (35, 30), (35, 40)]
        for x, y in puntos1:
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)

        # Dado 2 (más pequeño, detrás)
        path2 = QPainterPath()
        path2.addRoundedRect(42, 25, 25, 25, 3, 3)

        gradient2 = QLinearGradient(42, 25, 67, 50)
        gradient2.setColorAt(0, QColor('#3498db'))
        gradient2.setColorAt(1, QColor('#2980b9'))
        painter.fillPath(path2, QBrush(gradient2))

        painter.setPen(QPen(QColor('#21618c'), 2))
        painter.drawPath(path2)

        # Puntos del dado 2 (número 5)
        painter.setBrush(QBrush(QColor('white')))
        painter.setPen(Qt.PenStyle.NoPen)
        puntos2 = [(47, 30), (47, 45), (62, 30), (62, 45), (54.5, 37.5)]
        for x, y in puntos2:
            painter.drawEllipse(QPointF(x, y), 2, 2)

    def _dibujar_calendario(self, painter: QPainter):
        """Dibuja un calendario de pared."""
        # Marco del calendario
        path_marco = QPainterPath()
        path_marco.addRoundedRect(15, 20, 50, 45, 3, 3)

        gradient_marco = QLinearGradient(15, 20, 65, 65)
        gradient_marco.setColorAt(0, QColor('#ecf0f1'))
        gradient_marco.setColorAt(1, QColor('#bdc3c7'))
        painter.fillPath(path_marco, QBrush(gradient_marco))

        painter.setPen(QPen(QColor('#95a5a6'), 2))
        painter.drawPath(path_marco)

        # Anillas superior
        painter.setBrush(QBrush(QColor('#34495e')))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(27, 18), 3, 3)
        painter.drawEllipse(QPointF(40, 18), 3, 3)
        painter.drawEllipse(QPointF(53, 18), 3, 3)

        # Cabecera del calendario
        painter.setBrush(QBrush(QColor('#e74c3c')))
        painter.drawRect(15, 22, 50, 10)

        # Días (grid de puntos)
        painter.setBrush(QBrush(QColor('#3498db')))
        for fila in range(3):
            for col in range(5):
                x = 20 + col * 9
                y = 38 + fila * 8
                painter.drawEllipse(QPointF(x, y), 2, 2)

        # Marcar día actual
        painter.setBrush(QBrush(QColor('#27ae60')))
        painter.drawEllipse(QPointF(38, 46), 3, 3)

    def _dibujar_cruz_medica(self, painter: QPainter):
        """Dibuja un botiquín médico con cruz."""
        # Caja del botiquín
        path_caja = QPainterPath()
        path_caja.addRoundedRect(20, 25, 40, 35, 3, 3)

        gradient_caja = QLinearGradient(20, 25, 60, 60)
        gradient_caja.setColorAt(0, QColor('#e74c3c'))
        gradient_caja.setColorAt(1, QColor('#c0392b'))
        painter.fillPath(path_caja, QBrush(gradient_caja))

        painter.setPen(QPen(QColor('#a93226'), 2))
        painter.drawPath(path_caja)

        # Asa superior
        path_asa = QPainterPath()
        path_asa.moveTo(30, 25)
        path_asa.quadTo(40, 15, 50, 25)
        painter.setPen(QPen(QColor('#c0392b'), 3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawPath(path_asa)

        # Cruz blanca
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor('white')))
        # Vertical
        painter.drawRoundedRect(37, 33, 6, 20, 2, 2)
        # Horizontal
        painter.drawRoundedRect(30, 40, 20, 6, 2, 2)

        # Brillo
        painter.setBrush(QBrush(QColor(255, 255, 255, 60)))
        painter.drawEllipse(QPointF(28, 32), 8, 8)

    def _dibujar_grupo_personas(self, painter: QPainter):
        """Dibuja un grupo de 3 personas."""
        colores = [
            (QColor('#3498db'), QColor('#2980b9')),
            (QColor('#27ae60'), QColor('#229954')),
            (QColor('#e74c3c'), QColor('#c0392b'))
        ]

        posiciones = [(25, 40), (40, 35), (55, 40)]

        for idx, (x, y) in enumerate(posiciones):
            color1, color2 = colores[idx]

            # Cabeza
            gradient_cabeza = QLinearGradient(x, y-15, x, y-5)
            gradient_cabeza.setColorAt(0, color1.lighter(110))
            gradient_cabeza.setColorAt(1, color2)

            painter.setBrush(QBrush(gradient_cabeza))
            painter.setPen(QPen(color2.darker(120), 1.5))
            painter.drawEllipse(QPointF(x, y-10), 6, 6)

            # Cuerpo
            path_cuerpo = QPainterPath()
            path_cuerpo.moveTo(x, y-4)
            path_cuerpo.lineTo(x-8, y+12)
            path_cuerpo.lineTo(x-8, y+18)
            path_cuerpo.lineTo(x+8, y+18)
            path_cuerpo.lineTo(x+8, y+12)
            path_cuerpo.closeSubpath()

            gradient_cuerpo = QLinearGradient(x, y-4, x, y+18)
            gradient_cuerpo.setColorAt(0, color1)
            gradient_cuerpo.setColorAt(1, color2)

            painter.setBrush(QBrush(gradient_cuerpo))
            painter.setPen(QPen(color2.darker(120), 1.5))
            painter.drawPath(path_cuerpo)

    def _dibujar_documento_pdf(self, painter: QPainter):
        """Dibuja un documento PDF siendo exportado."""
        # Documento principal
        path_doc = QPainterPath()
        path_doc.moveTo(25, 15)
        path_doc.lineTo(50, 15)
        path_doc.lineTo(60, 25)
        path_doc.lineTo(60, 60)
        path_doc.lineTo(25, 60)
        path_doc.closeSubpath()

        gradient_doc = QLinearGradient(25, 15, 60, 60)
        gradient_doc.setColorAt(0, QColor('#ecf0f1'))
        gradient_doc.setColorAt(1, QColor('#bdc3c7'))
        painter.fillPath(path_doc, QBrush(gradient_doc))

        painter.setPen(QPen(QColor('#7f8c8d'), 2))
        painter.drawPath(path_doc)

        # Doblez esquina
        path_doblez = QPainterPath()
        path_doblez.moveTo(50, 15)
        path_doblez.lineTo(50, 25)
        path_doblez.lineTo(60, 25)
        painter.setBrush(QBrush(QColor('#95a5a6')))
        painter.drawPath(path_doblez)

        # Texto "PDF"
        painter.setPen(QPen(QColor('#e74c3c'), 2))
        painter.setFont(painter.font())
        font = painter.font()
        font.setBold(True)
        font.setPixelSize(12)
        painter.setFont(font)
        painter.drawText(30, 35, 30, 15, Qt.AlignmentFlag.AlignCenter, "PDF")

        # Flecha de descarga
        painter.setPen(QPen(QColor('#27ae60'), 3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawLine(42, 45, 42, 55)
        # Punta de flecha
        path_flecha = QPainterPath()
        path_flecha.moveTo(37, 51)
        path_flecha.lineTo(42, 56)
        path_flecha.lineTo(47, 51)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(path_flecha)

    def _dibujar_graficos_reportes(self, painter: QPainter):
        """Dibuja gráficos de barras y líneas."""
        # Fondo papel
        painter.setBrush(QBrush(QColor('#ecf0f1')))
        painter.setPen(QPen(QColor('#bdc3c7'), 2))
        painter.drawRoundedRect(15, 15, 50, 50, 3, 3)

        # Ejes
        painter.setPen(QPen(QColor('#34495e'), 2))
        painter.drawLine(22, 55, 22, 25)  # Eje Y
        painter.drawLine(22, 55, 58, 55)  # Eje X

        # Barras
        alturas = [15, 25, 20, 30]
        colores_barras = [QColor('#3498db'), QColor('#27ae60'),
                          QColor('#f39c12'), QColor('#e74c3c')]

        for i, (altura, color) in enumerate(zip(alturas, colores_barras)):
            x = 28 + i * 8

            gradient = QLinearGradient(x, 55-altura, x+5, 55)
            gradient.setColorAt(0, color.lighter(120))
            gradient.setColorAt(1, color)

            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(color.darker(120), 1))
            painter.drawRect(x, 55-altura, 5, altura)

        # Línea de tendencia
        puntos_linea = [QPointF(30, 45), QPointF(38, 38),
                        QPointF(46, 40), QPointF(54, 32)]
        path_linea = QPainterPath()
        path_linea.moveTo(puntos_linea[0])
        for punto in puntos_linea[1:]:
            path_linea.lineTo(punto)

        painter.setPen(QPen(QColor('#9b59b6'), 2.5, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawPath(path_linea)

        # Puntos en la línea
        painter.setBrush(QBrush(QColor('#9b59b6')))
        painter.setPen(QPen(QColor('white'), 1.5))
        for punto in puntos_linea:
            painter.drawEllipse(punto, 3, 3)


class BotonConDibujo(QWidget):
    """Contenedor que muestra un dibujo vectorial junto a un botón."""

    def __init__(
        self,
        texto: str,
        tipo_dibujo: str,
        parent: Optional[QWidget] = None,
    ):
        """
        Inicializa botón con dibujo.

        Args:
            texto: Texto del botón
            tipo_dibujo: Tipo de dibujo vectorial
            parent: Widget padre
        """
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Dibujo vectorial
        self.dibujo = DibujoVectorial(tipo_dibujo)
        layout.addWidget(self.dibujo)

        # Botón
        self.boton = QPushButton(texto)
        self.boton.setMinimumHeight(70)
        self.boton.setStyleSheet(
            """
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px 20px;
                font-size: 15px;
                font-weight: 600;
                text-align: left;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #5dade2, stop:1 #3498db);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #21618c);
            }
        """
        )
        layout.addWidget(self.boton, 1)

    def clicked_connect(self, slot):
        """Conecta la señal clicked del botón."""
        self.boton.clicked.connect(slot)


class TarjetaEstadistica(QFrame):
    """Tarjeta con una estadística destacada."""

    def __init__(
        self,
        titulo: str,
        valor: str,
        icono: str,
        color: str,
        parent: Optional[QWidget] = None,
    ):
        """
        Inicializa tarjeta de estadística.

        Args:
            titulo: Título de la estadística
            valor: Valor a mostrar
            icono: Emoji/icono
            color: Color de fondo (#hex)
            parent: Widget padre
        """
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            TarjetaEstadistica {{
                background-color: {color};
                border-radius: 8px;
                padding: 16px;
            }}
        """
        )

        layout = QVBoxLayout(self)

        # Icono
        icono_label = QLabel(icono)
        icono_label.setStyleSheet(
            "font-size: 32px; color: white; background: transparent;"
        )
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Valor
        valor_label = QLabel(valor)
        valor_label.setStyleSheet(
            "font-size: 28px; font-weight: bold; "
            "color: white; background: transparent;"
        )
        valor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Título
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(
            "font-size: 13px; color: rgba(255,255,255,0.9); "
            "background: transparent;"
        )
        titulo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titulo_label.setWordWrap(True)

        layout.addWidget(icono_label)
        layout.addWidget(valor_label)
        layout.addWidget(titulo_label)
        layout.addStretch()


class BotonAccesoRapido(QPushButton):
    """Botón de acceso rápido a funcionalidades."""

    def __init__(
        self,
        texto: str,
        icono: str,
        parent: Optional[QWidget] = None,
    ):
        """
        Inicializa botón de acceso rápido.

        Args:
            texto: Texto del botón
            icono: Emoji/icono
            parent: Widget padre
        """
        super().__init__(f"{icono}  {texto}", parent)
        self.setMinimumHeight(50)
        self.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """
        )


class DashboardResumen(QWidget):
    """Dashboard principal con resumen de estadísticas."""

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa dashboard.

        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self.session: Optional[Session] = None
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Título
        titulo = QLabel("📊 Dashboard - Resumen General")
        titulo.setStyleSheet(
            "font-size: 24px; font-weight: bold; color: #2c3e50;"
        )
        layout.addWidget(titulo)

        # Contenedor de tarjetas de estadísticas
        self.tarjetas_container = QGridLayout()
        self.tarjetas_container.setSpacing(16)
        layout.addLayout(self.tarjetas_container)

        # Sección de accesos rápidos
        accesos_titulo = QLabel("⚡ Accesos Rápidos")
        accesos_titulo.setStyleSheet(
            "font-size: 18px; font-weight: bold; "
            "color: #2c3e50; margin-top: 10px;"
        )
        layout.addWidget(accesos_titulo)

        accesos_grid = QGridLayout()
        accesos_grid.setSpacing(12)

        # Botones de acceso rápido con dibujos vectoriales
        btn_generar = BotonConDibujo("🎲 Generar Guardias", "generar")
        btn_calendario = BotonConDibujo("📅 Ver Calendario", "calendario")
        btn_ausencias = BotonConDibujo("🏥 Gestionar Ausencias", "ausencias")
        btn_profesores = BotonConDibujo("👥 Gestionar Profesores", "profesores")
        btn_exportar = BotonConDibujo("📄 Exportar PDFs", "exportar")
        btn_reportes = BotonConDibujo("📊 Generar Reportes", "reportes")

        accesos_grid.addWidget(btn_generar, 0, 0)
        accesos_grid.addWidget(btn_calendario, 0, 1)
        accesos_grid.addWidget(btn_ausencias, 1, 0)
        accesos_grid.addWidget(btn_profesores, 1, 1)
        accesos_grid.addWidget(btn_exportar, 2, 0)
        accesos_grid.addWidget(btn_reportes, 2, 1)

        layout.addLayout(accesos_grid)
        layout.addStretch()

        # Conectar señales (se conectarán desde la ventana principal)
        self.btn_generar = btn_generar
        self.btn_calendario = btn_calendario
        self.btn_ausencias = btn_ausencias
        self.btn_profesores = btn_profesores
        self.btn_exportar = btn_exportar
        self.btn_reportes = btn_reportes

    def cargar_estadisticas(self) -> None:
        """Carga y muestra estadísticas actuales."""
        # Limpiar tarjetas existentes
        while self.tarjetas_container.count():
            item = self.tarjetas_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            self.session = SessionLocal()

            # Obtener mes actual
            hoy = datetime.now()
            primer_dia_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                primer_dia_siguiente = datetime(hoy.year + 1, 1, 1)
            else:
                primer_dia_siguiente = datetime(
                    hoy.year, hoy.month + 1, 1
                )

            # 1. Total de profesores
            total_profesores = (
                self.session.query(Profesor)
                .filter(Profesor.activo == True)  # noqa: E712
                .count()
            )
            tarjeta_profesores = TarjetaEstadistica(
                "Profesores Activos",
                str(total_profesores),
                "👥",
                "#3498db",
            )
            self.tarjetas_container.addWidget(tarjeta_profesores, 0, 0)

            # 2. Guardias del mes actual
            guardias_mes = (
                self.session.query(Guardia)
                .filter(
                    Guardia.fecha >= primer_dia_mes,
                    Guardia.fecha < primer_dia_siguiente,
                )
                .count()
            )
            tarjeta_guardias = TarjetaEstadistica(
                "Guardias Este Mes",
                str(guardias_mes),
                "🛡️",
                "#27ae60",
            )
            self.tarjetas_container.addWidget(tarjeta_guardias, 0, 1)

            # 3. Ausencias del mes
            ausencias_mes = (
                self.session.query(Ausencia)
                .filter(
                    Ausencia.fecha_inicio <= primer_dia_siguiente,
                    Ausencia.fecha_fin >= primer_dia_mes,
                )
                .count()
            )
            tarjeta_ausencias = TarjetaEstadistica(
                "Ausencias Activas",
                str(ausencias_mes),
                "🏥",
                "#e74c3c",
            )
            self.tarjetas_container.addWidget(tarjeta_ausencias, 0, 2)

            # 4. Cobertura del mes (%)
            dias_laborables = self._calcular_dias_laborables(
                primer_dia_mes, primer_dia_siguiente
            )
            # Asumiendo 5 turnos por día (recreos)
            slots_necesarios = dias_laborables * 5

            if slots_necesarios > 0:
                cobertura_pct = int(
                    (guardias_mes / slots_necesarios) * 100
                )
            else:
                cobertura_pct = 0

            color_cobertura = (
                "#27ae60"
                if cobertura_pct >= 80
                else "#f39c12" if cobertura_pct >= 50 else "#e74c3c"
            )
            tarjeta_cobertura = TarjetaEstadistica(
                "Cobertura del Mes",
                f"{cobertura_pct}%",
                "📊",
                color_cobertura,
            )
            self.tarjetas_container.addWidget(tarjeta_cobertura, 0, 3)

            # 5. Profesores sin guardias este mes
            profesores_con_guardias = (
                self.session.query(Guardia.profesor_id)
                .filter(
                    Guardia.fecha >= primer_dia_mes,
                    Guardia.fecha < primer_dia_siguiente,
                )
                .distinct()
                .count()
            )
            sin_guardias = total_profesores - profesores_con_guardias
            color_sin_guardias = "#e74c3c" if sin_guardias > 0 else "#27ae60"
            tarjeta_sin_guardias = TarjetaEstadistica(
                "Sin Guardias Asignadas",
                str(sin_guardias),
                "⚠️",
                color_sin_guardias,
            )
            self.tarjetas_container.addWidget(tarjeta_sin_guardias, 1, 0)

            # 6. Guardias hoy
            guardias_hoy = (
                self.session.query(Guardia)
                .filter(Guardia.fecha == hoy.date())
                .count()
            )
            tarjeta_hoy = TarjetaEstadistica(
                "Guardias Hoy",
                str(guardias_hoy),
                "📅",
                "#9b59b6",
            )
            self.tarjetas_container.addWidget(tarjeta_hoy, 1, 1)

            # 7. Turnos disponibles
            turnos = (
                self.session.query(Profesor.turno)
                .filter(Profesor.activo == True)  # noqa: E712
                .distinct()
                .count()
            )
            tarjeta_turnos = TarjetaEstadistica(
                "Turnos Activos",
                str(turnos),
                "⏰",
                "#34495e",
            )
            self.tarjetas_container.addWidget(tarjeta_turnos, 1, 2)

            # 8. Promedio guardias/profesor este mes
            if total_profesores > 0:
                promedio = guardias_mes / total_profesores
                promedio_str = f"{promedio:.1f}"
            else:
                promedio_str = "0.0"

            tarjeta_promedio = TarjetaEstadistica(
                "Promedio Guardias/Profesor",
                promedio_str,
                "📈",
                "#16a085",
            )
            self.tarjetas_container.addWidget(tarjeta_promedio, 1, 3)

        except Exception as e:
            print(f"Error cargando estadísticas: {e}")
        finally:
            if self.session:
                self.session.close()

    def _calcular_dias_laborables(
        self, fecha_inicio: datetime, fecha_fin: datetime
    ) -> int:
        """
        Calcula días laborables entre dos fechas.

        Args:
            fecha_inicio: Fecha de inicio
            fecha_fin: Fecha de fin

        Returns:
            Número de días laborables (L-V)
        """
        from datetime import timedelta

        dias = 0
        fecha_actual = fecha_inicio
        while fecha_actual < fecha_fin:
            if fecha_actual.weekday() < 5:  # L-V
                dias += 1
            fecha_actual += timedelta(days=1)
        return dias

    def showEvent(self, event):
        """Se ejecuta cuando el widget se muestra."""
        super().showEvent(event)
        self.cargar_estadisticas()
