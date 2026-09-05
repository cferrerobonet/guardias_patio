"""
Gestor de bloqueos por intentos fallidos de login (lockout).

Implementa:
- Máximo 5 intentos fallidos
- Bloqueo de 15 minutos tras 5 fallos
- Delay progresivo: 1s, 2s, 4s, 8s, 16s
- Reseteo automático después del timeout
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from core.logging import get_logger
from core.paths import get_user_data_directory

logger = get_logger(__name__)

LOCKOUT_FILE = "lockout.json"
MAX_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
PROGRESIVE_DELAYS = [1, 2, 4, 8, 16]  # segundos


class LockoutManager:
    """Gestor de intentos fallidos y bloqueos."""

    def __init__(self, user_hash: str):
        """
        Args:
            user_hash: Hash del usuario (para isollar lockouts por usuario)
        """
        self.user_hash = user_hash
        self.user_dir = get_user_data_directory(user_hash)
        self.lockout_file = self.user_dir / LOCKOUT_FILE

    def _load_lockout_data(self) -> dict:
        """Carga datos de lockout desde archivo o devuelve dict vacío."""
        if not self.lockout_file.exists():
            return {}
        try:
            with self.lockout_file.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error al cargar lockout data: {e}")
            return {}

    def _save_lockout_data(self, data: dict):
        """Guarda datos de lockout en archivo."""
        try:
            self.lockout_file.parent.mkdir(parents=True, exist_ok=True)
            with self.lockout_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error al guardar lockout data: {e}")

    def record_failed_attempt(self, username: str) -> tuple[bool, Optional[float]]:
        """
        Registra un intento fallido.

        Returns:
            (is_locked, delay_seconds)
            - is_locked: True si el usuario está bloqueado
            - delay_seconds: segundos de delay a aplicar antes del siguiente intento
        """
        data = self._load_lockout_data()

        if username not in data:
            data[username] = {
                "attempts": 0,
                "locked_until": None,
                "first_attempt_at": datetime.now(timezone.utc).isoformat(),
            }

        user_data = data[username]

        # Verificar si está bloqueado actualmente
        if user_data["locked_until"]:
            locked_until = datetime.fromisoformat(user_data["locked_until"])
            now = datetime.now(timezone.utc)
            if now < locked_until:
                remaining = (locked_until - now).total_seconds()
                logger.warning(f"Usuario {username} bloqueado. Desbloqueará en {remaining:.0f}s")
                self._save_lockout_data(data)
                return True, remaining

        # Limpiar bloqueo si ha expirado
        user_data["locked_until"] = None
        user_data["attempts"] = user_data.get("attempts", 0) + 1

        # Calcular delay progresivo
        attempt_num = user_data["attempts"]
        delay = PROGRESIVE_DELAYS[min(attempt_num - 1, len(PROGRESIVE_DELAYS) - 1)]

        logger.warning(f"Intento fallido {attempt_num}/{MAX_ATTEMPTS} para {username}. Delay: {delay}s")

        # Si llegó a máximo intentos, bloquear
        if user_data["attempts"] >= MAX_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            user_data["locked_until"] = locked_until.isoformat()
            user_data["attempts"] = 0  # Reset para el siguiente ciclo
            logger.error(f"Usuario {username} bloqueado por {LOCKOUT_DURATION_MINUTES} min")

        self._save_lockout_data(data)
        return False, delay

    def reset_attempts(self, username: str):
        """Resetea los intentos fallidos tras login exitoso."""
        data = self._load_lockout_data()
        if username in data:
            data[username] = {
                "attempts": 0,
                "locked_until": None,
                "first_attempt_at": None,
            }
            self._save_lockout_data(data)
            logger.info(f"Intentos reseteados para {username}")

    def is_locked(self, username: str) -> bool:
        """Devuelve True si el usuario está bloqueado."""
        data = self._load_lockout_data()
        if username not in data:
            return False

        user_data = data[username]
        if not user_data.get("locked_until"):
            return False

        locked_until = datetime.fromisoformat(user_data["locked_until"])
        now = datetime.now(timezone.utc)

        if now >= locked_until:
            # Desbloquear automáticamente
            data[username]["locked_until"] = None
            self._save_lockout_data(data)
            logger.info(f"Usuario {username} desbloqueado automáticamente")
            return False

        return True

    def get_remaining_lockout_time(self, username: str) -> Optional[float]:
        """Devuelve segundos restantes de bloqueo, o None si no está bloqueado."""
        data = self._load_lockout_data()
        if username not in data or not data[username].get("locked_until"):
            return None

        locked_until = datetime.fromisoformat(data[username]["locked_until"])
        now = datetime.now(timezone.utc)

        if now >= locked_until:
            return None

        return (locked_until - now).total_seconds()
