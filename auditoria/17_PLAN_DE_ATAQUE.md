---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-05
estado: activo
prioridad: 1-urgente
tipo: referencia
---

# Plan de ataque (backlog único)

> [!NOTE] Uso
> Cada lote es reversible y se verifica con los tests indicados. Al completar un ítem, tacharlo aquí (`~~texto~~ ✅ RESUELTO vX.Y.Z`) y actualizar [[30_REGISTRO_HALLAZGOS]] en el mismo commit. Un lote = una versión (patch o minor).

| Orden | Lote | IDs | Resultado esperado | Sev. máx. | Riesgo | Esfuerzo | Depende de | Tests / gates | Estado |
| ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | **Diagnóstico Windows** | ~~CRW-006~~, ~~BLD-007~~ | `faulthandler` activo y build `-Diagnostico` ✅ **v5.44.0**. Falta ejecutar el protocolo en el PC Windows y confirmar la causa | P2 | bajo | XS+S | – | log + Visor de eventos adjuntos al registro | **parcial** — bloqueado por acceso a Windows |
| ~~0 bis~~ | ~~**La nube es la copia buena**~~ ✅ **v5.47.0** | SYNC-001…008, SYNC-010, SYNC-012, SYNC-014, SYNC-015 | Nunca caer a local en silencio; probar conexión al configurar; al abrir, reconstruir la base local desde la nube; sin descarga no hay subida; número de versión; subida atómica; versiones guardadas; bloqueo que falla cerrado | P0 | medio | M/L | – | 10 escenarios en `tests/audit/test_sincronizacion_nube.py` | **completado** |
| ~~0 ter~~ | ~~**Cuenta de verdad**~~ ✅ **v5.48.0** | SYNC-009, SYNC-013 | La ficha de la cuenta vive junto a los datos del usuario y se valida al entrar; las credenciales salen del fichero de datos. **Requisito**, no mejora: es lo único que separa los datos de una persona de los de otra | P0 | medio | M | 0 bis | verificado contra el servidor real y con tests de dos equipos | **completado** |
| ~~1~~ | ~~**Frontera solver↔Qt y cancelación**~~ ✅ **v5.52.0** | ~~CRW-001~~, ~~CRW-004~~, ~~CRW-002~~, ~~CRW-008~~ | Ningún callback de OR-Tools toca Qt; cancelar detiene el solver en < 2 s; log en vivo vía señal en cola | P0 | medio | M | 0 | 11 tests de `test_crash_windows_regresion.py` en verde (quedan 3 xfail, todos del lote 2) | **completado** — falta confirmar en Windows |
| 2 | **Hilos seguros** | CRW-005, CRW-007, CRW-009 | excepthook thread-aware; sync post-generación en worker; commit del audit log | P1 | bajo | S | 1 | ídem + `test_excepthook_no_crea_widgets_fuera_del_hilo_gui` | pendiente |
| 3 | **Sesión por hilo (generación y sync)** | CRW-003 (parcial), ESC-003 (parcial) | `SessionFactory` inyectada; worker de generación y `SyncWorker` con sesión propia; DTOs a la GUI | P1 | alto | L | 2 | `test_worker_no_reutiliza_sesion_gui`; suite completa; BD en fichero | pendiente |
| 4 | **Suite ejecutable de una pasada** | ~~QA-008~~, QA-001, QA-002, QA-003, QA-005, QA-009, QA-010 | Guarda de diálogos modales ✅ **v5.44.0**: 2.454 tests pasan de una pasada en 47 s. Falta `make venv` con todas las deps, `xfail_strict`, y migrar los tests del formulario muerto | P1 | bajo | M | – | `pytest tests/` termina sin bloqueos ✅; 0 fallos ✅ | **parcial** |
| 5 | **Build reproducible** | BLD-001, BLD-002, BLD-003, BLD-005 | Specs versionados; un script por plataforma; versión única; actualizador multiplataforma | P1 | bajo | S | – | `test_version_unica`; build en ambas plataformas | pendiente |
| 6 | **Preflight y panel de estado** | UXF-001, UXF-002, UXF-008, FUN-001 | Caso de uso `PreflightGeneracion`; vista Inicio con checklist; botones con motivo | P1 | medio | M | 3 | `tests/audit/test_guardarrailes_flujo.py` sin xfail; GP-1 ≤ 3 clics | pendiente |
| 7 | **Refresco de curso y dirty state** | UXA-007, UXA-004, UXF-004 | `ContentWrapper` expone widget; refresco atómico; guard central | P1 | medio | M | 6 | spies por vista A→B→A; matriz dirty×salida | pendiente |
| 8 | **Sistema de diseño base** | VIS-001, VIS-002, VIS-003, VIS-009, UXA-010 | `app.qss` desde tokens; fuente por SO; mínimo 1024×700; contrastes AA | P2 | alto | L | – | ratchets a cero (hex, font-size); snapshots | pendiente |
| 9 | **Componentes y feedback** | VIS-004, VIS-005, VIS-006, VIS-007, VIS-008, UXA-003, UXA-013 | `ViewHeader`, variantes de botón, iconos sin emoji, `ResultCard`, feedback único | P2 | medio | L | 8 | tests de componente; a11y | pendiente |
| 10 | **Clics y caminos dorados** | UXF-003, UXF-006, UXF-010, UXF-011, UXF-009 | GP-1/2/3 dentro de presupuesto; atajos; recordar carpeta; deshacer en ausencias | P2 | bajo | M | 9 | tests de flujo con cuenta de clics | pendiente |
| 11 | **Accesibilidad de formularios y tablas** | UXA-001, UXA-002, UXA-005, UXA-006, UXA-008, UXA-012 | FormField, foco visible, errores por campo, tablas con nombre | P1 | alto | L | 8 | introspección QAccessible; sesión NVDA/VoiceOver | pendiente |
| 12 | **Escalabilidad de datos** | ESC-001, ESC-005, UXA-011, UXA-009 | QTableView + modelo; caché por curso; gráficos accesibles | P2 | medio | L | 9 | benchmark 1.000 profesores; p95 < 100 ms | pendiente |
| 13 | **Solver escalable** | ESC-002, FUN-013, FUN-014 | workers = CPUs, timeout configurable, descomposición, diagnóstico por slot | P2 | medio | L | 1 | `tests/compliance` + benchmark | pendiente |
| 14 | **Calidad de código** | COD-001…008 | ruff limpio, jerarquía de excepciones, sin ORM en presentación, código muerto fuera, mypy en application | P2 | bajo | L (por lotes) | – | ruff/mypy/vulture/import-linter en CI | pendiente |
| 15 | **CI y firma** | BLD-004, BLD-006, SEC-001, SEC-002, SEC-003 | workflow matriz; notarización; keyring; API fail-closed | P2 | medio | M | 5 | pipeline verde; artefactos publicados | pendiente |
| 16 | **Funcionalidad** | FUN-002, FUN-004, FUN-005, FUN-006, FUN-007, FUN-012 | Generación incremental, historial/restauración, plantilla de curso, emails en worker, dry-run import, deshacer | – | medio | XL | 3, 6 | por feature | decisión de producto |
| 17 | **Multiusuario y consulta web** | ESC-004, FUN-009, FUN-010, FUN-011 | ADR; API como servicio; consulta web; tema oscuro; auto-update Windows | – | alto | XL | 15 | Playwright E2E | decisión de producto |

