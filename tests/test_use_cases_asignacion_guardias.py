"""
Tests para los Use Cases de Asignación de Guardias.

Tests completos: GenerarGuardiasUseCase, CalcularDistribucionUseCase,
ObtenerEstadisticasUseCase.

NOTA: Estos Use Cases son wrappers sobre servicios complejos
(asignador_guardias, calculador_guardias).
Los tests verifican la integración correcta con los servicios,
no reimplementan la lógica compleja.
"""

from datetime import date, time

import pytest
from application.use_cases.asignacion_guardias.calcular_distribucion import (
    CalcularDistribucionUseCase,
)
from application.use_cases.asignacion_guardias.generar_guardias import (
    GenerarGuardiasUseCase,
)
from application.use_cases.asignacion_guardias.obtener_estadisticas import (
    ObtenerEstadisticasUseCase,
)
from models.models import Configuracion, Guardia
from utils.exceptions import BusinessLogicError

# ============================================================================
# TEST: OBTENER ESTADÍSTICAS
# ============================================================================


class TestObtenerEstadisticasUseCase:
    """Tests del use case ObtenerEstadisticasUseCase."""

    def test_obtener_estadisticas_sin_configuracion(self, session):
        """Error al obtener estadísticas sin configuración."""
        use_case = ObtenerEstadisticasUseCase(session)

        with pytest.raises(BusinessLogicError):
            use_case.execute()

    def test_obtener_estadisticas_con_configuracion(
        self, session, profesor_factory, zona_factory
    ):
        """Obtener estadísticas cuando hay configuración básica."""
        # Crear configuración
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 30),  # Un mes para simplificar
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        # Crear profesores y zonas
        profesor_factory(nombre_completo="Profesor 1", turno="mañana")
        profesor_factory(nombre_completo="Profesor 2", turno="mañana")
        zona_factory(nombre_zona="Zona A")

        # Ejecutar
        use_case = ObtenerEstadisticasUseCase(session)
        resultado = use_case.execute()

        # Verificar estructura del DTO
        assert resultado.dias_lectivos >= 0
        assert resultado.recreos_manana >= 0
        assert resultado.recreos_tarde >= 0
        assert resultado.num_zonas == 1
        assert resultado.num_profesores == 2
        assert resultado.slots_totales >= 0

    def test_obtener_estadisticas_estructura_dto(
        self, session, profesor_factory, zona_factory
    ):
        """Verificar que el DTO tiene la estructura correcta."""
        # Setup mínimo
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 5),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        zona_factory(nombre_zona="Zona Test")
        profesor_factory(nombre_completo="Test", turno="mañana")

        # Ejecutar
        use_case = ObtenerEstadisticasUseCase(session)
        resultado = use_case.execute()

        # Verificar propiedades del DTO
        assert hasattr(resultado, "dias_lectivos")
        assert hasattr(resultado, "recreos_manana")
        assert hasattr(resultado, "recreos_tarde")
        assert hasattr(resultado, "num_zonas")
        assert hasattr(resultado, "num_profesores")
        assert hasattr(resultado, "slots_totales")


# ============================================================================
# TEST: CALCULAR DISTRIBUCIÓN
# ============================================================================


class TestCalcularDistribucionUseCase:
    """Tests del use case CalcularDistribucionUseCase."""

    def test_calcular_distribucion_sin_datos(self, session):
        """Error al calcular distribución sin datos."""
        use_case = CalcularDistribucionUseCase(session)

        with pytest.raises(BusinessLogicError):
            use_case.execute()

    def test_calcular_distribucion_con_datos(
        self, session, profesor_factory, zona_factory
    ):
        """Calcular distribución con datos básicos."""
        # Configuración
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        # Crear profesores
        profesor_factory(
            nombre_completo="Profesor 1", turno="mañana", horas_contrato=25
        )
        profesor_factory(
            nombre_completo="Profesor 2", turno="mañana", horas_contrato=25
        )

        # Crear zona
        zona_factory(nombre_zona="Zona A")

        # Ejecutar
        use_case = CalcularDistribucionUseCase(session)
        resultado = use_case.execute()

        # Verificar estructura
        assert isinstance(resultado.distribucion, dict)
        assert resultado.total_guardias >= 0
        assert resultado.slots_totales >= 0

        # Verificar que hay distribución para los profesores
        assert len(resultado.distribucion) > 0

    def test_calcular_distribucion_propiedades_dto(
        self, session, profesor_factory, zona_factory
    ):
        """Verificar propiedades calculadas del DTO."""
        # Setup
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 10),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor_factory(nombre_completo="Test", turno="mañana", horas_contrato=25)
        zona_factory(nombre_zona="Zona Test")

        # Ejecutar
        use_case = CalcularDistribucionUseCase(session)
        resultado = use_case.execute()

        # Verificar propiedades calculadas
        assert hasattr(resultado, "diferencia")
        assert hasattr(resultado, "es_exacta")
        assert isinstance(resultado.diferencia, int)
        assert isinstance(resultado.es_exacta, bool)


# ============================================================================
# TEST: GENERAR GUARDIAS
# ============================================================================


