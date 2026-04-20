"""Helpers de tabla para ProfesorForm.

Extraído desde profesor_form.py para reducir tamaño del formulario
sin cambiar comportamiento.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem


def cargar_tabla_profesores(*, session, table: QTableWidget, titulo_label, table_manager=None) -> None:
    """Cargar profesores y pintar filas en la tabla."""
    from application.app_services import AppServices

    table.setSortingEnabled(False)
    table.setRowCount(0)

    profesores = sorted(AppServices(session).profesores.get_all(), key=lambda p: p.nombre_completo)
    total_profesores = len(profesores)
    table.setRowCount(total_profesores)

    titulo_label.setText(f"PROFESORES REGISTRADOS ({total_profesores})")

    for i, prof in enumerate(profesores):
        # Nombre (con ID oculto)
        nombre_item = QTableWidgetItem(prof.nombre_completo or "")
        nombre_item.setData(Qt.ItemDataRole.UserRole, prof.id)
        table.setItem(i, 0, nombre_item)

        # Email
        email_item = QTableWidgetItem(str(prof.email_corporativo) if prof.email_corporativo else "-")
        table.setItem(i, 1, email_item)

        # Horas (centrado)
        horas_val = (
            prof.horas_contrato.value
            if hasattr(prof.horas_contrato, "value")
            else float(prof.horas_contrato)
        )
        horas_item = QTableWidgetItem(f"{horas_val:.1f}h")
        horas_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(i, 2, horas_item)

        # Turno (centrado)
        turno_item = QTableWidgetItem(str(prof.turno).capitalize())
        turno_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(i, 3, turno_item)

        # Tutor (centrado)
        tutor_text = "Sí" if getattr(prof, "es_tutor", getattr(prof, "tutor", False)) else "No"
        tutor_item = QTableWidgetItem(tutor_text)
        tutor_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(i, 4, tutor_item)

        # Fecha Inicio Guardias (centrado)
        fecha_inicio_text = (
            prof.fecha_inicio_guardias.strftime("%d/%m/%Y") if prof.fecha_inicio_guardias else "-"
        )
        fecha_inicio_item = QTableWidgetItem(fecha_inicio_text)
        fecha_inicio_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(i, 5, fecha_inicio_item)

        # Fecha Fin Guardias (centrado)
        fecha_fin_text = prof.fecha_fin_guardias.strftime("%d/%m/%Y") if prof.fecha_fin_guardias else "-"
        fecha_fin_item = QTableWidgetItem(fecha_fin_text)
        fecha_fin_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        table.setItem(i, 6, fecha_fin_item)

    table.setSortingEnabled(True)
    table.sortItems(0, Qt.SortOrder.AscendingOrder)

    if table_manager:
        table_manager.restore_selection()


def filtrar_tabla_profesores(*, table: QTableWidget, texto_busqueda: str) -> None:
    """Filtrar filas por nombre o email."""
    texto = texto_busqueda.lower().strip()

    if not texto:
        for i in range(table.rowCount()):
            table.setRowHidden(i, False)
        return

    for i in range(table.rowCount()):
        nombre_item = table.item(i, 0)
        email_item = table.item(i, 1)

        nombre = nombre_item.text().lower() if nombre_item else ""
        email = email_item.text().lower() if email_item else ""

        coincide = texto in nombre or texto in email
        table.setRowHidden(i, not coincide)
