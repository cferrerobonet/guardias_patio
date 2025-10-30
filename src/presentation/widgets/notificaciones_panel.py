"""
Panel de Notificaciones y Alertas.

Detecta y muestra problemas que requieren atención.
"""

from datetime import datetime
from typing import Optional

from database.db_manager import SessionLocal
from models.models import Ausencia, Guardia, Profesor
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import and_
from sqlalchemy.orm import Session


class Notificacion:
    """Representa una notificación/alerta."""

    def __init__(
        self,
        tipo: str,
        titulo: str,
        descripcion: str,
        severidad: str = "info",
        accion: Optional[str] = None,
    ):
        """
        Inicializa notificación.

        Args:
            tipo: Tipo de notificación (profesor_sin_guardias, etc.)
            titulo: Título breve
            descripcion: Descripción detallada
            severidad: Nivel (info, warning, error)
            accion: Texto de acción opcional
        """
        self.tipo = tipo
        self.titulo = titulo
        self.descripcion = descripcion
        self.severidad = severidad
        self.accion = accion
        self.timestamp = datetime.now()


class ItemNotificacion(QFrame):
    """Widget para mostrar una notificación individual."""

    accion_clicked = pyqtSignal(str)  # Emite el tipo de notificación

    def __init__(
        self,
        notificacion: Notificacion,
        parent: Optional[QWidget] = None,
    ):
        """
        Inicializa item de notificación.

        Args:
            notificacion: Objeto notificación
            parent: Widget padre
        """
        super().__init__(parent)
        self.notificacion = notificacion
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa interfaz de usuario."""
        self.setFrameShape(QFrame.Shape.StyledPanel)

        # Color según severidad
        colores = {
            "info": "#3498db",
            "warning": "#f39c12",
            "error": "#e74c3c",
        }
        color = colores.get(self.notificacion.severidad, "#95a5a6")

        self.setStyleSheet(
            f"""
            ItemNotificacion {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 4px;
                padding: 12px;
                margin: 4px 0px;
            }}
            ItemNotificacion:hover {{
                background-color: #f8f9fa;
            }}
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(6)

        # Título con icono
        iconos = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
        }
        icono = iconos.get(self.notificacion.severidad, "📌")

        titulo_layout = QHBoxLayout()
        titulo_label = QLabel(f"{icono} {self.notificacion.titulo}")
        titulo_label.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #2c3e50;"
        )
        titulo_layout.addWidget(titulo_label)
        titulo_layout.addStretch()

        # Timestamp
        tiempo_label = QLabel(
            self.notificacion.timestamp.strftime("%H:%M")
        )
        tiempo_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        titulo_layout.addWidget(tiempo_label)

        layout.addLayout(titulo_layout)

        # Descripción
        desc_label = QLabel(self.notificacion.descripcion)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 12px; color: #34495e;")
        layout.addWidget(desc_label)

        # Botón de acción (opcional)
        if self.notificacion.accion:
            btn_accion = QPushButton(self.notificacion.accion)
            btn_accion.setStyleSheet(
                """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
            """
            )
            btn_accion.clicked.connect(
                lambda: self.accion_clicked.emit(self.notificacion.tipo)
            )
            layout.addWidget(btn_accion, alignment=Qt.AlignmentFlag.AlignLeft)


