---
tags:
  - gestion-centro
  - auditoria
fecha_actualizacion: 2026-09-04
estado: activo
prioridad: 1-urgente
tipo: indice
---

# Auditoría integral — Guardias de Patio (app de escritorio PyQt6)

> [!NOTE] Cómo usar esta carpeta
> `30_REGISTRO_HALLAZGOS.md` es la única fuente de verdad del estado de cada hallazgo. `17_PLAN_DE_ATAQUE.md` es el único backlog de implementación. El resto de documentos aportan evidencia, inventarios, contratos y protocolos. No crear informes paralelos ni carpetas por ronda.

## Baseline

| Campo | Valor |
| --- | --- |
| Commit auditado | `742fe452fcdf646985011187eb9b4aea72cd9b0a` (`main`) |
| Versión app | 5.42.3 (`src/config/settings.py`) |
| Fecha / zona | 2026-09-04 · Europe/Madrid |
| Modo | `AUDIT_ONLY` para el código de la app + entrega autorizada de tests, skills y documentación |
| Intérprete válido | `/opt/homebrew/bin/python3.11` (Python 3.11.15, PyQt6 6.7.0, OR-Tools 9.14, pytest 8.4.2) |
| Suite | 2.457 funciones de test en 117 ficheros (+ `tests/ui`, `tests/compliance`) |

## Documentos

| Nº | Documento | Qué contiene |
| --- | --- | --- |
| 01 | [[01_BASELINE_Y_ADAPTADOR]] | Adaptador del proyecto, stack verificado, comandos reales, entorno, limitaciones |
| 02 | [[02_PLAN_MAESTRO_AUDITORIA]] | Plan exhaustivo por dimensiones para una app de escritorio de este stack, con checklist e IDs estables |
| 03 | [[03_UX_CASOS_DE_USO_Y_CAMINOS_DORADOS]] | Casos de uso, caminos dorados, presupuesto de clics, guardarraíles y secuencia obligatoria |
| 04 | [[04_INVENTARIO_SUPERFICIES_E_INCONSISTENCIAS_VISUALES]] | Inventario de vistas, diálogos, formularios y tablas; inconsistencias visuales detectadas |
| 05 | [[05_CONTRATO_SISTEMA_DE_DISENO]] | Contrato de diseño (tokens, componentes, estados, patrones) para una app hecha por una sola persona |
| 06 | [[06_CRASH_WINDOWS_GENERACION]] | Análisis del cierre de la app en Windows al terminar el cálculo: causas, evidencia, protocolo de diagnóstico y fixes |
| 07 | [[07_FUNCIONALIDAD_CALIDAD_ESCALABILIDAD]] | Mejoras funcionales, calidad de código, arquitectura objetivo y escalabilidad |
| 08 | [[08_ESTRATEGIA_DE_TESTS]] | Pirámide de tests, BD local en fichero, pytest-qt, hilos, compliance, Playwright para la superficie web |
| 09 | [[09_BUILD_Y_RELEASE]] | Estado del empaquetado exe/dmg, hallazgos, pipeline objetivo y checklist de release |
| 10 | [[10_SKILLS_RECOMENDADOS]] | Skills de GitHub con más estrellas aplicables, skills del proyecto creados y cómo instalarlos |
| 11 | [[11_EFICIENCIA_AGENTES_Y_TOKENS]] | Revisión de instrucciones, agentes y skills para sesiones más rápidas y baratas |
| 17 | [[17_PLAN_DE_ATAQUE]] | Backlog único por lotes, orden, dependencias y gates |
| 30 | [[30_REGISTRO_HALLAZGOS]] | Registro canónico de hallazgos con ID, severidad, estado y evidencia |

Artefactos intermedios: `_work/paquete_ux_accesibilidad.md` (paquete Ola 4 de 2026-08-04, hallazgos UXA-001…014, integrados en el registro).

## Recuentos (derivados de 30_REGISTRO_HALLAZGOS.md)

| Familia | P0 | P1 | P2 | P3 | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| CRW · Cierre en Windows / hilos | 1 | 4 | 3 | 1 | 9 |
| UXA · Accesibilidad y UX (Ola 4 previa) | 0 | 7 | 6 | 1 | 14 |
| UXF · Flujo, guardarraíles y clics | 0 | 2 | 7 | 2 | 11 |
| VIS · Consistencia visual | 0 | 0 | 7 | 3 | 10 |
| BLD · Build y release | 0 | 2 | 4 | 1 | 7 |
| QA · Tests y calidad de pruebas | 0 | 2 | 6 | 4 | 12 |
| COD · Calidad de código | 0 | 0 | 4 | 4 | 8 |
| ESC · Escalabilidad y arquitectura | 0 | 0 | 5 | 2 | 7 |
| SEC · Seguridad y privacidad | 0 | 0 | 1 | 2 | 3 |
| DEV · Eficiencia de agentes y tokens | 0 | 0 | 2 | 4 | 6 |
| **Total** | **1** | **17** | **45** | **24** | **87** |

Mejoras funcionales propuestas (FUN-001…012) se listan en 07 y en el registro como tipo `mejora`, sin severidad.

## Estado global

- **Veredicto:** `PARCIAL`. Hay evidencia estática reproducible y comandos ejecutados; faltan la reproducción del cierre en la máquina Windows y la validación manual con lector de pantalla.
- **Bloqueantes de certificación:** CRW-001/002/003/005, UXA-001…007, BLD-001/002, QA-001.
- **Resueltos y verificados en v5.45.0:** QA-012 (`.venv` reparado y alineado con `requirements.txt`; VS Code queda utilizable para ejecutar, depurar y compilar).
- **Resueltos y verificados en v5.44.0:** QA-008 (la suite completa vuelve a ejecutarse de una pasada: 2.454 pasan en 47 s), CRW-006 (`faulthandler`), CRW-008 (nombres indefinidos), BLD-007 (build de diagnóstico).
- **Gates ejecutados en este commit:** colección pytest, ruff, bandit y suite completa por fichero (2.376 pasan, 0 fallan, 4 ficheros bloqueados). Detalle y método en [[01_BASELINE_Y_ADAPTADOR]].

## Orden de lectura recomendado

1. 06 (crash Windows) → 17 (lote 1).
2. 03 + 05 (flujo y diseño) → lotes 2-4.
3. 08 + 09 (tests y build) → lotes 5-6.
4. 07 (escalabilidad y mejoras) → roadmap.
