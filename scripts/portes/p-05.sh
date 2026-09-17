#!/usr/bin/env bash
# PORTE P-05 : chaque écran déclaré dans web/ecrans.json s'atteint dans un vrai navigateur,
# Chromium et WebKit, thème clair et sombre, sans erreur (research.md R-12). La construction
# (web/.output) est servie par Playwright ; les écrans de développement le sont par un serveur
# nuxt dev que la porte lance et arrête elle-même.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-05 ÉCHOUÉE : $1" >&2; exit 1; }

[ -f web/.output/server/index.mjs ] || echec "aucune construction dans web/.output, lancer pnpm --filter nelo-web build"
export NELO_WEB_PORT="${NELO_WEB_PORT:-4310}"
export NELO_WEB_PORT_DEV="${NELO_WEB_PORT_DEV:-4311}"

read -r ecrans visites dev <<<"$(node -e '
  const { ecrans } = require("./web/ecrans.json")
  const visites = ecrans.reduce((n, e) => n + (e.personas?.length ?? 1), 0)
  console.log(ecrans.length, visites, ecrans.some((e) => e.developpement) ? 1 : 0)
')"

lancer() { pnpm --filter nelo-web portes:p05 2>&1; }
if [ "$dev" = 1 ]; then
  lancer() { scripts/avec-serveur-dev.sh pnpm --filter nelo-web portes:p05 2>&1; }
fi

if ! sortie=$(lancer); then
  motifs=$(grep -o "PORTE P-05 ÉCHOUÉE : [^\"]*" <<<"$sortie" | sort -u || true)
  if [ -n "$motifs" ]; then
    echo "$motifs" >&2
    exit 1
  fi
  echo "$sortie" | tail -25 >&2
  echec "Playwright a échoué hors des vérifications de la porte"
fi

echo "PORTE P-05 : $ecrans écrans, $visites visites × 2 moteurs × 2 thèmes, 0 erreur"
