# 🔧 Configuración Inicial - Validación SMTP/SFTP

## 📋 Descripción General

Sistema de validación de configuración inicial que se ejecuta automáticamente al arrancar la aplicación. Garantiza que los sistemas críticos (SFTP) estén configurados antes de permitir el uso de la aplicación.

---

## 🎯 Objetivo

Asegurar que la aplicación tenga configurados los sistemas esenciales para su funcionamiento:

- **SFTP (Obligatorio)**: Sincronización en la nube y copias de seguridad
- **SMTP (Opcional)**: Envío de emails (calendarios, recuperación de contraseñas)

---

## 🏗️ Arquitectura

### Componentes

#### 1. InitialConfigDialog
**Archivo**: `src/presentation/dialogs/initial_config_dialog.py`

Diálogo modal con dos tabs (SFTP y SMTP) que permite:
- Configurar servidores SFTP y SMTP
- Probar conexiones antes de guardar
- Validar datos ingresados
- Guardar configuración en archivo `.env`

#### 2. Integración en main.py
**Archivo**: `src/main.py`

Verifica al inicio si es necesaria la configuración:
```python
if InitialConfigDialog.is_configuration_needed():
    config_dialog = InitialConfigDialog()
    if config_dialog.exec() != InitialConfigDialog.DialogCode.Accepted:
        # Salir si no se configura SFTP
        sys.exit(0)
```

---

## 📊 Flujo de Ejecución

```
┌─────────────────────────────────────┐
│   Inicio de la Aplicación          │
│   (python src/main.py)              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  ¿Configuración SFTP completa?      │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
      NO              SÍ
       │               │
       ▼               ▼
┌─────────────┐   ┌─────────────────┐
│   Mostrar   │   │   Continuar     │
│   Diálogo   │   │   Login         │
└──────┬──────┘   └─────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│   Tab SFTP (Obligatorio)            │
│   - Host, Port, User, Password      │
│   - Botón: Probar Conexión          │
│   - Botón: Guardar                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   Tab SMTP (Opcional)               │
│   - Server, Port, User, Password    │
│   - Botón: Probar Conexión          │
│   - Botón: Guardar                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│   ¿SFTP configurado y probado?      │
└──────────────┬──────────────────────┘
               │
       ┌───────┴───────┐
       │               │
      NO              SÍ
       │               │
       ▼               ▼
┌─────────────┐   ┌─────────────────┐
│   Botón     │   │   Botón         │
│  Continuar  │   │  Continuar      │
│  BLOQUEADO  │   │  HABILITADO     │
└─────────────┘   └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Continuar     │
                  │   con Login     │
                  └─────────────────┘
```

---

## 🔑 Características Principales

### SFTP (Obligatorio)

**¿Por qué es obligatorio?**
- ✅ Sincronización en la nube entre múltiples dispositivos
- ✅ Copias de seguridad automáticas y fiables
- ✅ Recuperación ante pérdida de datos
- ✅ Trabajo colaborativo multiusuario

**Datos requeridos:**
```env
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=usuario_sftp
SFTP_PASSWORD=contraseña_sftp
SFTP_BASE_DIR=/aplicaciones/guardias_patio
```

**Validación:**
- Conexión SSH al servidor
- Verificación de credenciales
- Creación/verificación del directorio base

### SMTP (Opcional)

**¿Por qué es opcional?**
- ✅ Funcionalidad NO crítica
- ✅ La app funciona sin emails
- ✅ Se puede configurar más tarde
- ✅ Alternativa: copiar manualmente calendarios/códigos

