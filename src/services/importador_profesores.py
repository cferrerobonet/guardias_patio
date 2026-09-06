"""
Servicio para importar profesores desde archivos Excel o CSV.

Permite importar profesores desde archivos Excel (.xlsx) o CSV con soporte
para callbacks de progreso para mostrar el estado de la importación.
"""

import csv as csv_module
from pathlib import Path
from typing import Callable, Optional

from core.logging import get_logger
from core.privacidad import enmascarar_correo, enmascarar_nombre
from domain.entities.profesor_entity import ProfesorEntity
from infrastructure.repositories.repository_factory import RepositoryFactory

try:
    import pandas as pd
except ImportError:
    pd = None  # pandas es opcional

try:
    import openpyxl
except ImportError:
    openpyxl = None  # openpyxl es opcional

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


def leer_filas_de_profesores(
    archivo_path: str,
    skip_rows: int = 9,
    column_mapping: Optional[dict] = None,
) -> tuple:
    """Lee el fichero y devuelve `(filas, error)` sin tocar la base de datos.

    Cada fila es `{"fila": nº en el fichero, "nombre": ..., "email": ...}`.
    Separarlo de la escritura es lo que permite enseñar un informe antes de
    importar nada (FUN-007).
    """
    try:
        df = pd.read_excel(archivo_path, skiprows=skip_rows)
    except Exception as e:  # openpyxl y pandas lanzan de todo ante un fichero roto
        return [], f"Error al procesar archivo: {e}"

    if column_mapping:
        col_nombre = column_mapping.get("nombre")
        col_email = column_mapping.get("email")
        if col_nombre and col_nombre in df.columns:
            df = df.rename(columns={col_nombre: "nombre"})
        if col_email and col_email in df.columns:
            df = df.rename(columns={col_email: "email"})
        if "nombre" not in df.columns:
            return [], "La columna de nombre no se encontró en el archivo"
        if "email" not in df.columns:
            df["email"] = None
    else:
        columnas_esperadas = ["nombre", "tel_fijo", "tel_movil", "email"]
        if len(df.columns) < 4:
            return [], (
                f"El archivo no tiene suficientes columnas "
                f"(esperadas: 4, encontradas: {len(df.columns)})"
            )
        df.columns = columnas_esperadas + [f"extra_{i}" for i in range(len(df.columns) - 4)]

    df = df[df["nombre"].notna()]
    df = df[df["nombre"].astype(str).str.strip() != ""]

    filas = []
    for idx, row in df.iterrows():
        nombre = str(row["nombre"]).strip()
        if not nombre or nombre.lower() in ("nan", "none"):
            continue
        email = str(row["email"]).strip() if pd.notna(row["email"]) else None
        if email and email.lower() in ("nan", "none", ""):
            email = None
        # +2: la cabecera y que las filas de una hoja de cálculo empiezan en 1.
        filas.append({"fila": int(idx) + skip_rows + 2, "nombre": nombre, "email": email})
    return filas, None


def analizar_importacion(
    profesor_repo_or_session,
    archivo_path: str,
    skip_rows: int = 9,
    column_mapping: Optional[dict] = None,
) -> dict:
    """Dice qué pasaría al importar, sin escribir nada (FUN-007).

    Devuelve `archivo`, `error` y `filas`, donde cada fila lleva un `estado`:
    `nuevo`, `existente` o `repetido` —cuando el propio fichero trae el mismo
    nombre dos veces, que hasta ahora se importaba en silencio como uno solo—.
    """
    profesor_repo = _resolver_repositorio(profesor_repo_or_session)
    filas, error = leer_filas_de_profesores(archivo_path, skip_rows, column_mapping)

    informe = {
        "archivo": Path(archivo_path).name,
        "error": error,
        "filas": [],
        "nuevos": 0,
        "existentes": 0,
        "repetidos": 0,
    }
    if error:
        return informe

    vistos = set()
    for fila in filas:
        clave = normalizar_nombre(fila["nombre"])
        if clave in vistos:
            estado = "repetido"
        elif profesor_repo.find_by_nombre(fila["nombre"]):
            estado = "existente"
        else:
            estado = "nuevo"
        vistos.add(clave)
        informe["filas"].append({**fila, "estado": estado})
        contador = {"nuevo": "nuevos", "existente": "existentes", "repetido": "repetidos"}
        informe[contador[estado]] += 1

    return informe


