"""
Tests para los Use Cases de Zona.
Tests completos de CRUD: CrearZonaUseCase, ActualizarZonaUseCase,
EliminarZonaUseCase, ObtenerZonaUseCase, ListarZonasUseCase.
"""

import pytest
from sqlalchemy.exc import SQLAlchemyError
from application.dtos.zona_dto import ActualizarZonaDTO, CrearZonaDTO
from application.use_cases.zona.actualizar_zona import ActualizarZonaUseCase
from application.use_cases.zona.crear_zona import CrearZonaUseCase
from application.use_cases.zona.eliminar_zona import EliminarZonaUseCase
from application.use_cases.zona.listar_zonas import ListarZonasUseCase
from application.use_cases.zona.obtener_zona import ObtenerZonaUseCase
from core.exceptions import BusinessLogicError, NotFoundError
from infrastructure.database.models import Zona
from utils.cache import clear_all_cache

# ============================================================================
# TEST: CREAR ZONA
# ============================================================================


class TestCrearZonaUseCase:
    """Tests del use case CrearZonaUseCase."""

    def test_crear_zona_exitosamente(self, session):
        """Crear una zona con datos válidos."""
        use_case = CrearZonaUseCase(session)
        data = CrearZonaDTO(nombre_zona="Zona Principal", descripcion="Zona de recreo principal")

        resultado = use_case.execute(data)

        assert resultado.id is not None
        assert resultado.nombre_zona == "Zona Principal"
        assert resultado.descripcion == "Zona de recreo principal"

        # Verificar en BD
        zona_bd = session.query(Zona).filter_by(id=resultado.id).first()
        assert zona_bd is not None
        assert zona_bd.nombre_zona == "Zona Principal"

    def test_crear_zona_sin_descripcion(self, session):
        """Crear zona sin descripción (campo opcional)."""
        use_case = CrearZonaUseCase(session)
        data = CrearZonaDTO(nombre_zona="Zona Sin Desc")

        resultado = use_case.execute(data)

        assert resultado.id is not None
        assert resultado.nombre_zona == "Zona Sin Desc"
        assert resultado.descripcion is None

    def test_crear_zona_nombre_duplicado(self, session, zona_factory):
        """No permitir crear zona con nombre duplicado."""
        zona_factory(nombre_zona="Zona Existente")

        use_case = CrearZonaUseCase(session)
        data = CrearZonaDTO(nombre_zona="Zona Existente")

        with pytest.raises(BusinessLogicError, match="Ya existe una zona"):
            use_case.execute(data)

    def test_crear_zona_error_bd(self, session, mocker):
        """Manejar error de base de datos al crear zona."""
        use_case = CrearZonaUseCase(session)
        data = CrearZonaDTO(nombre_zona="Zona Test")

        # Mock session.commit() para simular error
        mocker.patch.object(session, "commit", side_effect=SQLAlchemyError("Error BD"))

        with pytest.raises(BusinessLogicError, match="Error al crear la zona"):
            use_case.execute(data)

        # Verificar rollback
        assert session.query(Zona).count() == 0


# ============================================================================
# TEST: ACTUALIZAR ZONA
# ============================================================================


