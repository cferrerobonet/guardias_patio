
# Roadmap Guardias de Patio - v3.0 y Futuro

## 📅 Planificación General

**Versión Actual**: v2.3 (Optimizaciones completadas)  
**Próxima Versión**: v2.4 (Mejoras de UX/UI)  
**Versión Objetivo**: v3.0 (Robustez y Escalabilidad)

---

## 🎯 Visión de Producto

### Objetivo v2.x → v3.0
Transformar **Guardias de Patio** de una **herramienta de generación** a una **plataforma completa de gestión** de guardias escolares con:

- ✅ Generación automatizada e inteligente
- ✅ Gestión continua y adaptativa (ausencias, sustituciones)
- ✅ Análisis y mejora continua
- ✅ Integración con ecosistema educativo

---

## 🚀 RELEASES PLANIFICADAS

### v2.4 - Mejoras de UX/UI 🎨
**Fecha Objetivo**: Febrero 2025  
**Duración**: 2-3 semanas  
**Prioridad**: ALTA ⭐⭐⭐

#### Objetivos
- Mejorar la experiencia de usuario con búsquedas y filtros
- Añadir feedback visual en operaciones largas
- Implementar atajos de teclado para usuarios avanzados
- Mejorar VistaCalendario con más interactividad

#### Features

##### 2.4.1 - Búsqueda y Filtrado Avanzado
**Tiempo**: 3-5 días  
**Complejidad**: BAJA

- [ ] **Búsqueda en tabla de profesores**
  - Campo de búsqueda en tiempo real sobre nombre/email
  - Resaltar coincidencias en la tabla
  - Limpiar búsqueda con botón X

- [ ] **Filtros combinados en ProfesorForm**
  - Dropdown: Filtrar por turno (mañana/tarde/mixto/todos)
  - Checkbox: Solo tutores / Solo no tutores
  - Slider: Filtrar por rango de horas (0-40)
  - Aplicar filtros sin recargar desde BD

- [ ] **Búsqueda global**
  - Barra de búsqueda en MainWindow
  - Buscar en todas las pestañas
  - Resultados agrupados por entidad

**Archivos afectados**:
- `src/main.py` (ProfesorForm, MainWindow)
- Nuevo: `src/widgets/barra_busqueda.py`

##### 2.4.2 - Feedback Visual
**Tiempo**: 2-3 días  
**Complejidad**: BAJA

- [ ] **Progress bar en generación de guardias**
  - QProgressDialog durante `generar_calendario_guardias()`
  - Actualizar progreso por día procesado
  - Cancelar generación si es muy lenta

- [ ] **Spinners en operaciones largas**
  - Exportación PDF masiva
  - Importación de datos
  - Carga inicial de VistaCalendario

- [ ] **Tooltips informativos**
  - Todos los campos de formularios
  - Botones con acciones no obvias
  - Iconos de estado en tablas

**Archivos afectados**:
- `src/main.py` (AsignacionGuardiasForm, ImportExportForm)
- `src/services/asignador_guardias.py` (añadir callbacks de progreso)
- Nuevo: `src/widgets/spinner_widget.py`

##### 2.4.3 - Atajos de Teclado
**Tiempo**: 2-3 días  
**Complejidad**: BAJA

- [ ] **Atajos globales**
  - `Ctrl+S`: Guardar (en formularios)
  - `Ctrl+F`: Buscar
  - `Ctrl+N`: Nuevo registro
  - `Ctrl+E`: Exportar datos
  - `Ctrl+Tab`: Siguiente pestaña
  - `Ctrl+Shift+Tab`: Pestaña anterior
  - `Ctrl+Q`: Salir

- [ ] **Atajos contextuales**
  - `F5`: Refrescar datos
  - `Del`: Eliminar seleccionado
  - `Esc`: Cancelar operación
  - `Enter`: Confirmar diálogo

**Archivos afectados**:
- `src/main.py` (MainWindow, todos los formularios)
- Usar `QShortcut` de PyQt6

##### 2.4.4 - Mejoras en VistaCalendario
**Tiempo**: 3-4 días  
**Complejidad**: MEDIA

- [ ] **Panel lateral con detalles**
  - Click en día → mostrar panel lateral
  - Lista completa de guardias del día
  - Botones: Editar, Eliminar, Reasignar
  - Cerrar panel con X o Esc

- [ ] **Drag & drop para reasignaciones**
  - Arrastrar celda de guardia a otro día
  - Validar antes de reasignar
  - Confirmar con diálogo

- [ ] **Exportación rápida del mes**
  - Botón "Exportar mes visible"
  - Opciones: PDF, Excel, JSON
  - Guardar configuración de exportación

- [ ] **Imprimir vista actual**
  - Botón "Imprimir"
  - Previsualización antes de imprimir
  - Ajustar a página A4

**Archivos afectados**:
- `src/widgets/vista_calendario.py`
- Nuevo: `src/widgets/panel_detalle_dia.py`

**Resultado v2.4**:
- 🎯 UX mejorada significativamente
- 🎯 Feedback visual en todas las operaciones
- 🎯 Atajos para usuarios avanzados
- 🎯 VistaCalendario más interactiva

---

