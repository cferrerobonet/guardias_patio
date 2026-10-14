# Scripts de compilación

| Script | Plataforma | Qué hace |
| --- | --- | --- |
| `build_dmg.sh` | macOS | Compila la app, la firma fuera de iCloud y crea el DMG. Con `SKIP_RELEASE=1` no publica el release. Se invoca con `make dmg`. |
| `create_icon.sh` | macOS | Genera el icono `.icns`. Lo llama `make icon`. |
| `../build_windows.ps1` | Windows | Único script de Windows. Genera el exe y el instalador de Inno Setup. Con `-Diagnostico` compila con consola y volcado de hilos. |

## Compilar sin tener un PC con Windows

El flujo `.github/workflows/compilar.yml` compila las dos plataformas en los
ordenadores de GitHub. Al publicar una etiqueta `vX.Y.Z` adjunta los dos
instaladores al release; también se puede lanzar a mano desde la pestaña
Actions para descargarlos sin publicar nada.

Los scripts obsoletos `build_simple.sh`, `create_dmg.sh`, `build_windows.ps1` y
`build_windows.bat` de esta carpeta se eliminaron en la versión 5.50.0: tenían
versiones fijas y referenciaban un fichero `.spec` que no existe.