class TestActualizarZonaUseCase:
    """Tests del use case ActualizarZonaUseCase."""

    def test_actualizar_zona_nombre(self, session, zona_factory):
        """Actualizar el nombre de una zona."""
        zona = zona_factory(nombre_zona="Zona Original", descripcion="Desc original")

        use_case = ActualizarZonaUseCase(session)
        data = ActualizarZonaDTO(nombre_zona="Zona Actualizada", descripcion="Desc original")

        resultado = use_case.execute(zona.id, data)

        assert resultado.nombre_zona == "Zona Actualizada"

        # Verificar en BD
        zona_bd = session.query(Zona).get(zona.id)
        assert zona_bd.nombre_zona == "Zona Actualizada"

    def test_actualizar_zona_descripcion(self, session, zona_factory):
        """Actualizar la descripción de una zona."""
        zona = zona_factory(nombre_zona="Zona Test", descripcion="Desc original")

        use_case = ActualizarZonaUseCase(session)
        data = ActualizarZonaDTO(nombre_zona="Zona Test", descripcion="Nueva descripción")

        resultado = use_case.execute(zona.id, data)

        assert resultado.descripcion == "Nueva descripción"

    def test_actualizar_zona_no_existente(self, session):
        """No permitir actualizar zona que no existe."""
        use_case = ActualizarZonaUseCase(session)
        data = ActualizarZonaDTO(nombre_zona="Zona Fantasma")

        with pytest.raises(NotFoundError, match="No se encontró la zona con ID 9999"):
            use_case.execute(9999, data)

    def test_actualizar_zona_nombre_duplicado(self, session, zona_factory):
        """No permitir actualizar con nombre de otra zona existente."""
        zona_factory(nombre_zona="Zona 1")
        zona2 = zona_factory(nombre_zona="Zona 2")

        use_case = ActualizarZonaUseCase(session)
        # Intentar cambiar Zona 2 al nombre de Zona 1
        data = ActualizarZonaDTO(nombre_zona="Zona 1")

        with pytest.raises(BusinessLogicError, match="Ya existe otra zona"):
            use_case.execute(zona2.id, data)

    def test_actualizar_zona_mismo_nombre(self, session, zona_factory):
        """Permitir actualizar zona manteniendo su mismo nombre."""
        zona = zona_factory(nombre_zona="Zona Test", descripcion="Desc original")

        use_case = ActualizarZonaUseCase(session)
        # Mismo nombre, cambiar solo descripción
        data = ActualizarZonaDTO(nombre_zona="Zona Test", descripcion="Nueva desc")

        resultado = use_case.execute(zona.id, data)

        assert resultado.nombre_zona == "Zona Test"
        assert resultado.descripcion == "Nueva desc"


# ============================================================================
# TEST: ELIMINAR ZONA
# ============================================================================


class TestEliminarZonaUseCase:
    """Tests del use case EliminarZonaUseCase."""

    def test_eliminar_zona_sin_guardias(self, session, zona_factory):
        """Eliminar zona que no tiene guardias asociadas."""
        zona = zona_factory(nombre_zona="Zona a Eliminar")
        zona_id = zona.id

        use_case = EliminarZonaUseCase(session)
        use_case.execute(zona_id)

        # Verificar que se eliminó
        zona_eliminada = session.query(Zona).get(zona_id)
        assert zona_eliminada is None

    def test_eliminar_zona_no_existente(self, session):
        """No permitir eliminar zona que no existe."""
        use_case = EliminarZonaUseCase(session)

        with pytest.raises(NotFoundError, match="No se encontró la zona con ID 9999"):
            use_case.execute(9999)

    def test_eliminar_zona_con_guardias(
        self, session, zona_factory, guardia_factory, profesor_factory
    ):
        """No permitir eliminar zona que tiene guardias asociadas."""
        zona = zona_factory(nombre_zona="Zona con Guardias")
        profesor = profesor_factory()

        # Crear una guardia asociada
        guardia_factory(zona_id=zona.id, profesor_id=profesor.id)

        use_case = EliminarZonaUseCase(session)

        with pytest.raises(BusinessLogicError, match="guardia.*asignada"):
            use_case.execute(zona.id)

        # Verificar que no se eliminó
        zona_existente = session.query(Zona).get(zona.id)
        assert zona_existente is not None


# ============================================================================
# TEST: OBTENER ZONA
# ============================================================================


class TestObtenerZonaUseCase:
    """Tests del use case ObtenerZonaUseCase."""

    def test_obtener_zona_por_id(self, session, zona_factory):
        """Obtener una zona por su ID."""
        zona = zona_factory(nombre_zona="Zona Test", descripcion="Descripción test")

        use_case = ObtenerZonaUseCase(session)
        resultado = use_case.execute(zona.id)

        assert resultado.id == zona.id
        assert resultado.nombre_zona == "Zona Test"
        assert resultado.descripcion == "Descripción test"

    def test_obtener_zona_no_existente(self, session):
        """Lanzar excepción si zona no existe."""
        use_case = ObtenerZonaUseCase(session)

        with pytest.raises(NotFoundError, match="No se encontró la zona con ID 9999"):
            use_case.execute(9999)


