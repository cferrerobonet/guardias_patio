"""Cifrado de los datos de salud dentro del volcado que va al servidor (PRIV-001).

El tipo de ausencia (`baja_medica`…) y su motivo son datos de salud y viajaban en
claro al servidor del hosting. Aquí se cifran con una clave derivada de la
contraseña de la cuenta: la misma en cualquier equipo en el que entre esa
persona, y que el servidor no tiene. La derivación se hace una vez, al entrar.

Los volcados anteriores llevan los valores en claro y se siguen leyendo.
"""

import base64
import hashlib
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PREFIJO = "enc1:"
ITERACIONES = 600_000


def derivar_clave(username: str, password: str, iteraciones: int = ITERACIONES) -> bytes:
    """Clave Fernet a partir de la contraseña de la cuenta; la sal es el usuario."""
    sal = hashlib.sha256(f"guardias-patio:{username.strip().lower()}".encode("utf-8")).digest()
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=sal, iterations=iteraciones)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def cifrar(texto: Optional[str], clave: Optional[bytes]) -> Optional[str]:
    """Con clave, `enc1:<token>`; sin clave o sin texto, el valor tal cual."""
    if texto is None or clave is None:
        return texto
    return PREFIJO + Fernet(clave).encrypt(str(texto).encode("utf-8")).decode("ascii")


def esta_cifrado(valor) -> bool:
    return isinstance(valor, str) and valor.startswith(PREFIJO)


def descifrar(valor: Optional[str], clave: Optional[bytes]) -> Optional[str]:
    """Devuelve el texto en claro. Un valor cifrado sin clave válida es un error."""
    if not esta_cifrado(valor):
        return valor
    if clave is None:
        raise ValueError(
            "los datos de ausencias del servidor están cifrados y esta sesión no tiene la "
            "clave: hay que entrar con la contraseña de la cuenta"
        )
    try:
        return Fernet(clave).decrypt(valor[len(PREFIJO):].encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as e:
        raise ValueError(
            "no se pueden descifrar los datos de ausencias del servidor: la contraseña con la "
            "que se subieron no es la de esta sesión"
        ) from e
