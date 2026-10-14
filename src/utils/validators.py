"""
Módulo de validadores para datos de entrada.

Contiene funciones para validar emails, fechas, nombres y otros datos
antes de guardarlos en la base de datos.
"""

import re
from datetime import date
from typing import Optional, Tuple


def validar_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Valida un email corporativo.

    Args:
        email: Email a validar

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validar_email("profesor@colegio.edu")
        (True, None)
        >>> validar_email("email_invalido")
        (False, "Formato de email inválido")
    """
    if not email or not email.strip():
        return False, "El email no puede estar vacío"

    # Patrón básico de email
    patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(patron, email):
        return False, "Formato de email inválido"

    return True, None


def validar_nombre_completo(nombre: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el formato de nombre completo (APELLIDOS, NOMBRE).

    Args:
        nombre: Nombre completo a validar

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> validar_nombre_completo("GARCÍA LÓPEZ, JUAN")
        (True, None)
        >>> validar_nombre_completo("Juan García")
        (False, "Formato incorrecto. Use: APELLIDOS, NOMBRE")
    """
    if not nombre or not nombre.strip():
        return False, "El nombre no puede estar vacío"

    # Debe contener una coma
    if "," not in nombre:
        return (
            False,
            "Formato incorrecto. Use: APELLIDOS, NOMBRE (con coma)",
        )

    partes = nombre.split(",")
    if len(partes) != 2:
        return (
            False,
            "Formato incorrecto. Use: APELLIDOS, NOMBRE (una sola coma)",
        )

    apellidos, nombre_propio = partes
    if not apellidos.strip() or not nombre_propio.strip():
        return (
            False,
            "Tanto apellidos como nombre deben estar presentes",
        )

    return True, None


def validar_fecha(fecha: date, fecha_minima: Optional[date] = None) -> Tuple[bool, Optional[str]]:
    """
    Valida una fecha.

    Args:
        fecha: Fecha a validar
        fecha_minima: Fecha mínima permitida (opcional)

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not fecha:
        return False, "La fecha no puede estar vacía"

    if fecha_minima and fecha < fecha_minima:
        return False, f"La fecha no puede ser anterior a {fecha_minima}"

    return True, None


def validar_rango_fechas(
    fecha_inicio: date,
    fecha_fin: date,
) -> Tuple[bool, Optional[str]]:
    """
    Valida un rango de fechas (inicio <= fin).

    Args:
        fecha_inicio: Fecha de inicio
        fecha_fin: Fecha de fin

    Returns:
        Tupla (es_valido, mensaje_error)

    Example:
        >>> from datetime import date
        >>> validar_rango_fechas(date(2025, 9, 1), date(2026, 6, 30))
        (True, None)
        >>> validar_rango_fechas(date(2026, 6, 30), date(2025, 9, 1))
        (False, "La fecha de inicio debe ser anterior a la fecha de fin")
    """
    if not fecha_inicio or not fecha_fin:
        return False, "Ambas fechas deben estar presentes"

    if fecha_inicio >= fecha_fin:
        return (
            False,
            "La fecha de inicio debe ser anterior a la fecha de fin",
        )

    return True, None


def validar_horas_contrato(horas: float) -> Tuple[bool, Optional[str]]:
    """
    Valida las horas de contrato de un profesor.

    Args:
        horas: Horas de contrato

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if horas <= 0:
        return False, "Las horas deben ser un número positivo"

    if horas > 40:
        return False, "Las horas no pueden superar las 40 horas semanales"

    return True, None


def validar_turno(turno: str) -> Tuple[bool, Optional[str]]:
    """
    Valida el turno de un profesor.

    Args:
        turno: Turno a validar

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    turnos_validos = ["mañana", "tarde", "mixto"]

    if turno not in turnos_validos:
        return (
            False,
            f"Turno inválido. Debe ser uno de: {', '.join(turnos_validos)}",
        )

    return True, None


def validar_dias_semana(dias_str: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Valida la cadena de días de semana permitidos.

    Args:
        dias_str: Cadena con días separados por comas (ej: "0,1,2,3,4")

    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not dias_str or not dias_str.strip():
        return True, None  # Es opcional

    try:
        dias = [int(d.strip()) for d in dias_str.split(",")]
        if not all(0 <= d <= 6 for d in dias):
            return False, "Los días deben estar entre 0 (lunes) y 6 (domingo)"
        return True, None
    except ValueError:
        return False, "Formato inválido. Use números separados por comas (ej: 0,1,2)"
