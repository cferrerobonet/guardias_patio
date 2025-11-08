"""
Tests para las entidades del dominio:
- ProfesorEntity
- ZonaEntity
- GuardiaEntity

Comprueban construcción, igualdad por valor y reglas de validación comunes.
"""
from datetime import date, timedelta

import pytest

from config import settings
from core.exceptions import (
    GuardiaConflictError,
    GuardiaInvalidaError,
    MaxGuardiasDiaExceededError,
    ProfesorAusenteError,
)
from src.domain.entities import GuardiaEntity, ProfesorEntity, ZonaEntity
from src.domain.value_objects import Email, HorasContrato, Turno, TurnoEnum, ZonaPreferida


class TestProfesorEntity:
    """Tests para ProfesorEntity."""

    def test_construccion_basica(self):
        """Test construcción básica con valores mínimos."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana López",
            email_corporativo=Email("ana@colegio.com"),
        )
        assert profesor.id == 1
        assert profesor.nombre_completo == "Ana López"
        assert profesor.email_corporativo.value == "ana@colegio.com"
        assert profesor.activo is True

    def test_construccion_completa(self):
        """Test construcción con todos los campos."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana López",
            email_corporativo=Email("ana@colegio.com"),
            horas_contrato=HorasContrato(25.0),
            porcentaje_jornada=100.0,
            turno=Turno(TurnoEnum.MANANA),
            es_tutor=True,
            zona_preferida=ZonaPreferida(zona_id=5),
            dias_semana_permitidos=[0, 1, 2, 3, 4],
            recreos_permitidos=[1, 2],
        )
        assert profesor.horas_contrato.value == 25.0
        assert profesor.es_tutor is True
        assert profesor.zona_preferida.zona_id == 5
        assert profesor.dias_semana_permitidos == [0, 1, 2, 3, 4]
        assert profesor.recreos_permitidos == [1, 2]

    def test_igualdad_por_id(self):
        """Test que dos profesores con mismo ID son iguales."""
        p1 = ProfesorEntity(id=1, nombre_completo="Ana López")
        p2 = ProfesorEntity(id=1, nombre_completo="Otro Nombre")
        assert p1 == p2

    def test_desigualdad_por_id(self):
        """Test que dos profesores con diferente ID son diferentes."""
        p1 = ProfesorEntity(id=1, nombre_completo="Ana López")
        p2 = ProfesorEntity(id=2, nombre_completo="Ana López")
        assert p1 != p2

    def test_igualdad_sin_id(self):
        """Test que profesores sin ID no son iguales."""
        p1 = ProfesorEntity(nombre_completo="Ana López")
        p2 = ProfesorEntity(nombre_completo="Ana López")
        assert p1 != p2

    def test_hash_por_id(self):
        """Test que el hash se basa en el ID."""
        p1 = ProfesorEntity(id=1, nombre_completo="Ana")
        p2 = ProfesorEntity(id=1, nombre_completo="Otro")
        assert hash(p1) == hash(p2)
        
        # Pueden usarse en sets
        profesores = {p1, p2}
        assert len(profesores) == 1

    def test_ajuste_guardias_tutor(self):
        """Test que tutores tienen el ajuste correcto."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana", es_tutor=True)
        assert profesor.ajuste_guardias == settings.ajuste_tutores

    def test_ajuste_guardias_no_tutor(self):
        """Test que no tutores tienen el ajuste correcto."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana", es_tutor=False)
        assert profesor.ajuste_guardias == settings.ajuste_no_tutores

    def test_guardias_esperadas_calculo(self):
        """Test cálculo de guardias esperadas."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            horas_contrato=HorasContrato(25.0),
            es_tutor=False,
        )
        ratio = 25.0 / settings.max_horas_contrato
        esperadas = ratio * settings.ajuste_no_tutores
        assert profesor.guardias_esperadas == pytest.approx(esperadas)

    def test_puede_hacer_guardia_en_fecha_valida(self):
        """Test que puede hacer guardia en fecha válida."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            fecha_inicio_guardias=hoy - timedelta(days=10),
            fecha_fin_guardias=hoy + timedelta(days=10),
        )
        assert profesor.puede_hacer_guardia_en_fecha(hoy) is True

    def test_puede_hacer_guardia_antes_de_inicio(self):
        """Test que no puede hacer guardia antes de fecha inicio."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            fecha_inicio_guardias=hoy + timedelta(days=5),
        )
        with pytest.raises(ProfesorAusenteError):
            profesor.puede_hacer_guardia_en_fecha(hoy)

    def test_puede_hacer_guardia_despues_de_fin(self):
        """Test que no puede hacer guardia después de fecha fin."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            fecha_fin_guardias=hoy - timedelta(days=5),
        )
        with pytest.raises(ProfesorAusenteError):
            profesor.puede_hacer_guardia_en_fecha(hoy)

    def test_puede_hacer_guardia_dia_no_permitido(self):
        """Test que no puede hacer guardia en día no permitido."""
        hoy = date.today()
        dia_semana = hoy.weekday()
        # Permitir todos EXCEPTO el día de hoy
        dias_permitidos = [d for d in range(7) if d != dia_semana]
        
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            dias_semana_permitidos=dias_permitidos,
        )
        assert profesor.puede_hacer_guardia_en_fecha(hoy) is False

    def test_puede_hacer_guardia_en_turno_manana(self):
        """Test que profesor de mañana puede hacer guardias de mañana."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
        )
        assert profesor.puede_hacer_guardia_en_turno("mañana") is True
        assert profesor.puede_hacer_guardia_en_turno("tarde") is False

    def test_puede_hacer_guardia_en_turno_tarde(self):
        """Test que profesor de tarde puede hacer guardias de tarde."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.TARDE),
        )
        assert profesor.puede_hacer_guardia_en_turno("tarde") is True
        assert profesor.puede_hacer_guardia_en_turno("mañana") is False

    def test_puede_hacer_guardia_en_turno_mixto(self):
        """Test que profesor mixto puede hacer guardias en ambos turnos."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MIXTO, horas_manana=10.0, horas_tarde=10.0),
        )
        assert profesor.puede_hacer_guardia_en_turno("mañana") is True
        assert profesor.puede_hacer_guardia_en_turno("tarde") is True

    def test_puede_hacer_guardia_en_recreo_permitido(self):
        """Test que puede hacer guardia en recreo permitido."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            recreos_permitidos=[1, 2],
        )
        assert profesor.puede_hacer_guardia_en_recreo(1) is True
        assert profesor.puede_hacer_guardia_en_recreo(2) is True
        assert profesor.puede_hacer_guardia_en_recreo(3) is False

    def test_puede_asignar_guardia_caso_valido(self):
        """Test asignación válida de guardia."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
            recreos_permitidos=[1, 2],
        )
        puede, razon = profesor.puede_asignar_guardia(hoy, "mañana", 1)
        assert puede is True
        assert razon is None

    def test_puede_asignar_guardia_turno_invalido(self):
        """Test que no puede asignar guardia en turno inválido."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
        )
        puede, razon = profesor.puede_asignar_guardia(hoy, "tarde", 1)
        assert puede is False
        assert "turno" in razon.lower()

    def test_puede_asignar_guardia_recreo_invalido(self):
        """Test que no puede asignar guardia en recreo inválido."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
            recreos_permitidos=[1],
        )
        puede, razon = profesor.puede_asignar_guardia(hoy, "mañana", 2)
        assert puede is False
        assert "recreo" in razon.lower()

    def test_puede_asignar_guardia_maximo_dia(self):
        """Test que no puede asignar más guardias si ya tiene el máximo."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
        )
        # Llenar hasta el máximo
        for _ in range(settings.max_guardias_por_profesor_dia):
            profesor.asignar_guardia()
        
        puede, razon = profesor.puede_asignar_guardia(hoy, "mañana", 1)
        assert puede is False
        assert "guardias" in razon.lower()

    def test_puede_asignar_guardia_zona_no_preferida(self):
        """Test advertencia cuando zona no es preferida."""
        hoy = date.today()
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana",
            turno=Turno(TurnoEnum.MANANA),
            zona_preferida=ZonaPreferida(zona_id=5),
        )
        puede, razon = profesor.puede_asignar_guardia(hoy, "mañana", 1, zona_id=10)
        assert puede is True
        assert razon is not None  # Advertencia
        assert "zona" in razon.lower()

    def test_asignar_guardia_incrementa_contador(self):
        """Test que asignar guardia incrementa el contador."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana")
        assert profesor.guardias_asignadas_dia == 0

        # Como max_guardias_por_profesor_dia = 1, solo podemos asignar 1
        profesor.asignar_guardia()
        assert profesor.guardias_asignadas_dia == 1

    def test_asignar_guardia_maximo_excedido(self):
        """Test que lanza error al exceder máximo de guardias."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana")
        
        # Llenar hasta el máximo
        for _ in range(settings.max_guardias_por_profesor_dia):
            profesor.asignar_guardia()
        
        # Intentar una más debe fallar
        with pytest.raises(MaxGuardiasDiaExceededError):
            profesor.asignar_guardia()

    def test_liberar_guardia_decrementa_contador(self):
        """Test que liberar guardia decrementa el contador."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana")
        # Asignar una guardia primero
        profesor.asignar_guardia()
        assert profesor.guardias_asignadas_dia == 1

        # Liberar debe decrementar
        profesor.liberar_guardia()
        assert profesor.guardias_asignadas_dia == 0

    def test_liberar_guardia_no_decrementa_si_cero(self):
        """Test que liberar guardia no baja de cero."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana")
        assert profesor.guardias_asignadas_dia == 0
        
        profesor.liberar_guardia()
        assert profesor.guardias_asignadas_dia == 0

    def test_resetear_contador_diario(self):
        """Test reseteo de contador diario."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana")
        # Asignar una guardia
        profesor.asignar_guardia()
        assert profesor.guardias_asignadas_dia == 1

        profesor.resetear_contador_diario()
        assert profesor.guardias_asignadas_dia == 0

    def test_str_representation(self):
        """Test representación en string."""
        profesor = ProfesorEntity(
            id=1,
            nombre_completo="Ana López",
            horas_contrato=HorasContrato(25.0),
            turno=Turno(TurnoEnum.MANANA),
        )
        resultado = str(profesor)
        assert "Ana López" in resultado
        assert "25.0" in resultado

    def test_repr_representation(self):
        """Test representación para debugging."""
        profesor = ProfesorEntity(id=1, nombre_completo="Ana López")
        resultado = repr(profesor)
        assert "ProfesorEntity" in resultado
        assert "id=1" in resultado
        assert "Ana López" in resultado


class TestZonaEntity:
    """Tests para ZonaEntity."""

    def test_construccion_basica(self):
        """Test construcción básica."""
        zona = ZonaEntity(id=1, nombre_zona="Patio Principal")
        assert zona.id == 1
        assert zona.nombre_zona == "Patio Principal"
        assert zona.activa is True

    def test_construccion_completa(self):
        """Test construcción con todos los campos."""
        zona = ZonaEntity(
            id=1,
            nombre_zona="Patio Norte",
            descripcion="Zona de recreo norte",
            capacidad_profesores=3,
            activa=True,
        )
        assert zona.descripcion == "Zona de recreo norte"
        assert zona.capacidad_profesores == 3
        assert zona.tiene_capacidad_limitada is True

    def test_nombre_display(self):
        """Test propiedad nombre_display."""
        zona = ZonaEntity(id=1, nombre_zona="Patio Principal")
        assert zona.nombre_display == "Patio Principal"

    def test_tiene_capacidad_limitada_true(self):
        """Test que tiene_capacidad_limitada es True cuando hay límite."""
        zona = ZonaEntity(id=1, nombre_zona="Patio", capacidad_profesores=3)
        assert zona.tiene_capacidad_limitada is True

    def test_tiene_capacidad_limitada_false(self):
        """Test que tiene_capacidad_limitada es False cuando no hay límite."""
        zona = ZonaEntity(id=1, nombre_zona="Patio")
        assert zona.tiene_capacidad_limitada is False

    def test_puede_asignar_profesor_zona_inactiva(self):
        """Test que no se puede asignar profesor a zona inactiva."""
        zona = ZonaEntity(id=1, nombre_zona="Patio", activa=False)
        assert zona.puede_asignar_profesor(0) is False

    def test_puede_asignar_profesor_sin_limite(self):
        """Test que se puede asignar profesor sin límite de capacidad."""
        zona = ZonaEntity(id=1, nombre_zona="Patio")
        assert zona.puede_asignar_profesor(10) is True
        assert zona.puede_asignar_profesor(100) is True

    def test_puede_asignar_profesor_con_capacidad_disponible(self):
        """Test que se puede asignar profesor con capacidad disponible."""
        zona = ZonaEntity(id=1, nombre_zona="Patio", capacidad_profesores=3)
        assert zona.puede_asignar_profesor(0) is True
        assert zona.puede_asignar_profesor(1) is True
        assert zona.puede_asignar_profesor(2) is True

    def test_puede_asignar_profesor_capacidad_completa(self):
        """Test que no se puede asignar profesor con capacidad completa."""
        zona = ZonaEntity(id=1, nombre_zona="Patio", capacidad_profesores=3)
        assert zona.puede_asignar_profesor(3) is False
        assert zona.puede_asignar_profesor(4) is False

    def test_igualdad_por_id(self):
        """Test que dos zonas con mismo ID son iguales."""
        z1 = ZonaEntity(id=1, nombre_zona="Patio Norte")
        z2 = ZonaEntity(id=1, nombre_zona="Otro Nombre")
        assert z1 == z2

    def test_desigualdad_por_id(self):
        """Test que dos zonas con diferente ID son diferentes."""
        z1 = ZonaEntity(id=1, nombre_zona="Patio")
        z2 = ZonaEntity(id=2, nombre_zona="Patio")
        assert z1 != z2

    def test_igualdad_sin_id(self):
        """Test que zonas sin ID no son iguales."""
        z1 = ZonaEntity(nombre_zona="Patio")
        z2 = ZonaEntity(nombre_zona="Patio")
        assert z1 != z2

    def test_hash_por_id(self):
        """Test que el hash se basa en el ID."""
        z1 = ZonaEntity(id=1, nombre_zona="Patio")
        z2 = ZonaEntity(id=1, nombre_zona="Otro")
        assert hash(z1) == hash(z2)

        # Pueden usarse en sets
        zonas = {z1, z2}
        assert len(zonas) == 1

    def test_str_representation_sin_capacidad(self):
        """Test representación en string sin capacidad."""
        zona = ZonaEntity(id=1, nombre_zona="Patio Principal")
        assert str(zona) == "Patio Principal"

    def test_str_representation_con_capacidad(self):
        """Test representación en string con capacidad."""
        zona = ZonaEntity(id=1, nombre_zona="Patio", capacidad_profesores=3)
        resultado = str(zona)
        assert "Patio" in resultado
        assert "3" in resultado

    def test_repr_representation(self):
        """Test representación para debugging."""
        zona = ZonaEntity(id=1, nombre_zona="Patio Principal")
        resultado = repr(zona)
        assert "ZonaEntity" in resultado
        assert "id=1" in resultado
        assert "Patio Principal" in resultado


class TestGuardiaEntity:
    """Tests para GuardiaEntity."""

    def test_construccion_basica(self):
        """Test construcción básica."""
        guardia = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert guardia.id == 1
        assert guardia.profesor_id == 1
        assert guardia.zona_id == 1
        assert guardia.fecha == date(2025, 11, 8)
        assert guardia.turno == "mañana"
        assert guardia.recreo == 1
        assert guardia.es_sustitucion is False

    def test_construccion_invalida_profesor_cero(self):
        """Test que falla construcción con profesor_id = 0."""
        with pytest.raises(GuardiaInvalidaError):
            GuardiaEntity(
                profesor_id=0,
                zona_id=1,
                fecha=date(2025, 11, 8),
                turno="mañana",
                recreo=1,
            )

    def test_construccion_invalida_zona_cero(self):
        """Test que falla construcción con zona_id = 0."""
        with pytest.raises(GuardiaInvalidaError):
            GuardiaEntity(
                profesor_id=1,
                zona_id=0,
                fecha=date(2025, 11, 8),
                turno="mañana",
                recreo=1,
            )

    def test_construccion_invalida_recreo_cero(self):
        """Test que falla construcción con recreo = 0."""
        with pytest.raises(GuardiaInvalidaError):
            GuardiaEntity(
                profesor_id=1,
                zona_id=1,
                fecha=date(2025, 11, 8),
                turno="mañana",
                recreo=0,
            )

    def test_construccion_invalida_turno(self):
        """Test que falla construcción con turno inválido."""
        with pytest.raises(GuardiaInvalidaError):
            GuardiaEntity(
                profesor_id=1,
                zona_id=1,
                fecha=date(2025, 11, 8),
                turno="mediodía",
                recreo=1,
            )

    def test_clave_unica(self):
        """Test generación de clave única."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        clave = guardia.clave_unica
        assert clave == (date(2025, 11, 8), "mañana", 1, 2)

    def test_clave_profesor_fecha(self):
        """Test generación de clave profesor-fecha."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        clave = guardia.clave_profesor_fecha
        assert clave == (1, date(2025, 11, 8), "mañana", 1)

    def test_es_valida_true(self):
        """Test que es_valida retorna True para guardia válida."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert guardia.es_valida() is True

    def test_es_mismo_momento_true(self):
        """Test que dos guardias en mismo momento son detectadas."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert g1.es_mismo_momento(g2) is True

    def test_es_mismo_momento_false_fecha(self):
        """Test que guardias en diferente fecha no son mismo momento."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 9),
            turno="mañana",
            recreo=1,
        )
        assert g1.es_mismo_momento(g2) is False

    def test_es_mismo_momento_false_turno(self):
        """Test que guardias en diferente turno no son mismo momento."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="tarde",
            recreo=1,
        )
        assert g1.es_mismo_momento(g2) is False

    def test_conflicto_mismo_profesor(self):
        """Test que detecta conflicto con mismo profesor."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert g1.conflicto_con(g2) is True

    def test_conflicto_misma_zona(self):
        """Test que detecta conflicto con misma zona."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert g1.conflicto_con(g2) is True

    def test_sin_conflicto_diferente_momento(self):
        """Test que no hay conflicto en diferente momento."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 9),
            turno="mañana",
            recreo=1,
        )
        assert g1.conflicto_con(g2) is False

    def test_sin_conflicto_diferente_profesor_zona(self):
        """Test que no hay conflicto con diferente profesor y zona."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert g1.conflicto_con(g2) is False

    def test_verificar_sin_conflicto_ok(self):
        """Test que verificar_sin_conflicto pasa sin conflicto."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g1.verificar_sin_conflicto(g2)  # No debe lanzar excepción

    def test_verificar_sin_conflicto_mismo_profesor(self):
        """Test que verificar_sin_conflicto lanza error con mismo profesor."""
        g1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            id=2,
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        with pytest.raises(GuardiaConflictError):
            g1.verificar_sin_conflicto(g2)

    def test_verificar_sin_conflicto_misma_zona(self):
        """Test que verificar_sin_conflicto lanza error con misma zona."""
        g1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            id=2,
            profesor_id=2,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        with pytest.raises(GuardiaConflictError):
            g1.verificar_sin_conflicto(g2)

    def test_marcar_como_sustitucion(self):
        """Test marcar guardia como sustitución."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert guardia.es_sustitucion is False
        assert guardia.profesor_sustituido_id is None

        guardia.marcar_como_sustitucion(profesor_sustituido_id=5)
        assert guardia.es_sustitucion is True
        assert guardia.profesor_sustituido_id == 5

    def test_quitar_sustitucion(self):
        """Test quitar marca de sustitución."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
            es_sustitucion=True,
            profesor_sustituido_id=5,
        )
        assert guardia.es_sustitucion is True

        guardia.quitar_sustitucion()
        assert guardia.es_sustitucion is False
        assert guardia.profesor_sustituido_id is None

    def test_igualdad_por_id(self):
        """Test que dos guardias con mismo ID son iguales."""
        g1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            id=1,
            profesor_id=2,
            zona_id=2,
            fecha=date(2025, 11, 9),
            turno="tarde",
            recreo=2,
        )
        assert g1 == g2

    def test_igualdad_por_clave_unica(self):
        """Test que dos guardias con misma clave única son iguales."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert g1 == g2

    def test_desigualdad(self):
        """Test que guardias diferentes no son iguales."""
        g1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            id=2,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 9),
            turno="mañana",
            recreo=1,
        )
        assert g1 != g2

    def test_hash_por_id(self):
        """Test que el hash se basa en el ID."""
        g1 = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            id=1,
            profesor_id=2,
            zona_id=2,
            fecha=date(2025, 11, 9),
            turno="tarde",
            recreo=2,
        )
        assert hash(g1) == hash(g2)

    def test_hash_por_clave_unica(self):
        """Test que el hash sin ID se basa en clave única."""
        g1 = GuardiaEntity(
            profesor_id=1,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        g2 = GuardiaEntity(
            profesor_id=2,
            zona_id=1,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        assert hash(g1) == hash(g2)

    def test_str_representation(self):
        """Test representación en string."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        resultado = str(guardia)
        assert "2025-11-08" in resultado
        assert "mañana" in resultado
        assert "R1" in resultado
        assert "P:1" in resultado
        assert "Z:2" in resultado

    def test_str_representation_sustitucion(self):
        """Test representación en string con sustitución."""
        guardia = GuardiaEntity(
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
            es_sustitucion=True,
        )
        resultado = str(guardia)
        assert "SUSTITUCIÓN" in resultado

    def test_repr_representation(self):
        """Test representación para debugging."""
        guardia = GuardiaEntity(
            id=1,
            profesor_id=1,
            zona_id=2,
            fecha=date(2025, 11, 8),
            turno="mañana",
            recreo=1,
        )
        resultado = repr(guardia)
        assert "GuardiaEntity" in resultado
        assert "id=1" in resultado
        assert "profesor_id=1" in resultado
        assert "zona_id=2" in resultado


