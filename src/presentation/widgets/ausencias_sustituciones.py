"""
Widget unificado para gestión de ausencias y sustituciones.
"""

from PyQt6.QtCore import QDate, Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from presentation.forms.base_form import BaseForm
from presentation.themes.tema_aplicacion import TEXT_SECONDARY, get_table_style
from utils.icons import icon_for_button

_DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


class AusenciasSustitucionesWidget(BaseForm):
    """Widget unificado para registrar ausencias y gestionar sus sustituciones."""

    sustitucion_guardada = pyqtSignal()

    def __init__(self, session):
        from infrastructure.repositories.repository_factory import RepositoryFactory

        session_real = session.session if isinstance(session, RepositoryFactory) else session
        super().__init__(session_real)
        self._guardias_en_tabla: list = []
        self.setup_ui()
        self.cargar_profesores()
        self.cargar_historial()

    # ── UI ────────────────────────────────────────────────────────────────

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        titulo = QLabel("AUSENCIAS / SUSTITUCIONES")
        titulo.setObjectName("titleMain")
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        desc = QLabel("Registra una ausencia para ver y cubrir las guardias afectadas")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(desc)

        layout.addWidget(self._crear_panel_ausencia())
        layout.addWidget(self._crear_panel_guardias())
        layout.addWidget(self._crear_panel_historial())

    def _crear_panel_ausencia(self) -> QGroupBox:
        grupo = QGroupBox("Registrar Ausencia")
        lay = QVBoxLayout()
        lay.setSpacing(12)
        lay.setContentsMargins(15, 20, 15, 15)

        fila = QHBoxLayout()
        fila.setSpacing(15)

        col_prof = QVBoxLayout()
        lbl = QLabel("Profesor ausente:")
        lbl.setObjectName("fieldLabel")
        col_prof.addWidget(lbl)
        self.combo_profesor = QComboBox()
        self.combo_profesor.setMinimumWidth(220)
        self.combo_profesor.setAccessibleName("Profesor ausente")
        col_prof.addWidget(self.combo_profesor)
        fila.addLayout(col_prof, 2)

        col_inicio = QVBoxLayout()
        lbl2 = QLabel("Desde:")
        lbl2.setObjectName("fieldLabel")
        col_inicio.addWidget(lbl2)
        self.fecha_inicio = QDateEdit()
        self.fecha_inicio.setDate(QDate.currentDate())
        self.fecha_inicio.setCalendarPopup(True)
        self.fecha_inicio.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inicio.setAccessibleName("Fecha de inicio de la ausencia")
        self.fecha_inicio.dateChanged.connect(self._validar_fechas)
        col_inicio.addWidget(self.fecha_inicio)
        fila.addLayout(col_inicio, 1)

        col_fin = QVBoxLayout()
        lbl3 = QLabel("Hasta:")
        lbl3.setObjectName("fieldLabel")
        col_fin.addWidget(lbl3)
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        self.fecha_fin.setDisplayFormat("dd/MM/yyyy")
        self.fecha_fin.setAccessibleName("Fecha de fin de la ausencia")
        self.fecha_fin.dateChanged.connect(self._validar_fechas)
        col_fin.addWidget(self.fecha_fin)
        fila.addLayout(col_fin, 1)

        col_btn = QVBoxLayout()
        col_btn.addWidget(QLabel(""))
        self.btn_buscar = QPushButton("Buscar guardias afectadas")
        self.btn_buscar.setIcon(icon_for_button("search"))
        self.btn_buscar.setMinimumHeight(40)
        self.btn_buscar.setAccessibleName("Buscar guardias del profesor en el período seleccionado")
        self.btn_buscar.clicked.connect(self.buscar_guardias)
        col_btn.addWidget(self.btn_buscar)
        fila.addLayout(col_btn, 2)

        lay.addLayout(fila)
        grupo.setLayout(lay)
        return grupo

    def _crear_panel_guardias(self) -> QWidget:
        contenedor = QWidget()
        lay = QVBoxLayout(contenedor)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        cabecera = QHBoxLayout()
        lbl_sec = QLabel("GUARDIAS A CUBRIR")
        lbl_sec.setStyleSheet("font-weight: 600; font-size: 13px;")
        cabecera.addWidget(lbl_sec)
        cabecera.addStretch()
        self.btn_auto = QPushButton("Auto-asignar todo")
        self.btn_auto.setIcon(icon_for_button("account-switch"))
        self.btn_auto.setMinimumHeight(35)
        self.btn_auto.setProperty("secondary", "true")
        self.btn_auto.setEnabled(False)
        self.btn_auto.setAccessibleName(
            "Asignar automáticamente sustitutos a todas las guardias pendientes"
        )
        self.btn_auto.clicked.connect(self.auto_asignar)
        cabecera.addWidget(self.btn_auto)
        lay.addLayout(cabecera)

        self.tabla_guardias = QTableWidget()
        self.tabla_guardias.setColumnCount(8)
        self.tabla_guardias.setHorizontalHeaderLabels(
            ["Fecha", "Día", "Turno", "Recreo", "Zona", "Prof. ausente", "Sustituto", "●"]
        )
        self.tabla_guardias.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_guardias.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.tabla_guardias.setAlternatingRowColors(True)
        self.tabla_guardias.setStyleSheet(get_table_style())
        self.tabla_guardias.setMinimumHeight(180)
        header = self.tabla_guardias.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        self.tabla_guardias.verticalHeader().setDefaultSectionSize(48)
        lay.addWidget(self.tabla_guardias)

        self.lbl_sin_guardias = QLabel(
            "Este profesor no tiene guardias en el período seleccionado."
        )
        self.lbl_sin_guardias.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_sin_guardias.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        self.lbl_sin_guardias.setVisible(False)
        lay.addWidget(self.lbl_sin_guardias)

        botones = QHBoxLayout()
        botones.addStretch()
        self.btn_cancelar_tabla = QPushButton("Cancelar")
        self.btn_cancelar_tabla.setIcon(icon_for_button("close"))
        self.btn_cancelar_tabla.setMinimumHeight(40)
        self.btn_cancelar_tabla.setEnabled(False)
        self.btn_cancelar_tabla.setAccessibleName("Cancelar cambios y limpiar tabla")
        self.btn_cancelar_tabla.clicked.connect(self.limpiar_formulario)
        botones.addWidget(self.btn_cancelar_tabla)
        self.btn_guardar = QPushButton("Guardar sustituciones")
        self.btn_guardar.setIcon(icon_for_button("save"))
        self.btn_guardar.setMinimumHeight(40)
        self.btn_guardar.setProperty("success", "true")
        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setAccessibleName("Guardar todas las sustituciones asignadas")
        self.btn_guardar.clicked.connect(self.guardar)
        botones.addWidget(self.btn_guardar)
        lay.addLayout(botones)

        self.lbl_resultado = QLabel("")
        self.lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_resultado.setStyleSheet("font-size: 12px; padding: 4px 0;")
        self.lbl_resultado.setVisible(False)
        lay.addWidget(self.lbl_resultado)

        return contenedor

    def _crear_panel_historial(self) -> QGroupBox:
        grupo = QGroupBox("Historial de Sustituciones (calendario actual)")
        lay = QVBoxLayout()
        lay.setSpacing(10)
        lay.setContentsMargins(15, 15, 15, 15)

        filtros = QHBoxLayout()
        filtros.setSpacing(10)

        lbl_d = QLabel("Desde:")
        lbl_d.setObjectName("fieldLabel")
        filtros.addWidget(lbl_d)
        self.hist_desde = QDateEdit()
        self.hist_desde.setCalendarPopup(True)
        self.hist_desde.setDisplayFormat("dd/MM/yyyy")
        self.hist_desde.setDate(QDate.currentDate().addMonths(-9))
        filtros.addWidget(self.hist_desde)

        lbl_h = QLabel("Hasta:")
        lbl_h.setObjectName("fieldLabel")
        filtros.addWidget(lbl_h)
        self.hist_hasta = QDateEdit()
        self.hist_hasta.setCalendarPopup(True)
        self.hist_hasta.setDisplayFormat("dd/MM/yyyy")
        self.hist_hasta.setDate(QDate.currentDate())
        filtros.addWidget(self.hist_hasta)

        lbl_p = QLabel("Profesor:")
        lbl_p.setObjectName("fieldLabel")
        filtros.addWidget(lbl_p)
        self.combo_hist_profesor = QComboBox()
        self.combo_hist_profesor.setMinimumWidth(160)
        filtros.addWidget(self.combo_hist_profesor)

        btn_filtrar = QPushButton("Filtrar")
        btn_filtrar.setIcon(icon_for_button("search"))
        btn_filtrar.setMinimumHeight(35)
        btn_filtrar.clicked.connect(self.cargar_historial)
        filtros.addWidget(btn_filtrar)

        filtros.addStretch()

        self.btn_limpiar_historial = QPushButton("Limpiar historial")
        self.btn_limpiar_historial.setIcon(icon_for_button("delete"))
        self.btn_limpiar_historial.setMinimumHeight(35)
        self.btn_limpiar_historial.setProperty("danger", "true")
        self.btn_limpiar_historial.setAccessibleName(
            "Eliminar todas las sustituciones del calendario actual"
        )
        self.btn_limpiar_historial.clicked.connect(self.limpiar_historial)

        self.btn_deshacer = QPushButton("Deshacer sustitución")
        self.btn_deshacer.setIcon(icon_for_button("undo"))
        self.btn_deshacer.setMinimumHeight(35)
        self.btn_deshacer.setAccessibleName(
            "Devolver la guardia seleccionada a su profesor original"
        )
        self.btn_deshacer.setToolTip(
            "Selecciona una fila del historial para devolver esa guardia al profesor original"
        )
        self.btn_deshacer.clicked.connect(self.deshacer_seleccion)
        filtros.addWidget(self.btn_deshacer)

        filtros.addWidget(self.btn_limpiar_historial)

        lay.addLayout(filtros)

        self.tabla_historial = QTableWidget()
        self.tabla_historial.setColumnCount(6)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha", "Turno", "Recreo", "Zona", "Profesor original", "Profesor sustituto"]
        )
        self.tabla_historial.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_historial.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_historial.setAlternatingRowColors(True)
        self.tabla_historial.setStyleSheet(get_table_style())
        self.tabla_historial.setMinimumHeight(150)
        hh = self.tabla_historial.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        lay.addWidget(self.tabla_historial)

        grupo.setLayout(lay)
        return grupo

    # ── Lógica ────────────────────────────────────────────────────────────

    def cargar_profesores(self):
        try:
            from application.app_services import AppServices

            profesores = sorted(
                AppServices(self.session).profesores.get_all(),
                key=lambda p: p.nombre_completo,
            )
            self.combo_profesor.clear()
            self.combo_hist_profesor.clear()
            self.combo_hist_profesor.addItem("— Todos —", None)
            for p in profesores:
                self.combo_profesor.addItem(p.nombre_completo, p.id)
                self.combo_hist_profesor.addItem(p.nombre_completo, p.id)
        except Exception as e:
            self.manejar_excepcion(e, "cargar profesores")

    def _validar_fechas(self):
        valido = self.fecha_fin.date() >= self.fecha_inicio.date()
        self.btn_buscar.setEnabled(valido)
        self.fecha_fin.setStyleSheet("" if valido else "border: 1px solid #E74C3C;")

    def buscar_guardias(self):
        try:
            profesor_id = self.combo_profesor.currentData()
            if profesor_id is None:
                self.mostrar_advertencia("Profesor requerido", "Selecciona un profesor ausente.")
                return

            inicio = self.fecha_inicio.date().toPyDate()
            fin = self.fecha_fin.date().toPyDate()

            from infrastructure.database.models import Ausencia
            from services.gestor_ausencias import obtener_guardias_afectadas_por_periodo

            solapadas = (
                self.session.query(Ausencia)
                .filter(
                    Ausencia.profesor_id == profesor_id,
                    Ausencia.activa == True,  # noqa: E712
                    Ausencia.fecha_inicio <= fin,
                    Ausencia.fecha_fin >= inicio,
                )
                .count()
            )
            if solapadas > 0:
                self.mostrar_advertencia(
                    "Ausencia solapada",
                    "Este profesor ya tiene una ausencia registrada en ese período.",
                )

            guardias = obtener_guardias_afectadas_por_periodo(
                self.session, profesor_id, inicio, fin
            )
            self._guardias_en_tabla = guardias
            self._rellenar_tabla(guardias)

            tiene = len(guardias) > 0
            self.lbl_sin_guardias.setVisible(not tiene)
            self.btn_auto.setEnabled(tiene)
            self.btn_guardar.setEnabled(tiene)
            self.btn_cancelar_tabla.setEnabled(True)
        except Exception as e:
            self.manejar_excepcion(e, "buscar guardias")

    def _rellenar_tabla(self, guardias):
        self.tabla_guardias.setRowCount(0)
        for i, g in enumerate(guardias):
            self.tabla_guardias.insertRow(i)

            fecha_item = QTableWidgetItem(g.fecha.strftime("%d/%m"))
            fecha_item.setData(Qt.ItemDataRole.UserRole, g.id)
            _set_readonly(fecha_item)

            dia_item = QTableWidgetItem(_DIAS[g.fecha.weekday()])
            _set_readonly(dia_item)

            turno_item = QTableWidgetItem(g.turno.capitalize())
            _set_readonly(turno_item)

            recreo_item = QTableWidgetItem(str(g.recreo))
            recreo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            _set_readonly(recreo_item)

            zona_item = QTableWidgetItem(g.zona.nombre_zona if g.zona else "N/A")
            _set_readonly(zona_item)

            prof_item = QTableWidgetItem(g.profesor.nombre_completo if g.profesor else "N/A")
            _set_readonly(prof_item)

            self.tabla_guardias.setItem(i, 0, fecha_item)
            self.tabla_guardias.setItem(i, 1, dia_item)
            self.tabla_guardias.setItem(i, 2, turno_item)
            self.tabla_guardias.setItem(i, 3, recreo_item)
            self.tabla_guardias.setItem(i, 4, zona_item)
            self.tabla_guardias.setItem(i, 5, prof_item)

            combo = self._combo_sustituto_para_guardia(g)
            self.tabla_guardias.setCellWidget(i, 6, combo)

            estado_lbl = QLabel("🟢" if g.es_sustitucion else "🔴")
            estado_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_guardias.setCellWidget(i, 7, estado_lbl)

            self.tabla_guardias.setRowHeight(i, 48)

            combo.currentIndexChanged.connect(
                lambda _, row=i, lbl=estado_lbl: self._on_combo_changed(row, lbl)
            )

    def _combo_sustituto_para_guardia(self, g) -> QComboBox:
        try:
            from services.gestor_ausencias import obtener_profesores_disponibles

            disponibles = obtener_profesores_disponibles(
                self.session,
                g.fecha,
                g.turno,
                g.recreo,
                excluir_profesor_id=g.profesor_id,
            )
        except Exception:
            disponibles = []

        combo = QComboBox()
        combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        combo.setMinimumWidth(200)
        combo.setMinimumHeight(36)
        combo.addItem("— Sin asignar —", None)
        for prof, _ in disponibles:
            combo.addItem(prof.nombre_completo, prof.id)

        if g.es_sustitucion:
            for idx in range(combo.count()):
                if combo.itemData(idx) == g.profesor_id:
                    combo.setCurrentIndex(idx)
                    break

        return combo

    def _on_combo_changed(self, row: int, estado_lbl: QLabel):
        combo = self.tabla_guardias.cellWidget(row, 6)
        if combo:
            asignado = combo.currentData() is not None
            # El contrato de diseño pide texto, no un círculo de color: un emoji
            # no lo distingue quien no ve colores ni lo lee bien un lector (VIS-004).
            estado_lbl.setText("Asignado" if asignado else "Sin asignar")
            estado_lbl.setAccessibleName(
                "Sustituto asignado" if asignado else "Sin sustituto asignado"
            )

    def auto_asignar(self):
        try:
            pendientes = [
                g
                for i, g in enumerate(self._guardias_en_tabla)
                if (w := self.tabla_guardias.cellWidget(i, 6)) and w.currentData() is None
            ]

            if not pendientes:
                self.mostrar_informacion(
                    "Sin pendientes",
                    "Todas las guardias ya tienen sustituto asignado.",
                )
                return

            from services.gestor_ausencias import reasignar_guardias_automaticamente

            resultado = reasignar_guardias_automaticamente(self.session, pendientes)

            self._rellenar_tabla(self._guardias_en_tabla)
            self.cargar_historial()
            self.sustitucion_guardada.emit()

            msg = f"{resultado['reasignadas']} guardias asignadas automáticamente."
            if resultado["fallidas"] > 0:
                msg += f" {resultado['fallidas']} sin disponible — asígnalas manualmente."
            self.mostrar_exito("Auto-asignación completada", msg)
        except Exception as e:
            self.manejar_excepcion(e, "auto-asignar guardias")

    def guardar(self):
        try:
            guardadas = 0
            errores = []
            for i, g in enumerate(self._guardias_en_tabla):
                combo = self.tabla_guardias.cellWidget(i, 6)
                if combo is None:
                    continue
                nuevo_profesor_id = combo.currentData()
                if nuevo_profesor_id is None:
                    continue
                try:
                    from services.gestor_ausencias import reasignar_guardia

                    reasignar_guardia(self.session, g.id, nuevo_profesor_id)
                    guardadas += 1
                except ValueError as ve:
                    errores.append(str(ve))

            if errores:
                self.mostrar_advertencia(
                    "Algunos cambios no pudieron guardarse",
                    "\n".join(errores[:5]),
                )
            if guardadas > 0:
                self._mostrar_resultado(
                    f"✔ {guardadas} sustitución(es) guardada(s) correctamente.", ok=True
                )
                self.limpiar_formulario()
                self.cargar_historial()
                self.sustitucion_guardada.emit()
            elif not errores:
                self._mostrar_resultado("Sin cambios: no hay sustitutos asignados.", ok=False)
        except Exception as e:
            self.manejar_excepcion(e, "guardar sustituciones")

    def _mostrar_resultado(self, texto: str, ok: bool):
        color = "#27AE60" if ok else "#E67E22"
        self.lbl_resultado.setStyleSheet(f"font-size: 12px; padding: 4px 0; color: {color};")
        self.lbl_resultado.setText(texto)
        self.lbl_resultado.setVisible(True)

    def limpiar_formulario(self):
        self.tabla_guardias.setRowCount(0)
        self._guardias_en_tabla = []
        self.lbl_sin_guardias.setVisible(False)
        self.lbl_resultado.setVisible(False)
        self.btn_auto.setEnabled(False)
        self.btn_guardar.setEnabled(False)
        self.btn_cancelar_tabla.setEnabled(False)

    def validar_formulario(self) -> tuple[bool, str]:
        return True, ""

    def cargar_historial(self):
        try:
            from infrastructure.database.models import Guardia

            desde = self.hist_desde.date().toPyDate()
            hasta = self.hist_hasta.date().toPyDate()
            prof_id = self.combo_hist_profesor.currentData()

            q = self.session.query(Guardia).filter(
                Guardia.es_sustitucion == True,  # noqa: E712
                Guardia.fecha >= desde,
                Guardia.fecha <= hasta,
            )
            if prof_id is not None:
                q = q.filter(Guardia.profesor_sustituido_id == prof_id)

            guardias = q.order_by(Guardia.fecha).all()

            from application.app_services import AppServices

            svc = AppServices(self.session)
            prof_cache: dict[int, object] = {}

            def _nombre(pid):
                if pid is None:
                    return "—"
                if pid not in prof_cache:
                    prof_cache[pid] = svc.profesores.get_by_id(pid)
                p = prof_cache[pid]
                return p.nombre_completo if p else "—"

            self.tabla_historial.setRowCount(0)
            for i, g in enumerate(guardias):
                self.tabla_historial.insertRow(i)
                zona_nombre = g.zona.nombre_zona if g.zona else "N/A"
                for j, texto in enumerate(
                    [
                        g.fecha.strftime("%d/%m/%Y"),
                        g.turno.capitalize(),
                        str(g.recreo),
                        zona_nombre,
                        _nombre(g.profesor_sustituido_id),
                        _nombre(g.profesor_id),
                    ]
                ):
                    item = QTableWidgetItem(texto)
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    if j == 0:
                        # El id viaja en la primera celda: es lo que permite deshacer
                        item.setData(Qt.ItemDataRole.UserRole, g.id)
                    self.tabla_historial.setItem(i, j, item)
        except Exception as e:
            self.manejar_excepcion(e, "cargar historial")

    def deshacer_seleccion(self):
        """Devuelve la sustitución seleccionada a su profesor original (UXF-009)."""
        fila = self.tabla_historial.currentRow()
        if fila < 0:
            self.mostrar_advertencia(
                "Nada seleccionado",
                "Selecciona en el historial la sustitución que quieres deshacer.",
            )
            return

        celda = self.tabla_historial.item(fila, 0)
        guardia_id = celda.data(Qt.ItemDataRole.UserRole) if celda else None
        if guardia_id is None:
            return

        fecha = celda.text()
        original = self.tabla_historial.item(fila, 4)
        sustituto = self.tabla_historial.item(fila, 5)
        if not self.confirmar_accion(
            "Deshacer sustitución",
            f"La guardia del {fecha} volverá a "
            f"{original.text() if original else 'su profesor'}.\n\n"
            f"Se retira a {sustituto.text() if sustituto else 'el sustituto'}.",
        ):
            return

        try:
            from services.gestor_ausencias import deshacer_sustitucion

            deshacer_sustitucion(self.session, guardia_id)
            self._mostrar_resultado(f"✔ Sustitución del {fecha} deshecha.", ok=True)
            self.cargar_historial()
            self.sustitucion_guardada.emit()
        except ValueError as e:
            self.mostrar_advertencia("No se pudo deshacer", str(e))
        except Exception as e:  # noqa: BLE001
            self.manejar_excepcion(e, "deshacer sustitución")

    def limpiar_historial(self):
        if not self.confirmar_accion(
            "Limpiar historial",
            "¿Eliminar todas las sustituciones del calendario actual?\n"
            "Esta acción no se puede deshacer.",
        ):
            return
        try:
            from infrastructure.database.models import Guardia

            self.session.query(Guardia).filter(
                Guardia.es_sustitucion == True  # noqa: E712
            ).update({"es_sustitucion": False, "profesor_sustituido_id": None})
            self.session.commit()
            self.cargar_historial()
            self.sustitucion_guardada.emit()
            self.mostrar_exito("Historial limpiado", "Todas las sustituciones han sido eliminadas.")
        except Exception as e:
            self.manejar_excepcion(e, "limpiar historial")

    def refrescar(self):
        self.cargar_profesores()
        self.cargar_historial()


def _set_readonly(item: QTableWidgetItem) -> None:
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
