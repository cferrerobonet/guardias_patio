# Características del Sistema - Guardias de Patio v1.2.0

## 📊 Vista General

**Guardias de Patio** es un sistema completo de gestión de guardias escolares que automatiza el cálculo, asignación, visualización y exportación de guardias de patio/recreo para centros educativos.

## ✅ Características Implementadas

### 1. Gestión de Profesores
- ✅ Alta de profesores con datos completos
  - Nombre, apellidos, email corporativo
  - Horas de contrato y porcentaje de jornada
  - Turno (mañana/tarde/mixto)
  - Indicador de tutoría
- ✅ Restricciones personalizadas por profesor
  - Fecha de inicio de guardias
  - Días de semana permitidos
  - Recreos permitidos
- ✅ Visualización en lista
- ✅ Eliminación con confirmación
- ✅ Importación/Exportación de datos

### 2. Gestión de Zonas
- ✅ Alta de zonas de vigilancia
  - Nombre y descripción
- ✅ Visualización en lista
- ✅ Eliminación con confirmación
- ✅ Importación/Exportación de datos

### 3. Configuración del Curso
- ✅ Fechas del curso escolar
  - Fecha de inicio y fin
  - Cálculo automático de días lectivos
- ✅ Recreos configurables
  - Hasta 2 recreos de mañana
  - Hasta 2 recreos de tarde
  - Horarios específicos
- ✅ Festivos automáticos
  - Fines de semana
  - Festivos nacionales
  - Periodos vacacionales (Navidad, Semana Santa)
- ✅ Días no lectivos personalizados
  - Fechas específicas configurables
  - Puentes y festivos locales
- ✅ Ajustes de carga por tutoría
  - Multiplicador para tutores
  - Multiplicador para no tutores
- ✅ Importación/Exportación de configuración

### 4. Cálculo de Guardias
- ✅ Distribución proporcional automática
  - Basada en porcentaje de jornada
  - Ajustada por turno (mañana/tarde/mixto)
  - Ponderada por tutoría
- ✅ Estadísticas del curso
  - Días lectivos totales
  - Recreos por turno
  - Slots totales a cubrir
  - Distribución esperada por profesor
- ✅ Visualización de distribución antes de generar

### 5. Asignación Inteligente de Guardias
- ✅ **Validaciones Críticas**
  - ✅ No simultaneidad de zonas (un profesor solo puede estar en un lugar a la vez)
  - ✅ Compatibilidad de turno
  - ✅ Respeto de cuotas máximas
  - ✅ Fecha de inicio de guardias
  - ✅ Días de semana permitidos
  - ✅ Recreos permitidos

- ✅ **Heurísticas de Optimización**
  - Continuidad de días consecutivos
  - Continuidad de zona
  - Continuidad de recreo
  - Balance de carga continuo
  - Déficit de cuota

- ✅ Generación completa del calendario
- ✅ Resumen por profesor
- ✅ Persistencia en base de datos

### 6. Visualización - Calendario Interactivo
- ✅ Widget de calendario mensual
- ✅ Selección de fechas
- ✅ **Filtros múltiples**
  - Por profesor
  - Por zona
  - Por turno (mañana/tarde/todos)
- ✅ Detalles del día seleccionado
  - Agrupación por turno y recreo
  - Asignaciones profesor → zona
- ✅ Estadísticas en tiempo real
  - Total de guardias filtradas
  - Distribución mañana/tarde
  - Información del profesor seleccionado

### 7. Importación/Exportación de Datos
- ✅ **Exportación completa a JSON**
  - Todos los profesores
  - Todas las zonas
  - Configuración del curso
  - Todas las guardias asignadas
- ✅ **Importación desde JSON**
  - Opción de limpiar datos existentes
  - Preservación de relaciones
  - Validación de integridad
- ✅ Formato legible y editable
- ✅ Interfaz gráfica con diálogos de archivo

## 🔒 Validaciones Implementadas

### Validaciones de Integridad
1. ✅ Profesores: email válido, horas > 0, turno válido
2. ✅ Zonas: nombre no vacío
3. ✅ Configuración: fecha_fin > fecha_inicio
4. ✅ No eliminar entidades en uso