## Decisiones requeridas de CarlosFB

0. ~~**Sincronización:** ¿uno cada vez o edición simultánea?~~ **Resuelto: uno cada vez.** Bastan los lotes 0 bis y 0 ter; la fusión real queda descartada.
1. ~~¿Modo local sin SFTP en el primer arranque (UXF-005)?~~ **Resuelto 2026-09-05: sí**, con aviso persistente mientras la nube no esté configurada. UXF-005 pasa a formar parte del lote 6.
2. ~~¿Paleta: #007ACC o #0E5FA8?~~ **Resuelto 2026-09-05: #0E5FA8** (6,5:1 con texto blanco frente a 4,5:1 del actual, que se queda justo en el mínimo AA y no deja margen para estados hover/pressed ni para el anillo de foco). Coincide con el contrato de [[05_CONTRATO_SISTEMA_DE_DISENO]], que no hay que retocar.
3. ~~¿Fuente por SO o embebida?~~ **Resuelto 2026-09-05: por SO** — Segoe UI en Windows, SF Pro en macOS, sin licencias y con render nativo.
4. ~~¿Generación incremental (FUN-002) antes que edición manual (FUN-003)?~~ **Resuelto 2026-09-05: incremental primero**, y antes que ninguna de las dos, FUN-004 (historial y restauración): es esfuerzo M, no depende de nada y ya cubre hoy el miedo real de que "Generar" borre el curso entero. Orden acordado: FUN-004 → FUN-002 → FUN-003.
5. ~~¿Cuenta Apple Developer para notarizar?~~ **Resuelto 2026-09-05: hay cuenta, hoy inactiva.** La notarización del lote 15 queda condicionada a reactivar la suscripción; mientras tanto se documenta el paso "Abrir de todos modos" en las instrucciones de instalación de macOS.

## Próximo gate

Dos frentes, independientes entre sí:

1. **Lote 2** (hilos seguros, CRW-005/007/009) — siguiente frente. Es corto (esfuerzo S), no depende de tener Windows delante y cierra el otro camino por el que un fallo en un hilo secundario puede tumbar el proceso: el `excepthook` que construye un `QMessageBox` desde cualquier hilo. Sus tres tests ya están escritos en xfail.
2. **Lote 0** en la máquina Windows: compilar con `scripts/build_windows.ps1 -Diagnostico` y ejecutar el protocolo de [[06_CRASH_WINDOWS_GENERACION]] §5. Ahora tiene más valor que antes: con la frontera solver↔Qt ya cerrada, si el cierre desaparece se confirma CRW-001 como causa, y si persiste queda señalado CRW-003/005.
