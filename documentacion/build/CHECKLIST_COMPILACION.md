# ✅ Checklist de Verificación Pre-Compilación

## Antes de Compilar

Usa este checklist para asegurarte de que no introducirás bugs de compilación:

---

### 🎯 1. Rutas de Archivos

**SIEMPRE usar funciones de `core/paths.py`, NUNCA rutas relativas.**

#### ✅ Verificar en cada archivo nuevo:

```python
# ❌ MAL - Rutas relativas
log_file = "logs/app.log"
icon_path = "imagenes/icons/login.svg"
db_path = "data/guardias.db"
users_file = "users.json"

# ✅ BIEN - Rutas adaptativas
from core.paths import get_logs_directory, get_resources_directory, get_data_directory

log_file = get_logs_directory() / "app.log"
icon_path = get_resources_directory() / "icons" / "login.svg"
db_path = get_data_directory() / "guardias.db"
users_file = get_data_directory() / "users.json"
```

#### 📝 Archivos críticos a verificar:

- [ ] `src/utils/icon_manager.py` - Debe usar `get_resources_directory()`
- [ ] `src/config/settings.py` - NO debe crear directorios en validadores
- [ ] `src/sync/sync_manager.py` - Debe usar `get_data_directory() / "users.json"`
- [ ] `src/core/logging.py` - Debe usar `get_logs_directory()`
- [ ] Cualquier nuevo archivo que acceda a recursos

---

### 🔍 2. Validadores de Pydantic

**NO crear directorios con rutas relativas en validadores de `settings.py`**

#### ❌ Evitar:

```python
@field_validator("log_file")
@classmethod
def create_log_dir(cls, v: str) -> str:
    log_path = Path(v)  # Ruta relativa
    log_path.parent.mkdir(parents=True, exist_ok=True)  # ¡ERROR en producción!
    return v
```

#### ✅ Correcto:

```python
@field_validator("log_file")
@classmethod
def validate_log_file(cls, v: str) -> str:
    """Solo valida, no crea directorios.
    
    Los directorios se crean en core/logging.py usando get_logs_directory()
    """
    return v
```

---

### 📦 3. Recursos (Imágenes, Iconos, Archivos)

**Verificar que todos los recursos estén en `--add-data` del comando PyInstaller**

#### Checklist de recursos:

- [ ] `imagenes/` incluido en `--add-data="imagenes:imagenes"`
- [ ] `alembic.ini` incluido en `--add-data="alembic.ini:."`
- [ ] `alembic/` incluido en `--add-data="alembic:alembic"`
- [ ] Nuevos recursos agregados al comando de compilación

#### Verificar en `build_simple.sh`:

```bash
--add-data="imagenes:imagenes" \
--add-data="alembic.ini:." \
--add-data="alembic:alembic" \
# ¿Hay nuevos recursos? Agregar aquí
```

---

### 🚫 4. NO Usar Archivos .spec

**NUNCA compilar usando archivos `.spec`**

#### ❌ Evitar:

```bash
pyinstaller "Guardias de Patio.spec"  # ¡Se colgará en "Building PKG"!
```

#### ✅ Siempre usar:

```bash
./build_simple.sh  # Usa comando directo de PyInstaller
```

**Motivo:** PyQt6 tiene un bug con symlinks en archivos .spec que causa que la compilación se cuelgue indefinidamente.

---

### 🧪 5. Testing Post-Compilación

Después de compilar, ejecutar TODAS estas pruebas:

#### Test 1: Ejecución directa del binario
```bash
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio 2>&1 | head -30
```

**Verificar:**
- [ ] No hay errores de "Icono no encontrado"
- [ ] No hay errores de "Read-only file system"
- [ ] La app abre la ventana de login

#### Test 2: Apertura con `open`
```bash
open "dist/Guardias de Patio.app"
```

