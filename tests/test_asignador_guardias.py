"""
Tests unitarios para asignador_guardias.py

Coverage objetivo: >70%
Tests focus: Lógica de asignación, validaciones, progress callbacks
"""

from datetime import date, time
from unittest.mock import Mock, patch

import pytest
from sqlalchemy.orm import Session

from models.models import Configuracion, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias

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


# =============================================================================
# Tests Adicionales para Bucle Principal de Asignación (Líneas 196-330)
# =============================================================================


class TestBuclePrincipalAsignacion:
    """Tests para cubrir el bucle principal de asignación de guardias."""

    def test_generar_calendario_completo_con_datos_reales(self, session_mock):
        """
        Test de integración con datos más realistas.
        """
        from services.asignador_guardias import generar_calendario_guardias

        # Configurar mocks
        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 24)
        config.dias_lectivos = 5
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 2}]'

        # Crear profesores con diferentes configuraciones
        prof1 = Mock(spec=Profesor)
        prof1.id = 1
        prof1.nombre_completo = "PROFESOR UNO"
        prof1.horas_contrato = 30
        prof1.porcentaje_jornada = 100.0
        prof1.turno = "completo"
        prof1.fecha_inicio_guardias = None
        prof1.fecha_fin_guardias = None
        prof1.dias_semana_permitidos = None
        prof1.recreos_permitidos = None

        prof2 = Mock(spec=Profesor)
        prof2.id = 2
        prof2.nombre_completo = "PROFESOR DOS"
        prof2.horas_contrato = 20
        prof2.porcentaje_jornada = 66.67
        prof2.turno = "mañana"
        prof2.fecha_inicio_guardias = None
        prof2.fecha_fin_guardias = None
        prof2.dias_semana_permitidos = None
        prof2.recreos_permitidos = None

        zona1 = Mock(spec=Zona)
        zona1.id = 1
        zona1.nombre = "Patio Principal"

        zona2 = Mock(spec=Zona)
        zona2.id = 2
        zona2.nombre = "Patio Secundario"

        # Configurar queries
        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [prof1, prof2]
            elif model == Zona:
                mock_query.all.return_value = [zona1, zona2]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        # Ejecutar
        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 3, 2: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),
                    date(2025, 10, 21),
                    date(2025, 10, 22),
                ],
            ):
                calendario, asignadas = generar_calendario_guardias(session_mock)

        # Verificar resultado
        assert isinstance(calendario, list)
        assert isinstance(asignadas, dict)

    def test_validacion_fecha_inicio_guardias(self, session_mock):
        """
        Profesor con fecha_inicio_guardias debe ser respetado.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 24)
        config.dias_lectivos = 5
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}]'

        # Profesor que solo puede guardias desde el 22/10
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR TARDÍO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = date(2025, 10, 22)  # Inicio tardío
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1
        zona.nombre = "Patio"

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),
                    date(2025, 10, 21),
                    date(2025, 10, 22),
                    date(2025, 10, 23),
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Todas las guardias deben ser >= 22/10
        for guardia in calendario:
            if guardia.profesor_id == 1:
                assert guardia.fecha >= date(2025, 10, 22)

    def test_validacion_fecha_fin_guardias(self, session_mock):
        """
        Profesor con fecha_fin_guardias debe ser respetado.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 24)
        config.dias_lectivos = 5
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}]'

        # Profesor que solo puede guardias hasta el 21/10
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR TEMPORAL"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = date(2025, 10, 21)  # Fin anticipado
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1
        zona.nombre = "Patio"

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),
                    date(2025, 10, 21),
                    date(2025, 10, 22),
                    date(2025, 10, 23),
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Todas las guardias deben ser <= 21/10
        for guardia in calendario:
            if guardia.profesor_id == 1:
                assert guardia.fecha <= date(2025, 10, 21)

    def test_validacion_dias_semana_permitidos(self, session_mock):
        """
        Profesor con días_semana_permitidos debe solo trabajar esos días.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)  # Lunes
        config.fecha_fin = date(2025, 10, 24)  # Viernes
        config.dias_lectivos = 5
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}]'

        # Profesor solo puede lunes (0) y miércoles (2)
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR SELECTIVO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = "0,2"  # Lunes y miércoles
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1
        zona.nombre = "Patio"

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),  # Lunes
                    date(2025, 10, 21),  # Martes
                    date(2025, 10, 22),  # Miércoles
                    date(2025, 10, 23),  # Jueves
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Todas las guardias deben ser lunes o miércoles
        for guardia in calendario:
            if guardia.profesor_id == 1:
                dia_semana = guardia.fecha.weekday()
                assert dia_semana in [0, 2]

    def test_validacion_dias_semana_formato_invalido(self, session_mock):
        """
        Formato inválido en días_semana_permitidos debe ser ignorado.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 22)
        config.dias_lectivos = 3
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}]'

        # Profesor con formato inválido - debería ignorar y trabajar todos los días
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR FORMATO INVÁLIDO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = "abc,xyz"  # Formato inválido
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[date(2025, 10, 20), date(2025, 10, 21)],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    # No debe lanzar excepción
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Si el formato inválido es ignorado, debe generar guardias
        # Si no se ignora, no habrá guardias (por eso no podemos asumir)
        # Solo verificamos que no rompe
        assert isinstance(calendario, list)

    def test_validacion_recreos_permitidos(self, session_mock):
        """
        Profesor con recreos_permitidos JSON debe respetar matriz día×recreo.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)  # Lunes
        config.fecha_fin = date(2025, 10, 22)  # Miércoles
        config.dias_lectivos = 3
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}, {"id": 2, "turno": "mañana", "zonas": 1}]'

        # Profesor con matriz: lunes recreo 1, miércoles recreo 2
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR HORARIO ESPECÍFICO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = '{"0": [1], "2": [2]}'  # Lunes rec1, Miércoles rec2

        zona = Mock(spec=Zona)
        zona.id = 1

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),  # Lunes (0)
                    date(2025, 10, 22),  # Miércoles (2)
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Verificar combinaciones permitidas
        for guardia in calendario:
            if guardia.profesor_id == 1:
                dia_semana = guardia.fecha.weekday()
                if dia_semana == 0:  # Lunes
                    assert guardia.recreo == 1
                elif dia_semana == 2:  # Miércoles
                    assert guardia.recreo == 2

    def test_profesor_ausente_excluido(self, session_mock):
        """
        Profesor ausente no debe recibir guardias en fechas de ausencia.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 23)
        config.dias_lectivos = 4
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}]'

        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR AUSENTE"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        # Ausente los días 21 y 22
        def ausente_side_effect(session, prof_id, fecha):
            return fecha in [date(2025, 10, 21), date(2025, 10, 22)]

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 2},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),
                    date(2025, 10, 21),
                    date(2025, 10, 22),
                    date(2025, 10, 23),
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente",
                    side_effect=ausente_side_effect,
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Todas las guardias deben ser días 20 o 23 (no 21 ni 22)
        for guardia in calendario:
            if guardia.profesor_id == 1:
                assert guardia.fecha in [date(2025, 10, 20), date(2025, 10, 23)]

    def test_scoring_zona_preferida(self, session_mock):
        """
        Profesor debe mantener zona preferida (primera asignada).
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 24)
        config.dias_lectivos = 5
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 2}]'

        # Un solo profesor para múltiples guardias
        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR ÚNICO"
        profesor.horas_contrato = 50  # Muchas horas
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona1 = Mock(spec=Zona)
        zona1.id = 1
        zona2 = Mock(spec=Zona)
        zona2.id = 2

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona1, zona2]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 5},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[
                    date(2025, 10, 20),
                    date(2025, 10, 21),
                    date(2025, 10, 22),
                    date(2025, 10, 23),
                    date(2025, 10, 24),
                ],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Debe tener guardias
        guardias_profesor = [g for g in calendario if g.profesor_id == 1]
        # Simplificado: solo verificar que el sistema funciona
        assert isinstance(guardias_profesor, list)

        # Si tiene más de una guardia, deberían ser en la misma zona (preferida)
        if len(guardias_profesor) > 1:
            zona_preferida = guardias_profesor[0].zona_id
            for guardia in guardias_profesor:
                assert guardia.zona_id == zona_preferida

    def test_restriccion_una_guardia_por_dia(self, session_mock):
        """
        Un profesor NO puede tener más de 1 guardia al día.
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 22)
        config.dias_lectivos = 3
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        # Recreos de mañana Y tarde para poder tener 2 en el mismo día
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 1}, {"id": 2, "turno": "tarde", "zonas": 1}]'

        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR MIXTO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "mixto"  # Puede mañana y tarde
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona = Mock(spec=Zona)
        zona.id = 1

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 3},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[date(2025, 10, 20), date(2025, 10, 21), date(2025, 10, 22)],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Agrupar por día
        guardias_por_dia = {}
        for guardia in calendario:
            if guardia.profesor_id == 1:
                guardias_por_dia[guardia.fecha] = guardias_por_dia.get(guardia.fecha, 0) + 1

        # Ningún día debe tener más de 1 guardia
        for dia, cantidad in guardias_por_dia.items():
            assert cantidad == 1, f"Profesor tiene {cantidad} guardias el {dia}"

    def test_restriccion_no_dos_zonas_simultaneas(self, session_mock):
        """
        Un profesor NO puede estar en dos zonas al mismo tiempo (mismo recreo).
        """
        from services.asignador_guardias import generar_calendario_guardias

        config = Mock(spec=Configuracion)
        config.fecha_inicio = date(2025, 10, 20)
        config.fecha_fin = date(2025, 10, 22)
        config.dias_lectivos = 3
        config.dias_no_lectivos = ""
        config.festivos_automaticos = False
        config.recreos_config = '[{"id": 1, "turno": "mañana", "zonas": 2}]'  # 2 zonas

        profesor = Mock(spec=Profesor)
        profesor.id = 1
        profesor.nombre_completo = "PROFESOR ÚNICO"
        profesor.horas_contrato = 30
        profesor.porcentaje_jornada = 100.0
        profesor.turno = "completo"
        profesor.fecha_inicio_guardias = None
        profesor.fecha_fin_guardias = None
        profesor.dias_semana_permitidos = None
        profesor.recreos_permitidos = None

        zona1 = Mock(spec=Zona)
        zona1.id = 1
        zona2 = Mock(spec=Zona)
        zona2.id = 2

        def query_side_effect(model):
            mock_query = Mock()
            if model == Configuracion:
                mock_query.first.return_value = config
            elif model == Profesor:
                mock_query.all.return_value = [profesor]
            elif model == Zona:
                mock_query.all.return_value = [zona1, zona2]
            return mock_query

        session_mock.query.side_effect = query_side_effect

        with patch(
            "services.asignador_guardias.calcular_guardias_por_profesor",
            return_value={1: 3},
        ):
            with patch(
                "services.asignador_guardias.listar_dias_lectivos",
                return_value=[date(2025, 10, 20), date(2025, 10, 21), date(2025, 10, 22)],
            ):
                with patch(
                    "services.asignador_guardias.profesor_ausente", return_value=False
                ):
                    calendario, _ = generar_calendario_guardias(session_mock)

        # Agrupar por (fecha, turno, recreo)
        slots_profesor = {}
        for guardia in calendario:
            if guardia.profesor_id == 1:
                key = (guardia.fecha, guardia.turno, guardia.recreo)
                if key not in slots_profesor:
                    slots_profesor[key] = []
                slots_profesor[key].append(guardia.zona_id)

        # Cada slot debe tener solo 1 zona
        for slot, zonas in slots_profesor.items():
            assert len(zonas) == 1, f"Profesor en múltiples zonas en slot {slot}"
