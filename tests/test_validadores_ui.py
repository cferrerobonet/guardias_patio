"""
Tests para Validadores UI con Feedback Visual.

Sprint 8 - Task 8.6
"""

import pytest
from PyQt6.QtWidgets import QLabel, QLineEdit

from widgets.validadores_ui import (
    ValidadorEmail,
    ValidadorFormulario,
    ValidadorHorasContrato,
    ValidadorNombreCompleto,
    ValidadorRequerido,
    aplicar_validacion_email,
    aplicar_validacion_horas,
    aplicar_validacion_nombre,
    aplicar_validacion_requerido,
    crear_label_error,
)

# ========== FIXTURES ==========

@pytest.fixture
def qapp(qapp):
    """Fixture para QApplication (provided by pytest-qt)."""
    return qapp


@pytest.fixture
def campo_texto(qapp):
    """Crear QLineEdit para tests."""
    return QLineEdit()


@pytest.fixture
def label_error(qapp):
    """Crear QLabel para mensajes de error."""
    return QLabel()


# ========== TESTS VALIDADOR EMAIL ==========

class TestValidadorEmail:
    """Tests para ValidadorEmail."""

    def test_email_valido(self, campo_texto, label_error, qtbot):
        """Validar email correcto."""
        validador = ValidadorEmail(campo_texto, label_error)

        # Simular entrada
        campo_texto.setText("profesor@example.com")

        # Validar inmediatamente
        assert validador.validar_inmediato() is True
        assert validador.es_valido is True
        assert "✓" in label_error.text()

    def test_email_invalido_sin_arroba(self, campo_texto, label_error, qtbot):
        """Rechazar email sin @."""
        validador = ValidadorEmail(campo_texto, label_error)

        campo_texto.setText("profesorexample.com")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False
        assert "⚠️" in label_error.text()

    def test_email_invalido_sin_dominio(self, campo_texto, label_error, qtbot):
        """Rechazar email sin dominio."""
        validador = ValidadorEmail(campo_texto, label_error)

        campo_texto.setText("profesor@")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False

    def test_email_vacio_estado_neutral(self, campo_texto, label_error, qtbot):
        """Email vacío debe estar en estado neutral."""
        validador = ValidadorEmail(campo_texto, label_error)

        campo_texto.setText("")
        qtbot.wait(100)

        assert validador.es_valido is False
        assert label_error.text() == ""

    def test_reset(self, campo_texto, label_error, qtbot):
        """Resetear validador a estado inicial."""
        validador = ValidadorEmail(campo_texto, label_error)

        campo_texto.setText("test@example.com")
        validador.validar_inmediato()

        validador.reset()

        assert campo_texto.text() == ""
        assert validador.es_valido is False
        assert label_error.text() == ""


# ========== TESTS VALIDADOR NOMBRE COMPLETO ==========

class TestValidadorNombreCompleto:
    """Tests para ValidadorNombreCompleto."""

    def test_nombre_valido(self, campo_texto, label_error, qtbot):
        """Validar nombre completo correcto (formato APELLIDOS, NOMBRE)."""
        validador = ValidadorNombreCompleto(campo_texto, label_error)

        campo_texto.setText("PÉREZ GARCÍA, Juan")

        assert validador.validar_inmediato() is True
        assert validador.es_valido is True
        assert "✓" in label_error.text()

    def test_nombre_invalido_sin_coma(self, campo_texto, label_error, qtbot):
        """Rechazar nombre sin coma."""
        validador = ValidadorNombreCompleto(campo_texto, label_error)

        campo_texto.setText("Juan Pérez García")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False
        assert "⚠️" in label_error.text()

    def test_nombre_invalido_solo_apellidos(self, campo_texto, label_error, qtbot):
        """Rechazar nombre con solo apellidos."""
        validador = ValidadorNombreCompleto(campo_texto, label_error)

        campo_texto.setText("PÉREZ GARCÍA,")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False

    def test_nombre_con_tildes(self, campo_texto, label_error, qtbot):
        """Aceptar nombres con tildes."""
        validador = ValidadorNombreCompleto(campo_texto, label_error)

        campo_texto.setText("HERNÁNDEZ, María José")
        assert validador.validar_inmediato() is True
        assert validador.es_valido is True


# ========== TESTS VALIDADOR HORAS CONTRATO ==========