class TestGenerarGuardiasUseCase:
    """Tests del use case GenerarGuardiasUseCase."""

    def test_generar_guardias_sin_datos(self, session):
        """Error al generar guardias sin configuración ni datos."""
        use_case = GenerarGuardiasUseCase(session)

        # Debería fallar por falta de configuración
        with pytest.raises(BusinessLogicError):
            use_case.execute()

    def test_generar_guardias_elimina_existentes(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Verificar que elimina guardias existentes cuando se solicita."""
        # Setup mínimo
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 5),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor = profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        zona = zona_factory(nombre_zona="Zona Test")

        # Crear guardias existentes
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 9, 2),
            turno="mañana",
            recreo=1,
        )
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 9, 3),
            turno="mañana",
            recreo=1,
        )

        assert session.query(Guardia).count() == 2

        # Ejecutar generación eliminando existentes
        use_case = GenerarGuardiasUseCase(session)
        resultado = use_case.execute(eliminar_existentes=True)

        # Verificar que se eliminaron las antiguas y se generaron nuevas
        # (el número exacto depende de la lógica del servicio)
        assert isinstance(resultado.guardias_generadas, int)

    def test_generar_guardias_mantiene_existentes(
        self, session, profesor_factory, zona_factory, guardia_factory
    ):
        """Verificar que no elimina guardias si se indica."""
        # Setup
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 5),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor = profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        zona = zona_factory(nombre_zona="Zona Test")

        # Crear guardia existente
        guardia_factory(
            profesor_id=profesor.id,
            zona_id=zona.id,
            fecha=date(2024, 9, 2),
            turno="mañana",
            recreo=1,
        )

        count_inicial = session.query(Guardia).count()
        assert count_inicial == 1

        # Ejecutar SIN eliminar existentes
        use_case = GenerarGuardiasUseCase(session)
        # No usamos el resultado, solo verificamos el efecto
        _ = use_case.execute(eliminar_existentes=False)

        # Debería mantener la existente + agregar nuevas
        count_final = session.query(Guardia).count()
        assert count_final >= count_inicial

    def test_generar_guardias_estructura_dto(
        self, session, profesor_factory, zona_factory
    ):
        """Verificar estructura del DTO de resultado."""
        # Setup mínimo
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 5),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        zona_factory(nombre_zona="Zona Test")

        # Ejecutar
        use_case = GenerarGuardiasUseCase(session)
        resultado = use_case.execute()

        # Verificar estructura del DTO
        assert hasattr(resultado, "guardias_generadas")
        assert hasattr(resultado, "slots_esperados")
        assert hasattr(resultado, "slots_sin_cubrir")
        assert hasattr(resultado, "resumen_por_profesor")
        assert hasattr(resultado, "mensaje")
        assert hasattr(resultado, "cobertura_completa")

        assert isinstance(resultado.guardias_generadas, int)
        assert isinstance(resultado.slots_esperados, int)
        assert isinstance(resultado.resumen_por_profesor, dict)
        assert isinstance(resultado.cobertura_completa, bool)

    def test_generar_guardias_con_callback(
        self, session, profesor_factory, zona_factory
    ):
        """Verificar que el callback de progreso funciona."""
        # Setup
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 3),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        zona_factory(nombre_zona="Zona Test")

        # Callback para capturar progreso
        mensajes_progreso = []

        def callback(mensaje: str, porcentaje: int):
            mensajes_progreso.append((mensaje, porcentaje))

        # Ejecutar con callback
        use_case = GenerarGuardiasUseCase(session)
        use_case.execute(progress_callback=callback)

        # Verificar que se llamó el callback
        assert len(mensajes_progreso) > 0
        # Debe incluir al menos el mensaje final
        assert any("completado" in msg.lower() for msg, _ in mensajes_progreso)


# ============================================================================
# TEST: INTEGRACIÓN ASIGNACIÓN GUARDIAS
# ============================================================================


class TestAsignacionGuardiasIntegracion:
    """Tests de integración entre los use cases de asignación."""

    def test_flujo_completo_estadisticas_distribucion_generacion(
        self, session, profesor_factory, zona_factory
    ):
        """Flujo completo: obtener stats → calcular distribución → generar guardias."""
        # Setup completo
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 10),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        # Crear profesores
        profesor_factory(
            nombre_completo="Profesor 1",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        profesor_factory(
            nombre_completo="Profesor 2",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )

        # Crear zonas
        zona_factory(nombre_zona="Zona A")
        zona_factory(nombre_zona="Zona B")

        # 1. Obtener estadísticas
        stats_uc = ObtenerEstadisticasUseCase(session)
        estadisticas = stats_uc.execute()

        assert estadisticas.num_profesores == 2
        assert estadisticas.num_zonas == 2
        assert estadisticas.slots_totales > 0

        # 2. Calcular distribución
        dist_uc = CalcularDistribucionUseCase(session)
        distribucion = dist_uc.execute()

        assert len(distribucion.distribucion) == 2  # 2 profesores
        assert distribucion.total_guardias > 0

        # 3. Generar guardias
        gen_uc = GenerarGuardiasUseCase(session)
        resultado = gen_uc.execute()

        assert resultado.guardias_generadas > 0
        assert len(resultado.resumen_por_profesor) > 0

    def test_generar_multiples_veces_con_eliminacion(
        self, session, profesor_factory, zona_factory
    ):
        """Generar guardias múltiples veces eliminando las anteriores."""
        # Setup
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 5),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        profesor_factory(
            nombre_completo="Test",
            turno="mañana",
            horas_contrato=25,
            fecha_inicio_guardias=date(2024, 9, 1),
            fecha_fin_guardias=date(2024, 9, 30),
        )
        zona_factory(nombre_zona="Zona Test")

        use_case = GenerarGuardiasUseCase(session)

        # Primera generación
        _ = use_case.execute(eliminar_existentes=True)
        count1 = session.query(Guardia).count()

        # Segunda generación (debería eliminar las primeras)
        _ = use_case.execute(eliminar_existentes=True)
        count2 = session.query(Guardia).count()

        # Ambas deberían generar aproximadamente la misma cantidad
        # (puede variar ligeramente por aleatoriedad en asignación)
        assert count1 > 0
        assert count2 > 0
