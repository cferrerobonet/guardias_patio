# Documentación - Sistema de Gestión de Guardias de Patio# 📚 Documentación del Sistema de Guardias de Patio



Bienvenido a la documentación completa del sistema de gestión de guardias de patio. Esta guía te ayudará a encontrar rápidamente la información que necesitas.Bienvenido a la documentación completa del sistema de gestión de guardias de patio.



## 📚 Índice General## 🆕 ÚLTIMA ACTUALIZACIÓN: v2.6.0 (17 de Octubre de 2025)



### [🎓 Guías de Usuario](guias/)**Nueva Funcionalidad Principal**: Matriz Visual Día × Recreo

Tutoriales y guías prácticas para el uso diario de la aplicación:

- [Atajos de Teclado](guias/atajos-teclado.md) - Mejora tu productividad con shortcuts✨ **Comienza aquí**: [RESUMEN_SESION_2025-10-17.md](RESUMEN_SESION_2025-10-17.md)

- [Ejemplos de Uso](guias/ejemplos-uso.md) - Casos prácticos y tutoriales paso a paso

### Documentación v2.6.0

### [⚙️ Funcionalidades](funcionalidades/)

Documentación detallada de cada módulo del sistema:| Documento | Descripción | Fecha |

|-----------|-------------|-------|

#### Profesores| **[RESUMEN_SESION_2025-10-17.md](RESUMEN_SESION_2025-10-17.md)** ⭐ | Vista rápida de todos los cambios de v2.6 | 17/10/2025 |

- [Gestión de Profesores](funcionalidades/profesores/) - Altas, bajas, ediciones| **[MATRIZ_HORARIO_DIA_RECREO.md](MATRIZ_HORARIO_DIA_RECREO.md)** 📖 | Tutorial completo de la matriz día×recreo | 17/10/2025 |

| **[CHANGELOG_v2.6.0.md](CHANGELOG_v2.6.0.md)** 📝 | Registro oficial de cambios v2.6 | 17/10/2025 |

#### Guardias| **[RESUMEN_MATRIZ_HORARIO_v2.6.md](RESUMEN_MATRIZ_HORARIO_v2.6.md)** 🔧 | Resumen técnico para desarrolladores | 17/10/2025 |

- [Zona Preferida v2.6](versiones/v2.6/zona-preferida.md) - Sistema de asignación por zona preferida| **[INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md)** 📑 | Índice completo de toda la documentación | 17/10/2025 |

- [Asignación de Guardias](funcionalidades/guardias/) - Algoritmo y reglas de asignación

---

#### Ausencias

- [Gestión de Ausencias](funcionalidades/ausencias/gestion.md) - Control de ausencias y sustituciones## 📖 Documentos Disponibles



#### Calendario### 🎯 Requisitos y Condiciones

- [Vista Mensual](funcionalidades/calendario/vista-mensual.md) - Visualización del calendario

| Documento | Descripción | Actualización |

#### Importar/Exportar|-----------|-------------|---------------|

- [Sistema de Importación/Exportación](funcionalidades/importar-exportar/README.md) - Backup y portabilidad de datos| **[REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)** | Documento maestro con todos los requisitos funcionales, validaciones críticas y especificaciones técnicas | 15/10/2025 v2.0 |

| **[REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)** | Especificación detallada del requisito de máximo 1 guardia por día por profesor | 15/10/2025 v2.0 |

### [✅ Validaciones y Reglas](validaciones/)

Reglas del sistema de asignación de guardias:### � Nuevas Funcionalidades

- [Reglas Completas](validaciones/reglas-completas.md) - Condiciones generales, particulares y validaciones

- [Máximo Una Guardia por Día](validaciones/max-una-guardia-dia.md) - Restricción diaria| Documento | Descripción | Actualización |

- [No Simultaneidad](validaciones/no-simultaneidad.md) - Validación de conflictos horarios|-----------|-------------|---------------|

| **[NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md)** | 📅 Vista Calendario, 📊 Estadísticas, 📄 Exportación PDF, 🔄 Gestión de Sustituciones | 16/10/2025 v2.1 ✨ **NUEVO** |

### [🔧 Desarrollo](desarrollo/)

