# Maintenance Guide

**Guardias de Patio** - Guía de Mantenimiento  
**Versión**: 3.0.2  
**Última actualización**: 12 de noviembre de 2025  
**Última auditoría**: 12 de noviembre de 2025 ✅ (FASE 8)

---

## 📋 Tabla de Contenidos

1. [Tareas de Mantenimiento Regular](#tareas-de-mantenimiento-regular)
2. [Gestión de Base de Datos](#gestión-de-base-de-datos)
3. [Limpieza de Archivos](#limpieza-de-archivos)
4. [Actualizaciones de Dependencias](#actualizaciones-de-dependencias)
5. [Monitoreo y Logs](#monitoreo-y-logs)
6. [Backups y Recuperación](#backups-y-recuperación)
7. [Optimización de Rendimiento](#optimización-de-rendimiento)
8. [Checklist de Mantenimiento](#checklist-de-mantenimiento)

---

## 🔄 Tareas de Mantenimiento Regular

### Diarias (Automáticas)

✅ **Logs rotativos** - Los logs se rotan automáticamente

```python
# Configuración en src/core/logging.py
handlers={
    "file": {
        "class": "logging.handlers.RotatingFileHandler",
        "maxBytes": 10485760,  # 10 MB
        "backupCount": 5,      # Mantener 5 archivos
    }
}
```

### Semanales (Manuales)

#### 1. Revisar Logs de Error

```bash
# Ver errores de la última semana
grep "ERROR" logs/app.log | tail -50

# Contar tipos de errores
grep "ERROR" logs/app.log | cut -d':' -f4 | sort | uniq -c | sort -rn
```

#### 2. Verificar Integridad de BD

```bash
# Ejecutar script de verificación
python scripts/maintenance/check_db_integrity.py
```

**Output esperado:**

```
✅ Base de datos: 142.5 KB
✅ Profesores: 45 registros
✅ Zonas: 8 registros
✅ Guardias: 1,234 registros
✅ Ausencias: 87 registros
✅ Configuraciones: 12 registros
✅ Sin registros huérfanos
✅ Índices optimizados
```

#### 3. Backup de Base de Datos

```bash
# Crear backup semanal
python scripts/maintenance/backup_database.py --weekly

# Verificar backup creado
ls -lh data/backups/
```

### Mensuales

#### 1. Limpieza de Logs Antiguos

```bash
# Eliminar logs de más de 30 días
find logs/ -name "*.log" -mtime +30 -delete

# Comprimir logs antiguos (opcional)
find logs/ -name "*.log" -mtime +7 -exec gzip {} \;
```

#### 2. Limpieza de Backups Antiguos

```bash
# Mantener solo últimos 6 backups mensuales
python scripts/maintenance/cleanup_old_backups.py --keep 6
```

#### 3. Actualizar Dependencias

```bash
# Revisar actualizaciones disponibles
pip list --outdated

# Actualizar dependencias de seguridad críticas
pip install --upgrade sqlalchemy cryptography

# Actualizar requirements.txt
pip freeze > requirements.txt

# Ejecutar tests
pytest

# Commit si todo funciona
git add requirements.txt
git commit -m "chore(deps): actualizar dependencias de seguridad"
git push
```

### Trimestrales

#### 1. Auditoría de Seguridad

```bash
# Auditar dependencias
pip install pip-audit
pip-audit

# Revisar política de seguridad
cat documentacion/SECURITY.md
```

#### 2. Optimización de Base de Datos

```bash
# Ejecutar VACUUM para recuperar espacio
python scripts/maintenance/optimize_database.py

# Reconstruir índices
python scripts/maintenance/rebuild_indexes.py
```

#### 3. Revisión de Documentación

- ✅ Verificar enlaces no rotos
- ✅ Actualizar versiones en documentos
- ✅ Revisar screenshots obsoletos
- ✅ Actualizar roadmap si aplica

### Anuales

#### 1. Limpieza de Datos Históricos

```bash
# Archivar guardias de años anteriores
python scripts/maintenance/archive_old_guardias.py --year 2023

# Comprimir archivos archivados
tar -czf data/archive_2023.tar.gz data/archive/2023/
```

#### 2. Actualización Mayor de Dependencias

```bash
# Revisar versiones mayores disponibles
pip list --outdated

# Crear rama para actualización
git checkout -b chore/major-deps-update

# Actualizar una por una
pip install --upgrade PyQt6
pytest  # Verificar

pip install --upgrade SQLAlchemy
pytest  # Verificar

# Actualizar requirements.txt y crear PR
```

---

## 🗄️ Gestión de Base de Datos

### Verificar Estado

```bash
# Información general
sqlite3 guardias_patio.db "SELECT 
    (SELECT COUNT(*) FROM profesores) as profesores,
    (SELECT COUNT(*) FROM zonas) as zonas,
    (SELECT COUNT(*) FROM guardias) as guardias,
    (SELECT COUNT(*) FROM ausencias) as ausencias;"
```

### Tamaño de BD

```bash
# Ver tamaño actual
ls -lh guardias_patio.db

# Ver tamaño por tabla
sqlite3 guardias_patio.db "SELECT 
    name,
    SUM(pgsize) as size_bytes
FROM dbstat
GROUP BY name
ORDER BY size_bytes DESC;"
```

### Limpiar Datos Obsoletos

```python
# scripts/maintenance/cleanup_old_data.py
from datetime import datetime, timedelta
from src.database.connection import SessionLocal
from src.models.guardias import Guardia

def limpiar_guardias_antiguas(dias: int = 365):
    """Elimina guardias de más de X días."""
    session = SessionLocal()
    fecha_limite = datetime.now() - timedelta(days=dias)
    
    count = session.query(Guardia).filter(
        Guardia.fecha < fecha_limite
    ).delete()
    
    session.commit()
    print(f"✅ Eliminadas {count} guardias antiguas")
    session.close()

if __name__ == "__main__":
    limpiar_guardias_antiguas(dias=730)  # 2 años
```

### Optimización

```bash
# VACUUM para recuperar espacio
sqlite3 guardias_patio.db "VACUUM;"

# ANALYZE para optimizar queries
sqlite3 guardias_patio.db "ANALYZE;"

# Verificar mejora
ls -lh guardias_patio.db
```

### Migraciones

```bash
# Revisar estado de migraciones
alembic current

# Ver historial
alembic history

# Crear nueva migración
alembic revision --autogenerate -m "descripción_del_cambio"

# Aplicar migración
alembic upgrade head

# Revertir última migración (si falla)
alembic downgrade -1
```

---

## 🧹 Limpieza de Archivos

### Estructura de Carpetas a Limpiar

```
guardias_patio/
├── logs/                    # Limpiar logs > 30 días
├── data/
│   ├── backups/            # Mantener últimos 6 backups
│   ├── exports/            # Limpiar > 7 días
│   └── temp/               # Limpiar todo
├── build/                  # Eliminar después de compilación
├── dist/                   # Eliminar después de distribución
└── htmlcov/               # Regenerar en cada test con coverage
```

### Script de Limpieza Automática

```bash
# scripts/maintenance/cleanup.sh
#!/bin/bash

echo "🧹 Iniciando limpieza..."

# Eliminar archivos temporales
rm -rf data/temp/*
echo "✅ Temporales eliminados"

# Limpiar logs antiguos
find logs/ -name "*.log" -mtime +30 -delete
echo "✅ Logs antiguos eliminados"

# Limpiar exports viejos
find data/exports/ -name "*.pdf" -mtime +7 -delete
find data/exports/ -name "*.ics" -mtime +7 -delete
echo "✅ Exports antiguos eliminados"

# Limpiar builds
rm -rf build/ dist/
echo "✅ Builds eliminados"

# Limpiar cache Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
echo "✅ Cache Python eliminado"

# Limpiar .DS_Store (macOS)
find . -name ".DS_Store" -delete
echo "✅ .DS_Store eliminados"

echo "✅ Limpieza completada"
```

**Ejecutar:**

```bash
chmod +x scripts/maintenance/cleanup.sh
./scripts/maintenance/cleanup.sh
```

### Archivos Seguros para Eliminar

✅ **Siempre seguro:**
- `__pycache__/`
- `*.pyc`
- `.DS_Store`
- `build/` y `dist/` (después de distribuir)
- `htmlcov/` (regenerable con `pytest --cov`)
- `logs/*.log` > 30 días
- `data/temp/*`
- `data/exports/*` > 7 días

⚠️ **Revisar antes de eliminar:**
- `data/backups/*` (mantener últimos 6)
- `guardias_patio.db.backup_*`

❌ **NUNCA eliminar:**
- `guardias_patio.db`
- `requirements.txt`
- `alembic/versions/*`
- `src/**/*.py`

---

## 📦 Actualizaciones de Dependencias

### Verificar Versiones Actuales

```bash
# Ver versión actual de cada dependencia
pip list

# Ver solo las principales
pip list | grep -E 'PyQt6|SQLAlchemy|pydantic|pytest'
```

### Proceso de Actualización Seguro

#### 1. Crear Entorno de Test

```bash
# Crear nuevo venv para testing
python3.11 -m venv venv_test
source venv_test/bin/activate

# Instalar dependencias actuales
pip install -r requirements.txt
```

#### 2. Actualizar y Testear

```bash
# Actualizar una dependencia
pip install --upgrade pydantic

# Ejecutar tests completos
pytest

# Si pasa, actualizar requirements
pip freeze > requirements_new.txt
```

#### 3. Comparar Cambios

```bash
# Ver diferencias
diff requirements.txt requirements_new.txt

# Si todo OK, reemplazar
mv requirements_new.txt requirements.txt
```

#### 4. Aplicar en Entorno Principal

```bash
# Volver a venv principal
deactivate
source venv/bin/activate

# Instalar actualizaciones
pip install -r requirements.txt

# Ejecutar tests una vez más
pytest

# Commit
git add requirements.txt
git commit -m "chore(deps): actualizar pydantic a 2.9.0"
git push
```

### Matriz de Compatibilidad

| Python | PyQt6 | SQLAlchemy | Pydantic | Estado |
|--------|-------|------------|----------|--------|
| 3.11.x | 6.7.x | 2.0.x | 2.8.x | ✅ Probado |
| 3.12.x | 6.7.x | 2.0.x | 2.8.x | ⚠️ No probado |
| 3.10.x | 6.6.x | 2.0.x | 2.7.x | ❌ No soportado |

---

## 📊 Monitoreo y Logs

### Ubicación de Logs

```
logs/
├── app.log              # Log principal rotativo
├── app.log.1            # Backup 1
├── app.log.2            # Backup 2
├── app.log.3            # Backup 3
├── app.log.4            # Backup 4
└── app.log.5            # Backup 5 (más antiguo)
```

### Niveles de Log

```python
# En producción: INFO
# En desarrollo: DEBUG

import logging
logger = logging.getLogger(__name__)

logger.debug("Detalle técnico")     # Solo en DEBUG
logger.info("Evento normal")        # INFO y superior
logger.warning("Advertencia")       # WARNING y superior
logger.error("Error recuperable")   # ERROR y superior
logger.critical("Error crítico")    # CRITICAL siempre
```

### Análisis de Logs

```bash
# Ver últimos errores
tail -f logs/app.log | grep ERROR

# Contar errores por tipo
grep ERROR logs/app.log | cut -d':' -f4 | sort | uniq -c | sort -rn

# Ver errores de hoy
grep "$(date +%Y-%m-%d)" logs/app.log | grep ERROR

# Buscar patrón específico
grep "ValidationError" logs/app.log
```

### Alertas Automáticas (opcional)

```python
# scripts/maintenance/check_errors.py
import subprocess
from datetime import datetime

def contar_errores_hoy():
    """Cuenta errores del día actual."""
    fecha = datetime.now().strftime("%Y-%m-%d")
    cmd = f"grep '{fecha}' logs/app.log | grep ERROR | wc -l"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return int(result.stdout.strip())

if __name__ == "__main__":
    errores = contar_errores_hoy()
    if errores > 10:
        print(f"⚠️  ALERTA: {errores} errores hoy")
        # Aquí podrías enviar email o notificación
    else:
        print(f"✅ {errores} errores hoy (normal)")
```

---

## 💾 Backups y Recuperación

### Estrategia de Backup

#### Backups Automáticos

```python
# scripts/maintenance/backup_database.py
from datetime import datetime
from pathlib import Path
import shutil

def crear_backup(tipo: str = "manual"):
    """Crea backup de la base de datos."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    origen = Path("guardias_patio.db")
    destino = Path(f"data/backups/backup_{tipo}_{timestamp}.db")
    
    destino.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(origen, destino)
    
    print(f"✅ Backup creado: {destino}")
    return destino

if __name__ == "__main__":
    import sys
    tipo = sys.argv[1] if len(sys.argv) > 1 else "manual"
    crear_backup(tipo)
```

**Ejecutar:**

```bash
# Backup manual
python scripts/maintenance/backup_database.py manual

# Backup semanal
python scripts/maintenance/backup_database.py weekly

# Backup mensual
python scripts/maintenance/backup_database.py monthly
```

#### Calendario de Backups

| Frecuencia | Retención | Script |
|------------|-----------|--------|
| **Manual** | Indefinido | Antes de cambios críticos |
| **Diario** | 7 días | Automatizado (opcional) |
| **Semanal** | 4 semanas | Domingo a las 23:00 |
| **Mensual** | 12 meses | Día 1 de mes a las 00:00 |
| **Anual** | 5 años | 31 diciembre a las 23:59 |

### Recuperación de Backup

```bash
# Listar backups disponibles
ls -lht data/backups/

# Restaurar backup específico
cp data/backups/backup_weekly_20251108_230000.db guardias_patio.db

# Verificar integridad después de restaurar
sqlite3 guardias_patio.db "PRAGMA integrity_check;"

# Si integrity_check = "ok", ejecutar app
python src/main.py
```

### Backup Remoto (opcional)

```bash
# Subir a almacenamiento remoto (ejemplo con rsync)
rsync -avz data/backups/ usuario@servidor:/backups/guardias_patio/

# O usar servicios cloud (OneDrive, Google Drive, Dropbox)
```

---

## ⚡ Optimización de Rendimiento

### Identificar Cuellos de Botella

```bash
# Ejecutar con profiling
python -m cProfile -o profile.stats src/main.py

# Analizar resultados
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### Optimizaciones Comunes

#### 1. Índices de Base de Datos

```sql
-- Ver índices existentes
SELECT name, tbl_name FROM sqlite_master WHERE type='index';

-- Crear índice para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_guardias_fecha ON guardias(fecha);
CREATE INDEX IF NOT EXISTS idx_guardias_profesor ON guardias(profesor_id);
```

#### 2. Cache de Queries Frecuentes

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def obtener_profesores_activos():
    """Cache de profesores activos."""
    # Query costosa
    pass
```

#### 3. Lazy Loading en UI

```python
# Cargar datos bajo demanda en lugar de todo al inicio
class VistaCalendario:
    def cargar_mes(self, mes: int, año: int):
        """Carga solo guardias del mes solicitado."""
        pass
```

### Métricas de Rendimiento

**Objetivos:**
- ✅ Inicio de aplicación: < 2 segundos
- ✅ Generación de guardias: < 5 segundos (100 guardias)
- ✅ Carga de calendario: < 1 segundo (mes completo)
- ✅ Exportación PDF: < 3 segundos
- ✅ Guardado de datos: < 500ms

**Medir:**

```python
import time

inicio = time.time()
# Operación a medir
fin = time.time()
print(f"Tiempo: {fin - inicio:.2f}s")
```

---

## ✅ Checklist de Mantenimiento

### Semanal

- [ ] Revisar logs de error (`grep ERROR logs/app.log`)
- [ ] Verificar integridad de BD (`check_db_integrity.py`)
- [ ] Crear backup semanal (`backup_database.py --weekly`)
- [ ] Revisar issues abiertos en GitHub

### Mensual

- [ ] Limpiar logs > 30 días (`find logs/ -mtime +30 -delete`)
- [ ] Limpiar backups antiguos (`cleanup_old_backups.py`)
- [ ] Actualizar dependencias de seguridad (`pip-audit`)
- [ ] Ejecutar tests completos (`pytest --cov`)
- [ ] Revisar métricas de rendimiento

### Trimestral

- [ ] Auditoría de seguridad completa (`pip-audit`)
- [ ] Optimizar base de datos (`VACUUM`, `ANALYZE`)
- [ ] Reconstruir índices (`rebuild_indexes.py`)
- [ ] Revisar y actualizar documentación
- [ ] Verificar enlaces no rotos en docs

### Anual

- [ ] Archivar datos históricos (> 2 años)
- [ ] Actualización mayor de dependencias
- [ ] Revisión completa de código (deuda técnica)
- [ ] Actualizar roadmap para próximo año
- [ ] Backup anual a almacenamiento remoto

---

## 📚 Scripts de Mantenimiento

Todos los scripts están en `scripts/maintenance/`:

```
scripts/maintenance/
├── backup_database.py          # Crear backups de BD
├── check_db_integrity.py       # Verificar integridad
├── cleanup.sh                  # Limpieza general
├── cleanup_old_backups.py      # Limpiar backups antiguos
├── cleanup_old_data.py         # Limpiar datos obsoletos
├── optimize_database.py        # VACUUM y ANALYZE
├── rebuild_indexes.py          # Reconstruir índices
├── archive_old_guardias.py     # Archivar guardias antiguas
└── check_errors.py             # Revisar errores en logs
```

**Documentación completa**: Ver README en cada script

---

## 📞 Contacto

Para dudas sobre mantenimiento:

**Email**: cferrerobonet@gmail.com  
**GitHub Issues**: https://github.com/cferrerobonet/guardias_patio/issues

---

**Última actualización**: 12 de noviembre de 2025  
**Última auditoría (FASE 8)**: 12 de noviembre de 2025 ✅  
**Próxima revisión**: 12 de febrero de 2026
