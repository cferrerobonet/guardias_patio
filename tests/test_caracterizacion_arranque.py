"""Caracterización de `main.main()`: fija el recorrido del arranque y del cierre.

Cada dependencia (aplicación Qt, pantalla de arranque, diálogos, servidor, base de
datos, bloqueo de sesión y sincronización) se sustituye por un doble que anota lo que
se le pide. Para cada escenario se fija el código de salida y la huella de esa
secuencia más los mensajes del registro de `main`. Sirve de red para partir la
función sin cambiar lo que hace. No toca red, llavero, `.env` real ni ventanas.

Si un cambio en el arranque es intencionado, las huellas se recalculan a propósito.
"""

import hashlib
import json
import logging
import sys
from types import SimpleNamespace

import pytest
from PyQt6.QtCore import QLocale
from PyQt6.QtWidgets import QMessageBox

USUARIO = "usuario.ficticio"


class _Senal:
    def __init__(self, ev, nombre):
        self.ev, self.nombre, self.funciones = ev, nombre, []

    def connect(self, fn):
        self.ev(f"connect {self.nombre}")
        self.funciones.append(fn)

    def emit(self, *args):
        for fn in self.funciones:
            fn(*args)


def _dobles(monkeypatch, tmp_path, esc, ev):
    import core.limpieza_de_rastros
    import core.paths
    import core.prueba_de_arranque
    import database.db_manager
    import main
    import presentation.dialogs.huella_servidor_dialog as huella
    import presentation.dialogs.initial_config_dialog as config_inicial
    import presentation.dialogs.session_locked_dialog as bloqueada
    import presentation.forms.login_dialog as login
    import presentation.theme.hoja_de_estilos as hoja
    import presentation.theme.modo_oscuro as modo_oscuro
    import presentation.theme.tokens as tokens
    import presentation.ventana_principal as ventana
    import presentation.widgets.pantalla_de_arranque as pantalla
    import presentation.widgets.sync_progress_dialog as progreso_sync
    import services.migrar_a_multi_curso as migracion
    import sync
    import sync.session_lock as bloqueo
    import utils.ui_helpers as ui_helpers
    from sync import SyncConfigurationError

    # ------------------------------------------------------------ Qt y arranque
    class App:
        lastWindowClosed = None
        aboutToQuit = None

        def __init__(self, argv):
            ev("QApplication")
            App.lastWindowClosed = _Senal(ev, "lastWindowClosed")
            App.aboutToQuit = _Senal(ev, "aboutToQuit")

        @staticmethod
        def setHighDpiScaleFactorRoundingPolicy(_politica):
            ev("dpi")

        def setFont(self, _f):
            ev("setFont")

        def setStyleSheet(self, h):
            ev(f"setStyleSheet {h}")

        def installTranslator(self, _t):
            ev("installTranslator")

        def exec(self):
            ev("app.exec")
            return esc["exec"]

        def quit(self):
            ev("quit")

    class Mensaje:
        Icon = QMessageBox.Icon
        ButtonRole = QMessageBox.ButtonRole

        def __init__(self, *args):
            self.datos = {"args": [str(a) for a in args]}
            self.botones = []

        def __getattr__(self, nombre):
            if nombre.startswith("set"):
                def anotar(*args):
                    self.datos[nombre] = [str(a) for a in args]
                return anotar
            raise AttributeError(nombre)

        def addButton(self, texto, _rol):
            self.botones.append(texto)
            return texto

        def clickedButton(self):
            return self.botones[0] if esc["eleccion_local"] else self.botones[1]

        def exec(self):
            datos = {k: v for k, v in self.datos.items() if k != "setWindowIcon"}
            ev(f"QMessageBox.exec {json.dumps(datos, ensure_ascii=False, sort_keys=True)}")

        @staticmethod
        def critical(_padre, titulo, texto):
            ev(f"QMessageBox.critical {titulo} | {texto}")

        @staticmethod
        def warning(_padre, titulo, texto):
            ev(f"QMessageBox.warning {titulo} | {texto.replace(str(main.log_file), '<log>')}")

    class Locale:
        Language = QLocale.Language
        Country = QLocale.Country

        def __init__(self, *_):
            pass

        @staticmethod
        def setDefault(_l):
            ev("QLocale.setDefault")

    class Traductor:
        def load(self, *_):
            ev("QTranslator.load")
            return esc["traduccion"]

    class Revision:
        def __init__(self):
            self.terminada = _Senal(ev, "revision.terminada")

        def start(self):
            ev("revision.start")
            self.terminada.emit(list(esc["fallos_entorno"]))

        def wait(self, ms):
            ev(f"revision.wait {ms}")

    class Pantalla:
        visible = True

        def hide(self):
            ev("arranque.hide")
            self.visible = False

        def show(self):
            ev("arranque.show")
            self.visible = True

        def isVisible(self):
            return self.visible

        def paso(self, msg):
            ev(f"paso {msg}")

        def terminar(self, w):
            ev(f"arranque.terminar {w.nombre}")

    monkeypatch.setattr(main, "QApplication", App)
    monkeypatch.setattr(main, "QMessageBox", Mensaje)
    monkeypatch.setattr(main, "QLocale", Locale)
    monkeypatch.setattr(main, "QTranslator", Traductor)
    monkeypatch.setattr(main, "_RevisionDeEntorno", Revision)
    monkeypatch.setattr(main, "debe_avisar_al_usuario", lambda: True)
    monkeypatch.setattr(main, "aplicar_icono_de_la_app", lambda _a: ev("icono"))
    monkeypatch.setattr(main, "apply_corporate_branding", lambda: ev("branding"))
    monkeypatch.setattr(main, "load_dotenv", lambda **kw: ev("load_dotenv"))
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)
    import signal

    monkeypatch.setattr(signal, "signal", lambda s, _f: ev(f"signal {int(s)}"))
    monkeypatch.setattr(modo_oscuro, "instalar", lambda _a: ev("modo_oscuro"))
    monkeypatch.setattr(core.prueba_de_arranque, "vigilar_si_se_pide",
                        lambda _a: ev("vigilar"))
    monkeypatch.setattr(tokens, "cargar_fuentes", lambda: ev("cargar_fuentes"))
    monkeypatch.setattr(tokens, "familias_del_sistema", lambda: ["Arial"])
    monkeypatch.setattr(tokens, "cuerpo_del_sistema", lambda: 13)
    monkeypatch.setattr(hoja, "construir_hoja_de_estilos", lambda: esc["hoja"])
    monkeypatch.setattr(pantalla, "abrir_pantalla_de_arranque",
                        lambda: Pantalla() if esc["pantalla"] else None)

    # ------------------------------------------------------------ configuración
    class ConfigInicial:
        DialogCode = SimpleNamespace(Accepted=1, Rejected=0)

        @staticmethod
        def is_configuration_needed():
            return esc["config_necesaria"]

        def exec(self):
            ev("InitialConfigDialog.exec")
            return 1 if esc["config_acepta"] else 0

    if esc["env"]:
        (tmp_path / ".env").write_text("X=1\n", encoding="utf-8")
    monkeypatch.setattr(config_inicial, "InitialConfigDialog", ConfigInicial)
    monkeypatch.setattr(core.paths, "get_base_directory", lambda: tmp_path)
    monkeypatch.setattr(core.limpieza_de_rastros, "revisar_y_limpiar",
                        lambda _d: ev("revisar_y_limpiar"))

    # ------------------------------------------------------------ servidor y login
    backends = list(esc["backends"])

    class Backend:
        def __init__(self, tipo):
            self.tipo = tipo
            if tipo == "local":
                self.base_path = None

        def close(self):
            ev("backend.close")
            if esc["cierre_backend"] == "falla":
                raise RuntimeError("cierre ficticio")

    def get_default_backend():
        tipo = backends.pop(0)
        ev(f"get_default_backend {tipo}")
        if tipo == "falla":
            raise SyncConfigurationError("servidor ficticio sin respuesta")
        return Backend(tipo)

    def confirmar():
        ev("confirmar_huella")
        return esc["huella"]

    class Login:
        DialogCode = SimpleNamespace(Accepted=1, Rejected=0)
        authenticated_user = USUARIO
        clave_datos = "clave-ficticia"

        def __init__(self, backend=None):
            ev(f"LoginDialog backend={getattr(backend, 'tipo', None)}")

        def exec(self):
            ev("LoginDialog.exec")
            return 1 if esc["login"] else 0

    monkeypatch.setattr(sync, "get_default_backend", get_default_backend)
    monkeypatch.setattr(huella, "confirmar_huella_si_hace_falta", confirmar)
    monkeypatch.setattr(login, "LoginDialog", Login)
    monkeypatch.setattr(ui_helpers, "get_app_icon", lambda: "icono")

    # ------------------------------------------------------------ base de datos
    class Sesion:
        def close(self):
            ev("session.close")

    def fabrica():
        ev("SessionFactory")
        if esc["sesion"] == "falla":
            raise RuntimeError("sesión ficticia rota")
        return Sesion()

    def inicializar(usuario):
        ev(f"initialize_user_database {usuario}")
        if esc["bd"] == "falla":
            raise RuntimeError("base ficticia rota")
        return "motor", fabrica

    def migrar(_s):
        ev("migracion")
        if esc["migracion"] == "falla":
            raise RuntimeError("migración ficticia rota")
        return esc["migracion"]

    monkeypatch.setattr(database.db_manager, "initialize_user_database", inicializar)
    monkeypatch.setattr(migracion, "ejecutar_migracion_si_necesario", migrar)

    # ------------------------------------------------------------ sync y bloqueo
    class Gestor:
        user_hash = "hash-ficticio"

        def __init__(self, backend, username, clave_datos=None):
            ev(f"SyncManager {backend.tipo} {username} {clave_datos}")
            if esc["sync_manager"] == "excepcion":
                raise RuntimeError("gestor ficticio roto")
            self.backend = backend
            self.motivo_bloqueo = esc["motivo_bloqueo"]

        def sync_on_startup(self, session=None):
            ev("sync_on_startup")
            return esc["sync_inicio"]

    acquires = list(esc["bloqueos"])
    respuestas = list(esc["dialogo_bloqueo"])

    class Bloqueo:
        motivo_del_fallo = None

        def __init__(self, backend, username, user_hash):
            ev(f"SessionLock {username} {user_hash}")

        def acquire_lock(self):
            r = acquires.pop(0)
            ev(f"acquire_lock {r}")
            self.motivo_del_fallo = "sin_servidor" if r == "sin_servidor" else None
            return r is True

        def get_lock_info(self):
            ev("get_lock_info")
            return {"equipo": "equipo-ficticio"} if esc["info_bloqueo"] else None

    class Latido:
        def __init__(self, _lock):
            ev("SessionLockManager")

        def start_heartbeat(self, _app):
            ev("start_heartbeat")

        def stop_heartbeat(self):
            ev("stop_heartbeat")

        def cleanup(self):
            ev("lock.cleanup")

    class DialogoBloqueo:
        DialogCode = SimpleNamespace(Accepted=1, Rejected=0)

        def __init__(self, info):
            ev(f"SessionLockedDialog {info}")

        def exec(self):
            r = respuestas.pop(0)
            ev(f"SessionLockedDialog.exec {r}")
            return 1 if r == "reintentar" else 0

    monkeypatch.setattr(sync, "SyncManager", Gestor)
    monkeypatch.setattr(bloqueo, "SessionLock", Bloqueo)
    monkeypatch.setattr(bloqueo, "SessionLockManager", Latido)
    monkeypatch.setattr(bloqueada, "SessionLockedDialog", DialogoBloqueo)
    if esc["sin_bloqueo"]:
        monkeypatch.setenv("DISABLE_SESSION_LOCK", "1")
    else:
        monkeypatch.delenv("DISABLE_SESSION_LOCK", raising=False)

    # ------------------------------------------------------------ ventana y cierre
    class Ventana:
        nombre = "ventana"

        def __init__(self, session, sync_manager=None):
            ev(f"VentanaPrincipal sync={sync_manager is not None}")
            if esc["ventana"] == "falla":
                raise RuntimeError("ventana ficticia rota")

    class DialogoProgreso:
        def __getattr__(self, nombre):
            if nombre.startswith("set_step"):
                return lambda *a, **kw: ev(f"{nombre} {a} {kw}")
            raise AttributeError(nombre)

        def exec(self):
            ev("SyncProgressDialog.exec")

    class Trabajador:
        def __init__(self, _gestor):
            ev("SyncWorker")
            self.progress_updated = _Senal(ev, "progress_updated")
            self.finished = _Senal(ev, "finished")

        def start(self):
            ev("worker.start")
            for paso, detalles in (("exporting", {}), ("connecting", {}),
                                   ("uploading", {"file_size_kb": 12}),
                                   ("uploading", {}), ("complete", {}),
                                   ("error", {"message": "fallo ficticio"}), ("error", {}),
                                   ("otro", {})):
                self.progress_updated.emit(paso, detalles)
            self.finished.emit(esc["sync_final"])

        def wait(self):
            ev("worker.wait")

    class Servicios:
        def __init__(self, _s):
            if esc["servicios"] == "falla":
                raise ValueError("servicios ficticios rotos")
            self.profesores = SimpleNamespace(get_all=lambda: [1, 2])
            self.zonas = SimpleNamespace(get_all=lambda: [1])

        def contar_guardias(self):
            return 5

    import application.app_services as app_services

    monkeypatch.setattr(ventana, "VentanaPrincipal", Ventana)
    monkeypatch.setattr(progreso_sync, "SyncProgressDialog", DialogoProgreso)
    monkeypatch.setattr(progreso_sync, "SyncWorker", Trabajador)
    monkeypatch.setattr(app_services, "AppServices", Servicios)
    return main


