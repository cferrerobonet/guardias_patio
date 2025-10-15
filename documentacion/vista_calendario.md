# Vista de Calendario - Guía de Uso

## 📅 ¿Qué es la Vista de Calendario?

La **Vista de Calendario** es una interfaz interactiva que permite visualizar todas las guardias asignadas de forma gráfica y organizada. Puedes navegar por fechas, aplicar filtros y ver detalles específicos de cada día.

## 🚀 Características Principales

### 1. **Calendario Interactivo**
- Navega por meses y años con los controles del calendario
- Haz clic en cualquier día para ver sus guardias
- Vista mensual clara y fácil de usar

### 2. **Filtros Avanzados**
Filtra las guardias mostradas por:
- **Profesor**: Ver solo las guardias de un profesor específico
- **Zona**: Filtrar por zona de vigilancia
- **Turno**: Mostrar solo guardias de mañana, tarde o todas

### 3. **Detalles del Día**
Al seleccionar un día, verás:
- Número total de guardias ese día
- Guardias organizadas por turno y recreo
- Nombre del profesor y zona asignada para cada guardia

### 4. **Estadísticas en Tiempo Real**
Panel de estadísticas que muestra:
- Total de guardias (según filtros aplicados)
- Guardias de mañana
- Guardias de tarde
- Si filtras por profesor: información adicional del profesor

## 📖 Cómo Usar la Vista de Calendario

### Paso 1: Acceder a la Vista
1. Abre la aplicación
2. Ve a la pestaña **"Calendario"**
3. El calendario se carga automáticamente con la fecha actual

### Paso 2: Navegar por Fechas
- **Cambiar de mes**: Usa las flechas en la cabecera del calendario
- **Cambiar de año**: Haz clic en el mes/año y selecciona
- **Volver a hoy**: Haz doble clic en cualquier día

### Paso 3: Ver Guardias de un Día
1. Haz clic en cualquier día del calendario
2. El panel derecho mostrará las guardias de ese día
3. Las guardias se organizan por turno y recreo

**Ejemplo de visualización:**
```
📅 15/10/2024 - 3 guardia(s)

🕐 MAÑANA - Recreo 1
────────────────────────────────────────
  • Juan Pérez → Patio Principal
  • María López → Biblioteca

🕐 TARDE - Recreo 1
────────────────────────────────────────
  • Carlos Martínez → Cafetería
```

### Paso 4: Aplicar Filtros

#### Filtrar por Profesor
1. En el panel derecho, despliega **"Profesor"**
2. Selecciona un profesor de la lista
3. El calendario y detalles se actualizan automáticamente
4. Solo verás guardias de ese profesor

**Uso típico**: "Quiero ver todas las guardias de Juan Pérez este mes"

#### Filtrar por Zona
1. Despliega **"Zona"**
2. Selecciona una zona (ej: "Patio Principal")
3. Solo verás guardias de esa zona

**Uso típico**: "¿Quién vigila la Biblioteca en octubre?"

#### Filtrar por Turno
1. Despliega **"Turno"**
2. Selecciona: Todos, mañana, o tarde
3. Las guardias se filtran por el turno seleccionado

**Uso típico**: "Solo quiero ver guardias de la tarde"

#### Combinar Filtros
Puedes combinar múltiples filtros:
- Profesor + Turno: "Guardias de mañana de María López"
- Zona + Turno: "Guardias de tarde en el Patio Principal"
- Todos: "Guardias de mañana de Juan en la Biblioteca"

### Paso 5: Limpiar Filtros
1. Haz clic en **"Limpiar filtros"**
2. Todos los filtros vuelven a "Todos"
3. Se muestran todas las guardias nuevamente

## 💡 Casos de Uso Prácticos

### 1. Verificar Asignación de un Profesor
**Situación**: Quieres ver todas las guardias de un profesor en el mes.

**Pasos**:
1. Selecciona el profesor en el filtro
2. Navega por el mes en el calendario
3. Haz clic en diferentes días para ver detalles
4. Las estadísticas te mostrarán el total de guardias

### 2. Comprobar Cobertura de una Zona
**Situación**: Necesitas asegurarte de que la Biblioteca tiene cobertura todos los días.

**Pasos**:
1. Selecciona "Biblioteca" en el filtro de zona
2. Navega por el mes
3. Los días sin guardias no mostrarán información
4. Identifica huecos en la cobertura

### 3. Revisar Guardias de un Día Específico
**Situación**: Quieres ver quién vigila el 15 de octubre.

**Pasos**:
1. Asegúrate de que los filtros estén en "Todos"
2. Navega hasta octubre
3. Haz clic en el día 15
4. Ve todos los detalles organizados por turno y recreo

### 4. Verificar Equidad en Turnos
**Situación**: Quieres confirmar que un profesor tiene guardias balanceadas entre mañana y tarde.

**Pasos**:
1. Selecciona el profesor en el filtro
2. Las estadísticas mostrarán:
   - Total guardias
   - Guardias de mañana
   - Guardias de tarde
