"""
Constantes globales de la aplicación.

Define valores constantes utilizados en toda la aplicación para evitar
"magic numbers" y facilitar el mantenimiento.
"""

# ========== CONSTANTES DE APLICACIÓN ==========
APP_NAME = "Gestión de Guardias de Patio"
APP_VERSION = "3.2.1"
APP_AUTHOR = "Carlos Ferrero Bonet"

# ========== CONSTANTES DE BASE DE DATOS ==========
DB_FILE = "guardias_patio.db"
MAX_RETRIES_DB = 3
TIMEOUT_DB = 30

# ========== CONSTANTES DE TURNOS ==========
TURNO_MANANA = "mañana"
TURNO_TARDE = "tarde"
TURNO_MIXTO = "mixto"
TURNOS_VALIDOS = [TURNO_MANANA, TURNO_TARDE, TURNO_MIXTO]

# ========== CONSTANTES DE DÍAS DE SEMANA ==========
DIA_LUNES = 0
DIA_MARTES = 1
DIA_MIERCOLES = 2
DIA_JUEVES = 3
DIA_VIERNES = 4
DIA_SABADO = 5
DIA_DOMINGO = 6

DIAS_SEMANA = {
    DIA_LUNES: "Lunes",
    DIA_MARTES: "Martes",
    DIA_MIERCOLES: "Miércoles",
    DIA_JUEVES: "Jueves",
    DIA_VIERNES: "Viernes",
    DIA_SABADO: "Sábado",
    DIA_DOMINGO: "Domingo",
}

# ========== CONSTANTES DE VALIDACIÓN ==========
MAX_HORAS_CONTRATO = 40.0
MIN_HORAS_CONTRATO = 1.0
MAX_RECREOS_DIA = 2
MAX_GUARDIAS_POR_PROFESOR_DIA = 1  # Requisito crítico: máximo 1 guardia por día

# ========== CONSTANTES DE UI ==========
WINDOW_MIN_WIDTH = 1200
WINDOW_MIN_HEIGHT = 800
MAX_WIDTH_INPUT_SHORT = 100  # Campos numéricos pequeños
MAX_WIDTH_INPUT_MEDIUM = 200  # Fechas, horas
MAX_WIDTH_INPUT_LONG = 350  # Nombres, emails
MAX_WIDTH_INPUT_XLARGE = 500  # Textos largos

# ========== CONSTANTES DE MENSAJES ==========
MSG_EXITO_GUARDAR = "✅ Datos guardados correctamente"
MSG_EXITO_ACTUALIZAR = "✅ Datos actualizados correctamente"
MSG_EXITO_ELIMINAR = "✅ Elemento eliminado correctamente"
MSG_ERROR_BD = "❌ Error de base de datos"
MSG_ERROR_VALIDACION = "⚠️ Error de validación"
MSG_CONFIRMACION_ELIMINAR = "¿Está seguro de que desea eliminar este elemento?"

# ========== CONSTANTES DE LOGGING ==========
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "logs/guardias_patio.log"

# ========== CONSTANTES DE EXPORTACIÓN ==========
EXPORT_FORMAT_JSON = "json"
EXPORT_FORMAT_CSV = "csv"
EXPORT_FORMAT_PDF = "pdf"

# ========== CONSTANTES DE CÁLCULO ==========
DEFAULT_MULTIPLICADOR_TUTORES = 0.9
DEFAULT_MULTIPLICADOR_NO_TUTORES = 1.0
DEFAULT_FESTIVOS_COMUNIDAD = 1  # 1 = Valencia

# ========== CONSTANTES DE RECREOS ==========
RECREO_MANANA_1_DEFAULT = "10:30"
RECREO_MANANA_2_DEFAULT = "12:00"
RECREO_TARDE_1_DEFAULT = "15:30"
RECREO_TARDE_2_DEFAULT = "17:00"
