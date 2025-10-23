"""
Formulario de asignación de guardias.

Permite calcular distribución y generar el calendario completo de guardias.
"""

from PyQt6.QtWidgets import (
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)
from sqlalchemy.orm import Session

from application.use_cases.asignacion_guardias import (
    CalcularDistribucionUseCase,
    GenerarGuardiasUseCase,
    ObtenerEstadisticasUseCase,
)
from models.models import Guardia, Profesor
from presentation.forms.base_form import BaseForm
from presentation.widgets.progress_indicators import ejecutar_con_progreso
from utils.exceptions import BusinessLogicError


class AsignacionGuardiasForm(BaseForm):
    """
    Formulario para calcular y asignar guardias.

    Permite:
    - Ver estadísticas del curso
    - Calcular distribución de guardias por profesor
    - Generar el calendario completo de guardias
    """

    def __init__(self, session: Session):
        """
        Inicializar el formulario de asignación de guardias.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        super().__init__(session)

        # Inicializar Use Cases
        self.obtener_estadisticas_uc = ObtenerEstadisticasUseCase(session)
        self.calcular_distribucion_uc = CalcularDistribucionUseCase(session)
        self.generar_guardias_uc = GenerarGuardiasUseCase(session)

        self.setWindowTitle("Asignación de Guardias")
        self.setup_ui()
        self.cargar_estadisticas()

    def setup_ui(self):
        """Configurar la interfaz de usuario del formulario"""
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("=== CÁLCULO Y ASIGNACIÓN DE GUARDIAS ===")
        titulo.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(titulo)

        # Área de estadísticas
        layout.addWidget(QLabel("\n📊 ESTADÍSTICAS DEL CURSO:"))
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(200)
        layout.addWidget(self.stats_text)

        # Botón para calcular distribución
        calc_button = QPushButton("📊 Calcular Distribución")
        calc_button.clicked.connect(self.calcular_distribucion)
        layout.addWidget(calc_button)

        # Área de resultados de distribución
        layout.addWidget(QLabel("\n📋 DISTRIBUCIÓN DE GUARDIAS POR PROFESOR:"))
        self.distribucion_text = QTextEdit()
        self.distribucion_text.setReadOnly(True)
        self.distribucion_text.setMaximumHeight(250)
        layout.addWidget(self.distribucion_text)

        # Botón para generar guardias (deshabilitado inicialmente)
        self.generar_button = QPushButton("🎯 Generar Asignación de Guardias")
        self.generar_button.setEnabled(False)
        self.generar_button.clicked.connect(self.generar_guardias)
        layout.addWidget(self.generar_button)

        # Área de resultados de generación
        self.resultado_text = QTextEdit()
        self.resultado_text.setReadOnly(True)
        self.resultado_text.setMaximumHeight(150)
        layout.addWidget(self.resultado_text)

        self.setLayout(layout)

    def cargar_estadisticas(self):
        """Cargar y mostrar estadísticas del curso"""
        try:
            # Ejecutar Use Case
            stats = self.obtener_estadisticas_uc.execute()

            # Formatear texto
            texto = f"""
Días lectivos: {stats.dias_lectivos} días (L-V)
Recreos mañana: {stats.recreos_manana}
Recreos tarde: {stats.recreos_tarde}
Total recreos/día: {stats.recreos_manana + stats.recreos_tarde}
Número de zonas: {stats.num_zonas}
Número de profesores: {stats.num_profesores}

