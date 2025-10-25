.PHONY: help install icon app dmg clean test

help:
	@echo "🛠️  Guardias de Patio - Comandos disponibles:"
	@echo ""
	@echo "  make install     - Instalar PyInstaller y dependencias"
	@echo "  make icon        - Crear icono .icns para macOS"
	@echo "  make app         - Crear aplicación .app"
	@echo "  make dmg         - Crear instalador DMG completo"
	@echo "  make clean       - Limpiar archivos de build"
	@echo "  make test        - Ejecutar tests"
	@echo ""

install:
	@echo "📦 Instalando dependencias de build..."
	pip install pyinstaller

icon:
	@echo "🎨 Creando icono..."
	chmod +x create_icon.sh
	./create_icon.sh

app: icon
	@echo "🔨 Construyendo aplicación..."
	chmod +x build_dmg.sh
	pyinstaller guardias_patio.spec

dmg: icon
	@echo "💿 Creando DMG instalable..."
	chmod +x build_dmg.sh
	./build_dmg.sh

clean:
	@echo "🧹 Limpiando archivos de build..."
	rm -rf build dist *.spec
	rm -rf imagenes/*.iconset
	@echo "✅ Limpieza completada"

test:
	@echo "🧪 Ejecutando tests..."
	pytest tests/ -v

run:
	@echo "🚀 Ejecutando aplicación..."
	/opt/homebrew/bin/python3.11 src/main.py
