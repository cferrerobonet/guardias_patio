"""Mover una guardia o cubrir a mano un hueco del calendario (GUA-CON-001).

Solo ofrece lo que el reparto permitiría: los recreos y zonas que ese día entran
en el reparto y, para cada hueco, los profesores que pueden hacerlo. Los que no,
aparecen desactivados y, al elegir uno, se dice por qué. Antes de guardar se pide
confirmación; después, el calendario ofrece deshacer.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
)

from infrastructure.database.models import Guardia, Zona
from services import edicion_manual_calendario as edicion
from utils import get_logger
from utils.ui_helpers import aplicar_caja

logger = get_logger(__name__)


class EditarGuardiaDialog(QDialog):
    """Con `guardia`, la mueve; sin ella, asigna el hueco elegido."""

    def __init__(
        self,
        session,
        fecha: date,
        guardia: Optional[Guardia] = None,
        hueco: Optional[edicion.Hueco] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.session = session
        self.guardia = guardia
        self.entrada = None  # la del historial, para poder deshacer
        self._inicial = hueco or (edicion.Hueco.de_guardia(guardia) if guardia else None)
        self._etiquetas = edicion.etiquetas_de_recreos(session)
        self._curso_id = edicion.curso_activo_id(session)

        self.setWindowTitle("Mover guardia" if guardia else "Asignar guardia")
        self.resize(560, self.sizeHint().height())
        self._setup_ui(fecha)
        self._al_cambiar_fecha()

    # -- interfaz ------------------------------------------------------------

    def _setup_ui(self, fecha: date) -> None:
        capa = QVBoxLayout(self)
        capa.setSpacing(12)

        if self.guardia is not None:
            quien = self.guardia.profesor.nombre_completo if self.guardia.profesor else "?"
            zona = self.guardia.zona.nombre_zona if self.guardia.zona else "?"
            texto = (
                f"Guardia de <b>{quien}</b> el <b>{self.guardia.fecha:%d/%m/%Y}</b>, "
                f"{self._etiqueta(self.guardia.recreo)} ({zona}). Elige adónde va y quién la hace."
            )
        else:
            texto = "Elige el recreo, la zona y el profesor que cubre el hueco."
        cabecera = QLabel(texto)
        cabecera.setWordWrap(True)
        capa.addWidget(cabecera)

        formulario = QFormLayout()
        self.fecha = QDateEdit()
        self.fecha.setCalendarPopup(True)
        self.fecha.setDisplayFormat("dd/MM/yyyy")
        self.fecha.setDate(QDate(fecha.year, fecha.month, fecha.day))
        self.fecha.setAccessibleName("Día de la guardia")
        self.fecha.dateChanged.connect(self._al_cambiar_fecha)
        formulario.addRow("Día:", self.fecha)

        self.combo_recreo = QComboBox()
        self.combo_recreo.setAccessibleName("Recreo")
        self.combo_recreo.currentIndexChanged.connect(self._al_cambiar_recreo)
        formulario.addRow("Recreo:", self.combo_recreo)

        self.combo_zona = QComboBox()
        self.combo_zona.setAccessibleName("Zona")
        self.combo_zona.currentIndexChanged.connect(self._al_cambiar_zona)
        formulario.addRow("Zona:", self.combo_zona)

        self.combo_profesor = QComboBox()
        self.combo_profesor.setAccessibleName("Profesor que hace la guardia")
        self.combo_profesor.currentIndexChanged.connect(self._comprobar)
        formulario.addRow("Profesor:", self.combo_profesor)
        capa.addLayout(formulario)

        self.aviso = QLabel("")
        self.aviso.setWordWrap(True)
        self.aviso.setAccessibleName("Comprobación del cambio")
        aplicar_caja(self.aviso, "info")
        capa.addWidget(self.aviso)

        self.botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.boton_ok = self.botones.button(QDialogButtonBox.StandardButton.Ok)
        self.boton_ok.setText("Mover" if self.guardia else "Asignar")
        self.botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        self.botones.accepted.connect(self._aceptar)
        self.botones.rejected.connect(self.reject)
        capa.addWidget(self.botones)

    def _etiqueta(self, recreo: int) -> str:
        return self._etiquetas.get(int(recreo), f"Recreo {recreo}")

    # -- opciones ------------------------------------------------------------

    def _fecha(self) -> date:
        return self.fecha.date().toPyDate()

    def _al_cambiar_fecha(self, *_args) -> None:
        self._huecos = edicion.huecos_del_dia(self.session, self._fecha())
        recreos = sorted({(h.turno, h.recreo) for h in self._huecos}, key=lambda t: t[1])
        self.combo_recreo.blockSignals(True)
        self.combo_recreo.clear()
        for turno, recreo in recreos:
            # La etiqueta ya dice el turno («Recreo 1 de tarde · 16:30»)
            texto = (self._etiquetas[int(recreo)] if int(recreo) in self._etiquetas
                     else f"Recreo {recreo} ({turno})")
            self.combo_recreo.addItem(texto, (turno, recreo))
        if self._inicial is not None:
            i = self.combo_recreo.findData((self._inicial.turno, self._inicial.recreo))
            if i >= 0:
                self.combo_recreo.setCurrentIndex(i)
        self.combo_recreo.blockSignals(False)
        self._al_cambiar_recreo()

    def _al_cambiar_recreo(self, *_args) -> None:
        dato = self.combo_recreo.currentData()
        self.combo_zona.blockSignals(True)
        self.combo_zona.clear()
        if dato is not None:
            turno, recreo = dato
            for h in self._huecos:
                if (h.turno, h.recreo) != (turno, recreo):
                    continue
                zona = self.session.get(Zona, h.zona_id)
                nombre = zona.nombre_zona if zona else f"Zona {h.zona_id}"
                ocupada = edicion.guardia_en_hueco(self.session, h, self._propia_id())
                if ocupada is not None:
                    quien = ocupada.profesor.nombre_completo if ocupada.profesor else "?"
                    nombre += f" (ocupada: {quien})"
                self.combo_zona.addItem(nombre, h)
            if self._inicial is not None:
                for i in range(self.combo_zona.count()):
                    if self.combo_zona.itemData(i).zona_id == self._inicial.zona_id:
                        self.combo_zona.setCurrentIndex(i)
                        break
        self.combo_zona.blockSignals(False)
        self._al_cambiar_zona()

    def _al_cambiar_zona(self, *_args) -> None:
        hueco = self.combo_zona.currentData()
        actual = self.combo_profesor.currentData()
        self.combo_profesor.blockSignals(True)
        self.combo_profesor.clear()
        self._motivos: dict = {}
        if hueco is not None:
            lista = edicion.candidatos(self.session, hueco, self._propia_id())
            # Primero los que pueden; los que no, al final y desactivados.
            for profesor, motivos in sorted(lista, key=lambda pm: bool(pm[1])):
                texto = profesor.nombre_completo + ("" if not motivos else " — no puede")
                self.combo_profesor.addItem(texto, profesor.id)
                self._motivos[profesor.id] = motivos
                if motivos:
                    item = self.combo_profesor.model().item(self.combo_profesor.count() - 1)
                    item.setEnabled(False)
                    item.setToolTip(" ".join(motivos))
            preferido = actual or (self.guardia.profesor_id if self.guardia else None)
            i = self.combo_profesor.findData(preferido) if preferido else -1
            if i < 0 or self._motivos.get(self.combo_profesor.itemData(i)):
                i = next(
                    (k for k in range(self.combo_profesor.count())
                     if not self._motivos.get(self.combo_profesor.itemData(k))),
                    i,
                )
            if i >= 0:
                self.combo_profesor.setCurrentIndex(i)
        self.combo_profesor.blockSignals(False)
        self._comprobar()

    def _propia_id(self) -> Optional[int]:
        return self.guardia.id if self.guardia is not None else None

    # -- comprobación --------------------------------------------------------

    def motivos_actuales(self) -> list:
        hueco = self.combo_zona.currentData()
        profesor_id = self.combo_profesor.currentData()
        if not self._huecos:
            return [
                f"El {self._fecha():%d/%m/%Y} no entra en el reparto (no es día lectivo del "
                "reparto oficial o no hay recreos ni zonas): elige otro día."
            ]
        if hueco is None:
            return ["Elige un recreo y una zona."]
        motivos = edicion.motivos_del_hueco(self.session, hueco, self._propia_id())
        if profesor_id is None:
            return motivos + ["No hay profesores activos."]
        motivos += self._motivos.get(profesor_id, [])
        if (
            not motivos
            and self.guardia is not None
            and edicion.Hueco.de_guardia(self.guardia) == hueco
            and self.guardia.profesor_id == profesor_id
        ):
            motivos.append("No has cambiado nada: elige otro día, recreo, zona o profesor.")
        return motivos

    def _comprobar(self, *_args) -> None:
        motivos = self.motivos_actuales()
        if motivos:
            self.aviso.setText("No se puede:\n• " + "\n• ".join(motivos))
            aplicar_caja(self.aviso, "aviso")
        else:
            self.aviso.setText(self._resumen())
            aplicar_caja(self.aviso, "exito")
        self.boton_ok.setEnabled(not motivos)

    def _resumen(self) -> str:
        profesor_id = self.combo_profesor.currentData()
        nombre = self.combo_profesor.currentText()
        total = edicion.guardias_del_profesor(self.session, profesor_id, self._curso_id)
        cambia_de_manos = self.guardia is None or self.guardia.profesor_id != profesor_id
        if cambia_de_manos:
            texto = f"Se puede. {nombre} pasará de {total} a {total + 1} guardias en el curso"
            if self.guardia is not None and self.guardia.profesor is not None:
                otro = edicion.guardias_del_profesor(
                    self.session, self.guardia.profesor_id, self._curso_id
                )
                texto += f" y {self.guardia.profesor.nombre_completo}, de {otro} a {otro - 1}"
            return texto + "."
        return f"Se puede. {nombre} sigue con {total} guardias en el curso."

    # -- acción --------------------------------------------------------------

    def _aceptar(self) -> None:
        if self.motivos_actuales():
            self._comprobar()
            return
        hueco = self.combo_zona.currentData()
        profesor_id = self.combo_profesor.currentData()
        zona = self.combo_zona.currentText().split(" (ocupada")[0]
        accion = "mover la guardia a" if self.guardia else "asignar"
        pregunta = QMessageBox(self)
        pregunta.setIcon(QMessageBox.Icon.Question)
        pregunta.setWindowTitle(self.windowTitle())
        pregunta.setText(
            f"¿{accion[0].upper() + accion[1:]} {self.combo_profesor.currentText()} el "
            f"{hueco.fecha:%d/%m/%Y}, {self._etiqueta(hueco.recreo)}, {zona}?"
        )
        pregunta.setInformativeText(self._resumen() + "\n\nDespués podrás deshacerlo.")
        pregunta.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        pregunta.setDefaultButton(QMessageBox.StandardButton.No)
        if pregunta.exec() != QMessageBox.StandardButton.Yes:
            return
        try:
            if self.guardia is not None:
                self.entrada = edicion.mover_guardia(self.session, self.guardia.id, hueco, profesor_id)
            else:
                self.entrada = edicion.asignar_guardia(self.session, hueco, profesor_id)
        except ValueError as e:
            self.session.rollback()
            QMessageBox.warning(self, "No se puede", str(e))
            return
        self.accept()
