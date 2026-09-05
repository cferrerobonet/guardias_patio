"""Widget combinado para generación de guardias y resultados.

Combina:
- Botones de Generar y Limpiar guardias
- Resultados de generación con métricas de equidad
- Análisis de incidencias y recomendaciones
"""

from contextlib import contextmanager

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy.exc import SQLAlchemyError

from application.dtos.domain_services_dtos import AnalisisEquidadRequest
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from application.use_cases.asignacion_guardias import GenerarGuardiasUseCase
from application.use_cases.configuracion.actualizar_configuracion import (
    ActualizarConfiguracionUseCase,
)
from application.use_cases.guardia import LimpiarGuardiasUseCase
from infrastructure.repositories import SQLAlchemyGuardiaRepository
from presentation.theme.terminal_format import (
    format_terminal_error,
    format_terminal_info,
    format_terminal_label,
    format_terminal_number,
    format_terminal_profesor,
    format_terminal_success,
    format_terminal_warning,
    wrap_terminal_html,
)
from presentation.theme.tokens import Spacing
from utils import get_logger
from utils.icons import icon_for_button

_logger = get_logger(__name__)


@contextmanager
def sesion_de_trabajo():
    """Abre una sesión propia sobre la base de datos del usuario activo.

    Una `Session` de SQLAlchemy no es thread-safe: `check_same_thread=False` sólo
    silencia la comprobación de sqlite3, no hace segura la sesión. Cada hilo abre
    la suya (CRW-003).
    """
    from database.db_manager import get_db_session

    with get_db_session() as sesion:
        yield sesion


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

    def __init__(self, session, sync_manager=None, parent=None, session_factory=None):
        """Inicializa el panel de generación.

        Args:
            session: Sesión de SQLAlchemy del hilo GUI.
            sync_manager: Gestor de sincronización con la nube.
            parent: Widget padre opcional.
            session_factory: Context manager que abre una sesión nueva. Lo usa el
                worker de generación, que corre en otro hilo y no puede compartir
                la sesión de la GUI (CRW-003). Por defecto, la del usuario activo.
        """
        super().__init__("Generación y Resultados", parent)
        self.session = session
        self.sync_manager = sync_manager
        self._session_factory = session_factory or sesion_de_trabajo
        self._ultimo_resumen = None

        # Use Cases. El de generación no se instancia aquí: lo crea el worker con
        # su propia sesión (CRW-003); los demás corren en el hilo GUI.
        guardia_repo = SQLAlchemyGuardiaRepository(session)
        self.limpiar_guardias_uc = LimpiarGuardiasUseCase(guardia_repo)
        self.analisis_equidad_uc = AnalisisEquidadUseCase(session)

        self.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #1E7E34;
                border-radius: 6px;
                margin-top: 16px;
                padding-top: 14px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 6px 12px;
                left: 12px;
                top: -2px;
                background-color: white;
                color: #166529;
            }
        """)
        self._setup_ui()
        self._mostrar_mensaje_inicial()
        self.comprobar_prerrequisitos()

    def _setup_ui(self):
        """Configura la UI del panel."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 8, 6, 8)
        layout.setSpacing(6)

        # Selector de algoritmo
        algoritmo_container = QHBoxLayout()
        algoritmo_container.setContentsMargins(0, 0, 0, 4)
        algoritmo_container.setSpacing(Spacing.SM)

        algoritmo_label = QLabel("Algoritmo:")
        algoritmo_label.setStyleSheet("font-weight: bold; color: #374151;")
        algoritmo_container.addWidget(algoritmo_label)

        self.algoritmo_combo = QComboBox()
        self.algoritmo_combo.addItem("Rápido (v4 Híbrido)", "v4.0")
        self.algoritmo_combo.addItem("Óptimo (CP-SAT)", "cpsat")
        self.algoritmo_combo.setCurrentIndex(1)  # Default: óptimo (CP-SAT)
        self.algoritmo_combo.setToolTip(
            "Rápido: ~1 segundo, heurístico\nÓptimo: ~10 segundos, garantiza la mejor solución"
        )
        self.algoritmo_combo.setStyleSheet("""
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background: white;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #1E7E34;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 4px;
            }
        """)
        algoritmo_container.addWidget(self.algoritmo_combo)
        algoritmo_container.addStretch()

        layout.addLayout(algoritmo_container)

        # Contenedor de botones
        button_container = QHBoxLayout()
        button_container.setContentsMargins(0, 0, 0, 4)
        button_container.setSpacing(10)

        # Botón Generar (deshabilitado hasta que se calculen cuotas)
        self.generar_button = QPushButton("Generar Asignación")
        self.generar_button.setIcon(icon_for_button("target"))
        self.generar_button.setMinimumHeight(36)
        self.generar_button.clicked.connect(self._generar_guardias)
        self.generar_button.setEnabled(False)  # Deshabilitado hasta calcular cuotas
        self.generar_button.setToolTip("Primero debe calcular las cuotas")
        # Generar es la acción principal de la pantalla: ocupa el triple que la
        # destructiva, que hasta ahora tenía el mismo peso visual (UXF-006).
        self.generar_button.setObjectName("botonPrimarioDeVista")
        button_container.addWidget(self.generar_button, 3)

        # Botón Limpiar
        self.limpiar_button = QPushButton("Limpiar Guardias")
        self.limpiar_button.setIcon(icon_for_button("delete"))
        self.limpiar_button.setProperty("danger", "true")
        self.limpiar_button.setMinimumHeight(32)
        self.limpiar_button.setToolTip("Borra todas las guardias del curso")
        self.limpiar_button.clicked.connect(self._limpiar_guardias)
        button_container.addWidget(self.limpiar_button, 1)

        layout.addLayout(button_container)

        # Motivo del bloqueo, visible sin pasar el ratón por encima (UXF-008)
        self.label_bloqueo = QLabel("")
        self.label_bloqueo.setWordWrap(True)
        self.label_bloqueo.setStyleSheet(
            "color: #92400e; background: #fef3c7; border: 1px solid #fcd34d;"
            " border-radius: 4px; padding: 6px 8px;"
        )
        self.label_bloqueo.setVisible(False)
        layout.addWidget(self.label_bloqueo)

        # Área de texto estilo terminal
        self.content_text = QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setMinimumHeight(350)
        self.content_text.setObjectName("terminalRetro")
        self.content_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self.content_text)

        # Botón de notificación por email (solo visible post-generación)
        self.btn_notificar = QPushButton("Enviar emails a profesores")
        self.btn_notificar.setIcon(icon_for_button("email"))
        self.btn_notificar.setMinimumHeight(36)
        self.btn_notificar.setProperty("success", "true")
        self.btn_notificar.setToolTip(
            "Envía un email a cada profesor con sus guardias asignadas"
        )
        self.btn_notificar.clicked.connect(self._enviar_notificaciones)
        self.btn_notificar.setVisible(False)
        layout.addWidget(self.btn_notificar)

        self.setLayout(layout)

    def _mostrar_mensaje_inicial(self):
        """Muestra mensaje inicial."""
        texto = format_terminal_info(
            "Los resultados se mostrarán aquí después de\n"
            "   generar el calendario de guardias.\n\n"
            "   Pulsa 'Calcular Cuotas' en el panel izquierdo\n"
            "   para habilitar 'Generar Asignación'."
        )
        self.content_text.setHtml(wrap_terminal_html(texto))

    def comprobar_prerrequisitos(self):
        """Vuelve a preguntar al dominio si se puede generar y ajusta la interfaz.

        Antes esto era un booleano de sesión que se perdía al cambiar de vista o de
        curso y no comprobaba nada real (UXF-002).
        """
        from application.use_cases.preflight_generacion import PreflightGeneracionUseCase

        try:
            estado = PreflightGeneracionUseCase(self.session).execute()
        except SQLAlchemyError as e:
            _logger.warning(f"No se pudo comprobar los prerrequisitos: {e}")
            return None

        self.generar_button.setEnabled(estado.listo)
        if estado.listo:
            self.generar_button.setToolTip("Generar el calendario de guardias")
            self.label_bloqueo.setVisible(False)
        else:
            self.generar_button.setToolTip(estado.motivo)
            self.label_bloqueo.setText(
                "No se puede generar todavía. " + estado.motivo + ".\n"
                + "\n".join(f"• {r.titulo}: {r.detalle}" for r in estado.faltantes)
            )
            self.label_bloqueo.setVisible(True)
        return estado

    def habilitar_generacion(self, habilitar: bool = True):
        """Reacciona al cálculo de cuotas.

        El permiso para generar ya no lo concede la interfaz: lo decide el estado de
        los datos. Este método sólo pinta el mensaje de "listo para generar" y vuelve
        a comprobar los prerrequisitos.
        """
        estado = self.comprobar_prerrequisitos()
        if habilitar and (estado is None or estado.listo):
            texto = format_terminal_info(
                "Cuotas calculadas correctamente.\n\n"
                "Pulsa 'Generar Asignación' para crear\n"
                "   el calendario de guardias del curso."
            )
            self.content_text.setHtml(wrap_terminal_html(texto))

    def _generar_guardias(self):
        """Genera el calendario de guardias."""

        from presentation.widgets.progress_indicators import ejecutar_con_progreso

        try:
            # Obtener algoritmo seleccionado y actualizar configuración
            algoritmo_seleccionado = self.algoritmo_combo.currentData()
            from application.dtos import ActualizarConfiguracionDTO

            ActualizarConfiguracionUseCase(self.session).execute(
                ActualizarConfiguracionDTO(algoritmo_asignacion=algoritmo_seleccionado)
            )

            from application.app_services import AppServices

            app_svc = AppServices(self.session)
            count_guardias = app_svc.contar_guardias()
            n_profesores = app_svc.contar_profesores_activos()
            eliminar_existentes = True

            # Estimación de tiempo: ~2s base + 0.5s por profesor (heurística empírica CP-SAT)
            segundos_est = max(5, 2 + int(n_profesores * 0.5))
            if segundos_est < 60:
                tiempo_est = f"~{segundos_est} segundos"
            else:
                tiempo_est = f"~{segundos_est // 60} min {segundos_est % 60}s"

            resumen_previo = (
                f"Profesores activos: {n_profesores}\n"
                f"Algoritmo: {algoritmo_seleccionado.upper()}\n"
                f"Tiempo estimado: {tiempo_est}"
            )

            desde = None
            if count_guardias > 0:
                desde, seguir = self._preguntar_alcance(count_guardias, resumen_previo)
                if not seguir:
                    return
            else:
                # Primera generación del curso: no hay nada que decidir, así que el
                # resumen se pinta en la propia vista en vez de en un modal que sólo
                # se puede aceptar (UXF-003).
                self.content_text.setHtml(
                    wrap_terminal_html(
                        format_terminal_info(
                            "Generando el calendario de guardias...\n\n" + resumen_previo
                        )
                    )
                )

            # Antes de nada, copia de seguridad: generar borra las guardias del
            # curso y hasta ahora no había vuelta atrás (FUN-004).
            self._copia_de_seguridad("generar guardias")

            # Función para ejecutar con progreso. OJO: corre en el WorkerThread,
            # así que abre su propia sesión en vez de usar la de la GUI (CRW-003).
            def tarea_generacion(progress_callback, cancelacion=None):
                def adapted_callback(mensaje: str, porcentaje: int):
                    progress_callback(porcentaje, 100, mensaje)

                with self._session_factory() as sesion_worker:
                    return GenerarGuardiasUseCase(sesion_worker).execute(
                        eliminar_existentes=eliminar_existentes,
                        progress_callback=adapted_callback,
                        cancelacion=cancelacion,
                        desde=desde,
                    )

            # Ejecutar con indicador de progreso
            resumen = ejecutar_con_progreso(
                self,
                tarea_generacion,
                titulo="Generando Guardias",
                mensaje=f"Preparando generación ({n_profesores} profesores, {tiempo_est})...",
                cerrar_al_terminar=True,
            )

            if resumen:
                # La generación ocurrió en otra sesión: la de la GUI conserva en su
                # mapa de identidad las guardias anteriores hasta que se caduquen.
                self.session.expire_all()
                self._ultimo_resumen = resumen
                self._mostrar_resultados(resumen)
                self.btn_notificar.setVisible(True)
                self.guardias_generadas.emit()

                # Sincronizar si está disponible
                if self.sync_manager:
                    self._sincronizar()

        except (SQLAlchemyError, ValueError, TypeError, OSError) as e:
            self._mostrar_error(f"Error al generar: {e}")

    def _enviar_notificaciones(self):
        """Envía email con guardias a cada profesor con email corporativo."""
        from datetime import date

        from PyQt6.QtWidgets import QMessageBox

        from infrastructure.database.models import Guardia, Profesor
        from services.email_service import get_email_service

        email_service = get_email_service()
        if not email_service:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("SMTP no configurado")
            msg.setText(
                "No hay configuración SMTP activa.\n\n"
                "Configura el servidor de correo en Ajustes → Configuración SMTP."
            )
            msg.exec()
            return

        hoy = date.today()
        mes_anio = hoy.strftime("%B %Y").capitalize()

        profesores = (
            self.session.query(Profesor)
            .filter(Profesor.activo == True, Profesor.email_corporativo.isnot(None))  # noqa: E712
            .all()
        )

        sin_email = []
        enviados = 0
        errores = []

        for prof in profesores:
            if not prof.email_corporativo or "@" not in prof.email_corporativo:
                sin_email.append(prof.nombre_completo)
                continue

            guardias = (
                self.session.query(Guardia)
                .filter(Guardia.profesor_id == prof.id)
                .order_by(Guardia.fecha)
                .all()
            )
            if not guardias:
                continue

            ok, msg_txt = email_service.send_guardias_notification(
                to_email=prof.email_corporativo,
                profesor_nombre=prof.nombre_completo,
                guardias=guardias,
                mes_anio=mes_anio,
            )
            if ok:
                enviados += 1
            else:
                errores.append(f"{prof.nombre_completo}: {msg_txt}")

        resumen = f"Emails enviados: {enviados}"
        if sin_email:
            resumen += f"\nSin email configurado: {len(sin_email)}"
        if errores:
            resumen += f"\nErrores: {len(errores)}\n" + "\n".join(errores[:5])

        msg = QMessageBox(self)
        msg.setIcon(
            QMessageBox.Icon.Information if not errores else QMessageBox.Icon.Warning
        )
        msg.setWindowTitle("Notificaciones enviadas")
        msg.setText(resumen)
        msg.exec()

    def _limpiar_guardias(self):
        """Limpia todas las guardias."""
        from PyQt6.QtWidgets import QMessageBox

        from application.app_services import AppServices

        count = AppServices(self.session).contar_guardias()
        if count == 0:
            msg = QMessageBox(self)
            msg.setWindowTitle("Sin Guardias")
            msg.setText("No hay guardias para eliminar.")
            msg.exec()
            return

        msg = QMessageBox(self)
        msg.setWindowTitle("Confirmar Eliminación")
        msg.setText(f"¿Eliminar las {count} guardias existentes?")
        msg.setInformativeText("Esta acción no se puede deshacer.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(QMessageBox.StandardButton.No)

        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                self._copia_de_seguridad("limpiar guardias")
                self.limpiar_guardias_uc.execute()
                self._mostrar_mensaje_inicial()
                self._ultimo_resumen = None
                self.guardias_limpiadas.emit()

                if self.sync_manager:
                    self._sincronizar()

            except SQLAlchemyError as e:
                self._mostrar_error(f"Error al limpiar: {e}")

    def _preguntar_alcance(self, count_guardias: int, resumen_previo: str):
        """¿Rehacer el curso entero o sólo de hoy en adelante? (FUN-002)

        Devuelve `(desde, seguir)`. `desde` es None cuando se rehace todo.

        Sustituye a la pregunta anterior, de sí/no, cuyo «no» añadía guardias
        encima de las existentes: un modo que dejaba el calendario incoherente.
        """
        from datetime import date

        from PyQt6.QtWidgets import QMessageBox

        hoy = date.today()
        caja = QMessageBox(self)
        caja.setIcon(QMessageBox.Icon.Question)
        caja.setWindowTitle("Ya hay guardias generadas")
        caja.setText(f"Ya existen {count_guardias} guardias en el curso.")
        caja.setInformativeText(
            f"¿Qué quieres recalcular?\n\n"
            f"• Desde hoy ({hoy.strftime('%d/%m/%Y')}): se conserva lo anterior y también "
            f"las sustituciones que hayas hecho a mano.\n"
            f"• Todo el curso: se rehace desde el principio y se pierde lo ajustado.\n\n"
            f"─────────────────────────\n{resumen_previo}"
        )
        boton_desde_hoy = caja.addButton(
            f"Desde hoy ({hoy.strftime('%d/%m')})", QMessageBox.ButtonRole.AcceptRole
        )
        boton_todo = caja.addButton("Todo el curso", QMessageBox.ButtonRole.DestructiveRole)
        boton_cancelar = caja.addButton("Cancelar", QMessageBox.ButtonRole.RejectRole)
        caja.setDefaultButton(boton_desde_hoy)
        caja.exec()

        pulsado = caja.clickedButton()
        if pulsado is boton_cancelar or pulsado is None:
            return None, False
        if pulsado is boton_todo:
            return None, True
        return hoy, True

    def _copia_de_seguridad(self, motivo: str) -> None:
        """Guarda el estado actual antes de una operación que destruye datos."""
        try:
            from database.db_manager import backup_antes_de, get_current_user_id

            usuario = get_current_user_id()
            if usuario:
                backup_antes_de(usuario, motivo)
        except Exception as e:  # noqa: BLE001 - no impedir la operación por esto
            _logger.warning(f"No se pudo crear la copia previa a {motivo}: {e}")

    def _sincronizar(self):
        """Sincroniza con la nube en un hilo aparte, con diálogo de progreso.

        Subir por SFTP desde el hilo GUI dejaba la ventana congelada varios segundos
        y cualquier error de red acababa en el manejador global, que anunciaba un
        "Error inesperado" después de una generación correcta (CRW-007).
        """
        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            from presentation.widgets.sync_progress_dialog import (
                SyncProgressDialog,
                SyncWorker,
            )

            logger.info("Sincronizando con la nube...")
            dialogo = SyncProgressDialog(self)
            worker = SyncWorker(self.sync_manager)  # abre su propia sesión (CRW-003)
            worker.finished.connect(lambda ok: self._fin_sincronizacion(dialogo, ok))
            worker.start()
            dialogo.exec()
            worker.wait()
        except Exception as e:  # noqa: BLE001
            logger.warning(f"⚠ Error al sincronizar: {type(e).__name__}: {e}")

    def _fin_sincronizacion(self, dialogo, correcto: bool):
        """Cierra el diálogo de sincronización y deja constancia del resultado."""
        from utils.logger import get_logger

        get_logger(__name__).info(
            "✓ Sincronizado correctamente" if correcto else "⚠ La sincronización no se completó"
        )
        dialogo.accept()

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
            lineas.append(format_terminal_success(f"✅ Cobertura: {cobertura_pct:.1f}% (completa)"))
        elif resumen.slots_sin_cubrir > 0:
            lineas.append(
                format_terminal_warning(
                    f"⚠️ Cobertura: {cobertura_pct:.1f}% ({resumen.slots_sin_cubrir} sin cubrir)"
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
                        format_terminal_warning(f"⚠️ {metricas.desbalances_detectados} desbalances")
                    )
                else:
                    lineas.append(format_terminal_success("✅ Sin desbalances"))
            else:
                lineas.append(format_terminal_info("(equidad no disponible)"))
        except (SQLAlchemyError, ValueError, TypeError, OSError):
            lineas.append(format_terminal_info("(equidad no disponible)"))

        lineas.append("")

        # ═══════════════════════════════════════════════════════════
        # SECCIÓN 3: DISTRIBUCIÓN POR PROFESOR (TODOS)
        # ═══════════════════════════════════════════════════════════
        if resumen.resumen_por_profesor:
            lineas.append(format_terminal_info("─" * 50))
            lineas.append(format_terminal_label("👥 DISTRIBUCIÓN DE GUARDIAS ASIGNADAS:"))
            lineas.append("")

            # Función para normalizar turno
            def normalizar_turno(turno: str) -> str:
                t = (turno or "mixto").lower().strip()
                if t in ("mañana", "manana", "morning"):
                    return "mañana"
                elif t in ("tarde", "afternoon"):
                    return "tarde"
                else:
                    return "mixto"

            # Agrupar profesores por turno
            turno_manana = []
            turno_tarde = []
            turno_mixto = []

            for pid, cnt in resumen.resumen_por_profesor.items():
                from application.app_services import AppServices

                prof = AppServices(self.session).profesores.get_by_id(pid)
                if prof:
                    turno = normalizar_turno(str(prof.turno))
                    if turno == "mañana":
                        turno_manana.append((prof, cnt))
                    elif turno == "tarde":
                        turno_tarde.append((prof, cnt))
                    else:
                        turno_mixto.append((prof, cnt))

            # Ordenar cada grupo alfabéticamente
            turno_manana.sort(key=lambda x: x[0].nombre_completo)
            turno_tarde.sort(key=lambda x: x[0].nombre_completo)
            turno_mixto.sort(key=lambda x: x[0].nombre_completo)

            # Mostrar TURNO MAÑANA
            if turno_manana:
                lineas.append(format_terminal_success("☀️ TURNO MAÑANA"))
                for prof, cnt in turno_manana:
                    pct = prof.porcentaje_jornada or 100
                    prof_name = format_terminal_profesor(prof.nombre_completo)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name} ({pct:.0f}%): {cnt_num} guardias")
                lineas.append("")

            # Mostrar TURNO TARDE
            if turno_tarde:
                lineas.append(format_terminal_success("🌙 TURNO TARDE"))
                for prof, cnt in turno_tarde:
                    pct = prof.porcentaje_jornada or 100
                    prof_name = format_terminal_profesor(prof.nombre_completo)
                    cnt_num = format_terminal_number(str(cnt))
                    lineas.append(f"  • {prof_name} ({pct:.0f}%): {cnt_num} guardias")
                lineas.append("")

            # Mostrar TURNO MIXTO
            if turno_mixto:
                lineas.append(format_terminal_success("🔄 TURNO MIXTO"))
                for prof, cnt in turno_mixto:
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
        pct_sin = (slots_sin / resumen.slots_esperados * 100) if resumen.slots_esperados > 0 else 0

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
        from application.app_services import AppServices

        _svc = AppServices(self.session)
        num_zonas = _svc.contar_zonas()
        num_prof = _svc.contar_profesores()
        lineas.append(format_terminal_label("📊 RECURSOS:"))
        lineas.append(
            f"  • {format_terminal_label('Profesores:')} {format_terminal_number(num_prof)}"
        )
        lineas.append(f"  • {format_terminal_label('Zonas:')} {format_terminal_number(num_zonas)}")
        if num_zonas > 0:
            ratio = num_prof / num_zonas
            lineas.append(
                f"  • {format_terminal_label('Ratio:')} {format_terminal_number(f'{ratio:.1f}')}"
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
        from application.app_services import AppServices

        profesores_fechas = AppServices(self.session).profesores_activos_con_fechas_especiales()

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
            from application.app_services import AppServices

            guardias_prof = AppServices(self.session).guardias.find_by_profesor(prof.id)

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
                fechas_info.append(f"Inicio: {prof.fecha_inicio_guardias.strftime('%d/%m/%Y')}")
            if prof.fecha_fin_guardias:
                fechas_info.append(f"Fin: {prof.fecha_fin_guardias.strftime('%d/%m/%Y')}")

            if cumple:
                cumplidos += 1
                estado = format_terminal_success("✅")
                lineas.append(f"  {estado} {prof_name}")
                lineas.append(f"      {format_terminal_info(' | '.join(fechas_info))}")
                lineas.append(
                    f"      {format_terminal_number(str(guardias_asignadas))} "
                    f"guardias asignadas correctamente"
                )
            else:
                no_cumplidos += 1
                estado = format_terminal_warning("⚠️")
                lineas.append(f"  {estado} {prof_name}")
                lineas.append(f"      {format_terminal_info(' | '.join(fechas_info))}")
                for problema in problemas:
                    lineas.append(f"      {format_terminal_warning(problema)}")

            lineas.append("")

        # Resumen
        total = len(profesores_fechas)
        if no_cumplidos > 0:
            lineas.append(
                format_terminal_warning(
                    f"📊 Resumen: {cumplidos}/{total} cumplidos, {no_cumplidos} con problemas"
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
        from application.app_services import AppServices

        self.comprobar_prerrequisitos()
        count = AppServices(self.session).contar_guardias()
        if count == 0:
            self._mostrar_mensaje_inicial()
            self._ultimo_resumen = None
