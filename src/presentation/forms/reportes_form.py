"""
Formulario de Reportes.

Permite generar calendarios PDF e informes estadísticos.
"""

import os
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from infrastructure.database.models import Configuracion, Profesor
from presentation.forms.base_form import BaseForm
from presentation.forms.reportes_widgets import (
    CalendariosPdfWidget,
    InformesEstadisticosWidget,
)
from presentation.themes.ccleaner_theme import TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from presentation.widgets.toast_notification import ToastNotification
from services.exportador_pdf import ExportadorPDF
from utils import get_logger
from utils.icons import icon_for_button

logger = get_logger(__name__)


def sesion_de_trabajo():
    """Sesión propia para las tareas que corren en el WorkerThread.

    Exportar un PDF supone cientos de consultas; hacerlas sobre la sesión de la GUI
    desde otro hilo es el escenario de CRW-003 (una `Session` de SQLAlchemy no es
    thread-safe). Se aísla en una función para poder sustituirla en los tests.
    """
    from database.db_manager import get_db_session

    return get_db_session()


class ReportesForm(BaseForm):
    """Formulario para generar reportes y calendarios PDF."""

    def __init__(self, session):
        """
        Inicializar formulario de reportes.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del formulario."""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Descripción
        desc = QLabel(
            "Genera calendarios PDF individuales o reportes estadísticos detallados "
            "con gráficos y análisis de guardias, carga de trabajo y cobertura."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            padding: 10px;
            font-size: 12px;
        """
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            """
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                background: white;
                padding: 10px;
            }
            QTabBar::tab {
                background: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 10px 20px;
                margin-right: 2px;
                font-size: 13px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid white;
                margin-bottom: -2px;
            }
            QTabBar::tab:hover {
                background: #d5dbdb;
            }
        """
        )

        # Tab 1: Calendarios PDF
        self.calendarios_widget = CalendariosPdfWidget(self.session, self)
        self.calendarios_widget.generar_pdfs_solicitado.connect(self.exportar_pdfs)
        self.tabs.addTab(self.calendarios_widget, "Calendarios PDF")

        # Tab 2: Informes Estadísticos
        self.informes_widget = InformesEstadisticosWidget(self.session, self)
        self.tabs.addTab(self.informes_widget, "Informes Estadísticos")

        # Tab 3: Exportar iCal
        ical_tab = self._crear_tab_ical()
        self.tabs.addTab(ical_tab, "📅 Exportar iCal")

        main_layout.addWidget(self.tabs)

        # Resultado (ancho completo)
        resultado_group = QGroupBox("Resultados")
        resultado_layout = QVBoxLayout()
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(180)
        self.resultado_text.setPlaceholderText(
            "Los resultados de las operaciones aparecerán aquí..."
        )
        resultado_layout.addWidget(self.resultado_text)
        resultado_group.setLayout(resultado_layout)
        main_layout.addWidget(resultado_group)

        self.setLayout(main_layout)

    # ========== PROPIEDADES DE COMPATIBILIDAD ==========

    @property
    def pdf_widget(self):
        """Acceso al widget de calendarios PDF."""
        return self.calendarios_widget

    # ========== FUNCIONES DE EXPORTACIÓN PDF ==========

    def exportar_pdfs(self):
        """Exportar calendarios PDF según el tipo seleccionado."""
        try:
            # Obtener configuración del widget
            config = self.calendarios_widget.get_configuracion_pdf()
            tipo = config["tipo"]
            enviar_email = config.get("enviar_email", False)

            # Si solo se envía por email (calendarios individuales), usar carpeta temporal
            # Para otros tipos o si no se envía email, pedir carpeta al usuario
            if tipo == "individual_seleccionados" and enviar_email:
                import tempfile

                carpeta = tempfile.mkdtemp()
                logger.info(f"Usando carpeta temporal para envío de emails: {carpeta}")
            else:
                # Diálogo para seleccionar carpeta, empezando por la última usada
                from utils.ui_helpers import pedir_carpeta

                carpeta = pedir_carpeta(self, "Seleccionar carpeta para guardar PDFs")

                if not carpeta:
                    return  # Usuario canceló

            # Validar selección de profesores si es necesario
            if tipo in ["mes_seleccionados", "curso_seleccionados", "individual_seleccionados"]:
                profesor_ids = config.get("profesores_ids", [])

                if not profesor_ids:
                    self.mostrar_advertencia(
                        "Sin selección", "Debes seleccionar al menos un profesor para exportar."
                    )
                    return

            # Ejecutar según el tipo
            if tipo == "mes_todos":
                self._exportar_mes_todos(config, carpeta)
            elif tipo == "mes_seleccionados":
                self._exportar_mes_seleccionados(config, carpeta)
            elif tipo == "curso_todos":
                self._exportar_curso_todos(config, carpeta)
            elif tipo == "curso_seleccionados":
                self._exportar_curso_seleccionados(config, carpeta)
            elif tipo == "individual_seleccionados":
                self._exportar_individual_seleccionados(config, carpeta)

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "generar PDFs")
            self.resultado_text.setText(f"Error al generar PDFs: {e}")

    def _exportar_mes_todos(self, config: dict, carpeta: str):
        """Exportar mes específico consolidado para todos los profesores."""
        mes = config["mes"]
        anio = config["anio"]

        # Nombre del archivo PDF consolidado
        meses_nombres = [
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
        nombre_archivo = f"Guardias_Consolidado_{meses_nombres[mes]}_{anio}.pdf"
        ruta_salida = os.path.join(carpeta, nombre_archivo)

        def tarea_exportacion(progress_callback):
            with sesion_de_trabajo() as sesion:  # hilo propio, sesión propia (CRW-003)
                return ExportadorPDF.exportar_mes_consolidado(
                    sesion, mes, anio, ruta_salida, progress_callback=progress_callback
                )

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando PDFs - Mes completo",
            mensaje="Preparando exportación...",
        )

        if resultado is not None:
            mensaje = (
                f"✅ PDF consolidado generado exitosamente\n\n"
                f"Tipo: Mes específico (todos los profesores)\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Carpeta: {carpeta}\n"
                f"Archivo: {nombre_archivo}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDF consolidado generado", "Se generó el calendario consolidado correctamente."
            )

    def _exportar_mes_seleccionados(self, config: dict, carpeta: str):
        """Exportar mes específico para profesores seleccionados."""
        mes = config["mes"]
        anio = config["anio"]
        profesor_ids = config["profesores_ids"]

        def tarea_exportacion(progress_callback):
            with sesion_de_trabajo() as sesion:  # hilo propio, sesión propia (CRW-003)
                return ExportadorPDF.exportar_profesores_seleccionados(
                    sesion, profesor_ids, mes, anio, carpeta, progress_callback=progress_callback
                )

        resultado = ejecutar_con_progreso(
            self,
            tarea_exportacion,
            titulo="Exportando PDFs - Mes seleccionados",
            mensaje="Preparando exportación...",
        )

        if resultado is not None:
            meses_nombres = [
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

            mensaje = (
                f"✅ PDFs generados exitosamente\n\n"
                f"Tipo: Mes específico (profesores seleccionados)\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Profesores: {len(profesor_ids)}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs creados: {resultado}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados", f"Se generaron {resultado} calendarios correctamente."
            )

    def _exportar_curso_todos(self, config: dict, carpeta: str):
        """Exportar curso completo para todos los profesores."""
        anio_inicio = config["anio_inicio_curso"]

        # Validar que hay curso activo
        if anio_inicio is None:
            self.mostrar_advertencia(
                "Sin curso activo",
                "No hay ningún curso escolar activo.\n\n"
                "Ve a Configuración → Gestión de Cursos para crear y activar un curso.",
            )
            return

        def tarea_exportacion(progress_callback):
            with sesion_de_trabajo() as sesion:  # hilo propio, sesión propia (CRW-003)
                return ExportadorPDF.exportar_curso_completo(
                    sesion, anio_inicio, carpeta, progress_callback=progress_callback
                )

        resultado = ejecutar_con_progreso(
            self,
            tarea_exportacion,
            titulo="Exportando PDF - Curso completo",
            mensaje="Preparando exportación...",
        )

        if resultado:
            mensaje = (
                f"✅ PDF del curso generado exitosamente\n\n"
                f"Tipo: Curso escolar completo\n"
                f"Curso: {anio_inicio}/{anio_inicio + 1}\n"
                f"Carpeta: {carpeta}\n"
                f"PDF: Guardias_Curso_{anio_inicio}_{anio_inicio + 1}_Completo.pdf\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDF generado",
                f"Se generó el calendario del curso {anio_inicio}/{anio_inicio + 1} correctamente.",
            )
        else:
            # No se generó el PDF
            mensaje = (
                f"❌ No se pudo generar el PDF del curso\n\n"
                f"Curso solicitado: {anio_inicio}/{anio_inicio + 1}\n"
                f"Rango de fechas: {anio_inicio} - {anio_inicio + 1} (año completo)\n\n"
                f"Posibles causas:\n"
                f"• No hay guardias asignadas en este curso escolar\n"
                f"• Las guardias existentes están fuera del rango de fechas\n\n"
                f"Revisa el año seleccionado y las fechas de las guardias."
            )
            self.resultado_text.setText(mensaje)
            self.mostrar_advertencia(
                "Sin datos para exportar",
                f"No hay guardias para generar el PDF del curso {anio_inicio}/{anio_inicio + 1}.",
            )

    def _exportar_curso_seleccionados(self, config: dict, carpeta: str):
        """Exportar curso completo para profesores seleccionados."""
        anio_inicio = config["anio_inicio_curso"]

        # Validar que hay curso activo
        if anio_inicio is None:
            self.mostrar_advertencia(
                "Sin curso activo",
                "No hay ningún curso escolar activo.\n\n"
                "Ve a Configuración → Gestión de Cursos para crear y activar un curso.",
            )
            return

        profesor_ids = config["profesores_ids"]

        def tarea_exportacion(progress_callback):
            with sesion_de_trabajo() as sesion:  # hilo propio, sesión propia (CRW-003)
                return ExportadorPDF.exportar_curso_completo(
                    sesion,
                    anio_inicio,
                    carpeta,
                    profesor_ids=profesor_ids,
                    progress_callback=progress_callback,
                )

        resultado = ejecutar_con_progreso(
            self,
            tarea_exportacion,
            titulo="Exportando PDF - Curso seleccionados",
            mensaje="Preparando exportación...",
        )

        if resultado:
            mensaje = (
                f"✅ PDF del curso generado exitosamente\n\n"
                f"Tipo: Curso escolar (profesores seleccionados)\n"
                f"Curso: {anio_inicio}/{anio_inicio + 1}\n"
                f"Profesores: {len(profesor_ids)}\n"
                f"Carpeta: {carpeta}\n"
                f"PDF: Guardias_Curso_{anio_inicio}_{anio_inicio + 1}_Completo.pdf\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDF generado",
                f"Se generó el calendario del curso {anio_inicio}/{anio_inicio + 1} correctamente.",
            )
        else:
            # No se generó el PDF
            mensaje = (
                f"❌ No se pudo generar el PDF del curso\n\n"
                f"Curso solicitado: {anio_inicio}/{anio_inicio + 1}\n"
                f"Profesores seleccionados: {len(profesor_ids)}\n"
                f"Rango de fechas: {anio_inicio} - {anio_inicio + 1} (año completo)\n\n"
                f"Posibles causas:\n"
                f"• Los profesores seleccionados no tienen guardias en este curso\n"
                f"• Las guardias existentes están fuera del rango de fechas\n\n"
                f"Revisa el año seleccionado y las fechas de las guardias."
            )
            self.resultado_text.setText(mensaje)
            self.mostrar_advertencia(
                "Sin datos para exportar",
                f"No hay guardias para generar el PDF del curso {anio_inicio}/{anio_inicio + 1}.",
            )

    def _exportar_individual_seleccionados(self, config: dict, carpeta: str):
        """Exportar calendarios individuales para profesores seleccionados."""

        profesor_ids = config["profesores_ids"]
        enviar_email = config.get("enviar_email", False)

        # Importar EmailService solo si es necesario
        email_service = None
        if enviar_email:
            from services.email_service import get_email_service

            email_service = get_email_service()
            if not email_service:
                ToastNotification(
                    self.window(),
                    "SMTP no configurado — los PDFs se generarán sin enviar email",
                    "error",
                )
                enviar_email = False

        def tarea_exportacion(progress_callback):
            """Generar PDFs individuales para cada profesor."""
            # Corre en el WorkerThread: sesión propia, no la de la GUI (CRW-003).
            with sesion_de_trabajo() as sesion:
                exitos = 0
                emails_enviados = 0
                profesores_sin_email = []
                errores_email = []
                total = len(profesor_ids)

                for idx, profesor_id in enumerate(profesor_ids):
                    # Obtener profesor
                    from application.app_services import AppServices
                    profesor = AppServices(sesion).profesores.get_by_id(profesor_id)
                    if not profesor:
                        continue

                    # Reportar progreso
                    porcentaje = int((idx / total) * 100) if total > 0 else 0
                    mensaje = f"Generando PDF para {profesor.nombre_completo}..."
                    if progress_callback:
                        progress_callback(porcentaje, mensaje)

                    # Obtener rango de fechas de guardias del profesor
                    from application.app_services import AppServices
                    guardias = AppServices(sesion).guardias.find_by_profesor(profesor_id)

                    if not guardias:
                        continue  # Profesor sin guardias

                    # Calcular rango real
                    fechas = [g.fecha for g in guardias]
                    fecha_inicio = min(fechas)
                    fecha_fin = max(fechas)

                    # Determinar curso escolar
                    anio_inicio = (
                        fecha_inicio.year if fecha_inicio.month >= 9 else fecha_inicio.year - 1
                    )
                    curso_escolar = f"{anio_inicio}/{anio_inicio + 1}"

                    # Generar nombre de archivo
                    nombre_archivo = f"Calendario_{profesor.nombre_completo.replace(' ', '_')}.pdf"
                    ruta_salida = f"{carpeta}/{nombre_archivo}"

                    # Exportar PDF individual
                    try:
                        resultado = ExportadorPDF.exportar_profesor_individual_optimizado(
                            sesion,
                            profesor_id,
                            fecha_inicio,
                            fecha_fin,
                            ruta_salida,
                            progress_callback=None,  # Ya manejamos el progreso aquí
                        )
                        if resultado:
                            exitos += 1

                            # Enviar email si está habilitado
                            if enviar_email and email_service:
                                if not profesor.email_corporativo:
                                    profesores_sin_email.append(profesor.nombre_completo)
                                    logger.warning(
                                        f"Profesor {profesor.nombre_completo} "
                                        f"no tiene email configurado"
                                    )
                                else:
                                    if progress_callback:
                                        progress_callback(
                                            porcentaje,
                                            f"Enviando email a {profesor.nombre_completo}...",
                                        )

                                    # Generar archivo .ics para adjuntar
                                    ics_path = None
                                    try:
                                        from services.icalendar_service import ICalendarService

                                        ics_filename = ICalendarService.obtener_nombre_archivo_ics(
                                            profesor.nombre_completo
                                        )
                                        ics_path = os.path.join(carpeta, ics_filename)

                                        # Obtener configuración para nombre del centro
                                        from application.app_services import AppServices
                                        config_db = (
                                            AppServices(sesion).configuracion_repo.get_first()
                                        )
                                        nombre_centro = "Centro Educativo"
                                        if config_db and hasattr(config_db, "nombre_centro"):
                                            nombre_centro = config_db.nombre_centro

                                        # Generar archivo .ics
                                        if ICalendarService.generar_icalendar_profesor(
                                            session=sesion,
                                            profesor_id=profesor.id,
                                            ruta_salida=ics_path,
                                            nombre_centro=nombre_centro,
                                        ):
                                            logger.info(f"Archivo iCalendar generado: {ics_path}")
                                        else:
                                            logger.warning(
                                                f"No se pudo generar iCalendar para "
                                                f"{profesor.nombre_completo}"
                                            )
                                            ics_path = None
                                    except (ValueError, TypeError, OSError) as e:
                                        logger.warning(f"Error al generar iCalendar: {e}")
                                        ics_path = None

                                    exito_email, mensaje_email = email_service.send_calendar_pdf(
                                        to_email=str(profesor.email_corporativo),
                                        profesor_nombre=profesor.nombre_completo,
                                        pdf_path=ruta_salida,
                                        curso_escolar=curso_escolar,
                                        ics_path=ics_path,
                                    )

                                    if exito_email:
                                        emails_enviados += 1
                                        logger.info(
                                            f"Email enviado a {profesor.email_corporativo}: "
                                            f"{mensaje_email}"
                                        )
                                    else:
                                        errores_email.append(
                                            f"{profesor.nombre_completo}: {mensaje_email}"
                                        )
                                        logger.warning(
                                            f"No se pudo enviar email a "
                                            f"{profesor.email_corporativo}: {mensaje_email}"
                                        )

                    except (ValueError, TypeError, OSError) as e:
                        logger.error(f"Error al exportar PDF para profesor {profesor_id}: {e}")

                # Progreso final
                if progress_callback:
                    progress_callback(100, "Exportación completada")

                return {
                    "exitos": exitos,
                    "emails_enviados": emails_enviados,
                    "profesores_sin_email": profesores_sin_email,
                    "errores_email": errores_email,
                }

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando Calendarios Individuales",
            mensaje="Preparando exportación...",
        )

        if resultado is not None:
            exitos = resultado.get("exitos", 0)
            emails_enviados = resultado.get("emails_enviados", 0)
            profesores_sin_email = resultado.get("profesores_sin_email", [])
            errores_email = resultado.get("errores_email", [])

            mensaje = (
                f"✅ Calendarios individuales generados exitosamente\n\n"
                f"Tipo: Calendario individual optimizado\n"
                f"Profesores seleccionados: {len(profesor_ids)}\n"
            )

            # Solo mostrar carpeta si no es temporal (no se envía solo por email)
            if not (enviar_email and carpeta.startswith("/var/folders")):
                mensaje += f"Carpeta: {carpeta}\n"

            mensaje += f"PDFs generados: {exitos}\n"

            if enviar_email:
                mensaje += f"Emails enviados: {emails_enviados}\n"

            mensaje += (
                "\nNota: Cada PDF muestra solo las fechas desde la primera "
                "hasta la última guardia del profesor."
            )

            self.resultado_text.setText(mensaje)

            # Mensajes detallados según el resultado
            if enviar_email and (profesores_sin_email or errores_email):
                detalles = f"Se generaron {exitos} calendarios individuales.\n\n"
                detalles += f"Emails enviados: {emails_enviados} de {exitos}\n\n"

                if profesores_sin_email:
                    detalles += "❌ Profesores sin email configurado:\n"
                    for nombre in profesores_sin_email:
                        detalles += f"  • {nombre}\n"
                    detalles += "\n"

                if errores_email:
                    detalles += "⚠️ Errores al enviar emails:\n"
                    for error in errores_email:
                        detalles += f"  • {error}\n"

                self.mostrar_advertencia("PDFs generados con problemas de email", detalles)
            else:
                self.mostrar_exito(
                    "PDFs generados",
                    f"Se generaron {exitos} calendarios individuales correctamente."
                    + (f"\n\n{emails_enviados} emails enviados." if enviar_email else ""),
                )

    # ========== TAB ICAL ==========

    def _crear_tab_ical(self) -> QWidget:
        """Crear la pestaña de exportación iCal."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        desc = QLabel(
            "Exporta las guardias de un profesor como archivo .ics compatible con "
            "Google Calendar, Outlook y Apple Calendar."
        )
        desc.setWordWrap(True)
        desc.setProperty("texto", "secundario")
        layout.addWidget(desc)

        # Selector de profesor
        row = QHBoxLayout()
        row.addWidget(QLabel("Profesor:"))
        self._ical_combo = QComboBox()
        self._ical_combo.setMinimumWidth(300)
        self._cargar_profesores_ical()
        row.addWidget(self._ical_combo)
        row.addStretch()
        layout.addLayout(row)

        # Botón exportar
        btn = QPushButton("Exportar archivo .ics")
        btn.setIcon(icon_for_button("calendar"))
        btn.setMinimumHeight(36)
        btn.clicked.connect(self._exportar_ical)
        layout.addWidget(btn)
        layout.addStretch()

        return tab

    def _cargar_profesores_ical(self):
        self._ical_combo.clear()
        try:
            profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()
            for p in profesores:
                self._ical_combo.addItem(p.nombre_completo, p.id)
        except Exception:
            pass

    def _exportar_ical(self):
        profesor_id = self._ical_combo.currentData()
        if profesor_id is None:
            self.mostrar_advertencia("Sin selección", "Selecciona un profesor.")
            return

        profesor_nombre = self._ical_combo.currentText()
        from services.icalendar_service import ICalendarService

        nombre_archivo = ICalendarService.obtener_nombre_archivo_ics(profesor_nombre)
        from utils.ui_helpers import recordar_carpeta, ultima_carpeta

        # Propone la última carpeta usada, en vez de empezar siempre de cero
        carpeta_previa = ultima_carpeta()
        propuesta = (
            str(Path(carpeta_previa) / nombre_archivo) if carpeta_previa else nombre_archivo
        )
        ruta, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar archivo iCal",
            propuesta,
            "iCalendar (*.ics)",
        )
        if not ruta:
            return
        recordar_carpeta(ruta)

        try:
            config = self.session.query(Configuracion).first()
            nombre_centro = "Centro Educativo"
            if config and hasattr(config, "nombre_centro") and config.nombre_centro:
                nombre_centro = config.nombre_centro

            ok = ICalendarService.generar_icalendar_profesor(
                session_or_factory=self.session,
                profesor_id=profesor_id,
                ruta_salida=ruta,
                nombre_centro=nombre_centro,
            )
            if ok:
                self.resultado_text.setText(
                    f"✅ Archivo iCal exportado\n\nProfesor: {profesor_nombre}\nArchivo: {ruta}"
                )
                self.mostrar_exito("iCal exportado", f"Guardado en {ruta}")
            else:
                self.mostrar_advertencia(
                    "Sin guardias", f"{profesor_nombre} no tiene guardias asignadas."
                )
        except (OSError, ValueError) as e:
            self.mostrar_error("Error al exportar", str(e))

