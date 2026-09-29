"""Un solo runtime de C++ de Microsoft, el más reciente, en el exe de Windows (BLD-020).

PyQt6 trae en `PyQt6/Qt6/bin` su propia copia de `MSVCP140.dll`, de 2020
(14.26). Qt se carga el primero, así que es esa copia la que queda en memoria, y
Windows entrega el módulo ya cargado a cualquiera que después pida una DLL con
ese nombre. OR-Tools está compilado con Visual Studio 2022 17.10 o posterior,
cuyo `std::mutex` necesita el runtime 14.40 o superior: con el viejo, el primer
`Solve` muere con «access violation» dentro de `MSVCP140.dll`. Sin traza de
Python, sin aviso, sin nada en pantalla.

Desde v6.1.1 la comprobación de arranque resuelve un modelo trivial (BLD-012),
así que la aplicación instalada (comprobado en v6.3.2) se cerraba sola a los
dos segundos de abrir, con la pantalla de arranque todavía a la vista. Es
también, con toda probabilidad, el cierre al generar guardias de la auditoría 06.

Aquí se sustituye cada copia del runtime que PyInstaller ha recogido por la de
versión más alta entre todas ellas y la del sistema del equipo que compila. El
runtime es compatible hacia atrás: Qt funciona igual con el nuevo.
"""

import os
from pathlib import Path
from typing import Callable, Iterable, Optional

#: Las DLL del «Microsoft Visual C++ Redistributable» que se reparten sueltas.
NOMBRES = frozenset(
    {
        "concrt140.dll",
        "msvcp140.dll",
        "msvcp140_1.dll",
        "msvcp140_2.dll",
        "msvcp140_atomic_wait.dll",
        "msvcp140_codecvt_ids.dll",
        "vccorlib140.dll",
        "vcruntime140.dll",
        "vcruntime140_1.dll",
    }
)

#: Lo mínimo que necesita un binario compilado con Visual Studio 2022 17.10+.
MINIMA_MSVCP = (14, 40)

Version = tuple


def version_de_fichero(ruta) -> Version:
    """Versión de fichero de una DLL de Windows, o () si no se puede leer."""
    try:
        import ctypes
        from ctypes import wintypes
    except ImportError:
        return ()
    if os.name != "nt":
        return ()
    version = ctypes.WinDLL("version")
    tam = version.GetFileVersionInfoSizeW(str(ruta), None)
    if not tam:
        return ()
    datos = ctypes.create_string_buffer(tam)
    if not version.GetFileVersionInfoW(str(ruta), 0, tam, datos):
        return ()
    puntero = ctypes.c_void_p()
    largo = wintypes.UINT()
    if not version.VerQueryValueW(datos, "\\", ctypes.byref(puntero), ctypes.byref(largo)):
        return ()
    # VS_FIXEDFILEINFO: firma, versión de estructura y luego FileVersionMS/LS.
    campos = ctypes.cast(puntero, ctypes.POINTER(wintypes.DWORD * 4)).contents
    ms, ls = campos[2], campos[3]
    return (ms >> 16, ms & 0xFFFF, ls >> 16, ls & 0xFFFF)


def carpeta_del_sistema() -> Path:
    return Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"


def unificar(
    binarios: Iterable[tuple],
    sistema: Optional[Path] = None,
    leer_version: Callable[[object], Version] = version_de_fichero,
    avisar: Callable[[str], None] = print,
) -> list:
    """Devuelve la lista de binarios con cada DLL del runtime apuntando a la más nueva.

    `binarios` es la TOC de PyInstaller: tuplas `(destino, origen, tipo)`. El
    destino no cambia —cada copia sigue donde la espera quien la usa—, sólo de
    dónde se copia.
    """
    binarios = list(binarios)
    sistema = sistema if sistema is not None else carpeta_del_sistema()

    candidatos: dict = {}
    for destino, origen, _tipo in binarios:
        nombre = Path(destino).name.lower()
        if nombre in NOMBRES:
            candidatos.setdefault(nombre, []).append(origen)

    mejor: dict = {}
    for nombre, origenes in candidatos.items():
        del_sistema = Path(sistema) / nombre
        if del_sistema.exists():
            origenes = [*origenes, str(del_sistema)]
        versiones = {origen: leer_version(origen) for origen in origenes}
        elegido = max(origenes, key=lambda o: versiones[o])
        mejor[nombre] = elegido
        detalle = ", ".join(
            f"{'.'.join(map(str, versiones[o])) or '?'} {o}" for o in dict.fromkeys(origenes)
        )
        # Sólo ASCII: la consola de Windows compila en cp1252 y una flecha la tumbaba.
        avisar(f"[runtime_msvc] {nombre}: {'.'.join(map(str, versiones[elegido]))} <- {detalle}")

    msvcp = mejor.get("msvcp140.dll")
    if msvcp is not None:
        version = leer_version(msvcp)
        if version and version[:2] < MINIMA_MSVCP:
            raise SystemExit(
                f"MSVCP140.dll {'.'.join(map(str, version))} es anterior a "
                f"{'.'.join(map(str, MINIMA_MSVCP))}: OR-Tools se caería al resolver. "
                "Instala el Visual C++ Redistributable 2015-2022 actual en el equipo que compila."
            )

    return [
        (destino, mejor.get(Path(destino).name.lower(), origen), tipo)
        for destino, origen, tipo in binarios
    ]
