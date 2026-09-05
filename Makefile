.PHONY: help venv install icon app dmg release clean test test-fast test-ui test-audit coverage bench mutation windows

# El entorno virtual vive FUERA del repositorio: está en iCloud, que duplica los
# binarios y deja a Qt sin complementos válidos (QA-013 en la auditoría).
VENV := $(HOME)/.venvs/guardias-patio
PY := $(VENV)/bin/python
PYTEST := $(PY) -m pytest

help:
	@echo "🛠️  Guardias de Patio - Comandos disponibles:"
	@echo ""
	@echo "  macOS:"
	@echo "  ────────────────────────────────────────"
	@echo "  make install     - Instalar PyInstaller"
	@echo "  make icon        - Crear icono .icns"
	@echo "  make app         - Crear aplicación .app"
	@echo "  make dmg         - Crear instalador DMG y publicar GitHub Release"
	@echo "  make release     - Publicar GitHub Release con el DMG existente (sin recompilar)"
	@echo ""
	@echo "  Windows (desde macOS con Wine/VM):"
	@echo "  ────────────────────────────────────────"
	@echo "  make windows     - Ver instrucciones para Windows"
	@echo ""
	@echo "  General:"
	@echo "  ────────────────────────────────────────"
	@echo "  make venv        - Crear/actualizar el entorno virtual con todas las dependencias"
	@echo "  make clean       - Limpiar archivos de build y bytecode"
	@echo "  make test        - Ejecutar todos los tests"
	@echo "  make test-fast   - Tests sin UI (~30s, paralelo con xdist)"
	@echo "  make test-ui     - Solo tests de UI (PyQt6)"
	@echo "  make test-audit  - Suite de auditoría (tests/audit)"
	@echo "  make coverage    - Tests con informe de cobertura"
	@echo "  make bench       - Benchmarks de rendimiento (pytest-benchmark)"
	@echo "  make mutation    - Ejecutar mutation testing (mutmut)"
	@echo "  make run         - Ejecutar aplicación"
	@echo ""

venv:
	@echo "🐍 Preparando entorno en $(VENV) (fuera de iCloud)..."
	@test -x "$(PY)" || python3.11 -m venv "$(VENV)"
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt
	@echo "✅ Entorno listo. Para los E2E de la API: $(PY) -m playwright install chromium"

install:
	@echo "📦 Instalando dependencias de build..."
	$(PY) -m pip install pyinstaller

icon:
	@echo "🎨 Creando icono..."
	chmod +x scripts/build/create_icon.sh
	scripts/build/create_icon.sh

app: icon
	@echo "🔨 Construyendo aplicación..."
	pyinstaller "Guardias de Patio.spec"

dmg: icon
	@echo "📀 Creando DMG instalable y publicando release..."
	chmod +x scripts/build/build_dmg.sh
	scripts/build/build_dmg.sh

release:
	@VERSION=$$(python3 -c "import sys; sys.path.insert(0,'src'); from config.settings import get_settings; print(get_settings().app_version)"); \
	DMG="GuardiasPatio_v$${VERSION}_macOS.dmg"; \
	if [ ! -f "$$DMG" ]; then echo "❌ No se encuentra $$DMG. Ejecuta primero: make dmg"; exit 1; fi; \
	TAG="v$${VERSION}"; \
	echo "🚀 Publicando $$TAG con $$DMG..."; \
	if git ls-remote --tags origin "$$TAG" | grep -q "$$TAG"; then \
		gh release upload "$$TAG" "$$DMG" --clobber; \
	else \
		git tag "$$TAG" 2>/dev/null || true; \
		git push origin "$$TAG"; \
		gh release create "$$TAG" "$$DMG" --title "Guardias de Patio $${VERSION}" --generate-notes; \
	fi; \
	echo "✅ Release publicado: https://github.com/cferrerobonet/guardias_patio/releases/tag/$$TAG"

clean:
	@echo "🧹 Limpiando archivos de build..."
	rm -rf build dist
	rm -rf imagenes/*.iconset
	@echo "🧹 Limpiando bytecode (puede quedar de otra ruta o de otra versión de pytest)..."
	find . -path ./.git -prune -o -name "__pycache__" -type d -print0 2>/dev/null | xargs -0 rm -rf
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage coverage.xml
	@echo "✅ Limpieza completada"

test:
	@echo "🧪 Ejecutando todos los tests..."
	$(PYTEST) tests/ -q

test-fast:
	@echo "⚡ Tests rápidos (sin UI, paralelo)..."
	$(PYTEST) tests/ -m "not ui and not slow and not benchmark" -n auto --tb=short -q

test-ui:
	@echo "🖥️  Tests de UI (PyQt6)..."
	$(PYTEST) tests/ -m "ui" --tb=short -q

test-audit:
	@echo "🔍 Suite de auditoría..."
	$(PYTEST) tests/audit -q

coverage:
	@echo "📈 Tests con informe de cobertura..."
	$(PYTEST) tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-branch -q
	@echo "✅ Informe en htmlcov/index.html"

bench:
	@echo "📊 Ejecutando benchmarks de rendimiento..."
	$(PYTEST) tests/test_benchmark_cpsat.py --benchmark-only --benchmark-sort=mean -v

mutation:
	@echo "🧬 Ejecutando mutation testing con mutmut..."
	$(PY) -m mutmut run --paths-to-mutate=src/domain

run:
	@echo "🚀 Ejecutando aplicación..."
	$(PY) src/main.py

windows:
	@echo "🪟 Instalador de Windows"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""
	@echo "Sin PC con Windows: publica una etiqueta y GitHub lo compila."
	@echo "  git tag v<versión> && git push --tags"
	@echo "  O a mano en la pestaña Actions → Compilar."
	@echo ""
	@echo "Desde un PC con Windows:"
	@echo "  powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1"
	@echo "  Añade -Diagnostico para compilar con consola y volcado de hilos."
	@echo ""
