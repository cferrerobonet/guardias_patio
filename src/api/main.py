"""
API REST - FastAPI Application

Aplicación FastAPI que expone endpoints REST para el sistema de guardias.

Endpoints disponibles:
- /api/v1/cuotas: Cálculo de cuotas
- /api/v1/equidad: Análisis de equidad
- /api/v1/guardias: Gestión de guardias
- /api/v1/profesores: Información de profesores
- /api/v1/estadisticas: Estadísticas y métricas

Documentación:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import (
    cuotas_router,
    equidad_router,
    estadisticas_router,
    guardias_router,
    profesores_router,
)
from core.logging import get_logger
from core.observability.health import get_health_checker

logger = get_logger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="Guardias de Patio API",
    description="API REST para gestión y análisis de guardias de patio",
    version="3.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "detail": "Error interno del servidor"},
    )


# Registrar routers bajo /api/v1
app.include_router(cuotas_router, prefix="/api/v1")
app.include_router(equidad_router, prefix="/api/v1")
app.include_router(guardias_router, prefix="/api/v1")
app.include_router(profesores_router, prefix="/api/v1")
app.include_router(estadisticas_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "nombre": "Guardias de Patio API",
        "version": "3.3.0",
        "descripcion": "API REST para gestión y análisis de guardias de patio",
        "documentacion": {"swagger_ui": "/docs", "redoc": "/redoc"},
        "endpoints": {
            "cuotas": "/api/v1/cuotas",
            "equidad": "/api/v1/equidad",
            "guardias": "/api/v1/guardias",
            "profesores": "/api/v1/profesores",
            "estadisticas": "/api/v1/estadisticas",
        },
    }


@app.get("/health")
def health_check():
    try:
        checker = get_health_checker()
        status = checker.check_all()
        state = status.overall_state.value
        components = {c.name: c.state.value for c in status.components}
        http_code = 503 if status.is_unhealthy else 200
        return JSONResponse(
            status_code=http_code,
            content={"status": state, "version": "3.3.0", "components": components},
        )
    except Exception:
        return {"status": "healthy", "version": "3.3.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
