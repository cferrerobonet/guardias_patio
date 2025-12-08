"""Widget combinado para generación de guardias y resultados.

Combina:
- Botones de Generar y Limpiar guardias
- Resultados de generación con métricas de equidad
- Análisis de incidencias y recomendaciones
"""

import ui_styles as styles
from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from application.use_cases.asignacion_guardias import GenerarGuardiasUseCase
from application.use_cases.guardia import LimpiarGuardiasUseCase
from infrastructure.database.models import Guardia, Profesor, Zona
from infrastructure.repositories import SQLAlchemyGuardiaRepository
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QGroupBox, QHBoxLayout, QPushButton, QTextEdit, QVBoxLayout
from sqlalchemy.orm import Session
from ui_styles import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_warning,
    wrap_terminal_html,
)


class GeneracionPanel(QGroupBox):
    """Panel combinado para generación y resultados de guardias.

    Incluye:
    - Botón Generar Asignación
    - Botón Limpiar Guardias
    - Resultados de generación con métricas de equidad
    - Análisis de incidencias y recomendaciones

    Señales:
        guardias_generadas: Emitida cuando se generan guardias exitosamente.
        guardias_limpiadas: Emitida cuando se limpian las guardias.
    """

    guardias_generadas = pyqtSignal()
    guardias_limpiadas = pyqtSignal()

    def __init__(self, session: Session, sync_manager=None, parent=None):
        """Inicializa el panel de generación.

        Args:
            session: Sesión de SQLAlchemy.
            sync_manager: Gestor de sincronización con la nube.
            parent: Widget padre opcional.
        """
        super().__init__("🎯 Generación y Resultados", parent)
        self.session = session
        self.sync_manager = sync_manager
        self._ultimo_resumen = None

        # Use Cases
        self.generar_guardias_uc = GenerarGuardiasUseCase(session)
        guardia_repo = SQLAlchemyGuardiaRepository(session)
        self.limpiar_guardias_uc = LimpiarGuardiasUseCase(guardia_repo)
        self.analisis_equidad_uc = AnalisisEquidadUseCase(session)

        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #10b981;
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
                color: #059669;
            }
        """)
        self._setup_ui()
        self._mostrar_mensaje_inicial()

    def _setup_ui(self):
        """Configura la UI del panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Contenedor de botones
        button_container = QHBoxLayout()
        button_container.setContentsMargins(0, 0, 0, 4)
        button_container.setSpacing(10)

        # Botón Generar
        self.generar_button = QPushButton("🎯 Generar Asignación")
        self.generar_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.generar_button.setMinimumHeight(36)
        self.generar_button.clicked.connect(self._generar_guardias)
        button_container.addWidget(self.generar_button, 1)

        # Botón Limpiar
        self.limpiar_button = QPushButton("🗑️ Limpiar Guardias")
        self.limpiar_button.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.limpiar_button.setMinimumHeight(36)
        self.limpiar_button.clicked.connect(self._limpiar_guardias)
        button_container.addWidget(self.limpiar_button, 1)

        layout.addLayout(button_container)

        # Área de texto estilo terminal
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMinimumHeight(350)
        self.content_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.content_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.content_text)

        self.setLayout(layout)

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial."""
        texto = format_terminal_info(
            "💡 Los resultados se mostrarán aquí después de\n"
            "   generar el calendario de guardias.\n\n"
            "   Pulsa 'Generar Asignación' para comenzar."
        )
        self.content_text.setHtml(wrap_terminal_html(texto))

    def _generar_guardias(self):
        """Genera el calendario de guardias."""
        from PyQt6.QtWidgets import QMessageBox
        from utils.ui_helpers import show_question_with_cancel

        from presentation.widgets.progress_indicators import ejecutar_con_progreso

        try:
            count_guardias = self.session.query(Guardia).count()
            eliminar_existentes = True

            if count_guardias > 0:
                respuesta = show_question_with_cancel(
                    self,
                    "⚠️ Guardias Existentes",
                    f"Ya existen {count_guardias} guardias.\n\n"
                    f"¿Deseas ELIMINAR todas antes de generar nuevas?\n\n"
                    f"• SÍ: Eliminará todas y generará desde cero\n"
                    f"• NO: Agregará nuevas a las existentes",
                    default_button="Yes",
                )

                if respuesta == QMessageBox.StandardButton.Cancel:
                    return

                eliminar_existentes = respuesta == QMessageBox.StandardButton.Yes

            # Función para ejecutar con progreso
            def tarea_generacion(progress_callback):
                def adapted_callback(mensaje: str, porcentaje: int):
                    progress_callback(porcentaje, 100, mensaje)

                return self.generar_guardias_uc.execute(
                    eliminar_existentes=eliminar_existentes,
                    progress_callback=adapted_callback,
                )

            # Ejecutar con indicador de progreso
            resumen = ejecutar_con_progreso(
                self,
                tarea_generacion,
                titulo="Generando Guardias",
                mensaje="Preparando generación de calendario...",
            )

            if resumen:
                self._ultimo_resumen = resumen
                self._mostrar_resultados(resumen)
                self.guardias_generadas.emit()

                # Sincronizar si está disponible
                if self.sync_manager:
                    self._sincronizar()

        except Exception as e:
            self._mostrar_error(f"Error al generar: {e}")

    def _limpiar_guardias(self):
        """Limpia todas las guardias."""
        from PyQt6.QtWidgets import QMessageBox
        from utils.ui_helpers import MESSAGEBOX_STYLE

        count = self.session.query(Guardia).count()
        if count == 0:
            msg = QMessageBox(self)
            msg.setWindowTitle("Sin Guardias")
            msg.setText("No hay guardias para eliminar.")
            msg.setStyleSheet(MESSAGEBOX_STYLE)
            msg.exec()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("⚠️ Confirmar Eliminación")
        msg.setText(f"¿Eliminar las {count} guardias existentes?")
        msg.setInformativeText("Esta acción no se puede deshacer.")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        msg.setStyleSheet(MESSAGEBOX_STYLE)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.limpiar_guardias_uc.execute()
                self.session.commit()
                self._mostrar_mensaje_inicial()
                self._ultimo_resumen = None
                self.guardias_limpiadas.emit()

                if self.sync_manager:
                    self._sincronizar()

            except Exception as e:
                self._mostrar_error(f"Error al limpiar: {e}")

    def _sincronizar(self):
        """Sincroniza con la nube."""
        try:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.info("Sincronizando con la nube...")
            if self.sync_manager.sync_on_shutdown(session=self.session):
                logger.info("✓ Sincronizado correctamente")
        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"⚠ Error al sincronizar: {e}")

    def _mostrar_resultados(self, resumen):
        """Muestra resultados de generación con incidencias."""
        lineas = []

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 1: RESUMEN DE GENERACIÓN
        # ═══════════════════════════════════════════════════════════
        lineas.append(format_terminal_success("═" * 50))
        lineas.append(format_terminal_success("  📊 RESUMEN DE GENERACIÓN"))
        lineas.append(format_terminal_success("═" * 50))
        lineas.append("")

        guardias_label = format_terminal_label("Guardias generadas:")
        guardias_num = format_terminal_number(str(resumen.guardias_generadas))
        lineas.append(f"{guardias_label} {guardias_num}")

        slots_label = format_terminal_label("Slots esperados:")
        slots_num = format_terminal_number(str(resumen.slots_esperados))
        lineas.append(f"{slots_label} {slots_num}")

        # Cobertura
        cobertura_pct = (
            resumen.guardias_generadas / resumen.slots_esperados * 100
            if resumen.slots_esperados > 0
            else 0
        )
        if resumen.cobertura_completa:
            lineas.append(
                format_terminal_success(f"✅ Cobertura: {cobertura_pct:.1f}% (completa)")
            )
        elif resumen.slots_sin_cubrir > 0:
            lineas.append(
                format_terminal_warning(
                    f"⚠️ Cobertura: {cobertura_pct:.1f}% "
                    f"({resumen.slots_sin_cubrir} sin cubrir)"
                )
            )
        lineas.append("")

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 2: ANÁLISIS DE EQUIDAD
        # ═══════════════════════════════════════════════════════════
        lineas.append(format_terminal_info("─" * 50))
        lineas.append(format_terminal_success("⚖️ ANÁLISIS DE EQUIDAD"))
        lineas.append("")

        try:
            request = AnalisisEquidadRequest(
                configuracion_id=None,
                incluir_detalle=True,
                umbral_desbalance=0.15,
            )
            response = self.analisis_equidad_uc.execute(request)

            if response.exitoso:
                metricas = response.metricas
                nivel_emoji = {
                    "EXCELENTE": "🌟",
                    "BUENO": "✅",
                    "ACEPTABLE": "⚠️",
                    "DEFICIENTE": "❌",
                }
                emoji = nivel_emoji.get(metricas.nivel_equidad, "📊")
                is_good = metricas.nivel_equidad in ["EXCELENTE", "BUENO"]
                nivel_fmt = format_terminal_success if is_good else format_terminal_warning

                lineas.append(
                    f"{format_terminal_label('Nivel:')} "
                    f"{nivel_fmt(f'{emoji} {metricas.nivel_equidad}')}"
                )
                lineas.append(
                    f"{format_terminal_label('Índice de equidad:')} "
                    f"{format_terminal_number(f'{metricas.indice_equidad:.1%}')}"
                )
                lineas.append(
                    f"{format_terminal_label('Coef. variación:')} "
                    f"{format_terminal_number(f'{metricas.coeficiente_variacion:.3f}')}"
                )

                if metricas.desbalances_detectados > 0:
                    lineas.append(
                        format_terminal_warning(
                            f"⚠️ {metricas.desbalances_detectados} desbalances"
                        )
                    )
                else:
                    lineas.append(format_terminal_success("✅ Sin desbalances"))
            else:
                lineas.append(format_terminal_info("(equidad no disponible)"))
        except Exception:
            lineas.append(format_terminal_info("(equidad no disponible)"))

        lineas.append("")

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 3: DISTRIBUCIÓN POR PROFESOR (TODOS)
        # ═══════════════════════════════════════════════════════════
        if resumen.resumen_por_profesor:
            lineas.append(format_terminal_info("─" * 50))
            lineas.append(format_terminal_label("👥 DISTRIBUCIÓN DE GUARDIAS ASIGNADAS:"))
            lineas.append("")

            # Ordenar TODOS los profesores por guardias (descendente)
            todos_ordenados = sorted(
                resumen.resumen_por_profesor.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            for pid, cnt in todos_ordenados:
                prof = self.session.query(Profesor).get(pid)
                if prof:
                    pct = prof.porcentaje_jornada or 100
                    prof_name = format_terminal_profesor(prof.nombre_completo)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name} ({pct:.0f}%): {cnt_num} guardias")

        lineas.append("")

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 3.5: PROFESORES CON FECHAS ESPECIALES
        # ═══════════════════════════════════════════════════════════
        lineas.extend(self._formato_profesores_fechas_especiales(resumen))

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 4: INCIDENCIAS / SIN INCIDENCIAS
        # ═══════════════════════════════════════════════════════════
        lineas.append(format_terminal_info("─" * 50))

        if resumen.cobertura_completa:
            lineas.extend(self._formato_sin_incidencias())
        else:
            lineas.extend(self._formato_con_incidencias(resumen))

        self.content_text.setHtml(wrap_terminal_html("\n".join(lineas)))

    def _formato_sin_incidencias(self) -> list:
        """Formatea mensaje cuando no hay incidencias."""
        lineas = []
        lineas.append(format_terminal_success("✅ SIN INCIDENCIAS"))
        lineas.append("")
        lineas.append(format_terminal_info("La generación se completó exitosamente."))
        lineas.append(format_terminal_success("• Todos los slots fueron cubiertos"))
        lineas.append(format_terminal_success("• Distribución óptima alcanzada"))
        lineas.append("")
        lineas.append(format_terminal_info("💡 Recomendaciones:"))
        lineas.append(format_terminal_info('• Revisa el calendario en "Calendario"'))
        lineas.append(format_terminal_info("• Exporta los resultados si lo necesitas"))
        return lineas

    def _formato_con_incidencias(self, resumen) -> list:
        """Formatea análisis de incidencias."""
        lineas = []
        slots_sin = resumen.slots_sin_cubrir
        pct_sin = (
            (slots_sin / resumen.slots_esperados * 100)
            if resumen.slots_esperados > 0
            else 0
        )

        lineas.append(format_terminal_error("⚠️ INCIDENCIAS DETECTADAS"))
        lineas.append("")
        lineas.append(
            f"{format_terminal_label('Slots sin cubrir:')} "
            f"{format_terminal_warning(f'{slots_sin} ({pct_sin:.1f}%)')}"
        )
        lineas.append("")

        # Causas principales
        lineas.append(format_terminal_warning("🔍 POSIBLES CAUSAS:"))
        lineas.append(format_terminal_info("• Restricciones de horario muy estrictas"))
        lineas.append(format_terminal_info("• Fechas de inicio/fin limitadas"))
        lineas.append(format_terminal_info("• Turnos incompatibles"))
        lineas.append("")

        # Recursos
        num_zonas = self.session.query(Zona).count()
        num_prof = self.session.query(Profesor).count()
        lineas.append(format_terminal_label("📊 RECURSOS:"))
        lineas.append(
            f"  • {format_terminal_label('Profesores:')} "
            f"{format_terminal_number(num_prof)}"
        )
        lineas.append(
            f"  • {format_terminal_label('Zonas:')} "
            f"{format_terminal_number(num_zonas)}"
        )
        if num_zonas > 0:
            ratio = num_prof / num_zonas
            lineas.append(
                f"  • {format_terminal_label('Ratio:')} "
                f"{format_terminal_number(f'{ratio:.1f}')}"
            )
            if ratio < 3:
                lineas.append(format_terminal_warning("  ⚠️ Ratio bajo (mínimo 3:1)"))
        lineas.append("")

        # Recomendaciones
        lineas.append(format_terminal_success("💡 SOLUCIONES:"))
        lineas.append(format_terminal_info("• Revisar restricciones de profesores"))
        lineas.append(format_terminal_info("• Flexibilizar recreos permitidos"))
        lineas.append(format_terminal_info("• Verificar configuración de zonas"))
        return lineas

    def _formato_profesores_fechas_especiales(self, resumen) -> list:
        """
        Formatea reporte de profesores con fecha_inicio o fecha_fin de guardias.

        Analiza si se cumplieron las fechas límite y cuántas guardias
        se asignaron dentro/fuera del rango esperado.
        """
        lineas = []

        # Obtener profesores con fechas especiales
        profesores_fechas = (
            self.session.query(Profesor)
            .filter(
                Profesor.activo.is_(True),
                (Profesor.fecha_inicio_guardias.isnot(None))
                | (Profesor.fecha_fin_guardias.isnot(None)),
            )
            .all()
        )

        if not profesores_fechas:
            return lineas  # No hay profesores con fechas especiales

        lineas.append(format_terminal_info("─" * 50))
        lineas.append(format_terminal_label("📅 PROFESORES CON FECHAS ESPECIALES:"))
        lineas.append("")

        cumplidos = 0
        no_cumplidos = 0

        for prof in profesores_fechas:
            guardias_asignadas = resumen.resumen_por_profesor.get(prof.id, 0)

            # Obtener guardias del profesor para analizar fechas
            guardias_prof = (
                self.session.query(Guardia)
                .filter(Guardia.profesor_id == prof.id)
                .all()
            )

            fechas_guardias = [g.fecha for g in guardias_prof]
            fecha_min = min(fechas_guardias) if fechas_guardias else None
            fecha_max = max(fechas_guardias) if fechas_guardias else None

            # Analizar cumplimiento
            problemas = []
            cumple = True

            if prof.fecha_inicio_guardias:
                if fecha_min and fecha_min < prof.fecha_inicio_guardias:
                    guardias_antes = sum(
                        1 for f in fechas_guardias if f < prof.fecha_inicio_guardias
                    )
                    problemas.append(
                        f"⚠️ {guardias_antes} guardias antes del inicio "
                        f"({prof.fecha_inicio_guardias.strftime('%d/%m')})"
                    )
                    cumple = False

            if prof.fecha_fin_guardias:
                if fecha_max and fecha_max > prof.fecha_fin_guardias:
                    guardias_despues = sum(
                        1 for f in fechas_guardias if f > prof.fecha_fin_guardias
                    )
                    problemas.append(
                        f"⚠️ {guardias_despues} guardias después del fin "
                        f"({prof.fecha_fin_guardias.strftime('%d/%m')})"
                    )
                    cumple = False

            # Formatear línea del profesor
            prof_name = format_terminal_profesor(prof.nombre_completo)

            # Construir info de fechas
            fechas_info = []
            if prof.fecha_inicio_guardias:
                fechas_info.append(
                    f"Inicio: {prof.fecha_inicio_guardias.strftime('%d/%m/%Y')}"
                )
            if prof.fecha_fin_guardias:
                fechas_info.append(
                    f"Fin: {prof.fecha_fin_guardias.strftime('%d/%m/%Y')}"
                )

            if cumple:
                cumplidos += 1
                estado = format_terminal_success("✅")
                lineas.append(f"  {estado} {prof_name}")
                lineas.append(
                    f"      {format_terminal_info(' | '.join(fechas_info))}"
                )
                lineas.append(
                    f"      {format_terminal_number(str(guardias_asignadas))} "
                    f"guardias asignadas correctamente"
                )
            else:
                no_cumplidos += 1
                estado = format_terminal_warning("⚠️")
                lineas.append(f"  {estado} {prof_name}")
                lineas.append(
                    f"      {format_terminal_info(' | '.join(fechas_info))}"
                )
                for problema in problemas:
                    lineas.append(f"      {format_terminal_warning(problema)}")

            lineas.append("")

        # Resumen
        total = len(profesores_fechas)
        if no_cumplidos > 0:
            lineas.append(
                format_terminal_warning(
                    f"📊 Resumen: {cumplidos}/{total} cumplidos, "
                    f"{no_cumplidos} con problemas"
                )
            )
        else:
            lineas.append(
                format_terminal_success(
                    f"📊 Resumen: {total}/{total} fechas respetadas correctamente"
                )
            )

        lineas.append("")
        return lineas

    def _mostrar_error(self, mensaje: str):
        """Muestra mensaje de error."""
        texto = format_terminal_error(f"❌ {mensaje}")
        self.content_text.setHtml(wrap_terminal_html(texto))

    def limpiar(self):
        """Limpia el panel."""
        self._ultimo_resumen = None
        self._mostrar_mensaje_inicial()

    def cargar_datos(self):
        """Recarga datos cuando cambia el curso."""
        count = self.session.query(Guardia).count()
        if count == 0:
            self._mostrar_mensaje_inicial()
            self._ultimo_resumen = None
