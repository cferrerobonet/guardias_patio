"""
Tests unitarios para el módulo de validadores.

Tests para todas las funciones de validación de datos.
"""

from datetime import date

from utils.validators import (
    validar_dias_semana,
    validar_email,
    validar_fecha,
    validar_horas_contrato,
    validar_nombre_completo,
    validar_rango_fechas,
    validar_turno,
)


class TestValidarEmail:
    """Tests para validar_email()"""

    def test_email_valido(self):
        """Email con formato correcto debe ser válido"""
        valido, error = validar_email("profesor@colegio.edu")
        assert valido is True
        assert error is None

    def test_email_vacio(self):
        """Email vacío no debe ser válido"""
        valido, error = validar_email("")
        assert valido is False
        assert "vacío" in error.lower()

    def test_email_sin_arroba(self):
        """Email sin @ no debe ser válido"""
        valido, error = validar_email("profesorcolegio.edu")
        assert valido is False
        assert "inválido" in error.lower()

    def test_email_sin_dominio(self):
        """Email sin dominio no debe ser válido"""
        valido, error = validar_email("profesor@")
        assert valido is False
        assert "inválido" in error.lower()

    def test_email_con_espacios(self):
        """Email con espacios debe ser considerado vacío tras strip"""
        valido, error = validar_email("   ")
        assert valido is False


class TestValidarNombreCompleto:
    """Tests para validar_nombre_completo()"""

    def test_nombre_formato_correcto(self):
        """Nombre con formato APELLIDOS, NOMBRE debe ser válido"""
        valido, error = validar_nombre_completo("GARCÍA LÓPEZ, JUAN")
        assert valido is True
        assert error is None

    def test_nombre_vacio(self):
        """Nombre vacío no debe ser válido"""
        valido, error = validar_nombre_completo("")
        assert valido is False
        assert "vacío" in error.lower()

    def test_nombre_sin_coma(self):
        """Nombre sin coma no debe ser válido"""
        valido, error = validar_nombre_completo("GARCÍA LÓPEZ JUAN")
        assert valido is False
        assert "coma" in error.lower()

    def test_nombre_multiples_comas(self):
        """Nombre con más de una coma no debe ser válido"""
        valido, error = validar_nombre_completo("GARCÍA, LÓPEZ, JUAN")
        assert valido is False
        assert "una sola coma" in error.lower()

    def test_nombre_apellidos_vacios(self):
        """Apellidos vacíos no deben ser válidos"""
        valido, error = validar_nombre_completo(", JUAN")
        assert valido is False
        assert "presentes" in error.lower()

    def test_nombre_nombre_vacio(self):
        """Nombre vacío después de coma no debe ser válido"""
        valido, error = validar_nombre_completo("GARCÍA LÓPEZ,")
        assert valido is False
        assert "presentes" in error.lower()


class TestValidarFecha:
    """Tests para validar_fecha()"""

    def test_fecha_valida(self):
        """Fecha válida debe pasar validación"""
        valido, error = validar_fecha(date(2025, 9, 1))
        assert valido is True
        assert error is None

    def test_fecha_none(self):
        """Fecha None no debe ser válida"""
        valido, error = validar_fecha(None)
        assert valido is False
        assert "vacía" in error.lower()

    def test_fecha_con_minima(self):
        """Fecha posterior a mínima debe ser válida"""
        fecha_min = date(2025, 1, 1)
        fecha_test = date(2025, 9, 1)
        valido, error = validar_fecha(fecha_test, fecha_minima=fecha_min)
        assert valido is True
        assert error is None

    def test_fecha_anterior_a_minima(self):
        """Fecha anterior a mínima no debe ser válida"""
        fecha_min = date(2025, 9, 1)
        fecha_test = date(2025, 1, 1)
        valido, error = validar_fecha(fecha_test, fecha_minima=fecha_min)
        assert valido is False
        assert "anterior" in error.lower()


