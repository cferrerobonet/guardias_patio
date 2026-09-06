"""
Configuración compartida para tests con pytest.

Este módulo contiene fixtures comunes y configuración
para todos los tests del proyecto.
"""

import os
import sys
from pathlib import Path
from typing import Generator

# La API exige una clave para firmar los tokens y, sin ella, `api.auth` lanza al
# importarse: dos módulos de tests fallaban en la fase de colección y tumbaban la
# suite entera (QA-001). Se fija aquí, antes de importar nada, y sin pisar la del
# entorno si ya viene puesta.
os.environ.setdefault("GUARDIAS_API_SECRET_KEY", "clave-solo-para-tests")

import pytest
from PyQt6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Insertar raíz del proyecto y src en sys.path para imports
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from infrastructure.database.models import Ausencia, Base, Guardia, Profesor, Zona  # noqa: E402

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
    session.close()  # Cerrar sesión
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

    from infrastructure.database.models import Configuracion

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
        recreos_config=json.dumps(
            [
                {"id": 1, "etiqueta": "Recreo 1 Mañana", "turno": "mañana", "hora": "11:00"},
                {"id": 2, "etiqueta": "Recreo 2 Mañana", "turno": "mañana", "hora": "12:00"},
                {"id": 3, "etiqueta": "Recreo 1 Tarde", "turno": "tarde", "hora": "16:00"},
                {"id": 4, "etiqueta": "Recreo 2 Tarde", "turno": "tarde", "hora": "17:00"},
            ]
        ),
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
            horas_tarde=12.5,
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
            horas_tarde=0,
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
            horas_tarde=25.0,
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
            horas_tarde=10.0,
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
    zona = Zona(nombre_zona="Patio Principal", descripcion="Zona central del patio")
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


# ============================================================================
# GUARDA CONTRA DIÁLOGOS MODALES (QA-008)
# ============================================================================


class DialogoModalMostrado:
    """Registro de un diálogo que la UI intentó abrir durante un test."""

    def __init__(self, clase: str, titulo: str, texto: str):
        self.clase = clase
        self.titulo = titulo
        self.texto = texto

    def __repr__(self) -> str:
        return f"<{self.clase} {self.titulo!r}: {self.texto[:60]!r}>"


