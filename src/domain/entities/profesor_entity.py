"""
Domain Entity: Profesor

Representa un profesor en el dominio de negocio con todas sus reglas.
Separado del modelo de persistencia (SQLAlchemy).
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from config import settings
from core.exceptions import (
    MaxGuardiasDiaExceededError,
    ProfesorAusenteError,
)
from domain.value_objects import Email, HorasContrato, Turno, ZonaPreferida


@dataclass
class ProfesorEntity:
    """
    Entidad de dominio que representa a un profesor.

    Esta clase contiene la lógica de negocio pura, independiente de la persistencia.

    Attributes:
        id: Identificador único del profesor
        nombre_completo: Nombre completo del profesor (formato libre, ej: "APELLIDOS, NOMBRE")
        email_corporativo: Email corporativo (Value Object)
        horas_contrato: Horas de contrato (Value Object)
        porcentaje_jornada: Porcentaje de jornada calculado
        turno: Turno de trabajo (Value Object)
        es_tutor: Indica si es tutor
        fecha_inicio_guardias: Fecha desde la que puede hacer guardias
        fecha_fin_guardias: Fecha hasta la que puede hacer guardias
        zona_preferida: Zona preferida para guardias (Value Object)
        dias_semana_permitidos: Lista de días permitidos (0=Lunes, 6=Domingo)
        recreos_permitidos: Lista de números de recreo permitidos
        guardias_asignadas_dia: Contador de guardias asignadas en el día actual

    Note:
        El campo nombre_completo es un único campo que contiene el nombre completo
        del profesor sin separación de apellidos y nombre.
    """

    # Identidad
    id: Optional[int] = None

    # Información básica
    nombre_completo: str = ""
    email_corporativo: Optional[Email] = None

    # Contrato y jornada
    horas_contrato: HorasContrato = field(default_factory=lambda: HorasContrato(25.0))
    porcentaje_jornada: float = 0.0
    turno: Turno = field(default_factory=lambda: Turno.from_string("mañana"))

    # Características
    es_tutor: bool = False

    # Disponibilidad temporal
    fecha_inicio_guardias: Optional[date] = None
    fecha_fin_guardias: Optional[date] = None

    # Preferencias
    zona_preferida: ZonaPreferida = field(default_factory=ZonaPreferida.sin_preferencia)
    dias_semana_permitidos: list[int] = field(default_factory=lambda: list(range(7)))
    recreos_permitidos: list[int] = field(default_factory=lambda: [1, 2])

    # Estado transiente (no persistido)
    guardias_asignadas_dia: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        """Inicialización y cálculos post-construcción."""
        # Calcular porcentaje de jornada si no está set
        if self.porcentaje_jornada == 0.0:
            self.porcentaje_jornada = self.horas_contrato.porcentaje_jornada()

    @property
    def ajuste_guardias(self) -> float:
        """Calcula el ajuste de guardias según si es tutor o no."""
        if self.es_tutor:
            return settings.ajuste_tutores
        return settings.ajuste_no_tutores

    @property
    def guardias_esperadas(self) -> float:
        """
        Calcula la cantidad esperada de guardias según horas de contrato y ajuste.

        Formula: (horas_contrato / horas_maximas) * ajuste
        """
        ratio = float(self.horas_contrato) / settings.max_horas_contrato
        return ratio * self.ajuste_guardias

    def puede_hacer_guardia_en_fecha(self, fecha: date) -> bool:
        """
        Verifica si el profesor puede hacer guardias en una fecha específica.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si puede hacer guardias en esa fecha

        Raises:
            ProfesorAusenteError: Si el profesor está ausente
        """
        # Verificar fecha de inicio
        if self.fecha_inicio_guardias and fecha < self.fecha_inicio_guardias:
            raise ProfesorAusenteError(
                profesor_id=self.id,
                fecha=fecha,
                message=(
                    f"El profesor aún no ha comenzado guardias "
                    f"(inicio: {self.fecha_inicio_guardias})"
                )
            )

        # Verificar fecha de fin
        if self.fecha_fin_guardias and fecha > self.fecha_fin_guardias:
            raise ProfesorAusenteError(
                profesor_id=self.id,
                fecha=fecha,
                message=f"El profesor ya terminó guardias (fin: {self.fecha_fin_guardias})"
            )

        # Verificar día de la semana
        dia_semana = fecha.weekday()
        if dia_semana not in self.dias_semana_permitidos:
            return False

        return True

    def puede_hacer_guardia_en_turno(self, turno_recreo: str) -> bool:
        """
        Verifica si el profesor puede hacer guardias en un turno específico.

        Args:
            turno_recreo: Turno del recreo ('mañana' o 'tarde')

        Returns:
            True si puede hacer guardias en ese turno
        """
        return self.turno.puede_hacer_guardia_en_turno(turno_recreo)

    def puede_hacer_guardia_en_recreo(self, numero_recreo: int) -> bool:
        """
        Verifica si el profesor puede hacer guardias en un recreo específico.

        Args:
            numero_recreo: Número del recreo (1, 2, etc.)

        Returns:
            True si puede hacer guardias en ese recreo
        """
        return numero_recreo in self.recreos_permitidos

    def puede_asignar_guardia(
        self,
        fecha: date,
        turno_recreo: str,
        numero_recreo: int,
        zona_id: Optional[int] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Verifica de forma completa si se puede asignar una guardia.

        Args:
            fecha: Fecha de la guardia
            turno_recreo: Turno del recreo
            numero_recreo: Número del recreo
            zona_id: ID de la zona (opcional)

        Returns:
            Tupla (puede_asignar, razon_si_no_puede)

        Examples:
            >>> profesor = ProfesorEntity(...)
            >>> puede, razon = profesor.puede_asignar_guardia(date.today(), "mañana", 1)
            >>> if puede:
            ...     profesor.asignar_guardia()
        """
        # Verificar fecha
        try:
            if not self.puede_hacer_guardia_en_fecha(fecha):
                return False, f"Fecha no disponible: {fecha}"
        except ProfesorAusenteError as e:
            return False, str(e)

        # Verificar turno
        if not self.puede_hacer_guardia_en_turno(turno_recreo):
            return False, f"No trabaja en turno {turno_recreo}"

        # Verificar recreo
        if not self.puede_hacer_guardia_en_recreo(numero_recreo):
            return False, f"No puede hacer guardia en recreo {numero_recreo}"

        # Verificar máximo de guardias por día
        if self.guardias_asignadas_dia >= settings.max_guardias_por_profesor_dia:
            return False, (
                f"Ya tiene {self.guardias_asignadas_dia} guardias hoy "
                f"(máx: {settings.max_guardias_por_profesor_dia})"
            )

        # Verificar zona preferida (si tiene)
        if self.zona_preferida.tiene_preferencia and zona_id:
            if not self.zona_preferida.coincide_con(zona_id):
                # Permitir pero con advertencia
                return True, f"Zona {zona_id} no es su preferida ({self.zona_preferida.zona_id})"

        return True, None

    def asignar_guardia(self) -> None:
        """
        Registra la asignación de una guardia al profesor.

        Incrementa el contador de guardias del día.

        Raises:
            MaxGuardiasDiaExceededError: Si ya tiene el máximo de guardias
        """
        if self.guardias_asignadas_dia >= settings.max_guardias_por_profesor_dia:
            raise MaxGuardiasDiaExceededError(
                profesor_id=self.id,
                guardias_actuales=self.guardias_asignadas_dia,
                message=f"El profesor ya tiene {self.guardias_asignadas_dia} guardias asignadas hoy"
            )

        self.guardias_asignadas_dia += 1

    def liberar_guardia(self) -> None:
        """
        Registra la liberación de una guardia del profesor.

        Decrementa el contador de guardias del día.
        """
        if self.guardias_asignadas_dia > 0:
            self.guardias_asignadas_dia -= 1

    def resetear_contador_diario(self) -> None:
        """Resetea el contador de guardias del día."""
        self.guardias_asignadas_dia = 0

    def __str__(self) -> str:
        """Representación en string."""
        return f"{self.nombre_completo} ({self.horas_contrato}, {self.turno})"

    def __repr__(self) -> str:
        """Representación para debugging."""
        return f"ProfesorEntity(id={self.id}, nombre='{self.nombre_completo}')"

    def __eq__(self, other: object) -> bool:
        """Comparación por identidad (ID)."""
        if not isinstance(other, ProfesorEntity):
            return False
        # Si ambos tienen ID, comparar por ID
        if self.id is not None and other.id is not None:
            return self.id == other.id
        # Si alguno no tiene ID, no son iguales
        return False

    def __hash__(self) -> int:
        """Hash basado en ID."""
        if self.id is not None:
            return hash(("ProfesorEntity", self.id))
        return hash(("ProfesorEntity", id(self)))  # Fallback a identidad de objeto
