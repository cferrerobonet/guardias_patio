"""
Ejemplo de integración del OrquestadorAsignacionGuardias con la UI.
Muestra cómo usar el sistema completo con fallback automático.
"""

from typing import Callable, Optional

from infrastructure.database.models import Configuracion
from PyQt6.QtWidgets import QWidget
from services.calculador_guardias import listar_dias_lectivos
from sqlalchemy.orm import Session

from src.presentation.dialogs.dialogo_diagnostico_guardias import DialogoDiagnosticoGuardias
from src.services.diagnosticador_guardias import DiagnosticoCompleto
from src.services.orquestador_asignacion_guardias import (
    OrquestadorAsignacionGuardias,
    ResultadoOrquestacion,
)


class IntegradorOrquestadorUI:
    """
    Integrador que conecta el orquestador con la interfaz de usuario.
    """

    def __init__(
        self,
        db: Session,
        parent_widget: Optional[QWidget] = None,
        callback_decision_custom: Optional[Callable] = None,
    ):
        """
        Args:
            db: Sesión de base de datos
            parent_widget: Widget padre para diálogos
            callback_decision_custom: Callback personalizado para decisiones (para threading seguro)
        """
        self.db = db
        self.parent_widget = parent_widget
        self.callback_decision_custom = callback_decision_custom

    def generar_guardias_inteligente(
        self, progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> ResultadoOrquestacion:
        """
        Ejecuta la generación de guardias con el sistema completo de fallback.

        Args:
            progress_callback: Función opcional para reportar progreso (mensaje, porcentaje)

        Returns:
            ResultadoOrquestacion con el resultado final
        """
        import traceback

        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            logger.info("📋 FASE 1: Obtener configuración")
            # 1. Obtener configuración
            config = self.db.query(Configuracion).first()
            if not config:
                raise ValueError("No hay configuración disponible")
            logger.info(f"✓ Configuración obtenida: {config.id}")

            # 2. Calcular días lectivos
            logger.info("📋 FASE 2: Calcular días lectivos")
            if progress_callback:
                progress_callback("Calculando días lectivos...", 10)

            dias_lectivos = listar_dias_lectivos(config)
            logger.info(f"✓ Días lectivos calculados: {len(dias_lectivos)} días")

            # 3. Crear orquestador
            logger.info("📋 FASE 3: Crear orquestador")
            if progress_callback:
                progress_callback("Preparando sistema híbrido...", 20)

            orquestador = OrquestadorAsignacionGuardias(self.db, config, dias_lectivos)
            logger.info("✓ Orquestador creado")

            # 4. Ejecutar con callback para decisión del usuario
            logger.info("📋 FASE 4: Ejecutar generación con fallback")
            logger.info("⚠️  PUNTO CRÍTICO: Iniciando orquestador.generar_guardias_con_fallback")
            resultado = orquestador.generar_guardias_con_fallback(
                umbral_cobertura_minima=0.95,  # 95%
                umbral_problemas_criticos=0,  # 0 problemas críticos
                callback_decision_usuario=self._mostrar_dialogo_decision,
                progress_callback=progress_callback,  # Pasar callback de progreso
            )

            return resultado

        except Exception as e:
            logger.error(f"❌ Error crítico en generar_guardias_inteligente: {str(e)}")
            logger.error(f"Traceback completo: {traceback.format_exc()}")

            # Crear resultado de error en lugar de propagar la excepción
            from src.services.orquestador_asignacion_guardias import (
                EstrategiaUsada,
                ResultadoOrquestacion,
            )

            return ResultadoOrquestacion(
                exitoso=False,
                guardias=[],
                estrategia_usada=EstrategiaUsada.NINGUNA,
                mensaje_usuario=f"Error al generar guardias: {str(e)}",
                requiere_intervencion_usuario=True,
                diagnostico=None,
            )

    def _mostrar_dialogo_decision(self, diagnostico: DiagnosticoCompleto) -> str:
        """
        Muestra diálogo al usuario para decidir qué hacer.

        IMPORTANTE: Este método NO debe ser llamado directamente desde un worker thread.
        Use callback_decision_custom si está en un worker thread.

        Args:
            diagnostico: Diagnóstico completo de problemas

        Returns:
            'ajustar', 'continuar_ilp' o 'cancelar'
        """
        import traceback

        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            # Si hay un callback personalizado (para threading), usarlo
            if self.callback_decision_custom:
                logger.info("📞 Usando callback personalizado para decisión (thread-safe)")
                return self.callback_decision_custom(diagnostico)

            # De lo contrario, mostrar diálogo directamente (solo desde thread principal)
            logger.info("📊 Mostrando DialogoDiagnosticoGuardias en thread principal")
            dialogo = DialogoDiagnosticoGuardias(diagnostico, self.parent_widget)

            if dialogo.exec():
                return dialogo.get_accion_elegida()
            else:
                return "cancelar"

        except Exception as e:
            logger.error(f"❌ Error al mostrar diálogo de diagnóstico: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            # En caso de error, retornar 'ajustar' por defecto (opción más segura)
            return "ajustar"


# EJEMPLO DE USO DESDE UN FORMULARIO O VENTANA
# ============================================


def ejemplo_uso_desde_formulario(db: Session, parent_widget: QWidget):
    """
    Ejemplo de cómo usar el integrador desde un formulario.
    """
    from PyQt6.QtWidgets import QMessageBox

    # Crear integrador
    integrador = IntegradorOrquestadorUI(db, parent_widget)

    try:
        # Ejecutar generación inteligente
        resultado = integrador.generar_guardias_inteligente()

        if resultado.exitoso:
            # Mostrar mensaje de éxito
            QMessageBox.information(parent_widget, "Guardias Generadas", resultado.mensaje_usuario)

            # Guardar guardias en base de datos
            # (eliminar guardias anteriores y guardar nuevas)
            from src.models.guardia import Guardia

            db.query(Guardia).delete()
            db.add_all(resultado.guardias)
            db.commit()

            return True

        else:
            if resultado.requiere_intervencion_usuario:
                # Usuario debe ajustar configuración
                QMessageBox.warning(
                    parent_widget, "Intervención Requerida", resultado.mensaje_usuario
                )
            else:
                # Usuario canceló
                QMessageBox.information(
                    parent_widget, "Operación Cancelada", resultado.mensaje_usuario
                )

            return False

    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Error al generar guardias: {str(e)}")
        return False


# EJEMPLO DE USO DESDE LA LÍNEA DE COMANDOS (SCRIPT)
# ==================================================


def ejemplo_uso_cli():
    """
    Ejemplo de uso del orquestador desde línea de comandos.
    """
    from src.database.session import SessionLocal

    db = SessionLocal()

    try:
        config = db.query(Configuracion).first()
        if not config:
            print("❌ No hay configuración disponible")
            return

        dias_lectivos = listar_dias_lectivos(config)

        orquestador = OrquestadorAsignacionGuardias(db, config, dias_lectivos)

        # Callback simple para CLI
        def decision_cli(diagnostico):
            print("\n" + diagnostico.mensaje_resumen)
            print("\n¿Qué desea hacer?")
            print("  1. Ajustar configuración manualmente")
            print("  2. Continuar con ILP avanzado")
            print("  3. Cancelar")

            while True:
                opcion = input("\nSeleccione opción (1/2/3): ").strip()
                if opcion == "1":
                    return "ajustar"
                elif opcion == "2":
                    return "continuar_ilp"
                elif opcion == "3":
                    return "cancelar"
                else:
                    print("Opción inválida")

        # Ejecutar
        resultado = orquestador.generar_guardias_con_fallback(
            callback_decision_usuario=decision_cli
        )

        print("\n" + "=" * 70)
        if resultado.exitoso:
            print("✅ ÉXITO")
            print(resultado.mensaje_usuario)

            # Guardar en BD
            from src.models.guardia import Guardia

            db.query(Guardia).delete()
            db.add_all(resultado.guardias)
            db.commit()

            print(f"\n✅ {len(resultado.guardias)} guardias guardadas en la base de datos")

        else:
            print("⚠️  NO COMPLETADO")
            print(resultado.mensaje_usuario)

            if resultado.requiere_intervencion_usuario and resultado.diagnostico:
                print("\n📋 DIAGNÓSTICO DETALLADO:")
                for problema in resultado.diagnostico.problemas_criticos:
                    print(f"\n🔴 {problema.descripcion}")
                    for sugerencia in problema.sugerencias:
                        print(f"   💡 {sugerencia}")

        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    ejemplo_uso_cli()
