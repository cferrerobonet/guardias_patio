"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y generar calendarios PDF para profesores.
"""

import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import ui_styles as styles
from models.models import Configuracion, Guardia, Profesor, Zona
from presentation.forms.base_form import BaseForm
from presentation.forms.import_export_widgets import (
    JsonOperationsWidget,
    PdfExportWidget,
)
from presentation.themes.ccleaner_theme import TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from services.importador_profesores import importar_profesores_desde_excel
from utils import get_logger

logger = get_logger(__name__)


class ImportExportForm(BaseForm):
    """Formulario para importar/exportar datos."""

    # Señales que se emiten cuando se importan datos
    profesores_importados = pyqtSignal()
    zonas_importadas = pyqtSignal()

    def __init__(self, session):
        """
        Inicializar formulario de importación/exportación.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setup_ui()

    # ========== PROPIEDADES DE COMPATIBILIDAD ==========

    @property
    def limpiar_checkbox(self):
        """Compatibilidad: acceso al checkbox de limpiar datos."""
        return self.json_widget.limpiar_checkbox

    @property
    def pdf_tipo_combo(self):
        """Compatibilidad: acceso al combo de tipo PDF."""
        return self.pdf_widget.pdf_tipo_combo

    @property
    def pdf_mes_combo(self):
        """Compatibilidad: acceso al combo de mes PDF."""
        return self.pdf_widget.pdf_mes_combo

    @property
    def pdf_anio_combo(self):
        """Compatibilidad: acceso al combo de año PDF."""
        return self.pdf_widget.pdf_anio_combo

    @property
    def pdf_curso_combo(self):
        """Compatibilidad: acceso al combo de curso PDF."""
        return self.pdf_widget.pdf_curso_combo

    @property
    def profesor_checkboxes(self):
        """Compatibilidad: acceso a la lista de checkboxes de profesores."""
        return self.pdf_widget.profesor_checkboxes

    @property
    def seleccionar_todos_check(self):
        """Compatibilidad: acceso al checkbox de seleccionar todos."""
        return self.pdf_widget.seleccionar_todos_check

    def setup_ui(self):
        """Construir la interfaz del formulario."""
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Título
        titulo = QLabel("💾 IMPORTAR / EXPORTAR DATOS")
        titulo.setStyleSheet(styles.STYLE_TITLE_MAIN)
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Gestiona la importación y exportación de datos de la aplicación. "
            "Puedes exportar/importar datos en JSON, importar profesores desde Excel "
            "o generar calendarios PDF individuales."
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

        # Layout en 2 columnas para las secciones principales
        layout_columnas = QHBoxLayout()
        layout_columnas.setSpacing(15)

        # Columna izquierda: JSON Operations Widget
        columna_izq = QVBoxLayout()
        self.json_widget = JsonOperationsWidget(self)
        self.json_widget.exportar_solicitado.connect(self.exportar_datos)
        self.json_widget.importar_solicitado.connect(self.importar_datos)
        columna_izq.addWidget(self.json_widget)
        columna_izq.addStretch()
        layout_columnas.addLayout(columna_izq, 1)

        # Columna derecha: Importar profesores y PDF
        columna_der = QVBoxLayout()
        columna_der.addWidget(self._crear_seccion_importar_profesores())
        self.pdf_widget = PdfExportWidget(self.session, self)
        self.pdf_widget.generar_pdfs_solicitado.connect(self.exportar_pdfs)
        columna_der.addWidget(self.pdf_widget)
        columna_der.addStretch()
        layout_columnas.addLayout(columna_der, 1)

        main_layout.addLayout(layout_columnas)

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

    def _crear_seccion_importar_profesores(self) -> QGroupBox:
        """Crear sección de importación de profesores desde Excel."""
        grupo = QGroupBox("📊 IMPORTAR PROFESORES DESDE EXCEL")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "Importa profesores desde un archivo Excel (.xlsx). "
            "Los nuevos se añadirán, los existentes se omitirán."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """
        )
        layout.addWidget(info)

        self.importar_profesores_btn = QPushButton("� Importar Profesores...")
        self.importar_profesores_btn.clicked.connect(self.importar_profesores)
        self.importar_profesores_btn.setMinimumHeight(40)
        self.importar_profesores_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        layout.addWidget(self.importar_profesores_btn)

        grupo.setLayout(layout)
        return grupo

    def exportar_datos(self):
        """Exportar todos los datos a archivo JSON."""
        try:
            # Diálogo para seleccionar archivo de destino
            archivo, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar datos",
                "guardias_patio_export.json",
                "Archivos JSON (*.json)",
            )

            if not archivo:
                return  # Usuario canceló

            # Exportar datos
            ExportadorDatos.exportar_todo(self.session, archivo)

            # Mostrar resumen
            prof_count = self.session.query(Profesor).count()
            zona_count = self.session.query(Zona).count()
            config_count = self.session.query(Configuracion).count()

            mensaje = (
                f"✅ Datos exportados exitosamente a:\n{archivo}\n\n"
                f"Datos exportados:\n"
                f"• Profesores: {prof_count}\n"
                f"• Zonas: {zona_count}\n"
                f"• Configuración: {config_count}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito("Datos exportados", "Los datos se exportaron correctamente.")

        except Exception as e:
            self.manejar_excepcion(e, "exportar datos")
            self.resultado_text.setText(f"❌ Error al exportar: {e}")

    def importar_datos(self):
        """Importar datos desde archivo JSON."""
        try:
            # Confirmación previa
            limpiar = self.limpiar_checkbox.isChecked()
            if limpiar:
                respuesta = QMessageBox.question(
                    self,
                    "Confirmar importación",
                    "⚠️ ATENCIÓN: Se eliminarán TODOS los datos actuales.\n\n"
                    "¿Está seguro de que desea continuar?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )

                if respuesta != QMessageBox.StandardButton.Yes:
                    return

            # Diálogo para seleccionar archivo
            archivo, _ = QFileDialog.getOpenFileName(
                self, "Importar datos", "", "Archivos JSON (*.json)"
            )

            if not archivo:
                return  # Usuario canceló

            # Importar datos
            resultado = ExportadorDatos.importar_todo(self.session, archivo, limpiar)

            mensaje = (
                f"✅ Datos importados exitosamente desde:\n{archivo}\n\n"
                f"Datos importados:\n"
                f"• Profesores: {resultado['profesores']}\n"
                f"• Zonas: {resultado['zonas']}\n"
                f"• Configuración: {resultado['configuracion']}\n"
                f"• Guardias: {resultado['guardias']}\n"
            )

            # Añadir info de SMTP y SFTP si se importaron
            if resultado.get("smtp_config", 0) > 0:
                mensaje += "• Configuración SMTP: ✅ Actualizada\n"
            if resultado.get("sftp_config", 0) > 0:
                mensaje += "• Configuración SFTP: ✅ Actualizada\n"

            self.resultado_text.setText(mensaje)

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Éxito")
            msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                "Datos importados correctamente.\n\n"
                "Se recomienda reiniciar la aplicación para ver los cambios."
            )
            msg.exec()

            # Emitir señales de datos importados
            if resultado.get("profesores", 0) > 0:
                self.profesores_importados.emit()
            if resultado.get("zonas", 0) > 0:
                self.zonas_importadas.emit()

        except Exception as e:
            self.manejar_excepcion(e, "importar datos")
            self.resultado_text.setText(f"❌ Error al importar: {e}")

    def exportar_pdfs(self):
        """Exportar calendarios PDF según el tipo seleccionado."""
        try:
            # Obtener configuración del widget
            config = self.pdf_widget.get_configuracion_pdf()
            tipo = config["tipo"]

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
                f"Tipo: Mes completo (todos los profesores)\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {resultado}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados", f"Se generaron {resultado} calendarios PDF correctamente."
            )

    def _exportar_mes_seleccionados(self, config: dict, carpeta: str):
        """Exportar mes específico para profesores seleccionados."""
        mes = config["mes"]
        anio = config["anio"]
        profesor_ids = config["profesores_ids"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_profesores_seleccionados(
                self.session, profesor_ids, mes, anio, carpeta, progress_callback=progress_callback
            )

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando PDFs - Profesores seleccionados",
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
                f"Tipo: Profesores seleccionados\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Profesores: {len(profesor_ids)}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {resultado}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados", f"Se generaron {resultado} calendarios PDF correctamente."
            )

    def _exportar_curso_todos(self, config: dict, carpeta: str):
        """Exportar curso completo para todos los profesores."""
        anio_inicio = config["anio_inicio_curso"]

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_curso_completo(
                self.session,
                anio_inicio,
                carpeta,
                profesor_ids=None,  # Todos los profesores
                progress_callback=progress_callback,
            )

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando PDF - Curso completo",
            mensaje="Generando curso escolar completo...",
        )

        if resultado is not None:
            mensaje = (
                f"✅ PDF del curso completo generado exitosamente\n\n"
                f"Tipo: Curso escolar completo (todos los profesores)\n"
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
            return ExportadorPDF.exportar_curso_completo(
                self.session,
                anio_inicio,
                carpeta,
                profesor_ids=profesor_ids,
                progress_callback=progress_callback,
            )

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando PDF - Curso seleccionado",
            mensaje="Generando curso escolar para profesores seleccionados...",
        )

        if resultado is not None:
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
                anio_inicio = fecha_inicio.year if fecha_inicio.month >= 9 else fecha_inicio.year - 1
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
                        if enviar_email and email_service and profesor.email_corporativo:
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
                                logger.warning(
                                    f"No se pudo enviar email a {profesor.email_corporativo}: {mensaje_email}"
                                )

                except Exception as e:
                    logger.error(f"Error al exportar PDF para profesor {profesor_id}: {e}")

            # Progreso final
            if progress_callback:
                progress_callback(100, "Exportación completada")

            return {"exitos": exitos, "emails_enviados": emails_enviados}

        resultado = ejecutar_con_progreso(
            self,  # parent
            tarea_exportacion,  # funcion
            titulo="Exportando Calendarios Individuales",
            mensaje="Preparando exportación...",
        )

        if resultado is not None:
            exitos = resultado.get("exitos", 0)
            emails_enviados = resultado.get("emails_enviados", 0)

            mensaje = (
                f"✅ Calendarios individuales generados exitosamente\n\n"
                f"Tipo: Calendario individual optimizado\n"
                f"Profesores seleccionados: {len(profesor_ids)}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {exitos}\n"
            )

            if enviar_email:
                mensaje += f"Emails enviados: {emails_enviados}\n"

            mensaje += (
                "\nNota: Cada PDF muestra solo las fechas desde la primera hasta la última guardia del profesor."
            )

            self.resultado_text.setText(mensaje)

            if enviar_email and emails_enviados < exitos:
                self.mostrar_exito(
                    "PDFs generados",
                    f"Se generaron {exitos} calendarios individuales.\n\n"
                    f"Emails enviados: {emails_enviados} de {exitos}\n\n"
                    f"Algunos profesores pueden no tener email configurado.",
                )
            else:
                self.mostrar_exito(
                    "PDFs generados",
                    f"Se generaron {exitos} calendarios individuales correctamente."
                    + (f"\n\n{emails_enviados} emails enviados." if enviar_email else ""),
                )

    def importar_profesores(self):
        """Importar profesores desde un archivo Excel."""
        try:
            # Diálogo para seleccionar archivo Excel
            archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo Excel de profesores",
                "",
                "Archivos Excel (*.xlsx *.xls)",
            )

            if not archivo:
                return  # Usuario canceló

            # Importar con indicador de progreso
            def tarea_importacion(progress_callback):
                return importar_profesores_desde_excel(
                    self.session,
                    archivo,
                    skip_rows=9,
                    progress_callback=progress_callback,
                )

            resultados, cancelado = ejecutar_con_progreso(
                self,  # parent
                tarea_importacion,  # funcion
                titulo="Importando Profesores",
                mensaje="Preparando importación...",
            )

            if cancelado:
                self.resultado_text.setText("⚠️ Importación cancelada por el usuario")
                return

            # Mostrar resultados
            mensaje = (
                f"✅ Importación completada\n\n"
                f"Archivo: {resultados['archivo']}\n"
                f"Profesores leídos: {resultados['leidos']}\n"
                f"✅ Nuevos importados: {resultados['importados']}\n"
                f"⏭️  Ya existentes: {resultados['existentes']}\n"
                f"❌ Errores: {resultados['errores']}\n"
            )

            self.resultado_text.setText(mensaje)

            if resultados["importados"] > 0:
                self.mostrar_exito(
                    "Profesores importados",
                    f"Se importaron {resultados['importados']} profesores correctamente.",
                )
                # Emitir señal de profesores importados
                self.profesores_importados.emit()
            elif resultados["existentes"] > 0:
                self.mostrar_informacion(
                    "Sin cambios",
                    f"Todos los profesores ({resultados['existentes']}) "
                    f"ya existían en la base de datos.",
                )

        except Exception as e:
            self.manejar_excepcion(e, "importar profesores desde Excel")
            self.resultado_text.setText(f"❌ Error al importar profesores: {e}")
