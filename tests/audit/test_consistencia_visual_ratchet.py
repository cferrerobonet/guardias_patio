"""Ratchets de consistencia visual. Umbrales = valor medido en el commit auditado (2026-09-04).
Sólo pueden bajar, salvo subida deliberada y anotada aquí. Ver auditoria/04 y 05.

Subidas registradas:
- 2026-09-06, v5.75.0: `setMinimum` 139 → 140. El diálogo de permutar guardias
  necesita un ancho mínimo para que quepan los dos desplegables; es superficie
  nueva, no deuda que crece.
- 2026-09-05, v5.56.0: `setStyleSheet` 287 → 289 (vista de estado del curso y aviso
  de bloqueo del panel de generación).
- 2026-09-05, v5.57.0: vuelve a 288 al retirarse la vista de estado del curso.

Bajadas registradas (lote 8, v5.58.0):
- `font_size_menor_12px` 89 → 0: el contrato de diseño fija 12 px como mínimo
  absoluto y había usos de hasta 7 px.
- `hex_literales` 631 → 526 (y `tokens.py` sale del recuento: es donde el color
  debe vivir, contarlo allí penalizaba centralizarlo).
- `setStyleSheet` 288 → 260 (v5.65.0): las hojas repetidas literalmente pasan a
  reglas semánticas de `light.qss` (`#tituloDialogo`, `[caja="aviso"]`…). El resto
  son estilos únicos por widget: sacarlos exige mirar cada vista, y eso sigue
  siendo el grueso de VIS-001."""

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PRES = ROOT / "src" / "presentation"
UMBRALES = {
    # 238 desde v5.89.0: extraídos a la hoja los estilos que estaban escritos
    # dos o tres veces. Los ~157 que quedan son distintos entre sí —ajustes de
    # un widget concreto—, así que sacarlos crearía un rol por widget.
    "setStyleSheet": 238,
    "hex_literales": 467,
    "font_size_menor_12px": 0,
    "qfont_menor_9pt": 0,
    "lineas_con_emoji": 315,
    # 17 desde v5.95.0: las casillas de la matriz de disponibilidad dejan de
    # tener tamaño fijo para poder estirarse. Un tamaño fijo es peor que un
    # mínimo cuando la pantalla escala (UXA-001), así que el cambio va en la
    # dirección buena aunque suba el contador de al lado.
    "setFixed": 17,
    # 142 desde v5.79.0. Sube una por el diálogo de envío de avisos (v5.78.0),
    # que parte la ventana en destinatarios y vista previa, y otra por el informe
    # previo de importación, que necesita una tabla de cuatro columnas legible.
    # Ya van tres subidas seguidas por diálogos nuevos: el mínimo de un diálogo
    # con tabla debería salir de un sitio común en vez de repetirse en cada uno.
    "setMinimum": 143,
}
EMOJI = re.compile("[\U0001f300-\U0001faff☀-➿]")


#: `tokens.py` queda fuera del recuento de colores: es el sitio donde los colores
#: DEBEN estar. Contarlo ahí penalizaba justo el movimiento que se persigue —sacar
#: el color de las vistas y centralizarlo— y convertía el ratchet en un incentivo
#: al revés.
FICHEROS_EXENTOS_DE_COLOR = {"tokens.py"}


def _fuentes():
    return [p.read_text(encoding="utf-8", errors="ignore") for p in PRES.rglob("*.py")]


def _fuentes_sin_tokens():
    return [
        p.read_text(encoding="utf-8", errors="ignore")
        for p in PRES.rglob("*.py")
        if p.name not in FICHEROS_EXENTOS_DE_COLOR
    ]


