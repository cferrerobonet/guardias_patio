"""
Formulario de asignación de guardias.

Permite calcular distribución y generar el calendario completo de guardias.
"""

import ui_styles as styles
from application.use_cases.asignacion_guardias import (
    CalcularDistribucionUseCase,
    GenerarGuardiasUseCase,
    ObtenerEstadisticasUseCase,
)
from application.use_cases.guardia import LimpiarGuardiasUseCase
from infrastructure.repositories import SQLAlchemyGuardiaRepository
from models.models import Guardia, Profesor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
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
from utils.exceptions import BusinessLogicError

from presentation.forms.base_form import BaseForm
from presentation.widgets.progress_indicators import ejecutar_con_progreso


class AsignacionGuardiasForm(BaseForm):
    """
    Formulario para calcular y asignar guardias.

    Permite:
    - Ver estadísticas del curso
    - Calcular distribución de guardias por profesor
    - Generar el calendario completo de guardias
    """

    def __init__(self, session: Session, sync_manager=None):
        """
        Inicializar el formulario de asignación de guardias.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
            sync_manager: Gestor de sincronización con la nube (opcional)
        """
        super().__init__(session)

        # Guardar sync_manager
        self.sync_manager = sync_manager

        # Inicializar Use Cases
        self.obtener_estadisticas_uc = ObtenerEstadisticasUseCase(session)
        self.calcular_distribucion_uc = CalcularDistribucionUseCase(session)
        self.generar_guardias_uc = GenerarGuardiasUseCase(session)

        # Repositorio para limpiar guardias
        guardia_repo = SQLAlchemyGuardiaRepository(session)
        self.limpiar_guardias_uc = LimpiarGuardiasUseCase(guardia_repo)

        self.setWindowTitle("Asignación de Guardias")
        self.setup_ui()
        self.cargar_estadisticas()

    def setup_ui(self):
        """Configurar la interfaz de usuario del formulario"""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)

        # Título principal
        titulo = QLabel("🎯 ASIGNACIÓN DE GUARDIAS")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        main_layout.addWidget(titulo)

        # Crear el contenedor con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor del contenido
        content_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(6)
        grid_layout.setVerticalSpacing(8)
        grid_layout.setContentsMargins(6, 4, 6, 4)
        content_widget.setLayout(grid_layout)

        # ============ COLUMNA IZQUIERDA ============

        # Estadísticas del curso
        label_stats = QLabel("📊 Estadísticas del Curso")
        label_stats.setStyleSheet(styles.STYLE_TITLE_SECTION)
        label_stats.setMaximumHeight(20)
        grid_layout.addWidget(label_stats, 0, 0)

        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMinimumHeight(280)
        self.stats_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.stats_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        grid_layout.addWidget(self.stats_text, 1, 0)

        # Botón calcular
        calc_button = QPushButton("📊 Calcular Distribución")
        calc_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        calc_button.setMinimumHeight(34)
        calc_button.setMaximumHeight(34)
        calc_button.clicked.connect(self.calcular_distribucion)
        grid_layout.addWidget(calc_button, 2, 0)

        # ============ COLUMNA DERECHA ============

        # Distribución por profesor
        label_dist = QLabel("📋 Distribución por Profesor")
        label_dist.setStyleSheet(styles.STYLE_TITLE_SECTION)
        label_dist.setMaximumHeight(20)
        grid_layout.addWidget(label_dist, 0, 1)

        self.distribucion_text = QTextEdit()
        self.distribucion_text.setReadOnly(True)
        self.distribucion_text.setMinimumHeight(280)
        self.distribucion_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.distribucion_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        grid_layout.addWidget(self.distribucion_text, 1, 1)

        # Botón generar
        self.generar_button = QPushButton("🎯 Generar Asignación")
        self.generar_button.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.generar_button.setMinimumHeight(34)
        self.generar_button.setMaximumHeight(34)
        self.generar_button.setEnabled(False)
        self.generar_button.clicked.connect(self.generar_guardias)
        grid_layout.addWidget(self.generar_button, 2, 1)

        # ============ FILA INFERIOR - COLUMNA IZQUIERDA ============

        # Resultados de generación
        label_resultado = QLabel("📈 Resultados de Generación")
        label_resultado.setStyleSheet(
            styles.STYLE_TITLE_SECTION + "margin-top: 12px;"
        )
        label_resultado.setMaximumHeight(20)
        grid_layout.addWidget(label_resultado, 3, 0)

        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMinimumHeight(320)
        self.resultado_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.resultado_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        grid_layout.addWidget(self.resultado_text, 4, 0)

        # ============ FILA INFERIOR - COLUMNA DERECHA ============

        # Análisis de Incidencias
        label_incidencias = QLabel("⚠️ Análisis de Incidencias y Recomendaciones")
        label_incidencias.setStyleSheet(
            styles.STYLE_TITLE_SECTION + "margin-top: 12px;"
        )
        label_incidencias.setMaximumHeight(20)
        grid_layout.addWidget(label_incidencias, 3, 1)

        self.incidencias_text = QTextEdit()
        self.incidencias_text.setReadOnly(True)
        self.incidencias_text.setMinimumHeight(320)
        self.incidencias_text.setStyleSheet(styles.STYLE_TERMINAL_RETRO)
        self.incidencias_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.incidencias_text.setPlaceholderText(
            "Las incidencias y recomendaciones se mostrarán aquí después de generar guardias..."
        )
        grid_layout.addWidget(self.incidencias_text, 4, 1)

        # Botón limpiar (centrado, abajo)
        button_container = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 4, 0, 0)
        button_container.setLayout(button_layout)

        button_layout.addStretch()
        self.limpiar_button = QPushButton("🗑️  Limpiar Todas las Guardias")
        self.limpiar_button.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.limpiar_button.setMinimumWidth(280)
        self.limpiar_button.setMinimumHeight(34)
        self.limpiar_button.setMaximumHeight(34)
        self.limpiar_button.clicked.connect(self.limpiar_guardias)
        button_layout.addWidget(self.limpiar_button)
        button_layout.addStretch()

        grid_layout.addWidget(button_container, 5, 0, 1, 2)

        # Configurar proporciones de columnas
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)

        # Agregar el widget al scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self.setLayout(main_layout)

    def cargar_estadisticas(self):
        """Cargar y mostrar estadísticas del curso"""
        try:
            # Ejecutar Use Case
            stats = self.obtener_estadisticas_uc.execute()

            # Calcular slots teóricos (sin considerar fechas de zonas)
            slots_teoricos = (
                stats.dias_lectivos
                * (stats.recreos_manana + stats.recreos_tarde)
                * stats.num_zonas
            )

            # Formatear texto con colores tipo terminal
            dias_val = format_terminal_value(f'{stats.dias_lectivos} días (L-V)')
            total_recreos = stats.recreos_manana + stats.recreos_tarde
            texto = f"""
{format_terminal_label('Días lectivos:')} {dias_val}
{format_terminal_label('Recreos mañana:')} {format_terminal_number(stats.recreos_manana)}
{format_terminal_label('Recreos tarde:')} {format_terminal_number(stats.recreos_tarde)}
{format_terminal_label('Total recreos/día:')} {format_terminal_number(total_recreos)}
{format_terminal_label('Número de zonas:')} {format_terminal_number(stats.num_zonas)}
{format_terminal_label('Número de profesores:')} {format_terminal_number(stats.num_profesores)}

{format_terminal_success(f'📌 SLOTS TOTALES: {stats.slots_totales} guardias')}
"""

            # Añadir explicación de la diferencia si hay zonas con fechas límite
            if stats.slots_totales < slots_teoricos:
                diferencia = slots_teoricos - stats.slots_totales
                porcentaje = (
                    (diferencia / slots_teoricos * 100) if slots_teoricos > 0 else 0
                )
                info_sin_fechas = (
                    f'(sin fechas: {stats.dias_lectivos} × '
                    f'{total_recreos} × {stats.num_zonas})'
                )
                reduccion_msg = f'{diferencia} slots ({porcentaje:.1f}%)'
                texto += f"""
   {format_terminal_label('• Slots teóricos:')} {format_terminal_number(slots_teoricos)}
     {format_terminal_info(info_sin_fechas)}
   {format_terminal_label('• Slots reales:')} {format_terminal_number(stats.slots_totales)}
   {format_terminal_label('• Reducción:')} {format_terminal_warning(reduccion_msg)}

   {format_terminal_info('ℹ️  Hay zonas con fechas de inicio/fin que reducen')}
   {format_terminal_info('el número total de slots disponibles.')}
"""
            else:
                formula = f"{stats.dias_lectivos} × {total_recreos} × {stats.num_zonas}"
                texto += f"""   {format_terminal_info(f'(días × recreos × zonas = {formula})')}
"""

            self.stats_text.setHtml(wrap_terminal_html(texto.strip()))

        except BusinessLogicError as e:
            self.stats_text.setHtml(wrap_terminal_html(format_terminal_error(f"⚠️  {str(e)}")))
        except Exception as e:
            self.manejar_excepcion(e, "cargar estadísticas")

    def calcular_distribucion(self):
        """Calcular y mostrar la distribución de guardias"""
        try:
            # Ejecutar Use Case
            distribucion_dto = self.calcular_distribucion_uc.execute()

            # Formatear texto con colores tipo terminal
            texto = (
                f"{format_terminal_success('📊 Distribución OBJETIVO (estimada):')}\n\n"
            )
            info_msg1 = 'ℹ️  Esta distribución es el objetivo ideal basado en porcentajes.'
            info_msg2 = 'El algoritmo puede ajustar ligeramente para cubrir todos los slots.'
            texto += (
                f"{format_terminal_info(info_msg1)}\n"
            )
            texto += (
                f"{format_terminal_info(info_msg2)}\n\n"
            )

            # Ordenar por número de guardias (descendente)
            profesores_ordenados = sorted(
                distribucion_dto.distribucion.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            for profesor_id, guardias in profesores_ordenados:
                profesor = self.session.query(Profesor).get(profesor_id)
                if profesor:
                    porcentaje_jornada = f'{profesor.porcentaje_jornada*100:.0f}%'
                    info_prof = f'({profesor.turno}, {porcentaje_jornada})'
                    texto += (
                        f"• {format_terminal_profesor(profesor.nombre_completo)} "
                        f"{format_terminal_info(info_prof)}: "
                        f"{format_terminal_number(f'{guardias} guardias')}\n"
                    )

            total_msg = f'✅ TOTAL: {distribucion_dto.total_guardias} guardias'
            texto += (
                f"\n{format_terminal_success(total_msg)}"
            )
            slots_label = format_terminal_label('📌 Slots disponibles:')
            slots_num = format_terminal_number(distribucion_dto.slots_totales)
            texto += (
                f"\n{slots_label} {slots_num}"
            )

            if distribucion_dto.es_exacta:
                texto += f"\n\n{format_terminal_success('✅ La distribución es exacta')}"
            else:
                diferencia_abs = abs(distribucion_dto.diferencia)
                dif_msg = f'⚠️  Diferencia: {diferencia_abs}'
                texto += (
                    f"\n\n{format_terminal_warning(dif_msg)}"
                )

            msg_resultados = '💡 Tras generar, verifica el reparto real en "Resultados"'
            texto += f"\n\n{format_terminal_info(msg_resultados)}"

            self.distribucion_text.setHtml(wrap_terminal_html(texto))

            # Habilitar botón de generación
            self.generar_button.setEnabled(True)

        except BusinessLogicError as e:
            self.mostrar_error("Error en Cálculo", str(e))
            error_msg = format_terminal_error(f"❌ Error: {str(e)}")
            self.distribucion_text.setHtml(wrap_terminal_html(error_msg))

        except Exception as e:
            self.manejar_excepcion(e, "calcular distribución")

    def generar_guardias(self):
        """Generar el calendario completo de guardias"""
        try:
            # Verificar si ya existen guardias
            count_guardias = self.session.query(Guardia).count()

            eliminar_existentes = True  # Por defecto, eliminar

            if count_guardias > 0:
                from PyQt6.QtWidgets import QMessageBox
                from utils.ui_helpers import show_question_with_cancel
                respuesta = show_question_with_cancel(
                    self,
                    "⚠️ Guardias Existentes",
                    f"Ya existen {count_guardias} guardias en la base de datos.\n\n"
                    f"¿Deseas ELIMINAR todas las guardias existentes "
                    f"antes de generar nuevas?\n\n"
                    f"• SÍ: Eliminará todas y generará desde cero (recomendado)\n"
                    f"• NO: Agregará nuevas guardias a las existentes "
                    f"(puede crear duplicados)",
                    default_button="Yes"
                )

                if respuesta == QMessageBox.StandardButton.Cancel:
                    return

                eliminar_existentes = respuesta == QMessageBox.StandardButton.Yes

                if eliminar_existentes:
                    self.mostrar_exito(
                        "Limpieza completada",
                        f"{count_guardias} guardias eliminadas. "
                        f"Generando calendario nuevo...",
                    )

            # Función para ejecutar con progreso
            def tarea_generacion(progress_callback):
                """Ejecuta la generación de guardias con callback de progreso."""
                # Adapter para convertir (mensaje, porcentaje) a formato esperado por ProgressDialog
                def adapted_callback(mensaje: str, porcentaje: int):
                    # El dialog espera (actual, total, detalle)
                    # Convertimos porcentaje (0-100) a actual/total
                    progress_callback(porcentaje, 100, mensaje)

                return self.generar_guardias_uc.execute(
                    eliminar_existentes=eliminar_existentes,
                    progress_callback=adapted_callback,
                )

            # Ejecutar con indicador de progreso mejorado
            resumen = ejecutar_con_progreso(
                self,  # parent debe ser el primer argumento
                tarea_generacion,
                titulo="Generando Guardias",
                mensaje="Preparando generación de calendario...",
            )

            if resumen:
                # Mostrar resumen en el área de resultados
                texto = self._formatear_resumen(resumen)
                self.resultado_text.setHtml(wrap_terminal_html(texto))

                # Analizar y mostrar incidencias
                self._analizar_incidencias(resumen)

                self.mostrar_exito(
                    "Asignación generada",
                    resumen.mensaje
                    or "Guardias generadas y guardadas en la base de datos.",
                )

                # Sincronizar con la nube si está disponible
                if self.sync_manager:
                    try:
                        from utils.logger import get_logger
                        logger = get_logger(__name__)
                        logger.info("Sincronizando guardias generadas con la nube...")
                        if self.sync_manager.sync_on_shutdown(session=self.session):
                            logger.info("✓ Guardias sincronizadas con la nube")
                            self.mostrar_exito(
                                "Sincronización completada",
                                "Las guardias generadas se han guardado en la nube correctamente."
                            )
                        else:
                            logger.warning("⚠ Problemas al sincronizar con la nube")
                    except Exception as e:
                        from utils.logger import get_logger
                        logger = get_logger(__name__)
                        logger.error(f"Error al sincronizar: {e}")
                        # No mostrar error al usuario, solo logging

        except BusinessLogicError as e:
            self.mostrar_error("Error en Generación", str(e))

        except Exception as e:
            self.manejar_excepcion(e, "generar guardias")

    def _formatear_resumen(self, resumen) -> str:
        """
        Formatear el resumen de generación para mostrarlo.

        Args:
            resumen: ResumenGeneracionDTO con los resultados

        Returns:
            Texto formateado con el resumen (HTML con colores terminal)
        """
        guardias_label = format_terminal_label('Guardias generadas:')
        guardias_num = format_terminal_number(resumen.guardias_generadas)
        slots_label = format_terminal_label('Slots esperados:')
        slots_num = format_terminal_number(resumen.slots_esperados)

        lineas = [
            f"{guardias_label} {guardias_num}",
            f"{slots_label} {slots_num}",
        ]

        if resumen.cobertura_completa:
            lineas.append(format_terminal_success("✅ Cobertura completa"))
        elif resumen.slots_sin_cubrir > 0:
            warning_msg = (
                f"⚠️ {resumen.slots_sin_cubrir} slots sin cubrir "
                f"(falta elegibilidad)"
            )
            lineas.append(format_terminal_warning(warning_msg))

        # Top profesores (máximo 10)
        if resumen.resumen_por_profesor:
            top = sorted(
                resumen.resumen_por_profesor.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            lineas.append(f"\n{format_terminal_info('Por profesor (top 10):')}")
            for pid, cnt in top:
                prof = self.session.query(Profesor).get(pid)
                if prof:
                    prof_name = format_terminal_profesor(prof.nombre_completo)
                    cnt_num = format_terminal_number(cnt)
                    lineas.append(f"• {prof_name}: {cnt_num}")

        return "\n".join(lineas)

        return "\n".join(lineas)

    def _analizar_incidencias(self, resumen):
        """
        Analizar incidencias de la generación y proporcionar recomendaciones.

        Args:
            resumen: ResumenGeneracionDTO con los resultados
        """
        incidencias = []

        # Analizar cobertura
        if resumen.cobertura_completa:
            incidencias.append(format_terminal_success("✅ SIN INCIDENCIAS"))
            incidencias.append("")
            incidencias.append(
                format_terminal_info("La generación se completó exitosamente:")
            )
            success_msg1 = f'Todos los {resumen.slots_esperados} slots fueron cubiertos'
            incidencias.append(
                f"• {format_terminal_success(success_msg1)}"
            )
            incidencias.append(
                f"• {format_terminal_success('La distribución de guardias es óptima')}"
            )
            incidencias.append("")
            incidencias.append(format_terminal_info("🎯 Recomendaciones:"))
            msg_calendario = 'Revisa el calendario generado en la sección "Calendario"'
            incidencias.append(f"• {format_terminal_info(msg_calendario)}")
            msg_exportar = 'Puedes exportar los resultados para compartir con el equipo'
            incidencias.append(
                f"• {format_terminal_info(msg_exportar)}"
            )
        else:
            # Hay incidencias
            slots_sin_cubrir = resumen.slots_sin_cubrir
            porcentaje_sin_cubrir = (
                (slots_sin_cubrir / resumen.slots_esperados * 100)
                if resumen.slots_esperados > 0
                else 0
            )

            incidencias.append(format_terminal_error("⚠️ INCIDENCIAS DETECTADAS"))
            incidencias.append("")
            incidencias.append(format_terminal_label("📊 Resumen:"))
            warning_msg = (
                f'{slots_sin_cubrir} de {resumen.slots_esperados} '
                f'({porcentaje_sin_cubrir:.1f}%)'
            )
            slots_label = format_terminal_label('Slots sin cubrir:')
            warning_val = format_terminal_warning(warning_msg)
            incidencias.append(
                f"• {slots_label} {warning_val}"
            )
            guardias_label = format_terminal_label('Guardias generadas:')
            guardias_num = format_terminal_number(resumen.guardias_generadas)
            incidencias.append(
                f"• {guardias_label} {guardias_num}"
            )
            incidencias.append("")

            # Analizar causas
            incidencias.append(format_terminal_warning("🔍 CAUSAS PRINCIPALES:"))
            incidencias.append("")

            # 1. Falta de profesores elegibles
            incidencias.append(
                format_terminal_label("1️⃣ FALTA DE ELEGIBILIDAD DE PROFESORES")
            )
            incidencias.append("")
            incidencias.append(
                format_terminal_info(
                    "   Algunos slots no tienen profesores disponibles porque:"
                )
            )
            incidencias.append(
                format_terminal_info("   • Restricciones de horario muy estrictas")
            )
            incidencias.append(
                format_terminal_info("   • Fechas de inicio/fin de guardias limitadas")
            )
            incidencias.append(
                format_terminal_info(
                    "   • Turnos incompatibles (profesores de mañana no cubren tarde)"
                )
            )
            incidencias.append(
                format_terminal_info(
                    "   • Profesores con jornada reducida ya asignados al máximo"
                )
            )
            incidencias.append("")

            # 2. Desequilibrio de recursos
            from models.models import Zona

            num_zonas = self.session.query(Zona).count()
            num_profesores = self.session.query(Profesor).count()

            incidencias.append(format_terminal_label("2️⃣ ANÁLISIS DE RECURSOS"))
            incidencias.append("")
            prof_label = format_terminal_label('Profesores activos:')
            prof_num = format_terminal_number(num_profesores)
            incidencias.append(
                f"   • {prof_label} {prof_num}"
            )
            zonas_label = format_terminal_label('Zonas configuradas:')
            zonas_num = format_terminal_number(num_zonas)
            incidencias.append(
                f"   • {zonas_label} {zonas_num}"
            )
            if num_zonas > 0:
                ratio = num_profesores / num_zonas
                ratio_label = format_terminal_label('Ratio profesor/zona:')
                ratio_num = format_terminal_number(f'{ratio:.2f}')
                incidencias.append(
                    f"   • {ratio_label} {ratio_num}"
                )
            else:
                incidencias.append(
                    f"   • {format_terminal_warning('Ratio: N/A (no hay zonas)')}"
                )

            if num_zonas > 0 and num_profesores / num_zonas < 3:
                incidencias.append("")
                warning_msg = "   ⚠️ El ratio profesor/zona es bajo. Recomendado: mínimo 3:1"
                incidencias.append(
                    format_terminal_warning(warning_msg)
                )
            incidencias.append("")

            # 3. Distribución desigual
            if resumen.resumen_por_profesor:
                guardias_por_prof = list(resumen.resumen_por_profesor.values())
                if guardias_por_prof:
                    max_guardias = max(guardias_por_prof)
                    min_guardias = min(guardias_por_prof)
                    diferencia = max_guardias - min_guardias

                    incidencias.append(
                        format_terminal_label("3️⃣ DISTRIBUCIÓN DE CARGA")
                    )
                    incidencias.append("")
                    max_label = format_terminal_label('Máximo de guardias asignadas:')
                    max_num = format_terminal_number(max_guardias)
                    incidencias.append(
                        f"   • {max_label} {max_num}"
                    )
                    min_label = format_terminal_label('Mínimo de guardias asignadas:')
                    min_num = format_terminal_number(min_guardias)
                    incidencias.append(
                        f"   • {min_label} {min_num}"
                    )
                    dif_label = format_terminal_label('Diferencia:')
                    dif_num = format_terminal_number(diferencia)
                    incidencias.append(
                        f"   • {dif_label} {dif_num}"
                    )

                    if diferencia > 20:
                        incidencias.append("")
                        incidencias.append(
                            format_terminal_warning(
                                "   ⚠️ Distribución muy desigual detectada"
                            )
                        )
                    incidencias.append("")

            # Recomendaciones
            incidencias.append("")
            incidencias.append(
                format_terminal_success("💡 SOLUCIONES RECOMENDADAS:")
            )
            incidencias.append("")
            incidencias.append(
                format_terminal_info("1. Revisar restricciones de profesores:")
            )
            incidencias.append(
                format_terminal_info(
                    "   • Ve a 'Profesores' y revisa las restricciones de horario"
                )
            )
            incidencias.append(
                format_terminal_info(
                    "   • Considera flexibilizar los recreos permitidos"
                )
            )
            incidencias.append(
                format_terminal_info("   • Verifica fechas de inicio/fin de guardias")
            )
            incidencias.append("")
            incidencias.append(format_terminal_info("2. Ajustar recursos:"))
            if num_zonas > 0 and num_profesores / num_zonas < 3:
                incidencias.append(
                    format_terminal_info("   • Añadir más profesores al sistema")
                )
                incidencias.append(
                    format_terminal_info("   • O reducir el número de zonas a vigilar")
                )
            else:
                incidencias.append(
                    format_terminal_info(
                        "   • La cantidad de profesores parece adecuada"
                    )
                )
            incidencias.append("")
            incidencias.append(format_terminal_info("3. Verificar configuración:"))
            incidencias.append(
                format_terminal_info(
                    "   • Revisa días lectivos en 'Configuración'"
                )
            )
            incidencias.append(
                format_terminal_info("   • Verifica número de recreos por turno")
            )
            incidencias.append(
                format_terminal_info(
                    "   • Asegúrate de que las zonas estén bien configuradas"
                )
            )
            incidencias.append("")
            incidencias.append(format_terminal_info("4. Alternativas:"))
            incidencias.append(
                format_terminal_info(
                    "   • Permite que profesores de mañana cubran tarde (o viceversa)"
                )
            )
            incidencias.append(
                format_terminal_info(
                    "   • Aumenta las horas de contrato de algunos profesores"
                )
            )
            incidencias.append(
                format_terminal_info(
                    "   • Considera contratar profesores de apoyo"
                )
            )

        self.incidencias_text.setHtml(wrap_terminal_html("\n".join(incidencias)))

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.distribucion_text.clear()
        self.resultado_text.clear()
        self.incidencias_text.clear()
        self.generar_button.setEnabled(False)
        self.cargar_estadisticas()

    def limpiar_guardias(self):
        """Eliminar todas las guardias del sistema"""
        try:
            # Contar guardias actuales
            count_actual = self.session.query(Guardia).count()

            if count_actual == 0:
                self.mostrar_advertencia(
                    "Sin guardias",
                    "No hay guardias en el sistema para eliminar."
                )
                return

            # Confirmar con el usuario
            confirmado = self.confirmar_accion(
                "⚠️  LIMPIAR TODAS LAS GUARDIAS",
                f"¿Estás seguro de que deseas eliminar TODAS las {count_actual} guardias?\n\n"
                "Esta acción:\n"
                "• Eliminará todas las asignaciones de guardias\n"
                "• Liberará a todos los profesores\n"
                "• Liberará todas las zonas\n"
                "• NO se puede deshacer\n\n"
                "¿Deseas continuar?"
            )

            if not confirmado:
                return

            # Ejecutar limpieza
            count = self.limpiar_guardias_uc.execute()

            # Actualizar UI
            self.resultado_text.clear()
            self.limpiar_formulario()

            self.mostrar_exito(
                "Limpieza completada",
                f"Se han eliminado {count} guardias del sistema.\n\n"
                "Ahora puedes:\n"
                "• Eliminar zonas o profesores\n"
                "• Generar nuevas guardias desde cero"
            )

        except Exception as e:
            self.manejar_excepcion(e, "limpiar guardias")

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
