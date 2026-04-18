"""
Tests para los Use Cases de Guardia.
Tests completos: AsignarGuardiaUseCase, ObtenerGuardiasUseCase.
"""

from datetime import date

import pytest
from application.dtos.guardia_dto import CrearGuardiaDTO, FiltroGuardiasDTO
from application.use_cases.guardia.asignar_guardia import AsignarGuardiaUseCase
from application.use_cases.guardia.obtener_guardias import ObtenerGuardiasUseCase
from core.exceptions import BusinessLogicError, NotFoundError, ValidationError
from infrastructure.database.models import Guardia

# ============================================================================
# TEST: ASIGNAR GUARDIA
# ============================================================================


class TestAsignarGuardiaUseCase:
    """Tests del use case AsignarGuardiaUseCase."""

    def test_asignar_guardia_exitosamente(self, session, profesor_factory, zona_factory):
        """Asignar una guardia con datos válidos."""
        profesor = profesor_factory(
            nombre_completo="Juan García",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Patio Principal")

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
            es_sustitucion=False,
        )

        resultado = use_case.execute(dto)

        assert resultado.id is not None
        assert resultado.profesor_id == profesor.id
        assert resultado.zona_id == zona.id
        assert resultado.fecha == date(2024, 10, 15)
        assert resultado.turno == "mañana"
        assert resultado.numero_recreo == 1
        assert resultado.es_sustitucion is False
        assert resultado.profesor_nombre == "Juan García"
        assert resultado.zona_nombre == "Patio Principal"

        # Verificar en BD
        guardia_bd = session.query(Guardia).filter_by(id=resultado.id).first()
        assert guardia_bd is not None
        assert guardia_bd.profesor_id == profesor.id

    def test_asignar_guardia_sustitucion(self, session, profesor_factory, zona_factory):
        """Asignar una guardia como sustitución."""
        profesor_titular = profesor_factory(nombre_completo="Titular")
        profesor_sustituto = profesor_factory(
            nombre_completo="Sustituto",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona A")

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor_sustituto.id,
            zona_id=zona.id,
            es_sustitucion=True,
            profesor_sustituido_id=profesor_titular.id,
        )

        resultado = use_case.execute(dto)

        assert resultado.id is not None
        assert resultado.profesor_id == profesor_sustituto.id
        assert resultado.es_sustitucion is True
        assert resultado.profesor_sustituido_id == profesor_titular.id

    def test_asignar_guardia_profesor_no_existe(self, session, zona_factory):
        """Error al asignar guardia a profesor inexistente."""
        zona = zona_factory(nombre_zona="Zona Test")

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=9999,  # No existe
            zona_id=zona.id,
        )

        with pytest.raises(NotFoundError, match="Profesor"):
            use_case.execute(dto)

    def test_asignar_guardia_zona_no_existe(self, session, profesor_factory):
        """Error al asignar guardia a zona inexistente."""
        profesor = profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=9999,  # No existe
        )

        with pytest.raises(NotFoundError, match="Zona"):
            use_case.execute(dto)

    def test_asignar_guardia_profesor_no_puede(self, session, profesor_factory, zona_factory):
        """Error al asignar guardia cuando el profesor no puede hacerla."""
        # Profesor con turno "tarde" no puede hacer guardias de "mañana"
        profesor = profesor_factory(
            nombre_completo="Profesor Tarde",
            turno="tarde",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona A")

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",  # Conflicto con turno del profesor
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )

        with pytest.raises(BusinessLogicError, match="No se puede asignar guardia"):
            use_case.execute(dto)

    def test_asignar_guardia_conflicto_profesor(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Error al asignar guardia cuando el profesor ya tiene una en ese momento."""
        profesor = profesor_factory(
            nombre_completo="Juan García",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona1 = zona_factory(nombre_zona="Zona A")
        zona2 = zona_factory(nombre_zona="Zona B")

        # Guardia existente
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona1.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        # Intentar asignar otra guardia en el mismo momento
        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=zona2.id,  # Zona diferente pero mismo momento
        )

        with pytest.raises(BusinessLogicError, match="ya tiene guardia asignada"):
            use_case.execute(dto)

    def test_asignar_guardia_zona_validacion(
        self, session, profesor_factory, zona_factory, guardia_factory, mocker
    ):
        """Error al asignar guardia cuando la zona no puede aceptar más profesores."""
        zona = zona_factory(nombre_zona="Zona Test")

        # Crear 2 profesores ya asignados
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

        guardia_factory(
            profesor_id=prof1.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=prof2.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        # Mock de ZonaEntity para simular capacidad limitada
        from domain.entities.zona_entity import ZonaEntity

        zona_entity_mock = ZonaEntity(
            id=zona.id, nombre_zona=zona.nombre_zona, capacidad_profesores=2
        )

        # Intentar asignar un tercer profesor (excede capacidad)
        prof3 = profesor_factory(
            nombre_completo="Profesor 3",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )

        use_case = AsignarGuardiaUseCase(session)

        # Mock del repositorio para devolver la entidad con capacidad limitada
        mocker.patch.object(use_case.zona_repo, "get_by_id", return_value=zona_entity_mock)

        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=prof3.id,
            zona_id=zona.id,
        )

        with pytest.raises(BusinessLogicError, match="capacidad máxima"):
            use_case.execute(dto)

    def test_asignar_guardia_error_bd(self, session, profesor_factory, zona_factory, mocker):
        """Manejar error de base de datos al asignar guardia."""
        profesor = profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona Test")

        use_case = AsignarGuardiaUseCase(session)
        dto = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )

        # Mock session.commit() para simular error
        mocker.patch.object(session, "commit", side_effect=Exception("Error BD"))

        with pytest.raises(ValidationError, match="Error al asignar guardia"):
            use_case.execute(dto)

        # Verificar rollback (no debe haber guardia creada)
        assert session.query(Guardia).count() == 0


# ============================================================================
# TEST: OBTENER GUARDIAS
# ============================================================================


class TestObtenerGuardiasUseCase:
    """Tests del use case ObtenerGuardiasUseCase."""

    def test_obtener_guardias_sin_filtros(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener todas las guardias sin aplicar filtros."""
        profesor = profesor_factory(nombre_completo="Juan García")
        zona = zona_factory(nombre_zona="Patio A")

        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 16),
            turno="tarde",
            recreo=2,
        )

        use_case = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO()

        resultado = use_case.execute(filtros)

        assert len(resultado) == 2
        assert all(g.profesor_nombre == "Juan García" for g in resultado)

    def test_obtener_guardias_por_rango_fechas(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener guardias filtrando por rango de fechas."""
        profesor = profesor_factory(nombre_completo="Test")
        zona = zona_factory(nombre_zona="Zona A")

        # Guardias en diferentes fechas
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 10),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 20),
            turno="mañana",
            recreo=1,
        )

        use_case = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(fecha_inicio=date(2024, 10, 12), fecha_fin=date(2024, 10, 18))

        resultado = use_case.execute(filtros)

        # Solo debe devolver la del 15 (entre 12 y 18)
        assert len(resultado) == 1
        assert resultado[0].fecha == date(2024, 10, 15)

    def test_obtener_guardias_por_profesor(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener guardias filtrando por profesor."""
        prof1 = profesor_factory(nombre_completo="Profesor 1")
        prof2 = profesor_factory(nombre_completo="Profesor 2")
        zona = zona_factory(nombre_zona="Zona A")

        guardia_factory(
            profesor_id=prof1.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=prof2.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        use_case = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(profesor_id=prof1.id)

        resultado = use_case.execute(filtros)

        assert len(resultado) == 1
        assert resultado[0].profesor_nombre == "Profesor 1"

    def test_obtener_guardias_por_zona(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener guardias filtrando por zona."""
        profesor = profesor_factory(nombre_completo="Test")
        zona1 = zona_factory(nombre_zona="Zona A")
        zona2 = zona_factory(nombre_zona="Zona B")

        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona1.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona2.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        use_case = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(zona_id=zona1.id)

        resultado = use_case.execute(filtros)

        assert len(resultado) == 1
        assert resultado[0].zona_nombre == "Zona A"

    def test_obtener_solo_sustituciones(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener solo guardias que son sustituciones."""
        profesor = profesor_factory(nombre_completo="Test")
        zona = zona_factory(nombre_zona="Zona A")

        # Guardia normal
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        # Guardia sustitución con es_sustitucion=True en BD
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 16),
            turno="mañana",
            recreo=1,
            es_sustitucion=True,
        )

        use_case = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(solo_sustituciones=True)

        resultado = use_case.execute(filtros)

        assert isinstance(resultado, list)
        assert len(resultado) == 1
        assert resultado[0].es_sustitucion is True

    def test_obtener_guardias_filtros_multiples(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Obtener guardias aplicando múltiples filtros."""
        prof1 = profesor_factory(nombre_completo="Profesor 1")
        prof2 = profesor_factory(nombre_completo="Profesor 2")
        zona = zona_factory(nombre_zona="Zona A")

        # Crear varias guardias con diferentes características
        guardia_factory(
            profesor_id=prof1.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=prof1.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="tarde",
            recreo=2,
        )
        guardia_factory(
            profesor_id=prof2.id,
            zona_id=zona.id,
            fecha=date(2024, 10, 15),
            turno="mañana",
            recreo=1,
        )

        use_case = ObtenerGuardiasUseCase(session)
        # Filtrar por rango de fechas + turno
        filtros = FiltroGuardiasDTO(
            fecha_inicio=date(2024, 10, 1),
            fecha_fin=date(2024, 10, 31),
            turno="mañana",
        )

        resultado = use_case.execute(filtros)

        # Solo debe devolver las guardias de mañana
        assert len(resultado) == 2
        assert all(g.turno == "mañana" for g in resultado)


# ============================================================================
# TEST: INTEGRACIÓN GUARDIAS
# ============================================================================


class TestGuardiaUseCasesIntegracion:
    """Tests de integración entre los use cases de Guardia."""

    def test_flujo_completo_asignar_y_obtener(self, session, profesor_factory, zona_factory):
        """Flujo completo: asignar guardia y luego obtenerla con filtros."""
        profesor = profesor_factory(
            nombre_completo="Juan García",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Patio Principal")

        # 1. Asignar guardia
        asignar_uc = AsignarGuardiaUseCase(session)
        dto_crear = CrearGuardiaDTO(
            fecha=date(2024, 10, 15),
            turno="mañana",
            numero_recreo=1,
            profesor_id=profesor.id,
            zona_id=zona.id,
        )

        guardia_asignada = asignar_uc.execute(dto_crear)
        assert guardia_asignada.id is not None

        # 2. Obtener guardia creada
        obtener_uc = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(profesor_id=profesor.id)

        guardias = obtener_uc.execute(filtros)

        assert len(guardias) == 1
        assert guardias[0].id == guardia_asignada.id
        assert guardias[0].profesor_nombre == "Juan García"
        assert guardias[0].zona_nombre == "Patio Principal"

    def test_asignar_multiples_y_filtrar_por_fecha(self, session, profesor_factory, zona_factory):
        """Asignar múltiples guardias y filtrar por rango de fechas."""
        profesor = profesor_factory(
            nombre_completo="María López",
            turno="mañana",
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2025, 6, 30),
        )
        zona = zona_factory(nombre_zona="Zona A")

        asignar_uc = AsignarGuardiaUseCase(session)

        # Asignar 3 guardias en fechas diferentes
        fechas = [date(2024, 10, 10), date(2024, 10, 15), date(2024, 10, 20)]
        for fecha in fechas:
            dto = CrearGuardiaDTO(
                fecha=fecha,
                turno="mañana",
                numero_recreo=1,
                profesor_id=profesor.id,
                zona_id=zona.id,
            )
            asignar_uc.execute(dto)

        # Filtrar solo las del rango 12-18 octubre
        obtener_uc = ObtenerGuardiasUseCase(session)
        filtros = FiltroGuardiasDTO(fecha_inicio=date(2024, 10, 12), fecha_fin=date(2024, 10, 18))

        resultado = obtener_uc.execute(filtros)

        assert len(resultado) == 1
        assert resultado[0].fecha == date(2024, 10, 15)
