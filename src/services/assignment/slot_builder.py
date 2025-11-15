"""
SlotBuilder - Construcción de slots de guardias

Responsabilidad: Generar la matriz de slots (fecha x recreo x zona)
donde se asignarán guardias.
"""

from dataclasses import dataclass
from datetime import date
from typing import List

from models.models import Configuracion, Zona
from services.calculador_guardias import _parse_recreos_config, listar_dias_lectivos
from sqlalchemy.orm import Session
from utils import get_logger

logger = get_logger(__name__)


@dataclass
class Slot:
    """Representa un espacio de guardia a asignar."""

    fecha: date
    recreo_id: int
    turno: str  # "mañana" | "tarde"
    zona_id: int


class SlotBuilder:
    """
    Constructor de slots de guardias.

    Genera la matriz completa de slots basándose en:
    - Días lectivos del periodo
    - Configuración de recreos
    - Zonas disponibles
    """

    def __init__(self, session: Session):
        self.session = session

    def build_slots(self, config: Configuracion) -> List[Slot]:
        """
        Construye todos los slots de guardias para el periodo.

        Args:
            config: Configuración con fechas y recreos

        Returns:
            Lista de Slot objetos
        """
        slots = []

        # Obtener días lectivos
        dias = listar_dias_lectivos(
            fecha_inicio=config.fecha_inicio,
            fecha_fin=config.fecha_fin,
            dias_lectivos=config.dias_lectivos,
            dias_no_lectivos=config.dias_no_lectivos or "",
            festivos_automaticos=config.festivos_automaticos,
        )

        if not dias:
            logger.warning("No hay días lectivos en el periodo configurado")
            return slots

        # Parsear configuración de recreos
        recreos = _parse_recreos_config(config.recreos_config)
        if not recreos:
            logger.warning("No hay recreos configurados, usando recreo por defecto")
            recreos = [{"id": 1, "turno": "mañana", "zonas": 1}]

        # Obtener zonas de la base de datos
        zonas = self.session.query(Zona).all()
        if not zonas:
            logger.warning("No hay zonas en BD, creando zona por defecto")
            zona_default = Zona(nombre="Zona Principal", descripcion="Zona única")
            self.session.add(zona_default)
            self.session.flush()
            zonas = [zona_default]

        # Construir slots: fecha × recreo × zona
        for dia in dias:
            for recreo in recreos:
                recreo_id = recreo["id"]
                turno = recreo.get("turno", "mañana")
                num_zonas = recreo.get("zonas", 1)

                # Asignar primeras N zonas al recreo
                zonas_asignadas = zonas[:num_zonas]

                for zona in zonas_asignadas:
                    slot = Slot(
                        fecha=dia,
                        recreo_id=recreo_id,
                        turno=turno,
                        zona_id=zona.id,
                    )
                    slots.append(slot)

        logger.info(
            f"Slots construidos: {len(slots)} "
            f"({len(dias)} días × {len(recreos)} recreos × ~{len(zonas)} zonas)"
        )

        return slots

    def count_slots_by_turno(self, slots: List[Slot]) -> dict:
        """
        Cuenta slots por turno.

        Args:
            slots: Lista de slots

        Returns:
            Dict con contadores: {"mañana": X, "tarde": Y}
        """
        contadores = {"mañana": 0, "tarde": 0}
        for slot in slots:
            if slot.turno in contadores:
                contadores[slot.turno] += 1
        return contadores

    def filter_slots_by_date_range(
        self, slots: List[Slot], fecha_inicio: date, fecha_fin: date
    ) -> List[Slot]:
        """
        Filtra slots por rango de fechas.

        Args:
            slots: Lista de slots
            fecha_inicio: Fecha inicio (inclusive)
            fecha_fin: Fecha fin (inclusive)

        Returns:
            Lista filtrada
        """
        return [
            slot
            for slot in slots
            if fecha_inicio <= slot.fecha <= fecha_fin
        ]
