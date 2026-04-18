"""
Configuración centralizada de la aplicación usando Pydantic Settings.

Proporciona tipado fuerte, validación automática y soporte para variables
de entorno. Reemplaza al antiguo constants.py con un enfoque más moderno.

IMPORTANTE - Rutas de Archivos:
    Este módulo NO debe crear directorios usando rutas relativas en los
    validadores. La creación de directorios del sistema (logs, data, etc.)
    se maneja en core/paths.py y core/logging.py usando rutas absolutas.

    Ver: documentacion/SOLUCION_COMPILACION.md para más detalles.

Ejemplo de uso:
    from config import settings

    print(settings.app_name)
    print(settings.database_url)
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

try:
    from pydantic import field_validator
    from pydantic_settings import BaseSettings, SettingsConfigDict

    PYDANTIC_V2 = True
except ImportError:
    # Fallback para Pydantic v1
    from pydantic import BaseSettings
    from pydantic import validator as field_validator

    PYDANTIC_V2 = False

    class SettingsConfigDict:
        """Stub para compatibilidad."""

        pass


class Settings(BaseSettings):
    """
    Configuración global de la aplicación.

    Los valores pueden ser sobrescritos mediante variables de entorno
    con el prefijo GUARDIAS_. Ejemplo: GUARDIAS_LOG_LEVEL=DEBUG
    """

    # ========== APLICACIÓN ==========
    app_name: str = "Gestión de Guardias de Patio"
    app_version: str = "3.5.0"
    app_author: str = "Carlos Ferrero Bonet"
    environment: Literal["development", "production", "testing"] = "production"

    # ========== BASE DE DATOS ==========
    # NOTA: database_url es solo fallback. En producción se usa initialize_user_database()
    # que crea BDs por usuario en data/users/{hash}/guardias_patio.db
    database_url: str = ""  # Se configura dinámicamente en db_manager.py
    database_echo: bool = False  # SQL logging
    max_retries_db: int = 3
    timeout_db: int = 30
    pool_size: int = 5
    max_overflow: int = 10

    # ========== LOGGING ==========
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: str = "logs/guardias_patio.log"
    log_to_console: bool = True
    log_to_file: bool = True
    structured_logging: bool = False  # Desactivado para evitar logs verbosos en consola

    # ========== TURNOS ==========
    turno_manana: str = "mañana"
    turno_tarde: str = "tarde"
    turno_mixto: str = "mixto"

    @property
    def turnos_validos(self) -> list[str]:
        """Retorna lista de turnos válidos."""
        return [self.turno_manana, self.turno_tarde, self.turno_mixto]

    # ========== VALIDACIÓN Y LÍMITES ==========
    max_horas_contrato: float = 40.0
    min_horas_contrato: float = 1.0
    max_recreos_dia: int = 2
    max_guardias_por_profesor_dia: int = 1  # Requisito crítico
    max_intentos_asignacion: int = 1000

    # ========== UI ==========
    window_min_width: int = 1200
    window_min_height: int = 800
    max_width_input_short: int = 100
    max_width_input_medium: int = 200
    max_width_input_long: int = 350
    max_width_input_xlarge: int = 500

    # ========== CACHE ==========
    cache_enabled: bool = True
    cache_ttl: int = 300  # 5 minutos
    cache_max_size: int = 1000

    # ========== PERFORMANCE ==========
    enable_query_optimization: bool = True
    enable_eager_loading: bool = True
    batch_size: int = 100

    # ========== CÁLCULO DE GUARDIAS ==========
    multiplicador_tutores: float = 0.9
    multiplicador_no_tutores: float = 1.0
    ajuste_tutores: float = 0.9  # Alias para compatibilidad
    ajuste_no_tutores: float = 1.0  # Alias para compatibilidad
    festivos_comunidad: int = 1  # 1 = Valencia

    # ========== RECREOS (horarios por defecto) ==========
    recreo_manana_1: str = "10:30"
    recreo_manana_2: str = "12:00"
    recreo_tarde_1: str = "15:30"
    recreo_tarde_2: str = "17:00"

    # ========== EXPORTACIÓN ==========
    export_format_json: str = "json"
    export_format_csv: str = "csv"
    export_format_pdf: str = "pdf"

    # ========== DÍAS DE LA SEMANA ==========
    @property
    def dias_semana(self) -> dict[int, str]:
        """Mapeo de números de día a nombres."""
        return {
            0: "Lunes",
            1: "Martes",
            2: "Miércoles",
            3: "Jueves",
            4: "Viernes",
            5: "Sábado",
            6: "Domingo",
        }

    # ========== MENSAJES ==========
    msg_exito_guardar: str = "✅ Datos guardados correctamente"
    msg_exito_actualizar: str = "✅ Datos actualizados correctamente"
    msg_exito_eliminar: str = "✅ Elemento eliminado correctamente"
    msg_error_bd: str = "❌ Error de base de datos"
    msg_error_validacion: str = "⚠️ Error de validación"
    msg_confirmacion_eliminar: str = "¿Está seguro de que desea eliminar este elemento?"

    # ========== DESARROLLO ==========
    debug: bool = False
    enable_profiling: bool = False
    enable_metrics: bool = False

    # Configuración del modelo
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="GUARDIAS_",
        case_sensitive=False,
        extra="ignore",  # Ignorar variables extra
    )

    @field_validator("log_file")
    @classmethod
    def create_log_dir(cls, v: str) -> str:
        """Valida la ruta del archivo de log.

        NOTA: No se crea el directorio aquí porque el sistema de logging
        en core/logging.py usa get_logs_directory() para determinar la
        ruta correcta según el entorno (desarrollo vs producción).
        """
        return v

    @field_validator("max_guardias_por_profesor_dia")
    @classmethod
    def validate_max_guardias(cls, v: int) -> int:
        """Valida que el máximo de guardias por día sea razonable."""
        if v < 1 or v > 3:
            raise ValueError("max_guardias_por_profesor_dia debe estar entre 1 y 3")
        return v

    @property
    def is_development(self) -> bool:
        """Retorna True si estamos en ambiente de desarrollo."""
        return self.environment == "development"

    @property
    def is_production(self) -> bool:
        """Retorna True si estamos en producción."""
        return self.environment == "production"

    @property
    def is_testing(self) -> bool:
        """Retorna True si estamos ejecutando tests."""
        return self.environment == "testing"

    def get_database_path(self) -> Path:
        """Retorna el path absoluto del archivo de base de datos."""
        if self.database_url.startswith("sqlite:///"):
            db_file = self.database_url.replace("sqlite:///", "")
            return Path(db_file).absolute()
        return Path("guardias_patio.db").absolute()


@lru_cache()
def get_settings() -> Settings:
    """
    Retorna instancia singleton de Settings.

    Usa LRU cache para evitar crear múltiples instancias.
    Útil para testing (se puede limpiar el cache).

    Returns:
        Settings: Configuración de la aplicación

    Example:
        >>> from config import get_settings
        >>> settings = get_settings()
        >>> print(settings.app_name)
    """
    return Settings()


# Instancia global para conveniencia
settings = get_settings()