# ============================================================================
# TEST: LISTAR ZONAS
# ============================================================================


class TestListarZonasUseCase:
    """Tests del use case ListarZonasUseCase."""

    def test_listar_zonas_vacio(self, session):
        """Listar cuando no hay zonas devuelve lista vacía."""
        use_case = ListarZonasUseCase(session)
        resultado = use_case.execute()

        assert isinstance(resultado, list)
        assert len(resultado) == 0

    def test_listar_zonas_con_datos(self, session, zona_factory):
        """Listar zonas devuelve todas las zonas."""
        zona_factory(nombre_zona="Zona A")
        zona_factory(nombre_zona="Zona B")
        zona_factory(nombre_zona="Zona C")

        use_case = ListarZonasUseCase(session)
        resultado = use_case.execute()

        assert len(resultado) == 3
        nombres = [z.nombre_zona for z in resultado]
        assert "Zona A" in nombres
        assert "Zona B" in nombres
        assert "Zona C" in nombres

    def test_listar_zonas_orden_alfabetico(self, session, zona_factory):
        """Listar zonas ordenadas alfabéticamente por nombre."""
        zona_factory(nombre_zona="Zona C")
        zona_factory(nombre_zona="Zona A")
        zona_factory(nombre_zona="Zona B")

        use_case = ListarZonasUseCase(session)
        resultado = use_case.execute()

        nombres = [z.nombre_zona for z in resultado]
        assert nombres == ["Zona A", "Zona B", "Zona C"]


# ============================================================================
# TEST: INTEGRACIÓN
# ============================================================================


class TestZonaUseCasesIntegracion:
    """Tests de integración entre use cases de Zona."""

    def test_flujo_completo_crud(self, session):
        """Flujo: Crear → Listar → Obtener → Actualizar → Eliminar."""
        # 1. Crear
        crear_uc = CrearZonaUseCase(session)
        data_crear = CrearZonaDTO(nombre_zona="Zona CRUD Test", descripcion="Test")
        zona_creada = crear_uc.execute(data_crear)
        zona_id = zona_creada.id
        assert zona_id is not None

        # 2. Listar (debe encontrar la zona creada)
        listar_uc = ListarZonasUseCase(session)
        zonas = listar_uc.execute()
        zona_encontrada = next((z for z in zonas if z.id == zona_id), None)
        assert zona_encontrada is not None
        assert zona_encontrada.nombre_zona == "Zona CRUD Test"

        # 3. Obtener
        obtener_uc = ObtenerZonaUseCase(session)
        zona_obtenida = obtener_uc.execute(zona_id)
        assert zona_obtenida.nombre_zona == "Zona CRUD Test"

        # 4. Actualizar
        actualizar_uc = ActualizarZonaUseCase(session)
        data_actualizar = ActualizarZonaDTO(
            nombre_zona="Zona Actualizada", descripcion="Nueva desc"
        )
        zona_actualizada = actualizar_uc.execute(zona_id, data_actualizar)
        assert zona_actualizada.nombre_zona == "Zona Actualizada"

        # 5. Eliminar
        eliminar_uc = EliminarZonaUseCase(session)
        eliminar_uc.execute(zona_id)

        # Limpiar cache para verificar eliminación real
        clear_all_cache()

        # Verificar eliminación (la zona ya no existe)
        with pytest.raises(NotFoundError):
            obtener_uc.execute(zona_id)

    def test_crear_multiples_zonas_listar(self, session):
        """Crear múltiples zonas y verificar listado."""
        crear_uc = CrearZonaUseCase(session)

        for i in range(5):
            data = CrearZonaDTO(nombre_zona=f"Zona {i + 1}")
            crear_uc.execute(data)

        listar_uc = ListarZonasUseCase(session)
        zonas = listar_uc.execute()

        assert len(zonas) == 5