### v2.5 - Gestión de Ausencias 🏥
**Fecha Objetivo**: Marzo 2025  
**Duración**: 3-4 semanas  
**Prioridad**: CRÍTICA ⭐⭐⭐⭐⭐

#### Objetivos
- Permitir registrar ausencias de profesores (bajas, permisos, vacaciones)
- Evitar asignación de guardias a profesores ausentes
- Reasignar automáticamente guardias afectadas por ausencias
- Visualizar ausencias en calendario

#### Features

##### 2.5.1 - Modelo de Datos de Ausencias
**Tiempo**: 2-3 días  
**Complejidad**: MEDIA

- [ ] **Nueva tabla: `ausencias`**
  ```python
  class Ausencia(Base):
      __tablename__ = 'ausencias'
      id = Column(Integer, primary_key=True)
      profesor_id = Column(Integer, ForeignKey('profesores.id'))
      fecha_inicio = Column(Date, nullable=False)
      fecha_fin = Column(Date, nullable=False)
      tipo_ausencia = Column(String, nullable=False)  # baja_medica, permiso, vacaciones, formacion
      motivo = Column(Text, nullable=True)
      documento_adjunto = Column(String, nullable=True)  # ruta a archivo PDF/imagen
      fecha_registro = Column(DateTime, default=datetime.now)
      activa = Column(Boolean, default=True)
      profesor = relationship('Profesor', back_populates='ausencias')
  ```

- [ ] **Migración Alembic**
  - Crear migración `add_ausencias_table`
  - Añadir relación en modelo Profesor
  - Índices: (profesor_id, fecha_inicio), (fecha_fin)

**Archivos afectados**:
- `src/models/models.py`
- Nuevo: `alembic/versions/xxxx_add_ausencias_table.py`

##### 2.5.2 - Validación de Ausencias en Asignador
**Tiempo**: 3-4 días  
**Complejidad**: MEDIA-ALTA

- [ ] **Validación crítica: No asignar a ausentes**
  - En `_es_elegible()`: Verificar ausencias activas
  - Consultar ausencias que intersecten con fecha de guardia
  - Logging: "Profesor X no elegible (ausencia del Y al Z)"

- [ ] **Función: `profesor_ausente(profesor_id, fecha)`**
  ```python
  def profesor_ausente(session, profesor_id, fecha):
      return session.query(Ausencia).filter(
          Ausencia.profesor_id == profesor_id,
          Ausencia.fecha_inicio <= fecha,
          Ausencia.fecha_fin >= fecha,
          Ausencia.activa == True
      ).first() is not None
  ```

- [ ] **Regeneración al registrar ausencia**
  - Al crear/editar ausencia: buscar guardias afectadas
  - Mostrar lista de guardias que quedan sin cubrir
  - Opción: Reasignar automáticamente

**Archivos afectados**:
- `src/services/asignador_guardias.py`
- Nuevo: `src/services/gestor_ausencias.py`

##### 2.5.3 - Interfaz de Gestión de Ausencias
**Tiempo**: 5-7 días  
**Complejidad**: MEDIA-ALTA

- [ ] **Nueva pestaña: "🏥 Ausencias"**
  - Layout similar a ProfesorForm (lista + formulario)

- [ ] **Lista de ausencias**
  - Tabla: Profesor, Tipo, Fecha Inicio, Fecha Fin, Días, Estado
  - Filtros: Por profesor, por tipo, por periodo
  - Ordenar por fecha
  - Colores: Verde (pasada), Amarillo (activa), Rojo (futura)

- [ ] **Formulario de registro**
  - Selector de profesor
  - Rango de fechas (inicio-fin)
  - Tipo de ausencia (dropdown)
  - Motivo (text area)
  - Adjuntar documento (opcional)
  - Validación: fecha_fin >= fecha_inicio

- [ ] **Acciones**
  - Guardar ausencia
  - Editar ausencia
  - Eliminar ausencia (con confirmación)
  - Desactivar ausencia (marcar como inactiva sin borrar)
  - Ver guardias afectadas

- [ ] **Reasignación de guardias afectadas**
  - Botón: "Buscar guardias afectadas"
  - Mostrar lista de guardias sin sustituto
  - Por cada guardia:
    - Mostrar profesores disponibles (sin ausencia ese día)
    - Asignar sustituto manualmente
    - O usar algoritmo de reasignación automática

**Archivos afectados**:
- Nuevo: `src/widgets/gestionar_ausencias.py`
- `src/main.py` (añadir pestaña)

##### 2.5.4 - Visualización de Ausencias en Calendario
**Tiempo**: 3-4 días  
**Complejidad**: MEDIA

- [ ] **Integración con VistaCalendario**
  - Marcar días con ausencias (icono 🏥)
  - Color diferente para días con ausencias
  - Tooltip: "2 profesores ausentes hoy"

- [ ] **Panel de ausencias del día**
  - En panel lateral: Sección "Ausencias activas"
  - Lista de profesores ausentes ese día
  - Tipo de ausencia y motivo

- [ ] **Filtro por ausencias**
  - Checkbox: "Mostrar solo días con ausencias"
  - Útil para planificar sustituciones

**Archivos afectados**:
- `src/widgets/vista_calendario.py`

