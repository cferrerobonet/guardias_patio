# Sistema de PDFs Corporativos - Guardias de Patio

## Resumen

Sistema estandarizado de generación de PDFs con estilo corporativo unificado para todos los documentos de la aplicación.

---

## Estructura

### 1. Módulo de Estilos (`src/services/pdf_styles.py`)

**Clase principal:** `PDFStyles`

Centraliza todos los estilos, colores y configuraciones para garantizar consistencia visual.

#### Paleta de Colores Corporativa

**Azules principales:**
- `AZUL_PRINCIPAL`: #1976D2 (Encabezados, fondo principal)
- `AZUL_OSCURO`: #0D47A1 (Bordes decorativos)
- `AZUL_CLARO`: #E3F2FD (Texto sobre azul)

**Colores para datos dinámicos** (compatibles con fondo azul):
- `COLOR_DATO_PRINCIPAL`: #FFD54F (Amarillo/dorado - MÁS destacado)
- `COLOR_DATO_SECUNDARIO`: #FFE082 (Amarillo claro - Medianamente destacado)
- `COLOR_DATO_TERCIARIO`: #FFF59D (Amarillo pastel - Menos destacado)

**Colores para zonas** (hasta 10 diferentes):
1. Rojo (#e74c3c)
2. Azul (#3498db)
3. Verde (#2ecc71)
4. Naranja (#f39c12)
5. Morado (#9b59b6)
6. Turquesa (#1abc9c)
7. Naranja oscuro (#e67e22)
8. Gris oscuro (#34495e)
9. Rosa (#e91e63)
10. Cian (#00bcd4)

**Colores para recreos:**
1. Verde (#4CAF50)
2. Naranja (#FF9800)
3. Morado (#9C27B0)
4. Rojo (#F44336)

**Colores para separación de meses** (fondos alternos):
- Verde muy claro (#E8F5E9)
- Azul muy claro (#E3F2FD)
- Naranja muy claro (#FFF3E0)
- Morado muy claro (#F3E5F5)
- Turquesa muy claro (#E0F2F1)

#### Tipografía Estandarizada

**Fuentes:**
- Títulos: `Helvetica-Bold`
- Subtítulos: `Helvetica-Bold`
- Texto normal: `Helvetica`
- Énfasis: `Helvetica-Bold`

**Tamaños:**
- Título principal: 18pt
- Subtítulo: 14pt
- Texto normal: 10pt
- Texto pequeño: 8pt
- Encabezado tabla: 10pt
- Cuerpo tabla: 9pt

#### Métodos Principales

```python
PDFStyles.get_titulo_principal(texto_color=None)
PDFStyles.get_subtitulo(texto_color=None)
PDFStyles.get_texto_normal(texto_color=None, alineacion=0)
PDFStyles.get_texto_pequeno(texto_color=None, alineacion=0)
PDFStyles.get_color_zona(zona_id)
PDFStyles.get_color_recreo(recreo)
PDFStyles.get_color_mes(mes_index)
PDFStyles.get_meses_nombres()
PDFStyles.get_dias_semana_completos()
PDFStyles.get_dias_semana_cortos()
```

---

### 2. Exportador de PDFs Actualizado (`src/services/exportador_pdf.py`)

#### Mejoras Implementadas

**A. Banner de Encabezado Mejorado**

```
┌─────────────────────────────────────────────────────────────┐
│ [FONDO AZUL PRINCIPAL #1976D2]                             │
│                                                             │
│     CALENDARIO PERSONAL DE GUARDIAS (Blanco)               │
│     GARCÍA PÉREZ, MARÍA (Amarillo dorado #FFD54F)          │
│                                                             │
│  Turno: Mañana (Amarillo claro) • Tutor: Sí (Amarillo claro)│
│  • Periodo: 01/09/2024 - 30/06/2025 (Amarillo pastel)      │
└─────────────────────────────────────────────────────────────┘
[BORDE AZUL OSCURO #0D47A1]
```

**Características:**
- Fondo azul corporativo
- Nombre del profesor en **amarillo dorado** (máxima visibilidad)
- Datos dinámicos en tonos amarillos compatibles con azul
- Distribución horizontal de información

**B. Tabla de Guardias con Separación Visual**

**Características:**
1. **Separación por meses:** Cada mes tiene un color de fondo alterno (verde claro, azul claro, naranja claro, etc.)
2. **Recreos diferenciados:** Texto en negrita con colores específicos:
   - Recreo 1: Verde
   - Recreo 2: Naranja
   - Recreo 3: Morado
   - Recreo 4: Rojo
3. **Zonas diferenciadas:** Texto en negrita con colores específicos según zona ID
4. **Líneas separadoras gruesas** entre meses (3pt, azul principal)

**Ejemplo visual:**

```
╔═══════════════════════════════════════════════════════════╗
║ Fecha    │ Día │ Turno  │ Recreo-Hora  │ Zona           ║
╠═══════════════════════════════════════════════════════════╣
║ [FONDO VERDE CLARO - SEPTIEMBRE]                         ║
║ 02/09/24 │ L   │ Mañana │ Recreo 1 (Verde) │ Patio (Rojo)║
║ 03/09/24 │ M   │ Mañana │ Recreo 2 (Naranja) │ Aula (Azul)║
╠═══════════════════════════════════════════════════════════╣ (LÍNEA GRUESA)
║ [FONDO AZUL CLARO - OCTUBRE]                             ║
║ 01/10/24 │ M   │ Tarde  │ Recreo 1 (Verde) │ Patio (Rojo)║
╚═══════════════════════════════════════════════════════════╝
```

**C. Mini-Calendarios Actualizados**

- Usan colores corporativos para zonas (hasta 10 colores)
- Formas diferenciadas por recreo:
  - ● Círculo = Recreo 1
  - ■ Cuadrado = Recreo 2
  - ▲ Triángulo = Recreo 3
  - ◆ Rombo = Recreo 4+

**D. Leyenda Compacta**

Muestra:
- Formas de recreos con explicación
- Colores de zonas utilizadas en el documento
- Diseño compacto en una sola línea

---

## Uso para Futuros PDFs

### Plantilla Estándar

```python
from services.pdf_styles import PDFStyles
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm

# Crear documento con márgenes corporativos
doc = SimpleDocTemplate(
    "salida.pdf",
    pagesize=PDFStyles.PAGESIZE,
    rightMargin=PDFStyles.MARGEN_DERECHO,
    leftMargin=PDFStyles.MARGEN_IZQUIERDO,
    topMargin=PDFStyles.MARGEN_SUPERIOR,
    bottomMargin=PDFStyles.MARGEN_INFERIOR,
)

elements = []

# Título con estilo corporativo
titulo_style = PDFStyles.get_titulo_principal()
titulo = Paragraph("Mi Título", titulo_style)
elements.append(titulo)
elements.append(Spacer(1, 0.5*cm))

# Texto normal
texto_style = PDFStyles.get_texto_normal()
contenido = Paragraph("Mi contenido...", texto_style)
elements.append(contenido)

# Construir PDF
doc.build(elements)
```

### Banner de Encabezado Reutilizable

```python
from reportlab.graphics.shapes import Drawing, Rect, String
from services.pdf_styles import PDFStyles

def crear_banner_corporativo(ancho, titulo, nombre, datos_dict):
    """
    Crea un banner corporativo estandarizado.
    
    Args:
        ancho: Ancho del banner
        titulo: Texto del título principal
        nombre: Nombre destacado (amarillo)
        datos_dict: Dict con {label: valor} para mostrar
    
    Returns:
        Drawing con el banner
    """
    altura = 2.5*cm
    banner = Drawing(ancho, altura)
    
    # Fondo azul
    fondo = Rect(
        0, 0, ancho, altura,
        fillColor=PDFStyles.AZUL_PRINCIPAL,
        strokeColor=None
    )
    banner.add(fondo)
    
    # Borde inferior
    borde = Rect(
        0, 0, ancho, 0.3*cm,
        fillColor=PDFStyles.AZUL_OSCURO,
        strokeColor=None
    )
    banner.add(borde)
    
    # Título
    titulo_texto = String(
        ancho/2, altura - 0.8*cm,
        titulo,
        fontSize=PDFStyles.TAMANO_TITULO_PRINCIPAL,
        fontName=PDFStyles.FUENTE_TITULO,
        textAnchor='middle',
        fillColor=colors.whitesmoke
    )
    banner.add(titulo_texto)
    
    # Nombre destacado
    nombre_texto = String(
        ancho/2, altura - 1.5*cm,
        nombre.upper(),
        fontSize=PDFStyles.TAMANO_SUBTITULO,
        fontName=PDFStyles.FUENTE_TITULO,
        textAnchor='middle',
        fillColor=PDFStyles.COLOR_DATO_PRINCIPAL
    )
    banner.add(nombre_texto)
    
    # Datos adicionales
    x_pos = 3*cm
    for label, valor in datos_dict.items():
        # Label en azul claro
        label_texto = String(
            x_pos, altura - 2.1*cm,
            f"{label}:",
            fontSize=9,
            fontName='Helvetica',
            textAnchor='start',
            fillColor=PDFStyles.AZUL_CLARO
        )
        banner.add(label_texto)
        
        # Valor en amarillo
        valor_texto = String(
            x_pos + 1.2*cm, altura - 2.1*cm,
            str(valor),
            fontSize=9,
            fontName='Helvetica-Bold',
            textAnchor='start',
            fillColor=PDFStyles.COLOR_DATO_SECUNDARIO
        )
        banner.add(valor_texto)
        
        x_pos += 4*cm
    
    return banner
```

### Tabla con Colores Corporativos

```python
from reportlab.platypus import Table, TableStyle
from services.pdf_styles import PDFStyles

# Crear tabla
data = [
    ['Col1', 'Col2', 'Col3'],
    ['Dato1', 'Dato2', 'Dato3'],
    ['Dato4', 'Dato5', 'Dato6'],
]

tabla = Table(data)

# Aplicar estilo corporativo
tabla.setStyle(TableStyle([
    # Encabezado corporativo
    ('BACKGROUND', (0, 0), (-1, 0), PDFStyles.FONDO_TABLA_HEADER),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('FONTNAME', (0, 0), (-1, 0), PDFStyles.FUENTE_NEGRITA),
    ('FONTSIZE', (0, 0), (-1, 0), PDFStyles.TAMANO_ENCABEZADO_TABLA),
    
    # Cuerpo
    ('FONTNAME', (0, 1), (-1, -1), PDFStyles.FUENTE_NORMAL),
    ('FONTSIZE', (0, 1), (-1, -1), PDFStyles.TAMANO_CUERPO_TABLA),
    ('TEXTCOLOR', (0, 1), (-1, -1), PDFStyles.TEXTO_OSCURO),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
]))
```

---

## Ventajas del Sistema

1. **Consistencia visual:** Todos los PDFs usan la misma paleta de colores y tipografía
2. **Mantenibilidad:** Cambios en estilos se hacen en un solo lugar
3. **Accesibilidad:** Colores con alto contraste para mejor legibilidad
4. **Profesionalismo:** Diseño corporativo unificado
5. **Escalabilidad:** Fácil agregar nuevos estilos o colores
6. **Reutilización:** Métodos auxiliares para casos comunes

---

## Ejemplos de Uso

### PDF de Guardias Individual

**Características implementadas:**
- ✅ Banner azul con datos en amarillo
- ✅ Mini-calendarios con colores por zona
- ✅ Tabla separada por meses
- ✅ Recreos y zonas diferenciados visualmente
- ✅ Leyenda compacta

### Futuros PDFs a Implementar

**Sugerencias:**
1. **Informe de Estadísticas:** Usar gráficos con colores corporativos
2. **Listado de Profesores:** Tabla con encabezado azul y datos alternados
3. **Calendario de Ausencias:** Separar por meses con fondos alternos
4. **Reporte de Configuración:** Banner azul con datos destacados

---

## Mantenimiento

### Agregar un Nuevo Color

```python
# En pdf_styles.py, clase PDFStyles:

NUEVO_COLOR = colors.HexColor('#RRGGBB')  # Describir uso
```

### Agregar un Nuevo Estilo

```python
@classmethod
def get_nuevo_estilo(cls, parametros):
    """Descripción del estilo."""
    styles = cls.get_base_styles()
    return ParagraphStyle(
        'NombreEstilo',
        parent=styles['Base'],
        fontSize=cls.TAMANO_TEXTO_NORMAL,
        textColor=cls.TEXTO_OSCURO,
        # ... otras propiedades
    )
```

---

## Notas Técnicas

- **Librería:** reportlab 4.x
- **Formato de página:** A4 landscape
- **Encoding:** UTF-8
- **Compatibilidad:** PDF 1.4+

---

**Autor:** Sistema de Guardias de Patio  
**Versión:** 1.0  
**Fecha:** Noviembre 2025
