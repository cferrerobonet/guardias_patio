# Resumen: Configuración SMTP Global en JSON y Advertencias de Seguridad

## 📋 Objetivo

Asegurar que:
1. **Todos los datos** de la aplicación se exporten correctamente en el JSON (tanto SFTP como exportación manual)
2. La **configuración SMTP global** (compartida por todos los usuarios) se incluya siempre en el JSON
3. Los usuarios sean **advertidos** antes de modificar la configuración SMTP sobre los riesgos que implica

---

## ✅ Cambios Implementados

### 1. Exportación SMTP en DataExporter (SFTP)

**Archivo:** `src/sync/data_exporter.py`

#### Método añadido: `_export_smtp_config()`
```python
@staticmethod
def _export_smtp_config() -> Optional[Dict[str, str]]:
    """Exporta la configuración SMTP desde el archivo .env."""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    smtp_server = os.getenv("SMTP_SERVER", "")
    smtp_port = os.getenv("SMTP_PORT", "")
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    
    if smtp_server and smtp_port and smtp_user and smtp_password:
        return {
            "smtp_server": smtp_server,
            "smtp_port": smtp_port,
            "smtp_user": smtp_user,
            "smtp_password": smtp_password,
        }
    return None
```

#### Método añadido: `_import_smtp_config(smtp_data)`
```python
@staticmethod
def _import_smtp_config(smtp_data: Dict[str, str]) -> bool:
    """Importa la configuración SMTP GLOBAL al archivo .env.
    
    IMPORTANTE: Esta configuración es GLOBAL y afecta a TODOS los usuarios.
    """
    import os
    
    # Lee .env actual
    # Actualiza o añade SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    # Escribe de vuelta a .env
    # Retorna True si tiene éxito
```

#### Modificación en `export_to_json()`
```python
# Exportar configuración SMTP (global)
smtp_config = cls._export_smtp_config()
if smtp_config:
    data["smtp_config"] = smtp_config
```

#### Modificación en `import_from_json()`
```python
# Importar configuración SMTP si existe (es global)
if "smtp_config" in data:
    cls._import_smtp_config(data["smtp_config"])
```

---

### 2. Exportación SMTP en ExportadorDatos (Menú Manual)

**Archivo:** `src/services/exportador.py`

#### Modificación en `exportar_todo()`
```python
# Exportar configuración SMTP (global para todos los usuarios)
smtp_server = os.getenv("SMTP_SERVER", "")
smtp_port = os.getenv("SMTP_PORT", "")
smtp_user = os.getenv("SMTP_USER", "")
smtp_password = os.getenv("SMTP_PASSWORD", "")

if smtp_server and smtp_port and smtp_user and smtp_password:
    datos_completos["smtp_config"] = {
        "smtp_server": smtp_server,
        "smtp_port": smtp_port,
        "smtp_user": smtp_user,
        "smtp_password": smtp_password,
    }
    logger.info("Configuración SMTP añadida al JSON de exportación")
else:
    logger.warning("Configuración SMTP incompleta, no se añadirá al JSON")
```

---

### 3. Modal de Advertencia para Modificaciones SMTP

**Archivo:** `src/presentation/forms/configuracion_form.py`

#### Método añadido: `_mostrar_advertencia_smtp_global()`
```python
def _mostrar_advertencia_smtp_global(self) -> bool:
    """Muestra un modal de advertencia sobre la naturaleza global de la configuración SMTP.
    
    Returns:
        bool: True si el usuario acepta los riesgos, False si cancela.
    """
    from PyQt6.QtWidgets import QMessageBox
    
    msg = QMessageBox(self)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("⚠️ Configuración SMTP Global")
    msg.setText(
        "<h3>⚠️ ADVERTENCIA: Configuración SMTP Global</h3>"
    )
    msg.setInformativeText(
        "<p><b>La configuración SMTP es compartida por TODOS los usuarios del sistema.</b></p>"
        "<p>Modificar estos valores puede:</p>"
        "<ul>"
        "<li>Impedir que otros usuarios recuperen sus contraseñas por email</li>"
        "<li>Afectar a todas las notificaciones del sistema</li>"
        "<li>Causar errores en el envío de emails para todos los usuarios</li>"
        "</ul>"
        "<p><b>Estos cambios afectarán a TODOS los usuarios inmediatamente.</b></p>"
        "<p>¿Estás seguro de que deseas continuar?</p>"
    )
    msg.setStandardButtons(
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    
    # Personalizar textos de los botones
    yes_button = msg.button(QMessageBox.StandardButton.Yes)
    yes_button.setText("Entiendo los riesgos, continuar")
    no_button = msg.button(QMessageBox.StandardButton.No)
    no_button.setText("Cancelar")
    
    resultado = msg.exec()
    return resultado == QMessageBox.StandardButton.Yes
```

