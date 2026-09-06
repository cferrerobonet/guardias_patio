"""
Utilidades para la interfaz de usuario.

Funciones helper para aplicar marca corporativa de forma discreta.
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QPixmapCache
from PyQt6.QtWidgets import QApplication, QMessageBox, QWidget

from core.logging import get_logger

logger = get_logger(__name__)


def announce(message: str, widget: Optional[QWidget] = None) -> None:
    """
    Anuncia un mensaje a lectores de pantalla mediante QAccessible.

    Emite un evento sobre el widget dado o sobre el widget con foco activo.
    Es un no-op si QAccessible no está disponible en esta build de PyQt6.

    Args:
        message: Texto a anunciar (corto y descriptivo).
        widget: Widget sobre el que emitir el evento; si es None usa el foco.
    """
    logger.debug("[a11y] announce: %s", message[:80])
    try:
        from PyQt6.QtGui import QAccessible, QAccessibleEvent  # type: ignore[attr-defined]
        target = widget or (QApplication.focusWidget() if QApplication.instance() else None)
        if target is not None:
            event = QAccessibleEvent(target, QAccessible.Event.NameChanged)
            QAccessible.updateAccessibility(event)
    except (ImportError, AttributeError, RuntimeError):
        pass  # QAccessible no disponible en esta build — ignorar

# Estilos consistentes para todos los QMessageBox
MESSAGEBOX_STYLE = """
    QMessageBox {
        background-color: white !important;
        min-width: 400px;
    }
    QMessageBox QLabel {
        color: #1f2937 !important;
        font-size: 14px;
        padding: 10px;
    }
    QMessageBox QPushButton {
        background-color: #166529 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        padding: 8px 24px !important;
        border: 2px solid #047857 !important;
        border-radius: 6px !important;
        min-width: 100px !important;
        min-height: 35px !important;
    }
    QMessageBox QPushButton:hover {
        background-color: #047857 !important;
    }
    QMessageBox QPushButton:pressed {
        background-color: #065f46 !important;
    }
    QMessageBox QPushButton:default {
        background-color: #0284c7 !important;
        border: 2px solid #0369a1 !important;
    }
    QMessageBox QPushButton:default:hover {
        background-color: #0369a1 !important;
    }
"""


def _get_logo_path() -> Path:
    return Path(__file__).parent.parent.parent / "imagenes" / "logo.png"


def _get_icons_dir() -> Path:
    return Path(__file__).parent.parent.parent / "imagenes" / "icons"


def get_icon(name: str, fallback: str = "") -> QIcon:
    """
    Obtiene un icono del directorio de iconos centralizado (imagenes/icons/).

    Busca primero ``<name>.svg``, luego ``<name>.png``. Si no existe,
    devuelve el ``fallback`` o un QIcon vacío. Usa QPixmapCache para
    evitar lecturas repetidas de disco.

    Args:
        name: Nombre del icono sin extensión (ej: "calendar", "delete").
        fallback: Nombre alternativo si el principal no existe.

    Returns:
        QIcon cargado desde disco, o QIcon vacío si no se encuentra.
    """
    icons_dir = _get_icons_dir()
    for candidate in ([name, fallback] if fallback else [name]):
        if not candidate:
            continue
        for ext in ("svg", "png"):
            path = icons_dir / f"{candidate}.{ext}"
            if path.exists():
                cache_key = str(path)
                px = QPixmapCache.find(cache_key)
                if px is None:
                    px = QPixmap(str(path))
                    if not px.isNull():
                        QPixmapCache.insert(cache_key, px)
                if px and not px.isNull():
                    return QIcon(px)
    return QIcon()

def _get_cached_pixmap(path: Path) -> Optional[QPixmap]:
    cache_key = str(path)
    cached = QPixmapCache.find(cache_key)
    if cached is not None:
        return cached

    pixmap = QPixmap(str(path))
    if pixmap.isNull():
        return None

    QPixmapCache.insert(cache_key, pixmap)
    return pixmap


def get_corporate_icon() -> QIcon:
    """
    Obtiene el icono corporativo de forma discreta.

    Returns:
        QIcon con el logo corporativo si existe, icono vacío si no.
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            return QIcon(str(icon_path))
    except (OSError, ValueError, RuntimeError):
        pass
    return QIcon()  # Fallback a icono por defecto


