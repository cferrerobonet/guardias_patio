"""
Formulario para importar/exportar datos de la aplicación.

Este módulo implementa la UI para exportar/importar datos en JSON
y profesores desde Excel.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from infrastructure.repositories.repository_factory import RepositoryFactory
from presentation.dialogs.column_mapping_dialog import ColumnMappingDialog
from presentation.forms.base_form import BaseForm
from presentation.forms.import_export_widgets import JsonOperationsWidget
from presentation.theme.tokens import Spacing
from presentation.themes.ccleaner_theme import TEXT_SECONDARY
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from services.exportador import ExportadorDatos
from services.importador_profesores import importar_profesores
from utils import get_logger
from utils.icons import icon_for_button

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
        main_layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        main_layout.setSpacing(15)

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
        columna_der.addWidget(self._crear_seccion_copias())
        columna_der.addStretch()
        layout_columnas.addLayout(columna_der, 1)

        main_layout.addLayout(layout_columnas)

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

    def _crear_seccion_importar_profesores(self) -> QGroupBox:
        """Crear sección de importación de profesores desde Excel."""
        grupo = QGroupBox("IMPORTAR PROFESORES DESDE EXCEL")

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
            font-size: 12px;
            font-weight: normal;
        """
        )
        layout.addWidget(info)

        self.importar_profesores_btn = QPushButton("Importar Profesores...")
        self.importar_profesores_btn.setIcon(icon_for_button("import"))
        self.importar_profesores_btn.clicked.connect(self.importar_profesores)
        self.importar_profesores_btn.setMinimumHeight(40)
        self.importar_profesores_btn.setProperty("warning", "true")
        layout.addWidget(self.importar_profesores_btn)

        grupo.setLayout(layout)
        return grupo

    def _crear_seccion_copias(self) -> QGroupBox:
        """Sección para volver a un estado anterior (FUN-004)."""
        grupo = QGroupBox("VOLVER A UN ESTADO ANTERIOR")

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)

        info = QLabel(
            "La aplicación guarda una copia antes de generar o limpiar las guardias. "
            "Si algo sale mal, puedes volver a como estaba."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            f"""
            color: {TEXT_SECONDARY};
            font-size: 12px;
            font-weight: normal;
        """
        )
        layout.addWidget(info)

        self.restaurar_btn = QPushButton("Ver copias de seguridad...")
        self.restaurar_btn.setIcon(icon_for_button("restore"))
        self.restaurar_btn.clicked.connect(self.restaurar_copia)
        self.restaurar_btn.setMinimumHeight(40)
        self.restaurar_btn.setAccessibleName("Ver y restaurar copias de seguridad")
        layout.addWidget(self.restaurar_btn)

        grupo.setLayout(layout)
        return grupo

    def restaurar_copia(self):
        """Muestra las copias disponibles y restaura la elegida."""
        from database.db_manager import get_current_user_id, listar_backups, restore_database

        usuario = get_current_user_id()
        copias = listar_backups(usuario) if usuario else []

        if not copias:
            self.mostrar_advertencia(
                "Sin copias",
                "Todavía no hay ninguna copia de seguridad.\n\n"
                "Se crea una automáticamente antes de generar o limpiar las guardias.",
            )
            return

        etiquetas = [
            f"{c['momento'].strftime('%d/%m/%Y a las %H:%M')}  ({c['tamano'] // 1024} KB)"
            for c in copias
        ]
        elegida, aceptado = QInputDialog.getItem(
            self,
            "Volver a un estado anterior",
            "Elige el momento al que quieres volver:",
            etiquetas,
            0,
            False,
        )
        if not aceptado:
            return

        copia = copias[etiquetas.index(elegida)]

        confirmacion = QMessageBox(self)
        confirmacion.setIcon(QMessageBox.Icon.Warning)
        confirmacion.setWindowTitle("Confirmar restauración")
        confirmacion.setText(f"Se volverá al estado del {elegida.split('  (')[0]}.")
        confirmacion.setInformativeText(
            "Todo lo hecho después de ese momento se perderá.\n\n"
            "Se guarda una copia del estado actual antes de restaurar, por si acaso.\n"
            "Al terminar hay que cerrar y volver a abrir la aplicación."
        )
        confirmacion.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        confirmacion.setDefaultButton(QMessageBox.StandardButton.No)
        if confirmacion.exec() != QMessageBox.StandardButton.Yes:
            return

        if restore_database(usuario, copia["ruta"]):
            self.resultado_text.setText(
                f"✅ Restaurado el estado del {elegida.split('  (')[0]}.\n\n"
                "Cierra y vuelve a abrir la aplicación para ver los datos restaurados."
            )
            self.mostrar_exito(
                "Restaurado",
                "Cierra y vuelve a abrir la aplicación para ver los datos restaurados.",
            )
        else:
            self.mostrar_error(
                "No se pudo restaurar",
                "Revisa el registro de la aplicación para ver el motivo.",
            )

    def exportar_datos(self):
        """Exportar todos los datos a archivo JSON."""
        try:
            # Diálogo para seleccionar archivo de destino
            from pathlib import Path

            from utils.ui_helpers import recordar_carpeta, ultima_carpeta

            nombre = "guardias_patio_export.json"
            carpeta_previa = ultima_carpeta()
            propuesta = str(Path(carpeta_previa) / nombre) if carpeta_previa else nombre
            archivo, _ = QFileDialog.getSaveFileName(
                self,
                "Exportar datos",
                propuesta,
                "Archivos JSON (*.json)",
            )

            if not archivo:
                return  # Usuario canceló
            recordar_carpeta(archivo)

            # Exportar datos
            ExportadorDatos.exportar_todo(self.session, archivo)

            # Mostrar resumen
            from application.app_services import AppServices
            from sync.sync_manager import UserAuth

            _svc = AppServices(self.session)
            prof_count = _svc.contar_profesores()
            zona_count = _svc.contar_zonas()
            config_count = _svc.contar_configuraciones()
            curso_count = _svc.contar_cursos()

            # Contar usuarios
            try:
                user_auth = UserAuth()
                usuario_count = len(user_auth.users)
            except (ValueError, TypeError, OSError):
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
            self.resultado_text.setText(f"Error al exportar: {e}")

    def importar_datos(self):
        """Importar datos desde archivo JSON."""
        try:
            # Confirmación previa
            limpiar = self.limpiar_checkbox.isChecked()
            if limpiar:
                from utils.ui_helpers import get_corporate_icon

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

                if msg.exec() != QMessageBox.StandardButton.Yes:
                    return

            # Diálogo para seleccionar archivo
            archivo, _ = QFileDialog.getOpenFileName(
                self, "Importar datos", "", "Archivos JSON (*.json)"
            )

            if not archivo:
                return  # Usuario canceló

            # Validar estructura del JSON antes de importar
            import json as _json
            try:
                with open(archivo, encoding="utf-8") as _f:
                    datos_preview = _json.load(_f)
            except _json.JSONDecodeError as je:
                self.mostrar_error(
                    "JSON inválido",
                    f"El archivo no es un JSON válido:\n{je.msg} (línea {je.lineno}, col {je.colno})",
                )
                return
            except OSError as oe:
                self.mostrar_error("Error al leer archivo", str(oe))
                return

            if not isinstance(datos_preview, dict):
                self.mostrar_error(
                    "Formato incorrecto",
                    f"El archivo debe contener un objeto JSON, no {type(datos_preview).__name__}.",
                )
                return

            _CLAVES_ESPERADAS = {"profesores", "zonas", "configuracion", "guardias",
                                  "ausencias", "cursos_escolares", "usuarios"}
            if not (set(datos_preview.keys()) & _CLAVES_ESPERADAS):
                claves = ", ".join(sorted(datos_preview.keys())) or "(ninguna)"
                self.mostrar_error(
                    "Backup incompatible",
                    f"El archivo no contiene secciones reconocidas.\n\n"
                    f"Claves encontradas: {claves}\n"
                    f"Se esperaba al menos una de: {', '.join(sorted(_CLAVES_ESPERADAS))}",
                )
                return

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

        except (ValueError, TypeError) as e:
            self.manejar_excepcion(e, "importar datos")
            self.resultado_text.setText(f"Error al importar: {e}")

    def importar_profesores(self):
        """Importar profesores desde un archivo Excel."""
        try:
            # Diálogo para seleccionar archivo Excel
            archivo, _ = QFileDialog.getOpenFileName(
                self,
                "Seleccionar archivo de profesores",
                "",
                "Archivos compatibles (*.xlsx *.xls *.csv);;Excel (*.xlsx *.xls);;CSV (*.csv)",
            )

            if not archivo:
                return  # Usuario canceló

            # Mostrar diálogo de mapeo de columnas
            dialogo = ColumnMappingDialog(archivo, parent=self)
            if dialogo.exec() != ColumnMappingDialog.DialogCode.Accepted:
                return

            col_mapping = dialogo.mapping
            skip = dialogo.skip_rows

            # Importar con indicador de progreso
            def tarea_importacion(progress_callback):
                # Corre en el WorkerThread: sesión propia, no la de la GUI (CRW-003).
                from database.db_manager import get_db_session

                with get_db_session() as sesion:
                    factory = RepositoryFactory(sesion)
                    profesor_repo = factory.create_profesor_repository()
                    return importar_profesores(
                        profesor_repo,
                        archivo,
                        skip_rows=skip,
                        column_mapping=col_mapping,
                        progress_callback=progress_callback,
                    )

            resultados, cancelado = ejecutar_con_progreso(
                self,  # parent
                tarea_importacion,  # funcion
                titulo="Importando Profesores",
                mensaje="Preparando importación...",
            )

            if cancelado:
                self.resultado_text.setText("Importación cancelada por el usuario")
                return

            # Mostrar resultados
            mensaje = (
                f"Importación completada\n\n"
                f"Archivo: {resultados['archivo']}\n"
                f"Profesores leídos: {resultados['leidos']}\n"
                f"Nuevos importados: {resultados['importados']}\n"
                f"Ya existentes: {resultados['existentes']}\n"
                f"Errores: {resultados['errores']}\n"
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

        except (ValueError, TypeError, OSError) as e:
            self.manejar_excepcion(e, "importar profesores desde Excel")
            self.resultado_text.setText(f"Error al importar profesores: {e}")
