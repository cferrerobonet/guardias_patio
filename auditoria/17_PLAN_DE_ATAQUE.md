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
| ~~2~~ | ~~**Hilos seguros**~~ ✅ **v5.53.0** | ~~CRW-005~~, ~~CRW-007~~, ~~CRW-009~~ | excepthook consciente del hilo; sync post-generación en worker; commit del audit log; cancelar deja de anunciarse como error | P1 | bajo | S | 1 | 16 tests de `test_crash_windows_regresion.py` en verde, sin ningún xfail | **completado** |
| ~~3~~ | ~~**Sesión por hilo (generación y sync)**~~ ✅ **v5.55.0** | ~~CRW-003~~, ESC-003 (parcial) | Fábrica de sesiones inyectable; generación, `SyncWorker` y las seis tareas del worker con sesión propia; guardarraíl por AST | P1 | alto | L | 2 | `test_worker_no_reutiliza_sesion_gui` ✅, `test_dos_sesiones_sobre_la_misma_bd_en_fichero` ✅, suite completa ✅ | **completado** |
| ~~4~~ | ~~**Suite ejecutable de una pasada**~~ ✅ **v5.54.0** | ~~QA-008~~, ~~QA-001~~, ~~QA-002~~, ~~QA-003~~, ~~QA-005~~, ~~QA-009~~, ~~QA-010~~ | `make venv` y objetivos del Makefile con el intérprete correcto; cobertura fuera de `addopts`; `xfail_strict`; tests migrados al formulario vivo; ningún xfail dependiente del orden | P1 | bajo | M | – | **2.503 tests pasan de una pasada en 51 s, cero fallos, sin variables de entorno** | **completado** — queda separar deps de ejecución y desarrollo (al lote 15) |
| 5 | **Build reproducible** | BLD-001, BLD-002, BLD-003, BLD-005 | Specs versionados; un script por plataforma; versión única; actualizador multiplataforma | P1 | bajo | S | – | `test_version_unica`; build en ambas plataformas | pendiente |
| ~~6~~ | ~~**Preflight y guardarraíles**~~ ✅ **v5.56.0** / v5.57.0 | ~~UXF-002~~, ~~UXF-008~~, ~~UXF-005~~, UXF-001 (parcial), FUN-001 (descartado) | `PreflightGeneracionUseCase`; motivo de bloqueo visible y detallado; modo local con aviso permanente. El panel de estado se construyó y se retiró: decisión de producto de CarlosFB | P1 | medio | M | 3 | `test_guardarrailes_flujo.py` sin xfail (11 tests) ✅. GP-1 baja de 6 a 5 clics; llegar a 3 es UXF-003, del lote 10 | **completado** |
| ~~7~~ | ~~**Refresco de curso y dirty state**~~ ✅ **v5.59.0** | ~~UXA-007~~, ~~UXA-004~~, ~~UXF-004~~ | `ContentWrapper` expone widget (v5.49.0); refresco atómico; guard central de cambios sin guardar en navegación, cierre y cambio de curso | P1 | medio | M | 6 | matriz sucio×salida×decisión en `test_cambios_sin_guardar.py` (16 tests) ✅ | **completado** |
| 8 | **Sistema de diseño base** | ~~VIS-002~~, ~~VIS-003~~, ~~VIS-009~~, VIS-001 (parcial), UXA-010 (parcial) | Hoja central construida desde tokens ✅; paleta única `#0E5FA8` ✅; fuente por SO ✅; mínimo 1024×700 ✅; tamaños ≥ 12 px ✅. **Queda 8 bis** | P2 | alto | L | – | `font_size_menor_12px` a 0 ✅; `hex_literales` 631→562 ✅ | **parcial v5.58.0** |
| 8 bis | **Vaciar los estilos en línea** | VIS-001 (resto) | Sacar los 288 `setStyleSheet` a la hoja central y retirar las capas `legacy_styles` (25 ficheros) y `ccleaner_theme` (14). Es trabajo por vista, con revisión visual de cada una | P2 | alto | L | 8 | ratchet `setStyleSheet` bajando por lotes; capturas antes/después | pendiente |
| 9 | **Componentes y feedback** | VIS-004, VIS-005, VIS-006, VIS-007, VIS-008, UXA-003, UXA-013 | `ViewHeader`, variantes de botón, iconos sin emoji, `ResultCard`, feedback único | P2 | medio | L | 8 | tests de componente; a11y | pendiente |
| 10 | **Clics y caminos dorados** | UXF-003, UXF-006, UXF-010, UXF-011, UXF-009 | GP-1/2/3 dentro de presupuesto; atajos; recordar carpeta; deshacer en ausencias | P2 | bajo | M | 9 | tests de flujo con cuenta de clics | pendiente |
| 11 | **Accesibilidad de formularios y tablas** | ~~UXA-002~~, ~~UXA-005~~, ~~UXA-006~~, ~~UXA-012~~, UXA-001 (parcial), UXA-008 (parcial) | Nombres accesibles deducidos automáticamente (63% de controles mudos → 0); anillo de foco en todo control; el error marca el campo y le lleva el foco; tablas presentadas | P1 | alto | L | 8 | introspección por `accessibleName` en `test_accesibilidad_formularios.py` (11 tests) ✅. **Falta la sesión real con NVDA/VoiceOver** | **parcial v5.60.0** |
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

Tres frentes, independientes entre sí:

1. **Lote 0** en la máquina Windows: compilar con `scripts/build_windows.ps1 -Diagnostico` y ejecutar el protocolo de [[06_CRASH_WINDOWS_GENERACION]] §5. **Es el único trabajo pendiente sobre el cierre en Windows: los nueve hallazgos CRW están resueltos.** Queda comprobar en la máquina real que el cierre ha desaparecido; si persistiera, habría que buscar una causa que la auditoría no vio.
2. **Lote 8 bis** (vaciar los estilos en línea) — lo que queda de VIS-001. Es el trabajo caro del bloque visual: 288 `setStyleSheet` repartidos por las vistas, más dos capas antiguas que hay que retirar. No se puede hacer a ciegas: cada vista necesita mirarse antes y después, así que conviene por lotes pequeños.
3. **Lote 14** (calidad de código, COD-001…008) — independiente de todo lo demás y se puede hacer por tandas: ruff limpio, jerarquía de excepciones, sin ORM en la capa de presentación, código muerto fuera. Incluye borrar `orquestador_asignacion_guardias.py`, que importa dos módulos que ya no existen.

**Comprobaciones que sólo puede hacer una persona** (ningún lote las cubre):
- El protocolo de Windows de [[06_CRASH_WINDOWS_GENERACION]] §5.
- Abrir la aplicación en una pantalla pequeña y con escalado al 125% (UXA-001).
- Una sesión real con NVDA o VoiceOver recorriendo Profesores y Zonas con el tabulador (UXA-002/005/006).