def get_corporate_pixmap(size: int = 64) -> Optional[QPixmap]:
    """
    Obtiene el pixmap del logo corporativo escalado.

    Args:
        size: Tamaño del icono en píxeles (por defecto 64x64)

    Returns:
        QPixmap con el logo corporativo escalado, None si no existe.
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            pixmap = _get_cached_pixmap(icon_path)
            if pixmap is not None:
                return pixmap.scaled(
                    size,
                    size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
    except Exception as e:
        logger.warning(f"Error cargando logo corporativo: {e}")
    return None


def apply_corporate_icon_to_messagebox(msg_box: QMessageBox) -> None:
    """
    Aplica el icono corporativo a un QMessageBox de forma confiable.

    En macOS, setIconPixmap() no siempre funciona, así que este método
    intenta múltiples enfoques.

    Args:
        msg_box: El QMessageBox al que aplicar el icono
    """
    try:
        icon_path = _get_logo_path()
        if icon_path.exists():
            pixmap = _get_cached_pixmap(icon_path)
            if pixmap is not None:
                # Escalar el pixmap
                scaled_pixmap = pixmap.scaled(
                    64,
                    64,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                # Forzar el uso del pixmap personalizado
                msg_box.setIconPixmap(scaled_pixmap)
                # No establecer un icono estándar, solo el pixmap
                return
    except Exception as e:
        logger.warning(f"Error aplicando icono corporativo: {e}")

    # Fallback: usar icono estándar de pregunta
    msg_box.setIcon(QMessageBox.Icon.Question)


def show_info(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra un mensaje informativo con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje a mostrar
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo sin establecer icono estándar primero
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_warning(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra una advertencia con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de advertencia
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_error(parent: Optional[QWidget], title: str, message: str) -> None:
    """
    Muestra un error con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de error
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    msg_box.exec()


def show_question(
    parent: Optional[QWidget], title: str, message: str, default_no: bool = True
) -> int:
    """
    Muestra una pregunta con icono corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Pregunta
        default_no: Si True, el botón No es el predeterminado

    Returns:
        Código de respuesta del botón presionado
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    if default_no:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec()


def show_question_with_cancel(
    parent: Optional[QWidget], title: str, message: str, default_button: str = "No"
) -> int:
    """
    Muestra una pregunta con Yes/No/Cancel y logo corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Pregunta
        default_button: Botón predeterminado ("Yes", "No", "Cancel")

    Returns:
        Código de respuesta del botón presionado (QMessageBox.StandardButton)
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(
        QMessageBox.StandardButton.Yes
        | QMessageBox.StandardButton.No
        | QMessageBox.StandardButton.Cancel
    )

    if default_button == "Yes":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    elif default_button == "Cancel":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec()


def show_confirmation(
    parent: Optional[QWidget], title: str, message: str, default_button: str = "No"
) -> bool:
    """
    Muestra una confirmación Yes/No con logo corporativo.

    Args:
        parent: Widget padre
        title: Título del diálogo
        message: Mensaje de confirmación
        default_button: Botón predeterminado ("Yes" o "No")

    Returns:
        True si se presionó Yes, False si se presionó No
    """
    msg_box = QMessageBox(parent)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setWindowIcon(get_corporate_icon())

    # Aplicar icono corporativo
    apply_corporate_icon_to_messagebox(msg_box)

    msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

    if default_button == "Yes":
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
    else:
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)

    # Aplicar estilos
    msg_box.setStyleSheet(MESSAGEBOX_STYLE)

    return msg_box.exec() == QMessageBox.StandardButton.Yes


# ---------------------------------------------------------------------------
# Nombres accesibles (UXA-005)
# ---------------------------------------------------------------------------

#: Controles que un lector de pantalla anuncia y que, por tanto, necesitan nombre.
_TIPOS_INTERACTIVOS = (
    "QLineEdit",
    "QPlainTextEdit",
    "QTextEdit",
    "QComboBox",
    "QCheckBox",
    "QRadioButton",
    "QSpinBox",
    "QDoubleSpinBox",
    "QDateEdit",
    "QTimeEdit",
    "QDateTimeEdit",
    "QPushButton",
    "QToolButton",
    "QTableWidget",
    "QTableView",
    "QListWidget",
    "QTreeWidget",
)