Información técnica para desarrolladores:### �🐛 Soluciones y Fixes

- [Guía de Desarrollo](desarrollo/guia-desarrollo.md) - Setup, arquitectura, contribución

- [Solución PyQt6](desarrollo/solucion-pyqt6.md) - Configuración de entorno PyQt6| Documento | Descripción | Actualización |

- [Solución Duplicados](desarrollo/solucion-duplicados.md) - Fix para duplicados en guardias|-----------|-------------|---------------|

- [Limpieza y .gitignore](desarrollo/limpieza-gitignore.md) - Estrategia de archivos Git| **[SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)** | Análisis y solución del problema de guardias duplicadas por ejecución múltiple | 15/10/2025 v1.3 |

- [Plan de Reorganización](desarrollo/plan-reorganizacion-docs.md) - Proceso de esta reorganización

---

### [📖 Técnico](tecnico/)

Documentación técnica del sistema:## 🎯 Guía Rápida por Tema

- [Características del Sistema](tecnico/caracteristicas-sistema.md) - Especificaciones técnicas

- [Ejemplo de Exportación](tecnico/ejemplo-exportacion.json) - Archivo JSON de ejemplo### Si quieres saber sobre...



### [📦 Versiones](versiones/)#### ✅ **Requisitos del Sistema**

Historial de cambios y características por versión:👉 Lee: [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)



#### v2.6 (Actual)**Encontrarás:**

- [Changelog v2.6](versiones/v2.6/changelog.md) - Cambios de la versión actual- Requisitos funcionales básicos

- [Zona Preferida](versiones/v2.6/zona-preferida.md) - Documentación completa de la feature- CRUD de profesores

- [Ejemplos Zona Preferida](versiones/v2.6/ejemplos-zona-preferida.md) - Casos de uso y tests- Gestión de guardias

- [Resumen Implementación](versiones/v2.6/resumen-implementacion.md) - Detalles técnicos- Configuración del curso



#### v2.5---

- [Changelog v2.5](versiones/v2.5/changelog.md) - Cambios de versiones anteriores

#### 🚀 **Nuevas Funcionalidades v2.1**

### [🚀 Roadmap](roadmap/)👉 Lee: [NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md)

Planificación de futuras versiones:

- [Roadmap v3.0](roadmap/roadmap-v3.0.md) - Próximas características y mejoras**Las 4 nuevas funcionalidades:**



## 🔍 Búsqueda Rápida1. **📅 Vista Calendario Mensual**: Visualización interactiva con colores por día

2. **📊 Panel de Estadísticas**: Dashboard con métricas, tablas y gráficos matplotlib

### Por Funcionalidad3. **📄 Exportador PDF**: Genera calendarios individuales por profesor (ReportLab)

4. **🔄 Gestor de Sustituciones**: Sistema para reasignar guardias en ausencias

| ¿Qué necesitas? | Documento |

|-----------------|-----------|---

| Aprender atajos de teclado | [Atajos](guias/atajos-teclado.md) |

| Ver ejemplos prácticos | [Ejemplos de Uso](guias/ejemplos-uso.md) |#### ⚠️ **Validaciones Críticas**

