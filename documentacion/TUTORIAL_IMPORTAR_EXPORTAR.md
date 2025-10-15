# Tutorial Paso a Paso: Importar y Exportar Datos

Este tutorial te guiará a través de ejemplos prácticos de uso de la funcionalidad de importación/exportación.

## 📚 Escenario 1: Configurar Varios Equipos con los Mismos Datos

### Situación
Tienes 3 equipos en el colegio que necesitan tener exactamente los mismos profesores, zonas y configuración.

### Solución

#### Paso 1: Configurar el Equipo Principal
1. Abre la aplicación en el equipo principal
2. Ve a la pestaña **"Profesores"**
3. Añade todos los profesores del centro
4. Ve a la pestaña **"Zonas"**
5. Crea todas las zonas de vigilancia
6. Ve a la pestaña **"Configuración"**
7. Configura fechas del curso, horarios, festivos, etc.

#### Paso 2: Exportar los Datos
1. Ve a la pestaña **"Importar / Exportar"**
2. Haz clic en **"Exportar a JSON..."**
3. Guarda el archivo como: `config_colegio_2024_2025.json`
4. Copia este archivo a un pendrive o súbelo a la nube

#### Paso 3: Configurar los Otros Equipos
Para cada equipo adicional:
1. Copia el archivo `config_colegio_2024_2025.json` al equipo
2. Abre la aplicación
3. Ve a **"Importar / Exportar"**
4. Asegúrate de que **"Eliminar datos existentes antes de importar"** está marcado
5. Haz clic en **"Importar desde JSON..."**
6. Selecciona el archivo `config_colegio_2024_2025.json`
7. Confirma la importación
8. Reinicia la aplicación

✅ **Resultado**: Los 3 equipos tendrán exactamente los mismos datos.

---

## 🔄 Escenario 2: Hacer Respaldo Mensual

### Situación
Quieres tener copias de seguridad de los datos cada mes.

### Solución

#### Proceso Mensual (5 minutos)
1. Abre la aplicación
2. Ve a **"Importar / Exportar"**
3. Haz clic en **"Exportar a JSON..."**
4. Guarda con nombre descriptivo: `respaldo_2024_10_octubre.json`
5. Copia el archivo a:
   - 💾 Disco externo
   - ☁️ Google Drive / OneDrive / Dropbox
   - 📧 Envíate un email (opcional)

#### Organización de Respaldos
```
📁 Respaldos/
  📄 respaldo_2024_09_septiembre.json
  📄 respaldo_2024_10_octubre.json
  📄 respaldo_2024_11_noviembre.json
  📄 respaldo_2024_12_diciembre.json
  ...
```

#### Si Necesitas Restaurar
1. Localiza el archivo de respaldo del mes que necesitas
2. Ve a **"Importar / Exportar"**
3. Marca **"Eliminar datos existentes antes de importar"**
4. Importa el archivo de respaldo
5. Reinicia la aplicación

---

## 🎓 Escenario 3: Preparar Nuevo Curso Escolar

### Situación
El curso 2023-2024 termina y necesitas configurar el 2024-2025 manteniendo la misma estructura.

### Solución

#### Paso 1: Guardar Histórico del Curso Anterior
1. **ANTES DE NADA**: Exportar el curso actual
2. Archivo: `curso_2023_2024_FINAL.json`
3. Guardar en carpeta de históricos

#### Paso 2: Limpiar Guardias Asignadas (Opcional)
Si quieres mantener profesores y zonas pero limpiar las guardias:
1. Exporta los datos actuales
2. Abre el archivo JSON con un editor de texto
3. Busca la sección `"guardias": [...]`
4. Reemplázala por `"guardias": []`
5. Guarda el archivo

#### Paso 3: Actualizar Configuración para Nuevo Curso
1. Abre el archivo JSON con editor de texto
2. Actualiza las fechas:
   ```json
   "fecha_inicio_curso": "2024-09-01",
   "fecha_fin_curso": "2025-06-30"
   ```
3. Actualiza los festivos personalizados si cambian
4. Guarda como: `curso_2024_2025_BASE.json`

#### Paso 4: Importar en la Aplicación
1. Abre la aplicación
2. Ve a **"Importar / Exportar"**
3. Marca **"Eliminar datos existentes antes de importar"**
4. Importa `curso_2024_2025_BASE.json`
5. Reinicia la aplicación

#### Paso 5: Ajustar Profesores si es Necesario
1. Ve a **"Profesores"**
2. Elimina profesores que ya no están
3. Añade nuevos profesores
4. Actualiza horas/turnos si cambiaron

#### Paso 6: Exportar Configuración Final
1. Exporta nuevamente como `curso_2024_2025_OFICIAL.json`
2. Este será tu archivo base para compartir con otros equipos

---

## 🔧 Escenario 4: Corregir Error Masivo

### Situación
Te das cuenta de que todos los profesores tienen el turno incorrecto. En lugar de corregir uno por uno, quieres hacerlo masivamente.

### Solución

#### Paso 1: Hacer Respaldo
**IMPORTANTE**: Antes de editar manualmente
1. Exporta los datos actuales: `antes_de_corregir.json`
2. Guárdalo en lugar seguro

#### Paso 2: Editar el Archivo JSON
1. Exporta datos a `corregir_turnos.json`
2. Abre con editor de texto (Visual Studio Code, Sublime, Notepad++)
3. Usa buscar/reemplazar:
   - Buscar: `"turno": "mañana"`
   - Reemplazar: `"turno": "tarde"`
