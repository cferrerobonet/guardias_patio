"""Use Case: Actualizar un perfil existente."""


from application.dtos.perfil_dto import ActualizarPerfilDTO, PerfilDTO
from core.exceptions import NotFoundError, ValidationError
from core.paths import get_data_directory
from database.db_manager import get_current_user_id, user_has_database
from sync.sync_manager import UserAuth


class ActualizarPerfilUseCase:
    """Actualiza los datos de un perfil existente."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self, dto: ActualizarPerfilDTO) -> PerfilDTO:
        """
        Actualiza un perfil existente.

        Args:
            dto: DTO con los nuevos datos del perfil

        Returns:
            PerfilDTO actualizado

        Raises:
            NotFoundError: Si el perfil no existe
            ValidationError: Si los datos son inválidos
        """
        # Validaciones
        if not dto.email or not dto.email.strip():
            raise ValidationError("El email es obligatorio")

        if "@" not in dto.email or "." not in dto.email:
            raise ValidationError("El email no es válido")

        # Verificar que existe
        if dto.username not in self.user_auth.users:
            raise NotFoundError(f"No existe el usuario '{dto.username}'")

        # Actualizar email
        self.user_auth.users[dto.username]["email"] = dto.email.strip()
        self.user_auth._save_users()

        # Retornar DTO actualizado
        current_user = get_current_user_id()
        logo_path = get_data_directory() / "imagenes" / f"{dto.username}.png"

        return PerfilDTO(
            username=dto.username,
            email=dto.email.strip(),
            tiene_bd=user_has_database(dto.username),
            tiene_logo=logo_path.exists(),
            es_actual=dto.username == current_user,
            ruta_logo=str(logo_path) if logo_path.exists() else None,
        )
