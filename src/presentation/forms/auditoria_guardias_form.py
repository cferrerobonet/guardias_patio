"""Registro de cambios en guardias (GUA-UXI-009): se abre desde Ajustes, solo lectura.

El periodo (Desde/Hasta) se consulta en la base, con un tope de 500 cambios; el
buscador, los filtros de acción y usuario, el orden y «Limpiar filtros» son los del
patrón común de listados (`ListadoFiltrable`), sin paginación.
"""

import json
from datetime import date, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from infrastructure.database.models import GuardiaAuditLog, Profesor
from presentation.widgets.listado_filtrable import (
    ESPACIO_ETIQUETA,
    Filtro,
    ListadoFiltrable,
)
from utils.ui_helpers import dotar_de_contrato, llenando_tabla, pintar_tabla_vacia

LIMITE = 500
DIAS_DE_SERIE = 30
COL_ACCION = 1
COL_USUARIO = 4
_ORDEN = Qt.ItemDataRole.UserRole + 1

_ETIQUETAS_ACCION = {
    "CREADA": "✚ Creada",
    "MODIFICADA": "✎ Modificada",
    "ELIMINADA": "✕ Eliminada",
    "SUSTITUIDA": "⇄ Sustitución",
    "GENERADA_BULK": "⚡ Generación",
    "ASIGNADA_A_MANO": "Asignada a mano",
    "MOVIDA_A_MANO": "Movida a mano",
    "EDICION_DESHECHA": "Edición deshecha",
}

_COLORES_ACCION = {
    "CREADA": "#E2F0E3",
    "MODIFICADA": "#E2F0E3",
    "ELIMINADA": "#F8E3E1",
    "SUSTITUIDA": "#FBF0D9",
    "GENERADA_BULK": "#F3E8FF",
}


class _Celda(QTableWidgetItem):
    """Celda que ordena por su clave (fecha real, número) y no por el texto."""

    def __lt__(self, other):
        propia, ajena = self.data(_ORDEN), other.data(_ORDEN)
        if propia is not None and ajena is not None and type(propia) is type(ajena):
            return propia < ajena
        return super().__lt__(other)


