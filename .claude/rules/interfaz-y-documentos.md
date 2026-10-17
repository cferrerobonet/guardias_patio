---
paths:
  - "src/presentation/**"
  - "src/services/pdf_styles.py"
  - "src/services/_pdf_*.py"
  - "src/services/exportador_pdf.py"
  - "src/services/recreos.py"
  - "src/services/icalendar_service.py"
  - "src/services/publicador_web.py"
  - "src/services/notificador_guardias.py"
  - "src/services/email_service.py"
  - "src/services/edicion_manual_calendario.py"
  - "src/utils/ui_helpers.py"
  - "src/utils/corporate_branding.py"
  - "imagenes/**"
  - "scripts/build/create_icon.sh"
  - "tests/test_pdf_guardias_impreso.py"
---

# Interfaz, documentos impresos y salidas

- **Tema y tokens**: `presentation/theme/tokens.py` (paleta clara y oscura, fuentes Barlow de `imagenes/fuentes`), `theme/light.qss` (medidas comunes: 34 px), `themes/tema_aplicacion.py` (solo lo propio de la ventana) + inline.
- **Documentos impresos** (A4, estilo Partes de salida, legibles en blanco y negro): `services/pdf_styles.py` (`Papel`, `ajustar`, cabeceras, pie «Página n de N», `construir_documento`; logos ya reducidos en `imagenes/*.jpg`), `_pdf_mini_calendario.py` (`CalendarioMes`, leyenda, festivos), `_pdf_individual_optimizado.py` (el del aviso) y `_pdf_mes_consolidado.py`. Prueba: `tests/test_pdf_guardias_impreso.py`.
- **Listados sin paginación** por decisión de CarlosFB (2026-10-17): todas las filas, con buscador, filtros y orden (`widgets/listado_filtrable.py`); cada etiqueta de filtro va pegada a su desplegable.
- **Icono de la app ≠ logo de EPLA** (7.5.3): ventanas, diálogos, barra de tareas, Dock e instaladores llevan `imagenes/icono.png` (`ui_helpers.get_app_icon`, `corporate_branding.aplicar_icono_de_la_app`); de él salen `icono.ico` (Pillow, 16-256) e `icono.icns` (`scripts/build/create_icon.sh`, que `make icon` rehace en cada compilación). El logo (`logo.png`, `get_corporate_pixmap`) solo va dentro: cabeceras, pantalla de inicio, PDF y correos.
- **Recreos**: la guardia guarda el id global del recreo (con la lista de Ajustes, 1-2 mañana y 3-4 tarde; sin ella, numeración compacta del reparto). Toda salida (PDF, .ics, web, correo, diálogos) lo traduce con `services/recreos.py` (`resolver`, `recreos_de`): «Recreo 1 de tarde · 16:30». Nunca pintar `guardia.recreo` tal cual. Zonas en los PDF compactos: `pdf_styles.abreviatura_zona`, nunca un código secuencial.