**Datos requeridos:**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email@gmail.com
SMTP_PASSWORD=app_password_xxxx
```

**Validación:**
- Conexión SMTP al servidor
- Autenticación con credenciales
- Test de envío (opcional)

---

## 📝 Estados del Diálogo

### Indicadores Visuales

#### SFTP No Configurado
```
☁️ SFTP: ❌ Configuración incompleta (OBLIGATORIO)
[Fondo rojo] [Borde rojo]
```

#### SFTP Datos Completos
```
☁️ SFTP: ⚠️ Datos completos - Guardar y probar
[Fondo amarillo] [Borde amarillo]
```

#### SFTP Configurado
```
☁️ SFTP: ✅ Configurado correctamente
[Fondo verde] [Borde verde]
```

#### SMTP No Configurado
```
📧 SMTP: ⚠️ No configurado (OPCIONAL)
[Fondo amarillo] [Borde amarillo]
```

#### SMTP Configurado
```
📧 SMTP: ✅ Configurado correctamente
[Fondo verde] [Borde verde]
```

---

## 🎨 Interfaz de Usuario

### Tab SFTP

```
┌────────────────────────────────────────────────────────┐
│  ℹ️ ¿Por qué es obligatorio SFTP?                      │
│                                                        │
│  • Sincronización en la nube                          │
│  • Copias de seguridad automáticas                    │
│  • Recuperación ante fallos                           │
│                                                        │
│  ⚠️ Sin SFTP, no se garantiza seguridad de datos     │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  ☁️ Datos del Servidor SFTP                           │
│                                                        │
│  Servidor:  [sftp.example.com________________]        │
│  Puerto:    [22]                                      │
│  Usuario:   [usuario_sftp____________________]        │
│  Contraseña:[••••••••________________________]        │
│  Dir. Base: [/aplicaciones/guardias_patio____]        │
│                                                        │
│  [🧪 Probar Conexión] [💾 Guardar Configuración]      │
└────────────────────────────────────────────────────────┘
```

### Tab SMTP

```
┌────────────────────────────────────────────────────────┐
│  ℹ️ Configuración SMTP (Opcional)                      │
│                                                        │
│  Permite enviar emails automáticos:                   │
│  • Calendarios por email a profesores                 │
│  • Recuperación de contraseñas                        │
│  • Notificaciones automáticas                         │
│                                                        │
│  ✅ NO es crítico - Puedes configurarlo más tarde    │
│                                                        │
│  💡 Usa cualquier cuenta: Gmail, Outlook, etc.       │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  📧 Datos del Servidor SMTP                           │
│                                                        │
│  Servidor:  [smtp.gmail.com__________________]        │
│  Puerto:    [587]                                     │
│  Email:     [tu_email@gmail.com______________]        │
│  Contraseña:[••••••••________________________]        │
│                                                        │
│  [🧪 Probar Conexión] [💾 Guardar Configuración]      │
└────────────────────────────────────────────────────────┘
```

### Botones Inferiores

```
┌────────────────────────────────────────────────────────┐
│  Estado:                                               │
│  📧 SMTP: ⚠️ No configurado (OPCIONAL)                │
│  ☁️ SFTP: ✅ Configurado correctamente                │
│                                                        │
│            [⏭️ Continuar sin SMTP] [✅ Continuar]      │
│                  (amarillo)           (verde)         │
└────────────────────────────────────────────────────────┘
```

---

## 🧪 Prueba de Conexiones

### Prueba SFTP

1. Validar que todos los campos estén completos
2. Crear transporte SSH con `paramiko.Transport`
3. Autenticar con usuario y contraseña
4. Crear cliente SFTP
5. Verificar directorio base (o crearlo)
6. Cerrar conexión

**Éxito:**
```
✅ Conexión Exitosa
La conexión SFTP a sftp.example.com se estableció correctamente.
Ahora puedes guardar la configuración.
```

**Error:**
```
❌ Error de Conexión
No se pudo conectar al servidor SFTP:
[mensaje de error detallado]
Verifica los datos e inténtalo de nuevo.
```

### Prueba SMTP

1. Validar que todos los campos estén completos
2. Crear conexión SMTP con `smtplib.SMTP`
3. Iniciar TLS
4. Autenticar con usuario y contraseña
5. Cerrar conexión

**Éxito:**
```
✅ Conexión Exitosa
La conexión SMTP a smtp.gmail.com se estableció correctamente.
Ahora puedes guardar la configuración.
```

**Error de Autenticación:**
```
❌ Error de Autenticación
Usuario o contraseña incorrectos.
Para Gmail, necesitas usar una App Password, no tu contraseña normal.
```

**Otro Error:**
```
❌ Error de Conexión
No se pudo conectar al servidor SMTP:
[mensaje de error detallado]
Verifica los datos e inténtalo de nuevo.
```

---

## 💾 Guardado de Configuración

### Método `_update_env_file()`

Actualiza el archivo `.env` en la raíz del proyecto:

```python
def _update_env_file(self, variables: dict) -> None:
    """
    Actualiza el archivo .env con las variables proporcionadas.
    
    Args:
        variables: Diccionario con las variables a actualizar
    """
    # Leer archivo existente o crear uno nuevo
    # Actualizar variables existentes
    # Agregar variables nuevas
    # Guardar archivo