##### 2.5.5 - Algoritmo de Reasignación Automática
**Tiempo**: 4-5 días  
**Complejidad**: ALTA

- [ ] **Función: `reasignar_guardias_automaticamente()`**
  - Input: Lista de guardias sin cubrir (por ausencia)
  - Para cada guardia:
    1. Buscar profesores disponibles ese día
    2. Filtrar por turno compatible
    3. Ordenar por:
       - Menor carga actual
       - Continuidad de zona (si ya estuvo en esa zona)
       - Distancia a cuota objetivo
    4. Asignar al mejor candidato
    5. Logging detallado

- [ ] **Modo batch vs individual**
  - Batch: Reasignar todas de golpe (opción predeterminada)
  - Individual: Sugerir candidatos y dejar al usuario decidir

- [ ] **Rollback si falla**
  - Usar transacciones SQLAlchemy
  - Si no se pueden cubrir todas las guardias: rollback completo
  - Mostrar informe de guardias que no se pudieron cubrir

**Archivos afectados**:
- `src/services/gestor_ausencias.py`
- `src/services/asignador_guardias.py` (reutilizar heurísticas)

**Resultado v2.5**:
- 🎯 Gestión completa de ausencias implementada
- 🎯 Asignación inteligente evita profesores ausentes
- 🎯 Reasignación automática de guardias afectadas
- 🎯 Visualización clara en calendario

---

### v2.6 - Exportación Avanzada 📊
**Fecha Objetivo**: Abril 2025  
**Duración**: 2-3 semanas  
**Prioridad**: ALTA ⭐⭐⭐

#### Objetivos
- Añadir exportación a Excel (muy demandado)
- Permitir exportación selectiva (filtros)
- Crear plantillas de exportación reutilizables

#### Features

##### 2.6.1 - Exportación a Excel
**Tiempo**: 5-7 días  
**Complejidad**: MEDIA-ALTA

- [ ] **Dependencia: openpyxl**
  - Añadir a requirements.txt
  - Librería moderna y completa para Excel

- [ ] **Clase: `ExportadorExcel`**
  - Método: `exportar_calendario_completo()`
    - Hoja 1: Calendario general (días x zonas)
    - Hoja 2: Resumen por profesor
    - Hoja 3: Resumen por zona
    - Hoja 4: Estadísticas

  - Método: `exportar_por_profesor(profesor_id, mes, anio)`
    - Similar a PDF pero en Excel
    - Formato tabular más fácil de editar

  - Método: `exportar_todos_los_profesores(mes, anio, carpeta)`
    - Un archivo Excel por profesor
    - O un archivo con múltiples hojas (uno por profesor)

- [ ] **Formato profesional**
  - Estilos: Colores alternados, bordes, fuentes
  - Encabezados: Negrita, fondo gris
  - Anchos de columna automáticos
  - Congelar paneles en encabezados
  - Filtros automáticos en tablas

**Archivos afectados**:
- Nuevo: `src/services/exportador_excel.py`
- `src/main.py` (ImportExportForm: añadir botones Excel)

##### 2.6.2 - Exportación Selectiva
**Tiempo**: 3-4 días  
**Complejidad**: MEDIA

- [ ] **Diálogo de exportación avanzado**
  - QDialog con opciones:
    - Formato: JSON, PDF, Excel
    - Rango de fechas (desde - hasta)
    - Filtros:
      - Profesores: Todos / Seleccionados / Por turno
      - Zonas: Todas / Seleccionadas
      - Recreos: Todos / Solo mañana / Solo tarde
    - Opciones de formato:
      - Incluir estadísticas (sí/no)
      - Incluir gráficos (solo PDF/Excel)
      - Tamaño de página (PDF)

- [ ] **Vista previa**
  - Mostrar resumen de lo que se exportará
  - "Se exportarán X guardias de Y profesores"
  - Botón: Ver detalles (lista completa)

- [ ] **Guardar configuración de exportación**
  - Checkbox: "Guardar esta configuración"
  - Dropdown para cargar configuraciones guardadas
  - Útil para exportaciones recurrentes

**Archivos afectados**:
- Nuevo: `src/widgets/dialogo_exportacion_avanzada.py`
- `src/services/exportador.py` (añadir parámetros de filtrado)
- `src/services/exportador_pdf.py` (idem)
- `src/services/exportador_excel.py` (idem)

##### 2.6.3 - Plantillas de Exportación
**Tiempo**: 2-3 días  
**Complejidad**: BAJA-MEDIA

- [ ] **Tabla: `plantillas_exportacion`**
  ```python
  class PlantillaExportacion(Base):
      __tablename__ = 'plantillas_exportacion'
      id = Column(Integer, primary_key=True)
      nombre = Column(String, nullable=False)
      descripcion = Column(Text)
      formato = Column(String)  # json, pdf, excel
      filtros_json = Column(Text)  # JSON con configuración
      fecha_creacion = Column(DateTime, default=datetime.now)
  ```

- [ ] **Plantillas predefinidas**
  - "Calendario mensual completo" (PDF, todos los profesores)
  - "Informe ejecutivo" (Excel, solo estadísticas)
  - "Guardias por turno de mañana" (PDF, filtrado)
  - "Respaldo completo" (JSON, todo)

