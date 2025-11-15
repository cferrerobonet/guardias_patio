# Scripts de Automatización - Plan de Refactorización v3.0

Este documento contiene scripts útiles para ejecutar las tareas del plan de refactorización.

---

## 📊 Scripts de Análisis

### 1. Análisis de Complejidad

```bash
#!/bin/bash
# scripts/analyze_complexity.sh

echo "Analizando complejidad del código..."
pip install radon

# Complejidad ciclomática
radon cc src/ -a -s

# Complejidad de mantenibilidad
radon mi src/ -s

# Identificar archivos problemáticos
radon cc src/ -a -s | grep -E "(A|B|C|D|E|F)" | head -20
```

### 2. Análisis de Duplicación

```bash
#!/bin/bash
# scripts/analyze_duplication.sh

echo "Buscando código duplicado..."
pip install duplic detector

# Buscar duplicados
pylint --disable=all --enable=duplicate-code src/

# O usar jscpd (más visual)
npm install -g jscpd
jscpd src/ --min-lines 10 --min-tokens 50
```

### 3. Análisis de Dependencias

```bash
#!/bin/bash
# scripts/analyze_dependencies.sh

echo "Analizando dependencias..."
pip install pydeps

# Generar gráfico de dependencias
pydeps src/services/asignador_guardias.py --max-bacon 2 -o deps.svg

# Detectar imports circulares
pydeps src/ --show-cycles
```

### 4. Métricas de Código

```python
#!/usr/bin/env python3
# scripts/code_metrics.py

import os
from pathlib import Path
from collections import defaultdict

def analyze_project():
    stats = {
        'total_files': 0,
        'total_lines': 0,
        'large_files': [],
        'files_by_size': defaultdict(int)
    }
    
    for py_file in Path('src').rglob('*.py'):
        with open(py_file) as f:
            lines = len(f.readlines())
            
        stats['total_files'] += 1
        stats['total_lines'] += lines
        
        if lines > 500:
            stats['large_files'].append((str(py_file), lines))
            
        if lines < 100:
            stats['files_by_size']['< 100'] += 1
        elif lines < 300:
            stats['files_by_size']['100-300'] += 1
        elif lines < 500:
            stats['files_by_size']['300-500'] += 1
        else:
            stats['files_by_size']['> 500'] += 1
    
    print("=" * 60)
    print("MÉTRICAS DEL PROYECTO")
    print("=" * 60)
    print(f"Total archivos: {stats['total_files']}")
    print(f"Total líneas: {stats['total_lines']:,}")
    print(f"Promedio líneas/archivo: {stats['total_lines'] / stats['total_files']:.1f}")
    print()
    print("Distribución por tamaño:")
    for size, count in sorted(stats['files_by_size'].items()):
        print(f"  {size:15s}: {count:3d} archivos")
    print()
    print("Archivos grandes (> 500 líneas):")
    for file, lines in sorted(stats['large_files'], key=lambda x: x[1], reverse=True):
        print(f"  {lines:4d} líneas: {file}")

if __name__ == '__main__':
    analyze_project()
```

---

## 🧪 Scripts de Testing

### 1. Ejecutar Tests con Coverage

```bash
#!/bin/bash
# scripts/run_tests_coverage.sh

echo "Ejecutando tests con coverage..."

# Coverage completo
pytest \
    --cov=src \
    --cov-report=html \
    --cov-report=term-missing \
    --cov-report=xml \
    -v

# Abrir reporte HTML
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
```

### 2. Tests por Módulo

```bash
#!/bin/bash
# scripts/test_module.sh

MODULE=${1:-""}

if [ -z "$MODULE" ]; then
    echo "Uso: ./test_module.sh <module>"
    echo "Ejemplo: ./test_module.sh domain"
    exit 1
fi

pytest tests/${MODULE}/ -v --cov=src/${MODULE}/ --cov-report=term
```

### 3. Tests de Performance

```bash
#!/bin/bash
# scripts/benchmark_tests.sh

echo "Ejecutando benchmarks..."

pytest tests/performance/ \
    --benchmark-only \
    --benchmark-sort=mean \
    --benchmark-autosave
```

### 4. Verificar Tests Rotos

```bash
#!/bin/bash
# scripts/check_broken_tests.sh

echo "Verificando tests rotos..."

# Ejecutar tests y capturar fallos
pytest --tb=no -q > /tmp/test_results.txt 2>&1

if grep -q "FAILED" /tmp/test_results.txt; then
    echo "❌ Tests fallidos encontrados:"
    grep "FAILED" /tmp/test_results.txt
    exit 1
else
    echo "✅ Todos los tests pasan"
    exit 0
fi
```

---

## 🔍 Scripts de Linting y Formatting

### 1. Format Code