3. Compara los números para verificar balance

### 5. Planificar Cambios
**Situación**: Un profesor pide cambiar una guardia específica.

**Pasos**:
1. Selecciona el profesor en el filtro
2. Navega hasta la fecha de la guardia
3. Ve los detalles exactos (turno, recreo, zona)
4. Anota la información para hacer el cambio manual

## 📊 Interpretación de Estadísticas

### Panel de Estadísticas

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

👤 Juan Pérez
   Turno: completo
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

## ⚙️ Configuración y Personalización

### Rango de Fechas Visible
El calendario muestra:
- Todos los días del mes actual
- Puedes navegar a cualquier mes/año
- No hay límite de navegación

### Actualización de Datos
Los datos se actualizan:
- ✅ Automáticamente al cambiar filtros
- ✅ Automáticamente al seleccionar un día
- ❌ NO automáticamente si cambias guardias en otra pestaña
  - Solución: Cambia de pestaña y vuelve para refrescar

## 🔍 Detalles Técnicos

### Formato de Fecha
- Visualización: `DD/MM/YYYY` (ej: 15/10/2024)
- Días de la semana en español
- Resaltado del día actual

### Organización de Guardias
Las guardias se muestran:
1. Agrupadas por turno (mañana primero, tarde después)
2. Dentro de cada turno, agrupadas por recreo
3. Ordenadas numéricamente por recreo (Recreo 1, Recreo 2, etc.)

### Rendimiento
- Carga rápida incluso con cientos de guardias
- Filtros instantáneos
- Sin lag al navegar por fechas

## 🚫 Limitaciones Conocidas

1. **No permite editar guardias**
   - Esta es solo una vista de visualización
   - Para editar, usa la pestaña "Asignación de Guardias"

2. **No resalta días con guardias**
   - Mejora futura: marcar días con guardias con color especial

3. **No muestra resumen mensual**
   - Mejora futura: vista de resumen por mes

4. **No exporta vista filtrada**
   - Mejora futura: exportar calendario filtrado a PDF/Excel

## 💡 Tips y Trucos

### Tip 1: Revisión Rápida de un Profesor
Para revisar rápidamente todas las guardias de un profesor:
1. Filtra por el profesor
2. Mira las estadísticas para el total
3. Navega mes a mes haciendo clic en diferentes días

### Tip 2: Encontrar Huecos de Cobertura
Para encontrar días sin cobertura en una zona:
1. Filtra por la zona
2. Navega por el mes
3. Los días sin guardias dirán "No hay guardias asignadas"

### Tip 3: Verificar Balance de Turnos
Para cada profesor, verifica el balance:
1. Filtra por el profesor
2. Compara los números de "Mañana" vs "Tarde" en estadísticas
3. Deberían ser similares para profesores de turno completo

### Tip 4: Combinación de Filtros para Análisis
Combina filtros para análisis específicos:
- Profesor + Zona: "¿Cuántas veces vigila Juan la Biblioteca?"
- Turno + Zona: "¿Quiénes vigilan el Patio en la tarde?"

## 🆘 Solución de Problemas

### No veo guardias en el calendario
**Posibles causas**:
1. No has generado guardias aún
   - Solución: Ve a "Asignación de Guardias" y genera
2. Los filtros están muy restrictivos
   - Solución: Limpia los filtros
3. Estás mirando un mes sin guardias asignadas
   - Solución: Navega al periodo del curso escolar

### Las estadísticas muestran 0
**Causa**: Los filtros están eliminando todas las guardias
**Solución**: Limpia los filtros uno por uno para ver cuál está causando el problema

### Al seleccionar un día no se actualiza
**Causa**: Posible bug de interfaz
**Solución**: 
1. Cambia de pestaña y vuelve
2. Si persiste, reinicia la aplicación

### Los filtros no se cargan
**Causa**: No hay profesores o zonas en la base de datos
**Solución**: Añade profesores y zonas en sus respectivas pestañas

## 🔮 Mejoras Futuras Planificadas

### Corto Plazo
- [ ] Resaltar días con guardias en el calendario
- [ ] Código de colores por turno o zona
- [ ] Vista de resumen mensual

### Medio Plazo
- [ ] Exportar vista filtrada a PDF/Excel
- [ ] Imprimir calendario del mes
- [ ] Vista de semana (más detallada)
- [ ] Búsqueda por rango de fechas

### Largo Plazo
- [ ] Vista de comparación entre profesores
- [ ] Gráficos de distribución
- [ ] Notificaciones de días sin cobertura
- [ ] Exportar calendario individual por profesor

## 📞 Feedback

¿Tienes sugerencias para mejorar la Vista de Calendario?
- Crea un issue en GitHub
- Describe el caso de uso
- Explica cómo ayudaría la mejora

---

**Versión**: 1.2.0  
**Fecha**: 15 de octubre de 2025  
**Autor**: Carlos Ferrero Bonet
