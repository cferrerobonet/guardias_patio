"""
Tests para el algoritmo v4.0 Híbrido de asignación de guardias.

Valida:
- Cobertura completa de slots
- Equidad entre profesores
- Respeto de restricciones
- Manejo de casos especiales
"""

from datetime import date
from unittest.mock import MagicMock

import pytest
from services.asignador_guardias_v4_hibrido import (
    ContextoAsignacion,
    Slot,
    _asignar_por_rondas,
    _calcular_matriz_elegibilidad,
    _calcular_urgencia,
    _completitud_forzada,
    _es_elegible,
    _parse_json_field,
    _profesor_ausente,
    _registrar_asignacion,
    _score_slot,
    _validar_resultado,
)

# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def profesor_mock():
    """Crea un profesor mock básico."""
    profesor = MagicMock()
    profesor.id = 1
    profesor.nombre_completo = "Profesor Test"
    profesor.activo = True
    profesor.turno = "mañana"
    profesor.fecha_inicio_guardias = None
    profesor.fecha_fin_guardias = None
    profesor.dias_semana_permitidos = None
    profesor.recreos_permitidos = None
    profesor.zona_preferida_id = None
    return profesor


@pytest.fixture
def slot_mock():
    """Crea un slot mock básico."""
    return Slot(
        fecha=date(2025, 1, 15),
        turno="mañana",
        recreo_id=1,
        zona_id=1,
    )


@pytest.fixture
def contexto_mock(profesor_mock, slot_mock):
    """Crea un contexto de asignación mock."""
    ctx = ContextoAsignacion()
    ctx.profesores = [profesor_mock]
    ctx.slots = [slot_mock]
    ctx.cuotas_ideales = {profesor_mock.id: 5}
    ctx.total_slots = 1
    return ctx


@pytest.fixture
def session_mock():
    """Crea una sesión mock de SQLAlchemy."""
    session = MagicMock()
    # Mock para ausencias
    session.query.return_value.filter.return_value.first.return_value = None
    return session


# =============================================================================
# TESTS DE ESTRUCTURAS DE DATOS
# =============================================================================


class TestSlot:
    """Tests para la estructura Slot."""

    def test_slot_es_hashable(self):
        """Los slots deben poder usarse como claves de diccionario."""
        slot1 = Slot(date(2025, 1, 15), "mañana", 1, 1)
        slot2 = Slot(date(2025, 1, 15), "mañana", 1, 1)

        # Deben ser iguales
        assert slot1 == slot2
        assert hash(slot1) == hash(slot2)

        # Deben poder usarse en sets
        slots_set = {slot1}
        assert slot2 in slots_set

    def test_slot_diferentes_son_diferentes(self):
        """Slots con datos diferentes deben ser diferentes."""
        slot1 = Slot(date(2025, 1, 15), "mañana", 1, 1)
        slot2 = Slot(date(2025, 1, 16), "mañana", 1, 1)  # Diferente fecha

        assert slot1 != slot2
        assert hash(slot1) != hash(slot2)


class TestContextoAsignacion:
    """Tests para ContextoAsignacion."""

    def test_contexto_inicializa_vacio(self):
        """El contexto debe inicializar con valores por defecto vacíos."""
        ctx = ContextoAsignacion()

        assert ctx.profesores == []
        assert ctx.slots == []
        assert ctx.calendario == []
        assert ctx.total_slots == 0


# =============================================================================
# TESTS DE UTILIDADES
# =============================================================================


class TestParseJsonField:
    """Tests para _parse_json_field."""

    def test_parse_lista_valida(self):
        """Debe parsear JSON de lista correctamente."""
        result = _parse_json_field("[1, 2, 3]", [])
        assert result == [1, 2, 3]

    def test_parse_diccionario_valido(self):
        """Debe parsear JSON de diccionario correctamente."""
        result = _parse_json_field('{"0": [1, 2]}', {})
        assert result == {"0": [1, 2]}

    def test_parse_none_devuelve_default(self):
        """None debe devolver el valor por defecto."""
        result = _parse_json_field(None, [1, 2, 3, 4])
        assert result == [1, 2, 3, 4]

    def test_parse_json_invalido_devuelve_default(self):
        """JSON inválido debe devolver el valor por defecto."""
        result = _parse_json_field("esto no es json", [99])
        assert result == [99]


