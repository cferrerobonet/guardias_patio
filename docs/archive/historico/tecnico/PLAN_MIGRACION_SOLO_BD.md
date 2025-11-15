# Plan de Migración: SQLite como Única Fuente de Verdad

## 🎯 Objetivo

Eliminar la duplicidad de datos entre BD SQLite y archivos JSON, estableciendo SQLite como la única fuente de verdad y usando JSON únicamente para:
- Exportación de datos
- Importación de datos
- Backup/Restauración local
- Sincronización con la nube

## ⚠️ Problema Actual

### Arquitectura Problemática
```
┌─────────────────────────────────────────────────────────────┐
│  APLICACIÓN                                                  │
│                                                              │
│  ┌─────────────┐              ┌──────────────┐             │
│  │   BD SQLite │◄────?────────┤  JSON Files  │             │
│  │ (guardias_  │              │  (guardias_  │             │
│  │  patio.db)  │────?────────►│   patio_     │             │
│  └─────────────┘              │   data.json) │             │
│        ▲                       └──────────────┘             │
│        │                              ▲                      │
│        │                              │                      │
│        ▼                              ▼                      │
│  ¿Cuál es la    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━          │
│  fuente de                                                   │
│  verdad? 🤔                                                  │
└─────────────────────────────────────────────────────────────┘
```

### Problemas Identificados

1. **Desincronización de datos**:
   - Los scripts actualizan JSON pero no BD
   - La aplicación lee de BD pero JSON puede estar desactualizado
   - No está claro qué prevalece en caso de conflicto

2. **Duplicación de lógica**:
   - Código de carga desde JSON
   - Código de carga desde BD
   - Código de sincronización JSON ↔ BD

3. **Bugs de consistencia**:
   - Profesores de tarde con cuota 0 en BD pero 30 en JSON
   - Recreos vacíos en BD pero llenos en JSON
   - Imposible saber qué datos son correctos

## ✅ Arquitectura Objetivo

### Arquitectura Limpia
```
┌─────────────────────────────────────────────────────────────┐
│  APLICACIÓN                                                  │
│                                                              │
│  ┌─────────────┐                                            │
│  │   BD SQLite │  ◄─── ÚNICA FUENTE DE VERDAD               │
│  │ (guardias_  │                                            │
│  │  patio.db)  │                                            │
│  └─────────────┘                                            │
│        │                                                     │
│        │ Exportar cuando sea necesario                      │
│        ▼                                                     │
│  ┌──────────────┐                                           │
│  │  JSON Files  │  ◄─── SOLO PARA:                          │
│  │  (guardias_  │       • Exportación manual                │
│  │   patio_     │       • Importación/Restauración          │
│  │   data.json) │       • Backup local                      │
│  │              │       • Sincronización nube               │
│  └──────────────┘                                           │
│                                                              │
│  FLUJO UNIDIRECCIONAL:                                       │
│  BD ──export──► JSON ──upload──► Nube                       │
│  BD ◄─import─── JSON ◄─download─ Nube                       │
└─────────────────────────────────────────────────────────────┘
```

## 📝 FASES DE IMPLEMENTACIÓN

### FASE 1: Auditoría y Análisis (1-2 horas)

**Objetivo**: Identificar todos los lugares donde se lee/escribe JSON

#### Tareas:
1. ✅ **Buscar todos los usos de JSON**:
   ```bash
   grep -r "guardias_patio_data.json" src/
   grep -r "json.load\|json.dump" src/
   grep -r "JSONDatabase\|json_database" src/
   ```

2. ✅ **Catalogar archivos afectados**:
   - `src/models/database.py` - Clase JSONDatabase
   - `src/sync/sync_manager.py` - Sincronización nube
   - Scripts de migración/importación
   - Cualquier form que lea/escriba JSON directamente

3. ✅ **Crear lista de migraciones necesarias**:
   - Formularios que escriben a JSON → cambiar a BD
   - Scripts que leen de JSON → cambiar a BD
   - Lógica de sincronización → refactorizar

#### Entregables:
- `AUDITORIA_JSON_USAGE.md` con lista completa de archivos
- Lista priorizada de cambios

---

### FASE 2: Implementar Sistema de Exportación/Importación (2-3 horas)

**Objetivo**: Crear servicios centralizados para exportar/importar JSON

#### 2.1 Crear Servicio de Exportación

**Archivo**: `src/services/export_service.py`

```python
class ExportService:
    """Servicio para exportar datos de BD a JSON."""
    
    def export_to_json(self, session: Session, output_path: Path) -> bool:
        """
        Exporta todos los datos de la BD a un archivo JSON.
        
        Args:
            session: Sesión de SQLAlchemy
            output_path: Ruta donde guardar el JSON
            
        Returns:
            True si la exportación fue exitosa
        """
        # Leer todos los datos de BD
        data = {
            'configuracion': self._export_configuracion(session),
            'profesores': self._export_profesores(session),
            'zonas': self._export_zonas(session),
            'guardias': self._export_guardias(session),
            'ausencias': self._export_ausencias(session),
            'metadata': {
                'exported_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }
        
        # Escribir JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return True
```

