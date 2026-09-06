"""ESC-006 — que el arranque se vea mientras ocurre.

Entre el login y la ventana principal se migran datos, se comprueba que la
cuenta no esté abierta en otro equipo y se descarga todo de la nube. Los tres
pasos corren en el hilo de la interfaz, así que en pantalla no había nada: ni
ventana, ni aviso, ni forma de distinguir «está trabajando» de «se ha colgado».

Los pasos siguen donde estaban —moverlos a un hilo obligaría a sacar de ahí los
diálogos que algunos abren—, pero ahora se cuentan.
"""

import inspect

from presentation.widgets.pantalla_de_arranque import (
    PantallaDeArranque,
    abrir_pantalla_de_arranque,
)


def test_la_pantalla_muestra_el_paso_en_curso(qapp):
    pantalla = PantallaDeArranque()

    pantalla.paso("Trayendo los datos de la nube…")

    assert "nube" in pantalla.message()
    pantalla.close()


def test_la_pantalla_no_roba_clics_ni_foco(qapp):
    """Es decorativa: si aceptase eventos podría tragarse un diálogo del arranque."""
    pantalla = PantallaDeArranque()

    assert pantalla.isEnabled() is False
    pantalla.close()


def test_cada_paso_repinta(qapp):
    """Sin procesar eventos el texto no llega a verse: el hilo sigue de largo."""
    fuente = inspect.getsource(PantallaDeArranque.paso)
    assert "processEvents" in fuente


def test_sin_interfaz_no_se_crea_nada(monkeypatch):
    from PyQt6.QtWidgets import QApplication

    monkeypatch.setattr(QApplication, "instance", staticmethod(lambda: None))

    assert abrir_pantalla_de_arranque() is None


def test_el_arranque_cuenta_los_tres_pasos_lentos():
    import main

    fuente = inspect.getsource(main)
    for esperado in ("Comprobando el formato", "no esté abierta en otro equipo", "de la nube"):
        assert esperado in fuente


def test_la_pantalla_se_cierra_al_abrir_la_ventana():
    import main

    fuente = inspect.getsource(main)
    assert fuente.index("arranque.terminar(window)") > fuente.index("VentanaPrincipal(session")


def test_los_avisos_normales_del_arranque_no_son_errores():
    """Dos mensajes de traza normales se registraban como ERROR y ensuciaban el log."""
    import main

    fuente = inspect.getsource(main)
    assert 'logger.error("🔧' not in fuente
