"""
Vista de calendario mensual para visualizar las guardias asignadas.
Muestra un calendario interactivo con las guardias de cada día.
"""

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session

from models.models import Ausencia, Guardia, Profesor, Zona


class VistaCalendario(QWidget):
    """Widget para mostrar el calendario mensual de guardias."""

    def __init__(self, session: Session):
        super().__init__()
        self.session = session
        self.fecha_actual = datetime.now().date()
        self.mes_mostrado = self.fecha_actual.month
        self.anio_mostrado = self.fecha_actual.year
        self.init_ui()

    def init_ui(self):
        """Inicializa la interfaz de usuario."""
        layout_principal = QVBoxLayout()

        # Selector de mes/año
        selector_layout = QHBoxLayout()

        self.btn_mes_anterior = QPushButton("◀ Mes Anterior")
        self.btn_mes_anterior.clicked.connect(self.mes_anterior)

        self.label_mes_anio = QLabel()
        self.label_mes_anio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        self.label_mes_anio.setFont(font)

        self.btn_mes_siguiente = QPushButton("Mes Siguiente ▶")
        self.btn_mes_siguiente.clicked.connect(self.mes_siguiente)

        self.btn_hoy = QPushButton("📅 Hoy")
        self.btn_hoy.clicked.connect(self.ir_a_hoy)

        selector_layout.addWidget(self.btn_mes_anterior)
        selector_layout.addStretch()
        selector_layout.addWidget(self.label_mes_anio)
        selector_layout.addStretch()
        selector_layout.addWidget(self.btn_mes_siguiente)
        selector_layout.addWidget(self.btn_hoy)

        layout_principal.addLayout(selector_layout)

        # Área de calendario
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.calendario_widget = QWidget()
        self.calendario_layout = QGridLayout()
        self.calendario_widget.setLayout(self.calendario_layout)
        self.scroll_area.setWidget(self.calendario_widget)

        layout_principal.addWidget(self.scroll_area)

        # Leyenda
        leyenda_layout = QHBoxLayout()
        leyenda_label = QLabel("📋 Leyenda:")
        leyenda_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        leyenda_layout.addWidget(leyenda_label)

        leyenda_sin_guardias = QLabel("⬜ Sin guardias")
        leyenda_layout.addWidget(leyenda_sin_guardias)

        leyenda_con_guardias = QLabel("🟦 Con guardias")
        leyenda_layout.addWidget(leyenda_con_guardias)

        leyenda_hoy = QLabel("🟨 Hoy")
        leyenda_layout.addWidget(leyenda_hoy)

        leyenda_ausencias = QLabel("🏥 Con ausencias")
        leyenda_layout.addWidget(leyenda_ausencias)

        leyenda_layout.addStretch()
        layout_principal.addLayout(leyenda_layout)

        self.setLayout(layout_principal)
        self.actualizar_calendario()

    def actualizar_calendario(self):
        """Actualiza el calendario con las guardias del mes."""
        # Limpiar calendario anterior
        while self.calendario_layout.count():
            item = self.calendario_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Actualizar etiqueta de mes/año
        meses = [
            "",
            "Enero",
            "Febrero",
            "Marzo",
            "Abril",
            "Mayo",
            "Junio",
            "Julio",
            "Agosto",
            "Septiembre",
            "Octubre",
            "Noviembre",
            "Diciembre",
        ]
        self.label_mes_anio.setText(
            f"{meses[self.mes_mostrado]} {self.anio_mostrado}"
        )

        # Encabezados de días de la semana
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        for i, dia in enumerate(dias_semana):
            label = QLabel(dia)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setBold(True)
            label.setFont(font)
            label.setStyleSheet("background-color: #3498db; color: white; padding: 10px;")
            self.calendario_layout.addWidget(label, 0, i)

        # Cargar guardias del mes
        primer_dia = date(self.anio_mostrado, self.mes_mostrado, 1)
        dias_en_mes = monthrange(self.anio_mostrado, self.mes_mostrado)[1]
        ultimo_dia = date(self.anio_mostrado, self.mes_mostrado, dias_en_mes)

        guardias = (
            self.session.query(Guardia)
            .filter(Guardia.fecha >= primer_dia, Guardia.fecha <= ultimo_dia)
            .all()
        )

        # Agrupar guardias por fecha
        guardias_por_fecha = defaultdict(list)
        for g in guardias:
            guardias_por_fecha[g.fecha].append(g)

        # Cargar ausencias del mes
        ausencias = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.activa == True,  # noqa: E712
                Ausencia.fecha_inicio <= ultimo_dia,
                Ausencia.fecha_fin >= primer_dia,
            )
            .all()
        )

        # Agrupar ausencias por fecha (una ausencia puede abarcar múltiples días)
        ausencias_por_fecha = defaultdict(list)
        for ausencia in ausencias:
            # Iterar sobre cada día de la ausencia
            fecha_actual_ausencia = max(ausencia.fecha_inicio, primer_dia)
            fecha_fin_ausencia = min(ausencia.fecha_fin, ultimo_dia)

            from datetime import timedelta

            while fecha_actual_ausencia <= fecha_fin_ausencia:
                if fecha_actual_ausencia.month == self.mes_mostrado:
                    ausencias_por_fecha[fecha_actual_ausencia].append(ausencia)
                fecha_actual_ausencia = fecha_actual_ausencia + timedelta(days=1)

        # Día de la semana del primer día (0=Lunes, 6=Domingo)
        dia_semana_inicio = primer_dia.weekday()

        # Renderizar días del mes
        fila = 1
        columna = dia_semana_inicio

        for dia_num in range(1, dias_en_mes + 1):
            fecha_dia = date(self.anio_mostrado, self.mes_mostrado, dia_num)
            guardias_dia = guardias_por_fecha.get(fecha_dia, [])
            ausencias_dia = ausencias_por_fecha.get(fecha_dia, [])

            # Crear celda de día
            celda = self.crear_celda_dia(dia_num, guardias_dia, fecha_dia, ausencias_dia)
            self.calendario_layout.addWidget(celda, fila, columna)

            columna += 1
            if columna > 6:  # Nueva fila después del domingo
                columna = 0
                fila += 1

    def crear_celda_dia(
        self, dia_num: int, guardias: list, fecha: date, ausencias: list = None
    ) -> QGroupBox:
        """Crea una celda para un día del calendario."""
        if ausencias is None:
            ausencias = []

        celda = QGroupBox()
        layout = QVBoxLayout()

        # Número del día con icono de ausencia si aplica
        texto_dia = str(dia_num)
        if len(ausencias) > 0:
            texto_dia = f"{dia_num} 🏥"

        label_dia = QLabel(texto_dia)
        label_dia.setAlignment(Qt.AlignmentFlag.AlignRight)
        font_dia = QFont()
        font_dia.setBold(True)
        font_dia.setPointSize(12)
        label_dia.setFont(font_dia)
        layout.addWidget(label_dia)

        # Determinar color de fondo
        es_hoy = fecha == self.fecha_actual
        tiene_guardias = len(guardias) > 0
        tiene_ausencias = len(ausencias) > 0

        if es_hoy:
            celda.setStyleSheet(
                """
                QGroupBox {
                    background-color: #fff9c4;
                    border: 2px solid #fbc02d;
                    border-radius: 5px;
                    min-height: 100px;
                    min-width: 120px;
                }
                """
            )
        elif tiene_guardias:
            celda.setStyleSheet(
                """
                QGroupBox {
                    background-color: #e3f2fd;
                    border: 1px solid #90caf9;
                    border-radius: 5px;
                    min-height: 100px;
                    min-width: 120px;
                }
                """
            )
        else:
            celda.setStyleSheet(
                """
                QGroupBox {
                    background-color: #fafafa;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    min-height: 100px;
                    min-width: 120px;
                }
                """
            )

        # Mostrar guardias (máximo 3 para no saturar)
        guardias_mostradas = 0
        for guardia in guardias[:3]:
            profesor = self.session.query(Profesor).get(guardia.profesor_id)
            zona = self.session.query(Zona).get(guardia.zona_id)

            if profesor and zona:
                # Extraer solo apellido
                nombre_completo = profesor.nombre_completo
                if "," in nombre_completo:
                    apellido = nombre_completo.split(",")[0]
                else:
                    apellido = nombre_completo

                texto = f"🕐 {guardia.turno[:1].upper()} R{guardia.recreo}"
                label_guardia = QLabel(f"{texto}\n{apellido[:15]}")
                label_guardia.setStyleSheet(
                    "font-size: 9px; padding: 2px; background-color: white; "
                    "border-radius: 3px; margin: 2px;"
                )
                label_guardia.setWordWrap(True)
                layout.addWidget(label_guardia)
                guardias_mostradas += 1

        # Mostrar ausencias
        if tiene_ausencias:
            profesores_ausentes = set()
            for ausencia in ausencias:
                if ausencia.profesor:
                    profesores_ausentes.add(ausencia.profesor.nombre_completo)

            if len(profesores_ausentes) > 0:
                texto_ausencias = f"🏥 {len(profesores_ausentes)} ausente(s)"
                label_ausencias = QLabel(texto_ausencias)
                label_ausencias.setStyleSheet(
                    "font-size: 8px; padding: 2px; background-color: #ffebee; "
                    "border-radius: 3px; margin: 2px; color: #c62828;"
                )
                layout.addWidget(label_ausencias)

        # Si hay más guardias, mostrar contador
        if len(guardias) > 3:
            label_mas = QLabel(f"+ {len(guardias) - 3} más...")
            label_mas.setStyleSheet("font-size: 8px; color: #666; font-style: italic;")
            layout.addWidget(label_mas)

        layout.addStretch()
        celda.setLayout(layout)
        return celda

    def mes_anterior(self):
        """Navega al mes anterior."""
        if self.mes_mostrado == 1:
            self.mes_mostrado = 12
            self.anio_mostrado -= 1
        else:
            self.mes_mostrado -= 1
        self.actualizar_calendario()

    def mes_siguiente(self):
        """Navega al mes siguiente."""
        if self.mes_mostrado == 12:
            self.mes_mostrado = 1
            self.anio_mostrado += 1
        else:
            self.mes_mostrado += 1
        self.actualizar_calendario()

    def ir_a_hoy(self):
        """Vuelve al mes actual."""
        self.mes_mostrado = self.fecha_actual.month
        self.anio_mostrado = self.fecha_actual.year
        self.actualizar_calendario()

    def refrescar(self):
        """Refresca el calendario (útil después de generar guardias)."""
        self.actualizar_calendario()
