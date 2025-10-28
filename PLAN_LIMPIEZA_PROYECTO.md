# 🧹 Plan de Limpieza y Reorganización del Proyecto

**Fecha:** 28 de octubre de 2025  
**Versión actual:** v2.9.0  
**Objetivo:** Limpiar archivos obsoletos, duplicados y reorganizar la estructura del proyecto

---

## 📊 Análisis del Estado Actual

### Problemas Detectados

1. **Archivos .spec duplicados** (4 archivos, solo usamos 1)
2. **Logs de compilación dispersos** (5 archivos .log en raíz)
3. **Scripts de build duplicados** (build_dmg.sh y create_dmg.sh hacen lo mismo)
4. **Documentación obsoleta** (changelogs antiguos, sprints archivados)
5. **Carpetas de documentación mal organizadas**
6. **Scripts en raíz** (deberían estar en `/scripts`)

---

## 🗑️ FASE 1: Eliminar Archivos Obsoletos

### 1.1. Archivos .spec Obsoletos (NO USAMOS .spec)

**ELIMINAR** ❌ (usamos comandos directos de PyInstaller):
```bash
rm "Guardias de Patio.spec"
rm "Guardias de Patio 2.spec"
rm "Guardias de Patio OneFile.spec"
rm "guardias_patio_windows.spec"
```

**Razón:** La v2.9.0 documentó que NO usamos .spec files debido al bug de symlinks de PyQt6. Usamos `build_simple.sh` con comandos directos.

---

### 1.2. Logs de Compilación Temporales

**ELIMINAR** ❌:
```bash
rm build.log
rm compile.log
rm compilation.log
rm rebuild.log
rm simple_build.log
```

**Razón:** Son archivos temporales de compilación que se regeneran. Ya están en `.gitignore`.

---

### 1.3. Scripts Duplicados

**ELIMINAR** ❌:
```bash
rm build_dmg.sh          # Duplicado de create_dmg.sh (obsoleto)
rm build_app_debug.sh    # Script temporal de debug
rm fix_pyqt6.sh          # Script obsoleto (ya no se usa)
```

**MANTENER** ✅:
```bash
build_simple.sh          # Script principal de compilación
create_dmg.sh            # Script de creación de DMG (OFICIAL)
create_icon.sh           # Generación de iconos
run_app.sh               # Ejecutar en desarrollo
```

---

### 1.4. Documentación Obsoleta en `/documentacion`

**ELIMINAR** ❌:
```bash
# Changelogs antiguos (ya consolidados)
rm documentacion/CHANGELOG_v2.8.md

# Documentos obsoletos
rm documentacion/CONSOLIDACION_DOCS.md          # Ya completado
rm documentacion/PLAN_CONSOLIDACION.md          # Plan antiguo
rm documentacion/LIMPIEZA_PROYECTO.md           # Obsoleto
rm documentacion/COMPILACION_Y_DISTRIBUCION.md  # Redundante con SOLUCION_COMPILACION.md

# Carpeta de versiones antiguas
rm -rf documentacion/versiones/v2.5/
rm -rf documentacion/versiones/v2.6/
rm documentacion/versiones/RELEASE_NOTES_v2.8.0.md
```

**MANTENER** ✅:
```bash
documentacion/CHANGELOG_v2.9.md                 # Changelog actual
documentacion/SOLUCION_COMPILACION.md           # Guía de compilación crítica
documentacion/README.md                         # Índice principal
documentacion/GUIA_SINCRONIZACION.md            # Documentación técnica
documentacion/REQUISITOS_SISTEMA.md             # Requisitos
```

---

### 1.5. Archivos de Sistema Innecesarios

**ELIMINAR** ❌:
```bash
rm .DS_Store
rm documentacion/.DS_Store
```

**Agregar a .gitignore:**
```bash
echo ".DS_Store" >> .gitignore
echo "**/.DS_Store" >> .gitignore
```