BASE = {
    "pantalla": True, "fallos_entorno": [], "hoja": "QSS", "env": False, "traduccion": True,
    "config_necesaria": False, "config_acepta": True, "eleccion_local": True,
    "backends": ["sftp"], "huella": False, "login": True, "bd": "ok", "sesion": "ok",
    "migracion": True, "sin_bloqueo": False, "bloqueos": [True], "info_bloqueo": True,
    "dialogo_bloqueo": [], "sync_manager": "ok", "sync_inicio": True, "motivo_bloqueo": None,
    "ventana": "ok", "exec": 0, "sync_final": True, "servicios": "ok", "cierre_backend": "ok",
}

ESCENARIOS = {
    "normal": {},
    "sin_pantalla_ni_hoja_ni_traduccion": {"pantalla": False, "hoja": "", "traduccion": False,
                                           "env": True},
    "fallos_de_entorno": {"fallos_entorno": ["Gráficas", "Correo"]},
    "config_cancelada_y_salir": {"config_necesaria": True, "config_acepta": False,
                                 "eleccion_local": False},
    "config_cancelada_local_sin_servidor_y_sin_login": {
        "config_necesaria": True, "config_acepta": False, "backends": ["falla"],
        "login": False},
    "config_aceptada_huella_confirmada": {
        "config_necesaria": True, "backends": ["falla", "sftp"], "huella": True,
        "sin_bloqueo": True, "sync_inicio": False, "motivo_bloqueo": "copia ficticia vieja",
        "exec": 3, "sync_final": False, "servicios": "falla"},
    "huella_confirmada_pero_sigue_sin_servidor": {
        "backends": ["falla", "falla"], "huella": True, "sync_inicio": False},
    "bloqueo_cancelado": {"bloqueos": [False], "dialogo_bloqueo": ["cancelar"]},
    "bloqueo_reintenta_y_entra": {"bloqueos": [False, True], "dialogo_bloqueo": ["reintentar"]},
    "bloqueo_sin_informacion": {"bloqueos": [False], "info_bloqueo": False},
    "bloqueo_agotado": {"bloqueos": [False, False, False],
                        "dialogo_bloqueo": ["reintentar"] * 3},
    "bloqueo_sin_servidor": {"bloqueos": ["sin_servidor"]},
    "gestor_de_sync_roto": {"sync_manager": "excepcion"},
    "base_de_datos_rota": {"bd": "falla"},
    "sesion_rota": {"sesion": "falla"},
    "migracion_rota": {"migracion": "falla"},
    "migracion_ya_hecha": {"migracion": False},
    "ventana_rota": {"ventana": "falla"},
    "backend_local_sin_ruta_y_cierre_roto": {"backends": ["local"], "cierre_backend": "falla"},
    "sin_sincronizacion_inicial_y_cierre_roto": {"sync_inicio": False, "motivo_bloqueo": None,
                                                 "cierre_backend": "falla"},
}

