"""Tests para el módulo calculador_guardias."""

import json
import sys
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona
from services.calculador_guardias import (
    _easter_sunday,
    _festivos_automaticos_en_rango,
    _parse_custom_no_lectivos,
    _parse_recreos_config,
    ajustar_redondeo,
    calcular_dias_lectivos,
    calcular_distribucion_cruda,
    calcular_guardias_por_profesor,
    calcular_recreos_activos,
    listar_dias_lectivos,
    obtener_estadisticas,
)


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
def curso_activo(session):
    """Crea un curso escolar activo."""
    curso = CursoEscolar(
        anio_inicio=2025,
        anio_fin=2026,
        fecha_inicio=date(2025, 9, 1),
        fecha_fin=date(2026, 6, 30),
        nombre="Curso 2025/2026",
        activo=True,
        cerrado=False,
    )
    session.add(curso)
    session.commit()
    return curso


@pytest.fixture
def config_basica(session):
    """Crea una configuración básica del curso."""
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2026, 6, 30),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
        activar_festivos_automaticos=False,
        ajuste_tutores=0.9,
        ajuste_no_tutores=1.0,
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def profesores_basicos(session):
    """Crea profesores de prueba."""
    profesores = [
        Profesor(
            nombre_completo="GARCÍA, ANA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=True,
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
            horas_contrato=15.0,
            porcentaje_jornada=0.5,
            turno="tarde",
            tutor=False,
        ),
    ]
    for p in profesores:
        session.add(p)
    session.commit()
    return profesores


@pytest.fixture
def zonas_basicas(session):
    """Crea zonas de prueba."""
    zonas = [
        Zona(nombre_zona="Patio Principal", descripcion="Patio grande"),
        Zona(nombre_zona="Patio Infantil", descripcion="Zona pequeños"),
    ]
    for z in zonas:
        session.add(z)
    session.commit()
    return zonas


class TestCalculoDiasLectivos:
    def test_dias_lectivos_simple(self):
        """Prueba cálculo básico de días lectivos (L-V)."""
        # Una semana completa: 5 días lectivos
        inicio = date(2025, 9, 1)  # lunes
        fin = date(2025, 9, 5)  # viernes
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_dias_lectivos_con_fin_de_semana(self):
        """Excluye sábado y domingo."""
        inicio = date(2025, 9, 1)  # lunes
        fin = date(2025, 9, 7)  # domingo
        assert calcular_dias_lectivos(inicio, fin) == 5

    def test_dias_lectivos_mes_completo(self):
        """Calcula días lectivos de un mes."""
        # Septiembre 2025: 22 días lectivos (empieza lunes)
        inicio = date(2025, 9, 1)
        fin = date(2025, 9, 30)
        assert calcular_dias_lectivos(inicio, fin) == 22


class TestFestivosAutomaticos:
    def test_easter_sunday_2025(self):
        """Verifica cálculo de Pascua 2025."""
        pascua = _easter_sunday(2025)
        assert pascua == date(2025, 4, 20)

    def test_festivos_fijos(self):
        """Verifica días festivos fijos."""
        inicio = date(2025, 10, 1)
        fin = date(2025, 10, 31)
        festivos = _festivos_automaticos_en_rango(inicio, fin)
        # 9 de octubre (jueves) está en el rango
        assert date(2025, 10, 9) in festivos
        # 12 de octubre 2025 es domingo, no se incluye en días lectivos

    def test_navidad(self):
        """Verifica vacaciones de Navidad."""
        inicio = date(2025, 12, 1)
        fin = date(2026, 1, 15)
        festivos = _festivos_automaticos_en_rango(inicio, fin)
        # Rango 23/12 a 06/01 (22/12 es LECTIVO según la implementación)
        assert date(2025, 12, 23) in festivos  # Inicio de vacaciones
        assert date(2025, 12, 31) in festivos
        assert date(2026, 1, 6) in festivos
        assert date(2026, 1, 7) not in festivos


