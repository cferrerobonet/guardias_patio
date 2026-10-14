"""Servidor SFTP falso para la prueba de arranque en CI (BLD-020).

Sirve una carpeta local por SFTP en 127.0.0.1 con paramiko, para que el exe
recorra el camino real del usuario —huella del servidor, cuentas remotas, marca
de sesión, traer los datos de la nube y subirlos al cerrar— sin tocar nunca el
servidor de verdad.

    python scripts/servidor_sftp_de_prueba.py --raiz C:/sftp --puerto 2222 \
        --usuario prueba --contrasena secreta --known-hosts ~/.ssh/known_hosts

Deja la clave del servidor en `known_hosts` y se queda escuchando hasta que lo
maten. Una conexión por hilo; sin más pretensiones.
"""

import argparse
import errno
import os
import socket
import threading
from pathlib import Path

import paramiko
from paramiko.sftp import SFTP_FAILURE, SFTP_OK
from paramiko.sftp_attr import SFTPAttributes
from paramiko.sftp_handle import SFTPHandle
from paramiko.sftp_server import SFTPServer, SFTPServerInterface


class _Servidor(paramiko.ServerInterface):
    def __init__(self, usuario: str, contrasena: str):
        self.usuario = usuario
        self.contrasena = contrasena

    def check_auth_password(self, username, password):
        if username == self.usuario and password == self.contrasena:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def get_allowed_auths(self, username):
        return "password"

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED


class _Fichero(SFTPHandle):
    def stat(self):
        try:
            return SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        return SFTP_OK


def _carpeta(raiz: Path):
    class _Carpeta(SFTPServerInterface):
        def _ruta(self, ruta: str) -> str:
            return str(raiz / self.canonicalize(ruta).lstrip("/"))

        def list_folder(self, path):
            ruta = self._ruta(path)
            try:
                salida = []
                for nombre in os.listdir(ruta):
                    attr = SFTPAttributes.from_stat(os.stat(os.path.join(ruta, nombre)))
                    attr.filename = nombre
                    salida.append(attr)
                return salida
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)

        def stat(self, path):
            try:
                return SFTPAttributes.from_stat(os.stat(self._ruta(path)))
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)

        lstat = stat

        def open(self, path, flags, attr):
            ruta = self._ruta(path)
            try:
                fd = os.open(ruta, flags | getattr(os, "O_BINARY", 0), 0o666)
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)
            if flags & os.O_WRONLY:
                modo = "ab" if flags & os.O_APPEND else "wb"
            elif flags & os.O_RDWR:
                modo = "a+b" if flags & os.O_APPEND else "r+b"
            else:
                modo = "rb"
            try:
                f = os.fdopen(fd, modo)
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)
            handle = _Fichero(flags)
            handle.filename = ruta
            handle.readfile = f
            handle.writefile = f
            return handle

        def remove(self, path):
            try:
                os.remove(self._ruta(path))
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)
            return SFTP_OK

        def rename(self, oldpath, newpath):
            try:
                os.replace(self._ruta(oldpath), self._ruta(newpath))
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)
            return SFTP_OK

        posix_rename = rename

        def mkdir(self, path, attr):
            try:
                os.mkdir(self._ruta(path))
            except OSError as e:
                if e.errno == errno.EEXIST:
                    return SFTP_FAILURE
                return SFTPServer.convert_errno(e.errno)
            return SFTP_OK

        def rmdir(self, path):
            try:
                os.rmdir(self._ruta(path))
            except OSError as e:
                return SFTPServer.convert_errno(e.errno)
            return SFTP_OK

        def chattr(self, path, attr):
            return SFTP_OK

    return _Carpeta


def _atender(conexion, clave, usuario, contrasena, raiz):
    transporte = paramiko.Transport(conexion)
    transporte.add_server_key(clave)
    transporte.set_subsystem_handler("sftp", SFTPServer, _carpeta(raiz))
    try:
        transporte.start_server(server=_Servidor(usuario, contrasena))
        while transporte.is_active():
            transporte.join(1)
    except Exception as e:  # noqa: BLE001 - un cliente roto no tumba el servidor
        print(f"conexión cerrada: {e}", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raiz", required=True)
    p.add_argument("--puerto", type=int, default=2222)
    p.add_argument("--usuario", required=True)
    p.add_argument("--contrasena", required=True)
    p.add_argument("--known-hosts", required=True)
    a = p.parse_args()

    raiz = Path(a.raiz)
    raiz.mkdir(parents=True, exist_ok=True)
    clave = paramiko.RSAKey.generate(2048)

    conocidos = Path(os.path.expanduser(a.known_hosts))
    conocidos.parent.mkdir(parents=True, exist_ok=True)
    with open(conocidos, "a", encoding="utf-8") as f:
        f.write(f"[127.0.0.1]:{a.puerto} {clave.get_name()} {clave.get_base64()}\n")

    oyente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    oyente.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    oyente.bind(("127.0.0.1", a.puerto))
    oyente.listen(10)
    print(f"SFTP de prueba en 127.0.0.1:{a.puerto}, raíz {raiz}", flush=True)
    while True:
        conexion, _ = oyente.accept()
        threading.Thread(
            target=_atender,
            args=(conexion, clave, a.usuario, a.contrasena, raiz),
            daemon=True,
        ).start()


if __name__ == "__main__":
    main()
