"""
Autenticación JWT para la API REST.

Flujo:
  POST /api/v1/auth/token  →  {username, password}  →  {access_token, token_type}
  Header: Authorization: Bearer <token>

La contraseña se valida contra data/users.json (hash bcrypt almacenado).
El token contiene {"sub": username, "exp": timestamp}.

Seguridad:
- Lockout: 5 intentos fallidos → 15 min bloqueado con delay progresivo
"""

import hashlib
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from config.settings import get_settings
from core.security import LockoutManager

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def _create_access_token(username: str) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.api_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.api_secret_key, algorithm=settings.api_algorithm)


def _hash_username(username: str) -> str:
    """Hashea username para generar ID de usuario consistente."""
    return hashlib.sha256(username.encode()).hexdigest()[:16]


def _verify_user(username: str, password: str) -> tuple[bool, Optional[str]]:
    """Valida credenciales contra data/users.json usando bcrypt.
    
    Returns:
        (is_valid, error_message)
    """
    import json
    from pathlib import Path

    user_hash = _hash_username(username)
    lockout_mgr = LockoutManager(user_hash)

    # Verificar si está bloqueado
    if lockout_mgr.is_locked(username):
        remaining = lockout_mgr.get_remaining_lockout_time(username)
        error_msg = f"Usuario bloqueado por seguridad. Intente nuevamente en {remaining:.0f} segundos."
        return False, error_msg

    users_file = Path(__file__).resolve().parents[2] / "data" / "users.json"
    if not users_file.exists():
        return False, "Archivo de usuarios no encontrado"

    try:
        with users_file.open(encoding="utf-8") as f:
            users: list[dict] = json.load(f)
    except (OSError, ValueError) as e:
        return False, "Error al leer archivo de usuarios"

    for user in users:
        if user.get("username") == username:
            stored_hash = user.get("password_hash", "")
            if not stored_hash:
                locked, delay = lockout_mgr.record_failed_attempt(username)
                if delay:
                    time.sleep(min(delay, 2))  # Máximo 2s de delay
                return False, "Credenciales incorrectas"
            try:
                import bcrypt

                is_valid = bcrypt.checkpw(password.encode(), stored_hash.encode())
                if is_valid:
                    lockout_mgr.reset_attempts(username)
                    return True, None
                else:
                    locked, delay = lockout_mgr.record_failed_attempt(username)
                    if delay:
                        time.sleep(min(delay, 2))
                    if locked:
                        remaining = lockout_mgr.get_remaining_lockout_time(username)
                        return False, f"Usuario bloqueado. Intente en {remaining:.0f}s"
                    return False, "Credenciales incorrectas"
            except (ValueError, TypeError, OSError) as e:
                locked, delay = lockout_mgr.record_failed_attempt(username)
                if delay:
                    time.sleep(min(delay, 2))
                return False, "Error de autenticación"
    
    # Usuario no encontrado también cuenta como intento fallido
    locked, delay = lockout_mgr.record_failed_attempt(username)
    if delay:
        time.sleep(min(delay, 2))
    return False, "Credenciales incorrectas"


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
    is_valid, error_msg = _verify_user(form_data.username, form_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_msg or "Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}
