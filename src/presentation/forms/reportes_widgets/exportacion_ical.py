"""Exportación iCal de la vista de reportes, fuera del formulario para que no crezca."""

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog

from infrastructure.database.models import Configuracion


def exportar_ical_desde(vista) -> None:
    """Exporta a .ics las guardias del profesor elegido en la pestaña iCal."""
    profesor_id = vista._ical_combo.currentData()
    if profesor_id is None:
        vista.mostrar_advertencia("Sin selección", "Selecciona un profesor.")
        return

    profesor_nombre = vista._ical_combo.currentText()
    from services.icalendar_service import ICalendarService

    nombre_archivo = ICalendarService.obtener_nombre_archivo_ics(profesor_nombre)
    from utils.ui_helpers import recordar_carpeta, ultima_carpeta

    # Propone la última carpeta usada, en vez de empezar siempre de cero
    carpeta_previa = ultima_carpeta()
    propuesta = (
        str(Path(carpeta_previa) / nombre_archivo) if carpeta_previa else nombre_archivo
    )
    ruta, _ = QFileDialog.getSaveFileName(
        vista,
        "Guardar archivo iCal",
        propuesta,
        "iCalendar (*.ics)",
    )
    if not ruta:
        return
    recordar_carpeta(ruta)

    try:
        config = vista.session.query(Configuracion).first()
        nombre_centro = "Centro Educativo"
        if config and hasattr(config, "nombre_centro") and config.nombre_centro:
            nombre_centro = config.nombre_centro

        ok = ICalendarService.generar_icalendar_profesor(
            session_or_factory=vista.session,
            profesor_id=profesor_id,
            ruta_salida=ruta,
            nombre_centro=nombre_centro,
        )
        if ok:
            vista.resultado_text.setText(
                f"✅ Archivo iCal exportado\n\nProfesor: {profesor_nombre}\nArchivo: {ruta}"
            )
            vista.mostrar_exito("iCal exportado", f"Guardado en {ruta}")
        else:
            vista.mostrar_advertencia(
                "Sin guardias", f"{profesor_nombre} no tiene guardias asignadas."
            )
    except (OSError, ValueError) as e:
        vista.mostrar_error("Error al exportar", str(e))