def _contar():
    textos = _fuentes()
    todo = "\n".join(textos)
    return {
        "setStyleSheet": todo.count("setStyleSheet"),
        "hex_literales": len(
            re.findall(r"#[0-9A-Fa-f]{6}\b", "\n".join(_fuentes_sin_tokens()))
        ),
        "font_size_menor_12px": sum(
            1 for m in re.findall(r"font-size: ?(\d+)px", todo) if int(m) < 12
        ),
        # Los gráficos no usan hojas de estilo: pintan con QFont, y por ahí se
        # colaban rótulos de 7 pt —unos 9 px— que el contador de arriba no veía
        # (UXA-014). 9 pt es el equivalente al mínimo de 12 px.
        "qfont_menor_9pt": sum(
            1 for m in re.findall(r"QFont\([^)]*?,\s*(\d+)", todo) if int(m) < 9
        ),
        "lineas_con_emoji": sum(1 for line in todo.splitlines() if EMOJI.search(line)),
        "setFixed": len(re.findall(r"setFixed(?:Size|Width|Height)\(", todo)),
        "setMinimum": len(re.findall(r"setMinimum(?:Size|Width|Height)\(", todo)),
    }


@pytest.mark.parametrize("metrica", sorted(UMBRALES))
def test_ratchet_no_empeora(metrica):
    valor = _contar()[metrica]
    assert valor <= UMBRALES[metrica], (
        f"{metrica}: {valor} > {UMBRALES[metrica]}. Si has reducido deuda, baja el umbral; "
        "nunca lo subas."
    )


def test_tokens_no_definen_dos_primarios_distintos():
    """VIS-002: los paneles usan Tailwind (#3B82F6/#10B981) mientras tokens usan #007ACC/#1E7E34."""
    todo = "\n".join(_fuentes()).upper()
    tailwind = {"#3B82F6", "#10B981", "#059669", "#2563EB"}
    usados = {c for c in tailwind if c in todo}
    if usados:
        pytest.xfail(f"VIS-002: colores fuera de tokens en uso: {sorted(usados)}")


def test_fuente_global_existe_en_windows():
    """VIS-003: '-apple-system' no es una familia válida en Windows/Linux."""
    main = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
    if 'QFont("-apple-system")' in main:
        pytest.xfail("VIS-003: fuente global -apple-system; usar pila por SO")


# ---------------------------------------------------------------------------
# VIS-001: la hoja de estilos se construye desde los tokens
# ---------------------------------------------------------------------------
QSS = ROOT / "src" / "presentation" / "theme" / "light.qss"

#: Colores que siguen escritos a mano en light.qss por no tener token todavía.
#: Sólo puede bajar: cada uno que se resuelva es un token nuevo o un duplicado menos.
LITERALES_SIN_TOKEN = 28


def test_la_hoja_de_estilos_no_repite_colores_que_ya_son_token():
    """Si un color tiene token, en la hoja va el marcador, no el hexadecimal."""
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from presentation.theme.tokens import Colors

    con_token = {
        v.upper() for v in vars(Colors).values() if isinstance(v, str) and v.startswith("#")
    }
    texto = QSS.read_text(encoding="utf-8")
    repetidos = sorted({h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", texto)} & con_token)

    assert not repetidos, (
        f"estos colores tienen token y están escritos a mano en light.qss: {repetidos}"
    )


def test_ratchet_de_colores_sueltos_en_la_hoja():
    literales = re.findall(r"#[0-9A-Fa-f]{6}\b", QSS.read_text(encoding="utf-8"))
    assert len(literales) <= LITERALES_SIN_TOKEN, (
        f"{len(literales)} colores sin token en light.qss (umbral {LITERALES_SIN_TOKEN}). "
        "Si añades color, dale un token; si has resuelto alguno, baja el umbral."
    )


def test_la_hoja_construida_no_deja_marcadores_sin_resolver():
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from presentation.theme.hoja_de_estilos import construir_hoja_de_estilos

    hoja = construir_hoja_de_estilos()
    assert hoja, "la hoja de estilos salió vacía"
    assert not re.findall(r"@[A-Z_]+@", hoja), "quedan marcadores sin token"
    # Y la familia tipográfica es la del sistema, no la del navegador.
    assert "-apple-system" not in hoja


def test_un_unico_minimo_de_ventana():
    """VIS-009: había 1400x900 en la ventana y 1200x800 en ajustes."""
    import inspect
    import sys

    sys.path.insert(0, str(ROOT / "src"))
    from presentation import ventana_principal

    fuente = inspect.getsource(ventana_principal.VentanaPrincipal.setup_ui)
    assert "setMinimumSize(1400, 900)" not in fuente
    assert "window_min_width" in fuente
