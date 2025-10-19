"""
Tests de Integración: Flujos CRUD Completos.

Estos tests verifican flujos end-to-end que cruzan múltiples capas:
- Presentation Layer (Forms/Widgets)
- Service Layer (Business Logic)
- Domain Layer (Models)
- Data Layer (Repositories)

Objetivo: Verificar que todo el stack funciona correctamente en conjunto.
"""

from datetime import date, time

from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
from application.dtos.guardia_dto import CrearGuardiaDTO
from application.dtos.profesor_dto import ActualizarProfesorDTO, CrearProfesorDTO
from application.dtos.zona_dto import CrearZonaDTO
from application.use_cases.configuracion.actualizar_configuracion import (
    ActualizarConfiguracionUseCase,
)
from application.use_cases.guardia.asignar_guardia import AsignarGuardiaUseCase
from application.use_cases.profesor.actualizar_profesor import ActualizarProfesorUseCase
from application.use_cases.profesor.crear_profesor import CrearProfesorUseCase
from application.use_cases.zona.crear_zona import CrearZonaUseCase
from models.models import Configuracion, Guardia, Profesor, Zona

# ============================================================================
# INTEGRATION: FLUJO COMPLETO SETUP INICIAL DEL SISTEMA
# ============================================================================


class TestIntegrationSetupInicial:
    """Tests del flujo completo de configuración inicial del sistema."""

    def test_setup_sistema_desde_cero(self, session):
        """
        Flujo completo: configurar sistema desde cero.

        Simula el primer uso del sistema:
        1. Configurar curso (fechas, recreos)
        2. Crear profesores
        3. Crear zonas
        4. Verificar que todo está listo para generar guardias
        """
        # PASO 1: Configurar curso
        config_uc = ActualizarConfiguracionUseCase(session)
        config_dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.2,
            ajuste_no_tutores=1.0,
        )
        config = config_uc.execute(config_dto)

        assert config is not None
        assert config.fecha_inicio_curso == date(2024, 9, 1)

        # Verificar que se guardó en BD
        config_bd = session.query(Configuracion).first()
        assert config_bd is not None
        assert config_bd.ajuste_tutores == 1.2

        # PASO 2: Crear profesores
        profesor_uc = CrearProfesorUseCase(session)

        dto1 = CrearProfesorDTO(
            nombre_completo="Ana García",
            horas_contrato=25,
            turno="mañana",
            tutor=True,
        )
        profesor1 = profesor_uc.execute(dto1)

        dto2 = CrearProfesorDTO(
            nombre_completo="Carlos López",
            horas_contrato=18,
            turno="mañana",
            tutor=False,
        )
        profesor2 = profesor_uc.execute(dto2)

        dto3 = CrearProfesorDTO(
            nombre_completo="María Rodríguez",
            horas_contrato=25,
            turno="tarde",
            tutor=True,
        )
        profesor3 = profesor_uc.execute(dto3)

        assert profesor1.id is not None
        assert profesor2.id is not None
        assert profesor3.id is not None

        # Verificar en BD
        profesores_bd = session.query(Profesor).all()
        assert len(profesores_bd) == 3

        # PASO 3: Crear zonas
        zona_uc = CrearZonaUseCase(session)

        zona_dto1 = CrearZonaDTO(
            nombre_zona="Patio Principal",
            descripcion="Zona principal del recreo",
        )
        zona1 = zona_uc.execute(zona_dto1)

        zona_dto2 = CrearZonaDTO(
            nombre_zona="Biblioteca",
            descripcion="Vigilancia de biblioteca",
        )
        zona2 = zona_uc.execute(zona_dto2)

        zona_dto3 = CrearZonaDTO(
            nombre_zona="Comedor",
            descripcion="Vigilancia del comedor",
        )
        zona3 = zona_uc.execute(zona_dto3)

        assert zona1.id is not None
        assert zona2.id is not None
        assert zona3.id is not None

        # Verificar en BD
        zonas_bd = session.query(Zona).all()
        assert len(zonas_bd) == 3

        # PASO 4: Verificar estado final
        # Sistema debe estar listo para generar guardias
        assert session.query(Configuracion).count() == 1
        assert session.query(Profesor).count() == 3
        assert session.query(Zona).count() == 3
        assert session.query(Guardia).count() == 0  # Aún no hay guardias

    def test_modificar_configuracion_existente(self, session):
        """
        Flujo: Modificar configuración después de crearla.

        Verifica que el patrón upsert funciona correctamente:
        - Primera llamada crea
        - Segunda llamada actualiza el mismo registro
        """
        config_uc = ActualizarConfiguracionUseCase(session)

        # Primera configuración
        dto1 = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
        )
        config1 = config_uc.execute(dto1)

        config1_id = config1.id
        assert session.query(Configuracion).count() == 1

        # Actualizar configuración (debe usar el mismo registro)
        dto2 = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 45),  # Cambio
            hora_recreo2_manana=time(12, 45),  # Cambio
            ajuste_tutores=1.5,  # Nuevo
        )
        config2 = config_uc.execute(dto2)

        # Debe seguir habiendo solo 1 configuración
        assert session.query(Configuracion).count() == 1
        assert config2.id == config1_id  # Mismo ID

        # Verificar cambios
        config_bd = session.query(Configuracion).first()
        assert config_bd.hora_recreo1_manana == time(10, 45)
        assert config_bd.ajuste_tutores == 1.5


