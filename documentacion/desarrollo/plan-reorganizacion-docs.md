# 📋 Plan de Reorganización de Documentación

## 🔍 Análisis de Situación Actual

### Archivos Totales: 50 archivos .md

#### Categorización Inicial:

**📁 OBSOLETOS (Para eliminar - 18 archivos)**
1. `paso01.md` a `paso10.md` (10 archivos) - Pasos de desarrollo ya completados
2. `NOTAS_VERSION_1_1_0.md` - Versión muy antigua
3. `NUEVAS_FUNCIONALIDADES_V2_1.md` - Versión antigua
4. `REFACTORIZACION_v2.2.md` - Refactorización completada
5. `RESUMEN_v2.2.1.md` - Versión antigua
6. `OPTIMIZACIONES_v2.3.md` - Ya incorporadas
7. `MEJORAS_UX_v2.4.md` - Ya incorporadas
8. `ANALISIS_ESTADO_ACTUAL_v2.3.1.md` - Análisis antiguo
9. `RESUMEN_EJECUTIVO_ANALISIS_v2.3.1.md` - Análisis antiguo
10. `VERIFICACION_PRUEBA_v2.3.md` - Prueba antigua

**📁 DUPLICADOS/REDUNDANTES (Para fusionar - 15 archivos)**
1. `RESUMEN_IMPORTACION_EXPORTACION.md` + `importar_exportar.md` + `TUTORIAL_IMPORTAR_EXPORTAR.md`
2. `condiciones_generales_asignacion.md` + `condiciones_particulares_profesores.md` + `validaciones_asignacion.md` + `REQUISITOS_Y_VALIDACIONES.md`
3. `SOLUCION_DUPLICADOS_GUARDIAS.md` + `REQUISITO_MAX_UNA_GUARDIA_DIA.md` + `RESUMEN_VALIDACION_NO_SIMULTANEIDAD.md`
4. `RESUMEN_SESION_2025-10-17.md` + `RESUMEN_IMPLEMENTACION_v2.6.1.md` + `RESUMEN_ZONA_PREFERIDA_v2.6.1.md`
5. `NUEVO_GITIGNORE_RESUMEN.md` + `ESTRATEGIA_GITIGNORE.md` + `LIMPIEZA_PROYECTO.md`
6. `RESUMEN_MATRIZ_HORARIO_v2.6.md` + `MATRIZ_HORARIO_DIA_RECREO.md`

**📁 ACTUALES Y ÚTILES (Para reorganizar - 17 archivos)**
1. `README.md` - Índice principal
2. `INDICE_DOCUMENTACION.md` - Índice actual
3. `CARACTERISTICAS_SISTEMA.md` - Características generales
4. `CHANGELOG_v2.5.md` - Ausencias (actual)
5. `CHANGELOG_v2.6.0.md` - Matriz horario (actual)
6. `CHANGELOG_v2.6.1.md` - Zona preferida (actual)
7. `GUIA_DESARROLLO.md` - Desarrollo
8. `GUIA_ATAJOS_TECLADO.md` - Usuario
9. `GUIA_GESTION_AUSENCIAS_v2.5.md` - Usuario
10. `EJEMPLOS_USO.md` - Usuario
11. `EJEMPLOS_ZONA_PREFERIDA_v2.6.1.md` - Usuario
12. `ZONA_PREFERIDA_v2.6.1.md` - Técnico
13. `vista_calendario.md` - Funcionalidad
14. `solucion_pyqt6.md` - Técnico
15. `ROADMAP_v3.0.md` - Planificación
16. `RESUMEN_FASE_3.md` - Desarrollo

---

## 🎯 Nueva Estructura Propuesta (ESCALABLE)

