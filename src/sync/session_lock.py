"""
Sistema de bloqueo de sesión única (Single Session Lock).

Previene que el mismo usuario inicie sesión simultáneamente desde
múltiples dispositivos o ubicaciones, evitando conflictos de datos.
"""

import json
import logging
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class SessionLock:
    """
    Gestiona el bloqueo de sesión única para un usuario.
    
    Utiliza un archivo de bloqueo en el servidor SFTP para coordinar
    el acceso exclusivo entre múltiples clientes.
    """
    
    def __init__(self, backend, user_id: str, user_hash: str):
        """
        Inicializa el sistema de bloqueo de sesión.
        
        Args:
            backend: Backend de sincronización (SFTP o Local)
            user_id: Identificador del usuario (email)
            user_hash: Hash del user_id para nombres de archivo
        """
        self.backend = backend
        self.user_id = user_id
        self.user_hash = user_hash
        self.lock_filename = "session.lock"
        self.heartbeat_interval = 30  # segundos
        self.lock_timeout = 90  # segundos (3x heartbeat)
        
        # Información de esta sesión
        self.session_info = {
            "user_id": user_id,
            "hostname": socket.gethostname(),
            "ip_address": self._get_local_ip(),
            "pid": None,  # Se establecerá al adquirir el lock
            "started_at": None,
            "last_heartbeat": None,
        }
    
    def _get_local_ip(self) -> str:
        """Obtiene la IP local del equipo."""
        try:
            # Truco: conectar a IP externa para obtener IP local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def _get_remote_lock_path(self) -> str:
        """Obtiene la ruta remota del archivo de bloqueo."""
        return f"users/{self.user_hash}/{self.lock_filename}"
    
    def _get_local_lock_path(self) -> Path:
        """Obtiene la ruta local del archivo de bloqueo."""
        return Path("data") / self.user_hash / self.lock_filename
    
    def acquire_lock(self) -> bool:
        """
        Intenta adquirir el bloqueo de sesión.
        
        Returns:
            True si se adquirió el bloqueo, False si ya está bloqueado
        """
        import os
        
        remote_path = self._get_remote_lock_path()
        local_path = self._get_local_lock_path()
        local_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Verificar si existe un bloqueo activo
        if self.backend.file_exists(remote_path):
            # Descargar archivo de bloqueo
            if self.backend.download_file(remote_path, local_path):
                with open(local_path, 'r') as f:
                    existing_lock = json.load(f)
                
                # Verificar si el bloqueo está expirado
                last_heartbeat = datetime.fromisoformat(existing_lock.get("last_heartbeat", ""))
                time_since_heartbeat = (datetime.now() - last_heartbeat).total_seconds()
                
                if time_since_heartbeat < self.lock_timeout:
                    # Bloqueo activo válido
                    logger.warning(
                        f"❌ Sesión bloqueada. Usuario '{self.user_id}' ya está activo en:\n"
                        f"   Equipo: {existing_lock.get('hostname')}\n"
                        f"   IP: {existing_lock.get('ip_address')}\n"
                        f"   Desde: {existing_lock.get('started_at')}\n"
                        f"   Último heartbeat: {existing_lock.get('last_heartbeat')}"
                    )
                    return False
                else:
                    # Bloqueo expirado, puede adquirirse
                    logger.info(
                        f"⚠️  Bloqueo anterior expirado (sin heartbeat por {int(time_since_heartbeat)}s). "
                        f"Adquiriendo nuevo bloqueo..."
                    )
        
        # Crear nuevo bloqueo
        self.session_info["pid"] = os.getpid()
        self.session_info["started_at"] = datetime.now().isoformat()
        self.session_info["last_heartbeat"] = datetime.now().isoformat()
        
        # Guardar localmente
        with open(local_path, 'w') as f:
            json.dump(self.session_info, f, indent=2)
        
        # Subir al servidor
        if self.backend.upload_file(local_path, remote_path):
            logger.info(
                f"✅ Bloqueo de sesión adquirido para '{self.user_id}'\n"
                f"   Equipo: {self.session_info['hostname']}\n"
                f"   IP: {self.session_info['ip_address']}"
            )
            return True
        else:
            logger.error("❌ Error al subir archivo de bloqueo al servidor")
            return False
    
    def update_heartbeat(self) -> bool:
        """
        Actualiza el heartbeat del bloqueo para indicar que la sesión sigue activa.
        
        Returns:
            True si se actualizó correctamente
        """
        remote_path = self._get_remote_lock_path()
        local_path = self._get_local_lock_path()
        
        if not local_path.exists():
            logger.warning("⚠️  No hay archivo de bloqueo local para actualizar")
            return False
        
        # Actualizar timestamp
        self.session_info["last_heartbeat"] = datetime.now().isoformat()
        
        # Guardar localmente
        with open(local_path, 'w') as f:
            json.dump(self.session_info, f, indent=2)
        
        # Subir al servidor
        if self.backend.upload_file(local_path, remote_path):
            logger.debug(f"💓 Heartbeat actualizado para '{self.user_id}'")
            return True
        else:
            logger.warning("⚠️  Error al actualizar heartbeat en el servidor")
            return False
    
    def release_lock(self) -> bool:
        """
        Libera el bloqueo de sesión al cerrar la aplicación.
        
        Returns:
            True si se liberó correctamente
        """
        remote_path = self._get_remote_lock_path()
        local_path = self._get_local_lock_path()
        
        # Eliminar archivo local
        if local_path.exists():
            local_path.unlink()
            logger.info(f"🔓 Archivo de bloqueo local eliminado")
        
        # Intentar eliminar del servidor
        # Nota: La interfaz actual de SyncBackend no tiene método delete()
        # Por ahora, solo eliminamos local y dejamos que expire en el servidor
        logger.info(
            f"✅ Bloqueo de sesión liberado para '{self.user_id}'\n"
            f"   El bloqueo remoto expirará en {self.lock_timeout}s"
        )
        
        return True
    
    def get_lock_info(self) -> Optional[Dict]:
        """
        Obtiene información del bloqueo actual (si existe).
        
        Returns:
            Dict con info del bloqueo o None si no existe
        """
        remote_path = self._get_remote_lock_path()
        local_path = self._get_local_lock_path()
        
        if not self.backend.file_exists(remote_path):
            return None
        
        # Descargar y leer
        if self.backend.download_file(remote_path, local_path):
            with open(local_path, 'r') as f:
                return json.load(f)
        
        return None


