# 📚 API Documentation

**Generada**: 12 de November de 2025

## Capas Documentadas

- **Domain**: Entidades, Value Objects, Repositories
- **Application**: Use Cases, DTOs  
- **Services**: Servicios de aplicación

## Acceso

La documentación completa puede generarse con:

```bash
# Instalar pdoc
pip install pdoc

# Generar docs
pdoc src/domain src/application --output-dir docs/api

# Ver en navegador
open docs/api/index.html
```

## Estructura

```
domain/
├── entities/       # ProfesorEntity, GuardiaEntity, etc.
├── value_objects/  # Email, Turno, HorasContrato
├── repositories/   # Protocols/Interfaces
└── schemas/        # Pydantic schemas

application/
├── use_cases/      # 12 casos de uso
└── dtos/           # Data Transfer Objects
```

---

**Nota**: La generación automática con pdoc tiene conflictos con Pydantic 2.0.  
Documentación manual disponible en ARCHITECTURE.md y TECHNICAL_GUIDE.md.

