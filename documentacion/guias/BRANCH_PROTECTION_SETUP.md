# 🛡️ Configuración de Branch Protection (GitHub)

> **Versión**: 1.0  
> **Última actualización**: 8 de noviembre de 2025  
> **Audiencia**: Repository Admin / Maintainers

---

## 📋 Tabla de Contenidos

- [Resumen](#resumen)
- [Configuración Recomendada](#configuración-recomendada)
- [Instrucciones de Aplicación](#instrucciones-de-aplicación)
- [Verificar Configuración](#verificar-configuración)
- [Bypass y Excepciones](#bypass-y-excepciones)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Resumen

**Branch Protection Rules** protegen la rama `main` de cambios accidentales o no revisados, asegurando que:

- ✅ Todo código pasa por **Pull Request**
- ✅ Todo PR es **revisado y aprobado**
- ✅ Todo PR pasa **tests y checks automáticos**
- ✅ No hay **force pushes** ni **eliminaciones**

**Resultado**: Código de mayor calidad y menos bugs en producción.

---

## ⚙️ Configuración Recomendada

### Rama Protegida: `main`

```yaml
# GitHub Settings → Branches → Branch protection rules

Branch name pattern: main

# ✅ Require a pull request before merging
require_pull_request_before_merging: true
  required_approving_review_count: 1
  dismiss_stale_reviews: true
  require_code_owner_reviews: false
  require_last_push_approval: false

# ✅ Require status checks to pass before merging
require_status_checks_before_merging: true
  strict: true  # Require branches to be up to date before merging
  
  # Status checks that must pass:
  required_status_checks:
    - "test (ubuntu-latest, 3.11)"  # ⚠️ Crítico
    - "test (macos-latest, 3.11)"   # ⚠️ Crítico
    - "lint"                         # ⚠️ Crítico
    # Nota: security y mypy son informativos (no bloquean)

# ✅ Require conversation resolution before merging
require_conversation_resolution: true

# ✅ Require linear history
require_linear_history: true

# ✅ Do not allow bypassing the above settings
allow_bypass: false  # Solo admin puede bypass

# ✅ Restrict pushes
restrict_pushes: true
  allowed_actors: []  # Nadie puede hacer push directo

# ✅ Additional protections
allow_force_pushes: false
allow_deletions: false
```

---

## 📖 Instrucciones de Aplicación

### Paso 1: Acceder a Configuración

1. Ve a tu repositorio en GitHub
2. Click en **Settings** (⚙️)
3. En el menú lateral, click en **Branches**
4. Click en **Add branch protection rule**

### Paso 2: Configurar Regla

#### A. Branch Name Pattern

```
Branch name pattern: main
```

#### B. Protect Matching Branches

**Activar estas opciones**:

##### 1. Require a pull request before merging

- ✅ **Activar** checkbox principal
- **Required number of approvals**: `1`
- ✅ **Dismiss stale pull request approvals when new commits are pushed**
- ❌ **Require review from Code Owners** (solo si usas CODEOWNERS)

##### 2. Require status checks to pass before merging

- ✅ **Activar** checkbox principal
- ✅ **Require branches to be up to date before merging**

**Status checks requeridos** (buscar y seleccionar):
```
test (ubuntu-latest, 3.11)
test (macos-latest, 3.11)
lint
```

**⚠️ IMPORTANTE**: Estos checks solo aparecen después de que el workflow se haya ejecutado al menos una vez. Si no los ves:
1. Haz un push a una branch de prueba
2. Espera a que el CI termine
3. Vuelve aquí y busca los checks

##### 3. Require conversation resolution before merging

- ✅ **Activar** checkbox

##### 4. Require linear history

- ✅ **Activar** checkbox
- Esto fuerza merge con `--ff-only` o squash merge

##### 5. Additional Options

- ✅ **Do not allow bypassing the above settings**
- ✅ **Restrict who can push to matching branches**
  - Seleccionar: **Restrict pushes that create matching branches** (vacío)
- ❌ **Allow force pushes** (DESACTIVAR)
- ❌ **Allow deletions** (DESACTIVAR)

### Paso 3: Guardar

Click en **Create** o **Save changes**

---

## ✅ Verificar Configuración

### Método 1: Interfaz Web

1. **Settings** → **Branches**
2. Bajo **Branch protection rules**, verás:
   ```
   main
   Required status checks: 3
   Required reviews: 1
   ```

### Método 2: Prueba Práctica

```bash
# Intentar push directo a main (debe fallar)
git checkout main
echo "test" >> README.md
git add README.md
git commit -m "test: verificar branch protection"
git push origin main

# Resultado esperado:
# remote: error: GH006: Protected branch update failed
# remote: error: At least 1 approving review is required
```

### Método 3: GitHub API

```bash
# Obtener configuración actual
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/repos/cferrerobonet/guardias_patio/branches/main/protection
```

---

## 🚨 Bypass y Excepciones

### Cuándo Usar Bypass

**Casos válidos**:
- 🔥 **Hotfix crítico** en producción (bug grave)
- 🔧 **CI roto** por causas externas (GitHub Actions down)
- 📝 **Actualización de docs** urgente (README, LICENSE)

**Casos NO válidos**:
- ❌ "No tengo tiempo para esperar revisión"
- ❌ "Es un cambio pequeño"
- ❌ "Los tests son falsos positivos"

### Cómo Hacer Bypass (Solo Admin)

#### Opción 1: Bypass Temporal

1. **Settings** → **Branches** → Editar regla `main`
2. Activar temporalmente: **Allow specified actors to bypass required pull requests**
3. Añadirte a la lista
4. Hacer el push necesario
5. **IMPORTANTE**: Remover el bypass inmediatamente después

#### Opción 2: Usar Branch Temporal

```bash
# Método recomendado (mantiene historial)
git checkout -b hotfix/critical-bug
git push origin hotfix/critical-bug

# En GitHub:
# 1. Crear PR
# 2. Aprobar tu propio PR (permitido en emergencias)
# 3. Mergear con "Merge without waiting for requirements"
```

### Documentar Bypass

**Siempre documentar** en commit message:

```bash
git commit -m "fix: corregir bug crítico de seguridad [BYPASS]

RAZÓN BYPASS: Vulnerabilidad crítica reportada por usuario.
CI bloqueado por issue externo (GitHub Actions timeout).
Revisión post-facto por @reviewer solicitada.

Fixes #234"
```

---

## 🔍 Troubleshooting

### Problema: "Required status check is not passing"

#### Síntoma

```
× test (ubuntu-latest, 3.11) - failed
```

#### Soluciones

1. **Ver logs del CI**:
   - GitHub → Actions → Click en workflow fallido
   - Ver error exacto

2. **Reproducir localmente**:
   ```bash
   pytest tests/ -v
   ```

3. **Corregir y re-push**:
   ```bash
   # Fix el código
   git add .
   git commit -m "fix: resolver tests fallidos"
   git push
   ```
   - CI se ejecuta automáticamente

### Problema: "Branch is out-of-date with base branch"

#### Síntoma

```
⚠️ This branch is out-of-date with the base branch
```

#### Solución

```bash
# Opción 1: Rebase (recomendado)
git checkout feature/mi-feature
git fetch origin
git rebase origin/main
git push --force-with-lease

# Opción 2: Merge (más seguro)
git checkout feature/mi-feature
git fetch origin
git merge origin/main
git push
```

### Problema: "Required review not submitted"

#### Síntoma

```
⚠️ 1 approving review required by reviewers
```

#### Solución

1. **Pedir revisión**:
   - En el PR, click en "Reviewers" → Añadir reviewer
   - O comentar: "@cferrerobonet ¿Puedes revisar?"

2. **Esperar aprobación**:
   - Revisor comentará y aprobará
   - O solicitará cambios

3. **Si eres admin**:
   - Solo en emergencias: Puedes aprobar tu propio PR
   - **Documentar razón** en comentario

### Problema: "Status check not found"

#### Síntoma

```
⚠️ Required status check "test (ubuntu-latest, 3.11)" has not been run
```

#### Causa

- El workflow CI no se ejecutó (por ejemplo, si solo cambiaste README)
- O el workflow tiene un error de sintaxis

#### Solución

```bash
# Forzar ejecución del CI con commit vacío
git commit --allow-empty -m "ci: trigger workflows"
git push
```

---

## 📚 Referencias

### Documentación Oficial

- [GitHub Branch Protection Rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [Status Checks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/collaborating-on-repositories-with-code-quality-features/about-status-checks)

### Documentación del Proyecto

- [CI_CD.md](../CI_CD.md) - Workflows automáticos
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Proceso de contribución
- [TECHNICAL_GUIDE.md](../TECHNICAL_GUIDE.md) - Arquitectura técnica

---

## 📊 Checklist de Configuración

```markdown
- [ ] Regla de branch protection creada para `main`
- [ ] Require pull request: ✅ (1 aprobación)
- [ ] Require status checks: ✅ (test ubuntu + macos + lint)
- [ ] Require branches up-to-date: ✅
- [ ] Require conversation resolution: ✅
- [ ] Require linear history: ✅
- [ ] Allow force pushes: ❌
- [ ] Allow deletions: ❌
- [ ] Allow bypass: ❌ (solo admin)
- [ ] Configuración verificada con push de prueba
- [ ] Equipo informado de las nuevas reglas
```

---

**Mantenido por**: Carlos Ferrero Bonet  
**Proyecto**: Guardias de Patio v3.0.0  
**Última revisión**: 8 de noviembre de 2025
