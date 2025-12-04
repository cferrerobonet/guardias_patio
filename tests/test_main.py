import subprocess
import sys
from pathlib import Path

import pytest


def test_main_importable():
    """Test que verifica que el módulo main se puede importar sin errores."""
    # Solo verificamos que la sintaxis del módulo es correcta
    # No intentamos ejecutar la GUI porque requiere interacción
    python_executable = sys.executable
    main_path = Path(__file__).parent.parent / "src" / "main.py"

    # Compilar el archivo para verificar sintaxis sin ejecutarlo
    result = subprocess.run(
        [python_executable, "-m", "py_compile", str(main_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )

    # Verificar que compila sin errores de sintaxis
    assert result.returncode == 0, f"Error de sintaxis: {result.stderr}"


@pytest.mark.skip(reason="Test GUI: requiere entorno gráfico y no termina automáticamente")
def test_hola_mundo():
    """Test que verifica que main.py se puede ejecutar (GUI, requiere display)."""
    python_executable = sys.executable
    main_path = Path(__file__).parent.parent / "src" / "main.py"

    result = subprocess.run(
        [python_executable, str(main_path)],
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert result.returncode == 0 or "¡Hola mundo" in result.stdout or "Guardias" in result.stdout
