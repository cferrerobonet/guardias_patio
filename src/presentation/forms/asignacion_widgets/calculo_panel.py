"""Widget combinado para estadísticas y cálculo de cuotas.

Integra estadísticas del curso y cuotas calculadas en un solo panel.
"""

from presentation.theme import legacy_styles as styles
from application.dtos.domain_services_dtos import CalcularCuotasRequest
from application.use_cases.calcular_cuotas_use_case import CalcularCuotasUseCase
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy.orm import Session
from presentation.theme.legacy_styles import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_value,
    format_terminal_warning,
    wrap_terminal_html,
)


class CalculoPanel(QGroupBox):
    """Panel combinado de estadísticas y cuotas."""

    cuotas_calculadas = pyqtSignal(dict)

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel combinado."""
        super().__init__("📊 Cálculo y Asignación", parent)
        self.session = session
        self.calcular_cuotas_uc = CalcularCuotasUseCase(session)
        self.configuracion_id = None
        self._ultima_response = None
        self._stats = None

        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #3b82f6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                left: 10px;
                top: -7px;
                background-color: white;
                color: #1e40af;
            }
        """)
        self._setup_ui()

    def _setup_ui(self):
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Botones en la parte superior
        button_layout = QHBoxLayout()

        self.calcular_button = QPushButton("🔢 Calcular Cuotas")
        self.calcular_button.setMinimumHeight(35)
        self.calcular_button.clicked.connect(self.calcular_cuotas)
        button_layout.addWidget(self.calcular_button)

        # Badge informativo de total (solo texto, no interactivo)
        self.total_badge = QLabel("Total: -- guardias")
        self.total_badge.setStyleSheet("""
            QLabel {
                background-color: #0f172a;
                color: #22c55e;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 20px;
                border-radius: 4px;
                border: 2px solid #22c55e;
            }
        """)
        self.total_badge.setMinimumHeight(35)
        button_layout.addWidget(self.total_badge)

        layout.addLayout(button_layout)

        # Área de texto con estilo terminal
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMinimumHeight(500)
        self.content_text.setObjectName("terminalRetro")
        self.content_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.content_text)
        self.setLayout(layout)
        self._mostrar_mensaje_inicial()

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial."""
        texto = format_terminal_info(
            "💡 Pulsa 'Calcular Cuotas' para ver las estadísticas\n"
            "   del curso y la distribución teórica de guardias.\n\n"
            "   La cuota se calcula en base a:\n"
            "   • Porcentaje de jornada\n"
            "   • Factor de tutoría"
        )
        self.content_text.setHtml(wrap_terminal_html(texto))

    def mostrar_estadisticas(self, stats):
        """Guarda las estadísticas para mostrarlas junto con las cuotas."""
        self._stats = stats
        self._mostrar_solo_estadisticas()

    def _mostrar_solo_estadisticas(self):
        """Muestra solo las estadísticas sin las cuotas."""
        if not self._stats:
            return

        stats = self._stats
        slots_teoricos = (
            stats.dias_lectivos
            * (stats.recreos_manana + stats.recreos_tarde)
            * stats.num_zonas
        )
        total_recreos = stats.recreos_manana + stats.recreos_tarde
        dias_info = f"{stats.dias_lectivos} días (L-V)"
        slots_info = f"{stats.slots_totales} guardias"
        calc_info = (
            f"{stats.dias_lectivos} × {total_recreos} × {stats.num_zonas}"
        )

        texto = f"""
{format_terminal_label("═" * 50)}
{format_terminal_label("  ESTADÍSTICAS DEL CURSO")}
{format_terminal_label("═" * 50)}

{format_terminal_label("Días lectivos:")} {format_terminal_value(dias_info)}
{format_terminal_label("Recreos mañana:")} {format_terminal_number(stats.recreos_manana)}
{format_terminal_label("Recreos tarde:")} {format_terminal_number(stats.recreos_tarde)}
{format_terminal_label("Total recreos/día:")} {format_terminal_number(total_recreos)}
{format_terminal_label("Número de zonas:")} {format_terminal_number(stats.num_zonas)}
{format_terminal_label("Número de profesores:")} {format_terminal_number(stats.num_profesores)}

{format_terminal_warning("🎯 SLOTS TOTALES:")} {format_terminal_value(slots_info)}
{format_terminal_label("   (Sin fechas: " + calc_info + ")")}
  • Slots teóricos: {format_terminal_number(slots_teoricos)}
  • Slots reales: {format_terminal_number(stats.slots_totales)}
