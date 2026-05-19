#!/bin/bash
# Limpieza de bases de datos - Conservar solo la BD de 67 profesores

set -e

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "================================================================================"
echo "LIMPIEZA DE BASES DE DATOS"
echo "================================================================================"
echo ""

# BD a conservar
CONSERVAR="./data/users/0db13e2857239ed8/guardias_patio.db"

# BDs a eliminar
BDS_ELIMINAR=(
    "./data/66f06c9433d74e80/guardias.db"
    "./data/users/0db13e2857239ed8/guardias.db"
    "./data/users/66f06c9433d74e80/guardias_patio.db"
    "./guardias_patio.db"
    "./src/guardias_patio.db"
)

# Directorios vacíos a limpiar
DIRS_LIMPIAR=(
    "./data/66f06c9433d74e80"
    "./data/users/66f06c9433d74e80"
)

echo -e "${GREEN}✓ BD A CONSERVAR:${NC}"
echo "  - $CONSERVAR (67 profesores)"
echo ""

echo -e "${RED}✗ BDs A ELIMINAR:${NC}"
for db in "${BDS_ELIMINAR[@]}"; do
    if [ -f "$db" ]; then
        echo "  - $db"
    fi
done
echo ""

echo -e "${YELLOW}⚠ Directorios a limpiar (si quedan vacíos):${NC}"
for dir in "${DIRS_LIMPIAR[@]}"; do
    if [ -d "$dir" ]; then
        echo "  - $dir"
    fi
done
echo ""

# Confirmación
echo -e "${YELLOW}¿Deseas continuar con la limpieza? (s/N):${NC} "
read -r respuesta

if [[ ! "$respuesta" =~ ^[Ss]$ ]]; then
    echo ""
    echo -e "${BLUE}Limpieza cancelada${NC}"
    exit 0
fi

echo ""
echo "================================================================================"
echo "EJECUTANDO LIMPIEZA..."
echo "================================================================================"
echo ""

# Eliminar BDs
eliminadas=0
for db in "${BDS_ELIMINAR[@]}"; do
    if [ -f "$db" ]; then
        echo -e "${RED}✗ Eliminando:${NC} $db"
        rm "$db"
        eliminadas=$((eliminadas + 1))
    fi
done

echo ""

# Limpiar directorios vacíos
for dir in "${DIRS_LIMPIAR[@]}"; do
    if [ -d "$dir" ]; then
        # Verificar si está vacío
        if [ -z "$(ls -A "$dir")" ]; then
            echo -e "${YELLOW}🗑 Eliminando directorio vacío:${NC} $dir"
            rmdir "$dir"
        else
            echo -e "${BLUE}ℹ Directorio no vacío (conservando):${NC} $dir"
        fi
    fi
done

echo ""
echo "================================================================================"
echo "RESUMEN"
echo "================================================================================"
echo -e "${GREEN}✓ BDs eliminadas: $eliminadas${NC}"
echo -e "${GREEN}✓ BD conservada: $CONSERVAR${NC}"
echo ""

# Verificar que la BD conservada existe
if [ -f "$CONSERVAR" ]; then
    size=$(du -h "$CONSERVAR" | cut -f1)
    echo -e "${GREEN}✓ BD conservada verificada: $size${NC}"
else
    echo -e "${RED}❌ ERROR: La BD conservada no existe!${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Limpieza completada exitosamente!${NC}"
echo ""
