---
tags:
  - gestion-centro
  - auditoria
  - ux
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 2-alta
tipo: referencia
---

# Inventario de superficies UI e inconsistencias visuales

## 1. Métricas deterministas (commit auditado)

Comandos ejecutados sobre `src/presentation` (ver [[01_BASELINE_Y_ADAPTADOR]] CMD-05):

| Métrica | Valor | Lectura |
| --- | ---: | --- |
| Llamadas `setStyleSheet` | 287 | Estilo inline por widget en vez de cascada global |
| Literales hex de color | 631 (199 distintos) | Frente a ~40 tokens en `theme/tokens.py` |
| Referencias `QMessageBox` | 285 | Modal como respuesta por defecto |
| `font-size` < 11 px | 43 | Texto por debajo del mínimo legible |
| Líneas con emoji | 327 | Emojis usados como iconos/estado |
| `setMinimumSize/Width/Height` | 150 | Layout por tamaños fijos |
| `setFixedSize/Width/Height` | 21 | Ídem |
| Capas de estilo | 4 ficheros (light.qss 348 líneas, ccleaner_theme.py 822, legacy_styles.py 308, ui_styles.py 391) + inline | Cuatro fuentes de verdad |

## 2. Inventario de vistas registradas

| Sección (sidebar) | Widget | Título en vista | Acción primaria | Acción destructiva | Feedback |
| --- | --- | --- | --- | --- | --- |
| Profesores | `ProfesorForm` | "Gestión de Profesores" (no renderizado por `ContentWrapper`) | Nuevo/Guardar | Eliminar (selección múltiple) | QMessageBox + toast |
| Zonas | `ZonaForm` | ídem | Nuevo/Guardar | Eliminar | QMessageBox |
| Ajustes | `AjustesForm` (pestañas: curso, SMTP, SFTP, perfil, conectividad) | ídem | Guardar | – | QMessageBox + label pendiente/guardado |
| Perfiles de Usuario | `PerfilesUsuarioForm` | ídem | Crear perfil | Eliminar perfil | QMessageBox |
| Cálculo y Asignación | `AsignacionCalculoForm` → `CalculoPanel` + `GeneracionPanel` | "CÁLCULO Y ASIGNACIÓN" (mayúsculas) | Calcular cuotas / Generar | Limpiar guardias (misma fila) | Terminal retro HTML + modales + ProgressDialog |
| Calendario | `VistaCalendario` | – | Navegar | – | – |
| Ausencias / Sustituciones | `AusenciasSustitucionesWidget` | – | Buscar / Auto-asignar / Guardar | Limpiar historial | Label inline + QMessageBox |
| Importar/Exportar | `ImportExportForm` | – | Exportar / Importar | Limpiar antes de importar (checkbox) | QMessageBox + ProgressDialog |
| Reportes | `ReportesForm` | – | 5 exportaciones PDF + iCal | – | QMessageBox + ProgressDialog |
| Estadísticas | `PanelEstadisticas` | – | Actualizar | – | Tarjetas, tablas, gráficos QPainter, heatmap |

Diálogos (21 clases `QDialog`): login, crear/editar/eliminar perfil, cambiar/olvidar/restablecer contraseña, configuración inicial, crear curso, diagnóstico de guardias, detalle de día, acerca de, mapeo de columnas, sesión bloqueada, progreso, progreso de sync, reasignación, modales de perfil.

Formularios: 128 construcciones de control (61 line edits, 22 combos, 15 checks, 14 fechas, 9 textos, 4 horas, 3 spin). Tablas: 12 `QTableWidget`, 69 columnas estáticas. El detalle campo a campo y columna a columna está en `_work/paquete_ux_accesibilidad.md` §Inventarios.

## 3. Inconsistencias visuales detectadas (VIS)

