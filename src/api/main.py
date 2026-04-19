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

import time
import uuid

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from api.auth import create_token_response, get_current_user
from api.routers import (
    cuotas_router,
    equidad_router,
    estadisticas_router,
    guardias_router,
    profesores_router,
)
from core.logging import get_logger
from core.observability.health import get_health_checker
from config.settings import get_settings

logger = get_logger(__name__)
_version = get_settings().app_version

# Rate limiter — máximo 60 peticiones/minuto por IP
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

# Crear aplicación FastAPI
app = FastAPI(
    title="Guardias de Patio API",
    description="API REST para gestión y análisis de guardias de patio",
    version=_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Adjuntar rate limiter al estado de la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Añade security headers HTTP a todas las respuestas (SEC-18)."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["API-Version"] = "1"
        return response


app.add_middleware(SecurityHeadersMiddleware)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Añade X-Correlation-ID, X-Request-ID y log estructurado por petición (API-10, API-15)."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request_id = str(uuid.uuid4())[:8]
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info(
        "[%s] %s %s → %s (%.3fs)",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration,
    )
    response.headers["X-Correlation-ID"] = correlation_id
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Error no controlado en %s", request.url)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_server_error", "message": "Error interno del servidor"}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": {"code": "validation_error", "message": str(exc.errors())}},
    )


# Endpoint de autenticación (público)
@app.post("/api/v1/auth/token", include_in_schema=True, tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return create_token_response(form_data)


# Registrar routers bajo /api/v1 (protegidos con JWT)
_auth = Depends(get_current_user)
app.include_router(cuotas_router, prefix="/api/v1", dependencies=[_auth])
app.include_router(equidad_router, prefix="/api/v1", dependencies=[_auth])
app.include_router(guardias_router, prefix="/api/v1", dependencies=[_auth])
app.include_router(profesores_router, prefix="/api/v1", dependencies=[_auth])
app.include_router(estadisticas_router, prefix="/api/v1", dependencies=[_auth])


@app.get("/")
def root():
    return {
        "nombre": "Guardias de Patio API",
        "version": _version,
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


@app.get("/health", tags=["sistema"], summary="Estado del sistema")
def health_check():
    try:
        checker = get_health_checker()
        status = checker.check_all()
        state = status.overall_state.value
        components = {c.name: c.state.value for c in status.components}
        http_code = 503 if status.is_unhealthy else 200
        return JSONResponse(
            status_code=http_code,
            content={"status": state, "version": _version, "components": components},
        )
    except (ValueError, TypeError, OSError) as e:
        return {"status": "healthy", "version": _version}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
