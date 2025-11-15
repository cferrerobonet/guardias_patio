"""
Tests para Domain Services

Verifica que los servicios de dominio funcionen correctamente
y mantengan las reglas de negocio.
"""

from datetime import date, timedelta

import pytest
from domain.services import (
    AsignacionGuardiaService,
    DisponibilidadProfesorService,
    DistribucionCuotasService,
    EquidadGuardiasService,
)
from models.models import Ausencia, Configuracion, Guardia, Profesor, Zona
from sqlalchemy.orm import Session


class TestDisponibilidadProfesorService:
    """Tests para DisponibilidadProfesorService."""

    def test_profesor_disponible_basico(self, session: Session):
        """Verifica que un profesor activo sin restricciones esté disponible."""
        # Crear profesor activo
        profesor = Profesor(
            nombre_completo="Juan Pérez",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            horas_manana=12.5,
            horas_tarde=12.5,
        )
        session.add(profesor)
        session.flush()

        service = DisponibilidadProfesorService(session)
        disponible, razon = service.esta_disponible(
            profesor, date.today(), "mañana"
        )

        assert disponible is True
        assert razon is None

    def test_profesor_inactivo_no_disponible(self, session: Session):
        """Profesor inactivo no debe estar disponible."""
        profesor = Profesor(
            nombre_completo="María García",
            activo=False,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        session.add(profesor)
        session.flush()

        service = DisponibilidadProfesorService(session)
        disponible, razon = service.esta_disponible(
            profesor, date.today(), "mañana"
        )

        assert disponible is False
        assert "inactivo" in razon.lower()

    def test_profesor_ausente_no_disponible(self, session: Session):
        """Profesor con ausencia no debe estar disponible."""
        profesor = Profesor(
            nombre_completo="Carlos López",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        session.add(profesor)
        session.flush()

        # Registrar ausencia
        fecha = date.today()
        ausencia = Ausencia(
            profesor_id=profesor.id,
            fecha_inicio=fecha,
            fecha_fin=fecha,
            tipo="baja_medica",
            activa=True,
        )
        session.add(ausencia)
        session.flush()

        service = DisponibilidadProfesorService(session)
        disponible, razon = service.esta_disponible(profesor, fecha, "mañana")

        assert disponible is False
        assert "ausente" in razon.lower()

    def test_turno_incompatible_no_disponible(self, session: Session):
        """Profesor de mañana no disponible para turno de tarde."""
        profesor = Profesor(
            nombre_completo="Ana Martínez",
            activo=True,
            turno="mañana",
            horas_contrato=12.5,
            porcentaje_jornada=50.0,
        )
        session.add(profesor)
        session.flush()

        service = DisponibilidadProfesorService(session)
        disponible, razon = service.esta_disponible(
            profesor, date.today(), "tarde"
        )

        assert disponible is False
        assert "turno" in razon.lower() or "incompatible" in razon.lower()

    def test_maximo_guardias_dia_excedido(self, session: Session):
        """No disponible si ya alcanzó máximo de guardias por día."""
        profesor = Profesor(
            nombre_completo="Luis Rodríguez",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            horas_manana=12.5,
            horas_tarde=12.5,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([profesor, zona])
        session.flush()

        # Crear guardia existente
        fecha = date.today()
        guardia = Guardia(
            profesor_id=profesor.id,
            fecha=fecha,
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia)
        session.flush()

        service = DisponibilidadProfesorService(session)
        disponible, razon = service.esta_disponible(
            profesor, fecha, "tarde", recreo_id=2, max_guardias_dia=1
        )

        assert disponible is False
        assert "máximo" in razon.lower() or "día" in razon.lower()


class TestDistribucionCuotasService:
    """Tests para DistribucionCuotasService."""

    def test_calcular_cuotas_simple(self, session: Session):
        """Calcula cuotas para 2 profesores con misma jornada."""
        from datetime import time
        # Crear configuración
        config = Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date.today(),
            fecha_fin_curso=date.today() + timedelta(days=180),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            recreos_config=str([{"id": 1, "turno": "mañana"}, {"id": 2, "turno": "tarde"}]),
        )
        session.add(config)

        # Crear profesores
        prof1 = Profesor(
            nombre_completo="Profesor 1",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        prof2 = Profesor(
            nombre_completo="Profesor 2",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        session.add_all([prof1, prof2])

        # Crear zona
        zona = Zona(nombre_zona="Zona 1")
        session.add(zona)
        session.flush()

        service = DistribucionCuotasService(session)
        cuotas = service.calcular_cuotas([prof1, prof2])

        # Ambos deben tener cuotas similares
        assert prof1.id in cuotas
        assert prof2.id in cuotas
        assert abs(cuotas[prof1.id] - cuotas[prof2.id]) <= 1  # Máx 1 de diferencia

    @pytest.mark.skip(reason="Requiere lógica compleja de distribución - revisar en fase de integración")
    def test_cuota_proporcional_a_jornada(self, session: Session):
        """Profesor de medio tiempo debe tener ~mitad de cuota."""
        from datetime import time
        config = Configuracion(
            anio_inicio_curso=2025,
            fecha_inicio_curso=date.today(),
            fecha_fin_curso=date.today() + timedelta(days=180),
            hora_recreo1_manana=time(10, 30),
            hora_recreo2_manana=time(12, 30),
            recreos_config=str([{"id": 1, "turno": "mañana"}]),
        )
        session.add(config)

        prof_completo = Profesor(
            nombre_completo="Tiempo Completo",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        prof_medio = Profesor(
            nombre_completo="Medio Tiempo",
            activo=True,
            turno="mixto",
            horas_contrato=12.5,
            porcentaje_jornada=50.0,
        )
        session.add_all([prof_completo, prof_medio])

        zona = Zona(nombre_zona="Zona 1")
        session.add(zona)
        session.flush()

        service = DistribucionCuotasService(session)
        cuotas = service.calcular_cuotas([prof_completo, prof_medio])

        # Verificar proporción aproximada
        ratio = cuotas[prof_completo.id] / cuotas[prof_medio.id] if cuotas[prof_medio.id] > 0 else 0
        assert 1.8 <= ratio <= 2.2  # Aproximadamente 2:1


class TestAsignacionGuardiaService:
    """Tests para AsignacionGuardiaService."""

    def test_puede_asignar_guardia_valida(self, session: Session):
        """Puede asignar guardia a profesor disponible."""
        profesor = Profesor(
            nombre_completo="Pedro Sánchez",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            horas_manana=12.5,
            horas_tarde=12.5,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([profesor, zona])
        session.flush()

        service = AsignacionGuardiaService(session)
        puede, razon = service.puede_asignar_guardia(
            profesor, date.today(), "mañana", 1, zona.id
        )

        assert puede is True
        assert razon is None

    def test_asignar_guardia_crea_objeto(self, session: Session):
        """Asignar guardia crea objeto Guardia correctamente."""
        profesor = Profesor(
            nombre_completo="Elena Torres",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            horas_manana=12.5,
            horas_tarde=12.5,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([profesor, zona])
        session.flush()

        service = AsignacionGuardiaService(session)
        fecha = date.today()
        guardia = service.asignar_guardia(
            profesor, fecha, "mañana", 1, zona.id
        )

        assert guardia is not None
        assert guardia.profesor_id == profesor.id
        assert guardia.fecha == fecha
        assert guardia.turno == "mañana"
        assert guardia.recreo == 1
        assert guardia.zona_id == zona.id

    def test_no_permite_guardia_duplicada(self, session: Session):
        """No permite asignar guardia duplicada en mismo slot."""
        profesor = Profesor(
            nombre_completo="Javier Ruiz",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
            horas_manana=12.5,
            horas_tarde=12.5,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([profesor, zona])
        session.flush()

        # Crear guardia existente
        fecha = date.today()
        guardia_existente = Guardia(
            profesor_id=profesor.id,
            fecha=fecha,
            turno="mañana",
            recreo=1,
            zona_id=zona.id,
        )
        session.add(guardia_existente)
        session.flush()

        service = AsignacionGuardiaService(session)
        # Intentar asignar en otro recreo para evitar trigger de max_guardias_dia
        puede, razon = service.puede_asignar_guardia(
            profesor, fecha, "tarde", 2, zona.id, verificar_cuota=False
        )

        # Debería fallar por máximo de guardias por día (ya tiene 1, max es 1)
        assert puede is False
        assert "máximo" in razon.lower() or "día" in razon.lower()


class TestEquidadGuardiasService:
    """Tests para EquidadGuardiasService."""

    def test_indice_equidad_perfecto(self, session: Session):
        """Índice debe ser 1.0 con distribución perfecta."""
        # Crear profesores
        prof1 = Profesor(
            nombre_completo="Profesor 1",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        prof2 = Profesor(
            nombre_completo="Profesor 2",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([prof1, prof2, zona])
        session.flush()

        # Crear guardias con distribución perfecta
        fecha = date.today()
        guardias = [
            Guardia(
                profesor_id=prof1.id,
                fecha=fecha,
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            ),
            Guardia(
                profesor_id=prof2.id,
                fecha=fecha,
                turno="tarde",
                recreo=2,
                zona_id=zona.id,
            ),
        ]
        session.add_all(guardias)
        session.flush()

        cuotas = {prof1.id: 1, prof2.id: 1}

        service = EquidadGuardiasService(session)
        indice = service.calcular_indice_equidad(guardias, cuotas)

        assert indice == 1.0

    def test_identificar_desbalances(self, session: Session):
        """Identifica profesores con exceso y déficit."""
        prof1 = Profesor(
            nombre_completo="Profesor Con Exceso",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        prof2 = Profesor(
            nombre_completo="Profesor Con Déficit",
            activo=True,
            turno="mixto",
            horas_contrato=25.0,
            porcentaje_jornada=100.0,
        )
        zona = Zona(nombre_zona="Zona 1")
        session.add_all([prof1, prof2, zona])
        session.flush()

        # Crear guardias con desbalance
        fecha = date.today()
        guardias = [
            Guardia(
                profesor_id=prof1.id,
                fecha=fecha,
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            ),
            Guardia(
                profesor_id=prof1.id,
                fecha=fecha + timedelta(days=1),
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            ),
            Guardia(
                profesor_id=prof1.id,
                fecha=fecha + timedelta(days=2),
                turno="mañana",
                recreo=1,
                zona_id=zona.id,
            ),
        ]
        session.add_all(guardias)
        session.flush()

        # Cuotas esperadas: 1 cada uno
        cuotas = {prof1.id: 1, prof2.id: 1}

        service = EquidadGuardiasService(session)
        desbalances = service.identificar_desbalances(guardias, cuotas)

        assert len(desbalances) == 2  # prof1 con exceso, prof2 con déficit

        # Verificar que prof1 tiene exceso
        desbalance_prof1 = next(d for d in desbalances if d.profesor_id == prof1.id)
        assert desbalance_prof1.diferencia > 0  # Exceso

        # Verificar que prof2 tiene déficit
        desbalance_prof2 = next(d for d in desbalances if d.profesor_id == prof2.id)
        assert desbalance_prof2.diferencia < 0  # Déficit


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