class TestValidadorHorasContrato:
    """Tests para ValidadorHorasContrato."""

    def test_horas_validas(self, campo_texto, label_error, qtbot):
        """Validar horas correctas."""
        validador = ValidadorHorasContrato(campo_texto, label_error)

        campo_texto.setText("20")

        assert validador.validar_inmediato() is True
        assert validador.es_valido is True
        assert "✓" in label_error.text()

    def test_horas_invalidas_negativas(self, campo_texto, label_error, qtbot):
        """Rechazar horas negativas."""
        validador = ValidadorHorasContrato(campo_texto, label_error)

        campo_texto.setText("-5")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False
        assert "⚠️" in label_error.text()

    def test_horas_invalidas_excesivas(self, campo_texto, label_error, qtbot):
        """Rechazar horas excesivas (>40)."""
        validador = ValidadorHorasContrato(campo_texto, label_error)

        campo_texto.setText("50")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False
        assert "⚠️" in label_error.text()

    def test_horas_invalidas_no_numero(self, campo_texto, label_error, qtbot):
        """Rechazar texto no numérico."""
        validador = ValidadorHorasContrato(campo_texto, label_error)

        campo_texto.setText("abc")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False
        assert "número" in label_error.text().lower()

    def test_horas_decimales_aceptadas(self, campo_texto, label_error, qtbot):
        """Aceptar horas decimales válidas."""
        validador = ValidadorHorasContrato(campo_texto, label_error)

        campo_texto.setText("20.5")
        assert validador.validar_inmediato() is True
        assert validador.es_valido is True


# ========== TESTS VALIDADOR REQUERIDO ==========

class TestValidadorRequerido:
    """Tests para ValidadorRequerido."""

    def test_campo_completo(self, campo_texto, label_error, qtbot):
        """Validar campo con contenido."""
        validador = ValidadorRequerido(campo_texto, label_error, "Nombre")

        campo_texto.setText("Contenido")

        assert validador.validar_inmediato() is True
        assert validador.es_valido is True
        assert "✓" in label_error.text()

    def test_campo_vacio(self, campo_texto, label_error, qtbot):
        """Rechazar campo vacío."""
        validador = ValidadorRequerido(campo_texto, label_error, "Nombre")

        campo_texto.setText("")
        assert validador.validar_inmediato() is False
        assert validador.es_valido is False

    def test_campo_solo_espacios(self, campo_texto, label_error, qtbot):
        """Rechazar campo con solo espacios."""
        validador = ValidadorRequerido(campo_texto, label_error, "Nombre")

        campo_texto.setText("   ")
        validador.validar_inmediato()

        assert validador.es_valido is False
        # Campo solo con espacios se considera vacío (tras .strip())
        assert label_error.text() == ""  # Estado neutral

    def test_mensaje_personalizado(self, campo_texto, label_error, qtbot):
        """Verificar mensaje con nombre de campo personalizado."""
        validador = ValidadorRequerido(campo_texto, label_error, "Email Corporativo")

        campo_texto.setText("contenido")  # Con contenido para ver mensaje de éxito
        validador.validar_inmediato()

        assert validador.es_valido is True
        assert "✓" in label_error.text()


# ========== TESTS VALIDADOR FORMULARIO ==========

class TestValidadorFormulario:
    """Tests para ValidadorFormulario."""

    def test_formulario_todos_validos(self, qapp, qtbot):
        """Validar formulario completo con todos los campos válidos."""
        # Crear campos
        campo_nombre = QLineEdit()
        campo_email = QLineEdit()
        campo_horas = QLineEdit()

        label_nombre = QLabel()
        label_email = QLabel()
        label_horas = QLabel()

        # Crear validadores
        val_nombre = ValidadorNombreCompleto(campo_nombre, label_nombre)
        val_email = ValidadorEmail(campo_email, label_email)
        val_horas = ValidadorHorasContrato(campo_horas, label_horas)

        # Crear formulario
        formulario = ValidadorFormulario()
        formulario.agregar_validador(val_nombre)
        formulario.agregar_validador(val_email)
        formulario.agregar_validador(val_horas)

        # Llenar datos válidos (formato APELLIDOS, NOMBRE)
        campo_nombre.setText("PÉREZ, Juan")
        campo_email.setText("juan@example.com")
        campo_horas.setText("25")

        # Validar
        es_valido, errores = formulario.validar_todo()

        assert es_valido is True
        assert len(errores) == 0

    def test_formulario_con_errores(self, qapp, qtbot):
        """Validar formulario con campos inválidos."""
        # Crear campos
        campo_nombre = QLineEdit()
        campo_email = QLineEdit()

        label_nombre = QLabel()
        label_email = QLabel()

        # Crear validadores
        val_nombre = ValidadorNombreCompleto(campo_nombre, label_nombre)
        val_email = ValidadorEmail(campo_email, label_email)

        # Crear formulario
        formulario = ValidadorFormulario()
        formulario.agregar_validador(val_nombre)
        formulario.agregar_validador(val_email)

        # Llenar datos inválidos
        campo_nombre.setText("Incompleto")  # Sin coma (formato inválido)
        campo_email.setText("invalido")  # Sin @

        # Validar
        es_valido, errores = formulario.validar_todo()

        assert es_valido is False
        assert len(errores) >= 1  # Al menos un error

    def test_formulario_reset(self, qapp, qtbot):
        """Resetear todos los campos del formulario."""
        campo = QLineEdit()
        label = QLabel()
        validador = ValidadorEmail(campo, label)

        formulario = ValidadorFormulario()
        formulario.agregar_validador(validador)

        # Llenar y validar
        campo.setText("test@example.com")
        validador.validar_inmediato()

        # Reset
        formulario.reset_todo()

        assert campo.text() == ""
        assert validador.es_valido is False

    def test_son_todos_validos(self, qapp, qtbot):
        """Verificar estado de validez sin ejecutar validación."""
        campo = QLineEdit()
        label = QLabel()
        validador = ValidadorEmail(campo, label)

        formulario = ValidadorFormulario()
        formulario.agregar_validador(validador)

        # Inicialmente inválido
        assert formulario.son_todos_validos() is False

        # Validar
        campo.setText("test@example.com")
        validador.validar_inmediato()

        # Ahora válido
        assert formulario.son_todos_validos() is True


