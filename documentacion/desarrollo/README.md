# Documentación para Desarrolladores

Esta carpeta contiene documentación técnica dirigida a desarrolladores que trabajan en el proyecto **Guardias de Patio**.

---

## 📚 Contenido

### 📖 Guías de Desarrollo

- **[CONTRIBUIR.md](CONTRIBUIR.md)**: Cómo contribuir al proyecto
  - Estándares de código
  - Proceso de desarrollo
  - Guía de commits
  - Pull requests

- **[HISTORIA_SPRINTS.md](HISTORIA_SPRINTS.md)**: Historial de sprints de desarrollo
  - Evolución del proyecto
  - Decisiones técnicas
  - Lecciones aprendidas

- **[PLAN_HOMOGENEIZACION_FORMULARIOS.md](PLAN_HOMOGENEIZACION_FORMULARIOS.md)**: Plan de estandarización de UI
  - Patrón de estilos
  - Componentes reutilizables
  - Guía de implementación

---

## 🏗️ Arquitectura

Para información sobre la arquitectura del proyecto, consulta:
- `../tecnico/ARCHITECTURE_PATTERNS.md` - Patrones arquitectónicos
- `../tecnico/ALGORITMO_PASADA_6.md` - Algoritmo de distribución de guardias

---

## 🧪 Testing

Para documentación sobre pruebas y validaciones:
- `../validaciones/` - Validaciones de negocio
- `../../tests/` - Tests del proyecto

---

## 🔧 Herramientas de Desarrollo

### Scripts Útiles

Ver `../../scripts/` para scripts de desarrollo y análisis:
- Profiling de rendimiento
- Análisis de queries
- Generación de reportes

### Compilación y Distribución

Ver `../build/` para:
- Compilación de la aplicación
- Creación de instaladores
- Solución de problemas

---

## 📝 Estándares de Código

### Python

- **Estilo:** PEP 8
- **Linter:** Ruff
- **Type checking:** MyPy
- **Imports:** isort

### Commits

Seguir **Conventional Commits**:
```
<tipo>(<alcance>): <descripción>

[cuerpo opcional]

[footer opcional]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `style`: Formateo de código
- `refactor`: Refactorización
- `test`: Tests
- `chore`: Tareas de mantenimiento

---

## 🚀 Flujo de Desarrollo

1. **Crear rama** desde `main`:
   ```bash
   git checkout -b feature/nombre-funcionalidad
   ```

2. **Desarrollar** siguiendo estándares

3. **Tests**: Verificar que los tests pasan
   ```bash
   pytest
   ```

4. **Commit** con mensaje descriptivo

5. **Push** y crear **Pull Request**

6. **Review** y merge a `main`

---

## 📦 Estructura del Proyecto

```
guardias_patio/
├── src/                    # Código fuente
│   ├── application/        # Casos de uso
│   ├── core/               # Núcleo del sistema
│   ├── infrastructure/     # Repositorios y BD
│   ├── models/             # Modelos de datos
│   ├── presentation/       # UI (PyQt6)
│   ├── services/           # Servicios de negocio
│   ├── sync/               # Sincronización SFTP
│   └── utils/              # Utilidades
├── tests/                  # Tests
├── scripts/                # Scripts de utilidad
├── documentacion/          # Documentación
└── ...
```

---

## 🔗 Enlaces Útiles

- **Repositorio:** https://github.com/cferrerobonet/guardias_patio
- **Issues:** https://github.com/cferrerobonet/guardias_patio/issues
- **Releases:** https://github.com/cferrerobonet/guardias_patio/releases

---

**Última actualización:** 28 de octubre de 2025  
**Versión:** 2.9.0
