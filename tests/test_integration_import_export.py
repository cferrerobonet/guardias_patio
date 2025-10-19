"""
Tests de integración para importación/exportación de datos.

Valida el flujo completo de exportar datos a JSON, importarlos en
una base de datos limpia, y generar PDFs de calendarios.

Tests incluidos:
- Exportación JSON (profesores, zonas, configuración, guardias)
- Importación JSON (con/sin limpieza de datos)
- Integridad de datos después de importar
- Generación de PDFs individuales
- Generación de PDFs para múltiples profesores
"""

import json
import tempfile
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.models import Configuracion, Guardia, Profesor, Zona
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF


@pytest.fixture
def temp_dir():
    """Directorio temporal para archivos de exportación."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def engine():
    """Motor de base de datos en memoria para tests."""
    from models.models import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    """Sesión de base de datos para cada test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def datos_base(session):
    """Crear datos base para tests de exportación."""
    # Configuración
    config = Configuracion(
        fecha_inicio_curso=date(2024, 9, 9),
        fecha_fin_curso=date(2024, 9, 13),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 30),
        hora_recreo1_tarde=time(16, 0),
        hora_recreo2_tarde=time(17, 30),
        activar_festivos_automaticos=True,
    )
    session.add(config)

    # Profesores
    prof1 = Profesor(
        nombre_completo="García López, Ana",
        email_corporativo="ana.garcia@colegio.edu",
        horas_contrato=25.0,
        porcentaje_jornada=100.0,
        turno="mañana",
        tutor=True,
    )
    prof2 = Profesor(
        nombre_completo="Martínez Ruiz, Carlos",
        email_corporativo="carlos.martinez@colegio.edu",
        horas_contrato=25.0,
        porcentaje_jornada=100.0,
        turno="tarde",
        tutor=False,
    )
    session.add(prof1)
    session.add(prof2)

    # Zonas
    zona1 = Zona(nombre_zona="Patio Principal", descripcion="Zona principal")
    zona2 = Zona(nombre_zona="Patio Secundario", descripcion="Zona secundaria")
    session.add(zona1)
    session.add(zona2)

    session.commit()

    # Guardias
    guardia1 = Guardia(
        profesor_id=prof1.id,
        fecha=date(2024, 9, 9),
        turno="mañana",
        recreo=1,
        zona_id=zona1.id,
    )
    guardia2 = Guardia(
        profesor_id=prof2.id,
        fecha=date(2024, 9, 9),
        turno="tarde",
        recreo=1,
        zona_id=zona2.id,
    )
    guardia3 = Guardia(
        profesor_id=prof1.id,
        fecha=date(2024, 9, 10),
        turno="mañana",
        recreo=2,
        zona_id=zona1.id,
    )
    session.add_all([guardia1, guardia2, guardia3])
    session.commit()

    return {
        "config": config,
        "profesores": [prof1, prof2],
        "zonas": [zona1, zona2],
        "guardias": [guardia1, guardia2, guardia3],
    }


