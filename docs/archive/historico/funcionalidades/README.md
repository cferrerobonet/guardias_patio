# Funcionalidades del Sistema

Documentación completa de todos los módulos y características del sistema de gestión de guardias.

## 📚 Módulos Principales

### [👨‍🏫 Profesores](profesores/)
Gestión completa del profesorado:
- Alta, baja y modificación de profesores
- Configuración de horarios y disponibilidad
- Restricciones por días y recreos
- Turnos (mañana, tarde, completo, mixto)
- Condiciones especiales (tutores, reducciones, etc.)

**Estado**: ✅ Implementado  
**Versión**: v2.6+

---

### [🔄 Guardias](guardias/)
Sistema de asignación y gestión de guardias:
- Algoritmo inteligente de asignación
- Zona preferida por profesor (v2.6)
- Distribución equitativa de carga
- Validaciones automáticas
- Asignación manual y automática

**Features Destacadas**:
- **[Zona Preferida](../versiones/v2.6/zona-preferida.md)**: Mantiene al profesor en su zona asignada
- **Scoring 5-tuplas**: Priorización inteligente de candidatos
- **Balance automático**: Distribución equitativa según horas contrato

**Estado**: ✅ Implementado  
**Versión**: v2.6+

---

### [🏥 Ausencias](ausencias/)
Control de ausencias y sustituciones:
- Registro de bajas, permisos, licencias
- Gestión de sustituciones
- Calendario de ausencias
- Impacto en asignación de guardias
- Histórico completo

**Documentación**:
- [Gestión de Ausencias](ausencias/gestion.md)

**Estado**: ✅ Implementado  
**Versión**: v2.5+

---

### [📅 Calendario](calendario/)
Visualización y gestión del calendario escolar:
- Vista mensual de guardias
- Navegación rápida entre meses
- Filtros por profesor/zona
- Resumen de estadísticas
- Exportación de reportes

**Documentación**:
- [Vista Mensual](calendario/vista-mensual.md)

**Estado**: ✅ Implementado  
**Versión**: v2.5+

---

### [📤 Importar/Exportar](importar-exportar/)
Sistema de portabilidad y backup de datos:
- Exportación completa a JSON
- Importación selectiva o completa
- Backup y restauración
- Migración entre equipos
- Edición manual de datos

**Documentación**:
- [Guía Completa](importar-exportar/README.md)

**Casos de Uso**:
- Respaldo periódico de datos
- Transferir configuración entre equipos
- Preparar nuevo curso escolar
- Correcciones masivas

**Estado**: ✅ Implementado  
**Versión**: v2.4+

---

## 🎯 Funcionalidades Transversales

### Validaciones Automáticas
Todas las operaciones están protegidas por validaciones:
- Máximo 1 guardia por día por profesor
- No simultaneidad horaria
- Respeto de días/recreos permitidos
- Exclusión de festivos y no lectivos

Ver [Validaciones](../validaciones/README.md) para más detalles.

### Estadísticas en Tiempo Real
El sistema calcula constantemente:
- Guardias asignadas vs esperadas por profesor
- Distribución por zonas
- Balance de carga
- Déficit/superávit de guardias

### Configuración Centralizada
Todos los parámetros configurables desde una única vista:
- Fechas de curso
- Horarios de recreos
- Festivos automáticos
- Multiplicadores (tutores/no tutores)
- Días no lectivos personalizados

## 🔍 Búsqueda Rápida por Necesidad

| ¿Qué necesitas hacer? | Módulo | Documentación |
|-----------------------|--------|---------------|
| Añadir un nuevo profesor | Profesores | [Gestión Profesores](profesores/) |
| Asignar guardias automáticamente | Guardias | [Zona Preferida](../versiones/v2.6/zona-preferida.md) |
| Registrar una baja médica | Ausencias | [Gestión Ausencias](ausencias/gestion.md) |
| Ver guardias del mes | Calendario | [Vista Mensual](calendario/vista-mensual.md) |
| Hacer backup de datos | Importar/Exportar | [Guía Completa](importar-exportar/README.md) |
| Cambiar horarios de recreos | Configuración | [Características](../tecnico/caracteristicas-sistema.md) |
| Ver estadísticas | Panel Estadísticas | [Guías](../guias/ejemplos-uso.md) |

