# API Técnica — Guardias de Patio

Versión: **5.17.0** · Base URL: `http://localhost:8000`  
Autenticación: Bearer JWT (OAuth2 password flow)

---

## Autenticación

### `POST /api/v1/auth/token`

Obtiene un token JWT.

**Request** (`application/x-www-form-urlencoded`)

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `username` | string | ✓ | Nombre de usuario |
| `password` | string | ✓ | Contraseña |

**Response 200**
```json
{ "access_token": "<jwt>", "token_type": "bearer" }
```

---

## Profesores

### `GET /api/v1/profesores`

Lista profesores con paginación.

**Query params**

| Param | Tipo | Default | Descripción |
|-------|------|---------|-------------|
| `activo` | bool | — | Filtrar por estado activo |
| `turno` | string | — | `mañana` \| `tarde` \| `mixto` |
| `offset` | int | 0 | Desplazamiento paginación |
| `limit` | int | 50 | Máx. resultados |

**Response 200** → `PaginatedProfesoresResponse`
```json
{ "items": [...], "total": 12, "offset": 0, "limit": 50 }
```

Cada ítem → `ProfesorResponse`: `id`, `nombre_completo`, `horas_contrato`, `porcentaje_jornada`, `turno`, `activo`, `email`

---

### `POST /api/v1/profesores`

Crea un nuevo profesor.

**Body JSON** — `CrearProfesorDTO`

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre_completo` | string (3–200) | ✓ | Nombre y apellidos |
| `horas_contrato` | float (1–40) | ✓ | Horas semanales de contrato |
| `turno` | string | ✓ | `mañana` \| `tarde` \| `mixto` |
| `email_corporativo` | string | — | Email institucional |
| `horas_manana` | float | — | Horas en turno de mañana (turno mixto) |
| `horas_tarde` | float | — | Horas en turno de tarde (turno mixto) |
| `tutor` | bool | — | Es tutor de grupo (default: false) |
| `fecha_inicio_guardias` | date | — | Inicio período de guardias |
| `fecha_fin_guardias` | date | — | Fin período de guardias |
| `zona_preferida_id` | int | — | ID de zona preferida |
| `dias_semana_permitidos` | list[int] | — | Días (0=Lun … 4=Vie), default [0,1,2,3,4] |
| `recreos_permitidos` | list[int] \| dict | — | Recreos (1–4) o dict por día |

**Response 201** → `ProfesorResponse`

**Errores**
- `422` — Validación (turno inválido, horas fuera de rango, nombre duplicado)

---

### `GET /api/v1/profesores/{profesor_id}`

Obtiene un profesor por ID.

**Response 200** → `ProfesorResponse`  
**Response 404** — Profesor no encontrado

---

### `PUT /api/v1/profesores/{profesor_id}`

Actualiza un profesor. Todos los campos son opcionales (`ActualizarProfesorDTO`).  
Mismos campos que `CrearProfesorDTO` pero ninguno requerido.

**Response 200** → `ProfesorResponse`  
**Response 404** — Profesor no encontrado

---

### `DELETE /api/v1/profesores/{profesor_id}`

Elimina un profesor.

**Response 200** → `{ "message": "Profesor eliminado" }`  
**Response 404** — Profesor no encontrado

---

## Zonas

### `GET /api/v1/zonas`

Lista todas las zonas de guardia.

**Response 200** → `list[ZonaResponse]`  
Cada ítem: `id`, `nombre_zona`, `descripcion`

---

### `POST /api/v1/zonas`

Crea una zona.

**Body JSON** — `CrearZonaDTO`

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre_zona` | string (2–100) | ✓ | Nombre de la zona |
| `descripcion` | string (máx 500) | — | Descripción |
| `fecha_inicio` | date | — | Inicio vigencia |
| `fecha_fin` | date | — | Fin vigencia |

**Response 201** → `ZonaResponse`  
**Errores** — `409` si el nombre ya existe

---

### `GET /api/v1/zonas/{zona_id}`

Obtiene una zona por ID.

**Response 200** → `ZonaResponse`  
**Response 404** — Zona no encontrada

---

### `PUT /api/v1/zonas/{zona_id}`

Actualiza una zona. Todos los campos opcionales (`ActualizarZonaDTO`).

**Response 200** → `ZonaResponse`

---

### `DELETE /api/v1/zonas/{zona_id}`

Elimina una zona.

**Response 200** → `{ "message": "Zona eliminada" }`

---

## Guardias

El parámetro `configuracion_id` corresponde al ID del `CursoEscolar` activo.

### `GET /api/v1/guardias`

Lista guardias con filtros y paginación.

**Query params**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `configuracion_id` | int | ✓ | ID del curso escolar |
| `fecha_inicio` | date | — | Filtro fecha inicio |
| `fecha_fin` | date | — | Filtro fecha fin |
| `profesor_id` | int | — | Filtrar por profesor |
| `zona_id` | int | — | Filtrar por zona |
| `turno` | string | — | `mañana` \| `tarde` \| `mixto` |
| `limit` | int | 100 | Máx. resultados (≤1000) |
| `offset` | int | 0 | Desplazamiento |