class SessionLockManager:
    """
    Gestor de alto nivel para el sistema de bloqueo de sesión.
    
    Se integra con QTimer para mantener heartbeats automáticos.
    """
    
    def __init__(self, session_lock: SessionLock):
        self.session_lock = session_lock
        self.heartbeat_timer = None
    
    def start_heartbeat(self, app):
        """
        Inicia el sistema de heartbeat automático usando QTimer.
        
        Args:
            app: Instancia de QApplication para crear el timer
        """
        from PyQt6.QtCore import QTimer
        
        self.heartbeat_timer = QTimer()
        self.heartbeat_timer.timeout.connect(self._on_heartbeat)
        self.heartbeat_timer.start(self.session_lock.heartbeat_interval * 1000)  # ms
        
        logger.info(
            f"💓 Sistema de heartbeat iniciado "
            f"(cada {self.session_lock.heartbeat_interval}s)"
        )
    
    def _on_heartbeat(self):
        """Callback del timer de heartbeat."""
        try:
            self.session_lock.update_heartbeat()
        except Exception as e:
            logger.error(f"Error en heartbeat: {e}")
    
    def stop_heartbeat(self):
        """Detiene el sistema de heartbeat."""
        if self.heartbeat_timer:
            self.heartbeat_timer.stop()
            logger.info("💤 Sistema de heartbeat detenido")
    
    def cleanup(self):
        """Limpieza completa al cerrar la aplicación."""
        self.stop_heartbeat()
        self.session_lock.release_lock()