- [ ] **Gestión de plantillas**
  - Crear nueva plantilla desde diálogo de exportación
  - Editar plantillas existentes
  - Eliminar plantillas personalizadas
  - Restaurar plantillas predefinidas

**Archivos afectados**:
- `src/models/models.py` (nueva tabla)
- `src/widgets/dialogo_exportacion_avanzada.py`
- Nuevo: `src/services/gestor_plantillas.py`

**Resultado v2.6**:
- 🎯 Exportación a Excel completa
- 🎯 Exportación selectiva con filtros avanzados
- 🎯 Plantillas reutilizables para exportaciones recurrentes

---

### v3.0 - Robustez y Escalabilidad 🏗️
**Fecha Objetivo**: Mayo 2025  
**Duración**: 3-4 semanas  
**Prioridad**: ALTA ⭐⭐⭐

#### Objetivos
- Garantizar seguridad de datos con backups automáticos
- Permitir gestionar múltiples cursos escolares
- Mejorar validaciones y detección de problemas

#### Features

##### 3.0.1 - Backup y Restauración
**Tiempo**: 4-5 días  
**Complejidad**: MEDIA

- [ ] **Sistema de backups automáticos**
  - Antes de operaciones destructivas:
    - Generar guardias (si ya existen)
    - Importar datos (si se va a limpiar)
    - Eliminar múltiples registros
  - Backup incremental diario (opcional)
  - Compresión de backups antiguos

- [ ] **Estructura de backups**
  ```
  backups/
  ├── automaticos/
  │   ├── 2025-01-15_10-30-00.db
  │   ├── 2025-01-14_10-30-00.db
  │   └── ...
  ├── manuales/
  │   ├── antes_importacion_2025-01-10.db
  │   └── ...
  └── config.json (configuración de retención)
  ```

- [ ] **Gestión de backups**
  - Nueva pestaña: "💾 Backups"
  - Lista de backups: Fecha, Tipo, Tamaño
  - Acciones:
    - Crear backup manual (con nombre personalizado)
    - Restaurar desde backup (con confirmación)
    - Eliminar backup
    - Exportar backup a otra ubicación
  - Configuración:
    - Activar/desactivar backups automáticos
    - Días de retención (ej: 30 días)
    - Tamaño máximo de carpeta backups

- [ ] **Restauración segura**
  - Antes de restaurar: Crear backup del estado actual
  - Mostrar comparación: Estado actual vs backup
  - Confirmación doble: "¿Estás seguro?"
  - Rollback automático si la restauración falla

**Archivos afectados**:
- Nuevo: `src/services/gestor_backups.py`
- Nuevo: `src/widgets/gestionar_backups.py`
- `src/main.py` (añadir pestaña)
- `src/database/db_manager.py` (hooks para backups automáticos)

##### 3.0.2 - Múltiples Cursos
**Tiempo**: 6-8 días  
**Complejidad**: ALTA

- [ ] **Modelo de datos multi-curso**
  - Nueva tabla: `cursos`
    ```python
    class Curso(Base):
        __tablename__ = 'cursos'
        id = Column(Integer, primary_key=True)
        nombre = Column(String, nullable=False)  # "2024-2025", "2025-2026"
        anio_inicio = Column(Integer, nullable=False)
        anio_fin = Column(Integer, nullable=False)
        activo = Column(Boolean, default=False)
        archivado = Column(Boolean, default=False)
        fecha_creacion = Column(DateTime, default=datetime.now)
    ```
  
  - Añadir `curso_id` a:
    - `configuracion` (relación 1:1 curso-config)
    - `guardias` (relación N:1)
    - Opcionalmente a `profesores` y `zonas` (si cambian por curso)
  
  - Migración compleja: Crear curso por defecto y asociar datos existentes

- [ ] **Selector de curso en MainWindow**
  - ComboBox en barra superior: "Curso: 2024-2025 ▼"
  - Cambiar de curso → recargar todas las pestañas
  - Guardar curso seleccionado en settings

- [ ] **Gestión de cursos**
  - Nueva pestaña: "📚 Cursos"
  - Acciones:
    - Crear nuevo curso
      - Opción 1: Desde cero
      - Opción 2: Copiar configuración de curso anterior
      - Opción 3: Copiar profesores/zonas (sin guardias)
    - Editar curso (nombre, fechas)
    - Archivar curso (marcar como archivado, solo lectura)
    - Eliminar curso (solo si no tiene guardias)
    - Clonar curso

- [ ] **Comparación entre cursos**
  - Botón: "Comparar con curso anterior"
  - Métricas:
    - Profesores nuevos/retirados
    - Zonas nuevas/eliminadas
    - Cambios en distribución de guardias
    - Estadísticas comparativas

- [ ] **Filtrado por curso**
  - Todas las queries deben filtrar por `curso_id` del curso activo
  - Índices en BD: (curso_id, fecha), (curso_id, profesor_id), etc.

**Archivos afectados**:
- `src/models/models.py` (nueva tabla + relaciones)
- `src/main.py` (selector de curso)
- Nuevo: `src/widgets/gestionar_cursos.py`
- Nuevo: `src/services/gestor_cursos.py`
- `src/database/db_manager.py` (filtrado global por curso)
- TODOS los servicios (añadir filtro curso_id)

