#!/usr/bin/env bash
# Sube la web de guardias (carpeta web/) al hosting de EPLA (IONOS) por SFTP con lftp.
# Una sola conexión por ejecución (IONOS cierra el puerto 22 si hay conexiones seguidas), también con -n,
# dentro del presupuesto común (scripts/ionos_presupuesto.sh: 2 cada 10 min; sin cupo, sale con 75 y no conecta).
# Nunca toca web/datos/ en el servidor: ahí publica la app los resúmenes (solo se sube su .htaccess).
# web/config.php (token y cuentas) está fuera de git: se crea desde config.example.php y se sube con la web.
#
# Uso:
#   scripts/deploy.sh      # sube lo que cambia
#   scripts/deploy.sh -n   # simulación: muestra qué subiría
#
# Requiere lftp (brew install lftp) y un .env en la raíz con SFTP_HOST, SFTP_USER, SFTP_PASS, SFTP_REMOTE_DIR.
# Ejecutar fuera del sandbox de Bash: la red hacia IONOS está bloqueada dentro.
set -euo pipefail
cd "$(dirname "$0")/.."
[[ -f .env ]] || { echo "Falta .env (copiar de .env.example)"; exit 1; }
set -a; source .env; set +a
: "${SFTP_HOST:?}" "${SFTP_USER:?}" "${SFTP_PASS:?}"
REMOTO="${SFTP_REMOTE_DIR:?Falta SFTP_REMOTE_DIR en .env}"
SIMULAR=""
for a in "$@"; do case "$a" in -n) SIMULAR="--dry-run";; esac; done
EXCL='--exclude-glob .DS_Store --exclude-glob datos/ --exclude-glob config.example.php'
# La contraseña va por la variable LFTP_PASSWORD (--env-password), nunca en la línea de órdenes
# (se vería con ps), como en el despliegue de Pinza.
export LFTP_PASSWORD="$SFTP_PASS"
AJUSTES="set sftp:auto-confirm yes; set net:max-retries 1; set net:timeout 20; set cmd:verbose no"
# Con --dry-run, lftp escribe cada orden con la URL completa, usuario y contraseña
# incluidos, aunque se den con «user» (visto en Calendarios el 2026-10-14). Toda
# salida de lftp va por este filtro; pipefail conserva su código de salida.
lftp_seguro() { lftp --env-password -u "$SFTP_USER" "sftp://$SFTP_HOST" -e "$AJUSTES; $1; bye" 2>&1 | sed -E 's#(sftp://)[^@/[:space:]]*@#\1***@#g'; }
# shellcheck source=scripts/ionos_presupuesto.sh
. scripts/ionos_presupuesto.sh
ionos_presupuesto -c 1 guardias-web "deploy${SIMULAR:+ simulación}" || exit 75
# Si lftp falla, se anota el fallo: el presupuesto deja 15 min de enfriamiento antes de otra conexión.
trap 'r=$?; unset LFTP_PASSWORD; [ "$r" -eq 0 ] || { ionos_presupuesto_fallo guardias-web "deploy (código $r)"; echo "✘ Ha fallado. No reintentar a ciegas: bash scripts/ionos_presupuesto.sh --estado dice cuándo se puede." >&2; }' EXIT
echo "→ Web → servidor de .env${SIMULAR:+ (simulación)}"
if [[ -n "$SIMULAR" ]]; then
  lftp_seguro "mirror -R --verbose=1 --only-newer $SIMULAR $EXCL web $REMOTO"
else
  lftp_seguro "mkdir -p -f $REMOTO; mirror -R --verbose=1 --only-newer $EXCL web $REMOTO; mkdir -p -f $REMOTO/datos; put -O $REMOTO/datos web/datos/.htaccess"
fi
echo "Deploy completado."
