#!/usr/bin/env bash
# ionos_presupuesto.sh — presupuesto común de conexiones nuevas al puerto 22 de IONOS.
# Copia común de la skill de usuario auditoria-apps (comun/). No se edita en el repositorio: se cambia
# en la skill y se reinstala con comun/instalar_en_repo.sh (el md5 de las dos copias tiene que coincidir).
#
# POR QUÉ: IONOS cuenta CONEXIONES NUEVAS al puerto 22 (no bytes ni órdenes) y cierra el puerto si ve
# varias seguidas (2026-09-16 y 2026-10-01, con un despliegue a medias). Todas las apps del hosting
# comparten un registro local y un mismo límite:
#   · como mucho IONOS_MAX_CONEXIONES (2) en los últimos IONOS_VENTANA segundos (600 = 10 min);
#   · ninguna durante IONOS_ENFRIAMIENTO segundos (900 = 15 min) tras una conexión que FALLÓ;
#   · sin cupo no se conecta: se dice cuánto esperar y se sale con 75 («ahora no»). No reintentar.
# Una conexión que viaja por una maestra ya abierta (ControlMaster) no es nueva: el script que la
# reutiliza no la declara.
#
# Registro (IONOS_REGISTRO, por defecto ~/.autoexam_ionos_conexiones.log): una línea por conexión,
#   <epoch> <OK|FALLO> <app> <motivo>
# Las líneas antiguas «<epoch> <OK|FALLO> <motivo>» se siguen contando igual.
#
# Con source (lo normal, desde el script de despliegue):
#   . scripts/ionos_presupuesto.sh
#   ionos_presupuesto [-c N] <app> <motivo> || exit 75   # antes de conectar: comprueba que caben N y las anota
#   ionos_presupuesto_comprobar [-c N]      || exit 75   # solo comprueba, no anota (para avisar pronto)
#   ionos_presupuesto_anotar <OK|FALLO> <app> <motivo> [N]   # anota sin comprobar (p. ej. el fallo al conectar)
#   ionos_presupuesto_fallo <app> <motivo>               # = ionos_presupuesto_anotar FALLO …
# Como orden:
#   bash scripts/ionos_presupuesto.sh [-c N] <app> <motivo>
#   bash scripts/ionos_presupuesto.sh --comprobar [-c N]
#   bash scripts/ionos_presupuesto.sh --fallo <app> <motivo>
#   bash scripts/ionos_presupuesto.sh --estado
# Salidas: 0 hay cupo (y queda anotado) · 75 no hay cupo, no conectar · 64 uso incorrecto.
# Compatible con el bash 3.2 de macOS y con set -euo pipefail en el script que lo carga.

IONOS_REGISTRO="${IONOS_REGISTRO:-$HOME/.autoexam_ionos_conexiones.log}"
IONOS_MAX_CONEXIONES="${IONOS_MAX_CONEXIONES:-2}"
IONOS_VENTANA="${IONOS_VENTANA:-600}"
IONOS_ENFRIAMIENTO="${IONOS_ENFRIAMIENTO:-900}"

# Cerrojo corto para que dos despliegues a la vez no lean el mismo cupo (mkdir es atómico).
_ionos_cerrar_registro() {
  local cerrojo="$IONOS_REGISTRO.cerrojo" i=0
  while ! mkdir "$cerrojo" 2>/dev/null; do
    # Un cerrojo de más de un minuto es de un script que murió a medias: se quita.
    if [ -n "$(find "$cerrojo" -maxdepth 0 -mmin +1 2>/dev/null)" ]; then rmdir "$cerrojo" 2>/dev/null || true; continue; fi
    i=$((i + 1))
    if [ "$i" -gt 100 ]; then
      echo "⛔ El registro de conexiones a IONOS está ocupado por otro script. No se conecta: vuelve a intentarlo en un minuto." >&2
      return 75
    fi
    sleep 0.1
  done
  return 0
}
_ionos_abrir_registro() { rmdir "$IONOS_REGISTRO.cerrojo" 2>/dev/null || true; }

# Lee -c N del principio de los argumentos: deja el número en _IONOS_N y cuántos consumió en _IONOS_DESPLAZA.
_ionos_leer_n() {
  _IONOS_N=1
  if [ "${1:-}" = "-c" ]; then
    _IONOS_N="${2:-}"
    case "$_IONOS_N" in ''|*[!0-9]*|0) echo "ionos_presupuesto: -c necesita un número de conexiones (1 o más)" >&2; return 64 ;; esac
    _IONOS_DESPLAZA=2
  else
    _IONOS_DESPLAZA=0
  fi
  return 0
}

