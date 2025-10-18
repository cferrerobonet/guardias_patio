"""
Script para integrar ConfiguracionForm refactorizado en main.py
"""

def integrar_configuracion_form():
    """Integra el ConfiguracionForm refactorizado en main.py."""

    # Leer main.py
    with open('src/main.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 1. Agregar import después de los imports de widgets
    import_line = (
        "from presentation.forms import "
        "ConfiguracionForm as ConfiguracionFormRefactorizado\n"
    )

    # Encontrar línea después de widgets imports
    for i, line in enumerate(lines):
        if line.strip() == "# Configurar logging al inicio":
            lines.insert(i, "\n# Importar forms refactorizados (Sprint 4)\n")
            lines.insert(i+1, import_line)
            break

    # 2. Encontrar y eliminar la clase ConfiguracionForm completa
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if line.strip() == "class ConfiguracionForm(QWidget):":
            start_idx = i
        elif start_idx is not None and line.strip().startswith("class ") and "QWidget" in line:
            # La siguiente clase después de ConfiguracionForm
            end_idx = i
            break

    if start_idx and end_idx:
        # Eliminar la clase antigua y agregar comentario
        comment = [
            "\n",
            "# " + "="*78 + "\n",
            "# ConfiguracionForm - Movida a src/presentation/forms/configuracion_form.py\n",
            "# La clase antigua ha sido eliminada y reemplazada por versión refactorizada\n",
            "# que sigue el patrón MVP (Sprint 4)\n",
            "# " + "="*78 + "\n",
            "\n\n"
        ]

        # Reemplazar la clase antigua con el comentario
        lines[start_idx:end_idx] = comment

    # 3. Reemplazar el uso en MainWindow
    for i, line in enumerate(lines):
        if 'ConfiguracionForm()' in line and '⚙️ Configuración' in line:
            # Reemplazar la línea
            indent = len(line) - len(line.lstrip())
            lines[i] = (
                " " * indent +
                "# Usar ConfiguracionForm refactorizado (Sprint 4)\n"
            )
            lines.insert(
                i+1,
                " " * indent +
                "self.tabs.addTab("
                "ConfiguracionFormRefactorizado(self.session), "
                "\"⚙️ Configuración\")\n"
            )
            break

    # Escribir el archivo modificado
    with open('src/main.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print("✅ ConfiguracionForm integrado correctamente")
    print("   - Import agregado")
    print("   - Clase antigua eliminada")
    print("   - Uso actualizado en MainWindow")


if __name__ == "__main__":
    integrar_configuracion_form()
