"""
Widget de gestión de cursos escolares para la sección de Configuración.

Permite visualizar todos los cursos y realizar operaciones de gestión.
"""

from typing import Optional

import ui_styles as styles
from core.logging import get_logger
from infrastructure.database.models import CursoEscolar, Guardia
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from services.gestor_cursos import GestorCursos
from sqlalchemy.orm import Session
from utils.icons import icon_for_button

from presentation.dialogs.dialogo_crear_curso import DialogoCrearCurso

logger = get_logger(__name__)


def _fix_messagebox_size(msgbox: QMessageBox) -> None:
    """
    Fix para QMessageBox en macOS que no muestra botones correctamente.

    Fuerza un tamaño mínimo para que los botones sean visibles.
    """
    # Programar el resize después de que el diálogo se muestre
    QTimer.singleShot(0, lambda: msgbox.setMinimumSize(400, 200))


class GestionCursosWidget(QWidget):
    """Widget para gestionar cursos escolares."""

    curso_modificado = pyqtSignal()  # Emitido cuando cambia algún curso

    def __init__(self, session: Session, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.session = session
        self._inicializar_ui()
        self._cargar_cursos()

    def showEvent(self, event):
        """Se llama cada vez que el widget se muestra."""
        super().showEvent(event)
        # Refrescar los datos cada vez que se muestra el widget
        self._cargar_cursos()

    def _inicializar_ui(self) -> None:
        """Crea la interfaz del widget."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)

        # GroupBox con estilo - Se expandirá verticalmente
        grupo = QGroupBox("Gestión de Cursos Escolares")
        grupo.setStyleSheet(styles.STYLE_GROUPBOX)
        grupo_layout = QVBoxLayout()
        grupo_layout.setSpacing(12)
        grupo_layout.setContentsMargins(20, 20, 20, 20)

        # Descripción
        descripcion = QLabel(
            "Administra los cursos escolares. Cada curso es independiente "
            "y tiene sus propias guardias y datos."
        )
        descripcion.setWordWrap(True)
        descripcion.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 5px;")
        grupo_layout.addWidget(descripcion)

        # Botones de acción con estilos consistentes - ALINEADOS A LA DERECHA
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)

        # Agregar stretch al inicio para empujar botones a la derecha
        botones_layout.addStretch()

        self.btn_crear = QPushButton("Crear Nuevo Curso")
        self.btn_crear.setIcon(icon_for_button("plus"))
        self.btn_crear.setStyleSheet(
            styles.STYLE_BUTTON_SUCCESS + "font-size: 12px; padding: 8px 16px; font-weight: bold;"
        )
        self.btn_crear.setToolTip("Crear un nuevo curso escolar")
        self.btn_crear.clicked.connect(self._crear_curso)
        botones_layout.addWidget(self.btn_crear)

        self.btn_activar = QPushButton("Activar")
        self.btn_activar.setIcon(icon_for_button("check"))
        self.btn_activar.setStyleSheet(
            styles.STYLE_BUTTON_PRIMARY + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_activar.setToolTip("Activar el curso seleccionado (incluso si está cerrado)")
        self.btn_activar.clicked.connect(self._activar_curso_seleccionado)
        self.btn_activar.setEnabled(False)
        botones_layout.addWidget(self.btn_activar)

        self.btn_cerrar = QPushButton("Cerrar")
        self.btn_cerrar.setIcon(icon_for_button("lock"))
        self.btn_cerrar.setStyleSheet(
            styles.STYLE_BUTTON_WARNING + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_cerrar.setToolTip(
            "Cerrar el curso seleccionado (no se podrán añadir más guardias)"
        )
        self.btn_cerrar.clicked.connect(self._cerrar_curso_seleccionado)
        self.btn_cerrar.setEnabled(False)
        botones_layout.addWidget(self.btn_cerrar)

        self.btn_eliminar = QPushButton("Eliminar")
        self.btn_eliminar.setIcon(icon_for_button("delete"))
        self.btn_eliminar.setStyleSheet(
            styles.STYLE_BUTTON_DANGER + "font-size: 12px; padding: 8px 16px;"
        )
        self.btn_eliminar.setToolTip("Eliminar el curso seleccionado y todas sus guardias")
        self.btn_eliminar.clicked.connect(self._eliminar_curso_seleccionado)
        self.btn_eliminar.setEnabled(False)
        botones_layout.addWidget(self.btn_eliminar)

        grupo_layout.addLayout(botones_layout)

        # Espaciado entre botones y tabla
        grupo_layout.addSpacing(15)

        # Tabla de cursos con scroll automático
        self.tabla_cursos = QTableWidget()
        self.tabla_cursos.setColumnCount(11)
        self.tabla_cursos.setHorizontalHeaderLabels(
            [
                "Curso",
                "Inicio",
                "Fin",
                "Estado",
                "Días Lect.",
                "G. Calc.",
                "G. Asig.",
                "G. Sin Asig.",
                "Profs.",
                "Zonas",
                "Creado",
            ]
        )

        # Configurar header para que las columnas se ajusten proporcionalmente
        header = self.tabla_cursos.horizontalHeader()
        header.setStretchLastSection(True)

        # Usar ResizeToContents para que se ajusten al contenido
        # pero con un mínimo establecido
        for i in range(11):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)

        self.tabla_cursos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_cursos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_cursos.setAlternatingRowColors(True)

        # Scroll automático
        self.tabla_cursos.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tabla_cursos.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.tabla_cursos.itemSelectionChanged.connect(self._on_seleccion_cambiada)

        # Añadir tabla con stretch=1 para que ocupe el espacio disponible
        grupo_layout.addWidget(self.tabla_cursos, 1)

        grupo.setLayout(grupo_layout)

        # Añadir GroupBox con stretch=1 para que se expanda verticalmente
        layout.addWidget(grupo, 1)

    def _cargar_cursos(self) -> None:
        """Carga todos los cursos en la tabla."""
        try:
            # Forzar refresco de la sesión para obtener datos actualizados
            self.session.expire_all()

            cursos = GestorCursos.listar_todos_cursos(self.session, incluir_cerrados=True)

            self.tabla_cursos.setRowCount(len(cursos))

            for i, curso in enumerate(cursos):
                # Nombre del curso
                item_nombre = QTableWidgetItem(curso.nombre)
                item_nombre.setData(Qt.ItemDataRole.UserRole, curso.id)
                item_nombre.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Resaltar curso activo
                if curso.activo:
                    item_nombre.setBackground(Qt.GlobalColor.yellow)
                    item_nombre.setText(f"⭐ {curso.nombre}")

                self.tabla_cursos.setItem(i, 0, item_nombre)

                # Fecha inicio
                item_inicio = QTableWidgetItem(curso.fecha_inicio.strftime("%d/%m/%Y"))
                item_inicio.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 1, item_inicio)

                # Fecha fin
                item_fin = QTableWidgetItem(curso.fecha_fin.strftime("%d/%m/%Y"))
                item_fin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 2, item_fin)

                # Estado
                estado = []
                if curso.activo:
                    estado.append("Activo")
                if curso.cerrado:
                    estado.append("Cerrado")
                if not curso.activo and not curso.cerrado:
                    estado.append("Inactivo")

                item_estado = QTableWidgetItem(" | ".join(estado))
                item_estado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 3, item_estado)

                # Calcular estadísticas del curso
                stats = self._calcular_estadisticas_curso(curso.id)

                # Días Lectivos
                item_dias = QTableWidgetItem(str(stats["dias_lectivos"]))
                item_dias.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 4, item_dias)

                # Guardias Calculadas
                item_calc = QTableWidgetItem(str(stats["guardias_calculadas"]))
                item_calc.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 5, item_calc)

                # Guardias Asignadas
                item_asig = QTableWidgetItem(str(stats["guardias_asignadas"]))
                item_asig.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 6, item_asig)

                # Guardias Sin Asignar
                sin_asignar = stats["guardias_calculadas"] - stats["guardias_asignadas"]
                item_sin = QTableWidgetItem(str(sin_asignar))
                item_sin.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Resaltar si hay guardias sin asignar
                if sin_asignar > 0:
                    item_sin.setBackground(Qt.GlobalColor.red)
                    item_sin.setForeground(Qt.GlobalColor.white)
                self.tabla_cursos.setItem(i, 7, item_sin)

                # Profesores
                item_prof = QTableWidgetItem(str(stats["profesores"]))
                item_prof.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 8, item_prof)

                # Zonas
                item_zonas = QTableWidgetItem(str(stats["zonas"]))
                item_zonas.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 9, item_zonas)

                # Fecha creación
                item_creado = QTableWidgetItem(curso.created_at.strftime("%d/%m/%Y %H:%M"))
                item_creado.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_cursos.setItem(i, 10, item_creado)  # Columna 10 (última)

            logger.info(f"Cargados {len(cursos)} cursos en tabla de gestión")

        except Exception as e:
            logger.error(f"Error al cargar cursos: {e}")
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"No se pudieron cargar los cursos:\n{e}")
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.setFixedSize(450, 200)
            msg_box.exec()

    def _calcular_estadisticas_curso(self, curso_id: int) -> dict:
        """
        Calcula estadísticas de un curso.

        Returns:
            Dict con: dias_lectivos, guardias_calculadas, guardias_asignadas,
                     profesores, zonas
        """
        try:
            # Obtener el curso
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            curso = _svc.cursos.get_by_id(curso_id)
            if not curso:
                logger.warning(f"No se encontró el curso con id={curso_id}")
                return {
                    "dias_lectivos": 0,
                    "guardias_calculadas": 0,
                    "guardias_asignadas": 0,
                    "profesores": 0,
                    "zonas": 0,
                }

            # Días lectivos del curso
            from datetime import timedelta

            dias_lectivos = 0

            # Buscar configuración que tenga este curso como activo
            config = _svc.configuracion_repo.find_by_curso_activo_id(curso_id)

            if config:
                # Usar la función de cálculo de días lectivos
                from services.calculador_guardias import listar_dias_lectivos

                dias_lectivos = len(listar_dias_lectivos(config))
                logger.debug(f"Curso {curso.nombre}: {dias_lectivos} días lectivos (desde config)")
            else:
                # Para cursos sin configuración, calcular días laborables entre fechas
                fecha_actual = curso.fecha_inicio
                while fecha_actual <= curso.fecha_fin:
                    # Contar días laborables (lunes a viernes)
                    if fecha_actual.weekday() < 5:  # 0-4 son lunes-viernes
                        dias_lectivos += 1
                    fecha_actual += timedelta(days=1)
                logger.debug(f"Curso {curso.nombre}: {dias_lectivos} días laborables (calculados)")

            # Guardias asignadas (todas las guardias del curso)
            guardias_asignadas = _svc.guardias.count_by_curso(curso_id)
            logger.debug(f"Curso {curso.nombre}: {guardias_asignadas} guardias asignadas")

            # Guardias calculadas: contar slots únicos
            guardias_totales = guardias_asignadas
            guardias_calculadas = guardias_totales

            # Profesores únicos que tienen guardias en este curso
            profesores = _svc.guardias.count_profesores_distintos_by_curso(curso_id)
            logger.debug(f"Curso {curso.nombre}: {profesores} profesores únicos")

            # Zonas únicas usadas en este curso
            zonas = _svc.guardias.count_zonas_distintas_by_curso(curso_id)
            logger.debug(f"Curso {curso.nombre}: {zonas} zonas únicas")

            return {
                "dias_lectivos": dias_lectivos,
                "guardias_calculadas": guardias_calculadas,
                "guardias_asignadas": guardias_asignadas,
                "profesores": profesores,
                "zonas": zonas,
            }

        except Exception as e:
            logger.error(f"Error al calcular estadísticas del curso {curso_id}: {e}", exc_info=True)
            return {
                "dias_lectivos": 0,
                "guardias_calculadas": 0,
                "guardias_asignadas": 0,
                "profesores": 0,
                "zonas": 0,
            }

    def _on_seleccion_cambiada(self) -> None:
        """Actualiza el estado de los botones según la selección."""
        items = self.tabla_cursos.selectedItems()
        hay_seleccion = len(items) > 0

        if not hay_seleccion:
            self.btn_activar.setEnabled(False)
            self.btn_cerrar.setEnabled(False)
            self.btn_eliminar.setEnabled(False)
            return

        # Obtener curso seleccionado
        curso_id = items[0].data(Qt.ItemDataRole.UserRole)
        from application.app_services import AppServices
        curso = AppServices(self.session).cursos.get_by_id(curso_id)

        if curso:
            # Activar: solo si no está activo (puede estar cerrado o no)
            # El botón "Activar" también reabre cursos cerrados
            self.btn_activar.setEnabled(not curso.activo)

            # Cerrar: solo si no está cerrado y está activo
            self.btn_cerrar.setEnabled(not curso.cerrado and curso.activo)

            # Eliminar: solo si no está activo
            self.btn_eliminar.setEnabled(not curso.activo)

    def _crear_curso(self) -> None:
        """Abre el diálogo de creación de curso."""
        try:
            logger.info("Abriendo diálogo de creación de curso...")

            # Crear diálogo SIN parent para evitar problemas de crash en macOS
            dialogo = DialogoCrearCurso(self.session, None)

            logger.info("Diálogo creado, ejecutando...")
            resultado = dialogo.exec()
            logger.info(f"Diálogo cerrado con resultado: {resultado}")

            if resultado:
                logger.info("Recargando lista de cursos...")
                self._cargar_cursos()
                self.curso_modificado.emit()
                logger.info("Cursos recargados correctamente")
        except Exception as e:
            logger.error(f"Error al abrir diálogo: {type(e).__name__}: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Error", f"Error al abrir el diálogo:\n{type(e).__name__}: {e}"
            )

    def _activar_curso_seleccionado(self) -> None:
        """Activa el curso seleccionado (incluso si está cerrado)."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            from application.app_services import AppServices
            curso = AppServices(self.session).cursos.get_by_id(curso_id)

            # Mensaje diferente si el curso está cerrado
            if curso.cerrado:
                mensaje = (
                    f"¿Activar el curso {curso.nombre}?\n\n"
                    "Este curso está cerrado. Se reabrirá automáticamente.\n"
                    "El curso activo actual se desactivará."
                )
            else:
                mensaje = (
                    f"¿Activar el curso {curso.nombre}?\n\nEl curso activo actual se desactivará."
                )

            # Usar QMessageBox explícito para control de tamaño
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Activar Curso")
            msg_box.setText(mensaje)
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
            msg_box.setFixedSize(500, 250)

            respuesta = msg_box.exec()

            if respuesta == QMessageBox.StandardButton.Yes:
                # Si está cerrado, reabrirlo primero
                if curso.cerrado:
                    GestorCursos.reabrir_curso(self.session, curso_id)

                # Luego activarlo
                GestorCursos.activar_curso(self.session, curso_id)

                # Mensaje de éxito
                msg_success = QMessageBox(self)
                msg_success.setIcon(QMessageBox.Icon.Information)
                msg_success.setWindowTitle("Curso Activado")
                msg_success.setText(f"El curso {curso.nombre} está ahora activo.")
                msg_success.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_success.setFixedSize(450, 200)
                msg_success.exec()

                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al activar curso: {e}")

            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo activar el curso:\n{e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.setFixedSize(450, 200)
            msg_error.exec()

    def _cerrar_curso_seleccionado(self) -> None:
        """Cierra el curso seleccionado."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            from application.app_services import AppServices
            curso = AppServices(self.session).cursos.get_by_id(curso_id)

            # Usar QMessageBox explícito
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Question)
            msg_box.setWindowTitle("Cerrar Curso")
            msg_box.setText(f"¿Cerrar el curso {curso.nombre}?")
            msg_box.setInformativeText(
                "Un curso cerrado no se puede modificar ni activar.\n"
                "Podrás reabrirlo más tarde si es necesario."
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)
            msg_box.setFixedSize(500, 300)

            respuesta = msg_box.exec()

            if respuesta == QMessageBox.StandardButton.Yes:
                GestorCursos.cerrar_curso(self.session, curso_id)

                # Mensaje de éxito
                msg_success = QMessageBox(self)
                msg_success.setIcon(QMessageBox.Icon.Information)
                msg_success.setWindowTitle("Curso Cerrado")
                msg_success.setText(f"El curso {curso.nombre} ha sido cerrado.")
                msg_success.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_success.setFixedSize(450, 200)
                msg_success.exec()

                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al cerrar curso: {e}")

            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo cerrar el curso:\n{e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.setFixedSize(450, 200)
            msg_error.exec()

    def _eliminar_curso_seleccionado(self) -> None:
        """Elimina el curso seleccionado (con confirmación fuerte)."""
        curso_id = self._obtener_curso_seleccionado_id()
        if curso_id is None:
            return

        try:
            from application.app_services import AppServices
            _svc = AppServices(self.session)
            curso = _svc.cursos.get_by_id(curso_id)

            # Contar guardias
            num_guardias = _svc.guardias.count_by_curso(curso_id)

            # Confirmación doble
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setWindowTitle("Eliminar Curso")
            msg_box.setText(f"¿ELIMINAR el curso {curso.nombre}?")
            msg_box.setInformativeText(
                f"Esta acción eliminará:\n"
                f"   • {num_guardias} guardias asignadas\n"
                f"   • Todos los datos asociados al curso\n\n"
                "Esta acción NO se puede deshacer."
            )
            msg_box.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            msg_box.setDefaultButton(QMessageBox.StandardButton.No)

            # FORZAR tamaño fijo para que se vean los botones en macOS
            msg_box.setFixedSize(550, 350)

            respuesta1 = msg_box.exec()

            if respuesta1 != QMessageBox.StandardButton.Yes:
                return

            # Segunda confirmación
            msg_box2 = QMessageBox(self)
            msg_box2.setIcon(QMessageBox.Icon.Critical)
            msg_box2.setWindowTitle("CONFIRMACIÓN FINAL")
            msg_box2.setText(f"¿Estás COMPLETAMENTE SEGURO de eliminar {curso.nombre}?")
            msg_box2.setInformativeText("Se perderán todos los datos permanentemente.")
            msg_box2.setStandardButtons(
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel
            )
            msg_box2.setDefaultButton(QMessageBox.StandardButton.Cancel)

            # FORZAR tamaño fijo para que se vean los botones en macOS
            msg_box2.setFixedSize(500, 300)

            respuesta2 = msg_box2.exec()

            if respuesta2 == QMessageBox.StandardButton.Yes:
                # Eliminar curso (cascade eliminará guardias)
                self.session.delete(curso)
                self.session.commit()

                # Mensaje de éxito
                msg_success = QMessageBox(self)
                msg_success.setIcon(QMessageBox.Icon.Information)
                msg_success.setWindowTitle("Curso Eliminado")
                msg_success.setText(f"El curso {curso.nombre} ha sido eliminado.")
                msg_success.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_success.setFixedSize(450, 200)
                msg_success.exec()

                self._cargar_cursos()
                self.curso_modificado.emit()

        except Exception as e:
            logger.error(f"Error al eliminar curso: {e}")
            self.session.rollback()

            msg_error = QMessageBox(self)
            msg_error.setIcon(QMessageBox.Icon.Critical)
            msg_error.setWindowTitle("Error")
            msg_error.setText(f"No se pudo eliminar el curso:\n{e}")
            msg_error.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_error.setFixedSize(450, 200)
            msg_error.exec()

    def _obtener_curso_seleccionado_id(self) -> Optional[int]:
        """Obtiene el ID del curso seleccionado en la tabla."""
        items = self.tabla_cursos.selectedItems()
        if items:
            return items[0].data(Qt.ItemDataRole.UserRole)
        return None

    def refrescar(self) -> None:
        """Recarga la tabla de cursos."""
        self._cargar_cursos()
