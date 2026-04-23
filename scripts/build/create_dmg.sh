#!/bin/bash
# Script para crear DMG instalable de Guardias de Patio
# PREREQUISITO: La app debe estar ya compilada en dist/Guardias de Patio.app
#
# Uso:
#   1. Compilar primero: ./build_simple.sh
#   2. Crear DMG: ./create_dmg.sh

set -e

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Variables
APP_NAME="Guardias de Patio"
VERSION="5.31.9"
DMG_NAME="GuardiasDePatio-${VERSION}-macOS"
APP_PATH="dist/${APP_NAME}.app"

echo "🎨 Creando instalador DMG para Guardias de Patio v${VERSION}"
echo ""

# Verificar que la app existe
if [ ! -d "$APP_PATH" ]; then
    echo -e "${RED}❌ Error: No se encontró la app compilada${NC}"
    echo "Ubicación esperada: $APP_PATH"
    echo ""
    echo "Por favor, compila primero la app con:"
    echo "  ./build_simple.sh"
    exit 1
fi

echo -e "${GREEN}✓ App encontrada: $APP_PATH${NC}"

# Crear carpeta temporal para el DMG
DMG_TEMP="dmg_temp"
rm -rf "$DMG_TEMP"
mkdir -p "$DMG_TEMP"

echo -e "${BLUE}📦 Preparando contenido del DMG...${NC}"

# Copiar la app al directorio temporal
cp -R "$APP_PATH" "$DMG_TEMP/"

# Crear symlink a /Applications
ln -s /Applications "$DMG_TEMP/Applications"

# Crear archivo README en el DMG
cat > "$DMG_TEMP/LEEME.txt" << 'EOF'
Guardias de Patio - Instalación

INSTALACIÓN:
1. Arrastra "Guardias de Patio.app" a la carpeta "Applications"
2. Abre "Guardias de Patio" desde tu carpeta de Aplicaciones
3. Si macOS te pregunta, confirma que quieres abrir la aplicación

PRIMERA EJECUCIÓN:
- Necesitarás crear un usuario administrador
- Los datos se guardarán en:
  ~/Library/Application Support/GuardiasDePatio/

REQUISITOS:
- macOS 11.0 o superior
- Apple Silicon (M1/M2/M3) o Intel

SOPORTE:
- Documentación: Incluida en la aplicación
- Versión: 5.31.6

¡Gracias por usar Guardias de Patio!
EOF

echo -e "${GREEN}✓ Contenido preparado${NC}"

# Eliminar DMG anterior si existe
DMG_PATH="dist/${DMG_NAME}.dmg"
rm -f "$DMG_PATH"

echo -e "${BLUE}💿 Creando archivo DMG...${NC}"

# Crear DMG temporal sin comprimir
hdiutil create -volname "$APP_NAME" \
    -srcfolder "$DMG_TEMP" \
    -ov -format UDRW \
    -size 500m \
    temp.dmg

echo -e "${BLUE}🎨 Personalizando DMG...${NC}"

# Montar el DMG para personalizarlo
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen temp.dmg | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')
VOLUME="/Volumes/$APP_NAME"

# Esperar a que se monte
sleep 2

# Configurar apariencia del DMG
if [ -d "$VOLUME" ]; then
    echo '
       tell application "Finder"
         tell disk "'$APP_NAME'"
               open
               set current view of container window to icon view
               set toolbar visible of container window to false
               set statusbar visible of container window to false
               set the bounds of container window to {400, 100, 920, 440}
               set viewOptions to the icon view options of container window
               set arrangement of viewOptions to not arranged
               set icon size of viewOptions to 72
               set position of item "'$APP_NAME'.app" of container window to {130, 150}
               set position of item "Applications" of container window to {390, 150}
               close
               open
               update without registering applications
               delay 2
         end tell
       end tell
    ' | osascript
    
    echo -e "${GREEN}✓ Apariencia configurada${NC}"
fi

# Desmontar el DMG temporal
hdiutil detach "${DEVICE}"
sleep 2

echo -e "${BLUE}🗜️  Comprimiendo DMG final...${NC}"

# Convertir a DMG comprimido final
hdiutil convert temp.dmg \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "$DMG_PATH"

# Limpiar
rm -f temp.dmg
rm -rf "$DMG_TEMP"

# Obtener tamaño del DMG
DMG_SIZE=$(du -h "$DMG_PATH" | cut -f1)

echo ""
echo -e "${GREEN}✅ ¡DMG CREADO EXITOSAMENTE!${NC}"
echo ""
echo "📍 Ubicación: $DMG_PATH"
echo "📦 Tamaño: $DMG_SIZE"
echo ""
echo "Para probar el DMG:"
echo "  open \"$DMG_PATH\""
echo ""
echo "Para distribuir:"
echo "  1. Prueba el DMG en otro Mac (o crea un usuario nuevo)"
echo "  2. Sube el archivo a tu plataforma de distribución"
echo ""
