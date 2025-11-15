# API REST - Guardias de Patio

API REST desarrollada con FastAPI para exponer la funcionalidad del sistema de Guardias de Patio.

## 🚀 Inicio Rápido

### Instalación de dependencias

```bash
pip install fastapi uvicorn[standard]
```

### Ejecutar la API

```bash
# Opción 1: Script automático
./scripts/run_api.sh

# Opción 2: Comando directo
cd src
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

La API estará disponible en `http://localhost:8000`

## 📚 Documentación Interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 Endpoints Disponibles

### 1. Cuotas (`/api/cuotas`)

#### `GET /api/cuotas`
Calcula las cuotas de guardias para todos los profesores.

**Parámetros:**
- `configuracion_id` (int, required): ID de la configuración del curso
- `solo_activos` (bool, optional): Solo profesores activos (default: true)

**Ejemplo:**
```bash
curl "http://localhost:8000/api/cuotas?configuracion_id=1&solo_activos=true"
```

**Respuesta:**
```json
{
  "exitoso": true,
  "cuotas": {
    "1": 45,
    "2": 38,
    "3": 42
  },
  "cuotas_detalle": [
    {
      "profesor_id": 1,
      "profesor_nombre": "García López, María",
      "cuota_esperada": 45,
      "cuota_asignada": 44
    }
  ],
  "total_guardias": 360,
  "mensaje": "Cuotas calculadas correctamente para 8 profesores"
}
```

---

### 2. Equidad (`/api/equidad`)

#### `GET /api/equidad`
Analiza la equidad en la distribución de guardias.

**Parámetros:**
- `configuracion_id` (int, required): ID de la configuración del curso
- `umbral_desbalance` (float, optional): Umbral para detectar desbalances (default: 0.15)
- `incluir_cuotas_detalle` (bool, optional): Incluir detalle de cuotas (default: false)

**Ejemplo:**
```bash
curl "http://localhost:8000/api/equidad?configuracion_id=1&umbral_desbalance=0.15&incluir_cuotas_detalle=true"
```

**Respuesta:**
```json
{
  "exitoso": true,
  "metricas": {
    "indice_equidad": 0.92,
    "coeficiente_variacion": 0.08,
    "desviacion_estandar": 3.2,
    "desbalances_detectados": 2,
    "profesores_con_deficit": 1,
    "profesores_con_exceso": 1
  },
  "cuotas": [
    {
      "profesor_id": 1,
      "profesor_nombre": "García López, María",
      "cuota_esperada": 45,
      "cuota_asignada": 44
    }
  ],
  "recomendaciones": [
    "Revisar asignación del profesor García (exceso: +5 guardias)"
  ],
  "mensaje": "Análisis completado"
}
```

---

### 3. Guardias (`/api/guardias`)

#### `GET /api/guardias`
Obtiene guardias con filtros opcionales.

**Parámetros:**
- `configuracion_id` (int, required): ID de la configuración del curso
- `fecha_inicio` (date, optional): Filtrar desde fecha
- `fecha_fin` (date, optional): Filtrar hasta fecha
- `profesor_id` (int, optional): Filtrar por profesor
- `zona_id` (int, optional): Filtrar por zona
- `turno` (str, optional): Filtrar por turno ("mañana" o "tarde")
- `limit` (int, optional): Máximo de resultados (default: 100, max: 1000)
- `offset` (int, optional): Desplazamiento para paginación (default: 0)

**Ejemplo:**
```bash
curl "http://localhost:8000/api/guardias?configuracion_id=1&turno=mañana&limit=10"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "fecha": "2024-09-02",
    "recreo": 1,
    "turno": "mañana",
    "zona_id": 1,
    "zona_nombre": "Patio Principal",
    "profesor_id": 3,
    "profesor_nombre": "Martínez Ruiz, Juan",
    "curso_id": 1
  }
]
```

#### `GET /api/guardias/count`
Cuenta guardias con filtros opcionales.

**Parámetros:** (mismos que GET /api/guardias excepto limit y offset)

**Ejemplo:**
```bash
curl "http://localhost:8000/api/guardias/count?configuracion_id=1&turno=tarde"
```

**Respuesta:**
```json
{
  "total": 180
}
```

---

### 4. Profesores (`/api/profesores`)

#### `GET /api/profesores`
Lista todos los profesores con filtros opcionales.

**Parámetros:**
- `activo` (bool, optional): Filtrar por estado activo
- `turno` (str, optional): Filtrar por turno

**Ejemplo:**
```bash
curl "http://localhost:8000/api/profesores?activo=true&turno=mañana"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre_completo": "García López, María",
    "horas_contrato": 25,
    "porcentaje_jornada": 100,
    "turno": "mañana",
    "activo": true,
    "email": "maria.garcia@colegio.com"
  }
]
```

#### `GET /api/profesores/{profesor_id}`
Obtiene un profesor por ID.

