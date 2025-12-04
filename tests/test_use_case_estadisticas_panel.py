"""
Tests para ObtenerEstadisticasPanelUseCase.

Verifica que el use case calcula correctamente las estadísticas
para el panel de UI.
"""

from datetime import date, timedelta

import pytest
from application.dtos.asignacion_guardias_dto import (
    DatosGraficoDTO,
    EstadisticasPanelCompletoDTO,
    ResumenPanelDTO,
)
from application.use_cases.asignacion_guardias import ObtenerEstadisticasPanelUseCase
from infrastructure.database.models import Guardia

# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def use_case(session):
    """Fixture para el use case."""
    return ObtenerEstadisticasPanelUseCase(session)


@pytest.fixture
def datos_completos(session, profesor_factory, zona_factory):
    """Fixture con profesores, zonas y guardias para tests completos."""
    # Crear 5 profesores
    profesores = [
        profesor_factory(nombre_completo=f"Profesor {i}", horas_contrato=25.0) for i in range(1, 6)
    ]
    session.add_all(profesores)

    # Crear 3 zonas
    zonas = [zona_factory(nombre_zona=f"Zona {chr(65 + i)}") for i in range(3)]
    session.add_all(zonas)
    session.commit()

    # Crear guardias distribuidas
    hoy = date.today()
    guardias = []

    # Profesor 1: 10 guardias (5 mañana, 5 tarde)
    for i in range(10):
        turno = "mañana" if i < 5 else "tarde"
        g = Guardia(
            fecha=hoy + timedelta(days=i),
            turno=turno,
            recreo=(i % 3) + 1,
            profesor_id=profesores[0].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesor 2: 6 guardias (todas mañana)
    for i in range(6):
        g = Guardia(
            fecha=hoy + timedelta(days=i + 10),
            turno="mañana",
            recreo=(i % 3) + 1,
            profesor_id=profesores[1].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesor 3: 4 guardias (todas tarde)
    for i in range(4):
        g = Guardia(
            fecha=hoy + timedelta(days=i + 20),
            turno="tarde",
            recreo=(i % 3) + 1,
            profesor_id=profesores[2].id,
            zona_id=zonas[i % 3].id,
        )
        guardias.append(g)

    # Profesores 4 y 5: sin guardias

    session.add_all(guardias)
    session.commit()

    return {"profesores": profesores, "zonas": zonas, "guardias": guardias}


# ============================================================================
# TESTS BÁSICOS
# ============================================================================


class TestObtenerEstadisticasPanelBasico:
    """Tests básicos del use case."""

    def test_crear_use_case(self, session):
        """Test que se puede crear el use case."""
        use_case = ObtenerEstadisticasPanelUseCase(session)
        assert use_case is not None
        assert use_case.session == session

    def test_execute_sin_datos(self, use_case):
        """Test execute cuando no hay datos."""
        resultado = use_case.execute()

        assert isinstance(resultado, EstadisticasPanelCompletoDTO)
        assert resultado.resumen.total_guardias == 0
        assert resultado.resumen.total_profesores == 0
        assert resultado.resumen.total_zonas == 0

    def test_execute_retorna_dto_completo(self, use_case, datos_completos):
        """Test que execute retorna DTO con todas las secciones."""
        resultado = use_case.execute()

        assert isinstance(resultado, EstadisticasPanelCompletoDTO)
        assert isinstance(resultado.resumen, ResumenPanelDTO)
        assert isinstance(resultado.por_profesor, list)
        assert isinstance(resultado.por_zona, list)
        assert isinstance(resultado.grafico_profesores, DatosGraficoDTO)
        assert isinstance(resultado.grafico_zonas, DatosGraficoDTO)


# ============================================================================
# TESTS RESUMEN
# ============================================================================


class TestObtenerEstadisticasPanelResumen:
    """Tests del cálculo de resumen."""

    def test_resumen_totales(self, use_case, datos_completos):
        """Test que calcula totales correctamente."""
        resultado = use_case.execute()
        resumen = resultado.resumen

        # Total guardias: 10 + 6 + 4 = 20
        assert resumen.total_guardias == 20

        # Total profesores: 5
        assert resumen.total_profesores == 5

        # Total zonas: 3
        assert resumen.total_zonas == 3

        # Profesores con guardias: 3 (prof1, prof2, prof3)
        assert resumen.profesores_con_guardias == 3

    def test_resumen_guardias_por_turno(self, use_case, datos_completos):
        """Test que calcula guardias por turno correctamente."""
        resultado = use_case.execute()
        resumen = resultado.resumen

        # Mañana: 5 (prof1) + 6 (prof2) = 11
        assert resumen.guardias_manana == 11

        # Tarde: 5 (prof1) + 4 (prof3) = 9
        assert resumen.guardias_tarde == 9

    def test_resumen_promedio(self, use_case, datos_completos):
        """Test que calcula promedio por profesor."""
        resultado = use_case.execute()
        resumen = resultado.resumen

        # 20 guardias / 3 profesores = 6.67
        assert 6.6 < resumen.promedio_por_profesor < 6.7

    def test_resumen_sin_guardias(self, use_case):
        """Test resumen cuando no hay guardias."""
        resultado = use_case.execute()
        resumen = resultado.resumen

        assert resumen.promedio_por_profesor == 0.0
        assert resumen.cobertura_estimada == 0


# ============================================================================
# TESTS POR PROFESOR
# ============================================================================


class TestObtenerEstadisticasPanelProfesor:
    """Tests del cálculo por profesor."""

    def test_lista_todos_profesores(self, use_case, datos_completos):
        """Test que incluye todos los profesores."""
        resultado = use_case.execute()

        assert len(resultado.por_profesor) == 5

    def test_datos_profesor_correcto(self, use_case, datos_completos):
        """Test que calcula datos de profesor correctamente."""
        resultado = use_case.execute()

        # Buscar Profesor 1
        prof1 = next(p for p in resultado.por_profesor if "Profesor 1" in p.nombre_completo)

        assert prof1.total == 10
        assert prof1.manana == 5
        assert prof1.tarde == 5
        assert "✅" in prof1.estado

    def test_estado_sin_guardias(self, use_case, datos_completos):
        """Test estado para profesor sin guardias."""
        resultado = use_case.execute()

        # Buscar Profesor 4 (sin guardias)
        prof4 = next(p for p in resultado.por_profesor if "Profesor 4" in p.nombre_completo)

        assert prof4.total == 0
        assert "❌" in prof4.estado

    def test_estado_pocas_guardias(self, use_case, session, profesor_factory, zona_factory):
        """Test estado para profesor con pocas guardias."""
        prof = profesor_factory(nombre_completo="Test Pocas", horas_contrato=25.0)
        zona = zona_factory(nombre_zona="Test")
        session.add_all([prof, zona])
        session.commit()

        # Solo 2 guardias
        for i in range(2):
            g = Guardia(
                fecha=date.today() + timedelta(days=i),
                turno="mañana",
                recreo=1,
                profesor_id=prof.id,
                zona_id=zona.id,
            )
            session.add(g)
        session.commit()

        resultado = use_case.execute()

        prof_dto = next(p for p in resultado.por_profesor if "Test Pocas" in p.nombre_completo)
        assert "⚠️" in prof_dto.estado

    def test_porcentaje_calculado(self, use_case, datos_completos):
        """Test que calcula porcentaje correctamente."""
        resultado = use_case.execute()

        # Profesor 1: 10 de 20 = 50%
        prof1 = next(p for p in resultado.por_profesor if "Profesor 1" in p.nombre_completo)
        assert 49.9 < prof1.porcentaje < 50.1


# ============================================================================
# TESTS POR ZONA
# ============================================================================


class TestObtenerEstadisticasPanelZona:
    """Tests del cálculo por zona."""

    def test_lista_todas_zonas(self, use_case, datos_completos):
        """Test que incluye todas las zonas."""
        resultado = use_case.execute()

        assert len(resultado.por_zona) == 3

    def test_datos_zona_correctos(self, use_case, datos_completos):
        """Test que calcula datos por zona correctamente."""
        resultado = use_case.execute()

        # Suma de guardias por zona debe ser 20
        total = sum(z.total_guardias for z in resultado.por_zona)
        assert total == 20

    def test_profesores_diferentes_por_zona(self, use_case, datos_completos):
        """Test que cuenta profesores diferentes por zona."""
        resultado = use_case.execute()

        # Cada zona tiene guardias de 3 profesores diferentes
        for zona in resultado.por_zona:
            assert zona.profesores_diferentes == 3


# ============================================================================
# TESTS GRÁFICOS
# ============================================================================


class TestObtenerEstadisticasPanelGraficos:
    """Tests de datos para gráficos."""

    def test_grafico_profesores_solo_con_guardias(self, use_case, datos_completos):
        """Test que solo incluye profesores con guardias."""
        resultado = use_case.execute()

        # Solo 3 profesores tienen guardias
        assert len(resultado.grafico_profesores.nombres) == 3
        assert len(resultado.grafico_profesores.cantidades) == 3

    def test_grafico_profesores_cantidades_correctas(self, use_case, datos_completos):
        """Test que cantidades son correctas."""
        resultado = use_case.execute()

        # Las cantidades deben sumar 20
        assert sum(resultado.grafico_profesores.cantidades) == 20

    def test_grafico_zonas_solo_con_guardias(self, use_case, datos_completos):
        """Test que solo incluye zonas con guardias."""
        resultado = use_case.execute()

        # 3 zonas tienen guardias
        assert len(resultado.grafico_zonas.nombres) == 3
        assert len(resultado.grafico_zonas.cantidades) == 3

    def test_grafico_nombres_truncados(self, use_case, session, profesor_factory, zona_factory):
        """Test que nombres largos se truncan."""
        prof = profesor_factory(
            nombre_completo="Apellido Muy Largo Larguísimo, Nombre Completo",
            horas_contrato=25.0,
        )
        zona = zona_factory(nombre_zona="Test")
        session.add_all([prof, zona])
        session.commit()

        g = Guardia(
            fecha=date.today(),
            turno="mañana",
            recreo=1,
            profesor_id=prof.id,
            zona_id=zona.id,
        )
        session.add(g)
        session.commit()

        resultado = use_case.execute()

        for nombre in resultado.grafico_profesores.nombres:
            assert len(nombre) <= 15

    def test_grafico_zonas_cantidades_correctas(self, use_case, datos_completos):
        """Test que cantidades por zona son correctas."""
        resultado = use_case.execute()

        # Las cantidades deben sumar 20
        assert sum(resultado.grafico_zonas.cantidades) == 20


# ============================================================================
# TESTS INTEGRACIÓN
# ============================================================================


class TestObtenerEstadisticasPanelIntegracion:
    """Tests de integración."""

    def test_multiples_llamadas_consistentes(self, use_case, datos_completos):
        """Test que múltiples llamadas dan resultados consistentes."""
        resultado1 = use_case.execute()
        resultado2 = use_case.execute()

        assert resultado1.resumen.total_guardias == resultado2.resumen.total_guardias
        assert len(resultado1.por_profesor) == len(resultado2.por_profesor)
        assert len(resultado1.por_zona) == len(resultado2.por_zona)

    def test_refleja_cambios_en_bd(self, use_case, session, profesor_factory, zona_factory):
        """Test que refleja cambios cuando se agregan datos."""
        # Sin datos
        resultado1 = use_case.execute()
        assert resultado1.resumen.total_guardias == 0

        # Agregar datos
        prof = profesor_factory(nombre_completo="Nuevo", horas_contrato=25.0)
        zona = zona_factory(nombre_zona="Nueva")
        session.add_all([prof, zona])
        session.commit()

        g = Guardia(
            fecha=date.today(),
            turno="mañana",
            recreo=1,
            profesor_id=prof.id,
            zona_id=zona.id,
        )
        session.add(g)
        session.commit()

        # Con datos
        resultado2 = use_case.execute()
        assert resultado2.resumen.total_guardias == 1
