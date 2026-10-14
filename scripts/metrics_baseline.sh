#!/bin/bash
# Script para generar métricas base del proyecto

echo "═══════════════════════════════════════════════════════"
echo "  MÉTRICAS BASE - Guardias de Patio"
echo "  Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════════════════"
echo

echo "📊 ESTADÍSTICAS DE CÓDIGO"
echo "──────────────────────────────────────────────────────"
echo "Total archivos .py:"
find src -name "*.py" | wc -l | xargs echo "  "
echo
echo "Total líneas de código:"
find src -name "*.py" -exec cat {} \; | wc -l | xargs echo "  "
echo
echo "Archivos > 500 líneas:"
find src -name "*.py" -exec wc -l {} + | awk '$1 > 500 {print "  "$1" líneas: "$2}' | sort -rn
echo

echo "🧪 TESTS"
echo "──────────────────────────────────────────────────────"
pytest --collect-only -q 2>/dev/null | tail -1 || echo "  Error al contar tests"
echo

echo "📂 ESTRUCTURA"
echo "──────────────────────────────────────────────────────"
echo "Módulos principales:"
ls -d src/*/ | xargs -I {} basename {} | xargs -I {} echo "  ✓ {}"
echo

echo "🔍 PROBLEMAS POTENCIALES"
echo "──────────────────────────────────────────────────────"
echo "Excepciones duplicadas:"
echo "  core/exceptions.py: $(wc -l < src/core/exceptions.py 2>/dev/null || echo 0) líneas"
echo "  utils/exceptions.py: $(wc -l < src/utils/exceptions.py 2>/dev/null || echo 0) líneas"
echo
echo "Acceso directo a BD desde presentation:"
grep -r "session.query" src/presentation/ 2>/dev/null | wc -l | xargs -I {} echo "  {} ocurrencias"
echo

echo "✅ Métricas generadas exitosamente"
echo "═══════════════════════════════════════════════════════"
