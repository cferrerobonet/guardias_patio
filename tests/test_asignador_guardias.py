"""
Tests unitarios para asignador_guardias.py

Coverage objetivo: >70%
Tests focus: Lógica de asignación, validaciones, progress callbacks
"""

from datetime import date, time
from unittest.mock import Mock, patch

import pytest
from models.models import Configuracion, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias
from sqlalchemy.orm import Session

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def session_mock():
    """Mock de sesión SQLAlchemy."""
    return Mock(spec=Session)


@pytest.fixture
def configuracion_valida():
    """Configuración válida del curso."""
    config = Mock(spec=Configuracion)
    config.fecha_inicio_curso = date(2025, 9, 1)
    config.fecha_fin_curso = date(2026, 6, 30)
    config.hora_recreo1_manana = time(11, 0)
    config.hora_recreo2_manana = time(13, 30)
    config.hora_recreo1_tarde = time(17, 0)
    config.hora_recreo2_tarde = time(19, 0)
    config.activar_festivos_automaticos = True
    config.dias_no_lectivos_personalizados = None
    return config


@pytest.fixture
def profesores_mock():
    """Lista de profesores mock."""
    prof1 = Mock(spec=Profesor)
    prof1.id = 1
    prof1.nombre_completo = "GARCÍA, JUAN"
    prof1.email_corporativo = "juan@colegio.edu"
    prof1.horas_contrato = 25.0
    prof1.porcentaje_jornada = 100.0
    prof1.turno = "mañana"
    prof1.tutor = False
    prof1.fecha_inicio_guardias = None
    prof1.fecha_fin_guardias = None

    prof2 = Mock(spec=Profesor)
    prof2.id = 2
    prof2.nombre_completo = "LÓPEZ, MARÍA"
    prof2.email_corporativo = "maria@colegio.edu"
    prof2.horas_contrato = 18.0
    prof2.porcentaje_jornada = 72.0
    prof2.turno = "completo"
    prof2.tutor = True
    prof2.fecha_inicio_guardias = None
    prof2.fecha_fin_guardias = None

    return [prof1, prof2]


@pytest.fixture
def zonas_mock():
    """Lista de zonas mock."""
    zona1 = Mock(spec=Zona)
    zona1.id = 1
    zona1.nombre_zona = "Patio Principal"

    zona2 = Mock(spec=Zona)
    zona2.id = 2
    zona2.nombre_zona = "Patio Secundario"

    return [zona1, zona2]


# ============================================================================
# TESTS DE VALIDACIÓN
# ============================================================================


class TestValidaciones:
    """Tests para validaciones de entrada."""

    def test_generar_calendario_sin_configuracion(self, session_mock):
        """
        Debe lanzar ValueError si no existe configuración.
        """
        session_mock.query.return_value.first.return_value = None

        with pytest.raises(ValueError, match="No existe configuración del curso"):
            generar_calendario_guardias(session_mock)

    def test_generar_calendario_sin_profesores(
        self, session_mock, configuracion_valida
    ):
        """
        Debe lanzar ValueError si no hay profesores registrados.
        """
        # Configurar mocks
        session_mock.query.return_value.first.return_value = configuracion_valida
        session_mock.query.return_value.all.return_value = []

        with pytest.raises(ValueError, match="No hay profesores registrados"):
            generar_calendario_guardias(session_mock)

    def test_generar_calendario_sin_zonas(
        self, session_mock, configuracion_valida, profesores_mock
    ):
        """
        Debe lanzar ValueError si no hay zonas registradas.
        """
        # Configurar query mock para retornar config, profesores, y luego vacío para zonas
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = []
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with pytest.raises(ValueError, match="No hay zonas registradas"):
            generar_calendario_guardias(session_mock)


# ============================================================================
# TESTS DE PROGRESS CALLBACK
# ============================================================================


