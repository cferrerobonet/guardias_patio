# Guía Completa de Funcionalidades - Guardias de Patio v2.9.0

**Versión:** 2.9.0  
**Fecha:** Diciembre 2025  
**Proyecto:** Guardias de Patio

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Vista de Calendario](#vista-de-calendario)
3. [Gestión de Ausencias](#gestión-de-ausencias)
4. [Importar y Exportar Datos](#importar-y-exportar-datos)
5. [Atajos de Teclado](#atajos-de-teclado)
6. [Solución de Problemas](#solución-de-problemas)
7. [Roadmap de Mejoras](#roadmap-de-mejoras)

---

## 1. Introducción

Este documento centraliza toda la documentación de **funcionalidades principales** del sistema Guardias de Patio v2.9.0, cubriendo las características más utilizadas por los usuarios finales.

### Funcionalidades Incluidas

- **📅 Vista de Calendario**: Visualización interactiva de guardias asignadas
- **🏥 Gestión de Ausencias**: Registro, reasignación y seguimiento de ausencias
- **📦 Importar/Exportar**: Portabilidad de datos en formato JSON

---

## 2. Vista de Calendario

### 📅 ¿Qué es la Vista de Calendario?

La **Vista de Calendario** es una interfaz interactiva que permite visualizar todas las guardias asignadas de forma gráfica y organizada. Puedes navegar por fechas, aplicar filtros y ver detalles específicos de cada día.

---

### 🚀 Características Principales

#### 1. **Calendario Interactivo**
- Navega por meses y años con los controles del calendario
- Haz clic en cualquier día para ver sus guardias
- Vista mensual clara y fácil de usar

#### 2. **Filtros Avanzados**
Filtra las guardias mostradas por:
- **Profesor**: Ver solo las guardias de un profesor específico
- **Zona**: Filtrar por zona de vigilancia
- **Turno**: Mostrar solo guardias de mañana, tarde o todas

#### 3. **Detalles del Día**
Al seleccionar un día, verás:
- Número total de guardias ese día
- Guardias organizadas por turno y recreo
- Nombre del profesor y zona asignada para cada guardia

#### 4. **Estadísticas en Tiempo Real**
Panel de estadísticas que muestra:
- Total de guardias (según filtros aplicados)
- Guardias de mañana
- Guardias de tarde
- Si filtras por profesor: información adicional del profesor

---

### 📖 Cómo Usar la Vista de Calendario

#### Paso 1: Acceder a la Vista
1. Abre la aplicación
2. Ve a la pestaña **"📅 Calendario"**
3. El calendario se carga automáticamente con la fecha actual

#### Paso 2: Navegar por Fechas
- **Cambiar de mes**: Usa las flechas en la cabecera del calendario
- **Cambiar de año**: Haz clic en el mes/año y selecciona
- **Volver a hoy**: Haz doble clic en cualquier día

#### Paso 3: Ver Guardias de un Día
1. Haz clic en cualquier día del calendario
2. El panel derecho mostrará las guardias de ese día
3. Las guardias se organizan por turno y recreo

**Ejemplo de visualización:**
```
📅 15/10/2025 - 3 guardia(s)

🕐 MAÑANA - Recreo 1
────────────────────────────────────────
  • GARCÍA LÓPEZ, JUAN → Patio Principal
  • MARTÍNEZ RUIZ, MARÍA → Biblioteca

🕐 TARDE - Recreo 1
────────────────────────────────────────
  • FERNÁNDEZ PÉREZ, CARLOS → Cafetería
```

#### Paso 4: Aplicar Filtros

##### Filtrar por Profesor
1. En el panel derecho, despliega **"Profesor"**
2. Selecciona un profesor de la lista
3. El calendario y detalles se actualizan automáticamente
4. Solo verás guardias de ese profesor

**Uso típico**: "Quiero ver todas las guardias de Juan Pérez este mes"

##### Filtrar por Zona
1. Despliega **"Zona"**
2. Selecciona una zona (ej: "Patio Principal")
3. Solo verás guardias de esa zona

**Uso típico**: "¿Quién vigila la Biblioteca en octubre?"

##### Filtrar por Turno
1. Despliega **"Turno"**
2. Selecciona: Todos, mañana, o tarde
3. Las guardias se filtran por el turno seleccionado

**Uso típico**: "Solo quiero ver guardias de la tarde"

##### Combinar Filtros
Puedes combinar múltiples filtros:
- Profesor + Turno: "Guardias de mañana de María López"
- Zona + Turno: "Guardias de tarde en el Patio Principal"
- Todos: "Guardias de mañana de Juan en la Biblioteca"

#### Paso 5: Limpiar Filtros
1. Haz clic en **"Limpiar filtros"**
2. Todos los filtros vuelven a "Todos"
3. Se muestran todas las guardias nuevamente

---

### 💡 Casos de Uso Prácticos

#### 1. Verificar Asignación de un Profesor
**Situación**: Quieres ver todas las guardias de un profesor en el mes.

**Pasos**:
1. Selecciona el profesor en el filtro
2. Navega por el mes en el calendario
3. Haz clic en diferentes días para ver detalles
4. Las estadísticas te mostrarán el total de guardias

#### 2. Comprobar Cobertura de una Zona
**Situación**: Necesitas asegurarte de que la Biblioteca tiene cobertura todos los días.

**Pasos**:
1. Selecciona "Biblioteca" en el filtro de zona
2. Navega por el mes
3. Los días sin guardias no mostrarán información
4. Identifica huecos en la cobertura

#### 3. Revisar Guardias de un Día Específico
**Situación**: Quieres ver quién vigila el 15 de octubre.

**Pasos**:
1. Asegúrate de que los filtros estén en "Todos"
2. Navega hasta octubre
3. Haz clic en el día 15
4. Ve todos los detalles organizados por turno y recreo

#### 4. Verificar Equidad en Turnos
**Situación**: Quieres confirmar que un profesor tiene guardias balanceadas entre mañana y tarde.

**Pasos**:
1. Selecciona el profesor en el filtro
2. Las estadísticas mostrarán:
   - Total guardias
   - Guardias de mañana
   - Guardias de tarde
3. Compara los números para verificar balance

---

### 📊 Interpretación de Estadísticas

#### Panel de Estadísticas

**Sin filtros aplicados:**
```
📊 Total guardias: 150
🌅 Mañana: 75
🌆 Tarde: 75
```
*Muestra todas las guardias en la base de datos*

**Con filtro de profesor:**
```
📊 Total guardias: 15
🌅 Mañana: 8
🌆 Tarde: 7

👤 GARCÍA LÓPEZ, JUAN
   Turno: mixto
   Tutor: Sí
```
*Muestra solo las guardias de ese profesor*

**Con filtro de zona:**
```
📊 Total guardias: 30
🌅 Mañana: 20
🌆 Tarde: 10
```
*Muestra solo las guardias de esa zona*

---

### ⚙️ Configuración y Actualización

#### Rango de Fechas Visible
El calendario muestra:
- Todos los días del mes actual
- Puedes navegar a cualquier mes/año
- No hay límite de navegación

#### Actualización de Datos
Los datos se actualizan:
- ✅ Automáticamente al cambiar filtros
- ✅ Automáticamente al seleccionar un día
- ❌ NO automáticamente si cambias guardias en otra pestaña
  - **Solución**: Cambia de pestaña y vuelve para refrescar

---

### 🚫 Limitaciones Conocidas

1. **No permite editar guardias**
   - Esta es solo una vista de visualización
   - Para editar, usa la pestaña "Asignación de Guardias"

2. **No resalta días con guardias**
   - Mejora futura: marcar días con guardias con color especial

3. **No muestra resumen mensual**
   - Mejora futura: vista de resumen por mes

4. **No exporta vista filtrada**
   - Mejora futura: exportar calendario filtrado a PDF/Excel

---

### 💡 Tips y Trucos

**Tip 1: Revisión Rápida de un Profesor**
Para revisar rápidamente todas las guardias de un profesor:
1. Filtra por el profesor
2. Mira las estadísticas para el total
3. Navega mes a mes haciendo clic en diferentes días

**Tip 2: Encontrar Huecos de Cobertura**
Para encontrar días sin cobertura en una zona:
1. Filtra por la zona
2. Navega por el mes
3. Los días sin guardias dirán "No hay guardias asignadas"

**Tip 3: Verificar Balance de Turnos**
Para cada profesor, verifica el balance:
1. Filtra por el profesor
2. Compara los números de "Mañana" vs "Tarde" en estadísticas
3. Deberían ser similares para profesores de turno mixto

---

## 3. Gestión de Ausencias

### 🏥 Introducción

La **Gestión de Ausencias** es una funcionalidad crítica introducida en la versión 2.5 que transforma la aplicación de un simple "generador" a un verdadero "gestor continuo" de guardias.

#### ¿Por qué es importante?

- ✅ **Prevención automática**: Profesores ausentes no reciben guardias al generar el calendario
- ✅ **Reasignación inteligente**: Las guardias afectadas pueden reasignarse automáticamente
- ✅ **Visibilidad clara**: El calendario muestra qué días tienen profesores ausentes
- ✅ **Historial completo**: Mantiene registro de todas las ausencias (activas e inactivas)

---

### 🚀 Características Principales

#### 1. Registro de Ausencias

**Tipos soportados**:
- 🏥 Baja médica
- 📋 Permiso
- 🏖️ Vacaciones
- 📝 Otros

**Campos**:
- Profesor
- Fechas (inicio y fin)
- Tipo
- Motivo (opcional)
- Estado (activa/inactiva)

#### 2. Gestión de Guardias Afectadas

- **Preview en tiempo real**: Muestra guardias afectadas antes de guardar
- **Reasignación automática**: Algoritmo inteligente selecciona los mejores sustitutos
- **Reasignación manual**: Opción de elegir sustituto específico
- **Validaciones**: Verifica disponibilidad y evita sobrecargas

#### 3. Visualización en Calendario

- **Icono 🏥**: Días con ausencias marcados claramente
- **Contador**: Muestra número de profesores ausentes por día
- **Colores**: Visual claro en la leyenda del calendario

---

### 📖 Acceso a la Funcionalidad

#### Ubicación

La funcionalidad de ausencias se encuentra en la pestaña **"🏥 Ausencias"** de la aplicación principal.

```
Menú Principal → Pestaña "🏥 Ausencias"
```

#### Layout de la Interfaz

**Panel Izquierdo: Lista de Ausencias**
- Tabla con todas las ausencias registradas
- Columnas: ID, Profesor, Tipo, Fecha Inicio, Fecha Fin, Días, Estado
- Códigos de color:
  - 🟨 **Amarillo**: Ausencia en curso (activa hoy)
  - 🔵 **Cyan**: Ausencia futura
  - ⬜ **Gris**: Ausencia pasada
  - 🔴 **Rojo**: Ausencia inactiva

**Panel Derecho: Formulario**
- Selector de profesor
- Campos de fecha
- Tipo de ausencia
- Motivo (opcional)
- Preview de guardias afectadas

---

### 📝 Registrar una Ausencia

#### Paso a Paso

##### 1. Acceder al Formulario

- Ir a la pestaña **"🏥 Ausencias"**
- El panel derecho muestra **"✏️ NUEVA AUSENCIA"**

##### 2. Completar Datos

**Seleccionar Profesor**
- Dropdown con lista de todos los profesores
- Ordenados alfabéticamente

**Seleccionar Tipo**
- baja_medica
- permiso
- vacaciones
- otros

**Establecer Fechas**
- **Fecha de inicio**: Primer día de ausencia
- **Fecha de fin**: Último día de ausencia
- Usa el calendario popup para selección rápida

**Motivo (Opcional)**
- Descripción libre
- Ejemplo: "Gripe estacional", "Permiso por asunto familiar"

##### 3. Preview de Guardias Afectadas

Mientras completas los datos, el panel **"📊 Guardias Afectadas (Preview)"** muestra automáticamente:

- Número total de guardias afectadas
- Lista detallada (primeras 10):
  - Fecha
  - Turno
  - Recreo
  - Zona

**Ejemplo de Preview:**

```
⚠️ 3 guardias afectadas:

• 18/10/2025 - mañana - Recreo 1 - Patio Principal
• 21/10/2025 - mañana - Recreo 2 - Porche
• 23/10/2025 - mañana - Recreo 1 - Patio Trasero
```

Si no hay guardias:
```
✅ No hay guardias asignadas en este periodo
```

##### 4. Guardar

- Click en **"💾 Guardar Ausencia"** (o presiona **Ctrl+S**)
- Mensaje de confirmación: "Ausencia registrada correctamente"
- La tabla se actualiza automáticamente

---

### 🔄 Gestionar Guardias Afectadas

#### Opción 1: Durante el Registro

Al guardar una ausencia, el sistema **NO reasigna automáticamente** las guardias. Esto te permite:

1. Registrar la ausencia
2. Seleccionarla de la tabla
3. Click en **"👁️ Ver Guardias Afectadas"**

#### Opción 2: Después del Registro

1. Selecciona una ausencia de la tabla (doble click o click + botón Editar)
2. Click en **"👁️ Ver Guardias Afectadas"**
3. Se abre el **Diálogo de Reasignación**

---

### 🤖 Diálogo de Reasignación

El diálogo muestra:

**Tabla de Guardias**: Todas las guardias del profesor ausente en ese periodo
- ID, Fecha, Turno, Recreo, Zona, Profesor Actual

**Opciones de Reasignación**:

#### A) Reasignación Automática

- Click en **"🤖 Reasignar Automáticamente"**
- El sistema:
  1. Busca profesores disponibles para cada guardia
  2. Ordena por menor carga actual
  3. Asigna al mejor candidato
  4. Muestra resultado:
     ```
     Reasignación completada:
     
     ✅ Reasignadas: 3
     ❌ Fallidas: 0
     ```

**Algoritmo de selección:**

```python
Para cada guardia:
  1. Buscar profesores con turno compatible
  2. Excluir profesores ausentes ese día
  3. Excluir profesores con guardia ese día
  4. Ordenar por:
     - Menor número de guardias asignadas hoy
     - Continuidad de zona (si ya estuvo ahí)
  5. Asignar al primero de la lista
```

#### B) Reasignación Manual

- Selecciona una guardia específica de la tabla
- Click en **"👤 Reasignar Seleccionada"**
- Se muestra lista de profesores disponibles:
  ```
  GARCÍA LÓPEZ, JUAN (0 guardias hoy)
  MARTÍNEZ RUIZ, ANA (0 guardias hoy)
  FERNÁNDEZ PÉREZ, LUIS (1 guardias hoy)
  ```
- Selecciona el profesor deseado
- Confirmación: "Guardia reasignada a [Profesor]"

---

### 📅 Visualización en Calendario

#### Marcadores en el Calendario

Al ir a la pestaña **"📅 Vista Calendario"**, los días con ausencias se identifican claramente:

**Icono 🏥 en el Número del Día**

```
┌─────────┐
│  18 🏥  │  ← Día con ausencias
│         │
│ 🕐 M R1 │
│ GARCÍA  │
└─────────┘
```

**Contador de Ausentes**

En la parte inferior de cada día:

```
🏥 2 ausente(s)
```

**Leyenda del Calendario**

```
📋 Leyenda:
⬜ Sin guardias   🟦 Con guardias   🟨 Hoy   🏥 Con ausencias
```

---

### 💡 Casos de Uso Comunes

#### Caso 1: Baja Médica de Corta Duración

**Escenario**: Un profesor enferma y estará ausente 3 días.

**Pasos**:

1. Ir a **🏥 Ausencias**
2. Seleccionar profesor
3. Tipo: `baja_medica`
4. Fecha inicio: Hoy
5. Fecha fin: Hoy + 2 días
6. Motivo: "Gripe"
7. **Guardar**
8. Click **"Ver Guardias Afectadas"**
9. Click **"Reasignar Automáticamente"**
10. Confirmar

**Resultado**: Las 3 guardias se reasignan a otros profesores disponibles.

---

#### Caso 2: Vacaciones Planificadas

**Escenario**: Un profesor solicitó vacaciones para la próxima semana (5 días lectivos).

**Pasos**:

1. **Antes de generar guardias del mes**:
   - Registrar ausencia con fechas de las vacaciones
   - Tipo: `vacaciones`
   - Motivo: "Vacaciones personales aprobadas"
   - Guardar

2. **Generar guardias normalmente**:
   - El sistema **automáticamente excluye** al profesor ausente
   - No necesita reasignación posterior

**Ventaja**: Prevención > Corrección

---

#### Caso 3: Reactivar Ausencia Desactivada

**Escenario**: Se desactivó una ausencia por error.

**Solución Temporal**:
- Eliminar la ausencia
- Crear nueva ausencia con los mismos datos

**Mejora Futura (v3.0)**: Botón "Reactivar" para ausencias inactivas.

---

### ✏️ Editar una Ausencia

#### Cuándo Editar

- Cambiar fechas (extender o acortar ausencia)
- Cambiar tipo o motivo
- Corregir datos incorrectos

#### Pasos

1. **Seleccionar** ausencia de la tabla (doble click)
2. El formulario se llena con los datos actuales
3. **Modificar** los campos necesarios
4. **Guardar** (Ctrl+S)
5. El sistema:
   - Actualiza la ausencia en BD
   - Recalcula preview de guardias afectadas
   - **NO reasigna automáticamente**

⚠️ **Importante**: Si cambias las fechas, revisa manualmente las guardias afectadas.

---

### 🗑️ Eliminar vs Desactivar

#### Eliminar (Borrado Permanente)

**Cuándo usar**:
- Ausencia registrada por error
- Datos completamente incorrectos

**Pasos**:
1. Seleccionar ausencia
2. Click **"🗑️ Eliminar"**
3. Confirmar eliminación
4. **Efecto**: Se borra de la base de datos (no recuperable)

#### Desactivar (Mantener Historial)

**Cuándo usar**:
- Ausencia que ya no aplica pero quieres conservar el registro
- Ausencia cancelada (profesor volvió antes)
- Necesitas historial para auditoría

**Pasos**:
1. Seleccionar ausencia
2. Click **"⏸️ Desactivar"**
3. **Efecto**:
   - Marca `activa = False` en BD
   - Se muestra en rojo en la tabla
   - No se considera en cálculos futuros
   - Preserva historial

---

### ❓ Preguntas Frecuentes

**¿Las ausencias afectan la generación de guardias?**

**Sí**. Al generar un nuevo calendario de guardias:
1. El sistema verifica ausencias activas para cada día
2. Profesores ausentes **NO reciben guardias** ese día
3. El algoritmo redistribuye automáticamente

**¿Puedo registrar una ausencia para un día pasado?**

**Sí**. El sistema permite registrar ausencias en cualquier fecha. Útil para:
- Actualizar registros históricos
- Justificar ausencias retrospectivamente

**¿Qué pasa si no hay profesores disponibles para reasignar?**

El sistema:
1. Intenta reasignar cada guardia
2. Si no encuentra sustituto disponible:
   - Marca como "fallida"
   - Incluye en el reporte final
   - La guardia queda asignada al profesor ausente (⚠️ requiere intervención manual)

**Recomendación**: Revisar el informe de reasignación y gestionar manualmente las guardias fallidas.

---

### 🔧 Arquitectura Técnica (Para Desarrolladores)

#### Modelo de Datos

**Tabla: `ausencias`**

```sql
CREATE TABLE ausencias (
    id INTEGER PRIMARY KEY,
    profesor_id INTEGER NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    tipo VARCHAR NOT NULL,
    motivo TEXT,
    documento_path VARCHAR,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME,
    FOREIGN KEY (profesor_id) REFERENCES profesores(id)
);
```

#### Servicios

**Archivo**: `src/services/gestor_ausencias.py`

**Funciones principales**:
- `registrar_ausencia()`: Crea nueva ausencia con validaciones
- `editar_ausencia()`: Modifica ausencia existente
- `eliminar_ausencia()`: Borra permanentemente
- `desactivar_ausencia()`: Marca como inactiva
- `obtener_guardias_afectadas()`: Busca guardias del periodo
- `reasignar_guardias_automaticamente()`: Algoritmo de reasignación
- `obtener_profesores_disponibles()`: Filtra candidatos para sustitución

#### Validaciones en Asignación

**Archivo**: `src/services/asignador_guardias.py`

**Función clave**: `profesor_ausente(session, profesor_id, fecha)`

Integrada en el algoritmo de generación de guardias:

```python
# VALIDACIÓN AUSENCIAS: Excluir profesores ausentes en esta fecha
if profesor_ausente(session, p.id, slot.fecha):
    logger.debug(f"Profesor {p.nombre_completo} ausente el {slot.fecha}")
    continue
```

---

## 4. Importar y Exportar Datos

### 📦 ¿Qué Datos se Exportan?

- ✅ **Profesores**: Nombre, email, horas, turno, restricciones
- ✅ **Zonas**: Todas las zonas de vigilancia configuradas  
- ✅ **Configuración**: Fechas de curso, horarios de recreos, festivos, multiplicadores
- ✅ **Guardias**: Todas las guardias asignadas (opcional)

---

### 🚀 Cómo Exportar

1. Ve a la pestaña **"Importar / Exportar"**
2. Clic en **"Exportar a JSON..."**
3. Selecciona ubicación (por defecto: `guardias_patio_export.json`)
4. Archivo guardado con todos los datos actuales

#### Formato del Archivo

```json
{
  "version": "1.0",
  "fecha_exportacion": "2025-12-01",
  "profesores": [
    {
      "nombre_completo": "GARCÍA LÓPEZ, JUAN",
      "email_corporativo": "juan.garcia@colegio.edu",
      "horas_contrato": 25.0,
      "porcentaje_jornada": 100.0,
      "turno": "mixto",
      "tutor": true,
      "fecha_inicio_guardias": "2025-09-01",
      "dias_semana_permitidos": "0,1,2,3,4",
      "recreos_permitidos": "1,2,3,4"
    }
  ],
  "zonas": [
    {
      "nombre_zona": "Patio Principal",
      "descripcion": "Zona principal del colegio"
    }
  ],
  "configuracion": {
    "fecha_inicio_curso": "2025-09-01",
    "fecha_fin_curso": "2026-06-30",
    "hora_recreo1_manana": "10:30",
    "hora_recreo2_manana": "12:30",
    "activar_festivos_automaticos": true,
    "ajuste_tutores": 0.90,
    "ajuste_no_tutores": 1.00
  },
  "guardias": []
}
```

---

### 📥 Cómo Importar

#### ⚠️ IMPORTANTE: Hacer Respaldo Antes

Antes de importar, **exporta datos actuales** como respaldo de seguridad.

#### Pasos:

1. Ve a **"Importar / Exportar"**
2. **(Recomendado)** Marca **"Eliminar datos existentes antes de importar"**
   - Evita conflictos y duplicados
   - Sincronización completa
3. Clic en **"Importar desde JSON..."**
4. Selecciona archivo JSON
5. Confirma operación
6. **Reinicia la aplicación** para ver cambios

#### Opciones de Importación:

**Con limpieza (recomendado)**:
- ✅ Evita duplicados
- ✅ Sincronización completa  
- ⚠️ Elimina datos actuales

**Sin limpieza**:
- ⚠️ Puede crear duplicados
- ⚠️ Conflictos con datos existentes
- ℹ️ Útil solo para añadir datos nuevos específicos

---

### 🔄 Casos de Uso

#### 1. Transferir Configuración Entre Equipos

**Equipo origen:**
```
1. Exportar → guardias_config.json
2. Copiar a pendrive/nube
```

**Equipo destino:**
```
1. Copiar archivo
2. Importar (con limpieza)
3. Reiniciar aplicación
```

#### 2. Respaldo Periódico

```
1. Exportar → respaldo_YYYY_MM_DD.json
2. Guardar en disco/nube
```

#### 3. Nuevo Curso Escolar

```
1. Exportar curso anterior (histórico)
2. Editar JSON: actualizar fechas
3. Limpiar guardias: "guardias": []
4. Importar nueva configuración
```

#### 4. Corrección Masiva de Datos

```
1. Exportar → corregir.json
2. Editar JSON con búsqueda/reemplazo
3. Importar (con limpieza)
```

---

### 🛠️ Solución de Problemas

**Archivo JSON no se puede importar**
- Verifica que sea JSON válido (abre con editor de texto)
- Revisa estructura (version, profesores, zonas, etc.)
- Comprueba que no esté corrupto

**Datos no aparecen tras importar**
- **Reinicia la aplicación** (vistas pueden estar cacheadas)

**Error al importar guardias**
- Las guardias requieren profesores y zonas existentes
- Importa archivo completo con todos los datos

**Perdí datos al importar**
- Si hiciste respaldo, impórtalo para restaurar
- Importación con limpieza elimina datos permanentemente

---

### 📋 Recomendaciones

1. **Respaldos regulares**: Exportar al menos mensualmente
2. **Nombrar con fechas**: `guardias_2025_12_01.json`
3. **Múltiples ubicaciones**: Local + nube
4. **Exportar antes de cambios**: Respaldo preventivo
5. **Verificar después**: Comprobar que todo importó correctamente

---

### 🔒 Seguridad y Privacidad

- Archivos contienen **datos personales** (nombres, emails)
- **No compartir públicamente**
- **Proteger** con contraseña si contiene información sensible
- Usar medios seguros al transferir (no email sin cifrar)

---

### 💡 Consejos Avanzados

#### Editar Manualmente el JSON

Puedes editar con editor de texto para:
- Corregir errores masivos
- Actualizar múltiples registros simultáneamente
- Modificar configuración antes de importar

**Ejemplo**: Cambiar turno de todos los profesores
```json
// Buscar/Reemplazar:
"turno": "mañana"  →  "turno": "tarde"
```

#### Combinar Datos de Múltiples Equipos

1. Exportar de cada equipo
2. Abrir ambos JSON con editor
3. Copiar secciones entre archivos
4. Importar archivo combinado

⚠️ **Cuidado con duplicados** al combinar manualmente

---

### 🔧 Implementación Técnica

#### Archivos Involucrados
- **Servicio**: `src/services/exportador.py` (clase `ExportadorDatos`)
- **UI**: `src/main.py` (clase `ImportExportForm`)
- **Tests**: `tests/test_exportador.py` (14 tests, 100% aprobados)

#### Métodos Principales
- `exportar_todo()` - Exporta todo a JSON
- `importar_todo()` - Importa desde JSON
- `exportar_profesores()`, `exportar_zonas()`, etc.
- Funciones helper para serialización de fechas/horas

---

## 5. Atajos de Teclado

### Pestaña: 🏥 Ausencias

| Atajo | Acción |
|-------|--------|
| **Ctrl+S** | Guardar ausencia actual |
| **Ctrl+F** | Enfocar campo de búsqueda de profesor |
| **F5** | Refrescar lista de ausencias |
| **Del** | Eliminar ausencia seleccionada |
| **Esc** | Cancelar edición y limpiar formulario |
| **Enter** | Guardar ausencia (si formulario tiene foco) |
| **Doble Click** | Editar ausencia seleccionada |

### Pestaña: 📅 Calendario

| Atajo | Acción |
|-------|--------|
| **← →** | Navegar entre meses |
| **Ctrl+H** | Ir a hoy |
| **Doble Click** | Seleccionar día |
| **Ctrl+F** | Enfocar filtros |
| **Esc** | Limpiar filtros |

---

## 6. Solución de Problemas

### Vista de Calendario

**No veo guardias en el calendario**

**Posibles causas**:
1. No has generado guardias aún
   - **Solución**: Ve a "Asignación de Guardias" y genera
2. Los filtros están muy restrictivos
   - **Solución**: Limpia los filtros
3. Estás mirando un mes sin guardias asignadas
   - **Solución**: Navega al periodo del curso escolar

**Las estadísticas muestran 0**

**Causa**: Los filtros están eliminando todas las guardias  
**Solución**: Limpia los filtros uno por uno para ver cuál está causando el problema

**Al seleccionar un día no se actualiza**

**Causa**: Posible bug de interfaz  
**Solución**: 
1. Cambia de pestaña y vuelve
2. Si persiste, reinicia la aplicación

---

### Gestión de Ausencias

**Las ausencias no se reflejan en guardias generadas**

**Causa**: Las guardias se generaron antes de registrar la ausencia  
**Solución**: 
1. Reasigna las guardias afectadas manualmente
2. O regenera el calendario completo

**No puedo reasignar una guardia**

**Causa**: No hay profesores disponibles ese día  
**Solución**: 
1. Verifica ausencias de otros profesores
2. Considera reasignar manualmente eligiendo un profesor con menor carga

**La reasignación automática falla**

**Causa**: Restricciones muy estrictas (días permitidos, recreos, etc.)  
**Solución**: 
1. Revisa restricciones de profesores
2. Usa reasignación manual con criterio profesional

---

### Importar/Exportar

**Error al importar JSON**

**Causa**: Formato JSON inválido  
**Solución**: 
1. Abre el archivo con un editor de texto
2. Valida la sintaxis JSON online (jsonlint.com)
3. Corrige errores de formato

**Faltan datos después de importar**

**Causa**: Archivo JSON incompleto o corrupto  
**Solución**: 
1. Restaura desde respaldo
2. Verifica que el archivo JSON contiene todas las secciones

**Duplicados después de importar**

**Causa**: Importaste sin marcar "Eliminar datos existentes"  
**Solución**: 
1. Exporta como respaldo
2. Importa nuevamente CON limpieza marcada

---

## 7. Roadmap de Mejoras

### v3.0 - Mejoras de Ausencias

- [ ] Filtros avanzados (por profesor, tipo, periodo)
- [ ] Exportación a Excel de ausencias
- [ ] Soporte para ausencias por turno (medio día)
- [ ] Notificaciones automáticas de ausencias próximas
- [ ] Botón "Reactivar" para ausencias desactivadas

### v3.1 - Mejoras de Calendario

- [ ] Resaltar días con guardias en el calendario
- [ ] Código de colores por turno o zona
- [ ] Vista de resumen mensual
- [ ] Exportar vista filtrada a PDF/Excel
- [ ] Imprimir calendario del mes
- [ ] Vista de semana (más detallada)

### v3.2 - Estadísticas de Ausencias

- [ ] Dashboard de ausencias (total, por tipo, tendencias)
- [ ] Gráficos de ausencias por mes
- [ ] Comparativa entre profesores
- [ ] Impacto en distribución de guardias

### v3.3 - Integración Avanzada

- [ ] Importar ausencias desde archivo Excel
- [ ] Sincronización con calendario Google/Outlook
- [ ] Notificaciones por email de reasignaciones
- [ ] API REST para integración con otros sistemas

---

## 📚 Referencias Técnicas

### Archivos de Interfaz

- **Vista Calendario**: `src/widgets/vista_calendario.py`
- **Gestión Ausencias**: `src/widgets/gestionar_ausencias.py`
- **Import/Export**: `src/main.py` (clase `ImportExportForm`)

### Servicios

- **Gestor Ausencias**: `src/services/gestor_ausencias.py`
- **Exportador Datos**: `src/services/exportador.py`
- **Asignador Guardias**: `src/services/asignador_guardias.py`

### Modelos

- **Ausencia**: `src/models/models.py` (clase `Ausencia`)
- **Guardia**: `src/models/models.py` (clase `Guardia`)
- **Profesor**: `src/models/models.py` (clase `Profesor`)

### Tests

- **Tests Exportador**: `tests/test_exportador.py` (14 tests)
- **Tests Asignador**: `tests/test_asignador.py` (12 tests)
- **Tests Ausencias**: Integrados en suite completa

---

## 📞 Soporte y Contacto

**Versión de la Documentación**: v2.9.0  
**Fecha**: Diciembre 2025  
**Mantenido por**: Equipo Guardias de Patio

**Para reportar bugs o sugerir mejoras**:
- GitHub Issues: [https://github.com/cferrerobonet/guardias_patio/issues](https://github.com/cferrerobonet/guardias_patio/issues)
- Email: soporte@guardiaspatio.edu

---

## ✨ Conclusión

Las funcionalidades documentadas en esta guía transforman Guardias de Patio en una herramienta profesional y completa:

✅ **Vista de Calendario**: Visualización clara y filtros potentes  
✅ **Gestión de Ausencias**: Prevención automática y reasignación inteligente  
✅ **Import/Export**: Portabilidad total de datos y respaldos seguros

¡Aprovecha al máximo estas funcionalidades para optimizar la gestión de guardias en tu centro educativo! 🚀

---

**Fin del documento**