# ============================================================================
# INTEGRATION: FLUJO COMPLETO DE ASIGNACIÓN DE GUARDIAS
# ============================================================================


class TestIntegrationAsignacionGuardias:
    """Tests del flujo completo de asignación de guardias."""

    def test_flujo_completo_asignar_guardia(
        self, session, profesor_factory, zona_factory
    ):
        """
        Flujo completo: asignar una guardia manualmente.

        1. Crear profesor
        2. Crear zona
        3. Asignar guardia
        4. Verificar en todas las capas
        """
        # PASO 1: Crear profesor
        profesor = profesor_factory(
            nombre_completo="Pedro Sánchez",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        assert profesor.id is not None

        # PASO 2: Crear zona
        zona = zona_factory(
            nombre_zona="Patio",
            descripcion="Patio principal",
        )
        assert zona.id is not None

        # PASO 3: Asignar guardia usando Use Case
        asignar_uc = AsignarGuardiaUseCase(session)
        guardia_dto = CrearGuardiaDTO(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
        )
        guardia = asignar_uc.execute(guardia_dto)

        assert guardia is not None
        assert guardia.id is not None
        assert guardia.profesor_id == profesor.id
        assert guardia.zona_id == zona.id

        # PASO 4: Verificar en BD
        guardia_bd = session.query(Guardia).first()
        assert guardia_bd is not None
        assert guardia_bd.profesor_id == profesor.id
        assert guardia_bd.zona_id == zona.id
        assert guardia_bd.fecha == date(2024, 10, 15)

        # Verificar relaciones ORM
        assert guardia_bd.profesor is not None
        assert guardia_bd.profesor.nombre_completo == "Pedro Sánchez"
        assert guardia_bd.zona is not None
        assert guardia_bd.zona.nombre_zona == "Patio"

    def test_flujo_multiples_guardias_mismo_dia(
        self, session, profesor_factory, zona_factory
    ):
        """
        Flujo: Asignar múltiples guardias en el mismo día.

        Verifica que:
        - Diferentes profesores pueden tener guardia el mismo día
        - Diferentes zonas pueden usarse
        - Recreos diferentes están permitidos
        """
        # Crear profesores
        prof1 = profesor_factory(
            nombre_completo="Profesor 1",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        prof2 = profesor_factory(
            nombre_completo="Profesor 2",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )

        # Crear zonas
        zona1 = zona_factory(nombre_zona="Zona 1")
        zona2 = zona_factory(nombre_zona="Zona 2")

        asignar_uc = AsignarGuardiaUseCase(session)

        # Asignar guardias
        dto1 = CrearGuardiaDTO(
            profesor_id=prof1.id,
            zona_id=zona1.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
        )
        guardia1 = asignar_uc.execute(dto1)

        dto2 = CrearGuardiaDTO(
            profesor_id=prof2.id,
            zona_id=zona2.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
        )
        guardia2 = asignar_uc.execute(dto2)

        dto3 = CrearGuardiaDTO(
            profesor_id=prof1.id,
            zona_id=zona1.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=2,  # Mismo profesor, diferente recreo
        )
        guardia3 = asignar_uc.execute(dto3)

        # Verificar
        assert guardia1.id != guardia2.id
        assert guardia1.id != guardia3.id

        guardias_bd = session.query(Guardia).filter_by(
            fecha=date(2024, 10, 15)
        ).all()
        assert len(guardias_bd) == 3


# ============================================================================
# INTEGRATION: FLUJO DE MODIFICACIÓN Y ELIMINACIÓN
# ============================================================================


class TestIntegrationModificacionEliminacion:
    """Tests de flujos de modificación y eliminación con cascada."""

    def test_eliminar_profesor_sin_guardias(
        self, session, profesor_factory
    ):
        """
        Flujo: Eliminar profesor que no tiene guardias asignadas.

        Debe eliminarse sin problemas.
        """
        from application.use_cases.profesor.eliminar_profesor import (
            EliminarProfesorUseCase,
        )

        # Crear profesor
        profesor = profesor_factory(nombre_completo="Test Delete")
        profesor_id = profesor.id

        assert session.query(Profesor).filter_by(id=profesor_id).count() == 1

        # Eliminar
        eliminar_uc = EliminarProfesorUseCase(session)
        eliminar_uc.execute(profesor_id=profesor_id)

        # Verificar eliminación
        assert session.query(Profesor).filter_by(id=profesor_id).count() == 0

    def test_eliminar_zona_sin_guardias(self, session, zona_factory):
        """
        Flujo: Eliminar zona que no tiene guardias asignadas.

        Debe eliminarse sin problemas.
        """
        from application.use_cases.zona.eliminar_zona import EliminarZonaUseCase

        # Crear zona
        zona = zona_factory(nombre_zona="Zona a eliminar")
        zona_id = zona.id

        assert session.query(Zona).filter_by(id=zona_id).count() == 1

        # Eliminar
        eliminar_uc = EliminarZonaUseCase(session)
        eliminar_uc.execute(zona_id=zona_id)

        # Verificar eliminación
        assert session.query(Zona).filter_by(id=zona_id).count() == 0

    def test_actualizar_profesor_con_guardias(
        self, session, profesor_factory, zona_factory
    ):
        """
        Flujo: Actualizar datos de profesor que tiene guardias.

        Las guardias deben mantenerse con el profesor actualizado.
        """

        # Crear profesor
        profesor = profesor_factory(
            nombre_completo="Nombre Original",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona Test")

        # Asignar guardia
        asignar_uc = AsignarGuardiaUseCase(session)
        guardia_dto = CrearGuardiaDTO(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
        )
        guardia = asignar_uc.execute(guardia_dto)

        guardia_id = guardia.id

        # Actualizar profesor
        actualizar_uc = ActualizarProfesorUseCase(session)
        actualizar_dto = ActualizarProfesorDTO(
            nombre_completo="Nombre Actualizado",
            turno="tarde",  # Cambio de turno
        )
        actualizar_uc.execute(profesor.id, actualizar_dto)

        # Verificar que la guardia sigue existiendo
        guardia_bd = session.query(Guardia).filter_by(id=guardia_id).first()
        assert guardia_bd is not None
        assert guardia_bd.profesor_id == profesor.id

        # Verificar que el nombre del profesor se actualizó
        assert guardia_bd.profesor.nombre_completo == "Nombre Actualizado"


# ============================================================================
# INTEGRATION: FLUJO COMPLETO CON SERVICIOS
# ============================================================================


class TestIntegrationConServicios:
    """Tests de integración que usan servicios de negocio."""

    def test_calcular_estadisticas_sistema_completo(
        self, session, profesor_factory, zona_factory
    ):
        """
        Flujo: Calcular estadísticas del sistema con datos reales.

        1. Configurar curso
        2. Crear profesores y zonas
        3. Calcular estadísticas
        4. Verificar resultados
        """
        from application.use_cases.asignacion_guardias.obtener_estadisticas import (
            ObtenerEstadisticasUseCase,
        )

        # PASO 1: Configurar
        config_uc = ActualizarConfiguracionUseCase(session)
        config_dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 30),  # Un mes
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
        )
        config_uc.execute(config_dto)

        # PASO 2: Crear datos
        profesor_factory(nombre_completo="Prof 1", turno="mañana")
        profesor_factory(nombre_completo="Prof 2", turno="mañana")
        profesor_factory(nombre_completo="Prof 3", turno="tarde")

        zona_factory(nombre_zona="Zona 1")
        zona_factory(nombre_zona="Zona 2")

        # PASO 3: Calcular estadísticas
        stats_uc = ObtenerEstadisticasUseCase(session)
        stats = stats_uc.execute()

        # PASO 4: Verificar
        assert stats.num_profesores == 3
        assert stats.num_zonas == 2
        assert stats.dias_lectivos > 0
        assert stats.slots_totales > 0

    def test_calcular_distribucion_con_datos_reales(
        self, session, profesor_factory, zona_factory
    ):
        """
        Flujo: Calcular distribución de guardias con profesores reales.

        Verifica que el algoritmo de distribución funciona correctamente.
        """
        from application.use_cases.asignacion_guardias.calcular_distribucion import (
            CalcularDistribucionUseCase,
        )

        # Configurar
        config_uc = ActualizarConfiguracionUseCase(session)
        config_dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 15),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
        )
        config_uc.execute(config_dto)

        # Crear profesores con diferentes características
        prof1 = profesor_factory(
            nombre_completo="Tutor 1",
            turno="mañana",
            horas_contrato=25,
            tutor=True,
        )
        profesor_factory(
            nombre_completo="No Tutor 1",
            turno="mañana",
            horas_contrato=25,
            tutor=False,
        )
        prof3 = profesor_factory(
            nombre_completo="Parcial 1",
            turno="mañana",
            horas_contrato=18,
            tutor=False,
        )

        zona_factory(nombre_zona="Zona 1")

        # Calcular distribución
        dist_uc = CalcularDistribucionUseCase(session)
        distribucion = dist_uc.execute()

        # Verificar
        assert len(distribucion.distribucion) == 3
        assert distribucion.total_guardias > 0
        assert distribucion.slots_totales > 0

        # El tutor debería tener menos guardias (ajuste 1.2 por defecto)
        # El de 18 horas debería tener menos que el de 25 horas
        guardias_prof1 = distribucion.distribucion.get(prof1.id, 0)
        guardias_prof3 = distribucion.distribucion.get(prof3.id, 0)

        # Verificar proporcionalidad
        assert guardias_prof3 < guardias_prof1  # Menos horas = menos guardias


