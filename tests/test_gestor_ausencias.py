"""
Tests para services.gestor_ausencias

Cubre todas las funcionalidades de gestión de ausencias:
- Registro, edición y eliminación de ausencias
- Búsqueda de guardias afectadas
- Obtención de profesores disponibles
- Reasignación manual y automática de guardias
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest
from infrastructure.database.models import Ausencia, Guardia, Profesor
from services.gestor_ausencias import (
    desactivar_ausencia,
    editar_ausencia,
    eliminar_ausencia,
    obtener_guardias_afectadas,
    obtener_guardias_afectadas_por_periodo,
    obtener_profesores_disponibles,
    reasignar_guardia,
    reasignar_guardias_automaticamente,
    registrar_ausencia,
)
from sqlalchemy.orm import Session


@pytest.fixture
def mock_session():
    """Crea un mock de sesión de SQLAlchemy."""
    return Mock(spec=Session)


@pytest.fixture
def profesor_fixture():
    """Fixture de profesor de ejemplo."""
    profesor = Mock(spec=Profesor)
    profesor.id = 1
    profesor.nombre_completo = "García Pérez, Juan"
    profesor.turno = "mañana"
    return profesor


@pytest.fixture
def ausencia_fixture():
    """Fixture de ausencia de ejemplo."""
    ausencia = Mock(spec=Ausencia)
    ausencia.id = 1
    ausencia.profesor_id = 1
    ausencia.fecha_inicio = date(2025, 10, 20)
    ausencia.fecha_fin = date(2025, 10, 25)
    ausencia.tipo = "baja_medica"
    ausencia.motivo = "Gripe"
    ausencia.activa = True
    ausencia.profesor = Mock(nombre_completo="García Pérez, Juan")
    return ausencia


@pytest.fixture
def guardia_fixture():
    """Fixture de guardia de ejemplo."""
    guardia = Mock(spec=Guardia)
    guardia.id = 1
    guardia.profesor_id = 1
    guardia.fecha = date(2025, 10, 23)
    guardia.turno = "mañana"
    guardia.recreo = 1
    guardia.zona = Mock(nombre_zona="Patio Principal")
    guardia.profesor = Mock(nombre_completo="García Pérez, Juan")
    return guardia


# =============================================================================
# TESTS: registrar_ausencia()
# =============================================================================


def test_registrar_ausencia_exito(mock_session, profesor_fixture):
    """Test: registrar ausencia correctamente."""
    # Arrange
    mock_session.query(Profesor).get.return_value = profesor_fixture
    profesor_id = 1
    fecha_inicio = date(2025, 10, 20)
    fecha_fin = date(2025, 10, 25)
    tipo = "baja_medica"
    motivo = "Gripe"

    # Act
    ausencia = registrar_ausencia(
        mock_session,
        profesor_id,
        fecha_inicio,
        fecha_fin,
        tipo,
        motivo,
    )

    # Assert
    assert ausencia.profesor_id == profesor_id
    assert ausencia.fecha_inicio == fecha_inicio
    assert ausencia.fecha_fin == fecha_fin
    assert ausencia.tipo == tipo
    assert ausencia.motivo == motivo
    assert ausencia.activa is True
    mock_session.add.assert_called_once()
    mock_session.commit.assert_called_once()


def test_registrar_ausencia_fecha_fin_antes_de_inicio(mock_session, profesor_fixture):
    """Test: error si fecha_fin < fecha_inicio."""
    # Arrange
    mock_session.query(Profesor).get.return_value = profesor_fixture
    fecha_inicio = date(2025, 10, 25)
    fecha_fin = date(2025, 10, 20)  # ¡Antes!

    # Act & Assert
    with pytest.raises(ValueError, match="fecha de fin debe ser posterior"):
        registrar_ausencia(
            mock_session,
            1,
            fecha_inicio,
            fecha_fin,
            "baja_medica",
        )


def test_registrar_ausencia_profesor_no_existe(mock_session):
    """Test: error si el profesor no existe."""
    # Arrange
    mock_session.query(Profesor).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe el profesor"):
        registrar_ausencia(
            mock_session,
            999,  # ID inexistente
            date(2025, 10, 20),
            date(2025, 10, 25),
            "baja_medica",
        )


def test_registrar_ausencia_tipo_no_estandar_warning(mock_session, profesor_fixture, caplog):
    """Test: warning si tipo de ausencia no es estándar."""
    # Arrange
    mock_session.query(Profesor).get.return_value = profesor_fixture

    # Act
    registrar_ausencia(
        mock_session,
        1,
        date(2025, 10, 20),
        date(2025, 10, 25),
        "tipo_raro",  # No estándar
    )

    # Assert
    assert "Tipo de ausencia no estándar" in caplog.text


def test_registrar_ausencia_con_documento(mock_session, profesor_fixture):
    """Test: registrar ausencia con documento adjunto."""
    # Arrange
    mock_session.query(Profesor).get.return_value = profesor_fixture
    documento_path = "/path/to/justificante.pdf"

    # Act
    ausencia = registrar_ausencia(
        mock_session,
        1,
        date(2025, 10, 20),
        date(2025, 10, 25),
        "baja_medica",
        documento_path=documento_path,
    )

    # Assert
    assert ausencia.documento_path == documento_path


# =============================================================================
# TESTS: editar_ausencia()
# =============================================================================


def test_editar_ausencia_exito(mock_session, ausencia_fixture):
    """Test: editar ausencia correctamente."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = ausencia_fixture
    nueva_fecha_fin = date(2025, 10, 30)

    # Act
    ausencia = editar_ausencia(
        mock_session,
        1,
        fecha_fin=nueva_fecha_fin,
    )

    # Assert
    assert ausencia.fecha_fin == nueva_fecha_fin
    mock_session.commit.assert_called_once()