class TestProfesorAusente:
    """Tests para _profesor_ausente."""

    def test_profesor_sin_ausencia(self, session_mock):
        """Un profesor sin ausencias no está ausente."""
        session_mock.query.return_value.filter.return_value.first.return_value = None

        resultado = _profesor_ausente(session_mock, profesor_id=1, fecha=date(2025, 1, 15))

        assert resultado is False

    def test_profesor_con_ausencia(self, session_mock):
        """Un profesor con ausencia activa está ausente."""
        ausencia_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = ausencia_mock

        resultado = _profesor_ausente(session_mock, profesor_id=1, fecha=date(2025, 1, 15))

        assert resultado is True


# =============================================================================
# TESTS DE ELEGIBILIDAD
# =============================================================================


class TestEsElegible:
    """Tests para _es_elegible."""

    def test_profesor_elegible_basico(self, profesor_mock, slot_mock, contexto_mock, session_mock):
        """Un profesor sin restricciones debe ser elegible."""
        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)
        assert resultado is True

    def test_profesor_turno_incompatible(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor de tarde no es elegible para slot de mañana."""
        profesor_mock.turno = "tarde"
        slot_manana = Slot(date(2025, 1, 15), "mañana", 1, 1)

        resultado = _es_elegible(profesor_mock, slot_manana, contexto_mock, session_mock)

        assert resultado is False

    def test_profesor_turno_completo_elegible(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor de turno completo es elegible para cualquier turno."""
        profesor_mock.turno = "completo"

        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)

        assert resultado is True

    def test_profesor_ausente_no_elegible(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor ausente no es elegible."""
        # Simular ausencia
        ausencia_mock = MagicMock()
        session_mock.query.return_value.filter.return_value.first.return_value = ausencia_mock

        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)

        assert resultado is False

    def test_profesor_fuera_rango_fechas(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor fuera de su rango de fechas no es elegible."""
        profesor_mock.fecha_inicio_guardias = date(2025, 2, 1)  # Después del slot

        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)

        assert resultado is False

    def test_slot_ocupado_no_elegible(self, profesor_mock, slot_mock, contexto_mock, session_mock):
        """Slot ya ocupado no es elegible."""
        contexto_mock.slots_ocupados.add(slot_mock)

        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)

        assert resultado is False

    def test_profesor_ya_tiene_guardia_ese_dia(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor con guardia ese día no es elegible (por defecto)."""
        contexto_mock.guardias_por_dia[(profesor_mock.id, slot_mock.fecha)] = True

        resultado = _es_elegible(profesor_mock, slot_mock, contexto_mock, session_mock)

        assert resultado is False

    def test_profesor_excede_cuota(self, profesor_mock, slot_mock, contexto_mock, session_mock):
        """Profesor que ya alcanzó su cuota no es elegible (sin ignorar cuota)."""
        contexto_mock.asignadas[profesor_mock.id] = 5  # Igual a cuota

        resultado = _es_elegible(
            profesor_mock, slot_mock, contexto_mock, session_mock, ignorar_cuota=False
        )

        assert resultado is False

    def test_profesor_excede_cuota_pero_ignorar(
        self, profesor_mock, slot_mock, contexto_mock, session_mock
    ):
        """Profesor que excede cuota ES elegible si ignoramos cuota."""
        contexto_mock.asignadas[profesor_mock.id] = 5  # Igual a cuota

        resultado = _es_elegible(
            profesor_mock, slot_mock, contexto_mock, session_mock, ignorar_cuota=True
        )

        assert resultado is True

    def test_recreo_no_permitido(self, profesor_mock, contexto_mock, session_mock):
        """Profesor con recreo no permitido no es elegible."""
        profesor_mock.recreos_permitidos = "[2, 3]"  # Solo recreos 2 y 3
        slot_recreo_1 = Slot(date(2025, 1, 15), "mañana", 1, 1)  # Recreo 1

        resultado = _es_elegible(profesor_mock, slot_recreo_1, contexto_mock, session_mock)

        assert resultado is False


# =============================================================================
# TESTS DE MATRIZ DE ELEGIBILIDAD
# =============================================================================


class TestMatrizElegibilidad:
    """Tests para _calcular_matriz_elegibilidad."""

    def test_matriz_cuenta_slots_correctamente(self, profesor_mock, session_mock):
        """La matriz debe contar correctamente los slots elegibles."""
        ctx = ContextoAsignacion()
        ctx.profesores = [profesor_mock]
        ctx.slots = [
            Slot(date(2025, 1, 15), "mañana", 1, 1),
            Slot(date(2025, 1, 16), "mañana", 1, 1),
            Slot(date(2025, 1, 17), "tarde", 1, 1),  # Tarde - no elegible para prof mañana
        ]
        ctx.cuotas_ideales = {profesor_mock.id: 10}

        matriz = _calcular_matriz_elegibilidad(ctx, session_mock)

        # Profesor de mañana solo puede hacer 2 slots de mañana
        assert matriz[profesor_mock.id] == 2


# =============================================================================
# TESTS DE URGENCIA
# =============================================================================


class TestCalcularUrgencia:
    """Tests para _calcular_urgencia."""

    def test_profesor_sin_fecha_inicio_baja_urgencia(self, profesor_mock):
        """Profesor sin fecha_inicio tiene baja urgencia."""
        config_mock = MagicMock()
        config_mock.fecha_fin_curso = date(2025, 6, 30)

        urgencia = _calcular_urgencia(profesor_mock, config_mock, 200)

        assert urgencia == 10000.0  # Valor alto = baja prioridad

    def test_profesor_con_fecha_inicio_alta_urgencia(self, profesor_mock):
        """Profesor con fecha_inicio cercana tiene alta urgencia."""
        profesor_mock.fecha_inicio_guardias = date(2025, 5, 1)  # Cerca del fin
        config_mock = MagicMock()
        config_mock.fecha_fin_curso = date(2025, 6, 30)

        urgencia = _calcular_urgencia(profesor_mock, config_mock, 200)

        # Valor más bajo = más urgente
        assert urgencia < 10000.0


# =============================================================================
# TESTS DE SCORING
# =============================================================================


class TestScoreSlot:
    """Tests para _score_slot."""

    def test_score_prioriza_zona_preferida(self, profesor_mock, contexto_mock):
        """El scoring debe priorizar la zona preferida."""
        contexto_mock.ultima_zona[profesor_mock.id] = 1

        slot_zona1 = Slot(date(2025, 1, 15), "mañana", 1, 1)
        slot_zona2 = Slot(date(2025, 1, 15), "mañana", 1, 2)

        score1 = _score_slot(profesor_mock, slot_zona1, contexto_mock)
        score2 = _score_slot(profesor_mock, slot_zona2, contexto_mock)

        # Menor score = mejor, zona preferida debe tener mejor score
        assert score1 < score2


# =============================================================================
# TESTS DE ASIGNACIÓN
# =============================================================================


class TestRegistrarAsignacion:
    """Tests para _registrar_asignacion."""

    def test_registrar_actualiza_estado(self, profesor_mock, slot_mock, contexto_mock):
        """Registrar debe actualizar todo el estado del contexto."""
        contexto_mock.curso_id = 1

        _registrar_asignacion(profesor_mock, slot_mock, contexto_mock)

        # Verificar que se actualizó todo
        assert len(contexto_mock.calendario) == 1
        assert contexto_mock.asignadas[profesor_mock.id] == 1
        assert slot_mock in contexto_mock.slots_ocupados
        assert (profesor_mock.id, slot_mock.fecha) in contexto_mock.guardias_por_dia
        assert contexto_mock.ultima_zona[profesor_mock.id] == slot_mock.zona_id


# =============================================================================
# TESTS DE VALIDACIÓN
# =============================================================================


class TestValidarResultado:
    """Tests para _validar_resultado."""

    def test_resultado_valido_100_cobertura(self, contexto_mock, profesor_mock, slot_mock):
        """Resultado con 100% cobertura es válido."""
        contexto_mock.slots_ocupados.add(slot_mock)
        contexto_mock.asignadas[profesor_mock.id] = 5  # Igual a cuota
        contexto_mock.calendario.append(MagicMock())

        resultado = _validar_resultado(contexto_mock, [])

        assert resultado.cobertura == 100.0
        assert resultado.slots_sin_cubrir == 0

    def test_resultado_invalido_con_slots_sin_cubrir(self, contexto_mock, slot_mock):
        """Resultado con slots sin cubrir es inválido."""
        resultado = _validar_resultado(contexto_mock, [slot_mock])

        assert resultado.slots_sin_cubrir == 1
        assert resultado.es_valido is False


# =============================================================================
# TESTS DE INTEGRACIÓN
# =============================================================================


class TestGenerarGuardiasV4Hibrido:
    """Tests de integración para generar_guardias_v4_hibrido."""

    def test_genera_con_datos_minimos(self, session_mock):
        """Debe generar guardias con datos mínimos - skip por complejidad de mocks."""
        # Este test requiere configurar muchos mocks de BD
        # Se prefiere testear las funciones individuales
        pytest.skip("Test de integración requiere BD real - ver tests funcionales")


# =============================================================================
# TESTS DE RONDAS EQUITATIVAS
# =============================================================================


class TestAsignarPorRondas:
    """Tests para _asignar_por_rondas."""

    def test_rondas_distribuyen_equitativamente(self, session_mock):
        """Las rondas deben distribuir equitativamente entre profesores."""
        # Crear 3 profesores con cuota 3 cada uno
        profesores = []
        for i in range(3):
            prof = MagicMock()
            prof.id = i + 1
            prof.nombre_completo = f"Profesor {i + 1}"
            prof.turno = "mañana"
            prof.fecha_inicio_guardias = None
            prof.fecha_fin_guardias = None
            prof.dias_semana_permitidos = None
            prof.recreos_permitidos = None
            prof.zona_preferida_id = None
            profesores.append(prof)

        # Crear 9 slots (3 por profesor)
        slots = []
        for day in range(1, 10):
            slots.append(Slot(date(2025, 1, day), "mañana", 1, 1))

        ctx = ContextoAsignacion()
        ctx.profesores = profesores
        ctx.slots = slots
        ctx.cuotas_ideales = {1: 3, 2: 3, 3: 3}
        ctx.total_slots = 9
        ctx.curso_id = 1

        # Inicializar tracking
        for p in profesores:
            ctx.ultima_zona[p.id] = None
            ctx.ultimo_recreo[p.id] = None
            ctx.ultima_fecha[p.id] = None

        # Ejecutar rondas
        asignaciones = _asignar_por_rondas(ctx, profesores, session_mock, lambda p, m: None)

        # Verificar distribución equitativa
        assert asignaciones == 9  # Todos los slots asignados
        for prof in profesores:
            assert ctx.asignadas[prof.id] == 3  # 3 guardias cada uno


# =============================================================================
# TESTS DE COMPLETITUD
# =============================================================================


class TestCompletitudForzada:
    """Tests para _completitud_forzada."""

    def test_completitud_cubre_slots_faltantes(self, profesor_mock, session_mock):
        """La completitud debe cubrir slots faltantes."""
        slot1 = Slot(date(2025, 1, 15), "mañana", 1, 1)
        slot2 = Slot(date(2025, 1, 16), "mañana", 1, 1)

        ctx = ContextoAsignacion()
        ctx.profesores = [profesor_mock]
        ctx.slots = [slot1, slot2]
        ctx.cuotas_ideales = {profesor_mock.id: 1}  # Cuota baja
        ctx.total_slots = 2
        ctx.slots_ocupados = {slot1}  # Solo 1 ocupado
        ctx.asignadas[profesor_mock.id] = 1
        ctx.curso_id = 1

        # Inicializar tracking
        ctx.ultima_zona[profesor_mock.id] = None
        ctx.ultimo_recreo[profesor_mock.id] = None
        ctx.ultima_fecha[profesor_mock.id] = None

        asignaciones, imposibles = _completitud_forzada(ctx, session_mock, lambda p, m: None)

        # Slot2 debe haberse asignado ignorando cuota
        assert asignaciones == 1
        assert len(imposibles) == 0
        assert slot2 in ctx.slots_ocupados
