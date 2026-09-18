#!/usr/bin/env bash
# Lance une commande pendant qu'un serveur nuxt dev sert les écrans de développement (la page
# de style), puis l'arrête, quoi qu'il arrive. Le port vient de NELO_WEB_PORT_DEV (4311 par défaut).
#
#   scripts/avec-serveur-dev.sh pnpm --filter nelo-web test:e2e
#
# Avec NELO_SESSION_SEMEE=1, il lance en plus l'API de test (research.md R-11) : la base
# nelo_web_test recréée et semée par scripts/bd-vierge.sh --avec-jeu-d-essai, dont il capture les
# `export` (NUMERO_A, ETAB_A, …), Valkey sur sa base 2, un journal des messages courts dans un
# fichier temporaire, et uvicorn sur NELO_PORT_API_TEST (8010 par défaut). L'application, servie
# en développement ici ou construite et lancée par Playwright, reçoit alors NUXT_API_BASE sur ce
# port. C'est ce qui permet au projet Playwright « setup » d'ouvrir une vraie session.
#
# US1 a livré les routes d'authentification : NELO_SESSION_SEMEE vaut donc 1 par défaut, et
# les portes ouvrent une vraie session. La poser à 0 fait tourner l'interface seule, sans API, ce
# qui reste utile pour travailler un écran sans base.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

export NELO_WEB_PORT_DEV="${NELO_WEB_PORT_DEV:-4311}"
# La page de style et les personas n'existent que dans une construction d'essai (research.md R-10).
export NELO_DEMONSTRATION="${NELO_DEMONSTRATION:-1}"

journal="$(mktemp "${TMPDIR:-/tmp}/nelo-dev.XXXXXX")"
journal_api=""
sms=""
serveur=""
api=""

arreter() {
  if [ -n "$api" ]; then
    kill "$api" 2>/dev/null || true
    pkill -f "uvicorn api.main:app --host localhost --port ${NELO_PORT_API_TEST:-}" 2>/dev/null || true
  fi
  if [ -n "$serveur" ]; then kill "$serveur" 2>/dev/null || true; fi
  pkill -f "nuxt dev --port $NELO_WEB_PORT_DEV" 2>/dev/null || true
  for _ in $(seq 1 20); do
    curl -s -o /dev/null "http://localhost:$NELO_WEB_PORT_DEV/" || break
    sleep 0.25
  done
  rm -f "$journal" "$journal_api" "$sms"
}
trap arreter EXIT

export NELO_SESSION_SEMEE="${NELO_SESSION_SEMEE:-1}"
if [ "$NELO_SESSION_SEMEE" = "1" ]; then
  source scripts/env.sh
  export NELO_PORT_API_TEST="${NELO_PORT_API_TEST:-8010}"
  # Une base à elle, recréée à chaque tour : les portes ne partagent rien avec le développement.
  export NELO_BD_NOM="${NELO_BD_NOM:-nelo_web_test}"
  # La base 2 de Valkey, pour la même raison.
  export NELO_VALKEY_URL="${NELO_VALKEY_URL%/*}/2"
  # Sur http://localhost, le navigateur refuse un cookie Secure.
  export NELO_COOKIES_SECURE=false
  export NUXT_COOKIES_SECURE=false
  export NELO_SECRET_JETON="${NELO_SECRET_JETON:-secret-des-portes-jamais-en-production}"
  : "${NELO_INDICATIF_DEFAUT:?API DE TEST : NELO_INDICATIF_DEFAUT manque (voir .env.exemple)}"
  sms="$(mktemp "${TMPDIR:-/tmp}/nelo-sms.XXXXXX")"
  export NELO_SMS_JOURNAL="$sms"
  export NUXT_API_BASE="http://localhost:$NELO_PORT_API_TEST"

  # L'éphémère se vide avec la base : sans cela, les sessions, les codes et les compteurs de
  # débit du tour précédent survivraient à des comptes qui n'existent plus, et la première
  # demande de code du tour suivant se ferait refuser par un délai de renvoi fantôme.
  docker compose exec -T valkey valkey-cli -n 2 FLUSHDB >/dev/null 2>&1 || true

  if ! semence=$(scripts/bd-vierge.sh --avec-jeu-d-essai 2>&1); then
    echo "API DE TEST : la base $NELO_BD_NOM ne se sème pas ($(tail -3 <<<"$semence"))" >&2
    exit 1
  fi
  # Le jeu d'essai imprime ses identifiants en forme `export` : ils passent dans l'environnement
  # de la commande, où les tests les lisent (NUMERO_A, ETAB_A, …).
  eval "$(grep '^export ' <<<"$semence" || true)"

  journal_api="$(mktemp "${TMPDIR:-/tmp}/nelo-api.XXXXXX")"
  uv run uvicorn api.main:app --host localhost --port "$NELO_PORT_API_TEST" >"$journal_api" 2>&1 &
  api=$!
  for _ in $(seq 1 120); do
    curl -s -o /dev/null "http://localhost:$NELO_PORT_API_TEST/api/v1/sante" && break
    if ! kill -0 "$api" 2>/dev/null; then
      echo "API DE TEST : arrêtée au démarrage ($(tail -5 "$journal_api"))" >&2
      exit 1
    fi
    sleep 0.5
  done
  if ! curl -s -o /dev/null "http://localhost:$NELO_PORT_API_TEST/api/v1/sante"; then
    echo "API DE TEST : /api/v1/sante ne répond pas ($(tail -5 "$journal_api"))" >&2
    exit 1
  fi
fi

if curl -s -o /dev/null "http://localhost:$NELO_WEB_PORT_DEV/"; then
  echo "SERVEUR DE DÉVELOPPEMENT : le port $NELO_WEB_PORT_DEV est déjà pris ; NELO_WEB_PORT_DEV en choisit un autre" >&2
  exit 1
fi

(cd web && exec pnpm exec nuxt dev --port "$NELO_WEB_PORT_DEV" --host localhost >"$journal" 2>&1) &
serveur=$!
disown "$serveur"

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
