#!/bin/bash

# Script para ejecutar la API REST de Guardias de Patio

echo "🚀 Iniciando API REST de Guardias de Patio..."
echo ""
echo "Documentación disponible en:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc:      http://localhost:8000/redoc"
echo ""
echo "Endpoints disponibles:"
echo "  - GET /api/cuotas"
echo "  - GET /api/equidad"
echo "  - GET /api/guardias"
echo "  - GET /api/profesores"
echo "  - GET /api/estadisticas/resumen"
echo "  - GET /api/estadisticas/por-profesor"
echo ""
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Cambiar al directorio src
cd "$(dirname "$0")/../src" || exit

# Ejecutar con uvicorn
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
