"""
Configuración compartida para tests con pytest.

Este módulo contiene fixtures comunes y configuración
para todos los tests del proyecto.
"""

import sys
from pathlib import Path
from typing import Generator

import pytest
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Insertar raíz del proyecto y src en sys.path para imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from models.models import Ausencia, Base, Guardia, Profesor, Zona  # noqa: E402

# ============================================================================
# FIXTURES DE BASE DE DATOS
# ============================================================================


@pytest.fixture(scope="session")
def engine():
    """
    Engine de SQLAlchemy en memoria para tests.

    Scope: session - se crea una vez por sesión de tests.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def session(engine) -> Generator[Session, None, None]:
    """
    Sesión de base de datos para tests.

    Cada test obtiene una sesión limpia que se revierte al finalizar.
    Scope: function - se crea una nueva para cada test.

    Yields:
        Session: Sesión de SQLAlchemy con rollback automático
    """
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    # Cleanup - orden correcto para evitar SAWarning
    session.rollback()  # Rollback de la sesión primero
    session.close()     # Cerrar sesión
    if transaction.is_active:
        transaction.rollback()  # Rollback de transacción solo si está activa
    connection.close()


@pytest.fixture
def db_with_data(session: Session) -> Session:
    """
    Sesión con datos de ejemplo pre-cargados.

    Útil para tests que necesitan datos existentes.

    Args:
        session: Sesión de base de datos

    Returns:
        Session: Sesión con datos de ejemplo
    """
    # Crear profesores de ejemplo
    prof1 = Profesor(
        nombre_completo="García López, María",
        horas_contrato=25,
        porcentaje_jornada=100,
        turno="mañana",
    )
    prof2 = Profesor(
        nombre_completo="Martínez Ruiz, Juan",
        horas_contrato=12.5,
        porcentaje_jornada=50,
        turno="tarde",
    )
    prof3 = Profesor(
        nombre_completo="Sánchez Pérez, Ana",
        horas_contrato=25,
        porcentaje_jornada=100,
        turno="mixto",
    )

    # Crear zonas de ejemplo
    zona1 = Zona(nombre_zona="Patio Principal", descripcion="Zona central del patio")
    zona2 = Zona(nombre_zona="Zona Deportiva", descripcion="Cancha y áreas deportivas")
    zona3 = Zona(nombre_zona="Cafetería", descripcion="Área de cafetería y comedor")

    # Agregar a la sesión
    session.add_all([prof1, prof2, prof3, zona1, zona2, zona3])
    session.commit()

    return session


# ============================================================================
# FIXTURES DE PYQT6
# ============================================================================


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    """
    QApplication para tests de UI.

    Scope: session - se crea una vez para todos los tests.

    Returns:
        QApplication: Instancia de aplicación Qt
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def qtbot(qapp, qtbot):
    """
    pytest-qt qtbot con QApplication.

    Permite interactuar con widgets Qt en tests.

    Args:
        qapp: Aplicación Qt
        qtbot: qtbot de pytest-qt

    Returns:
        qtbot configurado
    """
    return qtbot


# ============================================================================
# FIXTURES DE MODELOS
# ============================================================================


@pytest.fixture
def profesor_factory(session: Session):
    """
    Factory para crear profesores en tests.

    Args:
        session: Sesión de base de datos

    Returns:
        Callable: Función para crear profesores
    """

    def _create_profesor(
        nombre_completo: str = "Test Profesor",
        horas_contrato: float = 25,
        porcentaje_jornada: int = 100,
        turno: str = "mañana",
        **kwargs,
    ) -> Profesor:
        profesor = Profesor(
            nombre_completo=nombre_completo,
            horas_contrato=horas_contrato,
            porcentaje_jornada=porcentaje_jornada,
            turno=turno,
            **kwargs,
        )
        session.add(profesor)
        session.commit()
        return profesor

    return _create_profesor


@pytest.fixture
def zona_factory(session: Session):
    """
    Factory para crear zonas en tests.

    Args:
        session: Sesión de base de datos

    Returns:
        Callable: Función para crear zonas
    """

    def _create_zona(
        nombre_zona: str = "Zona Test", descripcion: str = "Zona de prueba", **kwargs
    ) -> Zona:
        zona = Zona(nombre_zona=nombre_zona, descripcion=descripcion, **kwargs)
        session.add(zona)
        session.commit()
        return zona

    return _create_zona


@pytest.fixture
def guardia_factory(session: Session):
    """
    Factory para crear guardias en tests.

    Args:
        session: Sesión de base de datos

    Returns:
        Callable: Función para crear guardias
    """
    from datetime import date

    def _create_guardia(
        profesor_id: int,
        zona_id: int,
        fecha: date = None,
        turno: str = "mañana",
        recreo: int = 1,
        **kwargs,
    ) -> Guardia:
        if fecha is None:
            fecha = date.today()

        guardia = Guardia(
            profesor_id=profesor_id,
            zona_id=zona_id,
            fecha=fecha,
            turno=turno,
            recreo=recreo,
            **kwargs,
        )
        session.add(guardia)
        session.commit()
        return guardia

    return _create_guardia


