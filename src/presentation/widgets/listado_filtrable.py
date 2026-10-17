"""Buscador, filtros y orden para las tablas que crecen (GUA-UXI-005).

Buscador, filtros por columna (profesor, zona, turno, estado), «Limpiar filtros»,
cabeceras ordenables, recuento «N de M» y la fila nueva resaltada y a la vista.
**Sin paginación** por decisión de CarlosFB (2026-10-17): la tabla muestra todas
las filas que pasan los filtros.

Se monta **encima** de un `QTableWidget` ya existente: la vista lo sigue llenando
como siempre y aquí solo se ocultan las filas que no tocan. Los filtros y el orden
se recuerdan entre sesiones, en `preferencias_listados.json` de la carpeta de datos.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

from PyQt6.QtCore import QObject, Qt, QTimer
from PyQt6.QtGui import QBrush
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QTableWidget,
    QWidget,
)

from utils.orden import clave_alfabetica

logger = logging.getLogger(__name__)

TODOS = "Todos"
ESPACIO_ETIQUETA = 6
ESPACIO_ENTRE_CONTROLES = 12


# --- Cálculos sin interfaz --------------------------------------------------


def texto_recuento(visibles: int, total: int, entidad: str = "") -> str:
    """«42 profesores», «5 de 42 profesores» con filtros, o «Sin resultados» a cero."""
    if visibles <= 0:
        return "Sin resultados"
    if visibles >= total:
        return f"{visibles} {entidad}".rstrip()
    return f"{visibles} de {total} {entidad}".rstrip()


def _normalizar(texto: str) -> str:
    return clave_alfabetica(texto).replace("n{", "n")


# --- Preferencias que se recuerdan -------------------------------------------


def _ruta_de_preferencias() -> Path:
    from core.paths import get_data_directory

    return get_data_directory() / "preferencias_listados.json"


def leer_preferencias(clave: str) -> dict:
    try:
        datos = json.loads(_ruta_de_preferencias().read_text(encoding="utf-8"))
        propias = datos.get(clave, {}) if isinstance(datos, dict) else {}
        return propias if isinstance(propias, dict) else {}
    except FileNotFoundError:
        return {}
    except (OSError, ValueError) as e:
        logger.warning(f"No se pudieron leer las preferencias de los listados: {e}")
        return {}


def guardar_preferencias(clave: str, valores: dict) -> None:
    ruta = _ruta_de_preferencias()
    try:
        try:
            datos = json.loads(ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, dict):
                datos = {}
        except (FileNotFoundError, ValueError):
            datos = {}
        datos[clave] = valores
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
    except OSError as e:
        logger.warning(f"No se pudieron guardar las preferencias de los listados: {e}")


# --- Filtros ----------------------------------------------------------------


@dataclass
class Filtro:
    """Un desplegable de filtro: «Turno», «Zona», «Estado»…

    `valor(tabla, fila)` da el valor de esa fila; las opciones del desplegable
    salen de los valores que haya en la tabla.
    """

    etiqueta: str
    valor: Callable[[QTableWidget, int], str]
    clave: str = ""
    combo: Optional[QComboBox] = field(default=None, repr=False)
    deseado: str = TODOS

    @classmethod
    def columna(cls, etiqueta: str, columna: int, clave: str = "") -> "Filtro":
        def _valor(tabla: QTableWidget, fila: int) -> str:
            item = tabla.item(fila, columna)
            return item.text().strip() if item is not None else ""

        return cls(etiqueta, _valor, clave or _normalizar(etiqueta))

    def __post_init__(self):
        if not self.clave:
            self.clave = _normalizar(self.etiqueta)


def texto_de_celdas(tabla: QTableWidget, fila: int, columnas=None) -> str:
    cols = range(tabla.columnCount()) if columnas is None else columnas
    partes = []
    for c in cols:
        if tabla.isColumnHidden(c):
            continue
        item = tabla.item(fila, c)
        if item is not None:
            partes.append(item.text())
        widget = tabla.cellWidget(fila, c)
        if isinstance(widget, QComboBox):
            partes.append(widget.currentText())
        elif isinstance(widget, QLabel):
            partes.append(widget.text())
    return " ".join(partes)


def filas_visibles_seleccionadas(tabla: QTableWidget) -> list[int]:
    """Las filas seleccionadas que se ven: «Seleccionar todo» de Qt también coge las ocultas."""
    modelo = tabla.selectionModel()
    if modelo is None:
        return []
    return sorted(
        {i.row() for i in modelo.selectedRows() if not tabla.isRowHidden(i.row())}
    )


def seleccionar_visibles(tabla: QTableWidget) -> None:
    """Ctrl+A sobre una tabla filtrada: solo lo que está a la vista."""
    tabla.clearSelection()
    modo = tabla.selectionMode()
    tabla.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
    try:
        for fila in range(tabla.rowCount()):
            if not tabla.isRowHidden(fila):
                tabla.selectRow(fila)
    finally:
        tabla.setSelectionMode(modo)


# --- El listado -------------------------------------------------------------


class ListadoFiltrable(QObject):
    """Buscador, filtros y orden sobre un `QTableWidget` que llena su vista.

    La vista coloca `barra` encima de la tabla y `pie` (el recuento) debajo. Para
    resaltar la fila recién creada, llama a `resaltar(clave)` después de recargar
    la tabla; `clave_fila(tabla, fila)` dice qué clave tiene cada fila.
    """

    def __init__(
        self,
        tabla: QTableWidget,
        clave: str,
        *,
        entidad: str = "",
        filtros: tuple | list = (),
        buscador: Optional[QLineEdit] = None,
        marcador: str = "Buscar…",
        columnas_busqueda=None,
        clave_fila: Optional[Callable[[QTableWidget, int], Any]] = None,
        boton_limpiar: Optional[QPushButton] = None,
        con_buscador: bool = True,
        con_limpiar: bool = True,
        recordar: tuple | list = (),
        filtros_propios: Optional[Callable[[], bool]] = None,
    ):
        super().__init__(tabla)
        self.tabla = tabla
        self.clave = clave
        self.entidad = entidad
        self.filtros: list[Filtro] = list(filtros)
        self._columnas_busqueda = columnas_busqueda
        self._clave_fila = clave_fila or _clave_de_la_primera_columna
        self._recordar = list(recordar)
        self._filtros_propios = filtros_propios
        self._total = 0
        self._resaltada: Any = None
        self._a_mostrar: Any = None
        self._items_resaltados: list = []
        self._aplicando = False
        self._pendiente = False
        self._recargada = True
        self._cargando_preferencias = False

        # Barra de filtros
        self.barra = QWidget()
        self.barra.setObjectName("barraDeListado")
        # Cada etiqueta va pegada a su desplegable: el ancho sobrante lo toma el
        # buscador o, si no lo hay, un muelle al final (antes se repartía entre
        # todos y la etiqueta quedaba lejos de su control).
        capa = QHBoxLayout(self.barra)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(ESPACIO_ENTRE_CONTROLES)
        self._buscador_propio = buscador is None
        self.buscador = buscador or QLineEdit()
        con_buscador_en_barra = self._buscador_propio and con_buscador
        if con_buscador_en_barra:
            self.buscador.setPlaceholderText(marcador)
            self.buscador.setClearButtonEnabled(True)
            self.buscador.setAccessibleName(f"Buscar en {entidad or 'la tabla'}")
            capa.addWidget(self.buscador, 1)
        self.buscador.textChanged.connect(self._al_cambiar_filtro)

        self.etiquetas: list[QLabel] = []
        for filtro in self.filtros:
            etiqueta = QLabel(f"{filtro.etiqueta}:")
            etiqueta.setObjectName("etiquetaDeFiltro")
            etiqueta.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
            combo = QComboBox()
            combo.setAccessibleName(f"Filtrar por {filtro.etiqueta.lower()}")
            combo.addItem(TODOS)
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo.currentTextChanged.connect(lambda texto, f=filtro: self._al_elegir(f, texto))
            filtro.combo = combo
            etiqueta.setBuddy(combo)
            par = QHBoxLayout()
            par.setContentsMargins(0, 0, 0, 0)
            par.setSpacing(ESPACIO_ETIQUETA)
            par.addWidget(etiqueta)
            par.addWidget(combo)
            capa.addLayout(par)
            self.etiquetas.append(etiqueta)

        self._con_limpiar = con_limpiar
        if boton_limpiar is None:
            self.limpiar = QPushButton("Limpiar filtros")
            self.limpiar.setProperty("secondary", "true")
            if con_limpiar:
                capa.addWidget(self.limpiar)
        else:
            self.limpiar = boton_limpiar
        if capa.count() == 0:
            self.barra.hide()  # nada que filtrar: ni buscador ni desplegables
        if not con_buscador_en_barra:
            capa.addStretch(1)
        if con_limpiar:
            self.limpiar.setToolTip("Quitar la búsqueda y los filtros")
            self.limpiar.clicked.connect(self.limpiar_filtros)

        # Pie: el recuento
        self.pie = QWidget()
        self.pie.setObjectName("pieDeListado")
        capa_pie = QHBoxLayout(self.pie)
        capa_pie.setContentsMargins(0, 0, 0, 0)
        self.recuento = QLabel("")
        self.recuento.setObjectName("secondary")
        self.recuento.setAccessibleName("Recuento de filas")
        capa_pie.addWidget(self.recuento)
        capa_pie.addStretch(1)

        # Cambios de la tabla: se recalcula una sola vez, al volver al bucle de eventos
        modelo = tabla.model()
        if modelo is not None:
            # Filas nuevas o quitadas: la vista ha recargado y se repone el orden
            # elegido. Reordenar o cambiar una celda solo vuelve a filtrar.
            modelo.rowsInserted.connect(self._programar_recarga)
            modelo.rowsRemoved.connect(self._programar_recarga)
            modelo.modelReset.connect(self._programar_recarga)
            modelo.layoutChanged.connect(self._programar)
            modelo.dataChanged.connect(self._programar)
        cabecera = tabla.horizontalHeader()
        if cabecera is not None:
            cabecera.sectionClicked.connect(lambda _c: QTimer.singleShot(0, self._guardar))

        self._cargar_preferencias()
        self._restaurar_orden()
        self.aplicar()

    # --- API ---------------------------------------------------------------

    @property
    def total(self) -> int:
        """Filas que pasan la búsqueda y los filtros."""
        return self._total

    def hay_filtros(self) -> bool:
        """Hay búsqueda, algún desplegable elegido o un filtro propio de la vista."""
        if self._filtros_propios is not None and self._filtros_propios():
            return True
        return bool(self.buscador.text().strip()) or any(
            f.combo is not None and f.combo.currentText() != TODOS for f in self.filtros
        )

    def limpiar_filtros(self) -> None:
        self._cargando_preferencias = True
        try:
            self.buscador.clear()
            for f in self.filtros:
                f.deseado = TODOS
                if f.combo is not None:
                    f.combo.setCurrentIndex(0)
        finally:
            self._cargando_preferencias = False
        self.aplicar()
        self._guardar()

    def resaltar(self, clave: Any) -> None:
        """Resalta la fila con esa clave y la lleva a la vista (la fila nueva)."""
        self._resaltada = clave
        self.mostrar(clave)

    def mostrar(self, clave: Any) -> None:
        """Desplaza la tabla hasta la fila con esa clave (la que se acaba de editar).

        Se llama justo después de recargar la tabla: el orden elegido se repone
        aquí mismo, para que el desplazamiento sea a su sitio definitivo.
        """
        self._a_mostrar = clave
        if self._recargada:
            self._recargada = False
            self._restaurar_orden()
        self.aplicar()

    def aplicar(self) -> None:
        """Oculta lo que no pasa la búsqueda o los filtros; el resto se ve entero."""
        if self._aplicando:
            return
        self._aplicando = True
        self._pendiente = False
        try:
            self._rehacer_opciones()
            tabla = self.tabla
            filas = tabla.rowCount()
            if self._es_aviso_de_vacia():
                tabla.setRowHidden(0, False)
                coincidentes: list[int] = []
            else:
                coincidentes = [f for f in range(filas) if self._coincide(f)]
            self._total = len(coincidentes)
            visibles = set(coincidentes)
            if not self._es_aviso_de_vacia():
                for f in range(filas):
                    tabla.setRowHidden(f, f not in visibles)
            self._pintar_resaltado(visibles)
            if self._a_mostrar is not None:
                fila = next((f for f in coincidentes if self._tiene_clave(f, self._a_mostrar)), None)
                if fila is not None:
                    self._llevar_a_la_vista(fila)
                self._a_mostrar = None
            registros = 0 if self._es_aviso_de_vacia() else filas
            self.recuento.setText(texto_recuento(self._total, registros, self.entidad))
            if self._con_limpiar:
                self.limpiar.setEnabled(self.hay_filtros())
        finally:
            self._aplicando = False

    # --- Interno -----------------------------------------------------------

    def _llevar_a_la_vista(self, fila: int) -> None:
        for c in range(self.tabla.columnCount()):
            item = self.tabla.item(fila, c)
            if item is not None and not self.tabla.isColumnHidden(c):
                self.tabla.scrollToItem(item, QTableWidget.ScrollHint.EnsureVisible)
                return

    def _programar_recarga(self, *_args) -> None:
        if self._aplicando:
            return
        self._recargada = True
        self._programar()

    def _programar(self, *_args) -> None:
        if self._aplicando or self._pendiente:
            return
        self._pendiente = True
        QTimer.singleShot(0, self._tras_cambio_de_tabla)

    def _tras_cambio_de_tabla(self) -> None:
        if not self._pendiente:
            return
        if self._recargada:
            self._recargada = False
            self._restaurar_orden()
        self.aplicar()

    def _restaurar_orden(self) -> None:
        orden = leer_preferencias(self.clave).get("orden")
        tabla = self.tabla
        if not orden or not tabla.isSortingEnabled():
            return
        try:
            columna, descendente = int(orden[0]), bool(orden[1])
        except (TypeError, ValueError, IndexError):
            return
        if not 0 <= columna < tabla.columnCount():
            return
        sentido = Qt.SortOrder.DescendingOrder if descendente else Qt.SortOrder.AscendingOrder
        cabecera = tabla.horizontalHeader()
        if cabecera.sortIndicatorSection() == columna and cabecera.sortIndicatorOrder() == sentido:
            return
        self._aplicando = True
        try:
            tabla.sortItems(columna, sentido)
        finally:
            self._aplicando = False

    def _es_aviso_de_vacia(self) -> bool:
        """La fila «No hay…» de `pintar_tabla_vacia` no es un registro."""
        tabla = self.tabla
        if tabla.rowCount() != 1 or tabla.columnCount() < 2:
            return False
        return tabla.columnSpan(0, 0) == tabla.columnCount()

    def _coincide(self, fila: int) -> bool:
        for f in self.filtros:
            if f.combo is None:
                continue
            elegido = f.combo.currentText()
            if elegido != TODOS and f.valor(self.tabla, fila) != elegido:
                return False
        palabras = _normalizar(self.buscador.text()).split()
        if not palabras:
            return True
        texto = _normalizar(texto_de_celdas(self.tabla, fila, self._columnas_busqueda))
        return all(p in texto for p in palabras)

    def _rehacer_opciones(self) -> None:
        if self._es_aviso_de_vacia():
            valores_por_filtro = {id(f): set() for f in self.filtros}
        else:
            valores_por_filtro = {
                id(f): {
                    v for v in (f.valor(self.tabla, r) for r in range(self.tabla.rowCount())) if v
                }
                for f in self.filtros
            }
        for f in self.filtros:
            combo = f.combo
            if combo is None:
                continue
            opciones = [TODOS] + sorted(valores_por_filtro[id(f)], key=clave_alfabetica)
            actuales = [combo.itemText(i) for i in range(combo.count())]
            if opciones != actuales:
                combo.blockSignals(True)
                combo.clear()
                combo.addItems(opciones)
                combo.blockSignals(False)
            # Lo elegido se mantiene aunque la tabla aún no tenga ese valor (se
            # recuerda de otra sesión y la tabla se llena después).
            objetivo = f.deseado if f.deseado in opciones else TODOS
            if combo.currentText() != objetivo:
                combo.blockSignals(True)
                combo.setCurrentIndex(opciones.index(objetivo))
                combo.blockSignals(False)

    def _al_elegir(self, filtro: Filtro, texto: str) -> None:
        if self._cargando_preferencias:
            return
        filtro.deseado = texto or TODOS
        self._al_cambiar_filtro()

    def _al_cambiar_filtro(self, *_args) -> None:
        if self._cargando_preferencias:
            return
        self.aplicar()
        self._guardar()

    def _tiene_clave(self, fila: int, clave: Any) -> bool:
        if clave is None:
            return False
        try:
            return str(self._clave_fila(self.tabla, fila)) == str(clave)
        except (AttributeError, TypeError, ValueError):
            return False

    def _es_resaltada(self, fila: int) -> bool:
        return self._tiene_clave(fila, self._resaltada)

    def _pintar_resaltado(self, visibles: set) -> None:
        from presentation.theme.modo_oscuro import color_fondo
        from presentation.theme.tokens import Colors

        for item in self._items_resaltados:
            try:
                item.setBackground(QBrush())
                fuente = item.font()
                fuente.setBold(False)
                item.setFont(fuente)
            except RuntimeError:
                pass  # la tabla se recargó y la celda ya no existe
        self._items_resaltados = []
        if self._resaltada is None:
            return
        fondo = QBrush(color_fondo(Colors.PRIMARY_LIGHT))
        for fila in visibles:
            if not self._es_resaltada(fila):
                continue
            for c in range(self.tabla.columnCount()):
                item = self.tabla.item(fila, c)
                if item is None:
                    continue
                item.setBackground(fondo)
                fuente = item.font()
                fuente.setBold(True)
                item.setFont(fuente)
                self._items_resaltados.append(item)
            self._llevar_a_la_vista(fila)

    # --- Recordar ----------------------------------------------------------

    def _cargar_preferencias(self) -> None:
        prefs = leer_preferencias(self.clave)
        self._cargando_preferencias = True
        try:
            texto = prefs.get("busqueda")
            if isinstance(texto, str):
                self.buscador.setText(texto)
            filtros = prefs.get("filtros", {})
            if isinstance(filtros, dict):
                for f in self.filtros:
                    valor = filtros.get(f.clave)
                    if isinstance(valor, str) and valor:
                        f.deseado = valor
            extra = prefs.get("extra", {})
            if isinstance(extra, dict):
                for widget in self._recordar:
                    valor = extra.get(widget.objectName())
                    if not isinstance(valor, str):
                        continue
                    if isinstance(widget, QComboBox):
                        i = widget.findText(valor)
                        if i >= 0:
                            widget.setCurrentIndex(i)
                    elif isinstance(widget, QLineEdit):
                        widget.setText(valor)
        finally:
            self._cargando_preferencias = False
        for widget in self._recordar:
            if isinstance(widget, QComboBox):
                widget.currentTextChanged.connect(lambda _t: self._guardar())
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(lambda _t: self._guardar())

    def _guardar(self) -> None:
        if self._cargando_preferencias:
            return
        valores: dict = {
            "busqueda": self.buscador.text(),
            "filtros": {f.clave: f.deseado for f in self.filtros if f.deseado != TODOS},
        }
        if self.tabla.isSortingEnabled():
            cabecera = self.tabla.horizontalHeader()
            valores["orden"] = [
                cabecera.sortIndicatorSection(),
                cabecera.sortIndicatorOrder() == Qt.SortOrder.DescendingOrder,
            ]
        else:
            anteriores = leer_preferencias(self.clave).get("orden")
            if anteriores:
                valores["orden"] = anteriores
        extra = {}
        for widget in self._recordar:
            if isinstance(widget, QComboBox):
                extra[widget.objectName()] = widget.currentText()
            elif isinstance(widget, QLineEdit):
                extra[widget.objectName()] = widget.text()
        if extra:
            valores["extra"] = extra
        guardar_preferencias(self.clave, valores)


def _clave_de_la_primera_columna(tabla: QTableWidget, fila: int):
    item = tabla.item(fila, 0)
    if item is None:
        return None
    dato = item.data(Qt.ItemDataRole.UserRole)
    return dato if dato is not None else item.text()