def _resolver_repositorio(profesor_repo_or_session):
    if hasattr(profesor_repo_or_session, "create_profesor_repository"):
        return profesor_repo_or_session.create_profesor_repository()
    if hasattr(profesor_repo_or_session, "find_by_nombre"):
        return profesor_repo_or_session
    return RepositoryFactory(profesor_repo_or_session).create_profesor_repository()


def importar_profesores_desde_excel(
    profesor_repo_or_session,
    archivo_path: str,
    skip_rows: int = 9,
    column_mapping: Optional[dict] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Importa profesores desde un archivo Excel.

    Args:
        profesor_repo_or_session: Repositorio de profesores o sesión (legacy)
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
    # Detectar si es session o repo y adaptar
    if hasattr(profesor_repo_or_session, "create_profesor_repository"):
        # Es RepositoryFactory
        profesor_repo = profesor_repo_or_session.create_profesor_repository()
    elif hasattr(profesor_repo_or_session, "find_by_nombre"):
        # Es ya un repo
        profesor_repo = profesor_repo_or_session
    else:
        # Es una session (legacy) - crear repo factory
        factory = RepositoryFactory(profesor_repo_or_session)
        profesor_repo = factory.create_profesor_repository()

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

        # Aplicar mapeo de columnas si se proporcionó; si no, usar posición legacy
        if column_mapping:
            col_nombre = column_mapping.get("nombre")
            col_email = column_mapping.get("email")
            if col_nombre and col_nombre in df.columns:
                df = df.rename(columns={col_nombre: "nombre"})
            if col_email and col_email in df.columns:
                df = df.rename(columns={col_email: "email"})
            if "nombre" not in df.columns:
                error_msg = "La columna de nombre no se encontró en el archivo"
                resultados["errores"] += 1
                resultados["detalles"].append({"estado": "error_archivo", "error": error_msg})
                reportar_progreso(100, f"❌ Error: {error_msg}")
                return resultados
            if "email" not in df.columns:
                df["email"] = None
        else:
            # Comportamiento legacy: asignación por posición
            columnas_esperadas = ["nombre", "tel_fijo", "tel_movil", "email"]
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
            df.columns = columnas_esperadas + [f"extra_{i}" for i in range(len(df.columns) - 4)]

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
                profesores_existentes = profesor_repo.find_by_nombre(nombre_completo)
                profesor_existente = profesores_existentes[0] if profesores_existentes else None

                if profesor_existente:
                    logger.debug(f"Profesor ya existe: {enmascarar_nombre(nombre_completo)}")
                    resultados["existentes"] += 1
                    resultados["detalles"].append(
                        {"nombre": nombre_completo, "estado": "existente"}
                    )
                    continue

                # Crear nuevo profesor
                # Validar email
                email_valido = email if email and email.lower() not in ["nan", "none", ""] else None

                nuevo_profesor = ProfesorEntity(
                    nombre_completo=nombre_completo,
                    horas_contrato=30,  # Por defecto 30h
                    email_corporativo=email_valido,
                    porcentaje_jornada=100.0,  # Por defecto jornada completa
                    turno="mixto",  # Por defecto turno mixto
                )

                profesor_repo.save(nuevo_profesor)
                resultados["importados"] += 1
                resultados["detalles"].append(
                    {
                        "nombre": nombre_completo,
                        "email": email,
                        "estado": "importado",
                    }
                )
                logger.info(
                    f"✅ Importado: {enmascarar_nombre(nombre_completo)} "
                    f"({enmascarar_correo(email)})"
                )

            except (ValueError, TypeError, OSError) as e:
                logger.error(f"Error al procesar fila {idx}: {str(e)}")
                resultados["errores"] += 1
                resultados["detalles"].append(
                    {
                        "fila": idx,
                        "estado": "error",
                        "error": str(e),
                    }
                )

        # Commit de todos los cambios (delegado al repositorio)
        reportar_progreso(95, "Cambios procesados en la base de datos...")
        logger.info(f"Procesados {resultados['importados']} profesores")

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


def importar_profesores_desde_csv(
    profesor_repo_or_session,
    archivo_path: str,
    delimiter: str = ";",
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Importa profesores desde un archivo CSV.

    Columnas esperadas (con o sin cabecera): nombre_completo, email_corporativo.
    Si solo hay una columna, se trata como nombre_completo.

    Args:
        profesor_repo_or_session: Repositorio de profesores o sesión (legacy)
        archivo_path: Ruta al archivo CSV
        delimiter: Separador de campos (default: ";")
        progress_callback: Callback para reportar progreso

    Returns:
        Diccionario con estadísticas igual que importar_profesores_desde_excel
    """
    # Detectar si es session o repo y adaptar
    if hasattr(profesor_repo_or_session, "create_profesor_repository"):
        # Es RepositoryFactory
        profesor_repo = profesor_repo_or_session.create_profesor_repository()
    elif hasattr(profesor_repo_or_session, "find_by_nombre"):
        # Es ya un repo
        profesor_repo = profesor_repo_or_session
    else:
        # Es una session (legacy) - crear repo factory
        factory = RepositoryFactory(profesor_repo_or_session)
        profesor_repo = factory.create_profesor_repository()

    def reportar(pct: int, msg: str):
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception as e:
                logger.exception("Error en progress_callback: %s", e)

    resultados: dict = {
        "archivo": Path(archivo_path).name,
        "leidos": 0,
        "importados": 0,
        "existentes": 0,
        "errores": 0,
        "detalles": [],
    }

    try:
        reportar(0, "Leyendo archivo CSV...")
        with open(archivo_path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv_module.Sniffer()
            try:
                detected = sniffer.sniff(sample, delimiters=";,\t")
                delimiter = detected.delimiter
            except csv_module.Error:
                pass
            has_header = sniffer.has_header(sample)
            reader = csv_module.reader(f, delimiter=delimiter)
            rows = list(reader)

        if has_header and rows:
            rows = rows[1:]

        rows = [r for r in rows if r and any(c.strip() for c in r)]
        resultados["leidos"] = len(rows)

        if not rows:
            reportar(100, "⚠️ No se encontraron profesores válidos en el CSV")
            return resultados

        reportar(10, f"Encontrados {len(rows)} profesores para importar")

        for i, row in enumerate(rows):
            progreso = 10 + int((i + 1) / len(rows) * 85)
            nombre_completo = row[0].strip() if row else ""
            email = row[1].strip() if len(row) > 1 else None

            if not nombre_completo:
                continue

            reportar(progreso, f"Procesando: {nombre_completo[:40]}")

            profesores_existentes = profesor_repo.find_by_nombre(nombre_completo)
            existente = profesores_existentes[0] if profesores_existentes else None

            if existente:
                resultados["existentes"] += 1
                resultados["detalles"].append({"nombre": nombre_completo, "estado": "existente"})
                continue

            email_valido = email if email and email.lower() not in ("nan", "none", "") else None
            nuevo = ProfesorEntity(
                nombre_completo=nombre_completo,
                horas_contrato=30,
                email_corporativo=email_valido,
                porcentaje_jornada=100.0,
                turno="mixto",
            )
            profesor_repo.save(nuevo)
            resultados["importados"] += 1
            resultados["detalles"].append({"nombre": nombre_completo, "email": email_valido, "estado": "importado"})

        reportar(95, "Guardando cambios...")
        reportar(100, f"✅ {resultados['importados']} nuevos, {resultados['existentes']} ya existentes, {resultados['errores']} errores")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al importar CSV: {error_msg}")
        resultados["errores"] += 1
        resultados["detalles"].append({"estado": "error_archivo", "error": error_msg})
        reportar(100, f"❌ Error: {error_msg}")

    return resultados


def importar_profesores(
    profesor_repo_or_session,
    archivo_path: str,
    skip_rows: int = 9,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Punto de entrada unificado. Detecta el formato por extensión.
    Soporta .xlsx, .xls y .csv.
    """
    ext = Path(archivo_path).suffix.lower()
    if ext == ".csv":
        return importar_profesores_desde_csv(
            profesor_repo_or_session, archivo_path, progress_callback=progress_callback
        )
    return importar_profesores_desde_excel(
        profesor_repo_or_session, archivo_path, skip_rows=skip_rows, progress_callback=progress_callback
    )
