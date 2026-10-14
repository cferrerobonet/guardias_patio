"""Guardias voluntarias antes del reparto oficial (decidido con CarlosFB, 2026-09-30).

Las primeras semanas del curso algunos profesores hacen guardias voluntarias. Desde el
inicio del reparto oficial todos hacen las suyas, y lo justo es que cada uno haga su
parte del curso contando las voluntarias como hechas:

- Ranuras oficiales S: sólo los días lectivos desde el inicio del reparto oficial.
- Se reparte S + W (W = voluntarias) con el algoritmo de siempre: parte_i.
- Cuota oficial_i = parte_i − V_i; las cuotas suman S.
- Quien hizo más de su parte queda a 0 y el grupo se reparte sin él.
- Con V = 0 y reparto desde el inicio de curso, todo sale igual que antes.
"""

import json
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import Base, Configuracion, CursoEscolar, Profesor, Zona
from services.calculador_guardias import (
    calcular_guardias_por_profesor,
    fecha_inicio_reparto,
    listar_dias_lectivos,
    listar_dias_reparto,
)
from services.distribucion_cuotas_service import OBS_HA_HECHO_DE_MAS, DistribucionCuotasService

ROOT = Path(__file__).resolve().parents[1]

INICIO_CURSO = date(2025, 8, 25)  # lunes
INICIO_OFICIAL = date(2025, 9, 1)  # lunes
FIN_CURSO = date(2025, 10, 20)  # lunes: 36 días lectivos desde el inicio oficial


# ─────────────────────────────────────────────────────────────────────────────
# Escenarios
# ─────────────────────────────────────────────────────────────────────────────


def _curso(session):
    session.add(
        CursoEscolar(
            anio_inicio=2025,
            anio_fin=2026,
            fecha_inicio=date(2025, 8, 1),
            fecha_fin=date(2026, 6, 30),
            nombre="Curso 2025/2026",
            activo=True,
            cerrado=False,
        )
    )


def _config(session, recreos, inicio=INICIO_CURSO, fin=FIN_CURSO, oficial=INICIO_OFICIAL,
            festivos=False, ajuste_tutores=1.0):
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=inicio,
        fecha_fin_curso=fin,
        fecha_inicio_reparto_oficial=oficial,
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        ajuste_tutores=ajuste_tutores,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=festivos,
        recreos_config=json.dumps(recreos),
    )
    session.add(config)
    return config


def _profesor(nombre, horas=30.0, turno="mixto", tutor=False, voluntarias=0, recreos=None):
    return Profesor(
        nombre_completo=nombre,
        horas_contrato=float(horas),
        porcentaje_jornada=horas / 30 * 100,
        turno=turno,
        tutor=tutor,
        activo=True,
        guardias_voluntarias=voluntarias,
        recreos_permitidos=recreos,
    )