### Validaciones de Asignación
1. ✅ **[CRÍTICO]** No simultaneidad de zonas
2. ✅ Compatibilidad de turno
3. ✅ Respeto de cuotas
4. ✅ Restricciones temporales (fecha de inicio)
5. ✅ Restricciones de días permitidos
6. ✅ Restricciones de recreos permitidos

## 📊 Tecnologías Utilizadas

- **Backend**: Python 3.9+
- **ORM**: SQLAlchemy 2.x
- **Base de datos**: SQLite
- **Migraciones**: Alembic
- **GUI**: PyQt6
- **Testing**: pytest
- **Linting**: ruff
- **Formato de exportación**: JSON

## 📈 Estadísticas del Proyecto

- **Líneas de código**: ~3,500
- **Tests**: 52 (100% pasando)
- **Cobertura**: Alta
- **Archivos de documentación**: 20
- **Páginas de documentación**: ~100

## 🎯 Casos de Uso Principales

### Caso 1: Inicio de Curso
1. Configurar fechas y recreos del curso
2. Dar de alta profesores con sus datos
3. Crear zonas de vigilancia
4. Calcular distribución de guardias
5. Generar calendario completo
6. Exportar para respaldo

### Caso 2: Visualización de Guardias
1. Abrir pestaña de Calendario
2. Seleccionar filtros (profesor, zona, turno)
3. Navegar por fechas
4. Consultar guardias del día
5. Ver estadísticas

### Caso 3: Transferencia entre Equipos
1. Exportar datos a JSON en equipo A
2. Copiar archivo a equipo B
3. Importar datos en equipo B
4. Verificar integridad

### Caso 4: Incorporación Tardía
1. Dar de alta nuevo profesor
2. Configurar fecha de inicio de guardias
3. Regenerar calendario (futuro)
4. Verificar nueva distribución

## 🚀 Roadmap de Características Futuras

### Versión 1.3.0 (Planificada)
- [ ] Regeneración de calendario con opciones
- [ ] Vista detallada por profesor
- [ ] Vista detallada por zona
- [ ] Marcadores visuales en calendario

### Versión 1.4.0 (Planificada)
- [ ] Exportación a Excel
  - Calendario completo
  - Hojas por profesor
  - Hojas por zona
- [ ] Exportación a PDF
  - Calendario general
  - PDFs individuales por profesor

### Versión 1.5.0 (Planificada)
- [ ] Exclusiones temporales
  - Bajas médicas
  - Permisos
  - Ausencias programadas
- [ ] Preferencias por profesor
  - Zonas preferidas
  - Zonas a evitar
  - Franjas horarias preferidas

### Versión 2.0.0 (Visión)
- [ ] Sistema multi-usuario
- [ ] API REST
- [ ] Cliente web
- [ ] Notificaciones por email
- [ ] Integración con calendario Google/Outlook
- [ ] Dashboard de estadísticas avanzadas
- [ ] Histórico de años anteriores
- [ ] Análisis de patrones y sugerencias

## 🏆 Puntos Fuertes

1. **Automatización completa**: De la configuración a la asignación
2. **Validaciones robustas**: Garantiza coherencia física y lógica
3. **Flexibilidad**: Múltiples turnos, restricciones personalizadas
4. **Portabilidad**: Exportación/importación completa
5. **Transparencia**: Estadísticas y visualización clara
6. **Documentación**: Guías completas para usuarios y desarrolladores
7. **Calidad del código**: 100% tests pasando, sin errores de lint
8. **Extensibilidad**: Arquitectura modular preparada para nuevas features

## 📞 Soporte y Contribuciones

- **Issues**: Reporta problemas en GitHub
- **Documentación**: Carpeta `documentacion/`
- **Tests**: Ejecuta `pytest tests/` para validar cambios
- **Linting**: Ejecuta `ruff check src/ tests/` antes de commit

---

**Versión actual**: 1.2.0  
**Última actualización**: 15 de octubre de 2025  
**Estado**: Estable y en producción  
**Licencia**: MIT (o la que corresponda)