def test_editar_ausencia_no_existe(mock_session):
    """Test: error si la ausencia no existe."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe la ausencia"):
        editar_ausencia(mock_session, 999)


def test_editar_ausencia_fechas_invalidas(mock_session, ausencia_fixture):
    """Test: error si fecha_fin < fecha_inicio tras edición."""
    # Arrange
    ausencia_fixture.fecha_inicio = date(2025, 10, 20)
    ausencia_fixture.fecha_fin = date(2025, 10, 25)
    mock_session.query(Ausencia).get.return_value = ausencia_fixture

    # Act & Assert
    with pytest.raises(ValueError, match="fecha de fin debe ser posterior"):
        editar_ausencia(
            mock_session,
            1,
            fecha_fin=date(2025, 10, 15),  # Antes del inicio
        )


def test_editar_ausencia_multiples_campos(mock_session, ausencia_fixture):
    """Test: editar múltiples campos a la vez."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = ausencia_fixture

    # Act
    ausencia = editar_ausencia(
        mock_session,
        1,
        tipo="permiso",
        motivo="Asuntos personales",
        activa=False,
    )

    # Assert
    assert ausencia.tipo == "permiso"
    assert ausencia.motivo == "Asuntos personales"
    assert ausencia.activa is False


# =============================================================================
# TESTS: eliminar_ausencia()
# =============================================================================


def test_eliminar_ausencia_exito(mock_session, ausencia_fixture):
    """Test: eliminar ausencia correctamente."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = ausencia_fixture

    # Act
    eliminar_ausencia(mock_session, 1)

    # Assert
    mock_session.delete.assert_called_once_with(ausencia_fixture)
    mock_session.commit.assert_called_once()


def test_eliminar_ausencia_no_existe(mock_session):
    """Test: error si la ausencia no existe."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe la ausencia"):
        eliminar_ausencia(mock_session, 999)


# =============================================================================
# TESTS: desactivar_ausencia()
# =============================================================================


def test_desactivar_ausencia_exito(mock_session, ausencia_fixture):
    """Test: desactivar ausencia (mantiene historial)."""
    # Arrange
    ausencia_fixture.activa = True
    mock_session.query(Ausencia).get.return_value = ausencia_fixture

    # Act
    ausencia = desactivar_ausencia(mock_session, 1)

    # Assert
    assert ausencia.activa is False
    mock_session.commit.assert_called_once()


def test_desactivar_ausencia_no_existe(mock_session):
    """Test: error si la ausencia no existe."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe la ausencia"):
        desactivar_ausencia(mock_session, 999)


# =============================================================================
# TESTS: obtener_guardias_afectadas()
# =============================================================================


def test_obtener_guardias_afectadas_exito(mock_session, ausencia_fixture, guardia_fixture):
    """Test: obtener guardias afectadas por ausencia."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = ausencia_fixture
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [guardia_fixture]

    # Act
    guardias = obtener_guardias_afectadas(mock_session, 1)

    # Assert
    assert len(guardias) == 1
    assert guardias[0] == guardia_fixture


