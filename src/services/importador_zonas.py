"""
Servicio para importar zonas desde archivos CSV o Excel.

Columnas esperadas en el CSV/Excel:
- nombre_zona (obligatorio)
- descripcion (opcional)
- activa (opcional, default True, acepta: 1/0, true/false, si/no)
- capacidad_profesores (opcional, entero)
"""

import csv as csv_module
from pathlib import Path
from typing import Callable, Optional

from infrastructure.database.models import Zona
from sqlalchemy.orm import Session
from utils import get_logger

try:
    import pandas as pd
except ImportError:
    pd = None

logger = get_logger(__name__)

_BOOL_TRUE = {"1", "true", "si", "sí", "yes", "verdadero"}
_BOOL_FALSE = {"0", "false", "no", "no", "falso"}


def _parse_bool(value: str, default: bool = True) -> bool:
    v = str(value).strip().lower()
    if v in _BOOL_TRUE:
        return True
    if v in _BOOL_FALSE:
        return False
    return default


def _parse_int_or_none(value: str) -> Optional[int]:
    try:
        return int(str(value).strip())
    except (ValueError, TypeError):
        return None


def importar_zonas_desde_csv(
    session: Session,
    archivo_path: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Importa zonas desde un archivo CSV.

    El CSV debe tener cabecera. Columna obligatoria: nombre_zona.

    Returns:
        dict con leidos, importadas, existentes, errores, detalles
    """
    resultados = {
        "archivo": Path(archivo_path).name,
        "leidos": 0,
        "importadas": 0,
        "existentes": 0,
        "errores": 0,
        "detalles": [],
    }

    def _progress(pct: int, msg: str) -> None:
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass

    _progress(0, "Leyendo archivo CSV...")

    try:
        with open(archivo_path, newline="", encoding="utf-8-sig") as f:
            reader = csv_module.DictReader(f)
            filas = list(reader)
    except Exception as e:
        logger.error(f"Error leyendo CSV de zonas: {e}")
        resultados["errores"] += 1
        resultados["detalles"].append(f"Error lectura: {e}")
        return resultados

    total = len(filas)
    for i, fila in enumerate(filas):
        resultados["leidos"] += 1
        nombre = fila.get("nombre_zona", "").strip()
        if not nombre:
            resultados["errores"] += 1
            resultados["detalles"].append(f"Fila {i + 1}: nombre_zona vacío, omitida")
            continue

        existente = session.query(Zona).filter(Zona.nombre_zona == nombre).first()
        if existente:
            resultados["existentes"] += 1
            resultados["detalles"].append(f"'{nombre}': ya existe, omitida")
        else:
            zona = Zona(
                nombre_zona=nombre,
                descripcion=fila.get("descripcion", "").strip() or None,
                activa=_parse_bool(fila.get("activa", "1")),
                capacidad_profesores=_parse_int_or_none(fila.get("capacidad_profesores", "")),
            )
            session.add(zona)
            resultados["importadas"] += 1
            resultados["detalles"].append(f"'{nombre}': importada")

        _progress(int((i + 1) / total * 100), f"Procesando {i + 1}/{total}...")

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar zonas importadas: {e}")
        resultados["errores"] += resultados["importadas"]
        resultados["importadas"] = 0
        resultados["detalles"].append(f"Error al guardar en BD: {e}")

    _progress(100, "Importación completada")
    logger.info(
        f"Importación zonas: {resultados['importadas']} importadas, "
        f"{resultados['existentes']} existentes, {resultados['errores']} errores"
    )
    return resultados


def importar_zonas_desde_excel(
    session: Session,
    archivo_path: str,
    sheet_name: int | str = 0,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Importa zonas desde un archivo Excel (.xlsx).

    Requiere pandas y openpyxl instalados.

    Returns:
        dict con leidos, importadas, existentes, errores, detalles
    """
    resultados = {
        "archivo": Path(archivo_path).name,
        "leidos": 0,
        "importadas": 0,
        "existentes": 0,
        "errores": 0,
        "detalles": [],
    }

    if pd is None:
        resultados["errores"] += 1
        resultados["detalles"].append("pandas no instalado. Instala con: pip install pandas openpyxl")
        return resultados

    def _progress(pct: int, msg: str) -> None:
        if progress_callback:
            try:
                progress_callback(pct, msg)
            except Exception:
                pass

    _progress(0, "Leyendo archivo Excel...")

    try:
        df = pd.read_excel(archivo_path, sheet_name=sheet_name, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        filas = df.to_dict("records")
    except Exception as e:
        logger.error(f"Error leyendo Excel de zonas: {e}")
        resultados["errores"] += 1
        resultados["detalles"].append(f"Error lectura: {e}")
        return resultados

    total = len(filas)
    for i, fila in enumerate(filas):
        resultados["leidos"] += 1
        nombre = str(fila.get("nombre_zona", "")).strip()
        if not nombre or nombre.lower() in ("nan", "none", ""):
            resultados["errores"] += 1
            resultados["detalles"].append(f"Fila {i + 1}: nombre_zona vacío, omitida")
            continue

        existente = session.query(Zona).filter(Zona.nombre_zona == nombre).first()
        if existente:
            resultados["existentes"] += 1
            resultados["detalles"].append(f"'{nombre}': ya existe, omitida")
        else:
            zona = Zona(
                nombre_zona=nombre,
                descripcion=str(fila.get("descripcion", "")).strip() or None,
                activa=_parse_bool(str(fila.get("activa", "1"))),
                capacidad_profesores=_parse_int_or_none(str(fila.get("capacidad_profesores", ""))),
            )
            session.add(zona)
            resultados["importadas"] += 1
            resultados["detalles"].append(f"'{nombre}': importada")

        _progress(int((i + 1) / total * 100), f"Procesando {i + 1}/{total}...")

    try:
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error al guardar zonas importadas: {e}")
        resultados["errores"] += resultados["importadas"]
        resultados["importadas"] = 0
        resultados["detalles"].append(f"Error al guardar en BD: {e}")

    _progress(100, "Importación completada")
    logger.info(
        f"Importación zonas Excel: {resultados['importadas']} importadas, "
        f"{resultados['existentes']} existentes, {resultados['errores']} errores"
    )
    return resultados


def importar_zonas(
    session: Session,
    archivo_path: str,
    progress_callback: Optional[Callable[[int, str], None]] = None,
) -> dict:
    """
    Punto de entrada unificado. Detecta formato por extensión (.csv / .xlsx).
    """
    ext = Path(archivo_path).suffix.lower()
    if ext == ".csv":
        return importar_zonas_desde_csv(session, archivo_path, progress_callback)
    elif ext in (".xlsx", ".xls"):
        return importar_zonas_desde_excel(session, archivo_path, progress_callback=progress_callback)
    else:
        return {
            "archivo": Path(archivo_path).name,
            "leidos": 0,
            "importadas": 0,
            "existentes": 0,
            "errores": 1,
            "detalles": [f"Formato no soportado: {ext}. Usa .csv o .xlsx"],
        }
