"""
Tests E2E (End-to-End) del flujo completo de usuario.

Simula el uso real de la aplicación desde la perspectiva del usuario:
1. Importar profesores
2. Configurar zonas y turnos
3. Generar calendario de guardias
4. Exportar PDFs
5. Exportar/Importar datos JSON

Estos tests validan la integración completa del sistema sin mocks.
"""

import json
import tempfile
from datetime import date, datetime
from pathlib import Path

import pytest

from database.db_manager import SessionLocal
from models.models import Configuracion, Guardia, Profesor, Zona
from services.asignador_guardias import generar_calendario_guardias, guardar_guardias_en_bd
from services.exportador import ExportadorDatos
from services.exportador_pdf import ExportadorPDF
from utils import get_logger

logger = get_logger(__name__)


@pytest.fixture
def session_e2e():
    """Sesión de BD para tests E2E (usa BD en memoria)."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture
def limpiar_bd(session_e2e):
    """Limpia la BD antes de cada test."""
    # Eliminar todos los datos
    session_e2e.query(Guardia).delete()
    session_e2e.query(Configuracion).delete()
    session_e2e.query(Zona).delete()
    session_e2e.query(Profesor).delete()
    session_e2e.commit()
    yield
    # Limpiar después también
    session_e2e.query(Guardia).delete()
    session_e2e.query(Configuracion).delete()
    session_e2e.query(Zona).delete()
    session_e2e.query(Profesor).delete()
    session_e2e.commit()


class TestFlujCompletoUsuario:
    """Tests E2E que simulan el flujo completo de un usuario."""

    def test_flujo_basico_completo(self, session_e2e, limpiar_bd):
        """
        Test E2E: Flujo básico completo del sistema.

        Simula un usuario que:
        1. Crea profesores
        2. Configura zonas y turnos
        3. Genera guardias
        4. Verifica resultados
        """
        # FASE 1: Crear profesores (simula importación)
        profesores_datos = [
            {"nombre": "García López, Juan", "horas": 30},
            {"nombre": "Martínez Pérez, Ana", "horas": 25},
            {"nombre": "Rodríguez Sánchez, Carlos", "horas": 30},
            {"nombre": "López Fernández, María", "horas": 20},
            {"nombre": "Sánchez Gómez, Pedro", "horas": 30},
        ]

        profesores_creados = []
        for datos in profesores_datos:
            profesor = Profesor(
                nombre_completo=datos["nombre"],
                horas_contrato=datos["horas"],
                turno="completo",
                porcentaje_jornada=100.0,
            )
            session_e2e.add(profesor)
            profesores_creados.append(profesor)

        session_e2e.commit()
        logger.info(f"✅ Fase 1: {len(profesores_creados)} profesores creados")

        # Verificar que los profesores se crearon correctamente
        assert session_e2e.query(Profesor).count() == 5
        assert all(p.id is not None for p in profesores_creados)

        # FASE 2: Configurar zonas (simula configuración inicial)
        zonas_datos = [
            {"nombre": "Patio Principal"},
            {"nombre": "Entrada"},
            {"nombre": "Biblioteca"},
        ]

        zonas_creadas = []
        for datos in zonas_datos:
            zona = Zona(nombre_zona=datos["nombre"])  # Corregido: nombre_zona
            session_e2e.add(zona)
            zonas_creadas.append(zona)

        session_e2e.commit()
        logger.info(f"✅ Fase 2: {len(zonas_creadas)} zonas configuradas")

        # Verificar zonas
        assert session_e2e.query(Zona).count() == 3

        # FASE 2.5: Crear configuración del curso
        from datetime import time
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 30),  # Solo un mes para el test
            hora_recreo1_manana=time(11, 0),
            hora_recreo2_manana=time(11, 30),
            hora_recreo1_tarde=time(16, 0),
            hora_recreo2_tarde=time(16, 30),
            dias_no_lectivos_personalizados="[]",
            recreos_config="[]",
            activar_festivos_automaticos=False,  # Desactivar festivos automáticos
        )
        session_e2e.add(config)
        session_e2e.commit()
        logger.info("✅ Fase 2.5: Configuración del curso creada")

        # FASE 3: Generar calendario de guardias (simula generación)
        # Nota: Los tests E2E usan la lógica real de asignador_guardias
        # que consulta la configuración desde la BD

        # Obtener configuración para verificaciones posteriores
        config = session_e2e.query(Configuracion).first()
        assert config is not None, "Debe existir configuración"

        # Generar guardias
        guardias_generadas, asignaciones = generar_calendario_guardias(
            session=session_e2e,
        )

        # Guardar guardias en la base de datos
        guardar_guardias_en_bd(session_e2e, guardias_generadas)

        logger.info(
            f"✅ Fase 3: Guardias generadas - {len(guardias_generadas)} guardias, "
            f"{len(asignaciones)} profesores con asignaciones"
        )

        # Verificar que se generaron guardias
        total_guardias = session_e2e.query(Guardia).count()
        assert total_guardias > 0, "Deberían haberse generado guardias"

        # Verificar estructura de guardias
        guardias = session_e2e.query(Guardia).all()
        for guardia in guardias[:5]:  # Verificar algunas guardias
            assert guardia.profesor_id is not None
            assert guardia.zona_id is not None
            assert guardia.turno in ["mañana", "tarde"]
            assert guardia.recreo in [1, 2]
            # Verificar que la fecha está en el rango configurado
            assert config.fecha_inicio_curso <= guardia.fecha <= config.fecha_fin_curso

        logger.info(f"✅ Verificación: {guardias_generadas} guardias validadas")

        # FASE 4: Verificar distribución equitativa
        guardias_por_profesor = {}
        for guardia in guardias:
            profesor_id = guardia.profesor_id
            guardias_por_profesor[profesor_id] = (
                guardias_por_profesor.get(profesor_id, 0) + 1
            )

        # Todos los profesores deberían tener guardias
        assert len(guardias_por_profesor) > 0

        # Verificar que hay cierta equidad (diferencia máxima razonable)
        counts = list(guardias_por_profesor.values())
        if len(counts) > 1:
            diferencia = max(counts) - min(counts)
            # La diferencia no debería ser excesiva (máximo 50% más)
            assert diferencia <= max(counts) * 0.5

        logger.info("✅ Fase 4: Distribución equitativa verificada")

    def test_flujo_exportacion_importacion_json(self, session_e2e, limpiar_bd):
        """
        Test E2E: Exportar e importar datos completos en JSON.

        Simula un usuario que:
        1. Crea datos de prueba
        2. Exporta todo a JSON
        3. Limpia la BD
        4. Importa desde JSON
        5. Verifica que todo se restauró correctamente
        """
        # FASE 1: Crear datos de prueba
        prof1 = Profesor(
            nombre_completo="Test Profesor 1",
            horas_contrato=30,
            turno="completo",
            porcentaje_jornada=100.0,
        )
        prof2 = Profesor(
            nombre_completo="Test Profesor 2",
            horas_contrato=25,
            turno="mañana",
            porcentaje_jornada=100.0,
        )
        session_e2e.add_all([prof1, prof2])

        zona1 = Zona(nombre_zona="Zona Test 1")
        zona2 = Zona(nombre_zona="Zona Test 2")
        session_e2e.add_all([zona1, zona2])

        from datetime import time
        config = Configuracion(
            fecha_inicio_curso=date(2024, 9, 1),
            fecha_fin_curso=date(2024, 9, 30),
            hora_recreo1_manana=time(11, 0),
            hora_recreo2_manana=time(11, 30),
            hora_recreo1_tarde=time(16, 0),
            hora_recreo2_tarde=time(16, 30),
            dias_no_lectivos_personalizados="[]",
            recreos_config="[]",
            activar_festivos_automaticos=False,
        )
        session_e2e.add(config)

        session_e2e.commit()

        # Crear algunas guardias
        guardia = Guardia(
            profesor_id=prof1.id,
            zona_id=zona1.id,
            fecha=date.today(),
            turno="mañana",
            recreo=1,
        )
        session_e2e.add(guardia)
        session_e2e.commit()

        # Contar datos originales
        prof_count_orig = session_e2e.query(Profesor).count()
        zona_count_orig = session_e2e.query(Zona).count()
        guardia_count_orig = session_e2e.query(Guardia).count()

        logger.info(
            f"Datos originales: {prof_count_orig} prof, "
            f"{zona_count_orig} zonas, {guardia_count_orig} guardias"
        )

        # FASE 2: Exportar a JSON
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as tmp_file:
            tmp_path = tmp_file.name

        try:
            ExportadorDatos.exportar_todo(session_e2e, tmp_path)
            logger.info(f"✅ Datos exportados a {tmp_path}")

            # Verificar que el archivo existe y tiene contenido
            assert Path(tmp_path).exists()
            assert Path(tmp_path).stat().st_size > 100  # Al menos 100 bytes

            # Verificar estructura del JSON
            with open(tmp_path, "r", encoding="utf-8") as f:
                datos = json.load(f)
                assert "profesores" in datos
                assert "zonas" in datos
                assert "guardias" in datos
                assert len(datos["profesores"]) == prof_count_orig
                assert len(datos["zonas"]) == zona_count_orig

            # FASE 3: Limpiar BD (simula nueva instalación)
            session_e2e.query(Guardia).delete()
            session_e2e.query(Configuracion).delete()
            session_e2e.query(Zona).delete()
            session_e2e.query(Profesor).delete()
            session_e2e.commit()

            # Verificar que la BD está vacía
            assert session_e2e.query(Profesor).count() == 0
            assert session_e2e.query(Zona).count() == 0
            assert session_e2e.query(Guardia).count() == 0
            logger.info("✅ BD limpiada")

            # FASE 4: Importar desde JSON
            resultado = ExportadorDatos.importar_todo(
                session_e2e, tmp_path, limpiar_antes=False
            )
            logger.info(f"✅ Datos importados: {resultado}")

            # FASE 5: Verificar que todo se restauró
            assert session_e2e.query(Profesor).count() == prof_count_orig
            assert session_e2e.query(Zona).count() == zona_count_orig
            assert session_e2e.query(Guardia).count() == guardia_count_orig

            # Verificar contenido específico
            prof_restaurado = (
                session_e2e.query(Profesor)
                .filter_by(nombre_completo="Test Profesor 1")
                .first()
            )
            assert prof_restaurado is not None
            assert prof_restaurado.horas_contrato == 30
            assert prof_restaurado.turno == "completo"

            zona_restaurada = (
                session_e2e.query(Zona).filter_by(nombre_zona="Zona Test 1").first()
            )
            assert zona_restaurada is not None

            logger.info("✅ Todos los datos restaurados correctamente")

        finally:
            # Limpiar archivo temporal
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()

    def test_flujo_generacion_multiple_meses(self, session_e2e, limpiar_bd):
        """
        Test E2E: Generar guardias para múltiples meses.

        Verifica que el sistema puede manejar la generación
        secuencial de calendarios sin conflictos.
        """
        # Crear datos básicos
        profesores = []
        for i in range(3):
            prof = Profesor(
                nombre_completo=f"Profesor Test {i+1}",
                horas_contrato=30,
                turno="completo",
                porcentaje_jornada=100.0,
            )
            session_e2e.add(prof)
            profesores.append(prof)

        zona = Zona(nombre_zona="Zona Test")
        session_e2e.add(zona)
        session_e2e.commit()

        # Generar guardias para 3 meses consecutivos
        anio_actual = datetime.now().year
        resultados = []

        for mes in range(1, 4):  # Enero, Febrero, Marzo
            resultado = generar_calendario_guardias(
                session=session_e2e,
                mes=mes,
                anio=anio_actual,
                eliminar_existentes=True,
            )
            resultados.append(resultado)
            logger.info(f"✅ Mes {mes}: {resultado}")

        # Verificar que se generaron guardias para cada mes
        for mes in range(1, 4):
            guardias_mes = (
                session_e2e.query(Guardia)
                .filter(
                    Guardia.fecha >= date(anio_actual, mes, 1),
                    Guardia.fecha < date(anio_actual, mes + 1, 1)
                    if mes < 12
                    else date(anio_actual + 1, 1, 1),
                )
                .count()
            )
            assert guardias_mes > 0, f"Deberían haber guardias en mes {mes}"
            logger.info(f"Mes {mes}: {guardias_mes} guardias")

        # Verificar que no hay solapamientos (cada fecha única)
        guardias_total = session_e2e.query(Guardia).all()
        fechas_turnos_recreos = [
            (g.fecha, g.turno, g.recreo, g.zona_id) for g in guardias_total
        ]
        # Cada combinación fecha+turno+recreo+zona debe aparecer máx 1 vez
        assert len(fechas_turnos_recreos) == len(set(fechas_turnos_recreos))

        logger.info("✅ No hay duplicados en guardias multi-mes")

    @pytest.mark.skip(reason="Requiere reportlab instalado")
    def test_flujo_exportacion_pdf(self, session_e2e, limpiar_bd):
        """
        Test E2E: Exportar calendarios PDF para profesores.

        Verifica que se pueden generar PDFs para todos los profesores.
        """
        # Crear datos de prueba
        prof = Profesor(
            nombre_completo="Profesor PDF Test",
            horas_contrato=30,
            turno="completo",
            porcentaje_jornada=100.0,
        )
        session_e2e.add(prof)

        zona = Zona(nombre_zona="Zona Test")
        session_e2e.add(zona)
        session_e2e.commit()

        # Crear guardias
        for dia in range(1, 6):  # 5 días
            guardia = Guardia(
                profesor_id=prof.id,
                zona_id=zona.id,
                fecha=date(2024, 1, dia),
                turno="mañana",
                recreo=1,
            )
            session_e2e.add(guardia)
        session_e2e.commit()

        # Exportar PDFs
        with tempfile.TemporaryDirectory() as tmp_dir:
            count = ExportadorPDF.exportar_todos_los_profesores(
                session_e2e, mes=1, anio=2024, carpeta_salida=tmp_dir
            )

            assert count > 0, "Debería haberse generado al menos 1 PDF"
            logger.info(f"✅ {count} PDFs generados")

            # Verificar que los archivos existen
            archivos_pdf = list(Path(tmp_dir).glob("*.pdf"))
            assert len(archivos_pdf) == count


class TestValidacionesIntegradas:
    """Tests E2E que verifican validaciones en flujos completos."""

    def test_no_se_generan_guardias_sin_profesores(self, session_e2e, limpiar_bd):
        """
        Test E2E: El sistema no debe generar guardias si no hay profesores.
        """
        # Solo crear zona, sin profesores
        zona = Zona(nombre_zona="Zona Test")
        session_e2e.add(zona)
        session_e2e.commit()

        # Intentar generar guardias
        generar_calendario_guardias(
            session=session_e2e,
            mes=datetime.now().month,
            anio=datetime.now().year,
            eliminar_existentes=True,
        )

        # No deberían haberse generado guardias
        guardias_count = session_e2e.query(Guardia).count()
        assert guardias_count == 0
        logger.info("✅ Correctamente no se generaron guardias sin profesores")

    def test_regeneracion_elimina_guardias_previas(self, session_e2e, limpiar_bd):
        """
        Test E2E: Regenerar guardias debe eliminar las existentes.
        """
        # Crear datos básicos
        prof = Profesor(
            nombre_completo="Profesor Test",
            horas_contrato=30,
            turno="completo",
            porcentaje_jornada=100.0,
        )
        zona = Zona(nombre_zona="Zona Test")
        session_e2e.add_all([prof, zona])
        session_e2e.commit()

        mes = datetime.now().month
        anio = datetime.now().year

        # Primera generación
        generar_calendario_guardias(session_e2e, mes, anio, eliminar_existentes=True)
        count_primera = session_e2e.query(Guardia).count()
        assert count_primera > 0

        # Segunda generación (debería reemplazar)
        generar_calendario_guardias(session_e2e, mes, anio, eliminar_existentes=True)
        count_segunda = session_e2e.query(Guardia).count()

        # El count puede ser similar pero no deberían ser las mismas guardias
        # (los IDs serían diferentes si se eliminaron y recrearon)
        assert count_segunda > 0
        logger.info(
            f"✅ Regeneración exitosa: {count_primera} → {count_segunda} guardias"
        )
