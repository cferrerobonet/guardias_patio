"""
Test para validar que un profesor NO haga más de 1 guardia al día
(sumando mañana y tarde).
"""
import sys
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Base, Configuracion, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_max_una_guardia_por_dia(session):
    """
    REQUISITO: Un profesor sólo puede hacer máximo 1 guardia al día,
    sin importar si es de mañana o tarde.
    """
    # Configuración básica con 2 recreos en mañana y 2 en tarde
    config = Configuracion(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2024, 9, 5),  # 5 días lectivos (L-V)
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(15, 30),
        hora_recreo2_tarde=time(16, 30),
        activar_festivos_automaticos=False,
        recreos_config='[{"id":1,"turno":"mañana","zonas":2},{"id":2,"turno":"mañana","zonas":2},{"id":3,"turno":"tarde","zonas":2},{"id":4,"turno":"tarde","zonas":2}]',
    )
    session.add(config)

    # 2 zonas
    zona1 = Zona(nombre_zona="Patio A")
    zona2 = Zona(nombre_zona="Patio B")
    session.add_all([zona1, zona2])

    # 10 profesores mixtos (pueden cubrir mañana y tarde)
    for i in range(10):
        prof = Profesor(
            nombre_completo=f"PROFESOR{i+1}, TEST",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mixto",
            tutor=False,
        )
        session.add(prof)

    session.commit()

    # Generar calendario
    calendario, _ = generar_calendario_guardias(session)

    # Verificar: Ningún profesor debe tener más de 1 guardia en el mismo día
    guardias_por_profesor_dia = {}
    for g in calendario:
        key = (g.profesor_id, g.fecha)
        if key not in guardias_por_profesor_dia:
            guardias_por_profesor_dia[key] = []
        guardias_por_profesor_dia[key].append(g)

    errores = []
    for (prof_id, fecha), guardias in guardias_por_profesor_dia.items():
        if len(guardias) > 1:
            profesor = session.query(Profesor).get(prof_id)
            turnos = [g.turno for g in guardias]
            recreos = [g.recreo for g in guardias]
            zonas = [g.zona_id for g in guardias]
            errores.append(
                f"Profesor {profesor.nombre_completo} (ID:{prof_id}) tiene "
                f"{len(guardias)} guardias el {fecha}: "
                f"turnos={turnos}, recreos={recreos}, zonas={zonas}"
            )

    # Assertion con mensaje detallado
    assert not errores, (
        f"Se encontraron {len(errores)} violaciones de la regla "
        f"'máximo 1 guardia por día':\n" + "\n".join(f"  - {e}" for e in errores)
    )


def test_distribucion_equilibrada_con_limite_diario(session):
    """
    Verifica que con el límite de 1 guardia/día, el algoritmo
    siga distribuyendo guardias de forma equilibrada.
    """
    config = Configuracion(
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2024, 9, 30),  # Mes completo (aprox. 22 días lectivos)
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(15, 30),
        hora_recreo2_tarde=None,
        activar_festivos_automaticos=False,
        recreos_config='[{"id":1,"turno":"mañana","zonas":3},{"id":2,"turno":"tarde","zonas":3}]',
    )
    session.add(config)

    # 3 zonas
    for i in range(3):
        session.add(Zona(nombre_zona=f"Zona {i+1}"))

    # 15 profesores mixtos
    for i in range(15):
        prof = Profesor(
            nombre_completo=f"APELLIDO{i+1}, NOMBRE{i+1}",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mixto",
            tutor=False,
        )
        session.add(prof)

    session.commit()

    # Generar calendario
    calendario, asignadas = generar_calendario_guardias(session)

    # Verificar límite diario
    guardias_por_profesor_dia = {}
    for g in calendario:
        key = (g.profesor_id, g.fecha)
        guardias_por_profesor_dia[key] = guardias_por_profesor_dia.get(key, 0) + 1

    max_guardias_dia = max(guardias_por_profesor_dia.values())
    assert max_guardias_dia == 1, (
        f"Se encontró un profesor con {max_guardias_dia} guardias en un día, "
        "cuando el máximo permitido es 1"
    )

    # Verificar que se generaron guardias
    assert len(calendario) > 0, "No se generaron guardias"

    # Verificar distribución razonablemente equilibrada
    # (con límite de 1/día, la variación puede ser mayor)
    if asignadas:
        valores = list(asignadas.values())
        max_asig = max(valores)
        min_asig = min(valores)
        # Permitir mayor variación debido a la restricción adicional
        assert max_asig - min_asig <= 5, (
            f"Distribución muy desigual: máximo={max_asig}, mínimo={min_asig}"
        )
