# Compilación y Distribución - Guardias de Patio

> **⚠️ IMPORTANTE**: Si tienes problemas de compilación, consulta primero [SOLUCION_COMPILACION.md](./SOLUCION_COMPILACION.md) que documenta todos los problemas conocidos y sus soluciones.

## 📋 Índice

1. [Configuración del Entorno](#configuración-del-entorno)
2. [Compilación de la Aplicación](#compilación-de-la-aplicación)
3. [Creación del DMG](#creación-del-dmg)
4. [Puntos Importantes](#puntos-importantes)
5. [Resolución de Problemas](#resolución-de-problemas)

---

## Configuración del Entorno

### Archivo de Entrada Correcto

⚠️ **IMPORTANTE**: La aplicación debe compilarse usando `main_ccleaner.py`, NO `main.py`

**Motivo**: 
- `main_ccleaner.py` utiliza el tema CCleaner (diseño moderno)
- `main.py` utiliza el tema antiguo Fluent

El archivo `Guardias de Patio.spec` está configurado correctamente para usar:

```python
a = Analysis(
    ['src/main_ccleaner.py'],  # ← Archivo correcto
    ...
)
```

### Sistema de Rutas

La aplicación utiliza un sistema de rutas centralizado en `src/core/paths.py` que:

1. **Detecta automáticamente** si está en modo desarrollo o producción (empaquetada)
2. **Usa directorios apropiados** del sistema operativo:
   - **macOS**: `~/Library/Application Support/GuardiasDePatio/`
   - **Windows**: `%APPDATA%/GuardiasDePatio/`
   - **Linux**: `~/.local/share/GuardiasDePatio/`

Estructura de directorios en producción (macOS):
```
~/Library/Application Support/GuardiasDePatio/
├── logs/
│   └── guardias_patio.log
├── data/
│   └── users/
│       └── {user_hash}/
│           └── guardias_patio.db
└── imagenes/
    ├── logo.png
    └── icono.icns
```

### Inicialización de Base de Datos

La aplicación **inicializa automáticamente** la base de datos en el primer arranque:

1. **Creación de tablas**: Usando `Base.metadata.create_all()`
2. **Migraciones Alembic**: Ejecuta `alembic upgrade head` automáticamente
3. **Esquema por usuario**: Cada usuario tiene su propia base de datos SQLite

Ver implementación en `src/database/db_manager.py` función `_run_alembic_migrations()`

---

## Compilación de la Aplicación

### Método 1: Usando PyInstaller directamente

```bash
cd "/Users/cferrerobonet/Documents/04 DESARROLLADOR/Python/Guardias de patio"

# Limpiar builds anteriores
rm -rf build/ dist/

# Compilar usando el spec file
/opt/homebrew/bin/python3.11 -m PyInstaller "Guardias de Patio.spec" --clean --noconfirm
```

### Método 2: Usando el script de build completo

```bash
cd "/Users/cferrerobonet/Documents/04 DESARROLLADOR/Python/Guardias de patio"

# Ejecutar script que compila y crea DMG
bash build_dmg.sh
```

### Archivos Incluidos en el Bundle

El spec file incluye automáticamente:

```python
datas = [
    ('imagenes', 'imagenes'),      # Iconos, logos, recursos visuales
    ('alembic.ini', '.'),          # Configuración de Alembic
    ('alembic', 'alembic')         # Scripts de migración
]
```

---

## Creación del DMG

### Script Automatizado

El script `build_dmg.sh` realiza:

1. **Limpieza** de builds anteriores
2. **Compilación** con PyInstaller
3. **Creación de DMG** con:
   - Fondo personalizado
   - Acceso directo a `/Applications`
   - Compresión optimizada

### Ejecución Manual

```bash
# 1. Compilar la app
/opt/homebrew/bin/python3.11 -m PyInstaller "Guardias de Patio.spec" --clean --noconfirm

# 2. Crear DMG
bash build_dmg.sh
```

### Resultado

Archivo DMG creado en:
```
dist/GuardiasDePatio-{VERSION}-macOS.dmg
```

Tamaño aproximado: ~90-100 MB (comprimido)

---

## Puntos Importantes

### 1. ✅ Tema Correcto (CCleaner)

La aplicación compilada DEBE usar `main_ccleaner.py` para:
- Diseño moderno estilo CCleaner
- Sidebar con navegación por iconos
- Tematización consistente

### 2. ✅ Rutas Adaptativas

El sistema de rutas en `core/paths.py` detecta automáticamente:
- **Desarrollo**: Usa directorios del proyecto (`data/`, `logs/`, `imagenes/`)
- **Producción**: Usa directorios del sistema (`~/Library/Application Support/...`)

### 3. ✅ Base de Datos Auto-inicializada

No requiere pasos manuales de inicialización:
- Primera ejecución: Crea tablas + ejecuta migraciones
- Ejecuciones posteriores: Usa esquema existente
- Por usuario: Bases de datos aisladas

### 4. ✅ Recursos Empaquetados

Los recursos (imágenes, iconos) se incluyen en el bundle y son accesibles mediante:

```python
from core.paths import get_resources_directory

logo_path = get_resources_directory() / "logo.png"
```

---

## Resolución de Problemas

### Error: "no such table: profesores"

**Causa**: Base de datos no inicializada o migraciones no ejecutadas

**Solución**: 
- La función `_run_alembic_migrations()` en `db_manager.py` lo hace automáticamente
- Si persiste, verificar que `alembic.ini` esté incluido en el bundle

### Error: "Read-only file system: 'logs'"

**Causa**: Intentando escribir en el directorio de la aplicación empaquetada

**Solución**: 
- Ya corregido usando `get_logs_directory()` de `core/paths.py`
- Los logs se escriben en `~/Library/Application Support/GuardiasDePatio/logs/`

### La App se Abre con Tema Incorrecto

**Causa**: Compilada usando `main.py` en lugar de `main_ccleaner.py`

**Solución**:
```bash
# Verificar Guardias de Patio.spec línea 13:
a = Analysis(
    ['src/main_ccleaner.py'],  # ← Debe ser main_ccleaner.py
    ...
)

# Recompilar
/opt/homebrew/bin/python3.11 -m PyInstaller "Guardias de Patio.spec" --clean --noconfirm
```

### Advertencia de Firma de Código

```
WARNING: Error while signing the bundle
```

**Explicación**: 
- Es normal en desarrollo sin certificado de desarrollador
- La app funciona correctamente
- Para distribución pública, se requiere certificado de Apple Developer

**Firma manual** (opcional):
```bash
codesign --deep --force --sign "Developer ID Application: TU NOMBRE" \
  "dist/Guardias de Patio.app"
```

### Verificar la Compilación

```bash
# Ver logs de la última ejecución
log show --predicate 'process == "Guardias de Patio"' --info --last 5m

# Ejecutar desde terminal para ver errores
cd "dist/Guardias de Patio.app/Contents/MacOS"
./"Guardias de Patio"

# Verificar que usa main_ccleaner
strings "dist/Guardias de Patio.app/Contents/MacOS/Guardias de Patio" | grep main_ccleaner
```

---

## Checklist Pre-Distribución

Antes de crear el DMG final:

- [ ] ✅ Spec file usa `main_ccleaner.py`
- [ ] ✅ Versión actualizada en `pyproject.toml`
- [ ] ✅ Tests pasando (`pytest`)
- [ ] ✅ Base de datos se inicializa correctamente
- [ ] ✅ Logs se escriben en directorio correcto
- [ ] ✅ Recursos (imágenes) accesibles
- [ ] ✅ Tema CCleaner se carga correctamente
- [ ] ✅ No hay errores en la consola de macOS
- [ ] ✅ DMG se monta y la app se arrastra a Applications

---

## Mantenimiento

### Actualizar Versión

1. Editar `pyproject.toml`:
   ```toml
   version = "2.8.0"  # Nueva versión
   ```

2. El script `build_dmg.sh` usa automáticamente esta versión para nombrar el DMG:
   ```
   GuardiasDePatio-2.8.0-macOS.dmg
   ```

### Añadir Nuevos Recursos

Si se añaden nuevas imágenes/iconos:

1. Colocarlos en `imagenes/`
2. Ya están incluidos automáticamente en el bundle
3. Accederlos usando:
   ```python
   from core.paths import get_resources_directory
   new_icon = get_resources_directory() / "nuevo_icono.png"
   ```

### Añadir Nuevas Dependencias

Si se instala un nuevo paquete:

1. Añadirlo a `requirements.txt`
2. Si PyInstaller no lo detecta automáticamente, añadirlo a `hiddenimports` en el spec file:
   ```python
   hiddenimports = [
       'sqlalchemy.sql.default_comparator',
       'PyQt6.QtCore',
       # ... existentes ...
       'nuevo_paquete',  # ← Añadir aquí
   ]
   ```

---

## Comandos Rápidos

```bash
# Compilar y crear DMG en un solo paso
bash build_dmg.sh

# Solo compilar (sin DMG)
/opt/homebrew/bin/python3.11 -m PyInstaller "Guardias de Patio.spec" --clean --noconfirm

# Limpiar todo
rm -rf build/ dist/

# Ver tamaño del bundle
du -sh "dist/Guardias de Patio.app"

# Probar la app
open "dist/Guardias de Patio.app"
```

---

**Última actualización**: 26 de octubre de 2025  
**Versión del documento**: 1.0  
**Autor**: Sistema de Compilación Guardias de Patio