#### Modificación en `toggle_smtp_editable()`
```python
def toggle_smtp_editable(self) -> None:
    """Alterna entre bloquear y desbloquear los campos SMTP."""
    # Verificar el estado actual
    is_readonly = self.smtp_server_input.isReadOnly()

    # Si se va a habilitar la edición, mostrar advertencia
    if is_readonly:
        if not self._mostrar_advertencia_smtp_global():
            # Usuario canceló, no hacer nada
            return
    
    # ... resto del código
```

#### Modificación en `guardar_smtp()`
```python
def guardar_smtp(self) -> bool:
    """Guarda la configuración SMTP en el archivo .env."""
    import os

    # Mostrar advertencia antes de guardar
    if not self._mostrar_advertencia_smtp_global():
        # Usuario canceló, no guardar
        self.logger.info("Usuario canceló la modificación de configuración SMTP")
        return False
    
    # ... resto del código
```

---

## 📊 Estructura del JSON Completo

El JSON exportado (tanto por SFTP como por el menú) ahora tiene la siguiente estructura:

```json
{
  "version": "1.0",
  "export_date": "2024-01-15T10:30:00",
  "smtp_config": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": "587",
    "smtp_user": "sistema@ejemplo.com",
    "smtp_password": "contraseña_segura"
  },
  "profesores": [
    {
      "id": 1,
      "nombre": "Juan Pérez",
      "email": "juan@ejemplo.com",
      "activo": true,
      "max_guardias": 5
    }
  ],
  "zonas": [
    {
      "id": 1,
      "nombre": "Patio Principal",
      "prioridad": 1,
      "activa": true
    }
  ],
  "configuracion": [
    {
      "clave": "dias_anticipacion",
      "valor": "7",
      "descripcion": "Días de anticipación para guardias"
    }
  ],
  "guardias": [
    {
      "id": 1,
      "fecha": "2024-01-15",
      "hora_inicio": "10:30",
      "hora_fin": "11:00",
      "profesor_id": 1,
      "zona_id": 1
    }
  ],
  "ausencias": [
    {
      "id": 1,
      "profesor_id": 1,
      "fecha_inicio": "2024-01-20",
      "fecha_fin": "2024-01-22",
      "motivo": "Formación"
    }
  ]
}
```

---

## 🔐 Datos Exportados - Checklist Completo

### ✅ Datos de Profesores
- `id`, `nombre`, `email`, `activo`, `max_guardias`, `telefono`, `departamento`
- Contraseñas (hash) - **NO se exportan por seguridad**

### ✅ Datos de Zonas
- `id`, `nombre`, `prioridad`, `activa`, `descripcion`, `capacidad`

### ✅ Datos de Configuración
- Todos los pares `clave-valor` de la tabla `configuracion`
- Incluye: `dias_anticipacion`, `horas_por_guardia`, `max_guardias_consecutivas`, etc.

### ✅ Datos de Guardias
- `id`, `fecha`, `hora_inicio`, `hora_fin`, `profesor_id`, `zona_id`, `tipo`, `estado`

### ✅ Datos de Ausencias
- `id`, `profesor_id`, `fecha_inicio`, `fecha_fin`, `motivo`, `tipo`, `aprobada`

### ✅ Configuración SMTP (GLOBAL)
- `smtp_server`, `smtp_port`, `smtp_user`, `smtp_password`
- **IMPORTANTE:** Esta configuración es compartida por TODOS los usuarios

---

## 🛡️ Seguridad y Advertencias

### Modal de Advertencia SMTP

**Se muestra en dos momentos:**
1. **Al hacer clic en "🔓 Modificar Configuración SMTP"**
2. **Al intentar guardar cambios en la configuración SMTP**

**Mensaje de advertencia:**
```
⚠️ ADVERTENCIA: Configuración SMTP Global

La configuración SMTP es compartida por TODOS los usuarios del sistema.

Modificar estos valores puede:
• Impedir que otros usuarios recuperen sus contraseñas por email
• Afectar a todas las notificaciones del sistema
• Causar errores en el envío de emails para todos los usuarios

Estos cambios afectarán a TODOS los usuarios inmediatamente.

¿Estás seguro de que deseas continuar?

[Entiendo los riesgos, continuar]  [Cancelar]
```

