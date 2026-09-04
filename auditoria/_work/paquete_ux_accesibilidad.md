# Paquete Ola 4 — UX/UI y accesibilidad de la aplicación PyQt6

## Control del paquete

- **Estado:** PARCIAL. Hay evidencia estática y una prueba automatizada focalizada, pero no se ha realizado una sesión manual con lector de pantalla ni una matriz real de escalado/SO. No permite certificar WCAG/EN 301 549 ni `ZERO-FIX`.
- **Modo:** `AUDIT_ONLY`. No se modificó código, configuración, dependencias ni datos.
- **Responsable:** agente Ola 4 UX/accesibilidad.
- **Fecha/zona:** 2026-08-04, Europe/Madrid.
- **Commit:** `264a2349c92da0e465bbc0063971c35e295d085f` (`main`).
- **Worktree inicial:** sucio exclusivamente por `?? .agents/AGENTE_AUDITORIA_INTEGRAL_PORTABLE.md`, fichero proporcionado para esta auditoría. Se preservó.
- **Producto:** aplicación de escritorio PyQt6 para gestionar profesores, zonas, cursos, asignación, calendario, ausencias/sustituciones, importación/exportación, informes y estadísticas; ver `README.md:1-39`.
- **Stack verificado:** Python 3.11; PyQt6 6.7.0 / Qt runtime 6.7.3 en la ejecución de pytest; QWidgets/QSS, SQLAlchemy y pytest-qt.
- **Contrato de producto/diseño:** `PRODUCT.md` y `DESIGN.md` no existen. `impeccable context.mjs` devolvió `NO_PRODUCT_MD`. Se usa el código actual y `README.md` como contrato provisional, pendiente de validación.
- **Alcance incluido:** navegación, formularios, tablas, diálogos/overlays, teclado/foco, nombres/relaciones accesibles, feedback y errores, tokens/temas/contraste, resize/escalado, rendimiento percibido de UI y anti-patrones Impeccable.
- **Fuera de alcance:** backend, permisos, integridad de datos, API, seguridad, PDF/impresión y correo salvo su interfaz; PWA/navegadores no aplican a esta app nativa.

## Referencias aplicadas

