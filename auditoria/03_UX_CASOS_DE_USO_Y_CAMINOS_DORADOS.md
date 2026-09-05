---
tags:
  - gestion-centro
  - auditoria
  - ux
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# UX: casos de uso, caminos dorados, presupuesto de clics y guardarraíles

## 1. Actores

| Actor | Descripción | Frecuencia de uso |
| --- | --- | --- |
| Jefatura / responsable de guardias | Configura el curso, genera y mantiene el calendario, gestiona ausencias, exporta y comunica | Diaria en septiembre, semanal después |
| Profesorado | Recibe su calendario (PDF, email, iCal). No usa la app | Consulta |
| Administrador local | Configura SFTP/SMTP, perfiles, actualiza la app | Puntual |

## 2. Catálogo de casos de uso

| ID | Caso de uso | Precondiciones | Resultado | Vista actual |
| --- | --- | --- | --- | --- |
| CU-01 | Primer arranque y configuración de conectividad | Instalación | SFTP/SMTP guardados en `.env` | `InitialConfigDialog` |
| CU-02 | Iniciar sesión / crear perfil | CU-01 | BD del usuario abierta y sincronizada | `LoginDialog`, `PerfilesUsuarioForm` |
| CU-03 | Crear o activar curso escolar | CU-02 | Curso activo | `GestionCursosWidget`, `SelectorCursoWidget` |
| CU-04 | Configurar fechas, recreos, festivos y factores | CU-03 | `Configuracion` completa | `AjustesForm` |
| CU-05 | Definir zonas de vigilancia | CU-03 | ≥1 zona activa | `ZonaForm` |
| CU-06 | Alta/importación de profesorado con restricciones | CU-03, CU-05 (zona preferida) | Profesores activos con horario | `ProfesorForm`, `ImportExportForm` |
| CU-07 | Calcular cuotas | CU-04, CU-05, CU-06 | Cuotas por profesor | `CalculoPanel` |
| CU-08 | Generar calendario de guardias | CU-07 | Guardias persistidas, resumen, equidad | `GeneracionPanel` |
| CU-09 | Revisar calendario (mes/semana/año, filtros) | CU-08 | Verificación visual | `VistaCalendario` |
| CU-10 | Registrar ausencia y cubrir sustituciones | CU-08 | Guardias reasignadas, historial | `AusenciasSustitucionesWidget` |
| CU-11 | Exportar PDF (mes/curso/individual), iCal, JSON | CU-08 | Ficheros | `ReportesForm`, `ImportExportForm` |
| CU-12 | Notificar por email | CU-08, SMTP | Emails enviados | `GeneracionPanel._enviar_notificaciones` |
| CU-13 | Analizar estadísticas y equidad | CU-08 | Tablas, gráficos, heatmap | `PanelEstadisticas` |
| CU-14 | Auditar cambios de guardias | CU-08 | Registro filtrable | `AuditoriaGuardiasForm` |
| CU-15 | Cambiar de curso | ≥2 cursos | Todas las vistas con datos del curso | `SelectorCursoWidget` |
| CU-16 | Cerrar la app con sincronización | Sesión abierta | JSON subido, bloqueo liberado | `CCleanerMainWindow.closeEvent`, `main.py` |
| CU-17 | Actualizar la app | Release publicada | Nueva versión instalada | `update_checker`, banner sidebar |

## 3. Secuencia obligatoria y guardarraíles

La app **no** hace visible la secuencia. El README la describe (`README.md:33-39`), pero la ventana abre en *Profesores* (`src/presentation/ccleaner_main_window.py:118`) y la sidebar ordena Profesores → Zonas → Ajustes → Perfiles → Cálculo → Calendario → Ausencias → Importar → Reportes → Estadísticas (`src/presentation/components/ccleaner_sidebar.py:178-216`). Un usuario nuevo empieza por profesores sin haber creado zonas ni configurado el curso.

### Matriz de prerrequisitos

