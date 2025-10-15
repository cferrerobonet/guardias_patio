# Importar y Exportar Datos

Esta funcionalidad permite exportar todos los datos de la aplicación a un archivo JSON para:
- **Portabilidad**: Copiar configuración y datos entre diferentes equipos
- **Respaldo**: Hacer copias de seguridad de toda la información
- **Migración**: Transferir datos cuando se actualiza la aplicación

## 📦 ¿Qué datos se exportan?

El archivo JSON exportado incluye:
- ✅ **Profesores**: Todos los datos del profesorado (nombre, apellidos, email, horas, turno, etc.)
- ✅ **Zonas**: Todas las zonas de vigilancia configuradas
- ✅ **Configuración**: Parámetros del curso (fechas, horarios de recreos, festivos, multiplicadores, etc.)
- ✅ **Guardias**: Todas las guardias asignadas (opcional, depende del uso)

## 🚀 Cómo exportar datos

1. Ve a la pestaña **"Importar / Exportar"** en la aplicación
2. Haz clic en el botón **"Exportar a JSON..."**
3. Selecciona dónde guardar el archivo (por defecto: `guardias_patio_export.json`)
4. El archivo se guardará con todos los datos actuales

### Formato del archivo exportado

```json
{
  "version": "1.0",
  "fecha_exportacion": "2024-10-15",
  "profesores": [
    {
      "nombre": "Juan",
      "apellidos": "Pérez",
      "email_corporativo": "juan.perez@colegio.edu",
      "horas_contrato": 25.0,
      "porcentaje_jornada": 100.0,
      "turno": "completo",
      "tutor": true,
      "fecha_inicio_guardias": "2024-09-01",
      "dias_semana_permitidos": "[0,1,2,3,4]",
      "recreos_permitidos": "[1,2]"
    }
  ],
  "zonas": [
    {
      "nombre_zona": "Patio Principal",
      "descripcion": "Zona principal del colegio"
    }
  ],
  "configuracion": {
    "fecha_inicio_curso": "2024-09-01",
    "fecha_fin_curso": "2025-06-30",
    "hora_recreo1_manana": "10:30",
    "hora_recreo2_manana": "12:30",
    "activar_festivos_automaticos": true,
    "ajuste_tutores": 1.5,
    "ajuste_no_tutores": 1.0
  },
  "guardias": []
}
```

## 📥 Cómo importar datos

### ⚠️ IMPORTANTE: Realizar respaldo antes de importar

Antes de importar datos, se recomienda **exportar los datos actuales** como respaldo de seguridad.

### Pasos para importar:

1. Ve a la pestaña **"Importar / Exportar"**
2. **(Recomendado)** Deja marcada la opción **"Eliminar datos existentes antes de importar"**
   - Esto evita conflictos y duplicados
   - Los datos antiguos se eliminarán y se reemplazarán con los del archivo
3. Haz clic en **"Importar desde JSON..."**
4. Selecciona el archivo JSON exportado previamente
5. Confirma la operación (se te pedirá confirmación si vas a eliminar datos)
6. **Reinicia la aplicación** para ver los cambios reflejados en todas las pestañas

### Opciones de importación:

- **Con limpieza (recomendado)**: Elimina todos los datos actuales y los reemplaza con los del archivo
  - ✅ Evita duplicados
  - ✅ Sincronización completa
  - ⚠️ Elimina datos actuales
  
- **Sin limpieza**: Añade los datos del archivo a los existentes
  - ⚠️ Puede crear duplicados
  - ⚠️ Conflictos si ya existen datos similares
  - ℹ️ Útil solo para añadir datos nuevos específicos

## 🔄 Casos de uso

### 1. Transferir configuración a otro equipo

**Equipo origen:**
```
1. Exportar datos → guardias_config.json
2. Copiar archivo a pendrive/nube
```

**Equipo destino:**
```
1. Copiar archivo al equipo
2. Importar datos (con limpieza)
3. Reiniciar aplicación
```

### 2. Hacer respaldo periódico

**Cada mes/trimestre:**
```
1. Exportar datos → respaldo_YYYY_MM_DD.json
2. Guardar en carpeta de respaldos
```

### 3. Restaurar desde respaldo

**Si se pierden datos:**
```
1. Localizar archivo de respaldo
2. Importar datos (con limpieza)
3. Reiniciar aplicación
```

### 4. Configurar nuevo curso escolar

**Al inicio de curso:**
```
1. Exportar curso anterior → curso_2023_2024.json (para histórico)
2. Limpiar guardias asignadas
3. Actualizar configuración de fechas y profesores
4. Exportar nueva configuración → curso_2024_2025.json
```

## 🛠️ Solución de problemas

### El archivo JSON no se puede importar

- **Verifica** que el archivo sea un JSON válido (puedes abrirlo con un editor de texto)
- **Revisa** que tenga la estructura correcta (version, profesores, zonas, etc.)
- **Comprueba** que el archivo no esté corrupto

### Los datos importados no aparecen en la interfaz

- **Reinicia la aplicación** después de importar
- Las vistas pueden estar cacheadas hasta que reinicias

### Error al importar guardias

- Las guardias requieren que existan los **profesores** y **zonas** referenciados
- Si importas solo guardias sin profesores/zonas, se ignorarán automáticamente
- Importa siempre el archivo completo con todos los datos

### Perdí datos al importar

- Si hiciste respaldo antes, puedes restaurarlo importando el archivo de respaldo
- La importación con limpieza **elimina permanentemente** los datos anteriores

## 📋 Recomendaciones

1. **Hacer respaldos regulares**: Exporta datos al menos una vez al mes
2. **Nombrar archivos con fechas**: `guardias_2024_10_15.json` facilita identificar versiones
3. **Guardar respaldos en múltiples ubicaciones**: Local + nube (Google Drive, OneDrive, etc.)
4. **Exportar antes de cambios importantes**: Antes de modificar configuración masivamente
5. **Verificar después de importar**: Revisar que los datos se importaron correctamente

## 🔒 Seguridad y privacidad

- Los archivos JSON contienen **datos personales** (nombres, emails de profesores)
- **No compartir** archivos exportados públicamente
- **Proteger** archivos de respaldo con contraseña si contienen información sensible
- Al transferir entre equipos, usar medios seguros (no email sin cifrar)

## 💡 Consejos avanzados

### Editar manualmente el archivo JSON

Puedes editar el archivo JSON con un editor de texto para:
- Corregir errores masivos
- Actualizar múltiples profesores a la vez
- Modificar configuración antes de importar

**Ejemplo**: Cambiar el turno de todos los profesores de "mañana" a "tarde"
```bash
# Abrir con editor de texto y buscar/reemplazar:
"turno": "mañana"  →  "turno": "tarde"
```

### Combinar datos de múltiples equipos

1. Exportar datos del Equipo A → `equipo_a.json`
2. Exportar datos del Equipo B → `equipo_b.json`
3. Abrir ambos archivos con editor de texto
4. Copiar profesores/zonas de un archivo al otro
5. Importar archivo combinado

⚠️ **Cuidado con duplicados** al combinar manualmente