```
documentacion/
├── README.md                          # Índice maestro actualizado
│
├── guias/                             # Guías para usuarios (SIN numeración)
│   ├── inicio-rapido.md               # Nueva: Quick start
│   ├── guia-usuario.md                # Fusión: guía completa
│   ├── atajos-teclado.md              # Renombrado
│   └── ejemplos-casos-uso.md          # Fusión de ejemplos
│
├── funcionalidades/                   # Una carpeta = Una feature (ESCALABLE)
│   ├── profesores/
│   │   ├── README.md                  # Índice de profesores
│   │   ├── configuracion.md           # Configurar profesores
│   │   └── matriz-horario.md          # Matriz día × recreo
│   │
│   ├── guardias/
│   │   ├── README.md                  # Índice de guardias
│   │   ├── generacion.md              # Generar calendario
│   │   ├── algoritmo.md               # Algoritmo de asignación
│   │   └── zona-preferida.md          # Zona preferida (v2.6.1)
│   │
│   ├── ausencias/
│   │   ├── README.md                  # Índice de ausencias
│   │   ├── gestion.md                 # Gestionar ausencias
│   │   └── sustituciones.md           # Sistema de sustituciones
│   │
│   ├── calendario/
│   │   ├── README.md                  # Índice de calendario
│   │   └── vista-mensual.md           # Vista de calendario
│   │
│   └── importar-exportar/
│       ├── README.md                  # Índice importar/exportar
│       ├── importar.md                # Importar datos
│       ├── exportar-json.md           # Exportar JSON
│       └── exportar-pdf.md            # Exportar PDF
│
├── desarrollo/                        # Para desarrolladores
│   ├── README.md                      # Índice desarrollo
│   ├── setup.md                       # Setup del entorno
│   ├── arquitectura.md                # Estructura del código
│   ├── base-datos.md                  # Modelos y migraciones
│   ├── algoritmos.md                  # Lógica de asignación
│   ├── testing.md                     # Cómo ejecutar tests
│   └── contribuir.md                  # Cómo contribuir
│
├── validaciones/                      # Reglas y validaciones
│   ├── README.md                      # Índice de validaciones
│   ├── reglas-asignacion.md           # Reglas de asignación
│   ├── restricciones.md               # Restricciones del sistema
│   └── requisitos-sistema.md          # Requisitos técnicos
│
├── tecnico/                           # Documentación técnica
│   ├── README.md                      # Índice técnico
│   ├── pyqt6.md                       # Solución PyQt6
│   ├── git.md                         # Git y .gitignore
│   └── troubleshooting.md             # Solución de problemas
│
├── versiones/                         # Historial (ESCALABLE por versión)
│   ├── README.md                      # Índice de versiones
│   ├── CHANGELOG.md                   # Changelog consolidado
│   ├── v2.5/
│   │   ├── README.md                  # Resumen v2.5
│   │   └── ausencias.md               # Detalle ausencias
│   │
│   ├── v2.6/
│   │   ├── README.md                  # Resumen v2.6
│   │   ├── v2.6.0-matriz.md           # v2.6.0 detallado
│   │   └── v2.6.1-zona.md             # v2.6.1 detallado
│   │
│   └── v3.0/                          # FUTURAS VERSIONES
│       └── README.md                  # Placeholder para v3.0
│
└── roadmap/                           # Planificación futura
    ├── README.md                      # Índice roadmap
    ├── v3.0.md                        # Roadmap v3.0
    └── ideas.md                       # Ideas y propuestas

```

---

## 🚀 Escalabilidad del Sistema

### ✅ Agregar Nueva Funcionalidad (Ejemplo: "Reportes")

```bash
# Crear carpeta para la nueva funcionalidad
mkdir -p funcionalidades/reportes

# Crear archivos
cat > funcionalidades/reportes/README.md << EOF
# 📊 Reportes

Documentación del sistema de reportes...
EOF

cat > funcionalidades/reportes/estadisticas.md << EOF
# Estadísticas
...
EOF
```

**Ventajas**:
- ✅ No afecta a otras carpetas
- ✅ Estructura clara y modular
- ✅ Fácil de encontrar

### ✅ Agregar Nueva Versión (Ejemplo: v3.1)

```bash
# Crear carpeta para v3.1
mkdir -p versiones/v3.1

# Crear documentación
cat > versiones/v3.1/README.md << EOF
# Versión 3.1

## Nuevas Características
- Feature X
- Feature Y
EOF
```

**Ventajas**:
- ✅ Historial organizado por versión
- ✅ Fácil comparar versiones
- ✅ No rompe estructura existente

### ✅ Agregar Nueva Guía de Usuario

```bash
# Simplemente añadir el archivo
cat > guias/exportar-excel.md << EOF
# Exportar a Excel

Nueva guía para exportar a Excel...
EOF
```

**Ventajas**:
- ✅ Carpeta plana, fácil navegación
- ✅ Sin límite de archivos
- ✅ Nombres descriptivos

---

## 📐 Principios de Diseño Escalable

