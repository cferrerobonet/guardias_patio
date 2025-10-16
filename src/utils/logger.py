"""
Sistema de logging centralizado para la aplicación de Guardias de Patio.

Este módulo proporciona funciones para configurar y obtener loggers
de forma consistente en toda la aplicación.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
) -> None:
    """
    Configura el sistema de logging de la aplicación.

    Args:
        log_file: Ruta al archivo de log (opcional)
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Formato personalizado de los mensajes de log
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configuración básica
    handlers = [logging.StreamHandler(sys.stdout)]

    # Añadir handler de archivo si se especifica
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=format_string,
        handlers=handlers,
        force=True,  # Sobrescribir configuración existente
    )


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.

    Args:
        name: Nombre del logger (generalmente __name__ del módulo)

    Returns:
        Logger configurado

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Aplicación iniciada")
    """
    logger = logging.getLogger(name)

    # Si no hay handlers configurados, configurar por defecto
    if not logger.handlers and not logging.root.handlers:
        setup_logging()

    return logger


def log_function_call(logger: logging.Logger):
    """
    Decorador para loggear llamadas a funciones.

    Args:
        logger: Logger a utilizar

    Example:
        >>> logger = get_logger(__name__)
        >>> @log_function_call(logger)
        ... def mi_funcion(x, y):
        ...     return x + y
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Llamando {func.__name__} con args={args}, kwargs={kwargs}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} completado exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en {func.__name__}: {e}", exc_info=True)
                raise

        return wrapper

    return decorator
