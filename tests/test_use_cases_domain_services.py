"""
Tests para Use Cases que integran Domain Services (Phase 3)

Tests de integración para validar que los Use Cases orquestan
correctamente los Domain Services.
"""

from datetime import date

from application.dtos.domain_services_dtos import (
    AnalisisEquidadRequest,
    CalcularCuotasRequest,
)
from application.use_cases.analisis_equidad_use_case import AnalisisEquidadUseCase
from application.use_cases.calcular_cuotas_use_case import CalcularCuotasUseCase
from models.models import Guardia, Profesor


def test_calcular_cuotas_use_case_exitoso(session, configuracion_base, profesores_variados, zona_patio):
    """Test del use case de cálculo de cuotas."""
    # Arrange
    use_case = CalcularCuotasUseCase(session)
    request = CalcularCuotasRequest(
        configuracion_id=configuracion_base.id,
        solo_activos=True
    )

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.exitoso is True
    assert len(response.cuotas) > 0
    assert response.total_guardias > 0
    assert len(response.cuotas_detalle) == len(profesores_variados)

    # Verificar que los DTOs tienen la información correcta
    for cuota_dto in response.cuotas_detalle:
        assert cuota_dto.profesor_id in response.cuotas
        assert cuota_dto.cuota_esperada == response.cuotas[cuota_dto.profesor_id]
        assert cuota_dto.profesor_nombre != ""


def test_calcular_cuotas_sin_profesores(session, configuracion_base):
    """Test cuando no hay profesores activos."""
    # Arrange: Desactivar todos los profesores
    session.query(Profesor).update({Profesor.activo: False})
    session.commit()

    use_case = CalcularCuotasUseCase(session)
    request = CalcularCuotasRequest(
        configuracion_id=configuracion_base.id,
        solo_activos=True
    )

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.exitoso is False
    assert "No hay profesores" in response.mensaje
    assert len(response.cuotas) == 0


def test_analisis_equidad_sin_guardias(session, configuracion_base, profesores_variados):
    """Test análisis de equidad sin guardias asignadas."""
    # Arrange
    use_case = AnalisisEquidadUseCase(session)
    request = AnalisisEquidadRequest(
        configuracion_id=configuracion_base.id,
        incluir_detalle=True
    )

    # Act
    response = use_case.execute(request)

    # Assert
    assert response.exitoso is False
    assert "No hay guardias" in response.mensaje
    assert response.metricas.indice_equidad == 0.0


def test_analisis_equidad_con_guardias(
    session,
    configuracion_base,
    profesores_variados,
    zona_patio
):
    """Test análisis de equidad con guardias asignadas."""
    # Arrange: Crear algunas guardias
    prof1 = profesores_variados[0]
    prof2 = profesores_variados[1]

    # Asignar 5 guardias a prof1 y 5 a prof2
    for i in range(5):
        guardia1 = Guardia(
            fecha=date(2024, 9, 2 + i),
            recreo=1,
            turno="mañana",
            zona_id=zona_patio.id,
            profesor_id=prof1.id,
            curso_id=None
        )
        guardia2 = Guardia(
            fecha=date(2024, 9, 2 + i),
            recreo=2,
            turno="mañana",
            zona_id=zona_patio.id,
            profesor_id=prof2.id,
            curso_id=None
        )
        session.add(guardia1)
        session.add(guardia2)
    session.commit()

    # Act
    use_case = AnalisisEquidadUseCase(session)
    request = AnalisisEquidadRequest(
        configuracion_id=None,  # Analizar todas las guardias
        incluir_detalle=True,
        umbral_desbalance=0.15
    )
    response = use_case.execute(request)

    # Assert
    assert response.exitoso is True
    assert response.metricas.indice_equidad > 0
    assert len(response.cuotas) > 0
    assert len(response.recomendaciones) > 0

    # Verificar que las métricas tienen sentido
    assert 0.0 <= response.metricas.indice_equidad <= 1.0
    assert response.metricas.nivel_equidad in ["EXCELENTE", "BUENO", "ACEPTABLE", "DEFICIENTE"]

    # Verificar cuotas DTOs
    cuotas_prof1 = [c for c in response.cuotas if c.profesor_id == prof1.id]
    assert len(cuotas_prof1) == 1
    assert cuotas_prof1[0].cuota_asignada == 5


