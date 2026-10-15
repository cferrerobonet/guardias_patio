"""El diálogo de versión nueva: logo de la app y botón de detalles entero.

En la 7.4.0 salía un «?» suelto como icono y «Mostrar los detalles…» cortado por
los dos lados, en macOS y en Windows: Qt mide ese botón con la fuente del sistema
y sin la hoja de estilos (Barlow seminegrita, 14 px de relleno a cada lado).
"""

from PyQt6.QtCore import QLibraryInfo, QLocale, QTranslator
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QMessageBox

from presentation.dialogs.actualizacion import dialogo_de_confirmacion
from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos
from presentation.theme.tokens import cargar_fuentes, cuerpo_del_sistema, familias_del_sistema


def test_lleva_el_logo_y_no_el_icono_de_pregunta(qapp):
    caja = dialogo_de_confirmacion(None, "9.9.9", "Notas de prueba")
    assert caja.icon() != QMessageBox.Icon.Question
    assert not caja.iconPixmap().isNull()


def test_el_boton_de_detalles_cabe_entero_con_la_hoja_de_estilos(qapp):
    # Como main.py: traducción de Qt (el texto en español es el largo), fuente y hoja
    traductor = QTranslator()
    traductor.load(
        QLocale(QLocale.Language.Spanish, QLocale.Country.Spain), "qtbase", "_",
        QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath),
    )
    qapp.installTranslator(traductor)
    fuente_anterior = qapp.font()
    cargar_fuentes()
    fuente = QFont()
    fuente.setFamilies(familias_del_sistema())
    fuente.setPointSize(cuerpo_del_sistema())
    qapp.setFont(fuente)
    qapp.setStyleSheet(construir_hoja_de_estilos())
    try:
        caja = dialogo_de_confirmacion(None, "9.9.9", "Notas de prueba")
        caja.show()
        qapp.processEvents()
        detalles = [
            b for b in caja.buttons()
            if caja.buttonRole(b) == QMessageBox.ButtonRole.ActionRole
        ]
        assert detalles, "Con notas tiene que haber botón de detalles"
        boton = detalles[0]
        necesario = boton.fontMetrics().horizontalAdvance(boton.text()) + 2 * 14
        assert boton.width() >= necesario, (boton.text(), boton.width(), necesario)
        caja.close()
    finally:
        qapp.setStyleSheet("")
        qapp.setFont(fuente_anterior)
        qapp.removeTranslator(traductor)
