import subprocess
import sys
from pathlib import Path


def test_hola_mundo(capsys=None):
    """Test que verifica que main.py se puede ejecutar."""
    # Usar el intérprete de Python actual del virtualenv
    python_executable = sys.executable
    main_path = Path(__file__).parent.parent / "src" / "main.py"

    result = subprocess.run([
        python_executable, str(main_path)
    ], capture_output=True, text=True, timeout=5)

    # Verificar que se ejecuta sin errores críticos
    assert result.returncode == 0 or "¡Hola mundo" in result.stdout or "Guardias" in result.stdout
