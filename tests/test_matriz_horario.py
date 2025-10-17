#!/usr/bin/env python3
"""
Script de prueba para la función _horario_permitido().
Verifica que la validación de la matriz día×recreo funciona correctamente.
"""

import json
from datetime import date
from typing import Optional


def _horario_permitido(
    fecha: date, recreo_id: int, horario_json: Optional[str]
) -> bool:
    """
    Valida si un día+recreo está permitido según la matriz JSON.
    """
    if not horario_json:
        return fecha.weekday() < 5

    try:
        datos = json.loads(horario_json)
        dia_str = str(fecha.weekday())

        if dia_str not in datos:
            return False

        recreos_permitidos = datos[dia_str]
        return recreo_id in recreos_permitidos

    except (json.JSONDecodeError, ValueError, KeyError):
        return fecha.weekday() < 5


def test_horario_permitido():
    """Ejecuta pruebas de la función _horario_permitido()"""

    print("🧪 Ejecutando tests de _horario_permitido()...\n")

    # Test 1: Sin restricciones (debe permitir L-V)
    print("Test 1: Sin restricciones")
    fecha_lunes = date(2025, 10, 20)  # Lunes
    fecha_sabado = date(2025, 10, 25)  # Sábado
    assert _horario_permitido(fecha_lunes, 1, None), (
        "❌ Fallo: Lunes debería estar permitido"
    )
    assert not _horario_permitido(fecha_sabado, 1, None), (
        "❌ Fallo: Sábado NO debería estar permitido"
    )
    print("✅ Sin restricciones: OK\n")

    # Test 2: Con restricciones específicas
    print("Test 2: Con restricciones específicas")
    horario = json.dumps({
        "0": [1, 2],     # Lunes: recreos 1 y 2
        "2": [1, 3, 4],  # Miércoles: recreos 1, 3 y 4
        "4": [2]         # Viernes: solo recreo 2
    })

    fecha_lunes = date(2025, 10, 20)      # Lunes
    fecha_martes = date(2025, 10, 21)     # Martes
    fecha_miercoles = date(2025, 10, 22)  # Miércoles
    fecha_viernes = date(2025, 10, 24)    # Viernes

    # Lunes
    assert _horario_permitido(fecha_lunes, 1, horario), (
        "❌ Lunes recreo 1 debería estar permitido"
    )
    assert _horario_permitido(fecha_lunes, 2, horario), (
        "❌ Lunes recreo 2 debería estar permitido"
    )
    assert not _horario_permitido(fecha_lunes, 3, horario), (
        "❌ Lunes recreo 3 NO debería estar permitido"
    )
    print("  ✅ Lunes: OK")

    # Martes (no está en el JSON)
    assert not _horario_permitido(fecha_martes, 1, horario), (
        "❌ Martes NO debería estar permitido"
    )
    print("  ✅ Martes: OK (no incluido)")

    # Miércoles
    assert _horario_permitido(fecha_miercoles, 1, horario), (
        "❌ Miércoles recreo 1 debería estar permitido"
    )
    assert not _horario_permitido(fecha_miercoles, 2, horario), (
        "❌ Miércoles recreo 2 NO debería estar permitido"
    )
    assert _horario_permitido(fecha_miercoles, 3, horario), (
        "❌ Miércoles recreo 3 debería estar permitido"
    )
    assert _horario_permitido(fecha_miercoles, 4, horario), (
        "❌ Miércoles recreo 4 debería estar permitido"
    )
    print("  ✅ Miércoles: OK")

    # Viernes
    assert not _horario_permitido(fecha_viernes, 1, horario), (
        "❌ Viernes recreo 1 NO debería estar permitido"
    )
    assert _horario_permitido(fecha_viernes, 2, horario), (
        "❌ Viernes recreo 2 debería estar permitido"
    )
    assert not _horario_permitido(fecha_viernes, 3, horario), (
        "❌ Viernes recreo 3 NO debería estar permitido"
    )
    print("  ✅ Viernes: OK\n")

    # Test 3: JSON malformado (debe usar comportamiento por defecto)
    print("Test 3: JSON malformado")
    horario_invalido = "esto no es json válido"
    assert _horario_permitido(fecha_lunes, 1, horario_invalido), (
        "❌ Con JSON inválido debería permitir L-V"
    )
    assert not _horario_permitido(fecha_sabado, 1, horario_invalido), (
        "❌ Con JSON inválido NO debería permitir sábado"
    )
    print("✅ JSON malformado manejado correctamente\n")

    # Test 4: Caso extremo - todos los días y recreos
    print("Test 4: Todos los días y recreos")
    horario_completo = json.dumps({
        str(i): [1, 2, 3, 4] for i in range(7)
    })
    for dia in range(7):
        fecha_test = date(2025, 10, 20 + dia)
        for recreo in [1, 2, 3, 4]:
            assert _horario_permitido(fecha_test, recreo, horario_completo), (
                f"❌ Día {dia} recreo {recreo} debería estar permitido"
            )
    print("✅ Todos los días y recreos: OK\n")

    print("=" * 60)
    print("🎉 ¡Todos los tests pasaron exitosamente!")
    print("=" * 60)


if __name__ == "__main__":
    test_horario_permitido()
