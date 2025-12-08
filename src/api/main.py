"""
API REST - FastAPI Application

Aplicación FastAPI que expone endpoints REST para el sistema de guardias.

Endpoints disponibles:
- /api/cuotas: Cálculo de cuotas
- /api/equidad: Análisis de equidad
- /api/guardias: Gestión de guardias
- /api/profesores: Información de profesores
- /api/estadisticas: Estadísticas y métricas

Documentación:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import (
    cuotas_router,
    equidad_router,
    estadisticas_router,
    guardias_router,
    profesores_router,
)

# Crear aplicación FastAPI
app = FastAPI(
    title="Guardias de Patio API",
    description="API REST para gestión y análisis de guardias de patio",
    version="3.2.1",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(cuotas_router, prefix="/api")
app.include_router(equidad_router, prefix="/api")
app.include_router(guardias_router, prefix="/api")
app.include_router(profesores_router, prefix="/api")
app.include_router(estadisticas_router, prefix="/api")


@app.get("/")
def root():
    """
    Endpoint raíz con información de la API.

    Returns:
        dict: Información de bienvenida y endpoints disponibles
    """
    return {
        "nombre": "Guardias de Patio API",
        "version": "3.2.1",
        "descripcion": "API REST para gestión y análisis de guardias de patio",
        "documentacion": {"swagger_ui": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "cuotas": "/api/cuotas",
            "equidad": "/api/equidad",
            "guardias": "/api/guardias",
            "profesores": "/api/profesores",
            "estadisticas": "/api/estadisticas",
        },
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.

    Returns:
        dict: Estado de salud de la API
    """
    return {"status": "healthy", "version": "3.2.1"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
