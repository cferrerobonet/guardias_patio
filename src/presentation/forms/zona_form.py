"""
Formulario de gestión de zonas de recreo.

Permite realizar operaciones CRUD sobre las zonas usando patrón MVP.
"""

import ui_styles as styles
from application.dtos.zona_dto import CrearZonaDTO
from application.use_cases.zona import (
    CrearZonaUseCase,
    EliminarZonaUseCase,
    ListarZonasUseCase,
)
from pydantic import ValidationError
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError, NotFoundError

from presentation.forms.base_form import BaseForm


class ZonaForm(BaseForm):
    """
    Formulario para gestionar zonas de recreo.

    Permite crear, listar y eliminar zonas siguiendo el patrón MVP.
    """

    # Señal que se emite cuando se modifican los datos de zonas
    datos_modificados = pyqtSignal()

    def __init__(self, session: Session):
        """
        Inicializar el formulario de zonas.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        super().__init__(session)

        # Inicializar Use Cases
        self.crear_zona_uc = CrearZonaUseCase(session)
        self.listar_zonas_uc = ListarZonasUseCase(session)
        self.eliminar_zona_uc = EliminarZonaUseCase(session)

        self.setWindowTitle("Gestión de Zonas")
        self.setup_ui()
        self.cargar_zonas()

    def setup_ui(self):
        """Configurar la interfaz de usuario del formulario"""
        # Layout principal vertical
        main_layout = QVBoxLayout()

        # Crear splitter horizontal para permitir redimensionamiento
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Widget izquierdo: Lista de zonas
        left_widget = self._crear_widget_lista()

        # Widget derecho: Formulario de alta
        right_widget = self._crear_widget_formulario()

        # Agregar widgets al splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        # Configurar proporciones del splitter (60% lista, 40% formulario)
        splitter.setStretchFactor(0, 60)
        splitter.setStretchFactor(1, 40)

        # Agregar splitter al layout principal
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def _crear_widget_lista(self) -> QWidget:
        """
        Crear el widget de la sección de lista de zonas.

        Returns:
            Widget contenedor con la lista y botones de gestión
        """
        widget = QWidget()
        layout = self._crear_seccion_lista()
        widget.setLayout(layout)
        return widget

    def _crear_widget_formulario(self) -> QWidget:
        """
        Crear el widget de la sección de formulario.

        Returns:
            Widget contenedor con el formulario de alta
        """
        widget = QWidget()
        layout = self._crear_seccion_formulario()
        widget.setLayout(layout)
        return widget

    def _crear_seccion_lista(self) -> QVBoxLayout:
        """
        Crear la sección de lista de zonas.

        Returns:
            Layout con la lista y botones de gestión
        """
        left_section = QVBoxLayout()
        left_section.setContentsMargins(10, 10, 10, 10)
        left_section.setSpacing(10)

        # Título con contador
        self.titulo_lista_zonas = QLabel("🏫 ZONAS REGISTRADAS (0)")
        self.titulo_lista_zonas.setStyleSheet(styles.STYLE_TITLE_MAIN)
        left_section.addWidget(self.titulo_lista_zonas)

        # Lista de zonas
        self.lista_zonas = QListWidget()
        self.lista_zonas.setStyleSheet(
            """
            QListWidget {
                border: 2px solid #e0e0e0;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """
        )
        left_section.addWidget(self.lista_zonas)

        # Botones de gestión
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("🔄 Actualizar")
        self.refresh_btn.setStyleSheet(styles.STYLE_BUTTON_PRIMARY)
        self.refresh_btn.clicked.connect(self.cargar_zonas)

        self.delete_btn = QPushButton("🗑️ Eliminar")
        self.delete_btn.setStyleSheet(styles.STYLE_BUTTON_DANGER)
        self.delete_btn.clicked.connect(self.eliminar_zona)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.delete_btn)
        btn_layout.addStretch()
        left_section.addLayout(btn_layout)

        return left_section

    def _crear_seccion_formulario(self) -> QVBoxLayout:
        """
        Crear la sección de formulario de alta.

        Returns:
            Layout con el formulario y botón de guardar
        """
        right_section = QVBoxLayout()
        right_section.setContentsMargins(10, 0, 10, 10)
        right_section.setSpacing(12)

        # Título del formulario
        titulo_form = QLabel("✏️ NUEVA ZONA")
        titulo_form.setStyleSheet(styles.STYLE_TITLE_MAIN)
        right_section.addWidget(titulo_form)

        # Grupo de datos
        grupo_datos = QGroupBox("📋 Datos de la Zona")
        grupo_datos.setStyleSheet(styles.STYLE_GROUPBOX)
        layout_datos = QVBoxLayout()
        layout_datos.setSpacing(8)

        # Campo: Nombre de la zona
        label_nombre = QLabel("Nombre de la zona:")
        label_nombre.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_nombre)

        self.nombre_zona_input = QLineEdit()
        self.nombre_zona_input.setPlaceholderText("Ej: Patio Principal, Porche, etc.")
        self.nombre_zona_input.setStyleSheet(styles.STYLE_INPUT)
        self.nombre_zona_input.setMaximumWidth(350)
        layout_datos.addWidget(self.nombre_zona_input)

        # Campo: Descripción
        label_desc = QLabel("Descripción (opcional):")
        label_desc.setStyleSheet(styles.STYLE_LABEL_FIELD)
        layout_datos.addWidget(label_desc)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("Detalles adicionales sobre la zona")
        self.descripcion_input.setStyleSheet(styles.STYLE_INPUT)
        self.descripcion_input.setMaximumWidth(350)
        layout_datos.addWidget(self.descripcion_input)

        grupo_datos.setLayout(layout_datos)
        right_section.addWidget(grupo_datos)

        # Botón de guardar
        self.submit_btn = QPushButton("💾 Guardar Zona")
        self.submit_btn.setStyleSheet(styles.STYLE_BUTTON_SUCCESS)
        self.submit_btn.clicked.connect(self.guardar_zona)
        right_section.addWidget(self.submit_btn)

        # Espacio flexible
        right_section.addStretch()

        return right_section

    def guardar_zona(self):
        """Guardar una nueva zona usando el Use Case"""
        try:
            # Crear DTO con los datos del formulario (incluye validación)
            zona_dto = CrearZonaDTO(
                nombre_zona=self.nombre_zona_input.text().strip(),
                descripcion=self.descripcion_input.text().strip() or None,
            )

            # Ejecutar Use Case
            zona_creada = self.crear_zona_uc.execute(zona_dto)

            # Mostrar mensaje de éxito
            self.mostrar_exito(
                "Zona guardada",
                f"Zona '{zona_creada.nombre_zona}' guardada correctamente."
            )

            # Limpiar formulario y recargar lista
            self.limpiar_formulario()
            self.cargar_zonas()

            # Emitir señal de modificación de datos
            self.datos_modificados.emit()

        except ValidationError as e:
            # Errores de validación de Pydantic
            errores = "; ".join([error["msg"] for error in e.errors()])
            self.mostrar_error("Datos inválidos", errores)

        except BusinessLogicError as e:
            # Errores de lógica de negocio (zona duplicada, etc.)
            self.mostrar_error("Error de lógica de negocio", str(e))

        except Exception as e:
            # Otros errores inesperados
            self.manejar_excepcion(e, "guardar la zona")

    def cargar_zonas(self):
        """Cargar la lista de zonas desde la base de datos usando el Use Case"""
        try:
            # Ejecutar Use Case (ya viene ordenado por nombre_zona)
            zonas = self.listar_zonas_uc.execute()

            # Limpiar lista actual
            self.lista_zonas.clear()

            # Actualizar contador en el título
            total_zonas = len(zonas)
            self.titulo_lista_zonas.setText(f"🏫 ZONAS REGISTRADAS ({total_zonas})")

            # Agregar zonas a la lista (ya vienen ordenadas alfabéticamente)
            for zona in zonas:
                desc = zona.descripcion if zona.descripcion else "Sin descripción"
                texto = f"[{zona.id}] {zona.nombre_zona} - {desc}"
                self.lista_zonas.addItem(texto)

            # Ordenar la lista visualmente (por si acaso)
            self.lista_zonas.sortItems()

        except Exception as e:
            self.manejar_excepcion(e, "cargar las zonas")

    def eliminar_zona(self):
        """Eliminar la zona seleccionada usando el Use Case"""
        # Verificar que haya una zona seleccionada
        item_actual = self.lista_zonas.currentItem()
        if not item_actual:
            self.mostrar_advertencia(
                "Selección requerida",
                "Selecciona una zona para eliminar."
            )
            return

        # Extraer ID del texto [ID] nombre...
        texto = item_actual.text()
        id_zona = int(texto.split("]")[0].replace("[", ""))

        # Confirmar eliminación
        if not self.confirmar_accion(
            "Confirmar eliminación",
            f"¿Eliminar zona con ID {id_zona}?"
        ):
            return

        try:
            # Ejecutar Use Case
            self.eliminar_zona_uc.execute(id_zona)

            # Mostrar mensaje de éxito
            self.mostrar_exito("Zona eliminada", "La zona ha sido eliminada correctamente.")

            # Recargar lista
            self.cargar_zonas()

            # Emitir señal de modificación de datos
            self.datos_modificados.emit()

        except NotFoundError as e:
            self.mostrar_error("Error", str(e))

        except BusinessLogicError as e:
            # Error por guardias asociadas
            self.mostrar_error("Error al eliminar zona", str(e))

        except Exception as e:
            self.manejar_excepcion(e, "eliminar la zona")

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.nombre_zona_input.clear()
        self.descripcion_input.clear()

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, Pydantic lo hace en el DTO).

        Returns:
            True siempre, la validación real ocurre en CrearZonaDTO
        """
        return True
