"""Lote 18 bis — lo que sólo se rompía en la aplicación instalada.

Tres fallos que la suite no veía porque en desarrollo todo está en su sitio:
- CFG-001: la configuración del servidor se congelaba al importar el módulo, antes
  de que nadie hubiera leído el `.env` de la carpeta del usuario, así que la
  aplicación instalada decía que no había nube aunque estuviera configurada;
- UXF-012: la pantalla de arranque tapaba los avisos y sus botones no recibían el
  clic, dejando la aplicación bloqueada;
- VIS-010: la hoja de estilos no viajaba dentro del paquete.
"""

import importlib
import re
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SRC = RAIZ / "src"


@pytest.fixture
def config_sftp(tmp_path, monkeypatch):
    """El módulo recién importado, con el entorno bajo control y sin `.env` real."""
    import config.sftp_config as modulo

    modulo = importlib.reload(modulo)
    # El orden importa: importar el módulo ya lee un `.env`, así que las
    # variables se limpian **después** de recargarlo. A partir de aquí sólo se
    # mira el `.env` de la carpeta temporal, nunca el de desarrollo, que lleva
    # los datos reales del centro (barrera antes que test).
    for clave in ("SFTP_HOST", "SFTP_PORT", "SFTP_USERNAME", "SFTP_USER", "SFTP_BASE_DIR"):
        monkeypatch.delenv(clave, raising=False)
    monkeypatch.setattr(modulo, "_rutas_candidatas", lambda: [tmp_path / ".env"])
    monkeypatch.setattr(modulo, "_contrasena_sftp", lambda: "")
    return modulo


# ---------------------------------------------------------------------------
# CFG-001 · la configuración se lee cuando se pide
# ---------------------------------------------------------------------------
def test_lo_configurado_despues_de_importar_tambien_cuenta(config_sftp, monkeypatch):
    """El caso real: el `.env` del usuario se carga después de importar este módulo."""
    assert config_sftp.validate_sftp_config() is False

    monkeypatch.setenv("SFTP_HOST", "servidor.ejemplo.es")
    monkeypatch.setenv("SFTP_USERNAME", "jefatura")
    monkeypatch.setattr(config_sftp, "_contrasena_sftp", lambda: "secreta")

    assert config_sftp.validate_sftp_config() is True
    assert config_sftp.get_sftp_config()["host"] == "servidor.ejemplo.es"


def test_el_env_se_busca_en_la_carpeta_del_usuario(config_sftp, tmp_path, monkeypatch):
    """Dentro del paquete no se puede escribir: el `.env` vive con los datos."""
    assert config_sftp._ruta_del_env() == tmp_path / ".env"

    (tmp_path / ".env").write_text(
        "SFTP_HOST=desde-el-fichero.es\nSFTP_USERNAME=jefatura\n", encoding="utf-8"
    )
    monkeypatch.setattr(config_sftp, "_contrasena_sftp", lambda: "secreta")

    assert config_sftp.get_sftp_config()["host"] == "desde-el-fichero.es"


def test_un_puerto_mal_escrito_no_tumba_el_arranque(config_sftp, monkeypatch):
    monkeypatch.setenv("SFTP_PORT", "no-es-un-numero")
    assert config_sftp.leer_configuracion()["port"] == 22


def test_sin_configuracion_no_se_inventa_ningun_servidor(config_sftp):
    config = config_sftp.leer_configuracion()
    assert config["host"] == "" and config["username"] == ""


# ---------------------------------------------------------------------------
# UXF-012 · los avisos tienen que poder pulsarse
# ---------------------------------------------------------------------------
def test_la_pantalla_de_arranque_se_quita_antes_de_cada_aviso():
    fuente = (SRC / "main.py").read_text(encoding="utf-8")
    assert "def ocultar_arranque()" in fuente

    # Cada aviso posterior a la pantalla de arranque la esconde primero.
    inicio = fuente.index("arranque = abrir_pantalla_de_arranque()")
    tramo = fuente[inicio:]
    avisos = list(re.finditer(r"\b(msg|aviso|locked_dialog)\.exec\(\)", tramo))
    assert avisos, "no se han encontrado avisos tras la pantalla de arranque"
    for aviso in avisos:
        anterior = tramo[max(0, aviso.start() - 2000):aviso.start()]
        assert "ocultar_arranque()" in anterior, (
            "este aviso puede quedar detrás de la pantalla de arranque: "
            + tramo[max(0, aviso.start() - 100):aviso.end()]
        )


def test_esconder_la_pantalla_no_falla_si_no_hay_interfaz():
    """Sin pantalla (servidor sin gráficos) el arranque es None y no debe reventar."""
    fuente = (SRC / "main.py").read_text(encoding="utf-8")
    assert "if arranque is not None:" in fuente