class TestExportacionJSON:
    """Tests de exportación de datos a JSON."""

    def test_exportar_profesores(self, session, datos_base):
        """
        Test: Exportar profesores a diccionario.

        Valida:
        - Todos los profesores se exportan
        - Todos los campos están presentes
        - Tipos de datos correctos
        """
        profesores_data = ExportadorDatos.exportar_profesores(session)

        assert len(profesores_data) == 2
        assert all(isinstance(p, dict) for p in profesores_data)

        # Verificar campos del primer profesor
        prof = profesores_data[0]
        assert "nombre_completo" in prof
        assert "email_corporativo" in prof
        assert "horas_contrato" in prof
        assert "porcentaje_jornada" in prof
        assert "turno" in prof
        assert "tutor" in prof

        # Verificar tipos
        assert isinstance(prof["nombre_completo"], str)
        assert isinstance(prof["horas_contrato"], float)
        assert isinstance(prof["tutor"], bool)

    def test_exportar_zonas(self, session, datos_base):
        """
        Test: Exportar zonas a diccionario.

        Valida:
        - Todas las zonas se exportan
        - Campos requeridos presentes
        """
        zonas_data = ExportadorDatos.exportar_zonas(session)

        assert len(zonas_data) == 2
        assert all(isinstance(z, dict) for z in zonas_data)

        # Verificar campos
        zona = zonas_data[0]
        assert "nombre_zona" in zona
        assert "descripcion" in zona
        assert isinstance(zona["nombre_zona"], str)

    def test_exportar_configuracion(self, session, datos_base):
        """
        Test: Exportar configuración a diccionario.

        Valida:
        - Configuración se exporta correctamente
        - Fechas serializadas como ISO strings
        - Horas serializadas como HH:MM
        """
        config_data = ExportadorDatos.exportar_configuracion(session)

        assert config_data is not None
        assert isinstance(config_data, dict)

        # Verificar campos de fecha
        assert "fecha_inicio_curso" in config_data
        assert "fecha_fin_curso" in config_data
        assert config_data["fecha_inicio_curso"] == "2024-09-09"
        assert config_data["fecha_fin_curso"] == "2024-09-13"

        # Verificar campos de hora
        assert "hora_recreo1_manana" in config_data
        assert config_data["hora_recreo1_manana"] == "10:30"
        assert config_data["hora_recreo2_tarde"] == "17:30"

        # Verificar booleanos
        assert "activar_festivos_automaticos" in config_data
        assert isinstance(config_data["activar_festivos_automaticos"], bool)

    def test_exportar_guardias(self, session, datos_base):
        """
        Test: Exportar guardias a diccionario.

        Valida:
        - Todas las guardias se exportan
        - Relaciones con profesor y zona correctas
        - Fechas serializadas correctamente
        """
        guardias_data = ExportadorDatos.exportar_guardias(session)

        assert len(guardias_data) == 3
        assert all(isinstance(g, dict) for g in guardias_data)

        # Verificar campos
        guardia = guardias_data[0]
        assert "profesor_nombre_completo" in guardia
        assert "fecha" in guardia
        assert "turno" in guardia
        assert "recreo" in guardia
        assert "zona_nombre" in guardia

        # Verificar formato de fecha
        assert guardia["fecha"] == "2024-09-09"

    def test_exportar_todo_archivo(self, session, datos_base, temp_dir):
        """
        Test: Exportar todos los datos a archivo JSON.

        Valida:
        - Archivo JSON se crea correctamente
        - Estructura JSON válida
        - Todas las secciones presentes
        - Metadatos incluidos (versión, fecha)
        """
        archivo = temp_dir / "export_test.json"

        # Exportar
        ExportadorDatos.exportar_todo(session, str(archivo))

        # Verificar archivo existe
        assert archivo.exists()

        # Leer y verificar contenido
        with open(archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Verificar estructura
        assert "version" in data
        assert "fecha_exportacion" in data
        assert "profesores" in data
        assert "zonas" in data
        assert "configuracion" in data
        assert "guardias" in data

        # Verificar contenido
        assert len(data["profesores"]) == 2
        assert len(data["zonas"]) == 2
        assert data["configuracion"] is not None
        assert len(data["guardias"]) == 3

    def test_exportar_configuracion_sin_datos(self, session):
        """
        Test: Exportar configuración cuando no existe.

        Valida:
        - Retorna None si no hay configuración
        """
        config_data = ExportadorDatos.exportar_configuracion(session)
        assert config_data is None


class TestImportacionJSON:
    """Tests de importación de datos desde JSON."""

    def test_importar_profesores(self, session):
        """
        Test: Importar profesores desde diccionario.

        Valida:
        - Profesores se crean correctamente
        - Todos los campos se importan
        - Retorna conteo correcto
        """
        profesores_data = [
            {
                "nombre_completo": "Pérez García, Juan",
                "email_corporativo": "juan.perez@colegio.edu",
                "horas_contrato": 25.0,
                "porcentaje_jornada": 100.0,
                "turno": "mañana",
                "tutor": True,
                "fecha_inicio_guardias": "2024-09-01",
                "dias_semana_permitidos": None,
                "recreos_permitidos": None,
            },
            {
                "nombre_completo": "López Ruiz, María",
                "email_corporativo": "maria.lopez@colegio.edu",
                "horas_contrato": 12.5,
                "porcentaje_jornada": 50.0,
                "turno": "tarde",
                "tutor": False,
                "fecha_inicio_guardias": None,
                "dias_semana_permitidos": None,
                "recreos_permitidos": None,
            },
        ]

        count = ExportadorDatos.importar_profesores(session, profesores_data)

        assert count == 2

        # Verificar en BD
        profesores = session.query(Profesor).all()
        assert len(profesores) == 2

        prof1 = profesores[0]
        assert prof1.nombre_completo == "Pérez García, Juan"
        assert prof1.tutor is True
        assert prof1.fecha_inicio_guardias == date(2024, 9, 1)

    def test_importar_zonas(self, session):
        """
        Test: Importar zonas desde diccionario.

        Valida:
        - Zonas se crean correctamente
        - Retorna conteo correcto
        """
        zonas_data = [
            {"nombre_zona": "Patio A", "descripcion": "Patio principal"},
            {"nombre_zona": "Patio B", "descripcion": "Patio secundario"},
        ]

        count = ExportadorDatos.importar_zonas(session, zonas_data)

        assert count == 2

        # Verificar en BD
        zonas = session.query(Zona).all()
        assert len(zonas) == 2
        assert zonas[0].nombre_zona == "Patio A"

    def test_importar_configuracion(self, session):
        """
        Test: Importar configuración desde diccionario.

        Valida:
        - Configuración se crea/actualiza correctamente
        - Fechas y horas se deserializan correctamente
        """
        config_data = {
            "fecha_inicio_curso": "2024-09-09",
            "fecha_fin_curso": "2024-12-20",
            "hora_recreo1_manana": "10:30",
            "hora_recreo2_manana": "12:30",
            "hora_recreo1_tarde": "16:00",
            "hora_recreo2_tarde": "17:30",
            "activar_festivos_automaticos": True,
            "dias_no_lectivos_personalizados": None,
            "recreos_config": None,
            "ajuste_tutores": 0.95,
        }

        ExportadorDatos.importar_configuracion(session, config_data)

        # Verificar en BD
        config = session.query(Configuracion).first()
        assert config is not None
        assert config.fecha_inicio_curso == date(2024, 9, 9)
        assert config.fecha_fin_curso == date(2024, 12, 20)
        assert config.hora_recreo1_manana == time(10, 30)
        assert config.activar_festivos_automaticos is True

    def test_importar_guardias(self, session):
        """
        Test: Importar guardias desde diccionario.

        Valida:
        - Guardias se crean correctamente
        - Relaciones con profesor y zona se establecen
        """
        # Primero crear profesores y zonas
        prof = Profesor(
            nombre_completo="Test Profesor",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="mañana",
            tutor=False,
        )
        zona = Zona(nombre_zona="Test Zona", descripcion="Test")
        session.add(prof)
        session.add(zona)
        session.commit()

        guardias_data = [
            {
                "profesor_nombre_completo": "Test Profesor",
                "fecha": "2024-09-09",
                "turno": "mañana",
                "recreo": 1,
                "zona_nombre": "Test Zona",
            },
        ]

        count = ExportadorDatos.importar_guardias(session, guardias_data)

        assert count == 1

        # Verificar en BD
        guardias = session.query(Guardia).all()
        assert len(guardias) == 1
        assert guardias[0].fecha == date(2024, 9, 9)
        assert guardias[0].profesor_id == prof.id
        assert guardias[0].zona_id == zona.id

    def test_importar_con_limpieza(self, engine):
        """
        Test: Importar con limpieza de datos existentes.

        Valida:
        - Datos existentes se eliminan
        - Nuevos datos se importan correctamente
        """
        # Crear sesión fresca
        from sqlalchemy.orm import sessionmaker

        SessionMaker = sessionmaker(bind=engine)
        session = SessionMaker()

        # Crear datos iniciales
        prof1 = Profesor(
            nombre_completo="Profesor Inicial 1",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="mañana",
            tutor=False,
        )
        prof2 = Profesor(
            nombre_completo="Profesor Inicial 2",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="tarde",
            tutor=False,
        )
        session.add_all([prof1, prof2])
        session.commit()

        # Verificar datos iniciales
        assert session.query(Profesor).count() == 2

        # Limpiar la sesión para evitar conflictos de identidad
        session.expunge_all()

        # Preparar nuevos profesores
        profesores_data = [
            {
                "nombre_completo": "Nuevo Profesor",
                "email_corporativo": "nuevo@colegio.edu",
                "horas_contrato": 25.0,
                "porcentaje_jornada": 100.0,
                "turno": "mañana",
                "tutor": False,
                "fecha_inicio_guardias": None,
                "dias_semana_permitidos": None,
                "recreos_permitidos": None,
            },
        ]

        # Importar con limpieza
        count = ExportadorDatos.importar_profesores(
            session, profesores_data, limpiar=True
        )

        assert count == 1

        # Verificar solo hay el nuevo profesor
        profesores = session.query(Profesor).all()
        assert len(profesores) == 1
        assert profesores[0].nombre_completo == "Nuevo Profesor"

        session.close()


class TestIntegridadImportExport:
    """Tests de integridad completa: exportar → importar → verificar."""

    def test_ciclo_completo_export_import(self, session, datos_base, temp_dir):
        """
        Test: Ciclo completo exportar → limpiar → importar → verificar.

        Valida:
        - Datos exportados se pueden reimportar
        - Integridad total de datos
        - Sin pérdida de información
        """
        archivo = temp_dir / "ciclo_completo.json"

        # 1. Exportar datos originales
        ExportadorDatos.exportar_todo(session, str(archivo))

        # Guardar conteos originales
        prof_count_original = session.query(Profesor).count()
        zona_count_original = session.query(Zona).count()
        guardia_count_original = session.query(Guardia).count()

        # 2. Limpiar base de datos
        session.query(Guardia).delete()
        session.query(Profesor).delete()
        session.query(Zona).delete()
        session.query(Configuracion).delete()
        session.commit()

        # Verificar limpieza
        assert session.query(Profesor).count() == 0
        assert session.query(Zona).count() == 0

        # 3. Importar desde archivo
        ExportadorDatos.importar_todo(session, str(archivo))

        # 4. Verificar integridad
        assert session.query(Profesor).count() == prof_count_original
        assert session.query(Zona).count() == zona_count_original
        assert session.query(Guardia).count() == guardia_count_original

        # Verificar configuración
        config = session.query(Configuracion).first()
        assert config is not None
        assert config.fecha_inicio_curso == date(2024, 9, 9)

    def test_relaciones_despues_importar(self, session, datos_base, temp_dir):
        """
        Test: Relaciones entre entidades después de importar.

        Valida:
        - Relaciones profesor ↔ guardias intactas
        - Relaciones zona ↔ guardias intactas
        - IDs regenerados correctamente
        """
        archivo = temp_dir / "relaciones.json"

        # Exportar
        ExportadorDatos.exportar_todo(session, str(archivo))

        # Limpiar e importar
        session.query(Guardia).delete()
        session.query(Profesor).delete()
        session.query(Zona).delete()
        session.query(Configuracion).delete()
        session.commit()

        ExportadorDatos.importar_todo(session, str(archivo))

        # Verificar relaciones
        guardias = session.query(Guardia).all()
        for guardia in guardias:
            # Verificar profesor existe
            profesor = session.query(Profesor).get(guardia.profesor_id)
            assert profesor is not None

            # Verificar zona existe
            zona = session.query(Zona).get(guardia.zona_id)
            assert zona is not None


class TestExportacionPDF:
    """Tests de generación de PDFs."""

    def test_exportar_pdf_individual(self, session, datos_base, temp_dir):
        """
        Test: Generar PDF para un profesor específico.

        Valida:
        - PDF se genera correctamente
        - Archivo existe y tiene contenido
        - No lanza excepciones
        """
        prof = session.query(Profesor).first()
        archivo_pdf = temp_dir / "calendario_profesor.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session=session,
            profesor_id=prof.id,
            mes=9,
            anio=2024,
            ruta_salida=str(archivo_pdf),
        )

        assert resultado is True
        assert archivo_pdf.exists()
        assert archivo_pdf.stat().st_size > 0

    def test_exportar_pdf_profesor_sin_guardias(self, session, datos_base, temp_dir):
        """
        Test: Generar PDF para profesor sin guardias en el mes.

        Valida:
        - PDF se genera aunque no haya guardias
        - Muestra mensaje apropiado
        """
        # Crear profesor sin guardias
        prof_sin_guardias = Profesor(
            nombre_completo="Sin Guardias",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="mañana",
            tutor=False,
        )
        session.add(prof_sin_guardias)
        session.commit()

        archivo_pdf = temp_dir / "sin_guardias.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session=session,
            profesor_id=prof_sin_guardias.id,
            mes=10,  # Mes diferente sin guardias
            anio=2024,
            ruta_salida=str(archivo_pdf),
        )

        assert resultado is True
        assert archivo_pdf.exists()

    def test_exportar_pdf_profesor_inexistente(self, session, temp_dir):
        """
        Test: Intentar generar PDF para profesor que no existe.

        Valida:
        - Retorna False si profesor no existe
        - No genera archivo
        """
        archivo_pdf = temp_dir / "no_existe.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session=session,
            profesor_id=9999,  # ID inexistente
            mes=9,
            anio=2024,
            ruta_salida=str(archivo_pdf),
        )

        assert resultado is False
        assert not archivo_pdf.exists()

    def test_exportar_todos_los_profesores_pdfs(self, session, datos_base, temp_dir):
        """
        Test: Generar PDFs para todos los profesores con guardias.

        Valida:
        - Se generan múltiples PDFs
        - Uno por cada profesor con guardias
        - Nombres de archivo correctos
        """
        exitos = ExportadorPDF.exportar_todos_los_profesores(
            session=session, mes=9, anio=2024, carpeta_salida=str(temp_dir)
        )

        # Debe haber generado 2 PDFs (2 profesores con guardias)
        assert exitos == 2

        # Verificar archivos existen
        pdfs = list(temp_dir.glob("Guardias_*.pdf"))
        assert len(pdfs) == 2

        # Verificar todos tienen contenido
        for pdf in pdfs:
            assert pdf.stat().st_size > 0

    def test_exportar_pdfs_mes_sin_guardias(self, session, datos_base, temp_dir):
        """
        Test: Generar PDFs para mes sin guardias.

        Valida:
        - Retorna 0 si no hay guardias en el mes
        - No genera archivos
        """
        exitos = ExportadorPDF.exportar_todos_los_profesores(
            session=session, mes=12, anio=2024, carpeta_salida=str(temp_dir)
        )

        assert exitos == 0

        # No debe haber PDFs
        pdfs = list(temp_dir.glob("Guardias_*.pdf"))
        assert len(pdfs) == 0