📌 SLOTS TOTALES: {stats.slots_totales} guardias
   (días × recreos × zonas = {stats.dias_lectivos} ×
   {stats.recreos_manana + stats.recreos_tarde} × {stats.num_zonas})
            """
            self.stats_text.setText(texto.strip())

        except BusinessLogicError as e:
            self.stats_text.setText(f"⚠️  {str(e)}")
        except Exception as e:
            self.manejar_excepcion(e, "cargar estadísticas")

    def calcular_distribucion(self):
        """Calcular y mostrar la distribución de guardias"""
        try:
            # Ejecutar Use Case
            distribucion_dto = self.calcular_distribucion_uc.execute()

            # Formatear texto con nombres de profesores
            texto = "Distribución calculada:\n\n"

            # Ordenar por número de guardias (descendente)
            profesores_ordenados = sorted(
                distribucion_dto.distribucion.items(),
                key=lambda x: x[1],
                reverse=True,
            )

            for profesor_id, guardias in profesores_ordenados:
                profesor = self.session.query(Profesor).get(profesor_id)
                if profesor:
                    texto += (
                        f"• {profesor.nombre_completo} "
                        f"({profesor.turno}, {profesor.porcentaje_jornada*100:.0f}%): "
                        f"{guardias} guardias\n"
                    )

            texto += f"\n✅ TOTAL: {distribucion_dto.total_guardias} guardias"
            texto += f"\n📌 Slots disponibles: {distribucion_dto.slots_totales}"

            if distribucion_dto.es_exacta:
                texto += "\n\n✅ La distribución es exacta"
            else:
                texto += f"\n\n⚠️  Diferencia: {abs(distribucion_dto.diferencia)}"

            self.distribucion_text.setText(texto)

            # Habilitar botón de generación
            self.generar_button.setEnabled(True)

        except BusinessLogicError as e:
            self.mostrar_error("Error en Cálculo", str(e))
            self.distribucion_text.setText(f"❌ Error: {str(e)}")

        except Exception as e:
            self.manejar_excepcion(e, "calcular distribución")

    def generar_guardias(self):
        """Generar el calendario completo de guardias"""
        try:
            # Verificar si ya existen guardias
            count_guardias = self.session.query(Guardia).count()

            eliminar_existentes = True  # Por defecto, eliminar

            if count_guardias > 0:
                respuesta = QMessageBox.question(
                    self,
                    "⚠️ Guardias Existentes",
                    f"Ya existen {count_guardias} guardias en la base de datos.\n\n"
                    f"¿Deseas ELIMINAR todas las guardias existentes "
                    f"antes de generar nuevas?\n\n"
                    f"• SÍ: Eliminará todas y generará desde cero (recomendado)\n"
                    f"• NO: Agregará nuevas guardias a las existentes "
                    f"(puede crear duplicados)",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                )

                if respuesta == QMessageBox.StandardButton.Cancel:
                    return

                eliminar_existentes = respuesta == QMessageBox.StandardButton.Yes

                if eliminar_existentes:
                    self.mostrar_exito(
                        "Limpieza completada",
                        f"{count_guardias} guardias eliminadas. "
                        f"Generando calendario nuevo...",
                    )

            # Función para ejecutar con progreso
            def tarea_generacion(progress_callback):
                """Ejecuta la generación de guardias con callback de progreso."""
                return self.generar_guardias_uc.execute(
                    eliminar_existentes=eliminar_existentes,
                    progress_callback=progress_callback,
                )

            # Ejecutar con indicador de progreso mejorado
            resumen, cancelado = ejecutar_con_progreso(
                tarea_generacion,
                titulo="Generando Guardias",
                mensaje="Preparando generación de calendario...",
                padre=self,
                cancelable=False,  # La generación no es cancelable
            )

            if not cancelado and resumen:
                # Mostrar resumen en el área de resultados
                texto = self._formatear_resumen(resumen)
                self.resultado_text.setText(texto)

                self.mostrar_exito(
                    "Asignación generada",
                    resumen.mensaje
                    or "Guardias generadas y guardadas en la base de datos.",
                )

        except BusinessLogicError as e:
            self.mostrar_error("Error en Generación", str(e))

        except Exception as e:
            self.manejar_excepcion(e, "generar guardias")

    def _formatear_resumen(self, resumen) -> str:
        """
        Formatear el resumen de generación para mostrarlo.

        Args:
            resumen: ResumenGeneracionDTO con los resultados

        Returns:
            Texto formateado con el resumen
        """
        lineas = [
            f"Guardias generadas: {resumen.guardias_generadas}",
            f"Slots esperados: {resumen.slots_esperados}",
        ]

        if resumen.cobertura_completa:
            lineas.append("✅ Cobertura completa")
        elif resumen.slots_sin_cubrir > 0:
            lineas.append(
                f"⚠️ {resumen.slots_sin_cubrir} slots sin cubrir "
                f"(falta elegibilidad)"
            )

        # Top profesores (máximo 10)
        if resumen.resumen_por_profesor:
            top = sorted(
                resumen.resumen_por_profesor.items(),
                key=lambda x: x[1],
                reverse=True,
            )[:10]
            lineas.append("\nPor profesor (top 10):")
            for pid, cnt in top:
                prof = self.session.query(Profesor).get(pid)
                if prof:
                    lineas.append(f"• {prof.nombre_completo}: {cnt}")

        return "\n".join(lineas)

    def limpiar_formulario(self):
        """Limpiar todos los campos del formulario"""
        self.distribucion_text.clear()
        self.resultado_text.clear()
        self.generar_button.setEnabled(False)
        self.cargar_estadisticas()

    def validar_formulario(self) -> bool:
        """
        Validar el formulario (no necesario, validación en Use Cases).

        Returns:
            True siempre, la validación real ocurre en los Use Cases
        """
        return True
