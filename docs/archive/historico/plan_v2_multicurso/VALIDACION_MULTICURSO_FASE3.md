# Validación Multicurso - FASE 3
## Checklist de Funcionalidad Post-Refactorización

**Fecha:** 12 de noviembre de 2025  
**Objetivo:** Verificar que las funcionalidades principales funcionan correctamente con el sistema multicurso

---

## ✅ Tests Completados (FASE 1-2)

- [x] Test 1: Tabla Gestión de Cursos (11 columnas)
- [x] Test 2: CRUD operations (crear/activar/cerrar/eliminar curso)
- [x] Test 3: Course switching (calendario vacío vs lleno)
- [x] Test 4: Selector muestra curso activo con ⭐
- [x] Test 5: Ausencias filtran por curso_activo
- [x] Test 6: Asignación filtra por curso_activo
- [x] Test 7: Asignador asigna curso_id correctamente
- [x] Test 8: PDF Exporter filtra por curso_activo
- [x] Bug crítico: Configuracion.curso_id eliminado

---

## 🧪 FASE 3: Tests de Regresión

### Test 9: Gestión de Profesores
**Objetivo:** Verificar CRUD de profesores funciona correctamente

#### Pasos:
1. Ir a GESTIÓN → Profesores
2. Ver lista de profesores existentes
3. Crear nuevo profesor:
   - Nombre: TEST MULTICURSO
   - Email: test@colegio.edu
   - Horas: 30.0h
   - Turno: Mañana
   - Es tutor: No
4. Verificar que aparece en la lista
5. Editar el profesor (cambiar turno a "Tarde")
6. Eliminar el profesor de prueba

**Resultado esperado:**
- ✅ Lista carga correctamente
- ✅ Crear funciona
- ✅ Editar funciona
- ✅ Eliminar funciona
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌ 
- Notas: _____________________

---

### Test 10: Gestión de Zonas
**Objetivo:** Verificar CRUD de zonas funciona correctamente

#### Pasos:
1. Ir a GESTIÓN → Zonas
2. Ver lista de zonas existentes (debería haber 4)
3. Crear nueva zona:
   - Nombre: ZONA TEST MULTICURSO
4. Verificar que aparece en la lista
5. Editar la zona (cambiar nombre)
6. Eliminar la zona de prueba

**Resultado esperado:**
- ✅ Lista carga correctamente
- ✅ Crear funciona
- ✅ Editar funciona
- ✅ Eliminar funciona
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 11: Vista Calendario - Navegación
**Objetivo:** Verificar que el calendario se navega correctamente

#### Pasos:
1. Ir a GUARDIAS → Calendario
2. Verificar que muestra el mes actual
3. Navegar a mes anterior (←)
4. Navegar a mes siguiente (→)
5. Hacer clic en "Hoy" para volver
6. Cambiar a vista semana
7. Cambiar a vista día

**Resultado esperado:**
- ✅ Calendario carga con guardias del curso activo
- ✅ Navegación entre meses funciona
- ✅ Botón "Hoy" funciona
- ✅ Cambio de vista funciona
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 12: Gestión de Ausencias - CRUD
**Objetivo:** Verificar que las ausencias se gestionan correctamente

#### Pasos:
1. Ir a PERSONAL → Ausencias
2. Seleccionar un profesor de la lista
3. Crear nueva ausencia:
   - Fecha inicio: Mañana
   - Fecha fin: En 3 días
   - Tipo: Permiso
4. Verificar que aparece en la lista
5. Editar la ausencia (cambiar tipo a "Baja médica")
6. Eliminar la ausencia de prueba

**Resultado esperado:**
- ✅ Lista de profesores carga (solo del curso activo)
- ✅ Crear ausencia funciona
- ✅ Editar funciona
- ✅ Eliminar funciona
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 13: Asignación de Guardias - Vista Estadísticas
**Objetivo:** Verificar que las estadísticas se calculan correctamente

