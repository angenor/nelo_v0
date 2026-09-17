#!/usr/bin/env bash
# Lance une commande pendant qu'un serveur nuxt dev sert les écrans de développement (la page
# de style), puis l'arrête, quoi qu'il arrive. Le port vient de NELO_WEB_PORT_DEV (4311 par défaut).
#
#   scripts/avec-serveur-dev.sh pnpm --filter nelo-web test:e2e
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export NELO_WEB_PORT_DEV="${NELO_WEB_PORT_DEV:-4311}"
journal="$(mktemp "${TMPDIR:-/tmp}/nelo-dev.XXXXXX")"

if curl -s -o /dev/null "http://localhost:$NELO_WEB_PORT_DEV/"; then
  echo "SERVEUR DE DÉVELOPPEMENT : le port $NELO_WEB_PORT_DEV est déjà pris ; NELO_WEB_PORT_DEV en choisit un autre" >&2
  exit 1
fi

(cd web && exec pnpm exec nuxt dev --port "$NELO_WEB_PORT_DEV" --host localhost >"$journal" 2>&1) &
serveur=$!
disown "$serveur"
arreter() {
  kill "$serveur" 2>/dev/null || true
  pkill -f "nuxt dev --port $NELO_WEB_PORT_DEV" 2>/dev/null || true
  for _ in $(seq 1 20); do
    curl -s -o /dev/null "http://localhost:$NELO_WEB_PORT_DEV/" || break
    sleep 0.25
  done
  rm -f "$journal"
}
trap arreter EXIT

for _ in $(seq 1 120); do
  curl -s -o /dev/null "http://localhost:$NELO_WEB_PORT_DEV/style" && break
  if ! kill -0 "$serveur" 2>/dev/null; then
    echo "SERVEUR DE DÉVELOPPEMENT : arrêté au démarrage ($(tail -3 "$journal"))" >&2
    exit 1
  fi
  sleep 0.5
done

if ! (cd web && node tests/prechauffer.mjs) >>"$journal" 2>&1; then
  echo "SERVEUR DE DÉVELOPPEMENT : la page de style ne s'hydrate pas ($(tail -3 "$journal"))" >&2
  exit 1
fi

"$@"
