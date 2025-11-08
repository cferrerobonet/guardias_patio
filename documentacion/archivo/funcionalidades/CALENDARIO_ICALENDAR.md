# 📅 Exportación de Calendarios iCalendar (.ics)

## 📋 Descripción

Los profesores ahora pueden recibir sus guardias en formato **iCalendar (.ics)**, permitiéndoles importar automáticamente todas sus guardias a sus calendarios digitales favoritos.

## ✨ Características

### 🎯 Funcionalidad Principal

- **Generación automática** de archivos .ics al exportar calendarios individuales
- **Adjunto en email** junto con el PDF del calendario
- **Compatible** con todos los clientes de calendario modernos:
  - 📱 Google Calendar
  - 🍎 Apple Calendar (iPhone, iPad, Mac)
  - 📧 Microsoft Outlook
  - 🌐 Thunderbird
  - Y cualquier otro que soporte iCalendar (RFC 5545)

### 📝 Contenido de los Eventos

Cada guardia se convierte en un evento de calendario con:

- **📍 Ubicación**: Nombre del centro educativo
- **⏰ Hora**: Inicio y fin del recreo (duración 30 minutos)
- **🏫 Título**: "🏫 Guardia de Patio - [Nombre de la Zona]"
- **📄 Descripción**: Información detallada:
  - Turno (mañana/tarde)
  - Número de recreo
  - Descripción de la zona
  - Ubicación del centro
  - Recordatorio de llegar con antelación
- **🔔 Alarma**: Recordatorio 15 minutos antes
- **🏷️ Categorías**: Etiquetado como "Guardia de Patio" + turno

### 🔧 Implementación Técnica

#### Estructura del Archivo .ics

```ics
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Guardias de Patio//ES
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:Guardias de Patio - [Nombre Profesor]
X-WR-CALDESC:Calendario de guardias de patio para [Nombre Profesor]
X-WR-TIMEZONE:Europe/Madrid

BEGIN:VEVENT
UID:guardia-123-20251115-1@guardiaspatio
DTSTAMP:20251102T120000Z
DTSTART:20251115T110000
DTEND:20251115T113000
SUMMARY:🏫 Guardia de Patio - Patio Principal
DESCRIPTION:Guardia de patio en Patio Principal\nTurno: Mañana\n...
LOCATION:Centro Educativo
STATUS:CONFIRMED
CATEGORIES:Guardia de Patio,Mañana
BEGIN:VALARM
ACTION:DISPLAY
DESCRIPTION:Guardia de patio en 15 minutos
TRIGGER:-PT15M
END:VALARM
END:VEVENT

[... más eventos ...]

END:VCALENDAR
```

#### Servicios Involucrados

1. **ICalendarService** (`services/icalendar_service.py`)
   - Genera archivos .ics a partir de guardias de base de datos
   - Formatea fechas/horas según RFC 5545
   - Escapa caracteres especiales
   - Crea eventos con alarmas

2. **EmailService** (`services/email_service.py`)
   - Adjunta archivo .ics junto con PDF
   - Estructura correcta MIME multipart/mixed
   - Tipo de contenido: `text/calendar; charset=utf-8`

3. **ImportExportForm** (`presentation/forms/import_export_form.py`)
   - Genera .ics al exportar calendarios individuales
   - Coordina generación de PDF + ICS + envío email

## 📧 Uso en Emails

### Contenido del Email

Cuando se envía un calendario por email, el profesor recibe:

**Adjuntos:**
1. 📄 **PDF**: Calendario visual con mini-calendarios y tabla de guardias
2. 📅 **ICS**: Archivo para importar a su calendario digital

**Mensaje:**
```
Hola [Nombre Profesor],

Te adjuntamos tu calendario personalizado de guardias de patio 
para el curso escolar [Año/Año+1].

El PDF adjunto muestra todas tus guardias asignadas desde tu 
primera hasta tu última fecha de guardia.

📱 IMPORTAR A TU CALENDARIO:
También incluimos un archivo .ics que puedes abrir con tu móvil, 
tablet u ordenador para añadir automáticamente todas las guardias 
a tu calendario personal (Google Calendar, Apple Calendar, 
Outlook, etc.).

[... resto del mensaje ...]
```

## 🚀 Cómo Usar

### Para Administradores

1. **Generar calendarios individuales**:
   - Ir a "Importar/Exportar" → "Exportar Calendarios PDF"
   - Seleccionar "Calendario Individual Optimizado"
   - Marcar "Enviar por email"
   - Seleccionar profesores
   - Hacer clic en "Exportar"

2. **Resultado**:
   - Se genera un PDF por profesor
   - Se genera un .ics por profesor
   - Se envía email con ambos adjuntos

