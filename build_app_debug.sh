#!/bin/bash

# Script de compilación con depuración para Guardias de Patio
# Incluye verificaciones y modo debug para diagnosticar problemas

set -e  # Salir en caso de error

# Usar Python 3.11 específicamente
PYTHON="/opt/homebrew/bin/python3.11"

echo "🔍 Verificando entorno de compilación..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar Python
if ! command -v $PYTHON &> /dev/null; then
    echo "❌ Python 3.11 no encontrado en $PYTHON"
    exit 1
fi
echo "✅ Python: $($PYTHON --version)"

# Verificar PyInstaller
if ! $PYTHON -c "import PyInstaller" &> /dev/null; then
    echo "❌ PyInstaller no instalado"
    echo "   Ejecuta: $PYTHON -m pip install pyinstaller"
    exit 1
fi
echo "✅ PyInstaller instalado"

# Verificar dependencias críticas
echo ""
echo "🔍 Verificando dependencias críticas..."
for module in PyQt6 sqlalchemy alembic pydantic paramiko; do
    if $PYTHON -c "import $module" &> /dev/null 2>&1; then
        echo "   ✅ $module"
    else
        echo "   ❌ $module NO ENCONTRADO"
        exit 1
    fi
done

# Verificar archivos necesarios
echo ""
echo "🔍 Verificando archivos necesarios..."
if [ ! -f "src/main.py" ]; then
    echo "❌ src/main.py no encontrado"
    exit 1
fi
echo "✅ src/main.py existe"

if [ ! -f "imagenes/icono.icns" ]; then
    echo "❌ imagenes/icono.icns no encontrado"
    exit 1
fi
echo "✅ imagenes/icono.icns existe"

if [ ! -f "Guardias de Patio.spec" ]; then
    echo "❌ Guardias de Patio.spec no encontrado"
    exit 1
fi
echo "✅ Guardias de Patio.spec existe"

# Limpiar builds anteriores
echo ""
echo "🧹 Limpiando builds anteriores..."
rm -rf build dist
echo "✅ Limpieza completada"

# Compilar con PyInstaller
echo ""
echo "🔨 Compilando aplicación (modo debug)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PYTHON -m PyInstaller --clean --noconfirm "Guardias de Patio.spec"

# Verificar que se creó la app
if [ ! -d "dist/Guardias de Patio.app" ]; then
    echo "❌ La aplicación no se compiló correctamente"
    exit 1
fi

echo ""
echo "✅ Compilación completada exitosamente"
echo ""
echo "📦 Aplicación creada en: dist/Guardias de Patio.app"
echo ""
echo "🧪 Para probar la aplicación:"
echo "   open 'dist/Guardias de Patio.app'"
echo ""
echo "📋 Para ver logs de ejecución:"
echo "   1. Abre Console.app"
echo "   2. Busca 'Guardias de Patio'"
echo "   3. O ejecuta en terminal:"
echo "      'dist/Guardias de Patio.app/Contents/MacOS/Guardias de Patio'"
echo ""

# Mostrar información del bundle
echo "ℹ️  Información del bundle:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
du -sh "dist/Guardias de Patio.app"
ls -lh "dist/Guardias de Patio.app/Contents/MacOS/"