##### 3.0.3 - Validaciones Avanzadas
**Tiempo**: 3-4 días  
**Complejidad**: MEDIA

- [ ] **Verificación de integridad al iniciar**
  - Al abrir la app: Ejecutar checks de integridad
  - Verificar:
    - Guardias sin profesor o sin zona (datos huérfanos)
    - Configuración incompleta
    - Profesores con horas inválidas
    - Fechas inconsistentes (fin < inicio)
  - Si hay problemas: Mostrar diálogo con opciones
    - Reparar automáticamente
    - Ver detalles
    - Ignorar (solo esta vez)
    - Crear reporte

- [ ] **Detección de duplicados**
  - Al importar datos: Verificar duplicados
  - Al crear profesor: Verificar si ya existe (por email o nombre)
  - Opciones:
    - Sobrescribir
    - Mantener ambos (renombrar)
    - Cancelar operación

- [ ] **Sugerencias de optimización**
  - Analizar configuración actual
  - Sugerencias:
    - "Tienes 3 profesores sin guardias asignadas"
    - "La zona X está sobrecargada (80% de guardias)"
    - "Profesor Y supera su cuota en 5 guardias"
    - "Ajustar 'ajuste_tutores' a 0.9 equilibraría la carga"
  - Aplicar sugerencias con un click

- [ ] **Modo de mantenimiento**
  - Botón en configuración: "Modo mantenimiento"
  - Al activar:
    - Bloquear generación de guardias
    - Bloquear importación/exportación
    - Solo permitir edición de profesores/zonas
  - Útil para:
    - Limpieza de datos
    - Corrección de errores
    - Preparación de nuevo curso

**Archivos afectados**:
- Nuevo: `src/services/validador_integridad.py`
- `src/main.py` (checks al iniciar)
- Nuevo: `src/widgets/dialogo_verificacion_integridad.py`

**Resultado v3.0**:
- 🎯 Backups automáticos garantizan seguridad de datos
- 🎯 Soporte multi-curso permite reutilizar app año tras año
- 🎯 Validaciones avanzadas detectan y corrigen problemas

---

### v3.1 - Análisis e Inteligencia 🧠
**Fecha Objetivo**: Junio 2025  
**Duración**: 3-4 semanas  
**Prioridad**: MEDIA ⭐⭐

#### Objetivos
- Crear dashboard ejecutivo con KPIs
- Implementar sugerencias inteligentes para optimización
- Añadir auditoría completa de cambios

#### Features

##### 3.1.1 - Dashboard Ejecutivo
**Tiempo**: 5-7 días  
**Complejidad**: MEDIA-ALTA

- [ ] **Nueva pestaña: "📈 Dashboard"**
  - Layout de 2 columnas:
    - Columna izquierda: KPIs (tarjetas)
    - Columna derecha: Gráficos principales

- [ ] **KPIs principales**
  - **Cobertura total**: X% de slots cubiertos
  - **Balance de carga**: Desviación estándar de guardias/profesor
  - **Profesores sub-utilizados**: Menos de Y guardias
  - **Profesores sobre-utilizados**: Más de Z guardias
  - **Zonas sin cubrir**: Días con zonas vacías
  - **Sustituciones realizadas**: En último mes
  - **Ausencias activas**: Profesores ausentes hoy

- [ ] **Gráficos interactivos con Plotly**
  - Gráfico 1: Distribución de guardias (histograma)
  - Gráfico 2: Evolución temporal (guardias por mes)
  - Gráfico 3: Heatmap (profesor x zona)
  - Gráfico 4: Comparación con curso anterior
  - Interactividad: Hover, zoom, filtros dinámicos

- [ ] **Alertas y recomendaciones**
  - Panel de alertas en parte superior
  - Tipos de alerta:
    - ⚠️ Crítico: Zonas sin cubrir hoy
    - ⚠️ Advertencia: Profesor cerca de límite de cuota
    - ℹ️ Info: Próximas ausencias programadas
  - Click en alerta → Ir a sección relevante

- [ ] **Comparación con periodos anteriores**
  - Selector: Comparar con mes anterior / curso anterior
  - Métricas comparativas:
    - Cobertura: +5% vs mes anterior
    - Sustituciones: -10% vs mes anterior
  - Gráficos lado a lado

**Archivos afectados**:
- Nuevo: `src/widgets/dashboard_ejecutivo.py`
- Dependencia nueva: `plotly` (gráficos interactivos)
- `src/services/calculador_guardias.py` (nuevas funciones de stats)

##### 3.1.2 - Sugerencias Inteligentes
**Tiempo**: 6-8 días  
**Complejidad**: ALTA

- [ ] **Motor de sugerencias**
  - Clase: `AnalizadorDistribucion`
  - Métodos:
    - `detectar_desequilibrios()`: Encuentra profesores sub/sobre-utilizados
    - `sugerir_reasignaciones()`: Propone intercambios para equilibrar
    - `optimizar_configuracion()`: Sugiere ajustes en config

