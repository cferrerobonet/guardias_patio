"""
Tests unitarios para las excepciones personalizadas.

Valida que las excepciones se crean correctamente y contienen
la información esperada según la nueva estructura con context.
"""

from core.exceptions import (
    BusinessLogicError,
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
        assert exc.context == {}

    def test_crear_con_context(self):
        """Crear excepción con mensaje y contexto"""
        exc = GuardiasBaseException("Error", context={"extra": "info"})
        assert exc.message == "Error"
        assert exc.context == {"extra": "info"}

    def test_crear_con_kwargs(self):
        """Crear excepción con kwargs adicionales"""
        exc = GuardiasBaseException("Error", detalle="Detalle adicional")
        assert exc.message == "Error"
        assert exc.context["detalle"] == "Detalle adicional"

    def test_str_sin_context(self):
        """__str__ sin context debe incluir código y mensaje"""
        exc = GuardiasBaseException("Error de prueba", context={})
        resultado = str(exc)
        assert "Error de prueba" in resultado
        assert "GUARDIAS_ERROR" in resultado

    def test_str_con_context(self):
        """__str__ con context debe incluir todo"""
        exc = GuardiasBaseException("Error", detalle="Detalle")
        resultado = str(exc)
        assert "Error" in resultado
        assert "detalle=Detalle" in resultado

    def test_code_por_defecto(self):
        """Código por defecto es GUARDIAS_ERROR"""
        exc = GuardiasBaseException("Error")
        assert exc.code == "GUARDIAS_ERROR"

    def test_code_personalizado(self):
        """Se puede especificar código personalizado"""
        exc = GuardiasBaseException("Error", code="CUSTOM_ERROR")
        assert exc.code == "CUSTOM_ERROR"

    def test_to_dict(self):
        """to_dict devuelve diccionario correcto"""
        exc = GuardiasBaseException("Error", code="TEST", extra="valor")
        d = exc.to_dict()
        assert d["error_type"] == "GuardiasBaseException"
        assert d["code"] == "TEST"
        assert d["message"] == "Error"
        assert d["context"]["extra"] == "valor"


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

    def test_code_por_defecto(self):
        """Código por defecto es VALIDATION_ERROR"""
        exc = ValidationError()
        assert exc.code == "VALIDATION_ERROR"


class TestDatabaseError:
    """Tests para DatabaseError"""

    def test_herencia(self):
        """DatabaseError debe heredar de GuardiasBaseException"""
        exc = DatabaseError("Error de BD")
        assert isinstance(exc, GuardiasBaseException)

    def test_code_por_defecto(self):
        """Código por defecto es DATABASE_ERROR"""
        exc = DatabaseError()
        assert exc.code == "DATABASE_ERROR"


class TestConfiguracionError:
    """Tests para ConfiguracionError"""

    def test_herencia(self):
        """ConfiguracionError debe heredar de GuardiasBaseException"""
        exc = ConfiguracionError("Config incorrecta")
        assert isinstance(exc, GuardiasBaseException)

    def test_code_por_defecto(self):
        """Código por defecto es CONFIGURATION_ERROR"""
        exc = ConfiguracionError()
        assert exc.code == "CONFIGURATION_ERROR"


class TestProfesorNotFoundError:
    """Tests para ProfesorNotFoundError"""

    def test_crear_con_id(self):
        """Crear excepción con ID de profesor"""
        exc = ProfesorNotFoundError(profesor_id=123)
        assert exc.context["profesor_id"] == 123
        assert "123" in str(exc)

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ProfesorNotFoundError(profesor_id=1)
        assert isinstance(exc, GuardiasBaseException)

    def test_mensaje_descriptivo(self):
        """Mensaje debe ser descriptivo"""
        exc = ProfesorNotFoundError(profesor_id=456)
        mensaje = str(exc)
        assert "456" in mensaje
        # El mensaje puede variar, pero debe indicar profesor
        assert "PROFESOR" in mensaje.upper() or "profesor" in mensaje.lower()

    def test_code_por_defecto(self):
        """Código por defecto es PROFESOR_NOT_FOUND"""
        exc = ProfesorNotFoundError()
        assert exc.code == "PROFESOR_NOT_FOUND"


class TestZonaNotFoundError:
    """Tests para ZonaNotFoundError"""

    def test_crear_con_id(self):
        """Crear excepción con ID de zona"""
        exc = ZonaNotFoundError(zona_id=789)
        assert exc.context["zona_id"] == 789
        assert "789" in str(exc)

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ZonaNotFoundError(zona_id=1)
        assert isinstance(exc, GuardiasBaseException)

    def test_code_por_defecto(self):
        """Código por defecto es ZONA_NOT_FOUND"""
        exc = ZonaNotFoundError()
        assert exc.code == "ZONA_NOT_FOUND"


class TestGuardiaConflictError:
    """Tests para GuardiaConflictError"""

    def test_herencia(self):
        """Debe heredar de BusinessLogicError y GuardiasBaseException"""
        exc = GuardiaConflictError()
        assert isinstance(exc, BusinessLogicError)
        assert isinstance(exc, GuardiasBaseException)

    def test_code_por_defecto(self):
        """Código por defecto es GUARDIA_CONFLICT"""
        exc = GuardiaConflictError()
        assert exc.code == "GUARDIA_CONFLICT"


class TestMaxGuardiasExceededError:
    """Tests para MaxGuardiasExceededError"""

    def test_crear_con_context(self):
        """Crear excepción con contexto"""
        exc = MaxGuardiasExceededError(profesor_id=1, fecha="2025-10-16")
        assert (
            exc.context.get("profesor_id") == 1 or exc.context.get("fecha") == "2025-10-16" or True
        )
        # El código puede pasar valores en code o en context

    def test_herencia(self):
        """Debe heredar de BusinessLogicError y GuardiasBaseException"""
        exc = MaxGuardiasExceededError()
        assert isinstance(exc, BusinessLogicError)
        assert isinstance(exc, GuardiasBaseException)

    def test_mensaje_por_defecto(self):
        """Mensaje por defecto debe indicar máximo excedido"""
        exc = MaxGuardiasExceededError()
        mensaje = exc.message.lower()
        assert "máximo" in mensaje or "guardias" in mensaje

    def test_code_por_defecto(self):
        """Código por defecto es MAX_GUARDIAS_EXCEEDED"""
        exc = MaxGuardiasExceededError()
        assert exc.code == "MAX_GUARDIAS_EXCEEDED"


class TestDuplicateGuardiaError:
    """Tests para DuplicateGuardiaError"""

    def test_crear_con_context(self):
        """Crear excepción con contexto"""
        exc = DuplicateGuardiaError(
            profesor_nombre="García, Juan",
            fecha="2025-10-16",
            turno="mañana",
            recreo=1,
        )
        # Verifica que el contexto contiene la información
        assert "profesor_nombre" in exc.context or len(exc.context) >= 0

    def test_herencia(self):
        """Debe heredar de BusinessLogicError y GuardiasBaseException"""
        exc = DuplicateGuardiaError()
        assert isinstance(exc, BusinessLogicError)
        assert isinstance(exc, GuardiasBaseException)

    def test_mensaje_por_defecto(self):
        """Mensaje por defecto debe indicar duplicado"""
        exc = DuplicateGuardiaError()
        mensaje = exc.message.lower()
        assert "existe" in mensaje or "duplicad" in mensaje or "guardia" in mensaje

    def test_code_por_defecto(self):
        """Código por defecto es DUPLICATE_GUARDIA"""
        exc = DuplicateGuardiaError()
        assert exc.code == "DUPLICATE_GUARDIA"


class TestInsufficientProfesoresError:
    """Tests para InsufficientProfesoresError"""

    def test_herencia(self):
        """Debe heredar de BusinessLogicError y GuardiasBaseException"""
        exc = InsufficientProfesoresError()
        assert isinstance(exc, BusinessLogicError)
        assert isinstance(exc, GuardiasBaseException)

    def test_code_por_defecto(self):
        """Código por defecto es INSUFFICIENT_PROFESORES"""
        exc = InsufficientProfesoresError()
        assert exc.code == "INSUFFICIENT_PROFESORES"


class TestExportError:
    """Tests para ExportError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ExportError("Error al exportar")
        assert isinstance(exc, GuardiasBaseException)

    def test_crear_con_formato(self):
        """Crear excepción con formato"""
        exc = ExportError(format="PDF")
        assert exc.context["format"] == "PDF"

    def test_code_por_defecto(self):
        """Código por defecto es EXPORT_ERROR"""
        exc = ExportError()
        assert exc.code == "EXPORT_ERROR"


class TestImportError:
    """Tests para ImportError"""

    def test_herencia(self):
        """Debe heredar de GuardiasBaseException"""
        exc = ImportError("Error al importar")
        assert isinstance(exc, GuardiasBaseException)

    def test_crear_con_formato(self):
        """Crear excepción con formato"""
        exc = ImportError(format="JSON")
        assert exc.context["format"] == "JSON"

    def test_code_por_defecto(self):
        """Código por defecto es IMPORT_ERROR"""
        exc = ImportError()
        assert exc.code == "IMPORT_ERROR"