- [WCAG 2.2, W3C Recommendation](https://www.w3.org/TR/WCAG22/), objetivo AA para 1.3.1, 1.4.3, 1.4.4, 1.4.10, 1.4.11, 2.1.1, 2.4.3, 2.4.7, 2.4.11, 2.5.8, 3.3.1–3.3.3, 4.1.2 y 4.1.3. La aplicación estricta a software no web se hace mediante EN 301 549.
- [EN 301 549 V3.2.1 (2021-03), ETSI](https://www.etsi.org/deliver/etsi_en/301500_301599/301549/03.02.01_20/en_301549v030201a.pdf): cláusulas 11.1.4.3/4/10, 11.2.1.1/2, 11.2.4.3/7, 11.3.3.1–3, 11.4.1.2/3 y 11.5.2.3/5/6/8/13/15 para software no web abierto a tecnología de apoyo.
- [Qt Accessibility for QWidget Applications](https://doc.qt.io/qt-6/accessible-qwidget.html): los widgets Qt estándar aportan roles/acciones, mientras que widgets personalizados deben exponer interfaz y emitir eventos accesibles.
- Impeccable 3.9.1: `reference/audit.native.md`, registro `reference/product.md` y prohibiciones compartidas.

## Evidencia reproducible

### CMD-UX-01 — baseline

- **Comando:** `git status --short; git rev-parse HEAD; git branch --show-current; git log -1 --format='%cI'`
- **Resultado:** commit y rama arriba; worktree preservado; `exit 0`.

### CMD-UX-02 — contexto Impeccable

- **Comando:** `node /Users/cferrerobonet/.codex/skills/impeccable/scripts/context.mjs`
- **Resultado:** `NO_PRODUCT_MD`; raíz resuelta correctamente; `exit 0`.

### CMD-UX-03 — inventario determinista

- **Comandos:** búsquedas `rg` sobre `src/presentation`, y script AST/regex de solo lectura para contar construcciones de controles.
- **Resultado:** 10 vistas registradas; 21 clases `QDialog`; 128 construcciones de controles de formulario en 39 ficheros; 108 `QPushButton`; 12 `QTableWidget`; 51 construcciones explícitas de `QMessageBox`; 24 llamadas a `ToastNotification`; 115 `setAccessibleName`, 0 `setAccessibleDescription`, 0 `setBuddy`, 39 `setTabOrder`; 287 `setStyleSheet`; 718 literales hexadecimales (168 valores distintos) en 54 ficheros de presentación/utilidades.
- **Limitación:** son sitios de construcción estáticos, no el número simultáneo de widgets en runtime; existen implementaciones duplicadas de algunos diálogos.

### CMD-UX-04 — regresión accesible existente

- **Comando:** `QT_QPA_PLATFORM=offscreen PYTHONDONTWRITEBYTECODE=1 pytest -p no:cacheprovider -q tests/test_a11y_regression.py`
- **Resultado:** `5 passed, 1 skipped`, 8,19 s; `exit 0`. El omitido es `AusenciasSustitucionesWidget` porque el propio test captura cualquier excepción y llama a `pytest.skip` (`tests/test_a11y_regression.py:172-185`).
- **Advertencia:** la configuración global de cobertura generó `coverage.xml` y `htmlcov`; se eliminaron inmediatamente al ser artefactos creados por esta ejecución. El worktree volvió al estado inicial.

### CMD-UX-05 — contraste

- **Comando:** cálculo WCAG de luminancia sRGB con script Python de solo lectura sobre los pares declarados.
- **Resultado:** blanco/#007ACC 4,51:1; blanco/#FFC107 1,63:1; #DC3545/#FEE2E2 3,71:1; #007ACC/#E6F2FA 3,96:1; #1E7E34/#D1FAE5 4,53:1; #856404/#FFF3CD 4,96:1.

## Veredicto de conformidad de plataforma

**Pasa como aplicación nativa, falla como experiencia nativa accesible y adaptable.** Usa controles Qt estándar, diálogos del sistema, tablas y atajos, por lo que no parece un port web. Sin embargo, el QSS sustituye estados de foco, hay un overlay flotante propio sin semántica accesible, el tamaño mínimo 1400×900 excluye ventanas/escalados habituales y los gráficos QPainter no exponen una interfaz accesible. No se puede afirmar conformidad EN 301 549.

## Score Impeccable separado (0–20)

| Dimensión | Score | Evidencia clave |
| --- | ---: | --- |
| Accesibilidad | 1/4 | Nombres parciales, feedback no anunciado, foco visual incompleto, gráficos personalizados sin semántica. |
| Rendimiento | 2/4 | Hay lazy loading y workers, pero tablas/heatmap se construyen sin paginación en el hilo UI. |
| Apariencia y temas | 2/4 | Existen tokens, pero conviven tres capas QSS, 718 hex y solo tema claro; hay contrastes AA fallidos. |
| Conformidad de plataforma | 3/4 | Predominan widgets Qt y patrones de escritorio; pierden puntos el toast propio, estilos que anulan foco y controles personalizados. |
| Adaptabilidad | 1/4 | Mínimo global 1400×900, diálogos fijos y texto de 7–10 px. |
| **Total** | **9/20 — Poor** | **Requiere resolver P1 antes de una validación manual asistida.** |

## Resumen ejecutivo

- **Hallazgos:** P0 0 / P1 7 / P2 6 / P3 1 = **14**.
- **Bloqueantes de certificación:** adaptabilidad de ventana; foco visible; nombres/relaciones de campos; feedback accesible; contraste; pérdida de cambios; refresco roto al cambiar de curso; ausencia de validación manual con AT.
- **Orden recomendado:** UXA-007 → UXA-004 → UXA-001/002/005/006 → UXA-003 → tablas/gráficos/rendimiento/tema → reauditoría manual.

## Inventarios resumidos

### Superficies

| Grupo | Superficies | Evidencia/resultado |
| --- | --- | --- |
| Navegación principal | Profesores, Zonas, Ajustes, Perfiles, Cálculo/Asignación, Calendario, Ausencias/Sustituciones, Importar/Exportar, Reportes, Estadísticas | 10 factories en `src/presentation/ccleaner_main_window.py:139-166`; HALLAZGO UXA-007/013. |
| Formularios | 128 construcciones: 61 line edits, 22 combos, 15 checks, 14 fechas, 9 textos, 4 horas y 3 spinboxes | 39 ficheros; HALLAZGO UXA-005/006/012. |
| Diálogos/overlays | 21 clases QDialog, QMessageBox generalizado y toast | HALLAZGO UXA-003/001/010. |
| Tablas/listados | 12 QTableWidget, 69 columnas estáticas más heatmap/preview dinámicos | HALLAZGO UXA-008/011. |
| Visualización | BarChartWidget, PieChartWidget, heatmap y celdas de calendario | HALLAZGO UXA-009/001/014. |

### Formularios campo por campo, agrupados

| Superficie | Campos inventariados | Label/nombre/error | Resultado |
| --- | --- | --- | --- |
| Login/registro/recuperación/password/borrado | usuario/email/password/confirmación/código/selector | Los flujos nuevos tienen `accessibleName`, orden explícito y foco en error (`src/presentation/forms/login_dialog.py:65-137`, `src/presentation/forms/change_password_dialog.py:89-139`); no hay prueba con lector real. | OK estático parcial; UXA-012. |
| Profesor — básicos | nombre, email, tutor | Nombres accesibles y orden; labels manuales sin relación buddy (`src/presentation/forms/profesor_widgets/datos_basicos_widget.py:46-99`). | UXA-005. |
| Profesor — horario | horas contrato, turno, horas mañana/tarde | Sin nombres accesibles ni buddy; labels manuales; errores modales (`src/presentation/forms/profesor_widgets/horario_widget.py:55-124`). | UXA-005/006. |
| Profesor — restricciones | activar restricciones, matriz días/recreos, fechas opcionales, zona preferida | Accesibilidad parcial; botones de matriz 44×32 y fechas nombradas (`src/presentation/forms/profesor_widgets/restricciones_widget.py:191-300`). | UXA-005. |
| Zona | nombre, descripción, activar/fecha inicio, activar/fecha fin | Nombres presentes; validación devuelve texto pero se muestra en modal sin asociarlo al campo (`src/presentation/forms/zona_widgets/datos_zona_widget.py:53-104,211-242`). | UXA-006. |
| Ajustes | fechas curso, cuatro recreos, festivos/no lectivos, factores tutores/no tutores, perfil, SMTP y SFTP | Muchos nombres y tab orders en SMTP/SFTP; persisten labels de 10 px y QSS local (`src/presentation/forms/config_widgets/ajustes_widget.py:57-115`). | UXA-001/010/014. |
| Ausencias/sustituciones | profesor, rango, filtros históricos, sustituto por fila | Controles superiores nombrados; combos creados por fila y estado emoji sin nombre (`src/presentation/widgets/ausencias_sustituciones.py:135-199,380-424`). | UXA-003/008. |
| Informes/PDF/iCal/importación | tipo, mes, año, curso, selección de profesorado, email, formato, fechas, limpiar | Accesibilidad desigual entre widgets; QFormLayout ayuda en informes; feedback y botones warning fallan (`src/presentation/forms/reportes_widgets/informes_estadisticos_widget.py:69-122`). | UXA-003/006/010. |
| Auditoría | desde, hasta, acción, profesor | Labels manuales sin buddy/nombres; tabla limitada a 500 sin paginación (`src/presentation/forms/auditoria_guardias_form.py:58-111,124-187`). | UXA-005/008/011. |

### Tablas y columnas

| Tabla | Columnas | Estados/orden/selección | A11y/adaptabilidad/rendimiento |
| --- | --- | --- | --- |
| Profesores | Nombre, Email, Horas, Turno, Tutor, Inicio, Fin | ordenable; multiselección; solo lectura | Sin nombre de tabla; anchos fijos parciales; carga total en QTableWidget. UXA-008/011. |
| Zonas | ID oculto, Nombre, Descripción, Inicio, Fin | ordenable; multiselección | Sin caption accesible; ID oculto correcto para UI. UXA-008. |
| Cursos | Curso, Inicio, Fin, Estado, Días, cuatro contadores, Profesores, Zonas, Creado | selección simple; todas las columnas Stretch | 11 columnas pierden utilidad en ancho reducido. UXA-001/008. |
| Ausencias/guardias | Fecha, Día, Turno, Recreo, Zona, Ausente, Sustituto, estado | combo por fila; no selección | Cabecera `●` y emojis rojo/verde no textuales; combo no nombrado por fila. UXA-008. |
| Historial sustituciones | Fecha, Turno, Recreo, Zona, Original, Sustituto | solo lectura | Sin caption accesible/paginación. UXA-008/011. |
| Perfiles | Usuario, Email, BD, Logo, Actual, Acciones | simple; solo lectura | Única tabla con `accessibleName` (`src/presentation/forms/perfiles_usuario_form.py:210-235`). Patrón positivo. |
| Estadísticas profesor/zona | 10 y 4 columnas | ResizeToContents | Headers y tooltips; tablas alternativas a gráficos, pero sin asociación accesible. UXA-008/009. |
| Heatmap | Profesor + una columna por semana | color y valor numérico | Dimensión dinámica O(profesores×semanas); colores no tokenizados. UXA-009/011. |
| Auditoría | Fecha/Hora, Acción, Guardia ID, Profesor, Usuario, Detalle | solo lectura; 500 registros | Sin nombre/paginación; el color se acompaña de texto. UXA-008/011. |
| Reasignación | ID, Fecha, Turno, Recreo, Zona, Profesor | selección por fila | diálogo mínimo 800×600; anchos fijos. UXA-001/008. |
| Preview columnas | columnas del fichero | primeras cinco filas | encabezados dinámicos correctos; lectura pandas sin feedback al fallar. UXA-008. |

## Hallazgos detallados

### [UXA-001] La ventana y varios diálogos no caben en pantallas o escalados habituales

- **Estado respecto a auditoría anterior:** NUEVO. **Categoría/tipo:** Adaptabilidad / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Estándar/requisito:** EN 301 549 11.1.4.4 y 11.1.4.10; WCAG 1.4.4/1.4.10 como criterio de comprobación; Impeccable Adaptivity.
- **Superficie/roles:** todos los usuarios; ventana principal, login, configuración inicial, calendarios y diálogos.
- **Ubicación exacta:** `src/presentation/ccleaner_main_window.py:84-93`; `src/presentation/forms/login_dialog.py:299-315`; `src/presentation/dialogs/initial_config_dialog.py:54-58`; `src/presentation/widgets/dialogo_reasignacion.py:43-47`.
- **Evidencia/resultado actual:** la ventana exige 1400×900 y se maximiza; LoginDialog fija 720×480; configuración inicial exige 700×720. En 1366×768 o escalado 150–200 % el marco o acciones pueden quedar fuera del área útil.
- **Reproducción:** iniciar con área lógica ≤1366×768; abrir login/config inicial; aumentar escala del SO a 150/200 %; comprobar acceso por teclado a todos los controles.
- **Esperado/impacto/frecuencia:** ninguna tarea debe requerir más que el área disponible; impacto de bloqueo o scroll bidimensional continuo; probable en portátiles y baja visión.
- **Causa/patrón:** tamaños fijos/mínimos usados como sustituto de layouts adaptables; 42 `setMinimumWidth`, 100 `setMinimumHeight` y múltiples fixed sizes.
- **Recomendación/alternativas:** `$impeccable adapt`; eliminar el mínimo global, definir tamaño recomendado acotado a `availableGeometry`, introducir scroll interno donde corresponda y probar high-DPI. Mantener tamaños mínimos solo en controles, no ventanas.
- **Archivos/datos/compatibilidad/seguridad:** presentación citada y layouts; sin migración ni impacto de datos/seguridad; mejora macOS/Windows/Linux.
- **Prueba de regresión propuesta:** pytest-qt parametrizado a 1024×768, 1280×720, 1366×768, 1440×900 y factores 1/1.5/2, verificando que cada control accionable intersecta el viewport y es alcanzable por Tab.
- **Criterios de aceptación:** [ ] ventana usable a 1024×768; [ ] login/config caben a 200 % en el mínimo soportado o documentan un mínimo validado; [ ] no hay texto/acciones recortados; [ ] teclado alcanza el final sin mover/redimensionar la ventana.
- **Esfuerzo/dependencias/producción/documentación:** L; primero tokens/layout; no requiere producción; documentar matriz de resolución/DPI soportada.

### [UXA-002] El QSS no proporciona foco visible consistente a botones y controles

- **Estado/categoría/tipo:** NUEVO / Accesibilidad / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Requisito:** WCAG 2.4.7 AA, 1.4.11; EN 301 549 11.2.4.7 y 11.5.2.13.
- **Superficie:** global, especialmente sidebar, diálogos y acciones destructivas.
- **Ubicación:** `src/presentation/themes/ccleaner_theme.py:450-594,692-732`; `src/presentation/theme/light.qss:6-95`; `src/presentation/components/ccleaner_sidebar.py:304-349`.
- **Evidencia/actual:** 0 selectores `QPushButton:focus` en presentación; botones redefinen borde/fondo y los inputs solo cambian un borde de 1 px; `outline: none` aparece en el helper de inputs (`src/presentation/themes/ccleaner_theme.py:345-348`). El foco nativo puede quedar oculto por QSS.
- **Reproducción:** navegar solo con Tab/Shift+Tab en sidebar, Profesor, Zona y un QMessageBox; observar cada foco con ratón apartado.
- **Esperado/impacto/frecuencia:** indicador visible en todos los controles; usuarios de teclado pueden perder posición y ejecutar una acción equivocada; continuo.
- **Causa/patrón:** sistema visual define default/hover/pressed/disabled, pero omite focus; estilos locales multiplican la omisión.
- **Recomendación:** `$impeccable harden`; token semántico de focus y estilo de 2 px/alto contraste que no dependa solo del color, preservando el foco nativo cuando sea mejor.
- **Archivos/datos/compatibilidad/seguridad:** temas y estilos locales; sin datos; verificar los tres SO y alto contraste.
- **Prueba:** test visual/screenshot por estado y test pytest-qt que recorra widgets focusables comprobando focusPolicy y propiedad de estilo; validación manual.
- **Criterios:** [ ] todos los controles muestran foco; [ ] indicador no queda tapado; [ ] diferencia de estado claramente perceptible en temas soportados; [ ] no se depende de hover; [ ] dialog buttons conservan foco/default diferenciados.
- **Esfuerzo/dependencias/producción/documentación:** M; depende de UXA-010; no; contrato Button/FormField.

### [UXA-003] Los toast y estados dinámicos no son anunciables, ajustables ni robustos

- **Estado/categoría/tipo:** NUEVO / Accesibilidad + feedback / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Requisito:** WCAG 4.1.3, 2.2.1 y 1.4.3; EN 301 549 11.4.1.3.1, 11.5.2.15 y 11.1.4.3.
- **Superficie:** guardado, cambio de curso/perfil, errores de perfiles, reasignación e informes.
- **Ubicación:** `src/presentation/widgets/toast_notification.py:5-62`; `src/presentation/forms/base_form.py:88-109`; `src/utils/ui_helpers.py:18-37`; usos de error en `src/presentation/forms/perfiles_usuario_form.py:319-351,434-499`.
- **Evidencia/actual:** QWidget frameless con QLabel, sin nombre/rol/evento accesible; desaparece a 2500 ms; no hace wrap; error/info dan 3,71:1 y 3,96:1. Existe `announce()`, pero no tiene consumidores y emite `NameChanged` sin establecer el mensaje en el target.
- **Reproducción:** provocar un error de perfil y un éxito; usar lector de pantalla; intentar releer, pausar o copiar un texto largo.
- **Esperado/impacto/frecuencia:** feedback anunciado sin mover foco, persistente si requiere acción y legible; usuarios ciegos no reciben resultado y textos largos pueden truncarse; frecuente.
- **Causa/patrón:** componente visual creado fuera de los servicios accesibles de Qt y uso indistinto para éxito/error.
- **Recomendación:** `$impeccable harden`; crear componente de status accesible (announcement/Alert según urgencia), cola de mensajes, wrap/ancho máximo, persistencia para errores y acción de cierre. QMessageBox para errores bloqueantes; status no modal para éxito.
- **Archivos/datos/compatibilidad/seguridad:** Toast, BaseForm y llamadores; sin datos; evitar anunciar detalles sensibles de excepciones.
- **Prueba:** spy de eventos QAccessible más NVDA/VoiceOver/Orca; timeout parametrizado; cadenas de 200 caracteres.
- **Criterios:** [ ] cada status se anuncia una vez; [ ] error permanece hasta cierre o recuperación; [ ] texto largo envuelve y cabe; [ ] contrastes ≥4,5:1; [ ] foco no se roba en éxitos; [ ] errores sensibles se sanitizan.
- **Esfuerzo/dependencias/producción/documentación:** M; depende de contrato Alert/Toast; no; documentar politeness/persistencia.

### [UXA-004] El contrato de cambios sin guardar está definido pero no conectado

- **Estado/categoría/tipo:** NUEVO / UX-recuperación / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Requisito:** prevención de pérdida de trabajo; EN 301 549 11.3.3.4 cuando la operación afecte datos; Impeccable Harden.
- **Superficie:** Profesor, Zona, Ajustes y cualquier BaseForm editable.
- **Ubicación:** API muerta en `src/presentation/forms/base_form.py:29-86`; navegación sin guard en `src/presentation/ccleaner_main_window.py:185-190`; cierre que limpia en `src/presentation/forms/profesor_form.py:345-349,391-395`.
- **Evidencia/actual:** `rg` solo encuentra definiciones de `_mark_dirty`, `_mark_clean`, `tiene_cambios` y `registrar_label_cambios`; ningún consumidor. Cambiar de sección o cerrar/cancelar limpia sin aviso.
- **Reproducción:** editar varios campos de Profesor/Zona sin guardar; pulsar otra sección, X del panel o Esc; regresar.
- **Esperado/impacto/frecuencia:** advertir con Guardar/Descartar/Cancelar o preservar borrador; pérdida silenciosa de trabajo, probable.
- **Causa/patrón:** infraestructura incompleta no integrada con routing ni señales de campos.
- **Recomendación:** `$impeccable harden`; conectar cambios de cada campo, crear guard central de navegación/cierre y no duplicar modales por formulario.
- **Archivos/datos/compatibilidad/seguridad:** BaseForm, MainWindow y formularios; sin migración; no guardar passwords en borradores.
- **Prueba:** tests parametrizados por formulario y salida (sidebar, Esc, X, cerrar app), verificando las tres decisiones y retorno de foco.
- **Criterios:** [ ] dirty se activa con todo campo mutable; [ ] se limpia solo tras save/reset confirmado; [ ] navegación y cierre bloquean pérdida accidental; [ ] Cancelar mantiene datos/foco; [ ] campos secretos nunca persisten.
- **Esfuerzo/dependencias/producción/documentación:** L; contrato transversal; no; documentar lifecycle de formulario.

### [UXA-005] Campos centrales carecen de nombre/relación accesible completa

- **Estado/categoría/tipo:** NUEVO / Accesibilidad-formularios / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Requisito:** WCAG 1.3.1, 2.4.6, 3.3.2, 4.1.2; EN 301 549 11.3.3.2, 11.4.1.2.1 y 11.5.2.5/8.
- **Superficie:** alta/edición de Profesor, filtros de auditoría y otros layouts manuales.
- **Ubicación:** controles sin nombre en `src/presentation/forms/profesor_widgets/horario_widget.py:55-109`; filtros en `src/presentation/forms/auditoria_guardias_form.py:58-83`; patrón correcto parcial en `src/presentation/forms/profesor_widgets/datos_basicos_widget.py:46-99`.
- **Evidencia/actual:** 0 `setBuddy`, 0 `setAccessibleDescription`; Horas/Turno/Horas mañana/Horas tarde no llaman a `setAccessibleName`; las labels visuales son QLabels independientes.
- **Reproducción:** recorrer Profesor y Auditoría con lector de pantalla/Inspector; registrar nombre/rol/valor/ayuda de cada control.
- **Esperado/impacto/frecuencia:** cada control anuncia label, requerido/opcional, ayuda, valor y dependencia; tarea principal difícil para usuarios ciegos; continua.
- **Causa/patrón:** accesibilidad añadida por pantalla, sin contrato FormField ni gate global.
- **Recomendación:** `$impeccable harden`; helper FormField que establezca buddy, accessibleName/Description, requerido, ayuda y error; conservar label visible en el nombre.
- **Archivos/datos/compatibilidad/seguridad:** todos los formularios; sin datos; no exponer valores password en descripción.
- **Prueba:** introspección de todos los QLineEdit/QComboBox/QDateEdit/etc. visibles y habilitados, exigiendo nombre, label relation y orden; sesión AT.
- **Criterios:** [ ] 100 % de campos inventariados tienen nombre no ambiguo; [ ] label visible forma parte del nombre; [ ] buddy/relación funciona; [ ] dependencias habilitado/oculto se anuncian; [ ] ayuda no depende solo de tooltip.
- **Esfuerzo/dependencias/producción/documentación:** L; crear contrato FormField primero; no; DESIGN.md.

### [UXA-006] Validaciones de formularios no identifican programáticamente el campo erróneo

- **Estado/categoría/tipo:** NUEVO / Accesibilidad + UX copy / bug. **Severidad/prioridad/confianza:** P1 / alta / alta.
- **Requisito:** WCAG 3.3.1–3.3.3; EN 301 549 11.3.3.1.1/2/3.
- **Superficie:** Profesor, Zona y configuración; contraste con flujo de perfil mejor resuelto.
- **Ubicación:** Profesor muestra modal y retorna sin foco (`src/presentation/forms/profesor_form.py:397-414`); Zona idem (`src/presentation/forms/zona_form.py:335-342`); patrón positivo inline en `src/presentation/dialogs/dialogo_crear_perfil.py:87-165`.
- **Evidencia/actual:** los validadores devuelven solo `(bool, str)`; la UI no recibe campo/ID, no marca `invalid`, no vincula error ni enfoca. El mensaje global obliga a buscar el campo.
- **Reproducción:** enviar Profesor con horas vacías o Zona con fechas invertidas; cerrar el aviso; comprobar foco y anuncio.
- **Esperado/impacto/frecuencia:** resumen + error inline asociado + foco en el primer campo; barrera relevante en formularios largos; frecuente.
- **Causa/patrón:** contrato de validación sin identidad de campo y dependencia de QMessageBox.
- **Recomendación:** `$impeccable clarify` y `$impeccable harden`; devolver errores estructurados por campo, resaltar sin depender solo de color y mantener valores.
- **Archivos/datos/compatibilidad/seguridad:** widgets/DTO de validación y forms; sin migración; sanitizar mensajes internos.
- **Prueba:** cada regla de cada campo debe verificar texto, relación accesible, foco, persistencia de valores y corrección.
- **Criterios:** [ ] error identifica campo y solución; [ ] lector recibe el cambio; [ ] primer error recibe foco; [ ] todos los errores siguen visibles; [ ] no se borra entrada válida; [ ] error no depende solo del rojo.
- **Esfuerzo/dependencias/producción/documentación:** L; después de UXA-005; no; catálogo de errores.

### [UXA-007] Cambiar de curso confirma un refresco que el wrapper impide ejecutar

- **Estado/categoría/tipo:** NUEVO / Estado y feedback / bug. **Severidad/prioridad/confianza:** P1 / inmediata / alta.
- **Requisito:** consistencia/feedback veraz; Impeccable Harden; no adjudicado como norma WCAG específica.
- **Superficie:** todas las vistas ya cargadas tras cambiar curso.
- **Ubicación:** `ContentWrapper` no guarda `content_widget` (`src/presentation/ccleaner_main_window.py:45-68`); handler salta wrappers sin ese atributo pero registra éxito (`src/presentation/ccleaner_main_window.py:238-257`); promesa al usuario `src/presentation/widgets/selector_curso_widget.py:118-166`.
- **Evidencia/actual:** `hasattr(wrapped, "content_widget")` siempre es falso para wrappers creados por `_ensure_view`; ninguna vista cargada se refresca, aunque el toast anuncia nuevo curso y el log dice todas refrescadas.
- **Reproducción:** abrir dos vistas, cambiar curso, inspeccionar datos sin reiniciar o probar con spies en `cargar_datos/refrescar`.
- **Esperado/impacto/frecuencia:** todas las vistas visibles/cargadas se invalidan y muestran el curso seleccionado; riesgo de actuar sobre datos visualmente obsoletos; cada cambio de curso.
- **Causa/patrón:** contrato roto wrapper↔handler y ausencia de test de integración.
- **Recomendación:** `$impeccable harden`; almacenar el hijo o exponer interfaz de refresh; refrescar/invalidar de forma atómica y anunciar solo al terminar.
- **Archivos/datos/compatibilidad/seguridad:** MainWindow/Selector; sin migración; revisar integridad funcional con el agente correspondiente.
- **Prueba:** spy por las 10 vistas, cambio A→B→A, vistas cargadas/no cargadas, fallo parcial; curso visible y queries deben coincidir.
- **Criterios:** [ ] cada vista cargada refresca exactamente una vez; [ ] no se mezclan datos A/B; [ ] el éxito se emite tras finalizar; [ ] fallo identifica vistas afectadas y ofrece reintento; [ ] test reproduce la regresión actual.
- **Esfuerzo/dependencias/producción/documentación:** S/M; validar con lógica de curso; no; contrato de refresh.

### [UXA-008] Las tablas carecen de un contrato accesible/adaptable común

- **Estado/categoría/tipo:** NUEVO / Tablas + accesibilidad / deuda. **Severidad/prioridad/confianza:** P2 / media / alta.
- **Requisito:** EN 301 549 11.5.2.6/7/8/13; WCAG 1.3.1, 2.4.3 y 4.1.2 por equivalencia.
- **Superficie:** 12 QTableWidget y columnas inventariadas.
- **Ubicación:** solo Perfiles tiene nombre (`src/presentation/forms/perfiles_usuario_form.py:210-235`); Profesor no (`src/presentation/forms/profesor_form.py:179-217`); estado/combo no nombrados en ausencias (`src/presentation/widgets/ausencias_sustituciones.py:146-165,380-424`).
- **Evidencia/actual:** 11/12 tablas sin `accessibleName`; cabecera `●`; emojis rojo/verde; combos de fila sin contexto; no hay contrato para empty/loading/error/paginación ni prioridad responsive.
- **Reproducción:** recorrer tablas con lector/teclado, ordenar/seleccionar y editar sustituto; reducir ventana.
- **Esperado/impacto/frecuencia:** anunciar nombre, fila/columna/header, orden, selección y acción; las tablas complejas son costosas y ambiguas para AT y ancho reducido.
- **Causa/patrón:** QTableWidget se usa directamente sin wrapper/contract.
- **Recomendación:** `$impeccable adapt` + `$impeccable harden`; Table/ListView común, nombres, estados textuales, accesibleName contextual por combo, prioridades de columna y scroll horizontal consciente.
- **Archivos/datos/compatibilidad/seguridad:** tablas listadas; sin datos; no ocultar columnas necesarias en exportación.
- **Prueba:** matriz tabla×columna×teclado×AT×ancho, incluyendo sort y embedded widgets.
- **Criterios:** [ ] 12/12 tablas tienen nombre; [ ] headers y sort se anuncian; [ ] cada combo anuncia guardia/fila; [ ] estados tienen texto, no solo emoji/color; [ ] vacío/error enseña recuperación; [ ] columnas prioritarias funcionan al ancho mínimo.
- **Esfuerzo/dependencias/producción/documentación:** L; tras tokens/FormField; no; contrato Table/ListView.

### [UXA-009] Gráficos QPainter no exponen semántica accesible ni escala tipográfica

- **Estado/categoría/tipo:** NUEVO / Accesibilidad visualización / deuda. **Severidad/prioridad/confianza:** P2 / media / alta.
- **Requisito:** WCAG 1.1.1, 1.4.1 y 4.1.2; EN 301 549 11.4.1.2/11.5.2.3/5/7; guía Qt para custom widgets.
- **Superficie:** Estadísticas, heatmap y DashboardForm si se reactiva.
- **Ubicación:** `src/presentation/widgets/bar_chart_widget.py:35-198,201-305`; heatmap `src/presentation/widgets/panel_estadisticas.py:231-323`.
- **Evidencia/actual:** custom QWidget solo pinta; no accessibleName/Description/interface/eventos; fuentes 7–10; etiquetas truncadas; colores codifican desviación. Estadísticas tiene tablas paralelas, pero no relación ni resumen; Dashboard no tiene alternativa tabular.
- **Reproducción:** inspeccionar árbol QAccessible y navegar a gráficos; aumentar texto/DPI.
- **Esperado/impacto/frecuencia:** nombre, resumen, datos equivalentes y cambios anunciables; personas ciegas o con baja visión pierden la visualización.
- **Causa/patrón:** canvas visual sin adaptador accesible.
- **Recomendación:** `$impeccable harden`; exponer resumen y tabla equivalente visible/accionable; interfaz accesible si el gráfico es interactivo; tokens de tipografía y no truncar sin alternativa.
- **Archivos/datos/compatibilidad/seguridad:** gráficos/panel; sin datos; preservar privacidad de nombres.
- **Prueba:** QAccessible tree + comparación 1:1 dataset/gráfico/tabla; DPI 200 %.
- **Criterios:** [ ] cada gráfico tiene nombre/resumen; [ ] 100 % de datos disponibles sin visión/color; [ ] cambios se anuncian; [ ] texto escala sin solape; [ ] paleta mantiene contraste.
- **Esfuerzo/dependencias/producción/documentación:** M/L; después de UXA-010; no; contrato Chart.

### [UXA-010] El sistema visual está fragmentado y contiene contrastes AA fallidos

- **Estado/categoría/tipo:** NUEVO / Theming / deuda con bug de contraste. **Severidad/prioridad/confianza:** P2 global; la instancia warning se cubre como prioridad alta / alta.
- **Requisito:** WCAG 1.4.3/1.4.11; EN 301 549 11.1.4.3; Impeccable product register.
- **Superficie:** global, botones Editar/Importar/Modificar y toast.
- **Ubicación:** tokens `src/presentation/theme/tokens.py:6-75`; QSS app `src/main.py:168-179`; QSS ventana `src/presentation/ccleaner_main_window.py:84-93`; warning `src/presentation/themes/ccleaner_theme.py:25-30,586-594`; uso `src/presentation/forms/profesor_form.py:244-257`.
- **Evidencia/actual:** light.qss + get_complete_stylesheet + 287 estilos inline; 718 hex/168 colores. Blanco/#FFC107 = 1,63:1 en botones warning activos. Toast error/info también fallan. No se detectó tema oscuro/alto contraste.
- **Reproducción:** abrir botones warning y toasts; calcular pares finales tras cascada; activar dark/high-contrast del SO.
- **Esperado/impacto/frecuencia:** una fuente semántica de verdad y ≥4,5:1 en texto normal; baja visión no distingue etiquetas; frecuente.
- **Causa/patrón:** migración incompleta de legacy e identidad duplicada.
- **Recomendación:** `$impeccable document` → `$impeccable colorize`; decidir un QSS global, tokens de estados completos y fallback a paleta del sistema/alto contraste. Eliminar overrides locales por lotes.
- **Archivos/datos/compatibilidad/seguridad:** temas + 54 consumidores con hex; sin datos; comprobar tres SO.
- **Prueba:** extractor de pares renderizados, gate AA light/dark/high contrast y snapshots por estado.
- **Criterios:** [ ] warning y toast ≥4,5:1; [ ] focus/bordes ≥3:1 cuando aplique; [ ] una cascada documentada; [ ] estados default/hover/focus/active/disabled/loading/error; [ ] tema del SO no produce texto invisible.
- **Esfuerzo/dependencias/producción/documentación:** XL por migración incremental; no; crear DESIGN.md.

### [UXA-011] Cargas de tablas y estadísticas pueden bloquear el hilo de UI con datasets grandes

- **Estado/categoría/tipo:** NUEVO / Rendimiento UI / deuda. **Severidad/prioridad/confianza:** P2 / media / media (evidencia estática; falta benchmark representativo).
- **Requisito:** Impeccable Performance; respuesta percibida y continuidad de foco.
- **Superficie:** Estadísticas, profesores, zonas, historial y ausencias.
- **Ubicación:** heatmap hace queries `.all()` y O(P×semanas) en UI (`src/presentation/widgets/panel_estadisticas.py:250-336`); profesor crea todos los items (`src/presentation/forms/profesor_table_helpers.py:13-72`); auditoría crea hasta 3.000 celdas (`src/presentation/forms/auditoria_guardias_form.py:124-187`).
- **Evidencia/actual:** QTableWidget materializa items; sin paginación/modelo lazy; los métodos se llaman desde constructores/slots. Positivo: views lazy y WorkerThread para operaciones largas.
- **Reproducción:** fixture 1.000 profesores/10.000 guardias/500 logs; medir event-loop stalls al abrir/filtrar/refrescar.
- **Esperado/impacto/frecuencia:** primer feedback <100 ms y sin congelaciones perceptibles; con centros/datos crecientes se degrada.
- **Causa/patrón:** acceso y render sincronizados, modelo item-based, filtros O(n) por tecla.
- **Recomendación:** `$impeccable optimize`; medir primero, luego QTableView/model, paginación/chunking, debounce y workers con cancelación; no optimizar tablas pequeñas sin datos.
- **Archivos/datos/compatibilidad/seguridad:** presentación/repos de lectura; sin migración necesaria; cuidar lifetime de sesión entre hilos.
- **Prueba:** benchmark pytest-qt p50/p95, contador de eventos UI y cancelación; presupuesto explícito.
- **Criterios:** [ ] dataset objetivo documentado; [ ] ninguna tarea UI >100 ms sin feedback; [ ] scroll/filtro fluido; [ ] carga cancelable; [ ] memoria acotada; [ ] selección/foco se preservan.
- **Esfuerzo/dependencias/producción/documentación:** L; perf baseline antes; no; presupuesto de rendimiento.

### [UXA-012] La suite A11Y actual puede quedar verde con cobertura insuficiente o skip amplio

- **Estado/categoría/tipo:** NUEVO / QA accesibilidad / deuda. **Severidad/prioridad/confianza:** P2 / alta / alta.
- **Requisito:** gate Ola 4; EN 301 549 requiere inspección funcional, no solo presencia de nombres.
- **Superficie:** `tests/test_a11y_regression.py` y ausencia de matriz manual.
- **Ubicación:** helper solo compara nombres (`tests/test_a11y_regression.py:34-55`); cubre tres diálogos y un widget; captura cualquier error como skip (`tests/test_a11y_regression.py:160-185`).
- **Evidencia/actual:** 5 passed/1 skipped, pero no prueba 10 vistas, 12 tablas, focus visible/order global, errores, contrastes, escalado, announcements, QAccessible roles ni AT real.
- **Reproducción:** eliminar un foco visual o romper un label fuera de esos diálogos: suite seguirá verde.
- **Esperado/impacto/frecuencia:** gates por inventario y evidencia manual; falsos verdes permiten regresiones.
- **Causa/patrón:** A11Y-BASIC orientado a unos nombres, sin manifiesto de cobertura.
- **Recomendación:** `$impeccable audit`; test parametrizado de todas las superficies, skips solo por causa concreta y plan manual NVDA/VoiceOver/Orca.
- **Archivos/datos/compatibilidad/seguridad:** tests/fixtures; sin datos productivos; usar fixtures sintéticas.
- **Prueba:** el propio gate debe fallar al introducir mutantes de nombre/foco/status/contraste.
- **Criterios:** [ ] 10/10 vistas y 21/21 diálogos asignados; [ ] cero `except Exception: skip`; [ ] teclado/foco/roles/nombres/status/resize cubiertos; [ ] skips contabilizados; [ ] sesión AT documentada por SO soportado.
- **Esfuerzo/dependencias/producción/documentación:** L; acompaña cada fix; no; checklist accesible versionada.

### [UXA-013] La navegación pierde título/contexto y estado accesible, sobre todo colapsada

- **Estado/categoría/tipo:** NUEVO / Arquitectura de información + navegación / deuda. **Severidad/prioridad/confianza:** P2 / media / alta.
- **Requisito:** WCAG 2.4.6, 4.1.2; EN 301 549 11.4.1.2 y 11.5.2.5/15.
- **Superficie:** MainWindow/Sidebar.
- **Ubicación:** `ContentWrapper` recibe `title` pero no lo renderiza ni lo guarda (`src/presentation/ccleaner_main_window.py:45-68`); activo se expresa como propiedad visual (`src/presentation/components/ccleaner_sidebar.py:304-366`); colapso borra texto y deja tooltip (`src/presentation/components/ccleaner_sidebar.py:570-591`).
- **Evidencia/actual:** no hay encabezado uniforme; botón activo no es checkable/selected accesible; al colapsar se ejecuta `setText("")` sin `accessibleName`; cambiar stack no enfoca/anuncia título.
- **Reproducción:** colapsar Ctrl+B y recorrer sidebar con lector; cambiar sección; escuchar nombre/estado/contexto.
- **Esperado/impacto/frecuencia:** nombre estable, current/selected anunciado, título de vista y foco predecible; desorientación moderada continua.
- **Causa/patrón:** estado y contexto solo visuales.
- **Recomendación:** `$impeccable clarify` + `$impeccable harden`; conservar accessibleName, usar checked/current semántico y encabezado común; anunciar cambio sin forzar foco salvo necesidad.
- **Archivos/datos/compatibilidad/seguridad:** MainWindow/Sidebar; sin datos; compatible.
- **Prueba:** sidebar expandida/colapsada, lectura de name/state, cambio de las 10 vistas y retorno de foco.
- **Criterios:** [ ] 10 botones mantienen nombre en ambos modos; [ ] activo se anuncia; [ ] cada vista tiene título único visible/accesible; [ ] cambio se anuncia una vez; [ ] Tab order no salta a controles ocultos.
- **Esfuerzo/dependencias/producción/documentación:** M; junto a UXA-002; no; contrato Navigation.

### [UXA-014] Persisten anti-patrones Impeccable y tipografía microscópica

- **Estado/categoría/tipo:** NUEVO / Polish / mejora. **Severidad/prioridad/confianza:** P3 / baja / alta.
- **Requisito:** prohibiciones Impeccable: side-stripe accents, hero metrics y texto desbordado; product register: densidad legible.
- **Superficie:** info boxes, métricas, calendario y gráficos.
- **Ubicación:** side stripes `src/presentation/themes/ccleaner_theme.py:629-664`; metric cards `src/presentation/widgets/panel_estadisticas.py:87-117`; fuentes 7–9 `src/presentation/widgets/_celda_dia.py:117-159,270-381` y `src/presentation/widgets/bar_chart_widget.py:91-123,139-198`.
- **Evidencia/actual:** 56 ocurrencias de 7–10 px; tarjeta de métrica repetida; bordes laterales de 4 px; calendario concentra mucha información en texto minúsculo.
- **Reproducción:** abrir calendario/estadísticas a DPI alto y comparar legibilidad/jerarquía.
- **Esperado/impacto/frecuencia:** densidad sin sacrificar lectura; impacto de polish y fatiga, no bloqueo aislado.
- **Causa/patrón:** compresión espacial y decoración heredada.
- **Recomendación:** `$impeccable typeset` + `$impeccable quieter`; reemplazar stripes por borde/fondo completo, reducir card scaffolding y establecer suelo tipográfico validado.
- **Archivos/datos/compatibilidad/seguridad:** UI; sin datos; revisar redimensionado.
- **Prueba:** snapshots a 100/150/200 %, legibilidad y no overflow.
- **Criterios:** [ ] ningún texto informativo esencial usa 7–9 px; [ ] side stripes >1 px eliminados; [ ] métricas conservan jerarquía sin grid clonado; [ ] calendario no recorta nombres/estados esenciales.
- **Esfuerzo/dependencias/producción/documentación:** M; tras UXA-001/010; no; tokens tipográficos.

## Patrones sistémicos

1. **Accesibilidad opt-in:** se añaden nombres/orden a algunos diálogos, pero no existe contrato ni gate por control/superficie.
2. **Estado visual sin notificación:** active, status, dirty, success/error y cambios de datos carecen de una política accesible unificada.
3. **Layout diseñado para el monitor del autor:** tamaños grandes/fijos y texto pequeño conviven, penalizando portátiles y ampliación.
4. **Tres capas de tema:** tokens existen, pero QSS global de app, QSS del main window y estilos inline compiten; esto dificulta contraste/foco/tema oscuro.
5. **QTableWidget como solución universal:** no hay contrato de caption, embedded controls, states, paginación o dataset límite.
6. **Modales como respuesta por defecto:** 51 QMessageBox y 21 QDialog; varios errores de campo podrían ser inline/progresivos.

## Aspectos positivos a preservar

- Uso mayoritario de widgets Qt estándar, que ya exponen roles/acciones de plataforma.
- Orden de tabulación y foco en error bien implementados en autenticación/perfiles (`src/presentation/dialogs/dialogo_crear_perfil.py:126-163`; `src/presentation/forms/change_password_dialog.py:89-139`).
- Botones destructivos de varios flujos usan default seguro `No/Cancel` (`src/presentation/widgets/selector_curso_widget.py:118-149`; `src/presentation/forms/base_form.py:194-212`).
- `ContentWrapper` introduce scroll en ambos ejes como red de seguridad (`src/presentation/ccleaner_main_window.py:52-68`).
- Carga perezosa de las 10 vistas reduce el arranque (`src/presentation/ccleaner_main_window.py:139-177`).
- Hay workers con progreso/cancelación para sincronización y tareas largas (`src/presentation/widgets/progress_worker.py:16-113`; `src/presentation/widgets/sync_progress_dialog.py:24-49`).
- Profesor desactiva sorting durante carga y lo restaura al final, evitando trabajo repetido (`src/presentation/forms/profesor_table_helpers.py:13-72`).
- Perfiles ofrece el mejor patrón de tabla nombrada y solo lectura (`src/presentation/forms/perfiles_usuario_form.py:210-235`).
- Las estadísticas incluyen tablas textuales además de gráficos; deben asociarse, no eliminarse.
- Colores del heatmap se acompañan de valores numéricos, evitando depender exclusivamente del color.

## Limitaciones y NO VERIFICADO

- **NO VERIFICADO:** NVDA/JAWS en Windows, VoiceOver en macOS y Orca en Linux; impide afirmar operabilidad real con lector.
- **NO VERIFICADO:** teclado exhaustivo, foco inicial/trap/retorno/Escape de los 21 diálogos; Qt aporta comportamiento base, pero estilos y controles personalizados requieren inspección.
- **NO VERIFICADO:** render real en macOS 11+, Windows 10+ y Ubuntu 20.04+, DPI 100/125/150/200 %, alto contraste y temas del SO.
- **NO VERIFICADO:** contraste de colores renderizados tras la cascada completa; solo se midieron pares inequívocos del código.
- **NO VERIFICADO:** benchmarks de datasets representativos; UXA-011 tiene confianza media.
- **NO VERIFICADO:** `prefers-reduced-motion` no aplica como CSS web; no se observó animación significativa, pero debe comprobarse cualquier progreso/transición en ejecución.
- `PRODUCT.md`/`DESIGN.md` ausentes; no existe contrato de resolución mínima, tema oscuro, AT soportada ni política de densidad.

## Lotes recomendados para modelos de remediación

| Orden | Lote | IDs | Comando | Riesgo | Gate mínimo |
| ---: | --- | --- | --- | --- | --- |
| 1 | Estado correcto al cambiar curso | UXA-007 | `$impeccable harden` | medio | test integración A→B→A en vistas cargadas/no cargadas |
| 2 | Prevención de pérdida | UXA-004 | `$impeccable harden` | medio | matriz dirty×salida×decisión |
| 3 | Fundamentos accesibles | UXA-002/005/006/013 | `$impeccable harden` | alto | teclado + QAccessible + errores por campo |
| 4 | Adaptabilidad | UXA-001/008 | `$impeccable adapt` | alto | resolución/DPI y tablas prioritarias |
| 5 | Status/overlay | UXA-003 | `$impeccable harden` | medio | anuncios, persistencia, texto largo, contraste |
| 6 | Sistema visual | UXA-010/014 | `$impeccable document`, luego `$impeccable colorize` y `$impeccable typeset` | alto | theme/contrast/focus snapshots |
| 7 | Datos visuales y rendimiento | UXA-009/011 | `$impeccable optimize` + `$impeccable harden` | medio | dataset límite + alternativa accesible |
| 8 | Ratchet de QA | UXA-012 | `$impeccable audit` | bajo | inventario 1:1, cero skips amplios, AT manual |
| 9 | Cierre | todos | `$impeccable polish` | medio | reauditoría completa Ola 4 sobre mismo commit |

Puede ejecutarse cada lote por separado o en el orden indicado. Tras los fixes, repetir `$impeccable audit` y no cerrar accesibilidad solo con tests automáticos.

## Contabilidad de salida

- **Vistas recibidas/procesadas:** 10/10 registradas; 1 DashboardForm adicional detectado pero no registrado en la navegación principal.
- **Form controls inventariados/procesados:** 128/128 por sitio de construcción, agrupados en este paquete; validación profunda representativa, no ejecución campo a campo con AT.
- **Tablas/columnas:** 12/12; 69 columnas estáticas + dos esquemas dinámicos.
- **Diálogos:** 21/21 inventariados; inspección manual de foco no ejecutada.
- **Candidatos aceptados:** 14; P0/P1 escalados: 0/7.
- **Producción pendiente:** N/A para esta auditoría local de escritorio; build distribuida no verificada.
- **Archivo actualizado por este paquete:** `auditoria/_work/paquete_ux_accesibilidad.md` exclusivamente.
- **Próximo gate:** adjudicación/deduplicación L3 con los otros paquetes, seguida de Lote 1 y matriz manual de accesibilidad.
