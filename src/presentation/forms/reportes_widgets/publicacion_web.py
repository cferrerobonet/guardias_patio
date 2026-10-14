"""Generar los calendarios web desde la pestaña de informes (FUN-009).

Vive aparte de `reportes_form.py` porque esa vista ya rozaba las 800 líneas y
el hallazgo COD-008 va justo de eso.
"""


def publicar_desde(vista) -> None:
    """Genera una página y un calendario por profesor en la carpeta elegida."""
    from PyQt6.QtWidgets import QMessageBox

    from services import publicador_web
    from utils.ui_helpers import pedir_carpeta

    carpeta = pedir_carpeta(
        vista, "Dónde dejar los calendarios web", clave="publicacion_web"
    )
    if not carpeta:
        return

    try:
        resumen = publicador_web.publicar(vista.session, carpeta)
    except (OSError, ValueError) as e:
        vista.mostrar_error("No se pudieron generar los calendarios", str(e))
        return

    if not resumen["publicados"]:
        vista.mostrar_informacion(
            "Nada que publicar",
            "Ningún profesor activo tiene guardias asignadas todavía.",
        )
        return

    listado = "\n".join(
        f"{nombre}  ·  {correo or 'sin correo'}  ·  {fichero}"
        for nombre, correo, fichero in resumen["enlaces"]
    )
    caja = QMessageBox(vista)
    caja.setIcon(QMessageBox.Icon.Information)
    caja.setWindowTitle("Calendarios generados")
    caja.setText(
        f"{resumen['publicados']} calendarios listos en:\n{resumen['carpeta']}"
    )
    caja.setInformativeText(
        "Sube la carpeta entera al servidor del centro y envía a cada profesor "
        "su dirección. Las direcciones no cambian al volver a publicar, así que "
        "quien se suscriba una vez lo tiene para todo el curso."
    )
    caja.setDetailedText(listado)
    caja.exec()
