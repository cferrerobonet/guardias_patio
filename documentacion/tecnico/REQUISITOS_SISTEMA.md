# Requisitos del Sistema

## 📋 Descripción General

Este documento especifica los requisitos mínimos de hardware y software necesarios para ejecutar correctamente la aplicación **Guardias de Patio**.

---

## 💻 Requisitos de Hardware

### Resolución de Pantalla

La aplicación ha sido diseñada para funcionar de manera óptima en pantallas modernas. Los requisitos de resolución son:

#### ✅ Requisitos Mínimos (Obligatorios)

- **Resolución mínima:** 1280 x 720 píxeles (HD 720p)
- **Relación de aspecto:** 16:9 o similar
- **Espacio de trabajo:** La aplicación se abrirá maximizada por defecto

> ⚠️ **IMPORTANTE:** Si tu pantalla no cumple con la resolución mínima de 1280x720, la aplicación **no se ejecutará** y mostrará un mensaje de error. Esto es para garantizar una experiencia de usuario óptima y evitar que campos, textos y controles se visualicen incorrectamente.

#### 🌟 Configuración Recomendada

- **Resolución recomendada:** 1920 x 1080 píxeles (Full HD) o superior
- **Resoluciones probadas:**
  - 1920 x 1080 (Full HD) - ✅ Óptima
  - 2560 x 1440 (2K QHD) - ✅ Excelente
  - 3840 x 2160 (4K UHD) - ✅ Excelente

> 💡 **Nota:** Si tu resolución está entre 1280x720 y 1920x1080, la aplicación se ejecutará pero mostrará una advertencia informativa. Algunos elementos de la interfaz podrían verse ligeramente reducidos, aunque seguirán siendo funcionales.

### Otros Requisitos de Hardware

- **Procesador:** Intel Core i3 (8ª gen) o equivalente AMD
- **Memoria RAM:** 4 GB mínimo, 8 GB recomendado
- **Espacio en disco:** 500 MB libres para instalación
- **Tarjeta gráfica:** Compatible con aceleración de hardware (para PyQt6)

---

## 🖥️ Sistemas Operativos Soportados

### macOS

- **Versión mínima:** macOS 10.14 (Mojave) o superior
- **Versión recomendada:** macOS 12 (Monterey) o superior
- **Arquitecturas:** Intel x86_64 y Apple Silicon (M1/M2/M3)

### Windows

- **Versión mínima:** Windows 10 (64-bit)
- **Versión recomendada:** Windows 11
- **Arquitecturas:** x86_64

### Linux (Experimental)

- **Distribuciones probadas:** Ubuntu 20.04+, Fedora 35+
- **Entorno de escritorio:** GNOME, KDE, XFCE con soporte Qt6
- **Nota:** Soporte experimental, puede requerir configuración adicional

---

## 📦 Requisitos de Software

### Versión Instalador (Recomendada)

Si usas el instalador DMG (macOS) o EXE (Windows), no necesitas instalar nada adicional. Todos los componentes están incluidos:

- ✅ Python 3.11 embebido
- ✅ PyQt6 y todas las dependencias
- ✅ Bibliotecas del sistema necesarias

### Versión desde Código Fuente

Si ejecutas la aplicación desde código fuente, necesitas:

- **Python:** 3.11.14 (otras versiones de Python 3.11.x pueden funcionar)
- **pip:** Gestor de paquetes de Python
- **Dependencias:** Instaladas automáticamente con `pip install -r requirements.txt`

---

## 🔍 Validación de Resolución

La aplicación incluye un sistema automático de validación de resolución que se ejecuta al inicio:

### Comportamiento del Validador

1. **Resolución < 1280x720 (Insuficiente)**
   - ❌ La aplicación NO se ejecutará
   - Se mostrará un diálogo modal con el error
   - Mensaje: "Resolución de Pantalla Insuficiente"
   - Acción requerida: Ajustar resolución de pantalla

2. **1280x720 ≤ Resolución < 1920x1080 (Por debajo de lo recomendado)**
   - ⚠️ La aplicación se ejecutará con advertencia
   - Se mostrará un diálogo informativo
   - Mensaje: "Resolución por debajo de lo recomendado"
   - Opción: Continuar o cancelar

3. **Resolución ≥ 1920x1080 (Óptima)**
   - ✅ La aplicación se ejecutará sin advertencias
   - Experiencia de usuario óptima garantizada

