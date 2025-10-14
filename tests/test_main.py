import subprocess


def test_hola_mundo(capsys=None):
    result = subprocess.run([
        "python", "src/main.py"
    ], capture_output=True, text=True)
    assert "¡Hola mundo desde Guardias de Patio!" in result.stdout
