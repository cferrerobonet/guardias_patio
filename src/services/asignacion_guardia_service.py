"""
Domain Service: Asignación de Guardias

Centraliza la lógica de negocio para asignar una guardia a un profesor.
Valida todas las reglas de negocio antes de crear la asignación.

Reglas de negocio implementadas:
1. Profesor debe estar activo
2. No puede estar ausente en la fecha
3. Turno debe ser compatible
4. No exceder máximo guardias por día
5. No duplicar guardias en mismo slot
6. Respetar zona preferida (si aplica)
7. Respetar fecha de inicio de guardias
"""

from datetime import date
from typing import Optional, Tuple

from core.exceptions import (
    BusinessLogicError,
)
from infrastructure.database.models import Guardia, Profesor, Zona
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from utils import get_logger

from services.disponibilidad_profesor_service import (
    DisponibilidadProfesorService,
)

logger = get_logger(__name__)


class AsignacionGuardiaService:
    """
    Servicio de dominio para validar y ejecutar asignaciones de guardias.

    Responsabilidades:
    - Validar todas las reglas de negocio
    - Crear asignaciones válidas
    - Rechazar asignaciones inválidas con razón clara
    - Mantener integridad de datos
    """

    def __init__(self, session: Session):
        """
        Inicializa el servicio.

        Args:
            session: Sesión de SQLAlchemy
        """
        self.session = session
        self.disponibilidad_service = DisponibilidadProfesorService(session)
        self.logger = logger

    def puede_asignar_guardia(
        self,
        profesor: Profesor,
        fecha: date,
        turno: str,
        recreo_id: int,
        zona_id: int,
        verificar_cuota: bool = False,
        cuota_maxima: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida si se puede asignar una guardia a un profesor.

        Args:
            profesor: Profesor candidato
            fecha: Fecha de la guardia
            turno: Turno del recreo ('mañana' o 'tarde')
            recreo_id: ID del recreo
            zona_id: ID de la zona
            verificar_cuota: Si debe verificar que no exceda cuota máxima
            cuota_maxima: Cuota máxima permitida (si verificar_cuota=True)

        Returns:
            Tupla (puede_asignar: bool, razon: Optional[str])
            - Si puede_asignar=True, razon=None
            - Si puede_asignar=False, razon explica por qué

        Examples:
            >>> service = AsignacionGuardiaService(session)
            >>> puede, razon = service.puede_asignar_guardia(
            ...     profesor, date(2024, 10, 15), "mañana", 1, 1
            ... )
            >>> if not puede:
            ...     print(f"No se puede asignar: {razon}")
        """
        # 1. Verificar disponibilidad básica (activo, ausencias, turno, max/día)
        disponible, razon = self.disponibilidad_service.esta_disponible(
            profesor, fecha, turno, recreo_id
        )

        if not disponible:
            return False, razon

        # 2. Verificar que no exista guardia duplicada en ese slot exacto
        existe = self._existe_guardia_en_slot(profesor.id, fecha, recreo_id, zona_id)
        if existe:
            return False, "Guardia duplicada: profesor ya tiene guardia en ese slot"

        # 3. Verificar fecha de inicio de guardias
        if profesor.fecha_inicio_guardias:
            fecha_valida, razon = self.disponibilidad_service.validar_fecha_inicio_guardias(
                profesor, fecha
            )
            if not fecha_valida:
                return False, razon

        # 4. Verificar cuota si se solicitó
        if verificar_cuota and cuota_maxima is not None:
            guardias_actuales = self._contar_guardias_profesor(profesor.id)
            if guardias_actuales >= cuota_maxima:
                return (
                    False,
                    f"Cuota alcanzada: {guardias_actuales}/{cuota_maxima}",
                )

        # 5. Verificar que la zona exista
        zona = self.session.query(Zona).get(zona_id)
        if not zona:
            return False, f"Zona {zona_id} no existe"

        return True, None

    def asignar_guardia(
        self,
        profesor: Profesor,
        fecha: date,
        turno: str,
        recreo_id: int,
        zona_id: int,
        curso_id: Optional[int] = None,
        validar_antes: bool = True,
    ) -> Guardia:
        """
        Crea una nueva asignación de guardia.

        Args:
            profesor: Profesor a asignar
            fecha: Fecha de la guardia
            turno: Turno del recreo
            recreo_id: ID del recreo
            zona_id: ID de la zona
            curso_id: ID del curso escolar (opcional)
            validar_antes: Si debe validar reglas antes de crear

        Returns:
            Guardia creada (sin hacer commit)

        Raises:
            BusinessLogicError: Si la validación falla y validar_antes=True

        Examples:
            >>> service = AsignacionGuardiaService(session)
            >>> guardia = service.asignar_guardia(
            ...     profesor, date(2024, 10, 15), "mañana", 1, 1
            ... )
            >>> session.add(guardia)
            >>> session.commit()
        """
        # Validar si se solicitó
        if validar_antes:
            puede, razon = self.puede_asignar_guardia(profesor, fecha, turno, recreo_id, zona_id)
            if not puede:
                raise BusinessLogicError(
                    message=f"No se puede asignar guardia: {razon}",
                    details={
                        "profesor_id": profesor.id,
                        "fecha": str(fecha),
                        "turno": turno,
                        "recreo_id": recreo_id,
                        "zona_id": zona_id,
                        "razon": razon,
                    },
                )

        # Crear guardia
        guardia = Guardia(
            profesor_id=profesor.id,
            fecha=fecha,
            turno=turno,
            recreo=recreo_id,
            zona_id=zona_id,
            curso_id=curso_id,
        )

        self.logger.debug(
            f"Guardia creada: {profesor.nombre_completo} - {fecha} - "
            f"Recreo {recreo_id} - Zona {zona_id}"
        )

        return guardia

    def reasignar_guardia(
        self,
        guardia: Guardia,
        nuevo_profesor: Profesor,
        validar_antes: bool = True,
    ) -> Guardia:
        """
        Reasigna una guardia existente a otro profesor.

        Args:
            guardia: Guardia a reasignar
            nuevo_profesor: Nuevo profesor
            validar_antes: Si debe validar antes de reasignar

        Returns:
            Guardia con profesor actualizado (sin commit)

        Raises:
            BusinessLogicError: Si validación falla
        """
        if validar_antes:
            puede, razon = self.puede_asignar_guardia(
                nuevo_profesor,
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
                guardia.zona_id,
            )
            if not puede:
                raise BusinessLogicError(
                    message=f"No se puede reasignar guardia: {razon}",
                    details={
                        "guardia_id": guardia.id,
                        "profesor_original": guardia.profesor_id,
                        "profesor_nuevo": nuevo_profesor.id,
                        "razon": razon,
                    },
                )

        profesor_anterior = guardia.profesor_id
        guardia.profesor_id = nuevo_profesor.id

        self.logger.info(
            f"Guardia reasignada: {guardia.id} - Profesor {profesor_anterior} → {nuevo_profesor.id}"
        )

        return guardia

    def eliminar_guardia(self, guardia: Guardia) -> None:
        """
        Elimina una guardia de la base de datos.

        Args:
            guardia: Guardia a eliminar
        """
        self.logger.info(
            f"Eliminando guardia: {guardia.id} - Profesor {guardia.profesor_id} - {guardia.fecha}"
        )
        self.session.delete(guardia)

    def validar_guardias_lote(
        self,
        asignaciones: list[
            Tuple[Profesor, date, str, int, int]
        ],  # (profesor, fecha, turno, recreo_id, zona_id)
    ) -> list[Tuple[int, bool, Optional[str]]]:
        """
        Valida un lote de asignaciones de una vez.

        Args:
            asignaciones: Lista de tuplas (profesor, fecha, turno, recreo_id, zona_id)

        Returns:
            Lista de tuplas (indice, valido, razon)
        """
        resultados = []
        for i, (profesor, fecha, turno, recreo_id, zona_id) in enumerate(asignaciones):
            puede, razon = self.puede_asignar_guardia(profesor, fecha, turno, recreo_id, zona_id)
            resultados.append((i, puede, razon))
        return resultados

    # Métodos privados auxiliares

    def _existe_guardia_en_slot(
        self, profesor_id: int, fecha: date, recreo_id: int, zona_id: int
    ) -> bool:
        """Verifica si ya existe una guardia en ese slot exacto."""
        return (
            self.session.query(Guardia)
            .filter(
                Guardia.profesor_id == profesor_id,
                Guardia.fecha == fecha,
                Guardia.recreo == recreo_id,
                Guardia.zona_id == zona_id,
            )
            .first()
            is not None
        )

    def _contar_guardias_profesor(self, profesor_id: int) -> int:
        """Cuenta el total de guardias de un profesor."""
        return self.session.query(Guardia).filter(Guardia.profesor_id == profesor_id).count()

    def calcular_carga_profesor(self, profesor: Profesor) -> dict:
        """
        Calcula métricas de carga del profesor.

        Returns:
            Dict con: total_guardias, guardias_por_mes, promedio_semanal, etc.
        """
        guardias = self.session.query(Guardia).filter(Guardia.profesor_id == profesor.id).all()

        if not guardias:
            return {
                "total_guardias": 0,
                "guardias_por_mes": {},
                "promedio_semanal": 0.0,
            }

        # Agrupar por mes
        from collections import defaultdict

        guardias_por_mes = defaultdict(int)
        for guardia in guardias:
            mes = (guardia.fecha.year, guardia.fecha.month)
            guardias_por_mes[mes] += 1

        # Calcular promedio semanal
        if guardias:
            fecha_min = min(g.fecha for g in guardias)
            fecha_max = max(g.fecha for g in guardias)
            dias_totales = (fecha_max - fecha_min).days + 1
            semanas = dias_totales / 7
            promedio_semanal = len(guardias) / semanas if semanas > 0 else 0
        else:
            promedio_semanal = 0

        return {
            "total_guardias": len(guardias),
            "guardias_por_mes": dict(guardias_por_mes),
            "promedio_semanal": promedio_semanal,
        }
