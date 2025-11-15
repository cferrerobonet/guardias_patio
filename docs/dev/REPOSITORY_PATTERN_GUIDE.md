# 📘 GUÍA DE USO: REPOSITORY PATTERN

## ✅ Fase 2.1 Completada: Repository Pattern Implementado

### Repositorios Creados

#### Interfaces (Domain Layer)
- ✅ `IConfiguracionRepository` - Gestión de configuración
- ✅ `IAusenciaRepository` - Gestión de ausencias
- ✅ `ICursoEscolarRepository` - Gestión de cursos escolares

#### Implementaciones (Infrastructure Layer)
- ✅ `SQLAlchemyConfiguracionRepository`
- ✅ `SQLAlchemyAusenciaRepository`
- ✅ `SQLAlchemyCursoEscolarRepository`
- ✅ `RepositoryFactory` - Factoría centralizada

---

## 📖 Cómo Usar los Repositorios

### Antes (Acceso directo a session.query)

```python
def obtener_configuracion(session: Session):
    # ❌ Acoplamiento directo a SQLAlchemy
    config = session.query(Configuracion).first()
    return config

def profesor_ausente(session: Session, profesor_id: int, fecha: date):
    # ❌ Lógica de persistencia mezclada con negocio
    ausencia = (
        session.query(Ausencia)
        .filter(
            Ausencia.profesor_id == profesor_id,
            Ausencia.fecha_inicio <= fecha,
            Ausencia.fecha_fin >= fecha,
            Ausencia.activa == True,
        )
        .first()
    )
    return ausencia is not None
```

### Después (Con Repository Pattern)

```python
from infrastructure.repositories.repository_factory import RepositoryFactory

class MiServicio:
    def __init__(self, session: Session):
        self.session = session
        factory = RepositoryFactory(session)
        self.config_repo = factory.create_configuracion_repository()
        self.ausencia_repo = factory.create_ausencia_repository()
    
    def obtener_configuracion(self):
        # ✅ Abstracción limpia
        return self.config_repo.get_first()
    
    def profesor_ausente(self, profesor_id: int, fecha: date) -> bool:
        # ✅ Lógica de negocio pura
        ausencia = self.ausencia_repo.find_by_profesor_and_date(
            profesor_id, fecha
        )
        return ausencia is not None
```

---

## 🎯 Beneficios Obtenidos

### 1. **Separación de Responsabilidades**
- ✅ Dominio independiente de infraestructura
- ✅ Lógica de negocio sin SQL
- ✅ Fácil cambio de ORM sin tocar servicios

### 2. **Testabilidad Mejorada**
```python
# Mock fácil para testing
class MockAusenciaRepository:
    def find_by_profesor_and_date(self, profesor_id, fecha):
        return None  # Simular sin ausencias

def test_asignacion():
    mock_repo = MockAusenciaRepository()
    servicio = MiServicio(mock_repo)
    # Test aislado sin base de datos
```

### 3. **Código Más Expresivo**
```python
# Antes: SQL críptico
session.query(CursoEscolar).filter_by(activo=True).first()

# Después: Intención clara
curso_repo.find_active()
```

### 4. **Reutilización**
- ✅ Mismo método en múltiples servicios
- ✅ Queries optimizadas en un solo lugar
- ✅ Eager loading centralizado

---

## 📊 Estado de Refactorización

### Archivos con `session.query()` Directo

| Archivo | Queries | Estado | Prioridad |
|---------|---------|---------|-----------|
| `exportador_pdf.py` | 12 | 🔴 Pendiente | Alta |
| `gestor_cursos.py` | 10 | 🟡 Parcial | Alta |
| `asignador_guardias_v3_simple.py` | 8 | 🔴 Pendiente | Media |
| `validador_guardias.py` | 6 | 🔴 Pendiente | Media |
| `validators/ausencia_checker.py` | 6 | 🔴 Pendiente | Media |
| `exportador.py` | 2 | 🔴 Pendiente | Baja |

**Total:** ~50 queries directas → Objetivo: 0

---

## 🚀 Próximos Pasos

### Fase 2.2: Separar Orquestador (En proceso)
- Split `asignador_guardias.py` en 5 clases especializadas
- Aplicar Single Responsibility Principle

### Fase 2.3: Centralizar Estadísticas
- Crear `EstadisticasService`
- Eliminar 200+ líneas duplicadas

---

## 💡 Ejemplos de Uso por Repositorio

### ConfiguracionRepository
```python
# Obtener configuración activa
config = config_repo.get_first()
print(f"Días lectivos: {config.dias_lectivos}")
```

### AusenciaRepository
```python
# Verificar ausencia en fecha
ausencia = ausencia_repo.find_by_profesor_and_date(profesor_id=1, fecha=date.today())
if ausencia:
    print(f"Profesor ausente: {ausencia.motivo}")

# Contar ausencias totales
total = ausencia_repo.count_by_profesor(profesor_id=1)
print(f"Ausencias: {total}")
```

### CursoEscolarRepository
```python
# Obtener curso activo
curso = curso_repo.find_active()
print(f"Curso activo: {curso.nombre}")

# Desactivar todos
curso_repo.deactivate_all()

# Buscar por año
curso_2024 = curso_repo.find_by_year(2024)
```

---

## ⚠️ Notas Importantes

1. **Transacciones**: Los repositorios NO hacen commit, solo flush
2. **Session Management**: La sesión debe gestionarse en el caller
3. **Factory Pattern**: Usar siempre RepositoryFactory para crear repos
4. **Type Hints**: Todas las interfaces tienen type hints completos

---

**Actualizado:** 14 de noviembre de 2025
**Estado:** Fase 2.1 Completa ✅
