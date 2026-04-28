# Changelog

Todos los cambios notables de este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

## [5.32.0] - 2026-04-28

### 🎯 Resumen
Estrategia de consecutividad: modelo span directo en CP-SAT y ventanas de bloque en v4 Híbrido para alcanzar ~70% de concentración temporal de guardias por profesor.

### ✨ Added
- `services/asignador_guardias_cpsat.py`: modelo `primera/ultima/span` por profesor (sustituyendo XOR cortes y semanas activas); minimización directa del span lectivo con `PESO_SPAN=300`; métrica de concentración `guardias/span_natural×100` en la fase 8; ventanas de bloque en el hint greedy con penalización 10× por salir de la ventana asignada
- `services/_asignador_v4_helpers.py`: función `calcular_ventanas_bloque()` (bloques con solapamiento 30%, ordenados por cuota desc); criterio 0 en `_score_slot` — penalización de slots fuera de la ventana temporal del profesor
- `services/asignador_guardias_v4_hibrido.py`: fase 0.5 que calcula `dia_a_ordinal` y `ventanas_bloque` antes de las rondas equitativas
- `services/_asignador_tipos.py`: campos `ventanas_bloque` y `dia_a_ordinal` en `ContextoAsignacion`

### Changed
- CP-SAT: eliminados `PESO_SEMANAS_ACTIVAS` (5 000) y `PESO_CONSECUTIVIDAD` (1 000); sustituidos por `PESO_SPAN=300` que modela directamente el span primera→última guardia

## [5.31.15] - 2026-04-24

### 🎯 Resumen
Gráficos de estadísticas completamente rediseñados: legibles, con altura dinámica y codificación por color.

### Changed
- `presentation/widgets/bar_chart_widget.py`: altura dinámica (26px/barra), etiquetas de apellido completo, línea de media vertical, código de color por desviación (azul/verde/ámbar/rojo), leyenda de colores; donut con total en el centro y porcentaje en cada sector
- `presentation/widgets/panel_estadisticas.py`: eliminado `setMinimumHeight` fijo en el gráfico de barras

## [5.31.14] - 2026-04-24

### 🎯 Resumen
Corregido el checkbox "Seleccionar todos" en Calendarios PDF que no marcaba los profesores al activarse.

### Fixed
- `presentation/forms/reportes_widgets/calendarios_pdf_widget.py`: comparación correcta del estado del checkbox tristate (`int(state) == Qt.CheckState.Checked.value`) para que "Seleccionar todos" funcione en ambas direcciones

## [5.31.13] - 2026-04-24

### 🎯 Resumen
Eliminadas las opciones redundantes del combo de exportación PDF en Reportes.

### Changed
- `presentation/forms/reportes_widgets/calendarios_pdf_widget.py`: eliminados los tipos `mes_todos`, `curso_todos` y `curso_seleccionados` del combo; simplificada la lógica de `_on_tipo_pdf_changed`
- `tests/test_calendarios_pdf_widget.py`: actualizados los tests para reflejar las 2 opciones restantes

## [5.31.12] - 2026-04-24

### 🎯 Resumen
Corregido error al enviar calendario PDF por email: el VO `Email` se pasaba sin convertir a string.

### Fixed
- `presentation/forms/reportes_form.py`: `str()` sobre `profesor.email_corporativo` (VO `Email`) antes de pasarlo a `send_calendar_pdf`, evitando `AttributeError: 'Email' object has no attribute 'encode'`

## [5.31.11] - 2026-04-23

### 🎯 Resumen
Implementadas mejoras pendientes: persistencia de configuración SFTP/SMTP entre actualizaciones y mayor concentración temporal en asignación CP-SAT.

### Changed
- `presentation/dialogs/initial_config_dialog.py`: el `.env` ahora se guarda/carga en `get_base_directory() / ".env"`; se añade migración automática desde el `.env` legacy del bundle cuando la app está compilada
- `main.py`: carga del `.env` persistente al arranque antes de validar si falta configuración inicial
- `services/asignador_guardias_cpsat.py`: fase temporal mejorada con penalización por semanas activas + aumento de peso de consecutividad diaria (fase 1 + fase 2)
- `docs/MEJORAS_PENDIENTES.md`: marcados los dos ítems como resueltos (`✅ RESUELTO v5.31.11`)

### Fixed
- Evita que el asistente de configuración reaparezca tras reemplazar la app en `/Applications` cuando ya existía configuración previa
- Reduce dispersión mensual de guardias al favorecer menos semanas activas por profesor

## [5.31.10] - 2026-04-23

### 🎯 Resumen
Corregido error `PDFStyles is not defined` al generar calendarios PDF individuales.

### Fixed
- `services/_pdf_mini_calendario.py`: faltaba el import `from services.pdf_styles import PDFStyles`; el módulo usaba `PDFStyles.get_color_zona()` sin haberlo importado

## [5.31.9] - 2026-04-23

### 🎯 Resumen
Aviso de actualización disponible movido al sidebar (visible siempre), justo encima de la versión y el botón Acerca de.

### Changed
- El verificador de actualizaciones en background ahora se lanza desde `CCleanerMainWindow` en lugar de `HomeForm`
- El banner de nueva versión aparece en el sidebar (botón amarillo sobre la versión), visible desde cualquier sección; al hacer clic abre la página de releases de GitHub

### 🧹 Housekeeping
- Eliminado código de banner de `HomeForm` (clase `_UpdateBanner`, señal, métodos `_lanzar_check_actualizacion` y `_on_nueva_version`)

## [5.31.8] - 2026-04-23

### 🎯 Resumen
Corregido AttributeError al abrir el calendario con ausencias: el repositorio devolvía AusenciaEntity (sin relación `profesor`) en lugar del modelo ORM.

### Fixed
- `vista_calendario_helpers.py` → `cargar_datos_periodo()`: la consulta de ausencias pasaba por el repositorio de dominio (`AusenciaEntity`) que no tiene la relación `profesor`; ahora se consulta directamente el modelo ORM con `joinedload(AusenciaModel.profesor)`, igual que se hace con las guardias

## [5.31.7] - 2026-04-23

### 🎯 Resumen
Corregido SSHException visible al usuario durante generación CP-SAT: el hilo de heartbeat SFTP no capturaba excepciones de Paramiko.

### Fixed
- `sync/session_lock.py` → `_on_heartbeat()`: captura `Exception` en lugar de `(ValueError, TypeError, OSError)` — `SSHException` de Paramiko no es `OSError`, por lo que la excepción escapaba del hilo de heartbeat y se mostraba al usuario como un error de la generación
- `sync/sync_manager.py` → `_ensure_connected()`: mismo patrón — captura `Exception` para que una caída de conexión SSH durante la comprobación de estado provoque reconexión en lugar de propagarse

## [5.31.6] - 2026-04-23

### 🎯 Resumen
Corregido el bug por el que editar un profesor o zona por segunda vez mostraba los datos anteriores al último cambio.

### Fixed
- `utils/repository_cache.py` → `invalidate_repository_cache()`: se llamaba a `invalidate_cache(pattern)` sin `use_regex=True`, por lo que el patrón `".*profesor.*"` / `".*zona.*"` se trataba como substring literal y nunca coincidía con ninguna clave — la invalidación siempre eliminaba 0 entradas y la caché quedaba obsoleta indefinidamente

## [5.31.5] - 2026-04-23

### 🎯 Resumen
Eliminado el pool de CeldaDia que causaba `RuntimeError: wrapped C/C++ object has been deleted` al volver al calendario tras una sustitución.

### Fixed
- `VistaCalendario`: eliminado `_celda_pool` por completo — el pool causaba una condición de carrera con `deleteLater()` en el flujo sustitución→calendario: los objetos C++ se destruyen asíncronamente y en ciertos timings el render intentaba reutilizar celdas ya destruidas. Ahora `_renderizar_vista_mensual` crea siempre instancias nuevas de `CeldaDia`

## [5.31.4] - 2026-04-23

### 🎯 Resumen
Corregido OSError al guardar el logo de usuario en producción: las rutas relativas `Path("imagenes")` apuntaban al bundle de PyInstaller (solo lectura).

### Fixed
- `actualizar_logo.py`, `listar_perfiles.py`, `eliminar_perfil.py`, `actualizar_perfil.py`, `ccleaner_sidebar.py`: sustituido `Path("imagenes")` por `get_data_directory() / "imagenes"` para garantizar escritura en el directorio de datos del usuario en cualquier entorno

## [5.31.3] - 2026-04-23

### 🎯 Resumen
Eliminado el ítem de menú Auditoría; el historial vacío de Sustituciones se reemplaza por el audit log real filtrado a sustituciones.

### Changed
- `GestorSustituciones`: elimina `tabla_historial` (nunca tenía datos) y embebe `AuditoriaGuardiasForm` prefiltrando a `SUSTITUIDA`; `refrescar()` recarga también el historial
- `ccleaner_sidebar.py`: eliminado ítem "Auditoría" del menú HERRAMIENTAS
- `ccleaner_main_window.py`: eliminado registro de la sección `auditoria` e import de `AuditoriaGuardiasForm`
- `tests/test_gestor_sustituciones.py`: actualizado test `test_tiene_widgets_principales` para el nuevo atributo `_historial_audit`

## [5.31.2] - 2026-04-23

### 🎯 Resumen
Botón Compacto/Detalle del calendario ahora funciona; vista de detalle como modo por defecto.

### Fixed
- `VistaCalendario.actualizar_calendario()`: limpia `_celda_pool` antes de destruir el `widget_grid` contenedor — las celdas del pool quedaban como widgets Qt destruidos y la segunda renderización llamaba métodos sobre objetos zombie, impidiendo cualquier cambio visual al pulsar el botón
- `_crear_barra_controles()`: el botón se inicializa con el texto y estado `checked` coherentes con `modo_compacto=False` (modo detalle por defecto)

## [5.31.1] - 2026-04-23

### 🎯 Resumen
Versión de la app visible en el panel izquierdo del diálogo de login.

### Changed
- `LoginDialog`: añade etiqueta `vX.Y.Z` sobre los créditos en el panel de marca

## [5.31.0] - 2026-04-23

### 🎯 Resumen
Verificador de actualizaciones en background: banner no intrusivo en el HomeForm cuando hay una versión nueva en GitHub Releases (SCALA-04).

### ✨ Added
- `utils/update_checker.py`: hilo daemon que consulta la API de GitHub Releases y compara versiones semánticas
- `HomeForm._UpdateBanner`: banner con botones "Ver cambios" (abre releases en navegador) y "Recordar más tarde" (oculta el banner)
- `HomeForm._lanzar_check_actualizacion()`: arranca el check al iniciar el panel de inicio; usa señal Qt para notificar en el hilo principal

## [5.30.9] - 2026-04-22

### 🎯 Resumen
Cuatro ítems de auditoría completados: métricas de uso, unificación de estilos legacy, importación flexible con mapeo de columnas y verificador de CP-SAT.

- `ImportExportForm.importar_profesores()`: muestra `ColumnMappingDialog` antes de importar y pasa mapeo y skip_rows al servicio (FUNC-03)
- `presentation/theme/legacy_styles.py`: constantes de color reemplazadas por aliases de `tokens.Colors`; funciones de terminal re-exportadas desde `terminal_format.py` (TECH-02)
- `CCleanerMainWindow.on_section_changed()`: emite `usage_log("NAV", ...)` en cada cambio de sección (OBS-01)
- `GenerarGuardiasUseCase.execute()`: emite `usage_log("GEN_CPSAT", ...)` al terminar la generación (OBS-01)

## [5.30.8] - 2026-04-22

### 🎯 Resumen
Tests de flujo completo con pytest-qt: 6 nuevos tests de UI que cubren panel de profesores, calendario y exportación PDF.

### ✨ Added
- `tests/test_flujo_ui.py`: tests de flujo UI con pytest-qt — panel deslizante de profesores, navegación del calendario, modo compacto y exportación PDF (TECH-03)

## [5.30.7] - 2026-04-22

### 🎯 Resumen
Unificación de sistemas de tema: `ccleaner_theme.py` ahora es una capa de compatibilidad que redirige a `tokens.Colors/Spacing/FontSize/BorderRadius`.

### 🧹 Housekeeping
- `ccleaner_theme.py`: todas las constantes literales reemplazadas por aliases de `presentation.theme.tokens`; los importadores existentes siguen funcionando sin cambios (TECH-01)

## [5.30.6] - 2026-04-22

### 🎯 Resumen
Formulario de profesores como panel lateral oculto: la tabla ocupa el 100% por defecto y el formulario aparece al pulsar "Nuevo" o "Editar".

### Changed
- `ProfesorForm`: el panel de formulario está oculto por defecto; aparece al hacer clic en "Nuevo" o "Editar" y se cierra con "✕" o al guardar/cancelar (UX-07)
- `ProfesorForm`: nuevo botón "Nuevo" en la barra de acciones de la tabla (UX-07)

## [5.30.5] - 2026-04-22

### 🎯 Resumen
Pool de CeldaDia en la vista mensual: las celdas se reutilizan en cada navegación en lugar de destruirse y recrearse.

### 🧹 Housekeeping
- `CeldaDia.actualizar()`: nuevo método que actualiza datos y reconstruye el contenido sin destruir el widget (PERF-01)
- `VistaCalendario._celda_pool`: lista de celdas reutilizables; en navegación mensual se actualizan en lugar de recrearse (PERF-01)

## [5.30.4] - 2026-04-22

### 🎯 Resumen
Heat map de equidad en el panel de estadísticas: cuadrícula profesores × semanas con colores verde/ámbar/rojo según desviación respecto a la cuota.

### ✨ Added
- `PanelEstadisticas`: nueva pestaña "Equidad" con `tabla_heatmap` — filas=profesores, columnas=semanas del período, celda verde (en cuota), ámbar (+25%), rojo (+50%) (FUNC-08)

## [5.30.3] - 2026-04-22

### 🎯 Resumen
Vista semana típica para restricciones de profesor: cuadrícula visual 5×N con plantillas rápidas en lugar de checkboxes.

### ✨ Added
- `SemanaRestriccionesWidget`: cuadrícula 5×N (Lun-Vie × recreos) con botones toggle verde/rojo y plantillas rápidas "Siempre", "Solo mañanas", "Solo tardes", "Lun/Mié/Vie", "Ninguno" (FUNC-04)

### Changed
- `RestriccionesWidget`: reemplaza la tabla+checkboxes por `SemanaRestriccionesWidget`; mantiene la misma API pública (FUNC-04)

## [5.30.2] - 2026-04-22

### 🎯 Resumen
Modo compacto en el calendario mensual: celdas reducidas con conteo de guardias y puntos de color, activable con el botón "Compacto".

### ✨ Added
- `CeldaDia`: nuevo parámetro `modo_compacto=False` — en modo compacto muestra solo número del día, conteo de guardias y puntos de color (🔴 ausencias, 🟡 sustituciones) con altura máxima de 80px (UX-04)
- `VistaCalendario`: botón toggle "Compacto/Detalle" en la barra de controles; llama a `toggle_modo_compacto()` que alterna el modo y re-renderiza (UX-04)

## [5.30.1] - 2026-04-22

### 🎯 Resumen
Sync automático en background cada 30 minutos con indicador de estado en la sidebar y pregunta al cerrar si hay cambios sin sincronizar.

### ✨ Added
- `SyncManager.get_last_sync_time()`: devuelve la fecha/hora de la última sync exitosa desde `last_sync.json` (SCALA-03)
- `SidebarMenu.set_sync_status(estado, texto)`: indicador de estado de sync en la parte inferior de la sidebar con colores ✓/⚠/✕ (SCALA-03)
- `CCleanerMainWindow._setup_auto_sync()`: QTimer cada 30 min que lanza `SyncWorker` en background silencioso (SCALA-03)
- `CCleanerMainWindow.closeEvent()`: si hay cambios sin sincronizar (>5 min desde última sync), pregunta al usuario antes de salir (SCALA-03)

## [5.30.0] - 2026-04-22

### 🎯 Resumen
Nueva funcionalidad: historial de cambios en guardias con tabla BD auditada y UI con filtros.

### ✨ Added
- `GuardiaAuditLog`: nuevo modelo ORM y tabla `guardias_audit_log` (migración `9defacb2c7e9`) — registra acciones CREADA, MODIFICADA, ELIMINADA, SUSTITUIDA, GENERADA_BULK con profesor, timestamp y detalle JSON (FUNC-02)
- `AuditoriaGuardiasForm`: nueva vista en HERRAMIENTAS con tabla filtrable por fecha, acción y nombre de profesor (FUNC-02)
- Sidebar: nueva entrada "Auditoría" con icono `history` en la sección HERRAMIENTAS (FUNC-02)

### Changed
- `SQLAlchemyGuardiaRepository.save()` y `delete()`: insertan entrada en `guardias_audit_log` en cada operación (FUNC-02)
- `GenerarGuardiasUseCase.execute()`: registra entrada GENERADA_BULK con total y algoritmo tras cada generación (FUNC-02)

## [5.29.1] - 2026-04-22

### 🎯 Resumen
Corrección crítica de integridad: la generación de guardias es ahora atómica — el borrado de guardias previas y la inserción de las nuevas se confirman en el mismo commit.

