"""
Autenticación JWT para la API REST.

Flujo:
  POST /api/v1/auth/token  →  {username, password}  →  {access_token, token_type}
  Header: Authorization: Bearer <token>

La contraseña se valida contra data/users.json (hash bcrypt almacenado).
El token contiene {"sub": username, "exp": timestamp}.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from config.settings import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _create_access_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.api_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.api_secret_key, algorithm=settings.api_algorithm)


def _verify_user(username: str, password: str) -> bool:
    """Valida credenciales contra data/users.json usando bcrypt."""
    import json
    from pathlib import Path

    users_file = Path(__file__).resolve().parents[2] / "data" / "users.json"
    if not users_file.exists():
        return False

    try:
        with users_file.open(encoding="utf-8") as f:
            users: list[dict] = json.load(f)
    except Exception:
        return False

    for user in users:
        if user.get("username") == username:
            stored_hash = user.get("password_hash", "")
            if not stored_hash:
                return False
            try:
                import bcrypt

                return bcrypt.checkpw(password.encode(), stored_hash.encode())
            except Exception:
                return False
    return False


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency FastAPI. Verifica el token y retorna el username."""
    settings = get_settings()
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=[settings.api_algorithm])
        username: str | None = payload.get("sub")
        if not username:
            raise credentials_exc
        return username
    except jwt.ExpiredSignatureError:
        raise credentials_exc
    except jwt.InvalidTokenError:
        raise credentials_exc


def create_token_response(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    """Handler para POST /api/v1/auth/token."""
    if not _verify_user(form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}
