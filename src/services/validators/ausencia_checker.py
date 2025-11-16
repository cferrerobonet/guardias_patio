"""
Validador de ausencias de profesores.

Este módulo centraliza toda la lógica relacionada con la validación
de ausencias de profesores en fechas específicas.

Fase 1.2 - Quick Wins: Centralización de validación de ausencias
"""

import logging
from datetime import date
from typing import List, Optional

from models.models import Ausencia, Profesor
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class AusenciaChecker:
    """
    Verificador de ausencias de profesores.

    Centraliza toda la lógica de verificación de ausencias para evitar
    código duplicado en múltiples servicios.

    Ejemplos:
        >>> checker = AusenciaChecker(session)
        >>> esta_ausente = checker.profesor_ausente(profesor_id=5, fecha=date(2025, 11, 14))
        >>> if not esta_ausente:
        ...     # Asignar guardia al profesor
    """

    def __init__(self, session: Session):
        """
        Inicializar checker de ausencias.

        Args:
            session: Sesión de SQLAlchemy para consultas a BD
        """
        self.session = session

    def profesor_ausente(
        self,
        profesor_id: int,
        fecha: date
    ) -> bool:
        """
        Verificar si un profesor está ausente en una fecha específica.

        Args:
            profesor_id: ID del profesor a verificar
            fecha: Fecha a verificar

        Returns:
            bool: True si está ausente, False si está disponible

        Examples:
            >>> checker = AusenciaChecker(session)
            >>> checker.profesor_ausente(5, date(2025, 11, 14))
            False
            >>> checker.profesor_ausente(5, date(2025, 12, 25))
            True
        """
        ausencia = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha
            )
            .first()
        )
        return ausencia is not None

    def obtener_ausencia(
        self,
        profesor_id: int,
        fecha: date
    ) -> Optional[Ausencia]:
        """
        Obtener la ausencia de un profesor en una fecha específica.

        Args:
            profesor_id: ID del profesor
            fecha: Fecha a verificar

        Returns:
            Ausencia si existe, None si no hay ausencia
        """
        return (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha
            )
            .first()
        )

    def profesores_ausentes_en_fecha(
        self,
        fecha: date,
        profesor_ids: Optional[List[int]] = None
    ) -> List[Profesor]:
        """
        Obtener lista de profesores ausentes en una fecha.

        Args:
            fecha: Fecha a verificar
            profesor_ids: Lista opcional de IDs de profesores a verificar.
                         Si es None, verifica todos los profesores.

        Returns:
            Lista de profesores ausentes en esa fecha
        """
        query = (
            self.session.query(Profesor)
            .join(Ausencia, Ausencia.profesor_id == Profesor.id)
            .filter(
                Ausencia.fecha_inicio <= fecha,
                Ausencia.fecha_fin >= fecha
            )
        )

        if profesor_ids is not None:
            query = query.filter(Profesor.id.in_(profesor_ids))

        return query.all()

    def profesores_disponibles_en_fecha(
        self,
        fecha: date,
        solo_activos: bool = True
    ) -> List[Profesor]:
        """
        Obtener lista de profesores disponibles (no ausentes) en una fecha.

        Args:
            fecha: Fecha a verificar
            solo_activos: Si True, solo incluye profesores activos

        Returns:
            Lista de profesores disponibles
        """
        # Obtener IDs de profesores ausentes
        ausentes_ids = [
            p.id for p in self.profesores_ausentes_en_fecha(fecha)
        ]

        # Consultar profesores no ausentes
        query = self.session.query(Profesor).filter(
            ~Profesor.id.in_(ausentes_ids) if ausentes_ids else True
        )

        if solo_activos:
            query = query.filter(Profesor.activo.is_(True))

        return query.all()

    def contar_ausencias_profesor(
        self,
        profesor_id: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> int:
        """
        Contar el número de ausencias de un profesor en un período.

        Args:
            profesor_id: ID del profesor
            fecha_inicio: Fecha de inicio del período (opcional)
            fecha_fin: Fecha de fin del período (opcional)

        Returns:
            Número de ausencias registradas
        """
        query = self.session.query(Ausencia).filter(
            Ausencia.profesor_id == profesor_id
        )

        if fecha_inicio:
            query = query.filter(Ausencia.fecha_fin >= fecha_inicio)

        if fecha_fin:
            query = query.filter(Ausencia.fecha_inicio <= fecha_fin)

        return query.count()

    def dias_ausente_en_periodo(
        self,
        profesor_id: int,
        fecha_inicio: date,
        fecha_fin: date
    ) -> int:
        """
        Calcular el número de días que un profesor estuvo ausente en un período.

        Args:
            profesor_id: ID del profesor
            fecha_inicio: Fecha de inicio del período
            fecha_fin: Fecha de fin del período

        Returns:
            Número de días ausente (aproximado)
        """
        ausencias = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio <= fecha_fin,
                Ausencia.fecha_fin >= fecha_inicio
            )
            .all()
        )

        if not ausencias:
            return 0

        # Calcular días totales de ausencia
        dias_totales = 0
        for ausencia in ausencias:
            inicio_efectivo = max(ausencia.fecha_inicio, fecha_inicio)
            fin_efectivo = min(ausencia.fecha_fin, fecha_fin)
            dias = (fin_efectivo - inicio_efectivo).days + 1
            dias_totales += dias

        return dias_totales

    def tiene_ausencias_futuras(
        self,
        profesor_id: int,
        desde_fecha: Optional[date] = None
    ) -> bool:
        """
        Verificar si un profesor tiene ausencias programadas a futuro.

        Args:
            profesor_id: ID del profesor
            desde_fecha: Fecha desde la cual buscar (por defecto hoy)

        Returns:
            bool: True si tiene ausencias futuras, False si no
        """
        if desde_fecha is None:
            desde_fecha = date.today()

        ausencias = (
            self.session.query(Ausencia)
            .filter(
                Ausencia.profesor_id == profesor_id,
                Ausencia.fecha_inicio >= desde_fecha
            )
            .first()
        )

        return ausencias is not None