class AuditoriaGuardiasForm(QWidget):
    re_sustituir_solicitada = pyqtSignal(int)

    def __init__(self, session, parent=None, *, solo_lectura: bool = False):
        super().__init__(parent)
        self.session = session
        self.solo_lectura = solo_lectura
        self._setup_ui()
        self.cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setAccessibleName("Cambios desde")
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setAccessibleName("Cambios hasta")
        self._poner_fechas_de_serie()

        # Tabla
        self.tabla = QTableWidget()
        dotar_de_contrato(
            self.tabla,
            "Historial de cambios en guardias",
            "Cada cambio hecho sobre una guardia: cuándo, qué acción, sobre cuál "
            "y quién lo hizo",
            ordenable=True,
        )
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha/Hora", "Acción", "Guardia ID", "Profesor", "Usuario", "Detalle"]
        )
        self.tabla.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla.horizontalHeader().setStretchLastSection(True)
        self.tabla.setColumnWidth(0, 160)
        self.tabla.setColumnWidth(1, 120)
        self.tabla.setColumnWidth(2, 90)
        self.tabla.setColumnWidth(3, 220)
        self.tabla.setColumnWidth(4, 120)
        # Patrón común de listados (GUA-UXI-005), sin paginación: buscador,
        # acción y usuario, orden por cabecera y «Limpiar filtros», que también
        # devuelve el periodo a los últimos 30 días.
        self.listado = ListadoFiltrable(
            self.tabla,
            "auditoria_guardias",
            entidad="cambios",
            marcador="Buscar por profesor, usuario o detalle…",
            filtros=(Filtro.columna("Acción", COL_ACCION), Filtro.columna("Usuario", COL_USUARIO)),
            filtros_propios=self._periodo_cambiado,
        )
        capa = self.listado.barra.layout()
        for i, (texto, editor) in enumerate(
            (("Desde:", self.fecha_desde), ("Hasta:", self.fecha_hasta))
        ):
            capa.insertLayout(1 + i, _par(texto, editor))
        self.listado.limpiar.clicked.connect(self._limpiar_periodo)
        self.fecha_desde.dateChanged.connect(lambda _d: self.cargar_datos())
        self.fecha_hasta.dateChanged.connect(lambda _d: self.cargar_datos())
        layout.addWidget(self.listado.barra)
        layout.addWidget(self.tabla)
        layout.addWidget(self.listado.pie)

        self.aviso_limite = QLabel(
            f"Se muestran los {LIMITE} cambios más recientes del periodo: "
            "acorta las fechas para ver los anteriores."
        )
        self.aviso_limite.setObjectName("secondary")
        self.aviso_limite.setWordWrap(True)
        self.aviso_limite.setVisible(False)
        layout.addWidget(self.aviso_limite)

        self.btn_resustituir = QPushButton("Re-sustituir seleccionada")
        self.btn_resustituir.setObjectName("secondaryButton")
        self.btn_resustituir.setEnabled(False)
        self.btn_resustituir.clicked.connect(self._emitir_resustituir)
        layout.addWidget(self.btn_resustituir)
        # Desde Ajustes es solo de consulta: sin acciones sobre las guardias
        self.btn_resustituir.setVisible(not self.solo_lectura)

        self.tabla.itemSelectionChanged.connect(self._actualizar_boton_resustituir)

    def _poner_fechas_de_serie(self) -> None:
        for editor, valor in (
            (self.fecha_desde, date.today() - timedelta(days=DIAS_DE_SERIE)),
            (self.fecha_hasta, date.today()),
        ):
            editor.blockSignals(True)
            editor.setDate(valor)
            editor.blockSignals(False)

    def _periodo_cambiado(self) -> bool:
        return self.fecha_desde.date().toPyDate() != date.today() - timedelta(
            days=DIAS_DE_SERIE
        ) or self.fecha_hasta.date().toPyDate() != date.today()

    def _limpiar_periodo(self) -> None:
        self._poner_fechas_de_serie()
        self.cargar_datos()

    def cargar_datos(self):
        desde = self.fecha_desde.date().toPyDate()
        hasta = self.fecha_hasta.date().toPyDate() + timedelta(days=1)

        registros = (
            self.session.query(GuardiaAuditLog)
            .filter(GuardiaAuditLog.timestamp >= desde, GuardiaAuditLog.timestamp < hasta)
            .order_by(GuardiaAuditLog.timestamp.desc())
            .limit(LIMITE)
            .all()
        )

        # Cargar nombres de profesores en una pasada
        ids_prof = {r.profesor_id for r in registros if r.profesor_id}
        nombres_prof: dict[int, str] = {}
        if ids_prof:
            for p in self.session.query(Profesor).filter(Profesor.id.in_(ids_prof)).all():
                nombres_prof[p.id] = p.nombre_completo

        with llenando_tabla(self.tabla):
            self.tabla.setRowCount(len(registros))
            for row, reg in enumerate(registros):
                ts = reg.timestamp.strftime("%d/%m/%Y %H:%M:%S") if reg.timestamp else ""
                etiqueta = _ETIQUETAS_ACCION.get(reg.accion, reg.accion)
                nombre = nombres_prof.get(reg.profesor_id, "-") if reg.profesor_id else "-"
                detalle = ""
                if reg.detalle:
                    try:
                        d = json.loads(reg.detalle)
                        detalle = ", ".join(f"{k}: {v}" for k, v in d.items())
                    except (json.JSONDecodeError, AttributeError):
                        detalle = reg.detalle

                celda_fecha = _Celda(ts)
                celda_fecha.setData(_ORDEN, reg.timestamp.isoformat() if reg.timestamp else "")
                celda_guardia = _Celda(str(reg.guardia_id) if reg.guardia_id else "-")
                celda_guardia.setData(_ORDEN, reg.guardia_id or 0)
                items = [
                    celda_fecha,
                    QTableWidgetItem(etiqueta),
                    celda_guardia,
                    QTableWidgetItem(nombre),
                    QTableWidgetItem(reg.usuario or "-"),
                    QTableWidgetItem(detalle),
                ]
                color = _COLORES_ACCION.get(reg.accion)
                for col, item in enumerate(items):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
                    )
                    if color:
                        from presentation.theme.modo_oscuro import color_fondo

                        item.setBackground(color_fondo(color))
                    self.tabla.setItem(row, col, item)
                # Guardar metadatos en la primera celda para el botón re-sustituir
                self.tabla.item(row, 0).setData(
                    Qt.ItemDataRole.UserRole, (reg.guardia_id, reg.accion)
                )

        pintar_tabla_vacia(
            self.tabla, "No hay cambios registrados en este periodo"
        )
        self.aviso_limite.setVisible(len(registros) >= LIMITE)
        self.listado.aplicar()

    def _actualizar_boton_resustituir(self):
        rows = self.tabla.selectedItems()
        if not rows:
            self.btn_resustituir.setEnabled(False)
            return
        data = self.tabla.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        guardia_id, accion = data if data else (None, None)
        self.btn_resustituir.setEnabled(accion == "SUSTITUIDA" and guardia_id is not None)

    def _emitir_resustituir(self):
        if self.solo_lectura:
            return
        rows = self.tabla.selectedItems()
        if not rows:
            return
        data = self.tabla.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        guardia_id, _ = data if data else (None, None)
        if guardia_id:
            self.re_sustituir_solicitada.emit(guardia_id)

    def _limpiar_filtros(self):
        self.listado.limpiar_filtros()
        self._limpiar_periodo()


def _par(texto: str, editor: QWidget) -> QHBoxLayout:
    """Etiqueta pegada a su control, como en la barra del listado."""
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("etiquetaDeFiltro")
    etiqueta.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
    etiqueta.setBuddy(editor)
    par = QHBoxLayout()
    par.setContentsMargins(0, 0, 0, 0)
    par.setSpacing(ESPACIO_ETIQUETA)
    par.addWidget(etiqueta)
    par.addWidget(editor)
    return par


class RegistroDeCambiosDialog(QDialog):
    """La ventana que abre «Registro de cambios» en Ajustes: solo de lectura."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registro de cambios en guardias")
        self.resize(1150, 700)
        capa = QVBoxLayout(self)
        capa.setContentsMargins(0, 0, 12, 12)
        self.registro = AuditoriaGuardiasForm(session, self, solo_lectura=True)
        capa.addWidget(self.registro)
        botones = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        botones.button(QDialogButtonBox.StandardButton.Close).setText("Cerrar")
        botones.rejected.connect(self.reject)
        capa.addWidget(botones)
