# Mejoras Pendientes — Guardias de Patio

> Documento de análisis técnico. Cada sección describe el problema, el diagnóstico de causa raíz y las opciones de solución valoradas.

---

## 1. Configuración SFTP/SMTP se pierde al actualizar la app

~~Pendiente de implementación~~ ✅ RESUELTO v5.31.11

### Descripción del problema

Cuando el usuario descarga un nuevo DMG, lo abre y arrastra la app a `/Applications`, la instalación anterior se reemplaza por completo. Al arrancar la versión nueva, la app muestra el wizard de configuración inicial (SFTP y SMTP) como si fuera la primera vez, obligando al usuario a volver a introducir credenciales que ya había configurado.

### Diagnóstico — causa raíz

El archivo `.env` (donde se persisten `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, `SMTP_*`) se guarda en la raíz del bundle de la aplicación:

```python
# src/presentation/dialogs/initial_config_dialog.py — método _update_env_file()
env_path = Path(__file__).parent.parent.parent.parent / ".env"
# → resuelve a: /Applications/Guardias de Patio.app/Contents/MacOS/.env
```

Al reemplazar el `.app` con la nueva versión, ese `.env` desaparece.

La detección de primera instalación en `main.py` (línea 121) llama a `InitialConfigDialog.is_configuration_needed()`, que simplemente comprueba si `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME` y `SFTP_PASSWORD` existen en el entorno (cargados desde `.env`). Si el archivo no existe → vuelve a mostrar el wizard.

```python
# src/presentation/dialogs/initial_config_dialog.py — línea 611
@staticmethod
def is_configuration_needed() -> bool:
    load_dotenv()
    sftp_complete = all([
        os.getenv("SFTP_HOST"),
        os.getenv("SFTP_PORT"),
        os.getenv("SFTP_USERNAME"),
        os.getenv("SFTP_PASSWORD"),
    ])
    return not sftp_complete
```

### Archivos involucrados

| Archivo | Relevancia |
|---------|------------|
| `src/presentation/dialogs/initial_config_dialog.py` | Wizard de config, `_update_env_file()`, `is_configuration_needed()` |
| `src/main.py` | Punto de entrada, llama a `is_configuration_needed()` |
| `src/core/paths.py` | `get_base_directory()` / `get_data_directory()` — rutas persistentes |

### Soluciones valoradas

#### Opción A — Mover el `.env` a la carpeta de datos del usuario (RECOMENDADA)

Guardar el `.env` en `~/Library/Application Support/GuardiasDePatio/` (misma ruta que las bases de datos), usando `get_base_directory()` de `core/paths.py`.

```python
# Cambio en _update_env_file():
from core.paths import get_base_directory
env_path = get_base_directory() / ".env"
```

```python
# Cambio en is_configuration_needed():
from core.paths import get_base_directory
load_dotenv(get_base_directory() / ".env")
```

**Ventajas:**
- Mínimo cambio de código (2 líneas modificadas)
- El `.env` sobrevive a cualquier actualización del DMG
- Coherente con la estrategia actual de persistencia (datos en Application Support)

**Inconvenientes:**
- En desarrollo (código fuente) el `.env` ya no estaría en la raíz del proyecto → habría que ajustar la lógica para que en modo desarrollo siga cargando desde la raíz (ya lo hace `python-dotenv` por defecto si se le pasa `dotenv_path=None`)

**Implementación:**
1. En `_update_env_file()`: cambiar `Path(__file__).parent × 4` por `get_base_directory() / ".env"`
2. En `is_configuration_needed()`: pasar la misma ruta a `load_dotenv(dotenv_path=...)`
3. En `main.py` o `app_initializer.py`: asegurar que al arrancar se carga el `.env` desde `get_base_directory()` antes de evaluar configuración
4. Migración automática (primera vez): si existe `.env` en bundle pero no en Application Support, copiarlo antes de continuar

#### Opción B — Archivo de marca separado (`config.lock`)

Crear un archivo `config.lock` en `get_base_directory()` que se genera tras la configuración exitosa. La detección de primera instalación comprueba este archivo en lugar del `.env`.

**Ventajas:** Desacopla "¿está configurado?" de "¿están las credenciales cargadas?"

**Inconvenientes:** No resuelve el problema real (las credenciales siguen en el bundle), solo evita mostrar el wizard si el `.env` ya existió en algún momento.

#### Opción C — Almacenar config en macOS Keychain

Guardar las credenciales SFTP/SMTP en el llavero del sistema usando `keyring`.

**Ventajas:** Más seguro (no credenciales en disco en texto plano)

**Inconvenientes:** Requiere `keyring` como dependencia, añade complejidad, y el wizard UI actual necesitaría refactorizarse para escribir/leer del keychain.

### Decisión recomendada

**Opción A**. Cambio mínimo, máximo impacto, sin nuevas dependencias. La migración automática garantiza que usuarios que ya tienen el `.env` en el bundle no pierdan su configuración al actualizar.

---

## 2. El algoritmo CP-SAT dispersa demasiado las guardias en el tiempo

~~Pendiente de implementación~~ ✅ RESUELTO v5.31.11

### Descripción del problema

El algoritmo encuentra la asignación óptima en cuanto a equidad de carga, pero distribuye las guardias de cada profesor a lo largo de todo el curso escolar en lugar de concentrarlas en períodos cortos y consecutivos.

**Ejemplo real (PDF adjunto — FERRERO BONET, CARLOS MANUEL, curso 2025/2026):**

| Mes | Guardias |
|-----|---------|
| Septiembre | 7 |
| Octubre | 0 |
| Noviembre | 7 |
| Diciembre | 4 |
| Enero | 4 |
| Febrero | 1 |
| Marzo | 7 |
| Abril | 0 |
| Mayo | 2 |
| Junio | 0 |

Las guardias aparecen en 7 meses distintos y hay "huecos" largos (octubre vacío, cuatro meses seguidos con pocas o cero guardias). El ideal sería períodos cortos y densos, por ejemplo todas las guardias del trimestre concentradas en 2-3 semanas consecutivas.

### Diagnóstico — causa raíz

El algoritmo tiene un término de consecutividad en la función objetivo, pero con un peso **muy bajo** (10) comparado con los términos de equidad (1.000.000 y 10.000):

```python
# src/services/asignador_guardias_cpsat.py — líneas 396-403
objetivo = (
    PESO_EQUIDAD        * max_dev +                    # 1_000_000
    PESO_EQUIDAD_SUMA   * sum(desviaciones) +           # 10_000
    PESO_CONSECUTIVIDAD * sum(penalizacion_consecutividad) +  # 10
    PESO_ZONA           * sum(penalizacion_zona)        # 3
)
model.Minimize(objetivo)
```

El término de consecutividad (peso 10) penaliza "cortes" entre días **calendáricos** consecutivos:

```python
# Si día D tiene guardia y día D+1 no (o viceversa) → penalización +1
```

Esto es demasiado granular: un hueco de un mes pesa igual que un hueco de un día. Con 60-70 profesores y 180 días lectivos, la penalización total de consecutividad es marginal frente a la escala del término de equidad, por lo que el solver la ignora efectivamente.

### Archivos involucrados

| Archivo | Relevancia |
|---------|------------|
| `src/services/asignador_guardias_cpsat.py` | Función objetivo, pesos, solver |
| `src/services/_asignador_cpsat_helpers.py` | `Slot`, elegibilidad, helpers |

### Soluciones valoradas

#### Opción A — Aumentar el peso de consecutividad (quick win)

Subir `PESO_CONSECUTIVIDAD` de 10 a un valor entre 500 y 2.000. Seguiría siendo una preferencia blanda (no rompe equidad) pero influiría más en la solución.

```python
PESO_EQUIDAD        = 1_000_000
PESO_EQUIDAD_SUMA   = 10_000
PESO_CONSECUTIVIDAD = 1_000   # antes: 10
PESO_ZONA           = 3
```

**Ventajas:** Cambio de una línea, sin nueva lógica.

**Inconvenientes:** La penalización sigue siendo por "día consecutivo", no por semana o quincena. Mejoraría la concentración de días adyacentes pero no necesariamente resolvería huecos grandes de semanas o meses.

**Estimación de mejora:** Moderada. Reduciría huecos de 1-3 días pero no los de semanas/meses.

#### Opción B — Penalización por semana en lugar de por día (RECOMENDADA)

Reemplazar la penalización de "corte entre días D y D+1" por una penalización de "semanas con presencia". Cada semana lectiva en que el profesor tiene ≥1 guardia cuenta como una "semana activa". Se penaliza el número de semanas activas (cuantas menos semanas con guardias, mejor).

```python
# Mapeo: fecha → semana_lectiva (índice ordinal)
dia_a_semana = {d: d.isocalendar().week for d in dias_unicos}

# Variable: tiene_guardia_semana[prof_id][semana]
tiene_guardia_semana = model.NewBoolVar(...)
model.AddMaxEquality(tiene_semana, [x[(prof_id, s_idx)] para slots de esa semana])

# Penalización = número de semanas distintas con ≥1 guardia
penalizacion_semanas = sum(tiene_guardia_semana[prof_id][semana] para todas las semanas)
```

**Función objetivo actualizada:**
```python
objetivo = (
    PESO_EQUIDAD       * max_dev +
    PESO_EQUIDAD_SUMA  * sum(desviaciones) +
    PESO_SEMANAS       * sum(penalizacion_semanas) +   # nuevo: 5_000
    PESO_ZONA          * sum(penalizacion_zona)
)
```

**Ventajas:**
- Ataca directamente el problema: menos semanas con guardias = más concentración temporal
- Peso de 5.000 es significativo pero no supera la equidad
- Los "huecos de meses" quedan penalizados con el mismo peso que los "huecos de días"

**Inconvenientes:**
- Añade O(profesores × semanas_lectivas) variables booleanas extra (~60 × 36 ≈ 2.160 vars)
- Puede incrementar ligeramente el tiempo de resolución (estimado: +5-15%)

#### Opción C — Restricción dura de "ventana temporal" (concentración forzada)

Añadir una restricción que limite las guardias de cada profesor a una ventana de N semanas consecutivas dentro de cada trimestre.

```python
# Hard constraint: todas las guardias del trimestre dentro de una ventana de W semanas
for trimestre in [t1, t2, t3]:
    dias_trimestre = [d for d in dias_lectivos if d in trimestre]
    semanas = sorted(set(semana(d) for d in dias_trimestre))
    
    # Variable: inicio_ventana[prof][trimestre] ∈ {0, ..., len(semanas)-W}
    inicio = model.NewIntVar(0, len(semanas) - W, ...)
    
    # Si el profesor tiene guardia fuera de la ventana → infactible
    for s_idx in slots_trimestre[prof]:
        semana_slot = semana_a_ordinal[slots[s_idx].fecha]
        model.Add(semana_slot >= inicio).OnlyEnforceIf(x[(prof, s_idx)])
        model.Add(semana_slot < inicio + W).OnlyEnforceIf(x[(prof, s_idx)])
```

**Ventajas:** Garantiza concentración (no es opcional).

**Inconvenientes:**
- Puede hacer el problema **infactible** para profesores con muchas ausencias o restricciones en el período concentrado
- Requiere que W sea configurable por el usuario
- Añade complejidad de modelado considerable

#### Opción D — Parámetro configurable en Ajustes

Exponer un control en la sección de Ajustes del Curso que permita al usuario elegir la estrategia de distribución temporal:

- **"Distribuida"** (actual): guardias repartidas a lo largo del curso
- **"Concentrada por semanas"**: penalización por número de semanas activas (Opción B)
- **"Forzar ventana de N semanas"**: restricción dura por trimestre (Opción C)

**Ventajas:** El usuario decide según sus necesidades pedagógicas.

**Inconvenientes:** Añade UI adicional y lógica condicional en el solver.

### Decisión recomendada

Implementar en dos fases:

1. **Fase 1 (quick win):** Opción A — subir `PESO_CONSECUTIVIDAD` a 1.000. Cambio de una línea, mejora inmediata, sin riesgo.

2. **Fase 2 (solución completa):** Opción B — añadir penalización por semanas activas con peso ~5.000. Resuelve el problema de raíz sin romper la equidad ni hacer el problema infactible.

La Opción D (configuración por el usuario) puede añadirse encima de la Fase 2 si se requiere más control.

---

*Documento generado el 23/04/2026. Pendiente de implementación.*