- [ ] **Algoritmo de detección de desequilibrios**
  1. Calcular media y desviación estándar de guardias/profesor
  2. Identificar outliers (> 2σ o < 2σ)
  3. Para cada outlier:
     - Buscar guardias que se puedan reasignar
     - Evaluar impacto de reasignación (score)
     - Ordenar por mejor score

- [ ] **Sugerencias de reasignación**
  - Para equilibrar carga:
    - "Reasignar 3 guardias de Profesor A a Profesor B equilibraría la distribución"
  - Para mejorar continuidad:
    - "Intercambiar guardias de Zona X entre Profesor A y B reduciría cambios de zona"
  - Para reducir exceso:
    - "Profesor C tiene 5 guardias más que su cuota. Sugerencias de redistribución"

- [ ] **Sugerencias de configuración**
  - Analizar configuración actual (ajuste_tutores, ajuste_no_tutores)
  - Simular diferentes valores
  - Recomendar el que minimice desviación estándar
  - Ejemplo: "Cambiar ajuste_tutores de 1.0 a 0.85 reduciría desequilibrio en 15%"

- [ ] **Aplicar sugerencias**
  - Mostrar lista de sugerencias con score
  - Vista previa del impacto
  - Aplicar individualmente o en batch
  - Rollback si el resultado no es satisfactorio

**Archivos afectados**:
- Nuevo: `src/services/analizador_distribucion.py`
- Nuevo: `src/widgets/panel_sugerencias.py`
- `src/services/asignador_guardias.py` (reutilizar heurísticas)

##### 3.1.3 - Auditoría Completa
**Tiempo**: 4-5 días  
**Complejidad**: MEDIA

- [ ] **Tabla de auditoría**
  ```python
  class AuditoriaLog(Base):
      __tablename__ = 'auditoria_log'
      id = Column(Integer, primary_key=True)
      fecha_hora = Column(DateTime, default=datetime.now)
      usuario = Column(String)  # Futuro: multi-usuario
      accion = Column(String)  # CREATE, UPDATE, DELETE
      entidad = Column(String)  # Profesor, Zona, Guardia, etc.
      entidad_id = Column(Integer)
      cambios_json = Column(Text)  # JSON con valores antes/después
      ip_address = Column(String, nullable=True)
  ```

- [ ] **Logging automático**
  - Usar SQLAlchemy event listeners
  - `@event.listens_for(Profesor, 'after_insert')`
  - `@event.listens_for(Profesor, 'after_update')`
  - `@event.listens_for(Profesor, 'after_delete')`
  - Registrar cambios en auditoria_log

- [ ] **Visualización de auditoría**
  - Nueva pestaña: "🔍 Auditoría"
  - Tabla: Fecha, Usuario, Acción, Entidad, Detalles
  - Filtros:
    - Por fecha (rango)
    - Por usuario
    - Por entidad (Profesor, Zona, etc.)
    - Por acción (CREATE, UPDATE, DELETE)
  - Exportar log a CSV/Excel

- [ ] **Detalles de cambio**
  - Click en fila → Diálogo con detalles
  - Mostrar valores antes y después (diff visual)
  - Opción: Revertir cambio (si es posible)

**Archivos afectados**:
- `src/models/models.py` (nueva tabla)
- Nuevo: `src/services/auditoria.py`
- Nuevo: `src/widgets/visualizador_auditoria.py`

**Resultado v3.1**:
- 🎯 Dashboard ejecutivo con KPIs y gráficos interactivos
- 🎯 Sugerencias inteligentes para optimizar distribución
- 🎯 Auditoría completa con trazabilidad total

---

### v4.0 - Integración y Automatización 🔗
**Fecha Objetivo**: Julio-Agosto 2025  
**Duración**: 4-6 semanas  
**Prioridad**: BAJA ⭐

#### Objetivos
- Integrar con ecosistema educativo (emails, calendarios externos)
- Automatizar comunicación con profesores
- Opcionalmente: Crear API REST para integraciones

#### Features

##### 4.0.1 - Envío Automático de Emails
**Tiempo**: 5-7 días  
**Complejidad**: MEDIA

- [ ] **Configuración SMTP**
  - Nueva sección en Configuración: "📧 Email"
  - Campos:
    - Servidor SMTP
    - Puerto
    - Usuario
    - Contraseña (encriptada)
    - Email remitente
  - Botón: "Probar conexión"

- [ ] **Plantillas de email**
  - Tabla: `plantillas_email`
    ```python
    class PlantillaEmail(Base):
        __tablename__ = 'plantillas_email'
        id = Column(Integer, primary_key=True)
        nombre = Column(String)
        asunto = Column(String)
        cuerpo_html = Column(Text)
        variables_disponibles = Column(Text)  # {nombre_profesor}, {mes}, etc.
    ```
  
  - Plantillas predefinidas:
    - "Calendario mensual"
    - "Recordatorio de guardia"
    - "Notificación de sustitución"
  
  - Editor de plantillas con WYSIWYG

- [ ] **Envío masivo**
  - Botón en ImportExportForm: "📧 Enviar calendarios por email"
  - Opciones:
    - Destinatarios: Todos / Seleccionados / Por turno
    - Plantilla a usar
    - Adjuntar PDF (sí/no)
    - Enviar ahora / Programar envío
  - Progress bar durante envío
  - Log de envíos: Éxitos/fallos

