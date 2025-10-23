# ✅ Checklist de fin de iteración / entrega

**Proyecto:** {{nombre_proyecto}}  
**Versión / Iteración:** {{vX.Y.Z o sprint N}}  
**Fecha:** {{dd/mm/aaaa}}  
**Responsable:** {{nombre}}

---

## 🧩 1. Arquitectura y diseño
- [ ] La estructura respeta el modelo previsto (hexagonal, capas, MVC, etc.).
- [ ] No existen dependencias circulares ni imports entre capas indebidas.
- [ ] Los **ADRs** están actualizados con las decisiones recientes.
- [ ] El diagrama de arquitectura refleja la estructura actual del proyecto.
- [ ] Las responsabilidades de cada módulo son claras y acotadas.

**Prompt Copilot**
> “Revisa la estructura actual del proyecto y dime si respeta el modelo hexagonal previsto. Señala dependencias cruzadas indebidas o violaciones de capa.”

---

## 🧱 2. Lógica de dominio
- [ ] La lógica de negocio está aislada de la infraestructura.
- [ ] Las entidades y value objects son coherentes y autoexplicativos.
- [ ] No hay duplicación de reglas de negocio.
- [ ] Los nombres de clases y funciones expresan claramente su intención.

**Prompt Copilot**
> “Analiza el módulo `domain/` y detecta lógica de infraestructura mezclada. Sugiere cómo aislarla.”

---

## ⚙️ 3. Base de datos y migraciones
- [ ] `alembic current` = `head` (sin migraciones pendientes).
- [ ] Las migraciones son reversibles y probadas (`upgrade → downgrade → upgrade`).
- [ ] Se han validado índices, constraints y claves foráneas.
- [ ] No hay `ALTER COLUMN` peligrosos para SQLite.
- [ ] Las migraciones tienen mensajes descriptivos.

**Prompt Copilot**
> “Verifica el estado de las migraciones Alembic y señala cambios inseguros o no reversibles.”

---

## 🧪 4. Tests y verificación
- [ ] Todos los tests pasan en limpio (`pytest -q` o `make test`).
- [ ] Se cubren casos felices, de borde y de error.
- [ ] Cobertura ≥ {{objetivo%}} en módulos críticos.
- [ ] Fixtures y datos semilla están actualizados.

**Prompt Copilot**
> “Enumera rutas del código no cubiertas por tests y genera casos mínimos de validación.”

---

## 🧼 5. Refactor y legibilidad
- [ ] No hay duplicación de código ni funciones demasiado largas.
- [ ] Se siguen los principios DRY / KISS / SOLID.
- [ ] `ruff`, `black` y `mypy` pasan sin errores ni warnings.
- [ ] No quedan `print()` ni `TODO` sin resolver.

**Prompt Copilot**
> “Detecta code smells y propone un plan de refactor atómico sin alterar comportamiento.”

---

## ⚡ 6. Rendimiento y eficiencia
- [ ] Se han medido tiempos o cuellos de botella (no suposiciones).
- [ ] Consultas e iteraciones son eficientes.
- [ ] Cachés o lazy loading aplicados donde aportan valor.
- [ ] El código puede escalar (10× datos/usuarios) sin rediseño mayor.

**Prompt Copilot**
> “Analiza el rendimiento de las funciones críticas y propone optimizaciones simples.”

---

## 🔒 7. Seguridad y robustez
- [ ] Entradas de usuario validadas / saneadas.
- [ ] No hay secretos hardcodeados (uso de `.env` o gestor seguro).
- [ ] Excepciones bien gestionadas (sin `except Exception` genérico).
- [ ] Dependencias auditadas (sin CVEs críticos).

**Prompt Copilot**
> “Haz un pase OWASP básico: entradas, auth, errores, dependencias y secretos.”

---

## 🧭 8. Configuración y despliegue
- [ ] El entorno se levanta con un único comando (`make setup` o `poetry install`).
- [ ] Las variables de entorno están documentadas en `.env.example`.
- [ ] `make clean` o script de limpieza deja el repo limpio.
- [ ] El flujo `init-db → migrate → seed → test` funciona de principio a fin.

**Prompt Copilot**
> “Simula un clon limpio del repo y genera pasos automáticos para instalar y ejecutar tests.”

---

## 🧾 9. Documentación y comunicación
- [ ] README actualizado (propósito, uso, dependencias, comandos).
- [ ] Changelog actualizado con cambios relevantes.
- [ ] ADRs actualizados con nuevas decisiones.
- [ ] Diagrama ASCII o imagen de arquitectura revisada.

**Prompt Copilot**
> “Genera un README actualizado con propósito, estructura, comandos principales y dependencias.”

---

## 🧠 10. Evaluación final
- [ ] Cumple los objetivos funcionales del sprint/versión.
- [ ] Puede ser mantenido o extendido por otra persona sin ayuda.
- [ ] Hay métricas de éxito (tests, rendimiento, seguridad, legibilidad).
- [ ] Pendientes o mejoras registradas en el backlog.

**Prompt Copilot**
> “Evalúa el estado general del proyecto como revisor externo y devuelve:  
> - puntos fuertes,  
> - riesgos críticos,  
> - tareas sugeridas para la próxima iteración.”

---

## 📝 Conclusión
**Resumen de estado:**  
✅ Listo para liberar / 🚧 Requiere mejoras

**Observaciones finales:**