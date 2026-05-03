# Diseño: Módulo Ausencias/Sustituciones (v2)

**Estado:** Propuesta aprobada — pendiente de implementación  
**Fecha:** 2026-05-03  
**Versión objetivo:** próxima minor tras aprobación

---

## Contexto y motivación

El módulo actual expone dos ítems de menú separados ("Ausencias" y "Sustituciones") para un flujo que el usuario vive como uno solo: *un profesor falta → alguien le cubre*. Esto genera fricción innecesaria: hay que navegar a dos pantallas distintas para completar una única tarea operativa.

Además, el concepto de "ausencia" como entidad persistente aporta poco valor real: lo que importa es la sustitución resultante. Y al conservar ausencias indefinidamente en BD aunque se regeneren las guardias, se acumulan datos huérfanos sin sentido.

**Objetivo:** unificar ambos ítems en uno solo, centrar la UX en las sustituciones, y limpiar ausencias automáticamente al regenerar el calendario.

---

## Cambios en la navegación

### Antes

```
PERSONAL
├─ Ausencias        [section_id="ausencias",    icon="hospital-box"]
└─ Sustituciones    [section_id="sustituciones", icon="swap-horizontal"]
```

### Después

```
PERSONAL
└─ Ausencias/Sustituciones    [section_id="ausencias_sustituciones", icon="account-switch"]
                               badge: nº guardias con es_sustitucion=False donde profesor está ausente
```

El badge muestra el número de guardias sin sustituto asignado del calendario actual. Desaparece cuando todas están cubiertas o no hay ausencias activas.

---

## Layout de pantalla

