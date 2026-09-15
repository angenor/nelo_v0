#!/usr/bin/env bash
# PORTE P-03 — le client TypeScript régénéré depuis OpenAPI ne produit aucun écart.
#
# Écrit contrat/openapi.json depuis l'application, en dérive contrat/client.d.ts, puis exige que
# les deux fichiers soient identiques à ce qui est commité (index compris) — et suivis par git.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-03 ÉCHOUÉE : $1" >&2; exit 1; }

uv run python -m api.contrat || echec "la spécification OpenAPI n'a pas pu être écrite"
pnpm exec openapi-typescript contrat/openapi.json -o contrat/client.d.ts >/dev/null 2>&1 \
  || echec "openapi-typescript n'a pas pu dériver contrat/client.d.ts"

for fichier in contrat/openapi.json contrat/client.d.ts; do
  git ls-files --error-unmatch "$fichier" >/dev/null 2>&1 || echec "$fichier n'est pas commité"
done

if ! git diff --quiet -- contrat/; then
  lignes=$(git diff --numstat -- contrat/ | awk '{s += $1 + $2} END {print s}')
  git diff -- contrat/ | head -20 >&2
  echec "$lignes ligne(s) d'écart entre le contrat régénéré et le contrat commité"
fi

echo "PORTE P-03 : 2 fichiers régénérés, 0 ligne d'écart"