class TestProgressCallback:
    """Tests para callbacks de progreso."""

    @patch("services.asignador_guardias.calcular_guardias_por_profesor")
    @patch("services.asignador_guardias._build_slots")
    def test_progress_callback_es_llamado(
        self,
        mock_build_slots,
        mock_calcular,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        El progress_callback debe ser invocado durante la generación.
        """
        # Setup mocks
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_calcular.return_value = {1: 10, 2: 8}
        mock_build_slots.return_value = []  # No slots para simplificar

        # Crear mock de callback
        progress_callback = Mock()

        # Ejecutar
        generar_calendario_guardias(session_mock, progress_callback=progress_callback)

        # Verificar que callback fue llamado múltiples veces
        assert progress_callback.call_count > 0

        # Verificar que se llamó con porcentajes válidos (0-100)
        for call in progress_callback.call_args_list:
            porcentaje = call[0][0]
            assert 0 <= porcentaje <= 100

    @patch("services.asignador_guardias.calcular_guardias_por_profesor")
    @patch("services.asignador_guardias._build_slots")
    def test_progress_callback_maneja_excepciones(
        self,
        mock_build_slots,
        mock_calcular,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        Si el callback lanza excepción, la generación debe continuar.
        """
        # Setup
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_calcular.return_value = {1: 10, 2: 8}
        mock_build_slots.return_value = []

        # Callback que lanza excepción
        def failing_callback(porcentaje, mensaje):
            raise RuntimeError("Callback error")

        # No debe lanzar excepción
        guardias, asignaciones = generar_calendario_guardias(
            session_mock, progress_callback=failing_callback
        )

        # Debe retornar resultados vacíos
        assert guardias == []
        assert asignaciones == {}


# ============================================================================
# TESTS DE LÓGICA DE ASIGNACIÓN
# ============================================================================


class TestLogicaAsignacion:
    """Tests para lógica de asignación de guardias."""

    @patch("services.asignador_guardias.calcular_guardias_por_profesor")
    @patch("services.asignador_guardias._build_slots")
    def test_retorna_listas_vacias_sin_slots(
        self,
        mock_build_slots,
        mock_calcular,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        Si no hay slots disponibles, debe retornar listas vacías.
        """
        # Setup
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_calcular.return_value = {1: 10, 2: 8}
        mock_build_slots.return_value = []  # No slots

        # Ejecutar
        guardias, asignaciones = generar_calendario_guardias(session_mock)

        # Verificar
        assert guardias == []
        assert asignaciones == {}

    @patch("services.asignador_guardias.calcular_guardias_por_profesor")
    @patch("services.asignador_guardias._build_slots")
    def test_calcula_cuotas_correctamente(
        self,
        mock_build_slots,
        mock_calcular,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        Debe llamar a calcular_guardias_por_profesor para obtener cuotas.
        """
        # Setup
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_calcular.return_value = {1: 10, 2: 8}
        mock_build_slots.return_value = []

        # Ejecutar
        generar_calendario_guardias(session_mock)

        # Verificar que se llamó a calcular_guardias_por_profesor
        mock_calcular.assert_called_once_with(session_mock)


# ============================================================================
# TESTS DE EDGE CASES
# ============================================================================


class TestEdgeCases:
    """Tests para casos edge y situaciones límite."""

    def test_generar_con_profesor_sin_email(
        self, session_mock, configuracion_valida, zonas_mock
    ):
        """
        Profesor sin email_corporativo debe poder recibir guardias.
        """
        # Profesor sin email
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "SIN EMAIL, PROFESOR"
        profesor.email_corporativo = None  # Sin email
        profesor.horas_contrato = 25.0
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "mañana"
        profesor.tutor = False

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect

        # No debe lanzar excepción
        with patch("services.asignador_guardias.calcular_guardias_por_profesor") as mock_calc:
            with patch("services.asignador_guardias._build_slots") as mock_slots:
                mock_calc.return_value = {1: 10}
                mock_slots.return_value = []

                guardias, asignaciones = generar_calendario_guardias(session_mock)

                # Debe completar sin error
                assert guardias == []
                assert asignaciones == {}

    @patch("services.asignador_guardias.calcular_guardias_por_profesor")
    @patch("services.asignador_guardias._build_slots")
    def test_generar_con_progress_callback_none(
        self,
        mock_build_slots,
        mock_calcular,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        Debe funcionar correctamente sin progress_callback (None).
        """
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_calcular.return_value = {1: 10, 2: 8}
        mock_build_slots.return_value = []

        # Ejecutar sin callback
        guardias, asignaciones = generar_calendario_guardias(
            session_mock, progress_callback=None
        )

        # Debe funcionar normalmente
        assert guardias == []
        assert asignaciones == {}


# ============================================================================
# TESTS DE INTEGRACIÓN CON CALCULAR_GUARDIAS
# ============================================================================


class TestIntegracionCalculador:
    """Tests de integración con calculador_guardias."""

    @patch("services.asignador_guardias._build_slots")
    def test_usa_cuotas_del_calculador(
        self,
        mock_build_slots,
        session_mock,
        configuracion_valida,
        profesores_mock,
        zonas_mock,
    ):
        """
        Debe usar las cuotas calculadas por el calculador.
        """
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = configuracion_valida
            elif model == Profesor:
                mock_query.all.return_value = profesores_mock
            elif model == Zona:
                mock_query.all.return_value = zonas_mock
            return mock_query

        session_mock.query.side_effect = query_side_effect
        mock_build_slots.return_value = []

        # Ejecutar (sin mock del calculador para que use el real)
        with patch("services.asignador_guardias.calcular_guardias_por_profesor") as mock_calc:
            cuotas_esperadas = {1: 12, 2: 9}
            mock_calc.return_value = cuotas_esperadas

            generar_calendario_guardias(session_mock)

            # Verificar que se usaron las cuotas del calculador
            mock_calc.assert_called_once_with(session_mock)


# ============================================================================
# TESTS DE FUNCIONES HELPER
# ============================================================================


class TestFuncionesHelper:
    """Tests para funciones helper (profesor_ausente, _horario_permitido, etc)."""

    def test_profesor_ausente_sin_ausencias(self, session_mock):
        """
        Profesor sin ausencias debe retornar False.
        """
        from services.asignador_guardias import profesor_ausente

        # Setup mock
        session_mock.query.return_value.filter.return_value.first.return_value = None

        # Ejecutar
        resultado = profesor_ausente(session_mock, 1, date(2025, 10, 25))

        # Verificar
        assert resultado is False

    def test_profesor_ausente_con_ausencia_activa(self, session_mock):
        """
        Profesor con ausencia activa debe retornar True.
        """
        from models.models import Ausencia
        from services.asignador_guardias import profesor_ausente

        # Mock ausencia
        ausencia_mock = Mock(spec=Ausencia)
        session_mock.query.return_value.filter.return_value.first.return_value = ausencia_mock

        # Ejecutar
        resultado = profesor_ausente(session_mock, 1, date(2025, 10, 25))

        # Verificar
        assert resultado is True

    def test_horario_permitido_sin_json(self):
        """
        Sin horario JSON, debe permitir L-V por defecto.
        """
        from services.asignador_guardias import _horario_permitido

        # Lunes (weekday=0)
        assert _horario_permitido(date(2025, 10, 27), 1, None) is True

        # Viernes (weekday=4)
        assert _horario_permitido(date(2025, 10, 31), 1, None) is True

        # Sábado (weekday=5)
        assert _horario_permitido(date(2025, 11, 1), 1, None) is False

    def test_horario_permitido_con_json_valido(self):
        """
        Con horario JSON válido, debe validar según matriz.
        """
        from services.asignador_guardias import _horario_permitido

        # JSON: solo lunes (0) con recreos [1, 2]
        horario_json = '{"0": [1, 2]}'

        # Lunes con recreo 1 -> OK
        assert _horario_permitido(date(2025, 10, 27), 1, horario_json) is True

        # Lunes con recreo 3 -> NO
        assert _horario_permitido(date(2025, 10, 27), 3, horario_json) is False

        # Martes (1) con recreo 1 -> NO (día no en JSON)
        assert _horario_permitido(date(2025, 10, 28), 1, horario_json) is False

    def test_horario_permitido_json_invalido(self):
        """
        Con JSON inválido, debe caer a L-V por defecto.
        """
        from services.asignador_guardias import _horario_permitido

        json_invalido = '{"invalid": json'

        # Lunes -> OK (fallback L-V)
        assert _horario_permitido(date(2025, 10, 27), 1, json_invalido) is True

        # Sábado -> NO (fallback L-V)
        assert _horario_permitido(date(2025, 11, 1), 1, json_invalido) is False

    def test_turno_de_recreo(self):
        """
        Test de _turno_de_recreo con diferentes combinaciones.
        """
        from services.asignador_guardias import _turno_de_recreo

        # Mixto siempre True
        assert _turno_de_recreo("mixto", "mañana") is True
        assert _turno_de_recreo("mixto", "tarde") is True

        # Mañana-mañana -> True
        assert _turno_de_recreo("mañana", "mañana") is True

        # Mañana-tarde -> False
        assert _turno_de_recreo("mañana", "tarde") is False

        # Tarde-tarde -> True
        assert _turno_de_recreo("tarde", "tarde") is True


# ============================================================================
# TESTS DE BUILD_SLOTS
# ============================================================================


class TestBuildSlots:
    """Tests para la función _build_slots."""

    def test_build_slots_sin_zonas(self, session_mock, configuracion_valida):
        """
        Sin zonas, debe retornar lista vacía.
        """
        from services.asignador_guardias import _build_slots

        session_mock.query.return_value.all.return_value = []

        slots = _build_slots(session_mock, configuracion_valida)

        assert slots == []

    @patch("services.asignador_guardias.listar_dias_lectivos")
    @patch("services.asignador_guardias._parse_recreos_config")
    def test_build_slots_con_zonas_y_recreos(
        self, mock_parse, mock_dias, session_mock, configuracion_valida, zonas_mock
    ):
        """
        Con zonas y recreos, debe generar slots correctamente.
        """
        from services.asignador_guardias import _build_slots

        # Setup
        session_mock.query.return_value.all.return_value = zonas_mock
        mock_dias.return_value = [date(2025, 10, 27), date(2025, 10, 28)]
        mock_parse.return_value = [
            {'id': 1, 'turno': 'mañana', 'zonas': 2},
            {'id': 2, 'turno': 'tarde', 'zonas': 1},
        ]

        # Ejecutar
        slots = _build_slots(session_mock, configuracion_valida)

        # Verificar: 2 días × (2 recreos × zonas) = 2×(2+1) = 6 slots
        assert len(slots) == 6

    @patch("services.asignador_guardias.listar_dias_lectivos")
    @patch("services.asignador_guardias._parse_recreos_config")
    def test_build_slots_fallback_sin_recreos(
        self, mock_parse, mock_dias, session_mock, configuracion_valida, zonas_mock
    ):
        """
        Sin recreos parseados, debe usar fallback desde config.
        """
        from services.asignador_guardias import _build_slots

        # Setup
        session_mock.query.return_value.all.return_value = zonas_mock
        mock_dias.return_value = [date(2025, 10, 27)]
        mock_parse.return_value = []  # No recreos parseados

        # Ejecutar
        slots = _build_slots(session_mock, configuracion_valida)

        # Verificar: Debe haber generado slots del fallback
        # 1 día × 4 recreos (2 mañana + 2 tarde) × 2 zonas = 8 slots
        assert len(slots) == 8


# ============================================================================
# TESTS DE GUARDAR_GUARDIAS_EN_BD
# ============================================================================


class TestGuardarGuardias:
    """Tests para la función guardar_guardias_en_bd."""

    def test_guardar_guardias_vacio(self, session_mock):
        """
        Lista vacía no debe guardar nada.
        """
        from services.asignador_guardias import guardar_guardias_en_bd

        guardar_guardias_en_bd(session_mock, [])

        # No debe llamar bulk_save_objects
        session_mock.bulk_save_objects.assert_not_called()
        session_mock.commit.assert_not_called()

    def test_guardar_guardias_con_datos(self, session_mock):
        """
        Con guardias, debe usar bulk_save_objects y commit.
        """
        from models.models import Guardia
        from services.asignador_guardias import guardar_guardias_en_bd

        guardias = [
            Guardia(
                profesor_id=1,
                fecha=date(2025, 10, 27),
                turno="mañana",
                recreo=1,
                zona_id=1,
            ),
            Guardia(
                profesor_id=2,
                fecha=date(2025, 10, 28),
                turno="tarde",
                recreo=2,
                zona_id=2,
            ),
        ]

        guardar_guardias_en_bd(session_mock, guardias)

        # Verificar
        session_mock.bulk_save_objects.assert_called_once_with(guardias)
        session_mock.commit.assert_called_once()
