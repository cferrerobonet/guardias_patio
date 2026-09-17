# -*- mode: python ; coding: utf-8 -*-
# Un único spec para las dos plataformas (BLD-008). Lo que cambia entre ellas:
#   • el nombre: Windows y su instalador esperan `GuardiasDePatio`; en macOS la
#     app se llama como se lee, «Guardias de Patio», y así la busca `build_dmg.sh`;
#   • el icono: `.ico` en Windows, `.icns` en macOS;
#   • el `BUNDLE`, que sólo existe en macOS y es quien crea el `.app`.
# Las rutas van siempre con barra normal: `src\main.py` sólo funcionaba en Windows
# y dejó sin DMG a las versiones 5.97.0, 5.98.0 y 5.99.0.
import os
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules

sys.path.insert(0, str(Path(SPECPATH) / "scripts" / "build"))
from nombres_ascii import copia_con_nombres_ascii  # noqa: E402

ES_MACOS = sys.platform == "darwin"
NOMBRE = "Guardias de Patio" if ES_MACOS else "GuardiasDePatio"
ICONO = "imagenes/icono.icns" if ES_MACOS else "imagenes/logo.ico"

# La variante de diagnóstico de Windows sale de este mismo spec: consola visible
# para ver la traza de un cierre y otro nombre para que no se confunda con la
# de verdad. Hasta v6.3.0 `build_windows.ps1` no pasaba por aquí: llamaba a
# PyInstaller con argumentos sueltos, PyInstaller escribía su propio spec encima
# de éste y el exe de Windows salía sin nada de lo que se arregla aquí (BLD-016).
DIAGNOSTICO = os.getenv("GUARDIAS_BUILD_DIAGNOSTICO") == "1"
if DIAGNOSTICO and not ES_MACOS:
    NOMBRE += "-debug"

# Las migraciones se empaquetan con el nombre sin acentos: uno solo con «ñ» rompía
# el sello de la firma al copiar la aplicación y macOS la daba por dañada (BLD-010).
datas = [
    ('imagenes', 'imagenes'),
    (copia_con_nombres_ascii('alembic'), 'alembic'),
    ('alembic.ini', '.'),
    # Sin esto la aplicación arrancaba sin estilos: PyInstaller sólo empaqueta
    # los `.py`, y el tema se construye a partir de esta hoja (VIS-001).
    ('src/presentation/theme/light.qss', 'presentation/theme'),
]
binaries = []
hiddenimports = ['logging.config', 'logging.handlers', 'dependency_injector.errors', 'ortools.sat.python.cp_model_helper', 'matplotlib', 'matplotlib.backends.backend_qtagg', 'reportlab']
datas += collect_data_files('ortools')
# El llavero elige su almacén en tiempo de ejecución, así que PyInstaller no
# ve esos imports por sí solo y la aplicación empaquetada se quedaría sin
# dónde guardar las contraseñas (SEC-001).
hiddenimports += collect_submodules('keyring.backends')
# Los widgets se cargan con `importlib` cuando alguien los pide (BLD-017), así
# que PyInstaller tampoco los ve: el portable de v6.3.1 moría al abrir la ventana
# con «No module named presentation.widgets.ausencias_sustituciones» (BLD-019).
hiddenimports += [
    f"presentation.widgets.{f.stem}"
    for f in sorted((Path(SPECPATH) / "src" / "presentation" / "widgets").glob("*.py"))
    if f.stem != "__init__"
]
binaries += collect_dynamic_libs('ortools')
hiddenimports += collect_submodules('ortools')
tmp_ret = collect_all('dependency_injector')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ortools')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'email_validator'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# UPX comprime el ejecutable y las librerías, y ese empaquetado es una firma
# heurística clásica de los antivirus: es la misma técnica con la que el malware
# se ofusca. En un build `onedir` el ahorro de tamaño no compensa que la
# instalación se bloquee en el equipo del usuario, que es donde no podemos
# depurar (BLD-011).
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=NOMBRE,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=DIAGNOSTICO,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=[ICONO],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=NOMBRE,
)

if ES_MACOS:
    app = BUNDLE(
        coll,
        name=f"{NOMBRE}.app",
        icon=ICONO,
        bundle_identifier='com.guardias-patio.app',
    )
