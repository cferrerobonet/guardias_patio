# Security Policy

**Guardias de Patio** - Política de Seguridad  
**Versión**: 3.0.0  
**Última actualización**: 8 de noviembre de 2025

---

## 📋 Tabla de Contenidos

1. [Versiones Soportadas](#versiones-soportadas)
2. [Reporte de Vulnerabilidades](#reporte-de-vulnerabilidades)
3. [Gestión de Secretos](#gestión-de-secretos)
4. [Validaciones de Seguridad](#validaciones-de-seguridad)
5. [Dependencias y Actualizaciones](#dependencias-y-actualizaciones)
6. [Seguridad en Base de Datos](#seguridad-en-base-de-datos)
7. [Buenas Prácticas](#buenas-prácticas)

---

## 🛡️ Versiones Soportadas

Las siguientes versiones de **Guardias de Patio** reciben actualizaciones de seguridad:

| Versión | Soporte | Fin de Soporte |
|---------|---------|----------------|
| **3.0.x** | ✅ Soporte completo | - |
| 2.9.x | ⚠️ Soporte crítico | 31 de diciembre de 2025 |
| 2.6.x | ❌ No soportado | 31 de octubre de 2025 |
| < 2.6 | ❌ No soportado | - |

**Recomendación**: Actualizar siempre a la última versión v3.0.x para recibir todas las correcciones de seguridad.

---

## 🚨 Reporte de Vulnerabilidades

### Cómo Reportar

Si descubres una vulnerabilidad de seguridad en **Guardias de Patio**, por favor:

#### 1. **NO crear issue público**

Las vulnerabilidades de seguridad deben reportarse de forma privada para evitar explotación.

#### 2. **Enviar reporte privado**

**Email**: cferrerobonet@gmail.com

**Asunto**: `[SECURITY] Vulnerabilidad en Guardias de Patio`

**Incluir en el reporte:**

```markdown
### Descripción de la Vulnerabilidad
[Descripción clara y concisa]

### Versión Afectada
[Versión exacta: v3.0.0, v2.9.1, etc.]

### Pasos para Reproducir
1. [Paso 1]
2. [Paso 2]
3. [Paso 3]

### Impacto
[Descripción del impacto potencial]

### Entorno
- Sistema Operativo: [macOS 14.5, Windows 11, etc.]
- Python: [3.11.8]
- Dependencias relevantes: [PyQt6 6.7.0, SQLAlchemy 2.0.31, etc.]

### Posible Solución (opcional)
[Si tienes sugerencias de cómo solucionarlo]

### Evidencia (opcional)
[Screenshots, logs, código PoC]
```

#### 3. **Tiempo de Respuesta Esperado**

- **Acuse de recibo**: Dentro de 48 horas
- **Evaluación inicial**: Dentro de 5 días hábiles
- **Actualización de estado**: Cada 7 días hasta resolución
- **Fix y release**: Según severidad (ver tabla abajo)

### Severidad y Tiempos

| Severidad | Descripción | Tiempo de Fix | Ejemplo |
|-----------|-------------|---------------|---------|
| 🔴 **Crítica** | Explotación remota, pérdida de datos | 24-48 horas | SQL injection, pérdida de BD |
| 🟠 **Alta** | Acceso no autorizado, corrupción de datos | 7 días | Bypass de validación |
| 🟡 **Media** | Exposición de información sensible | 30 días | Logs con contraseñas |
| 🟢 **Baja** | Impacto menor, requiere acceso local | 90 días | Información de versión |

### Proceso de Divulgación

1. **Confirmación**: Verificamos la vulnerabilidad
2. **Desarrollo del fix**: Creamos parche en rama privada
3. **Testing**: Validamos que el fix funciona sin romper funcionalidad
4. **Release**: Publicamos nueva versión con fix
5. **Divulgación coordinada**: Publicamos advisory 7 días después del release

---

## 🔐 Gestión de Secretos

### Secretos NO Permitidos en el Repositorio

❌ **Nunca commitear:**

- Contraseñas de base de datos
- API keys de servicios externos
- Credenciales SFTP
- Tokens de autenticación
- Certificados privados
- Archivos `.env` con secretos reales

### Archivos Protegidos en .gitignore

```gitignore
# Secretos y configuración sensible
.env
.env.local
*.key
*.pem
*.p12
*.pfx

# Base de datos con datos reales
guardias_patio.db
*.db
*.sqlite
*.sqlite3

# Backups que pueden contener datos sensibles
*.backup
*.bak
backup_*.db

# Logs que pueden contener información sensible
logs/*.log
*.log

# Archivos de configuración con credenciales
config/production.ini
sftp_config.json
```

### Variables de Entorno

Para desarrollo local, usar `.env.example` como plantilla:

```bash
# .env.example (commiteable)
DATABASE_URL=sqlite:///guardias_patio.db
SFTP_HOST=example.com
SFTP_PORT=22
SFTP_USER=usuario
SFTP_PASSWORD=changeme
LOG_LEVEL=INFO
```

**Uso:**

```bash
# Copiar plantilla
cp .env.example .env

# Editar con valores reales (NUNCA commitear .env)
nano .env
```

---

## ✅ Validaciones de Seguridad

### Validación de Entrada

Todas las entradas de usuario pasan por validaciones estrictas usando **Pydantic**:

#### 1. Emails

```python
from pydantic import EmailStr, field_validator

class ProfesorDTO(BaseModel):
    email: EmailStr  # Validación automática de formato
    
    @field_validator('email')
    def validar_dominio(cls, v):
        if not v.endswith('@escuela.com'):
            raise ValueError('Email debe ser del dominio de la escuela')
        return v
```

#### 2. Horas de Contrato

```python
@field_validator('horas_contrato')
def validar_horas(cls, v):
    if not (0 < v <= 40):
        raise ValueError('Horas debe estar entre 0 y 40')
    return v
```

#### 3. Fechas

```python
@field_validator('fecha_fin')
def validar_fechas(cls, v, info):
    if v < info.data['fecha_inicio']:
        raise ValueError('fecha_fin debe ser posterior a fecha_inicio')
    return v
```

### Prevención de SQL Injection

✅ **Usamos ORM (SQLAlchemy)** - Las queries están parametrizadas automáticamente:

```python
# ✅ SEGURO: SQLAlchemy parametriza automáticamente
profesor = session.query(Profesor).filter(
    Profesor.email == email_usuario
).first()

# ❌ NUNCA HACER: SQL directo con string concatenation
# query = f"SELECT * FROM profesores WHERE email = '{email_usuario}'"
```

### Sanitización de Inputs UI

```python
def sanitizar_texto(texto: str) -> str:
    """Elimina caracteres peligrosos de inputs."""
    # Eliminar HTML tags
    texto = re.sub(r'<[^>]+>', '', texto)
    # Eliminar caracteres de control
    texto = ''.join(c for c in texto if c.isprintable() or c.isspace())
    return texto.strip()
```

---

## 📦 Dependencias y Actualizaciones

### Dependencias Principales

Las siguientes dependencias críticas deben mantenerse actualizadas:

| Dependencia | Versión Actual | Función | Riesgo |
|-------------|----------------|---------|--------|
| **PyQt6** | 6.7.0 | Framework UI | Alto |
| **SQLAlchemy** | 2.0.31 | ORM | Crítico |
| **Pydantic** | 2.8.2 | Validación | Alto |
| **python-dotenv** | 1.0.1 | Gestión env | Medio |
| **cryptography** | 42.0.8 | Cifrado | Crítico |

### Auditoría de Dependencias

```bash
# Instalar herramienta de auditoría
pip install pip-audit

# Ejecutar auditoría
pip-audit

# Revisar vulnerabilidades conocidas
pip-audit --desc
```

### Proceso de Actualización

```bash
# 1. Revisar dependencias desactualizadas
pip list --outdated

# 2. Actualizar dependencia específica
pip install --upgrade sqlalchemy

# 3. Ejecutar tests completos
pytest

# 4. Actualizar requirements.txt
pip freeze > requirements.txt

# 5. Commit
git add requirements.txt
git commit -m "chore(deps): actualizar SQLAlchemy a 2.0.32 (fix CVE-2024-XXXX)"
```

### Dependabot/Renovate

**Recomendación**: Configurar Dependabot en GitHub para recibir PRs automáticos de actualizaciones.

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

---

## 🗄️ Seguridad en Base de Datos

### Backups Seguros

```bash
# Crear backup con timestamp
timestamp=$(date +%Y%m%d_%H%M%S)
cp guardias_patio.db "backup_${timestamp}.db"

# Comprimir y cifrar (requiere GPG)
tar czf - "backup_${timestamp}.db" | gpg -c > "backup_${timestamp}.db.tar.gz.gpg"

# Eliminar backup sin cifrar
rm "backup_${timestamp}.db"
```

### Permisos de Archivos

```bash
# BD solo lectura/escritura para usuario actual
chmod 600 guardias_patio.db

# Logs solo lectura/escritura para usuario actual
chmod 600 logs/*.log
```

### Migraciones

```bash
# Siempre hacer backup antes de migración
cp guardias_patio.db guardias_patio.db.backup_pre_migration

# Aplicar migración
alembic upgrade head

# Si algo falla, revertir
cp guardias_patio.db.backup_pre_migration guardias_patio.db
```

---

## 🔒 Buenas Prácticas

### Desarrollo

1. ✅ **Nunca commitear secretos**: Usar `.env` y `.gitignore`
2. ✅ **Validar todas las entradas**: Usar Pydantic o validadores personalizados
3. ✅ **Principio de mínimo privilegio**: Cada componente solo acceso necesario
4. ✅ **Logging seguro**: NO loguear contraseñas, emails completos, datos sensibles
5. ✅ **Type hints**: Ayudan a prevenir errores en tiempo de ejecución

### Testing

```python
# Test de validación
def test_email_invalido_rechazado():
    with pytest.raises(ValidationError):
        ProfesorDTO(email="invalido", ...)

# Test de sanitización
def test_html_tags_eliminados():
    resultado = sanitizar_texto("<script>alert('xss')</script>Texto")
    assert resultado == "Texto"
    assert "<script>" not in resultado
```

### Código Seguro

```python
# ✅ BIEN: Manejo seguro de archivos
def leer_archivo_seguro(ruta: Path) -> str:
    """Lee archivo validando ruta."""
    # Validar que la ruta está dentro del directorio permitido
    ruta = ruta.resolve()
    if not str(ruta).startswith(str(BASE_DIR)):
        raise ValueError("Acceso a ruta no permitida")
    
    with open(ruta, 'r', encoding='utf-8') as f:
        return f.read()

# ❌ MAL: Sin validación de ruta
def leer_archivo_inseguro(ruta: str) -> str:
    with open(ruta, 'r') as f:  # Vulnerable a path traversal
        return f.read()
```

### Logging Seguro

```python
# ✅ BIEN: Logging sin información sensible
logger.info(
    "Usuario actualizado",
    usuario_id=profesor.id,
    email_hash=hashlib.sha256(profesor.email.encode()).hexdigest()[:8]
)

# ❌ MAL: Logging de información sensible
logger.info(f"Usuario {profesor.email} con contraseña {password}")
```

---

## 📚 Referencias

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/faq/security.html)
- [Pydantic Security](https://docs.pydantic.dev/latest/concepts/validators/)

---

## 📞 Contacto de Seguridad

**Email de seguridad**: cferrerobonet@gmail.com  
**PGP Key**: [Disponible bajo pedido]

**Tiempo de respuesta**: 48 horas máximo para acuse de recibo

---

**Última revisión**: 8 de noviembre de 2025  
**Próxima revisión**: 8 de febrero de 2026 (trimestral)
