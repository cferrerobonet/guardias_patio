"""
Funciones helper para parsear campos JSON de profesores.

Este módulo centraliza la lógica de parseo para evitar duplicación
y manejar todos los formatos posibles de datos.
"""

import ast
import json
from typing import Any, List


def parse_json_field(value: Any, default: Any) -> Any:
    """
    Parsea un campo que puede estar en varios formatos.

    Formatos soportados:
    - Lista directa: [1, 2, 3]
    - JSON string: "[1,2,3]" o "[1, 2, 3]"
    - Python literal string: "[0, 1, 2, 3, 4]"
    - Dict (formato antiguo): {"0": [1,2], "1": [2]}

    Args:
        value: Valor a parsear (puede ser str, list, dict, None)
        default: Valor por defecto si el parseo falla

    Returns:
        Valor parseado o default si falla
    """
    if not value:
        return default

    # Si ya es una lista o dict, usarlo directamente
    if isinstance(value, (list, dict)):
        return value

    # Si es string, intentar parsearlo
    if isinstance(value, str):
        # 1. Intentar JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # 2. Intentar Python literal
        try:
            return ast.literal_eval(value)
        except (ValueError, SyntaxError):
            pass

    # Si todo falla, retornar default
    return default


def parse_dias_semana(value: Any) -> List[int]:
    """
    Parsea el campo dias_semana_permitidos.

    Args:
        value: Valor del campo (str, list, o None)

    Returns:
        Lista de días (0-6) o todos los días por defecto
    """
    default = list(range(7))
    result = parse_json_field(value, default)

    # Validar que es una lista
    if not isinstance(result, list):
        return default

    return result


def parse_recreos(value: Any) -> List[int]:
    """
    Parsea el campo recreos_permitidos.

    Maneja tanto el formato nuevo (lista) como el antiguo (dict).

    Args:
        value: Valor del campo (str, list, dict, o None)

    Returns:
        Lista de recreos permitidos o [1, 2] por defecto
    """
    default = [1, 2]
    result = parse_json_field(value, default)

    # Si es dict (formato antiguo), extraer recreos únicos
    if isinstance(result, dict):
        recreos_set = set()
        for recreos_list in result.values():
            if isinstance(recreos_list, list):
                recreos_set.update(recreos_list)
        return sorted(list(recreos_set)) if recreos_set else default

    # Si es lista, usarla directamente
    if isinstance(result, list):
        return result

    return default