---

### 1.6. Archivos de PyInstaller Obsoleto

**ELIMINAR** ❌:
```bash
rm fix_pyqt6_symlinks.py    # Script obsoleto
```

---

## 📁 FASE 2: Reorganizar Estructura

### 2.1. Mover Scripts a `/scripts`

**CREAR estructura:**
```bash
mkdir -p scripts/build
mkdir -p scripts/dev
mkdir -p scripts/maintenance
```

**MOVER** scripts de build:
```bash
mv build_simple.sh           scripts/build/
mv create_dmg.sh             scripts/build/
mv create_icon.sh            scripts/build/
```

**MOVER** scripts de desarrollo:
```bash
mv run_app.sh                scripts/dev/
```

**ACTUALIZAR** referencias en documentación:
- `COMPILACION_RAPIDA.md`: cambiar rutas de scripts
- `CHECKLIST_COMPILACION.md`: cambiar rutas de scripts
- `SOLUCION_COMPILACION.md`: cambiar rutas de scripts

---

### 2.2. Reorganizar `/documentacion`

**ESTRUCTURA PROPUESTA:**
```
documentacion/
├── README.md                          # Índice principal ✅
├── CHANGELOG_v2.9.md                  # Changelog actual ✅
│
├── build/                             # Compilación y distribución
│   ├── BUILD.md                       # ✅ (mantener)
│   ├── BUILD_DMG.md                   # ✅ (mantener)
│   ├── BUILD_WINDOWS.md               # ✅ (mantener)
│   └── SOLUCION_COMPILACION.md        # 🔄 MOVER desde raíz de documentacion/
│
├── guias/                             # Guías de usuario
│   ├── README.md                      # ✅
│   ├── atajos-teclado.md              # ✅
│   ├── ejemplos-uso.md                # ✅
│   └── GUIA_UI_FEATURES.md            # 🔄 MOVER desde raíz de documentacion/
│
├── tecnico/                           # Documentación técnica
│   ├── README.md                      # ✅
│   ├── ARCHITECTURE_PATTERNS.md       # 🔄 MOVER desde raíz
│   ├── ALGORITMO_PASADA_6.md          # 🔄 MOVER desde raíz
│   ├── GUIA_SINCRONIZACION.md         # 🔄 MOVER desde raíz
│   ├── RESUMEN_SMTP_GLOBAL.md         # 🔄 MOVER desde raíz
│   ├── CONFIGURACION_EMAIL.md         # 🔄 MOVER desde raíz
│   ├── REQUISITOS_SISTEMA.md          # 🔄 MOVER desde raíz
│   ├── caracteristicas-sistema.md     # ✅
│   ├── matriz-horario-dia-recreo.md   # ✅
│   └── resumen-matriz-horario.md      # ✅
│
├── desarrollo/                        # Para desarrolladores
│   ├── README.md                      # 🆕 CREAR
│   ├── CONTRIBUIR.md                  # 🔄 MOVER desde raíz
│   ├── PLAN_HOMOGENEIZACION_FORMULARIOS.md  # 🔄 MOVER desde raíz
│   └── HISTORIA_SPRINTS.md            # 🔄 MOVER desde raíz
│
├── funcionalidades/                   # ✅ (mantener estructura)
│   ├── README.md
│   ├── ausencias/
│   ├── calendario/
│   ├── guardias/
│   ├── importar-exportar/
│   └── profesores/
│
├── roadmap/                           # ✅ (mantener)
│   └── ...
│
├── sftp/                              # ✅ (mantener)
│   └── ...
│
├── validaciones/                      # ✅ (mantener)
│   └── ...
│
├── versiones/                         # Historial de versiones
│   ├── README.md                      # ✅
│   └── MEJORAS_CALENDARIO_v2.9.md     # 🔄 MOVER desde raíz
│
└── _archivo_sprints/                  # ✅ (mantener archivado)
    └── ... (57 archivos de sprints antiguos)
```