**Ejemplo:**
```bash
curl "http://localhost:8000/api/profesores/1"
```

---

### 5. Estadísticas (`/api/estadisticas`)

#### `GET /api/estadisticas/resumen`
Obtiene un resumen estadístico de guardias.

**Parámetros:**
- `configuracion_id` (int, required): ID de la configuración del curso
- `fecha_inicio` (date, optional): Filtrar desde fecha
- `fecha_fin` (date, optional): Filtrar hasta fecha

**Ejemplo:**
```bash
curl "http://localhost:8000/api/estadisticas/resumen?configuracion_id=1"
```

**Respuesta:**
```json
{
  "total_guardias": 360,
  "asignadas": 355,
  "sin_asignar": 5,
  "cobertura_porcentaje": 98.6,
  "por_turno": {
    "mañana": 180,
    "tarde": 180
  },
  "top_profesor": {
    "id": 3,
    "nombre": "Martínez Ruiz, Juan",
    "total_guardias": 48
  }
}
```

#### `GET /api/estadisticas/por-profesor`
Obtiene estadísticas de guardias por profesor.

**Parámetros:**
- `configuracion_id` (int, required): ID de la configuración del curso

**Ejemplo:**
```bash
curl "http://localhost:8000/api/estadisticas/por-profesor?configuracion_id=1"
```

**Respuesta:**
```json
{
  "profesores": [
    {
      "id": 3,
      "nombre": "Martínez Ruiz, Juan",
      "total_guardias": 48
    },
    {
      "id": 1,
      "nombre": "García López, María",
      "total_guardias": 45
    }
  ],
  "total_profesores": 8
}
```

---

## 🏗️ Arquitectura

### Estructura de Directorios

```
src/api/
├── __init__.py
├── main.py              # Aplicación FastAPI principal
├── dependencies.py      # Dependency injection (sesión DB)
└── routers/
    ├── __init__.py
    ├── cuotas.py       # Endpoints de cuotas
    ├── equidad.py      # Endpoints de equidad
    ├── guardias.py     # Endpoints de guardias
    ├── profesores.py   # Endpoints de profesores
    └── estadisticas.py # Endpoints de estadísticas
```

### Características Clave

1. **Reutilización de Use Cases**: La API reutiliza directamente los Use Cases de la capa de aplicación, sin duplicar lógica de negocio.

2. **Dependency Injection**: Gestión automática de sesiones de base de datos mediante `Depends(get_db)`.

3. **Documentación Automática**: Swagger UI y ReDoc generados automáticamente a partir de docstrings y type hints.

4. **Validación con Pydantic**: Validación automática de requests y responses mediante Pydantic models.

5. **CORS Habilitado**: Configurado para permitir requests desde cualquier origen (ajustar en producción).

6. **DTOs Serializables**: Los DTOs de domain services se convierten automáticamente a JSON mediante `dataclasses.asdict()`.

---

## 🔒 Seguridad

**Nota**: Esta API actual **NO tiene autenticación**. Para producción, considerar:

1. **OAuth2/JWT**: Implementar autenticación con tokens JWT
2. **Rate Limiting**: Limitar requests por IP/usuario
3. **HTTPS**: Usar siempre HTTPS en producción
4. **CORS**: Restringir orígenes permitidos
5. **API Keys**: Requerir API key para acceso

---

## 🧪 Testing

Ejemplo de test con `httpx`:

```python
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_obtener_cuotas():
    response = client.get("/api/cuotas?configuracion_id=1")
    assert response.status_code == 200
    assert "cuotas" in response.json()
```

---

## 📦 Deployment

### Producción con Gunicorn + Uvicorn

```bash
pip install gunicorn
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ .
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🔗 Integración con Frontend

### JavaScript/TypeScript

```typescript
// fetch API
const response = await fetch('http://localhost:8000/api/cuotas?configuracion_id=1');
const data = await response.json();

// axios
import axios from 'axios';
const { data } = await axios.get('http://localhost:8000/api/equidad', {
  params: { configuracion_id: 1, umbral_desbalance: 0.15 }
});
```

### Python

```python
import requests

response = requests.get(
    'http://localhost:8000/api/estadisticas/resumen',
    params={'configuracion_id': 1}
)
data = response.json()
```

---

## 📊 Beneficios

1. **Separación de Concerns**: UI (PyQt6) y API REST independientes
2. **Reutilización de Lógica**: Use Cases compartidos entre UI y API
3. **Escalabilidad**: API puede escalar independientemente de la UI
4. **Integraciones**: Fácil integración con apps móviles, dashboards externos, etc.
5. **Testing**: Endpoints HTTP más fáciles de testear que UI
6. **Documentación Automática**: Swagger/ReDoc sin esfuerzo adicional

---

## 📝 Licencia

Mismo que el proyecto principal.
