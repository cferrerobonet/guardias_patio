"""
Widgets refactorizados de la capa de presentación.

Los nombres públicos se cargan cuando alguien los pide, no al importar el
paquete: `ausencias_sustituciones` arrastra los formularios y, con ellos,
OR-Tools, pandas y SQLAlchemy. La pantalla de arranque vive aquí y tiene que
poder importarse en décimas de segundo, antes de que exista nada más (BLD-017).
"""

import importlib

_MODULOS = {
    "AusenciasSustitucionesWidget": ".ausencias_sustituciones",
    "PanelEstadisticas": ".panel_estadisticas",
    "SelectorCursoWidget": ".selector_curso_widget",
    "TableManager": ".table_manager",
    "ToastNotification": ".toast_notification",
    "VistaCalendario": ".vista_calendario",
}

__all__ = list(_MODULOS)


def __getattr__(nombre: str):
    if nombre in _MODULOS:
        valor = getattr(importlib.import_module(_MODULOS[nombre], __name__), nombre)
        globals()[nombre] = valor
        return valor
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")
