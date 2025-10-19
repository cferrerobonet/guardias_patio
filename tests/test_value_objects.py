"""
Tests unitarios para los Value Objects:
- Email
- Turno
- HorasContrato
- ZonaPreferida
Valida construcción, validaciones y edge cases.
"""
import pytest

from src.domain.value_objects import Email, HorasContrato, Turno, TurnoEnum, ZonaPreferida


class TestEmail:
    def test_email_valido(self):
        email = Email("usuario@dominio.com")
        assert email.value == "usuario@dominio.com"
    def test_email_invalido(self):
        with pytest.raises(Exception):
            Email("no-es-email")

class TestTurno:
    def test_turno_manana(self):
        turno = Turno(TurnoEnum.MANANA)
        assert turno.value == TurnoEnum.MANANA
        assert turno.horas_manana is None
        assert turno.horas_tarde is None
    def test_turno_mixto_valido(self):
        turno = Turno(TurnoEnum.MIXTO, horas_manana=10.0, horas_tarde=15.0)
        assert turno.value == TurnoEnum.MIXTO
        assert turno.horas_manana == 10.0
        assert turno.horas_tarde == 15.0
    def test_turno_mixto_sin_horas(self):
        with pytest.raises(Exception):
            Turno(TurnoEnum.MIXTO)
    def test_turno_simple_con_horas(self):
        with pytest.raises(Exception):
            Turno(TurnoEnum.MANANA, horas_manana=10.0)

class TestHorasContrato:
    def test_horas_valido(self):
        horas = HorasContrato(20.0)
        assert horas.value == 20.0
    def test_horas_negativas(self):
        with pytest.raises(Exception):
            HorasContrato(-5.0)

class TestZonaPreferida:
    def test_sin_preferencia(self):
        zp = ZonaPreferida.sin_preferencia()
        assert zp.value is None
    def test_con_preferencia(self):
        zp = ZonaPreferida("Patio Central")
        assert zp.value == "Patio Central"
