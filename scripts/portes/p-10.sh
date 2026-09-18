#!/usr/bin/env bash
# PORTE P-10 : aucun écran budgété ne dépasse son plafond (research.md R-13, R-16). La
# construction est déjà faite par verifier.sh ; Playwright la sert et Chromium la mesure.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-10 ÉCHOUÉE : $1" >&2; exit 1; }

[ -f web/.output/server/index.mjs ] || echec "aucune construction dans web/.output, lancer pnpm --filter nelo-web build"
export NELO_WEB_PORT="${NELO_WEB_PORT:-4310}"

# Les écrans de session se visitent avec une vraie session : la porte lance alors l'API de
# test et sa base semée, comme P-05 (research.md R-11).
session=$(node -e '
  const { ecrans } = require("./web/ecrans.json")
  console.log(ecrans.some((e) => e.session) ? 1 : 0)
')

lancer() { pnpm --filter nelo-web portes:p10 2>&1; }
if [ "$session" = 1 ]; then
  lancer() { scripts/avec-serveur-dev.sh pnpm --filter nelo-web portes:p10 2>&1; }
fi

if ! sortie=$(lancer); then
  motifs=$(grep -o "Error: PORTE P-10 ÉCHOUÉE : .*" <<<"$sortie" | sed 's/^Error: //' | sort -u || true)
  if [ -n "$motifs" ]; then
    echo "$motifs" >&2
    exit 1
  fi
  echo "$sortie" | tail -25 >&2
  echec "Playwright a échoué hors des vérifications de la porte"
fi
grep -o "PORTE P-10 : .*" <<<"$sortie"
