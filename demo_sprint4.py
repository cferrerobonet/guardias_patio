"""
Demo Sprint 4 - Presentation Layer Refactorizada

Este demo muestra el form SimpleProfesorForm que usa:
- BaseForm como clase base
- Use Cases de la Application Layer
- DTOs para validación
- Manejo estandarizado de errores

NOTA: Este es un ejemplo demostrativo, NO reemplaza el main.py actual.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent / "src"))  # noqa: E402

from database.db_manager import SessionLocal, engine  # noqa: E402
from models.models import Base  # noqa: E402
from presentation.forms.simple_profesor_form import SimpleProfesorForm  # noqa: E402
from PyQt6.QtWidgets import QApplication  # noqa: E402


def main():
    """Función principal del demo."""
    print("=" * 80)
    print("🚀 DEMO SPRINT 4 - PRESENTATION LAYER REFACTORIZADA")
    print("=" * 80)
    print()
    print("Este demo muestra un form de profesores refactorizado usando:")
    print("  ✅ BaseForm como clase base")
    print("  ✅ Use Cases en lugar de acceso directo a BD")
    print("  ✅ DTOs de Pydantic para validación")
    print("  ✅ Manejo estandarizado de errores")
    print("  ✅ Logging estructurado")
    print()
    print("Patrón:")
    print("  Vista (SimpleProfesorForm) → Use Case → Repository → Database")
    print()
    print("=" * 80)
    print()

    # Inicializar base de datos
    print("📦 Inicializando base de datos...")
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    print("✅ Base de datos lista")
    print()

    # Crear aplicación PyQt6
    print("🎨 Creando aplicación...")
    app = QApplication(sys.argv)

    # Crear y mostrar form
    form = SimpleProfesorForm(session)
    form.show()

    print("✅ Aplicación iniciada")
    print()
    print("💡 INSTRUCCIONES:")
    print("  1. El form muestra la lista de profesores existentes")
    print("  2. Completa los campos: Nombre completo, Email, Horas")
    print("  3. Click en 'Guardar Profesor'")
    print("  4. La validación con Pydantic detecta errores automáticamente")
    print("  5. Los errores se muestran con mensajes claros")
    print("  6. El Use Case maneja toda la lógica de negocio")
    print()
    print("🧪 PRUEBAS SUGERIDAS:")
    print("  - Nombre vacío → Advertencia de validación")
    print("  - Email inválido → Error de Pydantic")
    print("  - Horas fuera de rango (1-40) → Error de Pydantic")
    print("  - Datos válidos → Éxito + actualización automática")
    print()
    print("🔍 Observa los logs en consola para ver:")
    print("  - Structured logging de cada operación")
    print("  - Manejo de excepciones")
    print("  - Llamadas a Use Cases")
    print()
    print("=" * 80)

    # Ejecutar aplicación
    try:
        sys.exit(app.exec())
    finally:
        session.close()
        print("\n👋 Sesión cerrada")


if __name__ == "__main__":
    main()
