"""Tests para el módulo asignador_guardias."""

import sys
from collections import defaultdict
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Base, Configuracion, Guardia, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias, guardar_guardias_en_bd


@pytest.fixture
def session():
    """Crea una sesión de base de datos en memoria para tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def config_completa(session):
    """Crea una configuración completa del curso."""
    config = Configuracion(
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2025, 9, 5),  # 5 días lectivos (L-V)
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(15, 30),
        hora_recreo2_tarde=None,  # Solo 1 recreo de tarde
        activar_festivos_automaticos=False,
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def profesores_multiples(session):
    """Crea varios profesores de prueba."""
    profesores = [
        Profesor(
            nombre_completo="GARCÍA, ANA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        ),
        Profesor(
            nombre_completo="MARTÍNEZ, LUIS",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        ),
        Profesor(
            nombre_completo="LÓPEZ, CARMEN",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="tarde",
            tutor=False,
        ),
        Profesor(
            nombre_completo="SÁNCHEZ, PEDRO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mixto",
            tutor=False,
        ),
    ]
    for p in profesores:
        session.add(p)
    session.commit()
    return profesores


@pytest.fixture
def zonas_multiples(session):
    """Crea múltiples zonas de prueba."""
    zonas = [
        Zona(nombre_zona="Patio Principal", descripcion="Patio grande"),
        Zona(nombre_zona="Patio Infantil", descripcion="Zona pequeños"),
        Zona(nombre_zona="Patio Secundaria", descripcion="Zona mayores"),
    ]
    for z in zonas:
        session.add(z)
    session.commit()
    return zonas


class TestGeneracionCalendario:
    def test_generacion_basica(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Genera un calendario básico de guardias."""
        calendario, resumen = generar_calendario_guardias(session)

        assert len(calendario) > 0
        assert len(resumen) > 0
        # Verificar que todos los profesores tienen alguna guardia
        assert all(count > 0 for count in resumen.values())

    def test_no_duplicados_profesor_mismo_slot(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """VALIDACIÓN CRÍTICA: Un profesor NO puede estar en dos zonas al mismo tiempo.

        Esta es una regla fundamental: un mismo profesor no puede estar asignado
        a múltiples zonas en el mismo día, mismo turno y mismo recreo.
        """
        calendario, _ = generar_calendario_guardias(session)

        # Agrupar por (profesor_id, fecha, turno, recreo)
        slots_por_profesor = defaultdict(list)
        for guardia in calendario:
            key = (guardia.profesor_id, guardia.fecha, guardia.turno, guardia.recreo)
            slots_por_profesor[key].append(guardia)

        # Verificar que ningún profesor tiene más de una guardia en el mismo slot
        for key, guardias_en_slot in slots_por_profesor.items():
            profesor_id, fecha, turno, recreo = key
            assert len(guardias_en_slot) == 1, (
                f"Profesor {profesor_id} tiene {len(guardias_en_slot)} guardias "
                f"en el mismo slot: fecha={fecha}, turno={turno}, recreo={recreo}. "
                f"Zonas asignadas: {[g.zona_id for g in guardias_en_slot]}"
            )

    def test_respeta_cuotas(self, session, config_completa, profesores_multiples, zonas_multiples):
        """Verifica que ningún profesor supera su cuota asignada."""
        from services.calculador_guardias import calcular_guardias_por_profesor

        cuotas = calcular_guardias_por_profesor(session)
        calendario, resumen = generar_calendario_guardias(session)

        for profesor_id, guardias_asignadas in resumen.items():
            assert guardias_asignadas <= cuotas[profesor_id], (
                f"Profesor {profesor_id} tiene {guardias_asignadas} guardias "
                f"pero su cuota es {cuotas[profesor_id]}"
            )

    def test_turno_compatible(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Verifica que los profesores solo reciben guardias de su turno."""
        calendario, _ = generar_calendario_guardias(session)

        # Obtener profesores por ID
        profesores_dict = {p.id: p for p in profesores_multiples}

        for guardia in calendario:
            profesor = profesores_dict[guardia.profesor_id]
            if profesor.turno == "mañana":
                assert guardia.turno == "mañana", (
                    f"Profesor de mañana {profesor.nombre_completo} "
                    f"tiene guardia de {guardia.turno}"
                )
            elif profesor.turno == "tarde":
                assert guardia.turno == "tarde", (
                    f"Profesor de tarde {profesor.nombre_completo} "
                    f"tiene guardia de {guardia.turno}"
                )
            # Turno mixto puede tener ambos (no se valida)

    def test_respeta_fecha_inicio(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Verifica que se respeta la fecha de inicio de guardias."""
        # Configurar fecha de inicio para un profesor
        profesor = profesores_multiples[0]
        profesor.fecha_inicio_guardias = date(2025, 9, 3)  # Empieza el miércoles
        session.commit()

        calendario, _ = generar_calendario_guardias(session)

        # Verificar que este profesor no tiene guardias antes del 3 de septiembre
        for guardia in calendario:
            if guardia.profesor_id == profesor.id:
                assert guardia.fecha >= date(2025, 9, 3), (
                    f"Profesor tiene guardia el {guardia.fecha}, antes de su fecha de inicio"
                )

    @pytest.mark.xfail(reason="Asignador no respeta restricciones de días - requiere fix")
    def test_respeta_dias_permitidos(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Verifica que respeta restricciones de días de la semana."""
        profesor = profesores_multiples[0]
        profesor.dias_semana_permitidos = "0, 1, 2"  # Solo L, M, X
        session.commit()

        calendario, _ = generar_calendario_guardias(session)

        # Verificar que este profesor solo tiene guardias L, M, X
        for guardia in calendario:
            if guardia.profesor_id == profesor.id:
                dia_semana = guardia.fecha.weekday()
                assert dia_semana in [0, 1, 2], (
                    f"Profesor tiene guardia el día {dia_semana} (fecha={guardia.fecha}), "
                    f"pero solo puede trabajar L(0), M(1), X(2)"
                )

    def test_guardias_se_guardan_en_bd(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Verifica que las guardias se guardan correctamente en la base de datos."""
        calendario, _ = generar_calendario_guardias(session)

        # Guardar en BD
        guardar_guardias_en_bd(session, calendario)

        # Verificar que se guardaron
        guardias_bd = session.query(Guardia).all()
        assert len(guardias_bd) == len(calendario)

        # Verificar que tienen todos los campos
        for guardia in guardias_bd:
            assert guardia.profesor_id is not None
            assert guardia.fecha is not None
            assert guardia.turno is not None
            assert guardia.recreo is not None
            assert guardia.zona_id is not None

    def test_error_sin_configuracion(self, session):
        """Lanza error si no hay configuración."""
        with pytest.raises(ValueError, match="No existe configuración"):
            generar_calendario_guardias(session)

    def test_error_sin_profesores(self, session, config_completa):
        """Lanza error si no hay profesores."""
        with pytest.raises(ValueError, match="No hay profesores"):
            generar_calendario_guardias(session)

    def test_error_sin_zonas(self, session, config_completa, profesores_multiples):
        """Lanza error si no hay zonas."""
        with pytest.raises(ValueError, match="No hay zonas"):
            generar_calendario_guardias(session)


class TestCasosEspeciales:
    @pytest.mark.xfail(reason="Asignador no respeta restricciones combinadas - requiere fix")
    def test_profesor_con_restricciones_multiples(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Profesor con fecha de inicio y días permitidos restringidos."""
        profesor = profesores_multiples[0]
        profesor.fecha_inicio_guardias = date(2025, 9, 2)  # Martes
        profesor.dias_semana_permitidos = "1, 3"  # Solo martes (1) y jueves (3)
        session.commit()

        calendario, resumen = generar_calendario_guardias(session)

        # Verificar que tiene guardias
        assert profesor.id in resumen
        assert resumen[profesor.id] > 0

        # Verificar que todas sus guardias cumplen ambas restricciones
        for guardia in calendario:
            if guardia.profesor_id == profesor.id:
                assert guardia.fecha >= date(2025, 9, 2)
                assert guardia.fecha.weekday() in [1, 3]

    def test_multiples_zonas_mismo_dia(
        self, session, config_completa, profesores_multiples, zonas_multiples
    ):
        """Verifica que si hay muchas zonas, diferentes profesores las cubren."""
        calendario, _ = generar_calendario_guardias(session)

        # Agrupar por (fecha, turno, recreo)
        slots = defaultdict(list)
        for guardia in calendario:
            key = (guardia.fecha, guardia.turno, guardia.recreo)
            slots[key].append(guardia)

        # Verificar que en cada slot hay guardias en diferentes zonas
        for key, guardias_slot in slots.items():
            zonas_en_slot = [g.zona_id for g in guardias_slot]
            # No debe haber zonas duplicadas en el mismo slot
            assert len(zonas_en_slot) == len(set(zonas_en_slot)), (
                f"Slot {key} tiene zonas duplicadas: {zonas_en_slot}"
            )
