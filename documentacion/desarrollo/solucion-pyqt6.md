# Solución al problema de PyQt6 en macOS

## Problema
PyQt6 falla al cargar con error:
```
ImportError: Library not loaded: @rpath/QtCore.framework/Versions/A/QtCore
```

## Causa
En algunas situaciones, `pip install PyQt6` no instala correctamente el paquete `PyQt6-Qt6` que contiene los frameworks de Qt necesarios, o los archivos se corrompen entre instalaciones.

## Solución

### Opción 1: Reinstalación Limpia (Recomendado)
```bash
# Activar el entorno virtual
source .venv/bin/activate

# Eliminar completamente PyQt6
rm -rf .venv/lib/python3.9/site-packages/PyQt6*

# Reinstalar desde cero
pip install --no-cache-dir PyQt6==6.7.0

# Verificar
python -c "from PyQt6.QtCore import QT_VERSION_STR; print('Qt version:', QT_VERSION_STR)"
```

### Opción 2: Script Automático
Usar el script `fix_pyqt6.sh` incluido en el proyecto:
```bash
./fix_pyqt6.sh
```

## Prevención
Para evitar este problema en el futuro:

1. **Especificar ambas versiones en `requirements.txt`**:
   ```
   PyQt6==6.7.0
   PyQt6-Qt6==6.7.3
   ```

2. **Reinstalar después de problemas**:
   Si la app falla con errores de Qt, ejecutar:
   ```bash
   rm -rf .venv/lib/python3.9/site-packages/PyQt6*
   pip install --no-cache-dir -r requirements.txt
   ```

3. **NO usar** `pip install` y `pip uninstall` repetidamente sin limpiar primero.

## Notas Técnicas
- PyQt6 6.7.0 es compatible con PyQt6-Qt6 6.7.3
- Los binarios `.abi3.so` buscan frameworks en `@loader_path/Qt6/lib`
- En macOS ARM64, se debe usar la wheel específica de arquitectura
- La variable de entorno `QT_MAC_WANTS_LAYER=1` es necesaria en `run_app.sh`

## Verificación
Después de reinstalar, verificar que funciona:
```bash
./run_app.sh
```

La aplicación debería abrir sin errores de importación.
