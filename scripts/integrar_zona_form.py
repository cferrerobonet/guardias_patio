"""
Script para integrar ZonaForm refactorizado en main.py.

Realiza las siguientes operaciones:
1. Agrega el import de ZonaForm refactorizado
2. Elimina la clase ZonaForm antigua de main.py
3. Actualiza el uso en MainWindow para usar el nuevo ZonaForm
"""

import sys
from pathlib import Path


def integrar_zona_form():
    """Integrar ZonaForm refactorizado en main.py"""
    # Ruta al archivo main.py
    main_py_path = Path(__file__).parent.parent / "src" / "main.py"

    if not main_py_path.exists():
        print(f"❌ No se encontró {main_py_path}")
        sys.exit(1)

    # Leer el contenido actual
    with open(main_py_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Paso 1: Agregar import después de ConfiguracionForm
    import_line = (
        "from presentation.forms import "
        "ZonaForm as ZonaFormRefactorizado\n"
    )
    import_added = False

    for i, line in enumerate(lines):
        if (
            "from presentation.forms import ConfiguracionForm" in line
            and not import_added
        ):
            # Insertar después del import de ConfiguracionForm
            lines.insert(i + 1, import_line)
            import_added = True
            print("✅ Import agregado")
            break

    if not import_added:
        print("⚠️ No se pudo agregar el import (ya existe o no se encontró el lugar)")

    # Paso 2: Eliminar la clase ZonaForm antigua
    class_start = None
    class_end = None
    indent_level = 0

    for i, line in enumerate(lines):
        if line.strip().startswith("class ZonaForm(QWidget):"):
            class_start = i
            # Detectar el nivel de indentación de la clase
            indent_level = len(line) - len(line.lstrip())
            continue

        if class_start is not None and class_end is None:
            # Buscar el final de la clase (siguiente clase o final de archivo)
            if line.strip() and not line.strip().startswith("#"):
                current_indent = len(line) - len(line.lstrip())
                # Si encontramos algo al mismo nivel de indentación, terminó la clase
                if (
                    current_indent <= indent_level
                    and line.strip()
                    and not line.strip().startswith("class ZonaForm")
                ):
                    class_end = i
                    break

    # Si no encontró el final, usar hasta el final del archivo
    if class_start is not None and class_end is None:
        class_end = len(lines)

    # Eliminar la clase
    if class_start is not None and class_end is not None:
        # Agregar comentario explicativo
        comment = [
            "\n",
            (
                "# =========================================="
                "====================================\n"
            ),
            (
                "# ZonaForm - Movida a "
                "src/presentation/forms/zona_form.py\n"
            ),
            (
                "# La clase antigua ha sido eliminada y "
                "reemplazada por versión refactorizada\n"
            ),
            "# que sigue el patrón MVP (Sprint 4)\n",
            (
                "# =========================================="
                "====================================\n"
            ),
            "\n",
        ]
        lines[class_start:class_end] = comment
        print(f"✅ Clase antigua eliminada (líneas {class_start}-{class_end})")

    # Paso 3: Actualizar el uso en MainWindow
    for i, line in enumerate(lines):
        if "self.tabs.addTab(ZonaForm()" in line:
            # Obtener la indentación actual
            indent = len(line) - len(line.lstrip())
            # Reemplazar con el nuevo form que recibe session
            lines[i] = (
                " " * indent
                + "# Usar ZonaForm refactorizado (Sprint 4)\n"
            )
            lines.insert(
                i + 1,
                " " * indent
                + "self.tabs.addTab("
                "ZonaFormRefactorizado(self.session), "
                '"🏫 Zonas")\n',
            )
            print("✅ Uso actualizado en MainWindow")
            break

    # Escribir el archivo modificado
    with open(main_py_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print("✅ ZonaForm integrado correctamente")


if __name__ == "__main__":
    integrar_zona_form()