| Hacer backup de datos | [Importar/Exportar](funcionalidades/importar-exportar/README.md) |👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 2](REQUISITOS_Y_VALIDACIONES.md#validaciones-críticas-del-algoritmo)

| Gestionar ausencias | [Gestión Ausencias](funcionalidades/ausencias/gestion.md) |

| Ver calendario mensual | [Vista Calendario](funcionalidades/calendario/vista-mensual.md) |**Las 2 validaciones críticas:**

| Entender zona preferida | [Zona Preferida v2.6](versiones/v2.6/zona-preferida.md) |

| Conocer reglas de asignación | [Reglas Completas](validaciones/reglas-completas.md) |1. **No Duplicidad de Ubicaciones**: Un profesor NO puede estar en dos zonas al mismo tiempo

| Configurar entorno desarrollo | [Guía Desarrollo](desarrollo/guia-desarrollo.md) |   - Clave: mismo (día + turno + recreo)

| Ver qué hay en cada versión | [Changelogs](versiones/) |   - Implementación: `guardias_por_slot_prof`

| Planificación futura | [Roadmap v3.0](roadmap/roadmap-v3.0.md) |

2. **Máximo 1 Guardia por Día**: Un profesor solo hace 1 guardia al día (mañana + tarde)

### Por Rol   - Clave: mismo día (cualquier turno)

   - Implementación: `guardias_por_dia_prof`

**👨‍🏫 Coordinadores/Jefes de Estudios:**   - Detalle: [REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)

- [Ejemplos de Uso](guias/ejemplos-uso.md) - Casos prácticos del día a día

- [Gestión de Ausencias](funcionalidades/ausencias/gestion.md) - Control de sustituciones---

- [Importar/Exportar](funcionalidades/importar-exportar/README.md) - Backup y configuración inicial

#### 👨‍🏫 **Restricciones por Profesor**

**👩‍💼 Administradores del Sistema:**👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 3](REQUISITOS_Y_VALIDACIONES.md#restricciones-por-profesor)

- [Guía de Desarrollo](desarrollo/guia-desarrollo.md) - Setup y mantenimiento

- [Importar/Exportar](funcionalidades/importar-exportar/README.md) - Migración entre equipos**Configurables por profesor:**

- [Características del Sistema](tecnico/caracteristicas-sistema.md) - Especificaciones técnicas- Turno (mañana/tarde/mixto)

- Fecha inicio guardias

**👨‍💻 Desarrolladores:**- Días de semana permitidos

- [Guía de Desarrollo](desarrollo/guia-desarrollo.md) - Arquitectura y contribución- Recreos permitidos

- [Solución PyQt6](desarrollo/solucion-pyqt6.md) - Problemas comunes

- [Versiones](versiones/) - Historial de cambios técnicos---

- [Roadmap v3.0](roadmap/roadmap-v3.0.md) - Futuras implementaciones

#### 🐛 **Problema: Guardias Duplicadas**

## 📊 Estado de la Documentación👉 Lee: [SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)



### Estadísticas**Síntoma:** Al ejecutar "Generar Guardias" varias veces, se acumulan guardias duplicadas

- **Total de documentos**: ~25 archivos

- **Última reorganización**: Diciembre 2024**Solución:** Diálogo de confirmación que pregunta si eliminar guardias existentes antes de generar nuevas

- **Versión actual**: v2.6.1

---

### Estructura

```#### 📊 **Algoritmo de Asignación**

documentacion/👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 8](REQUISITOS_Y_VALIDACIONES.md#algoritmo-de-asignación---flujo-completo)

├── guias/                    # Guías de usuario (2 docs)

├── funcionalidades/          # Features del sistema (5 módulos)**Flujo completo:**

│   ├── profesores/1. Construcción de slots (día × turno × recreo × zona)

│   ├── guardias/2. Cálculo de cuotas proporcionales

│   ├── ausencias/3. Iteración por slot con filtrado de elegibles

│   ├── calendario/4. Scoring y selección del mejor candidato

│   └── importar-exportar/5. Asignación y registro en base de datos

├── desarrollo/               # Docs técnicos desarrollo (5 docs)

├── validaciones/             # Reglas del sistema (3 docs)---

├── tecnico/                  # Especificaciones técnicas (2 docs)

├── versiones/                # Changelog por versión (5 docs)#### 🧪 **Tests y Validación**

│   ├── v2.5/👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 7](REQUISITOS_Y_VALIDACIONES.md#resumen-de-tests)

│   └── v2.6/

└── roadmap/                  # Planificación futura (1 doc)**Suite de pruebas:**

```- 54 tests en total ✅

- Tests específicos:

## 🆕 Últimas Actualizaciones  - `test_no_duplicados_profesor_mismo_slot.py` - Validación 1

  - `test_max_una_guardia_dia.py` - Validación 2

### v2.6.1 - Diciembre 2024

- ✅ Implementada **Zona Preferida**: Los profesores mantienen su zona asignada---

- ✅ Reorganización completa de documentación (50 → 25 archivos)

- ✅ Estructura escalable sin numeración#### 🔧 **Implementación Técnica**

- ✅ Consolidación de contenidos duplicados👉 Lee: [REQUISITOS_Y_VALIDACIONES.md - Sección 9](REQUISITOS_Y_VALIDACIONES.md#referencias-técnicas)



### v2.5 - Octubre 2024**Archivos clave:**

- ✅ Sistema de gestión de ausencias- `src/models/models.py` - Modelos de datos

- ✅ Vista de calendario mensual- `src/services/asignador_guardias.py` - Algoritmo principal

- ✅ Mejoras en importación/exportación- `src/services/calculador_guardias.py` - Cálculos y distribución

- `src/main.py` - Interfaz gráfica (PyQt6)

## 🤝 Contribuir

---

Si encuentras errores o tienes sugerencias para mejorar la documentación:

## 📝 Historial de Requisitos

1. Revisa la [Guía de Desarrollo](desarrollo/guia-desarrollo.md)

2. Crea un issue describiendo el problema o sugerencia| Fecha | Versión | Requisito | Estado |

3. Si puedes, envía un pull request con la corrección|-------|---------|-----------|--------|

| 14/10/2025 | 1.0 | Unificación nombre/apellidos en `nombre_completo` | ✅ Completado |

## 📞 Soporte| 14/10/2025 | 1.1 | CRUD completo de profesores (con edición) | ✅ Completado |

| 15/10/2025 | 1.2 | UI profesional con QGroupBox y CSS | ✅ Completado |

- **Issues**: [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues)| 15/10/2025 | 1.3 | Fix: Duplicados en mismo slot (Validación 1) | ✅ Completado |

- **Email**: soporte@colegio.edu| **15/10/2025** | **2.0** | **Máximo 1 guardia por día (Validación 2)** | ✅ **Completado** |

- **Documentación Online**: [Wiki del Proyecto](https://github.com/tu-repo/guardias-patio/wiki)| **16/10/2025** | **2.1** | **Vista Calendario + Estadísticas + PDF + Sustituciones** | ✅ **Completado** |



## 📝 Licencia---



Este proyecto y su documentación están bajo la licencia MIT. Ver [LICENSE](../LICENSE) para más detalles.## 🚀 Inicio Rápido



---### Para Desarrolladores



**Última actualización**: Diciembre 2024  ```bash

**Versión de la aplicación**: v2.6.1  # 1. Leer documentación principal

**Estado**: ✅ Activo y mantenidocat documentacion/REQUISITOS_Y_VALIDACIONES.md


# 2. Ejecutar tests
source .venv/bin/activate
pytest tests/ -v

# 3. Ejecutar aplicación
python src/main.py
```

### Para Usuarios

1. **Lee primero**: [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md) para entender las reglas del sistema
2. **Nuevas funcionalidades**: [NUEVAS_FUNCIONALIDADES_V2_1.md](NUEVAS_FUNCIONALIDADES_V2_1.md) para descubrir las últimas mejoras ✨
3. **Problema con duplicados?**: [SOLUCION_DUPLICADOS_GUARDIAS.md](SOLUCION_DUPLICADOS_GUARDIAS.md)
4. **Duda sobre límite diario?**: [REQUISITO_MAX_UNA_GUARDIA_DIA.md](REQUISITO_MAX_UNA_GUARDIA_DIA.md)

---

## 📞 Contacto y Soporte

Para dudas sobre:
- **Requisitos funcionales**: Ver sección correspondiente en [REQUISITOS_Y_VALIDACIONES.md](REQUISITOS_Y_VALIDACIONES.md)
- **Bugs conocidos**: Consultar sección de soluciones
- **Nuevos requisitos**: Documentar en este mismo sistema

---

## 📦 Estructura de Documentación

```
documentacion/
├── README.md                              ← Este archivo (índice)
├── REQUISITOS_Y_VALIDACIONES.md          ← Documento maestro
├── REQUISITO_MAX_UNA_GUARDIA_DIA.md      ← Detalle requisito específico
├── NUEVAS_FUNCIONALIDADES_V2_1.md        ← 4 funcionalidades avanzadas ✨
└── SOLUCION_DUPLICADOS_GUARDIAS.md       ← Fix problema conocido
```

---

**Última actualización:** 16 de octubre de 2025  
**Versión del sistema:** 2.1  
**Estado:** ✅ Documentación completa y actualizada