# ---------------------------------------------------------------------------
# VIS-010 · la hoja de estilos viaja dentro del paquete
# ---------------------------------------------------------------------------
def test_la_hoja_de_estilos_se_empaqueta_donde_la_busca_la_aplicacion():
    from presentation.theme.hoja_de_estilos import RUTA_QSS

    relativa = RUTA_QSS.relative_to(SRC)
    assert str(relativa) == "presentation/theme/light.qss"

    spec = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    assert "('src/presentation/theme/light.qss', 'presentation/theme')" in spec


def test_ningun_otro_recurso_del_codigo_se_queda_fuera():
    """Si aparece otro fichero que no sea `.py` bajo `src/`, hay que empaquetarlo."""
    ignorar = {".pyc", ".pyi", ".typed"}
    fuera = []
    for fichero in SRC.rglob("*"):
        if not fichero.is_file() or fichero.suffix == ".py":
            continue
        partes = set(fichero.parts)
        if partes & {"__pycache__", ".mypy_cache", "guardias_de_patio.egg-info"}:
            continue
        if fichero.suffix in ignorar or fichero.name == "py.typed":
            continue
        if fichero.suffix == ".md":
            continue  # documentación, no hace falta dentro
        fuera.append(str(fichero.relative_to(SRC)))
    spec = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    sin_empaquetar = [f for f in fuera if Path(f).name not in spec]
    assert sin_empaquetar == [], sin_empaquetar


# ---------------------------------------------------------------------------
# BLD-011 · el empaquetado que se bloquea en el equipo del usuario
# BLD-012 · las funcionalidades que se caen en silencio
# ---------------------------------------------------------------------------


def test_el_spec_no_comprime_con_upx():
    """UPX es firma heurística de antivirus y el bloqueo pasa donde no depuramos."""
    spec = (RAIZ / "GuardiasDePatio.spec").read_text(encoding="utf-8")
    assert "upx=True" not in spec
    assert spec.count("upx=False") == 2, "el EXE y el COLLECT llevan cada uno el suyo"


def test_el_autodiagnostico_pasa_entero_en_desarrollo():
    """En desarrollo todo está en su sitio: cualquier fallo aquí es del módulo."""
    from core.autodiagnostico import revisar_entorno

    assert revisar_entorno() == []


def test_una_comprobacion_rota_no_tumba_el_arranque(monkeypatch):
    """La comprobación existe para avisar, nunca para impedir que la app abra."""
    from core import autodiagnostico

    def explota():
        raise RuntimeError("sin librería nativa")

    monkeypatch.setattr(
        autodiagnostico, "COMPROBACIONES", (("Motor de asignación", explota),)
    )
    assert autodiagnostico.revisar_entorno() == [
        "Motor de asignación: RuntimeError: sin librería nativa"
    ]


def test_el_motivo_del_fallo_viaja_con_el_nombre_de_la_funcionalidad(monkeypatch):
    """El usuario tiene que leer qué ha perdido, no un rastro de excepción."""
    from core import autodiagnostico

    monkeypatch.setattr(
        autodiagnostico,
        "COMPROBACIONES",
        (("Llavero del sistema", lambda: "no hay almacén de credenciales"),),
    )
    assert autodiagnostico.revisar_entorno() == [
        "Llavero del sistema: no hay almacén de credenciales"
    ]


def test_el_aviso_no_molesta_en_desarrollo(monkeypatch):
    """Empaquetada avisa; desde el código fuente sería ruido en cada arranque."""
    from core.autodiagnostico import debe_avisar_al_usuario

    monkeypatch.delenv("GUARDIAS_AUTODIAGNOSTICO", raising=False)
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert debe_avisar_al_usuario() is False

    monkeypatch.setattr(sys, "frozen", True, raising=False)
    assert debe_avisar_al_usuario() is True


def test_la_variable_de_entorno_permite_probar_el_aviso(monkeypatch):
    """Sin ella no habría forma de ver el aviso sin compilar la aplicación."""
    from core.autodiagnostico import debe_avisar_al_usuario

    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setenv("GUARDIAS_AUTODIAGNOSTICO", "1")
    assert debe_avisar_al_usuario() is True


def test_el_arranque_revisa_el_entorno():
    """Si alguien quita la llamada, los fallos vuelven a ser invisibles."""
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")
    assert "revisar_entorno()" in main
    assert "debe_avisar_al_usuario()" in main


def test_la_revision_no_bloquea_el_arranque():
    """Comprobar el entorno importa el backend de gráficas y resuelve un modelo
    del solucionador: ocho segundos largos antes de la primera ventana. Hacerlo
    por delante dejaba la aplicación sin pintar nada y, si una de esas librerías
    nativas se caía, parecía que no abría (BLD-014)."""
    main = (RAIZ / "src" / "main.py").read_text(encoding="utf-8")

    assert "class _RevisionDeEntorno(QThread)" in main, "la revisión va en su propio hilo"
    assert main.index("QApplication(sys.argv)") < main.index("revision.start()"), (
        "la aplicación se crea antes de revisar el entorno"
    )