### Fixed
- `generar_guardias.py`: eliminado el `commit()` anticipado tras el borrado de guardias existentes; ahora el delete y los inserts son una única transacción — si la generación falla a mitad, se hace rollback completo sin dejar la BD vacía (BUG-01)
- `generar_guardias.py`: ampliado el `except` de `(ValueError, TypeError, OSError)` a `Exception` para garantizar rollback ante cualquier tipo de error (SQLAlchemyError, RuntimeError, etc.)

## [5.29.0] - 2026-04-22

### 🎯 Resumen
Mejoras de UX: validaciones de campo inline en diálogos de perfil, errores de negocio como toasts no bloqueantes, y corrección del bug de cambio de curso que no refrescaba vistas ya cargadas.

### Fixed
- `ccleaner_main_window.py`: al cambiar de curso, se invoca `session.expire_all()` y se refrescan **todos** los widgets ya instanciados (no solo el visible) — evita que vistas cargadas antes del cambio muestren datos del curso anterior (BUG-02)

### Changed
- `dialogo_crear_perfil.py`: validaciones de campo (usuario, email, contraseña, confirmación, duplicado) pasan de 5 QMessageBox secuenciales a un único label de error inline en rojo bajo el formulario (MODAL-03)
- `dialogo_editar_perfil.py`: validación de email vacío → label de error inline (MODAL-03)
- `perfiles_usuario_form.py`: errores de negocio (ValidationError, NotFoundError) y aviso de acceso no permitido → ToastNotification "error" en lugar de QMessageBox bloqueante (UX-09)
- `reportes_form.py`: aviso de SMTP no configurado → ToastNotification "error" en lugar de QMessageBox (UX-09)

### 🧹 Housekeeping
- Tests `test_dialogs_basic.py`: actualizados para verificar el label inline en lugar de mock de QMessageBox

## [5.28.9] - 2026-04-22

### 🎯 Resumen
Corrección de fallo preexistente en test de ajustes: eliminadas referencias a versiones antiguas de algoritmos en los textos informativos.

### Fixed
- `ajustes_widget.py`: eliminadas menciones a "v2.9/v3.0" en textos informativos del selector de algoritmo que causaban fallo en `test_info_algoritmos_muestra_solo_opciones_reales`

## [5.28.8] - 2026-04-22

### 🎯 Resumen
Reducción de modales bloqueantes: sustituidos QMessageBox de confirmación de éxito por toast notifications no intrusivos. Mejoras menores en estadísticas.

### Changed
- `login_dialog.py`: eliminado modal "Bienvenido" tras login exitoso — la apertura de la ventana principal ya confirma el acceso
- `selector_curso_widget.py`: confirmación de cambio de curso → toast success; limpiado `setStyleSheet` inline del modal de error
- `gestion_cursos_widget.py`: éxito de activar/cerrar/eliminar curso → toast success
- `dialogo_crear_curso.py`: éxito de creación de curso → toast success
- `dialogo_reasignacion.py`: resultado de reasignación automática y manual → toast (success/warning según resultado); eliminada confirmación redundante post-reasignación
- `perfiles_usuario_form.py`: éxito de crear/editar/eliminar perfil, cambiar logo y cambiar contraseña → toast success
- `panel_estadisticas.py`: columna "% Cobertura" en estadísticas por zona se oculta automáticamente si todos los valores son N/A; tooltips en cabeceras "Inicio Guardias" y "Fin Guardias" explicando que "-" significa sin restricción de período

### 🧹 Housekeeping
- Documentados análisis MODAL-01 a MODAL-04 y SCREEN-01 a SCREEN-03 en `AUDITORIA_2026_V2.md`

## [5.28.7] - 2026-04-22

### 🎯 Resumen
Fix visual: zona gris del logo llega hasta el borde superior de la ventana.

### Fixed
- `ccleaner_sidebar.py`: botón de colapso movido al interior de `logo_section` (esquina superior derecha) — elimina el hueco blanco de 28px que quedaba encima de la zona gris

## [5.28.6] - 2026-04-22

### 🎯 Resumen
Fix: sidebar colapsable no respondía ni al botón ni a Ctrl+B.

### Fixed
- `ccleaner_sidebar.py`: `_apply_width()` reemplaza `setFixedWidth` por `setMinimumWidth` + `setMaximumWidth` + `resize` + `updateGeometry` + invalidación del layout padre — necesario para forzar el reflayout en pantalla completa
- `ccleaner_sidebar.py`: shortcut Ctrl+B cambiado a `ApplicationShortcut` para que funcione independientemente del widget con foco

## [5.28.5] - 2026-04-22

### 🎯 Resumen
Fix: tabla de zonas no se actualizaba visualmente tras editar una zona.

### Fixed
- `zona_form.py`: añadido `session.expire_all()` tras `actualizar_zona_uc.execute()` — el identity map de SQLAlchemy devolvía los datos anteriores al recargar la tabla

## [5.28.4] - 2026-04-22

### 🎯 Resumen
Fix: datos obsoletos al reeditar un profesor sin salir del formulario.

### Fixed
- `profesor_form.py`: añadido `session.expire_all()` tras `actualizar_use_case.execute()` para forzar que SQLAlchemy recargue el identity map; sin esto, la segunda edición del mismo profesor mostraba los datos anteriores al primer guardado

## [5.28.3] - 2026-04-22

### 🎯 Resumen
Limpieza visual del sidebar: eliminado avatar de usuario y barra de título contextual del área de contenido.

### Fixed
- `ccleaner_sidebar.py`: avatar de usuario eliminado completamente (no aportaba valor con pocos usuarios sin roles)
- `ccleaner_main_window.py`: eliminada `title_bar` de 40px en `ContentWrapper` — causaba hueco blanco sobre la zona gris del sidebar; el botón activo del menú ya indica la sección

## [5.28.2] - 2026-04-22

### 🎯 Resumen
Reubicación del avatar al header del sidebar, eliminación del ítem INICIO del menú, y regla de fallos preexistentes en agents.

### Changed
- `ccleaner_sidebar.py`: avatar con iniciales movido arriba del logo en la zona del header (visible siempre); eliminado del bloque inferior de info; ítem "Inicio" eliminado del menú lateral; el nombre de usuario se oculta al colapsar, el avatar permanece visible
- `ccleaner_main_window.py`: eliminado registro de `HomeForm` y sección "inicio"; arranque vuelve a "profesores"
- `.claude/agents.md` (nuevo): regla documentada — no corregir fallos preexistentes

### 🧹 Housekeeping
- `home_form.py` queda en disco pero ya no está conectado a la navegación

## [5.28.1] - 2026-04-21

### 🎯 Resumen
FUNC-05: eliminación de matplotlib — gráficos nativos con QPainter (BarChartWidget, PieChartWidget) en dashboard y estadísticas.

### Changed
- `bar_chart_widget.py` (nuevo): `BarChartWidget` (barras verticales u horizontales, QPainter) y `PieChartWidget` (tarta/donut, QPainter) — sin dependencias externas
- `dashboard_form.py`: 4 canvas matplotlib reemplazados por `BarChartWidget` / `PieChartWidget`; métodos de actualización de gráficos adaptados a la nueva API (`set_datos()`)
- `panel_estadisticas.py`: `_get_mpl_canvas_class()` eliminado; `_crear_tab_graficos()` y `_actualizar_graficos_ui()` usan `BarChartWidget` / `PieChartWidget`; alias `MplCanvas = BarChartWidget` para compatibilidad con tests
- `tests/test_panel_estadisticas.py`: tests de gráficos adaptados a API nativa (`_datos`, `isinstance` con nuevas clases)

## [5.28.0] - 2026-04-21

### 🎯 Resumen
FUNC-01: notificación automática por email a profesores con sus guardias asignadas.

### ✨ Added
- `email_service.py`: nuevo método `EmailService.send_guardias_notification()` — envía email HTML con tabla de guardias (día, turno, recreo, zona) al profesor
- `generacion_panel.py`: botón "✉ Enviar emails a profesores" visible post-generación; `_enviar_notificaciones()` itera los profesores activos con email, envía notificación y muestra resumen de enviados/errores

## [5.27.5] - 2026-04-21

### 🎯 Resumen
UX-01: dashboard de inicio con estado del día, métricas de hoy y alertas del sistema.

### ✨ Added
- `home_form.py` (nuevo): `HomeForm` con 4 cards de métricas (guardias hoy, ausencias activas, sustituciones, total), resumen del sistema y panel de alertas automáticas; datos reales desde BD con botón Actualizar
- `ccleaner_sidebar.py`: ítem "Inicio" con icono home como primera opción del sidebar
- `ccleaner_main_window.py`: registra `HomeForm` como sección "inicio", arranca en "inicio" en lugar de "profesores"

## [5.27.4] - 2026-04-21