**Response 200** → `PaginatedGuardiasResponse`
```json
{ "items": [...], "total": 42, "offset": 0, "limit": 100 }
```

Cada ítem → `GuardiaResponse`: `id`, `fecha`, `recreo`, `turno`, `zona_id`, `zona_nombre`, `profesor_id`, `profesor_nombre`, `es_sustitucion`

---

### `POST /api/v1/guardias`

Asigna una guardia manualmente.

**Body JSON** — `CrearGuardiaDTO`

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `fecha` | date | ✓ | Fecha de la guardia |
| `turno` | string | ✓ | `mañana` \| `tarde` |
| `numero_recreo` | int | ✓ | Número de recreo (1–4) |
| `profesor_id` | int | ✓ | ID del profesor asignado |
| `zona_id` | int | ✓ | ID de la zona |
| `es_sustitucion` | bool | — | Es sustitución (default: false) |
| `profesor_sustituido_id` | int | — | ID del profesor sustituido |

**Response 201** → `GuardiaResponse`

---

### `GET /api/v1/guardias/count`

Cuenta guardias con los mismos filtros que `GET /api/v1/guardias` (sin paginación).

**Response 200** → `GuardiasCountResponse`: `{ "total": 42, "asignadas": 38, "sin_asignar": 4 }`

---

### `GET /api/v1/guardias/export/csv`

Exporta guardias a CSV. Acepta los mismos filtros que `GET /api/v1/guardias`.

**Response 200** — `text/csv` con cabecera `Content-Disposition: attachment`

---

### `GET /api/v1/guardias/export/xlsx`

Exporta guardias a Excel. Acepta los mismos filtros que `GET /api/v1/guardias`.

**Response 200** — `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

---

### `DELETE /api/v1/guardias`

Elimina **todas** las guardias (operación destructiva, sin filtros).

**Response 200** → `{ "message": "Guardias eliminadas", "count": 42 }`

---

## Estadísticas

### `GET /api/v1/estadisticas/resumen`

Resumen estadístico global.

**Query params**: `configuracion_id`* · `fecha_inicio` · `fecha_fin`

**Response 200** → `ResumenEstadisticasResponse`
```json
{
  "total_guardias": 200,
  "asignadas": 185,
  "sin_asignar": 15,
  "cobertura_porcentaje": 92.5,
  "por_turno": { "mañana": 120, "tarde": 65 },
  "top_profesor": { "id": 3, "nombre": "Ana García", "total": 22 }
}
```

---

### `GET /api/v1/estadisticas/por-profesor`

Estadísticas desglosadas por profesor.

**Query params**: `configuracion_id`*

**Response 200** → `EstadisticasPorProfesorResponse`
```json
{
  "profesores": [
    { "profesor_id": 1, "nombre": "...", "total_guardias": 18, "turno": "mañana" }
  ]
}
```

---

## Equidad

### `GET /api/v1/equidad`

Análisis de equidad en la distribución de guardias.

**Query params**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `configuracion_id` | int | ✓ | ID del curso escolar |
| `umbral_desbalance` | float | — | Umbral de desbalance (default: 0.2) |
| `incluir_cuotas_detalle` | bool | — | Incluir detalle de cuotas (default: false) |

**Response 200** → `AnalisisEquidadApiResponse`
```json
{
  "exitoso": true,
  "metricas": { "desviacion_estandar": 1.4, "coeficiente_variacion": 0.12 },
  "cuotas": { "1": 18, "2": 20 },
  "recomendaciones": ["Profesor X tiene exceso de guardias"],
  "mensaje": "Distribución equilibrada"
}
```

---

## Cuotas

### `GET /api/v1/cuotas`

Calcula la cuota de guardias esperada por profesor.

**Query params**

| Param | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `configuracion_id` | int | ✓ | ID del curso escolar |
| `solo_activos` | bool | — | Solo profesores activos (default: true) |

**Response 200** → `CalcularCuotasApiResponse`
```json
{
  "exitoso": true,
  "cuotas": { "1": 18.5, "2": 20.0 },
  "cuotas_detalle": [...],
  "total_guardias": 200,
  "mensaje": "Cuotas calculadas correctamente"
}
```

---

## Sistema

### `GET /`

Información básica de la API.

**Response 200**
```json
{ "name": "Guardias de Patio API", "version": "5.17.0", "status": "running" }
```

### `GET /health`

Estado del sistema.

**Response 200**
```json
{ "status": "healthy", "database": "connected", "version": "5.17.0" }
```

---

## Códigos de error comunes

| Código | Descripción |
|--------|-------------|
| `400` | Petición inválida (lógica de negocio) |
| `401` | No autenticado |
| `404` | Recurso no encontrado |
| `409` | Conflicto (duplicado) |
| `422` | Error de validación Pydantic |
| `500` | Error interno del servidor |

Estructura de error:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Descripción del error",
    "details": { "errors": [...] }
  }
}
```