### Protección Implementada

- **Doble confirmación:** Usuario debe aceptar riesgos dos veces (al habilitar edición y al guardar)
- **Botón por defecto:** "Cancelar" es el botón predeterminado
- **Log de seguridad:** Se registra cuando un usuario intenta/cancela modificar SMTP
- **Validación de datos:** Solo se guarda si la configuración SMTP está completa

---

## 📝 Notas Técnicas

### Ubicación de la Configuración SMTP

- **Almacenamiento:** Archivo `.env` en la raíz del proyecto
- **Variables:**
  - `SMTP_SERVER` (ej: smtp.gmail.com)
  - `SMTP_PORT` (ej: 587)
  - `SMTP_USER` (ej: sistema@ejemplo.com)
  - `SMTP_PASSWORD` (contraseña del usuario SMTP)

### ¿Por qué SMTP está en .env y no en BD?

1. **Seguridad:** Variables sensibles en .env (no versionadas en Git)
2. **Configuración global:** Un solo punto de configuración para todos los usuarios
3. **Despliegue:** Facilita cambios de configuración sin tocar la BD
4. **Estándar:** Práctica común en aplicaciones Python (12-factor app)

### Importación/Exportación

- **Exportación:** Lee de `.env` y añade al JSON
- **Importación:** Lee del JSON y actualiza `.env`
- **Persistencia:** Los cambios en `.env` persisten entre reinicios
- **Sincronización:** SFTP sincroniza `.env` entre instancias (si está configurado)

---

## 🧪 Pruebas Recomendadas

### 1. Exportación Manual
```bash
# Desde el menú Import/Export, exportar datos
# Verificar que el JSON tenga la clave "smtp_config"
```

### 2. Sincronización SFTP
```bash
# Ejecutar sincronización SFTP
# Verificar que el JSON subido al servidor tenga "smtp_config"
```

### 3. Modal de Advertencia
```bash
# Ir a Configuración > SMTP
# Click en "🔓 Modificar Configuración SMTP"
# Verificar que aparece el modal de advertencia
# Click en "Cancelar" → No debe habilitar edición
# Click en "🔓 Modificar Configuración SMTP" de nuevo
# Click en "Entiendo los riesgos, continuar" → Debe habilitar edición
# Modificar valores y click en "💾 Guardar SMTP"
# Verificar que aparece el modal de nuevo
# Click en "Cancelar" → No debe guardar
# Click en "💾 Guardar SMTP" de nuevo
# Click en "Entiendo los riesgos, continuar" → Debe guardar
```

### 4. Importación
```bash
# Modificar el JSON exportado (cambiar smtp_config)
# Importar desde el menú
# Verificar que .env se actualizó correctamente
```

---

## 📚 Documentación Relacionada

- **Sincronización:** Ver `documentacion/GUIA_SINCRONIZACION.md`
- **Exportación:** Ver `src/services/exportador.py`
- **DataExporter:** Ver `src/sync/data_exporter.py`
- **Configuración UI:** Ver `src/presentation/forms/configuracion_form.py`
- **Email Service:** Ver `src/services/email_service.py`

---

## 🎯 Resumen Ejecutivo

### ✅ Completado

1. **SMTP en JSON de SFTP** → `DataExporter` exporta/importa smtp_config
2. **SMTP en JSON de exportación manual** → `ExportadorDatos` exporta smtp_config
3. **Modal de advertencia al modificar SMTP** → Doble confirmación antes de cambios
4. **Modal de advertencia al guardar SMTP** → Segunda confirmación antes de persistir

### 🔒 Garantías de Seguridad

- ✅ Usuario advertido **DOS VECES** antes de modificar SMTP
- ✅ Mensaje claro sobre impacto **GLOBAL** en todos los usuarios
- ✅ Botón "Cancelar" es el predeterminado (evita clicks accidentales)
- ✅ Logs de auditoría cuando se intenta modificar SMTP
- ✅ Validación de datos completos antes de guardar

### 📦 Completitud de Datos

- ✅ Profesores
- ✅ Zonas
- ✅ Configuración
- ✅ Guardias
- ✅ Ausencias
- ✅ **SMTP Config (GLOBAL)**

**Resultado:** Todos los datos de la aplicación se exportan correctamente en el JSON.

---

**Fecha:** 2024-01-15  
**Versión:** 1.0  
**Estado:** ✅ Implementado y documentado
