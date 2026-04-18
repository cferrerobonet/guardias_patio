"""Widget para mostrar cuotas calculadas con estilo terminal.

Integra CalcularCuotasUseCase para preview de distribución esperada.
Usa estilo terminal negro consistente con otros widgets.
"""

import ui_styles as styles
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
from ui_styles import (
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


class CuotasPanel(QGroupBox):
    """Panel para calcular y mostrar cuotas esperadas con estilo terminal.

    Muestra:
    - Total de guardias a distribuir
    - Distribución por profesor ordenada por cuota
    - Porcentaje de jornada y turno de cada profesor
    - Estado de la distribución (exacta o con diferencia)

    Señales:
        cuotas_calculadas: Emitida cuando se calculan cuotas exitosamente.
    """

    cuotas_calculadas = pyqtSignal(dict)  # Emite {profesor_id: cuota}

    def __init__(self, session: Session, parent=None):
        """Inicializa el panel de cuotas.

        Args:
            session: Sesión de SQLAlchemy para consultas.
            parent: Widget padre opcional.
        """
        super().__init__("📐 Cuotas Calculadas (Domain Services)", parent)
        self.session = session
        self.calcular_cuotas_uc = CalcularCuotasUseCase(session)
        self.configuracion_id = None
        self._ultima_response = None

        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #f59e0b;
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
                color: #d97706;
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
        self.calcular_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.calcular_button.setMinimumHeight(35)
        self.calcular_button.clicked.connect(self.calcular_cuotas)
        button_layout.addWidget(self.calcular_button)

        # Badge informativo de total (solo lectura, no interactivo)
        self.total_badge = QLabel("Total: -- guardias")
        self.total_badge.setStyleSheet("""
            QLabel {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                font-size: 14px;
                padding: 8px 20px;
                border-radius: 6px;
                border: none;
            }
        """)
        self.total_badge.setMinimumHeight(35)
        button_layout.addWidget(self.total_badge)

        layout.addLayout(button_layout)

        # Área de texto con estilo terminal (igual que otros widgets)
        self.cuotas_text = QTextEdit()
        self.cuotas_text.setReadOnly(True)
        self.cuotas_text.setMinimumHeight(380)  # Altura similar al panel izquierdo
        self.cuotas_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.cuotas_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)

        layout.addWidget(self.cuotas_text)
        self.setLayout(layout)

        # Mensaje inicial
        self._mostrar_mensaje_inicial()

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial."""
        texto = format_terminal_info(
            "💡 Pulsa 'Calcular Cuotas' para ver la distribución\n"
            "   teórica de guardias por profesor.\n\n"
            "   La cuota se calcula en base a:\n"
            "   • Porcentaje de jornada\n"
            "   • Turno (mañana/tarde/ambos)\n"
            "   • Días/recreos disponibles"
        )
        self.cuotas_text.setHtml(wrap_terminal_html(texto))

    def set_configuracion(self, configuracion_id: int):
        """Establece la configuración para calcular cuotas.

        Args:
            configuracion_id: ID de la configuración activa.
        """
        self.configuracion_id = configuracion_id

    def calcular_cuotas(self):
        """Calcula y muestra las cuotas usando el Use Case."""
        # Obtener configuración activa
        if not self.configuracion_id:
            from application.app_services import AppServices

            config_entity = AppServices(self.session).configuracion_repo.get_first()
            configuracion = config_entity

            if not configuracion:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import MESSAGEBOX_STYLE

                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Configuración")
                msg.setText(
                    "No hay una configuración para el sistema.\n\n"
                    "Debe configurar los parámetros en Ajustes del Curso Escolar."
                )
                msg.setStyleSheet(MESSAGEBOX_STYLE)
                msg.exec()
                return

            # Verificar curso activo
            from services.gestor_cursos import GestorCursos

            curso_activo = GestorCursos.obtener_curso_activo(self.session)
            if not curso_activo:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import MESSAGEBOX_STYLE

                msg = QMessageBox(self)
                msg.setWindowTitle("Sin Curso Activo")
                msg.setText("No hay un curso escolar activo.\n\nDebe activar un curso en Ajustes.")
                msg.setStyleSheet(MESSAGEBOX_STYLE)
                msg.exec()
                return

            self.configuracion_id = configuracion.id

        try:
            # Deshabilitar botón
            self.calcular_button.setEnabled(False)
            self.calcular_button.setText("⏳ Calculando...")

            # Ejecutar Use Case
            request = CalcularCuotasRequest(
                configuracion_id=self.configuracion_id, solo_activos=True
            )
            response = self.calcular_cuotas_uc.execute(request)

            if response.exitoso:
                self._ultima_response = response
                self._mostrar_cuotas(response)
                # Emitir señal con el diccionario de cuotas
                cuotas_dict = {c.profesor_id: c.cuota_esperada for c in response.cuotas_detalle}
                self.cuotas_calculadas.emit(cuotas_dict)
            else:
                self._mostrar_error_terminal(response.mensaje)

        except Exception as e:
            self._mostrar_error_terminal(f"Error al calcular cuotas: {str(e)}")
        finally:
            # Rehabilitar botón
            self.calcular_button.setEnabled(True)
            self.calcular_button.setText("🔢 Calcular Cuotas")

    def _mostrar_cuotas(self, response):
        """Muestra las cuotas en formato terminal.

        Args:
            response: CalcularCuotasResponse con cuotas detalladas.
        """
        # Actualizar badge de total
        self.total_badge.setText(f"Total: {response.total_guardias} guardias")

        # Construir texto formateado
        lineas = []

        # Cabecera
        lineas.append(format_terminal_success("�� DISTRIBUCIÓN OBJETIVO DE GUARDIAS"))
        lineas.append("")

        # Información contextual
        lineas.append(
            format_terminal_info("ℹ️  Esta distribución es el objetivo ideal basado en:")
        )
        lineas.append(format_terminal_info("   • Porcentaje de jornada de cada profesor"))
        lineas.append(format_terminal_info("   • Turno (mañana/tarde/ambos)"))
        lineas.append(format_terminal_info("   • Slots totales disponibles"))
        lineas.append("")

        # Resumen rápido
        total_label = format_terminal_label("Total guardias a distribuir:")
        total_val = format_terminal_number(str(response.total_guardias))
        lineas.append(f"{total_label} {total_val}")

        profesores_label = format_terminal_label("Profesores activos:")
        profesores_val = format_terminal_number(str(len(response.cuotas_detalle)))
        lineas.append(f"{profesores_label} {profesores_val}")
        lineas.append("")

        # Separador
        lineas.append(format_terminal_info("─" * 50))
        lineas.append(format_terminal_label("📋 CUOTAS POR PROFESOR (ordenado por turno):"))
        lineas.append(format_terminal_info("─" * 50))
        lineas.append("")

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
            lineas.append(format_terminal_success("☀️ TURNO MAÑANA"))
            lineas.append("")
            for cuota_dto in turno_manana:
                nombre = format_terminal_profesor(cuota_dto.profesor_nombre)
                jornada = f"{cuota_dto.porcentaje_jornada:.0f}%"
                cuota = format_terminal_number(str(cuota_dto.cuota_esperada))
                turno_info = format_terminal_info(f"({jornada})")
                lineas.append(f"  • {nombre} {turno_info}: {cuota} guardias")
            lineas.append("")

        # Mostrar TURNO TARDE
        if turno_tarde:
            lineas.append(format_terminal_success("🌙 TURNO TARDE"))
            lineas.append("")
            for cuota_dto in turno_tarde:
                nombre = format_terminal_profesor(cuota_dto.profesor_nombre)
                jornada = f"{cuota_dto.porcentaje_jornada:.0f}%"
                cuota = format_terminal_number(str(cuota_dto.cuota_esperada))
                turno_info = format_terminal_info(f"({jornada})")
                lineas.append(f"  • {nombre} {turno_info}: {cuota} guardias")
            lineas.append("")

        # Mostrar TURNO MIXTO
        if turno_mixto:
            lineas.append(format_terminal_success("🔄 TURNO MIXTO"))
            lineas.append("")
            for cuota_dto in turno_mixto:
                nombre = format_terminal_profesor(cuota_dto.profesor_nombre)
                jornada = f"{cuota_dto.porcentaje_jornada:.0f}%"
                cuota = format_terminal_number(str(cuota_dto.cuota_esperada))
                turno_info = format_terminal_info(f"({jornada})")
                lineas.append(f"  • {nombre} {turno_info}: {cuota} guardias")

        lineas.append("")

        # Verificar si hay diferencia
        if hasattr(response, "slots_totales") and response.slots_totales:
            diferencia = response.total_guardias - response.slots_totales
            if diferencia == 0:
                lineas.append(format_terminal_success("✅ La distribución es EXACTA"))
            else:
                dif_msg = f"⚠️  Diferencia: {abs(diferencia)} guardias"
                lineas.append(format_terminal_warning(dif_msg))
        else:
            lineas.append(format_terminal_success("✅ Cuotas calculadas correctamente"))

        lineas.append("")
        lineas.append(
            format_terminal_info('💡 Tras generar, verifica el reparto real en "Resultados"')
        )

        texto = "\n".join(lineas)
        self.cuotas_text.setHtml(wrap_terminal_html(texto))

    def _mostrar_error_terminal(self, mensaje: str):
        """Muestra mensaje de error en formato terminal."""
        error_html = wrap_terminal_html(format_terminal_error(f"⚠️  {mensaje}"))
        self.cuotas_text.setHtml(error_html)
        self.total_badge.setText("Total: -- guardias")

    def limpiar(self):
        """Limpia el contenido del panel."""
        self._mostrar_mensaje_inicial()
        self.total_badge.setText("Total: -- guardias")
        self._ultima_response = None

    def actualizar_estado_asignacion(self, cuotas_asignadas: dict):
        """Actualiza el estado después de asignar guardias.

        Compara cuotas esperadas con asignadas y muestra diferencias.

        Args:
            cuotas_asignadas: Diccionario {profesor_id: guardias_asignadas}
        """
        if not self._ultima_response:
            return

        lineas = []
        lineas.append(format_terminal_success("📊 RESULTADO DE ASIGNACIÓN"))
        lineas.append("")

        total_asignadas = sum(cuotas_asignadas.values())
        lineas.append(
            f"{format_terminal_label('Guardias asignadas:')} "
            f"{format_terminal_number(str(total_asignadas))}"
        )
        lineas.append("")

        # Comparar cada profesor
        for cuota_dto in self._ultima_response.cuotas_detalle:
            nombre = format_terminal_profesor(cuota_dto.profesor_nombre)
            esperada = cuota_dto.cuota_esperada
            asignada = cuotas_asignadas.get(cuota_dto.profesor_id, 0)
            diferencia = asignada - esperada

            if diferencia == 0:
                estado = format_terminal_success("✅")
            elif diferencia > 0:
                estado = format_terminal_warning(f"+{diferencia}")
            else:
                estado = format_terminal_error(f"{diferencia}")

            lineas.append(
                f"  • {nombre}: {format_terminal_value(str(asignada))}/{esperada} {estado}"
            )

        texto = "\n".join(lineas)
        self.cuotas_text.setHtml(wrap_terminal_html(texto))
