"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y profesores desde Excel.
"""

import ui_styles as styles
from infrastructure.database.models import Configuracion, Profesor, Zona
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
from services.exportador import ExportadorDatos
from services.importador_profesores import importar_profesores_desde_excel
from utils import get_logger

from presentation.forms.base_form import BaseForm
from presentation.forms.import_export_widgets import JsonOperationsWidget
from presentation.themes.ccleaner_theme import TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso

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
    def exportar_btn(self):
        """Compatibilidad: acceso al botón de exportar."""
        return self.json_widget.exportar_btn

    @property
    def importar_btn(self):
        """Compatibilidad: acceso al botón de importar."""
        return self.json_widget.importar_btn

    @property
    def exportar_pdf_btn(self):
        """Compatibilidad: acceso al botón de exportar PDF (no existe, retorna None)."""
        # El formulario actual no tiene botón de exportar PDF directamente
        # Se dejó para compatibilidad con tests
        return getattr(self, "_exportar_pdf_btn", None)

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
            "Puedes exportar/importar datos en formato JSON o importar profesores "
            "desde archivos Excel."
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

        # Columna derecha: Importar profesores
        columna_der = QVBoxLayout()
        columna_der.addWidget(self._crear_seccion_importar_profesores())
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
            from infrastructure.database.models import CursoEscolar
            from sync.sync_manager import UserAuth

            prof_count = self.session.query(Profesor).count()
            zona_count = self.session.query(Zona).count()
            config_count = self.session.query(Configuracion).count()
            curso_count = self.session.query(CursoEscolar).count()

            # Contar usuarios
            try:
                user_auth = UserAuth()
                usuario_count = len(user_auth.users)
            except Exception:
                usuario_count = 0

            mensaje = (
                f"✅ Datos exportados exitosamente a:\n{archivo}\n\n"
                f"Datos exportados:\n"
                f"• Profesores: {prof_count}\n"
                f"• Zonas: {zona_count}\n"
                f"• Configuración: {config_count}\n"
                f"• Usuarios (Perfiles): {usuario_count}\n"
                f"• Cursos Escolares: {curso_count}\n"
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
                from utils.ui_helpers import MESSAGEBOX_STYLE, get_corporate_icon

                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setWindowTitle("Confirmar importación")
                msg.setWindowIcon(get_corporate_icon())
                msg.setWindowFlags(
                    Qt.WindowType.Dialog
                    | Qt.WindowType.CustomizeWindowHint
                    | Qt.WindowType.WindowTitleHint
                )
                msg.setText(
                    "⚠️ ATENCIÓN: Se eliminarán TODOS los datos actuales.\n\n"
                    "¿Está seguro de que desea continuar?"
                )
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                msg.setDefaultButton(QMessageBox.StandardButton.No)
                msg.setStyleSheet(MESSAGEBOX_STYLE)

                if msg.exec() != QMessageBox.StandardButton.Yes:
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
                f"• Ausencias: {resultado.get('ausencias', 0)}\n"
                f"• Usuarios (Perfiles): {resultado.get('usuarios', 0)}\n"
                f"• Cursos Escolares: {resultado.get('cursos_escolares', 0)}\n"
            )

            # Añadir info de SMTP y SFTP si se importaron
            if resultado.get("smtp_config", 0) > 0:
                mensaje += "• Configuración SMTP: ✅ Actualizada\n"
            if resultado.get("sftp_config", 0) > 0:
                mensaje += "• Configuración SFTP: ✅ Actualizada\n"

            self.resultado_text.setText(mensaje)

            # Emitir señales de datos importados
            if resultado.get("profesores", 0) > 0:
                self.profesores_importados.emit()
            if resultado.get("zonas", 0) > 0:
                self.zonas_importadas.emit()

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Éxito")
            msg.setWindowFlags(
                Qt.WindowType.Dialog
                | Qt.WindowType.CustomizeWindowHint
                | Qt.WindowType.WindowTitleHint
            )
            msg.setText(
                "✅ Datos importados correctamente.\n\n"
                "Las tablas de profesores y zonas se han actualizado automáticamente."
            )
            msg.setStyleSheet(self.parent().styleSheet() if self.parent() else "")
            msg.exec()

        except Exception as e:
            self.manejar_excepcion(e, "importar datos")
            self.resultado_text.setText(f"❌ Error al importar: {e}")

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
