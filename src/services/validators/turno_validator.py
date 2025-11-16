"""
Validador de compatibilidad de turnos.

Este módulo centraliza toda la lógica relacionada con la validación
de turnos entre profesores y recreos/guardias.

Fase 1.1 - Quick Wins: Centralización de validación de turnos
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class TurnoValidator:
    """
    Validador de compatibilidad entre turnos de profesores y recreos.

    Reglas de negocio:
    - 'mañana': Solo compatible con recreos/guardias de mañana
    - 'tarde': Solo compatible con recreos/guardias de tarde
    - 'mixto' / 'completo': Compatible con ambos turnos
    - None / vacío: Se trata como 'completo' (compatible con todo)

    Ejemplos:
        >>> validator = TurnoValidator()
        >>> validator.es_compatible('mañana', 'mañana')
        True
        >>> validator.es_compatible('mañana', 'tarde')
        False
        >>> validator.es_compatible('mixto', 'tarde')
        True
    """

    # Constantes de turnos
    TURNO_MANANA = "mañana"
    TURNO_TARDE = "tarde"
    TURNO_MIXTO = "mixto"
    TURNO_COMPLETO = "completo"

    # Turnos que pueden trabajar en cualquier momento
    TURNOS_FLEXIBLES = {TURNO_MIXTO, TURNO_COMPLETO}

    def __init__(self):
        """Inicializar validador de turnos."""
        pass

    def es_compatible(
        self,
        turno_profesor: Optional[str],
        turno_recreo: str
    ) -> bool:
        """
        Verificar si un profesor puede cubrir un recreo según su turno.

        Args:
            turno_profesor: Turno del profesor ('mañana', 'tarde', 'mixto', 'completo', None)
            turno_recreo: Turno del recreo ('mañana', 'tarde')

        Returns:
            bool: True si son compatibles, False si no

        Examples:
            >>> validator = TurnoValidator()
            >>> validator.es_compatible('mañana', 'mañana')
            True
            >>> validator.es_compatible('mañana', 'tarde')
            False
            >>> validator.es_compatible(None, 'tarde')
            True
        """
        # None o vacío se trata como turno completo (compatible con todo)
        if not turno_profesor:
            return True

        turno_profesor = turno_profesor.lower().strip()
        turno_recreo = turno_recreo.lower().strip()

        # Turnos flexibles (mixto/completo) son compatibles con todo
        if turno_profesor in self.TURNOS_FLEXIBLES:
            return True

        # Turnos específicos deben coincidir
        return turno_profesor == turno_recreo

    def filtrar_profesores_compatibles(
        self,
        profesores: List,
        turno_recreo: str
    ) -> List:
        """
        Filtrar lista de profesores que sean compatibles con un turno.

        Args:
            profesores: Lista de objetos Profesor
            turno_recreo: Turno del recreo a cubrir

        Returns:
            Lista filtrada de profesores compatibles

        Example:
            >>> profesores = [prof1, prof2, prof3]
            >>> compatibles = validator.filtrar_profesores_compatibles(profesores, 'mañana')
        """
        return [
            p for p in profesores
            if self.es_compatible(p.turno, turno_recreo)
        ]

    def contar_profesores_por_turno(
        self,
        profesores: List,
        turno: str
    ) -> int:
        """
        Contar cuántos profesores pueden trabajar en un turno específico.

        Args:
            profesores: Lista de objetos Profesor
            turno: Turno a verificar

        Returns:
            Número de profesores compatibles con ese turno
        """
        return sum(
            1 for p in profesores
            if self.es_compatible(p.turno, turno)
        )

    def calcular_factor_participacion(
        self,
        turno_profesor: Optional[str],
        recreos_manana: int,
        recreos_tarde: int,
        horas_manana: int = 0,
        horas_tarde: int = 0
    ) -> float:
        """
        Calcular el factor de participación de un profesor.

        El factor indica qué proporción de recreos totales puede cubrir el profesor
        según su turno y distribución de horas.

        Args:
            turno_profesor: Turno del profesor
            recreos_manana: Número de recreos de mañana
            recreos_tarde: Número de recreos de tarde
            horas_manana: Horas que el profesor trabaja por la mañana (para turno mixto)
            horas_tarde: Horas que el profesor trabaja por la tarde (para turno mixto)

        Returns:
            float: Factor de participación (0.0 a 1.0)

        Examples:
            >>> validator.calcular_factor_participacion('mañana', 2, 2, 0, 0)
            0.5  # Solo puede cubrir la mitad (los recreos de mañana)

            >>> validator.calcular_factor_participacion('mixto', 2, 2, 10, 10)
            1.0  # Puede cubrir todos los recreos
        """
        recreos_totales = recreos_manana + recreos_tarde
        if recreos_totales == 0:
            return 0.0

        # None o vacío se trata como completo
        if not turno_profesor:
            turno_profesor = self.TURNO_COMPLETO

        turno_profesor = turno_profesor.lower().strip()

        if turno_profesor == self.TURNO_MANANA:
            # Solo puede cubrir recreos de mañana
            return recreos_manana / recreos_totales

        elif turno_profesor == self.TURNO_TARDE:
            # Solo puede cubrir recreos de tarde
            return recreos_tarde / recreos_totales

        else:  # mixto o completo
            # Si no hay información de horas o es turno completo, puede cubrir todo
            if turno_profesor == self.TURNO_COMPLETO or (horas_manana == 0 and horas_tarde == 0):
                return 1.0

            # Calcular proporción ponderada por horas en cada turno
            horas_totales = horas_manana + horas_tarde
            if horas_totales == 0:
                return 1.0

            factor_manana = (horas_manana / horas_totales) * (recreos_manana / recreos_totales)
            factor_tarde = (horas_tarde / horas_totales) * (recreos_tarde / recreos_totales)

            return factor_manana + factor_tarde

    def validar_turno(self, turno: Optional[str]) -> bool:
        """
        Validar que un turno sea válido.

        Args:
            turno: Turno a validar

        Returns:
            bool: True si es válido, False si no
        """
        if turno is None:
            return True

        turno = turno.lower().strip()
        return turno in {
            self.TURNO_MANANA,
            self.TURNO_TARDE,
            self.TURNO_MIXTO,
            self.TURNO_COMPLETO
        }

    def obtener_turnos_validos(self) -> List[str]:
        """
        Obtener lista de turnos válidos.

        Returns:
            Lista de strings con turnos válidos
        """
        return [
            self.TURNO_MANANA,
            self.TURNO_TARDE,
            self.TURNO_MIXTO,
            self.TURNO_COMPLETO
        ]