---

### 2.3. Mover Archivos de Raíz del Proyecto

**ESTRUCTURA RAÍZ LIMPIA:**
```
/
├── README.md                          # ✅ Principal
├── LICENSE                            # ✅
├── requirements.txt                   # ✅
├── pyproject.toml                     # ✅
├── pytest.ini                         # ✅
├── mypy.ini                           # ✅
├── alembic.ini                        # ✅
├── Makefile                           # ✅
│
├── CHECKLIST_COMPILACION.md           # 🔄 MOVER a documentacion/build/
├── COMPILACION_RAPIDA.md              # 🔄 MOVER a documentacion/build/
│
├── .github/                           # ✅
├── .vscode/                           # ✅
├── .venv/                             # ✅
├── alembic/                           # ✅
├── data/                              # ✅
├── dist/                              # ✅ (generado)
├── build/                             # ✅ (generado)
├── htmlcov/                           # ✅ (generado)
├── imagenes/                          # ✅
├── logs/                              # ✅
├── scripts/                           # 🔄 REORGANIZADO
├── src/                               # ✅
├── tests/                             # ✅
└── documentacion/                     # 🔄 REORGANIZADO
```

---

## 🔄 FASE 3: Actualizar Referencias

### 3.1. Actualizar README.md Principal

**Actualizar secciones:**
- ✅ Scripts de compilación: nuevas rutas en `/scripts/build/`
- ✅ Documentación: referencias actualizadas a nueva estructura

### 3.2. Actualizar documentacion/README.md

**Reescribir índice** con nueva estructura de carpetas.

### 3.3. Actualizar COMPILACION_RAPIDA.md

**Cambiar rutas:**
```bash
# ANTES:
./build_simple.sh
./create_dmg.sh

# DESPUÉS:
./scripts/build/build_simple.sh
./scripts/build/create_dmg.sh
```

### 3.4. Actualizar CHECKLIST_COMPILACION.md

**Cambiar rutas** de scripts.

---

## 📝 FASE 4: Crear Archivos Nuevos

### 4.1. scripts/README.md

```markdown
# Scripts del Proyecto

## Build Scripts (`/scripts/build/`)

- **build_simple.sh**: Compilación principal de la app para macOS
- **create_dmg.sh**: Creación del instalador DMG
- **create_icon.sh**: Generación de iconos de la aplicación

## Development Scripts (`/scripts/dev/`)

- **run_app.sh**: Ejecutar la aplicación en modo desarrollo

## Uso

```bash
# Compilar aplicación
./scripts/build/build_simple.sh

# Crear DMG
./scripts/build/create_dmg.sh

# Ejecutar en desarrollo
./scripts/dev/run_app.sh
```

Consulta `documentacion/build/` para guías detalladas.
```

### 4.2. documentacion/desarrollo/README.md

```markdown
# Documentación para Desarrolladores

## Guías de Desarrollo

- **CONTRIBUIR.md**: Cómo contribuir al proyecto
- **HISTORIA_SPRINTS.md**: Historial de sprints de desarrollo
- **PLAN_HOMOGENEIZACION_FORMULARIOS.md**: Plan de estandarización de UI

## Arquitectura

Ver `../tecnico/ARCHITECTURE_PATTERNS.md` para patrones arquitectónicos.

## Testing

Ver `../tecnico/` para documentación de pruebas y validaciones.
```

---

## 🎯 Resumen de Cambios

### Archivos Eliminados

| Tipo | Cantidad | Razón |
|------|----------|-------|
| .spec files | 4 | Obsoletos (no usamos .spec) |
| .log files | 5 | Temporales |
| Scripts duplicados | 3 | Redundantes |
| Docs obsoletos | 6 | Información duplicada/antigua |
| Versiones antiguas | 3 carpetas | Archivadas en _archivo_sprints |
| .DS_Store | 2+ | Archivos de sistema |

