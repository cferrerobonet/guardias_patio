"""
Tests para los Use Cases de Configuración.
Tests completos: ActualizarConfiguracionUseCase, ObtenerConfiguracionUseCase.
"""

from datetime import date, time

import pytest

from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
from application.use_cases.configuracion.actualizar_configuracion import (
    ActualizarConfiguracionUseCase,
)
from application.use_cases.configuracion.obtener_configuracion import (
    ObtenerConfiguracionUseCase,
)
from core.exceptions import NotFoundError
from models.models import Configuracion

# ============================================================================
# TEST: ACTUALIZAR CONFIGURACIÓN
# ============================================================================


class TestActualizarConfiguracionUseCase:
    """Tests del use case ActualizarConfiguracionUseCase."""

    def test_crear_configuracion_nueva(self, session):
        """Crear configuración cuando no existe ninguna."""
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            hora_recreo1_tarde=time(15, 30),
            hora_recreo2_tarde=time(17, 30),
            ajuste_tutores=1.2,
            ajuste_no_tutores=1.0,
            activar_festivos_automaticos=True,
        )

        resultado = use_case.execute(dto)

        assert resultado.id is not None
        assert resultado.fecha_inicio_curso == date(2024, 9, 1)
        assert resultado.fecha_fin_curso == date(2025, 6, 30)
        assert resultado.hora_recreo1_manana == time(10, 30)
        assert resultado.ajuste_tutores == 1.2
        assert resultado.ajuste_no_tutores == 1.0
        assert resultado.activar_festivos_automaticos is True

        # Verificar en BD
        config_bd = session.query(Configuracion).first()
        assert config_bd is not None
        assert config_bd.fecha_inicio_curso == date(2024, 9, 1)

    def test_actualizar_configuracion_existente(self, session):
        """Actualizar configuración cuando ya existe una."""
        # Crear configuración inicial
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config_inicial)
        session.commit()
        id_original = config_inicial.id

        # Actualizar
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 15),
            ajuste_tutores=1.5,
        )

        resultado = use_case.execute(dto)

        # Debe mantener el mismo ID
        assert resultado.id == id_original
        # Valores actualizados
        assert resultado.fecha_inicio_curso == date(2024, 9, 15)
        assert resultado.ajuste_tutores == 1.5
        # Valores no modificados (mantienen el original)
        assert resultado.fecha_fin_curso == date(2025, 6, 30)
        assert resultado.ajuste_no_tutores == 1.0

        # Verificar que solo hay una configuración
        assert session.query(Configuracion).count() == 1

    def test_actualizar_configuracion_parcial(self, session):
        """Actualizar solo algunos campos de la configuración."""
        # Crear configuración inicial
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config_inicial)
        session.commit()

        # Actualizar solo ajuste_tutores
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(ajuste_tutores=1.3)

        resultado = use_case.execute(dto)

        assert resultado.ajuste_tutores == 1.3
        assert resultado.fecha_inicio_curso == date(2024, 9, 1)  # No cambia
        assert resultado.ajuste_no_tutores == 1.0  # No cambia

    def test_crear_configuracion_con_valores_por_defecto(self, session):
        """Crear configuración con valores mínimos, usando defaults."""
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            # No especificamos ajuste_tutores, ajuste_no_tutores, activar_festivos
        )

        resultado = use_case.execute(dto)

        # Verificar valores por defecto
        assert resultado.ajuste_tutores == 1.0
        assert resultado.ajuste_no_tutores == 1.0
        assert resultado.activar_festivos_automaticos is True
        assert resultado.dias_no_lectivos_personalizados == ""
        assert resultado.recreos_config == ""

    def test_actualizar_configuracion_campos_opcionales(self, session):
        """Actualizar campos opcionales como horas de tarde."""
        # Crear configuración inicial sin horas de tarde
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config_inicial)
        session.commit()

        # Agregar horas de tarde
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            hora_recreo1_tarde=time(15, 30), hora_recreo2_tarde=time(17, 30)
        )

        resultado = use_case.execute(dto)

        assert resultado.hora_recreo1_tarde == time(15, 30)
        assert resultado.hora_recreo2_tarde == time(17, 30)

    def test_actualizar_configuracion_festivos_automaticos(self, session):
        """Actualizar solo campo activar_festivos_automaticos."""
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
            activar_festivos_automaticos=True,
        )
        session.add(config_inicial)
        session.commit()

        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(activar_festivos_automaticos=False)

        resultado = use_case.execute(dto)

        assert resultado.activar_festivos_automaticos is False

    def test_actualizar_configuracion_dias_no_lectivos(self, session):
        """Actualizar campo dias_no_lectivos_personalizados."""
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config_inicial)
        session.commit()

        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            dias_no_lectivos_personalizados='["2024-12-25", "2025-01-01"]'
        )

        resultado = use_case.execute(dto)

        assert '2024-12-25' in resultado.dias_no_lectivos_personalizados

    def test_actualizar_configuracion_recreos_config(self, session):
        """Actualizar campo recreos_config."""
        config_inicial = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config_inicial)
        session.commit()

        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            recreos_config='[{"id": 1, "turno": "mañana", "zonas": 2}]'
        )

        resultado = use_case.execute(dto)

        assert 'zonas' in resultado.recreos_config

    def test_actualizar_configuracion_error_bd(self, session, mocker):
        """Manejar error de base de datos al actualizar configuración."""
        use_case = ActualizarConfiguracionUseCase(session)
        dto = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
        )

        # Mock session.commit() para simular error
        mocker.patch.object(session, "commit", side_effect=Exception("Error BD"))

        with pytest.raises(Exception, match="Error BD"):
            use_case.execute(dto)

        # Verificar rollback (no debe haber configuración creada)
        assert session.query(Configuracion).count() == 0


