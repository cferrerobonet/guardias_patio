"""Use Case: Listar todos los perfiles del sistema."""

from pathlib import Path
from typing import List

from application.dtos.perfil_dto import PerfilDTO
from database.db_manager import get_current_user_id, user_has_database
from sync.sync_manager import UserAuth


class ListarPerfilesUseCase:
    """Lista todos los perfiles de usuario del sistema."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self) -> List[PerfilDTO]:
        """
        Obtiene la lista completa de perfiles.

        Returns:
            Lista de PerfilDTO con todos los perfiles del sistema
        """
        perfiles = []
        current_user = get_current_user_id()

        for username, data in self.user_auth.users.items():
            # Verificar si tiene BD
            tiene_bd = user_has_database(username)

            # Verificar si tiene logo
            logo_path = Path("imagenes") / f"{username}.png"
            tiene_logo = logo_path.exists()

            # Es el usuario actual
            es_actual = username == current_user

            perfil = PerfilDTO(
                username=username,
                email=data.get("email", ""),
                tiene_bd=tiene_bd,
                tiene_logo=tiene_logo,
                es_actual=es_actual,
                ruta_logo=str(logo_path) if tiene_logo else None,
            )
            perfiles.append(perfil)

        # Ordenar: usuario actual primero, luego alfabético
        perfiles.sort(key=lambda p: (not p.es_actual, p.username.lower()))

        return perfiles
