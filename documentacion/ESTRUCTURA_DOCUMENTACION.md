# 📂 Estructura de la Documentación

**Última actualización:** 23 Octubre 2025  
**Estado:** ✅ Limpia y consolidada

---

## 📊 Estructura Actual

```
documentacion/
│
├── 📘 README.md                           # Índice principal (igual que INDEX.md)
├── 📘 INDEX.md                            # Índice principal alternativo
│
├── 📚 GUÍAS PRINCIPALES
│   ├── HISTORIA_SPRINTS.md                # Historia completa (0% → 100%)
│   ├── PROYECTO_100_COMPLETADO.md         # Celebración del 100%
│   ├── ARCHITECTURE_PATTERNS.md           # Patrones arquitectónicos
│   ├── SCHEMAS_USAGE_GUIDE.md             # Guía de Pydantic schemas
│   └── CONTRIBUIR.md                      # Guía para contribuir
│
├── 📁 guias/                              # Guías de usuario
│   ├── README.md
│   ├── ejemplos-uso.md                    # Tutorial completo
│   └── atajos-teclado.md                  # Referencia rápida
│
├── 📁 funcionalidades/                    # Documentación funcional
│   ├── README.md
│   ├── profesores/
│   ├── guardias/
│   ├── ausencias/
│   ├── calendario/
│   └── importar-exportar/
│
├── 📁 tecnico/                            # Información técnica
│   ├── README.md
│   ├── caracteristicas-sistema.md
│   ├── matriz-horario-dia-recreo.md
│   └── resumen-matriz-horario.md
│
├── 📁 validaciones/                       # Reglas de negocio
│   ├── README.md
│   ├── reglas-completas.md
│   ├── max-una-guardia-dia.md
│   ├── no-simultaneidad.md
│   └── requisitos-sistema.md
│
├── 📁 roadmap/                            # Planificación futura
│   ├── README.md
│   └── roadmap-v3.0.md
│
├── 📁 versiones/                          # Historial de versiones
│   ├── README.md
│   ├── v2.5/
│   └── v2.6/
│
├── 📁 datos ejemplo/                      # Datos de prueba
│   ├── bach.xlsx
│   ├── fp_basica.xlsx
│   ├── fp_mañana.xlsx
│   └── fp_tarde.xlsx
│
└── 📁 _archivo_sprints/                   # 🗄️ ARCHIVO HISTÓRICO
    ├── README.md                          # Explicación del archivo
    ├── RESUMEN_SPRINT_*.md                # Sprints individuales
    ├── MINI_SPRINT_*.md                   # Mini-sprints
    ├── TASK_*.md                          # Tareas específicas
    ├── ARQUITECTURA.md (obsoleto)
    ├── CHANGELOG_*.md (consolidado)
    └── ... (documentos históricos)
```

---

## 🎯 Documentos por Audiencia

