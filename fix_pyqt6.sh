#!/bin/bash
# Script para arreglar la instalación de PyQt6 en macOS
# El problema: pip install no copia correctamente la carpeta Qt6/

set -e

echo "🔧 Arreglando instalación de PyQt6..."

# Activar venv
source .venv/bin/activate

# Directorio de trabajo temporal
TMPDIR=$(mktemp -d)
cd "$TMPDIR"

echo "📦 Descargando PyQt6-Qt6..."
pip download PyQt6-Qt6==6.7.3 --no-deps

echo "📂 Desempaquetando wheel..."
unzip -q PyQt6_Qt6-6.7.3-*.whl

# Ruta de destino
SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])")
DEST="$SITE_PACKAGES/PyQt6"

echo "📋 Copiando frameworks Qt6..."
if [ -d "$DEST/Qt6" ]; then
    echo "  ⚠️  Eliminando Qt6 anterior..."
    rm -rf "$DEST/Qt6"
fi

cp -R PyQt6/Qt6 "$DEST/"

echo "✅ Qt6 instalado en: $DEST/Qt6"
echo "✅ Frameworks disponibles:"
ls -1 "$DEST/Qt6/lib" | grep -i "\.framework$" | head -n 5
echo "   ... y $(ls -1 "$DEST/Qt6/lib" | grep -i "\.framework$" | wc -l | xargs) frameworks en total"

# Limpiar
cd -
rm -rf "$TMPDIR"

echo ""
echo "✅ PyQt6 arreglado correctamente"
echo "   Ahora puedes ejecutar: ./run_app.sh"
