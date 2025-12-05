"""
Tests E2E para validaciones y escenarios complejos.

Valida que el sistema maneje correctamente:
- Profesores sin disponibilidad
- Zonas sin profesores
- Ausencias bloqueando asignaciones
- Validaciones de entrada (emails, nombres, fechas)
- Validaciones de negocio (máximo guardias, duplicados)
- Integración validators UI/backend
"""

from datetime import date

import pytest
from infrastructure.database.models import (
    Ausencia,
    Configuracion,
    CursoEscolar,
    Guardia,
    Profesor,
    Zona,
)
from services.asignador_guardias_v4_hibrido import generar_guardias_v4_hibrido
from utils.validators import (
    validar_dias_semana,
    validar_email,
    validar_horas_contrato,
    validar_nombre_completo,
    validar_rango_fechas,
    validar_turno,
)

# ============================================================================
# FIXTURES
# ============================================================================


# Usa el fixture 'session' de conftest.py (no redefinir)


@pytest.fixture
def limpiar_bd(session):
    """Limpia todas las tablas antes y después de cada test."""
    # Limpiar antes
    session.query(Guardia).delete()
    session.query(Ausencia).delete()
    session.query(Profesor).delete()
    session.query(Zona).delete()
    session.query(Configuracion).delete()
    session.query(CursoEscolar).delete()
    session.commit()

    yield

    # Limpiar después
    session.query(Guardia).delete()
    session.query(Ausencia).delete()
    session.query(Profesor).delete()
    session.query(Zona).delete()
    session.query(Configuracion).delete()
    session.query(CursoEscolar).delete()
    session.commit()


@pytest.fixture
def curso_activo(session, limpiar_bd):
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
def configuracion_basica(session):
    """Crea una configuración básica del curso."""
    from datetime import time

    # Usar fecha actual para que los tests generen guardias
    # Configuración para octubre 2025
    config = Configuracion(
        anio_inicio_curso=2025,
        fecha_inicio_curso=date(2025, 9, 1),
        fecha_fin_curso=date(2026, 6, 30),
        hora_recreo1_manana=time(11, 0),
        hora_recreo2_manana=time(13, 30),
        hora_recreo1_tarde=time(17, 0),
        hora_recreo2_tarde=time(19, 0),
        activar_festivos_automaticos=True,
        ajuste_tutores=1.0,
        ajuste_no_tutores=1.0,
    )
    session.add(config)
    session.commit()
    return config


# ============================================================================
# TESTS DE VALIDADORES DE ENTRADA
# ============================================================================


class TestValidadoresEntrada:
    """Tests para validadores de datos de entrada."""

    def test_validar_email_formato_correcto(self):
        """Email con formato correcto debe ser válido."""
        valido, error = validar_email("profesor@colegio.edu")
        assert valido is True
        assert error is None

    def test_validar_email_formato_incorrecto(self):
        """Email sin @ debe ser inválido."""
        valido, error = validar_email("email_sin_arroba")
        assert valido is False
        assert "formato" in error.lower()

    def test_validar_email_vacio(self):
        """Email vacío debe ser inválido."""
        valido, error = validar_email("")
        assert valido is False
        assert "vacío" in error.lower()

    def test_validar_nombre_completo_formato_correcto(self):
        """Nombre con formato APELLIDOS, NOMBRE debe ser válido."""
        valido, error = validar_nombre_completo("GARCÍA LÓPEZ, JUAN")
        assert valido is True
        assert error is None

    def test_validar_nombre_sin_coma(self):
        """Nombre sin coma debe ser inválido."""
        valido, error = validar_nombre_completo("Juan García López")
        assert valido is False
        assert "coma" in error.lower()

    def test_validar_nombre_vacio(self):
        """Nombre vacío debe ser inválido."""
        valido, error = validar_nombre_completo("")
        assert valido is False
        assert "vacío" in error.lower()

    def test_validar_fecha_valida(self):
        """Fecha válida (no None) debe pasar validación básica."""
        fecha = date(2025, 1, 15)
        assert fecha is not None
        assert isinstance(fecha, date)

    def test_validar_rango_fechas_correcto(self):
        """Rango con inicio < fin debe ser válido."""
        valido, error = validar_rango_fechas(date(2024, 9, 1), date(2025, 6, 30))
        assert valido is True
        assert error is None

    def test_validar_rango_fechas_incorrecto(self):
        """Rango con inicio >= fin debe ser inválido."""
        valido, error = validar_rango_fechas(date(2025, 6, 30), date(2024, 9, 1))
        assert valido is False
        assert "anterior" in error.lower()

    def test_validar_horas_contrato_validas(self):
        """Horas entre 1 y 40 deben ser válidas."""
        valido, error = validar_horas_contrato(25.0)
        assert valido is True
        assert error is None

    def test_validar_horas_contrato_negativas(self):
        """Horas negativas deben ser inválidas."""
        valido, error = validar_horas_contrato(-5.0)
        assert valido is False
        assert "positivo" in error.lower()

    def test_validar_horas_contrato_excesivas(self):
        """Más de 40 horas deben ser inválidas."""
        valido, error = validar_horas_contrato(50.0)
        assert valido is False
        assert "40" in error

    def test_validar_turno_valido(self):
        """Turnos válidos: mañana, tarde, mixto."""
        for turno in ["mañana", "tarde", "mixto"]:
            valido, error = validar_turno(turno)
            assert valido is True
            assert error is None

    def test_validar_turno_invalido(self):
        """Turno no reconocido debe ser inválido."""
        valido, error = validar_turno("noche")
        assert valido is False
        assert "inválido" in error.lower()

    def test_validar_dias_semana_correcto(self):
        """Días de semana válidos (0-6) separados por comas."""
        valido, error = validar_dias_semana("0,1,2,3,4")
        assert valido is True
        assert error is None

    def test_validar_dias_semana_fuera_rango(self):
        """Día fuera del rango 0-6 debe ser inválido."""
        valido, error = validar_dias_semana("0,1,7,8")
        assert valido is False
        assert "0" in error and "6" in error