```

**Formato del archivo `.env`:**
```env
# Configuración SFTP
SFTP_HOST=sftp.example.com
SFTP_PORT=22
SFTP_USERNAME=usuario_sftp
SFTP_PASSWORD=contraseña_encriptada
SFTP_BASE_DIR=/aplicaciones/guardias_patio

# Configuración SMTP (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=email@gmail.com
SMTP_PASSWORD=app_password_xxxx
```

---

## 🔒 Seguridad

### Contraseñas Enmascaradas

- Las contraseñas se muestran como `••••••••`
- Se almacenan internamente en `_sftp_password` y `_smtp_password`
- Al guardar, se usa la contraseña almacenada si el campo muestra asteriscos

### Archivo .env

- Nunca se sube a Git (protegido por `.gitignore`)
- Solo accesible localmente
- Se recrea en cada instalación nueva

---

## 🚀 Casos de Uso

### Primera Instalación

1. Usuario instala la aplicación
2. Al iniciar, no existe archivo `.env` o está incompleto
3. Se muestra el diálogo de configuración inicial
4. Usuario configura SFTP (obligatorio)
5. Usuario opcionalmente configura SMTP
6. Se guarda la configuración
7. La aplicación continúa con el login

### Configuración Incompleta

1. Usuario tiene SMTP configurado pero no SFTP
2. Al iniciar, se detecta falta de SFTP
3. Se muestra el diálogo (tab SFTP resaltado)
4. Usuario completa configuración SFTP
5. La aplicación continúa

### Actualización de Configuración

1. Usuario quiere cambiar credenciales SMTP
2. Accede a Configuración → SMTP
3. Desbloquea campos
4. Modifica credenciales
5. Prueba y guarda

---

## 📊 Validaciones

### is_configuration_needed()

Método estático que verifica si es necesario mostrar el diálogo:

```python
@staticmethod
def is_configuration_needed() -> bool:
    """
    Verifica si es necesario mostrar el diálogo de configuración.
    
    Returns:
        True si falta configuración SFTP (obligatoria)
    """
    load_dotenv()
    
    sftp_complete = all([
        os.getenv("SFTP_HOST"),
        os.getenv("SFTP_PORT"),
        os.getenv("SFTP_USERNAME"),
        os.getenv("SFTP_PASSWORD")
    ])
    
    return not sftp_complete
```

**Retorna True si:**
- Falta cualquier variable SFTP en `.env`
- El archivo `.env` no existe

**Retorna False si:**
- Todas las variables SFTP están configuradas

---

## 🎓 Mensajes al Usuario

### SFTP Obligatorio

```
⚠️ SFTP Obligatorio
No puedes continuar sin configurar SFTP.

El servidor SFTP es necesario para garantizar copias de seguridad
y sincronización de datos.
```

### Continuar sin SMTP

```
⏭️ Continuar sin SMTP
¿Estás seguro de que quieres continuar sin configurar SMTP?

Sin SMTP no podrás:
• Enviar calendarios por email a profesores
• Recuperar contraseñas por email
• Recibir notificaciones automáticas

