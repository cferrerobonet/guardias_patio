---
paths:
  - "tests/**"
  - "pytest.ini"
  - ".coveragerc"
---

# Tests

- **Barrera antes que test** (obligatorio): un test que pueda tocar red, llavero, `.env`, servidor SFTP/SMTP o una base real se escribe **después** de la barrera en `tests/conftest.py`, nunca antes. El 2026-09-06 tres tests llegaron a IONOS, al Keychain y al `.env` de desarrollo por hacerlo al revés. Un fallo de test preexistente (no causado por la sesión) se anota y no se corrige en la misma sesión.
- Cuatro barreras automáticas en `tests/conftest.py`: `dialogos_modales`, `sin_smtp_de_verdad`, `sin_llavero_de_verdad`, `sin_env_de_verdad` (marcadores `modales_reales`, `smtp_real`, `llavero_real`, `env_real` para desactivarlas).
- Los tests de la API necesitan `GUARDIAS_API_SECRET_KEY` de 16 caracteres o más (con uno más corto fallan en la recogida y arrastran los ficheros de API) y `slowapi` instalado.
- En macOS no existe `timeout`: usar `perl -e 'alarm N; exec @ARGV'`.
- Ante un fallo nativo raro al arrancar, sospechar primero del entorno (iCloud) y no del código.
