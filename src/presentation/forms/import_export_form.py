"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y generar calendarios PDF para profesores.
"""

from datetime import datetime

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

import ui_styles as styles
from models.models import Configuracion, Profesor, Zona
from presentation.forms.base_form import BaseForm
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from services.importador_profesores import importar_profesores_desde_excel


class ImportExportForm(BaseForm):
    """Formulario para importar/exportar datos."""

    def __init__(self, session):
        """
        Inicializar formulario de importación/exportación.

        Args:
            session: Sesión de base de datos
        """
        super().__init__(session)
        self.setup_ui()

    def setup_ui(self):
        """Construir la interfaz del formulario."""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Importar / Exportar Datos")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(titulo)

        # Descripción
        desc = QLabel(
            "Exporta todos los datos de la aplicación (profesores, zonas, "
            "configuración, guardias)\n"
            "a un archivo JSON para copiar a otro equipo o hacer respaldo.\n\n"
            "También puedes importar datos desde un archivo JSON exportado previamente."
        )
        layout.addWidget(desc)

        # Sección de exportación
        layout.addLayout(self._crear_seccion_exportar())

        # Sección de importación
        layout.addLayout(self._crear_seccion_importar())

        # Sección de importación de profesores desde Excel
        layout.addLayout(self._crear_seccion_importar_profesores())

        # Sección de exportación a PDF
        layout.addLayout(self._crear_seccion_pdf())

        # Resultado
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(200)
        layout.addWidget(self.resultado_text)

        layout.addStretch()
        self.setLayout(layout)

    def _crear_seccion_exportar(self) -> QVBoxLayout:
        """Crear sección de exportación a JSON."""
        seccion = QVBoxLayout()

        export_label = QLabel("EXPORTAR DATOS")
        export_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        seccion.addWidget(export_label)

        export_info = QLabel(
            "Exporta todos los datos actuales de la base de datos a un archivo JSON."
        )
        seccion.addWidget(export_info)

        self.exportar_btn = QPushButton("Exportar a JSON...")
        self.exportar_btn.clicked.connect(self.exportar_datos)
        seccion.addWidget(self.exportar_btn)

        return seccion

    def _crear_seccion_importar(self) -> QVBoxLayout:
        """Crear sección de importación desde JSON."""
        seccion = QVBoxLayout()

        import_label = QLabel("IMPORTAR DATOS")
        import_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        seccion.addWidget(import_label)

        import_info = QLabel(
            "Importa datos desde un archivo JSON.\n"
            "⚠️ ATENCIÓN: Esto ELIMINARÁ todos los datos actuales y los reemplazará "
            "con los del archivo."
        )
        import_info.setStyleSheet("color: #d63031;")
        seccion.addWidget(import_info)

        self.limpiar_checkbox = QCheckBox(
            "Eliminar datos existentes antes de importar (recomendado)"
        )
        self.limpiar_checkbox.setChecked(True)
        seccion.addWidget(self.limpiar_checkbox)

        self.importar_btn = QPushButton("Importar desde JSON...")
        self.importar_btn.clicked.connect(self.importar_datos)
        seccion.addWidget(self.importar_btn)

        return seccion

    def _crear_seccion_importar_profesores(self) -> QVBoxLayout:
        """Crear sección de importación de profesores desde Excel."""
        seccion = QVBoxLayout()

        import_prof_label = QLabel("IMPORTAR PROFESORES DESDE EXCEL")
        import_prof_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        seccion.addWidget(import_prof_label)

        import_prof_info = QLabel(
            "Importa profesores desde un archivo Excel (.xlsx).\n"
            "Los profesores nuevos se añadirán, los existentes se omitirán."
        )
        seccion.addWidget(import_prof_info)

        self.importar_profesores_btn = QPushButton("Importar Profesores desde Excel...")
        self.importar_profesores_btn.clicked.connect(self.importar_profesores)
        seccion.addWidget(self.importar_profesores_btn)

        return seccion

    def _crear_seccion_pdf(self) -> QVBoxLayout:
        """Crear sección de exportación a PDF."""
        seccion = QVBoxLayout()

        pdf_label = QLabel("EXPORTAR A PDF")
        pdf_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
        seccion.addWidget(pdf_label)

        pdf_info = QLabel(
            "Genera calendarios individuales en PDF para cada profesor con sus guardias."
        )
        seccion.addWidget(pdf_info)

        # Controles de mes/año
        pdf_form_layout = QHBoxLayout()

        pdf_mes_label = QLabel("Mes:")
        pdf_mes_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        pdf_form_layout.addWidget(pdf_mes_label)

        self.pdf_mes_combo = QComboBox()
        meses = [
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
        self.pdf_mes_combo.addItems(meses)
        self.pdf_mes_combo.setCurrentIndex(datetime.now().month - 1)
        pdf_form_layout.addWidget(self.pdf_mes_combo)

        pdf_anio_label = QLabel("Año:")
        pdf_anio_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        pdf_form_layout.addWidget(pdf_anio_label)

        self.pdf_anio_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_anio_combo.addItem(str(anio))
        self.pdf_anio_combo.setCurrentIndex(1)  # Año actual
        pdf_form_layout.addWidget(self.pdf_anio_combo)

        seccion.addLayout(pdf_form_layout)

        # Botón de exportación
        self.exportar_pdf_btn = QPushButton("📄 Generar PDFs para todos los profesores...")
        self.exportar_pdf_btn.clicked.connect(self.exportar_pdfs)
        self.exportar_pdf_btn.setStyleSheet(
            """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            """
        )
        seccion.addWidget(self.exportar_pdf_btn)

        return seccion

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

            self.resultado_text.setText(mensaje)
            QMessageBox.information(
                self,
                "Éxito",
                "Datos importados correctamente.\n\n"
                "Se recomienda reiniciar la aplicación para ver los cambios.",
            )

        except Exception as e:
            self.manejar_excepcion(e, "importar datos")
            self.resultado_text.setText(f"❌ Error al importar: {e}")

    def exportar_pdfs(self):
        """Exportar calendarios PDF para todos los profesores."""
        try:
            # Obtener mes y año seleccionados
            mes = self.pdf_mes_combo.currentIndex() + 1
            anio = int(self.pdf_anio_combo.currentText())

            # Diálogo para seleccionar carpeta de destino
            carpeta = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta para guardar PDFs",
                "",
                QFileDialog.Option.ShowDirsOnly,
            )

            if not carpeta:
                return  # Usuario canceló

            # Generar PDFs con indicador de progreso
            def tarea_exportacion(progress_callback):
                return ExportadorPDF.exportar_todos_los_profesores(
                    self.session, mes, anio, carpeta, progress_callback=progress_callback
                )

            exitos, cancelado = ejecutar_con_progreso(
                tarea_exportacion,
                titulo="Exportando PDFs",
                mensaje="Preparando exportación...",
                padre=self,
                cancelable=False,
            )

            if cancelado:
                return

            meses = [
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
                f"Mes: {meses[mes]} {anio}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {exitos}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados", f"Se generaron {exitos} calendarios PDF correctamente."
            )

        except Exception as e:
            self.manejar_excepcion(e, "generar PDFs")
            self.resultado_text.setText(f"❌ Error al generar PDFs: {e}")

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
                tarea_importacion,
                titulo="Importando Profesores",
                mensaje="Preparando importación...",
                padre=self,
                cancelable=True,  # Permitir cancelar si hay muchos registros
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
            elif resultados["existentes"] > 0:
                self.mostrar_informacion(
                    "Sin cambios",
                    f"Todos los profesores ({resultados['existentes']}) "
                    f"ya existían en la base de datos.",
                )

        except Exception as e:
            self.manejar_excepcion(e, "importar profesores desde Excel")
            self.resultado_text.setText(f"❌ Error al importar profesores: {e}")
