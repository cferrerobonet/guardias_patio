"""Buscador, filtros, orden y paginación para las tablas que crecen (GUA-UXI-005).

El mismo patrón que los listados de la web de pedidos (`list-view-utils.js`) y que
la tabla paginada de Partes de salida: buscador, filtros por columna (profesor,
zona, turno, estado), «Limpiar filtros», cabeceras ordenables, filas por página
(5/10/15/20/50, 10 de serie), pie «Mostrando 1–10 de N» con primera, anterior,
cinco números, siguiente y última —los extremos se desactivan, no desaparecen— y
la fila nueva resaltada.

Se monta **encima** de un `QTableWidget` ya existente: la vista lo sigue llenando
como siempre y aquí solo se ocultan las filas que no tocan. Los filtros, las filas
por página y el orden se recuerdan entre sesiones, en `preferencias_listados.json`
de la carpeta de datos.
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
    QTableWidget,
    QWidget,
)

from utils.orden import clave_alfabetica

logger = logging.getLogger(__name__)

POR_PAGINA = (5, 10, 15, 20, 50)
POR_PAGINA_DE_SERIE = 10
TODOS = "Todos"


# --- Cálculos sin interfaz --------------------------------------------------


def ventana_paginas(actual: int, total: int) -> list[int]:
    """Los cinco números del pie, como en la web de pedidos: desde la actual − 2."""
    total = max(1, total)
    actual = max(1, min(actual, total))
    inicio = max(1, actual - 2)
    return list(range(inicio, min(total, inicio + 4) + 1))


def texto_recuento(pagina: int, por_pagina: int, total: int, entidad: str = "") -> str:
    """«Mostrando 1–10 de 42 profesores», o «Sin resultados» a cero."""
    if total <= 0:
        return "Sin resultados"
    desde = (pagina - 1) * por_pagina + 1
    hasta = min(pagina * por_pagina, total)
    return f"Mostrando {desde}–{hasta} de {total} {entidad}".rstrip()


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
    """Ctrl+A sobre una tabla filtrada o paginada: solo lo que está a la vista."""
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
    """Buscador, filtros y paginación sobre un `QTableWidget` que llena su vista.

    La vista coloca `barra` encima de la tabla y `pie` debajo. Para resaltar la
    fila recién creada, llama a `resaltar(clave)` después de recargar la tabla;
    `clave_fila(tabla, fila)` dice qué clave tiene cada fila.
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
    ):
        super().__init__(tabla)
        self.tabla = tabla
        self.clave = clave
        self.entidad = entidad
        self.filtros: list[Filtro] = list(filtros)
        self._columnas_busqueda = columnas_busqueda
        self._clave_fila = clave_fila or _clave_de_la_primera_columna
        self._recordar = list(recordar)
        self._pagina = 1
        self._paginas = 1
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
        capa = QHBoxLayout(self.barra)
        capa.setContentsMargins(0, 0, 0, 0)
        capa.setSpacing(8)
        self._buscador_propio = buscador is None
        self.buscador = buscador or QLineEdit()
        if self._buscador_propio and con_buscador:
            self.buscador.setPlaceholderText(marcador)
            self.buscador.setClearButtonEnabled(True)
            self.buscador.setAccessibleName(f"Buscar en {entidad or 'la tabla'}")
            capa.addWidget(self.buscador, 1)
        self.buscador.textChanged.connect(self._al_cambiar_filtro)

        for filtro in self.filtros:
            etiqueta = QLabel(f"{filtro.etiqueta}:")
            etiqueta.setObjectName("smallFieldLabel")
            combo = QComboBox()
            combo.setAccessibleName(f"Filtrar por {filtro.etiqueta.lower()}")
            combo.addItem(TODOS)
            combo.currentTextChanged.connect(lambda texto, f=filtro: self._al_elegir(f, texto))
            filtro.combo = combo
            etiqueta.setBuddy(combo)
            capa.addWidget(etiqueta)
            capa.addWidget(combo)

        etiqueta_pp = QLabel("Por página:")
        etiqueta_pp.setObjectName("smallFieldLabel")
        self.por_pagina = QComboBox()
        self.por_pagina.setAccessibleName("Filas por página")
        for n in POR_PAGINA:
            self.por_pagina.addItem(str(n), n)
        self.por_pagina.setCurrentIndex(POR_PAGINA.index(POR_PAGINA_DE_SERIE))
        self.por_pagina.currentIndexChanged.connect(self._al_cambiar_filtro)
        etiqueta_pp.setBuddy(self.por_pagina)
        capa.addWidget(etiqueta_pp)
        capa.addWidget(self.por_pagina)

        self._con_limpiar = con_limpiar
        if boton_limpiar is None:
            self.limpiar = QPushButton("Limpiar filtros")
            self.limpiar.setProperty("secondary", "true")
            if con_limpiar:
                capa.addWidget(self.limpiar)
        else:
            self.limpiar = boton_limpiar
        if con_limpiar:
            self.limpiar.setToolTip("Quitar la búsqueda y los filtros")
            self.limpiar.clicked.connect(self.limpiar_filtros)

        # Pie: recuento y paginación
        self.pie = QWidget()
        self.pie.setObjectName("pieDeListado")
        capa_pie = QHBoxLayout(self.pie)
        capa_pie.setContentsMargins(0, 0, 0, 0)
        capa_pie.setSpacing(4)
        self.recuento = QLabel("")
        self.recuento.setObjectName("secondary")
        self.recuento.setAccessibleName("Recuento de filas")
        capa_pie.addWidget(self.recuento)
        capa_pie.addStretch(1)
        self.botones: dict[str, QPushButton] = {}
        for nombre, texto, ayuda in (
            ("primera", "«", "Primera página"),
            ("anterior", "‹", "Página anterior"),
        ):
            self.botones[nombre] = self._boton(texto, ayuda)
            capa_pie.addWidget(self.botones[nombre])
        self.numeros: list[QPushButton] = []
        for _ in range(5):
            b = self._boton("", "Número de página")
            b.setCheckable(True)
            self.numeros.append(b)
            capa_pie.addWidget(b)
        for nombre, texto, ayuda in (
            ("siguiente", "›", "Página siguiente"),
            ("ultima", "»", "Última página"),
        ):
            self.botones[nombre] = self._boton(texto, ayuda)
            capa_pie.addWidget(self.botones[nombre])
        self.botones["primera"].clicked.connect(lambda: self.ir(1))
        self.botones["anterior"].clicked.connect(lambda: self.ir(self._pagina - 1))
        self.botones["siguiente"].clicked.connect(lambda: self.ir(self._pagina + 1))
        self.botones["ultima"].clicked.connect(lambda: self.ir(self._paginas))
        for b in self.numeros:
            b.clicked.connect(lambda _=False, boton=b: self.ir(int(boton.text() or 1)))

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
    def pagina(self) -> int:
        return self._pagina

    @property
    def paginas(self) -> int:
        return self._paginas

    @property
    def total(self) -> int:
        """Filas que pasan la búsqueda y los filtros."""
        return self._total

    def hay_filtros(self) -> bool:
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
        self._pagina = 1
        self.aplicar()
        self._guardar()

    def resaltar(self, clave: Any) -> None:
        """Resalta la fila con esa clave y salta a su página (la fila nueva)."""
        self._resaltada = clave
        self.mostrar(clave)

    def mostrar(self, clave: Any) -> None:
        """Salta a la página de la fila con esa clave (la que se acaba de editar).

        Se llama justo después de recargar la tabla: el orden elegido se repone
        aquí mismo, para que la página sea la de su sitio definitivo.
        """
        self._a_mostrar = clave
        if self._recargada:
            self._recargada = False
            self._restaurar_orden()
        self.aplicar()

    def ir(self, pagina: int) -> None:
        self._pagina = pagina
        self.aplicar()

    def aplicar(self) -> None:
        """Oculta lo que no pasa los filtros o no cabe en la página actual."""
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
            n = int(self.por_pagina.currentData() or POR_PAGINA_DE_SERIE)
            self._total = len(coincidentes)
            self._paginas = max(1, -(-self._total // n))
            if self._a_mostrar is not None:
                indice = next(
                    (
                        i
                        for i, f in enumerate(coincidentes)
                        if self._tiene_clave(f, self._a_mostrar)
                    ),
                    None,
                )
                if indice is not None:
                    self._pagina = indice // n + 1
                self._a_mostrar = None
            self._pagina = max(1, min(self._pagina, self._paginas))
            visibles = set(coincidentes[(self._pagina - 1) * n : self._pagina * n])
            if not self._es_aviso_de_vacia():
                for f in range(filas):
                    tabla.setRowHidden(f, f not in visibles)
            self._pintar_resaltado(visibles)
            self.recuento.setText(texto_recuento(self._pagina, n, self._total, self.entidad))
            self._pintar_pie()
            if self._con_limpiar:
                self.limpiar.setEnabled(self.hay_filtros())
        finally:
            self._aplicando = False

    # --- Interno -----------------------------------------------------------

    def _boton(self, texto: str, ayuda: str) -> QPushButton:
        b = QPushButton(texto)
        b.setProperty("pagina", "true")
        b.setToolTip(ayuda)
        b.setAccessibleName(ayuda)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        return b

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
        self._pagina = 1
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
            primera = self.tabla.item(fila, 0)
            if primera is not None:
                self.tabla.scrollToItem(primera)

    def _pintar_pie(self) -> None:
        actual, total = self._pagina, self._paginas
        self.botones["primera"].setEnabled(actual > 1)
        self.botones["anterior"].setEnabled(actual > 1)
        self.botones["siguiente"].setEnabled(actual < total)
        self.botones["ultima"].setEnabled(actual < total)
        numeros = ventana_paginas(actual, total)
        for i, b in enumerate(self.numeros):
            if i < len(numeros):
                p = numeros[i]
                b.setText(str(p))
                b.setChecked(p == actual)
                b.setToolTip(f"Página {p}")
                b.setAccessibleName(f"Página {p}" + (", actual" if p == actual else ""))
                b.setVisible(True)
            else:
                b.setVisible(False)

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
            n = prefs.get("por_pagina")
            if n in POR_PAGINA:
                self.por_pagina.setCurrentIndex(POR_PAGINA.index(n))
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
            "por_pagina": int(self.por_pagina.currentData() or POR_PAGINA_DE_SERIE),
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
