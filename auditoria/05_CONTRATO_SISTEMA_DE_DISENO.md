---
tags:
  - gestion-centro
  - auditoria
  - ux
fecha_actualizacion: 2026-09-04
estado: en-revision
prioridad: 2-alta
tipo: referencia
---

# Contrato del sistema de diseño (borrador pendiente de validación)

> [!NOTE] Propósito
> Que la app se sienta profesional, sobria y hecha por una sola persona con criterio: pocos patrones, aplicados siempre igual. Este contrato es la fuente para `DESIGN.md` en la raíz del repo cuando se apruebe.

## 1. Principios

1. **Un patrón por problema.** Un solo tipo de tabla, un solo formulario, un solo diálogo de confirmación, un solo feedback por categoría.
2. **La acción primaria es única y está siempre en el mismo sitio** (arriba a la derecha de la cabecera de vista o al pie del panel de edición).
3. **El color significa, no decora.** Azul = acción/selección. Verde = éxito. Ámbar = atención. Rojo = destructivo/error. Gris = neutro. Nada más.
4. **Texto antes que icono, icono antes que emoji.** Los emojis no son UI.
5. **Nunca bloquear sin decir por qué.** Todo control deshabilitado muestra el motivo en texto y un enlace.
6. **Silencio por defecto.** Sin modales informativos; el éxito se comunica con un toast breve o un cambio de estado visible.
7. **Adaptable.** Funciona a 1366×768 y a 200 % de escala; nada fijo por debajo de esa referencia.

## 2. Tokens (fuente única: `src/presentation/theme/tokens.py`)

### Color

| Token | Valor | Uso |
| --- | --- | --- |
| `primary` | #0E5FA8 | Botón primario, selección, enlaces, foco (≥ 4,5:1 sobre blanco) |
| `primary-hover` | #0B4C86 | Hover primario |
| `primary-soft` | #E8F1FA | Fondo de fila seleccionada, badges informativos |
| `success` / `success-soft` | #1E7E34 / #E6F4EA | Estado correcto |
| `warning` / `warning-soft` | #8A5A00 / #FFF4DB | Atención |
| `danger` / `danger-soft` | #B42318 / #FDECEC | Destructivo, error |
| `neutral-900…100` | #1F2937 · #374151 · #6B7280 · #9CA3AF · #D1D5DB · #E5E7EB · #F3F4F6 · #F9FAFB | Texto, bordes, superficies |
| `sidebar-bg` / `sidebar-fg` | #1F2A37 / #E5E7EB | Navegación |
| `focus-ring` | #0E5FA8 2 px + halo #BFD7F2 | Foco visible en todo control |

Regla: **cero literales hex fuera de `tokens.py`**. El QSS se genera con `str.format` desde los tokens en un único fichero `app.qss.tpl`. Ratchet en `tests/audit/test_consistencia_visual_ratchet.py`.

### Tipografía

| Token | px | Uso |
| --- | ---: | --- |
| `font-family` | "Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu", sans-serif | Global |
| `text-xs` | 12 | Metadatos, celdas densas (mínimo absoluto) |
| `text-sm` | 13 | Cuerpo de tablas y formularios |
| `text-md` | 14 | Cuerpo general |
| `text-lg` | 16 | Subtítulos, títulos de panel |
| `text-xl` | 20 | Título de vista |
| Peso | 400 / 600 | Sólo dos pesos |

### Espaciado y forma

- Escala 4/8/12/16/24/32 px. Márgenes de vista 24 px; de panel 16 px; entre controles 8 px.
- Radio 6 px en todo (botones, inputs, tarjetas). Bordes 1 px `neutral-300`.
- Sombras: ninguna en superficies planas; una sola sombra suave para popovers/toast.
- Altura de controles: 32 px (inputs, botones), 36 px sólo el primario de vista.

### Iconografía

- Set único MDI monocromo (ya en `utils/icons.py`), 16 px en botones, 20 px en sidebar, color heredado del texto.
- Estados en tablas: punto de color 8 px + texto ("Cubierta", "Sin cubrir"), nunca emoji.

## 3. Componentes y contratos

### Cabecera de vista (`ViewHeader`)

- Título `text-xl`, subtítulo opcional `text-sm neutral-500`, acción primaria a la derecha, acciones secundarias en un menú "Más" si hay más de dos.
- La renderiza `ContentWrapper` con el título registrado: elimina los títulos ad hoc en cada formulario.