#### 2.2 Crear Servicio de Importación

**Archivo**: `src/services/import_service.py`

```python
class ImportService:
    """Servicio para importar datos de JSON a BD."""
    
    def import_from_json(self, session: Session, json_path: Path) -> bool:
        """
        Importa datos desde un archivo JSON a la BD.
        
        Args:
            session: Sesión de SQLAlchemy
            json_path: Ruta del archivo JSON a importar
            
        Returns:
            True si la importación fue exitosa
        """
        # Leer JSON
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Limpiar BD actual (opcional, con confirmación)
        # self._clear_database(session)
        
        # Importar cada entidad
        self._import_configuracion(session, data.get('configuracion'))
        self._import_profesores(session, data.get('profesores', []))
        self._import_zonas(session, data.get('zonas', []))
        self._import_guardias(session, data.get('guardias', []))
        self._import_ausencias(session, data.get('ausencias', []))
        
        session.commit()
        return True
```

#### Entregables:
- ✅ `export_service.py` implementado y testeado
- ✅ `import_service.py` implementado y testeado
- ✅ Tests unitarios para ambos servicios

---

### FASE 3: Refactorizar Sincronización con Nube (2-3 horas)

**Objetivo**: Actualizar `SyncManager` para usar BD como fuente

#### 3.1 Modificar SyncManager

**Cambios en**: `src/sync/sync_manager.py`

```python
class SyncManager:
    """Gestor de sincronización con la nube."""
    
    def __init__(self, session: Session, export_service: ExportService):
        self.session = session
        self.export_service = export_service
        # ...
    
    def sync_on_shutdown(self) -> bool:
        """
        Sincroniza datos antes de cerrar la aplicación.
        
        FLUJO:
        1. Exportar BD → JSON temporal
        2. Subir JSON a nube
        3. Eliminar JSON temporal (opcional)
        """
        # 1. Exportar desde BD
        temp_json = Path("temp_export.json")
        self.export_service.export_to_json(self.session, temp_json)
        
        # 2. Subir a nube
        success = self._upload_to_cloud(temp_json)
        
        # 3. Cleanup (opcional)
        if success and not self.keep_local_backup:
            temp_json.unlink()
        
        return success
    
    def sync_on_startup(self) -> bool:
        """
        Sincroniza datos al iniciar la aplicación.
        
        FLUJO:
        1. Descargar JSON de nube
        2. Importar JSON → BD
        """
        # 1. Descargar
        temp_json = self._download_from_cloud()
        if not temp_json:
            return False
        
        # 2. Importar a BD
        from services.import_service import ImportService
        import_service = ImportService()
        success = import_service.import_from_json(self.session, temp_json)
        
        return success
```

#### Entregables:
- ✅ `SyncManager` refactorizado
- ✅ Sincronización funcional BD → Nube → BD
- ✅ Tests de integración

---

### FASE 4: Eliminar JSONDatabase (1-2 horas)

**Objetivo**: Remover completamente la clase JSONDatabase

#### 4.1 Identificar Dependencias

```bash
# Buscar todos los usos de JSONDatabase
grep -r "JSONDatabase" src/
grep -r "from.*json_database" src/
```

#### 4.2 Refactorizar Código

**Para cada archivo que use JSONDatabase**:
1. Cambiar a usar `session` de SQLAlchemy
2. Usar repositorios existentes (ProfesorRepository, etc.)
3. Eliminar imports de JSONDatabase

#### 4.3 Deprecar Archivo

1. Marcar `src/models/json_database.py` como deprecado
2. Añadir warning si alguien intenta usarlo
3. Eventualmente eliminar el archivo completo

#### Entregables:
- ✅ Todos los forms usan SQLAlchemy
- ✅ `json_database.py` eliminado
- ✅ Tests actualizados

---

### FASE 5: Actualizar UI para Exportar/Importar (1-2 horas)

**Objetivo**: Añadir opciones de exportación/importación en la UI

#### 5.1 Menú de Archivo

Añadir opciones en el menú principal:

