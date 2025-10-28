"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y generar calendarios PDF para profesores.
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
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
from models.models import Configuracion, Profesor, Zona
from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import ERROR_RED, TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from services.importador_profesores import importar_profesores_desde_excel


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
        desc.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            padding: 10px;
            font-size: 12px;
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(desc)

        # Layout en 2 columnas para las secciones principales
        layout_columnas = QHBoxLayout()
        layout_columnas.setSpacing(15)

        # Columna izquierda: Exportar e Importar JSON
        columna_izq = QVBoxLayout()
        columna_izq.addWidget(self._crear_seccion_exportar())
        columna_izq.addWidget(self._crear_seccion_importar())
        columna_izq.addStretch()
        layout_columnas.addLayout(columna_izq, 1)

        # Columna derecha: Importar profesores y PDF
        columna_der = QVBoxLayout()
        columna_der.addWidget(self._crear_seccion_importar_profesores())
        columna_der.addWidget(self._crear_seccion_pdf())
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

    def _crear_seccion_exportar(self) -> QGroupBox:
        """Crear sección de exportación a JSON."""
        grupo = QGroupBox("📤 EXPORTAR DATOS A JSON")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "Exporta todos los datos actuales a un archivo JSON para respaldo "
            "o transferencia a otro equipo."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """)
        layout.addWidget(info)

        self.exportar_btn = QPushButton("💾 Exportar a JSON...")
        self.exportar_btn.clicked.connect(self.exportar_datos)
        self.exportar_btn.setMinimumHeight(40)
        self.exportar_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        layout.addWidget(self.exportar_btn)

        grupo.setLayout(layout)
        return grupo

    def _crear_seccion_importar(self) -> QGroupBox:
        """Crear sección de importación desde JSON."""
        grupo = QGroupBox("📥 IMPORTAR DATOS DESDE JSON")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "⚠️ ATENCIÓN: Esto puede ELIMINAR los datos actuales si activas la opción."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            color: {ERROR_RED};
            font-size: 11px;
            font-weight: bold;
            padding: 5px;
        """)
        layout.addWidget(info)

        self.limpiar_checkbox = QCheckBox(
            "Eliminar datos existentes antes de importar"
        )
        self.limpiar_checkbox.setChecked(True)
        self.limpiar_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                font-weight: normal;
                color: {TEXT_SECONDARY};
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
            }}
        """)
        layout.addWidget(self.limpiar_checkbox)

        self.importar_btn = QPushButton("📂 Importar desde JSON...")
        self.importar_btn.clicked.connect(self.importar_datos)
        self.importar_btn.setMinimumHeight(40)
        self.importar_btn.setStyleSheet(styles.STYLE_BUTTON_WARNING)
        layout.addWidget(self.importar_btn)

        grupo.setLayout(layout)
        return grupo

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
        info.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """)
        layout.addWidget(info)

        self.importar_profesores_btn = QPushButton("👥 Importar Profesores...")
        self.importar_profesores_btn.clicked.connect(self.importar_profesores)
        self.importar_profesores_btn.setMinimumHeight(40)
        self.importar_profesores_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        layout.addWidget(self.importar_profesores_btn)

        grupo.setLayout(layout)
        return grupo

    def _crear_seccion_pdf(self) -> QGroupBox:
        """Crear sección de exportación a PDF."""
        grupo = QGroupBox("📄 GENERAR CALENDARIOS PDF")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "Genera calendarios individuales en PDF para cada profesor "
            "con sus guardias asignadas."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """)
        layout.addWidget(info)

        # Controles de mes/año en layout horizontal
        fecha_layout = QHBoxLayout()
        fecha_layout.setSpacing(10)

        # Mes
        mes_container = QVBoxLayout()
        mes_container.setSpacing(5)
        mes_label = QLabel("📅 Mes:")
        mes_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        mes_container.addWidget(mes_label)

        self.pdf_mes_combo = QComboBox()
        meses = [
            "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
            "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
        ]
        self.pdf_mes_combo.addItems(meses)
        self.pdf_mes_combo.setCurrentIndex(datetime.now().month - 1)
        self.pdf_mes_combo.setStyleSheet(styles.STYLE_INPUT)
        mes_container.addWidget(self.pdf_mes_combo)
        fecha_layout.addLayout(mes_container, 2)

        # Año
        anio_container = QVBoxLayout()
        anio_container.setSpacing(5)
        anio_label = QLabel("📆 Año:")
        anio_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        anio_container.addWidget(anio_label)

        self.pdf_anio_combo = QComboBox()
        anio_actual = datetime.now().year
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_anio_combo.addItem(str(anio))
        self.pdf_anio_combo.setCurrentIndex(1)  # Año actual
        self.pdf_anio_combo.setStyleSheet(styles.STYLE_INPUT)
        anio_container.addWidget(self.pdf_anio_combo)
        fecha_layout.addLayout(anio_container, 1)

        layout.addLayout(fecha_layout)

        # Botón de exportación
        self.exportar_pdf_btn = QPushButton("📄 Generar PDFs para Todos")
        self.exportar_pdf_btn.clicked.connect(self.exportar_pdfs)
        self.exportar_pdf_btn.setMinimumHeight(40)
        self.exportar_pdf_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        layout.addWidget(self.exportar_pdf_btn)

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
            if resultado.get('smtp_config', 0) > 0:
                mensaje += "• Configuración SMTP: ✅ Actualizada\n"
            if resultado.get('sftp_config', 0) > 0:
                mensaje += "• Configuración SFTP: ✅ Actualizada\n"

            self.resultado_text.setText(mensaje)

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Éxito")
            msg.setWindowFlags(
                Qt.WindowType.Dialog | Qt.WindowType.CustomizeWindowHint |
                Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                "Datos importados correctamente.\n\n"
                "Se recomienda reiniciar la aplicación para ver los cambios."
            )
            msg.exec()

            # Emitir señales de datos importados
            if resultado.get('profesores', 0) > 0:
                self.profesores_importados.emit()
            if resultado.get('zonas', 0) > 0:
                self.zonas_importadas.emit()

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