# ============================================================================
# INTEGRATION: FLUJO DE CONSISTENCIA DE DATOS
# ============================================================================


class TestIntegrationConsistenciaDatos:
    """Tests que verifican la consistencia de datos entre capas."""

    def test_profesor_factory_crea_en_bd(self, session, profesor_factory):
        """Verificar que profesor_factory crea realmente en la BD."""
        profesor = profesor_factory(nombre_completo="Test Factory")

        # Verificar que está en la sesión
        assert profesor in session

        # Verificar que está en la BD
        prof_bd = session.query(Profesor).filter_by(
            nombre_completo="Test Factory"
        ).first()
        assert prof_bd is not None
        assert prof_bd.id == profesor.id

    def test_zona_factory_crea_en_bd(self, session, zona_factory):
        """Verificar que zona_factory crea realmente en la BD."""
        zona = zona_factory(nombre_zona="Test Factory Zona")

        # Verificar que está en la sesión
        assert zona in session

        # Verificar que está en la BD
        zona_bd = session.query(Zona).filter_by(
            nombre_zona="Test Factory Zona"
        ).first()
        assert zona_bd is not None
        assert zona_bd.id == zona.id

    def test_relaciones_orm_bidireccionales(
        self, session, profesor_factory, zona_factory
    ):
        """
        Verificar que las relaciones ORM funcionan en ambas direcciones.

        - Guardia → Profesor
        - Profesor → Guardias
        - Guardia → Zona
        - Zona → Guardias
        """
        profesor = profesor_factory(
            nombre_completo="Prof Relaciones",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona Relaciones")

        # Crear guardias
        asignar_uc = AsignarGuardiaUseCase(session)
        dto1 = CrearGuardiaDTO(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
        )
        guardia1 = asignar_uc.execute(dto1)

        dto2 = CrearGuardiaDTO(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 16),
            turno="mañana",
            numero_recreo=1,
        )
        _ = asignar_uc.execute(dto2)

        # Refrescar desde BD
        session.expire_all()

        # Verificar relación Guardia → Profesor
        g1_bd = session.query(Guardia).filter_by(id=guardia1.id).first()
        assert g1_bd.profesor is not None
        assert g1_bd.profesor.nombre_completo == "Prof Relaciones"

        # Verificar relación Profesor → Guardias
        prof_bd = session.query(Profesor).filter_by(id=profesor.id).first()
        assert len(prof_bd.guardias) == 2

        # Verificar relación Guardia → Zona
        assert g1_bd.zona is not None
        assert g1_bd.zona.nombre_zona == "Zona Relaciones"

        # Verificar relación Zona → Guardias
        zona_bd = session.query(Zona).filter_by(id=zona.id).first()
        assert len(zona_bd.guardias) == 2