```python
# En main.py o main_window.py

def crear_menu_archivo(self):
    menu_archivo = self.menuBar().addMenu("📁 Archivo")
    
    # Exportar datos
    action_export = QAction("💾 Exportar Datos...", self)
    action_export.setShortcut("Ctrl+E")
    action_export.triggered.connect(self.exportar_datos)
    menu_archivo.addAction(action_export)
    
    # Importar datos
    action_import = QAction("📥 Importar Datos...", self)
    action_import.setShortcut("Ctrl+I")
    action_import.triggered.connect(self.importar_datos)
    menu_archivo.addAction(action_import)
    
    menu_archivo.addSeparator()
    
    # Backup local
    action_backup = QAction("💿 Crear Backup Local...", self)
    action_backup.triggered.connect(self.crear_backup)
    menu_archivo.addAction(action_backup)
    
    # Restaurar backup
    action_restore = QAction("♻️  Restaurar Backup...", self)
    action_restore.triggered.connect(self.restaurar_backup)
    menu_archivo.addAction(action_restore)

def exportar_datos(self):
    """Exportar todos los datos a JSON."""
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Exportar Datos",
        f"guardias_backup_{datetime.now():%Y%m%d_%H%M}.json",
        "JSON Files (*.json)"
    )
    
    if file_path:
        export_service = ExportService()
        success = export_service.export_to_json(self.session, Path(file_path))
        if success:
            QMessageBox.information(
                self,
                "Exportación Exitosa",
                f"Datos exportados a:\n{file_path}"
            )

def importar_datos(self):
    """Importar datos desde JSON."""
    # Confirmar que esto sobrescribirá datos
    reply = QMessageBox.question(
        self,
        "Confirmar Importación",
        "⚠️  ADVERTENCIA: Esto reemplazará TODOS los datos actuales.\n\n"
        "Se recomienda crear un backup antes de continuar.\n\n"
        "¿Desea continuar?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if reply != QMessageBox.StandardButton.Yes:
        return
    
    file_path, _ = QFileDialog.getOpenFileName(
        self,
        "Importar Datos",
        "",
        "JSON Files (*.json)"
    )
    
    if file_path:
        import_service = ImportService()
        success = import_service.import_from_json(self.session, Path(file_path))
        if success:
            QMessageBox.information(
                self,
                "Importación Exitosa",
                "Datos importados correctamente.\n\n"
                "Se recomienda reiniciar la aplicación."
            )
```

#### Entregables:
- ✅ Menú "Archivo" con opciones de exportar/importar
- ✅ Diálogos de confirmación para operaciones destructivas
- ✅ Mensajes de éxito/error claros

---

### FASE 6: Solucionar Problema Actual (URGENTE - 30 min)

**Objetivo**: Arreglar cuotas de profesores de tarde AHORA

#### Script de Reparación Inmediata

**Archivo**: `scripts/reparar_cuotas_bd.py`

```python
#!/usr/bin/env python3
"""
Script de reparación URGENTE: Actualiza cuotas en la BASE DE DATOS.

Este script lee los datos correctos del JSON (que ya fueron actualizados)
y los escribe en la BD SQLite, que es la que usa realmente la aplicación.
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import json
from models.database import SessionLocal
from models.models import Profesor

def main():
    print("=" * 80)
    print("REPARACIÓN URGENTE: Actualizar cuotas en BASE DE DATOS")
    print("=" * 80)
    print()
    
    # Ruta al JSON (que ya tiene los datos correctos)
    json_path = Path(__file__).parent.parent / "data/0db13e2857239ed8/guardias_patio_data.json"
    
    if not json_path.exists():
        print(f"❌ No se encontró: {json_path}")
        return
    
    # Leer JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    profesores_json = data.get('profesores', [])
    print(f"📄 JSON cargado: {len(profesores_json)} profesores")
    print()
    
    # Conectar a BD
    session = SessionLocal()
    
    # Actualizar cada profesor en BD
    actualizados = 0
    errores = 0
    
    for prof_data in profesores_json:
        try:
            # Buscar profesor en BD por ID
            prof_id = prof_data.get('id')
            if not prof_id:
                continue
            
            profesor = session.query(Profesor).filter(Profesor.id == prof_id).first()
            if not profesor:
                print(f"⚠️  Profesor ID {prof_id} no encontrado en BD")
                continue
            
            # Actualizar campos
            recreos = prof_data.get('recreos', [])
            cuota = prof_data.get('cuota_anual', 30.0)
            recreos_permitidos = prof_data.get('recreos_permitidos', '')
            
            # Solo actualizar si hay cambios
            cambios = []
            
            if profesor.recreos != recreos:
                profesor.recreos = recreos
                cambios.append(f"recreos: {recreos}")
            
            if profesor.cuota_anual != cuota:
                profesor.cuota_anual = cuota
                cambios.append(f"cuota: {cuota}")
            
            if profesor.recreos_permitidos != recreos_permitidos:
                profesor.recreos_permitidos = recreos_permitidos
                cambios.append(f"restricciones")
            
            if cambios:
                print(f"  ✓ {profesor.nombre_completo[:40]:40s} → {', '.join(cambios)}")
                actualizados += 1
            
        except Exception as e:
            print(f"  ❌ Error con profesor {prof_data.get('nombre_completo', 'desconocido')}: {e}")
            errores += 1
    
    # Guardar cambios
    session.commit()
    session.close()
    
    print()
    print("=" * 80)
    print("RESULTADO")
    print("=" * 80)
    print(f"  ✓ Profesores actualizados: {actualizados}")
    if errores > 0:
        print(f"  ❌ Errores: {errores}")
    print()
    print("✅ BASE DE DATOS actualizada correctamente")
    print("   Ahora puedes abrir la aplicación y regenerar las guardias.")
    print()

if __name__ == "__main__":
    main()
```

