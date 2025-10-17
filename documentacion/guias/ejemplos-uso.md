# 💡 Ejemplos de Uso - Sistema de Utilidades v2.2

## 📋 Índice

1. [Logging](#-logging)
2. [Validadores](#-validadores)
3. [Constantes](#-constantes)
4. [Excepciones](#️-excepciones)
5. [Patrones de Integración](#-patrones-de-integración)

---

## 📝 Logging

### Ejemplo 1: Configuración Inicial

```python
# src/main.py - Al inicio de la aplicación
from src.utils.logger import setup_logging
import sys
from pathlib import Path

def main():
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configurar logging
    setup_logging(
        log_file="logs/guardias.log",
        level="DEBUG" if "--debug" in sys.argv else "INFO",
        format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Resto de la aplicación
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

### Ejemplo 2: Logging en Servicios

```python
# src/services/profesor_service.py
from src.utils.logger import get_logger, log_function_call
from src.models.profesor import Profesor

logger = get_logger(__name__)

class ProfesorService:
    """Servicio para gestión de profesores."""
    
    @log_function_call(logger)
    def crear_profesor(self, nombre: str, email: str, horas_contrato: int) -> Profesor:
        """
        Crea un nuevo profesor.
        
        Este método se loguea automáticamente por el decorador @log_function_call
        que registra:
        - Inicio de la función con parámetros
        - Resultado de retorno
        - Cualquier excepción lanzada
        """
        logger.info(f"Creando profesor: {nombre}")
        logger.debug(f"Detalles - Email: {email}, Horas: {horas_contrato}")
        
        try:
            profesor = Profesor(
                nombre=nombre,
                email=email,
                horas_contrato=horas_contrato
            )
            self.session.add(profesor)
            self.session.commit()
            
            logger.info(f"✓ Profesor creado exitosamente: ID={profesor.id}")
            return profesor
            
        except IntegrityError as e:
            logger.error(f"✗ Error de integridad al crear profesor", exc_info=True)
            self.session.rollback()
            raise
        
        except Exception as e:
            logger.critical(f"✗ Error inesperado al crear profesor", exc_info=True)
            self.session.rollback()
            raise
```

### Ejemplo 3: Logging en Cálculos Complejos

```python
# src/services/calculador_guardias.py
from src.utils.logger import get_logger

logger = get_logger(__name__)

def calcular_distribucion_cruda(profesores, config):
    """Calcula la distribución inicial de guardias."""
    logger.info("=== Iniciando cálculo de distribución ===")
    logger.info(f"Profesores activos: {len(profesores)}")
    logger.debug(f"Configuración: {config}")
    
    # Cálculo de slots totales
    slots_totales = config.dias_lectivos * config.num_recreos * config.num_zonas
    logger.info(f"Slots totales a asignar: {slots_totales}")
    
    # Suma de horas ponderadas
    suma_horas = sum(p.horas_contrato * p.multiplicador for p in profesores)
    logger.debug(f"Suma horas ponderadas: {suma_horas}")
    
    if suma_horas == 0:
        logger.error("✗ Suma de horas es 0, no se puede calcular distribución")
        raise ValueError("No hay profesores con horas válidas")
    
    # Calcular guardias por profesor
    distribucion = {}
    for profesor in profesores:
        factor = (profesor.horas_contrato * profesor.multiplicador) / suma_horas
        guardias = int(slots_totales * factor)
        distribucion[profesor.id] = guardias
        
        logger.debug(
            f"Profesor {profesor.nombre}: "
            f"{profesor.horas_contrato}h × {profesor.multiplicador} = "
            f"{guardias} guardias ({factor*100:.1f}%)"
        )
    
    logger.info(f"✓ Distribución calculada para {len(distribucion)} profesores")
    logger.debug(f"Total guardias asignadas: {sum(distribucion.values())}")
    
    return distribucion
```

### Ejemplo 4: Logging en UI

```python
# src/main.py - En widgets de UI
from src.utils.logger import get_logger

logger = get_logger(__name__)

class ProfesorForm(QWidget):
    """Formulario de gestión de profesores."""
    
    def guardar_profesor(self):
        """Guarda un profesor con logging de la operación."""
        logger.info("Usuario solicitó guardar profesor")
        
        nombre = self.input_nombre.text()
        logger.debug(f"Datos del formulario - Nombre: {nombre}")
        
        # Validación
        valido, error = validar_nombre_completo(nombre)
        if not valido:
            logger.warning(f"Validación fallida: {error}")
            QMessageBox.warning(self, "Error", error)
            return
        
        try:
            # Guardar
            profesor = self.service.crear_profesor(nombre, email, horas)
            logger.info(f"✓ Profesor guardado desde UI: {profesor.nombre}")
            
            # Actualizar UI
            self.cargar_profesores()
            QMessageBox.information(self, "Éxito", "Profesor guardado")
            
        except Exception as e:
            logger.error(f"✗ Error al guardar profesor desde UI", exc_info=True)
            QMessageBox.critical(self, "Error", str(e))
```

---

## ✅ Validadores

### Ejemplo 1: Validación de Email

```python
from src.utils.validators import validar_email
from PyQt6.QtWidgets import QMessageBox

def validar_formulario_profesor(self):
    """Valida todos los campos del formulario de profesor."""
    email = self.input_email.text().strip()
    
    # Validar email
    valido, error = validar_email(email)
    if not valido:
        QMessageBox.warning(self, "Error de Validación", error)
        self.input_email.setFocus()
        self.input_email.selectAll()
        return False
    
    return True

# Ejemplos de uso:
# validar_email("profesor@colegio.es")        → (True, None)
# validar_email("profesor.garcia@edu.es")     → (True, None)
# validar_email("profesor")                   → (False, "Email con formato inválido")
# validar_email("")                           → (False, "El email no puede estar vacío")
# validar_email("@colegio.es")                → (False, "Email con formato inválido")
```

### Ejemplo 2: Validación de Nombre

```python
from src.utils.validators import validar_nombre_completo

def procesar_nombre_profesor(nombre: str):
    """Valida y procesa el nombre del profesor."""
    # Validar formato "APELLIDOS, NOMBRE"
    valido, error = validar_nombre_completo(nombre)
    
    if not valido:
        raise ValueError(error)
    
    # Si es válido, se puede procesar
    apellidos, nombre_propio = nombre.split(",")
    return apellidos.strip(), nombre_propio.strip()

# Ejemplos:
# validar_nombre_completo("García López, María")     → (True, None)
# validar_nombre_completo("Fernández, Juan Carlos")  → (True, None)
# validar_nombre_completo("García López María")      → (False, "El nombre debe tener el formato...")
# validar_nombre_completo("")                        → (False, "El nombre no puede estar vacío")
# validar_nombre_completo("García,")                 → (False, "El nombre debe tener el formato...")
```

### Ejemplo 3: Validación de Horas de Contrato

```python
from src.utils.validators import validar_horas_contrato

def calcular_carga_profesor(horas_str: str):
    """Calcula la carga de un profesor validando las horas."""
    try:
        horas = int(horas_str)
    except ValueError:
        return None, "Las horas deben ser un número entero"
    
    # Validar rango
    valido, error = validar_horas_contrato(horas)
    if not valido:
        return None, error
    
    # Calcular porcentaje de jornada
    porcentaje = (horas / 40) * 100
    return porcentaje, None

# Ejemplos:
# validar_horas_contrato(25)    → (True, None)
# validar_horas_contrato(40)    → (True, None)
# validar_horas_contrato(0)     → (True, None)  # Profesor sin horas (p.ej. baja)
# validar_horas_contrato(45)    → (False, "Las horas de contrato no pueden superar 40")
# validar_horas_contrato(-5)    → (False, "Las horas de contrato deben ser positivas")
```

### Ejemplo 4: Validación de Turno

```python
from src.utils.validators import validar_turno
from src.utils.constants import TURNO_MANANA, TURNO_TARDE, TURNO_MIXTO

def asignar_turno_profesor(turno: str):
    """Asigna un turno a un profesor validándolo previamente."""
    # Normalizar (minúsculas)
    turno_lower = turno.lower()
    
    # Validar
    valido, error = validar_turno(turno_lower)
    if not valido:
        raise ValueError(error)
    
    # Usar constantes para comparaciones
    if turno_lower == TURNO_MANANA:
        horario = "08:00 - 14:00"
    elif turno_lower == TURNO_TARDE:
        horario = "14:00 - 20:00"
    else:  # TURNO_MIXTO
        horario = "08:00 - 20:00"
    
    return turno_lower, horario

# Ejemplos:
# validar_turno("mañana")    → (True, None)
# validar_turno("tarde")     → (True, None)
# validar_turno("mixto")     → (True, None)
# validar_turno("noche")     → (False, "El turno debe ser uno de: mañana, tarde, mixto")
# validar_turno("")          → (False, "El turno no puede estar vacío")
```

### Ejemplo 5: Validación de Fechas

```python
from datetime import date, timedelta
from src.utils.validators import validar_fecha, validar_rango_fechas

def configurar_curso_escolar(fecha_inicio: date, fecha_fin: date):
    """Configura el curso escolar validando las fechas."""
    # Validar que ambas fechas sean válidas
    valido, error = validar_fecha(fecha_inicio, fecha_minima=date.today())
    if not valido:
        return None, f"Fecha inicio inválida: {error}"
    
    valido, error = validar_fecha(fecha_fin, fecha_minima=fecha_inicio)
    if not valido:
        return None, f"Fecha fin inválida: {error}"
    
    # Validar rango
    valido, error = validar_rango_fechas(fecha_inicio, fecha_fin)
    if not valido:
        return None, error
    
    # Calcular duración
    duracion = (fecha_fin - fecha_inicio).days + 1
    
    return {
        'inicio': fecha_inicio,
        'fin': fecha_fin,
        'duracion_dias': duracion
    }, None

# Ejemplos:
# fecha_inicio = date(2025, 9, 1)
# fecha_fin = date(2026, 6, 30)
# validar_rango_fechas(fecha_inicio, fecha_fin)  → (True, None)

# fecha_inicio = date(2025, 6, 30)
# fecha_fin = date(2025, 9, 1)
# validar_rango_fechas(fecha_inicio, fecha_fin)  → (False, "La fecha de inicio debe ser anterior...")
```

### Ejemplo 6: Validación de Días de la Semana

```python
from src.utils.validators import validar_dias_semana

def configurar_dias_guardias(dias_str: str):
    """Configura los días en que hay guardias."""
    # Validar formato
    valido, error = validar_dias_semana(dias_str)
    if not valido:
        return None, error
    
    # Convertir a lista
    dias = [dia.strip() for dia in dias_str.split(",")]
    
    # Procesar
    return {
        'dias': dias,
        'cantidad': len(dias),
        'incluye_viernes': 'viernes' in dias
    }, None

# Ejemplos:
# validar_dias_semana("lunes,miércoles,viernes")     → (True, None)
# validar_dias_semana("lunes, martes, jueves")       → (True, None)  # Espacios OK
# validar_dias_semana("lunes,martes,miércoles,jueves,viernes")  → (True, None)
# validar_dias_semana("lunes,domingo")               → (False, "Día inválido: domingo")
# validar_dias_semana("")                            → (False, "La cadena de días no puede estar vacía")
# validar_dias_semana("lunes,invalidodia,martes")    → (False, "Día inválido: invalidodia")
```

### Ejemplo 7: Validación Completa de Formulario

```python
from src.utils.validators import (
    validar_email,
    validar_nombre_completo,
    validar_horas_contrato,
    validar_turno
)

class ProfesorForm:
    """Formulario de profesor con validación completa."""
    
    def validar_y_guardar(self):
        """Valida todos los campos y guarda si son válidos."""
        errores = []
        
        # 1. Validar nombre
        nombre = self.input_nombre.text().strip()
        valido, error = validar_nombre_completo(nombre)
        if not valido:
            errores.append(f"Nombre: {error}")
        
        # 2. Validar email
        email = self.input_email.text().strip()
        valido, error = validar_email(email)
        if not valido:
            errores.append(f"Email: {error}")
        
        # 3. Validar horas
        try:
            horas = int(self.input_horas.text())
            valido, error = validar_horas_contrato(horas)
            if not valido:
                errores.append(f"Horas: {error}")
        except ValueError:
            errores.append("Horas: Debe ser un número entero")
        
        # 4. Validar turno
        turno = self.combo_turno.currentText().lower()
        valido, error = validar_turno(turno)
        if not valido:
            errores.append(f"Turno: {error}")
        
        # Mostrar errores o guardar
        if errores:
            mensaje = "Se encontraron los siguientes errores:\n\n"
            mensaje += "\n".join(f"• {e}" for e in errores)
            QMessageBox.warning(self, "Errores de Validación", mensaje)
            return False
        
        # Si todo es válido, guardar
        self.guardar_profesor(nombre, email, horas, turno)
        return True
```

---

## 📊 Constantes

### Ejemplo 1: Constantes de Turno

```python
from src.utils.constants import (
    TURNO_MANANA,
    TURNO_TARDE,
    TURNO_MIXTO,
    TURNOS_VALIDOS
)

def calcular_horario_profesor(turno: str):
    """Calcula el horario según el turno."""
    if turno == TURNO_MANANA:
        return "08:00", "14:00"
    elif turno == TURNO_TARDE:
        return "14:00", "20:00"
    elif turno == TURNO_MIXTO:
        return "08:00", "20:00"
    else:
        raise ValueError(f"Turno inválido. Debe ser uno de: {TURNOS_VALIDOS}")

# Poblar ComboBox
def poblar_combo_turnos(combo_box):
    """Puebla un QComboBox con los turnos válidos."""
    combo_box.clear()
    combo_box.addItems([
        TURNO_MANANA.capitalize(),
        TURNO_TARDE.capitalize(),
        TURNO_MIXTO.capitalize()
    ])
```

### Ejemplo 2: Constantes de Días

```python
from src.utils.constants import (
    DIA_LUNES, DIA_MARTES, DIA_MIERCOLES, DIA_JUEVES, DIA_VIERNES,
    DIAS_SEMANA
)

def convertir_fecha_a_dia_semana(fecha: date):
    """Convierte una fecha a nombre de día."""
    dia_numero = fecha.weekday()  # 0=Lunes, 6=Domingo
    return DIAS_SEMANA.get(dia_numero, "Desconocido")

# Ejemplo:
# fecha = date(2025, 1, 20)  # Lunes
# convertir_fecha_a_dia_semana(fecha)  → "lunes"

def es_dia_lectivo(fecha: date):
    """Verifica si un día es lectivo (lunes a viernes)."""
    dia_numero = fecha.weekday()
    return DIA_LUNES <= dia_numero <= DIA_VIERNES
```

### Ejemplo 3: Constantes de Validación

```python
from src.utils.constants import (
    MAX_HORAS_CONTRATO,
    MAX_GUARDIAS_POR_PROFESOR_DIA,
    MIN_PROFESORES_PARA_ASIGNACION
)

def validar_carga_profesores(profesores: list):
    """Valida que hay suficientes profesores."""
    if len(profesores) < MIN_PROFESORES_PARA_ASIGNACION:
        raise ValueError(
            f"Se requieren al menos {MIN_PROFESORES_PARA_ASIGNACION} profesores "
            f"para realizar la asignación"
        )
    
    # Validar horas de cada profesor
    for profesor in profesores:
        if profesor.horas_contrato > MAX_HORAS_CONTRATO:
            raise ValueError(
                f"El profesor {profesor.nombre} tiene {profesor.horas_contrato} horas, "
                f"superando el máximo de {MAX_HORAS_CONTRATO}"
            )

def puede_asignar_guardia(profesor, fecha):
    """Verifica si se puede asignar otra guardia al profesor."""
    guardias_hoy = contar_guardias_profesor_fecha(profesor.id, fecha)
    
    if guardias_hoy >= MAX_GUARDIAS_POR_PROFESOR_DIA:
        return False, f"El profesor ya tiene {MAX_GUARDIAS_POR_PROFESOR_DIA} guardias hoy"
    
    return True, None
```

### Ejemplo 4: Constantes de UI

```python
from src.utils.constants import (
    MAX_WIDTH_INPUT_SMALL,
    MAX_WIDTH_INPUT_MEDIUM,
    MAX_WIDTH_INPUT_LARGE,
    MAX_WIDTH_INPUT_XLARGE
)

def crear_formulario_profesor():
    """Crea un formulario con anchos consistentes."""
    layout = QFormLayout()
    
    # Campo corto (ID, código)
    input_id = QLineEdit()
    input_id.setMaximumWidth(MAX_WIDTH_INPUT_SMALL)
    layout.addRow("ID:", input_id)
    
    # Campo mediano (email)
    input_email = QLineEdit()
    input_email.setMaximumWidth(MAX_WIDTH_INPUT_MEDIUM)
    layout.addRow("Email:", input_email)
    
    # Campo grande (nombre completo)
    input_nombre = QLineEdit()
    input_nombre.setMaximumWidth(MAX_WIDTH_INPUT_LARGE)
    layout.addRow("Nombre:", input_nombre)
    
    # Campo extra grande (observaciones)
    input_observaciones = QTextEdit()
    input_observaciones.setMaximumWidth(MAX_WIDTH_INPUT_XLARGE)
    layout.addRow("Observaciones:", input_observaciones)
    
    return layout
```

### Ejemplo 5: Constantes de Mensajes

```python
from src.utils.constants import (
    MSG_EXITO_GUARDADO,
    MSG_EXITO_ELIMINADO,
    MSG_ERROR_TITULO,
    MSG_CONFIRMACION_ELIMINAR
)
from PyQt6.QtWidgets import QMessageBox

def guardar_profesor(self, profesor):
    """Guarda un profesor con mensajes consistentes."""
    try:
        self.service.guardar(profesor)
        QMessageBox.information(
            self,
            "Éxito",
            MSG_EXITO_GUARDADO
        )
    except Exception as e:
        QMessageBox.critical(
            self,
            MSG_ERROR_TITULO,
            f"Error al guardar: {str(e)}"
        )

def eliminar_profesor(self, profesor):
    """Elimina un profesor con confirmación."""
    respuesta = QMessageBox.question(
        self,
        "Confirmar Eliminación",
        MSG_CONFIRMACION_ELIMINAR.format(tipo="profesor", nombre=profesor.nombre),
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )
    
    if respuesta == QMessageBox.StandardButton.Yes:
        try:
            self.service.eliminar(profesor.id)
            QMessageBox.information(
                self,
                "Éxito",
                MSG_EXITO_ELIMINADO
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                f"Error al eliminar: {str(e)}"
            )
```

---

## ⚠️ Excepciones

### Ejemplo 1: Lanzar Excepciones de Validación

```python
from src.utils.exceptions import ValidationError

def crear_profesor(nombre: str, email: str, horas: int):
    """Crea un profesor validando los datos."""
    if not nombre:
        raise ValidationError("El nombre del profesor es obligatorio")
    
    if not email:
        raise ValidationError("El email del profesor es obligatorio")
    
    if horas < 0:
        raise ValidationError("Las horas de contrato no pueden ser negativas")
    
    # Procesar...
```

### Ejemplo 2: Excepciones de Entidad No Encontrada

```python
from src.utils.exceptions import ProfesorNotFoundError, ZonaNotFoundError

def obtener_profesor(self, profesor_id: int):
    """Obtiene un profesor por ID."""
    profesor = self.session.query(Profesor).get(profesor_id)
    
    if not profesor:
        raise ProfesorNotFoundError(profesor_id=profesor_id)
    
    return profesor

def obtener_zona(self, zona_id: int):
    """Obtiene una zona por ID."""
    zona = self.session.query(Zona).get(zona_id)
    
    if not zona:
        raise ZonaNotFoundError(zona_id=zona_id)
    
    return zona
```

### Ejemplo 3: Excepciones de Conflicto

```python
from src.utils.exceptions import (
    MaxGuardiasExceededError,
    DuplicateGuardiaError
)

def asignar_guardia(self, profesor, fecha, turno, recreo, zona):
    """Asigna una guardia validando conflictos."""
    # Verificar máximo de guardias por día
    guardias_hoy = self.contar_guardias_profesor_fecha(profesor.id, fecha)
    if guardias_hoy >= MAX_GUARDIAS_POR_PROFESOR_DIA:
        raise MaxGuardiasExceededError(
            profesor_nombre=profesor.nombre,
            fecha=fecha.isoformat()
        )
    
    # Verificar duplicados
    guardia_existente = self.buscar_guardia(
        profesor.id, fecha, turno, recreo
    )
    if guardia_existente:
        raise DuplicateGuardiaError(
            profesor=profesor.nombre,
            fecha=fecha.isoformat(),
            turno=turno,
            recreo=recreo
        )
    
    # Crear guardia...
```

### Ejemplo 4: Manejo de Excepciones en UI

```python
from src.utils.exceptions import (
    ValidationError,
    ProfesorNotFoundError,
    DatabaseError,
    GuardiasBaseException
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

def guardar_profesor(self):
    """Guarda un profesor con manejo completo de errores."""
    try:
        # Obtener datos
        nombre = self.input_nombre.text()
        email = self.input_email.text()
        
        # Intentar guardar
        profesor = self.service.crear_profesor(nombre, email)
        
        # Éxito
        QMessageBox.information(self, "Éxito", "Profesor guardado")
        logger.info(f"Profesor guardado: {profesor.nombre}")
        
    except ValidationError as e:
        # Error de validación (no crítico)
        logger.warning(f"Validación fallida: {e}")
        QMessageBox.warning(
            self,
            "Error de Validación",
            str(e)
        )
    
    except ProfesorNotFoundError as e:
        # Profesor no encontrado (error de lógica)
        logger.error(f"Profesor no encontrado: {e.profesor_id}")
        QMessageBox.critical(
            self,
            "Error",
            f"El profesor con ID {e.profesor_id} no existe"
        )
    
    except DatabaseError as e:
        # Error de base de datos (crítico)
        logger.error(f"Error de BD: {e.detalles}", exc_info=True)
        QMessageBox.critical(
            self,
            "Error de Base de Datos",
            "No se pudo guardar el profesor. Contacte al administrador."
        )
    
    except GuardiasBaseException as e:
        # Otras excepciones del sistema
        logger.error(f"Error del sistema: {e}", exc_info=True)
        QMessageBox.critical(
            self,
            "Error",
            f"Error del sistema: {str(e)}"
        )
    
    except Exception as e:
        # Error inesperado (muy crítico)
        logger.critical(f"Error inesperado", exc_info=True)
        QMessageBox.critical(
            self,
            "Error Inesperado",
            f"Ocurrió un error inesperado: {str(e)}"
        )
```

### Ejemplo 5: Excepciones en Cálculos

```python
from src.utils.exceptions import InsufficientProfesoresError

def calcular_distribucion(self, profesores, zonas, config):
    """Calcula la distribución de guardias."""
    # Validar profesores suficientes
    if len(profesores) < MIN_PROFESORES_PARA_ASIGNACION:
        raise InsufficientProfesoresError(
            requeridos=MIN_PROFESORES_PARA_ASIGNACION,
            disponibles=len(profesores)
        )
    
    # Calcular slots
    slots_totales = config.dias_lectivos * len(zonas) * config.num_recreos
    
    # Validar capacidad
    suma_horas = sum(p.horas_contrato for p in profesores)
    if suma_horas == 0:
        raise InsufficientProfesoresError(
            requeridos=1,
            disponibles=0
        )
    
    # Calcular...
```

---

## 🔗 Patrones de Integración

### Patrón 1: Servicio Completo

```python
from src.utils.logger import get_logger, log_function_call
from src.utils.validators import validar_email, validar_nombre_completo
from src.utils.constants import MAX_HORAS_CONTRATO
from src.utils.exceptions import ValidationError, DatabaseError, ProfesorNotFoundError

logger = get_logger(__name__)

class ProfesorService:
    """
    Servicio completo integrando todas las utilidades.
    """
    
    def __init__(self, session):
        self.session = session
        logger.info("ProfesorService inicializado")
    
    @log_function_call(logger)
    def crear_profesor(self, nombre: str, email: str, horas: int) -> Profesor:
        """Crea un profesor validando todos los datos."""
        logger.info(f"Creando profesor: {nombre}")
        
        # 1. Validar nombre
        valido, error = validar_nombre_completo(nombre)
        if not valido:
            raise ValidationError(f"Nombre inválido: {error}")
        
        # 2. Validar email
        valido, error = validar_email(email)
        if not valido:
            raise ValidationError(f"Email inválido: {error}")
        
        # 3. Validar horas
        if horas > MAX_HORAS_CONTRATO:
            raise ValidationError(
                f"Las horas ({horas}) superan el máximo ({MAX_HORAS_CONTRATO})"
            )
        
        # 4. Crear profesor
        try:
            profesor = Profesor(nombre=nombre, email=email, horas_contrato=horas)
            self.session.add(profesor)
            self.session.commit()
            
            logger.info(f"✓ Profesor creado: ID={profesor.id}")
            return profesor
            
        except IntegrityError as e:
            logger.error("Error de integridad", exc_info=True)
            self.session.rollback()
            raise DatabaseError(
                "No se pudo crear el profesor (posible duplicado)",
                detalles=str(e)
            )
        
        except Exception as e:
            logger.critical("Error inesperado", exc_info=True)
            self.session.rollback()
            raise DatabaseError(
                "Error inesperado al crear profesor",
                detalles=str(e)
            )
    
    def obtener_profesor(self, profesor_id: int) -> Profesor:
        """Obtiene un profesor por ID."""
        profesor = self.session.query(Profesor).get(profesor_id)
        
        if not profesor:
            raise ProfesorNotFoundError(profesor_id=profesor_id)
        
        return profesor
```

### Patrón 2: Widget UI Completo

```python
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox
from src.utils.logger import get_logger
from src.utils.validators import validar_email, validar_nombre_completo, validar_horas_contrato
from src.utils.constants import (
    MAX_WIDTH_INPUT_LARGE,
    MAX_WIDTH_INPUT_MEDIUM,
    MSG_EXITO_GUARDADO,
    MSG_ERROR_TITULO
)
from src.utils.exceptions import ValidationError, DatabaseError

logger = get_logger(__name__)

class ProfesorForm(QWidget):
    """
    Formulario completo integrando todas las utilidades.
    """
    
    def __init__(self, service):
        super().__init__()
        self.service = service
        logger.info("ProfesorForm inicializado")
        self.init_ui()
    
    def init_ui(self):
        """Inicializa la interfaz con anchos consistentes."""
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # Nombre
        self.input_nombre = QLineEdit()
        self.input_nombre.setMaximumWidth(MAX_WIDTH_INPUT_LARGE)
        self.input_nombre.setPlaceholderText("APELLIDOS, NOMBRE")
        form.addRow("Nombre:", self.input_nombre)
        
        # Email
        self.input_email = QLineEdit()
        self.input_email.setMaximumWidth(MAX_WIDTH_INPUT_MEDIUM)
        self.input_email.setPlaceholderText("profesor@colegio.es")
        form.addRow("Email:", self.input_email)
        
        # Horas
        self.input_horas = QLineEdit()
        self.input_horas.setMaximumWidth(MAX_WIDTH_INPUT_SMALL)
        self.input_horas.setPlaceholderText("25")
        form.addRow("Horas:", self.input_horas)
        
        layout.addLayout(form)
        
        # Botón guardar
        self.btn_guardar = QPushButton("Guardar Profesor")
        self.btn_guardar.clicked.connect(self.guardar_profesor)
        layout.addWidget(self.btn_guardar)
        
        self.setLayout(layout)
    
    def guardar_profesor(self):
        """Guarda un profesor con validación y manejo de errores completo."""
        logger.info("Usuario solicitó guardar profesor")
        
        # Obtener datos
        nombre = self.input_nombre.text().strip()
        email = self.input_email.text().strip()
        horas_str = self.input_horas.text().strip()
        
        # Validar nombre
        valido, error = validar_nombre_completo(nombre)
        if not valido:
            logger.warning(f"Validación nombre fallida: {error}")
            QMessageBox.warning(self, MSG_ERROR_TITULO, error)
            self.input_nombre.setFocus()
            return
        
        # Validar email
        valido, error = validar_email(email)
        if not valido:
            logger.warning(f"Validación email fallida: {error}")
            QMessageBox.warning(self, MSG_ERROR_TITULO, error)
            self.input_email.setFocus()
            return
        
        # Validar horas
        try:
            horas = int(horas_str)
        except ValueError:
            QMessageBox.warning(
                self,
                MSG_ERROR_TITULO,
                "Las horas deben ser un número entero"
            )
            self.input_horas.setFocus()
            return
        
        valido, error = validar_horas_contrato(horas)
        if not valido:
            logger.warning(f"Validación horas fallida: {error}")
            QMessageBox.warning(self, MSG_ERROR_TITULO, error)
            self.input_horas.setFocus()
            return
        
        # Guardar
        try:
            profesor = self.service.crear_profesor(nombre, email, horas)
            
            logger.info(f"✓ Profesor guardado desde UI: {profesor.nombre}")
            QMessageBox.information(self, "Éxito", MSG_EXITO_GUARDADO)
            
            # Limpiar formulario
            self.limpiar_formulario()
            
        except ValidationError as e:
            logger.warning(f"Error de validación: {e}")
            QMessageBox.warning(self, MSG_ERROR_TITULO, str(e))
        
        except DatabaseError as e:
            logger.error(f"Error de BD: {e.detalles}", exc_info=True)
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                "Error al guardar en la base de datos"
            )
        
        except Exception as e:
            logger.critical("Error inesperado", exc_info=True)
            QMessageBox.critical(
                self,
                MSG_ERROR_TITULO,
                f"Error inesperado: {str(e)}"
            )
    
    def limpiar_formulario(self):
        """Limpia todos los campos del formulario."""
        self.input_nombre.clear()
        self.input_email.clear()
        self.input_horas.clear()
        self.input_nombre.setFocus()
```

---

## 🎯 Conclusión

Estos ejemplos demuestran cómo integrar el sistema de utilidades v2.2 en diferentes contextos:

✅ **Logging**: Trazabilidad completa de operaciones  
✅ **Validadores**: Datos consistentes y validados  
✅ **Constantes**: Código mantenible sin valores mágicos  
✅ **Excepciones**: Manejo de errores profesional  

Para más información, consulta:
- [REFACTORIZACION_v2.2.md](REFACTORIZACION_v2.2.md) - Documentación técnica completa
- [GUIA_DESARROLLO.md](GUIA_DESARROLLO.md) - Guía de desarrollo
- [RESUMEN_v2.2.1.md](RESUMEN_v2.2.1.md) - Resumen ejecutivo

---

**Versión**: 2.2  
**Última actualización**: Enero 2025