```bash
#!/bin/bash
# scripts/format_code.sh

echo "Formateando código..."

# Black
black src/ tests/

# isort
isort src/ tests/

# Autoflake (remover imports no usados)
autoflake \
    --remove-all-unused-imports \
    --remove-unused-variables \
    --in-place \
    --recursive \
    src/ tests/

echo "✅ Código formateado"
```

### 2. Lint Code

```bash
#!/bin/bash
# scripts/lint_code.sh

echo "Ejecutando linters..."

# flake8
echo "Running flake8..."
flake8 src/ --max-line-length=100 --extend-ignore=E203

# pylint
echo "Running pylint..."
pylint src/ --max-line-length=100

# mypy
echo "Running mypy..."
mypy src/ --strict

echo "✅ Linting completado"
```

### 3. Pre-commit Check

```bash
#!/bin/bash
# scripts/pre_commit_check.sh

echo "Ejecutando checks pre-commit..."

# Format
./scripts/format_code.sh

# Lint
./scripts/lint_code.sh

# Tests
pytest --tb=short -q

if [ $? -eq 0 ]; then
    echo "✅ Pre-commit checks pasados"
    exit 0
else
    echo "❌ Pre-commit checks fallidos"
    exit 1
fi
```

---

## 🔨 Scripts de Refactorización

### 1. Buscar y Reemplazar Imports

```python
#!/usr/bin/env python3
# scripts/refactor_imports.py

import os
import re
from pathlib import Path

def replace_imports(old_import, new_import):
    """Reemplaza imports en todos los archivos .py"""
    
    count = 0
    for py_file in Path('src').rglob('*.py'):
        with open(py_file, 'r') as f:
            content = f.read()
        
        if old_import in content:
            new_content = content.replace(old_import, new_import)
            
            with open(py_file, 'w') as f:
                f.write(new_content)
            
            count += 1
            print(f"✓ {py_file}")
    
    print(f"\n✅ {count} archivos actualizados")

if __name__ == '__main__':
    # Ejemplo: Unificar excepciones
    replace_imports(
        'from utils.exceptions import',
        'from core.exceptions import'
    )
```

### 2. Detectar Código Muerto

```python
#!/usr/bin/env python3
# scripts/detect_dead_code.py

import ast
from pathlib import Path
from collections import defaultdict

def analyze_dead_code():
    """Detecta funciones/clases que nunca se usan"""
    
    definitions = defaultdict(list)
    usages = defaultdict(int)
    
    # Primera pasada: recolectar definiciones
    for py_file in Path('src').rglob('*.py'):
        with open(py_file) as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        definitions['functions'].append((str(py_file), node.name))
                    elif isinstance(node, ast.ClassDef):
                        definitions['classes'].append((str(py_file), node.name))
            except:
                pass
    
    # Segunda pasada: buscar usos
    for py_file in Path('src').rglob('*.py'):
        with open(py_file) as f:
            content = f.read()
            for _, name in definitions['functions']:
                if name in content:
                    usages[name] += 1
            for _, name in definitions['classes']:
                if name in content:
                    usages[name] += 1
    
    # Reportar posible código muerto
    print("Posible código muerto (usado solo 1 vez = definición):")
    for file, name in definitions['functions']:
        if usages[name] <= 1:
            print(f"  función: {name:30s} en {file}")
    for file, name in definitions['classes']:
        if usages[name] <= 1:
            print(f"  clase:   {name:30s} en {file}")

if __name__ == '__main__':
    analyze_dead_code()
```

### 3. Dividir Archivo Grande

```python
#!/usr/bin/env python3
# scripts/split_large_file.py

import ast
from pathlib import Path

def split_file(file_path, output_dir):
    """Divide un archivo grande en módulos por clase/función"""
    
    with open(file_path) as f:
        tree = ast.parse(f.read())
    
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Crear __init__.py
    (output_dir / '__init__.py').touch()
    
    # Extraer cada clase a su archivo
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            module_name = node.name.lower() + '.py'
            module_path = output_dir / module_name
            
            # Aquí iría la lógica para extraer el código
            # Por ahora solo mostramos
            print(f"Extraer {node.name} → {module_path}")

if __name__ == '__main__':
    split_file(
        'src/services/asignador_guardias.py',
        'src/services/asignador/'
    )
```

---

## 📊 Scripts de Monitoreo

### 1. Monitor de Performance

