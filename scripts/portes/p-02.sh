#!/usr/bin/env bash
# PORTE P-02 — aucune dépendance en intervalle ; les fichiers de verrouillage sont commités et à jour.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-02 ÉCHOUÉE : $1" >&2; exit 1; }

comptes=$(uv run --frozen python -m scripts.portes.p02_verrouillage) || exit 1
read -r dependances lockfiles <<<"$comptes"

git ls-files --error-unmatch uv.lock >/dev/null 2>&1 || echec "uv.lock n'est pas commité"
uv lock --check --offline >/dev/null 2>&1 || echec "uv.lock ne correspond pas aux pyproject.toml"
if [ -f package.json ]; then
  git ls-files --error-unmatch pnpm-lock.yaml >/dev/null 2>&1 || echec "pnpm-lock.yaml n'est pas commité"
  pnpm install --frozen-lockfile --offline --silent >/dev/null 2>&1 \
    || echec "pnpm-lock.yaml ne correspond pas à package.json"
fi

echo "PORTE P-02 : $dependances dépendances épinglées, $lockfiles lockfiles"
