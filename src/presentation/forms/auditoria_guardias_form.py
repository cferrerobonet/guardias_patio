import json
from datetime import date, timedelta

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from infrastructure.database.models import GuardiaAuditLog, Profesor


_ACCIONES = ["Todas", "CREADA", "MODIFICADA", "ELIMINADA", "SUSTITUIDA", "GENERADA_BULK"]

_ETIQUETAS_ACCION = {
    "CREADA": "✚ Creada",
    "MODIFICADA": "✎ Modificada",
    "ELIMINADA": "✕ Eliminada",
    "SUSTITUIDA": "⇄ Sustitución",
    "GENERADA_BULK": "⚡ Generación",
}

_COLORES_ACCION = {
    "CREADA": "#D1FAE5",
    "MODIFICADA": "#E6F2FA",
    "ELIMINADA": "#FEE2E2",
    "SUSTITUIDA": "#FFF3CD",
    "GENERADA_BULK": "#F3E8FF",
}


class AuditoriaGuardiasForm(QWidget):
    re_sustituir_solicitada = pyqtSignal(int)

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self.session = session
        self._setup_ui()
        self.cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        titulo = QLabel("HISTORIAL DE CAMBIOS EN GUARDIAS")
        titulo.setObjectName("titleMain")
        layout.addWidget(titulo)

        # Barra de filtros
        filtros = QHBoxLayout()
        filtros.setSpacing(12)

        filtros.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit()
        self.fecha_desde.setCalendarPopup(True)
        self.fecha_desde.setDate(date.today() - timedelta(days=30))
        filtros.addWidget(self.fecha_desde)

        filtros.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit()
        self.fecha_hasta.setCalendarPopup(True)
        self.fecha_hasta.setDate(date.today())
        filtros.addWidget(self.fecha_hasta)

        filtros.addWidget(QLabel("Acción:"))
        self.combo_accion = QComboBox()
        self.combo_accion.addItems(_ACCIONES)
        filtros.addWidget(self.combo_accion)

        filtros.addWidget(QLabel("Profesor:"))
        self.input_profesor = QLineEdit()
        self.input_profesor.setPlaceholderText("Buscar por nombre...")
        self.input_profesor.setMaximumWidth(200)
        filtros.addWidget(self.input_profesor)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.clicked.connect(self.cargar_datos)
        filtros.addWidget(btn_filtrar)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("secondaryButton")
        btn_limpiar.clicked.connect(self._limpiar_filtros)
        filtros.addWidget(btn_limpiar)

        filtros.addStretch()
        layout.addLayout(filtros)

        # Tabla
        self.tabla = QTableWidget()
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
        layout.addWidget(self.tabla)

        self.label_total = QLabel("")
        layout.addWidget(self.label_total)

        self.btn_resustituir = QPushButton("Re-sustituir seleccionada")
        self.btn_resustituir.setObjectName("secondaryButton")
        self.btn_resustituir.setEnabled(False)
        self.btn_resustituir.clicked.connect(self._emitir_resustituir)
        layout.addWidget(self.btn_resustituir)

        self.tabla.itemSelectionChanged.connect(self._actualizar_boton_resustituir)

    def cargar_datos(self):
        desde = self.fecha_desde.date().toPyDate()
        hasta = self.fecha_hasta.date().toPyDate() + timedelta(days=1)
        accion_filtro = self.combo_accion.currentText()
        texto_prof = self.input_profesor.text().strip().lower()

        query = (
            self.session.query(GuardiaAuditLog)
            .filter(GuardiaAuditLog.timestamp >= desde, GuardiaAuditLog.timestamp < hasta)
            .order_by(GuardiaAuditLog.timestamp.desc())
        )
        if accion_filtro != "Todas":
            query = query.filter(GuardiaAuditLog.accion == accion_filtro)

        registros = query.limit(500).all()

        # Cargar nombres de profesores en una pasada
        ids_prof = {r.profesor_id for r in registros if r.profesor_id}
        nombres_prof: dict[int, str] = {}
        if ids_prof:
            for p in self.session.query(Profesor).filter(Profesor.id.in_(ids_prof)).all():
                nombres_prof[p.id] = p.nombre_completo

        # Filtrar por nombre si hay texto
        if texto_prof:
            registros = [
                r for r in registros
                if texto_prof in nombres_prof.get(r.profesor_id, "").lower()
            ]

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

            items = [
                QTableWidgetItem(ts),
                QTableWidgetItem(etiqueta),
                QTableWidgetItem(str(reg.guardia_id) if reg.guardia_id else "-"),
                QTableWidgetItem(nombre),
                QTableWidgetItem(reg.usuario or "-"),
                QTableWidgetItem(detalle),
            ]
            color = _COLORES_ACCION.get(reg.accion)
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
                if color:
                    from PyQt6.QtGui import QColor
                    item.setBackground(QColor(color))
                self.tabla.setItem(row, col, item)
            # Guardar metadatos en la primera celda para el botón re-sustituir
            self.tabla.item(row, 0).setData(
                Qt.ItemDataRole.UserRole, (reg.guardia_id, reg.accion)
            )

        self.label_total.setText(f"{len(registros)} registros")

    def _actualizar_boton_resustituir(self):
        rows = self.tabla.selectedItems()
        if not rows:
            self.btn_resustituir.setEnabled(False)
            return
        data = self.tabla.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        guardia_id, accion = data if data else (None, None)
        self.btn_resustituir.setEnabled(accion == "SUSTITUIDA" and guardia_id is not None)

    def _emitir_resustituir(self):
        rows = self.tabla.selectedItems()
        if not rows:
            return
        data = self.tabla.item(rows[0].row(), 0).data(Qt.ItemDataRole.UserRole)
        guardia_id, _ = data if data else (None, None)
        if guardia_id:
            self.re_sustituir_solicitada.emit(guardia_id)

    def _limpiar_filtros(self):
        self.fecha_desde.setDate(date.today() - timedelta(days=30))
        self.fecha_hasta.setDate(date.today())
        self.combo_accion.setCurrentIndex(0)
        self.input_profesor.clear()
        self.cargar_datos()
