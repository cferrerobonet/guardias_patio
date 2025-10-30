"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y generar calendarios PDF para profesores.
"""

from datetime import datetime

import ui_styles as styles
from models.models import Configuracion, Profesor, Zona
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from services.importador_profesores import importar_profesores_desde_excel

from presentation.forms.base_form import BaseForm
from presentation.themes.ccleaner_theme import ERROR_RED, TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso


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
        """Crear sección de exportación a PDF con opciones avanzadas."""
        grupo = QGroupBox("📄 GENERAR CALENDARIOS PDF")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)

        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "Genera calendarios individuales en PDF para profesores "
            "con sus guardias asignadas."
        )
        info.setWordWrap(True)
        info.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 11px;
            font-weight: normal;
        """)
        layout.addWidget(info)

        # Tipo de exportación
        tipo_layout = QVBoxLayout()
        tipo_layout.setSpacing(5)
        tipo_label = QLabel("📋 Tipo de exportación:")
        tipo_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        tipo_layout.addWidget(tipo_label)

        self.pdf_tipo_combo = QComboBox()
        self.pdf_tipo_combo.addItem(
            "📅 Mes específico - Todos los profesores", "mes_todos"
        )
        self.pdf_tipo_combo.addItem(
            "👤 Mes específico - Profesores seleccionados", "mes_seleccionados"
        )
        self.pdf_tipo_combo.addItem(
            "📚 Curso completo - Todos los profesores", "curso_todos"
        )
        self.pdf_tipo_combo.addItem(
            "📚 Curso completo - Profesores seleccionados", "curso_seleccionados"
        )
        self.pdf_tipo_combo.currentIndexChanged.connect(self._on_tipo_pdf_changed)
        self.pdf_tipo_combo.setStyleSheet(styles.STYLE_INPUT)
        tipo_layout.addWidget(self.pdf_tipo_combo)
        layout.addLayout(tipo_layout)

        # Controles de mes/año (para opciones mensuales)
        self.fecha_container = QWidget()
        fecha_layout = QHBoxLayout(self.fecha_container)
        fecha_layout.setContentsMargins(0, 0, 0, 0)
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

        layout.addWidget(self.fecha_container)

        # Año de inicio del curso (para opciones de curso completo)
        self.curso_container = QWidget()
        curso_layout = QVBoxLayout(self.curso_container)
        curso_layout.setContentsMargins(0, 0, 0, 0)
        curso_layout.setSpacing(5)

        curso_label = QLabel("📚 Año de inicio del curso:")
        curso_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        curso_layout.addWidget(curso_label)

        self.pdf_curso_combo = QComboBox()
        for anio in range(anio_actual - 1, anio_actual + 3):
            self.pdf_curso_combo.addItem(f"{anio}/{anio + 1}", anio)
        self.pdf_curso_combo.setCurrentIndex(1)
        self.pdf_curso_combo.setStyleSheet(styles.STYLE_INPUT)
        curso_layout.addWidget(self.pdf_curso_combo)

        curso_info = QLabel(
            "ℹ️ Se generarán PDFs de Septiembre a Junio"
        )
        curso_info.setStyleSheet(f"""
            color: {TEXT_SECONDARY};
            font-size: 10px;
            font-style: italic;
        """)
        curso_layout.addWidget(curso_info)

        layout.addWidget(self.curso_container)
        self.curso_container.hide()  # Oculto por defecto

        # Lista de selección de profesores (para opciones con selección)
        self.profesores_container = QWidget()
        profesores_layout = QVBoxLayout(self.profesores_container)
        profesores_layout.setContentsMargins(0, 0, 0, 0)
        profesores_layout.setSpacing(5)

        prof_label = QLabel("👥 Seleccionar profesores:")
        prof_label.setStyleSheet(styles.STYLE_LABEL_FIELD)
        profesores_layout.addWidget(prof_label)

        # Scroll area para checkboxes de profesores
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: white;
            }
        """)

        scroll_widget = QWidget()
        self.profesores_checks_layout = QVBoxLayout(scroll_widget)
        self.profesores_checks_layout.setSpacing(5)
        self.profesores_checks_layout.setContentsMargins(10, 10, 10, 10)

        # Checkbox "Seleccionar todos"
        self.seleccionar_todos_check = QCheckBox("✅ Seleccionar todos")
        self.seleccionar_todos_check.setChecked(True)
        self.seleccionar_todos_check.stateChanged.connect(self._on_seleccionar_todos_changed)
        self.seleccionar_todos_check.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #1976D2;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
        """)
        self.profesores_checks_layout.addWidget(self.seleccionar_todos_check)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ccc; max-height: 1px;")
        self.profesores_checks_layout.addWidget(separator)

        # Lista dinámica de checkboxes de profesores
        self.profesor_checkboxes = []
        self._cargar_profesores_checkboxes()

        scroll_area.setWidget(scroll_widget)
        profesores_layout.addWidget(scroll_area)

        layout.addWidget(self.profesores_container)
        self.profesores_container.hide()  # Oculto por defecto

        # Botón de exportación
        self.exportar_pdf_btn = QPushButton("📄 Generar PDFs")
        self.exportar_pdf_btn.clicked.connect(self.exportar_pdfs)
        self.exportar_pdf_btn.setMinimumHeight(40)
        self.exportar_pdf_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        layout.addWidget(self.exportar_pdf_btn)

        grupo.setLayout(layout)
        return grupo

    def _cargar_profesores_checkboxes(self):
        """Cargar checkboxes de profesores desde la base de datos."""
        try:
            # Limpiar checkboxes anteriores
            for checkbox in self.profesor_checkboxes:
                checkbox.deleteLater()
            self.profesor_checkboxes.clear()

            # Obtener profesores
            profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()

            for profesor in profesores:
                checkbox = QCheckBox(f"{profesor.nombre_completo} ({profesor.turno})")
                checkbox.setChecked(True)  # Seleccionados por defecto
                checkbox.setProperty("profesor_id", profesor.id)
                checkbox.setStyleSheet("""
                    QCheckBox {
                        font-size: 11px;
                    }
                    QCheckBox::indicator {
                        width: 16px;
                        height: 16px;
                    }
                """)
                checkbox.stateChanged.connect(self._on_profesor_checkbox_changed)
                self.profesores_checks_layout.addWidget(checkbox)
                self.profesor_checkboxes.append(checkbox)

        except Exception as e:
            self.manejar_excepcion(e, "cargar lista de profesores")

    def _on_tipo_pdf_changed(self):
        """Manejar cambio en el tipo de exportación PDF."""
        tipo = self.pdf_tipo_combo.currentData()

        # Mostrar/ocultar controles según el tipo
        if tipo in ["mes_todos", "mes_seleccionados"]:
            self.fecha_container.show()
            self.curso_container.hide()
        else:  # curso_todos, curso_seleccionados
            self.fecha_container.hide()
            self.curso_container.show()

        if tipo in ["mes_seleccionados", "curso_seleccionados"]:
            self.profesores_container.show()
        else:
            self.profesores_container.hide()

        # Actualizar texto del botón
        if tipo == "mes_todos":
            self.exportar_pdf_btn.setText("📄 Generar PDFs para Todos (Mes)")
        elif tipo == "mes_seleccionados":
            self.exportar_pdf_btn.setText("📄 Generar PDFs Seleccionados (Mes)")
        elif tipo == "curso_todos":
            self.exportar_pdf_btn.setText("📚 Generar PDF Curso Completo (Todos)")
        else:  # curso_seleccionados
            self.exportar_pdf_btn.setText("📚 Generar PDF Curso Completo (Seleccionados)")

    def _on_seleccionar_todos_changed(self, state):
        """Manejar cambio en el checkbox de seleccionar todos."""
        seleccionado = (state == Qt.CheckState.Checked)
        for checkbox in self.profesor_checkboxes:
            checkbox.setChecked(seleccionado)

    def _on_profesor_checkbox_changed(self):
        """Manejar cambio en checkbox individual de profesor."""
        # Actualizar estado de "Seleccionar todos"
        todos_seleccionados = all(cb.isChecked() for cb in self.profesor_checkboxes)
        alguno_deseleccionado = any(not cb.isChecked() for cb in self.profesor_checkboxes)

        if todos_seleccionados:
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.Checked)
        elif alguno_deseleccionado:
            self.seleccionar_todos_check.setCheckState(Qt.CheckState.PartiallyChecked)

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
        """Exportar calendarios PDF según el tipo seleccionado."""
        try:
            tipo = self.pdf_tipo_combo.currentData()

            # Diálogo para seleccionar carpeta de destino
            carpeta = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar carpeta para guardar PDFs",
                "",
                QFileDialog.Option.ShowDirsOnly,
            )

            if not carpeta:
                return  # Usuario canceló

            # Obtener profesores seleccionados si es necesario
            profesor_ids_seleccionados = None
            if tipo in ["mes_seleccionados", "curso_seleccionados"]:
                profesor_ids_seleccionados = [
                    cb.property("profesor_id")
                    for cb in self.profesor_checkboxes
                    if cb.isChecked()
                ]

                if not profesor_ids_seleccionados:
                    self.mostrar_advertencia(
                        "Sin selección",
                        "Debes seleccionar al menos un profesor para exportar."
                    )
                    return

            # Ejecutar según el tipo
            if tipo == "mes_todos":
                self._exportar_mes_todos(carpeta)
            elif tipo == "mes_seleccionados":
                self._exportar_mes_seleccionados(carpeta, profesor_ids_seleccionados)
            elif tipo == "curso_todos":
                self._exportar_curso_todos(carpeta)
            elif tipo == "curso_seleccionados":
                self._exportar_curso_seleccionados(carpeta, profesor_ids_seleccionados)

        except Exception as e:
            self.manejar_excepcion(e, "generar PDFs")
            self.resultado_text.setText(f"❌ Error al generar PDFs: {e}")

    def _exportar_mes_todos(self, carpeta: str):
        """Exportar mes específico para todos los profesores."""
        mes = self.pdf_mes_combo.currentIndex() + 1
        anio = int(self.pdf_anio_combo.currentText())

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_todos_los_profesores(
                self.session, mes, anio, carpeta, progress_callback=progress_callback
            )

        exitos, cancelado = ejecutar_con_progreso(
            tarea_exportacion,
            titulo="Exportando PDFs - Mes completo",
            mensaje="Preparando exportación...",
            padre=self,
            cancelable=False,
        )

        if not cancelado:
            meses_nombres = [
                "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]

            mensaje = (
                f"✅ PDFs generados exitosamente\n\n"
                f"Tipo: Mes completo (todos los profesores)\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {exitos}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados",
                f"Se generaron {exitos} calendarios PDF correctamente."
            )

    def _exportar_mes_seleccionados(self, carpeta: str, profesor_ids: list[int]):
        """Exportar mes específico solo para profesores seleccionados."""
        mes = self.pdf_mes_combo.currentIndex() + 1
        anio = int(self.pdf_anio_combo.currentText())

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_profesores_seleccionados(
                self.session, profesor_ids, mes, anio, carpeta,
                progress_callback=progress_callback
            )

        exitos, cancelado = ejecutar_con_progreso(
            tarea_exportacion,
            titulo="Exportando PDFs - Profesores seleccionados",
            mensaje="Preparando exportación...",
            padre=self,
            cancelable=False,
        )

        if not cancelado:
            meses_nombres = [
                "", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]

            mensaje = (
                f"✅ PDFs generados exitosamente\n\n"
                f"Tipo: Profesores seleccionados\n"
                f"Mes: {meses_nombres[mes]} {anio}\n"
                f"Profesores: {len(profesor_ids)}\n"
                f"Carpeta: {carpeta}\n"
                f"PDFs generados: {exitos}\n"
            )

            self.resultado_text.setText(mensaje)
            self.mostrar_exito(
                "PDFs generados",
                f"Se generaron {exitos} calendarios PDF correctamente."
            )

    def _exportar_curso_todos(self, carpeta: str):
        """Exportar curso completo para todos los profesores."""
        anio_inicio = self.pdf_curso_combo.currentData()

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_curso_completo(
                self.session, anio_inicio, carpeta,
                profesor_ids=None,  # Todos los profesores
                progress_callback=progress_callback
            )

        exito, cancelado = ejecutar_con_progreso(
            tarea_exportacion,
            titulo="Exportando PDF - Curso completo",
            mensaje="Generando curso escolar completo...",
            padre=self,
            cancelable=False,
        )

        if not cancelado:
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
                f"Se generó el calendario del curso {anio_inicio}/{anio_inicio + 1} correctamente."
            )

    def _exportar_curso_seleccionados(self, carpeta: str, profesor_ids: list[int]):
        """Exportar curso completo solo para profesores seleccionados."""
        anio_inicio = self.pdf_curso_combo.currentData()

        def tarea_exportacion(progress_callback):
            return ExportadorPDF.exportar_curso_completo(
                self.session, anio_inicio, carpeta,
                profesor_ids=profesor_ids,
                progress_callback=progress_callback
            )

        exito, cancelado = ejecutar_con_progreso(
            tarea_exportacion,
            titulo="Exportando PDF - Curso seleccionado",
            mensaje="Generando curso escolar para profesores seleccionados...",
            padre=self,
            cancelable=False,
        )

        if not cancelado:
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
                f"Se generó el calendario del curso {anio_inicio}/{anio_inicio + 1} correctamente."
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
