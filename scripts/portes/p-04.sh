#!/usr/bin/env bash
# PORTE P-04 — la hiérarchie des paquets tient : aucun paquet de socle/ n'importe metier/, et
# chaque arête d'import entre membres de l'espace de travail est déclarée.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-04 ÉCHOUÉE : $1" >&2; exit 1; }

modules=$(uv run python -c "import grimp; print(len(grimp.build_graph('api', 'modules').modules))")
[ "$modules" -gt 0 ] || echec "aucun module inspecté"

if ! sortie=$(uv run lint-imports --contract hierarchie 2>&1); then
  echo "$sortie" | grep -E -A3 "BROKEN|->|is not allowed to import" >&2 || echo "$sortie" >&2
  echec "arête interdite par le contrat de hiérarchie"
fi
if ! sortie=$(uv run pytest tests/frontieres/test_graphe.py -q -p no:cacheprovider 2>&1); then
  echo "$sortie" | grep -E "^E  " >&2 || echo "$sortie" >&2
  echec "graphe d'imports : arête interdite ou non déclarée"
fi

echo "PORTE P-04 : $modules modules inspectés, 0 arête interdite"
