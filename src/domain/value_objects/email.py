"""
Value Object: Email Corporativo

Representa un email corporativo con validación automática.
Es inmutable y se compara por valor.
"""

import re
from dataclasses import dataclass
from typing import Optional

from core.exceptions import InvalidEmailError


@dataclass(frozen=True)
class Email:
    """
    Email corporativo validado.

    Attributes:
        value: El email en formato string

    Raises:
        InvalidEmailError: Si el email no tiene formato válido

    Examples:
        >>> email = Email("profesor@colegio.edu")
        >>> print(email.value)
        profesor@colegio.edu
        >>> print(email.domain)
        colegio.edu
        >>> email2 = Email("profesor@colegio.edu")
        >>> email == email2
        True
    """

    value: str

    # Patrón RFC 5322 simplificado
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __post_init__(self) -> None:
        """Valida el email después de la inicialización."""
        if not self.value:
            raise InvalidEmailError(email=self.value, message="El email no puede estar vacío")

        if not self.EMAIL_PATTERN.match(self.value):
            raise InvalidEmailError(
                email=self.value, message=f"El email '{self.value}' no tiene un formato válido"
            )

    @property
    def domain(self) -> str:
        """Retorna el dominio del email."""
        return self.value.split("@")[1] if "@" in self.value else ""

    @property
    def local_part(self) -> str:
        """Retorna la parte local del email (antes del @)."""
        return self.value.split("@")[0] if "@" in self.value else self.value

    def __str__(self) -> str:
        """Representación en string del email."""
        return self.value

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"Email('{self.value}')"

    @classmethod
    def from_optional(cls, value: Optional[str]) -> Optional["Email"]:
        """
        Crea un Email desde un valor opcional.

        Args:
            value: String que puede ser None o vacío

        Returns:
            Email si value es válido, None si value es None/vacío

        Raises:
            InvalidEmailError: Si value no es válido
        """
        if not value or not value.strip():
            return None
        return cls(value.strip().lower())
