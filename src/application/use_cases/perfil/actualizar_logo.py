"""Use Case: Actualizar logo corporativo de un perfil."""

import shutil
from pathlib import Path

from core.exceptions import NotFoundError, ValidationError
from sync.sync_manager import UserAuth


class ActualizarLogoUseCase:
    """Actualiza el logo corporativo de un perfil."""

    def __init__(self, user_auth: UserAuth):
        self.user_auth = user_auth

    def execute(self, username: str, ruta_imagen: str) -> str:
        """
        Actualiza el logo de un perfil.

        Args:
            username: Nombre del usuario
            ruta_imagen: Ruta al archivo de imagen

        Returns:
            Ruta donde se guardó el logo

        Raises:
            NotFoundError: Si el perfil no existe
            ValidationError: Si la imagen no es válida
        """
        # Verificar que existe el perfil
        if username not in self.user_auth.users:
            raise NotFoundError(f"No existe el usuario '{username}'")

        # Verificar que el archivo existe
        archivo_origen = Path(ruta_imagen)
        if not archivo_origen.exists():
            raise ValidationError("El archivo de imagen no existe")

        # Verificar extensión válida
        extensiones_validas = {".png", ".jpg", ".jpeg", ".bmp"}
        if archivo_origen.suffix.lower() not in extensiones_validas:
            raise ValidationError(f"Formato no válido. Use: {', '.join(extensiones_validas)}")

        # Crear carpeta si no existe
        carpeta_imagenes = Path("imagenes")
        carpeta_imagenes.mkdir(exist_ok=True)

        # Copiar imagen con nombre del usuario (siempre .png)
        destino = carpeta_imagenes / f"{username}.png"

        try:
            shutil.copy(archivo_origen, destino)
            return str(destino)
        except Exception as e:
            raise ValidationError(f"Error al copiar la imagen: {str(e)}")