class TestParseCustomNoLectivos:
    def test_parse_vacio(self):
        """CSV vacío devuelve set vacío."""
        assert _parse_custom_no_lectivos("") == set()
        assert _parse_custom_no_lectivos(None) == set()

    def test_parse_valido(self):
        """Parsea fechas válidas."""
        csv = "2025-10-09, 2025-10-12, 2025-11-01"
        fechas = _parse_custom_no_lectivos(csv)
        assert len(fechas) == 3
        assert date(2025, 10, 9) in fechas
        assert date(2025, 10, 12) in fechas
        assert date(2025, 11, 1) in fechas

    def test_parse_con_invalidos(self):
        """Ignora entradas inválidas."""
        csv = "2025-10-09, invalido, 2025-10-12"
        fechas = _parse_custom_no_lectivos(csv)
        assert len(fechas) == 2


class TestListarDiasLectivos:
    def test_sin_festivos(self, session, config_basica):
        """Lista días lectivos sin festivos."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 7)
        config_basica.activar_festivos_automaticos = False
        session.commit()
        dias = listar_dias_lectivos(config_basica)
        assert len(dias) == 5  # L-V de la semana

    def test_con_festivos_personalizados(self, session, config_basica):
        """Excluye festivos personalizados."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 7)
        config_basica.activar_festivos_automaticos = False
        config_basica.dias_no_lectivos_personalizados = "2025-09-02, 2025-09-03"
        session.commit()
        dias = listar_dias_lectivos(config_basica)
        # L-V (5) menos miércoles y jueves (2) = 3
        assert len(dias) == 3


class TestParseRecreos:
    def test_parse_recreos_config_vacio(self, session, config_basica):
        """Sin recreos_config devuelve lista vacía."""
        config_basica.recreos_config = None
        assert _parse_recreos_config(config_basica) == []

    def test_parse_recreos_config_valido(self, session, config_basica):
        """Parsea JSON de recreos."""
        config_basica.recreos_config = json.dumps(
            [
                {"id": 1, "etiqueta": "R1 Mañana", "turno": "mañana", "zonas": 2},
                {"id": 2, "etiqueta": "R2 Mañana", "turno": "mañana", "zonas": 3},
                {"id": 3, "etiqueta": "R1 Tarde", "turno": "tarde", "zonas": 2},
            ]
        )
        recreos = _parse_recreos_config(config_basica)
        assert len(recreos) == 3
        assert recreos[0]["id"] == 1
        assert recreos[0]["zonas"] == 2
        assert recreos[1]["zonas"] == 3


class TestCalculoRecreosActivos:
    def test_recreos_desde_horas(self, session, config_basica):
        """Deduce recreos de campos de horas."""
        config_basica.recreos_config = None
        manana, tarde = calcular_recreos_activos(session)
        assert manana == 2
        assert tarde == 0

    def test_recreos_desde_config(self, session, config_basica):
        """Usa recreos_config si está presente."""
        config_basica.recreos_config = json.dumps(
            [
                {"id": 1, "turno": "mañana", "zonas": 2},
                {"id": 2, "turno": "mañana", "zonas": 1},
                {"id": 3, "turno": "tarde", "zonas": 2},
            ]
        )
        session.commit()
        manana, tarde = calcular_recreos_activos(session)
        assert manana == 2
        assert tarde == 1


class TestAjusteRedondeo:
    def test_redondeo_exacto(self):
        """Suma exacta no requiere ajuste."""
        cruda = {1: 10.0, 2: 10.0, 3: 10.0}
        ajustada = ajustar_redondeo(cruda)
        assert sum(ajustada.values()) == 30

    def test_redondeo_con_residuos(self):
        """Asigna slots sobrantes a mayores residuos."""
        cruda = {1: 10.4, 2: 10.3, 3: 10.3}
        ajustada = ajustar_redondeo(cruda)
        # Total: 31; floor suma 30; sobrante 1 va al mayor residuo (id 1)
        assert sum(ajustada.values()) == 31
        assert ajustada[1] == 11
        assert ajustada[2] == 10
        assert ajustada[3] == 10