| Acción | Requiere | Cómo lo impone la app hoy | Hueco | Propuesta |
| --- | --- | --- | --- | --- |
| Crear profesor con zona preferida | ≥1 zona | Combo vacío | Silencioso | Aviso inline "Aún no hay zonas → Crear zona" |
| Calcular cuotas | Configuración con fechas y recreos, ≥1 profesor activo | `CalculoPanel.calcular_cuotas` muestra QMessageBox de error (`calculo_panel.py:177-210`) | Reactivo, después de pulsar | Botón deshabilitado con motivo visible y enlace; panel de estado |
| Generar asignación | Cuotas calculadas en esta sesión de UI, ≥1 zona activa, festivos cargados | Flag de sesión: `generar_button.setEnabled(False)` hasta señal `cuotas_calculadas` (`generacion_panel.py:156-163,190-205`) | El flag no representa el dominio: se pierde al cambiar de vista/curso, y no comprueba zonas ni fechas del curso; `cargar_datos()` no rehabilita | `PreflightGeneracion` en `application/`: devuelve lista de faltantes con enlace a vista; la UI sólo pinta |
| Limpiar guardias | Guardias existentes | Confirmación con *No* por defecto (`generacion_panel.py:397-411`) | Botón junto al primario, mismo tamaño | Acción secundaria en menú "Más" o al pie, en rojo sólo el texto |
| Registrar ausencia | Guardias generadas para ese profesor en el rango | Búsqueda devuelve vacío | Mensaje vacío genérico | Estado vacío explicativo: "No hay guardias en ese rango" + sugerencias |
| Exportar/Enviar | Guardias generadas | Diálogo de error si vacío | Reactivo | Deshabilitar con motivo |
| Enviar emails | SMTP configurado, emails corporativos | Modal "SMTP no configurado" (`generacion_panel.py:340-350`) | Reactivo, sin enlace | Botón con estado "Configurar SMTP" que navega a Ajustes |
| Cambiar de curso | Sin cambios pendientes | Confirmación modal | No detecta dirty; no refresca vistas (UXA-007) | Guard central de dirty + refresco atómico |
| Cerrar app | Sync realizada | Pregunta si >5 min desde última sync | Correcto; bloquea GUI en `closeEvent` con `dlg.exec()` sin cancelar | Mantener; añadir cancelación y tiempo máximo |

### Guardarraíl propuesto: panel "Estado del curso"

Vista inicial (sustituye a abrir en Profesores) con una lista de pasos con estado calculado desde dominio:

```
1. Curso activo 2025-2026              ✔
2. Fechas y recreos configurados       ✔  (4 recreos, 2 turnos)
3. Zonas de vigilancia                 ✔  5 activas
4. Profesorado                         ⚠  38 activos · 3 sin horario → Revisar
5. Cuotas calculadas                   ✘  → Calcular
6. Calendario generado                 ✘  (requiere 5)
7. Ausencias pendientes de cubrir      –
```

Cada línea es un botón que navega a la vista correspondiente con el foco en el control adecuado. El mismo servicio alimenta los botones deshabilitados del resto de vistas, de modo que la regla vive en un único sitio (`application/use_cases/preflight`).

## 4. Caminos dorados y presupuesto de clics

Se cuenta cada clic de ratón o pulsación equivalente que el usuario debe hacer desde que decide la tarea hasta ver el resultado. Los diálogos de fichero cuentan 2 (navegar + aceptar). Cifras actuales derivadas del código; se recomienda confirmarlas con grabación de sesión.

| Camino | Pasos actuales | Clics hoy | Objetivo | Cómo llegar |
| --- | --- | ---: | ---: | --- |
| GP-1 Generar guardias (curso configurado) | Sidebar Cálculo (1) → Generar (1) → modal resumen *OK* o *Sí/No* (1) → esperar → *Cerrar* progreso (1) → Sidebar Calendario (1). Desde v5.56.0 ya no hace falta pulsar «Calcular cuotas» antes: el permiso lo dan los datos | 5 | 3 | Cuotas se recalculan automáticamente si los datos cambiaron; resumen previo inline (no modal); el diálogo de progreso se cierra solo al acabar y muestra tarjeta de resultado con botón "Ver calendario" |
| GP-2 Registrar ausencia y cubrirla | Sidebar Ausencias (1) → combo profesor (2) → fecha inicio (2) → fecha fin (2) → Buscar (1) → Auto-asignar (1) → Guardar (1) → confirmación (1) | 11 | 6 | Fecha fin = inicio por defecto; buscar automático al cambiar filtros; auto-asignar como acción por defecto de Guardar; confirmación sustituida por toast con "Deshacer" |
| GP-3 Exportar PDF del mes para todos | Sidebar Reportes (1) → tipo (2) → mes (2) → Exportar (1) → carpeta (2) → aceptar aviso (1) | 9 | 4 | Mes actual por defecto; recordar carpeta; abrir carpeta al terminar en vez de modal |
| GP-4 Alta de profesor | Sidebar Profesores (1) → Nuevo (1) → nombre, horas, turno, tutor (≥4 campos) → Guardar (1) → *OK* modal (1) | 4 + campos | 3 + campos | Éxito por toast; foco vuelve a Nuevo para altas encadenadas; Ctrl+N/Ctrl+S |
| GP-5 Cambiar de curso | Selector (2) → confirmar (1) | 3 (+ reinicio para ver datos correctos) | 2 | Corregir UXA-007; confirmación sólo si hay cambios sin guardar |
| GP-6 Cerrar con sincronización | X (1) → *Sí* (1) → esperar | 2 | 1 | Sincronizar en segundo plano al guardar; al cerrar sólo si hay pendientes |
| GP-7 Enviar emails de guardias | Cálculo (1) → Enviar emails (1) → resultado modal (1) | 3 | 3 | Correcto; añadir vista previa y progreso en worker (FUN-006) |
| GP-8 Primer uso completo | CU-01…CU-09 | > 40 | < 25 | Asistente de primer curso con pasos y plantilla de curso anterior (FUN-005) |

