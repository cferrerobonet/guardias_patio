"""SYNC-002: no dar por buena una configuración de servidor sin probarla.

Bastaba con que los campos no estuvieran vacíos. Quien escribía mal la contraseña
veía «configuración guardada correctamente» y se enteraba de que no sincronizaba
mucho después, con una sesión entera de trabajo que no había salido del equipo.

De paso: la prueba de conexión capturaba `(OSError, ValueError)`, y las
excepciones de paramiko no heredan de `OSError`. Una contraseña rechazada no daba
«error de conexión»: reventaba el diálogo.
"""

import pytest
from PyQt6.QtWidgets import QMessageBox

pytestmark = pytest.mark.ui


@pytest.fixture
def dialogo(qapp, monkeypatch, tmp_path):
    from presentation.dialogs import initial_config_dialog as modulo

    # El .env de pruebas, fuera del proyecto
    monkeypatch.setattr(modulo.InitialConfigDialog, "_get_env_path", staticmethod(lambda: tmp_path / ".env"))
    d = modulo.InitialConfigDialog()
    yield d
    d.close()


def _rellenar(dialogo, host="servidor.example.com"):
    dialogo.sftp_host_input.setText(host)
    dialogo.sftp_port_input.setText("22")
    dialogo.sftp_user_input.setText("usuario")
    dialogo.sftp_password_input.setText("secreta")
    dialogo.sftp_basedir_input.setText("/datos")


def test_al_abrir_no_hay_ninguna_conexion_probada(dialogo):
    assert dialogo._sftp_probado_ok is False


def test_con_campos_incompletos_no_se_intenta_conectar(dialogo):
    dialogo.sftp_host_input.setText("")
    ok, mensaje = dialogo._probar_conexion_sftp()

    assert ok is False
    assert "faltan datos" in mensaje.lower()


def test_una_contrasena_rechazada_se_explica_en_vez_de_reventar(dialogo, monkeypatch):
    """`AuthenticationException` de paramiko no es `OSError`: antes escapaba."""
    import paramiko

    from presentation.dialogs import initial_config_dialog as modulo

    def transporte_que_rechaza(*_a, **_k):
        raise paramiko.AuthenticationException("Authentication failed.")

    monkeypatch.setattr(modulo.paramiko, "Transport", transporte_que_rechaza)
    _rellenar(dialogo)

    ok, mensaje = dialogo._probar_conexion_sftp()

    assert ok is False
    assert "usuario o la contraseña" in mensaje


def test_cualquier_fallo_del_servidor_se_explica(dialogo, monkeypatch):
    import paramiko

    from presentation.dialogs import initial_config_dialog as modulo

    def transporte_roto(*_a, **_k):
        raise paramiko.SSHException("Error reading SSH protocol banner")

    monkeypatch.setattr(modulo.paramiko, "Transport", transporte_roto)
    _rellenar(dialogo)

    ok, mensaje = dialogo._probar_conexion_sftp()

    assert ok is False
    assert "SSHException" in mensaje


def test_no_se_guarda_una_configuracion_que_no_conecta(dialogo, monkeypatch, tmp_path):
    """Es el fondo de SYNC-002: guardar algo que no funciona es peor que no guardar."""
    _rellenar(dialogo)
    monkeypatch.setattr(dialogo, "_probar_conexion_sftp", lambda: (False, "no responde"))
    escrituras = []
    monkeypatch.setattr(dialogo, "_update_env_file", lambda v: escrituras.append(v))
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)

    dialogo._save_sftp()

    assert not escrituras, "se guardó una configuración que no conecta"
    assert dialogo._sftp_configured is not True


def test_si_conecta_si_se_guarda(dialogo, monkeypatch):
    _rellenar(dialogo)
    monkeypatch.setattr(dialogo, "_probar_conexion_sftp", lambda: (True, "conectado"))
    escrituras = []
    monkeypatch.setattr(dialogo, "_update_env_file", lambda v: escrituras.append(v))
    monkeypatch.setattr(QMessageBox, "exec", lambda self: 0)

    dialogo._save_sftp()

    assert escrituras, "no se guardó una configuración válida"
    assert escrituras[0]["SFTP_HOST"] == "servidor.example.com"


def test_cambiar_un_dato_obliga_a_probar_otra_vez(dialogo):
    """Si no, se probaría con unos datos y se guardarían otros."""
    dialogo._sftp_probado_ok = True
    dialogo.sftp_host_input.textEdited.emit("otro.servidor.com")

    assert dialogo._sftp_probado_ok is False