- [ ] **Recordatorios automáticos**
  - Configuración: Enviar recordatorio X días antes
  - Cron job o tarea programada
  - Email: "Recuerda que tienes guardia el [fecha] en [zona]"

**Archivos afectados**:
- Nuevo: `src/services/gestor_emails.py`
- Nuevo: `src/widgets/configurar_email.py`
- `src/models/models.py` (nueva tabla plantillas)

##### 4.0.2 - Sincronización con Calendarios Externos
**Tiempo**: 6-8 días  
**Complejidad**: ALTA

- [ ] **Exportación a iCal (.ics)**
  - Botón: "Exportar a calendario iCal"
  - Generar archivo .ics con todas las guardias de un profesor
  - Compatible con Google Calendar, Outlook, Apple Calendar

- [ ] **Integración con Google Calendar API**
  - OAuth 2.0 para autenticación
  - Crear eventos en Google Calendar del profesor
  - Actualizar eventos al cambiar guardias
  - Eliminar eventos al eliminar guardias

- [ ] **Integración con Microsoft Outlook API**
  - Similar a Google Calendar
  - Usar Microsoft Graph API

- [ ] **Sincronización bidireccional (avanzado)**
  - Si profesor modifica evento en calendario externo → actualizar en app
  - Requiere webhook o polling periódico

- [ ] **Configuración de sincronización**
  - Por profesor: Conectar con Google/Outlook
  - Opciones:
    - Sincronización automática (sí/no)
    - Frecuencia (inmediata, cada hora, diaria)
    - Calendario destino (crear nuevo o usar existente)

**Archivos afectados**:
- Nuevo: `src/services/sincronizador_calendarios.py`
- Dependencias: `google-api-python-client`, `msal` (Microsoft)
- Nuevo: `src/widgets/configurar_sincronizacion.py`

##### 4.0.3 - API REST (Opcional)
**Tiempo**: 8-10 días  
**Complejidad**: MUY ALTA

- [ ] **Framework: FastAPI**
  - Crear proyecto paralelo o integrar en mismo repo
  - Endpoints:
    - `GET /api/profesores` - Listar profesores
    - `POST /api/profesores` - Crear profesor
    - `GET /api/guardias?fecha={fecha}` - Guardias de un día
    - `POST /api/guardias/generar` - Generar calendario
    - `GET /api/estadisticas` - Obtener estadísticas

- [ ] **Autenticación con JWT**
  - Login: `POST /api/auth/login` → devuelve token JWT
  - Todos los endpoints requieren Authorization header

- [ ] **Documentación automática con Swagger**
  - FastAPI genera docs automáticamente en `/docs`

- [ ] **Versionado de API**
  - `/api/v1/...`
  - Preparar para futuras versiones

- [ ] **Rate limiting**
  - Limitar requests por IP/usuario
  - Prevenir abuso

**Archivos afectados**:
- Nuevo: `api/` (carpeta separada)
  - `api/main.py`
  - `api/routes/profesores.py`
  - `api/routes/guardias.py`
  - `api/auth.py`
  - `api/models.py` (Pydantic schemas)

**Resultado v4.0**:
- 🎯 Envío automático de calendarios por email
- 🎯 Sincronización con Google Calendar y Outlook
- 🎯 (Opcional) API REST para integraciones

---

## 📅 TIMELINE VISUAL

```
Ene 2025      Feb 2025      Mar 2025      Abr 2025      May 2025      Jun 2025      Jul-Ago 2025
│             │             │             │             │             │             │
│─ v2.3 ✅    │             │             │             │             │             │
│   Optim.    │             │             │             │             │             │
│             │             │             │             │             │             │
├─────────────┼─ v2.4 ────┼│             │             │             │             │
│             │  UX/UI     ││             │             │             │             │
│             │  (2-3sem)  ││             │             │             │             │
│             │            ││             │             │             │             │
│             ├────────────┼┼─ v2.5 ─────┼────┤        │             │             │
│             │            ││  Ausencias  │    │        │             │             │
│             │            ││  (3-4sem)   │    │        │             │             │
│             │            ││             │    │        │             │             │
│             │            ├┼─────────────┼────┼─ v2.6 ┼──┤          │             │
│             │            ││             │    │  Export│  │          │             │
│             │            ││             │    │  (2-3s)│  │          │             │
│             │            ││             │    │        │  │          │             │
│             │            ││             │    ├────────┼──┼─ v3.0 ──┼────┤        │
│             │            ││             │    │        │  │  Robustez│    │        │
│             │            ││             │    │        │  │  (3-4sem)│    │        │
│             │            ││             │    │        │  │          │    │        │
│             │            ││             │    │        │  ├──────────┼────┼─ v3.1 ┼──┤
│             │            ││             │    │        │  │          │    │Análisis│  │
│             │            ││             │    │        │  │          │    │(3-4sem)│  │
│             │            ││             │    │        │  │          │    │        │  │
│             │            ││             │    │        │  │          │    ├────────┼──┼─ v4.0
│             │            ││             │    │        │  │          │    │        │  │Integr.
│             │            ││             │    │        │  │          │    │        │  │(4-6sem)
```

---

## 🎯 PRIORIDADES RECOMENDADAS