```python
#!/usr/bin/env python3
# scripts/monitor_performance.py

import time
import psutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database.db_manager import initialize_user_database
from services.asignador_guardias_v3_simple import generar_guardias

def monitor_generation():
    """Monitorea generación de guardias"""
    
    engine, SessionFactory = initialize_user_database('Jefatura_FpBach')
    session = SessionFactory()
    
    # Métricas iniciales
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    cpu_before = process.cpu_percent()
    
    print("=" * 60)
    print("MONITOREO DE PERFORMANCE")
    print("=" * 60)
    print(f"Memoria inicial: {mem_before:.1f} MB")
    print(f"CPU inicial: {cpu_before:.1f}%")
    print()
    
    # Ejecutar generación
    start = time.time()
    resultado = generar_guardias(session)
    duration = time.time() - start
    
    # Métricas finales
    mem_after = process.memory_info().rss / 1024 / 1024
    cpu_after = process.cpu_percent()
    
    print("RESULTADOS:")
    print(f"Tiempo: {duration:.2f}s")
    print(f"Memoria final: {mem_after:.1f} MB")
    print(f"Memoria usada: {mem_after - mem_before:.1f} MB")
    print(f"CPU pico: {cpu_after:.1f}%")
    print(f"Cobertura: {resultado.get('cobertura', 0):.1f}%")
    print()
    
    session.close()

if __name__ == '__main__':
    monitor_generation()
```

### 2. Monitor de Queries

```python
#!/usr/bin/env python3
# scripts/monitor_queries.py

from sqlalchemy import event, create_engine
from sqlalchemy.engine import Engine
import time

class QueryMonitor:
    def __init__(self):
        self.queries = []
        
    def setup(self):
        @event.listens_for(Engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            conn.info.setdefault('query_start_time', []).append(time.time())
            
        @event.listens_for(Engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - conn.info['query_start_time'].pop(-1)
            self.queries.append({
                'statement': statement,
                'duration': total
            })
            
    def report(self):
        print(f"\nTotal queries: {len(self.queries)}")
        print(f"Tiempo total: {sum(q['duration'] for q in self.queries):.3f}s")
        print("\nQueries más lentas:")
        for q in sorted(self.queries, key=lambda x: x['duration'], reverse=True)[:10]:
            print(f"  {q['duration']*1000:.2f}ms: {q['statement'][:100]}...")

# Uso:
# monitor = QueryMonitor()
# monitor.setup()
# ... ejecutar código ...
# monitor.report()
```

---

## 🚀 Makefile para Comandos Comunes

```makefile
# Makefile

.PHONY: help install test format lint clean

help:
	@echo "Comandos disponibles:"
	@echo "  make install      - Instalar dependencias"
	@echo "  make test         - Ejecutar tests"
	@echo "  make test-cov     - Tests con coverage"
	@echo "  make format       - Formatear código"
	@echo "  make lint         - Ejecutar linters"
	@echo "  make clean        - Limpiar archivos generados"
	@echo "  make metrics      - Métricas del código"
	@echo "  make pre-commit   - Check pre-commit"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing
	open htmlcov/index.html

format:
	black src/ tests/
	isort src/ tests/
	autoflake --remove-all-unused-imports --in-place --recursive src/ tests/

lint:
	flake8 src/ --max-line-length=100
	pylint src/
	mypy src/ --strict

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete

metrics:
	@python scripts/code_metrics.py
	@radon cc src/ -a -s

pre-commit:
	@./scripts/pre_commit_check.sh

benchmark:
	pytest tests/performance/ --benchmark-only

deps:
	pydeps src/services/asignador_guardias.py --max-bacon 2 -o deps.svg
```

---

## 📝 requirements-dev.txt

```txt
# Development dependencies

# Testing
pytest>=8.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
pytest-qt>=4.2.0
pytest-benchmark>=4.0.0
hypothesis>=6.80.0

# Code quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
pylint>=2.17.0
mypy>=1.4.0
autoflake>=2.1.0
radon>=5.1.0

# Pre-commit
pre-commit>=3.3.0

# Documentation
sphinx>=7.0.0
sphinx-rtd-theme>=1.2.0

# Profiling
memory-profiler>=0.61.0
py-spy>=0.3.14

# Dependencies
pydeps>=1.12.0

# Structured logging
structlog>=23.1.0

# Validation
pydantic>=2.0.0
```

---

## 🎯 Script de Inicio Rápido

```bash
#!/bin/bash
# scripts/quickstart.sh

echo "🚀 Guardias de Patio - Quick Start"
echo "=================================="
echo

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
echo "✓ Python: $python_version"

# Create venv
if [ ! -d ".venv" ]; then
    echo "📦 Creando virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies
echo "📥 Instalando dependencias..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Setup pre-commit
echo "🔧 Configurando pre-commit..."
pre-commit install

# Run tests
echo "🧪 Ejecutando tests..."
pytest --tb=short -q

# Check coverage
echo "📊 Verificando coverage..."
pytest --cov=src --cov-report=term --tb=no -q

echo
echo "✅ Setup completado!"
echo "Ejecuta 'make help' para ver comandos disponibles"
```

---

Este archivo proporciona todas las herramientas necesarias para ejecutar el plan de refactorización de manera eficiente y automatizada.