# ========== TESTS HELPER FUNCTIONS ==========

class TestHelperFunctions:
    """Tests para funciones auxiliares."""

    def test_crear_label_error(self, qapp):
        """Crear label de error configurado."""
        label = crear_label_error()

        assert isinstance(label, QLabel)
        assert label.wordWrap() is True
        assert label.maximumHeight() == 30

    def test_aplicar_validacion_email(self, qapp):
        """Helper para aplicar validación de email."""
        campo = QLineEdit()
        validador, label = aplicar_validacion_email(campo)

        assert isinstance(validador, ValidadorEmail)
        assert isinstance(label, QLabel)

    def test_aplicar_validacion_nombre(self, qapp):
        """Helper para aplicar validación de nombre."""
        campo = QLineEdit()
        validador, label = aplicar_validacion_nombre(campo)

        assert isinstance(validador, ValidadorNombreCompleto)
        assert isinstance(label, QLabel)

    def test_aplicar_validacion_horas(self, qapp):
        """Helper para aplicar validación de horas."""
        campo = QLineEdit()
        validador, label = aplicar_validacion_horas(campo)

        assert isinstance(validador, ValidadorHorasContrato)
        assert isinstance(label, QLabel)

    def test_aplicar_validacion_requerido(self, qapp):
        """Helper para aplicar validación de campo requerido."""
        campo = QLineEdit()
        validador, label = aplicar_validacion_requerido(campo, "Test")

        assert isinstance(validador, ValidadorRequerido)
        assert isinstance(label, QLabel)
        assert validador.nombre_campo == "Test"


# ========== TESTS DE INTEGRACIÓN ==========

@pytest.mark.integration
class TestIntegracionValidadoresUI:
    """Tests de integración de validadores en formularios."""

    def test_flujo_completo_validacion(self, qapp, qtbot):
        """Simular flujo completo de llenado de formulario."""
        # Crear formulario completo
        campo_nombre = QLineEdit()
        campo_email = QLineEdit()
        campo_horas = QLineEdit()

        val_nombre, label_nombre = aplicar_validacion_nombre(campo_nombre)
        val_email, label_email = aplicar_validacion_email(campo_email)
        val_horas, label_horas = aplicar_validacion_horas(campo_horas)

        formulario = ValidadorFormulario()
        formulario.agregar_validador(val_nombre)
        formulario.agregar_validador(val_email)
        formulario.agregar_validador(val_horas)

        # Simular usuario llenando campos
        campo_nombre.setText("GARCÍA, María")
        qtbot.wait(50)

        campo_email.setText("maria@example.com")
        qtbot.wait(50)

        campo_horas.setText("30")
        qtbot.wait(50)

        # Validar antes de guardar
        es_valido, errores = formulario.validar_todo()

        assert es_valido is True
        assert len(errores) == 0

        # Verificar feedback visual
        assert "✓" in label_nombre.text()
        assert "✓" in label_email.text()
        assert "✓" in label_horas.text()

    def test_corregir_errores_en_tiempo_real(self, qapp, qtbot):
        """Simular corrección de errores mientras el usuario escribe."""
        campo_email = QLineEdit()
        validador, label = aplicar_validacion_email(campo_email)

        # Usuario escribe email inválido (sin @ todavía)
        campo_email.setText("invalido")
        validador.validar_inmediato()

        assert validador.es_valido is False
        assert "⚠️" in label.text()

        # Usuario corrige agregando dominio completo
        campo_email.setText("valido@example.com")
        validador.validar_inmediato()

        # Ahora válido
        assert validador.es_valido is True
        assert "✓" in label.text()