### Reglas de presupuesto

- Toda tarea frecuente (GP-1, GP-2, GP-3) ≤ 6 clics y ≤ 1 diálogo modal.
- Ningún modal informativo que sólo tenga *OK*: convertir en toast o texto inline.
- Confirmar sólo destrucción irreversible (limpiar guardias, eliminar profesor/zona, eliminar perfil).
- Un diálogo de progreso no debe requerir clic para cerrarse cuando termina bien.

## 5. Hallazgos de flujo (UXF)

| ID | Sev. | Título | Evidencia |
| --- | --- | --- | --- |
| UXF-001 | P1 | No existe secuencia guiada ni panel de estado del curso · **panel DESCARTADO v5.57.0 por decisión de producto**: la guía de prerrequisitos se lee en el aviso de bloqueo del panel de generación, no en una pantalla propia | `ccleaner_main_window.py:118`, `ccleaner_sidebar.py:178-216`, `README.md:33-39` |
| ~~UXF-002~~ ✅ **v5.56.0** | P1 | ~~El guardarraíl "cuotas antes de generar" es un flag de UI~~ · resuelto con `PreflightGeneracionUseCase` | `generacion_panel.py:156-163,190-205`, `asignacion_calculo_form.py:53-58,151-155` |
| UXF-003 | P2 | Generar requiere 2 modales previos y 1 clic de cierre; resumen previo debería ser inline | `generacion_panel.py:263-292` |
| UXF-004 | P2 | Cambio de curso: confirmación + toast pero sin refresco (ver UXA-007) | `selector_curso_widget.py:118-166` |
| ~~UXF-005~~ ✅ **v5.56.0** | P2 | ~~Primer arranque exige SFTP~~ · se ofrece trabajar solo en este equipo, con aviso permanente | `main.py:120-134`, `initial_config_dialog.py:641-665` |
| UXF-006 | P2 | "Limpiar guardias" comparte fila, tamaño y prominencia con "Generar" | `generacion_panel.py:165-176` |
| UXF-007 | P2 | Sin protección de cambios sin guardar (duplica UXA-004 a efectos de flujo) | `base_form.py:29-86` |
| ~~UXF-008~~ ✅ **v5.56.0** | P3 | ~~Motivo de bloqueo sólo en tooltip~~ · etiqueta visible con los requisitos que faltan | `generacion_panel.py:163,203` |
| UXF-009 | P2 | Ausencias: sin deshacer ni vista previa del impacto de la reasignación | `ausencias_sustituciones.py:426-497` |
| UXF-010 | P2 | Cinco variantes de exportación PDF con diálogo de fichero cada una y sin recordar carpeta | `reportes_form.py:205-444` |
| UXF-011 | P3 | Sólo un atajo global (Ctrl+B); sin Ctrl+N/Ctrl+S/Escape consistentes | `ccleaner_sidebar.py:62-65`, `profesor_form.py:351-360` |

## 6. Estados de cada vista (contrato)

| Estado | Regla |
| --- | --- |
| Cargando | Skeleton o barra indeterminada en < 100 ms; nunca congelar |
| Vacío | Título + explicación + acción primaria ("Crear la primera zona") |
| Bloqueado por prerrequisito | Texto del motivo + enlace a la vista que lo resuelve |
| Error | Qué pasó, qué hacer, botón reintentar; detalles técnicos plegados |
| Éxito | Toast no modal 4 s con "Deshacer" cuando aplique |
| Sucio | Indicador en título de vista y guard al salir |

## 7. Tests que fijan estas reglas

Ver [[08_ESTRATEGIA_DE_TESTS]] y `tests/audit/test_guardarrailes_flujo.py`: los tests marcados `xfail(strict=True)` documentan el comportamiento objetivo y pasan a fallar (obligando a retirar la marca) cuando el fix llega.
