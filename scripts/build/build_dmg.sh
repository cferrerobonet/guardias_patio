#!/bin/bash
# Script para compilar Guardias de Patio en macOS
# Genera un archivo .dmg instalable

set -e

echo "════════════════════════════════════════════════════════════════"
echo "  Guardias de Patio - Build para macOS"
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
VERSION=$(python3 -c "import sys; sys.path.insert(0,'src'); from config.settings import get_settings; print(get_settings().app_version)")
SPEC_FILE="GuardiasDePatio.spec"
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

# Copiar la app sin atributos extendidos (iCloud Drive los añade y rompen codesign)
ditto --norsrc --noextattr --noqtn "$APP_PATH" "$TMP_DMG_DIR/${APP_NAME}.app"
xattr -cr "$TMP_DMG_DIR/${APP_NAME}.app"

# Firmar fuera de iCloud y verificar.
#
# Con un certificado Developer ID la aplicación se abre sin advertencias. Sin él
# se firma ad-hoc, que es lo mínimo para que macOS la ejecute, pero Gatekeeper
# seguirá diciendo que el desarrollador no está identificado (BLD-004).
#
# Para firmar de verdad, exportar antes:
#   APPLE_DEVELOPER_ID="Developer ID Application: Nombre (TEAMID)"
# Y para notarizar además:
#   APPLE_ID="correo@ejemplo.com"
#   APPLE_TEAM_ID="TEAMID"
#   APPLE_APP_PASSWORD="contraseña de aplicación"
if [ -n "${APPLE_DEVELOPER_ID:-}" ]; then
    echo "${BLUE}🔏 Firmando bundle con Developer ID...${NC}"
    codesign --force --deep --options runtime --timestamp \
        -s "$APPLE_DEVELOPER_ID" "$TMP_DMG_DIR/${APP_NAME}.app"
else
    echo "${BLUE}🔏 Firmando bundle (ad-hoc: sin certificado Developer ID)...${NC}"
    echo "  ⚠️  macOS dirá que la aplicación está dañada al abrirla: Gatekeeper"
    echo "     rechaza toda firma que no sea Developer ID notarizada (BLD-004)."
    echo "     El DMG lleva dentro las instrucciones para abrirla igualmente."
    codesign -s - --force --deep "$TMP_DMG_DIR/${APP_NAME}.app"
fi
codesign --verify --deep --strict "$TMP_DMG_DIR/${APP_NAME}.app"
echo "${GREEN}✓ Firma verificada${NC}"

# Crear enlace simbólico a Applications
ln -s /Applications "$TMP_DMG_DIR/Applications"

# Sin notarizar, macOS dice que la aplicación está dañada y propone la papelera.
# No lo está: es Gatekeeper rechazando una firma que no es de Apple. Quien instala
# necesita saberlo y necesita el comando, así que viajan dentro del propio DMG.
if [ -z "${APPLE_ID:-}" ]; then
    cat > "$TMP_DMG_DIR/LÉEME - si dice que está dañada.txt" <<'AVISO'
Si al abrir la aplicación macOS dice que "está dañada y no se puede abrir"
──────────────────────────────────────────────────────────────────────────

No está dañada. macOS bloquea cualquier aplicación que no esté firmada con un
certificado de pago de Apple, y este centro todavía no lo usa. El mensaje es el
mismo que daría un archivo corrupto, pero la causa es otra.

Para abrirla, una sola vez por ordenador:

  1. Arrastra la aplicación a la carpeta Aplicaciones, como siempre.
  2. Abre la aplicación Terminal (Launchpad → Otros → Terminal).
  3. Copia esta línea, pégala, y pulsa Intro:

     xattr -dr com.apple.quarantine "/Applications/Guardias de Patio.app"

  4. Abre la aplicación normalmente. No habrá que repetirlo en las
     siguientes actualizaciones salvo que vuelva a aparecer el aviso.

Ese comando sólo quita la marca de "descargado de internet". No modifica la
aplicación ni desactiva ninguna protección del sistema.
AVISO
fi

# Crear el DMG
hdiutil create \
    -volname "$APP_NAME $VERSION" \
    -srcfolder "$TMP_DMG_DIR" \
    -ov \
    -format UDZO \
    "$DMG_NAME"

# Notarizar y grapar el sello, si hay credenciales de Apple (BLD-004).
if [ -n "${APPLE_ID:-}" ] && [ -n "${APPLE_TEAM_ID:-}" ] && [ -n "${APPLE_APP_PASSWORD:-}" ]; then
    echo "${BLUE}📮 Enviando a notarizar (puede tardar unos minutos)...${NC}"
    xcrun notarytool submit "$DMG_NAME" \
        --apple-id "$APPLE_ID" \
        --team-id "$APPLE_TEAM_ID" \
        --password "$APPLE_APP_PASSWORD" \
        --wait
    echo "${BLUE}📎 Grapando el sello al DMG...${NC}"
    xcrun stapler staple "$DMG_NAME"
    echo "${GREEN}✓ DMG notarizado${NC}"
else
    echo "${BLUE}ℹ️  Sin credenciales de Apple: el DMG no se notariza.${NC}"
    echo "   Requiere una cuenta de Apple Developer activa."
fi

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

# Publicar GitHub Release con el DMG como asset
echo "${BLUE}🚀 Publicando GitHub Release v${VERSION}...${NC}"

if [ -n "${SKIP_RELEASE:-}" ]; then
    echo "${YELLOW}⏭  SKIP_RELEASE activo: no se publica el release (lo hará quien invocó el build)${NC}"
elif ! command -v gh &> /dev/null; then
    echo "${YELLOW}⚠️  GitHub CLI (gh) no encontrado. Instálalo con: brew install gh${NC}"
    echo "${YELLOW}   Luego sube el DMG manualmente: $DMG_NAME${NC}"
else
    TAG="v${VERSION}"

    # Si el tag ya existe en remoto, reutilizarlo; si no, crearlo
    if git ls-remote --tags origin "$TAG" | grep -q "$TAG"; then
        echo "  • Tag $TAG ya existe en remoto"
    else
        git tag "$TAG" 2>/dev/null || true
        git push origin "$TAG"
        echo "${GREEN}  ✓ Tag $TAG publicado${NC}"
    fi

    # Crear o actualizar el release y subir el DMG
    if gh release view "$TAG" &>/dev/null; then
        echo "  • Release $TAG ya existe, subiendo asset..."
        gh release upload "$TAG" "$DMG_NAME" --clobber
    else
        gh release create "$TAG" "$DMG_NAME" \
            --title "Guardias de Patio v${VERSION}" \
            --notes "## Guardias de Patio v${VERSION}

### Instalación (macOS)
1. Descarga el archivo \`$DMG_NAME\`
2. Abre el DMG y arrastra la aplicación a la carpeta Aplicaciones
3. Ejecuta la aplicación

La propia aplicación notificará automáticamente cuando haya una nueva versión disponible."
    fi

    echo "${GREEN}✓ Release publicado: https://github.com/cferrerobonet/guardias_patio/releases/tag/${TAG}${NC}"
fi
echo ""
