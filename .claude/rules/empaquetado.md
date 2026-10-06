---
paths:
  - "GuardiasDePatio.spec"
  - "installer_windows.iss"
  - "Makefile"
  - "scripts/build/**"
  - "scripts/build_windows.ps1"
  - "scripts/prueba_arranque_windows.ps1"
  - ".github/workflows/**"
  - "src/utils/update_checker.py"
  - "src/presentation/widgets/__init__.py"
---

# Empaquetado Windows y macOS

- **Build**: sin PC Windows, publicar la etiqueta `vX.Y.Z` → `.github/workflows/compilar.yml` compila las dos y las adjunta al release. En local: macOS `make dmg`; Windows `scripts/build_windows.ps1` (`-Diagnostico` para consola). **Un solo spec**: `GuardiasDePatio.spec` (lleva `keyring.backends`; lo vigila `tests/audit/test_un_solo_spec.py`).
- **Cada release de Windows lleva las dos variantes** (pedido por CarlosFB el 2026-09-17): `GuardiasDePatio-<v>-Windows-Setup.exe` (instalador Inno Setup) y `GuardiasDePatio-<v>-Windows-Portable.zip` (carpeta onedir). En el centro casi nadie es administrador y hay un equipo donde el instalador se atasca. No quitar ninguna al tocar `compilar.yml`, `build_windows.ps1` o el spec.
- **Imports dinámicos** (`importlib`, `__getattr__` de módulo, carga perezosa): PyInstaller no los ve. Cada uno nuevo exige su hidden import en el spec y un test en `tests/audit/test_un_solo_spec.py` en la misma sesión (el portable de v6.3.1 moría tras el login por esto). Si «la app no abre» en Windows, pedir antes de tocar código `%APPDATA%\GuardiasDePatio\logs\app_*.log`.
- **Certificados TLS**: el OpenSSL empaquetado no encuentra los del sistema; `update_checker.contexto_ssl()` usa `certifi`. No quitarlo (el DMG dejó de avisar de versiones nuevas).
- **La suite en verde no prueba la app instalada** (rutas de Windows en el spec, «ñ» que rompe la firma, configuración congelada al importar, hoja de estilos sin empaquetar). Antes de publicar una etiqueta, `make dmg` en local y, sobre `APP="dist/Guardias de Patio.app"`:
  - `find "$APP" -type f | LC_ALL=C grep -P '[^\x00-\x7F]'` (nombres con acentos rompen la firma);
  - `find "$APP" -name "*.qss"` (recursos que no son `.py`);
  - `codesign --verify --strict` solo vale sobre la copia del DMG, no sobre `dist/`;
  - arrancar con `QT_QPA_PLATFORM=offscreen SFTP_PASSWORD=cualquiera "$APP/Contents/MacOS/Guardias de Patio" &` (la variable evita el permiso del llavero, que sin pantalla no se puede aceptar); el registro sale en `~/Library/Application Support/GuardiasDePatio/logs/`.
- No editar ficheros mientras se compila o corre la suite: bash lee el script a trozos y `settings.py` se relee; el fallo despista. `build_dmg.sh` copia el bundle fuera de iCloud antes de firmarlo.
- Versión: `app_version` y `pyproject.toml` coinciden (ver `AGENTS.md`).
