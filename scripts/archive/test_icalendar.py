"""
Script de prueba para verificar la generación de archivos iCalendar.

Este script genera un archivo .ics de ejemplo para un profesor
y permite verificar que el formato es correcto.
"""

import sys
from datetime import date, time
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def crear_datos_prueba():
    """Crea datos de prueba en memoria (sin base de datos)."""
    from infrastructure.database.models import Configuracion, Guardia, Profesor, Zona

    # Crear profesor de prueba
    profesor = Profesor()
    profesor.id = 1
    profesor.nombre_completo = "GARCÍA LÓPEZ, JUAN"
    profesor.email_corporativo = "juan.garcia@ejemplo.com"

    # Crear zonas de prueba
    zona1 = Zona()
    zona1.id = 1
    zona1.nombre_zona = "Patio Principal"
    zona1.descripcion = "Patio principal del centro"

    zona2 = Zona()
    zona2.id = 2
    zona2.nombre_zona = "Patio Secundaria"
    zona2.descripcion = "Patio del edificio de secundaria"

    # Crear configuración de prueba
    config = Configuracion()
    config.hora_recreo1_manana = time(11, 0)  # 11:00
    config.hora_recreo2_manana = time(13, 30)  # 13:30
    config.hora_recreo1_tarde = time(16, 0)  # 16:00
    config.hora_recreo2_tarde = time(18, 0)  # 18:00

    # Crear guardias de prueba
    guardias = []

    # Guardia 1: Lunes 15/11/2025, mañana, recreo 1
    guardia1 = Guardia()
    guardia1.id = 1
    guardia1.profesor_id = 1
    guardia1.fecha = date(2025, 11, 15)
    guardia1.turno = "mañana"
    guardia1.recreo = 1
    guardia1.zona_id = 1
    guardia1.zona = zona1
    guardias.append(guardia1)

    # Guardia 2: Miércoles 17/11/2025, mañana, recreo 2
    guardia2 = Guardia()
    guardia2.id = 2
    guardia2.profesor_id = 1
    guardia2.fecha = date(2025, 11, 17)
    guardia2.turno = "mañana"
    guardia2.recreo = 2
    guardia2.zona_id = 2
    guardia2.zona = zona2
    guardias.append(guardia2)

    # Guardia 3: Viernes 19/11/2025, tarde, recreo 1
    guardia3 = Guardia()
    guardia3.id = 3
    guardia3.profesor_id = 1
    guardia3.fecha = date(2025, 11, 19)
    guardia3.turno = "tarde"
    guardia3.recreo = 1
    guardia3.zona_id = 1
    guardia3.zona = zona1
    guardias.append(guardia3)

    return profesor, guardias, config


def probar_generacion_icalendar():
    """Prueba la generación de un archivo iCalendar."""
    from services.icalendar_service import ICalendarService

    print("=" * 80)
    print("🧪 PRUEBA DE GENERACIÓN DE ARCHIVO iCALENDAR")
    print("=" * 80)
    print()

    # Crear datos de prueba
    print("1️⃣ Creando datos de prueba...")
    profesor, guardias, config = crear_datos_prueba()
    print(f"   ✅ Profesor: {profesor.nombre_completo}")
    print(f"   ✅ Guardias: {len(guardias)}")
    print()

    # Generar contenido iCalendar
    print("2️⃣ Generando contenido iCalendar...")
    try:
        contenido = ICalendarService._generar_contenido_ical(
            profesor=profesor,
            guardias=guardias,
            config=config,
            nombre_centro="IES Ejemplo",
        )
        print("   ✅ Contenido generado correctamente")
        print()
    except Exception as e:
        print(f"   ❌ Error al generar contenido: {e}")
        return False

    # Guardar archivo
    print("3️⃣ Guardando archivo...")
    ruta_salida = Path(__file__).parent / "prueba_calendario.ics"
    try:
        with open(ruta_salida, "w", encoding="utf-8") as f:
            f.write(contenido)
        print(f"   ✅ Archivo guardado en: {ruta_salida}")
        print()
    except Exception as e:
        print(f"   ❌ Error al guardar archivo: {e}")
        return False

    # Mostrar resumen
    print("4️⃣ Resumen del archivo generado:")
    print("-" * 80)

    # Contar eventos
    num_eventos = contenido.count("BEGIN:VEVENT")
    print(f"   📅 Número de eventos: {num_eventos}")

    # Mostrar primeras líneas
    print()
    print("   📄 Primeras 30 líneas del archivo:")
    print("-" * 80)
    lineas = contenido.split("\n")[:30]
    for linea in lineas:
        print(f"   {linea}")
    if len(contenido.split("\n")) > 30:
        print("   [... más líneas ...]")
    print("-" * 80)
    print()

    # Instrucciones
    print("5️⃣ Para probar el archivo:")
    print(f"   1. Abre el archivo: {ruta_salida}")
    print("   2. O importa en tu calendario:")
    print("      - Google Calendar: Configuración → Importar y exportar")
    print("      - Apple Calendar: Doble clic en el archivo")
    print("      - Outlook: Archivo → Abrir y exportar → Importar")
    print()

    print("✅ Prueba completada exitosamente!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    try:
        resultado = probar_generacion_icalendar()
        sys.exit(0 if resultado else 1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
