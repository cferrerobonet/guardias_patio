"""
Domain Entity: Guardia

Representa una guardia asignada a un profesor en una zona específica.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional

from core.exceptions import (
    GuardiaConflictError,
    GuardiaInvalidaError,
)


@dataclass
class GuardiaEntity:
    """
    Entidad de dominio que representa una guardia asignada.

    Una guardia es la asignación de un profesor a una zona en una fecha,
    turno y recreo específicos.

    Attributes:
        id: Identificador único de la guardia
        profesor_id: ID del profesor asignado
        zona_id: ID de la zona asignada
        fecha: Fecha de la guardia
        turno: Turno ('mañana' o 'tarde')
        recreo: Número del recreo (1, 2, etc.)
        es_sustitucion: Si es una guardia de sustitución
        profesor_sustituido_id: ID del profesor sustituido (si es sustitución)
        notas: Notas adicionales

    Examples:
        >>> guardia = GuardiaEntity(
        ...     profesor_id=1,
        ...     zona_id=2,
        ...     fecha=date(2025, 10, 17),
        ...     turno="mañana",
        ...     recreo=1
        ... )
        >>> guardia.es_valida()
        True
    """

    # Identidad
    id: Optional[int] = None

    # Asignación
    profesor_id: int = 0
    zona_id: int = 0

    # Temporalidad
    fecha: date = date.today()
    turno: str = "mañana"
    recreo: int = 1

    # Sustitución
    es_sustitucion: bool = False
    profesor_sustituido_id: Optional[int] = None

    # Metadatos
    notas: Optional[str] = None

    def __post_init__(self) -> None:
        """Validación post-construcción."""
        if not self.es_valida():
            raise GuardiaInvalidaError(
                guardia_id=self.id, message="La guardia no es válida: faltan datos requeridos"
            )

    @property
    def clave_unica(self) -> tuple:
        """
        Genera una clave única para identificar la guardia.

        Esta clave se usa para detectar duplicados.

        Returns:
            Tupla (fecha, turno, recreo, zona_id)

        Examples:
            >>> g1 = GuardiaEntity(fecha=date.today(), turno="mañana", recreo=1, zona_id=1)
            >>> g2 = GuardiaEntity(fecha=date.today(), turno="mañana", recreo=1, zona_id=1)
            >>> g1.clave_unica == g2.clave_unica
            True
        """
        return (self.fecha, self.turno, self.recreo, self.zona_id)

    @property
    def clave_profesor_fecha(self) -> tuple:
        """
        Genera clave única para el profesor en una fecha.

        Returns:
            Tupla (profesor_id, fecha, turno, recreo)
        """
        return (self.profesor_id, self.fecha, self.turno, self.recreo)

    def es_valida(self) -> bool:
        """
        Verifica si la guardia tiene todos los datos requeridos.

        Returns:
            True si la guardia es válida
        """
        return (
            self.profesor_id > 0
            and self.zona_id > 0
            and self.fecha is not None
            and self.turno in ["mañana", "tarde"]
            and self.recreo > 0
        )

    def es_mismo_momento(self, otra: "GuardiaEntity") -> bool:
        """
        Verifica si dos guardias son en el mismo momento.

        Args:
            otra: Otra guardia a comparar

        Returns:
            True si son en la misma fecha, turno y recreo
        """
        return self.fecha == otra.fecha and self.turno == otra.turno and self.recreo == otra.recreo

    def conflicto_con(self, otra: "GuardiaEntity") -> bool:
        """
        Verifica si hay conflicto con otra guardia.

        Un conflicto ocurre cuando:
        - Mismo profesor en el mismo momento
        - Misma zona en el mismo momento

        Args:
            otra: Otra guardia a comparar

        Returns:
            True si hay conflicto

        Examples:
            >>> g1 = GuardiaEntity(profesor_id=1, fecha=date.today(), turno="mañana", recreo=1)
            >>> g2 = GuardiaEntity(profesor_id=1, fecha=date.today(), turno="mañana", recreo=1)
            >>> g1.conflicto_con(g2)
            True
        """
        if not self.es_mismo_momento(otra):
            return False

        # Conflicto si mismo profesor
        if self.profesor_id == otra.profesor_id:
            return True

        # Conflicto si misma zona
        if self.zona_id == otra.zona_id:
            return True

        return False

    def verificar_sin_conflicto(self, otra: "GuardiaEntity") -> None:
        """
        Verifica que no haya conflicto con otra guardia.

        Args:
            otra: Otra guardia a comparar

        Raises:
            GuardiaConflictError: Si hay conflicto
        """
        if self.conflicto_con(otra):
            if self.profesor_id == otra.profesor_id:
                raise GuardiaConflictError(
                    guardia_id=self.id,
                    fecha=self.fecha,
                    message=f"El profesor {self.profesor_id} ya tiene guardia en este momento",
                )
            if self.zona_id == otra.zona_id:
                raise GuardiaConflictError(
                    guardia_id=self.id,
                    fecha=self.fecha,
                    message=f"La zona {self.zona_id} ya está ocupada en este momento",
                )

    def marcar_como_sustitucion(self, profesor_sustituido_id: int) -> None:
        """
        Marca la guardia como sustitución.

        Args:
            profesor_sustituido_id: ID del profesor que se sustituye
        """
        self.es_sustitucion = True
        self.profesor_sustituido_id = profesor_sustituido_id

    def quitar_sustitucion(self) -> None:
        """Quita la marca de sustitución de la guardia."""
        self.es_sustitucion = False
        self.profesor_sustituido_id = None

    def __str__(self) -> str:
        """Representación en string."""
        sustitucion = " (SUSTITUCIÓN)" if self.es_sustitucion else ""
        return (
            f"Guardia {self.fecha} {self.turno} R{self.recreo} - "
            f"P:{self.profesor_id} Z:{self.zona_id}{sustitucion}"
        )

    def __repr__(self) -> str:
        """Representación para debugging."""
        return (
            f"GuardiaEntity(id={self.id}, profesor_id={self.profesor_id}, "
            f"zona_id={self.zona_id}, fecha={self.fecha})"
        )

    def __eq__(self, other: object) -> bool:
        """Comparación por identidad (ID) o por clave única."""
        if not isinstance(other, GuardiaEntity):
            return False

        # Si ambos tienen ID, comparar por ID
        if self.id is not None and other.id is not None:
            return self.id == other.id

        # Si no, comparar por clave única
        return self.clave_unica == other.clave_unica

    def __hash__(self) -> int:
        """Hash basado en clave única."""
        if self.id is not None:
            return hash(("GuardiaEntity", self.id))
        return hash(("GuardiaEntity", self.clave_unica))
