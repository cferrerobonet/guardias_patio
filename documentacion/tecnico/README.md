# Documentación Técnica

Especificaciones técnicas, arquitectura del sistema y documentación de referencia.

## 📚 Contenido

### [Características del Sistema](caracteristicas-sistema.md)
Especificaciones completas del sistema:
- Funcionalidades principales
- Capacidades técnicas
- Requisitos del sistema
- Limitaciones conocidas
- Rendimiento esperado

**Ideal para**: Evaluación técnica, planificación de infraestructura

### [Ejemplo de Exportación](ejemplo-exportacion.json)
Archivo JSON de ejemplo con la estructura de datos:
- Estructura completa de exportación
- Formato de cada entidad (profesores, zonas, guardias)
- Tipos de datos y validaciones
- Ejemplo con datos reales anonimizados

**Ideal para**: Integración con otros sistemas, validación de formato

### [Matriz Horario Día-Recreo](matriz-horario-dia-recreo.md)
Documentación de la matriz de disponibilidad:
- Estructura de datos día × recreo
- Restricciones por profesor
- Implementación en base de datos
- Uso en algoritmo de asignación

**Ideal para**: Entender restricciones temporales

### [Resumen Matriz Horario](resumen-matriz-horario.md)
Resumen ejecutivo de la matriz de horarios:
- Concepto principal
- Casos de uso
- Integración con sistema
- Mejoras implementadas en v2.6

**Ideal para**: Overview rápido del sistema de restricciones

## 🔧 Stack Tecnológico

### Backend
- **Lenguaje**: Python 3.9+
- **ORM**: SQLAlchemy 2.0+
- **Base de Datos**: SQLite 3
- **Migraciones**: Alembic

### Frontend
- **Framework GUI**: PyQt6 6.7.0
- **Widgets personalizados**: QTableWidget, QCalendarWidget
- **Estilos**: Qt Stylesheets (CSS-like)

### Testing
- **Framework**: pytest
- **Cobertura**: pytest-cov
- **Fixtures**: pytest fixtures con DB en memoria

### Desarrollo
- **Linting**: Ruff (sustituto de flake8, black, isort)
- **Control de versiones**: Git
- **CI/CD**: GitHub Actions (futuro)

