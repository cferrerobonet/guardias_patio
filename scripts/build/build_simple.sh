#!/bin/bash
# Script de compilación simple para Guardias de Patio
# 
# IMPORTANTE: Este script usa PyInstaller directamente sin archivo .spec
# Motivo: Los archivos .spec tienen un bug con PyQt6 en macOS que causa
# que la compilación se cuelgue en "Building PKG". Usar siempre este método.
#
# ⚠️  ADVERTENCIA CRÍTICA: NO EXCLUIR matplotlib ni pandas
# La app requiere matplotlib para el panel de estadísticas (panel_estadisticas.py).
# Si se excluyen con --exclude-module, la app compilará pero crasheará al iniciar.
# Error resultante: "ModuleNotFoundError: No module named 'matplotlib'"
#
# Documentación completa: documentacion/archivo/SOLUCION_COMPILACION.md
#
# Este método:
# ✅ Evita problemas con symlinks de PyQt6
# ✅ Funciona tanto con 'open' como con ejecución directa
# ✅ Usa rutas adaptativas para desarrollo y producción
# ✅ Incluye matplotlib/pandas (REQUERIDOS - no excluir)

echo "=== Compilación de Guardias de Patio ==="
echo "Fecha: $(date)"
echo ""

# Verificar Python 3.11 en el entorno virtual del proyecto
PYTHON_PATH="$(pwd)/.venv/bin/python"
if [ ! -f "$PYTHON_PATH" ]; then
    echo "❌ Error: Python del entorno virtual no encontrado en $PYTHON_PATH"
    echo "Activa/crea el entorno con: python3.11 -m venv .venv && source .venv/bin/activate"
    exit 1
fi

echo "✓ Python encontrado: $("$PYTHON_PATH" --version)"

# Verificar PyInstaller
if ! "$PYTHON_PATH" -m PyInstaller --version > /dev/null 2>&1; then
    echo "❌ Error: PyInstaller no está instalado"
    echo "Instala con: $PYTHON_PATH -m pip install pyinstaller"
    exit 1
fi

echo "✓ PyInstaller encontrado: $("$PYTHON_PATH" -m PyInstaller --version)"
echo ""

# Limpiar compilaciones anteriores
echo "Limpiando directorios build y dist..."
rm -rf build dist

echo ""
echo "⚠️  NOTA IMPORTANTE:"
echo "La app compilada NO incluirá datos de desarrollo (users.json, bases de datos)."
echo "Los usuarios deberán registrarse de nuevo en la aplicación compilada."
echo ""

# Compilar
echo "Iniciando compilación..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⚠️  DEPENDENCIAS INCLUIDAS (NO EXCLUIR):"
echo "   • matplotlib - REQUERIDO por panel_estadisticas.py"
echo "   • pandas     - REQUERIDO por análisis de datos"
echo ""
echo "   Excluir estos módulos causa crash inmediato al iniciar la app."
echo "   Tamaño del DMG: ~100 MB (necesario para funcionalidad completa)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# IMPORTANTE: NO usar archivos .spec, causará que se cuelgue la compilación
# Usar siempre comando directo de PyInstaller
#
# ⚠️  NO AGREGAR: --exclude-module=matplotlib --exclude-module=pandas
# Estos módulos son REQUERIDOS. Si se excluyen, la app crasheará.
"$PYTHON_PATH" -m PyInstaller \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name "Guardias de Patio" \
    --icon="imagenes/icono.icns" \
    --add-data="imagenes:imagenes" \
    --add-data="alembic.ini:." \
    --add-data="alembic:alembic" \
    --exclude-module=tkinter \
    --collect-all dependency_injector \
    --hidden-import=logging.config \
    --osx-bundle-identifier="com.guardias-patio.app" \
    src/main.py

# Verificar resultado
if [ -d "dist/Guardias de Patio.app" ]; then
    echo ""
    echo "✅ ¡COMPILACIÓN EXITOSA!"
    echo ""
    echo "Ubicación: dist/Guardias de Patio.app"
    echo "Tamaño del ejecutable:"
    ls -lh "dist/Guardias de Patio.app/Contents/MacOS/Guardias de Patio"
    echo ""
    echo "Para probar la app, ejecuta:"
    echo "  open \"dist/Guardias de Patio.app\""
    echo ""
    echo "Para crear un DMG, ejecuta:"
    echo "  ./build_dmg.sh"
else
    echo ""
    echo "❌ Error: La compilación falló"
    echo "Revisa los logs arriba para más detalles"
    exit 1
fi