## 🆕 Últimas Actualizaciones

### v2.6.1 - Diciembre 2024
- ✨ **Zona Preferida**: Los profesores mantienen su zona asignada cada día
- 🐛 Fix: Turno mixto ahora muestra campos de horas correctamente
- 📊 Algoritmo mejorado con scoring de 5-tuplas

### v2.5 - Octubre 2024
- 🏥 **Gestión de Ausencias**: Sistema completo de bajas y sustituciones
- 📅 **Vista Calendario**: Visualización mensual mejorada
- 📤 Mejoras en importación/exportación

Ver [Versiones](../versiones/README.md) para historial completo.

## 🚀 Próximamente (v2.7)

- 🎨 Mejoras visuales en UI
- 📊 Dashboard de estadísticas avanzadas
- 🔔 Sistema de notificaciones
- 🌙 Modo oscuro
- ⚡ Optimizaciones de rendimiento

Ver [Roadmap](../roadmap/README.md) para planificación completa.

## 💡 Flujo de Trabajo Típico

### Setup Inicial (Una vez por curso)
1. **Configuración** → Definir fechas de curso, horarios, festivos
2. **Zonas** → Crear zonas de vigilancia
3. **Profesores** → Dar de alta todo el profesorado
4. **Exportar** → Hacer backup de configuración inicial

### Operación Diaria
1. **Ausencias** → Registrar bajas/permisos del día
2. **Calendario** → Revisar guardias del mes
3. **Asignar** → Ajustar guardias según necesidad
4. **Estadísticas** → Verificar balance de carga

### Mantenimiento Periódico
1. **Mensual** → Exportar backup de datos
2. **Trimestral** → Revisar estadísticas acumuladas
3. **Anual** → Preparar nuevo curso escolar

## 🎓 Guías de Aprendizaje

### Para Nuevos Usuarios
1. Lee [Ejemplos de Uso](../guias/ejemplos-uso.md)
2. Practica con datos de prueba
3. Aprende [Atajos de Teclado](../guias/atajos-teclado.md)

### Para Coordinadores Experimentados
1. Domina [Zona Preferida](../versiones/v2.6/zona-preferida.md) para optimizar asignaciones
2. Usa [Importar/Exportar](importar-exportar/README.md) para respaldos automáticos
3. Consulta [Validaciones](../validaciones/README.md) para resolver conflictos

### Para Administradores del Sistema
1. Revisa [Guía de Desarrollo](../desarrollo/guia-desarrollo.md)
2. Entiende [Arquitectura Técnica](../tecnico/README.md)
3. Configura [Estrategia de Git](../desarrollo/limpieza-gitignore.md)

## 📊 Comparación de Módulos

| Módulo | Complejidad | Frecuencia de Uso | Impacto |
|--------|-------------|-------------------|---------|
| Profesores | Media | Alta | Crítico |
| Guardias | Alta | Muy Alta | Crítico |
| Ausencias | Baja | Media | Alto |
| Calendario | Baja | Muy Alta | Medio |
| Importar/Exportar | Media | Baja | Alto |

**Leyenda**:
- **Complejidad**: Curva de aprendizaje
- **Frecuencia**: Cuánto se usa diariamente
- **Impacto**: Importancia para el sistema

## 🔗 Ver También

- [Guías de Usuario](../guias/README.md) - Tutoriales prácticos
- [Validaciones](../validaciones/README.md) - Reglas del sistema
- [Desarrollo](../desarrollo/README.md) - Información técnica
- [Versiones](../versiones/README.md) - Historial de cambios

## 📞 Ayuda y Soporte

- **Documentación**: Busca en los README de cada módulo
- **Ejemplos**: [Ejemplos de Uso](../guias/ejemplos-uso.md)
- **Issues**: [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues)
- **Email**: soporte@guardias-patio.com

---

[← Volver al índice principal](../README.md)