| ID | Sev. | Inconsistencia | Evidencia | Patrón correcto |
| --- | --- | --- | --- | --- |
| VIS-001 | P2 | Cuatro capas de estilo compiten: `light.qss` aplicado en `QApplication`, `get_complete_stylesheet()` en la ventana, `legacy_styles`/`ui_styles` y 287 inline | `main.py:168-176`, `ccleaner_main_window.py:87`, `theme/legacy_styles.py`, `ui_styles.py` | Un único `app.qss` generado desde `tokens.py`; inline prohibido salvo `objectName`/propiedades |
| VIS-002 | P2 | Dos identidades cromáticas: tokens usan azul #007ACC (PRIMARY) y verde #1E7E34; los paneles de cálculo usan Tailwind #3B82F6/#10B981/#059669; el terminal usa #0F172A/#22C55E | `theme/tokens.py:8-33`, `calculo_panel.py:46-60`, `generacion_panel.py:79-97` | Una paleta semántica de 8 colores + neutros; cada color con rol |
| VIS-003 | P2 | Fuente global `-apple-system` 14 pt no existe en Windows (fallback aleatorio); paneles fuerzan 13 px; 43 usos < 11 px; etiquetas del calendario 7-9 px | `main.py:163-165`, `_celda_dia.py:117-159`, `bar_chart_widget.py:91-123` | Pila por SO: "Segoe UI", "SF Pro Text", "Ubuntu", sans-serif; escala 12/13/14/16/20 px |
| VIS-004 | P3 | Emojis como iconos y estados (☀️🌙🔄📊✅⚠️❌✉) mezclados con iconos MDI de `icon_for_button`; render distinto por SO y no accesible | 327 líneas; `generacion_panel.py:171,183,545-575` | Iconos vectoriales monocromos de `utils/icons.py` + texto de estado |
| VIS-005 | P2 | "Terminal retro" oscuro para resultados dentro de una UI clara; resultados como HTML de líneas, no como datos | `generacion_panel.py:178-183`, `theme/terminal_format.py` | Tarjeta de resultado (métricas) + tabla ordenable por profesor + lista de incidencias con acciones |
| VIS-006 | P2 | Títulos inconsistentes: "CÁLCULO Y ASIGNACIÓN" en mayúsculas, otros en Title Case, y el título registrado no se pinta | `asignacion_calculo_form.py:78`, `ccleaner_main_window.py:45-68` | Cabecera común de vista (título + subtítulo + acciones) renderizada por `ContentWrapper` |
| VIS-007 | P2 | Botones sin jerarquía: propiedades `danger`/`success` + estilos inline + `setMinimumHeight(36)` repetido; primario y destructivo con mismo peso | `generacion_panel.py:155-176`, `profesor_form.py:244-257` | Tres variantes: primario (1 por vista), secundario, texto/peligro; altura desde token |
| VIS-008 | P3 | Tres lenguajes de feedback: `QMessageBox` (con hack `_fix_messagebox_size` para macOS), `ToastNotification` propia, labels inline | `gestion_cursos_widget.py:33-46`, `toast_notification.py`, `ausencias_sustituciones.py:492-497` | Regla única: inline para validación, toast para éxito, modal para destructivo/bloqueante |
| VIS-009 | P2 | Tamaño mínimo 1400×900 en ventana vs 1200×800 en settings; portátiles 1366×768 quedan fuera | `ccleaner_main_window.py:84`, `settings.py:109-110` | Mínimo 1024×700 con scroll interno; tamaño recomendado desde `availableGeometry` |
| VIS-010 | P3 | Identidad: tema y componentes llamados "ccleaner_*"; sidebar oscura genérica; logo/branding EPLA sólo en PDF y QMessageBox | `presentation/themes/ccleaner_theme.py`, `components/ccleaner_sidebar.py`, `utils/corporate_branding.py` | Renombrar a `app_theme`/`sidebar`; aplicar marca (color primario, logo en sidebar) de forma discreta |

## 4. Patrones lógicos que hoy se rompen

| Patrón esperado | Dónde se rompe |
| --- | --- |
| Misma posición para Guardar/Cancelar en todos los formularios | Profesor y Zona: panel lateral con ✕; Ajustes: botón al pie; Ausencias: barra intermedia |
| Misma estructura de tabla (toolbar → tabla → paginación) | Profesores tiene buscador; Zonas no; Auditoría filtros arriba y límite 500 sin aviso |
| Un color = un significado | Verde = éxito, pero también = borde del panel Generación; azul = primario, pero también = borde del panel Cálculo |
| Estado del sistema visible siempre | Sync en sidebar (bien), curso activo en sidebar (bien), pero estado de configuración/generación invisible |
| Iconos siempre a la izquierda del texto en botones | Emojis a veces al inicio (✉), a veces ausentes |

## 5. Aspectos visuales positivos a conservar

- Sidebar colapsable con estado de sync y selector de curso: buen centro de estado.
- Iconografía MDI vía `icon_for_button` ya existe: base para eliminar emojis.
- `tokens.py` define paleta con contrastes AA anotados: base del contrato.
- Panel de profesor oculto hasta Nuevo/Editar (UX-07 en CHANGELOG): patrón maestro-detalle correcto.
- Estadísticas con tablas equivalentes a los gráficos.
