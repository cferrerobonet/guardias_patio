#!/bin/bash

# Script para crear DMG instalable de Guardias de Patio para macOS
# Requiere PyInstaller instalado

set -e  # Salir si hay error

echo "🚀 Iniciando proceso de construcción del DMG..."

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variables
APP_NAME="Guardias de Patio"
VERSION="2.7.0"
BUNDLE_ID="com.guardias-patio.app"
DMG_NAME="GuardiasDePatio-${VERSION}-macOS"

# Limpiar builds anteriores
echo -e "${BLUE}📦 Limpiando builds anteriores...${NC}"
rm -rf build dist
rm -f *.spec

# Verificar que PyInstaller está instalado
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}❌ PyInstaller no está instalado${NC}"
    echo "Instalando PyInstaller..."
    pip install pyinstaller
fi

# Crear el .app con PyInstaller
echo -e "${BLUE}🔨 Construyendo aplicación con PyInstaller...${NC}"
pyinstaller --noconfirm \
    --name="$APP_NAME" \
    --windowed \
    --onefile \
    --clean \
    --osx-bundle-identifier="$BUNDLE_ID" \
    --icon="imagenes/icono.icns" \
    --add-data="imagenes:imagenes" \
    --add-data="alembic.ini:." \
    --add-data="alembic:alembic" \
    --hidden-import="sqlalchemy.sql.default_comparator" \
    --hidden-import="PyQt6.QtCore" \
    --hidden-import="PyQt6.QtGui" \
    --hidden-import="PyQt6.QtWidgets" \
    --hidden-import="pydantic" \
    --hidden-import="alembic" \
    --collect-all="sqlalchemy" \
    --collect-all="alembic" \
    src/main.py

# Verificar que se creó el .app
if [ ! -d "dist/$APP_NAME.app" ]; then
    echo -e "${RED}❌ Error: No se pudo crear la aplicación${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Aplicación creada exitosamente${NC}"

# Crear carpeta temporal para el DMG
echo -e "${BLUE}📦 Preparando DMG...${NC}"
DMG_TEMP="dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

# Copiar aplicación a carpeta temporal
cp -R "dist/$APP_NAME.app" "$DMG_TEMP/"

# Crear link simbólico a /Applications
ln -s /Applications "$DMG_TEMP/Applications"

# Crear archivo README en el DMG
cat > "$DMG_TEMP/README.txt" << EOF
Guardias de Patio v${VERSION}
=============================

Instalación:
1. Arrastra "Guardias de Patio.app" a la carpeta "Applications"
2. La primera vez que abras la app, macOS pedirá permiso
3. Ve a Preferencias del Sistema > Privacidad y Seguridad
4. Haz click en "Abrir de todas formas"

Requisitos:
- macOS 10.14 (Mojave) o superior
- Aproximadamente 200 MB de espacio en disco

Soporte:
Para reportar problemas o sugerencias:
https://github.com/cferrerobonet/guardias_patio

© 2025 - Gestión de Guardias de Recreo
EOF

# Crear el DMG
echo -e "${BLUE}💿 Creando archivo DMG...${NC}"
DMG_PATH="dist/${DMG_NAME}.dmg"

# Eliminar DMG anterior si existe
rm -f "$DMG_PATH"

# Crear DMG temporal sin comprimir
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDRW \
    -size 500m \
    temp.dmg

# Montar el DMG para personalizarlo
echo -e "${BLUE}🎨 Personalizando DMG...${NC}"
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen temp.dmg | egrep '^/dev/' | sed 1q | awk '{print $1}')
VOLUME="/Volumes/$APP_NAME"

# Esperar a que se monte
sleep 2

# Configurar apariencia del DMG
if [ -d "$VOLUME" ]; then
    # Configurar vista de iconos
    echo '
       tell application "Finder"
         tell disk "'$APP_NAME'"
               open
               set current view of container window to icon view
               set toolbar visible of container window to false
               set statusbar visible of container window to false
               set the bounds of container window to {400, 100, 900, 500}
               set viewOptions to the icon view options of container window
               set arrangement of viewOptions to not arranged
               set icon size of viewOptions to 72
               set position of item "'$APP_NAME'.app" of container window to {125, 180}
               set position of item "Applications" of container window to {375, 180}
               set background picture of viewOptions to file ".background:background.png"
               update without registering applications
               delay 2
               close
         end tell
       end tell
    ' | osascript || true
    
    # Desmontar
    sync
    hdiutil detach "$DEVICE"
fi

# Convertir a DMG comprimido final
echo -e "${BLUE}🗜️  Comprimiendo DMG...${NC}"
hdiutil convert temp.dmg \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$DMG_PATH"

# Limpiar archivos temporales
rm -f temp.dmg
rm -rf "$DMG_TEMP"

# Verificar tamaño del DMG
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)

echo ""
echo -e "${GREEN}✅ ¡DMG creado exitosamente!${NC}"
echo -e "${GREEN}📦 Ubicación: $DMG_PATH${NC}"
echo -e "${GREEN}💾 Tamaño: $DMG_SIZE${NC}"
echo ""
echo -e "${BLUE}Para distribuir:${NC}"
echo "  1. Prueba el DMG montándolo y arrastrando la app a Applications"
echo "  2. Opcionalmente, firma el DMG con tu certificado de desarrollador"
echo "  3. Distribuye el archivo DMG"
echo ""
