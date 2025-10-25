# -*- mode: python ; coding: utf-8 -*-
"""
Especificación de PyInstaller para Guardias de Patio
Genera una aplicación macOS (.app) standalone
"""

import sys
from pathlib import Path

block_cipher = None

# Rutas del proyecto
project_root = Path('.').absolute()
src_path = project_root / 'src'

# Datos adicionales a incluir
added_files = [
    ('imagenes', 'imagenes'),
    ('alembic.ini', '.'),
    ('alembic', 'alembic'),
]

# Imports ocultos necesarios
hidden_imports = [
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.pool',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtPrintSupport',
    'pydantic',
    'pydantic.fields',
    'pydantic.types',
    'alembic',
    'alembic.runtime.migration',
    'alembic.operations',
    'alembic.ddl',
]

a = Analysis(
    ['src/main.py'],
    pathex=[str(src_path)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

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