### 1. **Nombres sin numeración**
❌ Antes: `01_GUIAS_USUARIO/`, `02_FUNCIONALIDADES/`  
✅ Ahora: `guias/`, `funcionalidades/`

**Por qué**: Si añades una carpeta nueva, no necesitas renumerar todas

### 2. **Carpetas por feature, no por tipo**
❌ Antes: Todo en `FUNCIONALIDADES/`  
✅ Ahora: `funcionalidades/profesores/`, `funcionalidades/guardias/`

**Por qué**: Cada feature es independiente y escalable

### 3. **Versiones en subcarpetas**
❌ Antes: `VERSION_2.5.md`, `VERSION_2.6.0.md` (archivo único)  
✅ Ahora: `versiones/v2.5/`, `versiones/v2.6/`, `versiones/v3.0/`

**Por qué**: Puedes tener múltiples archivos por versión

### 4. **README.md en cada carpeta**
✅ Cada carpeta tiene su `README.md` como índice

**Por qué**: Navegación fácil, contexto claro

### 5. **Nombres en kebab-case (minúsculas con guiones)**
✅ `matriz-horario.md`, `zona-preferida.md`

**Por qué**: Más fácil de escribir, URLs amigables, compatible con sistemas Unix

---

## 🔮 Ejemplos de Escalabilidad Futura

### Escenario 1: Nueva Feature "Notificaciones Email"

```
funcionalidades/
└── notificaciones/              # ← NUEVA CARPETA
    ├── README.md                # Índice
    ├── configuracion.md         # Configurar email
    ├── plantillas.md            # Plantillas de email
    └── programacion.md          # Programar envíos
```

### Escenario 2: Versión 4.0 con múltiples características

```
versiones/
└── v4.0/                        # ← NUEVA VERSIÓN
    ├── README.md                # Resumen v4.0
    ├── migracion.md             # Guía de migración
    ├── breaking-changes.md      # Cambios incompatibles
    └── nuevas-features.md       # Nuevas características
```

### Escenario 3: Nueva guía para administradores

```
guias/
├── inicio-rapido.md
├── guia-usuario.md
└── guia-administrador.md        # ← NUEVA GUÍA
```

### Escenario 4: Documentación de API REST (futuro)

```
desarrollo/
├── README.md
├── setup.md
└── api/                         # ← NUEVA SUBCARPETA
    ├── README.md
    ├── endpoints.md
    └── autenticacion.md
```

---

## 📊 Comparación: Antes vs Después

### ❌ Estructura Rígida (NO escalable)

```
01_GUIAS/                # Numeración rígida
02_FUNCIONALIDADES/      # Todo junto, sin organización
03_DESARROLLO/
...
```

**Problemas**:
- Añadir carpeta nueva → Renumerar todo
- Nueva feature → Archivo plano sin contexto
- Nueva versión → Archivo único, difícil de manejar

### ✅ Estructura Flexible (ESCALABLE)

```
guias/                   # Sin números
funcionalidades/         # Subcarpetas por feature
  profesores/
  guardias/
  [nueva-feature]/       # ← Fácil añadir
versiones/
  v2.5/
  v2.6/
  v3.0/
  [v4.0]/                # ← Fácil añadir
```

**Ventajas**:
- ✅ Añadir carpeta nueva → Solo crearla
- ✅ Nueva feature → Carpeta independiente
- ✅ Nueva versión → Carpeta con múltiples archivos

---

## 🎯 Reglas de Escalabilidad

### Regla 1: Una Feature = Una Carpeta
```
funcionalidades/
└── [nombre-feature]/
    ├── README.md        # Siempre presente
    └── *.md             # Archivos relacionados
```

### Regla 2: Una Versión = Una Carpeta
```
versiones/
└── v[X.Y]/
    ├── README.md        # Resumen de la versión
    └── *.md             # Detalles específicos
```

### Regla 3: Nombres Descriptivos
```
✅ matriz-horario.md
✅ zona-preferida.md
✅ exportar-pdf.md

❌ feature1.md
❌ v2_6_1.md
❌ doc123.md
```

### Regla 4: README.md Como Índice
Cada carpeta principal tiene un README.md que:
- Lista los archivos contenidos
- Explica el propósito de la carpeta
- Proporciona enlaces rápidos

---

## ✅ Garantías de Escalabilidad

