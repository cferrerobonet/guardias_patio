# Solución de Problemas de Compilación - Guardias de Patio

## 📋 Historial de Problemas y Soluciones

### Fecha: 28 de Octubre de 2025

---

## 🚨 Problemas Encontrados y Resueltos

### 1. **Iconos SVG No Se Cargaban en App Compilada**

#### Síntoma:
```
⚠️ Icono no encontrado: .../Contents/imagenes/icons/login.svg
⚠️ Icono no encontrado: .../Contents/imagenes/icons/close.svg
⚠️ Icono no encontrado: .../Contents/imagenes/icons/account-plus.svg
```

#### Causa:
El `IconManager` en `src/utils/icon_manager.py` usaba rutas relativas hardcodeadas:

```python
# ❌ CÓDIGO ANTIGUO (INCORRECTO)
def __init__(self):
    if self._icons_path is None:
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent
        self._icons_path = project_root / "imagenes" / "icons"
```

Esto funcionaba en desarrollo pero fallaba en producción porque PyInstaller coloca los recursos en `Contents/Resources/` no en la raíz del bundle.

#### Solución:
Usar el sistema de rutas adaptativas de `core/paths.py`:

```python
# ✅ CÓDIGO NUEVO (CORRECTO)
from core.paths import get_resources_directory

def __init__(self):
    if self._icons_path is None:
        # Usar el sistema de rutas adaptativas para desarrollo y producción
        self._icons_path = get_resources_directory() / "icons"
```

#### Archivo Modificado:
- `src/utils/icon_manager.py` (líneas 1-32)

---

### 2. **App No Abría con `open` (Doble Clic) - Error "Read-only file system"**

#### Síntoma:
```
[PYI-14233:ERROR] Failed to execute script 'main' due to unhandled exception: 
[Errno 30] Read-only file system: 'logs'
```

La app funcionaba al ejecutar directamente el binario:
```bash
./dist/Guardias de Patio.app/Contents/MacOS/Guardias de Patio  # ✅ Funcionaba
```

Pero fallaba al abrir con `open`:
```bash
open "dist/Guardias de Patio.app"  # ❌ Fallaba
```

#### Causa:
Cuando macOS abre una app con `open` o doble clic, establece el **directorio de trabajo (CWD)** dentro del bundle `.app`, que es **de solo lectura**. 

El validador en `settings.py` intentaba crear el directorio `logs/` usando una ruta relativa:

```python
# ❌ CÓDIGO ANTIGUO (INCORRECTO)
@field_validator("log_file")
@classmethod
def create_log_dir(cls, v: str) -> str:
    """Crea el directorio de logs si no existe."""
    log_path = Path(v)  # v = "logs/guardias_patio.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)  # Intenta crear "logs/"
    return v
```

Esto intentaba crear `logs/` en el CWD (directorio actual), que es de solo lectura.

#### Solución:
Eliminar la creación del directorio del validador, ya que `core/logging.py` ya lo hace correctamente usando rutas absolutas:

```python
# ✅ CÓDIGO NUEVO (CORRECTO)
@field_validator("log_file")
@classmethod
def create_log_dir(cls, v: str) -> str:
    """Valida la ruta del archivo de log.
    
    NOTA: No se crea el directorio aquí porque el sistema de logging
    en core/logging.py usa get_logs_directory() para determinar la
    ruta correcta según el entorno (desarrollo vs producción).
    """
    return v
```

El sistema de logging en `core/logging.py` ya usa correctamente:
```python
from core.paths import get_logs_directory

logs_dir = get_logs_directory()  # ~/Library/Application Support/GuardiasDePatio/logs/
self.log_file = str(logs_dir / "guardias_patio.log")
```

#### Archivo Modificado:
- `src/config/settings.py` (líneas 162-170)

---

## 📁 Sistema de Rutas Adaptativas

El archivo `src/core/paths.py` proporciona funciones que detectan automáticamente si la app está en desarrollo o producción:

### Funciones Clave:

```python
get_base_directory()       # Directorio base de la app
get_data_directory()       # Datos de la app (bases de datos)
get_logs_directory()       # Logs del sistema
get_resources_directory()  # Recursos (imágenes, iconos)
```

### Comportamiento:

| Función | Desarrollo | Producción (macOS) |
|---------|------------|-------------------|
| `get_base_directory()` | `/path/to/project/` | `~/Library/Application Support/GuardiasDePatio/` |
| `get_data_directory()` | `/path/to/project/data/` | `~/Library/Application Support/GuardiasDePatio/data/` |
| `get_logs_directory()` | `/path/to/project/logs/` | `~/Library/Application Support/GuardiasDePatio/logs/` |
| `get_resources_directory()` | `/path/to/project/imagenes/` | `Contents/Resources/imagenes/` (dentro del bundle) |

### Detección de Entorno:

```python
if getattr(sys, "frozen", False):
    # Aplicación empaquetada (PyInstaller)
    # Usar directorios del sistema
else:
    # Desarrollo
    # Usar directorios del proyecto
```

---

## 🔧 Comando de Compilación Correcto

### Método 1: Comando Directo (Recomendado)