#### Ejecutar Script

```bash
cd "/Users/cferrerobonet/Documents/04 DESARROLLADOR/Python/Guardias de patio"
/opt/homebrew/bin/python3.11 scripts/reparar_cuotas_bd.py
```

#### Entregables:
- ✅ Script ejecutado
- ✅ BD actualizada con cuotas correctas
- ✅ Profesores de tarde con recreos [3,4] y cuota 30

---

### FASE 7: Testing y Validación (1-2 horas)

**Objetivo**: Verificar que todo funciona correctamente

#### 7.1 Tests Unitarios

```python
# tests/test_export_import.py

def test_export_import_cycle():
    """Exportar y reimportar debe mantener los datos intactos."""
    # Exportar
    export_service = ExportService()
    export_service.export_to_json(session, "test_export.json")
    
    # Importar
    import_service = ImportService()
    import_service.import_from_json(session, "test_export.json")
    
    # Verificar integridad
    assert todos_los_datos_iguales()
```

#### 7.2 Tests de Integración

1. ✅ Crear profesor en UI → verificar en BD
2. ✅ Exportar a JSON → verificar contenido
3. ✅ Importar JSON → verificar en BD
4. ✅ Sincronizar nube → verificar ciclo completo

#### 7.3 Tests Manuales

- [ ] Abrir aplicación
- [ ] Crear/editar/eliminar profesores
- [ ] Generar guardias
- [ ] Exportar datos
- [ ] Cerrar aplicación (sincronización)
- [ ] Abrir en otro dispositivo
- [ ] Verificar que los datos están sincronizados

---

## 📊 MÉTRICAS DE ÉXITO

### Antes de la Migración
- ❌ 2 fuentes de verdad (BD + JSON)
- ❌ Datos desincronizados
- ❌ Bugs de cuotas/recreos
- ❌ Código duplicado de lectura/escritura
- ❌ Confusión sobre qué datos son correctos

### Después de la Migración
- ✅ 1 única fuente de verdad (BD SQLite)
- ✅ Datos siempre consistentes
- ✅ JSON solo para exportar/importar/backup
- ✅ Código simplificado
- ✅ Claridad total sobre los datos

---

## 🚀 ORDEN DE EJECUCIÓN RECOMENDADO

### INMEDIATO (Hoy):
1. **FASE 6**: Ejecutar script de reparación urgente
   - Tiempo: 5 minutos
   - Prioridad: 🔴 CRÍTICA
   - Resultado: Profesores de tarde con cuotas correctas

### CORTO PLAZO (Esta semana):
2. **FASE 1**: Auditoría completa
   - Tiempo: 1-2 horas
   - Prioridad: 🟠 ALTA

3. **FASE 2**: Implementar servicios Export/Import
   - Tiempo: 2-3 horas
   - Prioridad: 🟠 ALTA

### MEDIO PLAZO (Próxima semana):
4. **FASE 3**: Refactorizar SyncManager
   - Tiempo: 2-3 horas
   - Prioridad: 🟡 MEDIA

5. **FASE 4**: Eliminar JSONDatabase
   - Tiempo: 1-2 horas
   - Prioridad: 🟡 MEDIA

6. **FASE 5**: Actualizar UI
   - Tiempo: 1-2 horas
   - Prioridad: 🟢 BAJA

7. **FASE 7**: Testing completo
   - Tiempo: 1-2 horas
   - Prioridad: 🟠 ALTA

---

## 💡 BENEFICIOS ESPERADOS

1. **Simplicidad**: Una única fuente de verdad
2. **Confiabilidad**: No más desincronización
3. **Mantenibilidad**: Código más limpio
4. **Debugging**: Más fácil encontrar problemas
5. **Performance**: No leer/escribir JSON constantemente
6. **Flexibilidad**: JSON cuando se necesite, no siempre

---

## 📚 DOCUMENTACIÓN ADICIONAL

- `ARQUITECTURA_BD_vs_JSON.md` - Comparación detallada
- `GUIA_EXPORT_IMPORT.md` - Manual de usuario
- `API_EXPORT_IMPORT.md` - Documentación técnica

---

**Autor**: GitHub Copilot  
**Fecha**: 1 de noviembre de 2025  
**Versión**: 1.0
