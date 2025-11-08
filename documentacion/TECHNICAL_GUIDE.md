# 📘 Guía Técnica - Guardias de Patio

**Versión**: 3.0.0  
**Última actualización**: 8 de noviembre de 2025  
**Autor**: Equipo de desarrollo

---

## 📚 Tabla de Contenidos

1. [Requisitos del Sistema](#1-requisitos-del-sistema)
2. [Arquitectura y Patrones](#2-arquitectura-y-patrones)
3. [Algoritmo de Asignación de Guardias](#3-algoritmo-de-asignación-de-guardias)
4. [Sistema de Validaciones](#4-sistema-de-validaciones)
5. [Sistema de Widgets](#5-sistema-de-widgets)
6. [Optimizaciones de Rendimiento](#6-optimizaciones-de-rendimiento)
7. [Sistema PDF Corporativo](#7-sistema-pdf-corporativo)
8. [Configuraciones Avanzadas](#8-configuraciones-avanzadas)
   - [8.1 Email SMTP](#81-email-smtp)
   - [8.2 Base de Datos](#82-base-de-datos)
   - [8.3 Sincronización Multi-usuario](#83-sincronización-multi-usuario)
9. [Especificaciones Técnicas](#9-especificaciones-técnicas)
10. [Mejoras UX y Accesibilidad](#10-mejoras-ux-y-accesibilidad)
11. [Referencias](#11-referencias)

---

## 1. Requisitos del Sistema

### 💻 Hardware

#### Resolución de Pantalla (CRÍTICO)

**Mínimos (Obligatorios)**:
- Resolución: 1280 x 720 píxeles (HD 720p)
- Relación de aspecto: 16:9 o similar
- ⚠️ **La aplicación NO se ejecutará** si no cumple con la resolución mínima

**Recomendados**:
- Resolución: 1920 x 1080 píxeles (Full HD) o superior
- Resoluciones probadas: Full HD ✅ | 2K QHD ✅ | 4K UHD ✅

**Otros Requisitos**:
- Procesador: Intel Core i3 (8ª gen) o AMD equivalente
- RAM: 4 GB mínimo, 8 GB recomendado
- Espacio: 500 MB libres (instalación)
- Gráficos: Compatible con aceleración PyQt6

### 🖥️ Sistemas Operativos

| SO | Mínimo | Recomendado | Arquitecturas |
|----|--------|-------------|---------------|
| **macOS** | 10.14 Mojave | 12 Monterey+ | Intel x86_64, Apple Silicon (M1/M2/M3) |
| **Windows** | 10 (64-bit) | 11 | x86_64 |
| **Linux** | Ubuntu 20.04+ | Fedora 35+ | x86_64 (experimental) |

### 📦 Software

**Instalador (Recomendado)**:
- ✅ Todo incluido (Python 3.11 embebido, PyQt6, dependencias)

**Desde Código Fuente**:
- Python 3.11.14 (otras 3.11.x pueden funcionar)
- pip + `requirements.txt`

### 🔍 Validación Automática

La aplicación valida la resolución al inicio:

1. **< 1280x720**: ❌ No se ejecuta, muestra error
2. **1280x720 - 1920x1080**: ⚠️ Advertencia, permite continuar
3. **≥ 1920x1080**: ✅ Sin advertencias, óptimo

Ver: `src/core/screen_validator.py`

---

## 2. Arquitectura y Patrones

### 🏗️ Clean Architecture

La aplicación sigue **Clean Architecture** con separación clara de responsabilidades:

```
src/
├── domain/              # Capa de dominio (entidades, lógica de negocio)
│   ├── entities/        # Entidades de dominio
│   ├── value_objects/   # Objetos de valor
│   └── exceptions/      # Excepciones de negocio
│
├── application/         # Capa de aplicación (casos de uso)
│   ├── use_cases/       # Casos de uso
│   ├── dtos/            # Data Transfer Objects
│   └── interfaces/      # Interfaces (repositories)
│
├── infrastructure/      # Capa de infraestructura (detalles técnicos)
│   ├── database/        # SQLAlchemy, modelos ORM
│   ├── repositories/    # Implementación de repositories
│   └── config/          # Configuración
│
├── presentation/        # Capa de presentación (UI)
│   ├── forms/           # Formularios PyQt6
│   ├── widgets/         # Widgets reutilizables
│   └── themes/          # Estilos Fluent Design
│
└── core/                # Utilidades compartidas
    ├── logging.py       # Sistema de logs
    ├── paths.py         # Gestión de rutas
    └── exceptions.py    # Excepciones base
```

### 📐 Patrones Implementados

#### Repository Pattern
- Abstracción del acceso a datos
- Interfaces en `application/interfaces/`
- Implementaciones en `infrastructure/repositories/`

**Ejemplo**:
```python
# Interface
class IProfesorRepository(ABC):
    @abstractmethod
    def crear(self, profesor: Profesor) -> Profesor:
        pass

# Implementación
class ProfesorRepository(IProfesorRepository):
    def crear(self, profesor: Profesor) -> Profesor:
        # Lógica SQLAlchemy
        ...
```

#### Use Case Pattern
- Cada acción = 1 caso de uso
- Lógica de negocio encapsulada
- Testeable e independiente

**Ejemplo**:
```python
class CrearProfesorUseCase:
    def __init__(self, repo: IProfesorRepository):
        self.repo = repo
    
    def execute(self, dto: CrearProfesorDTO) -> Profesor:
        # Validaciones
        # Lógica de negocio
        # Persistencia
        ...
```

#### DTO Pattern
- Transferencia de datos entre capas
- Validación con Pydantic
- Inmutables (frozen dataclasses)

**Ejemplo**:
```python
@dataclass(frozen=True)
class CrearProfesorDTO:
    nombre_completo: str
    email_corporativo: Optional[str]
    horas_contrato: int
    turno: Literal["Mañana", "Tarde", "Completo"]
```

### 🔄 Flujo de Datos

```
[UI Form] 
   ↓ (datos usuario)
[DTO] 
   ↓ (validado)
[Use Case] 
   ↓ (lógica negocio)
[Repository] 
   ↓ (persistencia)
[Database]
```

### 📊 Gestión de Estado

- **Session por ventana**: Cada formulario tiene su propia session SQLAlchemy
- **Transacciones**: Commit explícito después de cada operación
- **Rollback automático**: En caso de error
- **Refresh**: Refrescar entidades después de commit

---

## 3. Algoritmo de Asignación de Guardias

### 🎯 Objetivo

Asignar guardias de recreo a profesores de forma:
- ✅ **Equitativa**: Distribución justa según horas de contrato
- ✅ **Eficiente**: Minimizar sobrecarga y maximizar períodos libres
- ✅ **Respetuosa**: Cumplir restricciones (ausencias, preferencias)

### 📝 Premisas del Algoritmo

> Para documentación completa, ver: `documentacion/PREMISAS_ASIGNACION_GUARDIAS.md`

**Prioridades (de mayor a menor)**:

1. **Fechas consecutivas/agrupadas** (Prioridad ALTA)
   - Agrupar guardias en días consecutivos
   - Profesor termina sus guardias antes que otros empiecen
   - Minimiza interrupciones

2. **Cuotas de guardias** (Prioridad ALTA)
   - Calcular guardias según horas de contrato
   - Distribución proporcional por turno

3. **Respetar ausencias** (Prioridad ALTA)
   - No asignar guardias en fechas de ausencia
   - Validación automática

4. **Preferencias de zona** (Prioridad MEDIA)
   - Asignar zona preferida cuando sea posible
   - No bloquea asignación si no hay disponibilidad

5. **Restricciones de horario** (Prioridad MEDIA)
   - Respetar días/recreos permitidos
   - Matriz de disponibilidad personalizable

### 🔄 Iteraciones del Algoritmo

#### Iteración 1: Inicialización
```python
# Calcular cuotas
for profesor in profesores_activos:
    cuota = calcular_cuota(profesor.horas_contrato, profesor.turno)
    profesor.guardias_pendientes = cuota
```

#### Iteración 2: Preasignación por preferencias
```python
# Asignar zonas preferidas (si disponibles)
for guardia in guardias_sin_asignar:
    profesores_disponibles = filtrar_por_zona_preferida(guardia.zona)
    if profesores_disponibles:
        asignar_profesor(guardia, mejor_candidato(profesores_disponibles))
```

#### Iteración 3: Fechas consecutivas (CLAVE)
```python
# Agrupar guardias por profesor en fechas cercanas
for profesor in profesores_con_guardias_pendientes:
    bloques_consecutivos = encontrar_bloques_disponibles(profesor)
    asignar_bloque_optimo(profesor, bloques_consecutivos)
```

#### Iteración 4: Relleno equitativo
```python
# Asignar guardias restantes equitativamente
while guardias_sin_asignar:
    profesor = profesor_con_menos_guardias_asignadas()
    guardia = guardia_compatible(profesor)
    asignar(guardia, profesor)
```

#### Iteración 5: Balance final
```python
# Equilibrar cargas entre profesores del mismo turno
for turno in ["Mañana", "Tarde"]:
    profesores_turno = profesores_por_turno(turno)
    rebalancear_guardias(profesores_turno)
```

#### Iteración 6: Validación
```python
# Verificar que no hay conflictos
validar_sin_conflictos()
validar_cuotas_respetadas()
validar_ausencias_respetadas()
```

### 📊 Métricas de Calidad

El algoritmo calcula métricas para evaluar la asignación:

- **Cobertura**: % de guardias asignadas vs totales
  - Objetivo: ≥ 95%
  
- **Equidad**: Desviación estándar de guardias entre profesores
  - Objetivo: ≤ 15%
  
- **Agrupación**: % de guardias en bloques consecutivos
  - Objetivo: ≥ 60%

- **Preferencias satisfechas**: % de guardias en zona preferida
  - Objetivo: ≥ 70%

### 🔧 Configuración

```python
# src/infrastructure/config/algorithm_config.py
ALGORITMO_CONFIG = {
    "max_guardias_consecutivas": 5,
    "min_dias_libres_entre_bloques": 3,
    "peso_zona_preferida": 0.3,
    "peso_fechas_consecutivas": 0.5,
    "peso_equidad": 0.2
}
```

---

## 4. Sistema de Validaciones

### 🛡️ Capas de Validación

#### 1. Validación de Entrada (Presentation Layer)
- PyQt6 validators en formularios
- Validación en tiempo real (on-change)
- Feedback visual inmediato

#### 2. Validación de Negocio (Domain Layer)
- Reglas de negocio en entidades
- Validaciones complejas
- Excepciones personalizadas

#### 3. Validación de Persistencia (Infrastructure Layer)
- Constraints de base de datos
- Validaciones SQLAlchemy
- Integridad referencial

### 📋 Reglas de Negocio

#### Profesores
```python
# Nombre completo requerido (3-100 caracteres)
if not (3 <= len(nombre) <= 100):
    raise ValidationError("Nombre debe tener entre 3 y 100 caracteres")

# Email corporativo válido (opcional)
if email and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
    raise ValidationError("Email inválido")

# Horas de contrato válidas
if turno == "Mañana" and not (10 <= horas <= 18):
    raise ValidationError("Mañana: 10-18 horas")
elif turno == "Tarde" and not (10 <= horas <= 18):
    raise ValidationError("Tarde: 10-18 horas")
elif turno == "Completo" and not (20 <= horas <= 37):
    raise ValidationError("Completo: 20-37 horas")
```

#### Guardias
```python
# Fecha válida (dentro del año académico)
if not (fecha_inicio_curso <= fecha <= fecha_fin_curso):
    raise ValidationError("Fecha fuera del año académico")

# Turno y recreo compatibles
if turno == "Mañana" and recreo not in [1, 2]:
    raise ValidationError("Mañana: solo recreos 1 y 2")
elif turno == "Tarde" and recreo not in [3]:
    raise ValidationError("Tarde: solo recreo 3")

# No conflictos (un profesor, una guardia por turno/recreo/fecha)
if ya_existe_guardia(profesor, fecha, turno, recreo):
    raise ConflictError("Profesor ya tiene guardia en ese horario")
```

#### Zonas
```python
# Nombre único
if existe_zona(nombre):
    raise ValidationError("Ya existe una zona con ese nombre")

# Fechas coherentes
if fecha_fin < fecha_inicio:
    raise ValidationError("Fecha fin debe ser posterior a fecha inicio")

# Capacidad mínima
if not zona.tiene_profesores_asignados():
    raise ValidationError("Zona sin profesores asignados")
```

#### Ausencias
```python
# Rango de fechas válido
if fecha_fin < fecha_inicio:
    raise ValidationError("Fecha fin debe ser posterior a inicio")

# No solapamiento de ausencias del mismo profesor
if hay_ausencia_solapada(profesor, fecha_inicio, fecha_fin):
    raise ValidationError("Ya existe ausencia en ese rango")

# Reasignación automática
if ausencia.afecta_guardias:
    reasignar_guardias_automaticamente(ausencia.guardias_afectadas)
```

### 🚨 Excepciones Personalizadas

```python
# src/domain/exceptions.py

class BusinessLogicError(Exception):
    """Error de lógica de negocio"""
    pass

class ValidationError(BusinessLogicError):
    """Error de validación de datos"""
    pass

class ConflictError(BusinessLogicError):
    """Error de conflicto (duplicados, solapamiento)"""
    pass

class NotFoundError(BusinessLogicError):
    """Entidad no encontrada"""
    pass
```

### ✅ Testing de Validaciones

```python
# tests/test_validaciones.py

def test_profesor_nombre_muy_corto():
    with pytest.raises(ValidationError, match="entre 3 y 100"):
        Profesor(nombre_completo="AB")

def test_guardia_conflicto():
    # Crear guardia
    guardia1 = crear_guardia(profesor, fecha, turno, recreo)
    
    # Intentar crear duplicado
    with pytest.raises(ConflictError, match="ya tiene guardia"):
        guardia2 = crear_guardia(profesor, fecha, turno, recreo)
```

---

## 5. Sistema de Widgets

> ⚠️ **Nota**: Sección en construcción. Ver `documentacion/archivo/tecnico/PATRON_WIDGETS.md` para documentación completa.

### 🎨 Patrón de Widgets Reutilizables

Todos los widgets siguen un patrón consistente para mantener la coherencia visual y funcional.

### 📦 Widgets Principales

1. **TableManager**: Gestión avanzada de tablas
   - Selección múltiple (Ctrl, Shift, Ctrl+A)
   - Búsqueda en tiempo real
   - Restauración de selección después de recargas
   - Shortcuts (Supr para eliminar)

2. **BaseForm**: Clase base para formularios
   - Métodos comunes (mostrar_exito, mostrar_error, mostrar_advertencia)
   - Gestión de session SQLAlchemy
   - Shortcuts estándar (Ctrl+S guardar, Esc cancelar)

3. **Widgets de datos** (Profesores, Zonas, Ausencias)
   - Validación en tiempo real
   - get_datos() / set_datos(dict)
   - validar() -> (bool, str)
   - limpiar()

### 🎯 Ejemplo de Uso

```python
class MiFormulario(BaseForm):
    def __init__(self, session):
        super().__init__(session)
        
        # Crear widget de datos
        self.datos_widget = DatosWidget()
        
        # Crear TableManager
        self.table_manager = TableManager(
            self.tabla,
            on_delete=self.eliminar_seleccionados,
            on_double_click=self.editar_fila
        )
    
    def guardar(self):
        # Validar
        valido, error = self.datos_widget.validar()
        if not valido:
            self.mostrar_advertencia("Validación", error)
            return
        
        # Obtener datos
        datos = self.datos_widget.get_datos()
        
        # Procesar...
```

---

## 6. Optimizaciones de Rendimiento

> ⚠️ **Nota**: Sección en construcción. Ver `documentacion/archivo/tecnico/GUIA_OPTIMIZACIONES_RENDIMIENTO.md` para documentación completa.

### ⚡ Estrategias Implementadas

#### 1. Lazy Loading
- Cargar solo datos visibles
- Paginación en tablas grandes
- Defer loading de relaciones SQLAlchemy

#### 2. Caché de Consultas
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def obtener_profesores_activos(turno: str):
    return session.query(Profesor).filter_by(
        activo=True,
        turno=turno
    ).all()
```

#### 3. Bulk Operations
```python
# ❌ Lento: 1 INSERT por iteración
for guardia in guardias:
    session.add(guardia)
    session.commit()

# ✅ Rápido: 1 INSERT múltiple
session.bulk_save_objects(guardias)
session.commit()
```

#### 4. Índices de Base de Datos
```python
class Guardia(Base):
    __tablename__ = "guardias"
    
    # Índices para búsquedas frecuentes
    __table_args__ = (
        Index('idx_guardia_profesor', 'profesor_id'),
        Index('idx_guardia_fecha', 'fecha'),
        Index('idx_guardia_zona', 'zona_id'),
        Index('idx_guardia_unique', 'fecha', 'turno', 'recreo', 
              'zona_id', unique=True),
    )
```

---

## 7. Sistema PDF Corporativo

> ⚠️ **Nota**: Sección en construcción. Ver `documentacion/archivo/tecnico/SISTEMA_PDF_CORPORATIVO.md` para documentación completa.

### 🎨 Paleta de Colores

```python
CORPORATE_COLORS = {
    "primary_blue": "#0078D4",
    "secondary_gray": "#F3F2F1",
    "header_bg": "#005A9E",
    "zona_1": "#FFE699",
    "zona_2": "#C6E0B4",
    "zona_3": "#B4C7E7",
    # ... más colores
}
```

### 📄 Generación de PDFs

La aplicación usa **ReportLab** para generar PDFs con estilo corporativo consistente.

**Ejemplo básico**:
```python
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table

def generar_pdf_guardias(guardias, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4))
    elements = []
    
    # Header corporativo
    elements.append(crear_header_corporativo())
    
    # Tabla de guardias
    tabla_datos = preparar_datos_tabla(guardias)
    tabla = Table(tabla_datos, colWidths=[...])
    tabla.setStyle(estilo_corporativo())
    elements.append(tabla)
    
    doc.build(elements)
```

---

## 8. Configuraciones Avanzadas

### 8.1 Email SMTP

> Ver documentación completa en: `documentacion/archivo/tecnico/CONFIGURACION_EMAIL_SMTP.md`

**Configuración básica**:
```python
# src/infrastructure/config/email_config.py
EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "use_tls": True,
    "username": os.getenv("EMAIL_USERNAME"),
    "password": os.getenv("EMAIL_PASSWORD"),
    "from_address": "guardias@escuela.com"
}
```

**Envío de correo**:
```python
from src.infrastructure.email import EmailService

email_service = EmailService()
email_service.enviar_notificacion_guardias(
    destinatarios=["profesor@escuela.com"],
    guardias=guardias_asignadas,
    periodo="Noviembre 2025"
)
```

### 8.2 Base de Datos

> Ver documentación completa en: `documentacion/archivo/tecnico/UBICACION_BASE_DATOS.md`

**Ubicaciones**:
- **Desarrollo**: `data/guardias_patio.db`
- **Producción (macOS)**: `~/Library/Application Support/guardias_patio/guardias_patio.db`
- **Producción (Windows)**: `%APPDATA%/guardias_patio/guardias_patio.db`

**Gestión con Alembic**:
```bash
# Crear migración
alembic revision --autogenerate -m "descripción"

# Aplicar migraciones
alembic upgrade head

# Rollback
alembic downgrade -1
```

### 8.3 Sincronización Multi-usuario

> Ver documentación completa en: `documentacion/archivo/tecnico/GUIA_SINCRONIZACION_MULTIUSUARIO.md`

**Sistema de bloqueo**:
```python
# Adquirir bloqueo antes de editar
if not session_manager.acquire_lock(user_id):
    mostrar_advertencia("Otro usuario está editando")
    return

try:
    # Realizar cambios
    editar_profesor(...)
finally:
    # Liberar bloqueo
    session_manager.release_lock(user_id)
```

---

## 9. Especificaciones Técnicas

> Ver documentación completa en: `documentacion/archivo/tecnico/ESPECIFICACION_CALCULO_GUARDIAS.md`

### 📐 Cálculo de Cuotas de Guardias

**Fórmula base**:
```python
def calcular_cuota_guardias(horas_contrato: int, turno: str) -> int:
    """
    Calcula el número de guardias que debe hacer un profesor.
    
    Args:
        horas_contrato: Horas semanales de contrato
        turno: "Mañana", "Tarde" o "Completo"
    
    Returns:
        Número de guardias asignadas
    """
    # Profesores de mañana/tarde: 1 guardia por cada 3 horas
    if turno in ["Mañana", "Tarde"]:
        return horas_contrato // 3
    
    # Profesores de jornada completa: proporción especial
    elif turno == "Completo":
        # Hacen guardias de mañana Y tarde
        return (horas_contrato // 2) // 3
    
    return 0
```

**Ejemplos**:
- Profesor mañana, 15h → 5 guardias
- Profesor tarde, 12h → 4 guardias  
- Profesor completo, 30h → 5 guardias (pueden ser mañana o tarde)

### 📊 Distribución por Turno

```python
def distribuir_por_turno(profesor: Profesor, cuota: int) -> dict:
    """Distribuye las guardias entre recreos según turno."""
    
    if profesor.turno == "Mañana":
        # Solo recreos 1 y 2
        return {
            "recreo_1": cuota // 2,
            "recreo_2": cuota - (cuota // 2)
        }
    
    elif profesor.turno == "Tarde":
        # Solo recreo 3
        return {
            "recreo_3": cuota
        }
    
    elif profesor.turno == "Completo":
        # Puede hacer cualquier recreo
        # Priorizar según disponibilidad
        return distribuir_flexible(cuota)
```

---

## 10. Mejoras UX y Accesibilidad

> Ver documentación completa en: `documentacion/archivo/tecnico/MEJORAS_UX_TABLAS_v3.0.md`

### ✨ Mejoras Implementadas (v3.0)

#### Auto-save
- Matriz de restricciones se guarda automáticamente
- Sin botón "Guardar" innecesario
- Feedback visual de guardado

#### Navegación fluida
- Cambio entre días sin confirmaciones
- Auto-save al cambiar de vista
- No recargas innecesarias

#### Cancelar sin reload
- Botón "Cancelar" limpia formulario sin recargar tabla
- Más rápido y menos frustrante
- Consistente en todos los formularios

#### Confirmaciones inteligentes
- Solo para operaciones destructivas (eliminar, reasignar)
- No para operaciones reversibles (cancelar)
- Mensajes claros y descriptivos

### ♿ Accesibilidad

- Resolución mínima validada (1280x720)
- Fuentes legibles (Segoe UI 10pt+)
- Contraste alto (WCAG AA)
- Atajos de teclado para todas las acciones
- Lectores de pantalla parcialmente soportados

---

## 11. Referencias

### 📚 Documentación Archivada

Los siguientes documentos fueron consolidados en esta guía técnica y se mantienen en `documentacion/archivo/tecnico/` para referencia histórica:

- `ALGORITMO_ASIGNACION_GUARDIAS.md` (13 KB)
- `ARCHITECTURE_PATTERNS.md` (33 KB)
- `CONFIGURACION_EMAIL_SMTP.md` (20 KB)
- `ESPECIFICACION_CALCULO_GUARDIAS.md` (41 KB)
- `GUIA_OPTIMIZACIONES_RENDIMIENTO.md` (13 KB)
- `GUIA_SINCRONIZACION_MULTIUSUARIO.md` (32 KB)
- `MEJORAS_UX_TABLAS_v3.0.md` (8 KB)
- `PATRON_WIDGETS.md` (37 KB)
- `PLAN_MIGRACION_SOLO_BD.md` (20 KB)
- `REQUISITOS_SISTEMA.md` (7.5 KB)
- `SISTEMA_PDF_CORPORATIVO.md` (11 KB)
- `UBICACION_BASE_DATOS.md` (4.3 KB)
- `VALIDACIONES_NEGOCIO.md` (20 KB)
- `README.md` (9.3 KB)

### 🔗 Enlaces Útiles

- [Arquitectura](../ARCHITECTURE.md) - Documentación de arquitectura detallada
- [Testing](../TESTING.md) - Estrategia y cobertura de tests
- [Premisas del Algoritmo](../PREMISAS_ASIGNACION_GUARDIAS.md) - Reglas completas del algoritmo
- [Plan de Refactorización](../PLAN_REFACTORIZACION.md) - Historial de mejoras

### 📖 Documentación Externa

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [ReportLab User Guide](https://www.reportlab.com/docs/reportlab-userguide.pdf)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

## 📝 Notas Finales

Este documento consolida 14 archivos técnicos en una guía unificada para facilitar la navegación y mantenimiento. Para información más detallada sobre temas específicos, consulta los documentos originales en `documentacion/archivo/tecnico/`.

**Próximas secciones a expandir**:
- Sección 5 (Widgets): Añadir ejemplos completos
- Sección 6 (Optimizaciones): Métricas de rendimiento
- Sección 7 (PDFs): Guía completa de estilos

---

**Última actualización**: 8 de noviembre de 2025  
**Versión**: 1.0.0  
**Mantenedor**: Equipo de desarrollo
