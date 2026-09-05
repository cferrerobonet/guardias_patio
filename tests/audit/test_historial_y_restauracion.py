"""FUN-004: poder volver a antes de una generación.

`backup_database()` y `restore_database()` llevaban tiempo escritas en
`db_manager` sin que las llamara nadie desde la aplicación, igual que pasaba con
el contrato de cambios sin guardar. Generar borra todas las guardias del curso y
«Limpiar» también: hasta ahora no había vuelta atrás.
"""

import inspect

import pytest

pytestmark = pytest.mark.ui


# ---------------------------------------------------------------------------
# Copia previa a las operaciones que destruyen datos
# ---------------------------------------------------------------------------
def test_generar_hace_copia_antes_de_borrar_las_guardias():
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    fuente = inspect.getsource(GeneracionPanel._generar_guardias)
    assert "_copia_de_seguridad" in fuente
    # Y antes de lanzar el trabajo, no después. Se compara con la llamada, no con
    # el import del mismo nombre que hay al principio del método.
    assert fuente.index("_copia_de_seguridad") < fuente.index("resumen = ejecutar_con_progreso")


def test_limpiar_tambien_hace_copia():
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    fuente = inspect.getsource(GeneracionPanel._limpiar_guardias)
    assert "_copia_de_seguridad" in fuente
    assert fuente.index("_copia_de_seguridad") < fuente.index("limpiar_guardias_uc.execute")


def test_la_copia_no_impide_la_operacion_si_falla(qapp, session, monkeypatch):
    """Una copia fallida no puede dejar al usuario sin poder generar."""
    from presentation.forms.asignacion_widgets.generacion_panel import GeneracionPanel

    panel = GeneracionPanel(session)
    monkeypatch.setattr(
        "database.db_manager.get_current_user_id",
        lambda: (_ for _ in ()).throw(RuntimeError("sin usuario")),
    )

    panel._copia_de_seguridad("prueba")  # no debe lanzar
    panel.close()


# ---------------------------------------------------------------------------
# Listado de copias
# ---------------------------------------------------------------------------
def test_las_copias_se_listan_de_la_mas_reciente_a_la_mas_antigua(tmp_path, monkeypatch):
    import os
    import time

    from database import db_manager

    carpeta = tmp_path / "backups"
    carpeta.mkdir()
    monkeypatch.setattr(db_manager, "_get_user_backup_dir", lambda _u: carpeta)

    for i, nombre in enumerate(["a", "b", "c"]):
        fichero = carpeta / f"guardias_patio_backup_2026090{i}_00000{i}.db"
        fichero.write_bytes(b"x" * (1024 * (i + 1)))
        os.utime(fichero, (time.time() - (10 - i) * 60,) * 2)

    copias = db_manager.listar_backups("usuario")

    assert len(copias) == 3
    momentos = [c["momento"] for c in copias]
    assert momentos == sorted(momentos, reverse=True), "no están de más reciente a más antigua"
    assert all({"ruta", "momento", "tamano"} <= set(c) for c in copias)


def test_sin_carpeta_de_copias_devuelve_lista_vacia(tmp_path, monkeypatch):
    from database import db_manager

    monkeypatch.setattr(db_manager, "_get_user_backup_dir", lambda _u: tmp_path / "no-existe")
    assert db_manager.listar_backups("usuario") == []


# ---------------------------------------------------------------------------
# La vía de vuelta está en la interfaz
# ---------------------------------------------------------------------------
def test_importar_exportar_ofrece_restaurar(qapp, session):
    from presentation.forms.import_export_form import ImportExportForm

    vista = ImportExportForm(session)
    try:
        assert vista.restaurar_btn.accessibleName()
        assert hasattr(vista, "restaurar_copia")
    finally:
        vista.close()


def test_restaurar_avisa_cuando_no_hay_copias(qapp, session, monkeypatch):
    from presentation.forms.import_export_form import ImportExportForm

    vista = ImportExportForm(session)
    avisos = []
    monkeypatch.setattr(
        type(vista), "mostrar_advertencia", lambda self, t, m: avisos.append((t, m))
    )
    monkeypatch.setattr("database.db_manager.get_current_user_id", lambda: "usuario")
    monkeypatch.setattr("database.db_manager.listar_backups", lambda _u: [])

    vista.restaurar_copia()

    assert avisos, "no avisó de que no hay copias"
    assert "copia" in avisos[0][1].lower()
    vista.close()
