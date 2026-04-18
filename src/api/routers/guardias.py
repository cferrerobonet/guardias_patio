"""
API REST Router - Guardias

Endpoints para gestión de guardias (consultar, generar, asignar).
"""

import csv
import io
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from application.dtos import FiltroGuardiasDTO
from application.use_cases.guardia.obtener_guardias import ObtenerGuardiasUseCase

router = APIRouter(prefix="/guardias", tags=["guardias"])


class GuardiaResponse(BaseModel):
    """Schema de respuesta para guardia."""

    id: int
    fecha: date
    recreo: int
    turno: str
    zona_id: int
    zona_nombre: Optional[str] = None
    profesor_id: Optional[int] = None
    profesor_nombre: Optional[str] = None
    es_sustitucion: bool = False

    class Config:
        from_attributes = True


@router.get("", response_model=List[GuardiaResponse])
def obtener_guardias(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    limit: int = Query(default=100, le=1000),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Obtiene guardias con filtros opcionales.

    Args:
        configuracion_id: ID de la configuración del curso
        fecha_inicio: Filtrar desde fecha (opcional)
        fecha_fin: Filtrar hasta fecha (opcional)
        profesor_id: Filtrar por profesor (opcional)
        zona_id: Filtrar por zona (opcional)
        turno: Filtrar por turno (opcional)
        limit: Máximo de resultados (default: 100, max: 1000)
        offset: Desplazamiento para paginación
        db: Sesión de base de datos (inyectada)

    Returns:
        List[GuardiaResponse]: Lista de guardias

    Examples:
        GET /api/guardias?configuracion_id=1&turno=mañana&limit=50
    """
    try:
        filtros = FiltroGuardiasDTO(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            profesor_id=profesor_id,
            zona_id=zona_id,
            turno=turno,
        )
        use_case = ObtenerGuardiasUseCase(db)
        dtos = use_case.execute(filtros)

        # Filtrar por curso y paginar
        dtos = [g for g in dtos if True]  # curso_id se filtra en el use case si se añade
        paginados = dtos[offset: offset + limit]

        return [
            GuardiaResponse(
                id=g.id,
                fecha=g.fecha,
                recreo=g.numero_recreo,
                turno=g.turno,
                zona_id=g.zona_id,
                zona_nombre=g.zona_nombre,
                profesor_id=g.profesor_id,
                profesor_nombre=g.profesor_nombre,
                es_sustitucion=g.es_sustitucion,
            )
            for g in paginados
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al obtener guardias")


@router.get("/count")
def contar_guardias(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Cuenta guardias con filtros opcionales.

    Args:
        configuracion_id: ID de la configuración del curso
        fecha_inicio: Filtrar desde fecha (opcional)
        fecha_fin: Filtrar hasta fecha (opcional)
        profesor_id: Filtrar por profesor (opcional)
        zona_id: Filtrar por zona (opcional)
        turno: Filtrar por turno (opcional)
        db: Sesión de base de datos (inyectada)

    Returns:
        dict: Total de guardias

    Examples:
        GET /api/guardias/count?configuracion_id=1&turno=tarde
    """
    try:
        filtros = FiltroGuardiasDTO(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            profesor_id=profesor_id,
            zona_id=zona_id,
            turno=turno,
        )
        use_case = ObtenerGuardiasUseCase(db)
        dtos = use_case.execute(filtros)
        return {"total": len(dtos)}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error al contar guardias")


def _get_guardias_dtos(
    configuracion_id: int,
    fecha_inicio: Optional[date],
    fecha_fin: Optional[date],
    profesor_id: Optional[int],
    zona_id: Optional[int],
    turno: Optional[str],
    db: Session,
):
    filtros = FiltroGuardiasDTO(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        profesor_id=profesor_id,
        zona_id=zona_id,
        turno=turno,
    )
    use_case = ObtenerGuardiasUseCase(db)
    return use_case.execute(filtros)


_EXPORT_COLUMNS = ["id", "fecha", "recreo", "turno", "zona_id", "zona_nombre", "profesor_id", "profesor_nombre", "es_sustitucion"]


def _dto_to_row(g) -> list:
    return [g.id, g.fecha, g.numero_recreo, g.turno, g.zona_id, g.zona_nombre, g.profesor_id, g.profesor_nombre, g.es_sustitucion]


@router.get("/export/csv", response_class=Response, summary="Exportar guardias a CSV")
def exportar_guardias_csv(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Exporta las guardias filtradas como archivo CSV (UTF-8 con BOM para Excel)."""
    try:
        dtos = _get_guardias_dtos(configuracion_id, fecha_inicio, fecha_fin, profesor_id, zona_id, turno, db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener guardias")

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM UTF-8 para compatibilidad con Excel
    writer = csv.writer(buf, delimiter=";")
    writer.writerow(_EXPORT_COLUMNS)
    for g in dtos:
        writer.writerow(_dto_to_row(g))

    content = buf.getvalue().encode("utf-8")
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=guardias.csv"},
    )


@router.get("/export/xlsx", summary="Exportar guardias a Excel")
def exportar_guardias_xlsx(
    configuracion_id: int,
    fecha_inicio: Optional[date] = None,
    fecha_fin: Optional[date] = None,
    profesor_id: Optional[int] = None,
    zona_id: Optional[int] = None,
    turno: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Exporta las guardias filtradas como archivo Excel (.xlsx)."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl no disponible")

    try:
        dtos = _get_guardias_dtos(configuracion_id, fecha_inicio, fecha_fin, profesor_id, zona_id, turno, db)
    except Exception:
        raise HTTPException(status_code=500, detail="Error al obtener guardias")

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Guardias"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")

    ws.append(_EXPORT_COLUMNS)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill

    for g in dtos:
        ws.append(_dto_to_row(g))

    # Ajustar ancho de columnas
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 30)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=guardias.xlsx"},
    )