def _diez_iguales(session, voluntarias=None, oficial=INICIO_OFICIAL):
    """10 profesores iguales y 180 ranuras oficiales (36 días × 1 recreo × 5 zonas)."""
    voluntarias = voluntarias or {}
    _curso(session)
    session.add_all([Zona(nombre_zona=f"Z{i}", activa=True) for i in range(5)])
    _config(session, [{"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 5}], oficial=oficial)
    profes = [
        _profesor(f"P{i:02d}, Nombre", voluntarias=voluntarias.get(i, 0)) for i in range(10)
    ]
    session.add_all(profes)
    session.commit()
    return profes


def _escenario_variado(session, oficial=None):
    """Turnos, jornadas, tutorías y recreos variados; festivos automáticos activos."""
    _curso(session)
    session.add_all([Zona(nombre_zona=f"Z{i}", activa=True) for i in range(3)])
    _config(
        session,
        [
            {"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 3},
            {"id": 2, "etiqueta": "R2", "turno": "mañana", "zonas": 2},
            {"id": 3, "etiqueta": "R3", "turno": "tarde", "zonas": 2},
            {"id": 4, "etiqueta": "R4", "turno": "tarde", "zonas": 1},
        ],
        inicio=date(2025, 9, 8),
        fin=date(2025, 12, 19),
        oficial=oficial,
        festivos=True,
        ajuste_tutores=0.9,
    )
    datos = [
        ("A01, Uno", 30, "mañana", False, None),
        ("A02, Dos", 25, "mañana", True, None),
        ("A03, Tres", 15, "mañana", False, None),
        ("A04, Cuatro", 30, "tarde", False, None),
        ("A05, Cinco", 20, "tarde", True, None),
        ("A06, Seis", 30, "mixto", False, None),
        ("A07, Siete", 18, "mixto", True, None),
        ("A08, Ocho", 30, "mixto", False, "[3, 4]"),
        ("A09, Nueve", 22, "mixto", False, json.dumps({"0": [1], "2": [2]})),
        ("A10, Diez", 27, "mañana", False, None),
        ("A11, Once", 12, "tarde", False, None),
        ("A12, Doce", 30, "mixto", True, None),
    ]
    for nombre, horas, turno, tutor, recreos in datos:
        session.add(_profesor(nombre, horas, turno, tutor, recreos=recreos))
    session.commit()


# Cuotas del servicio con este escenario, sin voluntarias. Desde la v6.10.0
# (equidad primero, `reparto_equitativo`) los mixtos sólo ponen lo que falta en
# cada turno al mismo nivel que los fijos: con 30 h y sin tutoría, mañana (A01),
# tarde (A04), mixto (A06) y mixto sólo de tarde (A08) hacen 62-63. En la v6.3.3
# eran 58, 41, 98 y 40: el mixto cobraba la parte de los dos turnos. El total no
# cambia (584) y no queda ningún hueco.
CUOTAS_V633_SERVICIO = {
    "A01": 63, "A02": 47, "A03": 31, "A04": 62, "A05": 38, "A06": 63,
    "A07": 34, "A08": 63, "A09": 46, "A10": 56, "A11": 25, "A12": 56,
}  # fmt: skip
CUOTAS_V633_CALCULADOR = {
    "A01": 43, "A02": 32, "A03": 22, "A04": 43, "A05": 26, "A06": 87,
    "A07": 47, "A08": 87, "A09": 63, "A10": 39, "A11": 17, "A12": 78,
}  # fmt: skip


def _por_prefijo(session, cuotas):
    nombres = {p.id: p.nombre_completo[:3] for p in session.query(Profesor).all()}
    return {nombres[pid]: c for pid, c in cuotas.items()}


def _config_de(session):
    return session.query(Configuracion).first()


# ─────────────────────────────────────────────────────────────────────────────
# Días del reparto
# ─────────────────────────────────────────────────────────────────────────────


class TestDiasDelReparto:
    def test_sin_inicio_oficial_empieza_con_el_curso(self, session):
        _diez_iguales(session, oficial=None)
        config = _config_de(session)
        assert fecha_inicio_reparto(config) == INICIO_CURSO
        assert listar_dias_reparto(config) == listar_dias_lectivos(config)

    def test_inicio_oficial_recorta_los_dias_y_no_toca_los_lectivos(self, session):
        _diez_iguales(session)
        config = _config_de(session)
        dias = listar_dias_reparto(config)
        assert dias[0] == INICIO_OFICIAL
        assert len(dias) == 36
        assert len(listar_dias_lectivos(config)) == 41

    def test_inicio_oficial_anterior_al_curso_no_cuenta(self, session):
        _diez_iguales(session, oficial=date(2025, 8, 1))
        assert fecha_inicio_reparto(_config_de(session)) == INICIO_CURSO

    def test_inicio_oficial_recorta_las_ranuras(self, session):
        _diez_iguales(session)
        servicio = DistribucionCuotasService(session)
        config = _config_de(session)
        assert servicio._calcular_total_slots(config) == 180
        assert servicio._calcular_slots_por_turno(config) == {"mañana": 180, "tarde": 0}
        config.fecha_inicio_reparto_oficial = None
        session.commit()
        assert servicio._calcular_total_slots(config) == 205


# ─────────────────────────────────────────────────────────────────────────────
# Reparto con voluntarias
# ─────────────────────────────────────────────────────────────────────────────


class TestRepartoConVoluntarias:
    def test_ejemplo_de_carlosfb(self, session):
        profes = _diez_iguales(session, voluntarias={0: 10, 1: 10})
        cuotas = DistribucionCuotasService(session).calcular_cuotas()
        assert cuotas[profes[0].id] == 10
        assert cuotas[profes[1].id] == 10
        assert all(cuotas[p.id] == 20 for p in profes[2:])
        assert sum(cuotas.values()) == 180

    def test_desglose_parte_del_curso(self, session):
        profes = _diez_iguales(session, voluntarias={0: 10, 1: 10})
        servicio = DistribucionCuotasService(session)
        servicio.calcular_cuotas()
        assert servicio.ultima_parte_curso[profes[0].id] == 20
        assert servicio.ultimas_voluntarias[profes[0].id] == 10
        assert not servicio.ultimos_excedidos

    def test_el_que_hizo_de_mas_queda_a_cero_y_se_reparte_sin_el(self, session):
        profes = _diez_iguales(session, voluntarias={0: 30})
        servicio = DistribucionCuotasService(session)
        cuotas = servicio.calcular_cuotas()
        assert cuotas[profes[0].id] == 0
        assert all(cuotas[p.id] == 20 for p in profes[1:])
        assert sum(cuotas.values()) == 180
        assert servicio.ultimos_excedidos == {profes[0].id}

    def test_observacion_del_que_hizo_de_mas(self, session):
        profes = _diez_iguales(session, voluntarias={0: 30})
        info = DistribucionCuotasService(session).obtener_info_cuota(profes[0])
        assert info.cuota == 0
        assert info.ha_hecho_de_mas
        assert info.guardias_voluntarias == 30
        assert OBS_HA_HECHO_DE_MAS in info.observaciones

    def test_varios_excedidos_iterativo(self, session):
        # 200 + 100: parte 30 → el de 100 sale; luego (180 + 25) / 9 ≈ 22.8 < 25 → sale
        profes = _diez_iguales(session, voluntarias={0: 100, 1: 25})
        servicio = DistribucionCuotasService(session)
        cuotas = servicio.calcular_cuotas()
        assert cuotas[profes[0].id] == 0
        assert cuotas[profes[1].id] == 0
        assert sum(cuotas.values()) == 180
        assert all(cuotas[p.id] >= 0 for p in profes)
        assert servicio.ultimos_excedidos == {profes[0].id, profes[1].id}

    def test_sustituir_voluntarias_sin_guardar(self, session):
        profes = _diez_iguales(session)
        servicio = DistribucionCuotasService(session)
        cuotas = servicio.calcular_cuotas(voluntarias={profes[0].id: 10})
        assert cuotas[profes[0].id] == 9  # (180 + 10) / 10 = 19 − 10
        session.expire_all()
        assert session.get(Profesor, profes[0].id).guardias_voluntarias == 0

    def test_desglose_cuota_para_la_ficha(self, session):
        profes = _diez_iguales(session, voluntarias={0: 10, 1: 10})
        desglose = DistribucionCuotasService(session).desglose_cuota(profes[0].id, 15)
        # Sustituye sus 10 por 15: (180 + 25) / 10 = 20,5; el redondeo del grupo le da 21
        assert desglose == {
            "cuota": 6,
            "parte_curso": 21,
            "voluntarias": 15,
            "ha_hecho_de_mas": False,
        }

    def test_desglose_sin_configuracion_es_none(self, session):
        prof = _profesor("SOLO, Uno")
        session.add(prof)
        session.commit()
        assert DistribucionCuotasService(session).desglose_cuota(prof.id, 3) is None


class TestPorTurno:
    def _montar(self, session, voluntarias):
        _curso(session)
        session.add_all([Zona(nombre_zona=f"Z{i}", activa=True) for i in range(2)])
        _config(
            session,
            [
                {"id": 1, "etiqueta": "R1", "turno": "mañana", "zonas": 2},
                {"id": 3, "etiqueta": "R3", "turno": "tarde", "zonas": 1},
            ],
        )
        profes = (
            [_profesor(f"M{i}, M", turno="mañana") for i in range(4)]
            + [_profesor(f"T{i}, T", turno="tarde") for i in range(4)]
            + [_profesor(f"X{i}, X", turno="mixto") for i in range(2)]
        )
        for indice, v in voluntarias.items():
            profes[indice].guardias_voluntarias = v
        session.add_all(profes)
        session.commit()
        return profes

    def test_las_voluntarias_de_manana_no_tocan_la_tarde(self, session):
        profes = self._montar(session, {0: 12})
        servicio = DistribucionCuotasService(session)
        con = servicio.calcular_cuotas()
        slots = servicio._calcular_slots_por_turno(_config_de(session))
        for p in profes:
            p.guardias_voluntarias = 0
        session.commit()
        sin = servicio.calcular_cuotas()
        tarde = [p.id for p in profes if p.turno == "tarde"]
        assert all(con[pid] == sin[pid] for pid in tarde)
        assert con[profes[0].id] < sin[profes[0].id]
        assert sum(con.values()) == sum(sin.values()) == slots["mañana"] + slots["tarde"]

    def test_voluntarias_de_un_mixto_se_reparten_entre_turnos(self, session):
        profes = self._montar(session, {8: 12})
        servicio = DistribucionCuotasService(session)
        cuotas = servicio.calcular_cuotas()
        slots = servicio._calcular_slots_por_turno(_config_de(session))
        assert sum(cuotas.values()) == slots["mañana"] + slots["tarde"]
        mixto = profes[8].id
        assert servicio.ultima_parte_curso[mixto] - cuotas[mixto] == 12
        # Mañana tiene el doble de ranuras: la mayor parte de sus voluntarias va allí
        manana = [p.id for p in profes if p.turno == "mañana"]
        tarde = [p.id for p in profes if p.turno == "tarde"]
        for p in profes:
            p.guardias_voluntarias = 0
        session.commit()
        sin = servicio.calcular_cuotas()
        rebaja_manana = sum(sin[i] - cuotas[i] for i in manana)
        rebaja_tarde = sum(sin[i] - cuotas[i] for i in tarde)
        assert rebaja_manana <= 0 and rebaja_tarde <= 0  # los demás hacen más, no menos
        assert cuotas[mixto] < sin[mixto]


# ─────────────────────────────────────────────────────────────────────────────
# No regresión
# ─────────────────────────────────────────────────────────────────────────────


class TestNoRegresion:
    def test_servicio_igual_que_v633(self, session):
        _escenario_variado(session)
        cuotas = DistribucionCuotasService(session).calcular_cuotas()
        assert _por_prefijo(session, cuotas) == CUOTAS_V633_SERVICIO

    def test_calculador_igual_que_v633(self, session):
        _escenario_variado(session)
        assert _por_prefijo(session, calcular_guardias_por_profesor(session)) == (
            CUOTAS_V633_CALCULADOR
        )

    def test_inicio_oficial_igual_al_inicio_de_curso_no_cambia_nada(self, session):
        _escenario_variado(session, oficial=date(2025, 9, 8))
        cuotas = DistribucionCuotasService(session).calcular_cuotas()
        assert _por_prefijo(session, cuotas) == CUOTAS_V633_SERVICIO
        assert _por_prefijo(session, calcular_guardias_por_profesor(session)) == (
            CUOTAS_V633_CALCULADOR
        )


class TestCalculadorAntiguo:
    """El cálculo de las estadísticas aplica la misma fórmula que el servicio."""

    def test_mismas_cifras_que_el_servicio_con_voluntarias(self, session):
        _diez_iguales(session, voluntarias={0: 10, 1: 10})
        servicio = DistribucionCuotasService(session).calcular_cuotas()
        assert calcular_guardias_por_profesor(session) == servicio

    def test_mismas_cifras_que_el_servicio_con_excedido(self, session):
        _diez_iguales(session, voluntarias={0: 30})
        servicio = DistribucionCuotasService(session).calcular_cuotas()
        assert calcular_guardias_por_profesor(session) == servicio

    def test_estadisticas_cuentan_solo_el_reparto_oficial(self, session):
        from services.calculador_guardias import obtener_estadisticas

        _diez_iguales(session)
        stats = obtener_estadisticas(session)
        assert stats["dias_lectivos"] == 36
        assert stats["slots_totales"] == 180


# ─────────────────────────────────────────────────────────────────────────────
# Asignadores
# ─────────────────────────────────────────────────────────────────────────────


def _curso_corto(session):
    _curso(session)
    session.add_all([Zona(nombre_zona="A", activa=True), Zona(nombre_zona="B", activa=True)])
    _config(
        session,
        [{"id": 1, "etiqueta": "R1", "turno": "mañana"}],
        inicio=date(2025, 9, 15),
        fin=date(2025, 10, 15),
        oficial=date(2025, 10, 1),
    )
    session.add_all([_profesor(f"Prof{i:02d}, N", turno="mañana") for i in range(6)])
    session.commit()


@pytest.mark.slow
class TestAsignadores:
    def test_cpsat_no_genera_guardias_antes_del_inicio_oficial(self, session):
        from services.asignador_guardias_cpsat import generar_guardias_cpsat

        _curso_corto(session)
        guardias, _ = generar_guardias_cpsat(session, timeout_seconds=20)
        assert guardias
        assert min(g.fecha for g in guardias) >= date(2025, 10, 1)
        assert len(guardias) == len(listar_dias_reparto(_config_de(session)))


# ─────────────────────────────────────────────────────────────────────────────
# Esquema: migración Alembic y fallback
# ─────────────────────────────────────────────────────────────────────────────


def _alembic_upgrade(db_url):
    from alembic.config import Config

    from alembic import command

    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", str(ROOT / "alembic"))
    command.upgrade(cfg, "head")


class TestEsquema:
    def test_migracion_anade_las_columnas(self, tmp_path):
        db = tmp_path / "migracion.db"
        _alembic_upgrade(f"sqlite:///{db}")
        inspector = inspect(create_engine(f"sqlite:///{db}"))
        profesores = {c["name"]: c for c in inspector.get_columns("profesores")}
        config = {c["name"] for c in inspector.get_columns("configuracion")}
        assert "guardias_voluntarias" in profesores
        assert not profesores["guardias_voluntarias"]["nullable"]
        assert "fecha_inicio_reparto_oficial" in config

    def test_fallback_anade_las_columnas_con_valor_por_defecto(self, tmp_path):
        from database.db_manager import _apply_direct_migrations

        engine = create_engine(f"sqlite:///{tmp_path / 'antigua.db'}")
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE profesores (id INTEGER PRIMARY KEY, nombre_completo VARCHAR, "
                "activo BOOLEAN, zona_preferida_id INTEGER, dias_semana_permitidos TEXT, "
                "recreos_permitidos TEXT, curso_id INTEGER)"
            ))
            conn.execute(text(
                "CREATE TABLE configuracion (id INTEGER PRIMARY KEY, anio_inicio_curso INTEGER, "
                "curso_activo_id INTEGER, algoritmo_asignacion VARCHAR, recreos_config TEXT)"
            ))
            conn.execute(text("INSERT INTO profesores (id, nombre_completo) VALUES (1, 'A, B')"))
            conn.execute(text("INSERT INTO configuracion (id) VALUES (1)"))

        _apply_direct_migrations(engine)

        inspector = inspect(engine)
        assert "guardias_voluntarias" in {c["name"] for c in inspector.get_columns("profesores")}
        assert "fecha_inicio_reparto_oficial" in {
            c["name"] for c in inspector.get_columns("configuracion")
        }
        with engine.connect() as conn:
            assert conn.execute(text("SELECT guardias_voluntarias FROM profesores")).scalar() == 0
            assert conn.execute(
                text("SELECT fecha_inicio_reparto_oficial FROM configuracion")
            ).scalar() is None


# ─────────────────────────────────────────────────────────────────────────────
# Sincronización y exportación JSON (retrocompatibles)
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def otra_bd():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine)()
    yield sesion
    sesion.close()


def _origen(session):
    _curso(session)
    _config(session, [{"id": 1, "etiqueta": "R1", "turno": "mañana"}])
    session.add(_profesor("VOLUNTARIO, Uno", voluntarias=7))
    session.commit()


class TestSincronizacion:
    def test_ida_y_vuelta(self, session, otra_bd, tmp_path):
        from sync.data_exporter import DataExporter

        _origen(session)
        ruta = tmp_path / "sync.json"
        assert DataExporter.export_to_json(session, ruta)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        assert datos["profesores"][0]["guardias_voluntarias"] == 7
        assert datos["configuracion"][0]["fecha_inicio_reparto_oficial"] == "2025-09-01"

        assert DataExporter.import_from_json(otra_bd, ruta)
        assert otra_bd.query(Profesor).one().guardias_voluntarias == 7
        assert otra_bd.query(Configuracion).one().fecha_inicio_reparto_oficial == INICIO_OFICIAL

    def test_fichero_antiguo_sin_las_claves(self, session, otra_bd, tmp_path):
        from sync.data_exporter import DataExporter

        _origen(session)
        ruta = tmp_path / "sync.json"
        DataExporter.export_to_json(session, ruta)
        datos = json.loads(ruta.read_text(encoding="utf-8"))
        for p in datos["profesores"]:
            p.pop("guardias_voluntarias")
        for c in datos["configuracion"]:
            c.pop("fecha_inicio_reparto_oficial")
        ruta.write_text(json.dumps(datos), encoding="utf-8")

        assert DataExporter.import_from_json(otra_bd, ruta)
        assert otra_bd.query(Profesor).one().guardias_voluntarias == 0
        assert otra_bd.query(Configuracion).one().fecha_inicio_reparto_oficial is None

    def test_dtos_sin_las_claves(self):
        from sync.dtos import ConfiguracionSyncDTO, ProfesorSyncDTO

        profesor = ProfesorSyncDTO.from_dict(
            {"id": 1, "nombre_completo": "A, B", "horas_contrato": 30,
             "porcentaje_jornada": 100, "turno": "mañana"}
        )
        config = ConfiguracionSyncDTO.from_dict({"id": 1})
        assert profesor.guardias_voluntarias == 0
        assert config.fecha_inicio_reparto_oficial is None


class TestExportacionJSON:
    def test_ida_y_vuelta(self, session, otra_bd):
        from services.exportador import ExportadorDatos

        _origen(session)
        profesores = ExportadorDatos.exportar_profesores(session)
        config = ExportadorDatos.exportar_configuracion(session)
        assert profesores[0]["guardias_voluntarias"] == 7
        assert config["fecha_inicio_reparto_oficial"] == "2025-09-01"

        ExportadorDatos.importar_profesores(otra_bd, profesores)
        ExportadorDatos.importar_configuracion(otra_bd, config)
        otra_bd.commit()
        assert otra_bd.query(Profesor).one().guardias_voluntarias == 7
        assert otra_bd.query(Configuracion).one().fecha_inicio_reparto_oficial == INICIO_OFICIAL

    def test_copia_antigua_sin_las_claves(self, session, otra_bd):
        from services.exportador import ExportadorDatos

        _origen(session)
        profesores = ExportadorDatos.exportar_profesores(session)
        config = ExportadorDatos.exportar_configuracion(session)
        for p in profesores:
            p.pop("guardias_voluntarias")
        config.pop("fecha_inicio_reparto_oficial")

        ExportadorDatos.importar_profesores(otra_bd, profesores)
        ExportadorDatos.importar_configuracion(otra_bd, config)
        otra_bd.commit()
        assert otra_bd.query(Profesor).one().guardias_voluntarias == 0
        assert otra_bd.query(Configuracion).one().fecha_inicio_reparto_oficial is None


# ─────────────────────────────────────────────────────────────────────────────
# Capas: casos de uso de profesor y configuración
# ─────────────────────────────────────────────────────────────────────────────


class TestCasosDeUso:
    def test_crear_obtener_actualizar_listar_buscar(self, session):
        from application.dtos.profesor_dto import ActualizarProfesorDTO, CrearProfesorDTO
        from application.use_cases.profesor import (
            ActualizarProfesorUseCase,
            BuscarProfesoresUseCase,
            CrearProfesorUseCase,
            ListarProfesoresUseCase,
            ObtenerProfesorUseCase,
        )

        creado = CrearProfesorUseCase(session).execute(
            CrearProfesorDTO(
                nombre_completo="VOLUNTARIA, Ana", horas_contrato=30, turno="mañana",
                guardias_voluntarias=4,
            )
        )
        assert creado.guardias_voluntarias == 4
        assert ObtenerProfesorUseCase(session).execute(creado.id).guardias_voluntarias == 4

        actualizado = ActualizarProfesorUseCase(session).execute(
            creado.id, ActualizarProfesorDTO(guardias_voluntarias=9)
        )
        assert actualizado.guardias_voluntarias == 9
        listados = ListarProfesoresUseCase(session).execute()
        assert [p.guardias_voluntarias for p in listados if p.id == creado.id] == [9]
        encontrados = BuscarProfesoresUseCase(session).execute("VOLUNTARIA")
        assert encontrados[0].guardias_voluntarias == 9

    def test_actualizar_sin_el_campo_lo_conserva(self, session):
        from application.dtos.profesor_dto import ActualizarProfesorDTO
        from application.use_cases.profesor import ActualizarProfesorUseCase

        prof = _profesor("CONSERVA, Uno", voluntarias=5)
        session.add(prof)
        session.commit()
        dto = ActualizarProfesorUseCase(session).execute(
            prof.id, ActualizarProfesorDTO(nombre_completo="CONSERVA, Dos")
        )
        assert dto.guardias_voluntarias == 5

    def test_configuracion_guarda_limpia_y_conserva(self, session):
        from application.dtos.configuracion_dto import ActualizarConfiguracionDTO
        from application.use_cases.configuracion import (
            ActualizarConfiguracionUseCase,
            ObtenerConfiguracionUseCase,
        )

        _config(session, [{"id": 1, "etiqueta": "R1", "turno": "mañana"}], oficial=None)
        session.commit()
        actualizar = ActualizarConfiguracionUseCase(session)

        dto = actualizar.execute(
            ActualizarConfiguracionDTO(fecha_inicio_reparto_oficial=INICIO_OFICIAL)
        )
        assert dto.fecha_inicio_reparto_oficial == INICIO_OFICIAL
        # Sin el campo: se conserva
        actualizar.execute(ActualizarConfiguracionDTO(ajuste_tutores=0.8))
        assert ObtenerConfiguracionUseCase(session).execute().fecha_inicio_reparto_oficial == (
            INICIO_OFICIAL
        )
        # None explícito: vuelve a «igual que el inicio de curso»
        dto = actualizar.execute(ActualizarConfiguracionDTO(fecha_inicio_reparto_oficial=None))
        assert dto.fecha_inicio_reparto_oficial is None

    def test_mapper_de_configuracion(self, session):
        from infrastructure.mappers.configuracion_mapper import ConfiguracionMapper

        _config(session, [{"id": 1, "etiqueta": "R1", "turno": "mañana"}])
        session.commit()
        entidad = ConfiguracionMapper.to_entity(_config_de(session))
        assert entidad.fecha_inicio_reparto_oficial == INICIO_OFICIAL
        assert ConfiguracionMapper.to_model(entidad).fecha_inicio_reparto_oficial == INICIO_OFICIAL