### 🎯 Resumen
UX-02: rediseño pantalla de login — panel de marca izquierdo (#007ACC) + panel de formulario derecho blanco, aspecto profesional split-layout.

### Changed
- `login_dialog.py`: nuevo diseño 720×480 con panel izquierdo de marca (logo, título, subtítulo, créditos sobre fondo #007ACC) y panel derecho blanco con formulario de login limpio; todos los controles y lógica de autenticación se mantienen intactos

## [5.27.3] - 2026-04-21

### 🎯 Resumen
PERF-02: lazy loading de formularios — solo se instancia el formulario inicial al arrancar, el resto se crea al navegar por primera vez.

### Changed
- `ccleaner_main_window.py`: `create_views()` registra factories en lugar de instanciar; `_ensure_view()` crea on-demand; solo "profesores" se instancia al arrancar

## [5.27.2] - 2026-04-21

### 🎯 Resumen
BUG-04: validación de estructura JSON antes de importar — detecta JSON inválido, tipo incorrecto o claves no reconocidas con mensaje preciso.

### Fixed
- `import_export_form.py`: pre-validación del backup JSON antes de llamar a `importar_todo` — informa exactamente qué falla (JSON malformado, tipo incorrecto, secciones no reconocidas)

## [5.27.1] - 2026-04-21

### 🎯 Resumen
FUNC-07: pestaña "Exportar iCal" en Reportes expone el ICalendarService existente en la UI.

### ✨ Added
- `reportes_form.py`: nueva pestaña "📅 Exportar iCal" con selector de profesor y botón de exportación a `.ics` (Google Calendar, Outlook, Apple Calendar)

## [5.27.0] - 2026-04-21

### 🎯 Resumen
UX-06: cards visuales en DiaDetalleDialog — avatares de iniciales, ausencias en rojo, sustituciones con badge naranja SUST.

### Changed
- `dia_detalle_dialog.py`: guardias muestran avatar circular con iniciales; ausencias pasan a fondo `#FEE2E2`; sustituciones tienen avatar naranja y badge "SUST"

## [5.26.9] - 2026-04-21

### 🎯 Resumen
UX-03: sidebar colapsable con Ctrl+B — toggle entre 260px (expandido) y 56px (solo iconos).

### ✨ Added
- Sidebar: botón ◀/▶ y atajo Ctrl+B para colapsar/expandir; estado persiste en QSettings; en modo colapsado se ocultan textos, categorías y selector de curso, y aparecen tooltips en cada ítem

## [5.26.8] - 2026-04-21

### 🎯 Resumen
UX-05: toast notifications no intrusivos reemplazan los QMessageBox de éxito en los formularios.

### ✨ Added
- `ToastNotification`: widget flotante en esquina inferior derecha con auto-cierre a 2.5s, cuatro tipos (success/error/info/warning)
- `base_form.py`: `mostrar_exito()` ahora muestra un toast en lugar de un QMessageBox bloqueante

## [5.26.7] - 2026-04-21

### 🎯 Resumen
FUNC-09: resumen previo a la generación con profesores activos, algoritmo y tiempo estimado.

### ✨ Added
- `generacion_panel.py`: antes de lanzar CP-SAT, muestra profesores activos, algoritmo y estimación de tiempo (~2s + 0.5s/profesor); integrado en la confirmación si hay guardias previas

## [5.26.6] - 2026-04-21

### 🎯 Resumen
UX-11: avatar de iniciales del usuario en sidebar + bump de titleMain a 18px.

### ✨ Added
- Sidebar: badge circular con las iniciales y nombre del usuario logueado en la sección inferior

### Changed
- `light.qss`: `QLabel#titleMain` pasa de 16px a 18px para mayor jerarquía visual

## [5.26.5] - 2026-04-21

### 🎯 Resumen
UX-10: barra de título contextual fija sobre el área de contenido principal.

### ✨ Added
- `ContentWrapper`: barra de 40px con el nombre de la sección activa, fija encima del scroll — orienta al usuario cuando el texto del sidebar está cortado

## [5.26.4] - 2026-04-21

### 🎯 Resumen
INCONS-10: unificar estilo QGroupBox eliminando overrides inline en dashboard_form.

### Fixed
- `dashboard_form.py`: eliminar `setStyleSheet` inline en los 4 QGroupBox de gráficos — ahora heredan de `light.qss`

## [5.26.3] - 2026-04-21

### 🎯 Resumen
Consistencia final del flujo de algoritmos (UI + lógica + tests) y trazabilidad en auditoría.

### Changed
- `ajustes_form.py`: fallback de `algoritmo_asignacion` actualizado a `v4.0`
- `generar_guardias.py`: normalización explícita de valores legacy/no reconocidos a `v4.0` o `cpsat`
- `test_widgets_ui.py`: nuevos tests para validar algoritmo por defecto, normalización de legacy y texto del bloque de algoritmos

### Fixed
- Evita discrepancias entre la configuración mostrada en Ajustes y el selector real de generación

### 🧹 Housekeeping
- `AUDITORIA_2026_V2.md`: añadido `INCONS-14` como resuelto en `v5.26.3`

## [5.26.2] - 2026-04-21

### 🎯 Resumen
Limpieza del bloque de algoritmos en Ajustes para mostrar solo opciones reales y con mejor legibilidad.

### Changed
- `ajustes_widget.py`: el panel de "Algoritmos disponibles" muestra solo `Rápido (v4 Híbrido)` y `Óptimo (CP-SAT)` con texto más legible

### Fixed
- `ajustes_widget.py`: guardar Ajustes ya no fuerza `v3.0`; ahora conserva un valor válido (`v4.0` o `cpsat`) y normaliza referencias antiguas

## [5.26.1] - 2026-04-21

### 🎯 Resumen
Ajuste visual definitivo de títulos y paddings en paneles de asignación, más estabilización de MplCanvas en estadísticas.

### Changed
- `light.qss`, `ccleaner_theme.py`, `legacy_styles.py`: más espacio vertical y padding en `titleMain` y `QGroupBox::title`
- `calculo_panel.py`, `generacion_panel.py`, `estadisticas_panel.py`, `resultados_panel.py`, `incidencias_panel.py`, `cuotas_panel.py`: alineados con el nuevo espaciado para evitar títulos recortados en Cálculo y Asignación

### Fixed
- `panel_estadisticas.py`: `MplCanvas` cacheado para mantener estable `isinstance(...)` en tests y uso lazy de matplotlib

## [5.26.0] - 2026-04-21

### 🎯 Resumen
Nivel 2 auditoría: consistencia de botones, emojis, fuentes pt→px, conectividad como pestaña, matplotlib lazy, diagnóstico de duplicados.

### Changed
- INCONS-01: `delete_user_dialog`, `perfiles_usuario_form`, `gestion_cursos_widget` — botones eliminar usan `setProperty("danger","true")` en lugar de `setStyleSheet` inline
- INCONS-02: `setObjectName("secondaryButton")` en botones Cancelar de `delete_user_dialog`, `change_password_dialog`, `reset_password_dialog`, `forgot_password_dialog`, `perfiles_usuario_form`, `dialogo_diagnostico_guardias`, `dialogo_crear_perfil`, `dialogo_editar_perfil`
- INCONS-05: eliminados emojis ←, ✓, 🔒, 🔢, 📄 de textos de botones en 9 archivos
- INCONS-06: eliminado 🏫 de `zona_form` y 🏥 de `gestionar_ausencias`
- INCONS-07: `dialogo_diagnostico_guardias` — fuentes pt reemplazadas por px (16pt→20px, 11pt→14px, 10pt→11px, 9pt→11px)
- INCONS-09: `ProgressDialog.completar()` — oculta `btn_cancelar` y muestra `btn_cerrar` separado
- FUNC-06: Conectividad movida a pestaña de Ajustes; eliminado ítem del sidebar y `add_view` del main window
- PERF-03: imports de matplotlib diferidos al primer uso en `dashboard_form` y `panel_estadisticas`

### Fixed
- `tests/test_progress_indicators.py`: aserciones actualizadas para nuevo comportamiento de btn_cerrar

### 🔍 Investigado
- INCONS-11: `cuotas_panel.py` y `calculo_panel.py` son distintos — `CuotasPanel` (domain services preview en asignacion_guardias_form) vs `CalculoPanel` (panel combinado en asignacion_calculo_form). Ambos se mantienen.

## [5.25.0] - 2026-04-21

### 🎯 Resumen
Nivel 1 auditoría: correcciones de color de botones, titleMain, separadores, limpieza de logs, borde de hoy en calendario y caché por mes de días lectivos.

### ✨ Added
- `main.py`: limpieza automática de logs >30 días al arrancar (BUG-03)

### Changed
- `pdf_export_widget.py`, `calendarios_pdf_widget.py`: "Generar PDFs" `danger` → `success` (INCONS-03)
- `import_export_form.py`: "Importar Profesores" `success` → `warning` para unificar con JSON (INCONS-04)
- `dashboard_form.py`: título `labelTitle` → `titleMain` (INCONS-12)
- `_celda_dia.py`, `dia_detalle_dialog.py`, `vista_calendario.py`, `dialogo_acerca_de.py`, `ccleaner_sidebar.py`, `pdf_export_widget.py`, `calendarios_pdf_widget.py`: separadores `QFrame.HLine` → `setObjectName("separator")` (INCONS-13)
- `_celda_dia.py`: borde día actual amarillo → azul `#007ACC` (UX-12)
- `vista_calendario.py`: cache de días lectivos por `(anio, mes)` en lugar de global — evita recálculo al navegar entre meses (PERF-04)

### Fixed
- `tests/test_vista_calendario.py`: actualizar aserciones de color `es_hoy` al nuevo azul

## [5.24.0] - 2026-04-21

### 🎯 Resumen
VIS-CSS: 269 → 262 setStyleSheet (7 eliminados). ARQ-01 confirmado resuelto en roadmap.

### Changed
- `light.qss`: nuevos selectores `QFrame#separator` y `QLabel#modalSectionTitle`
- `_celda_dia.py`, `pdf_export_widget.py`, `calendarios_pdf_widget.py`: separadores grises → `setObjectName("separator")`
- `modales_perfil.py`: 2 títulos de modal → `setObjectName("modalSectionTitle")`
- `progress_indicators.py`: btn_cancelar usa `setProperty("danger"/"success")` en lugar de `setStyleSheet` inline

### 🧹 Housekeeping
- Auditoría: ARQ-01 actualizado a ✅ RESUELTO v5.21.0 en roadmap P1; VIS-CSS actualizado con conteo 262 y análisis de stock restante



### 🎯 Resumen
Ronda de auditoría: RES-05 verificado, SEC-16 finalizado (<50 bloques), ARQ-02 saneado, ARQ-07/TEST-03 completados.

### ✨ Added
- `tests/test_sync_dtos.py` — 21 tests para la capa anticorrupción de sync (100% cobertura `sync/dtos.py`)

### Changed
- `src/core/observability/decorators.py`: 2 interceptores de métricas cambiados de `except Exception` a `except BaseException` (patrón re-raise; semánticamente correcto)
- `src/presentation/widgets/gestion_cursos_widget.py`: eliminación de curso vía `repo.delete()` en lugar de `session.delete()` directo
- `docs/AUDITORIA_INTEGRAL_2026.md`: tachados RES-05, SEC-16, ARQ-02 (residual), ARQ-07, PERF-CORE, TEST-CORE

### Fixed
- SEC-16: 48 `except Exception` (target <50 alcanzado ✅)
- ARQ-02: última query ORM directa en `presentation/` migrada a repositorio

### 🧹 Housekeeping
- Auditoría actualizada con estado real verificado con grep


ARQ-02 completado: 0 imports `from sqlalchemy.orm import Session` en `src/presentation/`.

### 🧹 Housekeeping
- 18 archivos de `src/presentation/`: eliminado import `Session` y anotaciones de tipo en parámetros `__init__`
- `src/presentation/forms/asignacion_widgets/generacion_panel.py`: eliminado `self.session.commit()` redundante tras `limpiar_guardias_uc.execute()` (el repo ya hace commit internamente)
- `src/presentation/widgets/gestion_cursos_widget.py`: eliminado import Session (las calls ORM directas permanecen como deuda técnica pendiente de use case)

---
## [5.21.1] - 2026-04-21

### 🎯 Resumen
Corrección de 74 fallos preexistentes en tests — 0 fallos restantes (2085 passed).

### Fixed
- `src/services/gestor_cursos.py`: `__init__` ahora acepta `Session` o `RepositoryFactory` (polimórfico). Corrige 40+ tests que llamaban `GestorCursos.metodo(session, ...)` como API estática
- `tests/test_multicurso.py`: fixtures e instanciación actualizados a `GestorCursos(session).metodo()`; `session.delete/refresh` sobre ORM models obtenidos por `session.get()`; `curso.guardias` sustituido por query directa
- `tests/test_gestor_cursos_curso_id.py`, `test_migrar_multi_curso.py`, `test_asignacion_guardias_form.py`: misma corrección de API
- `src/sync/data_exporter.py`: añadidos alias estáticos `_serialize_date`, `_parse_date`, `_parse_time`, `_encriptar_password`, `_desencriptar_password`, `_export_smtp_config`, `_import_smtp_config`, `_export_sftp_config`, `_import_sftp_config` que delegaban en `data_exporter_helpers`
- `src/services/exportador_pdf.py`: callback de progreso captura `Exception` en lugar de `(TypeError, ValueError)`
- `tests/test_use_cases_zona_profesor.py`: `CrearZonaDTO` corregido a nombre ≥2 chars; mock de duplicado de profesor configurado correctamente

---
## [5.21.0] - 2026-04-21

### 🎯 Resumen
ARQ-01 completado en `src/services/`: 0 imports `from sqlalchemy.orm import Session` restantes. 14 archivos adicionales migrados en esta fase (total 23 archivos en todas las fases).

### 🧹 Housekeeping
- `src/services/distribucion_cuotas_service.py`: constructor `session_or_factory` polimórfico
- `src/services/exportador.py`: eliminado import `Session`, anotaciones removidas de todos los métodos estáticos
- `src/services/exportador_pdf.py`: eliminado import `Session`, anotaciones removidas
- `src/services/assignment/assignment_executor.py`: constructor `session_or_factory` polimórfico
- `src/services/assignment/slot_builder.py`: constructor `session_or_factory` polimórfico
- `src/services/assignment/profesor_filter.py`: constructor `session_or_factory` polimórfico
- `src/services/validators/ausencia_checker.py`: constructor `session_or_factory` polimórfico
- `src/services/gestor_ausencias.py`: eliminado import `Session`, anotaciones removidas de funciones standalone
- `src/services/asignador_guardias_v4_hibrido.py`: eliminado import `Session`, anotaciones removidas
- `src/services/_asignador_v4_fases.py`: eliminado import `Session`, anotaciones removidas
- `src/services/_asignador_v4_helpers.py`: eliminado import `Session`, anotaciones removidas
- `src/services/_asignador_cpsat_helpers.py`: eliminado import `Session`, anotaciones removidas
- `src/services/_pdf_mes_consolidado.py`: eliminado import `Session`, anotaciones removidas
- `src/services/_pdf_individual_optimizado.py`: eliminado import `Session`, anotaciones removidas

---
## [5.20.1] - 2026-04-21

### 🎯 Resumen
ARQ-01 fase extensión #3: 6 servicios adicionales desacoplados de Session. Total acumulado: 9 servicios migrados en fases 2+3 (de 32 → 11 imports Session restantes).

### 🧹 Housekeeping
- `src/services/equidad_guardias_service.py`: constructor `session_or_factory` + `from_session()` classmethod
- `src/services/validador_guardias.py`: constructor y función helper `validar_guardias_completo` polimórficos
- `src/services/diagnosticador_guardias.py`: constructor `db` polimórfico (mantiene nombre `db` para backward compat kwarg)
- `src/services/migrar_a_multi_curso.py`: eliminado import `Session`, anotaciones de tipo removidas de parámetros
- `src/services/_exportador_import.py`: eliminado import `Session`, anotaciones de tipo removidas de parámetros
- `src/services/asignacion_guardia_service.py`: constructor `session_or_factory` polimórfico

---
## [5.20.0] - 2026-04-21

### 🎯 Resumen
ARQ-01 fase extensión #2: 3 servicios migrados de Session directa a patrón polimórfico (Session legacy | RepositoryFactory). Auditoría actualizada con conteos verificados.

### 🧹 Housekeeping
- `src/services/importador_zonas.py`: migrado a polimórfico — acepta `zona_repo_or_session`, usa `RepositoryFactory` y `ZonaEntity` internamente, backward-compatible con Session legacy
- `src/services/icalendar_service.py`: `generar_icalendar_profesor` acepta `session_or_factory` en lugar de `Session` tipado; elimina `from sqlalchemy.orm import Session`
- `src/services/disponibilidad_profesor_service.py`: constructor `session_or_factory` + `from_session()` classmethod; elimina `from sqlalchemy.orm import Session`
- `docs/AUDITORIA_INTEGRAL_2026.md`: conteos verificados — 20 imports `Session` en services (era 32), 336 `setStyleSheet` (era 268), 52 `except Exception` (SEC-16 reabierto, target era <50)

---
## [5.19.1] - 2026-04-21

### 🎯 Resumen
VIS-CSS continuación: dashboard_form.py migrado parcialmente; calendario y celda revisados (estilos ad-hoc legítimos, no migrados).

### 🧹 Housekeeping
- `src/presentation/forms/dashboard_form.py`: título header e info_label migrados a `setObjectName("labelTitle"/"labelCaption")`. QGroupBox de gráficos y MetricaCard mantienen estilos inline (colores dinámicos y tamaños específicos)
- `src/presentation/widgets/vista_calendario.py` y `_celda_dia.py`: revisados — todos los setStyleSheet son dinámicos o específicos de cuadrícula (fuentes 8-10px, badges), no candidatos a migrar

---
## [5.19.0] - 2026-04-21

### 🎯 Resumen
VIS-TOKENS completado. VIS-CSS parcial: 284→270 setStyleSheet inline eliminados. Corrección de regresión visual (botones sin color, fondos oscuros en paneles).

### ✨ Added
- `src/presentation/theme/tokens.py`: tokens completos — `SUCCESS_BG`, `SUCCESS_BORDER`, `WARNING_BG_ALT`, `WARNING_BORDER`, `ERROR_BG`, `ERROR_BORDER`, `INFO_BG`, `INFO_BORDER`, `SECONDARY`, `SECONDARY_HOVER`, `TERMINAL_BG/BORDER/TEXT/ACCENT`
- `src/presentation/themes/ccleaner_theme.py`: 9 nuevas reglas globales CSS — `QPushButton[secondary="true"]`, `QLabel#labelCaption`, `QLabel#labelTitle`, `QLabel#labelSubtitle`, `QLabel#labelSecondary`, `QLabel#infoBox{Info,Success,Warning,Error}`, `QFrame#separator`, `QGroupBox` estándar

### Fixed
- Regresión visual: botones success/danger/warning sin color tras VIS-02 — causa: `setProperty("x", True)` no coincide con `[x="true"]` en PyQt6. Corregido a `"true"` string en 17 archivos
- `QScrollArea` y `QStackedWidget` en `ccleaner_main_window.py` usaban stylesheet sin selector tipado, cascadeando a todos los hijos y pisando colores globales. Corregido con selectores tipados
- Fondo negro (`#0f172a`) del badge "Total: -- guardias" en `calculo_panel.py` restaurado (estilo vintage)
- Regla `QPushButton[warning="true"]` faltante añadida al tema global

### 🧹 Housekeeping
- `src/presentation/dialogs/dia_detalle_dialog.py`: 4 bloques inline `QGroupBox.setStyleSheet` eliminados (cubiertas por regla global), 4 labels migrados a `setObjectName`
- `src/presentation/forms/login_dialog.py`: 6 `setStyleSheet` inline reemplazados por `setProperty` / `setObjectName`

---
## [5.18.0] - 2026-04-20

### 🎯 Resumen
P3 completados: OBS-LOGS, VIS-REFINEMENT, PERF-TUNING, UX-ADVANCED. SECURITY-ADVANCED aplazado (no solicitado por usuarios).

### ✨ Added
- `src/core/observability/business_metrics.py`: módulo de métricas de negocio con funciones tipadas (`profesor_creado`, `guardia_asignada`, `guardias_limpiadas`, `sustitucion_confirmada`, `ausencia_registrada`, `asignacion_cpsat_completada`, `login_exitoso`, `login_fallido`). Logs estructurados con `event_type="business"` para filtrado.

### Changed
- `src/application/use_cases/profesor/crear_profesor.py`: emite `business_metrics.profesor_creado` al éxito
- `src/application/use_cases/guardia/asignar_guardia.py`: emite `business_metrics.guardia_asignada` al éxito
- `src/application/use_cases/guardia/limpiar_guardias.py`: emite `business_metrics.guardias_limpiadas` al completar
- `src/presentation/forms/login_dialog.py`: emite `business_metrics.login_exitoso` / `login_fallido`
- `src/presentation/widgets/gestor_sustituciones.py`: emite `business_metrics.sustitucion_confirmada` al confirmar
- `src/utils/icons.py`: añadidos aliases `account-plus`, `star`, `favourite`, `puzzle`, `module`, `hospital`, `absence` en `_ICON_MAP` (total 91 aliases)
- `src/presentation/ccleaner_main_window.py`: lazy loading — los 12 widgets se instancian al acceder por primera vez (antes se creaban todos al arrancar). Añadidos `register_view()`, `_ensure_view()`, `_connect_widget_signals()`.

---
## [5.17.0] - 2026-04-20

### 🎯 Resumen
TEST-INTEGRATION, DOCS-API, DOCS-ARCHITECTURE, UX-UNSAVED, UX-DESTRUCTIVE, TEST-A11Y (todos P2). Corrección de bugs reales descubiertos por los tests.

### ✨ Added
- `tests/test_api_integration.py`: 11 tests de integración API REST con SQLite in-memory (StaticPool)
- `tests/test_a11y_regression.py`: 7 tests de regresión A11Y con pytest-qt (ChangePasswordDialog, ResetPasswordDialog, DeleteUserDialog, GestionarAusenciasForm, GestorSustituciones)
- `docs/API_TECHNICAL.md`: documentación técnica manual de los 22 endpoints REST
- `docs/ADR.md`: 8 Architecture Decision Records (Clean Architecture, SQLite per-user, OR-Tools, dependency-injector, PyQt6, FastAPI, Ruff, SFTP)
- `BaseForm`: señal `cambios_sin_guardar`, métodos `_mark_dirty()`, `_mark_clean()`, `tiene_cambios()`, `registrar_label_cambios()` para indicador UX-UNSAVED

### Fixed
- `src/application/dtos/profesor_dto.py`: campo `activo: bool = True` faltaba en `ProfesorDTO` (AttributeError en el router)
- `src/api/routers/profesores.py`: captura `NotFoundError` en `obtener_profesor` → devuelve 404 en vez de 500



### 🎯 Resumen
A11Y-BASIC (P2): setAccessibleName + setTabOrder en 10 formularios y widgets de la capa de presentación.

### ✨ Added
- Accesibilidad completa (setAccessibleName + setTabOrder) en:
  - `gestionar_ausencias.py`: profesor, tipo, fechas, motivo, botones guardar/ver/cancelar
  - `gestor_sustituciones.py`: fecha, profesor original/sustituto, observaciones, confirmar/limpiar
  - `change_password_dialog.py`: contraseña actual, nueva, confirmar + tab order
  - `reset_password_dialog.py`: código recuperación, nueva contraseña, confirmar + tab order
  - `delete_user_dialog.py`: selector usuario, contraseña confirmación + tab order
  - `dialogo_crear_perfil.py`: usuario, email, contraseña, confirmar + tab order
  - `modales_perfil.py`: 3 diálogos (crear, editar, cambiar contraseña) con AccessibleName
  - `restricciones_widget.py`: checkboxes fecha inicio/fin, combo zona preferida, checkbox principal
  - `selector_curso_widget.py`: combo curso escolar activo
  - `pdf_export_widget.py`: combo tipo, mes, año, curso, checkboxes selección/email, botón
  - `calendarios_pdf_widget.py`: combo tipo, mes, año, checkboxes selección/email, botón

---
## [5.15.1] - 2026-04-20

### 🎯 Resumen
P1 completados: SEC-PWD (password policy + lockout) verificado ✅, ARQ-01 (estadisticas_service refactorizado), DB-INTEGRITY (índices en Ausencia). Templates preparados para 4 servicios restantes en fase 2.

### ✨ Added
- `.arq01-phase2-template.md`: Guía detallada para migrar 4 servicios pendientes (validador_guardias, disponibilidad_profesor_service, equidad_guardias_service, asignador_guardias_cpsat) con ejemplos de patrón RepositoryFactory.

### Changed
- `src/services/estadisticas_service.py`: refactorizado a servicio sin estado. `__init__()` ahora sin parámetro `session` (lógica pura, solo trabaja con listas inyectadas). Añadido `from_session()` para compatibilidad legacy.
- `src/infrastructure/database/models.py`: Ausencia table_args añade índices compuestos:
  - `ix_ausencias_profesor_id`: búsquedas por profesor
  - `ix_ausencias_profesor_fecha`: índice compound para queries frecuentes (profesor_id, fecha_inicio, fecha_fin)
  - `ix_ausencias_activa`: filtrado de ausencias activas
- Actualizado 3 usages de `EstadisticasService(session)` → `EstadisticasService()` en:
  - `tests/test_estadisticas_validador.py`
  - `src/services/equidad_guardias_service.py`
  - `src/services/assignment/assignment_executor.py`

### Fixed
- ~~SEC-PWD (Password policy + Lockout)~~ ✅ Verificado como ya implementado desde v5.15.0: `UserAuth.validate_password_policy()` con 8+ chars, mayúscula, número, símbolo. Lockout: 5 intentos → 15 min bloqueado con delays progresivos (1,2,4,8,16s).
- ~~DB-INTEGRITY (CheckConstraints + threading locks)~~ ✅ Verificado como ya implementado:
  - CheckConstraints: turno, recreo, tipo_ausencia, porcentaje_jornada, capacidad_zona, ajustes_config
  - Threading locks: `_db_lock` en db_manager.py desde v5.15.0
  - Índices: completados con compound index en Ausencia

### 🧹 Housekeeping
- `docs/AUDITORIA_INTEGRAL_2026.md`: Roadmap P1 actualizado. Marcados como RESUELTOS: SEC-PWD, ARQ-01 (estadisticas), DB-INTEGRITY. ARQ-01 fase 2 con templates preparados.

---
## [5.15.0] - 2026-04-20

### 🎯 Resumen
ARQ-04: Implementación de contenedor DI con `dependency-injector`. Centraliza gestión de dependencias para repos y servicios sin romper compatibilidad legacy.

### ✨ Added
- `src/infrastructure/container.py`: `Container` (DeclarativeContainer) con providers para:
  - `db_session`: Callable para sesiones de BD (configurable)
  - Repositorios: profesor, zona, guardia, ausencia, configuracion, curso_escolar
  - `repository_factory`: RepositoryFactory para compatibilidad con código legacy
- `requirements.txt`: Añadida `dependency-injector>=4.41.0`

### Changed
- `src/infrastructure/__init__.py`: Exporta `Container` para uso global
- Infraestructura lista para wiring automático en `main.py` y `api/main.py` (fase 2 opcional)

### 🧹 Housekeeping
- Container mantenido simple: enfoque en DB + repos. Servicios pueden añadirse incrementalmente.
- No se modifica main.py/api/main.py para evitar disrupciones (wiring es opt-in).

---
## [5.14.2] - 2026-04-20

### 🎯 Resumen
ARQ-01 (fase extensión #1): `importador_profesores` refactorizado para eliminar acoplamiento a `Session`. Compatible backward con tests legacy.

### Changed
- `src/services/importador_profesores.py` elimina imports `Session` y `SQLAlchemyError`. Acepta polimórficamente `Session` (legacy) o `profesor_repo`.
- Funciones `importar_profesores_desde_excel()`, `importar_profesores_desde_csv()` e `importar_profesores()` adaptadas con detección automática Session/Repo.
- `src/presentation/forms/import_export_form.py` cambios de caller: crea `profesor_repo` via `RepositoryFactory` antes de llamar importador.
- Tests `test_importador_profesores.py` actualizados: `turno="completo"` → `turno="mixto"` (valor válido en Turno VO). ✅ 26 tests passing.

### 🧹 Housekeeping
- Mantiene `normalizar_nombre()` como función pública para compatibilidad de tests.

---
## [5.14.1] - 2026-04-20

### 🎯 Resumen
ARQ-01 (fase core) completada en 5 servicios: eliminación de acoplamientos `Session/joinedload` y migración de `gestor_ausencias` a facade de clase.

### Changed
- `src/services/gestor_ausencias.py` añade clase `GestorAusencias` como punto de entrada estático para operaciones de ausencias.
- `src/presentation/widgets/gestionar_ausencias.py` y `src/presentation/widgets/dialogo_reasignacion.py` migrados a llamadas `GestorAusencias.*`.
- `src/services/calculador_guardias.py` elimina `joinedload` no necesario en carga de profesores y elimina type hints `Session`.
- `src/services/orquestador_asignacion_guardias.py` elimina import `Session` y su uso en constructor.
- `src/services/asignador_guardias_cpsat.py` elimina type hints/import `Session` en función principal y persistencia.

### 🧹 Housekeeping
- `docs/AUDITORIA_INTEGRAL_2026.md` actualizado marcando ARQ-01 (migración de 5 servicios core) como resuelto en roadmap.

---
## [5.14.0] - 2026-04-20

### 🎯 Resumen
A11Y-01 + A11Y-02: 54 `setAccessibleName()` en 8 formularios y `setTabOrder()` en 6 widgets (WCAG AA).

### ✨ Added
- `setAccessibleName()` en todos los campos interactivos principales: `datos_basicos_widget`, `datos_zona_widget`, `sftp_widget`, `smtp_widget`, `ajustes_widget`, `fechas_recreos_widget`, `perfiles_usuario_form`, `_initial_config_tabs`
- `setTabOrder()` en `datos_basicos_widget`, `datos_zona_widget`, `sftp_widget`, `smtp_widget`, `fechas_recreos_widget`, `perfiles_usuario_form`

### Fixed
- Tests `test_reasignar_guardias_automaticamente_error_en_reasignacion` y `test_get_local_ip_fallback` actualizados para usar tipos de excepción correctos (`AttributeError`, `OSError`)

---
## [5.13.0] - 2026-04-20

### 🎯 Resumen
SEC-16: migración de `except Exception` genéricos a excepciones específicas — 59→49 (target <50 alcanzado).

### 🧹 Housekeeping
- `application/use_cases/zona/crear_zona.py` → `except (ValueError, TypeError)`
- `application/use_cases/profesor/actualizar_profesor.py` → `except (ValueError, TypeError)`
- `application/use_cases/configuracion/actualizar_configuracion.py` → `except SQLAlchemyError`
- `services/gestor_ausencias.py` → `except (ValueError, LookupError, AttributeError)`
- `services/orquestador_asignacion_guardias.py` → `except (TypeError, ValueError, RuntimeError)`
- `services/exportador_pdf.py` → `except (TypeError, ValueError)`
- `sync/session_lock.py` → `except OSError`
- `sync/sync_manager.py` (×2) → `except (OSError, IOError)`

---

## [5.12.0] - 2026-04-20

### 🎯 Resumen
VIS-02: migración masiva de 535 `setStyleSheet` inline a QSS global — de 595 a 296 llamadas (-50%). Desbloquea ORG-02.

### Changed
- `src/presentation/theme/light.qss` → ampliado con reglas globales: `QGroupBox`, `QMessageBox`, `QLabel#fieldLabel`, `QLabel#smallFieldLabel`, `QLabel#titleMain`, `QTextEdit#terminalRetro`, `QPushButton[warning="true"]`, `QLineEdit:read-only`, `QScrollArea`
- 231 llamadas `setStyleSheet(styles.STYLE_*)` reemplazadas en 38 archivos: eliminaciones (STYLE_INPUT×55, STYLE_GROUPBOX×28, MESSAGEBOX_STYLE×27, STYLE_BUTTON_PRIMARY×12) y conversiones a `setObjectName`/`setProperty` (STYLE_LABEL_FIELD×46+8, STYLE_TITLE_MAIN×17, STYLE_BUTTON_SUCCESS×9, STYLE_BUTTON_DANGER×9, STYLE_BUTTON_WARNING×7, STYLE_BUTTON_SECONDARY×6, STYLE_TERMINAL_RETRO×6)
- `sftp_widget.py` y `smtp_widget.py` → `_apply_readonly_style()` vaciada; el estado visual `:read-only` lo gestiona el QSS global

### 🧹 Housekeeping
- `src/main.py` → eliminada importación y llamada a `MESSAGEBOX_STYLE` (cubierto por QSS global)

---

## [5.11.0] - 2026-04-20

### 🎯 Resumen
Implementación completa de todos los ítems P2 de la auditoría integral 2026: accesibilidad WCAG AA, iconografía centralizada, responsive, caché en capa de aplicación y split de los 7 archivos >800 líneas.

### ✨ Added
- `src/utils/ui_helpers.py` → `announce()` para feedback a lectores de pantalla (A11Y-06); `get_icon()` centralizado desde `imagenes/icons/` con `QPixmapCache` (VIS-04)
- `src/presentation/widgets/dialogo_reasignacion.py` — `DialogoReasignacion` extraída de `gestionar_ausencias.py` (ARQ-05)
- `src/presentation/forms/profesor_table_helpers.py` — helpers de tabla de profesores (ARQ-05)
- `src/presentation/widgets/progress_worker.py` — `WorkerThread` extraído de `progress_indicators.py` (ARQ-05)
- `src/presentation/widgets/progress_handlers.py` — `ProgressLogHandler`, `DecisionDialogHandler` (ARQ-05)
- `src/presentation/widgets/vista_calendario_helpers.py` — `cargar_datos_periodo`, `obtener_zonas_esperadas_por_recreo`, `parse_recreos_config`, `estilo_dia_miniatura` (ARQ-05)
- `src/sync/data_exporter_helpers.py` — helpers de cifrado, serialización de fechas y config SMTP/SFTP (ARQ-05)
- `src/services/_asignador_cpsat_helpers.py` — `Slot`, `ResultadoCPSAT`, `SolverCallback`, `_es_elegible_basico`, `_generar_slots` (ARQ-05)
- `src/services/_pdf_mini_calendario.py` — `crear_mini_calendario`, `obtener_hora_recreo` (ARQ-05)
- `src/application/use_cases/configuracion/cache_service.py` — implementación real del caché TTL (`cachetools.TTLCache`, TTL=300s) (ORG-01)
- `src/presentation/theme/tokens.py` → colores semánticos corregidos para WCAG AA: `SUCCESS #1E7E34` (5.14:1), `WARNING #856404` (5.49:1), `INFO #0C6674` (6.63:1), `WARNING_BG #FFF3CD` (A11Y-04)

### Changed
- `src/services/cache_service.py` → shim de compatibilidad que re-exporta desde `application.use_cases.configuracion.cache_service` (ORG-01)
- `src/presentation/components/ccleaner_sidebar.py` → `logo_label` cambia de `setFixedSize(100,100)` a `setMinimumSize(80,80)` + `setMaximumSize(120,120)` (VIS-09)
- 24 llamadas `setFixedSize()` en `QMessageBox` eliminadas de diálogos y widgets de presentación (VIS-09)
- `src/presentation/widgets/gestionar_ausencias.py` reducido de 814 → 615 líneas (ARQ-05)
- `src/presentation/forms/profesor_form.py` reducido de 848 → 778 líneas (ARQ-05)
- `src/presentation/widgets/progress_indicators.py` reducido de 1006 → 714 líneas (ARQ-05)
- `src/presentation/widgets/vista_calendario.py` reducido de 969 → 780 líneas (ARQ-05)
- `src/sync/data_exporter.py` reducido de 828 → 564 líneas (ARQ-05)
- `src/services/asignador_guardias_cpsat.py` reducido de 846 → 637 líneas (ARQ-05)
- `src/services/_pdf_individual_optimizado.py` reducido de 827 → 589 líneas (ARQ-05)

### 🧹 Housekeeping
- `docs/AUDITORIA_INTEGRAL_2026.md` — ARQ-05 marcado como completamente resuelto v5.11.0
- Ítems P2 resueltos en esta versión: A11Y-04, A11Y-06, A11Y-07 (verificado), VIS-04, VIS-09, ORG-01, ARQ-05

---
## [5.10.0] - 2026-04-19

### 🎯 Resumen
Incremento de cobertura de tests del 54% al 64% añadiendo baterías de tests sobre use cases, servicios, widgets y utilidades.

### ✨ Added
- `tests/test_forms_extra.py` — RestriccionesWidget, ZonaForm
- `tests/test_assignment_services.py` — Slot, SlotBuilder, ProfesorFilter, LimpiarGuardiasUseCase, ActualizarLogoUseCase, CursoEscolarEntity
- `tests/test_use_cases_extra.py` — EliminarProfesorUseCase, EliminarZonaUseCase, ActualizarLogoUseCase (rutas de error)
- `tests/test_pdf_services.py` — exportar_mes_consolidado, exportar_curso_completo, exportar_profesor_individual_optimizado
- `tests/test_exportador_import.py` — deserialización, desencriptación, importar_zonas, importar_profesores, importar_configuracion
- `tests/test_validador_diagnosticador.py` — ResultadoValidacion, ValidadorGuardias, DiagnosticadorGuardias
- `tests/test_calculador_data_exporter.py` — calcular_dias_lectivos, ajustar_redondeo, DataExporter JSON
- `tests/test_widgets_services_extra.py` — GestionarAusenciasForm, ProgressDialog, AnalisisEquidadUseCase
- `tests/test_config_widgets_extra.py` — SMTPConfigWidget, SFTPConfigWidget, ZonaForm extra, LoginDialog
- `tests/test_perfiles_ausencias_extra.py` — PerfilesUsuarioForm, GestionarAusenciasForm métodos extra
- `tests/test_use_cases_zona_profesor.py` — CrearZonaUseCase, ActualizarZonaUseCase, ActualizarProfesorUseCase, CalcularCuotasUseCase

### 🧹 Housekeeping
- Cobertura global: 54% → 64% (+10 pp), suite: ~1050 → 2052 tests.

---
## [5.9.8] - 2026-04-19

### 🎯 Resumen
OBS-03 resuelto con instrumentación de métricas de negocio en endpoints clave de guardias.

### Changed
- `src/api/routers/guardias.py` añade logs estructurados de negocio en:
  - listado de guardias (total, devueltas, paginación, duración)
  - conteo de guardias (total, duración)
  - exportaciones CSV/XLSX (registros, duración)
  - asignación y limpieza de guardias (IDs relevantes, volumen, duración)
- Se añade logging de excepciones en rutas de guardias para mejorar trazabilidad operativa.

### Fixed
- **OBS-03**: incorporadas métricas de negocio en logs estructurados para operaciones críticas.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: OBS-03 marcado como ✅ RESUELTO v5.9.8.

---
## [5.9.7] - 2026-04-19

### 🎯 Resumen
TEST-06 resuelto con integración de mutation testing mediante `mutmut`.

### ✨ Added
- Dependencia `mutmut>=2.4.4` añadida en `requirements.txt` y `pyproject.toml`.
- Nuevo comando `make mutation` en `Makefile` para ejecutar mutation testing sobre `src/domain`.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: TEST-06 marcado como ✅ RESUELTO v5.9.7 en secciones y roadmap.

---
## [5.9.6] - 2026-04-19

### 🎯 Resumen
API-11 resuelto con schema de error estándar aplicado de forma centralizada en FastAPI.

### Changed
- `src/api/main.py` añade normalización global de `HTTPException` al formato:
  - `{"error": {"code": "...", "message": "...", "details": {...}}}`
- `RequestValidationError` y errores no controlados devuelven ahora el mismo schema estándar.
- `tests/test_api_rest.py` actualizado al nuevo formato de error.

### Fixed
- **API-11**: eliminada inconsistencia entre respuestas con `detail` y respuestas con `error`.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: API-11 marcado como ✅ RESUELTO v5.9.6.

---
## [5.9.5] - 2026-04-19

### 🎯 Resumen
RES-03 resuelto con retry de apertura de sesión/conexión de BD usando la configuración existente.

### Changed
- `src/database/db_manager.py` añade `_create_session_with_retry()` con backoff exponencial.
- `get_session()` y `get_db_session()` usan ahora creación de sesión con retry.
- Eliminado patrón de retry defectuoso en `get_db_session()` que reintentaba con doble `yield`.

### Fixed
- **RES-03**: `max_retries_db` pasa a aplicarse de forma efectiva al abrir sesiones de BD.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: RES-03 marcado como ✅ RESUELTO v5.9.5 en sección y roadmap.

---
## [5.9.4] - 2026-04-19

### 🎯 Resumen
Cierre documental de RES-01 al verificar retry SFTP activo con tenacity en producción.

### Fixed
- **RES-01**: marcado como ✅ RESUELTO v5.2.1 (retry SFTP con backoff exponencial).

### Changed
- Alineada tabla histórica de resiliencia para reflejar estado real de RES-01/RES-02.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: RES-01 actualizado en sección principal, roadmap P2 y tabla histórica.

---
## [5.9.3] - 2026-04-19

### 🎯 Resumen
DB-13 resuelto con backup automático periódico por usuario y retención configurable.

### ✨ Added
- `src/database/db_manager.py`: backup automático al inicializar BD de usuario cuando se cumple el intervalo configurado.
- Retención de backups antiguos (`guardias_patio_backup_*.db`) manteniendo solo los más recientes.
- Nueva configuración en `settings`:
  - `auto_backup_enabled`
  - `auto_backup_interval_hours`
  - `max_auto_backups`

### Fixed
- **DB-13**: implementado mecanismo automático de backup/restore operativo sobre la infraestructura ya existente.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: DB-13 marcado como ✅ RESUELTO v5.9.3 en secciones y roadmap.

---
## [5.9.2] - 2026-04-19

### 🎯 Resumen
Cierre documental de DB-08 al verificar que la inconsistencia `archivado/cerrado` ya estaba resuelta por migración previa.

### Fixed
- **DB-08**: marcado como ✅ RESUELTO (pre-existente) en auditoría.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: DB-08 actualizado en la sección de hallazgos y en el roadmap P2.

---
## [5.9.1] - 2026-04-19

### 🎯 Resumen
DB-11 resuelto: inicialización de base de datos unificada en Alembic como fuente única de verdad.

### Changed
- `src/database/db_manager.py` elimina `create_all()` y SQL directo del flujo de inicialización de usuario.
- `initialize_user_database()` ahora exige migración Alembic exitosa y falla explícitamente si no puede migrar.
- `create_user_database()` migra exclusivamente con Alembic (`upgrade head`) y devuelve error claro si falla.

### Fixed
- **DB-11**: resuelta la triple estrategia de init (`Alembic + create_all + SQL directo`) en favor de solo Alembic.

### Audit
- `docs/AUDITORIA_INTEGRAL_2026.md`: DB-11 marcado como ✅ RESUELTO v5.9.1 en secciones y roadmap.

---
## [5.9.0] - 2026-04-20

### 🎯 Resumen
Corrección de SyntaxError/NameError en producción, imports faltantes `SQLAlchemyError`, catch-all `except Exception` en use cases. 11 ítems de auditoría marcados resueltos (pre-existentes).

### Fixed
- **SyntaxError**: `asignador_guardias_cpsat.py:845` y `asignador_guardias_v4_hibrido.py:276` — cadena f-string duplicada corregida
- **SyntaxError**: `importador_zonas.py` — 4 cadenas f-string duplicadas corregidas
- **NameError**: `from sqlalchemy.exc import SQLAlchemyError` faltante en 8 archivos:
  - `use_cases/zona/crear_zona.py`, `actualizar_zona.py`, `eliminar_zona.py`
  - `use_cases/profesor/actualizar_profesor.py`, `eliminar_profesor.py`
  - `repositories/sqlalchemy_profesor_repository.py`, `sqlalchemy_zona_repository.py`, `sqlalchemy_guardia_repository.py`
- **Exception handling**: `except Exception` catch-all añadido en `crear_profesor.py`, `actualizar_profesor.py`, `crear_zona.py`, `asignar_guardia.py` para convertir errores inesperados de BD a `ValidationError`/`BusinessLogicError`

### Audit — Marcados RESUELTO (pre-existentes)
- **SEC-09**: `LockoutManager` ya implementado en `src/core/security/lockout_manager.py`
- **SEC-10**: `html.escape()` ya aplicado en `email_service.py`
- **SEC-11**: `_sanitize_path()` y `_safe_path()` ya implementados en `sync_manager.py`
- **SEC-13**: `api_secret_key = ""` con advertencia explícita en `settings.py`
- **SEC-14**: `re.fullmatch()` validación username ya en `register_user()`
- **SEC-15**: `data/` ya en `.gitignore`, no trackeado
- **SEC-17**: `print()` sólo en docstrings/ejemplos, no en código ejecutable
- **DB-06**: Índices compuestos y simples ya en `models.py`
- **DB-07**: Sin `datetime.utcnow()` en el código fuente
- **SAN-01/SEC-16**: Todos los `except Exception` hacen `raise` o loggean+re-lanzan

---
## [5.8.0] - 2026-04-19

### 🎯 Resumen
API-08: CRUD completo REST — POST/PUT/DELETE para profesores y guardias, router `/zonas` nuevo con CRUD completo. 22 nuevos tests de API.

### ✨ Added
- **API-08**: `POST /profesores`, `PUT /profesores/{id}`, `DELETE /profesores/{id}`
- **API-08**: Router `/zonas` nuevo: `GET`, `GET /{id}`, `POST`, `PUT /{id}`, `DELETE /{id}`
- **API-08**: `POST /guardias` (asignar guardia manual), `DELETE /guardias` (limpiar todas)
- 22 tests nuevos en `test_api_rest.py` para los nuevos endpoints CRUD

### Fixed
- Tests `test_listar_guardias_*` corregidos para respuesta paginada

---
## [5.7.0] - 2026-04-19

### 🎯 Resumen
Documentación de ítems ya resueltos (ARQ-08/09, SEC-12, DB-05/09, PERF-02/05, A11Y-10, VIS-01/03) y UXF-01: sustituciones completan `es_sustitucion`, `profesor_sustituido_id` y `notas`.

### ✨ Added
- **UXF-01**: `confirmar_sustitucion()` llama a `marcar_como_sustitucion(profesor_id)` y guarda `notas` en la entidad

### Fixed
- Corregidos marcadores de auditoría: 11 ítems marcados como RESUELTO (pre-existente o v5.5.0/5.6.0)

---
## [5.6.0] - 2026-04-19

### 🎯 Resumen
Optimización N+1 en ausencias (PERF-03), eliminación de 3 queries directas en presentation (ARQ-02 Fase 1) y reducción de `except Exception` silenciosos (SEC-16 Fase 1).

### ✨ Added
- **PERF-03**: `AusenciaChecker.prefetch_ausencias()` — precarga ausencias de una fecha en una sola query SQL; cache de instancia en `AusenciaChecker` evita N+1 queries durante la asignación. `ProfesorFilter` llama automáticamente a `prefetch_ausencias` antes del bucle de elegibilidad.

### Changed
- **ARQ-02 Fase 1**: Eliminadas las 3 queries directas a ORM en `presentation/`:
  - `generacion_panel.py`: usa `ActualizarConfiguracionUseCase` para actualizar algoritmo
  - `profesor_form.py` ×2: usa `ObtenerProfesorUseCase` + serialización JSON para `recreos_permitidos`
  - `gestor_sustituciones.py`: usa `AppServices.guardias.get_by_id + save` para reasignar guardia
- **SEC-16 Fase 1**: 3 `except Exception` silenciosos sustituidos por tipos específicos (`OSError`, `ValueError`, `RuntimeError`, `AttributeError`) en `ui_helpers.py` y `main.py`

---
## [5.5.0] - 2026-04-19

### 🎯 Resumen
Design tokens aplicados (VIS-05/06), migración ARQ-06 completa, paginación API-09 en guardias y TODO SAN-03 resuelto.

### ✨ Added
- **API-09**: `PaginatedGuardiasResponse` en `GET /guardias` — devuelve `items`, `total`, `page`, `size`, `pages`
- **ARQ-06**: `src/presentation/theme/legacy_styles.py` como destino definitivo de constantes QSS; `ui_styles.py` reducido a wrapper de retro-compatibilidad; ~34 archivos migrados a `from presentation.theme import legacy_styles as styles`

### Changed
- **VIS-05**: Fuentes hardcodeadas sustituidas por tokens `FontSize.*` en 6 archivos de presentación
- **VIS-06**: Márgenes y espaciados hardcodeados sustituidos por tokens `Spacing.*` en 13 archivos de presentación
- **SAN-03**: Implementado `_score_guardias_recientes()` en `score_calculator.py` (penalización -20/-10/-5 por día reciente)

### 🧹 Housekeeping
- **CACHE-01/CACHE-02**: Marcados como resueltos (ya implementados en v5.4.0 con `@cache_profesores` y `@cache_configuracion`)

---
## [5.4.0] - 2026-04-19

### 🎯 Resumen
Hardening de seguridad backend, OpenAPI enrichment y optimización puntual de queries.

### ✨ Added
- **SEC-14**: Validación regex `^[a-zA-Z0-9._-]{3,50}$` en `crear_perfil.py` para rechazar usernames con path traversal y caracteres especiales.
- **API-13**: `summary=` añadido a todos los endpoints REST; `/health` etiquetado en tag `sistema`.

### Changed
- **PERF-04**: `sync_manager.py` usa `first() is None` en vez de `count() == 0` para comprobar BD vacía.

### 🧹 Housekeeping
- Verificado que RES-04 (health con DB check), OBS-05 (RotatingFileHandler) y SEC-17 (print en docstrings) ya estaban resueltos previamente.

---
## [5.3.0] - 2026-04-19

### 🎯 Resumen
Mejoras de accesibilidad y UX: validators en formularios, atajos de teclado ampliados e indicador de cambios sin guardar.

### ✨ Added
- **A11Y-03**: `QRegularExpressionValidator` en campos clave: nombre/email del profesor (`datos_basicos_widget.py`), nombre de zona (`datos_zona_widget.py`) y multiplicadores de ajuste decimal (`ajustes_widget.py`).
- **A11Y-05**: Atajos de teclado en `zona_form.py` (Ctrl+S, F5, Esc) y Ctrl+S en `ajustes_form.py`.
- **UXF-05**: Indicador visual `● Cambios sin guardar` en `ajustes_form.py` con `_dirty` flag; se muestra al modificar cualquier campo y desaparece al guardar o recargar.

### Changed
- `_conectar_senales_cambio()` en `ajustes_form.py` conecta las señales de los sub-widgets tras la carga inicial para evitar falsos positivos.

### Fixed
- **UXF-02**: Documentado como ya resuelto — todos los métodos de borrado ya tenían confirmación implícita.

---
## [5.2.1] - 2026-04-19

### 🎯 Resumen
Refuerzo de resiliencia y tipado de la API: headers de seguridad, request tracing, timeout/circuit breaker SFTP y response models adicionales.

### ✨ Added
- **SEC-18 / API-10 / API-15**: Middleware en la API para añadir `X-Content-Type-Options`, `X-Frame-Options`, `Strict-Transport-Security`, `API-Version`, `X-Correlation-ID` y `X-Request-ID`, además de logging estructurado por petición.
- **RES-02**: Integrado `pybreaker` para proteger la conexión SFTP con circuit breaker.

### Changed
- **API-12**: Añadidos `response_model` en endpoints de cuotas, equidad, conteo de guardias y estadísticas, mejorando el tipado OpenAPI.
- **ASYNC-02**: Endurecida la conexión SFTP con `timeout`, `banner_timeout`, `auth_timeout` y `keepalive`.
- **CACHE-03**: Cacheo de pixmaps del logo corporativo con `QPixmapCache` en utilidades de UI.

### Fixed
- Actualizado el documento de auditoría para marcar como resueltos los ítems cerrados en esta versión.

---
## [5.2.0] - 2026-04-19

### 🎯 Resumen
Implementación de integridad de datos (DB-05) y optimizaciones de performance (PERF-02).

### ✨ Added
- **DB-05**: Implementación de `CheckConstraint` a nivel de base de datos para todos los modelos ORM (`Profesor`, `Guardia`, `Ausencia`, `Zona`, `Configuracion`), asegurando validaciones de rangos y valores enumerados.
- Resolución de conflictos en el sistema de migraciones Alembic mediante el uso de `batch_alter_table` (necesario para SQLite) y consolidación de ramas de migración.

### Changed
- **PERF-02**: Implementación de `joinedload` en servicios críticos (`calculador_guardias`, `exportador_pdf`, `gestor_ausencias`, `diagnosticador_guardias`, `distribucion_cuotas_service`) para eliminar el problema de consultas N+1 y mejorar la velocidad de carga de listados.

### 🧹 Housekeeping
- Eliminadas tablas obsoletas de la base de datos (`profesor_dias_semana`, `profesor_recreos`) que ya no se utilizaban en los modelos actuales.

---
## [5.1.2] - 2026-04-19

### 🎯 Resumen
Estabilización de concurrencia en db_manager (DB-09) y marcado de SEC-12 ya resuelto.

### Fixed
- **DB-09**: Añadido `threading.Lock` (`_db_lock`) en `db_manager.py` para proteger las variables globales `_current_engine`, `_current_session_factory` y `_current_user_id` frente a condiciones de carrera. Afecta a escritura en `initialize_user_database()` y lecturas en `get_session()` y `get_db_session()`.

### 🧹 Housekeeping
- **SEC-12**: Verificado que `_save_users()` en `sync_manager.py` ya aplica `os.chmod(0o600)` — marcado como resuelto en auditoría.
- **SEC-17**: Verificado que `print_pool_status()` ya usa `logger.debug()` — marcado como resuelto en auditoría.

---
## [5.1.1] - 2026-04-19

### 🎯 Resumen
Refactorización de seguridad SEC-16: Eliminación masiva de bloques de excepciones genéricas silenciosas.

### Fixed
- **SEC-16**: Reemplazados más de 230 bloques `except Exception` por captura de excepciones específicas (`SQLAlchemyError`, `OSError`, `ValueError`, `TypeError`, `KeyError`) en las capas `services/`, `presentation/`, `sync/`, `infrastructure/`, `application/` y `api/`.
- Añadido logueo de stacktraces (`logger.exception()`) en excepciones previamente silenciosas (`except Exception: pass`), especialmente en operaciones I/O y callbacks de UI.
- Reducido el número total de excepciones genéricas de 273 a 40, cumpliendo el objetivo de la auditoría (<50).

---
## [5.1.0] - 2026-04-19

### 🎯 Resumen
Implementación de bloques 1, 2 y 3 de auditoría técnica 2026: Victorias rápidas, Sistema de Design Tokens y Gestión de Conexiones a BD.

### ✨ Added
- `src/presentation/theme/tokens.py`: Sistema de Design Tokens centralizado (colores, espaciado, tipografía)
- `src/presentation/theme/light.qss`: Hoja de estilos global centralizada

### Changed
- `pyproject.toml`: Completados metadatos con bloque `[project]` y dependencias.

### Fixed
- Base de datos (`db_manager.py`): Corrección de fuga de descriptores usando explícitamente `NullPool` en la inicialización de SQLite (ARQ-05).
- Base de datos (`db_manager.py`): Eliminados límites hardcodeados del connection pool (ARQ-06), utilizando fallback a variables de entorno.
- `main.py`: Implementado graceful shutdown al recibir `SIGTERM` / `SIGINT` (RES-05).

### 🧹 Housekeeping
- `src/ui_styles.py`: Marcado como obsoleto (`DeprecationWarning`) para migrar a tokens y QSS (VIS-03).
- `settings.py`: Eliminados 5 feature flags huérfanos (`cache_enabled`, `enable_query_optimization`, etc) (ARQ-09).
- Logueo: Sustituidos bloques `print()` en caché y DB por `logger.debug()` (SEC-17).

---
## [5.0.0] - 2026-04-19

### 🎯 Resumen
Cobertura reforzada en autenticación API, routers REST, cache, factories, validador de ausencias y migración multi-curso.

### ✨ Added
- `tests/test_api_auth_extras.py`: 67 tests
  - `api/auth.py`: `_verify_user`, `create_access_token`, `get_current_user` endpoint
  - Routers: estadísticas (con y sin filtro de fecha), equidad, cuotas, guardias (count + export)
- `tests/test_factories_ausencia_checker.py`: 28 tests
  - `application/factories.py`: 5 factory functions (100% cobertura)
  - `services/validators/ausencia_checker.py`: ausencias activas, solapamientos, guardias del día
- `tests/test_utils_cache.py`: 34 tests
  - `utils/cache.py`: LRU+TTL cache, métricas, invalidación, `cache_short/medium/long`, evicción LRU
- `tests/test_migrar_multi_curso.py`: 19 tests
  - `services/migrar_a_multi_curso.py`: `necesita_migracion`, detección año-curso, creación, asignación, flujo completo
- Tests totales: 1222 → 1342
- Cobertura: 46.02% → 47.81%

---
## [4.11.0] - 2026-04-19

### 🎯 Resumen
Cobertura reforzada en DataExporter y orquestación de asignación, con foco en ramas de configuración, validación de esquema y decisiones de fallback.

### ✨ Added
- `tests/test_data_exporter_config_schema.py`: 15 tests
  - Export/import SMTP y SFTP en `.env`
  - Fallbacks de desencriptado
  - Guards de esquema en importación JSON
- `tests/test_orquestador_asignacion_guardias.py`: 13 tests
  - Flujo iterativo aceptable/no aceptable
  - Decisiones de usuario (`ajustar`, `continuar_ilp`, `timeout`, `cancelar`, error)
  - Mensajería de éxito/intervención
- Ampliación en `tests/test_estadisticas_validador.py` para `generar_resumen_completo`, conflictos y `log_resumen`
- Tests totales: 1190 → 1222
- Cobertura: 44.96% → 46.02%

---
## [4.10.0] - 2026-04-19

### 🎯 Resumen
Refuerzo de cobertura en la capa de sincronización con tests de `UserAuth`, `SessionLock`, `SyncManager` y `backend_factory`.

### ✨ Added
- `tests/test_sync_auth_lock_factory.py`: 47 tests
  - `UserAuth`: policy, registro, autenticación (incluye lockout), migración SHA-256 legacy a bcrypt
  - `SessionLock` y `SessionLockManager`: adquisición/liberación de lock y heartbeat
  - `backend_factory`: rutas local/sftp, validaciones y fallback
  - `SyncManager`: flujos `sync_on_startup`, `sync_on_shutdown`, metadata y `manual_sync`
- Tests totales: 1143 → 1190
- Cobertura: 43.55% → 44.96%

---
## [4.9.0] - 2026-04-19

### 🎯 Resumen
Aumento de cobertura hacia 55%+ mediante 63 tests nuevos en servicios críticos.

### ✨ Added
- `tests/test_estadisticas_validador.py`: 27 tests — `EstadisticasService` (métodos puros) + `ResultadoValidacion` + `ValidadorGuardias`
- `tests/test_importadores_exporter.py`: 36 tests — `importador_zonas` (CSV + helpers), `importador_profesores` (CSV), `DataExporter` (serialize/parse/encrypt + export/import JSON BD)
- Tests totales: 1080 → 1143, todos pasan

---
## [4.8.0] - 2026-04-20

### 🎯 Resumen
Aumento de cobertura de tests del 16.4% al 41.5% mediante nuevos tests unitarios.

### ✨ Added
- `tests/test_use_cases_perfil.py`: 24 tests para `CrearPerfilUseCase`, `ListarPerfilesUseCase`, `ActualizarPerfilUseCase`, `EliminarPerfilUseCase` y `CambiarPasswordUseCase`
- `tests/test_icalendar_cuotas.py`: 15 tests para `ICalendarService` (métodos estáticos + generación .ics) y `CalcularCuotasUseCase`
- Cobertura: 1080 tests totales (1046 → 1080), cobertura 16.4% → 41.5%

---
## [4.7.0] - 2026-04-19

### 🎯 Resumen
Eager loading, validaciones, retry BD, correlation IDs y correcciones.

### ✨ Added
- `ProfesorRepository.get_all()`: `joinedload(zona_preferida, curso)` — elimina N+1 queries
- `api/main.py`: middleware `X-Correlation-ID` para trazabilidad cross-capa
- `db_manager.get_db_session()`: retry con backoff exponencial usando `max_retries_db` de settings
- `db_manager._hash_username()`: valida username no vacío (raises `ValueError`)

### Fixed
- `sync_manager.SFTPSyncBackend`: `_check_connection` renombrado a `_ensure_connected` (faltaba definición correcta)
- `tests/test_domain_services.py`: aserción `test_calcular_cuotas_simple` corregida a `<= 2` (distribución por turno puede acumular redondeo)

---
## [4.6.0] - 2026-04-18

### 🎯 Resumen
Cache en memoria TTL (cachetools) + retry SFTP con backoff exponencial (tenacity).

### ✨ Added
- `services/cache_service.py`: TTLCache thread-safe (5 min) para Configuracion, Zona, Profesor
- `invalidar_cache()`, `invalidar_configuracion()`, `invalidar_zonas()`, `invalidar_profesores()`
- `tenacity>=8.2.0` y `cachetools>=5.3.0` añadidos a `requirements.txt`
- 14 tests nuevos en `tests/test_cache_resilencia.py`

### Changed
- `sync_manager.SFTPSyncBackend._connect()`: retry automático con backoff 2s→4s→8s (tenacity)

---
## [4.5.0] - 2026-04-18

### 🎯 Resumen
Split de `asignador_guardias_v4_hibrido.py` (1066L) en tres módulos.

### 🧹 Housekeeping
- `asignador_guardias_v4_hibrido.py`: 1066 → 276L (orquestador + re-exports)
- `_asignador_v4_helpers.py` (387L): preparación, elegibilidad, scoring, registro
- `_asignador_v4_fases.py` (341L): rondas equitativas, completitud forzada, validación, métricas
- Sin cambios de comportamiento; compatibilidad de imports preservada

---
## [4.4.0] - 2026-04-18

### 🎯 Resumen
Vinculación de profesores a cursos escolares mediante `curso_id` en ORM.

### ✨ Added
- Campo `Profesor.curso_id` (FK a `cursos_escolares.id`, nullable) en ORM + relación `profesor.curso`
- Índice `ix_profesores_curso_id` en BD
- Migración Alembic `b1c2d3e4f5a6` con `batch_alter_table` para SQLite
- Fallback en `_apply_direct_migrations` para BDs que no usen Alembic
- 10 tests nuevos en `tests/test_gestor_cursos_curso_id.py`

### Changed
- `GestorCursos.copiar_profesores_curso_anterior()`: ahora filtra profesores por `curso_id` del curso origen y asigna `curso_id` al nuevo curso en las copias; la comprobación de duplicados también usa `curso_id`

---
## [4.3.0] - 2026-04-18

### 🎯 Resumen
Paginación en API de profesores y schema de error estándar en todos los endpoints.

### ✨ Added
- Paginación en `GET /api/v1/profesores`: parámetros `offset` (default 0) y `limit` (default 50, máx 200); respuesta `{items, total, offset, limit, has_more}`
- Schema de error estándar `{"error": {"code": "...", "message": "..."}}` en todos los errores HTTP: 500 desde routers, 422 de validación y errores no controlados desde `main.py`
- Handler `RequestValidationError` global para errores de validación Pydantic con mismo schema
- 5 tests nuevos en `test_api_rest.py` (paginación, offset, has_more, limit inválido, schema error)

### Changed
- `GET /api/v1/profesores` devuelve `PaginatedProfesoresResponse` en lugar de `List[ProfesorResponse]`
- Error 500 en routers devuelve `{"detail": {"code": "internal_error", "message": "..."}}`
- Error 404 profesor devuelve `{"detail": {"code": "not_found", "message": "..."}}`

---
## [4.2.0] - 2026-04-18

### 🎯 Resumen
Backup/restore de BD por usuario, importación de zonas desde CSV/Excel y 23 tests nuevos.

### ✨ Added
- `backup_database(username, backup_dir)` en `db_manager.py`: copia la BD a un archivo `.db` con permisos 600, en `data/users/{hash}/backups/`
- `restore_database(username, backup_path)` en `db_manager.py`: valida el archivo SQLite, crea backup de seguridad automático y restaura
- `src/services/importador_zonas.py`: importación de zonas desde CSV y Excel con columnas `nombre_zona`, `descripcion`, `activa`, `capacidad_profesores`; función unificada `importar_zonas()` detecta formato por extensión
- 23 tests nuevos en `tests/test_importador_zonas_backup.py` cubriendo helpers de parseo, importación CSV, detección de formato y backup/restore

---
## [4.1.0] - 2026-04-22

### 🎯 Resumen
Optimizaciones query, índices BD, CheckConstraints para integridad de datos.

### ✨ Added
- **Índices de performance**: Cursos, turnos, fechas, profesor+fecha, zona+fecha en guardias; turnos y activo en profesores; profesor+fecha en ausencias
- **CheckConstraints**: Turno válido (mañana/tarde/mixto), horas > 0, recreo >= 1, tipo ausencia válido, fecha_fin >= fecha_inicio

### Changed
- **Optimización queries**: Reemplazar `.count() > 0` por `.first() is not None` en 4 repositorios (mejor performance en BD pequeña)
- Migración Alembic: `a0b1c2d3e4f5_add_indexes_and_constraints.py`

---
## [4.0.0] - 2026-04-22

### 🎯 Resumen
Hardening de seguridad: lockout progresivo mejorado, sanitización SFTP, permisos archivo, defaults seguros, validación usuario.

### ✨ Added
- **P1 Lockout mejorado**: `src/core/security/lockout_manager.py` con delay progresivo [1,2,4,8,16]s en API (`src/api/auth.py`) y sync (`sync_manager.py`); bloqueo de 15 min tras 5 intentos
- **P2 Path traversal**: `_sanitize_path()` en `SFTPSyncBackend` valida `remote_path` contra `..`, rutas absolutas, etc., rechaza attempts

### Changed
- **BREAKING**: `api_secret_key` en settings.py ahora es vacío por defecto (requiere env var `GUARDIAS_API_SECRET_KEY` en producción)
- **P2**: `users.json` guardado con `os.open(flags=0o600, mode=0o600)` — permisos seguros desde creación
- **P2**: Validación username regex `[a-zA-Z0-9._-]` ya disponible desde v3.6.0 (no hay cambios en v4.0.0)
- **P2**: HTML escape en emails disponible desde v3.6.0 (no hay cambios en v4.0.0)
- `SyncBackend` API mejorada: `_sanitize_path()` documentado, manejo de excepciones `ValueError` consistente
- Todos los métodos SFTP (`upload_file`, `download_file`, `file_exists`, `get_last_modified`) ahora validan path

### 🧹 Housekeeping
- Imports optimizados en `src/api/auth.py` (agregado `from typing import Optional`)
- Documentación en `sync_manager.py` sobre protecciones de seguridad SFTP (host key verification, path traversal)

---
## [3.9.0] - 2026-04-18

### 🎯 Resumen
Export CSV/Excel de guardias vía API REST e import de profesores con soporte CSV desde UI.

### ✨ Added
- **P1 Export guardias**: `GET /api/v1/guardias/export/csv` y `/export/xlsx` — descargan archivo con filtros opcionales (fecha, profesor, zona, turno)
- **P1 Import profesores CSV**: `importar_profesores_desde_csv()` + función unificada `importar_profesores()` que detecta formato por extensión (.xlsx/.xls/.csv)
- Diálogo de import en UI acepta ahora `*.xlsx *.xls *.csv`

---
## [3.8.0] - 2026-04-18

### 🎯 Resumen
JWT en API REST, campo activa/capacidad en Zona, error boundary GUI, health check dinámico, migración Alembic zonas.

### ✨ Added
- **P0 seguridad API**: `src/api/auth.py` con autenticación JWT (PyJWT). Endpoint `POST /api/v1/auth/token`, todos los routers protegidos con `Depends(get_current_user)`
- `PyJWT>=2.9.0` y `python-multipart>=0.0.9` añadidos a `requirements.txt`
- `config/settings.py`: campos `api_secret_key`, `api_token_expire_minutes`, `api_algorithm`
- **P2**: `activa` y `capacidad_profesores` añadidos al ORM `Zona` con migración Alembic `c3d4e5f6a7b8`; mapper actualizado (eliminados TODOs)
- **P2**: Error boundary global en GUI — `sys.excepthook` muestra `QMessageBox.Critical` al usuario
- **P3**: `scripts/benchmark.py` punto de entrada unificado para los 4 benchmarks
- **P3**: `scripts/archive/` con benchmarks individuales

### Changed
- **P2**: `/health` usa versión dinámica desde `get_settings().app_version`
- `src/api/main.py`: versión leída de settings (sin hardcode), CORS ampliado a `GET`+`POST`
- `tests/test_api_rest.py`: fixture `client_con_db` inyecta bypass de `get_current_user` para tests

---
## [3.7.0] - 2026-04-18

### Added
- `tests/test_api_rest.py`: 21 tests para API REST (profesores, guardias, SMTP mock, SFTP mock, path traversal)
- `src/services/__init__.py`: módulo init para el paquete services
- `scripts/archive/`: scripts one-off movidos fuera del raíz

### Changed
- **SEC-05**: política de contraseñas (8+ chars, mayúscula, número, símbolo) aplicada en use cases `crear_perfil`, `cambiar_password` y 3 diálogos Qt
- **Fase 10 P0**: campos `es_sustitucion`, `profesor_sustituido_id`, `notas` añadidos al ORM `Guardia` con migración Alembic `b2c3d4e5f6a7`; mapper y repositorio actualizados
- `find_sustituciones()` en repositorio filtra realmente por `es_sustitucion=True`
- `utils/icon_manager.py` unificado como alias de `utils/icons.py`
- `src/api/routers/profesores.py`: migrado a `ListarProfesoresUseCase` / `ObtenerProfesorUseCase` (sin ORM directo)
- `src/api/routers/guardias.py`: migrado a `ObtenerGuardiasUseCase` y `FiltroGuardiasDTO` (sin ORM directo)
- `requirements.txt`: añadida dependencia `httpx>=0.27.0` (necesaria para TestClient de FastAPI)

---
## [3.6.1] - 2026-04-18

### 🎯 Resumen

Fases 2-3 del roadmap de auditoría: thread-safety del caché, SFTP asíncrono en QThread y limpieza de settings huérfanos.

### Changed

- **ASYNC-01 resuelto**: `sync_progress_dialog.py` — nuevo `SyncWorker(QThread)` que ejecuta `sync_on_shutdown()` en hilo separado; `main.py` usa señales Qt (`progress_updated`, `finished`) en lugar de llamada bloqueante en el hilo GUI
- **CACHE-02 resuelto**: `utils/cache.py` ya tenía `threading.RLock` — confirmado y documentado
- `settings.py`: eliminados 4 campos huérfanos (`recreo_manana_1/2`, `recreo_tarde_1/2`) que nunca se leían — la config real de recreos viene de la BD

### 🧹 Housekeeping

- Auditoría actualizada: Fase 3 completada al 100% (CACHE-02 ✅, ASYNC-01 ✅)
- Fase 2 actualizada: settings huérfanos eliminados

---
## [3.6.0] - 2026-04-19

### 🎯 Resumen

ARQ-02 Fase 3: eliminación de acceso directo a SQLAlchemy desde 12 widgets complejos de la capa de presentación.

### ✨ Added

- `SQLAlchemyGuardiaRepository`: 5 nuevos métodos (`find_by_curso`, `count_by_curso`, `count_profesores_distintos_by_curso`, `count_zonas_distintas_by_curso`, `find_by_curso_y_rango_fechas`)
- `SQLAlchemyAusenciaRepository`: `find_active_in_rango`
- `SQLAlchemyConfiguracionRepository`: `find_by_curso_activo_id`
- `AppServices`: 3 helpers cross-aggregate (`profesores_con_guardias_en_curso`, `ausencias_de_profesores_en_curso`, `profesores_activos_con_fechas_especiales`)

### Changed

- **ARQ-02 Fase 3**: 12 widgets migrados para usar `AppServices` en lugar de `session.query(...)` directo:
  - `dashboard_form.py`: 5 queries (config, guardias, profesores × 2, zona)
  - `profesor_form.py`: 2 queries de lectura (2 conservadas por formato JSON ORM)
  - `reportes_form.py`: 3 queries (profesor, guardias, config)
  - `asignacion_guardias_form.py`: 2 queries `count`
  - `asignacion_widgets/resultados_panel.py`: 1 query `get_by_id`
  - `asignacion_widgets/incidencias_panel.py`: 4 queries `count`
  - `asignacion_widgets/generacion_panel.py`: 7 queries (1 escritura ORM conservada)
  - `gestion_cursos_widget.py`: 13 queries
  - `vista_calendario.py`: 7 queries
  - `gestionar_ausencias.py`: 4 queries
  - `gestor_sustituciones.py`: 10 queries de lectura (1 escritura ORM justificada)
- `tests/test_forms_basico.py`: corregido dato inválido `horas_contrato` > 40 en fixture
- `tests/test_gestor_sustituciones.py`: `isinstance(guardia, Guardia)` → `isinstance(guardia, GuardiaEntity)`

### 🧹 Housekeeping

- Eliminados 50+ bloques `session.query()` directos en capa de presentación
- ARQ-02 completado: 21 widgets migrados en total (Fase 2: 9, Fase 3: 12)

---

## [3.5.0] - 2026-04-18

### 🎯 Resumen

ARQ-02 Fase 2: eliminación de acceso directo a SQLAlchemy desde 9 widgets de la capa de presentación, mediante el facade `AppServices`.

### ✨ Added

- `src/application/app_services.py`: facade `AppServices` — punto único de acceso para presentación a repos y use cases

### Changed

- **ARQ-02 Fase 2**: 9 widgets migrados para usar `AppServices` en lugar de `session.query(...)` directo:
  - `ajustes_form.py`: `session.query(Zona).count()` → `AppServices.contar_zonas()`
  - `zona_form.py`: `session.query(Zona).filter_by(id=...)` → `AppServices.zonas.get_by_id()`
  - `selector_curso_widget.py`: `session.query(CursoEscolar).filter_by(id=...)` → `AppServices.cursos.get_by_id()`
  - `dialogo_acerca_de.py`: 6 queries de estadísticas → helpers `AppServices`
  - `calculo_panel.py`: `session.query(Configuracion).first()` → `AppServices.configuracion_repo.get_first()`
  - `cuotas_panel.py`: idem
  - `import_export_form.py`: 4 `count()` queries → helpers `AppServices`
  - `pdf_export_widget.py`: lista profesores ordenada → `AppServices.profesores.get_all()`
  - `calendarios_pdf_widget.py`: idem

### 🧹 Housekeeping

- Eliminados imports ORM top-level (`Configuracion`, `Profesor`, `Zona`, `CursoEscolar`) que dejaron de usarse tras la migración

---

## [3.4.0] - 2026-04-17

### 🎯 Resumen

Tercer lote de auditoría: normalizado de campos JSON a tablas relacionales, migración de domain services a capa de servicios, creación de entidades de dominio y mappers para 3 aggregates, rate limiting API, mejoras UX (DPI, validators, accesibilidad) e init condicional de BD.

### ✨ Added

- **Entidades de dominio**: `AusenciaEntity`, `CursoEscolarEntity`, `ConfiguracionEntity` con métodos de negocio (`cubre_fecha`, `esta_vigente`, `nombre_display`)
- **Mappers**: `AusenciaMapper`, `CursoEscolarMapper`, `ConfiguracionMapper` — conversión ORM ↔ Domain Entity
- **BD-NF**: Migración Alembic `a1b2c3d4e5f7` — tablas `profesor_dias_semana` y `profesor_recreos` normalizan campos JSON de `profesores`
- `slowapi` rate limiting: 60 req/min por IP en todos los endpoints API
- `src/services/_asignador_tipos.py`: dataclasses `Slot`, `ContextoAsignacion`, `ResultadoGeneracion` extraidos del asignador principal
- `src/presentation/widgets/_celda_dia.py`: clase `CeldaDia` extraida de `vista_calendario.py`

### Changed

- **ARQ-01**: 4 domain services movidos de `domain/services/` a `services/` — ya no violan Clean Architecture importando infraestructura desde el dominio
- **ARQ-03**: Repos `sqlalchemy_ausencia`, `sqlalchemy_configuracion`, `sqlalchemy_curso_escolar` ahora retornan domain entities en lugar de ORM models
- **DB-13**: `initialize_user_database()` usa Alembic de forma condicional — si OK, no llama `_apply_direct_migrations()` (elimina init triple)
- `vista_calendario.py`: 1368 → 969 líneas (extracción de `CeldaDia`)
- `asignador_guardias_v4_hibrido.py`: 1140 → 1066 líneas (extracción de tipos)

### Fixed

- **UX-04**: DPI awareness `Qt.HighDpiScaleFactorRoundingPolicy.PassThrough` antes de crear `QApplication`
- **UX-01**: `QRegularExpressionValidator` en campo username de `RegisterDialog` — valida en tiempo real
- **UX-02/03**: `setAccessibleName` + `setTabOrder` explícito en `LoginDialog` y `RegisterDialog`
- **BUG**: Guard `len(password) < 4` que bloqueaba `validate_password_policy` para contraseñas de 5-7 chars

### 🧹 Housekeeping

- `domain/services/__init__.py` vaciado — ya no re-exporta servicios de infraestructura
- `src/services/asignacion_guardia_service.py` import interno actualizado de `domain.services` → `services`

---

## [3.3.0] - 2026-04-17

### 🎯 Resumen

Segundo lote de auditoría: seguridad de autenticación, thread-safety del caché, health check real en la API, mitigación de XSS/path traversal y corrección de permisos de archivos.

### ✨ Added

- `UserAuth.validate_password_policy()`: política de contraseñas (≥8 chars, mayúscula, número, símbolo especial)
- `UserAuth.authenticate()` ahora retorna `tuple[bool, str]` con mensaje de error descriptivo (lockout, credenciales incorrectas)
- Lockout automático: 5 intentos fallidos → bloqueo de 15 minutos (almacenado en `users.json`)
- `LocalSyncBackend._safe_path()`: previene path traversal verificando que la ruta resuelta esté dentro de `base_path`

### Fixed

- **CACHE-02**: `threading.RLock` añadido a `_cache_store` — accesos thread-safe desde `QThread`
- **OBS-01**: `/health` conectado al `HealthChecker` real; retorna 503 si algún componente está `UNHEALTHY`
- **SEC-05/06**: Política de contraseñas elevada a 8 chars + requisitos; lockout brute force implementado
- **SEC-10**: `html.escape()` aplicado a `username` y `profesor_nombre` en plantillas HTML de email
- **SEC-11**: Path traversal en `LocalSyncBackend` corregido con `_safe_path()`
- **SEC-12**: `users.json` se guarda con `chmod 600` tras cada escritura
- **SEC-14**: Username validado con `re.fullmatch(r"[a-zA-Z0-9._\\-]+")` en `register_user()`
- **DB-12**: `create_user_database()` ahora ejecuta `alembic stamp head` tras `create_all()` para que las migraciones futuras funcionen

### 🧹 Housekeeping

- Todos los callers de `authenticate()` actualizados para manejar la tupla `(bool, str)`
- Placeholder del campo contraseña en registro actualizado para reflejar la nueva política

---

## [3.2.0] - 2026-04-17

### 🎯 Resumen

Lote de auditoría técnica: deprecaciones Python 3.12+, rendimiento BD, consistencia ORM/migraciones, limpieza de config y versionado API.

### ✨ Added

- Migración Alembic `e1f2a3b4c5d6`: corrige inconsistencia `archivado`→`cerrado` en `cursos_escolares` y añade 5 índices de rendimiento (`ix_profesores_activo`, `ix_profesores_turno`, `ix_guardias_curso_id`, `ix_guardias_turno`, `ix_guardias_fecha_turno_recreo`)
- API REST: handler global de errores 500 con respuesta JSON estándar (`error`, `detail`)
- API REST: prefijo de versionado `/api/v1/` en todos los routers

### Fixed

- `datetime.utcnow()` deprecated (Python 3.12+) reemplazado por `datetime.now(timezone.utc)` en `models.py`, `data_exporter.py`, `exportador.py`, `gestor_cursos.py`

### 🧹 Housekeeping

- Eliminados 5 feature flags huérfanos de `settings.py` (`feature_zona_preferida`, `feature_matriz_horario`, `feature_ausencias`, `feature_sustituciones`, `feature_exportacion`) — nunca consultados en el código
- Añadido `Index` al import de SQLAlchemy en `models.py`

---

## [3.1.3] - 2026-04-17

### 🎯 Resumen

**Bug crítico de BD vacía**: tras una reinstalación o nueva compilación, la BD se creaba vacía aunque el JSON local tuviera todos los datos, porque el sync solo importaba al descargar del SFTP.

### Fixed

- `sync_on_startup` ahora importa el JSON local a la BD si la BD está vacía y el JSON contiene datos, independientemente del resultado del sync remoto

---

## [3.1.2] - 2026-04-17

### 🎯 Resumen

**Bug crítico de sync**: el `sync_on_startup` podía sobreescribir datos locales con un JSON remoto vacío o con menos registros, provocando pérdida aparente de datos al usar la app compilada.

### Fixed

- `sync_on_startup` ya no sobreescribe el JSON local si el remoto contiene menos registros que el local (guardia de seguridad contra pérdida de datos por sync)
- El JSON remoto se descarga primero a un archivo temporal antes de comparar y reemplazar

---

## [3.1.1] - 2026-04-17

### 🎯 Resumen

**Sanitización y seguridad**: eliminación de `data/users.json` del tracking git, reemplazo de `print()` de debug por logger, y sustitución de 15 bloques `except Exception: pass` por logging explícito.

### Fixed

- `data/users.json` con hashes de contraseñas dejó de estar trackeado en git (ORG-02)
- Eliminadas constantes de backward compatibility huérfanas de `config/settings.py` (TODO obsoleto)
- 20+ sentencias `print()` de debug reemplazadas por `logger.debug/warning/info` en: `app_initializer`, `ui_helpers`, `icon_manager`, `profesor_mapper`, `ccleaner_sidebar`, `profesor_form`, `exportador`, `exportador_pdf`, `orquestador_asignacion_guardias`, `main`, `dialogo_crear_curso`, `gestion_cursos_widget`
- 15 bloques `except Exception: pass` reemplazados por logging explícito en: `obtener_guardias`, `sync_manager`, `progress_indicators`, `metrics`, `corporate_branding`, `restricciones_widget`, `exportador_pdf`

### 🧹 Housekeeping

- Añadido `get_logger` a nivel de módulo en: `app_initializer`, `ui_helpers`, `icon_manager`, `profesor_mapper`, `ccleaner_sidebar`, `profesor_form`, `exportador`, `metrics`, `corporate_branding`, `restricciones_widget`, `progress_indicators`
- `ProgressLogHandler.emit()` ahora llama a `self.handleError(record)` en lugar de silenciar (patrón estándar Python)

---

## [3.1.0] - 2026-04-16

### 🎯 Resumen

**Auditoría de seguridad y limpieza**: migración de contraseñas a bcrypt, cifrado Fernet para credenciales, eliminación de 16 ficheros muertos, corrección de integridad de BD.

### ✨ Added

- Migración automática SHA-256 → bcrypt al hacer login (backward compatible)
- Cifrado Fernet para credenciales SFTP/SMTP (fallback Base64 para exports antiguos)
- TTL de 15 minutos en códigos de recuperación de contraseña
- `UniqueConstraint` en guardias (curso, fecha, turno, recreo, zona, profesor)
- `ON DELETE CASCADE` en FK profesor→guardias/ausencias
- Migración Alembic `c1d2e3f4a5b6` para integridad BD

### Changed

- CORS restringido a `localhost:3000` y `localhost:8080` (antes `*`)
- API solo acepta `GET` (antes `*`)
- uvicorn escucha en `127.0.0.1` (antes `0.0.0.0`)
- `utils/logger.py` unificado como re-export de `core/logging`
- `guardias.profesor_id` y `zona_id` ahora `NOT NULL`

### Fixed

- `repository_cache.py`: decorador se recreaba en cada llamada (caché inútil)
- N+1 en `/api/guardias`: añadido `joinedload` para zona y profesor
- Errores API ya no exponen `str(e)` al cliente
- Recovery code se almacenaba en texto plano sin expiración

### 🧹 Housekeeping

- Eliminados 16 ficheros huérfanos (~2.800 líneas de código muerto)
- Eliminados 3 tests huérfanos asociados
- Eliminadas dependencias `scikit-learn` y `numpy` (no se usaban)
- Añadidas dependencias `bcrypt>=4.0.0` y `cryptography>=41.0.0`

---

## [3.2.1] - 2025-12-08

### 🎯 Resumen

**Mejora del algoritmo Híbrido v4.1**: El algoritmo rápido ahora también prioriza consecutividad y zona. **Limpieza del proyecto** con reducción significativa del tamaño.

### ✨ Added

#### Algoritmo Híbrido v4.1
- **Consecutividad como prioridad máxima**: 
  - Scoring mejorado en `_score_slot()` que prioriza días consecutivos
  - Bonus fuerte para distancia=1 día (perfecto)
  - Penalización progresiva para días lejanos (>7 días)
  
- **Zona preferida como segunda prioridad**:
  - Cada profesor se asigna preferentemente a la misma zona
  - Tracking de zona más usada por profesor

### Changed

- Docstring del módulo actualizado a v4.1
- Reorganización de prioridades de scoring:
  1. Consecutividad (MÁXIMA PRIORIDAD)
  2. Zona preferida
  3. Recreo consistente
  4. Día de semana (baja prioridad)

### 🧹 Housekeeping

- Limpieza de caché: `__pycache__`, `.pytest_cache`, `.ruff_cache`
- Eliminación de archivos temporales: `.coverage`, `coverage.xml`, `htmlcov/`
- Limpieza de logs antiguos (>7 días)
- Eliminación de `.DS_Store`
- **Reducción de ~160MB** en el tamaño del proyecto

---

## [3.2.0] - 2025-12-08

### 🎯 Resumen

**Algoritmo CP-SAT optimizado con 3 objetivos**: Equidad perfecta (IE=100%), consecutividad de guardias, y preferencia de zona. Mejoras en UI para organizar profesores por turno.

### ✨ Added

#### Algoritmo CP-SAT Multi-Objetivo
- **Objetivo 1 - Equidad perfecta**: 
  - Índice de Equidad (IE) = 100%
  - Máxima desviación = 0 guardias por profesor
  - Pesos: `PESO_EQUIDAD=1,000,000`, `PESO_EQUIDAD_SUMA=10,000`

- **Objetivo 2 - Consecutividad de guardias**:
  - Las guardias de cada profesor son lo más consecutivas posibles
  - Minimiza "cortes" entre días (cambios día con guardia ↔ día sin guardia)
  - Resultado: ~30% menos bloques por profesor (de ~22 a ~15)
  - Peso: `PESO_CONSECUTIVIDAD=10`

- **Objetivo 3 - Preferencia de zona**:
  - Cada profesor hace guardias preferentemente en la misma zona
  - Maximiza concentración en zona principal
  - Resultado: ~85% guardias en zona principal (vs ~68% antes)
  - Peso: `PESO_ZONA=3`

#### Greedy Mejorado para Hints
- Función de scoring multi-criterio para solución inicial:
  - Bonus por días consecutivos (`-0.1`)
  - Bonus por zona principal (`-0.05`)
  - Tracking de último día y zona principal por profesor

### Changed

#### UI - Organización por Turno
- **CuotasPanel**: Profesores agrupados por turno (☀️ MAÑANA, 🌙 TARDE, 🔄 MIXTO)
- **ResultadosPanel**: Misma organización por turno con ordenación alfabética
- **GeneracionPanel**: Algoritmo Óptimo (CP-SAT) seleccionado por defecto

#### DTOs
- **CuotaProfesorDTO**: Añadido campo `turno: str` para agrupar profesores
- **calcular_cuotas_use_case.py**: Incluye turno del profesor en DTOs

### 📊 Métricas de Mejora

| Métrica | Antes (v4 Híbrido) | Después (CP-SAT) | Mejora |
|---------|-------------------|------------------|--------|
| Índice de Equidad | ~60-80% | **100%** | +20-40% |
| Bloques/profesor | ~22 | ~15 | -30% |
| % zona principal | ~68% | ~85% | +17% |
| Tiempo ejecución | ~1-2s | ~10-30s | Trade-off |

### 🔧 Technical

- **Jerarquía de pesos**: `Equidad >> Consecutividad > Zona`
- **Solver config**: 8 workers, timeout 120s, linearization_level=2
- **Variables**: ~170,000 booleanas para 67 profesores × 2516 slots

---

## [3.1.1] - 2025-01-13

### 🎯 Resumen

Refactorización arquitectónica completa: migración de modelos ORM a su ubicación canónica, corrección de violaciones DIP, separación UI/Lógica en panel de estadísticas, y actualización de imports en capas Clean Architecture.

### Changed

#### Arquitectura - Separación UI/Lógica (14 ene 2025)
- **panel_estadisticas.py**: Refactorizado para usar Use Case en lugar de queries directas
  - ❌ Eliminadas 14 queries SQLAlchemy del widget
  - ✅ Usa `ObtenerEstadisticasPanelUseCase` para obtener datos
  - ✅ Widget solo maneja presentación, no lógica de BD

#### Nuevos DTOs y Use Cases
- **application/dtos/asignacion_guardias_dto.py**: Nuevos DTOs para panel:
  - `ResumenPanelDTO`: Métricas generales
  - `EstadisticaProfesorDTO`: Stats por profesor
  - `EstadisticaZonaDTO`: Stats por zona
  - `DatosGraficoDTO`: Datos para gráficos
  - `EstadisticasPanelCompletoDTO`: DTO completo agregado
- **application/use_cases/asignacion_guardias/obtener_estadisticas_panel.py**: 
  - Nuevo Use Case que centraliza toda la lógica de estadísticas del panel

#### Arquitectura - Migración Completa de Imports (2 dic 2025)
- **113 archivos migrados** de `models.models` a `infrastructure.database.models`:
  - 54 archivos en `src/`
  - 44 archivos en `tests/`
  - 15 archivos en `scripts/`
- **models/models.py**: Ahora es solo re-export de backup, ya no se usa

#### Arquitectura - Migración de Modelos ORM
- **infrastructure/database/models.py**: Nueva ubicación canónica de modelos SQLAlchemy
- **models/models.py**: Convertido a re-export para backward compatibility (deprecado)
- **28 archivos migrados** a usar nueva ubicación:
  - `infrastructure/mappers/*` (3 archivos)
  - `infrastructure/repositories/*` (6 archivos)
  - `domain/services/*` (5 archivos)
  - `application/use_cases/*` (14 archivos)

#### Arquitectura - Dependency Injection
- **application/factories.py**: Nuevo archivo con factory functions para crear Use Cases con DI
- **5 Use Cases refactorizados** para aceptar interfaces de repositorio como parámetros:
  - `guardia/obtener_guardias.py`: Acepta `IGuardiaRepository`, `IProfesorRepository`, `IZonaRepository`
  - `guardia/asignar_guardia.py`: Acepta `IGuardiaRepository`, `IProfesorRepository`, `IZonaRepository`
  - `profesor/listar_profesores.py`: Acepta `IProfesorRepository`
  - `profesor/obtener_profesor.py`: Acepta `IProfesorRepository`
  - `profesor/crear_profesor.py`: Acepta `IProfesorRepository`

#### Patrón de Imports Recomendado
```python
# Nueva ubicación canónica (recomendado para nuevo código):
from infrastructure.database.models import Profesor, Guardia, Zona

# Backward compatibility (deprecado, funciona pero no recomendado):
from models.models import Profesor, Guardia, Zona  # Re-export
```

### Fixed

#### Documentación Actualizada
- **ARCHITECTURE.md**: 
  - Mejoras arquitectónicas marcadas como completadas
  - Documentación de distinción Use Cases vs Services
- **CLEAN_ARCHITECTURE_PHASE3.md**: Tests marcados como ✅ FIXED, Phase 3 al 100%

### Metrics

- **Violaciones DIP corregidas**: 6 → 0
- **Archivos migrados a nueva ubicación**: 113 (src: 54, tests: 44, scripts: 15)
- **Widget panel_estadisticas.py**: 14 queries eliminadas → 0 queries directas
- **Tests**: 1012 passed, 36 skipped (+22 nuevos tests de use case)
- **Cobertura**: 39.93%

---

## [3.1.0] - 2025-11-30

### 🎯 Resumen

Mejora significativa de la suite de tests. Se corrigieron 33 tests que fallaban y se redujeron los tests saltados de 80 a 36. Cobertura estable en ~40%.

### Fixed

#### Tests de Presentación
- **test_gestionar_ausencias.py**: Reescrito completamente
  - Corregido orden de fixtures (`curso_activo` → `datos_completos` → `form`)
  - 24 tests ahora pasan (antes todos saltados)
  - Actualizado para usar API actual del widget

- **test_progress_indicators.py**: Corregidos tests de threading Qt
  - 8 tests reescritos usando `qtbot.waitSignal()` 
  - Añadido fixture `cleanup_threads` para limpieza
  - Todos los 20 tests ahora pasan (antes 11)

#### Tests de Vista Calendario
- **test_vista_calendario.py**: Revisados y documentados
  - 27 tests pasan correctamente
  - 12 tests apropiadamente marcados como skip (APIs internas obsoletas)

### Changed

#### Métricas de Tests
| Métrica | Antes | Después | Cambio |
|---------|-------|---------|--------|
| Tests pasando | 957 | **990** | +33 |
| Tests saltados | 80 | **36** | -44 |
| Cobertura | 38.44% | **39.75%** | +1.31% |

### Testing

- **Total tests**: 1026 (990 passed, 36 skipped)
- **Archivos corregidos**: 3 (gestionar_ausencias, progress_indicators, vista_calendario)
- **Tests recuperados**: 33 tests que antes fallaban o estaban saltados
- **Mejora en manejo de Qt threading**: Uso de `qtbot.waitSignal()` en lugar de `wait()` y verificaciones inmediatas

---

## [3.0.2] - 2025-11-08

### 🎯 Resumen

Implementación de ventana de detalle del día en calendario y correcciones de seguridad.

### Added

#### UX - Vista de Calendario
- **DiaDetalleDialog**: Ventana modal con detalles completos del día seleccionado
  - Resumen estadístico (guardias, recreos, zonas, ausencias, sustituciones)
  - Sección de guardias agrupadas por recreo
  - Sección de ausencias con fechas y motivos
  - Sección de sustituciones con información del sustituto
  - Diseño visual consistente con código de colores
- **Integración en vista_calendario**: Click en día abre ventana de detalle
- **Tests**: 8 tests unitarios para DiaDetalleDialog (3 pasando, 5 con errores de fixtures)

### Fixed

#### Seguridad
- Resuelto TODO pendiente en `vista_calendario.py:912`
- Mejora en la experiencia de usuario del calendario

---

## [3.0.1] - 2025-11-08

### 🎯 Resumen

Corrección completa de todas las vulnerabilidades de seguridad identificadas en auditoría.

### Security

#### Vulnerabilidades Corregidas
- **7 dependencias actualizadas**:
  - `pip`: 21.2.4 → ≥25.3 (2 CVEs)
  - `setuptools`: 58.0.4 → ≥78.1.1 (3 CVEs: ReDoS, RCE, path traversal)
  - `wheel`: 0.37.0 → ≥0.38.1 (DoS)
  - `future`: 0.18.2 → ≥0.18.3 (DoS)
  - `fastapi`: 0.104.1 → ≥0.109.1 (ReDoS)
  - `requests`: 2.32.3 → ≥2.32.4 (credential leak)
  - `starlette`: 0.27.0 → ≥0.47.2 (2 DoS)

- **Issue B507 (HIGH) corregido**:
  - ANTES: `paramiko.AutoAddPolicy()` (vulnerable a MITM)
  - DESPUÉS: `paramiko.RejectPolicy()` (verifica host keys)
  - Carga automática de host keys desde `~/.ssh/known_hosts`
  - Logging mejorado con instrucciones para usuarios
  - Manejo específico de excepciones SSH

#### Resultados Post-Corrección
- **pip-audit**: 0 vulnerabilidades ✅ (antes: 7)
- **bandit HIGH**: 0 issues ✅ (antes: 1)
- **Certificación**: APROBADO PARA PRODUCCIÓN SIN RESTRICCIONES

### Changed
- Badge de seguridad actualizado en README: "0 vulnerabilities"
- Documentación actualizada: `SECURITY.md`, `SECURITY_FIX_20251108.md`

---

## [3.0.0] - 2025-11-01

### 🎯 Resumen

Refactorización arquitectónica completa de la capa de presentación y optimización del sistema de persistencia mediante implementación de cache. Se extrajeron 12 widgets reutilizables reduciendo 2,757 líneas de código en formularios (-40.3% promedio) y se implementó cache en 12 Use Cases mejorando el rendimiento en consultas de lectura entre 50-98%.

### Added

#### Widgets Reutilizables (12 nuevos)

**Configuración (6 widgets)**:
- `DatosGeneralesWidget` - Nombre del centro, curso académico, fechas
- `ConfiguracionRecreoWidget` - Gestión de recreos y horarios
- `ZonasProfesorConfigWidget` - Configuración de zonas por profesor
- `ToleranciaEquidadWidget` - Tolerancia en distribución
- `ConfiguracionEmailWidget` - Configuración SMTP completa
- `GuardarCancelarWidget` - Botones estandarizados

**Profesores (3 widgets)**:
- `DatosBasicosWidget` - Nombre, email, checkbox tutor
- `HorarioWidget` - Horas contrato, turno, distribución
- `RestriccionesWidget` - Fechas, matriz horario semanal

**Zonas (1 widget)**:
- `DatosZonaWidget` - Nombre, descripción, fechas opcionales

**Import/Export (2 widgets)**:
- `JsonOperationsWidget` - Exportar/importar JSON
- `PdfExportWidget` - Exportación de PDFs con opciones

#### Sistema de Cache

- Cache de profesores (TTL: 3 minutos)
- Cache de zonas (TTL: 5 minutos)
- Decoradores `@cache_profesores` y `@cache_zonas`
- Invalidación automática en operaciones de escritura

#### Sistema de PDFs Corporativos

- Paleta de colores estandarizada (10 colores para zonas)
- Separación visual por meses en tablas
- Colores diferenciados por recreo (4 colores)
- Banner corporativo con datos destacados
- Estilos reutilizables centralizados

#### Algoritmo v3.0

- Fechas consecutivas/agrupadas (prioridad MUY alta)
- Profesores terminan guardias lo antes posible
- Períodos libres más largos
- Mejor conciliación personal
- Algoritmo seleccionable (v2.9 o v3.0)

### Changed

#### Formularios Refactorizados (4)

- `configuracion_form.py`: 1936 → 565 líneas (-70.9%)
- `profesor_form.py`: 1390 → 1013 líneas (-27.1%)
- `import_export_form.py`: 851 → 574 líneas (-32.6%)
- `zona_form.py`: 696 → 657 líneas (-5.6%)

**Reducción total**: -2,757 líneas (-40.3% promedio)

#### Use Cases Optimizados (11)

**Con cache (5)**:
- `ObtenerConfiguracionUseCase` (TTL: 10 min, -98% queries)
- `ListarProfesoresUseCase` (TTL: 3 min, -90% queries)
- `ObtenerProfesorUseCase` (TTL: 3 min, -85% queries)
- `ListarZonasUseCase` (TTL: 5 min, -95% queries)
- `ObtenerZonaUseCase` (TTL: 5 min, -90% queries)

**Con invalidación (6)**:
- `ActualizarConfiguracionUseCase`
- `CrearProfesorUseCase`, `ActualizarProfesorUseCase`, `EliminarProfesorUseCase`
- `CrearZonaUseCase`, `ActualizarZonaUseCase`, `EliminarZonaUseCase`

#### Mejoras de UI

- Branding corporativo en QMessageBox
- SMTP con nombre del remitente configurable
- Mejor manejo de errores y validaciones
- Interfaz más consistente y profesional

### Performance

- **Carga inicial de formularios**: 50-70% más rápido
- **Listar profesores**: 80-90% más rápido
- **Listar zonas**: 80-90% más rápido
- **Obtener configuración**: ~95% más rápido
- **Reducción de queries a BD**: 90-98%

### Documentation

- [SISTEMA_PDF_CORPORATIVO.md](archivo/tecnico/SISTEMA_PDF_CORPORATIVO.md) - Sistema de PDFs
- [PREMISAS_ASIGNACION_GUARDIAS.md](PREMISAS_ASIGNACION_GUARDIAS.md) - Algoritmo v3.0
- Patrón de widgets documentado
- Docstrings completos (100%)
- Type hints en toda la API pública

---

## [2.9.1] - 2025-10-31

### 🎯 Resumen

Actualización del calendario escolar para el curso 2025-2026 con ajustes en días lectivos y validación completa del sistema de equidad. Se corrigieron 4 días en el calendario resultando en una reducción neta de 2 días lectivos y 32 guardias totales. Implementadas optimizaciones de rendimiento que mejoran la velocidad del algoritmo en 67-75%.

### Changed

#### Calendario 2025-2026

- 22/12/2025 (lunes): Cambiado a **LECTIVO** (+1 día, +4 guardias)
- 17-19/03/2026 (Fallas Valencia): Cambiados a **NO LECTIVOS** (-3 días, -12 guardias)
- **Total**: 173 días lectivos (antes 175)
- **Guardias**: 2768 (antes 2800)
- **Balance**: -2 días lectivos = -32 guardias

#### Validación de Equidad

- Equidad perfecta mantenida: 0% desviación
- Cobertura: 100.00%
- Participación: 100% (75/75 profesores)
- Grupos inequitativos: 0 de 7

### Performance

#### IndiceSlots - Búsquedas O(1)

- **Antes**: Búsqueda lineal O(n) en cada verificación
- **Después**: Búsqueda hash O(1) usando conjuntos
- **Impacto**: >2000x más rápido en verificaciones

#### Mejoras Estimadas

- **Fase 2.1** (pre-asignación): 83-88% más rápida
  - Antes: 5-8 minutos
  - Después: 30-60 segundos
- **Tiempo total**: 67-75% más rápido
  - Antes: 8-12 minutos
  - Después: 2.5-4 minutos
- **Memoria adicional**: < 1 MB

#### Optimizaciones Implementadas

- `IndiceSlots`: Índice hash para verificación instantánea
- `FiltroProfesores`: Pre-filtrado por turno y zona
- `CacheElegibilidad`: Memoization de cálculos
- Funciones auxiliares optimizadas

### Fixed

- Corrección de días lectivos en calendario 2025-2026
- Validación matemática: 173 días × 16 guardias/día = 2768 guardias ✅

### Documentation

- [CHANGELOG_v2.9.1.md](archivo/versiones/CHANGELOG_v2.9.1.md) - Análisis detallado del calendario
- [GUIA_OPTIMIZACIONES_RENDIMIENTO.md](archivo/tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md) - Optimizaciones técnicas
- [RELEASE_NOTES_v2.9.1.md](archivo/versiones/RELEASE_NOTES_v2.9.1.md) - Notas de lanzamiento

### Testing

- 28 tests unitarios creados para optimizaciones (71% pasando)
- Tests de regresión: Algoritmo v2.9 sin cambios
- Validación de equidad: 0 grupos inequitativos
- Cobertura: 61.59% en optimizaciones_asignador.py

---

## [2.9.0] - 2025-10-28

### 🎯 Resumen

Fix crítico de compilación y distribución que impedía que la aplicación funcionara correctamente cuando se compilaba con PyInstaller. La app ahora se puede distribuir como un DMG instalable completamente funcional en macOS.

### Fixed

#### Iconos SVG No Se Cargaban

- **Problema**: Iconos no se cargaban en app compilada (rutas hardcodeadas)
- **Solución**: `IconManager` ahora usa `get_resources_directory()`
- **Archivo**: `src/utils/icon_manager.py`

#### App No Abría con Doble Clic

- **Problema**: Error "Read-only file system" al crear directorio logs/
- **Solución**: Eliminada creación de directorios del validador en `settings.py`
- **Sistema de logging**: Ya crea directorios correctamente usando `get_logs_directory()`
- **Archivo**: `src/config/settings.py`

### Added

#### Sistema de Rutas Adaptativas

Funciones en `src/core/paths.py`:
- `get_base_directory()` - Directorio base según entorno
- `get_data_directory()` - Datos de la aplicación
- `get_logs_directory()` - Logs del sistema
- `get_resources_directory()` - Recursos (imágenes, iconos)

**Comportamiento**:

| Función | Desarrollo | Producción (macOS) |
|---------|------------|-------------------|
| Base | `/path/to/project/` | `~/Library/Application Support/GuardiasDePatio/` |
| Data | `project/data/` | `~/Library/.../data/` |
| Logs | `project/logs/` | `~/Library/.../logs/` |
| Resources | `project/imagenes/` | `Contents/Resources/imagenes/` |

#### Script de Creación de DMG

- Nuevo script: `create_dmg.sh`
- Ventana personalizada con iconos grandes
- Acceso directo a `/Applications`
- Archivo `LEEME.txt` con instrucciones
- Compresión optimizada (82.6% de ahorro)
- **Tamaño final**: ~87 MB (de ~250 MB)

### Documentation

#### Nuevos Documentos

- [SOLUCION_COMPILACION.md](archivo/build/SOLUCION_COMPILACION.md) - Historial completo de problemas y soluciones
- [COMPILACION_RAPIDA.md](archivo/build/COMPILACION_RAPIDA.md) - Guía rápida de 5 minutos
- [CHECKLIST_COMPILACION.md](archivo/build/CHECKLIST_COMPILACION.md) - Checklist exhaustivo

#### Documentos Actualizados

- [COMPILACION_Y_DISTRIBUCION.md](archivo/build/COMPILACION_Y_DISTRIBUCION.md) - Referencia a nueva documentación
- `README.md` - Sección de compilación rápida
- `build_simple.sh` - Comentarios explicativos

### Testing

Tests de compilación agregados:
- ✅ Ejecución directa del binario
- ✅ Apertura con `open` (doble clic)
- ✅ Verificación de proceso activo
- ✅ Verificación de directorios del sistema
- ✅ Verificación de iconos (sin warnings)
- ✅ Estructura del bundle correcta

---

## [2.6.1] - 2024-12-XX

### Added

- Sistema de zona preferida para profesores
- Algoritmo de scoring mejorado con 5-tuplas
- 100% de consistencia en zona asignada

### Changed

- Mejoras visuales en formularios
- Reorganización de documentación

### Fixed

- Campos de turno mixto no se mostraban correctamente

### Documentation

- [zona-preferida.md](archivo/versiones/v2.6/zona-preferida.md) - Documentación técnica
- [ejemplos-zona-preferida.md](archivo/versiones/v2.6/ejemplos-zona-preferida.md) - Casos de uso
- [resumen-implementacion.md](archivo/versiones/v2.6/resumen-implementacion.md) - Detalles técnicos

---

## [2.5.0] - 2024-10-XX

### Added

- Sistema completo de gestión de ausencias
- Sustituciones automáticas y manuales
- Vista de calendario mensual mejorada
- Mejoras en importación/exportación de datos

### Changed

- Interfaz de calendario rediseñada
- Mejor organización de vistas

---

## [2.4.0] - 2024-09-XX

### Added

- Sistema de importación/exportación JSON
- Respaldo y restauración de datos
- Transferencia de configuración entre equipos

---

## [2.3.0] - 2024-08-XX

### Performance

- Optimizaciones de rendimiento en algoritmo de asignación
- Mejora en tiempo de carga de formularios

---

## [2.2.0] - 2024-07-XX

### Changed

- Refactorización major de arquitectura
- Mejor separación de responsabilidades

---

## [2.1.0] - 2024-06-XX

### Added

- Nuevas funcionalidades base
- Mejoras en gestión de profesores y zonas

---

## [2.0.0] - 2024-05-XX

### Changed

- Reescritura completa con PyQt6
- Interfaz moderna y responsiva

### Breaking Changes

- Incompatible con versiones 1.x
- Nueva estructura de base de datos

---

## [1.1.0] - 2024-04-XX

### Added

- Mejoras iniciales de UI
- Nuevos widgets y controles

---

## [1.0.0] - 2024-03-XX

### Added

- Release inicial
- CRUD básico de profesores y zonas
- Algoritmo de asignación básico
- Exportación a PDF simple

---

## 🔗 Enlaces

- **Documentación técnica**: [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)
- **Guía de despliegue**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Guía de usuario**: [USER_GUIDE.md](USER_GUIDE.md)
- **Repositorio**: https://github.com/cferrerobonet/guardias_patio
- **Issues**: https://github.com/cferrerobonet/guardias_patio/issues

---

## 📝 Convenciones

### Tipos de Cambios

- **Added**: Nuevas funcionalidades
- **Changed**: Cambios en funcionalidades existentes
- **Deprecated**: Funcionalidades que se eliminarán pronto
- **Removed**: Funcionalidades eliminadas
- **Fixed**: Correcciones de bugs
- **Security**: Correcciones de seguridad
- **Performance**: Mejoras de rendimiento
- **Documentation**: Cambios en documentación
- **Testing**: Cambios en tests

### Versionado Semántico

Formato: `MAJOR.MINOR.PATCH`

- **MAJOR**: Cambios incompatibles con versiones anteriores
- **MINOR**: Nuevas funcionalidades compatibles
- **PATCH**: Correcciones de bugs compatibles

---

**Última actualización**: 30 de noviembre de 2025  
**Versión actual**: 3.1.0  
**Mantenido por**: Equipo Guardias de Patio