class TestValidarRangoFechas:
    """Tests para validar_rango_fechas()"""

    def test_rango_valido(self):
        """Rango con inicio < fin debe ser válido"""
        inicio = date(2025, 9, 1)
        fin = date(2026, 6, 30)
        valido, error = validar_rango_fechas(inicio, fin)
        assert valido is True
        assert error is None

    def test_rango_invertido(self):
        """Rango con inicio >= fin no debe ser válido"""
        inicio = date(2026, 6, 30)
        fin = date(2025, 9, 1)
        valido, error = validar_rango_fechas(inicio, fin)
        assert valido is False
        assert "anterior" in error.lower()

    def test_fechas_iguales(self):
        """Fechas iguales no deben ser válidas"""
        fecha = date(2025, 9, 1)
        valido, error = validar_rango_fechas(fecha, fecha)
        assert valido is False

    def test_fecha_inicio_none(self):
        """Fecha inicio None no debe ser válida"""
        valido, error = validar_rango_fechas(None, date(2025, 9, 1))
        assert valido is False
        assert "presentes" in error.lower()


class TestValidarHorasContrato:
    """Tests para validar_horas_contrato()"""

    def test_horas_validas(self):
        """Horas entre 0 y 40 deben ser válidas"""
        valido, error = validar_horas_contrato(30.0)
        assert valido is True
        assert error is None

    def test_horas_cero(self):
        """Horas cero no deben ser válidas"""
        valido, error = validar_horas_contrato(0.0)
        assert valido is False
        assert "positivo" in error.lower()

    def test_horas_negativas(self):
        """Horas negativas no deben ser válidas"""
        valido, error = validar_horas_contrato(-5.0)
        assert valido is False
        assert "positivo" in error.lower()

    def test_horas_excesivas(self):
        """Horas superiores a 40 no deben ser válidas"""
        valido, error = validar_horas_contrato(45.0)
        assert valido is False
        assert "40" in error

    def test_horas_limite(self):
        """40 horas exactas deben ser válidas"""
        valido, error = validar_horas_contrato(40.0)
        assert valido is True


class TestValidarTurno:
    """Tests para validar_turno()"""

    def test_turno_manana(self):
        """Turno 'mañana' debe ser válido"""
        valido, error = validar_turno("mañana")
        assert valido is True
        assert error is None

    def test_turno_tarde(self):
        """Turno 'tarde' debe ser válido"""
        valido, error = validar_turno("tarde")
        assert valido is True
        assert error is None

    def test_turno_mixto(self):
        """Turno 'mixto' debe ser válido"""
        valido, error = validar_turno("mixto")
        assert valido is True
        assert error is None

    def test_turno_invalido(self):
        """Turno no válido no debe pasar validación"""
        valido, error = validar_turno("noche")
        assert valido is False
        assert "inválido" in error.lower()

    def test_turno_mayusculas(self):
        """Turno en mayúsculas no debe ser válido (case-sensitive)"""
        valido, error = validar_turno("MAÑANA")
        assert valido is False


class TestValidarDiasSemana:
    """Tests para validar_dias_semana()"""

    def test_dias_validos(self):
        """String con días válidos debe pasar validación"""
        valido, error = validar_dias_semana("0,1,2,3,4")
        assert valido is True
        assert error is None

    def test_dias_vacio(self):
        """String vacío debe ser válido (opcional)"""
        valido, error = validar_dias_semana("")
        assert valido is True
        assert error is None

    def test_dias_none(self):
        """None debe ser válido (opcional)"""
        valido, error = validar_dias_semana(None)
        assert valido is True
        assert error is None

    def test_dias_fuera_rango(self):
        """Días fuera del rango 0-6 no deben ser válidos"""
        valido, error = validar_dias_semana("0,1,7")
        assert valido is False
        assert "0" in error and "6" in error

    def test_dias_formato_invalido(self):
        """Formato no numérico no debe ser válido"""
        valido, error = validar_dias_semana("lun,mar,mie")
        assert valido is False
        assert "formato" in error.lower() or "inválido" in error.lower()

    def test_dias_con_espacios(self):
        """Días con espacios deben funcionar (se hace strip)"""
        valido, error = validar_dias_semana("0, 1, 2")
        assert valido is True
