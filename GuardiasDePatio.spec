# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('imagenes', 'imagenes'), ('alembic', 'alembic'), ('alembic.ini', '.')]
binaries = []
hiddenimports = ['logging.config', 'logging.handlers', 'dependency_injector.errors', 'ortools.sat.python.cp_model_helper', 'matplotlib', 'matplotlib.backends.backend_qtagg', 'reportlab']
datas += collect_data_files('ortools')
# El llavero elige su almacén en tiempo de ejecución, así que PyInstaller no
# ve esos imports por sí solo y la aplicación empaquetada se quedaría sin
# dónde guardar las contraseñas (SEC-001).
hiddenimports += collect_submodules('keyring.backends')
binaries += collect_dynamic_libs('ortools')
hiddenimports += collect_submodules('ortools')
tmp_ret = collect_all('dependency_injector')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('ortools')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['src\\main.py'],
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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GuardiasDePatio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['imagenes\\logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GuardiasDePatio',
)