**Verificar:**
- [ ] La app se abre (ventana visible)
- [ ] El proceso aparece en `ps aux | grep Guardias`
- [ ] No hay crashes en logs del sistema

#### Test 3: Verificar proceso activo
```bash
sleep 3 && ps aux | grep -i "guardias" | grep -v grep
```

**Debe mostrar:**
```
usuario   12345  0.0  0.5  ... /Users/.../Guardias de Patio.app/Contents/MacOS/Guardias de Patio
```

#### Test 4: Verificar directorios del sistema
```bash
ls -la ~/Library/Application\ Support/GuardiasDePatio/
```

**Debe tener:**
- [ ] `data/` (creado al iniciar)
- [ ] `logs/` (creado al iniciar)

#### Test 5: Sin iconos faltantes
```bash
./dist/Guardias\ de\ Patio.app/Contents/MacOS/Guardias\ de\ Patio 2>&1 | grep "Icono no encontrado"
```

**No debe retornar nada** (grep exit code 1)

#### Test 6: Estructura del bundle correcta
```bash
ls -la "dist/Guardias de Patio.app/Contents/Resources/imagenes/icons/" | head -10
```

**Debe mostrar todos los archivos .svg**

---

### 📝 6. Documentación

**Si modificas rutas o compilación, actualizar:**

- [ ] `documentacion/SOLUCION_COMPILACION.md` - Si encuentras/arreglas un bug
- [ ] `COMPILACION_RAPIDA.md` - Si cambia el proceso de compilación
- [ ] `build_simple.sh` - Comentarios sobre cambios
- [ ] Comentarios en código modificado

---

### 🔴 7. Red Flags (Señales de Peligro)

Si ves cualquiera de estos patrones en código nuevo, **¡DETENTE!**:

```python
# 🚨 PELIGRO 1: Rutas relativas
Path("logs/app.log")
Path("data/db.sqlite")
"imagenes/icons/icon.svg"

# 🚨 PELIGRO 2: Crear directorios en validadores de Pydantic
@field_validator("some_field")
def validator(cls, v):
    Path(v).parent.mkdir(parents=True, exist_ok=True)  # ¡NO!

# 🚨 PELIGRO 3: Hardcodear rutas del proyecto
project_root = Path(__file__).parent.parent.parent
icons_path = project_root / "imagenes" / "icons"

# 🚨 PELIGRO 4: Asumir CWD es el proyecto
os.chdir("somewhere")
with open("file.txt") as f:  # ¡Depende de CWD!
```

**Solución para todos:** Usar funciones de `core/paths.py`

---

### ✅ 8. Comando de Compilación Final

**Antes de hacer commit, ejecutar:**

```bash
# 1. Limpiar
rm -rf dist build

# 2. Compilar
./scripts/build/build_simple.sh

# 3. Probar con open
open "dist/Guardias de Patio.app"

# 4. Verificar sin errores
sleep 5 && ps aux | grep Guardias | grep -v grep
```

**Si todo funciona:** ✅ Safe to commit

**Si algo falla:** ❌ Revisar este checklist

---

## 🆘 En Caso de Problemas

1. **Lee primero:** [`SOLUCION_COMPILACION.md`](SOLUCION_COMPILACION.md)
2. **Verifica:** Este checklist completo
3. **Logs del sistema:** `log show --predicate 'process == "Guardias de Patio"' --last 5m`
4. **Ejecuta pruebas:** Sección 5 de este checklist

---

## 📚 Recursos

- **Solución de problemas:** [`SOLUCION_COMPILACION.md`](SOLUCION_COMPILACION.md)
- **Guía rápida:** [`COMPILACION_RAPIDA.md`](COMPILACION_RAPIDA.md)
- **Sistema de rutas:** `../../src/core/paths.py` (leer docstring)
- **Build DMG:** [`BUILD_DMG.md`](BUILD_DMG.md)

---

**Última actualización:** 28 de Octubre de 2025  
**Mantenedor:** Carlos Ferrero Bonet
