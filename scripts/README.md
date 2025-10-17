# 📁 Scripts de Utilidad

Este directorio contiene scripts auxiliares para mantenimiento y gestión de datos.

---

## 📊 `importar_profesores_desde_excel.py`

### Descripción
Script para importar profesores masivamente desde archivos Excel ubicados en `documentacion/datos ejemplo/`.

### Funcionalidad
- Lee archivos `.xlsx` con datos de profesores
- Extrae: Nombre completo y Correo electrónico
- **Valida duplicados**: Si el profesor ya existe (por nombre), lo omite
- **Crea nuevos profesores** con valores por defecto:
  - `horas_contrato`: 30h
  - `porcentaje_jornada`: 100%
  - `turno`: completo
  - `email_corporativo`: del archivo Excel

### Uso

```bash
python scripts/importar_profesores_desde_excel.py
```

### Formato de archivos Excel esperado

Los archivos deben tener:
- **9 filas de encabezado** (se saltan automáticamente)
- **Fila 10**: Columnas del tipo: `Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico`
- **Fila 11+**: Datos de profesores

**Ejemplo de estructura:**
```
[Filas 1-9: Encabezados institucionales]
Fila 10: Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico
Fila 11: GARCÍA LÓPEZ, JUAN | 96123456 | 612345678 | juan.garcia@epla.es
Fila 12: MARTÍNEZ RUIZ, ANA | 96234567 | 623456789 | ana.martinez@epla.es
...
```

### Salida

El script muestra estadísticas detalladas:

```
================================================================================
🎓 IMPORTACIÓN DE PROFESORES DESDE EXCEL
================================================================================

📂 Procesando: bach.xlsx
--------------------------------------------------------------------------------
   Profesores leídos: 30
   ✅ Importados: 13
   ⏭️  Ya existentes: 17
   ❌ Errores: 0

📂 Procesando: fp_mañana.xlsx
...

================================================================================
📊 RESUMEN FINAL
================================================================================
Archivos procesados: 4
Total profesores leídos: 127
✅ Total importados: 41
⏭️  Total ya existentes: 86
❌ Total errores: 0
================================================================================
```

### Logs

El script registra operaciones en el log de la aplicación:
- ✅ Profesores importados exitosamente
- ⏭️ Profesores que ya existían (omitidos)
- ❌ Errores encontrados (con detalles)

### Notas importantes

1. **Seguridad**: El script hace commit automático solo después de procesar cada archivo completo
2. **Validación**: Omite filas vacías o con nombres inválidos
3. **Emails opcionales**: Si un profesor no tiene email, se guarda con `None`
4. **Idempotente**: Puedes ejecutar el script múltiples veces sin duplicar datos
5. **Normalización**: Los nombres se validan y comparan ignorando mayúsculas/minúsculas

### Dependencias

```bash
pip install pandas openpyxl
```

---

## 🔮 Scripts Futuros

Aquí se añadirán más scripts de utilidad:
- `migrar_guardias.py` - Migración de datos históricos
- `backup_database.py` - Copias de seguridad automáticas
- `generar_reportes.py` - Reportes estadísticos
- etc.
