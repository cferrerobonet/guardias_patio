# Diagrama de Arquitectura - Guardias de Patio

## Dependencias entre Capas (Estado Real)

```mermaid
graph TD
    subgraph Presentation["🖥️ PRESENTATION (PyQt6)"]
        Forms[Forms<br/>Formularios principales]
        Widgets[Widgets<br/>Componentes reutilizables]
        Dialogs[Dialogs<br/>Diálogos modales]
    end

    subgraph Application["📋 APPLICATION"]
        UseCases[Use Cases<br/>12 casos de uso]
        DTOs[DTOs<br/>Pydantic models]
        Controllers[Controllers<br/>Legacy]
    end

    subgraph Services["⚙️ SERVICES (Application Services)"]
        Asignador[asignador_guardias.py<br/>95KB - Algoritmo principal]
        Calculador[calculador_guardias.py<br/>19KB - Estadísticas]
        Exportadores[exportador.py + exportador_pdf.py<br/>122KB - Transformadores]
        Gestores[gestor_ausencias.py + gestor_cursos.py<br/>25KB - Gestores dominio]
        Otros[email + icalendar + importador<br/>36KB - Servicios externos]
    end

    subgraph Infrastructure["🗄️ INFRASTRUCTURE"]
        Repos[Repositories<br/>SQLAlchemy implementations]
        Mappers[Mappers<br/>ORM ↔ Domain]
        Database[(SQLite<br/>guardias.db)]
    end

    subgraph Domain["💎 DOMAIN (Core)"]
        Entities[Entities<br/>ProfesorEntity, GuardiaEntity, etc.]
        ValueObjects[Value Objects<br/>Email, Turno, HorasContrato]
        RepoInterfaces[Repository Protocols<br/>Interfaces abstractas]
        DomainServices[Domain Services<br/>Lógica de negocio pura]
    end

    %% Dependencias correctas
    Forms --> UseCases
    Widgets --> UseCases
    Dialogs --> UseCases
    
    UseCases -.-> RepoInterfaces
    
    Services --> Repos
    Services --> Mappers
    Services --> Entities
    
    Repos --> Mappers
    Repos --> Database
    
    Mappers --> Entities
    Mappers --> ValueObjects
    
    RepoInterfaces -.-> Repos
    
    %% Violaciones conocidas (6 use cases)
    UseCases ==> Repos
    
    %% Estilos
    style Domain fill:#e1f5e1,stroke:#4caf50,stroke-width:2px
    style Application fill:#e3f2fd,stroke:#2196f3,stroke-width:2px
    style Services fill:#fff3e0,stroke:#ff9800,stroke-width:2px
    style Infrastructure fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    style Presentation fill:#f3e5f5,stroke:#9c27b0,stroke-width:2px
    
    classDef violation stroke:#f44336,stroke-width:3px,stroke-dasharray: 5 5
    class UseCases violation
```

## Leyenda

- `-->` Dependencia correcta (flecha sólida)
- `-.->` Dependencia ideal vía interfaces (flecha punteada)
- `==>` ⚠️ **Violación arquitectónica** (flecha gruesa - 6 use cases)

## Violaciones Conocidas

**Cantidad**: 6 imports directos `application → infrastructure`

**Archivos afectados**:
1. `application/use_cases/guardia/obtener_guardias.py`
2. `application/use_cases/guardia/asignar_guardia.py`
3. `application/use_cases/profesor/listar_profesores.py`
4. `application/use_cases/profesor/obtener_profesor.py`
5. `application/use_cases/profesor/crear_profesor.py` (2 imports)

**Patrón actual** ❌:
```python
from infrastructure.repositories import SQLAlchemyProfesorRepository
```

**Patrón esperado** ✅:
```python
from domain.repositories import ProfesorRepositoryProtocol
```

## Capas y Responsabilidades

| Capa | Responsabilidad | Tamaño | Conformidad |
|------|----------------|--------|-------------|
| **Domain** | Lógica de negocio pura | ~50KB | ✅ 100% |
| **Application** | Casos de uso | ~80KB | ⚠️ 85% |
| **Services** | Lógica aplicación compleja | 361KB | ⚠️ N/A |
| **Infrastructure** | Persistencia, BD | ~120KB | ✅ 95% |
| **Presentation** | UI PyQt6 | ~200KB | ✅ 100% |

**Puntuación Global**: ⭐⭐⭐⭐ (4/5)

## Notas

- La carpeta `/services` está en `src/services/` por pragmatismo (idealmente sería `src/application/services/`)
- Las 6 violaciones son de severidad **media** (no bloqueantes, pero rompen DIP)
- Domain está **perfectamente aislado** (0 violaciones)
- Presentation solo depende de Application (correcto)

---

**Fecha**: 12 de noviembre de 2025  
**Fuente**: Auditoría FASE 2 - Consolidación de Código