### Sprint 1 (Inmediato): v2.4 - Quick Wins UX
- ✅ Búsqueda y filtrado
- ✅ Feedback visual
- ✅ Atajos de teclado

**ROI**: Alto - Poco esfuerzo, gran impacto en experiencia

### Sprint 2-3 (Crítico): v2.5 - Ausencias
- ✅ Gestión completa de ausencias
- ✅ Reasignación automática

**ROI**: Muy Alto - Feature más demandada, transforma app en herramienta de gestión continua

### Sprint 4 (Alto Valor): v2.6 - Exportación Excel
- ✅ Exportar a Excel
- ✅ Exportación selectiva

**ROI**: Alto - Excel es estándar en centros educativos

### Sprint 5-6 (Fundacional): v3.0 - Robustez
- ✅ Backups
- ✅ Múltiples cursos
- ✅ Validaciones avanzadas

**ROI**: Muy Alto - Garantiza longevidad y confianza en la app

### Sprints 7-8 (Optimización): v3.1 - Análisis
- ✅ Dashboard
- ✅ Sugerencias inteligentes

**ROI**: Medio-Alto - Añade valor, pero no es crítico

### Sprints 9+ (Integración): v4.0 - Automatización
- ✅ Emails
- ✅ Calendarios externos
- ⚠️ API (solo si hay demanda)

**ROI**: Variable - Depende de necesidades específicas

---

## 📊 MÉTRICAS DE ÉXITO

### v2.4 - UX/UI
- ✅ Reducción de tiempo de búsqueda: -70%
- ✅ Reducción de clics para tareas comunes: -40%
- ✅ Satisfacción de usuario: +30%

### v2.5 - Ausencias
- ✅ Cobertura de guardias: 95%+ incluso con ausencias
- ✅ Tiempo de reasignación: < 2 minutos
- ✅ Adopción: 80%+ de usuarios usan gestión de ausencias

### v2.6 - Exportación Excel
- ✅ 70%+ de exportaciones en formato Excel
- ✅ Reducción de trabajo manual: -60%

### v3.0 - Robustez
- ✅ 0 pérdidas de datos en 6 meses
- ✅ 90%+ de usuarios gestionan múltiples cursos
- ✅ Tiempo de resolución de problemas: -80%

### v3.1 - Análisis
- ✅ Mejora en balance de carga: -25% desviación estándar
- ✅ Adopción de sugerencias: 60%+

### v4.0 - Integración
- ✅ 50%+ de profesores conectan calendarios externos
- ✅ Tasa de apertura de emails: 70%+

---

## 🚧 RIESGOS Y MITIGACIONES

### Riesgo 1: Sobrecarga de Features
**Probabilidad**: Alta  
**Impacto**: Medio  
**Mitigación**:
- Priorizar ruthlessly
- Implementar solo lo que aporta valor real
- Recoger feedback de usuarios reales

### Riesgo 2: Complejidad de Múltiples Cursos
**Probabilidad**: Media  
**Impacto**: Alto  
**Mitigación**:
- Planificar migración cuidadosamente
- Tests exhaustivos
- Rollout gradual (beta testers primero)

### Riesgo 3: Integración con APIs Externas
**Probabilidad**: Media  
**Impacto**: Medio  
**Mitigación**:
- Manejo robusto de errores
- Fallback si API no disponible
- Documentación clara de limitaciones

### Riesgo 4: Performance con Datos Grandes
**Probabilidad**: Baja (ya optimizado en v2.3)  
**Impacto**: Alto  
**Mitigación**:
- Monitorear queries (ya tenemos query_optimizer)
- Paginación en tablas grandes
- Lazy loading donde sea posible

---

## 🔄 PROCESO DE DESARROLLO

### 1. Planificación
- Seleccionar features del sprint
- Estimar esfuerzo (días de desarrollo)
- Identificar dependencias

### 2. Diseño
- Diseño de UI (mockups si es necesario)
- Diseño de BD (nuevas tablas, migraciones)
- Diseño de API (interfaces de servicios)

### 3. Implementación
- Desarrollo TDD (tests primero)
- Commits frecuentes
- Code review (si hay equipo)

### 4. Testing
- Tests unitarios (mantener 98%+ cobertura)
- Tests de integración
- Tests manuales (escenarios de usuario)

### 5. Documentación
- Actualizar README si cambian features principales
- Actualizar GUIA_DESARROLLO.md con nuevos componentes
- Crear guías de usuario para features complejas

### 6. Release
- Actualizar CHANGELOG.md
- Tag de versión en git
- Generar release notes
- Comunicar cambios a usuarios

---

## 📞 FEEDBACK Y CONTRIBUCIONES

Este roadmap es **vivo y flexible**. Se actualizará en base a:
- Feedback de usuarios reales
- Cambios en prioridades
- Nuevas ideas y oportunidades
- Restricciones técnicas descubiertas

**Canales de feedback**:
- GitHub Issues (reportar bugs, solicitar features)
- Discusiones con usuarios
- Encuestas de satisfacción

---

**Mantenido por**: Equipo de Desarrollo Guardias de Patio  
**Última actualización**: 15 de enero de 2025  
**Versión del documento**: 1.0
