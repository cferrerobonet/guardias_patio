"""
Servicio para importar profesores desde archivos Excel.

Permite importar profesores desde archivos Excel (.xlsx) con soporte
para callbacks de progreso para mostrar el estado de la importación.
"""

from pathlib import Path
from typing import Callable, Optional

from sqlalchemy.orm import Session

from models.models import Profesor
from utils import get_logger

try:
    import pandas as pd
except ImportError:
    pd = None  # pandas es opcional

logger = get_logger(__name__)


def normalizar_nombre(nombre: str) -> str:
    """
    Normaliza el nombre eliminando espacios extra y convirtiendo a mayúsculas.

    Args:
        nombre: Nombre a normalizar

    Returns:
        Nombre normalizado
    """
    return " ".join(nombre.strip().upper().split())


def importar_profesores_desde_excel(
    session: Session,
    archivo_path: str,
    skip_rows: int = 9,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Importa profesores desde un archivo Excel.

    Args:
        session: Sesión de base de datos
        archivo_path: Ruta al archivo Excel
        skip_rows: Número de filas a saltar antes del encabezado (default: 9)
        progress_callback: Callback para reportar progreso (porcentaje, mensaje)

    Returns:
        Diccionario con estadísticas de importación:
        - archivo: Nombre del archivo
        - leidos: Número de profesores leídos
        - importados: Número de profesores importados
        - existentes: Número de profesores que ya existían
        - errores: Número de errores encontrados
        - detalles: Lista con detalles de cada operación
    """

    def reportar_progreso(porcentaje: int, mensaje: str):
        """Helper para reportar progreso de forma segura."""
        if progress_callback:
            try:
                progress_callback(porcentaje, mensaje)
            except Exception as e:
                logger.warning(f"Error al reportar progreso: {e}")

    resultados = {
        "archivo": Path(archivo_path).name,
        "leidos": 0,
        "importados": 0,
        "existentes": 0,
        "errores": 0,
        "detalles": [],
    }

    try:
        reportar_progreso(0, "Leyendo archivo Excel...")

        # Leer Excel saltando las primeras filas de cabecera
        df = pd.read_excel(archivo_path, skiprows=skip_rows)

        reportar_progreso(10, "Archivo leído correctamente")

        # Renombrar columnas para facilitar acceso
        # Esperamos: Apellidos y nombre | Tel. fijo | Tel. móvil | Correo electrónico
        columnas_esperadas = ["nombre", "tel_fijo", "tel_movil", "email"]

        # Verificar que tengamos al menos 4 columnas
        if len(df.columns) < 4:
            error_msg = (
                f"El archivo no tiene suficientes columnas "
                f"(esperadas: 4, encontradas: {len(df.columns)})"
            )
            logger.error(error_msg)
            resultados["errores"] += 1
            resultados["detalles"].append({"estado": "error_archivo", "error": error_msg})
            reportar_progreso(100, f"❌ Error: {error_msg}")
            return resultados

        # Asignar nombres de columnas
        df.columns = columnas_esperadas + [
            f"extra_{i}" for i in range(len(df.columns) - 4)
        ]

        reportar_progreso(15, "Validando datos...")

        # Filtrar filas válidas (que tengan nombre)
        df = df[df["nombre"].notna()]
        df = df[df["nombre"].str.strip() != ""]

        resultados["leidos"] = len(df)

        if len(df) == 0:
            reportar_progreso(100, "⚠️ No se encontraron profesores válidos en el archivo")
            return resultados

        logger.info(f"Procesando {len(df)} profesores desde {Path(archivo_path).name}")
        reportar_progreso(20, f"Encontrados {len(df)} profesores para importar")

        # Procesar cada profesor (20% - 95%)
        total_profesores = len(df)
        for idx, row in df.iterrows():
            try:
                # Calcular progreso: desde 20% hasta 95%
                progreso_actual = 20 + int((idx + 1) / total_profesores * 75)

                nombre_completo = str(row["nombre"]).strip()
                email = str(row["email"]).strip() if pd.notna(row["email"]) else None

                # Validar que tenga nombre
                if not nombre_completo or nombre_completo.lower() in ["nan", "none", ""]:
                    continue

                reportar_progreso(
                    progreso_actual,
                    f"Procesando profesor {idx + 1}/{total_profesores}: {nombre_completo[:30]}...",
                )

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
        reportar_progreso(95, "Guardando cambios en la base de datos...")
        session.commit()
        logger.info(f"Commit completado para {resultados['importados']} profesores")

        # Resumen final
        reportar_progreso(
            100,
            f"✅ Importación completada: {resultados['importados']} nuevos, "
            f"{resultados['existentes']} ya existentes, {resultados['errores']} errores",
        )

    except Exception as e:
        error_msg = f"Error al procesar archivo: {str(e)}"
        logger.error(error_msg)
        resultados["errores"] += 1
        resultados["detalles"].append({"estado": "error_archivo", "error": str(e)})
        reportar_progreso(100, f"❌ Error: {error_msg}")

    return resultados
