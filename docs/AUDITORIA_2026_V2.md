# Auditoría Técnica y Funcional — Guardias de Patio v2.0
**Fecha:** 21 de abril de 2026  
**Versión auditada:** 5.24.0  
**Auditor:** GitHub Copilot (Claude Sonnet 4.6)

---

## Índice

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Inconsistencias de patrones UX/UI](#2-inconsistencias-de-patrones-uxui)
3. [UX/UI — Lo que duele y lo que hay que hacer](#3-uxui--lo-que-duele-y-lo-que-hay-que-hacer)
4. [Funcionalidades — Qué cambiar, qué quitar, qué añadir](#4-funcionalidades--qué-cambiar-qué-quitar-qué-añadir)
5. [Rendimiento](#5-rendimiento)
6. [Detección de bugs y observabilidad](#6-detección-de-bugs-y-observabilidad)
7. [Escalabilidad y compatibilidad futura](#7-escalabilidad-y-compatibilidad-futura)
7. [Deuda técnica residual](#7-deuda-técnica-residual)
8. [Roadmap priorizado](#8-roadmap-priorizado)

---

## 1. Resumen ejecutivo

La app tiene una base técnica sólida (Clean Architecture, CP-SAT, multi-curso, sync SFTP) y funciona. El problema real es que **visualmente parece una app de 2018** en un mundo donde los usuarios comparan con Notion, Linear o cualquier app moderna. Hay un gap enorme entre la complejidad del backend y la calidad percibida de la UI.

Lo más urgente no es código: es el **primer impacto visual** y la **fluidez del flujo de trabajo diario** del usuario. Un director de colegio que usa esto cada mañana debería sentir que la app es suya, rápida y clara.

**Lo mejor que tiene**: el motor CP-SAT con OR-Tools es una ventaja competitiva real. Nada en el mercado educativo español ofrece optimización matemática garantizada para guardias.  
**Lo peor que tiene**: el login abre en pantalla completa con un fondo blanco plano y una interfaz que podría ser una app de Python de 2014.

---

## 2. Inconsistencias de patrones UX/UI

Esta sección documenta inconsistencias **verificadas en el código fuente** (no teóricas). Son situaciones en las que el mismo tipo de elemento tiene comportamiento visual o semántico diferente según en qué pantalla estés. La falta de uniformidad obliga al usuario a re-aprender la interfaz en cada sección y da sensación de que la app fue construida a trozos por personas diferentes.

---

### ~~INCONS-01 — Botones de eliminar: tres formas de hacer lo mismo~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** `delete_user_dialog.py`, `perfiles_usuario_form.py`, `gestion_cursos_widget.py`, `zona_form.py`, `profesor_form.py`, `gestionar_ausencias.py`

Hay tres mecanismos distintos para estilizar un botón de "Eliminar" rojo:

| Mecanismo | Archivos | Resultado visual |
|---|---|---|
| `setProperty("danger", "true")` | `zona_form`, `profesor_form`, `gestionar_ausencias` | Rojo del tema global (`#DC3545`) — correcto |
| `setStyleSheet("background-color: #c0392b...")` inline | `delete_user_dialog` | Rojo diferente al del tema (`#c0392b` ≠ `#DC3545`) — inconsistente |
| `setStyleSheet("background-color: #e74c3c...")` inline | `perfiles_usuario_form`, `gestion_cursos_widget` | Tercer rojo distinto (`#e74c3c`) — inconsistente |

El resultado es que los botones de eliminar tienen **tres tonos de rojo diferentes** según la pantalla. El del `delete_user_dialog` además ignora el sistema de temas: si el tema cambia, ese botón no se actualiza.

**Corrección:**
Eliminar los `setStyleSheet()` inline en todos los botones de eliminar y usar exclusivamente `setProperty("danger", "true")` seguido de `style().polish(self)`.

```python
# Patrón correcto (único permitido para botones de eliminación):
self.delete_btn = QPushButton("Eliminar")
self.delete_btn.setIcon(icon_for_button("delete"))
self.delete_btn.setProperty("danger", "true")

# Patrón INCORRECTO que hay que eliminar:
delete_btn.setStyleSheet("""
    QPushButton {
        background-color: #c0392b;  # Rojo hardcodeado fuera del tema
        ...
    }
""")
```

---

### ~~INCONS-02 — El botón "Cancelar" tiene color verde, gris o sin color según el formulario~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** `profesor_form.py`, `zona_form.py`, `perfiles_usuario_form.py`, `dialogo_editar_perfil.py`, `dialogo_crear_perfil.py`

El botón "Cancelar" debería comunicar siempre la misma semántica: "acción neutra, volver atrás sin guardar". Pero:

| Archivo | Estilo del botón "Cancelar" | Color resultante |
|---|---|---|
| `profesor_form.py` | `setProperty("danger", "true")` | **Rojo** — como si cancelar fuera peligroso |
| `zona_form.py` | `setObjectName("secondaryButton")` | **Gris neutro** — correcto |
| `gestionar_ausencias.py` | `setObjectName("secondaryButton")` | **Gris neutro** — correcto |
| `perfiles_usuario_form.py` | Sin estilo | **Azul primario** (por defecto) — incorrecto |
| `dialogo_editar_perfil.py` | Sin estilo | **Azul primario** — incorrecto |
| `dialogo_crear_perfil.py` | Sin estilo | **Azul primario** — incorrecto |

Un botón rojo de "Cancelar" en `profesor_form` hace que el usuario dude — ¿cancelar es peligroso? ¿Va a borrar algo? La convención universal es que rojo = destructivo irreversible.

**Corrección:**
Todos los botones "Cancelar" y "Cerrar" deben usar `setObjectName("secondaryButton")` sin excepción.

---

### ~~INCONS-03 — "Generar PDFs" es rojo (danger) cuando no es una acción destructiva~~ ✅ RESUELTO v5.25.0
**Archivos afectados:** `pdf_export_widget.py`, `calendarios_pdf_widget.py`

```python
# pdf_export_widget.py y calendarios_pdf_widget.py:
self.exportar_pdf_btn = QPushButton("📄 Generar PDFs")
self.exportar_pdf_btn.setProperty("danger", "true")  # ← ROJO
```

Generar un PDF es una acción **completamente segura y reversible** (solo crea un archivo). Pintarlo de rojo transmite al usuario que algo puede salir mal o que es destructivo. El rojo debe reservarse para acciones que eliminan o modifican datos de forma irreversible.

Contrasta con `btn_generar` de `informes_estadisticos_widget.py`, que genera un reporte y está en `success` (verde). La misma categoría de acción (generar un documento) tiene dos colores opuestos.

**Corrección:**
```python
# Exportar PDF → acción positiva principal → azul primario (por defecto) o success verde
self.exportar_pdf_btn.setProperty("success", "true")

# O simplemente dejar el azul primario sin setProperty:
self.exportar_pdf_btn = QPushButton("📄 Generar PDFs")
self.exportar_pdf_btn.setIcon(icon_for_button("export"))
# Sin setProperty → azul primario, correcto para acción principal
```

---

### ~~INCONS-04 — "Importar JSON" es ámbar (warning) pero "Importar Profesores" es verde (success)~~ ✅ RESUELTO v5.25.0
**Archivos afectados:** `json_operations_widget.py`, `import_export_form.py`

```python
# json_operations_widget.py:
self.importar_btn.setProperty("warning", "true")     # Ámbar ← importar JSON

# import_export_form.py:
self.importar_profesores_btn.setProperty("success", "true")  # Verde ← importar Excel
```

Ambas son acciones de importación de datos. Semánticamente son idénticas: el usuario trae datos externos al sistema. Sin embargo, una es ámbar (precaución) y la otra verde (éxito/positivo). No hay criterio claro que justifique la diferencia.

La confusión es mayor porque el ámbar del `warning` normalmente comunica "puede haber consecuencias no esperadas, procede con cuidado" — lo cual es razonable para una importación que sobreescribe datos. Pero si eso es la razón para usar ámbar en JSON, debería usarse también para la importación de Excel.

**Corrección:**
Unificar ambas en `warning` (ámbar) si la importación puede sobreescribir datos, o en el azul primario si es aditiva. Documentar el criterio en un comentario.

---

### ~~INCONS-05 — Iconos en el texto del botón (emoji) vs. iconos en `setIcon()` — dos patrones mezclados~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** múltiples

Hay dos formas de añadir un icono a un botón en la app, y se usan indistintamente sin ningún criterio:

**Patrón A — `icon_for_button()` + texto limpio (correcto):**
```python
self.save_btn = QPushButton("Guardar Configuración")
self.save_btn.setIcon(icon_for_button("save"))
```

**Patrón B — Emoji/símbolo unicode directamente en el texto del botón (inconsistente):**
```python
# calculo_panel.py y cuotas_panel.py:
self.calcular_button = QPushButton("🔢 Calcular Cuotas")

# pdf_export_widget.py:
self.exportar_pdf_btn = QPushButton("📄 Generar PDFs")

# config_widgets/perfil_usuario_widget.py:
self.change_password_btn = QPushButton("🔒 Cambiar Contraseña")

# reset_password_dialog.py:
reset_btn = QPushButton("✓ Cambiar Contraseña")

# login_dialog.py:
cancel_btn = QPushButton("← Cancelar")
```

Los emojis en el texto no escalan con el DPI de la pantalla, no se pueden cambiar con el tema, y tienen diferente renderizado en macOS vs. Windows. El símbolo `"✓"` y la flecha `"←"` son caracteres unicode que no son emojis, pero siguen siendo inconsistentes con el uso de `icon_for_button()` en otros lados.

Además, el botón "Cambiar Contraseña" aparece como `"✓ Cambiar Contraseña"` en un diálogo y como `"🔒 Cambiar Contraseña"` en otro. Son el mismo botón con diferente icono.

**Corrección:**
Eliminar todos los emojis y símbolos del texto de los botones. Usar siempre `setIcon(icon_for_button("..."))` para el icono y texto limpio para la etiqueta.

---

### ~~INCONS-06 — Títulos de sección: algunos con emoji, otros sin él~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** `zona_form.py`, `gestionar_ausencias.py`, `profesor_form.py`, `gestor_sustituciones.py`, `panel_estadisticas.py`

Los títulos en mayúsculas que encabezan cada formulario o panel de lista son inconsistentes:

| Archivo | Título | Emoji |
|---|---|---|
| `zona_form.py` | `"🏫 ZONAS REGISTRADAS (0)"` | Sí |
| `gestionar_ausencias.py` | `"🏥 GESTIÓN DE AUSENCIAS"` | Sí |
| `profesor_form.py` | `"PROFESORES REGISTRADOS (0)"` | No |
| `gestor_sustituciones.py` | `"GESTIÓN DE SUSTITUCIONES"` | No |
| `panel_estadisticas.py` | `"ESTADÍSTICAS DE GUARDIAS"` | No |
| `reportes_form.py` | `"REPORTES E INFORMES"` | No |
| `ajustes_form.py` | `"AJUSTES DEL CURSO ESCOLAR"` | No |

No hay ningún criterio visible para que algunos tengan emoji y otros no. El resultado es que la app parece inacabada en las secciones sin emoji o excesivamente informal en las que lo tienen.

**Corrección:** Elegir un criterio y aplicarlo uniformemente. La opción más profesional es **quitar todos los emojis de los títulos** y usar `icon_for_form()` como icono de cabecera si se quiere iconografía, o directamente texto limpio en mayúsculas con el `objectName="titleMain"` establecido.

---

### ~~INCONS-07 — Tamaños de fuente inline en tres escalas distintas (px, pt, y valores arbitrarios)~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** `dialogo_diagnostico_guardias.py`, `dia_detalle_dialog.py`, `_celda_dia.py`, `vista_calendario.py`, `login_dialog.py`

El módulo `tokens.py` define `FontSize` con valores en píxeles (`CAPTION=11`, `BODY=14`, `SUBTITLE=16`, etc.). Pero en los `setStyleSheet()` inline se usan valores completamente distintos que no corresponden a ningún token:

```python
# dialogo_diagnostico_guardias.py — usa PUNTOS (pt), no píxeles:
titulo.setStyleSheet("font-size: 16pt; font-weight: bold;")
subtitulo.setStyleSheet("font-size: 11pt; color: #7f8c8d;")
lbl_descripcion.setStyleSheet("font-size: 10pt;")
lbl_detalle.setStyleSheet("font-size: 9pt;")

# dia_detalle_dialog.py — usa píxeles pero tamaños no en tokens:
label_icono.setStyleSheet("font-size: 18px;")
label_motivo.setStyleSheet("font-size: 10px;")
label_zona.setStyleSheet("font-size: 9px;")  # 9px es ilegible en muchas pantallas

# _celda_dia.py — fuentes microscópicas:
label_indicadores.setStyleSheet("font-size: 9px;")
label_total.setStyleSheet("font-size: 8px;")     # 8px es prácticamente ilegible
nombre_label.setStyleSheet("font-size: 8px;")

# vista_calendario.py:
label_titulo.setStyleSheet("font-size: 10px; color: #1976D2;")
label.setStyleSheet("font-size: 8px; font-weight: bold; color: #666;")
```

Mezclar `px` y `pt` es especialmente problemático: en macOS con Retina, `1pt ≠ 1px` a efectos de renderizado de Qt. Los valores de 8px y 9px son prácticamente ilegibles en pantallas estándar y completamente ilegibles en alta densidad si no se hace bien el escalado.

**Corrección:**
1. Usar exclusivamente `px` (nunca `pt` en QSS de PyQt6).
2. Usar siempre los tokens de `FontSize` en lugar de valores arbitrarios.
3. No usar fuentes menores de `FontSize.CAPTION` (11px). Si el contenido no cabe, replantear el layout.

```python
# MAL:
label.setStyleSheet("font-size: 8px;")

# BIEN:
from presentation.theme.tokens import FontSize
label.setStyleSheet(f"font-size: {FontSize.CAPTION}px; color: {Colors.TEXT_SECONDARY};")
```

---

### INCONS-08 — Diálogos de confirmación de borrado: cuatro patrones distintos
**Archivos afectados:** `profesor_form.py`, `zona_form.py`, `gestionar_ausencias.py`, `delete_user_dialog.py`, `perfiles_usuario_form.py`

Cuando el usuario quiere eliminar algo, la app responde de cuatro maneras diferentes:

| Caso | Mecanismo de confirmación |
|---|---|
| Eliminar profesor | `QMessageBox.question()` estándar de Qt |
| Eliminar zona | `QMessageBox.question()` estándar de Qt |
| Eliminar ausencia | `QMessageBox.question()` estándar de Qt |
| Eliminar usuario del sistema | `DeleteUserDialog` — diálogo completo personalizado con campo de confirmación por texto |
| Eliminar perfil | `QMessageBox.warning()` — diferente tipo que los anteriores |

No hay ningún estándar. La eliminación de un usuario (que tiene su propio diálogo de confirmación con escritura de texto) recibe más atención que la eliminación de un profesor con sus guardias asociadas, que solo pide `Sí/No` en un diálogo genérico.

**Corrección:**
Crear un único `ConfirmDeleteDialog` reutilizable que reciba `(titulo, mensaje, nombre_entidad)` y que use siempre el mismo aspecto. Para acciones muy destructivas (borrar usuario, borrar curso), añadir campo de confirmación por texto.

```python
# src/presentation/dialogs/confirm_delete_dialog.py
class ConfirmDeleteDialog(QDialog):
    """Diálogo unificado de confirmación de borrado."""
    def __init__(self, titulo: str, mensaje: str, nombre_a_confirmar: str = None, parent=None):
        # Si nombre_a_confirmar no es None → mostrar campo de texto para confirmación
        # Si es None → solo botones Sí/No
        ...
```

---

### ~~INCONS-09 — El botón de progreso "Cancelar" se convierte en "Cerrar" pero `sync_progress_dialog` tiene botones separados~~ ✅ RESUELTO v5.26.0
**Archivos afectados:** `progress_indicators.py`, `sync_progress_dialog.py`

En `ProgressDialog` (para generación de guardias):
```python
# Al inicio:
self.btn_cancelar = QPushButton("Cancelar")
# Al finalizar:
self.btn_cancelar.setText("Cerrar")  # El mismo botón cambia de función
```

En `SyncProgressDialog` (para sincronización SFTP):
```python
# Dos botones separados desde el inicio:
self.close_button = QPushButton("Cerrar")   # siempre ahí
# No hay botón de cancelar explícito
```

Un botón que cambia su texto y función a mitad de una operación es confuso. El usuario que estaba pensando en cancelar puede pulsar "Cerrar" por inercia. El patrón correcto es tener el botón "Cancelar" desactivado o cambiarlo por un botón "Cerrar" separado que aparece al finalizar.

**Corrección:**
```python
# En ProgressDialog.finalizar():
self.btn_cancelar.setVisible(False)
self.btn_cerrar = QPushButton("Cerrar")
self.btn_cerrar.setObjectName("secondaryButton")
self.btn_cerrar.clicked.connect(self.accept)
self.layout().addWidget(self.btn_cerrar)
```

---

### INCONS-10 — `QGroupBox` vs. `QFrame` vs. sin contenedor: tres formas de agrupar contenido relacionado
**Archivos afectados:** `dashboard_form.py`, `asignacion_widgets`, `dia_detalle_dialog.py`, `gestionar_ausencias.py`

El contenido relacionado se agrupa de tres maneras distintas a lo largo de la app:

**Opción A — `QGroupBox` con título** (usado en generacion_panel, panel_estadisticas, gestionar_ausencias):
```python
grupo = QGroupBox("Generación y Resultados")
```

**Opción B — `QFrame` con borde** (usado en dia_detalle_dialog, algunos widgets de dashboard):
```python
frame = QFrame()
frame.setFrameShape(QFrame.Shape.StyledPanel)
```

**Opción C — Sin contenedor, solo `QVBoxLayout` con título manual** (usado en ajustes_form, reportes_form):
```python
titulo = QLabel("AJUSTES DEL CURSO ESCOLAR")
# Sin ningún contenedor visual
```

El usuario ve secciones con caja gris con título, secciones con línea de borde, y secciones con texto en mayúsculas. Son tres lenguajes visuales para el mismo concepto de "agrupar campos relacionados".

**Corrección:**
Definir un único componente `SectionCard` o `SectionGroup` que se use consistentemente. Puede ser un `QGroupBox` estilizado en el QSS global. Prohibir `QFrame.StyledPanel` como contenedor de sección (solo para separadores) y el patrón de título manual sin contenedor.

---

### ~~INCONS-11 — Dos botones "Calcular Cuotas" idénticos en dos widgets que coexisten en el mismo formulario~~ ✅ INVESTIGADO v5.26.0 — No son duplicados: CuotasPanel (domain preview en asignacion_guardias_form) ≠ CalculoPanel (combinado en asignacion_calculo_form)
**Archivos afectados:** `calculo_panel.py`, `cuotas_panel.py`

```python
# calculo_panel.py:
self.calcular_button = QPushButton("🔢 Calcular Cuotas")

# cuotas_panel.py:
self.calcular_button = QPushButton("🔢 Calcular Cuotas")
```

Ambos widgets aparecen en el formulario de asignación. El texto es literalmente idéntico. El usuario no sabe cuál pulsar ni qué diferencia hay entre ellos. Es posible que uno sea residual (de una refactorización anterior) y ya no debería existir.

**Corrección:**
Verificar si `cuotas_panel.py` es realmente necesario o si es un duplicado de `calculo_panel.py`. Si ambos tienen funciones distintas, diferenciar claramente el texto y el icono de cada botón.

---

### ~~INCONS-12 — Los `setObjectName("titleMain")` no se aplican en todos los títulos de formulario~~ ✅ RESUELTO v5.25.0
**Archivos afectados:** `asignacion_calculo_form.py` (usa `titleMain`), resto de formularios (no lo usan)

Solo `asignacion_calculo_form.py` aplica el objectName de título del tema:
```python
# asignacion_calculo_form.py:
titulo = QLabel("CÁLCULO Y ASIGNACIÓN")
titulo.setObjectName("titleMain")  # ← correcto, usa el tema
```

El resto de formularios crean sus títulos sin `objectName`, lo que significa que su estilo depende de lo que herede de `QWidget` + `QLabel` globalmente, y no del selector específico `#titleMain` definido en el QSS. Si el diseño de `#titleMain` cambia, solo se actualiza un formulario.

**Corrección:**
Añadir `titulo.setObjectName("titleMain")` en todos los formularios que tienen título principal. Verificar que el selector `QLabel#titleMain` en `light.qss` cubre las propiedades deseadas (tamaño, color, peso).

---

### ~~INCONS-13 — Los separadores horizontales se crean de tres formas distintas~~ ✅ RESUELTO v5.25.0
**Archivos afectados:** `dia_detalle_dialog.py`, `_celda_dia.py`, `pdf_export_widget.py`, `calendarios_pdf_widget.py`

```python
# Forma 1 — QFrame.HLine (dia_detalle_dialog.py):
separador = QFrame()
separador.setFrameShape(QFrame.Shape.HLine)
separador.setFrameShadow(QFrame.Shadow.Sunken)

# Forma 2 — setObjectName("separator") con CSS (celda_dia.py, pdf_export_widget.py):
separador = QFrame()
separador.setObjectName("separator")
# CSS en light.qss: QFrame#separator { background: #ccc; max-height: 1px; }

# Forma 3 — inline style (residuos que pueden quedar en otros sitios):
separador.setStyleSheet("background-color: #ccc; max-height: 1px;")
```

`QFrame.HLine` con `Shadow.Sunken` produce una línea gris con sombra estilo Windows XP. El `objectName("separator")` produce una línea plana de 1px definida en el tema. Son visualmente distintos y semánticamente iguales.

**Corrección:**
Usar exclusivamente `setObjectName("separator")` para todos los separadores horizontales. Eliminar todos los `QFrame.HLine + Shadow.Sunken` de la presentación.

---

### ~~INCONS-14 — El bloque "Algoritmos disponibles" en Ajustes muestra opciones legacy~~ ✅ RESUELTO v5.26.3
**Archivos afectados:** `ajustes_widget.py`, `ajustes_form.py`, `generar_guardias.py`

El bloque informativo en Ajustes mostraba `v3.0`, `v2.9` y "Híbrido + ILP", aunque la generación real ya usa `v4.0` y `CP-SAT`.

**Corrección aplicada:**
1. El bloque visual muestra únicamente `Rápido (v4 Híbrido)` y `Óptimo (CP-SAT)` con mejor legibilidad.
2. Se normalizan valores legacy (`v2.9`, `v3.0`) a `v4.0` en ejecución.
3. El guardado en Ajustes ya no fuerza valores legacy.

---

### Resumen de inconsistencias por impacto

| ID | Inconsistencia | Archivos afectados | Impacto visual | Esfuerzo corrección |
|---|---|---|---|---|
| INCONS-01 | 3 rojos distintos para "Eliminar" | 6 archivos | Alto | S |
| INCONS-02 | "Cancelar" en rojo, gris o azul | 5 archivos | Alto | S |
| INCONS-03 | "Generar PDF" en rojo (danger) | 2 archivos | Medio | XS |
| INCONS-04 | Importar JSON vs. Importar Excel: ámbar vs. verde | 2 archivos | Medio | XS |
| INCONS-05 | Emojis en texto del botón vs. `setIcon()` | 8+ archivos | Medio | M |
| INCONS-06 | Títulos con emoji o sin él sin criterio | 7 archivos | Medio | S |
| INCONS-07 | Fuentes 8px, 9px, mezcla px/pt | 5 archivos | Alto — accesibilidad | M |
| INCONS-08 | 4 patrones distintos de confirmación de borrado | 5 archivos | Alto | L |
| INCONS-09 | Botón que cambia de función vs. botones separados | 2 archivos | Medio | S |
| INCONS-10 | QGroupBox vs. QFrame vs. sin contenedor | Muchos | Alto | XL |
| INCONS-11 | Dos botones "Calcular Cuotas" idénticos | 2 archivos | Alto | XS |
| INCONS-12 | `titleMain` solo en un formulario | Todos los forms | Bajo | S |
| INCONS-13 | 3 formas de hacer separadores | 4+ archivos | Bajo | S |
| INCONS-14 | Algoritmos legacy en bloque de Ajustes | 3 archivos | Medio | XS |

---

## 3. UX/UI — Lo que duele y lo que hay que hacer

### UX-01 — La app arranca directa al formulario de profesores (sin dashboard útil)
**Severidad: Alta**

La ventana principal activa la sección "profesores" al arrancar (`self.sidebar.set_active_section("profesores")`). Esto es un error de diseño. El usuario llega a una tabla vacía o con datos que no le interesan nada más entrar.

**Lo correcto:** Arrancar en un dashboard de "estado del día". Algo que muestre de un vistazo:
- ¿Hay guardias asignadas hoy?
- ¿Hay ausencias registradas hoy?
- ¿Hay sustituciones pendientes?
- Próximos días lectivos
- Alertas activas (profesor sin recreos configurados, zona sin asignar, etc.)

**Cómo implementarlo:**
1. Crear `src/presentation/forms/home_form.py` con un `HomeForm(BaseForm)`.
2. Layout: 2 columnas. Izquierda: cards de estado (hoy, esta semana). Derecha: feed de actividad reciente.
3. Añadir en `ccleaner_sidebar.py` el ítem `"inicio"` como primera opción de la categoría GESTIÓN.
4. En `ccleaner_main_window.py`, cambiar `set_active_section("profesores")` a `set_active_section("inicio")`.
5. Las cards de estado deben mostrar datos reales del curso activo (query a `Guardia` y `Ausencia` filtrando por `date.today()`).

**Estructura del widget:**
```python
# src/presentation/forms/home_form.py
class HomeForm(BaseForm):
    def setup_ui(self):
        layout = QHBoxLayout()
        
        # Columna izquierda: estado hoy
        left = self._build_today_panel()
        # Columna derecha: alertas y accesos rápidos
        right = self._build_alerts_panel()
        
        layout.addWidget(left, stretch=2)
        layout.addWidget(right, stretch=1)

    def _build_today_panel(self):
        # Cards: "Guardias hoy", "Ausencias hoy", "Sustituciones pendientes"
        # Usar MetricaCard existente de dashboard_form.py
        pass

    def _build_alerts_panel(self):
        # Lista de alertas detectadas automáticamente
        # Ej: "3 profesores sin zona preferida"
        # Ej: "No hay guardias generadas para este mes"
        # Botones de acción directa
        pass
```

---

### UX-02 — Login con fondo blanco plano. Aspecto amateur.
**Severidad: Alta**

El diálogo de login tiene el logo y el título sobre un fondo `#f8f9fa` (gris casi blanco), sin gradiente, sin estructura visual real. Comparado con cualquier app moderna, parece una demo.

**Propuesta:**
1. Dividir el diálogo en dos columnas: **izquierda** con panel de marca (fondo en gradiente `#1e3a5f → #007ACC`, logo grande centrado, tagline), **derecha** con el formulario sobre fondo blanco.
2. El panel izquierdo tiene `setMinimumWidth(240)` y usa `QLinearGradient` o directamente CSS gradient en el QSS.
3. Eliminar el área de logo y título actual del layout de la derecha — la marca ya está a la izquierda.

**Cómo implementarlo** (archivo: `src/presentation/forms/login_dialog.py`):
```python
# Reemplazar _create_login_tab y la parte de logo/título

# En setup_ui(), sustituir layout único por:
main_layout = QHBoxLayout(self)
main_layout.setContentsMargins(0, 0, 0, 0)
main_layout.setSpacing(0)

# Panel izquierdo de marca
brand_panel = QWidget()
brand_panel.setMinimumWidth(240)
brand_panel.setStyleSheet("""
    QWidget {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
            stop:0 #1e3a5f, stop:1 #007ACC);
    }
""")
brand_layout = QVBoxLayout(brand_panel)
brand_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
# Logo + nombre app + año en blanco sobre el gradiente
...

# Panel derecho — formulario existente
form_panel = QWidget()
form_panel.setStyleSheet("QWidget { background-color: white; }")
...

main_layout.addWidget(brand_panel)
main_layout.addWidget(form_panel)
self.setFixedSize(700, 480)
```

---

### UX-03 — La sidebar tiene 260px fijos y ocupa demasiado a 1366px
**Severidad: Media**

En portátiles de 13-14" (1366x768), la sidebar de 260px fijos se lleva el 19% del ancho. En pantalla completa es tolerable pero en ventana normal machaca el contenido.

**Propuesta:** Sidebar colapsable. Ancho expandido: 240px. Ancho colapsado: 56px (solo iconos). Botón de toggle arriba a la derecha del sidebar o con `Ctrl+B`.

**Cómo implementarlo:**
1. En `SidebarMenu`, añadir `self.collapsed = False` y botón de colapso en la parte superior.
2. Añadir método `toggle_collapse()` que cambia `self.setFixedWidth(56 if self.collapsed else 240)`.
3. Los `QLabel` de texto de cada menú item se ocultan/muestran con `setVisible(not self.collapsed)`.
4. En modo colapsado, mostrar tooltip con el nombre al pasar el ratón sobre cada ítem.
5. Guardar el estado en `QSettings` para recordarlo entre sesiones.

---

### UX-04 — El calendario mensual no cabe en pantalla a resoluciones normales
**Severidad: Alta**

El `QGridLayout` del calendario mensual con 7 columnas y 5-6 filas llena bien una pantalla 1920x1080 pero a 1366x768 o en ventana no maximizada las celdas quedan ridículamente pequeñas o se genera scroll horizontal.

**Propuesta:**
1. Añadir un modo de vista **"compacto"** que muestre solo el nombre del profesor (iniciales) en lugar del texto completo.
2. El `_CeldaDia` debe tener un modo compacto: `setMinimumHeight(60)` en lugar de `100`, y mostrar solo el conteo de guardias + puntos de colores.
3. Botón "Modo compacto / Modo detalle" en la toolbar del calendario.

**Cómo implementarlo:**
```python
# En VistaCalendario, añadir:
self.modo_compacto = False

def toggle_modo_compacto(self):
    self.modo_compacto = not self.modo_compacto
    self.cargar_mes()  # Reconstruir con el nuevo modo

# En _crear_celda_dia(), pasar modo_compacto al CeldaDia:
celda = CeldaDia(fecha, guardias_dia, ausencias_dia, modo_compacto=self.modo_compacto)
```

---

### UX-05 — No hay feedback visual de "guardando..." / "cargando..."
**Severidad: Media**

Cuando el usuario pulsa "Guardar" en el formulario de profesor o ajustes, no pasa nada visible durante el guardado (que normalmente es <100ms pero puede tardar si hay muchas entidades). No hay spinner, no hay mensaje "Guardado ✓".

**Propuesta:** Después de guardar correctamente, mostrar un **toast notification** en la esquina inferior derecha durante 2 segundos. No un QMessageBox (que interrumpe el flujo), sino un widget flotante.

**Cómo implementarlo** (nuevo archivo `src/presentation/widgets/toast_notification.py`):
```python
from PyQt6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout

class ToastNotification(QWidget):
    """Notificación flotante no intrusiva."""
    
    def __init__(self, parent, message: str, tipo: str = "success", duracion_ms: int = 2000):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Colores por tipo
        colores = {
            "success": ("#1E7E34", "#D1FAE5"),
            "error": ("#DC3545", "#FEE2E2"),
            "info": ("#007ACC", "#E6F2FA"),
            "warning": ("#856404", "#FFF3CD"),
        }
        fg, bg = colores.get(tipo, colores["info"])
        
        layout = QVBoxLayout(self)
        label = QLabel(message)
        label.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {fg};
                border-radius: 6px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        layout.addWidget(label)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.adjustSize()
        
        # Posicionar en esquina inferior derecha del padre
        parent_rect = parent.rect()
        x = parent_rect.width() - self.width() - 20
        y = parent_rect.height() - self.height() - 20
        self.move(x, y)
        self.show()
        
        # Auto-cerrar
        QTimer.singleShot(duracion_ms, self.close)

# USO en cualquier formulario:
def guardar_profesor(self):
    # ... lógica de guardado ...
    ToastNotification(self.window(), "✓ Profesor guardado correctamente", "success")
```

---

### UX-06 — Los diálogos de detalle del día (DiaDetalleDialog) son solo texto
**Severidad: Media**

Al hacer clic en un día del calendario, el diálogo muestra la información correcta pero en formato de texto plano agrupado en QGroupBox. No hay diferenciación visual entre guardias cubiertas, ausencias, y sustituciones más allá del agrupado.

**Propuesta:**
1. Cada guardia se muestra como una **card horizontal** con: avatar/iniciales del profesor, nombre, zona, turno (badge de color).
2. Las ausencias tienen fondo `#FEE2E2` con icono de hospital.
3. Las sustituciones tienen badge "SUST" en naranja.
4. Añadir botón "➕ Añadir sustitución" directamente en este diálogo (ahora hay que ir a otra sección).
5. Añadir botón "✉ Notificar al profesor" si hay email configurado.

**Cómo implementarlo:**
```python
# En DiaDetalleDialog._crear_seccion_guardias(), reemplazar el layout actual:
def _crear_card_guardia(self, guardia: Guardia) -> QWidget:
    card = QFrame()
    card.setFrameShape(QFrame.Shape.StyledPanel)
    card.setStyleSheet("""
        QFrame {
            background-color: white;
            border: 1px solid #E1E4E8;
            border-radius: 6px;
            padding: 8px;
        }
        QFrame:hover { border-color: #007ACC; }
    """)
    layout = QHBoxLayout(card)
    
    # Avatar con iniciales
    avatar = QLabel(self._iniciales(guardia.profesor.nombre_completo))
    avatar.setFixedSize(36, 36)
    avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
    avatar.setStyleSheet("""
        QLabel {
            background-color: #007ACC;
            color: white;
            border-radius: 18px;
            font-weight: bold;
            font-size: 12px;
        }
    """)
    
    # Info
    info = QVBoxLayout()
    nombre = QLabel(guardia.profesor.nombre_completo)
    nombre.setStyleSheet("font-weight: bold;")
    zona = QLabel(guardia.zona.nombre_zona if guardia.zona else "Sin zona")
    zona.setStyleSheet("color: #6B7280; font-size: 12px;")
    info.addWidget(nombre)
    info.addWidget(zona)
    
    # Badge turno
    badge = QLabel("M" if guardia.turno == "M" else "T")
    badge.setStyleSheet("""
        QLabel {
            background-color: #E6F2FA;
            color: #007ACC;
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: bold;
        }
    """)
    
    layout.addWidget(avatar)
    layout.addLayout(info)
    layout.addStretch()
    layout.addWidget(badge)
    return card
```

---

### UX-07 — El formulario de profesores mezcla tabla y formulario en pantalla partida: es confuso
**Severidad: Media**

`ProfesorForm` usa un `QSplitter` vertical con la tabla arriba y el formulario abajo. Para editar hay que seleccionar en la tabla (arriba) y rellenar abajo. En pantallas pequeñas el formulario queda muy comprimido o hay que hacer scroll.

**Propuesta:** Cambiar a un flujo de **panel deslizante o modal**:
1. La tabla ocupa toda la pantalla.
2. Al hacer doble clic en una fila o pulsar "Editar", se abre un `QDialog` (o panel lateral animado) con el formulario completo.
3. Esto da más espacio a la tabla y al formulario, y el flujo es más natural.

**Alternativa más sencilla sin modal:** Mantener el splitter pero que el panel del formulario esté oculto por defecto y aparezca solo al seleccionar/editar. Añadir botón "✕ Cerrar formulario" en el panel inferior.

---

### UX-08 — Falta barra de búsqueda global
**Severidad: Media**

Para encontrar un profesor, hay que ir a la sección de profesores y usar el filtro local. No hay forma de buscar globalmente "García López" y que aparezcan sus guardias, ausencias y sustituciones.

**Propuesta:** Añadir una barra de búsqueda en la parte superior de la sidebar (o como botón `Ctrl+K` que abre un modal de búsqueda rápida). El modal muestra resultados de profesores, guardias de hoy, ausencias activas.

**Cómo implementarlo** (nuevo archivo `src/presentation/widgets/quick_search.py`):
```python
# Ctrl+K abre QuickSearchDialog
class QuickSearchDialog(QDialog):
    resultado_seleccionado = pyqtSignal(str, int)  # ("profesor", id)
    
    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setMinimumWidth(500)
        # Input de búsqueda
        self.input = QLineEdit()
        self.input.setPlaceholderText("Buscar profesor, zona, guardia...")
        self.input.textChanged.connect(self.buscar)
        # Lista de resultados con QListWidget
        self.lista = QListWidget()
        ...
    
    def buscar(self, texto: str):
        if len(texto) < 2:
            return
        # Buscar en profesores, zonas, etc.
        profesores = session.query(Profesor).filter(
            Profesor.nombre_completo.ilike(f"%{texto}%")
        ).limit(10).all()
        ...
```

---

### UX-09 — Las notificaciones de error son QMessageBox bloqueantes
**Severidad: Media**

Casi todos los errores de formulario usan `QMessageBox.warning()` que bloquea la UI y fuerza al usuario a hacer clic en "OK" antes de continuar. Para errores de validación (campo vacío, formato incorrecto) esto es excesivo.

**Propuesta:**
1. Para **validaciones de campo**: mostrar un label de error rojo **debajo del campo** (estilo Bootstrap), no un popup. Usar `QLabel#fieldError { color: #DC3545; font-size: 11px; }`.
2. Para **errores de negocio** (no se puede eliminar porque tiene guardias): usar el toast del UX-05 con tipo "error".
3. Reservar `QMessageBox` solo para acciones destructivas irreversibles (eliminar datos).

**Cómo implementarlo en los formularios:**
```python
# En el formulario, añadir un QLabel debajo de cada campo crítico:
self.nombre_input = QLineEdit()
self.nombre_error = QLabel("")
self.nombre_error.setObjectName("fieldError")  # CSS: color rojo, font-size 11px
self.nombre_error.setVisible(False)

# Al validar:
def _validar_nombre(self):
    if not self.nombre_input.text().strip():
        self.nombre_error.setText("El nombre es obligatorio")
        self.nombre_error.setVisible(True)
        self.nombre_input.setStyleSheet("border-color: #DC3545;")
        return False
    self.nombre_error.setVisible(False)
    self.nombre_input.setStyleSheet("")  # Resetear
    return True
```

---

### UX-10 — El sidebar no indica en qué sección estás si el texto está cortado
**Severidad: Baja**

En resoluciones pequeñas, los textos del sidebar pueden quedar cortados. Y no hay breadcrumb ni título de sección en el área de contenido para orientar al usuario.

**Propuesta:** Añadir una barra de título contextual fija en la parte superior del área de contenido:
```
[icono]  Gestión de Profesores    [botón de ayuda contextual]
```
Implementar en `ContentWrapper.setup_ui()`: añadir un `QLabel` con el título de la sección antes del `QScrollArea`.

---

### UX-11 — El tema visual no tiene personalidad. Parece genérico.
**Severidad: Media — Impacto alto en percepción**

El esquema de colores azul `#007ACC` + gris + blanco es el mismo que usa VS Code, Windows 10 y la mitad de las apps Python. No hay ningún elemento visual que haga única a la app.

**Propuesta — Identidad visual:**
1. **Color de acento secundario**: añadir un naranja educativo `#E67E22` para badges de "hoy", contadores activos, indicadores de urgencia. Ya existe en tokens como `WARNING`.
2. **Ilustración vacía state**: cuando no hay guardias generadas, mostrar una ilustración SVG simple (calendario vacío) con un CTA "Generar guardias". Esto sustituye la tabla vacía o el texto de error.
3. **Fuente ligeramente mayor en títulos**: los títulos de sección (`QLabel#titleMain`) podrían estar en 22px bold en lugar de 20px, con un subrayado de acento de 3px en el color primario.
4. **Avatar de usuario en el sidebar**: mostrar las iniciales del usuario logueado en la parte inferior del sidebar (pequeño badge circular).

---

### ~~UX-12 — No hay modo "día de hoy" en el calendario~~ ✅ RESUELTO v5.25.0
**Severidad: Media**

El calendario se abre en el mes actual pero no hay botón "Hoy" para volver rápido si el usuario navega a otros meses. Tampoco hay resaltado especial de la celda del día actual.

**Propuesta:**
1. Añadir botón "Hoy" junto a los controles de navegación del calendario.
2. La celda del día actual tiene `border: 2px solid #007ACC` en lugar del gris por defecto.
3. La celda del día actual tiene el número del día en negrita y con color primario.

**Cómo implementarlo en `VistaCalendario._crear_celda_dia()`:**
```python
es_hoy = fecha == date.today()
celda = CeldaDia(fecha, guardias_dia, ausencias_dia, es_hoy=es_hoy)

# En CeldaDia.__init__():
if es_hoy:
    self.setStyleSheet("QFrame { border: 2px solid #007ACC; border-radius: 4px; }")
```

---

## 4. Funcionalidades — Qué cambiar, qué quitar, qué añadir

### FUNC-01 — AÑADIR: Notificación automática por email al profesor de guardia
**Severidad: Alta — Valor real para el usuario**

El modelo `Profesor` tiene `email_corporativo`. Existe `email_service.py`. Pero nunca se usa para notificar a los profesores que tienen guardia. El director tiene que avisar manualmente.

**Lo que hay que hacer:**
1. Al generar guardias (post-CP-SAT), ofrecer un botón "Enviar notificaciones por email" que mande un email a cada profesor con su calendario de guardias del mes.
2. El email incluye: días de guardia, turno, recreo, zona asignada. Formato HTML simple.
3. En `GeneracionPanel`, después de la generación exitosa, añadir:
   ```python
   self.btn_notificar = QPushButton("✉ Enviar emails a profesores")
   self.btn_notificar.setProperty("success", "true")
   self.btn_notificar.clicked.connect(self._enviar_notificaciones)
   ```
4. `_enviar_notificaciones()` invoca `email_service.py` con un template HTML para cada profesor con guardias ese mes.

**Template de email sugerido** (HTML):
```html
<h2>Guardias de patio — {mes} {año}</h2>
<p>Estimado/a {nombre},</p>
<p>Tus guardias de patio asignadas para este mes son:</p>
<table>
  <tr><th>Día</th><th>Turno</th><th>Recreo</th><th>Zona</th></tr>
  {filas}
</table>
<p>Centro educativo {nombre_centro}</p>
```

---

### FUNC-02 — AÑADIR: Historial de cambios (log de auditoría de guardias)
**Severidad: Media**

No existe registro de quién cambió qué guardia y cuándo. Si hay una queja de un profesor ("yo no tenía guardia ese día"), no hay forma de verificarlo.

**Lo que hay que hacer:**
1. Crear tabla `guardias_audit_log` en Alembic:
   ```python
   class GuardiaAuditLog(Base):
       __tablename__ = "guardias_audit_log"
       id = Column(Integer, primary_key=True)
       guardia_id = Column(Integer, ForeignKey("guardias.id"), nullable=True)
       accion = Column(String, nullable=False)  # "CREADA", "MODIFICADA", "ELIMINADA", "SUSTITUIDA"
       profesor_id = Column(Integer, nullable=True)
       usuario = Column(String, nullable=True)  # usuario del sistema (perfil)
       timestamp = Column(DateTime, default=_now_utc)
       detalle = Column(Text, nullable=True)  # JSON con datos antes/después
   ```
2. En `SQLAlchemyGuardiaRepository.save()` y `delete()`, insertar un registro en el log.
3. En la sección "Herramientas", añadir una pestaña "Auditoría" que muestre este log con filtros por fecha, profesor, tipo de acción.

---

### FUNC-03 — AÑADIR: Importación de horarios/guardias desde CSV/Excel más flexible
**Severidad: Media**

El importador de profesores desde Excel existe pero es rígido: requiere un formato exacto de columnas. Si el archivo tiene el nombre de la columna ligeramente diferente ("Nombre Completo" vs "nombre_completo"), falla.

**Lo que hay que hacer:**
1. Al importar un Excel/CSV, mostrar una pantalla de **mapeo de columnas**: "Columna del archivo → Campo de la app". El usuario arrastra o selecciona qué columna del archivo corresponde a cada campo.
2. Guardar el último mapeo usado en `QSettings` para no tener que rehacerlo.
3. Previsualizar las primeras 5 filas antes de confirmar la importación.

**Implementación en `importador_profesores.py`:**
```python
# Nuevo paso previo a la importación:
class ColumnMappingDialog(QDialog):
    """Diálogo para mapear columnas del archivo a campos de la app."""
    def __init__(self, columnas_archivo: list[str], campos_app: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mapear columnas")
        # Para cada campo_app requerido, mostrar un QComboBox con las columnas del archivo
        ...
```

---

### FUNC-04 — AÑADIR: Modo "semana típica" para restricciones de profesor
**Severidad: Media**

Las restricciones de días y recreos de un profesor son configurables (JSON en `dias_semana_permitidos` y `recreos_permitidos`). Pero la UI para configurarlas es una rejilla de checkboxes que no es intuitiva.

**Lo que hay que hacer:**
1. Reemplazar la rejilla de checkboxes por una **vista visual de semana**: una cuadrícula 5×N (Lun-Vie × recreos) donde cada celda es un toggle coloreado (verde = disponible, rojo = no disponible).
2. Añadir plantillas predefinidas: "Siempre disponible", "Solo mañanas", "Solo tardes", "Lunes-miércoles".

**Implementación sugerida** (en `src/presentation/forms/profesor_widgets/restricciones_widget.py`):
```python
class SemanaRestriccionesWidget(QWidget):
    """Rejilla visual de disponibilidad: filas=recreos, columnas=días."""
    
    DIAS = ["Lun", "Mar", "Mié", "Jue", "Vie"]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.celdas = {}  # (dia, recreo) -> QPushButton toggle
        self._build_grid()
    
    def _build_grid(self):
        layout = QGridLayout(self)
        # Cabecera
        for col, dia in enumerate(self.DIAS):
            layout.addWidget(QLabel(dia), 0, col + 1)
        # Filas de recreos
        for recreo in range(1, 4):  # 1, 2, 3 recreos
            layout.addWidget(QLabel(f"R{recreo}"), recreo, 0)
            for col, _ in enumerate(self.DIAS):
                btn = QPushButton("✓")
                btn.setCheckable(True)
                btn.setChecked(True)
                btn.setFixedSize(40, 32)
                btn.toggled.connect(lambda checked, d=col, r=recreo: self._on_toggle(d, r, checked))
                self.celdas[(col, recreo)] = btn
                layout.addWidget(btn, recreo, col + 1)
```

---

### FUNC-05 — CAMBIAR: El dashboard de métricas usa Matplotlib embebido — es lento y feo
**Severidad: Media**

`DashboardForm` y `PanelEstadisticas` usan `matplotlib` con `FigureCanvasQTAgg`. Los gráficos tardan 1-3 segundos en renderizarse y tienen el aspecto genérico de matplotlib (fuente Computer Modern, bordes grises, etc.).

**Lo que hay que hacer:**
1. Reemplazar los gráficos de barras simples por componentes **nativos PyQt6** usando `QPainter`. Un histograma de guardias por profesor es perfectamente dibujable con `QPainter.fillRect()`.
2. Para gráficos más complejos (líneas de equidad temporal), considerar `pyqtgraph` que es mucho más rápido y tiene mejor aspecto.
3. Si se quiere mantener matplotlib, al menos personalizar el estilo: `plt.style.use('seaborn-v0_8-whitegrid')` y setear `rcParams` para usar la misma fuente que la app.

**Implementación de un histograma nativo:**
```python
# src/presentation/widgets/bar_chart_widget.py
class BarChartWidget(QWidget):
    """Histograma nativo con QPainter. Sin dependencias externas."""
    
    def __init__(self, datos: list[tuple[str, int, str]], parent=None):
        # datos: [(label, valor, color_hex), ...]
        super().__init__(parent)
        self.datos = datos
        self.setMinimumHeight(200)
    
    def paintEvent(self, event):
        if not self.datos:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        w, h = self.width(), self.height()
        padding = 40
        max_val = max(v for _, v, _ in self.datos) or 1
        bar_w = (w - 2 * padding) / len(self.datos) - 4
        
        for i, (label, valor, color) in enumerate(self.datos):
            x = padding + i * (bar_w + 4)
            bar_h = (valor / max_val) * (h - 2 * padding)
            y = h - padding - bar_h
            
            painter.fillRect(int(x), int(y), int(bar_w), int(bar_h),
                           QColor(color))
            # Label
            painter.drawText(int(x), h - padding + 15, int(bar_w), 20,
                           Qt.AlignmentFlag.AlignCenter, label[:8])
```

---

### ~~FUNC-06 — QUITAR o SIMPLIFICAR: "Conectividad" como sección separada del menú~~ ✅ RESUELTO v5.26.0
**Severidad: Baja — UX medium**

La sección "Conectividad" del sidebar lleva a un formulario con configuración SMTP y SFTP. Es una sección de administración técnica que el usuario final rara vez toca. Ocupa un slot del menú que podría ser mejor usado.

**Lo que hay que hacer:**
Mover la configuración de conectividad a dentro de "Ajustes" como una pestaña más. Eliminar "Conectividad" del sidebar. Esto libera espacio en el menú.

**Implementación:**
1. En `AjustesForm`, añadir una pestaña "Conectividad" que cargue el `ConectividadForm` como widget.
2. En `ccleaner_sidebar.py`, eliminar la línea `self.add_menu_item(menu_layout, "conectividad", ...)`.
3. En `ccleaner_main_window.py`, eliminar el `add_view("conectividad", ...)`.

---

### FUNC-07 — AÑADIR: Exportación a Google Calendar / iCal para profesores
**Severidad: Media — Alto valor percibido**

Ya existe `icalendar_service.py`. Hay que exponerlo en la UI de forma accesible. Cada profesor debería poder descargar su calendario de guardias como `.ics` para importarlo en Google Calendar, Outlook o Apple Calendar.

**Lo que hay que hacer:**
1. En la pantalla de detalle del día (`DiaDetalleDialog`), añadir botón "📅 Exportar a calendario" que llame a `icalendar_service`.
2. En la sección Reportes, añadir opción "Exportar calendario iCal" por profesor o global.
3. El archivo `.ics` se guarda con `QFileDialog.getSaveFileName()`.

---

### FUNC-08 — AÑADIR: Vista de "Carga por profesor" tipo heat map
**Severidad: Media**

No hay una vista rápida que muestre qué profesores tienen más guardias acumuladas vs. su cuota teórica. El panel de estadísticas tiene datos pero no una visualización inmediata.

**Lo que hay que hacer:**
Añadir en `PanelEstadisticas` (o en el `HomeForm` propuesto en UX-01) una tabla de calor donde:
- Filas = profesores
- Columnas = semanas del mes
- Color de celda = verde (en cuota) / ámbar (ligeramente sobre) / rojo (muy sobre)

Esto permite al director ver de un vistazo la equidad real sin interpretar gráficos de barras.

---

### FUNC-09 — CAMBIAR: La generación de guardias no tiene estimación de tiempo
**Severidad: Baja**

El CP-SAT puede tardar entre 5 y 60 segundos dependiendo del número de profesores, zonas y días. La barra de progreso muestra porcentaje pero no da una estimación de tiempo restante útil.

**Lo que hay que hacer:**
1. Mostrar en el `ProgressDialog` el tiempo transcurrido (ya existe `label_tiempo`) y una estimación basada en la velocidad actual del solver.
2. Mostrar también "Soluciones encontradas: X" — el CP-SAT callback ya tiene esta información en `SolverCallback`.
3. Añadir un resumen previo a la generación: "Se asignarán X guardias a Y profesores en Z días lectivos. Tiempo estimado: ~15 segundos."

---

### FUNC-10 — AÑADIR: Plantillas de configuración para tipos de centro
**Severidad: Baja — Alto valor en onboarding**

Configurar la app desde cero (fechas, recreos, zonas, profesores) lleva tiempo. Para un nuevo usuario el proceso es opaco.

**Lo que hay que hacer:**
1. En el `InitialConfigDialog`, añadir una pantalla de "Plantilla de inicio rápido" con opciones como:
   - "Colegio de infantil/primaria (1 recreo mañana)"
   - "IES con jornada partida (recreo mañana + recreo tarde)"
   - "Centro con jornada continua"
2. Cada plantilla preconfigura: número de recreos, horarios típicos, zonas sugeridas (Patio Norte, Patio Sur, Entrada, Pasillos).
3. El usuario puede modificar después, pero tiene un punto de partida razonable.

---

## 5. Rendimiento

### PERF-01 — El calendario reconstruye todo el grid en cada navegación
**Severidad: Media**

Cada vez que el usuario cambia de mes, `VistaCalendario.cargar_mes()` destruye y reconstruye todo el `QGridLayout` con todos los `CeldaDia`. Para un mes con 30 días × ~10 guardias/día, esto crea y destruye ~300 widgets.

**Lo que hay que hacer:**
1. Reutilizar las celdas del grid (pool de CeldaDia). En lugar de `for child in children: child.deleteLater()`, actualizar el contenido de las celdas existentes con un método `celda.actualizar(nueva_fecha, nuevas_guardias)`.
2. Alternativamente, cachear los datos del mes anterior y solo re-renderizar si cambiaron.

**Métricas esperadas:** El tiempo de navegación debería bajar de ~500ms a ~100ms.

---

### PERF-02 — La app carga todos los formularios al arrancar
**Severidad: Media**

En `CCleanerMainWindow.create_views()`, se instancian todos los formularios (`ProfesorForm`, `ZonaForm`, `AjustesForm`, etc.) al arrancar, aunque el usuario solo verá uno. Esto ralentiza el arranque innecesariamente.

**Lo que hay que hacer:**
1. Implementar **lazy loading**: crear el widget solo la primera vez que el usuario navega a esa sección.
2. Usar un diccionario `self.widgets_cache = {}` y crear on-demand en `on_section_changed()`.

```python
def on_section_changed(self, section: str):
    if section not in self.widgets_cache:
        self.widgets_cache[section] = self._create_widget_for_section(section)
        self.content_stack.addWidget(self.widgets_cache[section])
    self.content_stack.setCurrentWidget(self.widgets_cache[section])
```

**Métricas esperadas:** Arranque de ~3s a ~1s.

---

### ~~PERF-03 — Matplotlib se importa en el hilo principal al arrancar~~ ✅ RESUELTO v5.26.0
**Severidad: Baja**

`import matplotlib` en `dashboard_form.py` y `panel_estadisticas.py` tarda ~300-500ms. Al estar en el hilo principal, congela brevemente la UI.

**Lo que hay que hacer:**
Mover los imports de matplotlib al interior de los métodos que los usan (lazy import), o usar `importlib.import_module()` en un hilo secundario al arrancar.

---

### ~~PERF-04 — No hay caché de los días lectivos entre cambios de mes~~ ✅ RESUELTO v5.25.0
**Severidad: Baja**

`listar_dias_lectivos()` se llama cada vez que se navega en el calendario. Si la configuración no ha cambiado, el resultado es idéntico. Añadir `@lru_cache` o cachear en el widget.

```python
# En VistaCalendario:
from functools import lru_cache

@lru_cache(maxsize=12)  # Un cache por mes del año
def _dias_lectivos_cached(self, anio: int, mes: int) -> list:
    return listar_dias_lectivos(self.session, anio, mes)
```

---

## 6. Detección de bugs y observabilidad

### BUG-01 — Estado inconsistente si la generación CP-SAT falla a mitad
**Severidad: Alta**

Si `generar_guardias_cpsat()` falla después de insertar algunas guardias (ej: excepción de BD, timeout del solver), la BD queda en estado parcial. No hay rollback garantizado.

**Lo que hay que hacer:**
Envolver toda la generación en una transacción explícita con rollback:
```python
# En GenerarGuardiasUseCase.execute():
try:
    with self.session.begin_nested():  # Savepoint
        guardias = _generar(...)
        for g in guardias:
            self.session.add(g)
    self.session.commit()
except Exception:
    self.session.rollback()
    raise
```

---

### BUG-02 — El selector de curso no actualiza todos los widgets correctamente
**Severidad: Media**

Cuando el usuario cambia de curso escolar en el `SelectorCursoWidget` del sidebar, la señal se propaga a los formularios via `cargar_datos()`. Pero no todos los widgets están conectados a esta señal — solo los que tienen `BaseForm` como base y están registrados. Los formularios cargados por primera vez después del cambio de curso pueden mostrar datos del curso anterior.

**Lo que hay que hacer:**
1. Añadir un test de integración que cambie el curso activo y verifique que todos los widgets relevantes recargan datos.
2. En `CCleanerMainWindow`, al recibir la señal de cambio de curso, forzar `session.expire_all()` y llamar `cargar_datos()` en todos los widgets cacheados.

---

### ~~BUG-03 — Los archivos de log se acumulan sin límite~~ ✅ RESUELTO v5.25.0
**Severidad: Baja**

Cada arranque crea un archivo `app_YYYYMMDD_HHMMSS.log`. Con uso diario durante un curso escolar (180 días × 2-3 arranques/día), se acumulan ~400-500 archivos en `/logs`.

**Lo que hay que hacer:**
En `src/main.py`, añadir limpieza de logs antiguos al arrancar:
```python
# Eliminar logs de más de 30 días
import glob
logs_antiguos = [f for f in glob.glob("logs/app_*.log")
                 if (datetime.now() - datetime.fromtimestamp(os.path.getmtime(f))).days > 30]
for log in logs_antiguos:
    os.remove(log)
```

---

### BUG-04 — No hay validación de integridad al importar JSON
**Severidad: Media**

Al importar un backup JSON, si el archivo está corrupto o es de una versión anterior con campos diferentes, la app puede fallar silenciosamente o con un traceback genérico.

**Lo que hay que hacer:**
1. Antes de importar, validar la estructura del JSON con Pydantic:
   ```python
   class BackupSchema(BaseModel):
       version: str
       fecha_exportacion: str
       cursos: list[CursoEscolarSyncDTO]
       profesores: list[ProfesorSyncDTO]
       ...
   ```
2. Si la validación falla, mostrar exactamente qué campo es inválido.

---

### ~~BUG-05 — Los `QTimer` de `ProgressDialog` no se detienen si el diálogo se cierra externamente~~ ✅ RESUELTO v5.25.0
**Severidad: Baja**

`ProgressDialog` tiene un `QTimer` para actualizar el contador de tiempo. Si el diálogo se cierra sin llamar a `finalizar()` (ej: cierre de la app, excepción), el timer sigue activo y puede causar acceso a widgets destruidos.

**Lo que hay que hacer:**
En `closeEvent()`:
```python
def closeEvent(self, event):
    if hasattr(self, '_timer') and self._timer.isActive():
        self._timer.stop()
    super().closeEvent(event)
```

---

### OBS-01 — No hay métricas de uso de la app
**Severidad: Baja**

No se sabe qué secciones usa el usuario, cuánto tiempo tarda en generar guardias, cuántas veces falla el CP-SAT. Esto dificulta priorizar mejoras.

**Lo que hay que hacer:**
Añadir logging de eventos de uso (local, sin envío externo) en un archivo separado `usage.log`:
```python
# Al navegar entre secciones:
logger.info(f"NAV: {section} | user: {current_user} | curso: {curso_activo}")
# Al generar guardias:
logger.info(f"GEN_CPSAT: resultado={resultado} | tiempo={elapsed}s | guardias={n}")
```
Esto permite analizar el log después para entender el uso real.

---

## 7. Escalabilidad y compatibilidad futura

### SCALA-01 — El modelo de datos no permite guardias "compartidas" entre dos profesores
**Severidad: Media — Limitación funcional**

`Guardia.profesor_id` es una FK a un único profesor. Hay centros donde una zona grande requiere dos profesores simultáneamente (patio + entrada al mismo tiempo). El modelo actual no lo soporta.

**Lo que hay que hacer:**
Añadir una relación many-to-many entre Guardia y Profesor, o añadir un campo `co_profesor_id` opcional en `Guardia`:
```python
co_profesor_id = Column(Integer, ForeignKey("profesores.id"), nullable=True)
co_profesor = relationship("Profesor", foreign_keys=[co_profesor_id])
```
Migración Alembic correspondiente. La UI del detalle del día ya debería mostrar ambos profesores.

---

### SCALA-03 — La sincronización SFTP es manual y puede fallar silenciosamente
**Severidad: Media**

El usuario tiene que hacer clic en "Sincronizar" para subir datos al servidor SFTP. Si olvida sincronizar, los datos quedan solo locales. Si la sincronización falla, el feedback es mínimo.

**Lo que hay que hacer:**
1. Añadir sincronización automática en background cada X minutos (configurable, por defecto 30min). Usar `QTimer` en `SyncManager`.
2. Mostrar en la parte inferior de la sidebar un indicador de estado de sync: `✓ Sincronizado hace 5 min` / `⚠ Sin sincronizar (45 min)` / `✕ Error de sync`.
3. Al cerrar la app, si hay cambios sin sincronizar, preguntar si sincronizar antes de salir.

**Implementación:**
```python
# En SidebarMenu, añadir:
self.sync_status_label = QLabel("✓ Sincronizado")
self.sync_status_label.setObjectName("syncStatus")
# Al final del layout, antes del stretch

# En CCleanerMainWindow:
self.sync_timer = QTimer()
self.sync_timer.timeout.connect(self._auto_sync)
self.sync_timer.start(30 * 60 * 1000)  # 30 minutos
```

---

### SCALA-04 — No hay mecanismo de actualización de la app
**Severidad: Baja**

No hay forma de que el usuario sepa que hay una nueva versión disponible. Con macOS y el build de PyInstaller, hay que distribuir manualmente.

**Lo que hay que hacer:**
1. Al arrancar, verificar en background (hilo secundario) si hay una versión más nueva en GitHub Releases (GET a la API pública de GitHub).
2. Si hay una versión nueva, mostrar un banner no intrusivo: "Nueva versión disponible: v5.X.Y [Ver cambios] [Recordar más tarde]".
3. El banner se muestra en el `HomeForm` propuesto en UX-01.

```python
# src/utils/update_checker.py
import urllib.request
import json
from threading import Thread

def check_for_updates(current_version: str, callback):
    def _check():
        try:
            url = "https://api.github.com/repos/cferrerobonet/guardias_patio/releases/latest"
            with urllib.request.urlopen(url, timeout=5) as r:
                data = json.loads(r.read())
                latest = data["tag_name"].lstrip("v")
                if latest > current_version:
                    callback(latest)
        except Exception:
            pass  # No interrumpir si no hay internet
    Thread(target=_check, daemon=True).start()
```

---

### SCALA-05 — El formato del campo `nombre_completo` es opaco
**Severidad: Baja**

`Profesor.nombre_completo` almacena "APELLIDOS, NOMBRE" como string libre. No hay separación entre nombre y apellidos en la BD. Esto hace difícil:
- Ordenar por apellido (se puede, pero solo si el formato se respeta)
- Mostrar "Nombre Apellidos" en vez de "APELLIDOS, Nombre" en emails
- Exportar a otros formatos

**Lo que hay que hacer:**
Añadir campos `nombre` y `apellidos` en el modelo `Profesor`. Mantener `nombre_completo` como propiedad calculada `@property` que devuelve `f"{self.apellidos}, {self.nombre}"`. Migración Alembic con script de split del string existente.

---

## 8. Deuda técnica residual

### TECH-01 — Dos sistemas de tema coexisten: `light.qss` y `ccleaner_theme.py`
**Severidad: Media**

`src/presentation/theme/light.qss` es el sistema nuevo. `src/presentation/themes/ccleaner_theme.py` (834 líneas) es el anterior. Ambos coexisten y se aplican en diferentes partes de la app. Esto crea inconsistencias visuales entre secciones.

**Lo que hay que hacer:**
1. Auditar qué selectores de `ccleaner_theme.py` no están en `light.qss` y migrarlos.
2. Eliminar `ccleaner_theme.py` y usar solo el QSS global.
3. Los colores y tokens que se importan de `ccleaner_theme.py` (`PRIMARY_BLUE`, `SUCCESS_GREEN`, etc.) deben migrar a `tokens.py`.

**Archivos afectados** (grep por `from presentation.themes.ccleaner_theme import`):
- `ccleaner_main_window.py`
- `ccleaner_sidebar.py`
- `panel_estadisticas.py`
- `reportes_form.py`
- `informes_estadisticos_widget.py`
- `vista_calendario_helpers.py`

---

### TECH-02 — `legacy_styles.py` con funciones `format_terminal_*` usadas en producción
**Severidad: Baja**

`src/presentation/theme/legacy_styles.py` contiene funciones HTML de formateo de tipo "terminal retro" que se usan en `GeneracionPanel` para el output del CP-SAT. Son estilos embebidos en Python, difíciles de mantener.

**Lo que hay que hacer:**
Extraer el output del generador a un `QTextBrowser` con un CSS externo, o al menos mover los templates HTML a un archivo `.html` cargado como recurso.

---

### TECH-03 — Tests de UI con `pytest-qt` no cubren los flujos críticos
**Severidad: Media**

Hay ~2127 tests pero la mayoría son unitarios. Los flujos críticos (login → selección de curso → generación de guardias → exportación PDF) no tienen tests de integración end-to-end.

**Lo que hay que hacer:**
Añadir 5-10 tests de flujo completo con `pytest-qt` usando fixtures de BD in-memory. Los más críticos:
1. `test_flujo_login_y_carga_datos()`: login correcto → datos cargados → logout
2. `test_generacion_guardias_basico()`: configurar curso → generar con CP-SAT → verificar guardias en BD
3. `test_exportar_pdf_un_profesor()`: guardia existente → exportar PDF → archivo creado
4. `test_cambio_curso_actualiza_calendario()`: cambiar curso → calendario muestra datos del nuevo curso

---

### TECH-04 — `src/presentation/theme/legacy_styles.py` tiene estilos de botones duplicados en `light.qss`
**Severidad: Baja**

`STYLE_BUTTON_SUCCESS`, `STYLE_BUTTON_DANGER`, etc. en `legacy_styles.py` duplican los selectores `QPushButton[success="true"]` y `QPushButton[danger="true"]` de `light.qss`. Hay que elegir uno.

---

## 9. Roadmap priorizado

### Escala de esfuerzo
- **XS**: < 1h | **S**: 1-4h | **M**: 4-8h | **L**: 1-2 días | **XL**: 2-5 días

### P0 — Impacto máximo, esfuerzo bajo-medio

| # | ID | Descripción | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | UX-01 | Dashboard de inicio con estado del día y alertas | L | Muy alto — primer impacto |
| 2 | UX-02 | Rediseñar login con panel de marca izquierdo | M | Muy alto — primera impresión |
| 3 | UX-05 | Toast notifications (reemplazar QMessageBox en validaciones) | M | Alto — fluidez diaria |
| 4 | UX-12 | Botón "Hoy" y celda actual resaltada en calendario | S | Alto — uso diario |
| 5 | BUG-01 | Transacción explícita en generación CP-SAT | S | Crítico — integridad datos |
| 6 | BUG-03 | Limpieza automática de logs antiguos | XS | Medio — mantenimiento |

### P1 — Alto valor, esfuerzo razonable

| # | ID | Descripción | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | FUNC-01 | Notificación email automática a profesores con sus guardias | M | Muy alto — diferenciador |
| 2 | UX-06 | Cards visuales en DiaDetalleDialog (avatares, badges) | M | Alto — UX uso diario |
| 3 | UX-03 | Sidebar colapsable con Ctrl+B | M | Alto — densidad información |
| 4 | FUNC-02 | Historial de cambios (audit log de guardias) | L | Alto — confianza del sistema |
| 5 | PERF-02 | Lazy loading de formularios al arrancar | M | Alto — velocidad arranque |
| 6 | TECH-01 | Unificar `ccleaner_theme.py` en `light.qss` | XL | Medio — mantenibilidad |
| 7 | UX-09 | Validación inline de campos (errores bajo el input) | L | Alto — UX formularios |
| 8 | SCALA-03 | Sync automático en background + indicador estado | L | Alto — robustez |

### P2 — Mejoras importantes, más esfuerzo

| # | ID | Descripción | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | UX-07 | Formulario de profesores como modal/panel deslizante | L | Medio — UX tabla |
| 2 | FUNC-04 | Vista semana típica para restricciones de profesor | M | Alto — UX restricciones |
| 3 | FUNC-05 | Reemplazar matplotlib por QPainter o pyqtgraph | XL | Medio — rendimiento visual |
| 4 | FUNC-07 | Exportar a iCal/Google Calendar para profesores | S | Alto — diferenciador |
| 5 | FUNC-08 | Heat map de carga por profesor | M | Alto — visibilidad equidad |
| 6 | UX-04 | Modo compacto en el calendario mensual | M | Alto — escalabilidad UI |
| 7 | PERF-01 | Pool de CeldaDia para el calendario (no destruir/recrear) | L | Medio — rendimiento |
| 8 | TECH-03 | Tests de flujo completo con pytest-qt | XL | Medio — confianza deploy |
| 9 | BUG-04 | Validación de esquema JSON en importación | M | Medio — robustez |

### P3 — Nice-to-have

| # | ID | Descripción | Esfuerzo | Impacto |
|---|---|---|---|---|
| 1 | UX-08 | Barra de búsqueda global (Ctrl+K) | L | Medio |
| 2 | UX-11 | Avatar de usuario en sidebar, acento de color secundario | S | Bajo-Medio |
| 3 | UX-10 | Barra de título contextual en área de contenido | S | Bajo |
| 4 | FUNC-03 | Mapeo de columnas al importar Excel | L | Medio |
| 5 | FUNC-09 | Estimación de tiempo en generación CP-SAT | S | Bajo |
| 6 | FUNC-10 | Plantillas de configuración para tipos de centro | M | Medio |
| 7 | SCALA-01 | Soporte co-profesor en guardia (many-to-many) | L | Bajo-Medio |
| 8 | SCALA-04 | Verificador de actualizaciones en background | M | Medio |
| 9 | SCALA-05 | Separar nombre/apellidos en modelo Profesor | L | Bajo |
| 10 | FUNC-06 | Mover Conectividad dentro de Ajustes | S | Bajo |

---

## Notas finales

**Lo que está bien y hay que conservar:**
- El motor CP-SAT con OR-Tools es una ventaja competitiva real. No tocarlo.
- La arquitectura Clean (entities, repos, use cases) es correcta y permite testear.
- El sistema multi-curso es una decisión correcta a largo plazo.
- El sistema de sync SFTP, aunque manual, funciona bien.

**La apuesta principal si tuviera que elegir solo 3 cosas:**
1. **UX-01** (dashboard de inicio) — cambia completamente la percepción de la app.
2. **FUNC-01** (emails a profesores) — es la funcionalidad que falta y que más valor aporta al usuario final.
3. **UX-02** (rediseño del login) — primera impresión, y actualmente es la parte más débil visualmente.

Con estos 3 ítems la app pasaría de "app funcional de Python" a "app profesional de gestión educativa".
