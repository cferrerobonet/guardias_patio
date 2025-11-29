"""Tests para el módulo exportador_pdf."""

import sys
from datetime import date, time
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Añadir src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.models import Base, Configuracion, Guardia, Profesor, Zona
from services.exportador_pdf import ExportadorPDF


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
def config_basica(session):
    """Crea una configuración básica del curso."""
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2026, 6, 30),
        hora_recreo1_manana=time(10, 30),
        hora_recreo2_manana=time(12, 0),
    )
    session.add(config)
    session.commit()
    return config


@pytest.fixture
def profesores_con_guardias(session, config_basica):
    """Crea profesores y zonas con guardias asignadas."""
    # Crear profesores
    prof1 = Profesor(
        nombre_completo="GARCÍA, ANA",
        horas_contrato=30.0,
        porcentaje_jornada=1.0,
        turno="mañana",
        tutor=True,
    )
    prof2 = Profesor(
        nombre_completo="MARTÍNEZ, LUIS",
        horas_contrato=30.0,
        porcentaje_jornada=1.0,
        turno="tarde",
        tutor=False,
    )
    prof3 = Profesor(
        nombre_completo="LÓPEZ, CARMEN",
        horas_contrato=15.0,
        porcentaje_jornada=0.5,
        turno="mañana",
        tutor=False,
    )
    session.add_all([prof1, prof2, prof3])

    # Crear zonas
    zona1 = Zona(nombre_zona="Patio Principal", descripcion="Patio grande")
    zona2 = Zona(nombre_zona="Patio Infantil", descripcion="Zona pequeños")
    session.add_all([zona1, zona2])
    session.commit()

    # Crear guardias para octubre 2025
    guardias = [
        # Prof1 - varias guardias
        Guardia(
            profesor_id=prof1.id,
            fecha=date(2025, 10, 1),
            turno="mañana",
            recreo=1,
            zona_id=zona1.id,
        ),
        Guardia(
            profesor_id=prof1.id,
            fecha=date(2025, 10, 3),
            turno="mañana",
            recreo=1,
            zona_id=zona2.id,
        ),
        Guardia(
            profesor_id=prof1.id,
            fecha=date(2025, 10, 3),
            turno="mañana",
            recreo=2,
            zona_id=zona1.id,
        ),
        Guardia(
            profesor_id=prof1.id,
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona1.id,
        ),
        # Prof2 - guardias de tarde
        Guardia(
            profesor_id=prof2.id,
            fecha=date(2025, 10, 2),
            turno="tarde",
            recreo=1,
            zona_id=zona1.id,
        ),
        Guardia(
            profesor_id=prof2.id,
            fecha=date(2025, 10, 8),
            turno="tarde",
            recreo=1,
            zona_id=zona2.id,
        ),
    ]
    for g in guardias:
        session.add(g)
    session.commit()

    return {"profesores": [prof1, prof2, prof3], "zonas": [zona1, zona2]}


