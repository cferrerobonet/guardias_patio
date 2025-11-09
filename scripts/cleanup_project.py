"""
Script para limpiar archivos temporales y caché del proyecto.

Este script elimina:
- Archivos __pycache__
- Archivos .pyc, .pyo
- Carpetas build/ (excepto documentación)
- Carpetas htmlcov/ (cobertura de tests)
- Archivos .coverage
- Carpetas .pytest_cache
- Carpetas .mypy_cache
- Archivos de logs antiguos (opcional)
- Bases de datos de usuarios cerrados (opcional)
"""

import shutil
from pathlib import Path


def get_size(path: Path) -> int:
    """Obtiene el tamaño de un archivo o directorio en bytes."""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
    return 0


def format_size(bytes_size: int) -> str:
    """Formatea el tamaño en bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} TB"


def analyze_project_size(project_root: Path):
    """Analiza qué carpetas ocupan más espacio."""
    print("\n" + "="*60)
    print("📊 ANÁLISIS DE ESPACIO DEL PROYECTO")
    print("="*60 + "\n")

    folders_to_check = [
        ("__pycache__", "**/__pycache__"),
        ("build", "build/"),
        ("htmlcov", "htmlcov/"),
        (".pytest_cache", ".pytest_cache/"),
        (".mypy_cache", ".mypy_cache/"),
        ("logs", "logs/"),
        ("data/users", "data/users/"),
        (".venv", ".venv/"),
        ("documentacion", "documentacion/"),
    ]

    sizes = []

    for name, pattern in folders_to_check:
        total_size = 0
        count = 0

        if "/" in pattern and not pattern.startswith("**"):
            # Carpeta específica
            folder = project_root / pattern
            if folder.exists():
                total_size = get_size(folder)
                count = 1
        else:
            # Patrón glob
            for item in project_root.rglob(pattern.replace("**/", "")):
                if item.is_dir():
                    total_size += get_size(item)
                    count += 1

        if total_size > 0:
            sizes.append((name, total_size, count))

    # Ordenar por tamaño
    sizes.sort(key=lambda x: x[1], reverse=True)

    print(f"{'Carpeta':<20} {'Tamaño':<15} {'Cantidad':<10}")
    print("-" * 60)

    total = 0
    for name, size, count in sizes:
        print(f"{name:<20} {format_size(size):<15} {count:<10}")
        total += size

    print("-" * 60)
    print(f"{'TOTAL':<20} {format_size(total):<15}")
    print()


def clean_pycache(project_root: Path, dry_run: bool = True):
    """Elimina todos los archivos __pycache__ y .pyc."""
    print("\n🧹 Limpiando __pycache__ y archivos .pyc...")

    deleted_count = 0
    freed_space = 0

    # Eliminar carpetas __pycache__
    for pycache in project_root.rglob("__pycache__"):
        size = get_size(pycache)
        if not dry_run:
            shutil.rmtree(pycache)
        deleted_count += 1
        freed_space += size
        print(f"  {'[DRY RUN] ' if dry_run else ''}Eliminado: {pycache.relative_to(project_root)}")

    # Eliminar archivos .pyc y .pyo
    for pyc in project_root.rglob("*.pyc"):
        size = get_size(pyc)
        if not dry_run:
            pyc.unlink()
        deleted_count += 1
        freed_space += size

    for pyo in project_root.rglob("*.pyo"):
        size = get_size(pyo)
        if not dry_run:
            pyo.unlink()
        deleted_count += 1
        freed_space += size

    print(f"\n  Carpetas/archivos eliminados: {deleted_count}")
    print(f"  Espacio liberado: {format_size(freed_space)}")


def clean_build_htmlcov(project_root: Path, dry_run: bool = True):
    """Elimina carpetas build/ y htmlcov/ (excepto documentación)."""
    print("\n🧹 Limpiando build/ y htmlcov/...")

    freed_space = 0

    # Build (excepto documentacion/build)
    build_dir = project_root / "build"
    if build_dir.exists() and build_dir.is_dir():
        size = get_size(build_dir)
        if not dry_run:
            shutil.rmtree(build_dir)
        freed_space += size
        print(f"  {'[DRY RUN] ' if dry_run else ''}Eliminado: build/ ({format_size(size)})")

    # htmlcov
    htmlcov_dir = project_root / "htmlcov"
    if htmlcov_dir.exists():
        size = get_size(htmlcov_dir)
        if not dry_run:
            shutil.rmtree(htmlcov_dir)
        freed_space += size
        print(f"  {'[DRY RUN] ' if dry_run else ''}Eliminado: htmlcov/ ({format_size(size)})")

    # .coverage
    coverage_file = project_root / ".coverage"
    if coverage_file.exists():
        size = get_size(coverage_file)
        if not dry_run:
            coverage_file.unlink()
        freed_space += size
        print(f"  {'[DRY RUN] ' if dry_run else ''}Eliminado: .coverage ({format_size(size)})")

    print(f"\n  Espacio liberado: {format_size(freed_space)}")


def clean_pytest_mypy(project_root: Path, dry_run: bool = True):
    """Elimina caché de pytest y mypy."""
    print("\n🧹 Limpiando caché de pytest y mypy...")

    freed_space = 0

    for cache_dir in [".pytest_cache", ".mypy_cache"]:
        cache_path = project_root / cache_dir
        if cache_path.exists():
            size = get_size(cache_path)
            if not dry_run:
                shutil.rmtree(cache_path)
            freed_space += size
            print(f"  {'[DRY RUN] ' if dry_run else ''}Eliminado: {cache_dir}/ ({format_size(size)})")

    print(f"\n  Espacio liberado: {format_size(freed_space)}")


def main():
    """Función principal."""
    project_root = Path(__file__).parent.parent

    print("\n" + "="*60)
    print("🧹 LIMPIEZA DEL PROYECTO - Guardias de Patio")
    print("="*60)

    # Analizar tamaño actual
    analyze_project_size(project_root)

    # Preguntar si hacer limpieza
    print("\n⚠️  OPCIONES DE LIMPIEZA:")
    print("  1. Análisis solamente (ya realizado)")
    print("  2. Simulación (Dry Run) - Ver qué se eliminaría")
    print("  3. Limpieza completa - ⚠️ ELIMINA ARCHIVOS")
    print("  4. Salir")

    opcion = input("\nSelecciona una opción (1-4): ").strip()

    if opcion == "2":
        print("\n" + "="*60)
        print("🔍 SIMULACIÓN DE LIMPIEZA (Dry Run)")
        print("="*60)
        clean_pycache(project_root, dry_run=True)
        clean_build_htmlcov(project_root, dry_run=True)
        clean_pytest_mypy(project_root, dry_run=True)

    elif opcion == "3":
        confirmar = input("\n⚠️  ¿Estás seguro de que quieres ELIMINAR estos archivos? (escribe 'SI' para confirmar): ")
        if confirmar == "SI":
            print("\n" + "="*60)
            print("🗑️  EJECUTANDO LIMPIEZA")
            print("="*60)
            clean_pycache(project_root, dry_run=False)
            clean_build_htmlcov(project_root, dry_run=False)
            clean_pytest_mypy(project_root, dry_run=False)
            print("\n✅ Limpieza completada!")
        else:
            print("\n❌ Limpieza cancelada.")

    elif opcion == "4":
        print("\n👋 Saliendo...")

    else:
        print("\n📊 Análisis completado. No se realizó limpieza.")


if __name__ == "__main__":
    main()