@pytest.fixture(autouse=True)
def dialogos_modales(request):
    """
    Impide que un diálogo modal bloquee la suite indefinidamente.

    `QMessageBox.exec()` y `QDialog.exec()` detienen el hilo hasta que alguien
    pulsa un botón. En una ejecución desatendida no hay nadie, así que el test
    se cuelga para siempre y ni pytest-timeout lo rescata: su manejador de
    señales no llega a ejecutarse mientras Qt está dentro de su bucle de
    eventos en C++.

    Esta fixture sustituye ambos métodos por una respuesta inmediata y segura,
    y deja constancia de cada diálogo para poder afirmar sobre él:

        def test_avisa_al_borrar(dialogos_modales, ...):
            form.eliminar()
            assert any("eliminar" in d.texto.lower() for d in dialogos_modales)

    La respuesta es el botón por defecto del propio diálogo; si no lo tiene, se
    elige la opción más conservadora disponible (No, luego Cancel, luego Ok).

    Para probar el comportamiento modal real, marcar el test con
    `@pytest.mark.modales_reales`.
    """
    mostrados: list = []

    if "modales_reales" in request.keywords:
        yield mostrados
        return

    from PyQt6.QtWidgets import QDialog, QMessageBox

    exec_messagebox_original = QMessageBox.exec
    exec_dialog_original = QDialog.exec

    def _respuesta_segura(caja: "QMessageBox") -> int:
        boton_defecto = caja.defaultButton()
        if boton_defecto is not None:
            return caja.standardButton(boton_defecto)
        disponibles = caja.standardButtons()
        for opcion in (
            QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Close,
            QMessageBox.StandardButton.Ok,
        ):
            if disponibles & opcion:
                return opcion
        return QMessageBox.StandardButton.NoButton

    def _exec_messagebox(self):
        mostrados.append(DialogoModalMostrado("QMessageBox", self.windowTitle(), self.text()))
        return _respuesta_segura(self)

    def _exec_dialog(self):
        mostrados.append(
            DialogoModalMostrado(type(self).__name__, self.windowTitle(), "")
        )
        return QDialog.DialogCode.Rejected

    # Los métodos estáticos de conveniencia (information, question, warning...) no
    # pasan por QMessageBox.exec: abren su propio bucle modal en C++ y cuelgan la
    # suite igual que aquél. Se sustituyen por la respuesta por defecto de cada uno.
    ESTATICOS_POR_DEFECTO = {
        "information": QMessageBox.StandardButton.Ok,
        "warning": QMessageBox.StandardButton.Ok,
        "critical": QMessageBox.StandardButton.Ok,
        "about": None,
        "aboutQt": None,
        "question": QMessageBox.StandardButton.No,
    }
    estaticos_originales = {
        nombre: getattr(QMessageBox, nombre) for nombre in ESTATICOS_POR_DEFECTO
    }

    def _hacer_estatico(nombre, respuesta):
        def _estatico(parent=None, title="", text="", *args, **kwargs):
            mostrados.append(DialogoModalMostrado(f"QMessageBox.{nombre}", title, text))
            if respuesta is None:
                return None
            # Si el llamante ofrece botones concretos, respetar el que pida por defecto.
            if args and isinstance(args[0], QMessageBox.StandardButton):
                botones = args[0]
                for opcion in (
                    QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Ok,
                ):
                    if botones & opcion:
                        return opcion
            return respuesta

        return staticmethod(_estatico)

    QMessageBox.exec = _exec_messagebox
    QDialog.exec = _exec_dialog
    for nombre, respuesta in ESTATICOS_POR_DEFECTO.items():
        setattr(QMessageBox, nombre, _hacer_estatico(nombre, respuesta))
    try:
        yield mostrados
    finally:
        QMessageBox.exec = exec_messagebox_original
        QDialog.exec = exec_dialog_original
        for nombre, original in estaticos_originales.items():
            setattr(QMessageBox, nombre, original)


@pytest.fixture(autouse=True)
def _cache_limpio():
    """
    Vacía la caché de consultas antes de cada test.

    Varios casos de uso cachean su resultado durante minutos en una caché global
    del proceso, que sobrevive de un test al siguiente. Sin esta limpieza, un test
    recibe el resultado calculado por otro.

    La causa original —la clave incluía la dirección de memoria del objeto y
    Python las reutiliza— se corrigió en v5.63.0 (ESC-007), pero la caché sigue
    siendo global y aislar cada test sigue siendo lo correcto.
    """
    from utils.cache import clear_all_cache

    clear_all_cache()
    yield
    clear_all_cache()


@pytest.fixture(autouse=True)
def sin_smtp_de_verdad(request, monkeypatch):
    """Impide que un test acabe hablando con el servidor de correo real.

    Este equipo tiene credenciales SMTP válidas en `smtp_config.json`, así que
    un test que no sustituya el servicio sale a internet y manda correo de
    verdad —pasó al escribir los tests de FUN-006—. Aquí `smtplib.SMTP` falla
    con un mensaje claro salvo que el test se marque `smtp_real`.
    """
    import smtplib

    if request.node.get_closest_marker("smtp_real"):
        return

    def prohibido(*args, **kwargs):
        raise AssertionError(
            "Un test ha intentado abrir una conexión SMTP real. Sustituye "
            "`smtplib.SMTP` o pasa un servicio falso."
        )

    monkeypatch.setattr(smtplib, "SMTP", prohibido)
    monkeypatch.setattr(smtplib, "SMTP_SSL", prohibido)