4. Guarda el archivo

#### Paso 3: Importar Datos Corregidos
1. Ve a **"Importar / Exportar"**
2. Marca **"Eliminar datos existentes antes de importar"**
3. Importa `corregir_turnos.json`
4. Reinicia la aplicación

✅ **Resultado**: Todos los turnos corregidos en 2 minutos.

Si algo sale mal: Importa `antes_de_corregir.json` para volver al estado anterior.

---

## 📊 Escenario 5: Combinar Datos de Dos Equipos

### Situación
El Equipo A tiene profesores de primaria, el Equipo B tiene profesores de secundaria. Necesitas un equipo con todos los profesores.

### Solución

#### Paso 1: Exportar de Ambos Equipos
- Equipo A → `primaria.json`
- Equipo B → `secundaria.json`

#### Paso 2: Combinar Manualmente
1. Abre ambos archivos con editor de texto
2. Copia la sección `"profesores"` de `primaria.json`
3. Pega en `secundaria.json` dentro del array de profesores
4. Asegúrate de que la sintaxis JSON es correcta (comas entre elementos)
5. Guarda como: `todos_profesores.json`

Ejemplo de combinación:
```json
{
  "profesores": [
    // Profesores de primaria (copiados)
    {
      "nombre": "Ana",
      "apellidos": "Primaria",
      ...
    },
    // Profesores de secundaria (ya estaban)
    {
      "nombre": "Carlos",
      "apellidos": "Secundaria",
      ...
    }
  ],
  ...
}
```

#### Paso 3: Importar Datos Combinados
1. Importa `todos_profesores.json` en el equipo que quieres usar
2. Verifica que todos los profesores aparecen

⚠️ **Cuidado**: Si hay profesores con el mismo nombre en ambos archivos, se duplicarán.

---

## 🚨 Escenario 6: Recuperación de Desastre

### Situación
La base de datos se corrompió o borraste datos por error.

### Solución

#### Si Tienes Respaldo Reciente
1. Localiza el archivo de respaldo más reciente
2. Ve a **"Importar / Exportar"**
3. Marca **"Eliminar datos existentes antes de importar"**
4. Importa el archivo de respaldo
5. Reinicia la aplicación

✅ **Datos recuperados**.

#### Si NO Tienes Respaldo
1. Ve a la carpeta de la aplicación
2. Busca archivos `guardias_patio_export.json` (si habías exportado antes)
3. Si encuentras alguno, impórtalo
4. Si no, deberás reintroducir los datos manualmente

**Lección aprendida**: Hacer respaldos periódicos 📅

---

## 💡 Consejos Profesionales

### 1. Automatizar Respaldos
Crea un recordatorio mensual:
- 📅 Día 1 de cada mes
- ⏰ 10:00 AM
- 📋 Tarea: "Exportar respaldo de guardias"

### 2. Nombrar Archivos de Forma Consistente
Usa siempre el formato: `tipo_YYYY_MM_descripcion.json`

Ejemplos:
- ✅ `respaldo_2024_10_octubre.json`
- ✅ `config_2024_2025_inicial.json`
- ✅ `migracion_2024_10_15.json`
- ❌ `datos.json` (muy genérico)
- ❌ `export (1).json` (confuso)

### 3. Mantener Estructura de Carpetas
```
📁 Guardias_Patio_Datos/
  📁 Respaldos/
    📄 respaldo_2024_09.json
    📄 respaldo_2024_10.json
  📁 Historicos/
    📄 curso_2022_2023.json
    📄 curso_2023_2024.json
  📁 Configuraciones/
    📄 config_base_colegio.json
    📄 config_solo_primaria.json
```

### 4. Validar Después de Importar
Siempre verifica:
- ✅ Número de profesores correcto
- ✅ Zonas completas
- ✅ Configuración de fechas correcta
- ✅ Guardias (si las importaste)

### 5. Compartir de Forma Segura
Al enviar archivos con datos personales:
- 🔒 Usa almacenamiento cifrado (OneDrive con contraseña)
- 📧 No envíes por email sin cifrar
- 💾 Usa pendrive con cifrado si es física
- 🗑️ Elimina archivos temporales después de transferir

---

## ❓ Preguntas Frecuentes

### ¿Puedo editar el JSON manualmente?
✅ Sí, es seguro. Solo asegúrate de que la sintaxis JSON sea válida.

### ¿Se pierden los IDs al importar?
⚠️ Sí, se generan nuevos IDs. Pero las relaciones se mantienen por nombres.

### ¿Puedo importar sin limpiar datos?
⚠️ Sí, pero puedes crear duplicados. Solo úsalo si sabes lo que haces.

### ¿Qué pasa con las guardias asignadas?
📊 Se exportan e importan también. Si solo quieres configuración, edita el JSON y vacía el array de guardias.

### ¿Funciona entre versiones diferentes de la aplicación?
⚠️ Depende. Versiones futuras podrían cambiar el formato. Siempre usa la misma versión o consulta notas de migración.

### ¿Cuánto espacio ocupa un archivo de exportación?
📦 Típicamente 10-100 KB. Muy liviano, perfecto para email o nube.

---

**¿Tienes más dudas?** Consulta la [documentación completa](importar_exportar.md) o crea un issue en GitHub.