class NotificacionesPanel(QWidget):
    """Panel principal de notificaciones."""

    accion_notificacion = pyqtSignal(str)  # Emite tipo de notificación

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Inicializa panel de notificaciones.

        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self.session: Optional[Session] = None
        self.notificaciones: list[Notificacion] = []
        self._init_ui()

    def _init_ui(self) -> None:
        """Inicializa interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera
        header = QFrame()
        header.setStyleSheet(
            """
            QFrame {
                background-color: #2c3e50;
                padding: 16px;
            }
        """
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        titulo = QLabel("🔔 Notificaciones y Alertas")
        titulo.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: white;"
        )
        header_layout.addWidget(titulo)

        # Contador
        self.contador_label = QLabel("0")
        self.contador_label.setStyleSheet(
            """
            QLabel {
                background-color: #e74c3c;
                color: white;
                border-radius: 10px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """
        )
        header_layout.addWidget(self.contador_label)

        # Botón actualizar
        btn_actualizar = QPushButton("🔄 Actualizar")
        btn_actualizar.setStyleSheet(
            """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """
        )
        btn_actualizar.clicked.connect(self.detectar_notificaciones)
        header_layout.addWidget(btn_actualizar)

        layout.addWidget(header)

        # Área de scroll para notificaciones
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: #ecf0f1;
            }
        """
        )

        # Contenedor de notificaciones
        self.notificaciones_widget = QWidget()
        self.notificaciones_layout = QVBoxLayout(self.notificaciones_widget)
        self.notificaciones_layout.setContentsMargins(16, 16, 16, 16)
        self.notificaciones_layout.setSpacing(8)
        self.notificaciones_layout.addStretch()

        scroll.setWidget(self.notificaciones_widget)
        layout.addWidget(scroll)

    def detectar_notificaciones(self) -> None:
        """Detecta y genera notificaciones automáticamente."""
        self.notificaciones.clear()

        try:
            self.session = SessionLocal()
            hoy = datetime.now()

            # Obtener mes actual
            primer_dia_mes = datetime(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                primer_dia_siguiente = datetime(hoy.year + 1, 1, 1)
            else:
                primer_dia_siguiente = datetime(
                    hoy.year, hoy.month + 1, 1
                )

            # 1. Profesores sin guardias este mes
            profesores_activos = (
                self.session.query(Profesor)
                .filter(Profesor.activo == True)  # noqa: E712
                .all()
            )

            profesores_con_guardias_ids = (
                self.session.query(Guardia.profesor_id)
                .filter(
                    Guardia.fecha >= primer_dia_mes.date(),
                    Guardia.fecha < primer_dia_siguiente.date(),
                )
                .distinct()
                .all()
            )
            ids_con_guardias = {pid[0] for pid in profesores_con_guardias_ids}

            for profesor in profesores_activos:
                if profesor.id not in ids_con_guardias:
                    self.notificaciones.append(
                        Notificacion(
                            tipo="profesor_sin_guardias",
                            titulo=(
                                f"Profesor sin guardias: "
                                f"{profesor.nombre_completo}"
                            ),
                            descripcion=(
                                f"{profesor.nombre_completo} "
                                f"({profesor.turno}) no tiene guardias "
                                f"asignadas este mes."
                            ),
                            severidad="warning",
                            accion="Ver Profesor",
                        )
                    )

            # 2. Profesores con exceso de carga (>150% de su cuota)
            for profesor in profesores_activos:
                guardias_asignadas = (
                    self.session.query(Guardia)
                    .filter(
                        Guardia.profesor_id == profesor.id,
                        Guardia.fecha >= primer_dia_mes.date(),
                        Guardia.fecha < primer_dia_siguiente.date(),
                    )
                    .count()
                )

                # Asumiendo cuota ideal de ~20 guardias/mes
                cuota_ideal = 20
                if guardias_asignadas > cuota_ideal * 1.5:
                    self.notificaciones.append(
                        Notificacion(
                            tipo="exceso_carga",
                            titulo=(
                                f"Exceso de carga: "
                                f"{profesor.nombre_completo}"
                            ),
                            descripcion=(
                                f"{profesor.nombre_completo} tiene "
                                f"{guardias_asignadas} guardias este mes "
                                f"(+{int((guardias_asignadas/cuota_ideal-1)*100)}% "
                                f"sobre lo ideal)."
                            ),
                            severidad="error",
                            accion="Ver Calendario",
                        )
                    )

            # 3. Ausencias activas hoy
            ausencias_hoy = (
                self.session.query(Ausencia)
                .join(Profesor)
                .filter(
                    and_(
                        Ausencia.fecha_inicio <= hoy.date(),
                        Ausencia.fecha_fin >= hoy.date(),
                    )
                )
                .all()
            )

            if ausencias_hoy:
                nombres = ", ".join(
                    a.profesor.nombre_completo for a in ausencias_hoy
                )
                self.notificaciones.append(
                    Notificacion(
                        tipo="ausencias_activas",
                        titulo=f"Ausencias activas hoy: {len(ausencias_hoy)}",
                        descripcion=f"Profesores ausentes: {nombres}",
                        severidad="info",
                        accion="Ver Ausencias",
                    )
                )

            # 4. Guardias sin asignar hoy (si existen slots vacíos)
            # Esto requeriría conocer la estructura de slots esperados
            # Por ahora, solo contamos guardias asignadas
            guardias_hoy = (
                self.session.query(Guardia)
                .filter(Guardia.fecha == hoy.date())
                .count()
            )

            # Asumiendo 5 recreos por día
            slots_esperados = 5
            if guardias_hoy < slots_esperados:
                self.notificaciones.append(
                    Notificacion(
                        tipo="slots_sin_cubrir",
                        titulo="Guardias sin asignar hoy",
                        descripcion=(
                            f"Solo {guardias_hoy}/{slots_esperados} "
                            f"guardias asignadas para hoy."
                        ),
                        severidad="error",
                        accion="Generar Guardias",
                    )
                )

            # 5. Baja cobertura del mes
            total_guardias_mes = (
                self.session.query(Guardia)
                .filter(
                    Guardia.fecha >= primer_dia_mes.date(),
                    Guardia.fecha < primer_dia_siguiente.date(),
                )
                .count()
            )

            # Estimar días laborables y slots necesarios
            dias_laborables = self._calcular_dias_laborables(
                primer_dia_mes, primer_dia_siguiente
            )
            slots_necesarios = dias_laborables * 5

            if slots_necesarios > 0:
                cobertura = (total_guardias_mes / slots_necesarios) * 100
                if cobertura < 50:
                    self.notificaciones.append(
                        Notificacion(
                            tipo="baja_cobertura",
                            titulo="Cobertura baja este mes",
                            descripcion=(
                                f"Solo el {int(cobertura)}% de las guardias "
                                f"están asignadas este mes."
                            ),
                            severidad="warning",
                            accion="Generar Guardias",
                        )
                    )

        except Exception as e:
            print(f"Error detectando notificaciones: {e}")
        finally:
            if self.session:
                self.session.close()

        # Mostrar notificaciones
        self._mostrar_notificaciones()

    def _mostrar_notificaciones(self) -> None:
        """Muestra notificaciones en el panel."""
        # Limpiar layout
        while self.notificaciones_layout.count() > 1:
            item = self.notificaciones_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Actualizar contador
        self.contador_label.setText(str(len(self.notificaciones)))

        if not self.notificaciones:
            # Mostrar mensaje de "sin notificaciones"
            mensaje = QLabel(
                "✅ No hay alertas en este momento.\n\n"
                "Todo está funcionando correctamente."
            )
            mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
            mensaje.setStyleSheet(
                "font-size: 14px; color: #7f8c8d; padding: 40px;"
            )
            self.notificaciones_layout.insertWidget(0, mensaje)
        else:
            # Añadir items de notificaciones
            for notif in self.notificaciones:
                item = ItemNotificacion(notif)
                item.accion_clicked.connect(self.accion_notificacion.emit)
                self.notificaciones_layout.insertWidget(
                    self.notificaciones_layout.count() - 1, item
                )

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

    def obtener_numero_notificaciones(self) -> int:
        """
        Retorna el número actual de notificaciones.

        Returns:
            Número de notificaciones activas
        """
        return len(self.notificaciones)

    def showEvent(self, event):
        """Se ejecuta cuando el widget se muestra."""
        super().showEvent(event)
        self.detectar_notificaciones()