def _limpiar_etiqueta(texto: str) -> str:
    """Deja el texto de una etiqueta en algo pronunciable."""
    import re

    texto = re.sub(r"<[^>]+>", " ", texto or "")          # marcado HTML
    texto = re.sub(r"[\U0001f300-\U0001faff☀-➿]", " ", texto)  # emojis
    texto = texto.replace("&", "")                          # acelerador de Qt
    texto = re.sub(r"[\s:*]+$", "", texto.strip())          # dos puntos y asteriscos finales
    return re.sub(r"\s{2,}", " ", texto).strip()


def _nombre_desde_la_etiqueta_asociada(campo) -> str:
    """Busca la etiqueta que acompaña al campo en su formulario."""
    from PyQt6.QtWidgets import QFormLayout, QLabel

    padre = campo.parentWidget()
    while padre is not None:
        distribucion = padre.layout()
        if isinstance(distribucion, QFormLayout):
            etiqueta = distribucion.labelForField(campo)
            if isinstance(etiqueta, QLabel) and etiqueta.text():
                return _limpiar_etiqueta(etiqueta.text())
        padre = padre.parentWidget()

    # Etiqueta con `buddy` explícito
    ventana = campo.window()
    if ventana is not None:
        for etiqueta in ventana.findChildren(QLabel):
            if etiqueta.buddy() is campo and etiqueta.text():
                return _limpiar_etiqueta(etiqueta.text())
    return ""


def _nombre_desde_el_grupo(campo) -> str:
    """Último recurso: el título del recuadro que lo contiene.

    Sirve sobre todo para tablas y listas, que no llevan etiqueta propia pero sí
    viven dentro de un grupo con título ("Zonas registradas") (UXA-008).
    """
    from PyQt6.QtWidgets import QGroupBox

    padre = campo.parentWidget()
    while padre is not None:
        if isinstance(padre, QGroupBox) and padre.title():
            return _limpiar_etiqueta(padre.title())
        padre = padre.parentWidget()
    return ""


def _nombre_propio_del_control(campo) -> str:
    """Nombre deducible del propio control, sin mirar alrededor."""
    for atributo in ("placeholderText", "text", "toolTip"):
        obtener = getattr(campo, atributo, None)
        if obtener is None:
            continue
        try:
            valor = _limpiar_etiqueta(obtener())
        except TypeError:
            continue
        if valor:
            return valor
    return ""


def asignar_nombres_accesibles(raiz: QWidget) -> int:
    """Da nombre accesible a los controles que no lo tengan.

    Un lector de pantalla anuncia el `accessibleName`; sin él dice sólo el tipo
    de control ("cuadro de edición") y la pantalla resulta inoperable a ciegas
    (UXA-005). El nombre se deduce, por este orden, de la etiqueta asociada en el
    formulario, del texto de marcador de posición, del texto del propio control o
    de su descripción emergente.

    Devuelve cuántos controles ha nombrado. No pisa los nombres ya puestos a mano.
    """
    from PyQt6.QtWidgets import QWidget as _QWidget

    nombrados = 0
    for hijo in raiz.findChildren(_QWidget):
        if type(hijo).__name__ not in _TIPOS_INTERACTIVOS:
            continue
        if hijo.accessibleName():
            continue

        nombre = (
            _nombre_desde_la_etiqueta_asociada(hijo)
            or _nombre_propio_del_control(hijo)
            or _nombre_desde_el_grupo(hijo)
        )
        if nombre:
            hijo.setAccessibleName(nombre)
            nombrados += 1
    return nombrados


# ---------------------------------------------------------------------------
# Carpetas recordadas (UXF-010)
# ---------------------------------------------------------------------------

_ORGANIZACION = "EPLA"
_APLICACION = "GuardiasDePatio"


def ultima_carpeta(clave: str = "exportacion") -> str:
    """Última carpeta que se usó para esa clase de guardado.

    Antes cada diálogo abría en el directorio por omisión: en septiembre, con
    cinco exportaciones seguidas, había que rebuscar la misma carpeta cada vez
    (UXF-010).
    """
    from PyQt6.QtCore import QSettings

    ajustes = QSettings(_ORGANIZACION, _APLICACION)
    guardada = ajustes.value(f"carpetas/{clave}", "", type=str)
    return guardada if guardada and Path(guardada).is_dir() else ""