class TestExportarCalendarioProfesor:
    """Tests para exportar_calendario_profesor."""

    def test_exportar_calendario_basico(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta calendario de un profesor con guardias."""
        prof1 = profesores_con_guardias["profesores"][0]
        archivo_salida = tmp_path / "calendario_prof1.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is True
        assert archivo_salida.exists()
        assert archivo_salida.stat().st_size > 0

    def test_exportar_profesor_inexistente(self, session, tmp_path):
        """Intenta exportar calendario de profesor que no existe."""
        archivo_salida = tmp_path / "calendario_inexistente.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, profesor_id=9999, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is False
        assert not archivo_salida.exists()

    def test_exportar_profesor_sin_guardias(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta calendario de profesor sin guardias en el mes."""
        prof3 = profesores_con_guardias["profesores"][2]  # Sin guardias
        archivo_salida = tmp_path / "calendario_sin_guardias.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof3.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is True
        assert archivo_salida.exists()
        # Debe generar PDF con mensaje "No hay guardias"
        assert archivo_salida.stat().st_size > 0

    def test_exportar_diferentes_meses(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta calendarios de diferentes meses."""
        prof1 = profesores_con_guardias["profesores"][0]

        # Octubre tiene guardias
        archivo_oct = tmp_path / "octubre.pdf"
        resultado_oct = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=str(archivo_oct)
        )
        assert resultado_oct is True

        # Noviembre no tiene guardias
        archivo_nov = tmp_path / "noviembre.pdf"
        resultado_nov = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=11, anio=2025, ruta_salida=str(archivo_nov)
        )
        assert resultado_nov is True

    def test_formato_pdf_con_multiple_guardias_mismo_dia(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Verifica que se manejan correctamente múltiples guardias en un día."""
        prof1 = profesores_con_guardias["profesores"][0]
        # Prof1 tiene 2 guardias el día 3 de octubre
        archivo_salida = tmp_path / "multiples_guardias.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is True
        assert archivo_salida.exists()

    def test_error_ruta_invalida(self, session, profesores_con_guardias):
        """Maneja error cuando la ruta de salida es inválida."""
        prof1 = profesores_con_guardias["profesores"][0]
        # Ruta inválida (carpeta que no existe y no puede crearse)
        ruta_invalida = "/ruta/inexistente/no/creada/archivo.pdf"

        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=ruta_invalida
        )

        # Debe manejar el error y retornar False
        assert resultado is False

    def test_guardias_turno_manana_y_tarde(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta calendario con guardias de mañana y tarde."""
        prof1 = profesores_con_guardias["profesores"][0]
        prof2 = profesores_con_guardias["profesores"][1]

        # Prof1 tiene solo mañana
        archivo1 = tmp_path / "solo_manana.pdf"
        resultado1 = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=str(archivo1)
        )

        # Prof2 tiene solo tarde
        archivo2 = tmp_path / "solo_tarde.pdf"
        resultado2 = ExportadorPDF.exportar_calendario_profesor(
            session, prof2.id, mes=10, anio=2025, ruta_salida=str(archivo2)
        )

        assert resultado1 is True
        assert resultado2 is True


class TestExportarTodosLosProfesores:
    """Tests para exportar_todos_los_profesores."""

    def test_exportar_todos_sin_callback(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta PDFs para todos los profesores sin progress_callback."""
        carpeta_salida = tmp_path / "pdfs"

        total = ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_salida)
        )

        # Debe generar PDFs para prof1 y prof2 (tienen guardias)
        assert total == 2
        assert carpeta_salida.exists()

        # Verificar archivos generados
        archivos = list(carpeta_salida.glob("*.pdf"))
        assert len(archivos) == 2

    def test_exportar_todos_con_progress_callback(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta PDFs con callback de progreso."""
        carpeta_salida = tmp_path / "pdfs_con_progreso"

        progreso_llamadas = []

        def callback_progreso(porcentaje: int, mensaje: str):
            progreso_llamadas.append((porcentaje, mensaje))

        total = ExportadorPDF.exportar_todos_los_profesores(
            session,
            mes=10,
            anio=2025,
            carpeta_salida=str(carpeta_salida),
            progress_callback=callback_progreso,
        )

        assert total == 2
        # Debe haber varias llamadas al callback
        assert len(progreso_llamadas) > 0
        # Primera llamada debe ser 0%
        assert progreso_llamadas[0][0] == 0
        # Última llamada debe ser 100%
        assert progreso_llamadas[-1][0] == 100

    def test_exportar_todos_mes_sin_guardias(self, session, tmp_path):
        """Exporta cuando no hay guardias en el mes."""
        # Crear profesor sin guardias
        prof = Profesor(
            nombre_completo="SIN, GUARDIAS",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        session.add(prof)
        session.commit()

        carpeta_salida = tmp_path / "sin_guardias"

        total = ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_salida)
        )

        assert total == 0
        assert carpeta_salida.exists()

    def test_exportar_todos_crea_carpeta_si_no_existe(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Crea la carpeta de salida si no existe."""
        carpeta_salida = tmp_path / "nueva" / "carpeta" / "pdfs"
        # Carpeta no existe aún

        total = ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_salida)
        )

        assert total == 2
        assert carpeta_salida.exists()
        assert carpeta_salida.is_dir()

    def test_exportar_todos_nombres_archivo_seguros(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Genera nombres de archivo seguros (sin espacios, comas)."""
        carpeta_salida = tmp_path / "nombres_seguros"

        ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_salida)
        )

        archivos = list(carpeta_salida.glob("*.pdf"))
        for archivo in archivos:
            # No debe contener espacios ni comas
            assert " " not in archivo.name
            assert "," not in archivo.name
            # Debe contener el mes y año
            assert "_10_2025.pdf" in archivo.name

    def test_callback_con_error_no_interrumpe(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Callback que lanza error no interrumpe la exportación."""
        carpeta_salida = tmp_path / "callback_error"

        def callback_error(porcentaje: int, mensaje: str):
            raise Exception("Error en callback")

        # No debe lanzar excepción
        total = ExportadorPDF.exportar_todos_los_profesores(
            session,
            mes=10,
            anio=2025,
            carpeta_salida=str(carpeta_salida),
            progress_callback=callback_error,
        )

        # Debe completarse exitosamente a pesar del error en callback
        assert total == 2

    def test_exportar_multiples_profesores_diferentes_turnos(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Exporta profesores con diferentes turnos."""
        carpeta_salida = tmp_path / "multiples_turnos"

        total = ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_salida)
        )

        assert total == 2

        # Verificar que se generaron PDFs
        archivos = list(carpeta_salida.glob("*.pdf"))
        assert len(archivos) == 2

        # Los nombres deben contener los apellidos de los profesores
        nombres = [archivo.stem for archivo in archivos]
        assert any("GARCÍA" in nombre or "GARCIA" in nombre for nombre in nombres)
        assert any("MARTÍNEZ" in nombre or "MARTINEZ" in nombre for nombre in nombres)


class TestIntegracionExportadorPDF:
    """Tests de integración para el exportador PDF."""

    def test_ciclo_completo_exportacion(
        self, session, profesores_con_guardias, tmp_path
    ):
        """Test de ciclo completo: crear datos, exportar individual y masivo."""
        prof1 = profesores_con_guardias["profesores"][0]

        # 1. Exportar un profesor individual
        archivo_individual = tmp_path / "individual.pdf"
        resultado1 = ExportadorPDF.exportar_calendario_profesor(
            session, prof1.id, mes=10, anio=2025, ruta_salida=str(archivo_individual)
        )
        assert resultado1 is True

        # 2. Exportar todos los profesores
        carpeta_masiva = tmp_path / "masiva"
        total = ExportadorPDF.exportar_todos_los_profesores(
            session, mes=10, anio=2025, carpeta_salida=str(carpeta_masiva)
        )
        assert total == 2

        # 3. Verificar que ambos métodos funcionaron
        assert archivo_individual.exists()
        assert len(list(carpeta_masiva.glob("*.pdf"))) == 2

    def test_exportar_profesor_con_muchas_guardias(
        self, session, config_basica, tmp_path
    ):
        """Exporta profesor con muchas guardias (stress test)."""
        prof = Profesor(
            nombre_completo="MUCHAS, GUARDIAS",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Test", descripcion="Test")
        session.add_all([prof, zona])
        session.commit()

        # Crear 30 guardias (casi todos los días del mes)
        for dia in range(1, 31):
            try:
                guardia = Guardia(
                    profesor_id=prof.id,
                    fecha=date(2025, 10, dia),
                    turno="mañana",
                    recreo=1,
                    zona_id=zona.id,
                )
                session.add(guardia)
            except ValueError:
                # Día 31 no existe en octubre
                pass
        session.commit()

        archivo_salida = tmp_path / "muchas_guardias.pdf"
        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is True
        assert archivo_salida.exists()
        # PDF debe ser más grande por tener más contenido
        assert archivo_salida.stat().st_size > 4000


class TestCasosEdge:
    """Tests para casos edge y extremos."""

    def test_mes_limites(self, session, config_basica, tmp_path):
        """Exporta calendarios de meses límite (enero y diciembre)."""
        prof = Profesor(
            nombre_completo="TEST, EDGE",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona", descripcion="Test")
        session.add_all([prof, zona])
        session.commit()

        # Guardia en enero
        g1 = Guardia(
            profesor_id=prof.id,
            fecha=date(2025, 1, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        # Guardia en diciembre
        g2 = Guardia(
            profesor_id=prof.id,
            fecha=date(2025, 12, 20),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add_all([g1, g2])
        session.commit()

        # Exportar enero
        archivo_enero = tmp_path / "enero.pdf"
        resultado1 = ExportadorPDF.exportar_calendario_profesor(
            session, prof.id, mes=1, anio=2025, ruta_salida=str(archivo_enero)
        )

        # Exportar diciembre
        archivo_dic = tmp_path / "diciembre.pdf"
        resultado2 = ExportadorPDF.exportar_calendario_profesor(
            session, prof.id, mes=12, anio=2025, ruta_salida=str(archivo_dic)
        )

        assert resultado1 is True
        assert resultado2 is True

    def test_zona_sin_descripcion(self, session, config_basica, tmp_path):
        """Maneja zona sin descripción correctamente."""
        prof = Profesor(
            nombre_completo="TEST, ZONA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        zona = Zona(nombre_zona="Zona Sin Desc", descripcion=None)
        session.add_all([prof, zona])
        session.commit()

        guardia = Guardia(
            profesor_id=prof.id,
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.commit()

        archivo_salida = tmp_path / "zona_sin_desc.pdf"
        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        assert resultado is True

    def test_guardia_sin_zona(self, session, config_basica, tmp_path):
        """Maneja guardia con zona_id que no existe."""
        prof = Profesor(
            nombre_completo="TEST, SIN_ZONA",
            horas_contrato=30.0,
            porcentaje_jornada=1.0,
            turno="mañana",
            tutor=False,
        )
        session.add(prof)
        session.commit()

        # Guardia con zona_id que no existe
        guardia = Guardia(
            profesor_id=prof.id,
            fecha=date(2025, 10, 15),
            turno="mañana",
            recreo=1,
            zona_id=9999,  # ID inexistente
        )
        session.add(guardia)
        session.commit()

        archivo_salida = tmp_path / "sin_zona.pdf"
        resultado = ExportadorPDF.exportar_calendario_profesor(
            session, prof.id, mes=10, anio=2025, ruta_salida=str(archivo_salida)
        )

        # Debe manejar el caso y mostrar "N/A"
        assert resultado is True
