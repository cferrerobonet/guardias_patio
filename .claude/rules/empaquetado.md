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

- **Build**: sin PC Windows, publicar la etiqueta `vX.Y.Z` → `.github/workflows/compilar.yml` compila las dos y las adjunta al release. **No se compila nunca en local** (norma de CarlosFB, 2026-10-10: no quiere DMG, `dist/` ni `build/` de compilaciones locales). Ni `make dmg` (que además **publica la etiqueta y el release por su cuenta**, sin esperar al commit) ni `make app`, ni `pyinstaller`, ni `scripts/build_windows.ps1` salvo que CarlosFB lo pida expresamente. **Un solo spec**: `GuardiasDePatio.spec` (lleva `keyring.backends`; lo vigila `tests/audit/test_un_solo_spec.py`).
- **Cada release de Windows lleva las dos variantes** (pedido por CarlosFB el 2026-09-17): `GuardiasDePatio-<v>-Windows-Setup.exe` (instalador Inno Setup) y `GuardiasDePatio-<v>-Windows-Portable.zip` (carpeta onedir). En el centro casi nadie es administrador y hay un equipo donde el instalador se atasca. No quitar ninguna al tocar `compilar.yml`, `build_windows.ps1` o el spec.
- **Imports dinámicos** (`importlib`, `__getattr__` de módulo, carga perezosa): PyInstaller no los ve. Cada uno nuevo exige su hidden import en el spec y un test en `tests/audit/test_un_solo_spec.py` en la misma sesión (el portable de v6.3.1 moría tras el login por esto). Si «la app no abre» en Windows, pedir antes de tocar código `%APPDATA%\GuardiasDePatio\logs\app_*.log`.
- **Certificados TLS**: el OpenSSL empaquetado no encuentra los del sistema; `update_checker.contexto_ssl()` usa `certifi`. No quitarlo (el DMG dejó de avisar de versiones nuevas).
- **La suite en verde no prueba la app instalada** (rutas de Windows en el spec, «ñ» que rompe la firma, configuración congelada al importar, hoja de estilos sin empaquetar). Esa comprobación la hacen los trabajos de GitHub (`compilar.yml`, `arranque-windows.yml`): se publica la etiqueta **después** del commit y del push de `main`, se espera a que `Compilar` termine en verde y se mira el release. Si falla, se corrige y se mueve la etiqueta; no se arregla compilando en el Mac. Fallos conocidos que mirar en el registro de GitHub: nombres de fichero con acentos (rompen la firma; `scripts/build/nombres_ascii.py`), recursos que no son `.py` sin empaquetar (`*.qss`) y `codesign --verify --strict`, que solo vale sobre la copia del DMG.
- No editar ficheros mientras se compila o corre la suite: bash lee el script a trozos y `settings.py` se relee; el fallo despista. `build_dmg.sh` copia el bundle fuera de iCloud antes de firmarlo.
- Versión: `app_version` y `pyproject.toml` coinciden (ver `AGENTS.md`).
- **Sin LÉEME en el DMG** (desde la 7.3.0, pedido de CarlosFB el 2026-10-10). La app va firmada ad-hoc y sin notarizar: en otro Mac que la descargue, macOS puede decir «está dañada» (Gatekeeper, no un fallo de la app). Remedio: `xattr -dr com.apple.quarantine "/Applications/Guardias de Patio.app"`. Si vuelve a ser un problema, la solución de fondo es la notarización (`APPLE_DEVELOPER_ID` en `build_dmg.sh`), no recuperar el texto.