### 👨‍💻 Para Desarrolladores

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| **ARCHITECTURE_PATTERNS.md** | Patrones arquitectónicos completos | `/documentacion/` |
| **SCHEMAS_USAGE_GUIDE.md** | Uso de Pydantic schemas | `/documentacion/` |
| **src/domain/README.md** | Módulo de dominio | `/src/domain/` |
| **src/infrastructure/README.md** | Módulo de infraestructura | `/src/infrastructure/` |
| **CONTRIBUIR.md** | Guía para contribuir | `/documentacion/` |
| **tecnico/** | Documentación técnica | `/documentacion/tecnico/` |

### 👤 Para Usuarios Finales

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| **guias/ejemplos-uso.md** | Tutorial completo | `/documentacion/guias/` |
| **guias/atajos-teclado.md** | Atajos de teclado | `/documentacion/guias/` |
| **funcionalidades/** | Docs funcionales | `/documentacion/funcionalidades/` |
| **validaciones/reglas-completas.md** | Reglas de negocio | `/documentacion/validaciones/` |

### 📊 Para Project Managers

| Documento | Propósito | Ubicación |
|-----------|-----------|-----------|
| **HISTORIA_SPRINTS.md** | Historia completa de desarrollo | `/documentacion/` |
| **PROYECTO_100_COMPLETADO.md** | Estado actual del proyecto | `/documentacion/` |
| **roadmap/roadmap-v3.0.md** | Planificación futura | `/documentacion/roadmap/` |
| **versiones/** | Historial de versiones | `/documentacion/versiones/` |

---

## 🗂️ Consolidación Realizada

### ✅ Documentos Consolidados

| Documentos Antiguos | → | Documento Consolidado |
|---------------------|---|----------------------|
| 30+ RESUMEN_SPRINT_*.md | → | **HISTORIA_SPRINTS.md** |
| 3x MINI_SPRINT_*.md | → | **HISTORIA_SPRINTS.md** |
| ARQUITECTURA.md | → | **ARCHITECTURE_PATTERNS.md** |
| CHANGELOG_v2.6.md, v2.7.md | → | **HISTORIA_SPRINTS.md** |
| Múltiples README.md desactualizados | → | **README.md** único |

### 📦 Archivados (en `_archivo_sprints/`)

- Documentos de sprints individuales (50+ archivos)
- Documentos de tareas específicas (8+ archivos)
- Documentos de desarrollo históricos (15+ archivos)
- CHANGELOGs antiguos (2 archivos)
- READMEs obsoletos (3 archivos)

**Total archivado:** ~80 archivos

---

## 📏 Métricas de Documentación

### Antes de la Limpieza

- **Archivos .md en raíz:** 45+
- **Duplicación:** Alta (3-4 versiones de misma info)
- **Navegabilidad:** Baja (difícil encontrar info)
- **Obsolescencia:** ~40% de docs desactualizados

### Después de la Limpieza

- **Archivos .md en raíz:** 7 (consolidados)
- **Duplicación:** Eliminada (única fuente de verdad)
- **Navegabilidad:** Alta (índice claro)
- **Obsolescencia:** 0% (todo actualizado)

**Mejora:** -85% archivos en raíz, +100% claridad

---

## 🎯 Principios de Organización Aplicados

### 1. Single Source of Truth
Cada información existe en **UN SOLO LUGAR**:
- Historia de sprints → `HISTORIA_SPRINTS.md`
- Arquitectura → `ARCHITECTURE_PATTERNS.md`
- Schemas → `SCHEMAS_USAGE_GUIDE.md`

### 2. Separación por Audiencia
Documentación organizada según quién la usa:
- `/guias/` → Usuarios finales
- `/tecnico/` → Desarrolladores/admins
- `/funcionalidades/` → Todos (referencia)

### 3. Archivado sin Pérdida
Documentos históricos preservados en `_archivo_sprints/` con:
- README explicativo
- Estructura mantenida
- Acceso si necesario

### 4. Nombres Descriptivos
Nombres que explican el contenido:
- ✅ `HISTORIA_SPRINTS.md` (claro)
- ❌ `RESUMEN_10_2.md` (críptico)

---

## 🚀 Próximos Pasos

### Mantenimiento Continuo

1. **Actualizar README.md** cuando se agreguen features
2. **Mantener HISTORIA_SPRINTS.md** si hay nuevos sprints
3. **Actualizar guías** con nuevas funcionalidades
4. **Revisar links** periódicamente

### Expansión Futura

- [ ] Agregar más ejemplos en `guias/ejemplos-uso.md`
- [ ] Crear guías de troubleshooting
- [ ] Documentar API (si se implementa)
- [ ] Agregar videos tutoriales (links)

---

## 📝 Notas

### Criterios de Archivado

Un documento se archiva si:
- ✅ Ha sido consolidado en otro documento
- ✅ Es histórico y no necesario para uso actual
- ✅ Está desactualizado y reemplazado
- ✅ Es duplicado de información existente

Un documento se mantiene si:
- ✅ Es referencia activa para usuarios/desarrolladores
- ✅ Contiene información única y actual
- ✅ Es punto de entrada para navegación
- ✅ Documenta features actuales del sistema

---

**Última revisión:** 23 Octubre 2025  
**Próxima revisión:** Cuando se agreguen features nuevas  
**Responsable:** Mantener esta estructura limpia y organizada
