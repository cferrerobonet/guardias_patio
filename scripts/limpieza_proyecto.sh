#!/bin/bash
# Script de limpieza de archivos obsoletos del proyecto

cd "$(dirname "$0")/.." || exit 1

echo "========================================"
echo "LIMPIEZA DE ARCHIVOS OBSOLETOS"
echo "========================================"
echo ""

# 1. Eliminar logs de regeneración (obsoletos)
echo "1. Eliminando logs de regeneración obsoletos..."
rm -f regeneracion.log regeneracion2.log regeneracion3.log test_v3_output.log benchmark_results.log
echo "   ✓ Logs eliminados"
echo ""

# 2. Eliminar build y dist (se regeneran en cada compilación)
echo "2. Limpiando directorios de compilación..."
rm -rf build/ dist/
echo "   ✓ Directorios build/ y dist/ eliminados"
echo ""

# 3. Eliminar DMG de distribución (versión vieja, se regenera)
echo "3. Eliminando DMG de distribución anterior..."
rm -f *.dmg checksums_v2.9.1.txt
echo "   ✓ DMG eliminado"
echo ""

# 4. Eliminar .spec obsoletos (mantener solo uno actualizado si existe)
echo "4. Revisando archivos .spec..."
if [ -f "GuardiasDePatio.spec" ]; then
    echo "   ℹ Manteniendo GuardiasDePatio.spec"
fi
echo ""

# 5. Limpiar documentación obsoleta
echo "5. Reorganizando documentación..."

# Mover archivos de raíz de documentacion a carpetas apropiadas
if [ -f "documentacion/CHANGELOG_v2.9.md" ]; then
    mv documentacion/CHANGELOG_v2.9.md documentacion/versiones/ 2>/dev/null || true
    echo "   ✓ CHANGELOG_v2.9.md → versiones/"
fi

if [ -f "documentacion/GUIA_DISTRIBUCION_v2.9.1.md" ]; then
    mv documentacion/GUIA_DISTRIBUCION_v2.9.1.md documentacion/build/ 2>/dev/null || true
    echo "   ✓ GUIA_DISTRIBUCION_v2.9.1.md → build/"
fi

echo ""

# 6. Eliminar archivos de documentación duplicados/obsoletos
echo "6. Eliminando documentación obsoleta/duplicada..."

# En tecnico/: Eliminar archivos que ahora están consolidados
rm -f documentacion/tecnico/matriz-horario-dia-recreo.md \
      documentacion/tecnico/resumen-matriz-horario.md \
      documentacion/tecnico/caracteristicas-sistema.md 2>/dev/null || true
echo "   ✓ Documentos obsoletos de tecnico/ eliminados"

# En guias/: Eliminar duplicados
rm -f documentacion/guias/ejemplos-uso.md 2>/dev/null || true
echo "   ✓ Documentos obsoletos de guias/ eliminados"

echo ""

# 7. Verificar estado final
echo "7. Estado final del proyecto:"
echo "   - Usuarios registrados: $(cat users.json | grep -c '@')"
echo "   - Bases de datos activas: $(find ./data/users -maxdepth 1 -type d | tail -n +2 | wc -l | tr -d ' ')"
echo "   - Documentos en /documentacion: $(find documentacion -name "*.md" | wc -l | tr -d ' ')"
echo ""

echo "========================================"
echo "✓ LIMPIEZA COMPLETADA"
echo "========================================"