```bash
python3.11 -m PyInstaller \
  --clean \
  --onedir \
  --windowed \
  --name="Guardias de Patio" \
  --icon="imagenes/icono.icns" \
  --add-data="imagenes:imagenes" \
  --add-data="alembic.ini:." \
  --add-data="alembic:alembic" \
  --hidden-import=sqlalchemy.sql.default_comparator \
  --hidden-import=PyQt6.QtCore \
  --hidden-import=PyQt6.QtGui \
  --hidden-import=PyQt6.QtWidgets \
  --hidden-import=pydantic \
  --hidden-import=alembic \
  --collect-all=sqlalchemy \
  --collect-all=alembic \
  --exclude-module=tkinter \
  src/main.py
```

### Método 2: Usando Script

```bash
./build_simple.sh
```

### ⚠️ NO Usar Archivos .spec

Los archivos `.spec` tienen un bug conocido con PyQt6 en macOS que causa que la compilación se cuelgue indefinidamente en la fase "Building PKG". Usar siempre comandos directos de PyInstaller.

---

## ✅ Checklist de Compilación

Antes de compilar, verificar:

- [ ] **Iconos**: `src/utils/icon_manager.py` usa `get_resources_directory()`
- [ ] **Logs**: `src/config/settings.py` NO crea directorios con rutas relativas
- [ ] **Users**: `src/sync/sync_manager.py` usa `get_data_directory() / "users.json"`
- [ ] **Recursos**: Todos los archivos de datos usan funciones de `core/paths.py`
- [ ] **Python**: Usar Python 3.11 (`python3.11 -m PyInstaller`)
- [ ] **Limpieza**: Ejecutar `rm -rf dist build` antes de compilar

---

## 🧪 Pruebas Post-Compilación

### 1. Probar ejecución directa del binario:
```bash
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio
```
Debe abrir sin errores de iconos o logs.

### 2. Probar apertura con `open`:
```bash
open "dist/Guardias de Patio.app"
```
Debe abrir la ventana de login correctamente.

### 3. Verificar proceso ejecutándose:
```bash
ps aux | grep -i "guardias" | grep -v grep
```
Debe mostrar el proceso activo.

### 4. Verificar directorios del sistema:
```bash
ls -la ~/Library/Application\ Support/GuardiasDePatio/
```
Debe tener:
- `data/` (bases de datos por usuario)
- `logs/` (logs del sistema)

### 5. Verificar que NO hay advertencias de iconos:
```bash
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio 2>&1 | grep "Icono no encontrado"
```
No debe retornar nada.

---

## 🐛 Debugging

### Ver logs de macOS:
```bash
log show --predicate 'process == "Guardias de Patio"' --info --last 5m
```

### Ver errores específicos de PyInstaller:
```bash
log show --predicate 'process == "Guardias de Patio"' --info --last 5m | grep "PYI-.*ERROR"
```

### Verificar estructura del bundle:
```bash
ls -la "dist/Guardias de Patio.app/Contents/Resources/imagenes/icons/"
```
Debe contener todos los archivos `.svg`.

---

## 📝 Notas Importantes

### ⚠️ Diferencia entre `open` y ejecución directa:

**Ejecución directa:**
```bash
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio
```
- CWD (directorio actual) = `/Users/.../Guardias de patio/`
- Puede escribir en el CWD
- Útil para debugging

**Apertura con `open` (doble clic):**
```bash
open "dist/Guardias de Patio.app"
```
- CWD (directorio actual) = `dist/Guardias de Patio.app/Contents/` (de solo lectura)
- NO puede escribir en el CWD
- Es como el usuario final abrirá la app

**Por eso es CRÍTICO usar rutas absolutas del sistema, nunca rutas relativas.**

### ✅ Regla de Oro:

**SIEMPRE usar las funciones de `core/paths.py`:**

```python
# ❌ NUNCA hacer esto:
log_file = "logs/app.log"
users_file = "users.json"
icon_path = "imagenes/icons/login.svg"

# ✅ SIEMPRE hacer esto:
from core.paths import get_logs_directory, get_data_directory, get_resources_directory

log_file = get_logs_directory() / "app.log"
users_file = get_data_directory() / "users.json"
icon_path = get_resources_directory() / "icons" / "login.svg"
```

---

## 📚 Referencias

- **PyInstaller Docs**: https://pyinstaller.org/
- **PyQt6 + PyInstaller**: https://doc.qt.io/qtforpython/deployment-pyinstaller.html
- **macOS App Bundle Structure**: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/BundleTypes/BundleTypes.html

---

## 🎯 Resumen Ejecutivo

### Cambios Críticos Realizados:

1. **`src/utils/icon_manager.py`**
   - Cambiado de rutas hardcodeadas a `get_resources_directory()`
   - Fix: Iconos se cargan correctamente en producción

2. **`src/config/settings.py`**
   - Eliminada creación de directorio con rutas relativas
   - Fix: App abre correctamente con `open` (doble clic)

### Resultado:
✅ App compilada funciona perfectamente tanto en desarrollo como en producción  
✅ Todos los recursos (iconos, logs, datos) usan rutas adaptativas  
✅ La app se puede distribuir sin problemas  

---

**Última actualización:** 28 de Octubre de 2025  
**Versión compilada exitosamente:** PyInstaller 6.16.0 + Python 3.11.14 + PyQt6
