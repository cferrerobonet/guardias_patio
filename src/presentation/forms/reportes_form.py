"""
Formulario de Reportes.

Permite generar calendarios PDF e informes estadísticos.
"""

import os

import ui_styles as styles
from models.models import Configuracion, Guardia, Profesor
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QLabel,
    QMessageBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
)
from services.exportador_pdf import ExportadorPDF
from utils import get_logger

from presentation.forms.base_form import BaseForm
from presentation.forms.reportes_widgets import (
    CalendariosPdfWidget,
    InformesEstadisticosWidget,
)
from presentation.themes.ccleaner_theme import TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso

logger = get_logger(__name__)


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

        # Título
        titulo = QLabel("📊 REPORTES E INFORMES")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

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
        self.tabs.addTab(self.calendarios_widget, "📅 Calendarios PDF")

        # Tab 2: Informes Estadísticos
        self.informes_widget = InformesEstadisticosWidget(self.session, self)
        self.tabs.addTab(self.informes_widget, "📊 Informes Estadísticos")

        main_layout.addWidget(self.tabs)

        # Resultado (ancho completo)
        resultado_group = QGroupBox("📋 Resultados")
        resultado_group.setStyleSheet(styles.STYLE_GROUPBOX)
        resultado_layout = QVBoxLayout()
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(180)
        self.resultado_text.setStyleSheet(styles.STYLE_INPUT)
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
                # Diálogo para seleccionar carpeta de destino
                carpeta = QFileDialog.getExistingDirectory(
                    self,
                    "Seleccionar carpeta para guardar PDFs",
                    "",
                    QFileDialog.Option.ShowDirsOnly,
                )

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

        except Exception as e:
            self.manejar_excepcion(e, "generar PDFs")
            self.resultado_text.setText(f"❌ Error al generar PDFs: {e}")

    def _exportar_mes_todos(self, config: dict, carpeta: str):
        """Exportar mes específico para todos los profesores."""
        mes = config["mes"]
        anio = config["anio"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_todos_los_profesores(
                self.session, mes, anio, carpeta, progress_callback=progress_callback
            )

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando PDFs - Mes completo",
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
                f"Tipo: Mes específico (todos los profesores)\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs creados: {resultado}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito("PDFs generados", f"Se generaron {resultado} calendarios correctamente.")

    def _exportar_mes_seleccionados(self, config: dict, carpeta: str):
        """Exportar mes específico para profesores seleccionados."""
        mes = config["mes"]
        anio = config["anio"]
        profesor_ids = config["profesores_ids"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_profesores_seleccionados(
                self.session, mes, anio, profesor_ids, carpeta, progress_callback=progress_callback
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
            self.mostrar_exito("PDFs generados", f"Se generaron {resultado} calendarios correctamente.")

    def _exportar_curso_todos(self, config: dict, carpeta: str):
        """Exportar curso completo para todos los profesores."""
        anio_inicio = config["anio_inicio_curso"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_curso_completo(
                self.session, anio_inicio, carpeta, progress_callback=progress_callback
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

    def _exportar_curso_seleccionados(self, config: dict, carpeta: str):
        """Exportar curso completo para profesores seleccionados."""
        anio_inicio = config["anio_inicio_curso"]
        profesor_ids = config["profesores_ids"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_curso_seleccionados(
                self.session,
                anio_inicio,
                profesor_ids,
                carpeta,
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
                QMessageBox.warning(
                    self,
                    "Email no configurado",
                    "La configuración SMTP no está disponible.\n\n"
                    "Los PDFs se generarán pero no se enviarán por email.\n\n"
                    "Para configurar el email, ve a Configuración > SMTP.",
                )
                enviar_email = False

        def tarea_exportacion(progress_callback):
            """Generar PDFs individuales para cada profesor."""
            exitos = 0
            emails_enviados = 0
            profesores_sin_email = []
            errores_email = []
            total = len(profesor_ids)

            for idx, profesor_id in enumerate(profesor_ids):
                # Obtener profesor
                profesor = self.session.query(Profesor).get(profesor_id)
                if not profesor:
                    continue

                # Reportar progreso
                porcentaje = int((idx / total) * 100) if total > 0 else 0
                mensaje = f"Generando PDF para {profesor.nombre_completo}..."
                if progress_callback:
                    progress_callback(porcentaje, mensaje)

                # Obtener rango de fechas de guardias del profesor
                guardias = (
                    self.session.query(Guardia)
                    .filter(Guardia.profesor_id == profesor_id)
                    .all()
                )

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
                        self.session,
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
                                    f"Profesor {profesor.nombre_completo} no tiene email configurado"
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
                                    config_db = (
                                        self.session.query(Configuracion).first()
                                    )
                                    nombre_centro = "Centro Educativo"
                                    if config_db and hasattr(config_db, "nombre_centro"):
                                        nombre_centro = config_db.nombre_centro

                                    # Generar archivo .ics
                                    if ICalendarService.generar_icalendar_profesor(
                                        session=self.session,
                                        profesor_id=profesor.id,
                                        ruta_salida=ics_path,
                                        nombre_centro=nombre_centro,
                                    ):
                                        logger.info(
                                            f"Archivo iCalendar generado: {ics_path}"
                                        )
                                    else:
                                        logger.warning(
                                            f"No se pudo generar iCalendar para "
                                            f"{profesor.nombre_completo}"
                                        )
                                        ics_path = None
                                except Exception as e:
                                    logger.warning(
                                        f"Error al generar iCalendar: {e}"
                                    )
                                    ics_path = None

                                exito_email, mensaje_email = email_service.send_calendar_pdf(
                                    to_email=profesor.email_corporativo,
                                    profesor_nombre=profesor.nombre_completo,
                                    pdf_path=ruta_salida,
                                    curso_escolar=curso_escolar,
                                    ics_path=ics_path,
                                )

                                if exito_email:
                                    emails_enviados += 1
                                    logger.info(
                                        f"Email enviado a {profesor.email_corporativo}: {mensaje_email}"
                                    )
                                else:
                                    errores_email.append(
                                        f"{profesor.nombre_completo}: {mensaje_email}"
                                    )
                                    logger.warning(
                                        f"No se pudo enviar email a {profesor.email_corporativo}: {mensaje_email}"
                                    )

                except Exception as e:
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
                "\nNota: Cada PDF muestra solo las fechas desde la primera hasta la última guardia del profesor."
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
