"""Tests para el servicio de exportación e importación de datos."""
import json
import sys
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Base, Configuracion, Guardia, Profesor, Zona
from services.exportador import ExportadorDatos


@pytest.fixture
def session():
    """Crea una sesión de base de datos en memoria para pruebas."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def datos_prueba(session: Session):
    """Crea datos de prueba en la base de datos."""
    # Profesores
    prof1 = Profesor(
        nombre_completo="PÉREZ, JUAN",
        email_corporativo="juan.perez@colegio.edu",
        horas_contrato=25.0,
        porcentaje_jornada=100.0,
        turno="completo",
        tutor=True,
        fecha_inicio_guardias=date(2024, 9, 1),
        dias_semana_permitidos="[0,1,2,3,4]",
        recreos_permitidos="[1,2]",
    )
    prof2 = Profesor(
        nombre_completo="GARCÍA, MARÍA",
        horas_contrato=12.5,
        porcentaje_jornada=50.0,
        turno="mañana",
        tutor=False,
    )
    session.add_all([prof1, prof2])

    # Zonas
    zona1 = Zona(nombre_zona="Patio Principal", descripcion="Zona principal del colegio")
    zona2 = Zona(nombre_zona="Biblioteca", descripcion="Zona de lectura")
    session.add_all([zona1, zona2])

    # Configuración
    config = Configuracion(
        anio_inicio_curso=2024,
        fecha_inicio_curso=date(2024, 9, 1),
        fecha_fin_curso=date(2025, 6, 30),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 30),
        hora_recreo1_tarde=time(15, 30),
        hora_recreo2_tarde=None,
        activar_festivos_automaticos=True,
        dias_no_lectivos_personalizados='["2024-12-25", "2024-12-26"]',
        recreos_config='[{"id": 1, "etiqueta": "Recreo 1"}]',
        ajuste_tutores=1.5,
        ajuste_no_tutores=1.0,
    )
    session.add(config)

    session.commit()

    # Guardias (requiere IDs después del commit)
    guardia1 = Guardia(
        profesor_id=prof1.id,
        fecha=date(2024, 9, 10),
        turno="mañana",
        recreo=1,
        zona_id=zona1.id,
    )
    session.add(guardia1)
    session.commit()

    return {"profesores": [prof1, prof2], "zonas": [zona1, zona2], "config": config}


class TestExportarProfesores:
    """Tests para exportación de profesores."""

    def test_exportar_profesores_completo(self, session: Session, datos_prueba):
        """Exporta profesores con todos los campos."""
        profesores = ExportadorDatos.exportar_profesores(session)

        assert len(profesores) == 2
        assert profesores[0]["nombre_completo"] == "PÉREZ, JUAN"
        assert profesores[0]["email_corporativo"] == "juan.perez@colegio.edu"
        assert profesores[0]["horas_contrato"] == 25.0
        assert profesores[0]["tutor"] is True
        assert profesores[0]["fecha_inicio_guardias"] == "2024-09-01"
        assert profesores[0]["dias_semana_permitidos"] == "[0,1,2,3,4]"

    def test_exportar_profesores_vacio(self, session: Session):
        """Exporta cuando no hay profesores."""
        profesores = ExportadorDatos.exportar_profesores(session)
        assert profesores == []


class TestExportarZonas:
    """Tests para exportación de zonas."""

    def test_exportar_zonas_completo(self, session: Session, datos_prueba):
        """Exporta zonas con todos los campos."""
        zonas = ExportadorDatos.exportar_zonas(session)

        assert len(zonas) == 2
        assert zonas[0]["nombre_zona"] == "Patio Principal"
        assert zonas[0]["descripcion"] == "Zona principal del colegio"

    def test_exportar_zonas_vacio(self, session: Session):
        """Exporta cuando no hay zonas."""
        zonas = ExportadorDatos.exportar_zonas(session)
        assert zonas == []


class TestExportarConfiguracion:
    """Tests para exportación de configuración."""

    def test_exportar_configuracion_completo(self, session: Session, datos_prueba):
        """Exporta configuración con todos los campos."""
        config = ExportadorDatos.exportar_configuracion(session)

        assert config is not None
        assert config["fecha_inicio_curso"] == "2024-09-01"
        assert config["fecha_fin_curso"] == "2025-06-30"
        assert config["hora_recreo1_manana"] == "10:30"
        assert config["hora_recreo2_manana"] == "12:30"
        assert config["hora_recreo1_tarde"] == "15:30"
        assert config["hora_recreo2_tarde"] is None
        assert config["activar_festivos_automaticos"] is True
        assert config["ajuste_tutores"] == 1.5

    def test_exportar_configuracion_vacio(self, session: Session):
        """Exporta cuando no hay configuración."""
        config = ExportadorDatos.exportar_configuracion(session)
        assert config is None


class TestExportarGuardias:
    """Tests para exportación de guardias."""

    def test_exportar_guardias_completo(self, session: Session, datos_prueba):
        """Exporta guardias con referencias a profesor y zona."""
        guardias = ExportadorDatos.exportar_guardias(session)

        assert len(guardias) == 1
        assert guardias[0]["profesor_nombre_completo"] == "PÉREZ, JUAN"
        assert guardias[0]["fecha"] == "2024-09-10"
        assert guardias[0]["turno"] == "mañana"
        assert guardias[0]["recreo"] == 1
        assert guardias[0]["zona_nombre"] == "Patio Principal"


class TestExportarTodo:
    """Tests para exportación completa."""

    def test_exportar_todo_archivo(self, session: Session, datos_prueba, tmp_path):
        """Exporta todos los datos a un archivo JSON."""
        archivo = tmp_path / "export.json"
        ExportadorDatos.exportar_todo(session, archivo)

        assert archivo.exists()

        # Leer y verificar contenido
        with archivo.open("r", encoding="utf-8") as f:
            datos = json.load(f)

        assert "version" in datos
        assert "fecha_exportacion" in datos
        assert len(datos["profesores"]) == 2
        assert len(datos["zonas"]) == 2
        assert datos["configuracion"] is not None
        assert len(datos["guardias"]) == 1


class TestImportarProfesores:
    """Tests para importación de profesores."""

    def test_importar_profesores_nuevos(self, session: Session):
        """Importa profesores a base de datos vacía."""
        datos = [
            {
                "nombre": "Pedro",
                "apellidos": "López",
                "email_corporativo": "pedro@colegio.edu",
                "horas_contrato": 20.0,
                "porcentaje_jornada": 80.0,
                "turno": "mañana",
                "tutor": True,
                "fecha_inicio_guardias": "2024-09-01",
                "dias_semana_permitidos": "[0,1,2]",
                "recreos_permitidos": "[1]",
            }
        ]

        count = ExportadorDatos.importar_profesores(session, datos, limpiar=False)
        assert count == 1

        profesores = session.query(Profesor).all()
        assert len(profesores) == 1
        assert profesores[0].nombre_completo == "López, Pedro"
        assert profesores[0].email_corporativo == "pedro@colegio.edu"
        assert profesores[0].tutor is True

    def test_importar_profesores_limpiar(self, session: Session, datos_prueba):
        """Importa profesores limpiando datos existentes."""
        datos = [
            {
                "nombre": "Nuevo",
                "apellidos": "Profesor",
                "horas_contrato": 15.0,
                "porcentaje_jornada": 60.0,
                "turno": "tarde",
            }
        ]

        # Cerrar la sesión actual y crear una nueva para evitar conflictos
        session.close()
        from database.db_manager import SessionLocal
        new_session = SessionLocal()

        try:
            count = ExportadorDatos.importar_profesores(new_session, datos, limpiar=True)
            assert count == 1

            new_session.expire_all()
            profesores = new_session.query(Profesor).all()
            assert len(profesores) == 1
            assert profesores[0].nombre_completo == "Profesor, Nuevo"
        finally:
            new_session.close()


class TestImportarZonas:
    """Tests para importación de zonas."""

    def test_importar_zonas_nuevas(self, session: Session):
        """Importa zonas a base de datos vacía."""
        datos = [
            {"nombre_zona": "Gimnasio", "descripcion": "Zona deportiva"},
            {"nombre_zona": "Cafetería", "descripcion": None},
        ]

        count = ExportadorDatos.importar_zonas(session, datos, limpiar=False)
        assert count == 2

        zonas = session.query(Zona).all()
        assert len(zonas) == 2
        assert zonas[0].nombre_zona == "Gimnasio"


class TestImportarConfiguracion:
    """Tests para importación de configuración."""

    def test_importar_configuracion_nueva(self, session: Session):
        """Importa configuración a base de datos vacía."""
        datos = {
            "fecha_inicio_curso": "2024-09-01",
            "fecha_fin_curso": "2025-06-30",
            "hora_recreo1_manana": "10:30",
            "hora_recreo2_manana": "12:30",
            "hora_recreo1_tarde": None,
            "hora_recreo2_tarde": None,
            "activar_festivos_automaticos": True,
            "dias_no_lectivos_personalizados": None,
            "recreos_config": None,
            "ajuste_tutores": 1.0,
            "ajuste_no_tutores": 1.0,
        }

        resultado = ExportadorDatos.importar_configuracion(session, datos, limpiar=False)
        assert resultado is True

        config = session.query(Configuracion).first()
        assert config is not None
        assert config.fecha_inicio_curso == date(2024, 9, 1)
        assert config.hora_recreo1_manana == time(10, 30)


class TestImportarTodo:
    """Tests para importación completa."""

    def test_importar_todo_archivo(self, session: Session, tmp_path):
        """Importa todos los datos desde un archivo JSON."""
        # Crear archivo de prueba
        archivo = tmp_path / "import.json"
        datos = {
            "version": "1.0",
            "fecha_exportacion": "2024-10-15",
            "profesores": [
                {
                    "nombre": "Ana",
                    "apellidos": "Martínez",
                    "email_corporativo": "ana@colegio.edu",
                    "horas_contrato": 25.0,
                    "porcentaje_jornada": 100.0,
                    "turno": "completo",
                    "tutor": False,
                    "fecha_inicio_guardias": None,
                    "dias_semana_permitidos": None,
                    "recreos_permitidos": None,
                }
            ],
            "zonas": [{"nombre_zona": "Patio", "descripcion": "Patio principal"}],
            "configuracion": {
                "fecha_inicio_curso": "2024-09-01",
                "fecha_fin_curso": "2025-06-30",
                "hora_recreo1_manana": "10:30",
                "hora_recreo2_manana": "12:30",
                "hora_recreo1_tarde": None,
                "hora_recreo2_tarde": None,
                "activar_festivos_automaticos": True,
                "dias_no_lectivos_personalizados": None,
                "recreos_config": None,
                "ajuste_tutores": 1.0,
                "ajuste_no_tutores": 1.0,
            },
            "guardias": [],
        }

        with archivo.open("w", encoding="utf-8") as f:
            json.dump(datos, f)

        # Importar
        resultado = ExportadorDatos.importar_todo(session, archivo, limpiar=False)

        assert resultado["profesores"] == 1
        assert resultado["zonas"] == 1
        assert resultado["configuracion"] == 1
        assert resultado["guardias"] == 0

        # Verificar datos
        assert session.query(Profesor).count() == 1
        assert session.query(Zona).count() == 1
        assert session.query(Configuracion).count() == 1

    def test_ciclo_exportar_importar(self, session: Session, datos_prueba, tmp_path):
        """Test de ciclo completo: exportar y luego importar."""
        # Exportar
        archivo = tmp_path / "ciclo.json"
        ExportadorDatos.exportar_todo(session, archivo)

        # Limpiar base de datos
        session.query(Guardia).delete()
        session.query(Profesor).delete()
        session.query(Zona).delete()
        session.query(Configuracion).delete()
        session.commit()

        assert session.query(Profesor).count() == 0

        # Importar
        resultado = ExportadorDatos.importar_todo(session, archivo, limpiar=False)

        # Verificar que se restauraron los datos
        assert resultado["profesores"] == 2
        assert resultado["zonas"] == 2
        assert resultado["configuracion"] == 1
        assert resultado["guardias"] == 1

        profesores = session.query(Profesor).all()
        assert len(profesores) == 2
        assert any(p.nombre_completo == "PÉREZ, JUAN" for p in profesores)