```
┌─────────────────────────────────────────────────────────────────────┐
│  ╔═══════════════════════════════════════════════════════════════╗  │
│  ║  REGISTRAR AUSENCIA  [▲ colapsar]                            ║  │
│  ║                                                              ║  │
│  ║  Profesor ausente: [▼ Apellidos, Nombre    ]                 ║  │
│  ║  Desde: [ 05/05/2026 📅 ]   Hasta: [ 05/05/2026 📅 ]        ║  │
│  ║                                                              ║  │
│  ║                          [ Buscar guardias afectadas → ]    ║  │
│  ╚═══════════════════════════════════════════════════════════════╝  │
│                                                                     │
│  GUARDIAS A CUBRIR                           [ Auto-asignar todo ]  │
│  ┌──────┬──────────┬─────────┬───────┬──────────┬──────────┬─────┐ │
│  │Fecha │ Día      │ Turno   │Recreo │ Zona     │ Sustituto│  ●  │ │
│  ├──────┼──────────┼─────────┼───────┼──────────┼──────────┼─────┤ │
│  │05/05 │ Martes   │ Mañana  │   2   │ Patio    │[▼ combo ]│ 🔴  │ │
│  │05/05 │ Martes   │ Mañana  │   3   │ Pasillos │ García, A│ 🟢  │ │
│  │06/05 │ Miércoles│ Tarde   │   1   │ Entrada  │[▼ combo ]│ 🔴  │ │
│  └──────┴──────────┴─────────┴───────┴──────────┴──────────┴─────┘ │
│                                          [ Guardar ]  [ Cancelar ]  │
│                                                                     │
│  ─────────────────────────────────────────────────────────────────  │
│  HISTORIAL DE SUSTITUCIONES (calendario actual)   [▼ expandir]      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Panel superior: Registrar ausencia

Panel colapsable (`QGroupBox` con `setCheckable(False)` + botón colapso manual). Por defecto expandido si no hay sustituciones en curso; colapsado si ya hay guardias en la tabla.

| Campo | Widget | Obligatorio | Comportamiento |
|-------|--------|-------------|----------------|
| Profesor ausente | `QComboBox` | Sí | Orden alfabético (Apellidos, Nombre). Incluye solo profesores activos. |
| Fecha inicio | `QDateEdit` | Sí | Default: hoy. Calendar popup. |
| Fecha fin | `QDateEdit` | Sí | Default: hoy. Calendar popup. Validar ≥ fecha inicio al cambiar. |
| [Buscar] | `QPushButton` | — | Deshabilitado hasta que hay profesor y fechas válidas. Al pulsar: llama a `GestorAusencias.obtener_guardias_afectadas_por_periodo()` y rellena la tabla central. |

> Sin campo "Motivo", sin campo "Documento adjunto", sin campo "Tipo". Todo eliminado por aportar complejidad sin valor operativo en el uso diario.

**Validaciones en tiempo real:**
- Si fecha fin < fecha inicio: borde rojo en `QDateEdit` de fecha fin, botón Buscar deshabilitado.
- Si el profesor no tiene guardias en el período: mensaje inline bajo la tabla ("Este profesor no tiene guardias en el período seleccionado.").

---

## Tabla central: Guardias a cubrir

`QTableWidget` con 8 columnas. Muestra las guardias del profesor ausente en el período buscado. Persiste en pantalla hasta que el usuario pulsa Cancelar o hace una nueva búsqueda.

### Columnas

| # | Columna | Tipo | `QTableWidget` |
|---|---------|------|----------------|
| 0 | Fecha | `dd/MM` | `QTableWidgetItem`, ordenable |
| 1 | Día | texto | `QTableWidgetItem` |
| 2 | Turno | texto | `QTableWidgetItem` |
| 3 | Recreo | número | `QTableWidgetItem` |
| 4 | Zona | texto | `QTableWidgetItem` |
| 5 | Prof. ausente | texto | `QTableWidgetItem`, flags sin edición |
| 6 | Sustituto | `QComboBox` via `setCellWidget` | ver detalle abajo |
| 7 | Estado | `QLabel` via `setCellWidget` | "🔴" / "🟢" |

Guardar en cada fila el `guardia_id` como `UserRole` en la columna 0: `item.setData(Qt.ItemDataRole.UserRole, guardia.id)`.

### Combo "Sustituto" (columna 6)

Al construir cada fila, rellenar el combo con:

```python
# Llamada de servicio existente:
disponibles = GestorAusencias.obtener_profesores_disponibles(
    session, fecha=guardia.fecha, turno=guardia.turno,
    recreo_id=guardia.recreo, excluir_profesor_id=guardia.profesor_id
)
```

- Primera opción: `("— Sin asignar —", None)` — almacenar el `profesor_id` como `itemData`.
- Ordenar por menor carga de guardias ese día (el servicio ya lo hace).
- Si `guardia.es_sustitucion == True`, preseleccionar `guardia.profesor_id` y mostrar 🟢.
- Señal `currentIndexChanged` → actualizar icono de la columna 7.

### Botón "Auto-asignar todo"

```python
# Reusa el servicio existente en src/services/gestor_ausencias.py:
resultados = GestorAusencias.reasignar_guardias_automaticamente(session, guardias_pendientes)
# resultados = {"reasignadas": int, "fallidas": int, "detalles": List[Dict]}
```

- Actualiza combos de las filas afectadas sin tocar las ya en 🟢.
- Muestra `QMessageBox.information`: *"X guardias asignadas automáticamente. Y sin disponible."*

### Botones inferiores

| Botón | Estilo | Acción |
|-------|--------|--------|
| Guardar | `success` | Para cada fila con sustituto seleccionado: llama `GestorAusencias.reasignar_guardia(session, guardia_id, nuevo_profesor_id)`. Registra en `GuardiaAuditLog` acción `"SUSTITUIDA"`. Actualiza badge. Toast. |
| Cancelar | `secondary` | Limpia `QTableWidget`. Resetea combos. No toca BD. |

**`reasignar_guardia` ya existente** (`src/services/gestor_ausencias.py`):
- Pone `guardia.es_sustitucion = True`
- Pone `guardia.profesor_sustituido_id = profesor_anterior_id`
- Crea entrada en `GuardiaAuditLog` con `accion="SUSTITUIDA"` y `detalle={"profesor_anterior": nombre, "origen": "ausencia"}`

---

## Panel inferior: Historial de sustituciones

`QGroupBox` colapsable por defecto. Query base:

```python
session.query(Guardia).filter(Guardia.es_sustitucion == True).all()
```

### Columnas

| Columna | Campo ORM |
|---------|-----------|
| Fecha | `guardia.fecha` |
| Turno | `guardia.turno` |
| Recreo | `guardia.recreo` |
| Zona | `guardia.zona.nombre` (join) |
| Profesor original | `guardia.profesor_sustituido.nombre_completo` (via `profesor_sustituido_id`) |
| Profesor sustituto | `guardia.profesor.nombre_completo` |

### Filtros

- Rango de fechas: `QDateEdit` inicio + fin, ambos opcionales → `Guardia.fecha.between(desde, hasta)`.
- Combo "Profesor original": filtra por `Guardia.profesor_sustituido_id`.

### Botón "Limpiar historial"

```python
session.query(Guardia).filter(Guardia.es_sustitucion == True).update(
    {"es_sustitucion": False, "profesor_sustituido_id": None}
)
session.commit()
```

Requiere `QMessageBox.warning` de confirmación antes de ejecutar.

---

## Comportamiento al regenerar el calendario

**Archivo:** `src/services/assignment/assignment_executor.py`  
**Método:** `guardar_guardias` (línea ~187)

Añadir **antes** de `self.session.query(Guardia).delete()`:

```python
from infrastructure.database.models import Ausencia  # import ya disponible en el módulo
self.session.query(Ausencia).delete()
```

Orden de borrado final:
```python
self.session.query(Ausencia).delete()   # NUEVO
self.session.query(Guardia).delete()    # ya existía
```

Después del `session.flush()`, la pantalla de Ausencias/Sustituciones queda vacía automáticamente porque no hay filas que mostrar. El badge vuelve a 0.

El aviso al usuario lo muestra la pantalla de generación (`AsignacionCalculoForm`) con el mecanismo `mostrar_exito()` ya existente en `BaseForm`.

---

## Estructura del nuevo widget

**Archivo nuevo:** `src/presentation/widgets/ausencias_sustituciones.py`  
**Clase:** `AusenciasSustitucionesWidget(BaseForm)`

```python
class AusenciasSustitucionesWidget(BaseForm):
    sustitucion_guardada = pyqtSignal()   # para actualizar badge en sidebar

    def __init__(self, session_or_factory):
        super().__init__()
        # patrón polimórfico obligatorio del proyecto:
        from infrastructure.repositories.repository_factory import RepositoryFactory
        self.session = (
            session_or_factory.session
            if isinstance(session_or_factory, RepositoryFactory)
            else session_or_factory
        )
        self._guardias_en_tabla: list[dict] = []   # cache fila → guardia_id + estado
        self.setup_ui()
        self.cargar_profesores()
        self.cargar_historial()

    def setup_ui(self): ...
    def cargar_profesores(self): ...        # puebla combo profesor ausente
    def buscar_guardias(self): ...          # llama obtener_guardias_afectadas_por_periodo
    def _rellenar_tabla(self, guardias): ...
    def _combo_sustituto_para_fila(self, guardia) -> QComboBox: ...
    def auto_asignar(self): ...             # llama reasignar_guardias_automaticamente
    def guardar(self): ...                  # llama reasignar_guardia por cada fila modificada
    def cancelar(self): ...
    def cargar_historial(self): ...         # query es_sustitucion=True
    def limpiar_historial(self): ...        # update + confirm dialog
    def _actualizar_badge(self): ...        # emite sustitucion_guardada
