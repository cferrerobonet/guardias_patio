---
paths:
  - "src/services/asignador_guardias_cpsat.py"
  - "src/services/_asignador_cpsat_helpers.py"
  - "src/services/reparto_agrupado.py"
  - "src/services/distribucion_cuotas_service.py"
  - "src/application/use_cases/asignacion_guardias/**"
  - "tests/test_reparto_parametros.py"
---

# Criterios del reparto de guardias (fijados por CarlosFB, 2026-10-03)

1. **Equidad primero**: nunca se cambia una guardia de diferencia con la cuota por agrupar mejor.
2. **Agrupación**: las guardias de cada profesor en tramos de días seguidos, en la misma zona y el mismo recreo (1º o 2º): «carriles» (recreo × zona) en `reparto_agrupado.py` más objetivo de CP-SAT.
3. **Fechas de inicio/fin**: el profesor hace la cuota del curso entero concentrada en su periodo (no proporcional); si no le cabe (1 guardia/día), el sobrante lo reparten los de su turno.
4. **Ningún parámetro configurable queda fuera del algoritmo**: `tests/test_reparto_parametros.py` obliga a clasificar cada columna nueva de Profesor, Zona, Configuración y Ausencia (CP-SAT llegó a ignorar `Zona.activa` y `dias_semana_permitidos`).

- Un cambio en cuotas o generación se valida con el verificador de reglas y de dispersión sobre volcados reales, en memoria, nunca contra la base real.
- Decidido: los mixtos se ajustan a mano en la rejilla de recreos (sus horas no reparten turnos); `Zona.capacidad_profesores` no existe; el algoritmo «Rápido» está retirado: siempre CP-SAT con cobertura blanda.
