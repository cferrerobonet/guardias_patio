"""
Use Case: Buscar profesores por nombre o email.

Permite buscar profesores filtrando por nombre o email corporativo.
"""

import json
from typing import List

from core.observability import with_metrics
from models.models import Profesor
from sqlalchemy.orm import Session

from application.dtos.profesor_dto import ProfesorDTO


class BuscarProfesoresUseCase:
    """
    Caso de uso para buscar profesores.

    Busca profesores por nombre completo o email corporativo.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    @with_metrics("buscar_profesores")
    def execute(self, termino_busqueda: str) -> List[ProfesorDTO]:
        """
        Ejecutar la búsqueda de profesores.

        Args:
            termino_busqueda: Término a buscar en nombre o email

        Returns:
            Lista de ProfesorDTO que coinciden con la búsqueda,
            ordenados alfabéticamente por nombre
        """
        if not termino_busqueda or not termino_busqueda.strip():
            # Si no hay término de búsqueda, devolver todos
            profesores = self.session.query(Profesor).order_by(Profesor.nombre_completo).all()
        else:
            # Buscar por nombre o email (case-insensitive)
            termino = f"%{termino_busqueda.strip()}%"
            profesores = (
                self.session.query(Profesor)
                .filter(
                    (Profesor.nombre_completo.ilike(termino))
                    | (Profesor.email_corporativo.ilike(termino))
                )
                .order_by(Profesor.nombre_completo)
                .all()
            )

        return [self._convertir_a_dto(prof) for prof in profesores]

    def _convertir_a_dto(self, profesor: Profesor) -> ProfesorDTO:
        """Convertir modelo a DTO parseando campos JSON"""
        # Parsear recreos_permitidos y convertir dict a lista si es necesario
        recreos_permitidos = [1, 2]  # Default
        if profesor.recreos_permitidos:
            parsed = json.loads(profesor.recreos_permitidos)
            if isinstance(parsed, dict):
                # Si es dict {"0": [1,2], "1": [2]}, extraer todos los recreos únicos
                recreos_set = set()
                for recreos_list in parsed.values():
                    recreos_set.update(recreos_list)
                recreos_permitidos = sorted(list(recreos_set))
            elif isinstance(parsed, list):
                recreos_permitidos = parsed

        return ProfesorDTO(
            id=profesor.id,
            nombre_completo=profesor.nombre_completo,
            email_corporativo=profesor.email_corporativo,
            horas_contrato=profesor.horas_contrato,
            porcentaje_jornada=profesor.porcentaje_jornada,
            turno=profesor.turno,
            horas_manana=profesor.horas_manana,
            horas_tarde=profesor.horas_tarde,
            tutor=profesor.tutor,
            fecha_inicio_guardias=profesor.fecha_inicio_guardias,
            fecha_fin_guardias=profesor.fecha_fin_guardias,
            dias_semana_permitidos=(
                json.loads(profesor.dias_semana_permitidos)
                if profesor.dias_semana_permitidos
                else list(range(7))
            ),
            recreos_permitidos=recreos_permitidos,
        )
