# 📖 Guía de Usuario - Guardias de Patio

**Versión:** 3.0  
**Fecha:** Noviembre 2025  
**Proyecto:** Sistema de Gestión de Guardias de Patio

---

## 📋 Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Primeros Pasos](#2-primeros-pasos)
3. [Interfaz de Usuario](#3-interfaz-de-usuario)
4. [Gestión de Profesores](#4-gestión-de-profesores)
5. [Gestión de Zonas](#5-gestión-de-zonas)
6. [Gestión de Ausencias](#6-gestión-de-ausencias)
7. [Configuración del Sistema](#7-configuración-del-sistema)
8. [Generación de Guardias](#8-generación-de-guardias)
9. [Vista de Calendario](#9-vista-de-calendario)
10. [Reportes y Exportación](#10-reportes-y-exportación)
11. [Calendarios iCalendar](#11-calendarios-icalendar)
12. [Atajos de Teclado](#12-atajos-de-teclado)
13. [Solución de Problemas](#13-solución-de-problemas)

---

## 1. Introducción

### 🎯 ¿Qué es Guardias de Patio?

**Guardias de Patio** es una aplicación profesional para centros educativos que automatiza la asignación y gestión de guardias de recreo. El sistema distribuye equitativamente las guardias entre el profesorado, respetando restricciones horarias, ausencias y preferencias.

### ✨ Características Principales

- ✅ **Generación automática** de calendarios de guardias
- ✅ **Algoritmos inteligentes** con múltiples opciones (v2.9 y v3.0)
- ✅ **Gestión de ausencias** con reasignación automática
- ✅ **Exportación a PDF** de calendarios personalizados
- ✅ **Calendarios iCalendar** (.ics) para importar a Google Calendar, Outlook, etc.
- ✅ **Interfaz moderna** con diseño Microsoft Fluent
- ✅ **Estadísticas en tiempo real** de distribución de guardias
- ✅ **Importar/Exportar** datos en formato JSON

### 👥 ¿Para Quién es Esta Guía?

Esta guía está dirigida a:
- **Administradores** del centro educativo
- **Jefes de estudios** encargados de las guardias
- **Personal administrativo** que gestiona horarios
- **Coordinadores** de profesorado

---

## 2. Primeros Pasos

### 📥 Instalación

#### Requisitos del Sistema

**Hardware:**
- **RAM**: 4 GB mínimo (8 GB recomendado)
- **Espacio en disco**: 500 MB mínimo
- **Resolución de pantalla**: 1280x720 píxeles mínimo (1920x1080 recomendado)

**Sistemas operativos soportados:**
- ✅ macOS 11 Big Sur o superior
- ✅ Windows 10/11 (64 bits)
- ✅ Linux (Ubuntu 20.04+, Debian 11+)

Para más detalles, consulta **[TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md)** → Sección "Requisitos del Sistema".

#### Primera Instalación

1. **Descargar** la aplicación desde la release más reciente en GitHub
2. **Instalar**:
   - **macOS**: Abrir archivo `.dmg` y arrastrar a Aplicaciones
   - **Windows**: Ejecutar archivo `.exe` e instalar
3. **Ejecutar** la aplicación por primera vez

### 🔧 Configuración Inicial

Al iniciar por primera vez, la aplicación te solicitará configurar los servicios esenciales:

#### 1. Configuración SFTP (Obligatorio)

El servidor SFTP es necesario para:
- ✅ Sincronización en la nube entre dispositivos
- ✅ Copias de seguridad automáticas
- ✅ Recuperación ante pérdida de datos

**Datos requeridos:**
```
Servidor: sftp.tudominio.com
Puerto: 22
Usuario: tu_usuario_sftp
Contraseña: tu_contraseña
Directorio base: /aplicaciones/guardias_patio
```

**Pasos:**
1. La aplicación mostrará el diálogo de configuración inicial
2. Completa los campos del tab **SFTP**
3. Haz clic en **"🧪 Probar Conexión"** para verificar
4. Si la conexión es exitosa, haz clic en **"💾 Guardar Configuración"**

⚠️ **Importante**: Sin SFTP configurado, la aplicación no iniciará.

#### 2. Configuración SMTP (Opcional)

El servidor SMTP permite:
- 📧 Enviar calendarios por email a profesores
- 🔐 Recuperación de contraseñas
- 📬 Notificaciones automáticas

**Datos requeridos:**
```
Servidor: smtp.gmail.com (o tu servidor)
Puerto: 587
Email: tu_email@dominio.com
Contraseña: contraseña_app (para Gmail, usar App Password)
```

**Pasos:**
1. Ve al tab **SMTP** en el diálogo de configuración
2. Completa los campos
3. Haz clic en **"🧪 Probar Conexión"**
4. Si funciona, haz clic en **"💾 Guardar Configuración"**
5. O puedes hacer clic en **"⏭️ Continuar sin SMTP"** y configurarlo más tarde

💡 **Tip**: Puedes configurar SMTP más tarde desde **Configuración → Email**.

#### 3. Configuración del Curso Escolar

Una vez dentro de la aplicación, ve a **Configuración → Configuración del Curso**:

**Datos básicos:**
- **Nombre del centro**: Tu colegio o instituto
- **Fecha inicio curso**: Ejemplo: 01/09/2025
- **Fecha fin curso**: Ejemplo: 30/06/2026

**Horarios de recreos:**
- **Recreo 1 mañana**: Ejemplo: 10:30
- **Recreo 2 mañana**: Ejemplo: 12:30
- **Recreo 1 tarde**: Ejemplo: 16:00
- **Recreo 2 tarde**: Ejemplo: 17:30

**Multiplicadores de equidad:**
- **Ajuste tutores**: 0.90 (tutores reciben 10% menos guardias)
- **Ajuste no tutores**: 1.00 (sin ajuste)

Haz clic en **"💾 Guardar Configuración"** (o presiona **Ctrl+S**).

---

## 3. Interfaz de Usuario

### 🎨 Diseño Microsoft Fluent

La aplicación utiliza un diseño moderno inspirado en **Microsoft Fluent Design System**, similar a aplicaciones como Microsoft 365, Azure Portal y Visual Studio Code.

#### Estructura Principal

```
┌─────────────────────────────────────────┐
│ 🏫 Guardias de Patio         [👤][⚙][❓]│  ← Barra superior
├─────────┬───────────────────────────────┤
│ GESTIÓN │ Gestión › Profesores          │  ← Breadcrumbs
│ 👨‍🏫 Prof.│                               │
│ 🏫 Zonas│   📝 Canvas de trabajo        │
│ ⚙️ Config                               │
│         │   (Contenido dinámico)        │
│ GUARDIAS│                               │
│ 🎯 Asig.│                               │
│ 📆 Cal. │                               │
│ 📊 Est. │                               │
│ 🏥 Aus. │                               │
└─────────┴───────────────────────────────┘
```

**Componentes:**

1. **Barra Superior**:
   - Logo y nombre de la aplicación
   - Breadcrumbs (ruta de navegación)
   - Botones de acciones rápidas (usuario, configuración, ayuda)

2. **Menú Lateral (Sidebar)**:
   - **GESTIÓN**: Profesores, Zonas, Configuración
   - **GUARDIAS**: Asignación, Calendario, Estadísticas, Ausencias
   - Estado activo visual claro
   - Colapsable (solo iconos)

3. **Canvas Central**:
   - Área de trabajo principal
   - Contenido dinámico según la sección seleccionada
   - Scroll independiente

### 🎨 Paleta de Colores

La aplicación usa colores consistentes:

- **Azul Microsoft** (#0078D4): Acciones principales, enlaces
- **Verde** (#107C10): Éxito, confirmaciones positivas
- **Naranja** (#CA5010): Advertencias
- **Rojo** (#D13438): Errores, acciones destructivas
- **Gris claro** (#F3F2F1): Fondo principal
- **Blanco** (#FFFFFF): Tarjetas, paneles

### 📱 Validación de Resolución

La aplicación verifica automáticamente tu resolución de pantalla:

- **✅ Óptimo**: ≥ 1920x1080 (Full HD)
- **⚠️ Mínimo**: 1280x720 (se muestra advertencia)
- **❌ Insuficiente**: < 1280x720 (no permite ejecutar)

Si tu pantalla es muy pequeña, ajusta la resolución antes de usar la aplicación.

---

## 4. Gestión de Profesores

### 👨‍🏫 Vista General

Ve a **Gestión → Profesores** para gestionar el profesorado.

La interfaz tiene dos partes:
- **Panel izquierdo**: Lista de profesores
- **Panel derecho**: Formulario de edición/creación

### ➕ Crear un Nuevo Profesor

1. **Completar el formulario**:

   **Datos básicos:**
   - **Nombre completo**: Apellidos, Nombre (ej: GARCÍA LÓPEZ, JUAN)
   - **Email corporativo**: juan.garcia@colegio.edu

   **Contrato y jornada:**
   - **Horas de contrato**: Ejemplo: 25 horas semanales
   - **% Jornada**: 100% (tiempo completo) o parcial
   - **Turno**: Mañana / Tarde / Mixto

   **Estado:**
   - **¿Es tutor?**: Marca si es tutor de grupo
   - **Fecha inicio guardias**: Desde cuándo puede hacer guardias

   **Restricciones (opcional):**
   - **Días permitidos**: Lunes a viernes por defecto
   - **Recreos permitidos**: 1, 2, 3, 4 por defecto
   - **Notas**: Observaciones adicionales

2. **Guardar**: Haz clic en **"💾 Guardar Profesor"** o presiona **Ctrl+S**

### ✏️ Editar un Profesor

1. **Buscar** el profesor:
   - Usa el campo de búsqueda (presiona **Ctrl+F** para enfocarlo)
   - Escribe nombre, apellido o email
   - Los resultados se filtran automáticamente

2. **Seleccionar**:
   - Haz **doble clic** en el profesor
   - O selecciónalo y presiona **Enter**

3. **Modificar** los campos necesarios

4. **Guardar** los cambios (Ctrl+S)

⚠️ **Nota**: El formulario se limpia automáticamente después de guardar para evitar confusión.

### 🗑️ Eliminar un Profesor

1. Selecciona el profesor en la lista
2. Presiona **Del** o haz clic en **"🗑️ Eliminar"**
3. Confirma la eliminación

⚠️ **Advertencia**: No se puede eliminar un profesor con guardias asignadas. Primero elimina sus guardias o reasígnalas.

### 🔍 Búsqueda y Filtrado

- **Ctrl+F**: Activa el campo de búsqueda
- Escribe cualquier término: nombre, apellido, email
- Filtrado instantáneo en tiempo real
- **✖**: Limpia la búsqueda

### 💡 Consejos para Profesores

**Restricciones de horario:**
- Si un profesor solo trabaja **mañanas**, selecciona turno "mañana"
- Si trabaja **ambos turnos**, selecciona "mixto"
- Los tutores reciben automáticamente **10% menos guardias** (configurable)

**Días permitidos:**
- Si un profesor no trabaja los viernes, desmarca ese día
- El algoritmo respetará esta restricción automáticamente

**Fecha de inicio:**
- Si un profesor se incorpora más tarde, establece su fecha de inicio
- No recibirá guardias antes de esa fecha

---

## 5. Gestión de Zonas

### 🏫 Vista General

Ve a **Gestión → Zonas** para gestionar las zonas de vigilancia.

### ➕ Crear una Nueva Zona

1. Completa el formulario:
   - **Nombre de la zona**: Ej: "Patio Principal", "Biblioteca", "Cafetería"
   - **Descripción** (opcional): Detalles adicionales

2. Haz clic en **"💾 Guardar Zona"** (Ctrl+S)

### ✏️ Editar una Zona

1. Selecciona la zona en la lista (doble clic)
2. Modifica los campos
3. Guarda los cambios

### 🗑️ Eliminar una Zona

1. Selecciona la zona
2. Presiona **Del** o haz clic en **"🗑️ Eliminar"**
3. Confirma

⚠️ **Advertencia**: No se puede eliminar una zona con guardias asignadas.

### 💡 Consejos para Zonas

**Nombres claros:**
- Usa nombres descriptivos: "Patio Principal" en vez de "Patio 1"
- Facilita la identificación en calendarios

**Descripción detallada:**
- Incluye ubicación exacta
- Anota responsabilidades específicas de esa zona
- Ejemplo: "Patio Principal - Vigilar entrada y zona de juegos"

---

## 6. Gestión de Ausencias

### 🏥 Introducción

La gestión de ausencias es una funcionalidad crítica que permite:
- ✅ Registrar ausencias de profesores (bajas, permisos, vacaciones)
- ✅ Prevenir asignaciones automáticas a profesores ausentes
- ✅ Reasignar guardias afectadas automáticamente
- ✅ Mantener historial completo de ausencias

### 📍 Acceso

Ve a **Guardias → Ausencias** (🏥).

### ➕ Registrar una Ausencia

#### Paso 1: Completar el Formulario

1. **Seleccionar profesor**: Despliega la lista y elige
2. **Tipo de ausencia**:
   - 🏥 Baja médica
   - 📋 Permiso
   - 🏖️ Vacaciones
   - 📝 Otros
3. **Fechas**:
   - **Fecha inicio**: Primer día de ausencia
   - **Fecha fin**: Último día de ausencia
4. **Motivo** (opcional): Descripción breve

#### Paso 2: Preview de Guardias Afectadas

Mientras completas los datos, verás automáticamente:

```
⚠️ 3 guardias afectadas:

• 18/10/2025 - mañana - Recreo 1 - Patio Principal
• 21/10/2025 - mañana - Recreo 2 - Porche
• 23/10/2025 - mañana - Recreo 1 - Patio Trasero
```

Si no hay guardias asignadas en ese periodo:
```
✅ No hay guardias asignadas en este periodo
```

#### Paso 3: Guardar

Haz clic en **"💾 Guardar Ausencia"** (Ctrl+S).

La ausencia se registra, pero **NO se reasignan automáticamente las guardias**. Esto te permite revisar antes de reasignar.

### 🔄 Reasignar Guardias Afectadas

#### Opción A: Reasignación Automática

1. Selecciona la ausencia de la tabla
2. Haz clic en **"👁️ Ver Guardias Afectadas"**
3. Se abre el **Diálogo de Reasignación** mostrando todas las guardias afectadas
4. Haz clic en **"🤖 Reasignar Automáticamente"**
5. El sistema:
   - Busca profesores disponibles para cada guardia
   - Ordena por menor carga actual
   - Asigna al mejor candidato automáticamente
6. Verás el resultado:
   ```
   Reasignación completada:
   
   ✅ Reasignadas: 3
   ❌ Fallidas: 0
   ```

**Algoritmo de selección automática:**
- Busca profesores con turno compatible
- Excluye profesores ausentes ese día
- Excluye profesores que ya tienen guardia ese día
- Ordena por menor número de guardias actuales
- Prioriza continuidad de zona (si ya estuvo ahí antes)

#### Opción B: Reasignación Manual

1. En el **Diálogo de Reasignación**, selecciona una guardia específica
2. Haz clic en **"👤 Reasignar Seleccionada"**
3. Se muestra lista de profesores disponibles:
   ```
   GARCÍA LÓPEZ, JUAN (0 guardias hoy)
   MARTÍNEZ RUIZ, ANA (0 guardias hoy)
   FERNÁNDEZ PÉREZ, LUIS (1 guardias hoy)
   ```
4. Selecciona el profesor deseado
5. Confirmación: "Guardia reasignada a [Profesor]"

### ✏️ Editar una Ausencia

1. **Selecciona** la ausencia de la tabla (doble clic)
2. El formulario se llena con los datos actuales
3. **Modifica** los campos necesarios (fechas, tipo, motivo)
4. **Guarda** los cambios (Ctrl+S)

⚠️ **Importante**: Si cambias las fechas, las guardias afectadas cambian. Revisa manualmente el nuevo preview y reasigna si es necesario.

### 🗑️ Eliminar vs Desactivar

#### Eliminar (Borrado Permanente)

**Cuándo usar:**
- Ausencia registrada por error
- Datos completamente incorrectos

**Pasos:**
1. Selecciona la ausencia
2. Haz clic en **"🗑️ Eliminar"**
3. Confirma
4. Se borra de la base de datos (no recuperable)

#### Desactivar (Mantener Historial)

**Cuándo usar:**
- Ausencia cancelada (profesor volvió antes)
- Quieres conservar el registro para auditoría
- Historial para estadísticas

**Pasos:**
1. Selecciona la ausencia
2. Haz clic en **"⏸️ Desactivar"**
3. Se marca como `activa = False`
4. Aparece en **rojo** en la tabla
5. **No se considera** en cálculos futuros
6. Historial preservado

### 📊 Estados Visuales

La tabla de ausencias usa colores para identificar estados:

| Color | Estado | Descripción |
|-------|--------|-------------|
| 🟨 **Amarillo** | En curso | Ausencia activa hoy |
| 🔵 **Cyan** | Futura | Ausencia programada (aún no comenzó) |
| ⬜ **Gris** | Pasada | Ausencia terminada |
| 🔴 **Rojo** | Inactiva | Ausencia desactivada manualmente |

### 💡 Casos de Uso Prácticos

#### Caso 1: Baja Médica de Corta Duración

**Escenario**: Un profesor enferma y estará ausente 3 días.

**Pasos**:
1. Ir a **🏥 Ausencias**
2. Registrar ausencia:
   - Profesor: Juan García
   - Tipo: Baja médica
   - Fecha inicio: Hoy
   - Fecha fin: Hoy + 2 días
   - Motivo: "Gripe"
3. **Guardar**
4. Ver guardias afectadas
5. Reasignar automáticamente
6. ✅ Las 3 guardias se reasignan a otros profesores

#### Caso 2: Vacaciones Planificadas

**Escenario**: Un profesor solicitó vacaciones para la próxima semana (5 días).

**Estrategia de prevención:**
1. **ANTES de generar guardias del mes**:
   - Registrar ausencia con fechas de vacaciones
   - Tipo: Vacaciones
   - Motivo: "Vacaciones personales aprobadas"
2. **Generar guardias normalmente**:
   - El algoritmo automáticamente excluye al profesor ausente
   - No necesita reasignación posterior

✨ **Ventaja**: Prevención > Corrección

#### Caso 3: Ausencia Cancelada

**Escenario**: Se registró una ausencia, pero el profesor volvió antes de lo previsto.

**Solución**:
1. Seleccionar la ausencia
2. Hacer clic en **"⏸️ Desactivar"**
3. La ausencia se conserva en el historial pero no afecta cálculos futuros

---

## 7. Configuración del Sistema

### ⚙️ Configuración del Curso

Ve a **Gestión → Configuración** para acceder a la configuración completa.

### 📋 Secciones de Configuración

#### 1. Información del Centro

- **Nombre del centro**: Nombre completo del colegio
- **Ubicación**: Dirección completa
- **Teléfono / Email**: Datos de contacto

#### 2. Periodo del Curso

- **Fecha inicio curso**: Ejemplo: 01/09/2025
- **Fecha fin curso**: Ejemplo: 30/06/2026
- **Días festivos**: Marcar días no lectivos
- **Activar festivos automáticos**: Incluye festivos nacionales/autonómicos

#### 3. Horarios de Recreos

Configura los horarios de cada recreo:

**Turno de mañana:**
- Recreo 1: Ejemplo: 10:30 - 11:00
- Recreo 2: Ejemplo: 12:30 - 13:00

**Turno de tarde:**
- Recreo 1: Ejemplo: 16:00 - 16:30
- Recreo 2: Ejemplo: 17:30 - 18:00

#### 4. Multiplicadores de Equidad

Ajustan la distribución de guardias según el rol del profesor:

- **Ajuste tutores**: 0.90 (tutores reciben 10% menos guardias)
- **Ajuste no tutores**: 1.00 (sin ajuste)
- **Ajuste jornada parcial**: Automático según % de jornada

**Ejemplo de cálculo:**
```
Profesor tutor, jornada completa:
Cuota base: 20 guardias
Con ajuste: 20 × 0.90 = 18 guardias
```

#### 5. Algoritmo de Asignación

Selecciona el algoritmo a usar:

| Algoritmo | Descripción | Cuándo usar |
|-----------|-------------|-------------|
| **v2.9 - Clásico** | 7 fases (CSP, Simulated Annealing) | Muchas restricciones, flexibilidad |
| **v3.0 - Simple Determinista** | Determinista, garantiza 100% cobertura | Necesitas cobertura completa, resultados predecibles |

💡 **Recomendación**: Empieza con v3.0. Si tienes restricciones muy complejas, prueba v2.9.

#### 6. Configuración de Email (SMTP)

- **Servidor SMTP**: smtp.gmail.com (o tu servidor)
- **Puerto**: 587
- **Usuario**: tu_email@dominio.com
- **Contraseña**: Contraseña o App Password

**Botones:**
- **🧪 Probar Conexión**: Verifica que los datos son correctos
- **💾 Guardar**: Guarda la configuración

#### 7. Configuración de SFTP

- **Servidor**: sftp.tudominio.com
- **Puerto**: 22
- **Usuario**: usuario_sftp
- **Contraseña**: contraseña_sftp
- **Directorio base**: /aplicaciones/guardias_patio

**Botones:**
- **🧪 Probar Conexión**: Verifica conectividad
- **💾 Guardar**: Guarda la configuración

### 💾 Guardar Configuración

Después de hacer cambios, siempre haz clic en **"💾 Guardar Configuración"** (Ctrl+S) al final de cada sección.

---

## 8. Generación de Guardias

### 🎯 Vista General

Ve a **Guardias → Asignación** para generar el calendario de guardias.

### 🚀 Generar Nuevo Calendario

#### Paso 1: Configuración Previa

Antes de generar, asegúrate de tener:
- ✅ Profesores creados y configurados
- ✅ Zonas de vigilancia definidas
- ✅ Configuración del curso completada
- ✅ Ausencias registradas (si las hay)

#### Paso 2: Calcular Distribución

1. Haz clic en **"📊 Calcular Distribución"**
2. El sistema calcula las cuotas para cada profesor:
   ```
   📊 Distribución de Guardias
   
   GARCÍA LÓPEZ, JUAN: 18 guardias
   MARTÍNEZ RUIZ, ANA: 20 guardias
   FERNÁNDEZ PÉREZ, LUIS: 15 guardias (tutor, ajuste 0.90)
   ...
   ```

Revisa que las cuotas sean equitativas antes de continuar.

#### Paso 3: Generar Guardias

1. Haz clic en **"🎯 Generar Guardias"**
2. Si ya existen guardias previas, confirma si quieres eliminarlas
3. El progreso se muestra en tiempo real:

**Con algoritmo v3.0:**
```
PASO 1 (0-10%): Calcular cuotas por profesor
PASO 2 (10-20%): Generar todos los slots disponibles
PASO 3 (20-30%): Calcular prioridades y ordenar profesores
PASO 4 (30-90%): Asignar guardias profesor por profesor
PASO 5 (90-100%): Validación y estadísticas
```

**Con algoritmo v2.9:**
```
FASE 1: Inicialización y validación
FASE 2: Asignación por restricciones
FASE 3: CSP (Constraint Satisfaction Problem)
FASE 4: Simulated Annealing
FASE 5: Optimización local
FASE 6: Relleno de huecos
FASE 7: Validación final
```

#### Paso 4: Revisar Resultados

Al finalizar, verás estadísticas:

```
✅ Generación completada

Total guardias: 350
Cobertura: 100.0%
Slots vacíos: 0
Tiempo: 23.5 segundos

Distribución por profesor:
- GARCÍA LÓPEZ, JUAN: 18/18 ✅
- MARTÍNEZ RUIZ, ANA: 20/20 ✅
- FERNÁNDEZ PÉREZ, LUIS: 15/15 ✅
```

### 📊 Estadísticas

El panel de estadísticas muestra en tiempo real:

- **Total guardias asignadas**
- **% Cobertura** (guardias asignadas / slots totales)
- **Slots vacíos** (si los hay)
- **Distribución por turno** (mañana/tarde)
- **Distribución por recreo**
- **Equidad**: Desviación estándar (cuanto menor, mejor)

### 🔄 Regenerar Guardias

Si no estás satisfecho con el resultado:

1. Haz clic nuevamente en **"🎯 Generar Guardias"**
2. Confirma eliminar guardias existentes
3. El algoritmo generará una nueva distribución

**Algoritmo v2.9**: Puede dar resultados ligeramente diferentes cada vez (usa aleatoriedad controlada)

**Algoritmo v3.0**: Siempre da el mismo resultado (determinista) con los mismos datos

### ⚠️ Problemas Comunes

**No se alcanzan 100% cobertura:**
- Verifica que hay suficientes profesores
- Revisa restricciones muy estrictas (días, turnos)
- Revisa ausencias que reducen disponibilidad
- Considera usar algoritmo v2.9 (más flexible)

**Algunos profesores sin guardias:**
- Verifica su fecha de inicio de guardias
- Revisa restricciones de días/recreos
- Verifica ausencias en todo el periodo

**Distribución muy desigual:**
- Ajusta multiplicadores de equidad
- Revisa % de jornada de cada profesor
- Usa algoritmo v3.0 (más equitativo)

---

## 9. Vista de Calendario

### 📅 Acceso

Ve a **Guardias → Calendario** para visualizar las guardias asignadas.

### 🖼️ Interfaz del Calendario

**Panel central:**
- Calendario mensual interactivo
- Días con guardias marcados visualmente
- Días con ausencias marcados con 🏥
- Navegación entre meses con flechas

**Panel derecho:**
- **Filtros**: Profesor, Zona, Turno
- **Detalles del día**: Guardias del día seleccionado
- **Estadísticas**: Total, mañana, tarde

### 🎯 Uso del Calendario

#### Ver Guardias de un Día

1. Haz clic en cualquier día del calendario
2. El panel derecho muestra las guardias:

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

#### Filtrar por Profesor

1. Despliega **"Profesor"** en filtros
2. Selecciona un profesor
3. El calendario y estadísticas se actualizan
4. Solo verás guardias de ese profesor

**Uso típico**: "Quiero ver todas las guardias de Juan este mes"

#### Filtrar por Zona

1. Despliega **"Zona"**
2. Selecciona una zona (ej: "Patio Principal")
3. Solo verás guardias de esa zona

**Uso típico**: "¿Quién vigila la Biblioteca en octubre?"

#### Filtrar por Turno

1. Despliega **"Turno"**
2. Selecciona: Todos / Mañana / Tarde
3. Las guardias se filtran por turno

#### Combinar Filtros

Puedes usar múltiples filtros simultáneamente:
- Profesor + Turno: "Guardias de mañana de María"
- Zona + Turno: "Guardias de tarde en el Patio"
- Todos: "Guardias de mañana de Juan en la Biblioteca"

#### Limpiar Filtros

Haz clic en **"Limpiar filtros"** para ver todas las guardias.

### 📊 Estadísticas del Calendario

**Sin filtros:**
```
📊 Total guardias: 150
🌅 Mañana: 75
🌆 Tarde: 75
```

**Con filtro de profesor:**
```
📊 Total guardias: 15
🌅 Mañana: 8
🌆 Tarde: 7

👤 GARCÍA LÓPEZ, JUAN
   Turno: mixto
   Tutor: Sí
```

### 🏥 Indicador de Ausencias

Los días con profesores ausentes se marcan claramente:

```
┌─────────┐
│  18 🏥  │  ← Icono de ausencia
│         │
│ 🕐 M R1 │
└─────────┘

🏥 2 ausente(s)  ← Contador en la parte inferior
```

### 💡 Casos de Uso Prácticos

**Verificar asignación de un profesor:**
1. Filtrar por profesor
2. Navegar por meses
3. Ver estadísticas de total de guardias

**Comprobar cobertura de una zona:**
1. Filtrar por zona
2. Verificar que todos los días tienen guardias
3. Identificar posibles huecos

**Revisar día específico:**
1. Sin filtros (mostrar todo)
2. Hacer clic en el día
3. Ver detalles completos organizados por turno

---

## 10. Reportes y Exportación

### 📦 Importar y Exportar Datos

Ve a **Importar / Exportar** para gestionar tus datos.

### 📤 Exportar a JSON

#### ¿Qué se Exporta?

- ✅ **Profesores**: Todos los datos (nombre, email, restricciones, etc.)
- ✅ **Zonas**: Todas las zonas configuradas
- ✅ **Configuración**: Fechas, horarios, multiplicadores
- ✅ **Guardias** (opcional): Todas las guardias asignadas

#### Cómo Exportar

1. Haz clic en **"📤 Exportar a JSON..."**
2. Selecciona ubicación para guardar
3. Nombre sugerido: `guardias_patio_export_YYYY_MM_DD.json`
4. El archivo se guarda con todos los datos actuales

#### Formato del Archivo

```json
{
  "version": "1.0",
  "fecha_exportacion": "2025-11-08",
  "profesores": [...],
  "zonas": [...],
  "configuracion": {...},
  "guardias": [...]
}
```

### 📥 Importar desde JSON

#### ⚠️ Importante: Hacer Respaldo

**ANTES de importar**, exporta tus datos actuales como respaldo de seguridad.

#### Cómo Importar

1. **(Recomendado)** Marca **"Eliminar datos existentes antes de importar"**
   - Evita duplicados
   - Sincronización completa
2. Haz clic en **"📥 Importar desde JSON..."**
3. Selecciona archivo JSON
4. Confirma operación
5. **Reinicia la aplicación** para ver los cambios

#### Opciones de Importación

**Con limpieza (recomendado):**
- ✅ Evita duplicados
- ✅ Sincronización completa
- ⚠️ Elimina datos actuales

**Sin limpieza:**
- ⚠️ Puede crear duplicados
- ⚠️ Conflictos con datos existentes
- ℹ️ Útil solo para añadir datos específicos

### 🔄 Casos de Uso

#### 1. Transferir Configuración Entre Equipos

**Equipo A (origen):**
1. Exportar → `config_colegio.json`
2. Copiar a USB/nube

**Equipo B (destino):**
1. Copiar archivo
2. Importar (con limpieza)
3. Reiniciar aplicación

#### 2. Respaldo Periódico

```
Frecuencia recomendada: Mensual

Nombre: guardias_2025_11_08.json
Ubicación: Carpeta dedicada + copia en nube
```

#### 3. Inicio de Nuevo Curso

1. Exportar curso anterior (histórico)
2. Editar JSON:
   - Actualizar fechas del curso
   - Limpiar guardias: `"guardias": []`
   - Actualizar ausencias si es necesario
3. Importar nueva configuración (con limpieza)

### 📄 Exportar Calendarios PDF

#### Calendario Individual Optimizado

1. Ve a **Importar / Exportar**
2. Selecciona **"Calendario Individual Optimizado"**
3. Opciones:
   - **Seleccionar profesores**: Marca los que quieres exportar
   - **Enviar por email**: Marca si quieres enviarlos automáticamente
4. Haz clic en **"Exportar"**

**Resultado:**
- Un PDF por profesor con su calendario personalizado
- Incluye mini-calendarios visuales
- Tabla detallada de todas sus guardias
- Si marcaste email: se envía automáticamente con archivo .ics adjunto

#### Calendario Completo del Centro

1. Selecciona **"Calendario Completo"**
2. Elige ubicación para guardar
3. Se genera un PDF con:
   - Todas las guardias del centro
   - Organizadas por fecha
   - Tabla completa con profesor, turno, recreo, zona

### 📧 Contenido del Email

Cuando envías calendarios por email, el profesor recibe:

**Asunto:**
```
Tu calendario de guardias de patio 2025/2026
```

**Adjuntos:**
1. 📄 **PDF**: Calendario visual completo
2. 📅 **ICS**: Archivo iCalendar para importar

**Mensaje:**
```
Hola Juan García,

Te adjuntamos tu calendario personalizado de guardias de patio
para el curso escolar 2025/2026.

El PDF adjunto muestra todas tus guardias asignadas.

📱 IMPORTAR A TU CALENDARIO:
También incluimos un archivo .ics que puedes abrir con tu móvil
para añadir automáticamente todas las guardias a tu calendario
personal (Google Calendar, Apple Calendar, Outlook, etc.).

Simplemente toca o haz doble clic en el archivo .ics y se
importarán todos los eventos con recordatorios automáticos.
```

---

## 11. Calendarios iCalendar

### 📅 ¿Qué son los Calendarios iCalendar?

Los archivos **iCalendar (.ics)** permiten a los profesores importar automáticamente sus guardias a sus calendarios digitales favoritos.

### ✨ Características

**Compatible con:**
- 📱 Google Calendar
- 🍎 Apple Calendar (iPhone, iPad, Mac)
- 📧 Microsoft Outlook
- 🌐 Thunderbird
- Y cualquier cliente que soporte RFC 5545

**Cada guardia incluye:**
- **📍 Ubicación**: Nombre del centro
- **⏰ Hora**: Inicio y fin del recreo (30 minutos)
- **🏫 Título**: "🏫 Guardia de Patio - [Zona]"
- **📄 Descripción**: Turno, recreo, zona, ubicación
- **🔔 Alarma**: Recordatorio 15 minutos antes
- **🏷️ Categorías**: "Guardia de Patio" + turno

### 🚀 Cómo Usar (Para Profesores)

#### En el Móvil/Tablet

1. Abrir el email recibido
2. Tocar el archivo `.ics` adjunto
3. El sistema pregunta: "¿Añadir a calendario?"
4. Seleccionar calendario de destino
5. ✅ ¡Todas las guardias se importan!

#### En Ordenador - Google Calendar

1. Descargar el archivo `.ics`
2. Ir a Google Calendar
3. Clic en "+" junto a "Otros calendarios"
4. Seleccionar "Importar"
5. Elegir el archivo `.ics`
6. Seleccionar calendario de destino
7. Clic en "Importar"

#### En Ordenador - Apple Calendar

1. Hacer doble clic en el archivo `.ics`
2. Calendar se abre automáticamente
3. Seleccionar calendario de destino
4. Clic en "Aceptar"

#### En Ordenador - Microsoft Outlook

1. Abrir Outlook
2. "Archivo" → "Abrir y exportar" → "Importar/Exportar"
3. "Importar un archivo iCalendar (.ics)"
4. Elegir el archivo
5. Clic en "Aceptar"

### ✅ Ventajas

**Para los profesores:**
- ✨ Sincronización automática con su calendario personal
- 🔔 Recordatorios 15 minutos antes
- 📱 Acceso desde cualquier dispositivo sincronizado
- 🗓️ Visión global junto con otros eventos personales
- 🎯 No necesitan introducir nada manualmente

**Para el centro:**
- 📧 Comunicación eficiente
- 🤝 Mejor organización
- ⚡ Menos consultas sobre fechas
- 📊 Mayor adopción

### 🛠️ Solución de Problemas

**El archivo .ics no se abre:**
- Instala una aplicación de calendario
- O impórtalo manualmente desde la app

**Guardias duplicadas:**
- Se importó el mismo archivo dos veces
- Elimina el calendario y vuelve a importar

**La hora no es correcta:**
- Verifica zona horaria del dispositivo
- Verifica configuración de horarios en la app

---

## 12. Atajos de Teclado

### ⌨️ Atajos Globales

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| **Ctrl + Tab** | Siguiente sección | Cambia a la sección siguiente |
| **Ctrl + Shift + Tab** | Sección anterior | Cambia a la sección anterior |
| **Ctrl + Q** | Salir | Cierra la aplicación |

### 👨‍🏫 Profesores

| Atajo | Acción | Descripción |
|-------|--------|-------------|
| **Ctrl + F** | Buscar | Enfoca campo de búsqueda |
| **F5** | Refrescar | Recarga lista desde BD |
| **Del** | Eliminar | Elimina profesor seleccionado |
| **Enter** | Editar | Carga profesor en formulario |
| **Ctrl + S** | Guardar | Guarda profesor actual |
| **Esc** | Cancelar | Limpia formulario |

### 🏫 Zonas

| Atajo | Acción |
|-------|--------|
| **Ctrl + S** | Guardar zona |
| **F5** | Refrescar lista |
| **Del** | Eliminar zona |

### 🏥 Ausencias

| Atajo | Acción |
|-------|--------|
| **Ctrl + S** | Guardar ausencia |
| **Ctrl + F** | Buscar profesor |
| **F5** | Refrescar lista |
| **Del** | Eliminar ausencia |
| **Esc** | Cancelar edición |

### 📅 Calendario

| Atajo | Acción |
|-------|--------|
| **← →** | Navegar meses |
| **Ctrl + H** | Ir a hoy |
| **Ctrl + F** | Enfocar filtros |
| **Esc** | Limpiar filtros |

### ⚙️ Configuración

| Atajo | Acción |
|-------|--------|
| **Ctrl + S** | Guardar configuración |

### 💡 Tips de Productividad

**Flujo rápido de edición:**
```
Ctrl+Tab → Ir a Profesores
Ctrl+F → Buscar
Escribe nombre → Filtrar
Enter → Seleccionar
Modifica campos
Ctrl+S → Guardar
```

**Navegación sin ratón:**
```
Ctrl+Tab → Cambiar sección
Tab → Navegar entre campos
Espacio → Activar checkbox
Enter → Confirmar
Esc → Cancelar
```

---

## 13. Solución de Problemas

### 🚨 Problemas Comunes

#### La aplicación no inicia

**Posibles causas:**
1. **SFTP no configurado**
   - La app requiere SFTP obligatoriamente
   - Configura servidor SFTP en el diálogo inicial

2. **Resolución de pantalla insuficiente**
   - Mínimo: 1280x720 píxeles
   - Ajusta resolución de tu monitor

3. **Faltan dependencias**
   - Reinstala la aplicación
   - Verifica requisitos del sistema

#### No se generan guardias

**Posibles causas:**
1. **Faltan datos básicos**
   - Verifica que hay profesores activos
   - Verifica que hay zonas configuradas
   - Verifica configuración del curso

2. **Restricciones imposibles**
   - Revisa restricciones de días/turnos
   - Verifica ausencias que reducen disponibilidad
   - Prueba con algoritmo v2.9 (más flexible)

3. **Fechas incorrectas**
   - Verifica fecha inicio/fin del curso
   - Verifica fechas de inicio de profesores

#### Cobertura menor al 100%

**Causas comunes:**
1. **Pocos profesores**
   - Añade más profesores
   - Revisa % de jornada de cada uno

2. **Muchas ausencias**
   - Revisa ausencias registradas
   - Reduce restricciones innecesarias

3. **Restricciones muy estrictas**
   - Revisa días permitidos de cada profesor
   - Revisa recreos permitidos
   - Prueba con algoritmo v2.9

#### No se envían emails

**Posibles causas:**
1. **SMTP no configurado**
   - Ve a Configuración → Email
   - Completa datos y prueba conexión

2. **Credenciales incorrectas**
   - Para Gmail: usa App Password, no contraseña normal
   - Verifica usuario y contraseña

3. **Firewall/Antivirus**
   - Permite conexión saliente en puerto 587
   - Añade excepción para la aplicación

#### Datos no aparecen tras importar

**Solución:**
- **Reinicia la aplicación**
- Las vistas pueden estar cacheadas
- El reinicio fuerza recarga completa

#### Error al importar JSON

**Causas:**
1. **Formato JSON inválido**
   - Valida sintaxis en jsonlint.com
   - Abre con editor de texto y corrige errores

2. **Archivo corrupto**
   - Usa un respaldo anterior
   - Exporta de nuevo desde origen

### 🔧 Logs y Diagnóstico

#### Ubicación de Logs

Los logs se guardan en:
```
logs/guardias_patio.log
```

#### Revisar Errores

1. Abre el archivo de logs con un editor de texto
2. Busca líneas con `[ERROR]` o `[WARNING]`
3. Identifica el timestamp del error
4. Lee el contexto alrededor del error

#### Información Útil para Soporte

Si necesitas reportar un problema, incluye:
- Versión de la aplicación
- Sistema operativo y versión
- Mensaje de error exacto
- Extracto relevante del log
- Pasos para reproducir el problema

### 📞 Soporte

**Para reportar bugs o solicitar ayuda:**
- GitHub Issues: [https://github.com/cferrerobonet/guardias_patio/issues](https://github.com/cferrerobonet/guardias_patio/issues)
- Email: soporte@guardiaspatio.edu

**Documentación técnica:**
- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Guía técnica completa
- [DEPLOYMENT.md](DEPLOYMENT.md) - Instalación y despliegue
- [README.md](../README.md) - Documentación principal

---

## 🎓 Conclusión

Esta guía cubre todas las funcionalidades principales de **Guardias de Patio v3.0**. El sistema está diseñado para simplificar la gestión de guardias, automatizar tareas repetitivas y proporcionar una experiencia moderna y profesional.

### 🚀 Próximos Pasos

1. **Configura** tu centro: profesores, zonas, horarios
2. **Genera** tu primer calendario de guardias
3. **Exporta** calendarios PDF e iCalendar
4. **Gestiona** ausencias y reasignaciones
5. **Optimiza** con estadísticas y reportes

### ✨ Recuerda

- **Haz respaldos periódicos** (exportar a JSON mensualmente)
- **Registra ausencias** antes de generar guardias (prevención)
- **Usa algoritmo v3.0** para máxima cobertura
- **Aprovecha atajos de teclado** para mayor productividad
- **Envía calendarios .ics** para mejor adopción

¡Aprovecha al máximo Guardias de Patio para optimizar la gestión de tu centro educativo! 🎓

---

**Versión de la guía**: 3.0  
**Fecha**: 8 de noviembre de 2025  
**Mantenido por**: Equipo Guardias de Patio

**Referencias Relacionadas:**
- [TECHNICAL_GUIDE.md](TECHNICAL_GUIDE.md) - Documentación técnica
- [DEPLOYMENT.md](DEPLOYMENT.md) - Guías de instalación
- [README.md](../README.md) - Visión general del proyecto
