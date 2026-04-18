"""
Celda individual del calendario de guardias.

Widget QGroupBox que muestra los datos de un día: guardias, ausencias,
sustituciones e indicadores visuales de zonas sin cobertura.
"""

from collections import defaultdict
from datetime import date
from typing import Dict, List, Tuple

from infrastructure.database.models import Ausencia, Guardia, Zona
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class CeldaDia(QGroupBox):
    """Celda individual para un día del calendario con scroll interno."""

    dia_clicked = pyqtSignal(date)  # Señal cuando se hace click en el día

    def __init__(
        self,
        fecha: date,
        guardias: List[Guardia],
        ausencias: List[Ausencia],
        sustituciones: List[Guardia],
        zonas_esperadas_por_recreo: Dict[Tuple[str, int], List[Zona]] = None,
        es_dia_lectivo: bool = True,
        es_hoy: bool = False,
    ):
        super().__init__()
        self.fecha = fecha
        self.guardias = guardias
        self.ausencias = ausencias
        self.sustituciones = sustituciones
        self.zonas_esperadas_por_recreo = zonas_esperadas_por_recreo or {}
        self.es_dia_lectivo = es_dia_lectivo
        self.es_hoy = es_hoy

        self.setup_ui()

    def setup_ui(self):
        """Construir interfaz de la celda."""
        layout_principal = QVBoxLayout()
        layout_principal.setContentsMargins(4, 4, 4, 4)
        layout_principal.setSpacing(2)

        # Encabezado con número del día e indicadores
        header_layout = QHBoxLayout()
        header_layout.setSpacing(4)

        # Número del día
        label_dia = QLabel(str(self.fecha.day))
        font_dia = QFont()
        font_dia.setBold(True)
        font_dia.setPointSize(11)
        label_dia.setFont(font_dia)
        header_layout.addWidget(label_dia)

        # Indicadores de estado
        indicadores = []
        if self.ausencias:
            indicadores.append(f"A:{len(self.ausencias)}")
        if self.sustituciones:
            indicadores.append(f"S:{len(self.sustituciones)}")

        if indicadores:
            label_indicadores = QLabel(" ".join(indicadores))
            label_indicadores.setStyleSheet("font-size: 9px; color: #666;")
            header_layout.addWidget(label_indicadores)

        header_layout.addStretch()
        layout_principal.addLayout(header_layout)

        # Separador
        separador = QFrame()
        separador.setFrameShape(QFrame.Shape.HLine)
        separador.setStyleSheet("background-color: #ccc; max-height: 1px;")
        layout_principal.addWidget(separador)

        # Área de scroll para guardias
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(600)

        # Contenedor de guardias
        guardias_widget = QWidget()
        guardias_layout = QVBoxLayout()
        guardias_layout.setContentsMargins(2, 2, 2, 2)
        guardias_layout.setSpacing(3)

        # Mostrar todas las guardias agrupadas por turno y recreo
        self._agregar_guardias_agrupadas(guardias_layout)

        # Mostrar ausencias si hay
        if self.ausencias:
            self._agregar_ausencias(guardias_layout)

        guardias_layout.addStretch()
        guardias_widget.setLayout(guardias_layout)
        scroll_area.setWidget(guardias_widget)

        layout_principal.addWidget(scroll_area, 1)

        # Contador total al final
        total_guardias = len(self.guardias)
        if total_guardias > 0:
            label_total = QLabel(f"Total: {total_guardias} guardias")
            label_total.setStyleSheet("font-size: 8px; color: #999; font-weight: bold;")
            label_total.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_principal.addWidget(label_total)

        self.setLayout(layout_principal)

        # Aplicar estilo según estado
        self._aplicar_estilo()

    def _agregar_guardias_agrupadas(self, layout: QVBoxLayout):
        """Agregar guardias agrupadas por turno y recreo, ordenadas por zona."""
        if not self.es_dia_lectivo:
            return

        grupos = defaultdict(list)
        for guardia in self.guardias:
            clave = (guardia.turno, guardia.recreo)
            grupos[clave].append(guardia)

        orden_turno = {"mañana": 0, "tarde": 1}
        claves_ordenadas = sorted(grupos.keys(), key=lambda x: (orden_turno.get(x[0], 2), x[1]))

        if self.zonas_esperadas_por_recreo:
            for clave in self.zonas_esperadas_por_recreo.keys():
                if clave not in claves_ordenadas:
                    claves_ordenadas.append(clave)
            claves_ordenadas = sorted(
                claves_ordenadas, key=lambda x: (orden_turno.get(x[0], 2), x[1])
            )

        for turno, recreo in claves_ordenadas:
            guardias_grupo = grupos.get((turno, recreo), [])

            guardias_ordenadas = sorted(
                guardias_grupo,
                key=lambda g: (
                    int(g.zona.nombre_zona[1])
                    if g.zona and g.zona.nombre_zona.startswith("Z")
                    else 999
                ),
            )

            icono_turno = "☀" if turno == "mañana" else "🌙"
            label_grupo = QLabel(f"{icono_turno} Recreo {recreo} ({turno})")
            label_grupo.setStyleSheet(
                "font-size: 9px; font-weight: bold; color: #1565C0; "
                "background-color: #E3F2FD; padding: 3px 5px; border-radius: 2px;"
            )
            layout.addWidget(label_grupo)

            zonas_con_guardia = {g.zona_id for g in guardias_ordenadas if g.zona_id}
            zonas_esperadas = self.zonas_esperadas_por_recreo.get((turno, recreo), [])
            zonas_faltantes = [z for z in zonas_esperadas if z.id not in zonas_con_guardia]

            for guardia in guardias_ordenadas:
                self._agregar_guardia_individual(layout, guardia)

            if self.es_dia_lectivo:
                for zona in zonas_faltantes:
                    self._agregar_zona_sin_guardia(layout, zona)

    def _agregar_guardia_individual(self, layout: QVBoxLayout, guardia: Guardia):
        """Agregar una guardia individual con mejor diseño."""
        profesor_nombre = guardia.profesor.nombre_completo if guardia.profesor else "Sin asignar"
        zona_nombre = guardia.zona.nombre_zona if guardia.zona else "??"
        nombre_mostrar = profesor_nombre
        es_sustitucion = guardia in self.sustituciones

        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(3, 2, 3, 2)
        h_layout.setSpacing(5)

        zona_label = QLabel(zona_nombre)
        zona_label.setStyleSheet("""
            background-color: #1976D2;
            color: white;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 2px;
            min-width: 18px;
        """)
        zona_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(zona_label)

        nombre_label = QLabel(nombre_mostrar)
        nombre_label.setStyleSheet("font-size: 8px; color: #333;")
        h_layout.addWidget(nombre_label, 1)

        if es_sustitucion:
            sust_label = QLabel("S")
            sust_label.setToolTip("Sustitución")
            sust_label.setStyleSheet("font-size: 8px;")
            h_layout.addWidget(sust_label)

        if es_sustitucion:
            widget.setStyleSheet("""
                QWidget {
                    background-color: #FFF3E0;
                    border-left: 3px solid #FF9800;
                    border-radius: 3px;
                    margin: 1px 0px;
                }
            """)
            widget.setToolTip(f"SUSTITUCIÓN: {profesor_nombre} en {zona_nombre}")
        else:
            widget.setStyleSheet("""
                QWidget {
                    background-color: white;
                    border-left: 2px solid #4CAF50;
                    border-radius: 2px;
                    margin: 1px 0px;
                }
            """)
            widget.setToolTip(f"{profesor_nombre} en {zona_nombre}")

        layout.addWidget(widget)

    def _agregar_zona_sin_guardia(self, layout: QVBoxLayout, zona: Zona):
        """Agregar un indicador visual de zona sin guardia asignada."""
        widget = QWidget()
        h_layout = QHBoxLayout(widget)
        h_layout.setContentsMargins(3, 2, 3, 2)
        h_layout.setSpacing(5)

        zona_label = QLabel(zona.nombre_zona)
        zona_label.setStyleSheet("""
            background-color: #D32F2F;
            color: white;
            font-size: 8px;
            font-weight: bold;
            padding: 2px 4px;
            border-radius: 2px;
            min-width: 18px;
        """)
        zona_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.addWidget(zona_label)

        texto_label = QLabel("SIN GUARDIA ASIGNADA")
        texto_label.setStyleSheet("font-size: 8px; color: #B71C1C; font-weight: bold;")
        h_layout.addWidget(texto_label, 1)

        widget.setStyleSheet("""
            QWidget {
                background-color: #FFEBEE;
                border-left: 3px solid #D32F2F;
                border-radius: 3px;
                margin: 1px 0px;
            }
        """)
        widget.setToolTip(f"ALERTA: La zona {zona.nombre_zona} no tiene guardia asignada")

        layout.addWidget(widget)

    def _agregar_ausencias(self, layout: QVBoxLayout):
        """Agregar información de ausencias."""
        label_titulo = QLabel("🏥 Ausencias:")
        label_titulo.setStyleSheet(
            "font-size: 9px; font-weight: bold; color: #C62828; "
            "background-color: #FFEBEE; padding: 2px; border-radius: 2px; margin-top: 4px;"
        )
        layout.addWidget(label_titulo)

        for ausencia in self.ausencias[:5]:
            profesor = ausencia.profesor.nombre_completo if ausencia.profesor else "Desconocido"
            if "," in profesor:
                apellido = profesor.split(",")[0].strip()
            else:
                partes = profesor.split()
                apellido = partes[-1] if partes else profesor

            motivo = ausencia.motivo[:15] if ausencia.motivo else "Sin motivo"
            texto = f"  • {apellido}: {motivo}"

            label = QLabel(texto)
            label.setStyleSheet(
                "font-size: 8px; padding: 1px 3px; margin-left: 5px; "
                "background-color: #FFCDD2; border-left: 2px solid #F44336; color: #B71C1C;"
            )
            label.setToolTip(f"Ausencia: {profesor} - {ausencia.motivo}")
            layout.addWidget(label)

        if len(self.ausencias) > 5:
            label_mas = QLabel(f"  ... y {len(self.ausencias) - 5} más")
            label_mas.setStyleSheet("font-size: 7px; color: #999; font-style: italic;")
            layout.addWidget(label_mas)

    def _aplicar_estilo(self):
        """Aplicar estilo CSS a la celda según su estado."""
        tiene_guardias = len(self.guardias) > 0
        tiene_ausencias = len(self.ausencias) > 0
        tiene_sustituciones = len(self.sustituciones) > 0

        if not self.es_dia_lectivo:
            estilo = """
                QGroupBox {
                    background-color: #F5F5F5;
                    border: 1px solid #BDBDBD;
                    border-radius: 6px;
                    opacity: 0.7;
                }
                QLabel {
                    color: #757575;
                }
            """
        elif self.es_hoy:
            estilo = """
                QGroupBox {
                    background-color: #FFF9C4;
                    border: 3px solid #FBC02D;
                    border-radius: 6px;
                }
            """
        elif tiene_sustituciones:
            estilo = """
                QGroupBox {
                    background-color: #FFF3E0;
                    border: 2px solid #FF9800;
                    border-radius: 6px;
                }
            """
        elif tiene_ausencias and tiene_guardias:
            estilo = """
                QGroupBox {
                    background-color: #FCE4EC;
                    border: 2px solid #E91E63;
                    border-radius: 6px;
                }
            """
        elif tiene_guardias:
            estilo = """
                QGroupBox {
                    background-color: #E3F2FD;
                    border: 1px solid #90CAF9;
                    border-radius: 6px;
                }
            """
        else:
            estilo = """
                QGroupBox {
                    background-color: #FAFAFA;
                    border: 1px solid #E0E0E0;
                    border-radius: 6px;
                }
            """

        self.setStyleSheet(estilo)

    def mousePressEvent(self, event):
        """Emitir señal cuando se hace click en el día."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dia_clicked.emit(self.fecha)
        super().mousePressEvent(event)