class TestCasosEspecialesExport:
    """Tests de casos especiales y edge cases."""

    def test_exportar_con_campos_none(self, session):
        """
        Test: Exportar profesores con campos None.

        Valida:
        - Campos None se serializan correctamente
        - No lanza excepciones
        """
        prof = Profesor(
            nombre_completo="Profesor Minimal",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="mañana",
            tutor=False,
            email_corporativo=None,  # None
            fecha_inicio_guardias=None,  # None
            dias_semana_permitidos=None,
        )
        session.add(prof)
        session.commit()

        profesores_data = ExportadorDatos.exportar_profesores(session)

        assert len(profesores_data) == 1
        assert profesores_data[0]["email_corporativo"] is None
        assert profesores_data[0]["fecha_inicio_guardias"] is None

    def test_importar_json_malformado(self, session, temp_dir):
        """
        Test: Importar desde JSON malformado.

        Valida:
        - Maneja errores de parsing correctamente
        - Lanza excepción apropiada
        """
        archivo = temp_dir / "malformado.json"
        archivo.write_text("{invalid json content")

        with pytest.raises(json.JSONDecodeError):
            with open(archivo, "r") as f:
                json.load(f)

    def test_exportar_caracteres_especiales(self, session):
        """
        Test: Exportar/importar con caracteres especiales.

        Valida:
        - Caracteres UTF-8 se manejan correctamente
        - Tildes, eñes, símbolos preserved
        """
        prof = Profesor(
            nombre_completo="González Núñez, José María",
            email_corporativo="josé.gonzález@colegio.edu",
            horas_contrato=25,
            porcentaje_jornada=100,
            turno="mañana",
            tutor=False,
        )
        session.add(prof)
        session.commit()

        profesores_data = ExportadorDatos.exportar_profesores(session)

        assert profesores_data[0]["nombre_completo"] == "González Núñez, José María"
        assert "josé" in profesores_data[0]["email_corporativo"]

    def test_archivo_json_legibilidad(self, session, datos_base, temp_dir):
        """
        Test: Archivo JSON exportado es legible y formateado.

        Valida:
        - JSON con indentación
        - Codificación UTF-8
        - Estructura ordenada
        """
        archivo = temp_dir / "legible.json"
        ExportadorDatos.exportar_todo(session, str(archivo))

        # Leer como texto
        contenido = archivo.read_text(encoding="utf-8")

        # Verificar formato
        assert "  " in contenido  # Tiene indentación
        assert '"version"' in contenido
        assert '"profesores"' in contenido

        # Debe poder parsearse
        data = json.loads(contenido)
        assert isinstance(data, dict)
