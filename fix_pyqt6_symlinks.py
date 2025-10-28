"""
Runtime hook para solucionar problema de symlinks en PyQt6
"""
import os
import sys


def fix_qt_symlinks():
    """
    Elimina symlinks duplicados que causan problemas en la compilación
    """
    if sys.platform == 'darwin':  # Solo en macOS
        qt_path = os.path.join(sys._MEIPASS, 'PyQt6', 'Qt6', 'lib')

        if os.path.exists(qt_path):
            for framework in os.listdir(qt_path):
                framework_path = os.path.join(qt_path, framework)
                if framework.endswith('.framework') and os.path.isdir(framework_path):
                    resources_link = os.path.join(framework_path, 'Resources')

                    # Si Resources es un symlink, lo eliminamos y creamos un directorio
                    if os.path.islink(resources_link):
                        try:
                            os.unlink(resources_link)
                            os.makedirs(resources_link, exist_ok=True)
                        except Exception:
                            pass  # Ignorar errores, la app funcionará de todos modos


# Ejecutar al importar
try:
    fix_qt_symlinks()
except Exception:
    pass  # No fallar si hay problemas