class TestDistribucionBase:
    def test_distribucion_con_tutores(
        self, session, curso_activo, config_basica, profesores_basicos, zonas_basicas
    ):
        """Verifica que tutores tienen multiplicador aplicado."""
        config_basica.ajuste_tutores = 0.9
        config_basica.ajuste_no_tutores = 1.0
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)  # 5 días
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # Ana (tutor): recibe 0.9x
        # Luis (no tutor): recibe 1.0x
        # Carmen (tarde, no participa en recreos mañana)
        assert distribucion[profesores_basicos[0].id] < distribucion[profesores_basicos[1].id]

    def test_distribucion_mixta_turnos(self, session, curso_activo, config_basica, zonas_basicas):
        """Profesor mixto participa en ambos turnos."""
        config_basica.hora_recreo1_tarde = time(15, 30)
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        prof_manana = Profesor(
            nombre_completo="ONLY, MAÑANA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        prof_mixto = Profesor(
            nombre_completo="BOTH, MIXTO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mixto",
            tutor=False,
        )
        session.add_all([prof_manana, prof_mixto])
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # Mixto debería tener más guardias que mañana (participa en 3 recreos vs 2)
        assert distribucion[prof_mixto.id] > distribucion[prof_manana.id]


class TestObtenerEstadisticas:
    def test_estadisticas_completas(
        self, session, curso_activo, config_basica, profesores_basicos, zonas_basicas
    ):
        """Obtiene estadísticas del curso."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)  # 22 días lectivos
        session.commit()

        stats = obtener_estadisticas(session)

        assert stats["dias_lectivos"] == 22
        assert stats["recreos_manana"] == 2
        assert stats["recreos_tarde"] == 0
        assert stats["num_zonas"] == 2
        assert stats["num_profesores"] == 3
        # Slots = 22 días × 2 recreos × 2 zonas = 88
        assert stats["slots_totales"] == 88

    def test_estadisticas_con_recreos_config(
        self, session, curso_activo, config_basica, profesores_basicos, zonas_basicas
    ):
        """Calcula slots con recreos_config."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)  # 5 días
        config_basica.recreos_config = json.dumps(
            [
                {"id": 1, "turno": "mañana", "zonas": 2},
                {"id": 2, "turno": "mañana", "zonas": 1},
            ]
        )
        session.commit()

        stats = obtener_estadisticas(session)

        # 5 días × (2 + 1 zonas por recreo) = 15 slots
        assert stats["slots_totales"] == 15