| Escenario | ¿Cómo se maneja? | ¿Rompe estructura? |
|-----------|------------------|-------------------|
| Nueva funcionalidad | Crear `funcionalidades/[nombre]/` | ❌ No |
| Nueva versión | Crear `versiones/v[X.Y]/` | ❌ No |
| Nueva guía | Añadir archivo en `guias/` | ❌ No |
| Subdivir funcionalidad | Crear subcarpetas | ❌ No |
| Deprecar funcionalidad | Mover a `versiones/[deprecadas]/` | ❌ No |
| Añadir idioma | Crear `[carpeta]/[lang]/` | ❌ No |

---

## 🚀 Migración Futura

Si en el futuro necesitas cambiar algo:

### Opción 1: Añadir Idiomas
```
guias/
├── es/                  # Español
│   ├── inicio-rapido.md
│   └── guia-usuario.md
└── en/                  # Inglés
    ├── quick-start.md
    └── user-guide.md
```

### Opción 2: Separar Documentación Técnica
```
tecnico/
├── backend/
│   └── arquitectura.md
└── frontend/
    └── componentes.md
```

### Opción 3: Añadir Tutoriales en Video
```
guias/
├── inicio-rapido.md
└── videos/
    ├── README.md
    └── tutorial-1.md
```

**Todas estas opciones son compatibles con la estructura actual** ✅

---

## ✅ Acciones Detalladas

### FASE 1: Eliminar Obsoletos (18 archivos)
```bash
# Eliminar pasos de desarrollo
rm paso01.md paso02.md paso03.md paso04.md paso05.md
rm paso06.md paso07.md paso08.md paso09.md paso10.md

# Eliminar versiones antiguas
rm NOTAS_VERSION_1_1_0.md
rm NUEVAS_FUNCIONALIDADES_V2_1.md
rm REFACTORIZACION_v2.2.md
rm RESUMEN_v2.2.1.md
rm OPTIMIZACIONES_v2.3.md
rm MEJORAS_UX_v2.4.md
rm ANALISIS_ESTADO_ACTUAL_v2.3.1.md
rm RESUMEN_EJECUTIVO_ANALISIS_v2.3.1.md
rm VERIFICACION_PRUEBA_v2.3.md
```

### FASE 2: Crear Estructura de Carpetas
```bash
mkdir -p 01_GUIAS_USUARIO
mkdir -p 02_FUNCIONALIDADES  
mkdir -p 03_DESARROLLO
mkdir -p 04_VALIDACIONES
mkdir -p 05_TECNICO
mkdir -p 06_CHANGELOGS
mkdir -p 07_PLANIFICACION
```

### FASE 3: Fusionar y Reorganizar

#### 01_GUIAS_USUARIO/

**GUIA_RAPIDA.md** (Nueva)
- Introducción al sistema
- Instalación y primer uso
- Conceptos básicos

**GUIA_COMPLETA_USUARIO.md** (Fusión)
- De: `EJEMPLOS_USO.md`
- De: `GUIA_GESTION_AUSENCIAS_v2.5.md`
- De: Partes de `CARACTERISTICAS_SISTEMA.md`

**ATAJOS_TECLADO.md** (Mover)
- De: `GUIA_ATAJOS_TECLADO.md`

**EJEMPLOS_Y_CASOS_USO.md** (Fusión)
- De: `EJEMPLOS_USO.md`
- De: `EJEMPLOS_ZONA_PREFERIDA_v2.6.1.md`

#### 02_FUNCIONALIDADES/

**GESTION_PROFESORES.md** (Nueva consolidación)
- Añadir profesores
- Configurar turnos
- Matriz día × recreo
- Fechas de guardias

**GESTION_GUARDIAS.md** (Nueva consolidación)
- Algoritmo de asignación
- Generación de calendario
- Validaciones

**GESTION_AUSENCIAS.md** (Basado en v2.5)
- De: `GUIA_GESTION_AUSENCIAS_v2.5.md`

**MATRIZ_HORARIO.md** (Basado en v2.6.0)
- De: `MATRIZ_HORARIO_DIA_RECREO.md`
- De: `RESUMEN_MATRIZ_HORARIO_v2.6.md`

**ZONA_PREFERIDA.md** (Basado en v2.6.1)
- De: `ZONA_PREFERIDA_v2.6.1.md`
- De: `EJEMPLOS_ZONA_PREFERIDA_v2.6.1.md`
- De: partes de `RESUMEN_ZONA_PREFERIDA_v2.6.1.md`