**Total eliminado:** ~25 archivos

---

### Archivos Reubicados

| Desde | Hacia | Cantidad |
|-------|-------|----------|
| `/` (raíz) → | `/scripts/build/` | 3 scripts |
| `/` (raíz) → | `/scripts/dev/` | 1 script |
| `/` (raíz) → | `/documentacion/build/` | 2 docs |
| `/documentacion/` → | `/documentacion/tecnico/` | 7 docs |
| `/documentacion/` → | `/documentacion/guias/` | 1 doc |
| `/documentacion/` → | `/documentacion/desarrollo/` | 3 docs |
| `/documentacion/` → | `/documentacion/versiones/` | 1 doc |
| `/documentacion/` → | `/documentacion/build/` | 1 doc |

**Total reubicado:** ~19 archivos

---

### Archivos Nuevos

1. `scripts/README.md`
2. `documentacion/desarrollo/README.md`

**Total creado:** 2 archivos

---

## ✅ Beneficios Esperados

1. **Claridad** 📌
   - Raíz del proyecto limpia y enfocada
   - Documentación organizada por temática
   - Scripts agrupados por función

2. **Mantenibilidad** 🔧
   - Fácil localizar archivos
   - Estructura lógica y escalable
   - Sin duplicados ni obsoletos

3. **Profesionalismo** 💼
   - Proyecto ordenado
   - Documentación accesible
   - Buenas prácticas de estructura

4. **Reducción de Tamaño** 📦
   - ~25 archivos menos
   - Menos confusión
   - Repositorio más limpio

---

## 🚀 Plan de Ejecución

### Paso 1: Backup
```bash
git add -A
git commit -m "chore: Backup antes de limpieza del proyecto"
git push origin main
```

### Paso 2: Eliminar Archivos Obsoletos
```bash
# Ejecutar comandos de FASE 1
```

### Paso 3: Crear Estructura de Carpetas
```bash
mkdir -p scripts/{build,dev,maintenance}
mkdir -p documentacion/desarrollo
```

### Paso 4: Mover Archivos
```bash
# Ejecutar comandos de FASE 2
```

### Paso 5: Actualizar Referencias
```bash
# Editar archivos según FASE 3
```

### Paso 6: Crear Archivos Nuevos
```bash
# Crear READMEs según FASE 4
```

### Paso 7: Commit y Push
```bash
git add -A
git commit -m "chore: Limpieza y reorganización del proyecto

- Eliminados 25+ archivos obsoletos (.spec, .log, duplicados)
- Reorganizados scripts en /scripts/{build,dev}
- Reorganizada documentación por temática
- Actualizadas referencias en documentación
- Creados READMEs para nuevas estructuras

Ref: PLAN_LIMPIEZA_PROYECTO.md"
git push origin main
```

---

## 📋 Checklist de Validación

Después de ejecutar el plan:

- [ ] ✅ Raíz del proyecto solo contiene archivos esenciales
- [ ] ✅ Scripts organizados en `/scripts/`
- [ ] ✅ Documentación organizada por tema
- [ ] ✅ No hay archivos .spec en el proyecto
- [ ] ✅ No hay archivos .log en raíz
- [ ] ✅ No hay .DS_Store
- [ ] ✅ README.md actualizado con nuevas rutas
- [ ] ✅ COMPILACION_RAPIDA.md con rutas correctas
- [ ] ✅ Compilación funciona: `./scripts/build/build_simple.sh`
- [ ] ✅ DMG funciona: `./scripts/build/create_dmg.sh`
- [ ] ✅ App de desarrollo: `./scripts/dev/run_app.sh`
- [ ] ✅ Commit y push exitosos

---

**Estado:** ⏳ Pendiente de aprobación y ejecución  
**Fecha estimada:** 28 de octubre de 2025  
**Responsable:** Equipo de desarrollo
