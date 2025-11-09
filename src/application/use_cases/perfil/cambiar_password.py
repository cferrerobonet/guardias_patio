"""Use Case: Cambiar contraseña del usuario actual."""

import hashlib

from application.dtos.perfil_dto import CambiarPasswordDTO
from core.exceptions import ValidationError
from database.db_manager import get_current_user_id
from sync.sync_manager import UserAuth


class CambiarPasswordUseCase:
    """Cambia la contraseña del usuario actual."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self, dto: CambiarPasswordDTO) -> bool:
        """
        Cambia la contraseña del usuario.

        Args:
            dto: DTO con las contraseñas

        Returns:
            True si se cambió correctamente

        Raises:
            ValidationError: Si las validaciones fallan
        """
        # Solo se puede cambiar la contraseña del usuario actual
        current_user = get_current_user_id()
        if dto.username != current_user:
            raise ValidationError("Solo puedes cambiar tu propia contraseña")

        # Validar que las contraseñas nuevas coinciden
        if dto.password_nueva != dto.password_confirmacion:
            raise ValidationError("Las contraseñas nuevas no coinciden")

        # Validar longitud mínima
        if len(dto.password_nueva) < 4:
            raise ValidationError("La contraseña debe tener al menos 4 caracteres")

        # Verificar contraseña actual usando authenticate
        if not self.user_auth.authenticate(dto.username, dto.password_actual):
            raise ValidationError("La contraseña actual es incorrecta")

        # Cambiar contraseña
        if dto.username in self.user_auth.users:
            # Hashear nueva contraseña (igual que en UserAuth)
            password_hash = hashlib.sha256(dto.password_nueva.encode()).hexdigest()
            self.user_auth.users[dto.username]["password_hash"] = password_hash
            self.user_auth._save_users()
            return True

        raise ValidationError("Error al cambiar la contraseña")