"""

        if stats.slots_totales < slots_teoricos:
            reduccion = slots_teoricos - stats.slots_totales
            pct = (reduccion / slots_teoricos) * 100 if slots_teoricos > 0 else 0
            red_text = f"{reduccion} slots ({pct:.1f}%)"
            texto += f"  • Reducción: {format_terminal_warning(red_text)}\n"
            texto += f"\n{format_terminal_info('ℹ️  Hay zonas con fechas que reducen')}\n"
            texto += f"{format_terminal_info('   el total de slots disponibles.')}\n"

        texto += f"""
{format_terminal_label("─" * 50)}
{format_terminal_info("💡 Pulsa 'Calcular Cuotas' para ver la distribución")}
{format_terminal_info("   de guardias por profesor.")}
"""
        self.content_text.setHtml(wrap_terminal_html(texto))

    def set_configuracion(self, configuracion_id: int):
        """Establece la configuración para calcular cuotas."""
        self.configuracion_id = configuracion_id

    def calcular_cuotas(self):
        """Calcula y muestra las cuotas usando el Use Case."""
        if not self.configuracion_id:
            from application.app_services import AppServices
            from PyQt6.QtWidgets import QMessageBox
            from utils.ui_helpers import MESSAGEBOX_STYLE

            config_entity = AppServices(self.session).configuracion_repo.get_first()
            configuracion = config_entity

            if not configuracion:
                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Configuración")
                msg.setText(
                    "No hay una configuración para el sistema.\n\n"
                    "Debe configurar los parámetros en Ajustes."
                )
                msg.exec()
                return

            from services.gestor_cursos import GestorCursos

            curso_activo = GestorCursos.from_session(self.session).obtener_curso_activo()
            if not curso_activo:
                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Curso Activo")
                msg.setText("No hay un curso escolar activo.")
                msg.exec()
                return

            self.configuracion_id = configuracion.id

        try:
            self.calcular_button.setEnabled(False)
            self.calcular_button.setText("⏳ Calculando...")

            request = CalcularCuotasRequest(
                configuracion_id=self.configuracion_id, solo_activos=True
            )
            response = self.calcular_cuotas_uc.execute(request)

            if response.exitoso:
                self._ultima_response = response
                self._mostrar_contenido_completo(response)
                self.cuotas_calculadas.emit(response.cuotas)
            else:
                self._mostrar_error(response.mensaje)

        except (ValueError, TypeError, OSError) as e:
            self._mostrar_error(str(e))

        finally:
            self.calcular_button.setEnabled(True)
            self.calcular_button.setText("🔢 Calcular Cuotas")

    def _mostrar_contenido_completo(self, response):
        """Muestra estadísticas y cuotas combinadas."""
        self.total_badge.setText(f"Total: {response.total_guardias} guardias")

        texto = ""

        # Sección de estadísticas
        if self._stats:
            stats = self._stats
            slots_teoricos = (
                stats.dias_lectivos
                * (stats.recreos_manana + stats.recreos_tarde)
                * stats.num_zonas
            )
            total_recreos = stats.recreos_manana + stats.recreos_tarde
            dias_info = f"{stats.dias_lectivos} días (L-V)"
            slots_info = f"{stats.slots_totales} guardias"
            calc_info = (
                f"{stats.dias_lectivos} × {total_recreos} × {stats.num_zonas}"
            )

            texto += f"""
{format_terminal_label("═" * 50)}
{format_terminal_label("  ESTADÍSTICAS DEL CURSO")}
{format_terminal_label("═" * 50)}

{format_terminal_label("Días lectivos:")} {format_terminal_value(dias_info)}
{format_terminal_label("Recreos mañana:")} {format_terminal_number(stats.recreos_manana)}
{format_terminal_label("Recreos tarde:")} {format_terminal_number(stats.recreos_tarde)}
{format_terminal_label("Total recreos/día:")} {format_terminal_number(total_recreos)}
{format_terminal_label("Número de zonas:")} {format_terminal_number(stats.num_zonas)}
{format_terminal_label("Número de profesores:")} {format_terminal_number(stats.num_profesores)}

{format_terminal_warning("🎯 SLOTS TOTALES:")} {format_terminal_value(slots_info)}
{format_terminal_label("   (Sin fechas: " + calc_info + ")")}
  • Slots teóricos: {format_terminal_number(slots_teoricos)}
  • Slots reales: {format_terminal_number(stats.slots_totales)}
"""
            if stats.slots_totales < slots_teoricos:
                reduccion = slots_teoricos - stats.slots_totales
                pct = (reduccion / slots_teoricos) * 100 if slots_teoricos > 0 else 0
                red_text = f"{reduccion} slots ({pct:.1f}%)"
                texto += f"  • Reducción: {format_terminal_warning(red_text)}\n"

        # Sección de cuotas
        total_txt = str(response.total_guardias)
        texto += f"""