ESPERADO = {  # (código de salida, huella del recorrido y del registro)
    "normal": (
        0, "d76954c2bc3ef663dc82ebbf675e81f50f5eded91adda1d9883c9f2176f09542",
    ),
    "sin_pantalla_ni_hoja_ni_traduccion": (
        0, "64854bf85721558fe12f8c415065a472a6162bc499d61c9a52908a4ca58ee9bb",
    ),
    "fallos_de_entorno": (
        0, "4b20ba5ef3290704db5ca1373b8b36bfdee42e51a775cdbe7717ce78d5def8db",
    ),
    "config_cancelada_y_salir": (
        0, "56612d487d033a308687fa21f0adace8d4e2a895b02493f4415c25f5aaebf107",
    ),
    "config_cancelada_local_sin_servidor_y_sin_login": (
        0, "8c670613f919dd5d5024b84411b86bc7461c5531d450950600691e341a9f4231",
    ),
    "config_aceptada_huella_confirmada": (
        3, "2e4857c09674cdc2d6121d4934e2a18f863d436dea15ffa6bb18f0fc78345ce0",
    ),
    "huella_confirmada_pero_sigue_sin_servidor": (
        0, "3f42297d5d4a4ea158a4bfdad57601a0b10edd9919ae58c48e62a466d070f246",
    ),
    "bloqueo_cancelado": (
        0, "896be11ab55a0fc861551ed584e23fb6e6fe034b4982894877b16dcdccfb57fd",
    ),
    "bloqueo_reintenta_y_entra": (
        0, "f7cd53d6be4833186d231fb9f4a5e831dcc426aa429c215e9148cff9b5302323",
    ),
    "bloqueo_sin_informacion": (
        1, "968c43ae17d890c23738a715d95e824c0a3920bcaecc0ac5f07016756ef40678",
    ),
    "bloqueo_agotado": (
        1, "45774ea128e5e8bfb212ac6f8b025209da4d1d4fdf9d4de698dfaf9ac02e72c9",
    ),
    "bloqueo_sin_servidor": (
        0, "0b325e79304a3977c044cd0a7f9f03a7d75c7a2298faf67c8ef03088c23a3405",
    ),
    "gestor_de_sync_roto": (
        0, "7add680165af53da1c0aa817e359ab98d2d5ff8969874c2e62e555f388745387",
    ),
    "base_de_datos_rota": (
        1, "5406285819a38392ac4ac4e4de61d658c3192ea6e2c378455ae75e07c9f2cd4c",
    ),
    "sesion_rota": (
        1, "ca0f82a6d52555ba1252a722d22da8c71def277f3495ae135e67b0b03b4fe5f6",
    ),
    "migracion_rota": (
        0, "3ac22bb70cd92bd957c637837a303fa8c81d0af916329a1666662f4436261e12",
    ),
    "migracion_ya_hecha": (
        0, "300887026835538db6fbf886347f0b542d7bd54c6aa5ad1eda1ccfa95b81fd53",
    ),
    "ventana_rota": (
        1, "8f51b6d0280f884350b25a05760de1ff15a1c21135629adf09a4b714f57c6c68",
    ),
    "backend_local_sin_ruta_y_cierre_roto": (
        0, "ddae38c113dd80eb0ce6d913732912b734954bc36f261e22f0792ccf9b1f1b46",
    ),
    "sin_sincronizacion_inicial_y_cierre_roto": (
        0, "960bbeabeb28b7c7d8259f19460aa8bed5ea93d35f4b24cee177d87952f7d4a4",
    ),
}


