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

    def test_email_igualdad(self):
        """Test: comparación de emails."""
        email1 = Email("test@example.com")
        email2 = Email("test@example.com")
        email3 = Email("other@example.com")

        assert email1 == email2
        assert email1 != email3

    def test_email_sin_arroba(self):
        """Test: email sin @ debe fallar."""
        with pytest.raises(Exception):
            Email("usuariodominio.com")

    def test_email_sin_dominio(self):
        """Test: email sin dominio debe fallar."""
        with pytest.raises(Exception):
            Email("usuario@")

    def test_email_repr(self):
        """Test: representación del email."""
        email = Email("test@example.com")
        assert "test@example.com" in repr(email)

    def test_email_formatos_validos(self):
        """Test: diferentes formatos válidos."""
        assert Email("user@example.com").value == "user@example.com"
        assert Email("user.name@example.com").value == "user.name@example.com"
        assert Email("user+tag@example.co.uk").value == "user+tag@example.co.uk"


class TestTurno:
    def test_turno_manana(self):
        turno = Turno(TurnoEnum.MANANA)
        assert turno.value == TurnoEnum.MANANA
        assert turno.horas_manana is None
        assert turno.horas_tarde is None

    def test_turno_tarde(self):
        """Test: crear turno tarde."""
        turno = Turno(TurnoEnum.TARDE)
        assert turno.value == TurnoEnum.TARDE
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

    def test_turno_str(self):
        """Test: representación string."""
        turno_m = Turno(TurnoEnum.MANANA)
        turno_t = Turno(TurnoEnum.TARDE)
        turno_mix = Turno(TurnoEnum.MIXTO, horas_manana=10.0, horas_tarde=15.0)

        assert "mañana" in str(turno_m).lower() or "MANANA" in str(turno_m)
        assert "tarde" in str(turno_t).lower() or "TARDE" in str(turno_t)
        assert "mixto" in str(turno_mix).lower() or "MIXTO" in str(turno_mix)

    def test_turno_igualdad(self):
        """Test: comparación de turnos."""
        turno1 = Turno(TurnoEnum.MANANA)
        turno2 = Turno(TurnoEnum.MANANA)
        turno3 = Turno(TurnoEnum.TARDE)

        assert turno1 == turno2
        assert turno1 != turno3

    def test_turno_es_manana_property(self):
        """Test: verificar propiedad es_manana."""
        turno_m = Turno(TurnoEnum.MANANA)
        turno_t = Turno(TurnoEnum.TARDE)

        assert turno_m.es_manana is True
        assert turno_t.es_manana is False

    def test_turno_es_tarde_property(self):
        """Test: verificar propiedad es_tarde."""
        turno_m = Turno(TurnoEnum.MANANA)
        turno_t = Turno(TurnoEnum.TARDE)

        assert turno_m.es_tarde is False
        assert turno_t.es_tarde is True

    def test_turno_es_mixto_property(self):
        """Test: verificar propiedad es_mixto."""
        turno_m = Turno(TurnoEnum.MANANA)
        turno_mix = Turno(TurnoEnum.MIXTO, horas_manana=10.0, horas_tarde=15.0)

        assert turno_m.es_mixto is False
        assert turno_mix.es_mixto is True

    def test_turno_valores_validos(self):
        """Test: todos los valores de enum son válidos."""
        for valor in TurnoEnum:
            if valor == TurnoEnum.MIXTO:
                turno = Turno(valor, horas_manana=10.0, horas_tarde=15.0)
            else:
                turno = Turno(valor)
            assert turno.value == valor


class TestHorasContrato:
    def test_horas_valido(self):
        horas = HorasContrato(20.0)
        assert horas.value == 20.0

    def test_horas_negativas(self):
        with pytest.raises(Exception):
            HorasContrato(-5.0)

    def test_horas_maximas(self):
        """Test: horas máximas (40.0)."""
        horas = HorasContrato(40.0)
        assert horas.value == 40.0

    def test_horas_exceden_maximo(self):
        """Test: horas > 40 deben fallar."""
        with pytest.raises(Exception):
            HorasContrato(50.0)

    def test_horas_float(self):
        """Test: conversión a float."""
        horas = HorasContrato(25.5)
        assert float(horas) == 25.5

    def test_horas_str(self):
        """Test: representación string."""
        horas = HorasContrato(25.5)
        assert "25.5" in str(horas)

    def test_horas_comparacion(self):
        """Test: comparación de horas."""
        horas1 = HorasContrato(20.0)
        horas2 = HorasContrato(25.0)
        horas3 = HorasContrato(20.0)

        assert horas1 < horas2
        assert horas2 > horas1
        assert horas1 <= horas3
        assert horas1 >= horas3
        assert horas1 == horas3
        assert horas1 != horas2

    def test_horas_limites_minimos(self):
        """Test: horas mínimas permitidas (1.0)."""
        horas = HorasContrato(1.0)
        assert horas.value == 1.0

    def test_horas_debajo_minimo(self):
        """Test: horas < 1.0 deben fallar."""
        with pytest.raises(Exception):
            HorasContrato(0.5)

    def test_horas_valores_intermedios(self):
        """Test: diferentes valores intermedios."""
        for valor in [1.0, 10.5, 20.0, 25.0, 30.5, 40.0]:
            horas = HorasContrato(valor)
            assert horas.value == valor

    def test_horas_repr(self):
        """Test: representación repr."""
        horas = HorasContrato(25.0)
        assert "25.0" in repr(horas) or "HorasContrato" in repr(horas)


class TestZonaPreferida:
    def test_sin_preferencia(self):
        zp = ZonaPreferida.sin_preferencia()
        assert zp.value is None

    def test_con_preferencia(self):
        zp = ZonaPreferida("Patio Central")
        assert zp.value == "Patio Central"

    def test_zona_str(self):
        """Test: representación string."""
        zona = ZonaPreferida("Patio Central")
        assert "Patio Central" in str(zona)

        zona_sin = ZonaPreferida.sin_preferencia()
        assert "Sin preferencia" in str(zona_sin) or "sin preferencia" in str(zona_sin).lower()

    def test_zona_igualdad(self):
        """Test: comparación de zonas."""
        zona1 = ZonaPreferida("Patio A")
        zona2 = ZonaPreferida("Patio A")
        zona3 = ZonaPreferida("Patio B")

        assert zona1 == zona2
        assert zona1 != zona3

    def test_zona_tiene_preferencia_property(self):
        """Test: verificar propiedad tiene_preferencia."""
        zona_con = ZonaPreferida("Patio Central")
        zona_sin = ZonaPreferida.sin_preferencia()

        assert zona_con.tiene_preferencia is True
        assert zona_sin.tiene_preferencia is False

    def test_zona_diferentes_nombres(self):
        """Test: diferentes nombres de zona."""
        zonas = ["Patio Central", "Entrada Principal", "Biblioteca", "Cafetería", "Zona Deportiva"]

        for nombre in zonas:
            zona = ZonaPreferida(nombre)
            assert zona.value == nombre
            assert zona.tiene_preferencia is True

    def test_zona_repr(self):
        """Test: representación repr."""
        zona = ZonaPreferida("Patio A")
        repr_str = repr(zona)
        assert "Patio A" in repr_str or "ZonaPreferida" in repr_str
