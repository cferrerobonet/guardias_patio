# Guía de Contribución - Guardias de Patio

## 📋 Índice

1. [Bienvenida](#bienvenida)
2. [Configuración del Entorno](#configuración-del-entorno)
3. [Flujo de Trabajo Git](#flujo-de-trabajo-git)
4. [Estándares de Código](#estándares-de-código)
5. [Testing](#testing)
6. [Documentación](#documentación)
7. [Proceso de Pull Request](#proceso-de-pull-request)
8. [Añadir Nuevas Funcionalidades](#añadir-nuevas-funcionalidades)
9. [FAQ](#faq)

---

## 👋 Bienvenida

¡Gracias por tu interés en contribuir a **Guardias de Patio**! Este documento te guiará en el proceso de configuración, desarrollo y envío de contribuciones.

### Valores del Proyecto

- ✅ **Calidad sobre velocidad**: Preferimos código bien testeado y documentado
- ✅ **Clean Architecture**: Separación de responsabilidades
- ✅ **Testing exhaustivo**: Mínimo 70% de cobertura
- ✅ **Comunicación clara**: Issues y PRs descriptivos

---

## 🛠️ Configuración del Entorno

### Prerrequisitos

- **Python**: 3.9 o superior
- **Git**: 2.30 o superior
- **Sistema Operativo**: macOS, Linux o Windows

### 1. Fork y Clonar el Repositorio

```bash
# 1. Haz fork del repositorio en GitHub
# 2. Clona tu fork localmente
git clone https://github.com/TU_USUARIO/guardias-patio.git
cd guardias-patio

# 3. Añade el repositorio original como "upstream"
git remote add upstream https://github.com/REPO_ORIGINAL/guardias-patio.git
```

### 2. Crear Entorno Virtual

```bash
# Crear entorno virtual
python3 -m venv .venv

# Activar entorno (macOS/Linux)
source .venv/bin/activate

# Activar entorno (Windows)
.venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Instalar dependencias principales
pip install -r requirements.txt

# Instalar dependencias de desarrollo
pip install pytest pytest-cov pytest-qt pytest-mock

# Instalar herramientas de profiling (opcional)
pip install snakeviz memory-profiler line-profiler
```

### 4. Configurar Base de Datos

```bash
# Aplicar migraciones
alembic upgrade head

# Verificar que la BD se creó correctamente
ls -lh guardias_patio.db
```

### 5. Verificar Instalación

```bash
# Ejecutar tests
pytest

# Debe mostrar algo como:
# ===== 94 passed in 5.23s =====

# Ejecutar aplicación
python src/main.py
```

---

## 🔀 Flujo de Trabajo Git

### Estructura de Ramas

```
main (producción)
  │
  ├─── develop (desarrollo principal)
  │     │
  │     ├─── feature/nueva-funcionalidad
  │     ├─── bugfix/corregir-error
  │     └─── refactor/mejorar-codigo
  │
  └─── hotfix/arreglo-urgente
```

### Crear una Nueva Rama

```bash
# Actualizar tu repositorio local
git checkout develop
git pull upstream develop

# Crear rama para tu feature/bugfix
git checkout -b feature/nombre-descriptivo

# Ejemplos:
git checkout -b feature/validador-dni
git checkout -b bugfix/corregir-asignacion-guardias
git checkout -b refactor/mejorar-repositorios
```

### Nomenclatura de Ramas

| Tipo | Prefijo | Ejemplo | Uso |
|------|---------|---------|-----|
| **Feature** | `feature/` | `feature/validador-email` | Nueva funcionalidad |
| **Bugfix** | `bugfix/` | `bugfix/fix-duplicados-guardias` | Corrección de bug |
| **Hotfix** | `hotfix/` | `hotfix/critical-db-error` | Fix urgente en producción |
| **Refactor** | `refactor/` | `refactor/improve-repositories` | Mejora de código sin cambio funcional |
| **Docs** | `docs/` | `docs/update-readme` | Solo documentación |
| **Test** | `test/` | `test/add-validator-tests` | Solo tests |

### Commits Semánticos

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Formato
<tipo>(<alcance>): <descripción corta>

<cuerpo opcional>

<footer opcional>
```

#### Tipos de Commit

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `feat` | Nueva funcionalidad | `feat(validadores): añadir validador de DNI` |
| `fix` | Corrección de bug | `fix(guardias): corregir duplicados en asignación` |
| `docs` | Cambios en documentación | `docs(readme): actualizar instrucciones de instalación` |
| `style` | Formato, espacios (no afecta lógica) | `style(ui): ajustar espaciado en formularios` |
| `refactor` | Refactorización (sin cambio funcional) | `refactor(repos): mejorar mappers de entidades` |
| `test` | Añadir o modificar tests | `test(validadores): añadir tests para Email` |
| `perf` | Mejora de performance | `perf(db): añadir índices a tabla guardias` |
| `chore` | Tareas de mantenimiento | `chore(deps): actualizar dependencias` |

#### Ejemplos de Commits

```bash
# Feature
git commit -m "feat(validadores): añadir ValidadorDNI con validación NIF/NIE

- Implementa validación de letra de control
- Soporta formato con y sin guiones
- Añade tests con 95% cobertura"

# Bugfix
git commit -m "fix(asignador): evitar asignar más de una guardia por día

Cierra #142"

# Refactor
git commit -m "refactor(repos): extraer lógica de mapeo a ProfesorMapper"

# Docs
git commit -m "docs(arquitectura): añadir diagrama de capas Clean Architecture"
```

### Mantener Tu Rama Actualizada

```bash
# Periódicamente, actualiza desde upstream
git checkout develop
git pull upstream develop

# Rebase tu rama sobre develop actualizado
git checkout feature/tu-feature
git rebase develop

# Si hay conflictos, resuélvelos y continúa
git add .
git rebase --continue
```

---

## 📝 Estándares de Código

### PEP 8 - Guía de Estilo

Seguimos [PEP 8](https://peps.python.org/pep-0008/) con algunas adaptaciones:

#### Longitud de Línea

```python
# ✅ BIEN: 88 caracteres máximo (black default)
def crear_profesor(nombre: str, email: str, horas: float) -> Profesor:
    return Profesor(nombre, email, horas)

# ❌ MAL: Línea muy larga
def crear_profesor_con_toda_la_informacion_completa_en_el_nombre(nombre_completo_del_profesor: str, email_corporativo_institucional: str, horas_de_contrato_semanales: float) -> Profesor:
```

#### Indentación

```python
# ✅ BIEN: 4 espacios
def funcion():
    if condicion:
        hacer_algo()
        
# ❌ MAL: Tabs o 2 espacios
def funcion():
  if condicion:
      hacer_algo()
```

#### Imports

```python
# ✅ BIEN: Ordenados y agrupados
# 1. Standard library
import os
from datetime import datetime
from typing import List, Optional

# 2. Third-party
from sqlalchemy import Column, Integer, String
from PyQt6.QtWidgets import QWidget

# 3. Local
from src.domain.entities import ProfesorEntity
from src.application.dtos import ProfesorDTO

# ❌ MAL: Desordenados
from src.domain.entities import ProfesorEntity
import os
from PyQt6.QtWidgets import QWidget
from datetime import datetime
```

### Type Hints

Siempre usa type hints en funciones públicas:

```python
# ✅ BIEN: Type hints completos
def crear_profesor(
    nombre: str,
    email: str,
    horas_contrato: float,
    tutor: bool = False
) -> ProfesorEntity:
    """Crea un nuevo profesor."""
    return ProfesorEntity(nombre, email, horas_contrato, tutor)

# ✅ BIEN: Type hints para listas y opcionales
def obtener_profesores(
    activos: bool = True
) -> List[ProfesorEntity]:
    """Obtiene lista de profesores."""
    pass

def buscar_profesor(id: int) -> Optional[ProfesorEntity]:
    """Busca profesor por ID. Devuelve None si no existe."""
    pass

# ❌ MAL: Sin type hints
def crear_profesor(nombre, email, horas_contrato, tutor=False):
    return ProfesorEntity(nombre, email, horas_contrato, tutor)
```

### Docstrings

Usa [Google Style Docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings):

```python
def calcular_guardias_pendientes(
    profesor_id: int,
    fecha_inicio: datetime,
    fecha_fin: datetime
) -> int:
    """Calcula las guardias pendientes de un profesor en un periodo.
    
    Args:
        profesor_id: ID del profesor.
        fecha_inicio: Fecha de inicio del periodo (inclusive).
        fecha_fin: Fecha de fin del periodo (inclusive).
        
    Returns:
        Número de guardias pendientes en el periodo.
        
    Raises:
        ValueError: Si fecha_fin es anterior a fecha_inicio.
        ProfesorNoEncontradoError: Si el profesor no existe.
        
    Example:
        >>> calcular_guardias_pendientes(1, date(2024,1,1), date(2024,1,31))
        5
    """
    if fecha_fin < fecha_inicio:
        raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
    
    # Implementación...
    return 5
```

### Nombres Descriptivos

```python
# ✅ BIEN: Nombres descriptivos
def calcular_distribucion_guardias(profesores: List[Profesor]) -> Dict[int, int]:
    guardias_por_profesor = {}
    for profesor in profesores:
        guardias_por_profesor[profesor.id] = calcular_guardias(profesor)
    return guardias_por_profesor

# ❌ MAL: Nombres crípticos
def calc_dist(profs: List[Profesor]) -> Dict[int, int]:
    gpd = {}
    for p in profs:
        gpd[p.id] = calc(p)
    return gpd
```

### Clean Code Principles

#### 1. Funciones Pequeñas

```python
# ✅ BIEN: Funciones enfocadas
def validar_email(email: str) -> bool:
    """Valida formato de email."""
    return "@" in email and "." in email.split("@")[1]

def validar_horas_contrato(horas: float) -> bool:
    """Valida que las horas sean positivas."""
    return 0 < horas <= 40

def validar_profesor(email: str, horas: float) -> bool:
    """Valida datos de profesor."""
    return validar_email(email) and validar_horas_contrato(horas)

# ❌ MAL: Función gigante que hace todo
def validar_profesor(email, horas, nombre, dni, ...):
    # 200 líneas de validaciones mezcladas
    pass
```

#### 2. DRY (Don't Repeat Yourself)

```python
# ✅ BIEN: Extraer lógica común
def formatear_nombre_profesor(nombre: str, apellidos: str) -> str:
    """Formatea nombre en formato APELLIDOS, Nombre."""
    return f"{apellidos.upper()}, {nombre.title()}"

profesor1 = formatear_nombre_profesor("Juan", "Pérez")
profesor2 = formatear_nombre_profesor("María", "García")

# ❌ MAL: Código duplicado
profesor1 = f"{apellidos1.upper()}, {nombre1.title()}"
profesor2 = f"{apellidos2.upper()}, {nombre2.title()}"
```

#### 3. Single Responsibility

```python
# ✅ BIEN: Cada clase una responsabilidad
class ProfesorRepository:
    """Solo maneja persistencia de profesores."""
    def guardar(self, profesor): pass
    def obtener(self, id): pass

class ValidadorProfesor:
    """Solo valida datos de profesores."""
    def validar(self, profesor): pass

# ❌ MAL: Clase que hace todo
class ProfesorManager:
    def guardar(self, profesor): pass
    def validar(self, profesor): pass
    def enviar_email(self, profesor): pass
    def generar_pdf(self, profesor): pass
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest tests/test_validadores_ui.py

# Con cobertura
pytest --cov=src --cov-report=html

# Solo tests rápidos (excluir lentos)
pytest -m "not slow"

# Ver output detallado
pytest -v
```

### Estructura de Tests

```python
# tests/test_validadores.py
import pytest
from src.domain.value_objects import Email

class TestEmail:
    """Suite de tests para Email value object."""
    
    def test_email_valido_acepta_formato_correcto(self):
        """Debe aceptar email con formato válido."""
        # Arrange
        email_str = "usuario@example.com"
        
        # Act
        email = Email(email_str)
        
        # Assert
        assert email.valor == email_str
    
    def test_email_sin_arroba_lanza_excepcion(self):
        """Debe rechazar email sin @."""
        # Arrange
        email_invalido = "usuario.example.com"
        
        # Act & Assert
        with pytest.raises(ValueError, match="Email inválido"):
            Email(email_invalido)
    
    @pytest.mark.parametrize("email_invalido", [
        "sin_arroba",
        "@sin_usuario",
        "usuario@",
        "usuario@@doble.com",
    ])
    def test_emails_invalidos(self, email_invalido):
        """Debe rechazar emails con formato inválido."""
        with pytest.raises(ValueError):
            Email(email_invalido)
```

### Fixtures

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.models.models import Base

@pytest.fixture
def db_session():
    """Crea sesión de BD en memoria para tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()

@pytest.fixture
def profesor_ejemplo():
    """Fixture con profesor de ejemplo."""
    from src.domain.entities import ProfesorEntity
    from src.domain.value_objects import Email, HorasContrato
    
    return ProfesorEntity(
        id=None,
        nombre_completo="PÉREZ, Juan",
        email_corporativo=Email("juan.perez@school.edu"),
        horas_contrato=HorasContrato(25.0),
        tutor=False
    )
```

### Mocking

```python
# tests/test_use_cases.py
import pytest
from unittest.mock import Mock
from src.application.use_cases import CrearProfesor
from src.application.dtos import CrearProfesorDTO

def test_crear_profesor_llama_repository():
    """Debe llamar al repositorio para persistir."""
    # Arrange
    mock_repo = Mock()
    mock_repo.guardar.return_value = Mock(id=1)
    use_case = CrearProfesor(mock_repo)
    dto = CrearProfesorDTO(
        nombre_completo="PÉREZ, Juan",
        email_corporativo="juan@school.edu",
        horas_contrato=25.0,
        tutor=False
    )
    
    # Act
    resultado = use_case.execute(dto)
    
    # Assert
    assert resultado.id == 1
    mock_repo.guardar.assert_called_once()
```

### Cobertura Mínima

- **Domain**: 90%+ (lógica crítica)
- **Application**: 80%+ (use cases)
- **Infrastructure**: 70%+ (repositorios)
- **Presentation**: 30%+ (UI es difícil de testear)

```bash
# Generar reporte de cobertura
pytest --cov=src --cov-report=html

# Ver reporte en navegador
open htmlcov/index.html
```

---

## 📚 Documentación

### README.md

- Mantener instrucciones de instalación actualizadas
- Añadir screenshots de nuevas features
- Documentar requisitos del sistema

### Docstrings

Toda función pública debe tener docstring:

```python
def calcular_guardias_mensuales(
    profesor_id: int,
    mes: int,
    año: int
) -> int:
    """Calcula las guardias de un profesor en un mes específico.
    
    Args:
        profesor_id: ID del profesor.
        mes: Mes (1-12).
        año: Año (formato YYYY).
        
    Returns:
        Número de guardias en el mes.
        
    Raises:
        ValueError: Si mes no está entre 1-12.
        ProfesorNoEncontradoError: Si el profesor no existe.
    """
    pass
```

### Documentación Técnica

Para cambios arquitectónicos significativos:

```bash
# Crear documento en documentacion/
touch documentacion/NUEVA_FUNCIONALIDAD.md

# Contenido típico:
# 1. Contexto y motivación
# 2. Diseño propuesto
# 3. Alternativas consideradas
# 4. Decisión final
# 5. Consecuencias
```

---

## 🔍 Proceso de Pull Request

### 1. Preparar el PR

```bash
# Asegúrate de que todo funciona
pytest
pytest --cov=src --cov-report=term

# Actualiza tu rama con develop
git checkout develop
git pull upstream develop
git checkout feature/tu-feature
git rebase develop

# Push a tu fork
git push origin feature/tu-feature
```

### 2. Crear el PR en GitHub

**Título**: Usa formato de commit semántico

```
feat(validadores): añadir validador de DNI con NIF/NIE
```

**Descripción**: Usa esta plantilla

```markdown
## 📋 Descripción

Breve descripción de los cambios.

## 🎯 Motivación

¿Por qué es necesario este cambio?

## 🔧 Cambios Realizados

- [ ] Implementación de ValidadorDNI
- [ ] Tests con 95% cobertura
- [ ] Documentación actualizada
- [ ] Ejemplo de uso añadido

## 🧪 Tests

```bash
pytest tests/test_validador_dni.py -v
# 15 passed in 0.32s
```

## 📸 Screenshots (si aplica)

![Captura de pantalla](url)

## ✅ Checklist

- [x] Tests añadidos y pasando
- [x] Documentación actualizada
- [x] Sin conflictos con develop
- [x] Código sigue estándares del proyecto
- [x] Commits siguen Conventional Commits

## 🔗 Issues Relacionados

Cierra #123
Relacionado con #456
```

### 3. Code Review

**Espera feedback** del equipo:

- ✅ **Aprobar**: Merge automático
- ⚠️ **Request Changes**: Hacer ajustes y volver a pushear
- 💬 **Comment**: Responder dudas

**Responder a comentarios**:

```markdown
> ¿Por qué usaste este patrón?

Buena pregunta. Usé el patrón Repository porque permite...

Hice los cambios sugeridos en commit abc1234.
```

### 4. Merge

Una vez aprobado:

```bash
# El maintainer hará merge con squash
# (todos los commits se combinan en uno)

# Después, actualiza tu fork
git checkout develop
git pull upstream develop
git push origin develop

# Elimina la rama local
git branch -d feature/tu-feature

# Elimina la rama remota
git push origin --delete feature/tu-feature
```

---

## ➕ Añadir Nuevas Funcionalidades

### Ejemplo Completo: Añadir Validador de DNI

#### Paso 1: Crear Issue

```markdown
**Título**: Añadir validador de DNI (NIF/NIE)

**Descripción**:
Necesitamos validar DNI/NIF/NIE españoles en el formulario de profesores.

**Requisitos**:
- [ ] Validar formato: 12345678A o X1234567A
- [ ] Validar letra de control
- [ ] Soportar formatos con/sin guiones
- [ ] Tests con 90%+ cobertura

**Aceptación**:
- El validador rechaza DNIs inválidos
- El validador acepta DNIs válidos
- La UI muestra error en tiempo real
```

#### Paso 2: Crear Rama

```bash
git checkout develop
git pull upstream develop
git checkout -b feature/validador-dni
```

#### Paso 3: Implementar Domain (Value Object)

```python
# src/domain/value_objects/dni.py
from typing import Optional

class DNI:
    """Value Object para DNI español (NIF/NIE)."""
    
    LETRAS = "TRWAGMYFPDXBNJZSQVHLCKE"
    
    def __init__(self, valor: str):
        """Crea DNI validando formato y letra.
        
        Args:
            valor: DNI en formato 12345678A o X1234567A.
            
        Raises:
            ValueError: Si el formato es inválido.
        """
        valor_limpio = valor.replace("-", "").replace(" ", "").upper()
        
        if not self._es_formato_valido(valor_limpio):
            raise ValueError(f"Formato de DNI inválido: {valor}")
        
        if not self._es_letra_valida(valor_limpio):
            raise ValueError(f"Letra de control inválida: {valor}")
        
        self._valor = valor_limpio
    
    @staticmethod
    def _es_formato_valido(dni: str) -> bool:
        """Valida formato 8 dígitos + letra o X + 7 dígitos + letra."""
        if len(dni) != 9:
            return False
        
        if dni[0].isdigit():
            return dni[:8].isdigit() and dni[8].isalpha()
        elif dni[0] in "XYZ":
            return dni[1:8].isdigit() and dni[8].isalpha()
        else:
            return False
    
    @staticmethod
    def _es_letra_valida(dni: str) -> bool:
        """Valida letra de control."""
        numero_str = dni[:8]
        if dni[0] in "XYZ":
            numero_str = str("XYZ".index(dni[0])) + dni[1:8]
        
        numero = int(numero_str)
        letra_calculada = DNI.LETRAS[numero % 23]
        return dni[8] == letra_calculada
    
    @property
    def valor(self) -> str:
        """Devuelve DNI sin formato."""
        return self._valor
    
    def formateado(self) -> str:
        """Devuelve DNI con formato 12345678-A."""
        return f"{self._valor[:8]}-{self._valor[8]}"
    
    def __str__(self) -> str:
        return self.formateado()
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, DNI):
            return False
        return self._valor == other._valor
```

#### Paso 4: Tests Domain

```python
# tests/test_dni.py
import pytest
from src.domain.value_objects import DNI

class TestDNI:
    """Tests para value object DNI."""
    
    def test_dni_valido_con_formato_correcto(self):
        """Debe aceptar DNI válido."""
        dni = DNI("12345678Z")
        assert dni.valor == "12345678Z"
    
    def test_dni_valido_con_guiones(self):
        """Debe aceptar DNI con guiones."""
        dni = DNI("12345678-Z")
        assert dni.valor == "12345678Z"
    
    def test_nie_valido_con_x(self):
        """Debe aceptar NIE con X."""
        dni = DNI("X1234567L")
        assert dni.valor == "X1234567L"
    
    @pytest.mark.parametrize("dni_invalido,motivo", [
        ("1234567", "muy corto"),
        ("123456789", "sin letra"),
        ("1234567AA", "dos letras"),
        ("12345678A", "letra incorrecta"),
        ("ABCDEFGHI", "sin números"),
    ])
    def test_dni_invalido_lanza_excepcion(self, dni_invalido, motivo):
        """Debe rechazar DNI inválido."""
        with pytest.raises(ValueError):
            DNI(dni_invalido)
    
    def test_formateado_devuelve_con_guion(self):
        """Debe formatear con guion."""
        dni = DNI("12345678Z")
        assert dni.formateado() == "12345678-Z"
    
    def test_igualdad_entre_dnis(self):
        """Dos DNIs con mismo valor deben ser iguales."""
        dni1 = DNI("12345678Z")
        dni2 = DNI("12345678-Z")
        assert dni1 == dni2

# Ejecutar
# pytest tests/test_dni.py -v
```

#### Paso 5: Implementar UI (Widget Validador)

```python
# src/widgets/validadores_ui.py (añadir a archivo existente)

class ValidadorDNI(ValidadorCampo):
    """Widget de validación de DNI/NIE."""
    
    def __init__(self, parent=None, requerido: bool = True):
        super().__init__(parent, requerido)
        self.setPlaceholderText("12345678-Z o X1234567-L")
    
    def validar_inmediato(self, texto: str) -> Tuple[bool, Optional[str]]:
        """Valida DNI en tiempo real."""
        if not texto and not self.requerido:
            return (True, None)
        
        if not texto:
            return (False, "⚠️ El DNI es obligatorio")
        
        try:
            DNI(texto)
            return (True, None)
        except ValueError as e:
            return (False, f"❌ {str(e)}")
    
    def obtener_valor(self) -> Optional[DNI]:
        """Devuelve value object DNI."""
        texto = self.text().strip()
        if not texto:
            return None
        return DNI(texto)
```

#### Paso 6: Tests UI

```python
# tests/test_validadores_ui.py (añadir)

class TestValidadorDNI:
    """Tests para ValidadorDNI widget."""
    
    def test_dni_valido_muestra_tick_verde(self, qtbot):
        """Debe mostrar tick verde con DNI válido."""
        validador = ValidadorDNI()
        qtbot.addWidget(validador)
        
        validador.setText("12345678Z")
        
        assert validador.es_valido()
        assert validador.icono_estado.pixmap().toImage() == # icono verde
    
    def test_dni_invalido_muestra_cruz_roja(self, qtbot):
        """Debe mostrar cruz roja con DNI inválido."""
        validador = ValidadorDNI()
        qtbot.addWidget(validador)
        
        validador.setText("12345678A")  # Letra incorrecta
        
        assert not validador.es_valido()
        # Verificar que muestra error
    
    def test_obtener_valor_devuelve_value_object(self, qtbot):
        """Debe devolver value object DNI."""
        validador = ValidadorDNI()
        qtbot.addWidget(validador)
        validador.setText("12345678Z")
        
        dni = validador.obtener_valor()
        
        assert isinstance(dni, DNI)
        assert dni.valor == "12345678Z"
```

#### Paso 7: Integrar en Formulario

```python
# src/presentation/forms/profesor_form.py (modificar)

class ProfesorForm(QWidget):
    def _init_ui(self):
        # ... código existente ...
        
        # Añadir validador de DNI
        self.txt_dni = ValidadorDNI(requerido=False)
        self.txt_dni.setToolTip("DNI/NIF/NIE del profesor (opcional)")
        
        form_layout.addRow("DNI:", self.txt_dni)
```

#### Paso 8: Actualizar Documentación

```markdown
# documentacion/VALIDADORES.md (crear o actualizar)

## ValidadorDNI

Valida DNI/NIF/NIE español con letra de control.

**Formatos aceptados**:
- `12345678Z` (NIF)
- `12345678-Z` (con guion)
- `X1234567L` (NIE)

**Validación**:
- ✅ Formato 8 dígitos + letra
- ✅ Letra de control correcta
- ✅ Soporta NIE (X, Y, Z)

**Uso**:
```python
validador = ValidadorDNI(requerido=False)
layout.addWidget(validador)

# Obtener valor
dni = validador.obtener_valor()  # Devuelve DNI value object
```
```

#### Paso 9: Commit y Push

```bash
# Añadir archivos
git add src/domain/value_objects/dni.py
git add src/widgets/validadores_ui.py
git add tests/test_dni.py
git add tests/test_validadores_ui.py
git add documentacion/VALIDADORES.md

# Commit semántico
git commit -m "feat(validadores): añadir ValidadorDNI con NIF/NIE

- Implementa value object DNI con validación de letra
- Soporta formatos con/sin guiones
- Añade widget ValidadorDNI para UI
- Tests con 95% cobertura
- Documentación en VALIDADORES.md"

# Push a tu fork
git push origin feature/validador-dni
```

#### Paso 10: Crear Pull Request

Ver [Proceso de Pull Request](#-proceso-de-pull-request)

---

## ❓ FAQ

### ¿Cómo añado una nueva dependencia?

```bash
# Instalar
pip install nueva-libreria

# Añadir a requirements.txt
pip freeze | grep nueva-libreria >> requirements.txt

# Documentar en PR por qué es necesaria
```

### ¿Cómo depuro la aplicación?

```python
# Añadir breakpoint
import pdb; pdb.set_trace()

# O usar logging
from src.core.logging import logger
logger.debug(f"Valor de variable: {variable}")
```

### ¿Cómo ejecuto solo un test?

```bash
# Un archivo
pytest tests/test_validadores.py

# Una clase
pytest tests/test_validadores.py::TestEmail

# Un test específico
pytest tests/test_validadores.py::TestEmail::test_email_valido
```

### ¿Qué hago si mis tests fallan en CI pero pasan local?

```bash
# Ejecutar en modo estricto como CI
pytest --strict-markers

# Verificar versiones de dependencias
pip list

# Recrear entorno desde cero
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

### ¿Cómo cambio la base de datos de SQLite a PostgreSQL?

```python
# Solo cambiar DATABASE_URL en .env
DATABASE_URL=postgresql://user:pass@localhost/guardias_patio

# El código sigue igual gracias a SQLAlchemy
```

### ¿Dónde va la lógica de negocio?

**Domain Layer** (entidades y value objects):

```python
# ✅ CORRECTO: Lógica en domain
class ProfesorEntity:
    def puede_tener_guardias(self) -> bool:
        return self.horas_contrato >= 10

# ❌ INCORRECTO: Lógica en UI
class ProfesorForm:
    def verificar_guardias(self):
        if self.profesor.horas_contrato >= 10:
            ...
```

---

## 📞 Contacto

- **Issues**: https://github.com/REPO/guardias-patio/issues
- **Discussions**: https://github.com/REPO/guardias-patio/discussions
- **Email**: tu-email@example.com

---

## ✅ Checklist Final

Antes de enviar tu PR, verifica:

- [ ] ✅ Tests añadidos y pasando (pytest)
- [ ] ✅ Cobertura mínima cumplida (pytest --cov)
- [ ] ✅ Código sigue PEP 8
- [ ] ✅ Type hints en funciones públicas
- [ ] ✅ Docstrings en clases y funciones
- [ ] ✅ Sin conflictos con develop
- [ ] ✅ Commits siguen Conventional Commits
- [ ] ✅ Documentación actualizada
- [ ] ✅ CHANGELOG.md actualizado (si aplica)

---

**¡Gracias por contribuir a Guardias de Patio!** 🎉

Tu tiempo y esfuerzo ayudan a mejorar la gestión de guardias escolares para todos. Si tienes dudas, no dudes en abrir un issue o discussion.

---

**Última actualización**: 19 de octubre de 2025  
**Versión**: 1.0
