# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('imagenes', 'imagenes'), ('alembic.ini', '.'), ('alembic', 'alembic')]
binaries = []
hiddenimports = ['sqlalchemy.sql.default_comparator', 'PyQt6.QtCore', 'PyQt6.QtGui', 'PyQt6.QtWidgets', 'pydantic', 'alembic']
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('alembic')
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
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Guardias de Patio',
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
    icon=['imagenes/icono.icns'],
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Guardias de Patio',
)

app = BUNDLE(
    coll,
    name='Guardias de Patio.app',
    icon='imagenes/icono.icns',
    bundle_identifier='com.guardias-patio.app',
    version='2.7.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Guardias de Patio',
        'CFBundleDisplayName': 'Guardias de Patio',
        'CFBundleGetInfoString': 'Gestión de guardias de recreo',
        'CFBundleVersion': '2.7.0',
        'CFBundleShortVersionString': '2.7.0',
        'NSHumanReadableCopyright': '© 2025 Guardias de Patio',
        'LSMinimumSystemVersion': '10.14.0',
    },
)