```

Hereda de `BaseForm` (`src/presentation/forms/base_form.py`) para usar:
- `self.manejar_excepcion(e)` en bloques `except`
- `self.mostrar_exito(msg)` / `self.mostrar_advertencia(msg)`

---

## Cambios en archivos existentes

### `src/presentation/components/ccleaner_sidebar.py` — líneas 200–205

```python
# ANTES:
self.add_menu_item(menu_layout, "ausencias", "Ausencias", "ausencias", "hospital-box")
self.add_menu_item(menu_layout, "sustituciones", "Sustituciones", "sustituciones", "swap-horizontal")

# DESPUÉS:
self.add_menu_item(
    menu_layout, "ausencias_sustituciones",
    "Ausencias/Sustituciones", "ausencias_sustituciones", "account-switch"
)
```

El badge se implementa añadiendo un `QLabel` superpuesto al botón (ver patrón en otros proyectos PyQt6) o sobreescribiendo el texto con `btn.setText(f" Ausencias/Sustituciones  ({n})")` mientras `n > 0`.

### `src/presentation/ccleaner_main_window.py` — líneas 37–38 y 155–158

```python
# ANTES (imports):
from presentation.widgets import GestionarAusenciasForm, GestorSustituciones, ...

# DESPUÉS (imports):
from presentation.widgets import AusenciasSustitucionesWidget, ...

