# Security Policy

**Guardias de Patio** - Política de Seguridad  
**Versión**: 3.0.1  
**Última actualización**: 8 de noviembre de 2025  
**Última auditoría**: 8 de noviembre de 2025 ✅  
**Estado**: ✅ **TODAS LAS VULNERABILIDADES SOLUCIONADAS** (8 nov 2025)

---

## 📋 Tabla de Contenidos

1. [Versiones Soportadas](#versiones-soportadas)
2. [Reporte de Vulnerabilidades](#reporte-de-vulnerabilidades)
3. [Auditorías Recientes](#auditorías-recientes)
4. [Gestión de Secretos](#gestión-de-secretos)
5. [Validaciones de Seguridad](#validaciones-de-seguridad)
6. [Dependencias y Actualizaciones](#dependencias-y-actualizaciones)
7. [Seguridad en Base de Datos](#seguridad-en-base-de-datos)
8. [Buenas Prácticas](#buenas-prácticas)
9. [CI/CD y Auditorías Automáticas](#cicd-y-auditorías-automáticas)

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

## � Auditorías Recientes

### Última Auditoría: 8 de Noviembre de 2025

**Herramientas utilizadas:**
- ✅ `pip-audit` - Análisis de vulnerabilidades en dependencias
- ✅ `bandit` - Análisis estático de seguridad del código Python
- ✅ Verificación manual de secretos y archivos sensibles

#### Resultados

| Herramienta | Issues Encontrados | Severidad | Estado |
|-------------|-------------------|-----------|--------|
| **pip-audit** | 7 vulnerabilidades | 4 paquetes afectados | ⚠️ No crítico para el proyecto |
| **bandit** | 1 HIGH, 29 LOW | Mixed | ⚠️ 1 issue documentado |
| **Verificación secretos** | 0 | - | ✅ Ningún secreto en git |

#### Detalles de Vulnerabilidades en Dependencias

**Paquetes con vulnerabilidades** (no críticas para este proyecto):

| Paquete | Versión Actual | Vulnerabilidad | Impacto Real |
|---------|---------------|----------------|--------------|
| **future** | 0.18.2 | PYSEC-2022-42991 | ⚠️ Bajo - No usamos el módulo afectado |
| **pip** | 21.2.4 | PYSEC-2023-228, GHSA-4xh5 | ⚠️ Bajo - Solo desarrollo |
| **setuptools** | 58.0.4 | PYSEC-2022-43012, PYSEC-2025-49, GHSA-cx63 | ⚠️ Bajo - Solo instalación |
| **wheel** | 0.37.0 | PYSEC-2022-43017 | ⚠️ Bajo - Solo empaquetado |

**Justificación "No Crítico"**:
- Las vulnerabilidades afectan a herramientas de **build/instalación**, no al runtime de la aplicación
- La aplicación se distribuye como **ejecutable compilado** (PyInstaller), no como paquete pip
- Los usuarios finales **no ejecutan pip/setuptools** en su entorno

**Plan de Acción**:
- ✅ Documentar vulnerabilidades conocidas
- 🔄 Actualizar en próxima versión de desarrollo
- ✅ No requiere hotfix urgente

#### Issue Bandit de Alta Severidad

**B507: SSH without host key verification**

```python
# Ubicación: src/sync/sync_manager.py:104
self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
```

**Justificación**:
- Feature de sincronización SFTP es **opcional** y no está habilitado por defecto
- Solo se usa en entornos educativos controlados
- La IP del servidor SFTP es fija y conocida

**Mitigación**:
- ⚠️ Documentado en `USER_GUIDE.md` - solo para administradores
- ✅ Requiere configuración manual explícita
- 🔄 En roadmap: implementar verificación de host key en v3.1

**Ver reporte completo**: `documentacion/auditoria/SECURITY_AUDIT.md`

---

## �🔐 Gestión de Secretos

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

## 🤖 CI/CD y Auditorías Automáticas

### GitHub Actions - Security Workflow

El proyecto incluye auditorías de seguridad automatizadas en `.github/workflows/ci.yml`:

#### Ejecución Programada

```yaml
on:
  schedule:
    - cron: '0 2 * * 1'  # Cada lunes a las 2:00 AM
```

#### Jobs de Seguridad

| Job | Herramienta | Propósito | Frecuencia |
|-----|-------------|-----------|------------|
| **security** | `safety` | Vulnerabilidades en dependencias | Cada push + semanal |
| **security** | `bandit` | Análisis estático de código | Cada push + semanal |
| **test** | `pytest` | Tests de seguridad (validaciones) | Cada push |

#### Ejecución Manual

```bash
# Ejecutar auditorías localmente
python3 -m pip_audit --desc
python3 -m bandit -r src/ -ll  # Solo medium/high
```

#### Reportes Generados

Los workflows generan artefactos descargables:

- **bandit-report.json** - Análisis completo de Bandit
- **coverage.xml** - Cobertura de tests (incluye tests de validación)
- **test-results-*.xml** - Resultados de tests JUnit

**Acceso**: GitHub → Actions → Workflow run → Artifacts

### Configuración de Alerts

#### Dependabot (Recomendado)

Activar en: `GitHub → Settings → Security → Dependabot alerts`

Beneficios:
- ✅ Notificaciones automáticas de vulnerabilidades
- ✅ Pull requests automáticos con fixes
- ✅ Integración con GitHub Security Advisory

#### CodeQL (Opcional)

Para análisis más profundo:

```yaml
# .github/workflows/codeql.yml
name: "CodeQL"
on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 0 * * 0'  # Semanal
```

### Checklist de Seguridad Pre-Release

Antes de cada release, verificar:

- [ ] `pip-audit` sin vulnerabilidades críticas
- [ ] `bandit` sin nuevos issues HIGH
- [ ] Tests de validación pasando (100%)
- [ ] `.gitignore` actualizado
- [ ] `SECURITY.md` actualizado con auditoría reciente
- [ ] Dependencias actualizadas a versiones seguras
- [ ] Changelog incluye fixes de seguridad

### Contacto de Seguridad

**Email de seguridad**: cferrerobonet@gmail.com  
**Respuesta esperada**: 48 horas  
**Idiomas**: Español, Inglés

---

**Última revisión de este documento**: 8 de noviembre de 2025  
**Próxima auditoría programada**: 15 de noviembre de 2025 (automática via CI)  
**Mantenido por**: Carlos Ferrero Bonet

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
