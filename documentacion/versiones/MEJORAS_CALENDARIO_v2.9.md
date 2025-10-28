# Mejoras del Calendario - v2.9

## Resumen de Cambios

Se han implementado mejoras significativas en el calendario de visualización de guardias para resolver los problemas de navegación, visualización y tooltips.

## Cambios Implementados

### 1. Barra de Navegación del Calendario ✅

Se ha añadido una **barra de navegación personalizada** con los siguientes elementos:

- **Botón "◀ Mes Anterior"**: 
  - Tamaño: 60x35px
  - Color: Azul Material (#2196F3)
  - Icono: chevron-left
  - Función: Navega al mes anterior

- **Label "Mes Año"**:
  - Muestra el mes y año actual en español
  - Estilo: Fuente 16px, negrita, fondo azul claro (#E3F2FD)
  - Se actualiza automáticamente al cambiar de mes

- **Botón "Mes Siguiente ▶"**:
  - Tamaño: 60x35px
  - Color: Azul Material (#2196F3)
  - Icono: chevron-right
  - Función: Navega al mes siguiente

- **Botón "Hoy"**:
  - Tamaño: 70x35px
  - Color: Verde (#4CAF50)
  - Icono: calendar-month
  - Función: Vuelve rápidamente a la fecha de hoy

**Ubicación**: La barra de navegación se muestra en la parte superior del calendario, con márgenes de 10px y espaciado entre botones.

### 2. Calendario Compacto ✅

Se ha optimizado el calendario para que quepa completamente en la ventana sin scroll:

- **Altura fija**: 280px (reducido de 350px)
- **Barra de navegación nativa oculta**: Se usa `setNavigationBarVisible(False)` para ocultar la barra nativa del QCalendarWidget y usar solo nuestra barra personalizada
- **Sin encabezado vertical**: Eliminadas las columnas de números de semana con `setVerticalHeaderFormat(NoVerticalHeader)`
- **Fuente compacta**: 10px para las celdas del calendario
- **Estilo mejorado**: Líneas de cuadrícula sutiles (#d0d0d0)

### 3. Sistema de Tooltips Mejorado ✅

Se ha implementado un **sistema robusto de tooltips** que muestra información detallada al pasar el mouse sobre las celdas:

#### Implementación Técnica:

1. **EventFilter en el Viewport**: 
   - Se instala un `eventFilter` en el viewport del QTableView interno del calendario
   - Se habilita el tracking del mouse en múltiples niveles (widget, view, viewport)

2. **Cálculo Preciso de Fechas**:
   - Se calcula la fecha exacta basándose en la posición del cursor (fila y columna)
   - Se considera el offset del primer día del mes
   - Se valida que el día calculado esté dentro del rango válido del mes

3. **Información Mostrada en el Tooltip**:
   ```
   📅 [Fecha] - [N] guardia(s)
   
   🕐 RECREO: X guardias
     • [Nombre Profesor 1]
     • [Nombre Profesor 2]
     • [Nombre Profesor 3]
     • ... y X más
   
   🕐 TARDE: Y guardias
     • [Nombre Profesor 1]
     ...
   ```

4. **Características**:
   - Agrupación por turno (recreo, tarde, etc.)
   - Muestra hasta 3 profesores por turno
   - Indica cuántos profesores adicionales hay si hay más de 3
   - Solo se muestra si hay guardias asignadas en esa fecha

### 4. Indicadores Visuales en Celdas

Se mantiene el sistema de **círculos de colores** con contadores:

- 🟢 **Verde**: 8 o más guardias
- 🔵 **Azul**: 4-7 guardias  
- 🟠 **Naranja**: 1-3 guardias

Los círculos se muestran en la esquina inferior derecha de cada celda con el número de guardias.

## Archivos Modificados

- `src/presentation/forms/calendario_guardias_form.py`:
  - Clase `CalendarioGuardiasWidget`: Añadido `eventFilter()` para tooltips
  - Método `_crear_panel_calendario()`: Barra de navegación completa
  - Métodos de navegación: `_mes_anterior()`, `_mes_siguiente()`, `_ir_a_hoy()`
  - Método `_actualizar_label_mes_anio()`: Actualiza el label con nombres de meses en español

## Beneficios para el Usuario

1. ✅ **Navegación intuitiva**: Botones grandes y claros para moverse entre meses
2. ✅ **Sin scroll**: El calendario cabe completamente en la ventana
3. ✅ **Información al instante**: Tooltips informativos al pasar el mouse sobre los días
4. ✅ **Diseño limpio**: Barra de navegación nativa oculta, solo se muestra la personalizada
5. ✅ **Acceso rápido**: Botón "Hoy" para volver rápidamente a la fecha actual
6. ✅ **Visual consistente**: Colores Material Design coherentes con el resto de la aplicación

## Pruebas Recomendadas

1. Abrir el calendario de guardias
2. Verificar que se muestran los botones de navegación (◀, ▶, Hoy)
3. Hacer clic en "◀" y "▶" para cambiar de mes
4. Hacer clic en "Hoy" para volver a la fecha actual
5. Pasar el mouse sobre días con guardias asignadas y verificar que aparece el tooltip
6. Verificar que el calendario no requiere scroll vertical

## Notas Técnicas

- El sistema de tooltips usa `eventFilter()` en lugar de `event()` para capturar eventos específicamente en el viewport del calendario
- Se calcula la fecha precisa basándose en la geometría del QTableView interno
- La barra de navegación personalizada se sincroniza automáticamente con el estado del calendario mediante `currentPageChanged`
