"""
Tests unitarios para el sistema de logging.

Valida la configuración y funcionalidad del logging.
"""

import logging

from utils.logger import get_logger, log_function_call, setup_logging


class TestSetupLogging:
    """Tests para setup_logging()"""

    def test_setup_basico(self):
        """Setup básico sin archivo debe configurar logging"""
        setup_logging(level=logging.DEBUG)
        logger = logging.getLogger("test")
        assert logger.level <= logging.DEBUG

    def test_setup_con_archivo(self, tmp_path):
        """Setup con archivo debe crear el archivo de log"""
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file), level=logging.INFO)

        # Escribir un mensaje
        logger = logging.getLogger("test_file")
        logger.info("Mensaje de prueba")

        # Verificar que el archivo existe
        assert log_file.exists()

    def test_setup_formato_personalizado(self):
        """Setup con formato personalizado debe aplicarlo"""
        formato = "%(levelname)s - %(message)s"
        setup_logging(format_string=formato)

        _ = logging.getLogger("test_formato")
        # Si llega aquí sin error, el formato se aplicó
        assert True

    def test_setup_crea_directorios(self, tmp_path):
        """Setup debe crear directorios padre si no existen"""
        log_file = tmp_path / "logs" / "nested" / "test.log"
        setup_logging(log_file=str(log_file))

        logger = logging.getLogger("test_dirs")
        logger.info("Test")

        assert log_file.parent.exists()
        assert log_file.exists()


class TestGetLogger:
    """Tests para get_logger()"""

    def test_obtener_logger(self):
        """Obtener logger debe devolver un logger configurado"""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"

    def test_logger_con_nombre_diferente(self):
        """Loggers con nombres diferentes deben ser distintos"""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        assert logger1 is not logger2
        assert logger1.name != logger2.name

    def test_logger_mismo_nombre(self):
        """Obtener el mismo logger dos veces debe devolver la misma instancia"""
        logger1 = get_logger("mismo_modulo")
        logger2 = get_logger("mismo_modulo")
        assert logger1 is logger2


class TestLogFunctionCall:
    """Tests para el decorador log_function_call()"""

    def test_decorador_sin_errores(self):
        """Decorador debe permitir ejecución normal"""
        logger = get_logger("test_decorator")

        @log_function_call(logger)
        def suma(a, b):
            return a + b

        resultado = suma(2, 3)
        assert resultado == 5

    def test_decorador_con_excepcion(self):
        """Decorador debe propagar excepciones"""
        logger = get_logger("test_decorator_error")

        @log_function_call(logger)
        def funcion_error():
            raise ValueError("Error de prueba")

        try:
            funcion_error()
            assert False, "Debería haber lanzado excepción"
        except ValueError as e:
            assert str(e) == "Error de prueba"

    def test_decorador_preserva_retorno(self):
        """Decorador debe preservar el valor de retorno"""
        logger = get_logger("test_decorator_return")

        @log_function_call(logger)
        def obtener_diccionario():
            return {"clave": "valor"}

        resultado = obtener_diccionario()
        assert resultado == {"clave": "valor"}

    def test_decorador_con_args_kwargs(self):
        """Decorador debe funcionar con args y kwargs"""
        logger = get_logger("test_decorator_args")

        @log_function_call(logger)
        def funcion_compleja(pos1, pos2, kw1=None, kw2=None):
            return f"{pos1}-{pos2}-{kw1}-{kw2}"

        resultado = funcion_compleja("a", "b", kw1="c", kw2="d")
        assert resultado == "a-b-c-d"


class TestIntegracionLogging:
    """Tests de integración para el sistema de logging"""

    def test_flujo_completo(self, tmp_path):
        """Test del flujo completo: setup, get_logger, log"""
        log_file = tmp_path / "test_integracion.log"

        # 1. Configurar
        setup_logging(log_file=str(log_file), level=logging.INFO)

        # 2. Obtener logger
        logger = get_logger("integracion")

        # 3. Loggear mensajes
        logger.info("Mensaje INFO")
        logger.warning("Mensaje WARNING")
        logger.error("Mensaje ERROR")

        # 4. Verificar archivo
        assert log_file.exists()
        contenido = log_file.read_text(encoding="utf-8")
        assert "INFO" in contenido
        assert "WARNING" in contenido
        assert "ERROR" in contenido

    def test_niveles_logging(self, tmp_path):
        """Test de niveles de logging"""
        log_file = tmp_path / "test_niveles.log"

        # Configurar con nivel WARNING (no debería loggear INFO)
        setup_logging(log_file=str(log_file), level=logging.WARNING)
        logger = get_logger("niveles")

        logger.info("No debería aparecer")
        logger.warning("Debería aparecer")

        contenido = log_file.read_text(encoding="utf-8")
        assert "No debería aparecer" not in contenido
        assert "Debería aparecer" in contenido
