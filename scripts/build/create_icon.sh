#!/bin/bash

# Crea el icono .icns de macOS desde imagenes/icono.png (el icono de la app,
# 1024×1024 con transparencia). El logo de EPLA (logo.png) no es el icono: se
# queda dentro de la app, en cabeceras, pantalla de inicio, PDF y correos.

set -e

ORIGEN="imagenes/icono.png"

echo "🎨 Creando icono .icns para macOS..."

if [ ! -f "$ORIGEN" ]; then
    echo "❌ Error: No se encontró $ORIGEN"
    exit 1
fi

# Crear carpeta temporal para iconset
ICONSET="imagenes/icono.iconset"
rm -rf "$ICONSET"
mkdir -p "$ICONSET"

# Generar todos los tamaños necesarios para macOS
echo "📐 Generando múltiples tamaños..."

# Usando sips (herramienta nativa de macOS)
sips -z 16 16     "$ORIGEN" --out "$ICONSET/icon_16x16.png"
sips -z 32 32     "$ORIGEN" --out "$ICONSET/icon_16x16@2x.png"
sips -z 32 32     "$ORIGEN" --out "$ICONSET/icon_32x32.png"
sips -z 64 64     "$ORIGEN" --out "$ICONSET/icon_32x32@2x.png"
sips -z 128 128   "$ORIGEN" --out "$ICONSET/icon_128x128.png"
sips -z 256 256   "$ORIGEN" --out "$ICONSET/icon_128x128@2x.png"
sips -z 256 256   "$ORIGEN" --out "$ICONSET/icon_256x256.png"
sips -z 512 512   "$ORIGEN" --out "$ICONSET/icon_256x256@2x.png"
sips -z 512 512   "$ORIGEN" --out "$ICONSET/icon_512x512.png"
sips -z 1024 1024 "$ORIGEN" --out "$ICONSET/icon_512x512@2x.png"

# Crear el archivo .icns
echo "🎨 Creando archivo .icns..."
iconutil -c icns "$ICONSET" -o imagenes/icono.icns

# Limpiar carpeta temporal
rm -rf "$ICONSET"

echo "✅ Icono creado: imagenes/icono.icns"