### Barra de estado de prerrequisitos (`PreflightBanner`)

- Aparece bajo la cabecera cuando falta algo: icono de aviso, texto "Para generar necesitas: fechas del curso, ≥1 zona" y enlaces. Desaparece cuando todo está OK.

### Panel (`Card`)

- Fondo blanco, borde `neutral-300`, radio 6, padding 16, título `text-lg`. Sin bordes de color: el color va en el contenido, no en el marco.

### Botón

| Variante | Uso | Estilo |
| --- | --- | --- |
| Primario | 1 por vista | fondo `primary`, texto blanco |
| Secundario | resto | fondo blanco, borde `neutral-300` |
| Texto | acciones terciarias | sin borde, texto `primary` |
| Peligro | destructivas | variante secundaria con texto `danger`; nunca relleno rojo salvo en el diálogo de confirmación |

Estados obligatorios: hover, focus (anillo), pressed, disabled (opacidad 0,5 + motivo en texto adyacente), loading (spinner 16 px + texto "Generando…").

### Campo de formulario (`FormField`)

- Label encima, `setBuddy`, ayuda debajo en `text-xs`, error debajo en `danger` con icono y foco en el primer error. Requerido con "·" en el label, no con asterisco rojo.

### Tabla (`DataTable`)

- `QTableView` + modelo; toolbar (buscar, filtros, acciones sobre selección), cabecera ordenable, filas 32 px, zebra sutil, selección con `primary-soft`, estado vacío y de carga integrados, paginación o carga incremental > 500 filas, `accessibleName` obligatorio.

### Feedback

| Tipo | Componente | Duración | Cuándo |
| --- | --- | --- | --- |
| Validación | inline bajo el campo | persistente | errores de campo |
| Éxito | toast inferior derecha con "Deshacer" opcional | 4 s | guardar, generar, sincronizar |
| Aviso | banner bajo cabecera | hasta resolver | prerrequisitos, sync fallida |
| Bloqueante | `QMessageBox` con botones explícitos | – | destructivo, pérdida de datos |
| Progreso | `ProgressDialog` (cancelable, cierre automático al terminar bien) | – | > 1 s |

### Resultado de generación (`ResultCard`)

Sustituye al terminal retro: tarjeta con 4 métricas (guardias, cobertura, equidad, tiempo), tabla por profesor (asignadas vs cuota, desviación con barra), lista de incidencias con acción "Ver profesor", botones "Ver calendario" (primario) y "Enviar emails" (secundario).

### Diálogo

- Título, cuerpo, botones a la derecha con el destructivo a la izquierda del grupo; foco inicial en la acción segura; Escape = cancelar. Sin `Sheet` en macOS para diálogos de progreso (evita bloqueos con hilos).

## 4. Navegación

- Orden de sidebar = orden del flujo: Inicio (estado) → Ajustes → Zonas → Profesores → Cálculo → Calendario → Ausencias → Reportes → Estadísticas → Importar/Exportar → Perfiles.
- Elemento activo: fondo `primary-soft` + borde izquierdo 3 px `primary` + `checked` accesible.
- Badges numéricos en sidebar para pendientes (ausencias sin cubrir, cambios sin sincronizar).
- Atajos: Ctrl+1…9 secciones, Ctrl+N nuevo, Ctrl+S guardar, Ctrl+F buscar, Ctrl+G generar, Escape cancelar/cerrar panel.

## 5. Ventanas y escalado

- Ventana principal: mínimo 1024×700, arranque maximizada, recuerda tamaño/posición por usuario.
- Diálogos: `sizeHint` desde layout; nunca `setFixedSize`; máximo 90 % del área disponible con scroll interno.
- `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` (ya aplicado) + fuentes en px lógicos.

## 6. Ruta de adopción (incremental, sin big-bang)

1. Congelar tokens nuevos y generador de `app.qss`; eliminar `light.qss`, `legacy_styles.py`, `ui_styles.py` y `get_complete_stylesheet` (lote VIS-001/002).
2. `ContentWrapper` renderiza `ViewHeader`; retirar títulos locales (VIS-006).
3. Sustituir estilos inline de botones por variantes (VIS-007) y emojis por iconos (VIS-004).
4. `ResultCard` para generación (VIS-005) junto con el fix del crash (CRW).
5. `DataTable` en Profesores como piloto, luego resto (ESC-001, UXA-008).
6. Ratchets a cero y snapshots por estado como gate.
