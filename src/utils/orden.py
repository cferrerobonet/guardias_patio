"""Orden alfabético como el de un diccionario, para nombres de profesores y zonas.

SQLite y `sorted` comparan por código de carácter: «DÍAZ» quedaba detrás de
«DOMÍNGUEZ» y «Ávila» detrás de «Zapata», en todas las listas de la aplicación
(2026-10-03).
"""

import unicodedata


def clave_alfabetica(texto) -> str:
    """Sin tildes ni mayúsculas, y la ñ entre la n y la o."""
    descompuesto = unicodedata.normalize("NFD", str(texto or "").casefold())
    # «{» va justo detrás de la «z»: «nz» < «ña» < «o».
    descompuesto = descompuesto.replace("ñ", "n{")
    return "".join(c for c in descompuesto if not unicodedata.combining(c))