# Comprueba, sin anotar, que caben N conexiones nuevas. 0 = sí; 75 = no (con el motivo y la espera).
ionos_presupuesto_comprobar() {
  local ahora recientes ultimo_fallo espera sobran limite_ts
  _ionos_leer_n "$@" || return 64
  ahora=$(date +%s)
  touch "$IONOS_REGISTRO" 2>/dev/null || { echo "⛔ No se puede escribir el registro de conexiones ($IONOS_REGISTRO). No se conecta." >&2; return 75; }
  if [ "$_IONOS_N" -gt "$IONOS_MAX_CONEXIONES" ]; then
    echo "⛔ Esta tarea abriría $_IONOS_N conexiones a IONOS y el máximo es $IONOS_MAX_CONEXIONES cada $((IONOS_VENTANA / 60)) min." >&2
    echo "   Hay que agruparlas en una sola (conexión maestra) o repartir la tarea. No se conecta." >&2
    return 75
  fi
  ultimo_fallo=$(awk '$2 == "FALLO" { u = $1 } END { print u + 0 }' "$IONOS_REGISTRO")
  if [ "$ultimo_fallo" -gt 0 ] && [ $((ahora - ultimo_fallo)) -lt "$IONOS_ENFRIAMIENTO" ]; then
    espera=$((IONOS_ENFRIAMIENTO - (ahora - ultimo_fallo)))
    echo "⛔ La última conexión a IONOS falló hace $(( (ahora - ultimo_fallo) / 60 )) min: el puerto 22 puede estar bloqueado." >&2
    echo "   No se conecta hasta dentro de $(( (espera + 59) / 60 )) min (cada intento podría alargar el bloqueo)." >&2
    return 75
  fi
  recientes=$(awk -v t="$ahora" -v v="$IONOS_VENTANA" '$1 ~ /^[0-9]+$/ && $1 >= t - v' "$IONOS_REGISTRO" | wc -l | tr -d ' ')
  if [ $((recientes + _IONOS_N)) -gt "$IONOS_MAX_CONEXIONES" ]; then
    # Tienen que caducar las «sobran» más antiguas de la ventana: la última de ellas marca la espera.
    sobran=$((recientes + _IONOS_N - IONOS_MAX_CONEXIONES))
    limite_ts=$(awk -v t="$ahora" -v v="$IONOS_VENTANA" '$1 ~ /^[0-9]+$/ && $1 >= t - v { print $1 }' "$IONOS_REGISTRO" | sort -n | sed -n "${sobran}p")
    espera=$(( ${limite_ts:-$ahora} + IONOS_VENTANA - ahora ))
    [ "$espera" -gt 0 ] || espera=1
    echo "⛔ Ya van $recientes conexiones a IONOS en los últimos $((IONOS_VENTANA / 60)) min (máximo $IONOS_MAX_CONEXIONES) y esta tarea necesita $_IONOS_N." >&2
    echo "   Espera $(( (espera + 59) / 60 )) min antes de volver a conectar. No reintentar antes." >&2
    return 75
  fi
  return 0
}

# Anota N líneas sin comprobar. $1 = OK | FALLO, $2 = app, $3 = motivo, $4 = N (1 por defecto).
ionos_presupuesto_anotar() {
  local estado="${1:-}" app motivo n="${4:-1}" ahora i=0
  case "$estado" in OK|FALLO) ;; *) echo "ionos_presupuesto_anotar: el estado es OK o FALLO" >&2; return 64 ;; esac
  case "$n" in ''|*[!0-9]*|0) n=1 ;; esac
  app=$(printf '%s' "${2:-sin-app}" | tr -c 'A-Za-z0-9._-' '_')
  motivo=$(printf '%s' "${3:-}" | tr '\n\r\t' '   ' | cut -c1-200)
  ahora=$(date +%s)
  while [ "$i" -lt "$n" ]; do
    printf '%s %s %s %s\n' "$ahora" "$estado" "$app" "$motivo" >> "$IONOS_REGISTRO"
    i=$((i + 1))
  done
}

ionos_presupuesto_fallo() { ionos_presupuesto_anotar FALLO "${1:-}" "${2:-}"; }

# Antes de conectar: comprueba que caben N conexiones y, si caben, las anota (fecha epoch, app, motivo).
ionos_presupuesto() {
  local n app motivo r=0
  _ionos_leer_n "$@" || return 64
  n="$_IONOS_N"; shift "$_IONOS_DESPLAZA"
  app="${1:-}"; motivo="${2:-}"
  if [ -z "$app" ]; then echo "Uso: ionos_presupuesto [-c N] <app> <motivo>" >&2; return 64; fi
  _ionos_cerrar_registro || return 75
  ionos_presupuesto_comprobar -c "$n" || r=$?
  if [ "$r" -eq 0 ]; then ionos_presupuesto_anotar OK "$app" "$motivo" "$n"; fi
  _ionos_abrir_registro
  return "$r"
}

ionos_presupuesto_estado() {
  local ahora recientes
  ahora=$(date +%s); touch "$IONOS_REGISTRO" 2>/dev/null || true
  recientes=$(awk -v t="$ahora" -v v="$IONOS_VENTANA" '$1 ~ /^[0-9]+$/ && $1 >= t - v' "$IONOS_REGISTRO" 2>/dev/null | wc -l | tr -d ' ')
  echo "Conexiones a IONOS en los últimos $((IONOS_VENTANA / 60)) min: $recientes de $IONOS_MAX_CONEXIONES."
  if ionos_presupuesto_comprobar 2>/dev/null; then echo "✔ Se puede conectar ahora."; else ionos_presupuesto_comprobar; fi
}

# Ejecutado como orden (no con source)
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -u
  case "${1:-}" in
    --comprobar) shift; ionos_presupuesto_comprobar "$@"; exit $? ;;
    --fallo) shift; ionos_presupuesto_fallo "$@"; exit $? ;;
    --estado) ionos_presupuesto_estado; exit $? ;;
    -h|--help) sed -n '2,32p' "$0"; exit 0 ;;
    '') sed -n '2,32p' "$0" >&2; exit 64 ;;
    *) ionos_presupuesto "$@"; exit $? ;;
  esac
fi
