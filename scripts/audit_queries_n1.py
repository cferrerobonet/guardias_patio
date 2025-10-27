#!/usr/bin/env python3
"""
Script de auditoría de queries N+1.

Analiza el código para identificar patrones problemáticos de queries
que pueden causar problemas N+1.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Colores para output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"


def find_n1_patterns(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Busca patrones N+1 en un archivo.

    Returns:
        Lista de (línea, patrón, contexto)
    """
    patterns = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines, 1):
        # Patrón 1: session.query().get() dentro de un loop
        if re.search(r'session\.query\(.*\)\.get\(', line):
            # Buscar si está en un loop (for/while en líneas anteriores cercanas)
            context_start = max(0, i - 5)
            context = ''.join(lines[context_start:i])
            if re.search(r'\b(for|while)\b', context):
                patterns.append((i, "session.query().get() en loop", line.strip()))

        # Patrón 2: Acceso a relaciones sin eager loading
        if re.search(r'\.(profesor|zona|guardia|ausencia)\b(?!\s*=)', line):
            # Verificar si está después de un .all() o .filter()
            context_start = max(0, i - 10)
            context = ''.join(lines[context_start:i])
            if re.search(r'\.(all|filter)\(\)', context) and 'joinedload' not in context and 'selectinload' not in context:
                patterns.append((i, "Acceso a relación sin eager loading", line.strip()))

        # Patrón 3: Loop sobre resultados con acceso a FK
        if 'for ' in line and re.search(r'\b(guardias|profesores|ausencias|zonas)\b', line):
            # Buscar accesos a relaciones en las siguientes líneas
            context_end = min(len(lines), i + 10)
            next_context = ''.join(lines[i:context_end])
            if re.search(r'\.(profesor|zona|guardia)\.', next_context):
                patterns.append((i, "Loop con acceso a FK sin eager loading", line.strip()))

    return patterns


def analyze_repository_files() -> Dict[str, List]:
    """Analiza archivos de repositorios."""
    results = {}
    repo_path = Path("src/infrastructure/repositories")

    if not repo_path.exists():
        print(f"{RED}❌ No se encontró {repo_path}{RESET}")
        return results

    for file in repo_path.glob("*.py"):
        if file.name == "__init__.py":
            continue

        patterns = find_n1_patterns(file)
        if patterns:
            results[str(file)] = patterns

    return results


def analyze_use_case_files() -> Dict[str, List]:
    """Analiza archivos de use cases."""
    results = {}
    uc_path = Path("src/application/use_cases")

    if not uc_path.exists():
        print(f"{RED}❌ No se encontró {uc_path}{RESET}")
        return results

    for file in uc_path.rglob("*.py"):
        if file.name == "__init__.py":
            continue

        patterns = find_n1_patterns(file)
        if patterns:
            results[str(file)] = patterns

    return results


def analyze_service_files() -> Dict[str, List]:
    """Analiza archivos de servicios."""
    results = {}
    service_path = Path("src/services")

    if not service_path.exists():
        print(f"{RED}❌ No se encontró {service_path}{RESET}")
        return results

    for file in service_path.glob("*.py"):
        if file.name == "__init__.py":
            continue

        patterns = find_n1_patterns(file)
        if patterns:
            results[str(file)] = patterns

    return results


def print_results(title: str, results: Dict[str, List]):
    """Imprime resultados de análisis."""
    if not results:
        print(f"{GREEN}✅ {title}: No se encontraron patrones N+1{RESET}")
        return

    print(f"\n{YELLOW}⚠️  {title}: {len(results)} archivos con posibles N+1{RESET}")
    print("=" * 80)

    for file, patterns in results.items():
        print(f"\n{BLUE}📄 {file}{RESET}")
        for line_num, pattern_type, code in patterns:
            print(f"  {RED}L{line_num}{RESET}: {pattern_type}")
            print(f"    {code[:100]}")


def main():
    """Función principal."""
    print(f"\n{BLUE}🔍 AUDITORÍA DE QUERIES N+1{RESET}")
    print("=" * 80)

    # Análisis por capas
    repo_results = analyze_repository_files()
    uc_results = analyze_use_case_files()
    service_results = analyze_service_files()

    # Imprimir resultados
    print_results("REPOSITORIOS", repo_results)
    print_results("USE CASES", uc_results)
    print_results("SERVICIOS", service_results)

    # Resumen
    total_files = len(repo_results) + len(uc_results) + len(service_results)
    total_patterns = sum(len(p) for p in repo_results.values()) + \
                     sum(len(p) for p in uc_results.values()) + \
                     sum(len(p) for p in service_results.values())

    print(f"\n{BLUE}📊 RESUMEN{RESET}")
    print("=" * 80)
    print(f"Archivos con posibles N+1: {total_files}")
    print(f"Patrones detectados: {total_patterns}")

    if total_patterns > 0:
        print(f"\n{YELLOW}💡 RECOMENDACIONES:{RESET}")
        print("1. Usar joinedload() para relaciones many-to-one/one-to-one")
        print("2. Usar selectinload() para relaciones one-to-many")
        print("3. Agregar options(joinedload(...)) en queries de repositorios")
        print("4. Considerar lazy='selectin' en modelos para relaciones frecuentes")
    else:
        print(f"\n{GREEN}🎉 ¡Excelente! No se detectaron patrones N+1 obvios{RESET}")


if __name__ == "__main__":
    main()