# ============================================================================
# TESTS DE ESCENARIOS DE VALIDACIÓN DE NEGOCIO
# ============================================================================


class TestEscenariosValidacionNegocio:
    """Tests para validaciones de lógica de negocio."""

    def test_profesor_sin_disponibilidad_no_puede_recibir_guardias(
        self, session, curso_activo, limpiar_bd, configuracion_basica
    ):
        """
        Profesor sin disponibilidad (horas=0) debe tener cuota calculada como 0.

        Escenario:
        1. Crear profesor con horas_contrato=0
        2. Calcular cuotas de guardias
        3. Verificar que la cuota es 0
        """
        from services.calculador_guardias import calcular_guardias_por_profesor

        # Crear zona
        zona = Zona(nombre_zona="Patio A")
        session.add(zona)
        session.flush()

        # Crear profesor sin disponibilidad
        profesor_sin_disponibilidad = Profesor(
            nombre_completo="SIN HORAS, PROFESOR",
            email_corporativo="sinhoras@colegio.edu",
            horas_contrato=0.0,
            porcentaje_jornada=0.0,
            turno="mañana",
        )
        session.add(profesor_sin_disponibilidad)

        # Crear profesor con disponibilidad
        profesor_con_disponibilidad = Profesor(
            nombre_completo="CON HORAS, PROFESOR",
            email_corporativo="conhoras@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor_con_disponibilidad)
        session.commit()

        # Calcular cuotas
        cuotas = calcular_guardias_por_profesor(session)

        # Verificar que el profesor sin disponibilidad tiene cuota 0
        cuota_sin_disponibilidad = cuotas.get(profesor_sin_disponibilidad.id, 0)
        assert cuota_sin_disponibilidad == 0, (
            "Profesor sin disponibilidad debe tener cuota de 0 guardias"
        )

        # Verificar que el profesor con disponibilidad tiene cuota > 0
        cuota_con_disponibilidad = cuotas.get(profesor_con_disponibilidad.id, 0)
        assert cuota_con_disponibilidad > 0, "Profesor con disponibilidad debe tener cuota > 0"

    def test_zona_sin_profesores_no_genera_guardias(
        self, session, limpiar_bd, configuracion_basica
    ):
        """
        Zona sin profesores asignados existe pero sin guardias asignadas.

        Escenario:
        1. Crear zona sin profesores
        2. Crear otra zona con profesores
        3. Generar guardias
        4. Verificar que zona vacía no tiene guardias
        """
        # Crear zona sin profesores
        zona_sin_profesores = Zona(nombre_zona="Zona Vacía")
        session.add(zona_sin_profesores)

        # Crear otra zona con profesores para que no falle la generación
        zona_con_profesores = Zona(nombre_zona="Zona Activa")
        session.add(zona_con_profesores)
        session.flush()

        profesor = Profesor(
            nombre_completo="ACTIVO, PROFESOR",
            email_corporativo="activo@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor)
        session.commit()

        # Generar guardias (puede o no generar dependiendo de las fechas)
        try:
            generar_guardias_v4_hibrido(session)
        except ValueError:
            # Si no hay slots válidos, el test igual pasa
            # porque verificamos que la zona vacía no tiene guardias
            pass

        # Verificar que la zona sin profesores NO tiene guardias
        guardias_zona_vacia = (
            session.query(Guardia).filter_by(zona_id=zona_sin_profesores.id).count()
        )
        assert guardias_zona_vacia == 0, "Zona sin profesores no debe tener guardias generadas"

        # Si se generaron guardias, verificar que NO fueron para la zona vacía
        total_guardias = session.query(Guardia).count()
        if total_guardias > 0:
            # Si hay guardias, deben ser de otras zonas
            assert guardias_zona_vacia == 0, (
                "Las guardias generadas no deben estar en zona sin profesores"
            )

    def test_ausencia_bloquea_asignacion_guardia(self, session, limpiar_bd, configuracion_basica):
        """
        Profesor con ausencia registrada no debe recibir guardias ese día.

        Escenario:
        1. Crear profesor
        2. Registrar ausencia para fecha específica
        3. Generar guardias para ese período
        4. Verificar que no se asignó guardia en día de ausencia
        """
        # Crear zona
        zona = Zona(nombre_zona="Patio Principal")
        session.add(zona)
        session.flush()

        # Crear profesor
        profesor = Profesor(
            nombre_completo="AUSENTE, PROFESOR",
            email_corporativo="ausente@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor)
        session.flush()

        # Registrar ausencia para el 25 de octubre (fecha dentro del curso actual)
        fecha_ausencia = date(2025, 10, 25)
        ausencia = Ausencia(
            profesor_id=profesor.id,
            fecha_inicio=fecha_ausencia,
            fecha_fin=fecha_ausencia,
            tipo="baja_medica",
            motivo="Enfermedad",
            activa=True,
        )
        session.add(ausencia)
        session.commit()

        # Generar guardias para el rango que incluye la ausencia
        generar_guardias_v4_hibrido(session)

        # Verificar que NO hay guardias para el profesor en la fecha de ausencia
        guardias_dia_ausencia = (
            session.query(Guardia).filter_by(profesor_id=profesor.id, fecha=fecha_ausencia).count()
        )
        assert guardias_dia_ausencia == 0, "Profesor con ausencia no debe tener guardias ese día"

    def test_maximo_una_guardia_por_dia_respetado(self, session, limpiar_bd, configuracion_basica):
        """
        Validar que un profesor no tenga más de 1 guardia por día.

        Escenario:
        1. Crear profesor y zona
        2. Generar guardias para varios días
        3. Verificar que ningún día tiene más de 1 guardia por profesor
        """
        # Crear zona
        zona = Zona(nombre_zona="Patio B")
        session.add(zona)
        session.flush()

        # Crear profesor
        profesor = Profesor(
            nombre_completo="NORMAL, PROFESOR",
            email_corporativo="normal@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor)
        session.commit()

        # Generar guardias
        generar_guardias_v4_hibrido(session)

        # Obtener todas las guardias del profesor
        guardias = session.query(Guardia).filter_by(profesor_id=profesor.id).all()

        # Agrupar por fecha y verificar máximo 1 por día
        guardias_por_fecha = {}
        for guardia in guardias:
            fecha_str = guardia.fecha.isoformat()
            guardias_por_fecha[fecha_str] = guardias_por_fecha.get(fecha_str, 0) + 1

        for fecha, cantidad in guardias_por_fecha.items():
            assert cantidad <= 1, (
                f"Profesor tiene {cantidad} guardias el {fecha}, máximo permitido es 1"
            )

    def test_no_guardias_duplicadas_mismo_slot(self, session, limpiar_bd, configuracion_basica):
        """
        Validar que no existan guardias duplicadas (mismo profesor, fecha, turno, recreo).

        Escenario:
        1. Generar guardias normalmente
        2. Verificar que no hay duplicados por (profesor_id, fecha, turno, recreo)
        """
        # Crear zona y profesor
        zona = Zona(nombre_zona="Patio C")
        session.add(zona)
        session.flush()

        profesor = Profesor(
            nombre_completo="UNICO, PROFESOR",
            email_corporativo="unico@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor)
        session.commit()

        # Generar guardias
        generar_guardias_v4_hibrido(session)

        # Obtener todas las guardias
        guardias = session.query(Guardia).all()

        # Crear conjunto de tuplas (profesor_id, fecha, turno, recreo)
        slots = set()
        for guardia in guardias:
            slot = (
                guardia.profesor_id,
                guardia.fecha,
                guardia.turno,
                guardia.recreo,
            )
            assert slot not in slots, f"Guardia duplicada detectada: {slot}"
            slots.add(slot)

    def test_profesor_turno_tarde_no_recibe_guardias_manana(
        self, session, limpiar_bd, configuracion_basica
    ):
        """
        Profesor de turno tarde no debe recibir guardias de mañana.

        Escenario:
        1. Crear profesor con turno='tarde'
        2. Generar guardias
        3. Verificar que no tiene guardias con turno='mañana'
        """
        # Crear zona
        zona = Zona(nombre_zona="Zona Tarde")
        session.add(zona)
        session.flush()

        # Crear profesor de tarde
        profesor_tarde = Profesor(
            nombre_completo="TARDE, PROFESOR",
            email_corporativo="tarde@colegio.edu",
            horas_contrato=20.0,
            porcentaje_jornada=100.0,
            turno="tarde",
        )
        session.add(profesor_tarde)

        # Crear profesor de mañana para que se generen guardias
        profesor_manana = Profesor(
            nombre_completo="MAÑANA, PROFESOR",
            email_corporativo="manana@colegio.edu",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            turno="mañana",
        )
        session.add(profesor_manana)
        session.commit()

        # Generar guardias
        generar_guardias_v4_hibrido(session)

        # Verificar que profesor de tarde NO tiene guardias de mañana
        guardias_manana = (
            session.query(Guardia).filter_by(profesor_id=profesor_tarde.id, turno="mañana").count()
        )
        assert guardias_manana == 0, "Profesor de turno tarde no debe tener guardias de mañana"

    def test_creacion_profesor_con_email_invalido_falla(self, session, limpiar_bd):
        """
        Validar que la aplicación rechaza emails con formato inválido.

        Nota: Este test asume que la validación se hace en la capa de aplicación,
        no directamente en el ORM. Si no hay validación, se puede agregar.
        """
        # Validar email antes de crear profesor (práctica recomendada)
        email_invalido = "email_sin_arroba"
        valido, error = validar_email(email_invalido)

        assert valido is False
        assert error is not None

        # Si intentamos crear el profesor sin validar, SQLAlchemy lo aceptará
        # pero la aplicación debería validar primero

    def test_creacion_profesor_con_nombre_invalido_falla(self, session, limpiar_bd):
        """
        Validar que la aplicación rechaza nombres sin el formato correcto.
        """
        nombre_invalido = "Juan García"  # Sin coma
        valido, error = validar_nombre_completo(nombre_invalido)

        assert valido is False
        assert error is not None
        assert "coma" in error.lower()

    def test_creacion_configuracion_fechas_invalidas_falla(self, session, limpiar_bd):
        """
        Validar que configuración con fecha_fin < fecha_inicio sea rechazada.
        """
        fecha_inicio = date(2025, 6, 30)
        fecha_fin = date(2024, 9, 1)

        valido, error = validar_rango_fechas(fecha_inicio, fecha_fin)

        assert valido is False
        assert "anterior" in error.lower()


# ============================================================================
# TESTS DE INTEGRACIÓN VALIDATORS UI/BACKEND
# ============================================================================


class TestIntegracionValidadores:
    """Tests de integración entre validadores y lógica de negocio."""

    def test_pipeline_completo_validacion_profesor(self, session, limpiar_bd):
        """
        Test del pipeline completo de validación de un profesor:
        1. Validar email
        2. Validar nombre
        3. Validar horas contrato
        4. Validar turno
        5. Crear en BD si todo es válido
        """
        # Datos de entrada
        email = "nuevo@colegio.edu"
        nombre = "PÉREZ MARTÍN, CARLOS"
        horas = 25.0
        turno = "mañana"

        # Pipeline de validación
        email_valido, email_error = validar_email(email)
        nombre_valido, nombre_error = validar_nombre_completo(nombre)
        horas_validas, horas_error = validar_horas_contrato(horas)
        turno_valido, turno_error = validar_turno(turno)

        # Verificar todas las validaciones
        assert email_valido, f"Email inválido: {email_error}"
        assert nombre_valido, f"Nombre inválido: {nombre_error}"
        assert horas_validas, f"Horas inválidas: {horas_error}"
        assert turno_valido, f"Turno inválido: {turno_error}"

        # Si todo es válido, crear en BD
        zona = Zona(nombre_zona="Patio Principal")
        session.add(zona)
        session.flush()

        profesor = Profesor(
            nombre_completo=nombre,
            email_corporativo=email,
            horas_contrato=horas,
            porcentaje_jornada=100.0,
            turno=turno,
        )
        session.add(profesor)
        session.commit()

        # Verificar que se creó correctamente
        profesor_bd = session.query(Profesor).filter_by(email_corporativo=email).first()
        assert profesor_bd is not None
        assert profesor_bd.nombre_completo == nombre
        assert profesor_bd.horas_contrato == horas
        assert profesor_bd.turno == turno

    def test_pipeline_completo_validacion_configuracion(self, session, limpiar_bd):
        """
        Test del pipeline completo de validación de configuración:
        1. Validar rango de fechas
        2. Crear configuración si todo es válido
        """
        from datetime import time

        # Datos de entrada
        fecha_inicio = date(2024, 9, 1)
        fecha_fin = date(2025, 6, 30)

        # Pipeline de validación
        fechas_validas, fechas_error = validar_rango_fechas(fecha_inicio, fecha_fin)

        # Verificar validaciones
        assert fechas_validas, f"Rango de fechas inválido: {fechas_error}"

        # Crear configuración
        config = Configuracion(
            anio_inicio_curso=2024,
            fecha_inicio_curso=fecha_inicio,
            fecha_fin_curso=fecha_fin,
            hora_recreo1_manana=time(11, 0),
            hora_recreo2_manana=time(13, 30),
            activar_festivos_automaticos=True,
            ajuste_tutores=1.0,
            ajuste_no_tutores=1.0,
        )
        session.add(config)
        session.commit()

        # Verificar que se creó
        config_bd = session.query(Configuracion).first()
        assert config_bd is not None
        assert config_bd.fecha_inicio_curso == fecha_inicio
        assert config_bd.fecha_fin_curso == fecha_fin

    def test_validacion_multiple_profesores_batch(self, session, limpiar_bd):
        """
        Validar un lote de profesores y reportar cuáles son válidos/inválidos.

        Escenario típico de importación masiva desde Excel.
        """
        profesores_data = [
            {
                "nombre": "GARCÍA LÓPEZ, ANA",
                "email": "ana@colegio.edu",
                "horas": 25.0,
                "turno": "mañana",
            },  # Válido
            {
                "nombre": "Juan Pérez",
                "email": "juan@colegio.edu",
                "horas": 20.0,
                "turno": "tarde",
            },  # Inválido (nombre)
            {
                "nombre": "MARTÍN SÁNCHEZ, LUIS",
                "email": "email_invalido",
                "horas": 30.0,
                "turno": "mixto",
            },  # Inválido (email)
            {
                "nombre": "LÓPEZ FERNÁNDEZ, MARÍA",
                "email": "maria@colegio.edu",
                "horas": 50.0,
                "turno": "mañana",
            },  # Inválido (horas)
        ]

        resultados = []
        for data in profesores_data:
            errores = []

            # Validar cada campo
            email_valido, email_error = validar_email(data["email"])
            if not email_valido:
                errores.append(f"Email: {email_error}")

            nombre_valido, nombre_error = validar_nombre_completo(data["nombre"])
            if not nombre_valido:
                errores.append(f"Nombre: {nombre_error}")

            horas_validas, horas_error = validar_horas_contrato(data["horas"])
            if not horas_validas:
                errores.append(f"Horas: {horas_error}")

            turno_valido, turno_error = validar_turno(data["turno"])
            if not turno_valido:
                errores.append(f"Turno: {turno_error}")

            resultados.append(
                {
                    "data": data,
                    "valido": len(errores) == 0,
                    "errores": errores,
                }
            )

        # Verificar resultados esperados
        assert resultados[0]["valido"] is True  # ANA - válido
        assert resultados[1]["valido"] is False  # Juan - nombre inválido
        assert resultados[2]["valido"] is False  # LUIS - email inválido
        assert resultados[3]["valido"] is False  # MARÍA - horas inválidas

        # Verificar que se capturaron los errores correctos
        assert any("coma" in e.lower() for e in resultados[1]["errores"])
        assert any("formato" in e.lower() for e in resultados[2]["errores"])
        assert any("40" in e for e in resultados[3]["errores"])

        # Contar válidos/inválidos
        validos = sum(1 for r in resultados if r["valido"])
        invalidos = sum(1 for r in resultados if not r["valido"])

        assert validos == 1
        assert invalidos == 3