def recordar_carpeta(carpeta: str, clave: str = "exportacion") -> None:
    """Guarda la carpeta elegida para proponerla la próxima vez."""
    from PyQt6.QtCore import QSettings

    if not carpeta:
        return
    ruta = Path(carpeta)
    destino = ruta if ruta.is_dir() else ruta.parent
    QSettings(_ORGANIZACION, _APLICACION).setValue(f"carpetas/{clave}", str(destino))


def pedir_carpeta(
    parent: Optional[QWidget],
    titulo: str = "Seleccionar carpeta",
    clave: str = "exportacion",
) -> str:
    """Pide una carpeta empezando por la última usada, y recuerda la elegida."""
    from PyQt6.QtWidgets import QFileDialog

    carpeta = QFileDialog.getExistingDirectory(
        parent, titulo, ultima_carpeta(clave), QFileDialog.Option.ShowDirsOnly
    )
    recordar_carpeta(carpeta, clave)
    return carpeta


def dotar_de_contrato(
    tabla,
    nombre: str,
    descripcion: str = "",
    ordenable: bool = False,
) -> None:
    """Da a una tabla lo mínimo para poder usarla sin ver la pantalla (UXA-008).

    Un `QTableWidget` recién creado no dice qué contiene: un lector de pantalla
    anuncia «tabla» y poco más. Aquí se le pone nombre y descripción, se permite
    ordenar por la cabecera y se alternan los colores de fila, que es lo que
    tenían ya Profesores y Zonas y no el resto.
    """
    tabla.setAccessibleName(nombre)
    if descripcion:
        tabla.setAccessibleDescription(descripcion)
    if ordenable:
        # Ojo: Qt reordena a cada `setItem`, así que llenar la tabla con el orden
        # activo baraja las filas a medio escribirlas. Quien la llene tiene que
        # hacerlo dentro de `llenando_tabla()`.
        tabla.setSortingEnabled(True)
    tabla.setAlternatingRowColors(True)
    cabecera = tabla.horizontalHeader()
    if cabecera is not None:
        cabecera.setAccessibleName(f"Cabecera de {nombre.lower()}")


def pintar_tabla_vacia(tabla, mensaje: str) -> bool:
    """Si la tabla no tiene filas, escribe una que explique por qué (UXA-008).

    Una tabla vacía y una tabla que aún no ha cargado se ven igual: en blanco.
    Devuelve True si ha tenido que escribir el mensaje.
    """
    from PyQt6.QtCore import Qt
    from PyQt6.QtGui import QColor
    from PyQt6.QtWidgets import QTableWidgetItem

    if tabla.rowCount() > 0:
        return False

    columnas = max(1, tabla.columnCount())
    tabla.setRowCount(1)
    celda = QTableWidgetItem(mensaje)
    celda.setFlags(Qt.ItemFlag.ItemIsEnabled)
    celda.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    celda.setForeground(QColor("#6B7280"))
    tabla.setItem(0, 0, celda)
    if columnas > 1:
        tabla.setSpan(0, 0, 1, columnas)
    return True


@contextmanager
def llenando_tabla(tabla):
    """Suspende la ordenación mientras se escriben las filas (UXA-008).

    Con el orden activo, Qt recoloca la tabla cada vez que se pone una celda: la
    fila que se estaba rellenando se mueve y las celdas siguientes acaban en
    otra. Al salir se restaura el estado anterior y se reordena una sola vez.
    """
    estaba = tabla.isSortingEnabled()
    tabla.setSortingEnabled(False)
    try:
        yield tabla
    finally:
        tabla.setSortingEnabled(estaba)


def aplicar_caja(etiqueta, papel: str) -> None:
    """Cambia el papel de un recuadro de estado y lo repinta.

    Cambiar una propiedad no repinta nada por su cuenta: Qt sólo evalúa los
    selectores por propiedad al aplicar la hoja de estilos. Sin este repolish,
    los avisos de la configuración inicial se quedaban con el color del primer
    pintado por mucho que cambiara el texto.
    """
    etiqueta.setProperty("caja", papel)
    estilo = etiqueta.style()
    if estilo is not None:
        estilo.unpolish(etiqueta)
        estilo.polish(etiqueta)
