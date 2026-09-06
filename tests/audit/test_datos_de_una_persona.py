"""Lote 18 — PRIV-003: antes de borrar a alguien hay que decir qué se pierde.

Borrar un profesor arrastra sus ausencias por la clave foránea en cascada, y
entre ellas van las bajas médicas. Aquí se fija que se pueda contar y exportar.
"""

import json
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from infrastructure.database.models import (
    Ausencia,
    Base,
    Guardia,
    GuardiaAuditLog,
    Profesor,
    Zona,
)
from services.datos_de_una_persona import (
    exportar_persona,
    resumen_de_persona,
    texto_de_lo_que_se_pierde,
)

SRC = Path(__file__).resolve().parents[2] / "src"


@pytest.fixture
def bd():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    sesion = sessionmaker(bind=engine, expire_on_commit=False)()
    sesion.add(Zona(id=1, nombre_zona="Patio"))
    sesion.add(
        Profesor(
            id=1, nombre_completo="García, Ana", horas_contrato=25.0,
            porcentaje_jornada=100, turno="mañana",
        )
    )
    sesion.add(
        Profesor(
            id=2, nombre_completo="Pérez, Luis", horas_contrato=25.0,
            porcentaje_jornada=100, turno="tarde",
        )
    )
    sesion.add(
        Guardia(id=1, profesor_id=1, fecha=date(2026, 9, 1), turno="mañana", recreo=1, zona_id=1)
    )
    sesion.add(
        Ausencia(
            id=1, profesor_id=1, fecha_inicio=date(2026, 9, 2), fecha_fin=date(2026, 9, 3),
            tipo="baja_medica", motivo="Intervención", documento_path="/tmp/parte.pdf",
        )
    )
    sesion.add(
        Ausencia(
            id=2, profesor_id=1, fecha_inicio=date(2026, 9, 9), fecha_fin=date(2026, 9, 9),
            tipo="permiso",
        )
    )
    sesion.add(GuardiaAuditLog(id=1, guardia_id=1, accion="CREADA", profesor_id=1))
    sesion.commit()
    return sesion


def test_el_resumen_cuenta_lo_que_cuelga_de_la_persona(bd):
    resumen = resumen_de_persona(bd, 1)
    assert resumen["nombre_completo"] == "García, Ana"
    assert resumen["guardias"] == 1
    assert resumen["ausencias"] == 2
    assert resumen["bajas_medicas"] == 1
    assert resumen["registro_de_actividad"] == 1


def test_una_persona_sin_nada_no_genera_aviso(bd):
    assert texto_de_lo_que_se_pierde(resumen_de_persona(bd, 2)) == ""


def test_una_persona_que_no_existe_no_revienta(bd):
    assert resumen_de_persona(bd, 99) == {}
    assert exportar_persona(bd, 99, Path("/tmp/nunca.json")) is None


def test_el_aviso_nombra_las_bajas_medicas(bd):
    texto = texto_de_lo_que_se_pierde(resumen_de_persona(bd, 1))
    assert "1 guardia" in texto
    assert "2 ausencias" in texto and "1 baja médica" in texto
    assert "registro de actividad" in texto


def test_la_exportacion_se_lleva_todo_lo_de_esa_persona(bd, tmp_path):
    destino = exportar_persona(bd, 1, tmp_path / "ana.json")
    assert destino is not None
    datos = json.loads(destino.read_text(encoding="utf-8"))
    assert datos["profesor"]["nombre_completo"] == "García, Ana"
    assert len(datos["guardias"]) == 1
    assert len(datos["ausencias"]) == 2
    assert len(datos["registro_de_actividad"]) == 1
    # La copia es para la persona: aquí sí van el motivo y el justificante.
    assert datos["ausencias"][0]["motivo"] == "Intervención"
    assert datos["ausencias"][0]["documento_path"] == "/tmp/parte.pdf"


def test_la_exportacion_no_se_lleva_lo_de_otra_persona(bd, tmp_path):
    destino = exportar_persona(bd, 2, tmp_path / "luis.json")
    datos = json.loads(destino.read_text(encoding="utf-8"))
    assert datos["guardias"] == [] and datos["ausencias"] == []


def test_la_copia_queda_solo_para_su_dueno(bd, tmp_path):
    destino = exportar_persona(bd, 1, tmp_path / "ana.json")
    assert oct(destino.stat().st_mode)[-3:] == "600"


def test_la_pantalla_avisa_y_ofrece_copia_antes_de_borrar():
    fuente = (SRC / "presentation/forms/profesor_form.py").read_text(encoding="utf-8")
    assert "_detalle_de_lo_que_se_borra" in fuente
    assert "Se borrará también" in fuente
    assert "no se puede deshacer" in fuente
    # Cancelar en el diálogo de copia no borra nada.
    assert "not self._ofrecer_copia_antes_de_borrar(profesores_a_eliminar)" in fuente
