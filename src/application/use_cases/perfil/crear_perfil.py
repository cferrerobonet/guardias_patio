"""Use Case: Crear un nuevo perfil de usuario."""


from application.dtos.perfil_dto import CrearPerfilDTO, PerfilDTO
from core.exceptions import ValidationError
from database.db_manager import create_user_database, get_current_user_id
from sync.sync_manager import UserAuth


class CrearPerfilUseCase:
    """Crea un nuevo perfil de usuario con su base de datos."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self, dto: CrearPerfilDTO) -> PerfilDTO:
        """
        Crea un nuevo perfil.

        Args:
            dto: DTO con los datos del nuevo perfil

        Returns:
            PerfilDTO del perfil creado

        Raises:
            ValidationError: Si los datos son inválidos o el usuario ya existe
        """
        # Validaciones
        if not dto.username or not dto.username.strip():
            raise ValidationError("El nombre de usuario es obligatorio")

        if not dto.email or not dto.email.strip():
            raise ValidationError("El email es obligatorio")

        if "@" not in dto.email or "." not in dto.email:
            raise ValidationError("El email no es válido")

        if not dto.password or len(dto.password) < 4:
            raise ValidationError("La contraseña debe tener al menos 4 caracteres")

        username = dto.username.strip()
        email = dto.email.strip()

        # Verificar que no exista
        if username in self.user_auth.users:
            raise ValidationError(f"Ya existe un usuario con el nombre '{username}'")

        # Crear usuario en UserAuth con register_user
        if not self.user_auth.register_user(username, dto.password, email):
            raise ValidationError("No se pudo crear el usuario")

        # Crear base de datos
        if not create_user_database(username):
            # Revertir creación de usuario con unregister_user
            self.user_auth.unregister_user(username)
            raise ValidationError("No se pudo crear la base de datos del usuario")

        # Retornar DTO del perfil creado
        current_user = get_current_user_id()
        return PerfilDTO(
            username=username,
            email=email,
            tiene_bd=True,
            tiene_logo=False,
            es_actual=username == current_user,
            ruta_logo=None,
        )