def test_obtener_guardias_afectadas_ausencia_no_existe(mock_session):
    """Test: error si la ausencia no existe."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe la ausencia"):
        obtener_guardias_afectadas(mock_session, 999)


def test_obtener_guardias_afectadas_sin_guardias(mock_session, ausencia_fixture):
    """Test: ausencia sin guardias afectadas."""
    # Arrange
    mock_session.query(Ausencia).get.return_value = ausencia_fixture
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = []

    # Act
    guardias = obtener_guardias_afectadas(mock_session, 1)

    # Assert
    assert guardias == []


# =============================================================================
# TESTS: obtener_guardias_afectadas_por_periodo()
# =============================================================================


def test_obtener_guardias_afectadas_por_periodo_exito(mock_session, guardia_fixture):
    """Test: obtener guardias en periodo específico."""
    # Arrange
    mock_query = Mock()
    mock_session.query.return_value = mock_query
    mock_query.filter.return_value = mock_query
    mock_query.all.return_value = [guardia_fixture]

    # Act
    guardias = obtener_guardias_afectadas_por_periodo(
        mock_session,
        1,
        date(2025, 10, 20),
        date(2025, 10, 25),
    )

    # Assert
    assert len(guardias) == 1
    assert guardias[0] == guardia_fixture


# =============================================================================
# TESTS: obtener_profesores_disponibles()
# =============================================================================


def test_obtener_profesores_disponibles_exito(mock_session, profesor_fixture):
    """Test: obtener profesores disponibles para una guardia."""
    # Arrange
    profesor_fixture.turno = "mañana"
    mock_query_profesores = Mock()
    mock_query_guardias = Mock()

    # Configurar queries separados
    def query_side_effect(model):
        if model == Profesor:
            return mock_query_profesores
        return mock_query_guardias

    mock_session.query.side_effect = query_side_effect
    mock_query_profesores.all.return_value = [profesor_fixture]
    mock_query_guardias.filter.return_value = mock_query_guardias
    mock_query_guardias.count.return_value = 0

    # Mock profesor_ausente
    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=False):
        # Act
        disponibles = obtener_profesores_disponibles(
            mock_session,
            date(2025, 10, 23),
            "mañana",
            1,
        )

        # Assert
        assert len(disponibles) == 1
        assert disponibles[0][0] == profesor_fixture
        assert disponibles[0][1] == 0  # 0 guardias ese día


def test_obtener_profesores_disponibles_excluye_profesor(mock_session, profesor_fixture):
    """Test: excluir profesor específico de los disponibles."""
    # Arrange
    mock_session.query(Profesor).all.return_value = [profesor_fixture]

    # Act
    disponibles = obtener_profesores_disponibles(
        mock_session,
        date(2025, 10, 23),
        "mañana",
        1,
        excluir_profesor_id=1,
    )

    # Assert
    assert len(disponibles) == 0


def test_obtener_profesores_disponibles_turno_incompatible(mock_session, profesor_fixture):
    """Test: no incluir profesores con turno incompatible."""
    # Arrange
    profesor_fixture.turno = "mañana"
    mock_session.query(Profesor).all.return_value = [profesor_fixture]

    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=False):
        # Act
        disponibles = obtener_profesores_disponibles(
            mock_session,
            date(2025, 10, 23),
            "tarde",  # Turno diferente
            1,
        )

        # Assert
        assert len(disponibles) == 0


def test_obtener_profesores_disponibles_profesor_ausente(mock_session, profesor_fixture):
    """Test: no incluir profesores ausentes."""
    # Arrange
    profesor_fixture.turno = "mañana"
    mock_session.query(Profesor).all.return_value = [profesor_fixture]

    # Act
    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=True):
        disponibles = obtener_profesores_disponibles(
            mock_session,
            date(2025, 10, 23),
            "mañana",
            1,
        )

        # Assert
        assert len(disponibles) == 0


def test_obtener_profesores_disponibles_ya_tiene_guardia(mock_session, profesor_fixture):
    """Test: no incluir profesores que ya tienen guardia ese día."""
    # Arrange
    profesor_fixture.turno = "mañana"
    mock_query_profesores = Mock()
    mock_query_guardias = Mock()

    def query_side_effect(model):
        if model == Profesor:
            return mock_query_profesores
        return mock_query_guardias

    mock_session.query.side_effect = query_side_effect
    mock_query_profesores.all.return_value = [profesor_fixture]
    mock_query_guardias.filter.return_value = mock_query_guardias
    mock_query_guardias.count.return_value = 1  # Ya tiene 1 guardia

    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=False):
        # Act
        disponibles = obtener_profesores_disponibles(
            mock_session,
            date(2025, 10, 23),
            "mañana",
            1,
        )

        # Assert
        assert len(disponibles) == 0


# =============================================================================
# TESTS: reasignar_guardia()
# =============================================================================


def test_reasignar_guardia_exito(mock_session, guardia_fixture):
    """Test: reasignar guardia a nuevo profesor."""
    # Arrange
    nuevo_profesor = Mock(spec=Profesor)
    nuevo_profesor.id = 2
    nuevo_profesor.nombre_completo = "López Martín, Ana"

    mock_session.query(Guardia).get.return_value = guardia_fixture
    mock_session.query(Profesor).get.return_value = nuevo_profesor

    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=False):
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0

        # Act
        guardia = reasignar_guardia(mock_session, 1, 2)

        # Assert
        assert guardia.profesor_id == 2
        mock_session.commit.assert_called_once()


def test_reasignar_guardia_no_existe(mock_session):
    """Test: error si la guardia no existe."""
    # Arrange
    mock_session.query(Guardia).get.return_value = None

    # Act & Assert
    with pytest.raises(ValueError, match="No existe la guardia"):
        reasignar_guardia(mock_session, 999, 2)


def test_reasignar_guardia_profesor_no_existe(mock_session, guardia_fixture):
    """Test: error si el nuevo profesor no existe."""

    # Arrange
    def get_side_effect(entity_id):
        if entity_id == 1:  # guardia_id
            return guardia_fixture
        return None  # profesor_id=999 no existe

    mock_session.query().get.side_effect = get_side_effect

    # Act & Assert
    with pytest.raises(ValueError, match="No existe el profesor"):
        reasignar_guardia(mock_session, 1, 999)


def test_reasignar_guardia_profesor_ausente(mock_session, guardia_fixture):
    """Test: error si el nuevo profesor está ausente."""
    # Arrange
    nuevo_profesor = Mock(spec=Profesor)
    nuevo_profesor.id = 2
    nuevo_profesor.nombre_completo = "López Martín, Ana"

    guardia_fixture.fecha = date(2025, 10, 23)  # Asegurar que tiene fecha

    def get_side_effect(entity_id):
        if entity_id == 1:  # guardia_id
            return guardia_fixture
        return nuevo_profesor  # profesor_id=2

    mock_session.query().get.side_effect = get_side_effect

    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=True):
        # Act & Assert
        with pytest.raises(ValueError, match="está ausente"):
            reasignar_guardia(mock_session, 1, 2)


def test_reasignar_guardia_profesor_ya_tiene_guardia_ese_dia(mock_session, guardia_fixture):
    """Test: error si el profesor ya tiene guardia ese día."""
    # Arrange
    nuevo_profesor = Mock(spec=Profesor)
    nuevo_profesor.id = 2
    nuevo_profesor.nombre_completo = "López Martín, Ana"

    mock_session.query(Guardia).get.return_value = guardia_fixture
    mock_session.query(Profesor).get.return_value = nuevo_profesor

    with patch("services.validators.AusenciaChecker.profesor_ausente", return_value=False):
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1  # Ya tiene guardia

        # Act & Assert
        with pytest.raises(ValueError, match="ya tiene una guardia"):
            reasignar_guardia(mock_session, 1, 2)


# =============================================================================
# TESTS: reasignar_guardias_automaticamente()
# =============================================================================


def test_reasignar_guardias_automaticamente_exito(mock_session, guardia_fixture):
    """Test: reasignación automática exitosa."""
    # Arrange
    profesor_disponible = Mock(spec=Profesor)
    profesor_disponible.id = 2
    profesor_disponible.nombre_completo = "López Martín, Ana"

    with patch(
        "services.gestor_ausencias.obtener_profesores_disponibles",
        return_value=[(profesor_disponible, 0)],
    ):
        # Act
        resultados = reasignar_guardias_automaticamente(
            mock_session,
            [guardia_fixture],
        )

        # Assert
        assert resultados["reasignadas"] == 1
        assert resultados["fallidas"] == 0
        assert len(resultados["detalles"]) == 1
        assert resultados["detalles"][0]["estado"] == "reasignada"
        mock_session.commit.assert_called_once()


def test_reasignar_guardias_automaticamente_sin_disponibles(mock_session, guardia_fixture):
    """Test: no hay profesores disponibles."""
    # Arrange
    with patch(
        "services.gestor_ausencias.obtener_profesores_disponibles",
        return_value=[],  # Sin disponibles
    ):
        # Act
        resultados = reasignar_guardias_automaticamente(
            mock_session,
            [guardia_fixture],
        )

        # Assert
        assert resultados["reasignadas"] == 0
        assert resultados["fallidas"] == 1
        assert resultados["detalles"][0]["estado"] == "fallida"
        assert "No hay profesores disponibles" in resultados["detalles"][0]["razon"]


def test_reasignar_guardias_automaticamente_error_en_reasignacion(mock_session, guardia_fixture):
    """Test: error durante reasignación."""
    # Arrange
    profesor_disponible = Mock(spec=Profesor)
    profesor_disponible.id = 2

    with patch(
        "services.gestor_ausencias.obtener_profesores_disponibles",
        return_value=[(profesor_disponible, 0)],
    ):
        # Simular error al asignar
        guardia_fixture.profesor = Mock()
        type(guardia_fixture).profesor_id = property(
            lambda self: (_ for _ in ()).throw(Exception("Error de prueba"))
        )

        # Act
        resultados = reasignar_guardias_automaticamente(
            mock_session,
            [guardia_fixture],
        )

        # Assert
        assert resultados["fallidas"] == 1


def test_reasignar_guardias_automaticamente_multiples_guardias(mock_session):
    """Test: reasignar múltiples guardias."""
    # Arrange
    guardia1 = Mock(spec=Guardia)
    guardia1.id = 1
    guardia1.fecha = date(2025, 10, 23)
    guardia1.turno = "mañana"
    guardia1.recreo = 1
    guardia1.zona = Mock(nombre_zona="Patio A")
    guardia1.profesor = Mock(nombre_completo="Profesor A")
    guardia1.profesor_id = 1

    guardia2 = Mock(spec=Guardia)
    guardia2.id = 2
    guardia2.fecha = date(2025, 10, 24)
    guardia2.turno = "mañana"
    guardia2.recreo = 1
    guardia2.zona = Mock(nombre_zona="Patio B")
    guardia2.profesor = Mock(nombre_completo="Profesor B")
    guardia2.profesor_id = 1

    profesor_disponible = Mock(spec=Profesor)
    profesor_disponible.id = 2
    profesor_disponible.nombre_completo = "Profesor Suplente"

    with patch(
        "services.gestor_ausencias.obtener_profesores_disponibles",
        return_value=[(profesor_disponible, 0)],
    ):
        # Act
        resultados = reasignar_guardias_automaticamente(
            mock_session,
            [guardia1, guardia2],
        )

        # Assert
        assert resultados["reasignadas"] == 2
        assert resultados["fallidas"] == 0
        assert len(resultados["detalles"]) == 2


def test_reasignar_guardias_automaticamente_commit_parcial(mock_session):
    """Test: commit parcial si algunas exitosas y otras fallidas."""
    # Arrange
    guardia_exitosa = Mock(spec=Guardia)
    guardia_exitosa.id = 1
    guardia_exitosa.fecha = date(2025, 10, 23)
    guardia_exitosa.turno = "mañana"
    guardia_exitosa.recreo = 1
    guardia_exitosa.zona = Mock(nombre_zona="Patio A")
    guardia_exitosa.profesor = Mock(nombre_completo="Profesor A")
    guardia_exitosa.profesor_id = 1

    guardia_fallida = Mock(spec=Guardia)
    guardia_fallida.id = 2
    guardia_fallida.fecha = date(2025, 10, 24)
    guardia_fallida.turno = "mañana"
    guardia_fallida.recreo = 1
    guardia_fallida.zona = Mock(nombre_zona="Patio B")
    guardia_fallida.profesor = Mock(nombre_completo="Profesor B")

    profesor_disponible = Mock(spec=Profesor)
    profesor_disponible.id = 2
    profesor_disponible.nombre_completo = "Suplente"

    def side_effect_disponibles(session, fecha, turno, recreo, excluir_profesor_id=None):
        if fecha == date(2025, 10, 23):
            return [(profesor_disponible, 0)]
        else:
            return []  # Sin disponibles para segunda guardia

    with patch(
        "services.gestor_ausencias.obtener_profesores_disponibles",
        side_effect=side_effect_disponibles,
    ):
        # Act
        resultados = reasignar_guardias_automaticamente(
            mock_session,
            [guardia_exitosa, guardia_fallida],
        )

        # Assert
        assert resultados["reasignadas"] == 1
        assert resultados["fallidas"] == 1
        mock_session.commit.assert_called()  # Commit parcial