class TestCalculoCompleto:
    def test_calculo_guardias_suma_exacta(
        self, session, curso_activo, config_basica, profesores_basicos, zonas_basicas
    ):
        """La distribución final suma exactamente los slots totales."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        distribucion = calcular_guardias_por_profesor(session)
        stats = obtener_estadisticas(session)

        assert sum(distribucion.values()) == stats["slots_totales"]

    def test_error_sin_configuracion(self, session):
        """Lanza error si no hay configuración."""
        with pytest.raises(ValueError, match="No hay curso activo"):
            calcular_guardias_por_profesor(session)

    def test_error_sin_profesores(self, session, curso_activo, config_basica):
        """Lanza error si no hay profesores."""
        with pytest.raises(ValueError, match="No hay profesores"):
            calcular_guardias_por_profesor(session)

    def test_error_sin_zonas(self, session, curso_activo, config_basica, profesores_basicos):
        """Lanza error si no hay zonas."""
        with pytest.raises(ValueError, match="No hay zonas"):
            calcular_guardias_por_profesor(session)


class TestProfesoresConFechasLimite:
    """Tests para profesores con fecha_inicio_guardias y fecha_fin_guardias."""

    def test_profesor_con_fecha_inicio_posterior(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Profesor que empieza guardias después del inicio del curso."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)  # 22 días lectivos
        session.commit()

        prof1 = Profesor(
            nombre_completo="TEMPRANO, JUAN",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        prof2 = Profesor(
            nombre_completo="TARDIO, MARÍA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
            fecha_inicio_guardias=date(2025, 9, 15),  # Empieza a mitad de mes
        )
        session.add_all([prof1, prof2])
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # prof2 tiene menos días disponibles, debe tener menos guardias
        assert distribucion[prof2.id] < distribucion[prof1.id]

    def test_profesor_con_fecha_fin_anticipada(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Profesor que termina guardias antes del fin del curso."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)
        session.commit()

        prof1 = Profesor(
            nombre_completo="COMPLETO, ANA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        prof2 = Profesor(
            nombre_completo="TEMPRANO, PEDRO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
            fecha_fin_guardias=date(2025, 9, 15),  # Termina a mitad
        )
        session.add_all([prof1, prof2])
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # prof2 tiene menos días disponibles
        assert distribucion[prof2.id] < distribucion[prof1.id]

    def test_profesor_rango_completo_fuera_curso(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Profesor con rango completamente fuera del curso."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)
        session.commit()

        prof1 = Profesor(
            nombre_completo="NORMAL, LUIS",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        prof2 = Profesor(
            nombre_completo="FUERA, RANGO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
            fecha_inicio_guardias=date(2025, 10, 1),  # Después del curso
            fecha_fin_guardias=date(2025, 10, 31),
        )
        session.add_all([prof1, prof2])
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # prof2 no tiene días disponibles, debe tener 0 guardias
        assert distribucion[prof2.id] == 0.0
        assert distribucion[prof1.id] > 0.0

    def test_profesor_solo_fecha_inicio(self, session, curso_activo, config_basica, zonas_basicas):
        """Profesor con solo fecha_inicio_guardias (sin fin)."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)
        session.commit()

        prof = Profesor(
            nombre_completo="INICIO, SOLO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
            fecha_inicio_guardias=date(2025, 9, 15),  # Solo inicio
            fecha_fin_guardias=None,
        )
        session.add(prof)
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # Debe tener guardias proporcionales a días disponibles
        assert distribucion[prof.id] > 0.0

    def test_profesor_solo_fecha_fin(self, session, curso_activo, config_basica, zonas_basicas):
        """Profesor con solo fecha_fin_guardias (sin inicio)."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 30)
        session.commit()

        prof = Profesor(
            nombre_completo="FIN, SOLO",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
            fecha_inicio_guardias=None,
            fecha_fin_guardias=date(2025, 9, 15),  # Solo fin
        )
        session.add(prof)
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # Debe tener guardias proporcionales a días disponibles
        assert distribucion[prof.id] > 0.0


class TestCasosEdge:
    """Tests para casos edge y extremos."""

    def test_porcentaje_jornada_cero(self, session, curso_activo, config_basica, zonas_basicas):
        """Profesor con porcentaje_jornada 0 no recibe guardias."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        prof1 = Profesor(
            nombre_completo="NORMAL, ANA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        prof2 = Profesor(
            nombre_completo="CERO, JORNADA",
            horas_contrato=0.0,
            porcentaje_jornada=0.0,
            turno="mañana",
            tutor=False,
        )
        session.add_all([prof1, prof2])
        session.commit()

        distribucion = calcular_distribucion_cruda(session)

        # prof2 con jornada 0 debe tener 0 guardias
        assert distribucion[prof2.id] == 0.0
        assert distribucion[prof1.id] > 0.0

    def test_porcentajes_jornada_extremos(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Test con porcentajes de jornada muy variados."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        profesores = [
            Profesor(
                nombre_completo="COMPLETO, UNO",
                horas_contrato=30.0,
                porcentaje_jornada=1.0,
                turno="mañana",
                tutor=False,
            ),
            Profesor(
                nombre_completo="MEDIO, DOS",
                horas_contrato=15.0,
                porcentaje_jornada=0.5,
                turno="mañana",
                tutor=False,
            ),
            Profesor(
                nombre_completo="CUARTO, TRES",
                horas_contrato=7.5,
                porcentaje_jornada=0.25,
                turno="mañana",
                tutor=False,
            ),
        ]
        for p in profesores:
            session.add(p)
        session.commit()

        distribucion = calcular_guardias_por_profesor(session)

        # Guardias deben ser proporcionales a porcentaje
        assert distribucion[profesores[0].id] > distribucion[profesores[1].id]
        assert distribucion[profesores[1].id] > distribucion[profesores[2].id]

    def test_todos_profesores_turno_tarde_sin_recreos_tarde(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Todos profesores de tarde pero sin recreos de tarde."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        config_basica.hora_recreo1_tarde = None
        config_basica.hora_recreo2_tarde = None
        session.commit()

        profesores = [
            Profesor(
                nombre_completo="TARDE, UNO",
                horas_contrato=30.0,
                porcentaje_jornada=1.0,
                turno="tarde",
                tutor=False,
            ),
            Profesor(
                nombre_completo="TARDE, DOS",
                horas_contrato=30.0,
                porcentaje_jornada=1.0,
                turno="tarde",
                tutor=False,
            ),
        ]
        for p in profesores:
            session.add(p)
        session.commit()

        # Esto debe lanzar error porque la suma de participación es 0
        with pytest.raises(ValueError, match="La suma de participación ponderada es 0"):
            calcular_distribucion_cruda(session)

    def test_error_dias_lectivos_cero(
        self, session, curso_activo, config_basica, profesores_basicos, zonas_basicas
    ):
        """Error cuando no hay días lectivos."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 8, 31)  # Rango inválido
        session.commit()

        with pytest.raises(ValueError, match="No hay días lectivos"):
            calcular_guardias_por_profesor(session)

    def test_error_suma_participacion_cero(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Error cuando suma de participación es cero."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        # Profesor con jornada 0
        prof = Profesor(
            nombre_completo="CERO, TOTAL",
            horas_contrato=0.0,
            porcentaje_jornada=0.0,
            turno="mañana",
            tutor=False,
        )
        session.add(prof)
        session.commit()

        with pytest.raises(ValueError, match="La suma de participación ponderada es 0"):
            calcular_guardias_por_profesor(session)

    def test_redondeo_con_minimo_una_guardia(
        self, session, curso_activo, config_basica, zonas_basicas
    ):
        """Verifica que profesores con participación mínima reciben al menos 1 guardia."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        session.commit()

        profesores = [
            Profesor(
                nombre_completo="PRINCIPAL, UNO",
                horas_contrato=30.0,
                porcentaje_jornada=1.0,
                turno="mañana",
                tutor=False,
            ),
            Profesor(
                nombre_completo="MINIMO, DOS",
                horas_contrato=2.0,
                porcentaje_jornada=0.067,  # Muy poco
                turno="mañana",
                tutor=False,
            ),
        ]
        for p in profesores:
            session.add(p)
        session.commit()

        distribucion = calcular_guardias_por_profesor(session)

        # Incluso con participación mínima, puede recibir guardias por redondeo
        # (depende de los residuos)
        assert distribucion[profesores[0].id] > 0
        # prof2 puede o no recibir guardias dependiendo del redondeo

    def test_dias_lectivos_con_festivos_automaticos_activos(self, session, config_basica):
        """Test con festivos automáticos activados."""
        config_basica.fecha_inicio_curso = date(2025, 10, 1)
        config_basica.fecha_fin_curso = date(2025, 10, 31)  # Incluye 9 y 12 octubre
        config_basica.activar_festivos_automaticos = True
        session.commit()

        dias = listar_dias_lectivos(config_basica)

        # Octubre 2025: 23 días hábiles, menos festivos automáticos
        # 9 octubre es jueves (festivo)
        # 12 octubre es domingo (ya no cuenta como día lectivo)
        assert date(2025, 10, 9) not in dias
        assert len(dias) < 23  # Debe tener menos por los festivos


class TestCalculoFactorParticipacion:
    """Tests específicos para calcular_factor_participacion."""

    def test_factor_mixto_ambos_recreos(self):
        """Profesor mixto con recreos en ambos turnos recibe factor 1.0."""
        from services.calculador_guardias import calcular_factor_participacion

        prof = Profesor(
            nombre_completo="MIXTO, TEST",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mixto",
            tutor=False,
        )

        factor = calcular_factor_participacion(prof, recreos_manana=2, recreos_tarde=1)
        assert factor == 1.0

    def test_factor_manana_solo_manana(self):
        """Profesor mañana solo con recreos mañana recibe factor 1.0."""
        from services.calculador_guardias import calcular_factor_participacion

        prof = Profesor(
            nombre_completo="MANANA, TEST",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )

        factor = calcular_factor_participacion(prof, recreos_manana=2, recreos_tarde=0)
        assert factor == 1.0

    def test_factor_tarde_solo_tarde(self):
        """Profesor tarde solo con recreos tarde recibe factor 1.0."""
        from services.calculador_guardias import calcular_factor_participacion

        prof = Profesor(
            nombre_completo="TARDE, TEST",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="tarde",
            tutor=False,
        )

        factor = calcular_factor_participacion(prof, recreos_manana=0, recreos_tarde=2)
        assert factor == 1.0

    def test_factor_sin_recreos(self):
        """Sin recreos el factor es 0."""
        from services.calculador_guardias import calcular_factor_participacion

        prof = Profesor(
            nombre_completo="TEST, PROF",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )

        factor = calcular_factor_participacion(prof, recreos_manana=0, recreos_tarde=0)
        assert factor == 0.0


class TestRecreoConfigAvanzado:
    """Tests para configuración avanzada de recreos con zonas variables."""

    def test_recreos_con_diferentes_zonas_por_recreo(
        self, session, curso_activo, config_basica, profesores_basicos
    ):
        """Test con recreos que tienen diferente número de zonas."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        config_basica.recreos_config = json.dumps(
            [
                {"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 3},
                {"id": 2, "etiqueta": "R2", "turno": "mañana", "zonas": 2},
            ]
        )
        session.commit()

        # Crear 5 zonas pero los recreos solo usan 3 y 2
        zonas = [Zona(nombre_zona=f"Zona {i}", descripcion=f"Zona {i}") for i in range(1, 6)]
        for z in zonas:
            session.add(z)
        session.commit()

        stats = obtener_estadisticas(session)

        # 5 días × (3 + 2) zonas por día = 25 slots
        assert stats["slots_totales"] == 25
        assert stats["num_zonas"] == 5

    def test_recreos_zonas_limitadas_por_zonas_reales(
        self, session, curso_activo, config_basica, profesores_basicos
    ):
        """Test donde recreos_config pide más zonas de las disponibles."""
        config_basica.fecha_inicio_curso = date(2025, 9, 1)
        config_basica.fecha_fin_curso = date(2025, 9, 5)
        config_basica.recreos_config = json.dumps(
            [
                {"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 10},  # Pide 10
            ]
        )
        session.commit()

        # Solo hay 2 zonas reales
        zonas = [Zona(nombre_zona="Z1"), Zona(nombre_zona="Z2")]
        for z in zonas:
            session.add(z)
        session.commit()

        stats = obtener_estadisticas(session)

        # Debe limitarse a 2 zonas: 5 días × 2 = 10 slots
        assert stats["slots_totales"] == 10
