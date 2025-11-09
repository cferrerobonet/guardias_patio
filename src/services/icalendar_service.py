"""
Servicio para generar archivos iCalendar (.ics) con guardias de patio.
Permite a los profesores importar sus guardias a calendarios digitales.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from models.models import Configuracion, Guardia, Profesor
from utils import get_logger

logger = get_logger(__name__)


class ICalendarService:
    """Servicio para generar archivos iCalendar (.ics) con guardias."""

    # Duración típica de un recreo en minutos
    DURACION_RECREO_MINUTOS = 20

    @staticmethod
    def _obtener_hora_recreo(
        config: Configuracion, turno: str, recreo: int
    ) -> Optional[datetime.time]:
        """
        Obtiene la hora configurada para un recreo específico.

        Args:
            config: Configuración del curso
            turno: "mañana" o "tarde"
            recreo: Número de recreo (1 o 2)

        Returns:
            Hora del recreo o None si no está configurada
        """
        if turno.lower() == "mañana":
            if recreo == 1 and config.hora_recreo1_manana:
                return config.hora_recreo1_manana
            elif recreo == 2 and config.hora_recreo2_manana:
                return config.hora_recreo2_manana
        elif turno.lower() == "tarde":
            if recreo == 1 and config.hora_recreo1_tarde:
                return config.hora_recreo1_tarde
            elif recreo == 2 and config.hora_recreo2_tarde:
                return config.hora_recreo2_tarde
        return None

    @staticmethod
    def _formatear_datetime_ical(dt: datetime) -> str:
        """
        Formatea una fecha/hora al formato iCalendar (YYYYMMDDTHHMMSS).

        Args:
            dt: Fecha y hora a formatear

        Returns:
            String en formato iCalendar
        """
        return dt.strftime("%Y%m%dT%H%M%S")

    @staticmethod
    def _escapar_texto_ical(texto: str) -> str:
        """
        Escapa caracteres especiales para formato iCalendar.

        Args:
            texto: Texto a escapar

        Returns:
            Texto escapado
        """
        # Escapar caracteres especiales según RFC 5545
        texto = texto.replace("\\", "\\\\")
        texto = texto.replace(",", "\\,")
        texto = texto.replace(";", "\\;")
        texto = texto.replace("\n", "\\n")
        return texto

    @staticmethod
    def generar_icalendar_profesor(
        session: Session,
        profesor_id: int,
        ruta_salida: str,
        nombre_centro: str = "Centro Educativo",
    ) -> bool:
        """
        Genera un archivo iCalendar (.ics) con todas las guardias de un profesor.

        Args:
            session: Sesión de base de datos
            profesor_id: ID del profesor
            ruta_salida: Ruta donde guardar el archivo .ics
            nombre_centro: Nombre del centro educativo

        Returns:
            True si se generó exitosamente, False en caso contrario
        """
        try:
            # Obtener profesor
            profesor = session.query(Profesor).filter_by(id=profesor_id).first()
            if not profesor:
                logger.error(f"Profesor con ID {profesor_id} no encontrado")
                return False

            # Obtener configuración
            config = session.query(Configuracion).first()
            if not config:
                logger.error("No existe configuración del curso")
                return False

            # Obtener todas las guardias del profesor
            guardias = (
                session.query(Guardia)
                .options(joinedload(Guardia.zona))
                .filter(Guardia.profesor_id == profesor_id)
                .order_by(Guardia.fecha, Guardia.recreo)
                .all()
            )

            if not guardias:
                logger.warning(
                    f"No hay guardias para {profesor.nombre_completo}"
                )
                return False

            # Generar archivo iCalendar
            ical_content = ICalendarService._generar_contenido_ical(
                profesor=profesor,
                guardias=guardias,
                config=config,
                nombre_centro=nombre_centro,
            )

            # Guardar archivo
            with open(ruta_salida, "w", encoding="utf-8") as f:
                f.write(ical_content)

            logger.info(
                f"Archivo iCalendar generado: {ruta_salida} "
                f"({len(guardias)} guardias)"
            )
            return True

        except Exception as e:
            logger.error(f"Error al generar iCalendar: {e}")
            return False

    @staticmethod
    def _generar_contenido_ical(
        profesor: Profesor,
        guardias: List[Guardia],
        config: Configuracion,
        nombre_centro: str,
    ) -> str:
        """
        Genera el contenido del archivo iCalendar.

        Args:
            profesor: Profesor dueño del calendario
            guardias: Lista de guardias
            config: Configuración del curso
            nombre_centro: Nombre del centro educativo

        Returns:
            Contenido del archivo .ics
        """
        # Encabezado iCalendar
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//Guardias de Patio//ES",
            "CALSCALE:GREGORIAN",
            "METHOD:PUBLISH",
            f"X-WR-CALNAME:Guardias de Patio - {profesor.nombre_completo}",
            f"X-WR-CALDESC:Calendario de guardias de patio para "
            f"{profesor.nombre_completo}",
            "X-WR-TIMEZONE:Europe/Madrid",
        ]

        # Generar eventos para cada guardia
        for guardia in guardias:
            evento = ICalendarService._generar_evento_guardia(
                guardia=guardia,
                config=config,
                nombre_centro=nombre_centro,
            )
            if evento:
                lines.extend(evento)

        # Cierre del calendario
        lines.append("END:VCALENDAR")

        return "\n".join(lines)

    @staticmethod
    def _generar_evento_guardia(
        guardia: Guardia,
        config: Configuracion,
        nombre_centro: str,
    ) -> Optional[List[str]]:
        """
        Genera un evento VEVENT para una guardia.

        Args:
            guardia: Guardia a convertir en evento
            config: Configuración del curso
            nombre_centro: Nombre del centro educativo

        Returns:
            Lista de líneas del evento o None si no se puede generar
        """
        # Obtener hora del recreo
        hora_recreo = ICalendarService._obtener_hora_recreo(
            config, guardia.turno, guardia.recreo
        )

        if not hora_recreo:
            logger.warning(
                f"No se encontró hora para {guardia.turno} "
                f"recreo {guardia.recreo}"
            )
            return None

        # Crear fecha/hora de inicio
        dt_inicio = datetime.combine(guardia.fecha, hora_recreo)

        # Calcular fecha/hora de fin (recreo + duración)
        dt_fin = dt_inicio + timedelta(
            minutes=ICalendarService.DURACION_RECREO_MINUTOS
        )

        # Información de la zona
        zona_nombre = (
            guardia.zona.nombre_zona if guardia.zona else "Sin zona asignada"
        )
        zona_descripcion = (
            guardia.zona.descripcion
            if guardia.zona and guardia.zona.descripcion
            else ""
        )

        # Título del evento
        titulo = f"🏫 Guardia de Patio - {zona_nombre}"

        # Descripción del evento
        descripcion_parts = [
            f"Guardia de patio en {zona_nombre}",
            f"Turno: {guardia.turno.capitalize()}",
            f"Recreo: {guardia.recreo}",
        ]

        if zona_descripcion:
            descripcion_parts.append(f"Descripción: {zona_descripcion}")

        descripcion_parts.extend(
            [
                "",
                f"📍 Ubicación: {nombre_centro}",
                "⏰ Recuerda llegar unos minutos antes",
                "",
                "Generado por Guardias de Patio",
            ]
        )

        descripcion = "\\n".join(descripcion_parts)

        # Generar UID único pero determinístico
        uid = (
            f"guardia-{guardia.id}-"
            f"{guardia.fecha.strftime('%Y%m%d')}-"
            f"{guardia.recreo}@guardiaspatio"
        )

        # Timestamp de creación
        dtstamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")

        # Construir evento
        evento = [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{dtstamp}",
            f"DTSTART:{ICalendarService._formatear_datetime_ical(dt_inicio)}",
            f"DTEND:{ICalendarService._formatear_datetime_ical(dt_fin)}",
            f"SUMMARY:{ICalendarService._escapar_texto_ical(titulo)}",
            f"DESCRIPTION:{descripcion}",
            f"LOCATION:{ICalendarService._escapar_texto_ical(nombre_centro)}",
            "STATUS:CONFIRMED",
            "TRANSP:OPAQUE",
            f"CATEGORIES:Guardia de Patio,{guardia.turno.capitalize()}",
            # Alarma: 15 minutos antes
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            "DESCRIPTION:Guardia de patio en 15 minutos",
            "TRIGGER:-PT15M",
            "END:VALARM",
            "END:VEVENT",
        ]

        return evento

    @staticmethod
    def obtener_nombre_archivo_ics(profesor_nombre: str) -> str:
        """
        Genera un nombre de archivo .ics válido para un profesor.

        Args:
            profesor_nombre: Nombre completo del profesor

        Returns:
            Nombre de archivo válido (ej: "guardias_LOPEZ_GARCIA_JUAN.ics")
        """
        # Limpiar nombre: quitar caracteres especiales y espacios
        nombre_limpio = (
            profesor_nombre.upper()
            .replace(" ", "_")
            .replace(",", "")
            .replace(".", "")
            .replace("á", "a")
            .replace("é", "e")
            .replace("í", "i")
            .replace("ó", "o")
            .replace("ú", "u")
            .replace("ñ", "n")
        )

        return f"guardias_{nombre_limpio}.ics"
