"""
Use Case: Actualizar un profesor existente.

Permite modificar los datos de un profesor registrado en el sistema.
"""

import json

from models.models import Profesor
from sqlalchemy.orm import Session
from utils.exceptions import BusinessLogicError, NotFoundError
from utils.logger import get_logger
from utils.validators import validar_email, validar_horas_contrato, validar_nombre_completo

from application.dtos.profesor_dto import ActualizarProfesorDTO, ProfesorDTO

logger = get_logger(__name__)


class ActualizarProfesorUseCase:
    """
    Caso de uso para actualizar un profesor existente.

    Permite modificar cualquiera de los campos del profesor.
    """

    def __init__(self, session: Session):
        """
        Inicializar el caso de uso.

        Args:
            session: Sesión de SQLAlchemy para acceso a base de datos
        """
        self.session = session

    def execute(self, profesor_id: int, data: ActualizarProfesorDTO) -> ProfesorDTO:
        """
        Ejecutar la actualización de un profesor.

        Args:
            profesor_id: ID del profesor a actualizar
            data: DTO con los datos a actualizar (campos opcionales)

        Returns:
            ProfesorDTO con los datos actualizados del profesor

        Raises:
            NotFoundError: Si no existe un profesor con ese ID
            BusinessLogicError: Si el nuevo nombre ya está en uso por otro profesor
        """
        # Buscar el profesor a actualizar
        profesor = self.session.query(Profesor).filter(Profesor.id == profesor_id).first()

        if not profesor:
            raise NotFoundError(f"No se encontró el profesor con ID {profesor_id}")

        # Si se va a cambiar el nombre, verificar que no exista otro profesor con ese nombre
        if data.nombre_completo and data.nombre_completo != profesor.nombre_completo:
            try:
                validar_nombre_completo(data.nombre_completo)
            except ValueError as e:
                raise BusinessLogicError(str(e)) from e

            profesor_existente = (
                self.session.query(Profesor)
                .filter(Profesor.nombre_completo == data.nombre_completo)
                .filter(Profesor.id != profesor_id)
                .first()
            )

            if profesor_existente:
                raise BusinessLogicError(
                    f"Ya existe otro profesor con el nombre '{data.nombre_completo}'"
                )

        # Validar otros campos si se proporcionan
        if data.horas_contrato is not None:
            try:
                validar_horas_contrato(data.horas_contrato)
            except ValueError as e:
                raise BusinessLogicError(str(e)) from e

        if data.email_corporativo:
            try:
                validar_email(data.email_corporativo)
            except ValueError as e:
                raise BusinessLogicError(str(e)) from e

        # Actualizar campos si se proporcionan
        if data.nombre_completo is not None:
            profesor.nombre_completo = data.nombre_completo

        if data.email_corporativo is not None:
            profesor.email_corporativo = data.email_corporativo

        if data.horas_contrato is not None:
            profesor.horas_contrato = data.horas_contrato
            # Recalcular porcentaje de jornada
            profesor.porcentaje_jornada = data.horas_contrato / 25.0

        if data.turno is not None:
            profesor.turno = data.turno

        if data.horas_manana is not None:
            profesor.horas_manana = data.horas_manana

        if data.horas_tarde is not None:
            profesor.horas_tarde = data.horas_tarde

        if data.tutor is not None:
            profesor.tutor = data.tutor

        if data.fecha_inicio_guardias is not None:
            profesor.fecha_inicio_guardias = data.fecha_inicio_guardias

        if data.fecha_fin_guardias is not None:
            profesor.fecha_fin_guardias = data.fecha_fin_guardias

        if data.dias_semana_permitidos is not None:
            profesor.dias_semana_permitidos = json.dumps(data.dias_semana_permitidos)

        if data.recreos_permitidos is not None:
            profesor.recreos_permitidos = json.dumps(data.recreos_permitidos)

        try:
            self.session.commit()
            self.session.refresh(profesor)

            logger.info(
                f"Profesor actualizado: {profesor.nombre_completo} (ID: {profesor.id})"
            )

            return self._convertir_a_dto(profesor)

        except Exception as e:
            self.session.rollback()
            raise BusinessLogicError(f"Error al actualizar el profesor: {str(e)}") from e

    def _convertir_a_dto(self, profesor: Profesor) -> ProfesorDTO:
        """Convertir modelo a DTO parseando campos JSON"""
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
            recreos_permitidos=(
                json.loads(profesor.recreos_permitidos)
                if profesor.recreos_permitidos
                else [1, 2]
            ),
        )
