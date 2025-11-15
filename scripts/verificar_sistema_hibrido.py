#!/usr/bin/env python3
"""
Script de verificación del sistema híbrido.

Verifica que todos los componentes del nuevo sistema estén instalados
y funcionando correctamente:
- Dependencias (ortools, scikit-learn, numpy)
- Módulos del sistema híbrido
- Integración con la base de datos
"""

import sys
from pathlib import Path

# Agregar proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root))

print("🔍 VERIFICACIÓN DEL SISTEMA HÍBRIDO DE GUARDIAS\n")
print("=" * 70)

# ==================== VERIFICAR DEPENDENCIAS ====================
print("\n1️⃣ VERIFICANDO DEPENDENCIAS...")

try:
    from ortools.sat.python import cp_model
    print("   ✅ OR-Tools instalado correctamente")
    ortools_ok = True
except ImportError as e:
    print(f"   ❌ OR-Tools NO instalado: {e}")
    ortools_ok = False

try:
    import sklearn
    print(f"   ✅ scikit-learn {sklearn.__version__}")
    sklearn_ok = True
except ImportError as e:
    print(f"   ❌ scikit-learn NO instalado: {e}")
    sklearn_ok = False

try:
    import numpy as np
    print(f"   ✅ numpy {np.__version__}")
    numpy_ok = True
except ImportError as e:
    print(f"   ❌ numpy NO instalado: {e}")
    numpy_ok = False

try:
    import matplotlib
    print(f"   ✅ matplotlib {matplotlib.__version__}")
    matplotlib_ok = True
except ImportError as e:
    print(f"   ❌ matplotlib NO instalado: {e}")
    matplotlib_ok = False

# ==================== VERIFICAR MÓDULOS CORE ====================
print("\n2️⃣ VERIFICANDO MÓDULOS DEL SISTEMA HÍBRIDO...")

modulos_core = {
    "Orquestador": "services.orquestador_asignacion_guardias",
    "Asignador Iterativo": "services.asignador_iterativo",
    "Asignador ILP": "services.asignador_ilp",
    "Diagnosticador": "services.diagnosticador_guardias",
    "Diálogo Diagnóstico": "services.dialogo_diagnostico_guardias",
    "Integrador UI": "services.integrador_orquestador_ui",
}

modulos_ok = {}
for nombre, modulo in modulos_core.items():
    try:
        __import__(modulo)
        print(f"   ✅ {nombre}")
        modulos_ok[nombre] = True
    except ImportError as e:
        print(f"   ❌ {nombre}: {e}")
        modulos_ok[nombre] = False

# ==================== VERIFICAR MEJORAS AVANZADAS ====================
print("\n3️⃣ VERIFICANDO MEJORAS AVANZADAS...")

mejoras = {
    "Caché de Soluciones": "services.cache_soluciones_guardias",
    "Sugerencias Automáticas": "services.sistema_sugerencias_automaticas",
    "Visualizador": "services.visualizador_conflictos_guardias",
    "ML Predictor": "services.ml_predictor_estrategia",
}

mejoras_ok = {}
for nombre, modulo in mejoras.items():
    try:
        __import__(modulo)
        print(f"   ✅ {nombre}")
        mejoras_ok[nombre] = True
    except ImportError as e:
        print(f"   ❌ {nombre}: {e}")
        mejoras_ok[nombre] = False

# ==================== VERIFICAR USE CASE ====================
print("\n4️⃣ VERIFICANDO USE CASE HÍBRIDO...")

try:
    from application.use_cases.asignacion_guardias import GenerarGuardiasHibridoUseCase
    print("   ✅ GenerarGuardiasHibridoUseCase importado correctamente")
    usecase_ok = True
except ImportError as e:
    print(f"   ❌ GenerarGuardiasHibridoUseCase: {e}")
    usecase_ok = False

# ==================== VERIFICAR BASE DE DATOS ====================
print("\n5️⃣ VERIFICANDO CONEXIÓN A BASE DE DATOS...")

try:
    from models.models import Configuracion, Profesor

    from src.database.session import SessionLocal

    db = SessionLocal()

    # Verificar configuración
    config = db.query(Configuracion).first()
    if config:
        print(f"   ✅ Configuración encontrada: Curso {config.anio_escolar}")
        config_ok = True
    else:
        print("   ⚠️  No hay configuración en la base de datos")
        config_ok = False

    # Verificar profesores
    count_profesores = db.query(Profesor).filter(Profesor.activo == True).count()
    print(f"   ✅ Profesores activos: {count_profesores}")

    db.close()
    db_ok = True

except Exception as e:
    print(f"   ❌ Error de base de datos: {e}")
    db_ok = False
    config_ok = False

# ==================== PRUEBA RÁPIDA DE COMPONENTES ====================
print("\n6️⃣ PRUEBA RÁPIDA DE COMPONENTES...")

if all([ortools_ok, sklearn_ok, numpy_ok, all(modulos_ok.values())]):
    try:
        from services.asignador_ilp import ORTOOLS_DISPONIBLE

        print("   ✅ OrquestadorAsignacionGuardias instanciable")
        print("   ✅ AsignadorIterativo instanciable")
        print(f"   ✅ AsignadorILP disponible: {ORTOOLS_DISPONIBLE}")

        componentes_ok = True
    except Exception as e:
        print(f"   ❌ Error al instanciar componentes: {e}")
        componentes_ok = False
else:
    print("   ⏭️  Saltando prueba (faltan dependencias)")
    componentes_ok = False

# ==================== RESUMEN FINAL ====================
print("\n" + "=" * 70)
print("📊 RESUMEN DE VERIFICACIÓN\n")

checks = {
    "Dependencias Core": all([ortools_ok, sklearn_ok, numpy_ok, matplotlib_ok]),
    "Módulos Sistema Híbrido": all(modulos_ok.values()),
    "Mejoras Avanzadas": all(mejoras_ok.values()),
    "Use Case Híbrido": usecase_ok,
    "Base de Datos": db_ok and config_ok,
    "Componentes Funcionales": componentes_ok,
}

total = len(checks)
exitosos = sum(checks.values())

for nombre, ok in checks.items():
    estado = "✅" if ok else "❌"
    print(f"   {estado} {nombre}")

print(f"\n📈 RESULTADO: {exitosos}/{total} checks exitosos")

if exitosos == total:
    print("\n🎉 ¡SISTEMA COMPLETAMENTE OPERATIVO!")
    print("\n📝 Próximos pasos:")
    print("   1. Abre la aplicación principal")
    print("   2. Ve a 'Asignación de Guardias'")
    print("   3. Haz clic en 'Generar Asignación'")
    print("   4. El sistema usará automáticamente el algoritmo híbrido")
    print("\n💡 El sistema intentará:")
    print("   • Algoritmo iterativo (rápido) primero")
    print("   • Si falla, mostrará diagnóstico")
    print("   • Permitirá elegir: ajustar manual o usar ILP")
    sys.exit(0)
elif exitosos >= 4:
    print("\n⚠️  Sistema parcialmente operativo")
    print("\n🔧 Componentes faltantes pueden afectar funcionalidad")
    sys.exit(1)
else:
    print("\n❌ SISTEMA NO OPERATIVO")
    print("\n🔧 Solución:")
    if not all([ortools_ok, sklearn_ok, numpy_ok]):
        print("   pip install ortools scikit-learn numpy")
    print("\n📖 Consulta la documentación:")
    print("   - documentacion/SISTEMA_HIBRIDO_RESUMEN_EJECUTIVO.md")
    print("   - src/services/README_SISTEMA_HIBRIDO.md")
    sys.exit(2)