def test_analisis_equidad_incluir_detalle(
    session,
    configuracion_base,
    profesores_variados,
    zona_patio
):
    """Test que el flag incluir_detalle funciona correctamente."""
    # Arrange: Crear guardia
    guardia = Guardia(
        fecha=date(2024, 9, 2),
        recreo=1,
        turno="mañana",
        zona_id=zona_patio.id,
        profesor_id=profesores_variados[0].id,
        curso_id=None
    )
    session.add(guardia)
    session.commit()

    use_case = AnalisisEquidadUseCase(session)

    # Act: Con detalle
    request_con_detalle = AnalisisEquidadRequest(incluir_detalle=True)
    response_con_detalle = use_case.execute(request_con_detalle)

    # Act: Sin detalle
    request_sin_detalle = AnalisisEquidadRequest(incluir_detalle=False)
    response_sin_detalle = use_case.execute(request_sin_detalle)

    # Assert
    assert len(response_con_detalle.cuotas) > 0
    assert len(response_sin_detalle.cuotas) == 0


def test_cuota_dto_propiedades(profesores_variados):
    """Test de las propiedades calculadas del CuotaProfesorDTO."""
    from application.dtos.domain_services_dtos import CuotaProfesorDTO

    # Caso 1: Deficit
    cuota_deficit = CuotaProfesorDTO(
        profesor_id=1,
        profesor_nombre="Test",
        cuota_esperada=10,
        cuota_asignada=7
    )
    assert cuota_deficit.deficit == 3
    assert cuota_deficit.porcentaje_cumplimiento == 70.0

    # Caso 2: Exceso
    cuota_exceso = CuotaProfesorDTO(
        profesor_id=2,
        profesor_nombre="Test2",
        cuota_esperada=10,
        cuota_asignada=12
    )
    assert cuota_exceso.deficit == -2
    assert cuota_exceso.porcentaje_cumplimiento == 120.0

    # Caso 3: Perfecto
    cuota_perfecta = CuotaProfesorDTO(
        profesor_id=3,
        profesor_nombre="Test3",
        cuota_esperada=10,
        cuota_asignada=10
    )
    assert cuota_perfecta.deficit == 0
    assert cuota_perfecta.porcentaje_cumplimiento == 100.0


def test_equidad_metricas_dto_nivel(profesores_variados):
    """Test de clasificación de nivel de equidad."""
    from application.dtos.domain_services_dtos import EquidadMetricasDTO

    # Excelente
    metricas_exc = EquidadMetricasDTO(
        indice_equidad=0.96,
        coeficiente_variacion=0.05,
        desviacion_estandar=0.02,
        desbalances_detectados=0,
        profesores_con_deficit=0,
        profesores_con_exceso=0
    )
    assert metricas_exc.nivel_equidad == "EXCELENTE"

    # Bueno
    metricas_bueno = EquidadMetricasDTO(
        indice_equidad=0.88,
        coeficiente_variacion=0.12,
        desviacion_estandar=0.08,
        desbalances_detectados=2,
        profesores_con_deficit=1,
        profesores_con_exceso=1
    )
    assert metricas_bueno.nivel_equidad == "BUENO"

    # Aceptable
    metricas_acept = EquidadMetricasDTO(
        indice_equidad=0.75,
        coeficiente_variacion=0.20,
        desviacion_estandar=0.15,
        desbalances_detectados=5,
        profesores_con_deficit=3,
        profesores_con_exceso=2
    )
    assert metricas_acept.nivel_equidad == "ACEPTABLE"

    # Deficiente
    metricas_def = EquidadMetricasDTO(
        indice_equidad=0.50,
        coeficiente_variacion=0.40,
        desviacion_estandar=0.30,
        desbalances_detectados=10,
        profesores_con_deficit=5,
        profesores_con_exceso=5
    )
    assert metricas_def.nivel_equidad == "DEFICIENTE"