def _recorrido(monkeypatch, tmp_path, caplog, cambios):
    esc = {**BASE, **cambios}
    eventos = []
    main = _dobles(monkeypatch, tmp_path, esc, eventos.append)
    caplog.clear()
    # Una configuración de logging anterior de la suite puede dejarlo deshabilitado.
    monkeypatch.setattr(logging.getLogger("main"), "disabled", False)
    with caplog.at_level(logging.DEBUG, logger="main"):
        codigo = main.main()
    registro = [
        f"{r.levelname} {r.getMessage()}" for r in caplog.records
        if r.name == "main" and "Thread" not in r.getMessage()
    ]
    eventos.append(f"excepthook {getattr(sys.excepthook, '__name__', '')}")
    return codigo, eventos, registro


@pytest.mark.parametrize("nombre", list(ESCENARIOS))
def test_recorrido_del_arranque(monkeypatch, tmp_path, caplog, qapp, nombre):
    codigo, eventos, registro = _recorrido(monkeypatch, tmp_path, caplog, ESCENARIOS[nombre])
    huella = hashlib.sha256(
        json.dumps([eventos, registro], ensure_ascii=False).encode()
    ).hexdigest()
    assert (codigo, huella) == ESPERADO[nombre], "\n".join(eventos + ["--"] + registro)
