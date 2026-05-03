.PHONY: help install icon app dmg clean test test-fast test-ui bench mutation windows

help:
	@echo "🛠️  Guardias de Patio - Comandos disponibles:"
	@echo ""
	@echo "  macOS:"
	@echo "  ────────────────────────────────────────"
	@echo "  make install     - Instalar PyInstaller"
	@echo "  make icon        - Crear icono .icns"
	@echo "  make app         - Crear aplicación .app"
	@echo "  make dmg         - Crear instalador DMG"
	@echo ""
	@echo "  Windows (desde macOS con Wine/VM):"
	@echo "  ────────────────────────────────────────"
	@echo "  make windows     - Ver instrucciones para Windows"
	@echo ""
	@echo "  General:"
	@echo "  ────────────────────────────────────────"
	@echo "  make clean       - Limpiar archivos de build"
	@echo "  make test        - Ejecutar todos los tests"
	@echo "  make test-fast   - Tests sin UI (~30s, paralelo con xdist)"
	@echo "  make test-ui     - Solo tests de UI (PyQt6)"
	@echo "  make bench       - Benchmarks de rendimiento (pytest-benchmark)"
	@echo "  make mutation    - Ejecutar mutation testing (mutmut)"
	@echo "  make run         - Ejecutar aplicación"
	@echo ""

install:
	@echo "📦 Instalando dependencias de build..."
	pip install pyinstaller

icon:
	@echo "🎨 Creando icono..."
	chmod +x scripts/build/create_icon.sh
	scripts/build/create_icon.sh

app: icon
	@echo "🔨 Construyendo aplicación..."
	pyinstaller "Guardias de Patio.spec"

dmg: icon
	@echo "📀 Creando DMG instalable..."
	chmod +x scripts/build/build_dmg.sh
	scripts/build/build_dmg.sh

clean:
	@echo "🧹 Limpiando archivos de build..."
	rm -rf build dist *.spec
	rm -rf imagenes/*.iconset
	@echo "✅ Limpieza completada"

test:
	@echo "🧪 Ejecutando todos los tests..."
	pytest tests/ -v

test-fast:
	@echo "⚡ Tests rápidos (sin UI, paralelo)..."
	pytest tests/ -m "not ui and not slow and not benchmark" -n auto --tb=short -q

test-ui:
	@echo "🖥️  Tests de UI (PyQt6)..."
	pytest tests/ -m "ui" --tb=short -v

bench:
	@echo "📊 Ejecutando benchmarks de rendimiento..."
	pytest tests/test_benchmark_cpsat.py --benchmark-only --benchmark-sort=mean -v

mutation:
	@echo "🧬 Ejecutando mutation testing con mutmut..."
	mutmut run --paths-to-mutate=src/domain

run:
	@echo "🚀 Ejecutando aplicación..."
	/opt/homebrew/bin/python3.11 src/main.py

windows:
	@echo "🪟 Construcción para Windows"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Para crear el instalador de Windows, necesitas:"
	@echo ""
	@echo "1️⃣  Un PC con Windows (o VM/Wine)"
	@echo ""
	@echo "2️⃣  Ejecutar uno de estos scripts:"
	@echo "    • build_windows.bat  (simple - solo EXE)"
	@echo "    • build_windows.ps1  (completo - EXE + Instalador)"
	@echo ""
	@echo "3️⃣  Opcionalmente, instalar Inno Setup:"
	@echo "    https://jrsoftware.org/isdl.php"
	@echo ""
	@echo "📚 Documentación completa: BUILD_WINDOWS.md"
	@echo ""

