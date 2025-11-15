#!/usr/bin/env python3
"""
Script de prueba para visualizar el contador de tiempo en el diálogo de progreso.

Uso:
    python scripts/test_contador_tiempo.py
"""

import sys
import time
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from presentation.widgets.progress_indicators import ProgressDialog
from PyQt6.QtWidgets import QApplication


def simular_proceso_largo(callback_progreso):
    """Simula un proceso largo para probar el contador."""
    total_pasos = 20

    for i in range(total_pasos):
        # Simular trabajo
        time.sleep(0.5)  # Medio segundo por paso = 10 segundos total

        # Actualizar progreso
        callback_progreso(
            i + 1,
            total_pasos,
            f"Procesando paso {i + 1} de {total_pasos}"
        )

    return "Proceso completado exitosamente"


def main():
    """Función principal."""
    app = QApplication(sys.argv)

    # Crear diálogo
    dialog = ProgressDialog(
        title="Prueba de Contador de Tiempo",
        message="Observa el contador de tiempo funcionando...",
        show_details=True
    )

    print("=" * 60)
    print("PRUEBA DEL CONTADOR DE TIEMPO")
    print("=" * 60)
    print("\n📊 El diálogo mostrará:")
    print("   • Barra de progreso")
    print("   • 🆕 Contador de tiempo (HH:MM:SS)")
    print("   • Detalles del proceso")
    print("\n⏱️  El proceso durará aproximadamente 10 segundos")
    print("   (20 pasos × 0.5 segundos)")
    print("\n🎯 Observa cómo el contador se actualiza cada segundo")
    print("=" * 60)
    print()

    dialog.show()

    # Simular proceso
    def actualizar(actual, total, detalle):
        dialog.actualizar_progreso(actual, total, detalle)

    # Ejecutar proceso en "foreground" para demo
    try:
        for i in range(20):
            time.sleep(0.5)
            actualizar(i + 1, 20, f"Procesando paso {i + 1} de 20")
            app.processEvents()  # Procesar eventos de Qt

        dialog.completar("✓ Proceso completado - Observa el tiempo final")

        print("\n✅ PRUEBA COMPLETADA")
        print("   • El contador debería mostrar aproximadamente 00:00:10")
        print("   • Presiona 'Cerrar' para salir")

    except KeyboardInterrupt:
        print("\n⚠️  Prueba cancelada por el usuario")
        dialog._cancelar()

    # Mantener diálogo abierto
    dialog.exec()

    return 0


if __name__ == "__main__":
    sys.exit(main())
