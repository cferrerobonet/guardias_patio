"""
Tests unitarios para las excepciones personalizadas.

Valida que las excepciones se crean correctamente y contienen
la información esperada.
"""

from src.utils.exceptions import (
    ConfiguracionError,
    DatabaseError,
    DuplicateGuardiaError,
    ExportError,
    GuardiaConflictError,
    GuardiasBaseException,
    ImportError,
    InsufficientProfesoresError,
    MaxGuardiasExceededError,
    ProfesorNotFoundError,
    ValidationError,
    ZonaNotFoundError,
)


class TestGuardiasBaseException:
    """Tests para la excepción base"""

    def test_crear_con_mensaje(self):
        """Crear excepción solo con mensaje"""
        exc = GuardiasBaseException("Error de prueba")
        assert exc.message == "Error de prueba"
        assert exc.detalles is None

    def test_crear_con_detalles(self):
        """Crear excepción con mensaje y detalles"""
        exc = GuardiasBaseException("Error", detalles="Detalle adicional")
        assert exc.message == "Error"
        assert exc.detalles == "Detalle adicional"

    def test_str_sin_detalles(self):
        """__str__ sin detalles debe devolver solo el mensaje"""
        exc = GuardiasBaseException("Error de prueba")
        assert str(exc) == "Error de prueba"

    def test_str_con_detalles(self):
        """__str__ con detalles debe incluir ambos"""
        exc = GuardiasBaseException("Error", detalles="Detalle")
        resultado = str(exc)
        assert "Error" in resultado
        assert "Detalle" in resultado


class TestValidationError:
    """Tests para ValidationError"""

    def test_herencia(self):
        """ValidationError debe heredar de GuardiasBaseException"""
        exc = ValidationError("Error de validación")
        assert isinstance(exc, GuardiasBaseException)

    def test_crear_con_mensaje(self):
        """Crear ValidationError con mensaje"""
        exc = ValidationError("Email inválido")
        assert exc.message == "Email inválido"


class TestDatabaseError:
    """Tests para DatabaseError"""

    def test_herencia(self):
        """DatabaseError debe heredar de GuardiasBaseException"""
        exc = DatabaseError("Error de BD")
        assert isinstance(exc, GuardiasBaseException)


class TestConfiguracionError:
    """Tests para ConfiguracionError"""

    def test_herencia(self):
        """ConfiguracionError debe heredar de GuardiasBaseException"""
        exc = ConfiguracionError("Config incorrecta")
        assert isinstance(exc, GuardiasBaseException)


class TestProfesorNotFoundError:
    """Tests para ProfesorNotFoundError"""

    def test_crear_con_id(self):
        """Crear excepción con ID de profesor"""
        exc = ProfesorNotFoundError(profesor_id=123)
        assert exc.profesor_id == 123
        assert "123" in exc.message

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ProfesorNotFoundError(profesor_id=1)
        assert isinstance(exc, GuardiasBaseException)

    def test_mensaje_descriptivo(self):
        """Mensaje debe ser descriptivo"""
        exc = ProfesorNotFoundError(profesor_id=456)
        mensaje = str(exc)
        assert "456" in mensaje
        assert "no encontrado" in mensaje.lower()


class TestZonaNotFoundError:
    """Tests para ZonaNotFoundError"""

    def test_crear_con_id(self):
        """Crear excepción con ID de zona"""
        exc = ZonaNotFoundError(zona_id=789)
        assert exc.zona_id == 789
        assert "789" in exc.message

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ZonaNotFoundError(zona_id=1)
        assert isinstance(exc, GuardiasBaseException)


class TestGuardiaConflictError:
    """Tests para GuardiaConflictError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = GuardiaConflictError("Conflicto")
        assert isinstance(exc, GuardiasBaseException)


class TestMaxGuardiasExceededError:
    """Tests para MaxGuardiasExceededError"""

    def test_crear_con_parametros(self):
        """Crear excepción con nombre y fecha"""
        exc = MaxGuardiasExceededError("García, Juan", "2025-10-16")
        mensaje = str(exc)
        assert "García, Juan" in mensaje
        assert "2025-10-16" in mensaje

    def test_herencia(self):
        """Debe heredar de GuardiaConflictError"""
        exc = MaxGuardiasExceededError("Profesor", "2025-10-16")
        assert isinstance(exc, GuardiaConflictError)
        assert isinstance(exc, GuardiasBaseException)

    def test_mensaje_descriptivo(self):
        """Mensaje debe indicar máximo excedido"""
        exc = MaxGuardiasExceededError("López, Ana", "2025-10-20")
        mensaje = str(exc).lower()
        assert "máximo" in mensaje or "excedido" in mensaje


class TestDuplicateGuardiaError:
    """Tests para DuplicateGuardiaError"""

    def test_crear_con_parametros(self):
        """Crear excepción con todos los parámetros"""
        exc = DuplicateGuardiaError(
            profesor_nombre="García, Juan",
            fecha="2025-10-16",
            turno="mañana",
            recreo=1,
        )
        mensaje = str(exc)
        assert "García, Juan" in mensaje
        assert "2025-10-16" in mensaje
        assert "mañana" in mensaje
        assert "1" in mensaje

    def test_herencia(self):
        """Debe heredar de GuardiaConflictError"""
        exc = DuplicateGuardiaError("Profesor", "2025-10-16", "tarde", 2)
        assert isinstance(exc, GuardiaConflictError)

    def test_mensaje_duplicada(self):
        """Mensaje debe indicar que es duplicada"""
        exc = DuplicateGuardiaError("Prof", "2025-10-16", "tarde", 1)
        mensaje = str(exc).lower()
        assert "duplicad" in mensaje


class TestInsufficientProfesoresError:
    """Tests para InsufficientProfesoresError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = InsufficientProfesoresError("No hay suficientes profesores")
        assert isinstance(exc, GuardiasBaseException)


class TestExportError:
    """Tests para ExportError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ExportError("Error al exportar")
        assert isinstance(exc, GuardiasBaseException)


class TestImportError:
    """Tests para ImportError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ImportError("Error al importar")
        assert isinstance(exc, GuardiasBaseException)
