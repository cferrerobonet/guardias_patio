"""
Dashboard de Resumen General.

Muestra estadísticas clave y accesos rápidos.
"""

from datetime import datetime
from typing import Optional

from database.db_manager import SessionLocal
from models.models import Ausencia, Guardia, Profesor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session


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

        # Botones de acceso rápido
        btn_generar = BotonAccesoRapido("Generar Guardias", "🎲")
        btn_calendario = BotonAccesoRapido("Ver Calendario", "📅")
        btn_ausencias = BotonAccesoRapido("Gestionar Ausencias", "🏥")
        btn_profesores = BotonAccesoRapido("Gestionar Profesores", "👥")
        btn_exportar = BotonAccesoRapido("Exportar PDFs", "📄")
        btn_reportes = BotonAccesoRapido("Generar Reportes", "📊")

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
