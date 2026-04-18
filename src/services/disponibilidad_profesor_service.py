"""
Domain Service: Disponibilidad de Profesores

Centraliza toda la lógica de negocio relacionada con determinar
si un profesor está disponible para realizar una guardia.

Integra:
- TurnoValidator (compatibilidad de turnos)
- AusenciaChecker (ausencias registradas)
- Reglas de negocio adicionales
"""

from datetime import date
from typing import List, Optional, Tuple

from infrastructure.database.models import Ausencia, Guardia, Profesor
from services.validators import AusenciaChecker, TurnoValidator
from sqlalchemy.orm import Session
from utils import get_logger

from domain.value_objects import Turno

logger = get_logger(__name__)


class DisponibilidadProfesorService:
    """
    Servicio de dominio para evaluar disponibilidad de profesores.

    Responsabilidades:
    - Verificar si un profesor puede hacer una guardia en fecha/turno específico
    - Comprobar ausencias
    - Validar compatibilidad de turnos
    - Verificar máximo de guardias por día
    - Filtrar profesores disponibles para un slot
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio.

        Args:
            session: Sesión de SQLAlchemy para consultas a BD
        """
        self.session = session
        self.turno_validator = TurnoValidator()
        self.ausencia_checker = AusenciaChecker(session)
        self.logger = logger

    def esta_disponible(
        self,
        profesor: Profesor,
        fecha: date,
        turno_recreo: str,
        recreo_id: Optional[int] = None,
        max_guardias_dia: int = 1,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un profesor está disponible para una guardia.

        Args:
            profesor: Profesor a verificar
            fecha: Fecha de la guardia
            turno_recreo: Turno del recreo ('mañana' o 'tarde')
            recreo_id: ID del recreo (opcional, para validaciones adicionales)
            max_guardias_dia: Máximo de guardias permitidas por día

        Returns:
            Tupla (disponible: bool, razon: Optional[str])
            - Si disponible=True, razon=None
            - Si disponible=False, razon contiene el motivo

        Examples:
            >>> service = DisponibilidadProfesorService(session)
            >>> disponible, razon = service.esta_disponible(profesor, date(2024, 10, 15), "mañana")
            >>> if not disponible:
            ...     print(f"No disponible: {razon}")
        """
        # 1. Verificar que el profesor esté activo
        if not profesor.activo:
            return False, "Profesor inactivo"

        # 2. Verificar ausencias
        if self.ausencia_checker.profesor_ausente(profesor.id, fecha):
            return False, f"Profesor ausente el {fecha}"

        # 3. Verificar compatibilidad de turno
        turno_profesor = Turno.from_string(
            profesor.turno,
            horas_manana=profesor.horas_manana,
            horas_tarde=profesor.horas_tarde,
        )

        if not turno_profesor.puede_hacer_guardia_en_turno(turno_recreo):
            return (
                False,
                f"Turno incompatible: profesor trabaja {profesor.turno}, recreo es {turno_recreo}",
            )

        # 4. Verificar máximo de guardias por día
        guardias_dia = self._contar_guardias_dia(profesor.id, fecha)
        if guardias_dia >= max_guardias_dia:
            return (
                False,
                f"Máximo de guardias por día alcanzado ({guardias_dia}/{max_guardias_dia})",
            )

        # 5. Verificar que no tenga guardia en el mismo recreo
        if recreo_id and self._tiene_guardia_en_recreo(profesor.id, fecha, recreo_id):
            return False, f"Profesor ya tiene guardia en recreo {recreo_id} el {fecha}"

        return True, None

    def esta_ausente(self, profesor_id: int, fecha: date) -> bool:
        """
        Verifica si un profesor está ausente en una fecha.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha a verificar

        Returns:
            True si está ausente, False si está disponible
        """
        return self.ausencia_checker.profesor_ausente(profesor_id, fecha)

    def obtener_profesores_disponibles(
        self,
        profesores: List[Profesor],
        fecha: date,
        turno_recreo: str,
        recreo_id: int,
        excluir_profesor_id: Optional[int] = None,
        max_guardias_dia: int = 1,
    ) -> List[Profesor]:
        """
        Filtra profesores disponibles para un slot específico.

        Args:
            profesores: Lista de profesores candidatos
            fecha: Fecha de la guardia
            turno_recreo: Turno del recreo
            recreo_id: ID del recreo
            excluir_profesor_id: ID de profesor a excluir (opcional)
            max_guardias_dia: Máximo de guardias por día

        Returns:
            Lista de profesores disponibles (puede estar vacía)
        """
        disponibles = []

        for profesor in profesores:
            # Excluir si se especificó
            if excluir_profesor_id and profesor.id == excluir_profesor_id:
                continue

            # Verificar disponibilidad
            disponible, _ = self.esta_disponible(
                profesor, fecha, turno_recreo, recreo_id, max_guardias_dia
            )

            if disponible:
                disponibles.append(profesor)

        return disponibles

    def validar_fecha_inicio_guardias(
        self, profesor: Profesor, fecha_guardia: date
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida si la fecha de guardia respeta la fecha de inicio configurada.

        Args:
            profesor: Profesor a validar
            fecha_guardia: Fecha propuesta para la guardia

        Returns:
            Tupla (valido: bool, razon: Optional[str])
        """
        if not profesor.fecha_inicio_guardias:
            return True, None

        if fecha_guardia < profesor.fecha_inicio_guardias:
            dias_diferencia = (profesor.fecha_inicio_guardias - fecha_guardia).days
            return (
                False,
                f"Guardia antes de fecha de inicio: faltan {dias_diferencia} días",
            )

        return True, None

    def obtener_ausencias_profesor(
        self, profesor_id: int, fecha_inicio: date, fecha_fin: date
    ) -> List[Ausencia]:
        """
        Obtiene las ausencias de un profesor en un rango de fechas.

        Args:
            profesor_id: ID del profesor
            fecha_inicio: Fecha inicio del rango
            fecha_fin: Fecha fin del rango

        Returns:
            Lista de ausencias en el rango
        """
        return (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.activa == True,  # noqa: E712
                Ausencia.fecha_fin >= fecha_inicio,
                Ausencia.fecha_inicio <= fecha_fin,
            )
            .all()
        )

    # Métodos privados auxiliares

    def _contar_guardias_dia(self, profesor_id: int, fecha: date) -> int:
        """Cuenta cuántas guardias tiene un profesor en una fecha."""
        return (
            self.session.query(Guardia)
            .filter(Guardia.profesor_id == profesor_id, Guardia.fecha == fecha)
            .count()
        )

    def _tiene_guardia_en_recreo(self, profesor_id: int, fecha: date, recreo_id: int) -> bool:
        """Verifica si el profesor ya tiene una guardia en ese recreo/fecha."""
        return (
            self.session.query(Guardia)
            .filter(
                Guardia.profesor_id == profesor_id,
                Guardia.fecha == fecha,
                Guardia.recreo == recreo_id,
            )
            .first()
            is not None
        )

    def verificar_disponibilidad_multiple(
        self, profesores: List[Profesor], fecha: date, turno_recreo: str
    ) -> dict[int, Tuple[bool, Optional[str]]]:
        """
        Verifica disponibilidad de múltiples profesores de una vez.

        Args:
            profesores: Lista de profesores
            fecha: Fecha a verificar
            turno_recreo: Turno del recreo

        Returns:
            Dict[profesor_id: (disponible, razon)]
        """
        resultado = {}
        for profesor in profesores:
            disponible, razon = self.esta_disponible(profesor, fecha, turno_recreo)
            resultado[profesor.id] = (disponible, razon)
        return resultado