## 📊 Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────┐
│                  GUI (PyQt6)                        │
│  MainWindow → Tabs → Forms/Widgets                  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              Services Layer                          │
│  - AsignadorGuardias                                │
│  - CalculadorGuardias                               │
│  - GestorAusencias                                  │
│  - ExportadorDatos                                  │
│  - ExportadorPDF                                    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│           Database Layer (SQLAlchemy)               │
│  - DBManager (session management)                   │
│  - Models (Profesor, Zona, Guardia, etc.)          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│                SQLite Database                       │
│  guardias_patio.db                                  │
└─────────────────────────────────────────────────────┘
```

## 🗄️ Modelo de Datos

### Entidades Principales

**Profesor**
```python
- id: Integer (PK)
- nombre_completo: String  # Formato: "APELLIDOS, NOMBRE"
- email_corporativo: String (nullable)
- horas_contrato: Float
- porcentaje_jornada: Float
- turno: String (completo/mañana/tarde/mixto)
- horas_manana: Float (nullable, para turno mixto)
- horas_tarde: Float (nullable, para turno mixto)
- tutor: Boolean (default: False)
- fecha_inicio_guardias: Date (nullable)
- fecha_fin_guardias: Date (nullable)
- dias_semana_permitidos: Text (JSON: [0..6])
- recreos_permitidos: Text (JSON: [1..N])
```

**Zona**
```python
- id: Integer (PK)
- nombre_zona: String (unique)
- descripcion: Text
```

**Guardia**
```python
- id: Integer (PK)
- profesor_id: ForeignKey(Profesor)
- zona_id: ForeignKey(Zona)
- fecha: Date
- turno: String
- recreo: Integer
```

**Ausencia**
```python
- id: Integer (PK)
- profesor_id: ForeignKey(Profesor)
- fecha_inicio: Date
- fecha_fin: Date
- tipo: String (baja_medica/permiso/vacaciones/otros)
- motivo: Text (nullable)
- documento_path: String (nullable) - Ruta al justificante
- activa: Boolean (default: True)
- created_at: DateTime
- updated_at: DateTime
```

**Configuracion**
```python
- id: Integer (PK) - Singleton
- fecha_inicio_curso: Date
- fecha_fin_curso: Date
- hora_recreo1_manana: Time
- hora_recreo2_manana: Time
- hora_recreo1_tarde: Time
- hora_recreo2_tarde: Time
- activar_festivos_automaticos: Boolean
- dias_no_lectivos_personalizados: JSON Array
- recreos_config: JSON Object
- ajuste_tutores: Float
- ajuste_no_tutores: Float
```

## 📏 Límites y Capacidades

| Aspecto | Límite/Capacidad | Notas |
|---------|------------------|-------|
| Profesores | ~1000 | Sin límite técnico, UI puede degradarse |
| Zonas | ~50 | Suficiente para centros grandes |
| Guardias | ~10,000/año | 200 días × 50 profesores |
| Ausencias | Ilimitadas | Solo limitado por disco |
| Curso escolar | 1 año académico | No multi-año simultáneo |
| Tamaño DB | ~50-100 MB/año | Con 100 profesores |

## ⚡ Rendimiento

### Operaciones Típicas

| Operación | Tiempo Esperado | Complejidad |
|-----------|----------------|-------------|
| Listar profesores | < 50ms | O(n) |
| Asignar 1 guardia | < 100ms | O(n × m) |
| Generar calendario mes | < 5s | O(días × profesores × zonas) |
| Exportar a JSON | < 2s | O(n) |
| Importar desde JSON | < 5s | O(n) + transacciones |
| Calcular estadísticas | < 1s | O(n) |

### Optimizaciones Implementadas
- ✅ Caché de consultas frecuentes
- ✅ Índices en columnas de búsqueda
- ✅ Lazy loading de relaciones
- ✅ Batch inserts para importación
- ✅ Query optimization con SQLAlchemy

## 🔐 Seguridad

### Datos Personales (RGPD)
- Los emails corporativos son datos personales
- Sistema cumple con RGPD: derecho al olvido (eliminar profesor)
- No hay cifrado en BD (SQLite local)
- Responsabilidad del centro: proteger archivos de backup

### Autenticación
- ❌ No implementada (aplicación local monousuario)
- 🔮 Planificada para v3.0 (versión web)

### Autorización
- ❌ No implementada (todos los accesos son admin)
- 🔮 Planificada para v3.0 (roles: admin, coordinador, profesor)

## 🌐 Plataformas Soportadas

| Plataforma | Soporte | Notas |
|------------|---------|-------|
| Windows 10/11 | ✅ Completo | PyQt6 nativo |
| macOS 12+ | ✅ Completo | Requiere permisos de Accesibilidad |
| Linux (Ubuntu/Debian) | ✅ Completo | Requiere Qt dependencies |
| Linux (otras distros) | ⚠️ No testeado | Debería funcionar |

## 📦 Empaquetado

### Formatos Disponibles
- **Python**: Código fuente con requirements.txt
- **PyInstaller**: Ejecutable standalone (futuro)
- **Docker**: Contenedor con todo incluido (futuro)

### Tamaño
- Código fuente: ~500 KB
- Con dependencias: ~150 MB (PyQt6 es pesado)
- Ejecutable standalone: ~200 MB

## 🔗 APIs Externas

### Festivos Automáticos
- **API**: festivos.es o similar (a configurar)
- **Uso**: Poblar días no lectivos automáticamente
- **Estado**: Configurable, por defecto desactivado

### Email (Futuro)
- **Uso**: Notificar asignaciones a profesores
- **Protocolo**: SMTP
- **Estado**: No implementado

## 📊 Formato de Exportación

### JSON Schema (simplificado)
```json
{
  "version": "1.0",
  "fecha_exportacion": "YYYY-MM-DD",
  "profesores": [
    {
      "nombre": "string",
      "apellidos": "string",
      "email_corporativo": "string",
      "horas_contrato": "number",
      ...
    }
  ],
  "zonas": [...],
  "configuracion": {...},
  "guardias": [...]
}
```

Ver [ejemplo-exportacion.json](ejemplo-exportacion.json) para estructura completa.

## 🧪 Testing

### Cobertura Actual
- **Total de tests**: ~43
- **Cobertura de código**: ~85%
- **Tests por módulo**:
  - asignador_guardias: 10 tests
  - calculador_guardias: 8 tests
  - exportador: 14 tests
  - validators: 5 tests
  - zona_preferida: 6 tests

### Estrategia
- Tests unitarios para lógica de negocio
- Tests de integración para DB
- Tests de UI (limitados, PyQt6 complejo)
- Fixtures compartidos con DB en memoria

## 🔗 Ver También

- [Guía de Desarrollo](../desarrollo/guia-desarrollo.md) - Setup y contribución
- [Características](caracteristicas-sistema.md) - Specs completas
- [Validaciones](../validaciones/README.md) - Reglas de negocio

---

[← Volver al índice principal](../README.md)