# ============================================================================
# TEST: OBTENER CONFIGURACIÓN
# ============================================================================


class TestObtenerConfiguracionUseCase:
    """Tests del use case ObtenerConfiguracionUseCase."""

    def test_obtener_configuracion_exitoso(self, session):
        """Obtener configuración cuando existe."""
        # Crear configuración
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            hora_recreo1_tarde=time(15, 30),
            hora_recreo2_tarde=time(17, 30),
            ajuste_tutores=1.2,
            ajuste_no_tutores=1.0,
            activar_festivos_automaticos=True,
            dias_no_lectivos_personalizados='["2024-12-25", "2025-01-01"]',
            recreos_config='[{"id": 1, "turno": "mañana"}]',
        )
        session.add(config)
        session.commit()

        # Obtener
        use_case = ObtenerConfiguracionUseCase(session)
        resultado = use_case.execute()

        assert resultado.id == config.id
        assert resultado.fecha_inicio_curso == date(2024, 9, 1)
        assert resultado.fecha_fin_curso == date(2025, 6, 30)
        assert resultado.hora_recreo1_manana == time(10, 30)
        assert resultado.ajuste_tutores == 1.2
        assert resultado.activar_festivos_automaticos is True
        assert '2024-12-25' in resultado.dias_no_lectivos_personalizados

    def test_obtener_configuracion_no_existe(self, session):
        """Error al obtener configuración cuando no existe."""
        use_case = ObtenerConfiguracionUseCase(session)

        with pytest.raises(NotFoundError, match="No existe configuración"):
            use_case.execute()


# ============================================================================
# TEST: INTEGRACIÓN CONFIGURACIÓN
# ============================================================================


class TestConfiguracionUseCasesIntegracion:
    """Tests de integración entre los use cases de Configuración."""

    def test_flujo_completo_crear_y_obtener(self, session):
        """Flujo completo: crear configuración y luego obtenerla."""
        # 1. Crear configuración
        actualizar_uc = ActualizarConfiguracionUseCase(session)
        dto_crear = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.2,
            ajuste_no_tutores=1.0,
        )

        config_creada = actualizar_uc.execute(dto_crear)
        assert config_creada.id is not None

        # 2. Obtener configuración creada
        obtener_uc = ObtenerConfiguracionUseCase(session)
        config_obtenida = obtener_uc.execute()

        assert config_obtenida.id == config_creada.id
        assert config_obtenida.fecha_inicio_curso == date(2024, 9, 1)
        assert config_obtenida.ajuste_tutores == 1.2

    def test_flujo_actualizar_y_verificar(self, session):
        """Crear configuración, actualizarla, y verificar cambios."""
        actualizar_uc = ActualizarConfiguracionUseCase(session)

        # 1. Crear
        dto_crear = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            ajuste_tutores=1.0,
        )
        config_inicial = actualizar_uc.execute(dto_crear)
        id_inicial = config_inicial.id

        # 2. Actualizar
        dto_actualizar = ActualizarConfiguracionDTO(
            ajuste_tutores=1.5, activar_festivos_automaticos=False
        )
        config_actualizada = actualizar_uc.execute(dto_actualizar)

        # 3. Verificar que es la misma configuración (mismo ID)
        assert config_actualizada.id == id_inicial

        # 4. Verificar cambios
        assert config_actualizada.ajuste_tutores == 1.5
        assert config_actualizada.activar_festivos_automaticos is False

        # 5. Verificar que los valores no actualizados se mantienen
        assert config_actualizada.fecha_inicio_curso == date(2024, 9, 1)

        # 6. Obtener y verificar
        obtener_uc = ObtenerConfiguracionUseCase(session)
        config_final = obtener_uc.execute()

        assert config_final.id == id_inicial
        assert config_final.ajuste_tutores == 1.5
        assert config_final.activar_festivos_automaticos is False

    def test_solo_una_configuracion_en_sistema(self, session):
        """Verificar que solo puede existir una configuración en el sistema."""
        actualizar_uc = ActualizarConfiguracionUseCase(session)

        # Crear primera configuración
        dto1 = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2025, 6, 30),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
        )
        config1 = actualizar_uc.execute(dto1)
        id1 = config1.id

        # "Crear" segunda configuración (en realidad debe actualizar la primera)
        dto2 = ActualizarConfiguracionDTO(
            fecha_inicio_curso=date(2024, 9, 15), ajuste_tutores=1.5
        )
        config2 = actualizar_uc.execute(dto2)

        # Debe ser la misma configuración (mismo ID)
        assert config2.id == id1

        # Solo debe haber una configuración en la BD
        assert session.query(Configuracion).count() == 1
