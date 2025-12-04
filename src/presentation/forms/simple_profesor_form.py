"""
Simple Profesor Form - Ejemplo Refactorizado

Este es un ejemplo simplificado de cómo sería ProfesorForm
usando Clean Architecture con Use Cases y DTOs.

Este form NO reemplaza el actual, es solo una demostración del patrón.
"""

from application.dtos import CrearProfesorDTO
from application.use_cases.profesor import (
    CrearProfesorUseCase,
    ListarProfesoresUseCase,
)
from PyQt6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)
from sqlalchemy.orm import Session

from presentation.forms.base_form import BaseForm


class SimpleProfesorForm(BaseForm):
    """
    Form simplificado para gestión de profesores.

    Demuestra el patrón:
    - Herencia de BaseForm
    - Uso de Use Cases en lugar de acceso directo a BD
    - Validación con DTOs
    - Manejo de errores estandarizado
    """

    def __init__(self, session: Session, parent=None):
        """
        Inicializa el formulario de profesores.

        Args:
            session: Sesión de SQLAlchemy
            parent: Widget padre
        """
        super().__init__(session, parent)

        # Inicializar Use Cases
        self.crear_profesor_uc = CrearProfesorUseCase(session)
        self.listar_profesores_uc = ListarProfesoresUseCase(session)

        # Configurar UI
        self.setup_ui()

        # Cargar datos iniciales
        self.cargar_profesores()

    def setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Gestión de Profesores - Ejemplo Refactorizado")
        self.setMinimumSize(800, 600)

        # Layout principal
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("👥 Gestión de Profesores (Ejemplo Refactorizado)")
        titulo.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                padding: 10px;
                background-color: #2c3e50;
                color: white;
                border-radius: 5px;
            }
        """)
        layout.addWidget(titulo)

        # Formulario de entrada
        form_layout = QFormLayout()

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("APELLIDOS, NOMBRE")
        form_layout.addRow("Nombre completo:", self.nombre_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("profesor@colegio.edu")
        form_layout.addRow("Email:", self.email_input)

        self.horas_input = QLineEdit()
        self.horas_input.setPlaceholderText("25.0")
        form_layout.addRow("Horas contrato:", self.horas_input)

        layout.addLayout(form_layout)

        # Botones de acción
        botones_layout = QHBoxLayout()

        self.guardar_btn = QPushButton("💾 Guardar Profesor")
        self.guardar_btn.clicked.connect(self.guardar_profesor)
        self.guardar_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        botones_layout.addWidget(self.guardar_btn)

        self.limpiar_btn = QPushButton("🧹 Limpiar")
        self.limpiar_btn.clicked.connect(self.limpiar_formulario)
        botones_layout.addWidget(self.limpiar_btn)

        self.actualizar_btn = QPushButton("🔄 Actualizar Lista")
        self.actualizar_btn.clicked.connect(self.cargar_profesores)
        botones_layout.addWidget(self.actualizar_btn)

        layout.addLayout(botones_layout)

        # Tabla de profesores
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(4)
        self.tabla.setHorizontalHeaderLabels(["ID", "Nombre Completo", "Email", "Horas Contrato"])
        self.tabla.setAlternatingRowColors(True)
        layout.addWidget(self.tabla)

        # Info footer
        self.info_label = QLabel("💡 Este es un ejemplo simplificado del patrón MVP")
        self.info_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def guardar_profesor(self) -> None:
        """
        Guarda un nuevo profesor usando el Use Case.

        Este método demuestra:
        - Validación de formulario
        - Creación de DTO
        - Ejecución de Use Case
        - Manejo de excepciones
        """
        try:
            # 1. Validar formulario básico
            es_valido, mensaje = self.validar_formulario()
            if not es_valido:
                self.mostrar_advertencia("Validación", mensaje)
                return

            # 2. Crear DTO (Pydantic valida automáticamente)
            dto = CrearProfesorDTO(
                nombre_completo=self.nombre_input.text().strip(),
                email_corporativo=self.email_input.text().strip() or None,
                horas_contrato=float(self.horas_input.text().strip()),
                turno="mañana",  # Simplificado para el ejemplo
                es_tutor=False,
            )

            # 3. Ejecutar Use Case
            profesor = self.crear_profesor_uc.execute(dto)

            # 4. Mostrar éxito
            self.mostrar_exito(
                "Profesor Creado",
                f"Profesor {profesor.nombre_completo} creado exitosamente con ID {profesor.id}",
            )

            # 5. Actualizar UI
            self.limpiar_formulario()
            self.cargar_profesores()

        except Exception as e:
            # Manejo estandarizado de excepciones
            self.manejar_excepcion(e, "guardar profesor")

    def cargar_profesores(self) -> None:
        """
        Carga la lista de profesores usando el Use Case.

        Demuestra:
        - Llamada a Use Case de consulta
        - Actualización de tabla
        - Logging automático
        """
        try:
            # Ejecutar Use Case
            profesores = self.listar_profesores_uc.execute()

            # Actualizar tabla
            self.tabla.setRowCount(len(profesores))
            for row, profesor in enumerate(profesores):
                self.tabla.setItem(row, 0, QTableWidgetItem(str(profesor.id)))
                self.tabla.setItem(row, 1, QTableWidgetItem(profesor.nombre_completo))
                self.tabla.setItem(row, 2, QTableWidgetItem(profesor.email_corporativo or ""))
                self.tabla.setItem(row, 3, QTableWidgetItem(str(profesor.horas_contrato)))

            # Actualizar info
            self.info_label.setText(f"📊 {len(profesores)} profesores cargados")

        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def limpiar_formulario(self) -> None:
        """Limpia todos los campos del formulario."""
        self.nombre_input.clear()
        self.email_input.clear()
        self.horas_input.clear()
        self.nombre_input.setFocus()

    def validar_formulario(self) -> tuple[bool, str]:
        """
        Valida los datos del formulario antes de crear el DTO.

        Returns:
            Tupla (es_valido, mensaje_error)
        """
        if not self.nombre_input.text().strip():
            return False, "El nombre completo es obligatorio"

        if not self.horas_input.text().strip():
            return False, "Las horas de contrato son obligatorias"

        try:
            horas = float(self.horas_input.text().strip())
            if horas <= 0 or horas > 40:
                return False, "Las horas deben estar entre 1 y 40"
        except ValueError:
            return False, "Las horas deben ser un número válido"

        return True, ""
