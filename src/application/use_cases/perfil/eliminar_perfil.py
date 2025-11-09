"""Use Case: Eliminar un perfil de usuario."""

from pathlib import Path

from core.exceptions import NotFoundError, ValidationError
from database.db_manager import delete_user_database, get_current_user_id
from sync.sync_manager import UserAuth


class EliminarPerfilUseCase:
    """Elimina un perfil de usuario y todos sus datos asociados."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self, username: str) -> bool:
        """
        Elimina un perfil y sus datos.

        Args:
            username: Nombre del usuario a eliminar

        Returns:
            True si se eliminó correctamente

        Raises:
            NotFoundError: Si el perfil no existe
            ValidationError: Si se intenta eliminar el perfil actual
        """
        # Validar que no sea el usuario actual
        current_user = get_current_user_id()
        if username == current_user:
            raise ValidationError("No puedes eliminar tu propio perfil mientras estás logueado")

        # Verificar que existe
        if username not in self.user_auth.users:
            raise NotFoundError(f"No existe el usuario '{username}'")

        # Eliminar base de datos
        delete_user_database(username)

        # Eliminar logo si existe
        logo_path = Path("imagenes") / f"{username}.png"
        if logo_path.exists():
            logo_path.unlink()

        # Eliminar del sistema de autenticación usando unregister_user
        self.user_auth.unregister_user(username)

        return True