# ANTES (_setup_views):
self._register("ausencias",      "Gestión de Ausencias",      lambda: GestionarAusenciasForm(session))
self._register("sustituciones",  "Gestión de Sustituciones",  lambda: GestorSustituciones(session))

# DESPUÉS:
self._register(
    "ausencias_sustituciones",
    "Ausencias / Sustituciones",
    lambda: AusenciasSustitucionesWidget(session)
)
```

### `src/presentation/widgets/__init__.py`

```python
# Añadir:
from .ausencias_sustituciones import AusenciasSustitucionesWidget
# Eliminar (o mantener por compatibilidad hasta borrar los archivos):
# from .gestionar_ausencias import GestionarAusenciasForm
# from .gestor_sustituciones import GestorSustituciones
```

---

## Servicios existentes a reutilizar (no reimplementar)

| Servicio | Archivo | Método |
|----------|---------|--------|
| Obtener guardias en período | `src/services/gestor_ausencias.py` | `obtener_guardias_afectadas_por_periodo(session, profesor_id, fecha_inicio, fecha_fin)` |
| Profesores disponibles para una franja | `src/services/gestor_ausencias.py` | `obtener_profesores_disponibles(session, fecha, turno, recreo_id, excluir_profesor_id)` |
| Reasignar una guardia | `src/services/gestor_ausencias.py` | `reasignar_guardia(session, guardia_id, nuevo_profesor_id)` → sets `es_sustitucion=True`, `profesor_sustituido_id`, crea `GuardiaAuditLog` |
| Reasignar múltiples automáticamente | `src/services/gestor_ausencias.py` | `reasignar_guardias_automaticamente(session, guardias)` → devuelve `{"reasignadas": int, "fallidas": int, "detalles": [...]}` |

---

## Decisiones de simplificación

| Eliminado | Justificación |
|-----------|---------------|
| Ítem "Ausencias" (independiente) | Unificado |
| Ítem "Sustituciones" (independiente) | Unificado |
| Gestión CRUD de ausencias | La ausencia es solo el disparador para encontrar guardias |
| Estado activa/inactiva en ausencias | Irrelevante en el nuevo modelo |
| Campo Motivo / Documento adjunto | Raramente utilizado; añade ruido al formulario |
| Campo Tipo de ausencia | Solo útil para estadísticas futuras |
| `dialogo_reasignacion.py` | La asignación ocurre inline en la tabla central |
| Panel "Preview de guardias afectadas" | La tabla principal ya cumple ese rol |

---

## Orden de implementación recomendado

1. `src/services/assignment/assignment_executor.py` — añadir borrado de ausencias (2 líneas).
2. `src/presentation/widgets/ausencias_sustituciones.py` — crear widget nuevo completo.
3. `src/presentation/widgets/__init__.py` — actualizar exportación.
4. `src/presentation/ccleaner_main_window.py` — cambiar imports y `_register`.
5. `src/presentation/components/ccleaner_sidebar.py` — sustituir dos `add_menu_item` por uno.
6. Tests: verificar que `buscar_guardias`, `guardar` y `limpiar_historial` funcionan con BD real.
7. Borrar `gestionar_ausencias.py` y `gestor_sustituciones.py` (y `dialogo_reasignacion.py` si queda sin usos).