**VISTA_CALENDARIO.md** (Mover)
- De: `vista_calendario.md`

**IMPORTAR_EXPORTAR.md** (Fusión)
- De: `RESUMEN_IMPORTACION_EXPORTACION.md`
- De: `importar_exportar.md`
- De: `TUTORIAL_IMPORTAR_EXPORTAR.md`

**EXPORTAR_PDF.md** (Nueva)
- Generación de PDFs
- Configuración de exportación

#### 03_DESARROLLO/

**GUIA_DESARROLLO.md** (Mejorar existente)
- Setup del entorno
- Estructura del proyecto
- Cómo contribuir

**ARQUITECTURA.md** (Nueva)
- Estructura de carpetas
- Módulos principales
- Flujo de datos

**BASE_DATOS.md** (Nueva)
- Modelos SQLAlchemy
- Migraciones Alembic
- Esquema de BD

**ALGORITMOS.md** (Nueva consolidación)
- De partes de: `condiciones_generales_asignacion.md`
- De: `REQUISITOS_Y_VALIDACIONES.md`
- Algoritmo de asignación
- Sistema de scoring
- Zona preferida

**TESTING.md** (Nueva)
- Cómo ejecutar tests
- Tests disponibles
- Escribir nuevos tests

#### 04_VALIDACIONES/

**VALIDACIONES_COMPLETAS.md** (Mega fusión)
- De: `condiciones_generales_asignacion.md`
- De: `condiciones_particulares_profesores.md`
- De: `validaciones_asignacion.md`
- De: `REQUISITOS_Y_VALIDACIONES.md`
- De: `SOLUCION_DUPLICADOS_GUARDIAS.md`
- De: `REQUISITO_MAX_UNA_GUARDIA_DIA.md`
- De: `RESUMEN_VALIDACION_NO_SIMULTANEIDAD.md`

**REQUISITOS_SISTEMA.md** (Nueva)
- Requisitos de software
- Dependencias
- Compatibilidad

#### 05_TECNICO/

**SOLUCION_PYQT6.md** (Mover)
- De: `solucion_pyqt6.md`

**GITIGNORE_Y_GIT.md** (Fusión)
- De: `NUEVO_GITIGNORE_RESUMEN.md`
- De: `ESTRATEGIA_GITIGNORE.md`
- De: `LIMPIEZA_PROYECTO.md`

**TROUBLESHOOTING.md** (Nueva)
- Problemas comunes
- Soluciones
- FAQ

#### 06_CHANGELOGS/

**CHANGELOG.md** (Consolidado completo)
- Todas las versiones en uno
- v2.6.1, v2.6.0, v2.5, anteriores

**VERSION_2.5_AUSENCIAS.md** (Detallado)
- De: `CHANGELOG_v2.5.md`

**VERSION_2.6.0_MATRIZ.md** (Detallado)
- De: `CHANGELOG_v2.6.0.md`

**VERSION_2.6.1_ZONA.md** (Detallado)
- De: `CHANGELOG_v2.6.1.md`

#### 07_PLANIFICACION/

**ROADMAP.md** (Mover y actualizar)
- De: `ROADMAP_v3.0.md`
- De partes de: `RESUMEN_FASE_3.md`

---

## 📊 Resumen de Cambios

| Categoría | Antes | Después | Cambio |
|-----------|-------|---------|--------|
| Archivos totales | 50 | ~25 | -50% |
| Obsoletos eliminados | - | 18 | -18 |
| Fusionados | - | ~15 | -15 |
| Nuevos consolidados | - | ~8 | +8 |
| Carpetas | 0 | 7 | +7 |

---

## ✅ Beneficios

1. **Claridad**: Documentación organizada por propósito
2. **Actualidad**: Solo información vigente
3. **Accesibilidad**: Fácil encontrar lo que se busca
4. **Mantenibilidad**: Estructura escalable
5. **Profesionalismo**: Documentación de calidad

---

## 🎯 Prioridad de Ejecución

1. ✅ Eliminar obsoletos (Fase 1)
2. ✅ Crear estructura (Fase 2)
3. ✅ Fusionar y mover (Fase 3)
4. ✅ Crear nuevos consolidados (Fase 3)
5. ✅ Actualizar README maestro
6. ✅ Revisar y validar

---

**Fecha del plan**: 17 de octubre de 2025  
**Estado**: Pendiente de aprobación
