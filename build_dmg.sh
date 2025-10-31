#!/bin/bash
# Script para compilar Guardias de Patio en macOS
# Genera un archivo .dmg instalable

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Guardias de Patio v2.9.1 - Build para macOS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
APP_NAME="Guardias de Patio"
VERSION="2.9.1"
SPEC_FILE="Guardias de Patio.spec"
DMG_NAME="GuardiasPatio_v${VERSION}_macOS.dmg"

echo "${BLUE}📋 Configuración:${NC}"
echo "  • Aplicación: $APP_NAME"
echo "  • Versión: $VERSION"
echo "  • Archivo spec: $SPEC_FILE"
echo "  • DMG salida: $DMG_NAME"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "$SPEC_FILE" ]; then
    echo "${RED}❌ Error: No se encuentra $SPEC_FILE${NC}"
    echo "   Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Verificar PyInstaller
echo "${BLUE}🔍 Verificando PyInstaller...${NC}"
if ! command -v pyinstaller &> /dev/null; then
    echo "${YELLOW}⚠️  PyInstaller no encontrado. Instalando...${NC}"
    pip install pyinstaller
fi
echo "${GREEN}✓ PyInstaller disponible${NC}"
echo ""

# Limpiar builds anteriores
echo "${BLUE}🧹 Limpiando builds anteriores...${NC}"
rm -rf build dist
echo "${GREEN}✓ Limpieza completada${NC}"
echo ""

# Compilar con PyInstaller
echo "${BLUE}🔨 Compilando aplicación...${NC}"
pyinstaller "$SPEC_FILE" --clean --noconfirm
echo "${GREEN}✓ Compilación completada${NC}"
echo ""

# Verificar que se creó la app
APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "${RED}❌ Error: No se generó $APP_PATH${NC}"
    exit 1
fi
echo "${GREEN}✓ Aplicación creada: $APP_PATH${NC}"
echo ""

# Crear DMG
echo "${BLUE}💿 Creando DMG instalable...${NC}"

# Crear directorio temporal
TMP_DMG_DIR="$(mktemp -d)"
echo "  • Directorio temporal: $TMP_DMG_DIR"

# Copiar la app
cp -R "$APP_PATH" "$TMP_DMG_DIR/"

# Crear enlace simbólico a Applications
ln -s /Applications "$TMP_DMG_DIR/Applications"

# Crear el DMG
hdiutil create \
    -volname "$APP_NAME $VERSION" \
    -srcfolder "$TMP_DMG_DIR" \
    -ov \
    -format UDZO \
    "$DMG_NAME"

# Limpiar
rm -rf "$TMP_DMG_DIR"

echo "${GREEN}✓ DMG creado: $DMG_NAME${NC}"
echo ""

# Mostrar información del DMG
DMG_SIZE=$(du -h "$DMG_NAME" | cut -f1)
echo "${BLUE}📊 Información del instalador:${NC}"
echo "  • Archivo: $DMG_NAME"
echo "  • Tamaño: $DMG_SIZE"
echo ""

echo "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo "${GREEN}✅ BUILD COMPLETADO EXITOSAMENTE${NC}"
echo "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "${YELLOW}📦 Para distribuir:${NC}"
echo "  1. Prueba el DMG: open $DMG_NAME"
echo "  2. Arrastra '$APP_NAME.app' a Applications"
echo "  3. Ejecuta la aplicación"
echo "  4. Si todo funciona, sube el DMG a GitHub Releases"
echo ""
