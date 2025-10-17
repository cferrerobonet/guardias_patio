# Documentación de Desarrollo

Información técnica para desarrolladores, administradores del sistema y colaboradores del proyecto.

## 📚 Contenido

### [Guía de Desarrollo](guia-desarrollo.md)
Guía completa para configurar el entorno y contribuir al proyecto:
- Requisitos del sistema (Python 3.9+, PyQt6, SQLAlchemy)
- Instalación y setup del proyecto
- Arquitectura de la aplicación
- Convenciones de código
- Cómo contribuir (issues, pull requests)
- Ejecución de tests

**Ideal para**: Nuevos desarrolladores y contribuidores

### [Solución PyQt6](solucion-pyqt6.md)
Problemas comunes con PyQt6 y sus soluciones:
- Errores de instalación en diferentes plataformas
- Conflictos de dependencias
- Problemas de visualización
- Incompatibilidades con versiones de Python

**Ideal para**: Setup inicial, troubleshooting

### [Solución Duplicados de Guardias](solucion-duplicados.md)
Fix para el problema de guardias duplicadas:
- Descripción del bug
- Causa raíz del problema
- Solución implementada
- Prevención de futuros duplicados
- Migración de datos afectados

**Ideal para**: Debugging, mantenimiento

### [Limpieza del Proyecto y .gitignore](limpieza-gitignore.md)
Estrategia de gestión de archivos en Git:
- Qué archivos ignorar y por qué
- Política de preservación de datos
- Estructura de archivos regenerables
- Mejores prácticas de versionado
- Limpieza de archivos temporales

**Ideal para**: Configuración de Git, mantenimiento del repo

### [Plan de Reorganización de Docs](plan-reorganizacion-docs.md)
Proceso de reorganización de la documentación:
- Estado anterior (50 archivos desorganizados)
- Análisis de archivos obsoletos y duplicados
- Nueva estructura escalable
- Consolidación de contenidos
- Migración ejecutada

**Ideal para**: Entender la estructura actual de docs

### [README Original](readme-original.md)
Versión histórica del README de documentación antes de la reorganización.

**Ideal para**: Referencia histórica

## 🎯 Público Objetivo

Esta sección está diseñada para:
- 👨‍💻 Desarrolladores del proyecto
- 🔧 Administradores del sistema
- 🤝 Colaboradores externos
- 🆕 Nuevos miembros del equipo

## 🚀 Primeros Pasos para Desarrolladores

### Setup Inicial

1. **Lee primero**: [Guía de Desarrollo](guia-desarrollo.md) - Sección "Instalación"
2. **Configura**: Sigue los pasos de setup del entorno
3. **Soluciona problemas**: Consulta [Solución PyQt6](solucion-pyqt6.md) si encuentras errores
4. **Familiarízate**: Lee la arquitectura del proyecto en la Guía de Desarrollo

### Contribuir al Proyecto

1. **Lee**: [Guía de Desarrollo](guia-desarrollo.md) - Sección "Cómo Contribuir"
2. **Explora**: Revisa los issues abiertos en GitHub
3. **Crea**: Fork del repositorio y trabaja en tu feature branch
4. **Prueba**: Ejecuta todos los tests antes de hacer PR
5. **Documenta**: Actualiza documentación relevante

## 🔧 Stack Técnico

- **Lenguaje**: Python 3.9+
- **GUI**: PyQt6 6.7.0
- **Base de Datos**: SQLite con SQLAlchemy
- **Migraciones**: Alembic
- **Testing**: pytest
- **Linting**: Ruff
- **Control de Versiones**: Git

## 📦 Estructura del Proyecto

```
guardias-patio/
├── src/
│   ├── main.py                 # Punto de entrada
│   ├── database/               # DB manager
│   ├── models/                 # Modelos SQLAlchemy
│   ├── services/               # Lógica de negocio
│   ├── widgets/                # Componentes UI
│   └── utils/                  # Utilidades
├── tests/                      # Suite de tests
├── alembic/                    # Migraciones DB
├── documentacion/              # Docs (esta carpeta)
└── scripts/                    # Scripts auxiliares
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=src tests/

# Solo un archivo
pytest tests/test_asignador.py
```

## 📊 Estado del Desarrollo

### Versión Actual: v2.6.1

**Últimas Implementaciones**:
- ✅ Zona preferida para profesores (v2.6.1)
- ✅ Sistema de gestión de ausencias (v2.5)
- ✅ Vista de calendario mensual (v2.5)
- ✅ Importación/Exportación JSON (v2.4)

**En Desarrollo**:
- 🔄 Mejoras en UI (v2.7)
- 🔄 Optimizaciones de rendimiento (v2.7)

Ver [Roadmap v3.0](../roadmap/roadmap-v3.0.md) para planificación futura.

## 🐛 Problemas Conocidos

### Resueltos
- ✅ Duplicados en guardias → Ver [Solución Duplicados](solucion-duplicados.md)
- ✅ Turno mixto no visible → Fix en v2.6
- ✅ PyQt6 installation issues → Ver [Solución PyQt6](solucion-pyqt6.md)

### Abiertos
Consulta [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues) para lista actualizada.

## 💡 Mejores Prácticas

### Código
- Seguir PEP 8 (enforced por Ruff)
- Tipado estático donde sea posible
- Docstrings en funciones públicas
- Tests para nuevas features

### Git
- Commits atómicos y descriptivos
- Feature branches para nuevas funcionalidades
- Pull requests con descripción clara
- Code review antes de merge a main

### Documentación
- Actualizar docs con cada feature nueva
- Mantener CHANGELOG.md actualizado
- Incluir ejemplos prácticos
- Screenshots donde aplique

## 🔗 Ver También

- [Características del Sistema](../tecnico/caracteristicas-sistema.md) - Especificaciones técnicas
- [Versiones](../versiones/) - Historial de cambios detallado
- [Roadmap](../roadmap/roadmap-v3.0.md) - Planificación futura

## 📞 Contacto

- **Issues**: [GitHub Issues](https://github.com/tu-repo/guardias-patio/issues)
- **Discussions**: [GitHub Discussions](https://github.com/tu-repo/guardias-patio/discussions)
- **Email**: dev@colegio.edu

---

[← Volver al índice principal](../README.md)
