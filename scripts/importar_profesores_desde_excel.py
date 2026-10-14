"""
Script para importar profesores desde archivos Excel.
Lee los archivos en documentacion/datos ejemplo/ e importa profesores a la BD.
Si el profesor ya existe (por nombre), lo omite.
Si no existe, lo crea con email y 30h de contrato por defecto.
"""

import sys
from pathlib import Path

import pandas as pd

# Añadir el directorio src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_manager import SessionLocal
from infrastructure.database.models import Profesor
from utils import get_logger

logger = get_logger(__name__)


def normalizar_nombre(nombre: str) -> str:
    """Normaliza el nombre eliminando espacios extra y convirtiendo a mayúsculas."""
    return " ".join(nombre.strip().upper().split())


def importar_profesores_desde_excel(archivo_path: str, skip_rows: int = 9) -> dict:
    """
    Importa profesores desde un archivo Excel.

    Args:
        archivo_path: Ruta al archivo Excel
        skip_rows: Número de filas a saltar antes del encabezado (default: 9)

    Returns:
        Diccionario con estadísticas de importación
    """
    resultados = {
        "archivo": Path(archivo_path).name,
        "leidos": 0,
        "importados": 0,
        "existentes": 0,
        "errores": 0,
        "detalles": [],
    }

    try:
        # Leer Excel saltando las primeras filas de cabecera
        df = pd.read_excel(archivo_path, skiprows=skip_rows)

        # Renombrar columnas para facilitar acceso
        # Esperamos: Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico
        columnas_esperadas = ["nombre", "tel_fijo", "tel_movil", "email"]

        # Verificar que tengamos al menos 4 columnas
        if len(df.columns) < 4:
            logger.error(f"El archivo {archivo_path} no tiene suficientes columnas")
            resultados["errores"] += 1
            return resultados

        # Asignar nombres de columnas
        df.columns = columnas_esperadas + [f"extra_{i}" for i in range(len(df.columns) - 4)]

        # Filtrar filas válidas (que tengan nombre)
        df = df[df["nombre"].notna()]
        df = df[df["nombre"].str.strip() != ""]

        resultados["leidos"] = len(df)
        logger.info(f"Procesando {len(df)} profesores desde {Path(archivo_path).name}")

        with SessionLocal() as session:
            for idx, row in df.iterrows():
                try:
                    nombre_completo = str(row["nombre"]).strip()
                    email = str(row["email"]).strip() if pd.notna(row["email"]) else None

                    # Validar que tenga nombre
                    if not nombre_completo or nombre_completo.lower() in ["nan", "none", ""]:
                        continue

                    # Verificar si el profesor ya existe (por nombre)
                    profesor_existente = (
                        session.query(Profesor)
                        .filter(Profesor.nombre_completo.ilike(f"%{nombre_completo}%"))
                        .first()
                    )

                    if profesor_existente:
                        logger.debug(f"Profesor ya existe: {nombre_completo}")
                        resultados["existentes"] += 1
                        resultados["detalles"].append(
                            {"nombre": nombre_completo, "estado": "existente"}
                        )
                        continue

                    # Crear nuevo profesor
                    # Validar email
                    email_valido = (
                        email if email and email.lower() not in ["nan", "none", ""] else None
                    )

                    nuevo_profesor = Profesor(
                        nombre_completo=nombre_completo,
                        horas_contrato=30,  # Por defecto 30h
                        email_corporativo=email_valido,
                        porcentaje_jornada=100.0,  # Por defecto jornada completa
                        turno="completo",  # Por defecto turno completo
                    )

                    session.add(nuevo_profesor)
                    resultados["importados"] += 1
                    resultados["detalles"].append(
                        {
                            "nombre": nombre_completo,
                            "email": email,
                            "estado": "importado",
                        }
                    )
                    logger.info(f"✅ Importado: {nombre_completo} ({email})")

                except Exception as e:
                    logger.error(f"Error al procesar fila {idx}: {str(e)}")
                    resultados["errores"] += 1
                    resultados["detalles"].append(
                        {
                            "fila": idx,
                            "estado": "error",
                            "error": str(e),
                        }
                    )

            # Commit de todos los cambios
            session.commit()
            logger.info(f"Commit completado para {resultados['importados']} profesores")

    except Exception as e:
        logger.error(f"Error al procesar archivo {archivo_path}: {str(e)}")
        resultados["errores"] += 1
        resultados["detalles"].append({"estado": "error_archivo", "error": str(e)})

    return resultados


def main():
    """Función principal que procesa todos los archivos Excel."""
    # Directorio con los archivos Excel
    directorio_datos = Path(__file__).parent.parent / "documentacion" / "datos ejemplo"

    if not directorio_datos.exists():
        logger.error(f"No se encuentra el directorio: {directorio_datos}")
        return

    # Buscar todos los archivos .xlsx
    archivos_excel = list(directorio_datos.glob("*.xlsx"))

    if not archivos_excel:
        logger.warning(f"No se encontraron archivos Excel en {directorio_datos}")
        return

    logger.info(f"Encontrados {len(archivos_excel)} archivos Excel")
    print("\n" + "=" * 80)
    print("🎓 IMPORTACIÓN DE PROFESORES DESDE EXCEL")
    print("=" * 80 + "\n")

    # Procesar cada archivo
    resultados_totales = {
        "archivos_procesados": 0,
        "total_leidos": 0,
        "total_importados": 0,
        "total_existentes": 0,
        "total_errores": 0,
    }

    for archivo in archivos_excel:
        print(f"\n📂 Procesando: {archivo.name}")
        print("-" * 80)

        resultados = importar_profesores_desde_excel(str(archivo))

        # Mostrar resultados del archivo
        print(f"   Profesores leídos: {resultados['leidos']}")
        print(f"   ✅ Importados: {resultados['importados']}")
        print(f"   ⏭️  Ya existentes: {resultados['existentes']}")
        print(f"   ❌ Errores: {resultados['errores']}")

        # Acumular totales
        resultados_totales["archivos_procesados"] += 1
        resultados_totales["total_leidos"] += resultados["leidos"]
        resultados_totales["total_importados"] += resultados["importados"]
        resultados_totales["total_existentes"] += resultados["existentes"]
        resultados_totales["total_errores"] += resultados["errores"]

    # Resumen final
    print("\n" + "=" * 80)
    print("📊 RESUMEN FINAL")
    print("=" * 80)
    print(f"Archivos procesados: {resultados_totales['archivos_procesados']}")
    print(f"Total profesores leídos: {resultados_totales['total_leidos']}")
    print(f"✅ Total importados: {resultados_totales['total_importados']}")
    print(f"⏭️  Total ya existentes: {resultados_totales['total_existentes']}")
    print(f"❌ Total errores: {resultados_totales['total_errores']}")
    print("=" * 80 + "\n")

    if resultados_totales["total_importados"] > 0:
        print("✅ Importación completada exitosamente")
    else:
        print("ℹ️  No se importaron nuevos profesores (todos ya existían)")


if __name__ == "__main__":
    main()