@pytest.fixture
def ausencia_factory(session: Session):
    """
    Factory para crear ausencias en tests.

    Args:
        session: Sesión de base de datos

    Returns:
        Callable: Función para crear ausencias
    """
    from datetime import date, timedelta

    def _create_ausencia(
        profesor_id: int,
        fecha_inicio: date = None,
        fecha_fin: date = None,
        tipo: str = "baja_medica",
        activa: bool = True,
        **kwargs,
    ) -> Ausencia:
        if fecha_inicio is None:
            fecha_inicio = date.today()
        if fecha_fin is None:
            fecha_fin = fecha_inicio + timedelta(days=3)

        ausencia = Ausencia(
            profesor_id=profesor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo=tipo,
            activa=activa,
            **kwargs,
        )
        session.add(ausencia)
        session.commit()
        return ausencia

    return _create_ausencia


# ============================================================================
# FIXTURES DE UTILIDADES
# ============================================================================


@pytest.fixture
def mock_session(mocker):
    """
    Mock de sesión de base de datos.

    Útil para tests que no necesitan base de datos real.

    Args:
        mocker: pytest-mock mocker

    Returns:
        Mock: Mock de Session
    """
    return mocker.MagicMock(spec=Session)


@pytest.fixture
def sample_dates():
    """
    Fechas de ejemplo para tests.

    Returns:
        dict: Diccionario con fechas útiles
    """
    from datetime import date, timedelta

    today = date.today()
    return {
        "today": today,
        "yesterday": today - timedelta(days=1),
        "tomorrow": today + timedelta(days=1),
        "next_week": today + timedelta(days=7),
        "last_week": today - timedelta(days=7),
        "next_month": today + timedelta(days=30),
    }


# ============================================================================
# HOOKS DE PYTEST
# ============================================================================


def pytest_configure(config):
    """
    Configuración inicial de pytest.

    Se ejecuta antes de todos los tests.
    """
    # Agregar markers personalizados
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "ui: UI tests")
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "db: Database tests")


# ============================================================================
# FIXTURES PARA TESTS DE USE CASES Y DOMAIN SERVICES
# ============================================================================


@pytest.fixture
def configuracion_base(session: Session):
    """
    Fixture de configuración básica para tests.

    Returns:
        Configuracion: Configuración con datos mínimos
    """
    import json
    from datetime import date, time

    from models.models import Configuracion

    config = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(12, 0),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 0),
        algoritmo_asignacion="v2.9",
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
        activar_festivos_automaticos=True,
        recreos_config=json.dumps([
            {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "11:00"},
            {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:00"},
            {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:00"},
            {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "17:00"},
        ]),
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def profesores_variados(session: Session):
    """
    Fixture con varios profesores de diferentes tipos.

    Returns:
        List[Profesor]: Lista de profesores variados
    """
    from datetime import date

    profesores = [
        # Profesor jornada completa
        Profesor(
            nombre_completo="García López, María",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="completo",
            activo=True,
            fecha_inicio_guardias=date(2024, 9, 1),
            horas_manana=12.5,
            horas_tarde=12.5
        ),
        # Profesor media jornada mañana
        Profesor(
            nombre_completo="Martínez Ruiz, Juan",
            horas_contrato=12.5,
            porcentaje_jornada=50.0,
            turno="mañana",
            activo=True,
            fecha_inicio_guardias=date(2024, 9, 1),
            horas_manana=12.5,
            horas_tarde=0
        ),
        # Profesor jornada completa tarde
        Profesor(
            nombre_completo="Sánchez Pérez, Ana",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="tarde",
            activo=True,
            fecha_inicio_guardias=date(2024, 9, 1),
            horas_manana=0,
            horas_tarde=25.0
        ),
        # Profesor turno mixto
        Profesor(
            nombre_completo="Rodríguez Gómez, Carlos",
            horas_contrato=20.0,
            porcentaje_jornada=80.0,
            turno="mixto",
            activo=True,
            fecha_inicio_guardias=date(2024, 9, 1),
            horas_manana=10.0,
            horas_tarde=10.0
        ),
    ]

    for prof in profesores:
        session.add(prof)
    session.commit()

    return profesores


@pytest.fixture
def zona_patio(session: Session):
    """
    Fixture de zona de patio básica.

    Returns:
        Zona: Zona de patio
    """
    zona = Zona(
        nombre_zona="Patio Principal",
        descripcion="Zona central del patio"
    )
    session.add(zona)
    session.commit()
    return zona


def pytest_collection_modifyitems(config, items):
    """
    Modificar items de tests recolectados.

    Agrega markers automáticamente basándose en nombres.
    """
    for item in items:
        # Marcar tests de UI
        if "ui" in item.nodeid or "widget" in item.nodeid or "form" in item.nodeid:
            item.add_marker(pytest.mark.ui)

        # Marcar tests de DB
        if "db" in item.nodeid or "session" in item.keywords:
            item.add_marker(pytest.mark.db)

        # Marcar tests de integración
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        else:
            # Por defecto, marcar como unit
            item.add_marker(pytest.mark.unit)