#### Pasos:
1. Ir a GUARDIAS → Asignación
2. Esperar a que carguen las estadísticas
3. Verificar columnas:
   - Profesor
   - Asignadas
   - Ideales
   - Diferencia
   - % Equidad
4. Verificar que los números tienen sentido
5. Verificar que solo muestra profesores del curso activo

**Resultado esperado:**
- ✅ Estadísticas cargan correctamente
- ✅ Números son coherentes
- ✅ Solo profesores del curso activo
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 14: Exportar PDF Individual
**Objetivo:** Verificar que la exportación PDF funciona

#### Pasos:
1. Ir a GUARDIAS → Calendario
2. Hacer clic derecho en un profesor con guardias
3. Seleccionar "Exportar PDF individual"
4. Elegir directorio de destino
5. Abrir el PDF generado
6. Verificar que solo muestra guardias del curso activo

**Resultado esperado:**
- ✅ Diálogo de exportación aparece
- ✅ PDF se genera sin errores
- ✅ PDF contiene solo guardias del curso activo
- ✅ Formato correcto (fechas, zonas, recreos)
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 15: Configuración de Horarios
**Objetivo:** Verificar que la configuración sigue funcionando

#### Pasos:
1. Ir a GESTIÓN → Ajustes
2. Verificar que los campos cargan:
   - Fecha inicio/fin curso
   - Horas de recreos
   - Ajustes de tutores
   - Algoritmo de asignación
3. NO modificar nada, solo verificar lectura

**Resultado esperado:**
- ✅ Configuración carga correctamente
- ✅ Todos los campos tienen valores
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

### Test 16: Generar Guardias para Nuevo Curso
**Objetivo:** Verificar que se pueden generar guardias para un curso vacío

#### Pasos:
1. Ir a GESTIÓN → Gestión de Cursos
2. Crear nuevo curso: "2026/2027"
3. Activar el curso "2026/2027"
4. Ir a GUARDIAS → Asignación
5. Hacer clic en "Generar Guardias"
6. Configurar:
   - Fecha inicio: 08/09/2026
   - Fecha fin: 12/06/2027
7. Confirmar generación
8. Esperar a que complete
9. Verificar estadísticas

**Resultado esperado:**
- ✅ Generación inicia sin errores
- ✅ Barra de progreso funciona
- ✅ Se crean guardias para el curso 2026/2027
- ✅ Estadísticas muestran las nuevas guardias
- ✅ Sin errores en consola

**Resultado real:**
- [ ] ✅ / ❌
- Notas: _____________________

---

## 🐛 Bugs Conocidos (Para Fix Posterior)

### Bug #7: Auto-refresh no funciona
**Descripción:** Al cambiar de curso con el selector, las vistas no se refrescan automáticamente.

**Workaround:** Cerrar y reabrir la aplicación después de cambiar de curso.

**Prioridad:** Media (funcionalidad core funciona, solo UX afectado)

**Status:** Pendiente de debug detallado

---

## 📊 Resultados Globales

**Tests Fase 3:**
- Total tests: 8 (Test 9-16)
- Pasados: ___ / 8
- Fallados: ___ / 8
- Bloqueados: ___ / 8

**Bugs Críticos Encontrados:**
- Ninguno hasta ahora ✅

**Bugs Menores Encontrados:**
- Bug #7: Auto-refresh (ya documentado)

---

## 📝 Conclusiones

[Completar después de ejecutar todos los tests]

**Funcionalidades Core:**
- [ ] ✅ Sistema multicurso funciona correctamente
- [ ] ✅ Filtrado por curso_activo opera bien
- [ ] ✅ CRUD operations funcionan
- [ ] ✅ Generador de guardias funciona

**Próximos Pasos:**
1. [ ] Fix Bug #7 (auto-refresh)
2. [ ] Escribir tests automatizados (pytest)
3. [ ] Actualizar documentación de usuario
4. [ ] Validación final con datos reales

---

**Responsable:** Carlos Ferrero Bonet  
**Última actualización:** 12/11/2025