Podrás configurarlo más tarde desde el menú de configuración.
```

### Configuración Incompleta (al salir sin SFTP)

```
Configuración Incompleta
No se puede iniciar la aplicación sin configurar SFTP.

El servidor SFTP es necesario para garantizar copias de seguridad
y sincronización de datos.
```

---

## 🛠️ Instalación y Uso

### Para Desarrolladores

**Crear archivo de prueba:**
```bash
# Script ya incluido
python scripts/test_initial_config.py
```

**Integración en main.py:**
```python
from presentation.dialogs.initial_config_dialog import InitialConfigDialog

# Al inicio de main()
if InitialConfigDialog.is_configuration_needed():
    config_dialog = InitialConfigDialog()
    if config_dialog.exec() != InitialConfigDialog.DialogCode.Accepted:
        sys.exit(0)
```

### Para Usuarios

1. **Primera vez**: El diálogo aparece automáticamente
2. **Reconfigurar**: Ir a Configuración → SMTP/SFTP → Modificar
3. **Probar conexión**: Botón "🧪 Probar Conexión" en cada tab
4. **Guardar**: Botón "💾 Guardar Configuración"

---

## 📚 Referencias

### Archivos Relacionados

- `src/presentation/dialogs/initial_config_dialog.py` - Diálogo principal
- `src/main.py` - Integración en arranque
- `src/presentation/forms/config_widgets/smtp_widget.py` - Widget SMTP
- `src/presentation/forms/config_widgets/sftp_widget.py` - Widget SFTP
- `src/config/sftp_config.py` - Utilidades de configuración SFTP

### Documentación Adicional

- [CONFIGURACION_EMAIL_SMTP.md](./CONFIGURACION_EMAIL_SMTP.md)
- [README.md](../../README.md)

---

## ✅ Checklist de Implementación

- [x] Crear InitialConfigDialog
- [x] Integrar en main.py
- [x] Implementar validación SFTP
- [x] Implementar validación SMTP
- [x] Implementar pruebas de conexión
- [x] Implementar guardado en .env
- [x] Manejo de contraseñas enmascaradas
- [x] Indicadores visuales de estado
- [x] Botón "Continuar sin SMTP"
- [x] Botón "Continuar" (bloqueado sin SFTP)
- [x] Mensajes informativos claros
- [x] Documentación completa
- [ ] Pruebas con usuarios reales

---

## 🐛 Troubleshooting

### El diálogo no aparece

**Causa**: La configuración SFTP ya está completa

**Solución**: 
1. Borrar variables SFTP del archivo `.env`
2. O ejecutar `python scripts/test_initial_config.py` para forzar visualización

### Error al guardar configuración

**Causa**: Permisos insuficientes en archivo `.env`

**Solución**:
```bash
chmod 644 .env
```

### Contraseña no se guarda

**Causa**: Caracteres especiales en contraseña no escapados

**Solución**: 
- No usar comillas en el valor de la contraseña en `.env`
- El sistema maneja automáticamente el formato

### Conexión SFTP falla

**Posibles causas**:
- Firewall bloqueando puerto 22
- Credenciales incorrectas
- Directorio base no existe y no se puede crear

**Solución**:
1. Verificar conectividad: `ssh usuario@host`
2. Verificar credenciales en panel de control del hosting
3. Crear directorio manualmente si es necesario

---

## 📈 Mejoras Futuras

- [ ] Autodetección de servidor SMTP según dominio de email
- [ ] Importar configuración desde archivo JSON
- [ ] Encriptación de contraseñas en .env
- [ ] Validación de formato de email
- [ ] Test de envío de email real (con destinatario)
- [ ] Opción de "Recordarme más tarde" para SMTP
- [ ] Asistente paso a paso (wizard)
- [ ] Integración con gestores de contraseñas

---

**Versión**: 1.0  
**Fecha**: Noviembre 2025  
**Autor**: Sistema de Guardias de Patio
