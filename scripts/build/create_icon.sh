#!/bin/bash

# Script para crear icono .icns para macOS desde logo.png

set -e

echo "🎨 Creando icono .icns para macOS..."

# Verificar que existe logo.png
if [ ! -f "imagenes/logo.png" ]; then
    echo "❌ Error: No se encontró imagenes/logo.png"
    exit 1
fi

# Crear carpeta temporal para iconset
ICONSET="imagenes/icono.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Generar todos los tamaños necesarios para macOS
echo "📐 Generando múltiples tamaños..."

# Usando sips (herramienta nativa de macOS)
sips -z 16 16     imagenes/logo.png --out "$ICONSET/icon_16x16.png"
sips -z 32 32     imagenes/logo.png --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     imagenes/logo.png --out "$ICONSET/icon_32x32.png"
sips -z 64 64     imagenes/logo.png --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   imagenes/logo.png --out "$ICONSET/icon_128x128.png"
sips -z 256 256   imagenes/logo.png --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   imagenes/logo.png --out "$ICONSET/icon_256x256.png"
sips -z 512 512   imagenes/logo.png --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   imagenes/logo.png --out "$ICONSET/icon_512x512.png"
sips -z 1024 1024 imagenes/logo.png --out "$ICONSET/icon_512x512@2x.png"

# Crear el archivo .icns
echo "🎨 Creando archivo .icns..."
iconutil -c icns "$ICONSET" -o imagenes/icono.icns

# Limpiar carpeta temporal
rm -rf "$ICONSET"

echo "✅ Icono creado: imagenes/icono.icns"