{format_terminal_label("═" * 50)}
{format_terminal_label("  DISTRIBUCIÓN OBJETIVO DE GUARDIAS")}
{format_terminal_label("═" * 50)}

{format_terminal_info("ℹ️  Esta distribución es el objetivo ideal basado en:")}
{format_terminal_info("   • Porcentaje de jornada de cada profesor")}
{format_terminal_info("   • Factor de tutoría (tutores = 0.5)")}

{format_terminal_label("Total guardias:")} {format_terminal_value(total_txt)}
{format_terminal_label("Profesores:")} {format_terminal_number(len(response.cuotas_detalle))}

{format_terminal_label("─" * 50)}
{format_terminal_label("📋 CUOTAS POR PROFESOR (ordenado por turno):")}
"""

        # Agrupar por turno y ordenar alfabéticamente dentro de cada grupo
        def normalizar_turno(turno: str) -> str:
            """Normaliza el nombre del turno."""
            t = (turno or "mixto").lower().strip()
            if t in ("mañana", "manana", "morning"):
                return "mañana"
            elif t in ("tarde", "afternoon"):
                return "tarde"
            else:
                return "mixto"

        # Separar en categorías
        turno_manana = []
        turno_tarde = []
        turno_mixto = []

        for cuota_dto in response.cuotas_detalle:
            turno = normalizar_turno(cuota_dto.turno)
            if turno == "mañana":
                turno_manana.append(cuota_dto)
            elif turno == "tarde":
                turno_tarde.append(cuota_dto)
            else:
                turno_mixto.append(cuota_dto)

        # Ordenar cada grupo alfabéticamente por nombre
        turno_manana.sort(key=lambda c: c.profesor_nombre)
        turno_tarde.sort(key=lambda c: c.profesor_nombre)
        turno_mixto.sort(key=lambda c: c.profesor_nombre)

        # Mostrar TURNO MAÑANA
        if turno_manana:
            texto += f"\n\n{format_terminal_success('☀️ TURNO MAÑANA')}"
            for cuota_dto in turno_manana:
                nombre = cuota_dto.profesor_nombre
                pct = cuota_dto.porcentaje_jornada
                cuota = cuota_dto.cuota_esperada
                cuota_str = format_terminal_value(str(cuota))
                nombre_fmt = format_terminal_profesor(nombre)
                texto += f"\n  • {nombre_fmt} ({pct:.0f}%): {cuota_str} guardias"

        # Mostrar TURNO TARDE
        if turno_tarde:
            texto += f"\n\n{format_terminal_success('🌙 TURNO TARDE')}"
            for cuota_dto in turno_tarde:
                nombre = cuota_dto.profesor_nombre
                pct = cuota_dto.porcentaje_jornada
                cuota = cuota_dto.cuota_esperada
                cuota_str = format_terminal_value(str(cuota))
                nombre_fmt = format_terminal_profesor(nombre)
                texto += f"\n  • {nombre_fmt} ({pct:.0f}%): {cuota_str} guardias"

        # Mostrar TURNO MIXTO
        if turno_mixto:
            texto += f"\n\n{format_terminal_success('🔄 TURNO MIXTO')}"
            for cuota_dto in turno_mixto:
                nombre = cuota_dto.profesor_nombre
                pct = cuota_dto.porcentaje_jornada
                cuota = cuota_dto.cuota_esperada
                cuota_str = format_terminal_value(str(cuota))
                nombre_fmt = format_terminal_profesor(nombre)
                texto += f"\n  • {nombre_fmt} ({pct:.0f}%): {cuota_str} guardias"

        texto += f"\n\n{format_terminal_success('✅ Cuotas calculadas correctamente')}"
        msg_generar = '💡 Ahora pulsa "Generar Asignación" para crear el calendario'
        texto += f"\n{format_terminal_info(msg_generar)}"
        texto += f"\n{format_terminal_info('   respetando estas cuotas.')}"

        self.content_text.setHtml(wrap_terminal_html(texto))

    def _mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error."""
        texto = format_terminal_error(f"❌ Error al calcular cuotas:\n   {mensaje}")
        self.content_text.setHtml(wrap_terminal_html(texto))

    def limpiar(self):
        """Limpia el contenido del panel."""
        self._ultima_response = None
        self._stats = None
        self.total_badge.setText("Total: -- guardias")
        self._mostrar_mensaje_inicial()

    def mostrar_error(self, mensaje: str):
        """Muestra un mensaje de error."""
        self._mostrar_error(mensaje)