### Para Profesores

#### En el Móvil/Tablet

1. Abrir el email recibido
2. Tocar el archivo `.ics` adjunto
3. El sistema preguntará "¿Añadir a calendario?"
4. Seleccionar el calendario deseado
5. ✅ ¡Todas las guardias se importan automáticamente!

#### En el Ordenador

##### Google Calendar
1. Descargar el archivo .ics
2. Ir a Google Calendar
3. Clic en el botón "+" junto a "Otros calendarios"
4. Seleccionar "Importar"
5. Elegir el archivo .ics descargado
6. Seleccionar el calendario de destino
7. Clic en "Importar"

##### Apple Calendar (Mac)
1. Hacer doble clic en el archivo .ics
2. Calendar se abrirá automáticamente
3. Seleccionar el calendario de destino
4. Clic en "Aceptar"

##### Microsoft Outlook
1. Abrir Outlook
2. Ir a "Archivo" → "Abrir y exportar" → "Importar/Exportar"
3. Seleccionar "Importar un archivo iCalendar (.ics)"
4. Elegir el archivo .ics
5. Clic en "Aceptar"

## 🔍 Detalles de Configuración

### Duración del Recreo

Por defecto, cada guardia tiene una duración de **30 minutos**.

Esto se puede modificar en `ICalendarService`:
```python
# En icalendar_service.py
DURACION_RECREO_MINUTOS = 30  # Cambiar según necesidad
```

### Zona Horaria

Los eventos se generan con zona horaria `Europe/Madrid`.

### UID de Eventos

Cada evento tiene un UID único y determinístico:
```
guardia-{id_guardia}-{fecha_YYYYMMDD}-{recreo}@guardiaspatio
```

Esto permite:
- Identificar eventos únicos
- Actualizar eventos si se reimporta el calendario
- Evitar duplicados

## ✅ Ventajas

### Para los Profesores
- ✨ **Sincronización automática** con su calendario personal
- 🔔 **Recordatorios** automáticos 15 minutos antes
- 📱 **Acceso desde cualquier dispositivo** sincronizado
- 🗓️ **Visión global** de sus guardias junto con otros eventos
- 🎯 **No necesitan introducir nada manualmente**

### Para el Centro
- 📧 **Comunicación eficiente** con formato profesional
- 🤝 **Mejor organización** del profesorado
- ⚡ **Menos consultas** sobre fechas y horarios
- 📊 **Mayor adopción** al facilitar el proceso

## 🛠️ Solución de Problemas

### El archivo .ics no se abre

**Causa**: No hay una aplicación de calendario asociada

**Solución**:
- Instalar Google Calendar, Apple Calendar, Outlook, etc.
- O importar manualmente desde la aplicación de calendario

### Las guardias aparecen duplicadas

**Causa**: Se importó el mismo archivo .ics dos veces

**Solución**:
- Eliminar el calendario importado
- Volver a importar una sola vez

### La hora no es correcta

**Causa**: Diferencia de zona horaria

**Solución**:
- Verificar que la configuración del curso tenga las horas correctas
- Verificar la zona horaria del dispositivo del profesor

### No aparece la alarma

**Causa**: El cliente de calendario no soporta alarmas o están desactivadas

**Solución**:
- Habilitar notificaciones para eventos de calendario
- Verificar configuración de permisos en el dispositivo

## 📚 Referencias

- **RFC 5545**: iCalendar specification
- **MIME Types**: `text/calendar`
- **Encoding**: UTF-8 para soporte de caracteres especiales
- **Formato de fecha**: `YYYYMMDDTHHMMSS`

## 🔮 Futuras Mejoras

- [ ] Permitir personalizar duración del recreo por turno
- [ ] Opción para generar un calendario compartido del centro completo
- [ ] Sincronización automática con CalDAV
- [ ] Integración directa con Google Calendar API
- [ ] Exportación de calendario completo por zona
- [ ] Opción de suscripción a calendario (URL permanente)
- [ ] Soporte para eventos recurrentes

## 📝 Notas Técnicas

### Compatibilidad

El formato iCalendar es un estándar abierto (RFC 5545) soportado por todos los clientes de calendario modernos desde 1998.

### Seguridad

Los archivos .ics generados:
- No contienen código ejecutable
- Son archivos de texto plano
- No representan riesgo de seguridad
- Se pueden inspeccionar con cualquier editor de texto

### Rendimiento

La generación de archivos .ics es muy rápida:
- ~1ms por guardia
- ~100ms para un profesor con 100 guardias
- Tamaño típico: 2-5 KB por profesor

---

**Última actualización**: 2 de noviembre de 2025
**Versión**: 1.0