### Ejemplo de Diálogo de Error

```
⚠️ Resolución de Pantalla Insuficiente

La resolución actual de tu pantalla es 1024x768 píxeles.

Para una correcta visualización de la aplicación, se requiere una resolución mínima de:

• Mínimo requerido: 1280x720 píxeles
• Recomendado: 1920x1080 píxeles o superior

La aplicación no se ejecutará para evitar una mala experiencia de usuario
con campos y textos que no se visualizan correctamente.

Por favor, ajusta la resolución de tu pantalla e intenta de nuevo.
```

---

## 🛠️ Solución de Problemas

### "La aplicación no se ejecuta - Error de resolución"

**Problema:** Recibes un mensaje de "Resolución Insuficiente"

**Soluciones:**

1. **Ajustar resolución en macOS:**
   - Ve a  → Preferencias del Sistema → Pantallas
   - Selecciona una resolución de al menos 1280x720
   - Si tu monitor lo soporta, selecciona 1920x1080 o superior

2. **Ajustar resolución en Windows:**
   - Click derecho en el escritorio → Configuración de pantalla
   - En "Resolución de pantalla", selecciona 1280x720 o superior
   - Recomendado: 1920x1080 o superior

3. **Usar monitor externo:**
   - Si tu laptop tiene una pantalla pequeña, conecta un monitor externo
   - Configura el monitor externo como pantalla principal
   - Asegúrate de que el monitor externo esté configurado a 1920x1080 o superior

### "Algunos elementos se ven apretados o pequeños"

**Problema:** La aplicación se ejecuta pero algunos elementos se ven mal

**Soluciones:**

1. **Aumentar resolución:**
   - Cambia a una resolución mayor (1920x1080 recomendado)
   
2. **Maximizar ventana:**
   - La aplicación se abre maximizada por defecto
   - Si la redimensionaste, maximízala de nuevo (botón verde en macOS, o doble click en barra de título en Windows)

3. **Ajustar escala del sistema:**
   - En Windows: Configuración → Sistema → Pantalla → Escala y diseño
   - En macOS: Preferencias del Sistema → Pantallas → Resolución (selecciona "Por Defecto para pantalla")

---

## 📊 Tabla Resumen de Requisitos

| Componente | Mínimo | Recomendado | Óptimo |
|------------|--------|-------------|--------|
| **Resolución** | 1280 x 720 | 1920 x 1080 | 2560 x 1440+ |
| **Procesador** | Intel i3 8ª gen | Intel i5 10ª gen | Intel i7 11ª gen+ |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Disco** | 500 MB | 1 GB | 2 GB |
| **macOS** | 10.14 Mojave | 12 Monterey | 14 Sonoma |
| **Windows** | 10 (64-bit) | 11 | 11 |

---

## ✅ Verificación Pre-instalación

Antes de instalar, verifica que tu sistema cumple con los requisitos:

### Verificar Resolución (macOS)

```bash
system_profiler SPDisplaysDataType | grep Resolution
```

### Verificar Resolución (Windows PowerShell)

```powershell
Get-WmiObject -Class Win32_VideoController | Select-Object CurrentHorizontalResolution, CurrentVerticalResolution
```

### Verificar Python (si ejecutas desde código fuente)

```bash
python3 --version
# Debe mostrar: Python 3.11.x
```

---

## 📞 Soporte

Si tienes problemas relacionados con los requisitos del sistema:

1. Revisa esta documentación completamente
2. Verifica que tu hardware cumple con los mínimos
3. Consulta la sección de Solución de Problemas
4. Si el problema persiste, abre un issue en GitHub con:
   - Resolución de pantalla actual
   - Sistema operativo y versión
   - Mensaje de error completo (si aplica)
   - Captura de pantalla (si es posible)

---

## 📝 Notas Adicionales

- La validación de resolución se ejecuta automáticamente al iniciar la aplicación
- No es posible desactivar la validación de resolución mínima
- La validación está implementada en `src/utils/screen_validator.py`
- Los valores mínimos y recomendados están definidos como constantes de clase:
  - `MIN_WIDTH = 1280`
  - `MIN_HEIGHT = 720`
  - `RECOMMENDED_WIDTH = 1920`
  - `RECOMMENDED_HEIGHT = 1080`

---

**Última actualización:** Octubre 2025  
**Versión de la aplicación:** 2.7.0
