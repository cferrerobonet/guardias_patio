# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_data_files, collect_submodules

# Datos de la aplicación
datas = [
    ('imagenes', 'imagenes'),
    ('alembic.ini', '.'),
    ('alembic', 'alembic'),
]

# Binarios (vacío por ahora)
binaries = []

# Importaciones ocultas críticas
hiddenimports = [
    # PyQt6
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtPrintSupport',
    'PyQt6.sip',
    # SQLAlchemy
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.ext.declarative',
    'sqlalchemy.orm',
    'sqlalchemy.pool',
    # Alembic
    'alembic',
    'alembic.runtime.migration',
    'alembic.operations',
    # Pydantic
    'pydantic',
    'pydantic.types',
    'pydantic.fields',
    # Paramiko (para SFTP)
    'paramiko',
    'cryptography',
    # Otros módulos del proyecto
    'presentation',
    'presentation.ccleaner_main_window',
    'presentation.forms',
    'presentation.widgets',
    'presentation.themes',
    'models',
    'models.models',
    'sync',
    'sync.sftp_backend',
    'database',
    'database.db_manager',
    'ui',
    'ui.dialogs',
    'ui.widgets',
]

# Recoger todos los módulos de SQLAlchemy
tmp_ret = collect_all('sqlalchemy')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Recoger todos los módulos de Alembic
tmp_ret = collect_all('alembic')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Recoger todos los módulos de Paramiko
tmp_ret = collect_all('paramiko')
datas += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Recoger traducciones de PyQt6
try:
    tmp_ret = collect_data_files('PyQt6', include_py_files=False)
    datas += tmp_ret
except Exception:
    pass

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 
        'matplotlib', 
        'pandas',
        # Excluir Qt3D completo (no usado)
        'PyQt6.Qt3D',
        'PyQt6.Qt3DAnimation',
        'PyQt6.Qt3DCore',
        'PyQt6.Qt3DExtras',
        'PyQt6.Qt3DInput',
        'PyQt6.Qt3DLogic',
        'PyQt6.Qt3DRender',
        # Excluir WebEngine (no usado)
        'PyQt6.QtWebEngine',
        'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineQuick',
        'PyQt6.QtWebView',
        # Excluir multimedia avanzado (no usado)
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        # Excluir QML/Quick (no usado)
        'PyQt6.QtQml',
        'PyQt6.QtQuick',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtQuick3D',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# Crear ejecutable de una pieza (onefile)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Guardias de Patio',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='imagenes/icono.icns',
)

# Crear bundle macOS
app = BUNDLE(
    exe,
    name='Guardias de Patio.app',
    icon='imagenes/icono.icns',
    bundle_identifier='com.guardias-patio.app',
    info_plist={
        'CFBundleName': 'Guardias de Patio',
        'CFBundleDisplayName': 'Guardias de Patio',
        'CFBundleVersion': '2.8.0',
        'CFBundleShortVersionString': '2.8.0',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.13.0',
    },
)
