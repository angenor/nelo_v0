#!/usr/bin/env bash
# PORTE P-11 — le cloisonnement tient, par trois verrous (docs/01-stack.md § 7.4) :
# déclaration, graphe d'imports (imports différés et chaînes compris), surface.
# Un compilateur refusait, un test signale — c'est plus faible, et c'est écrit.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "PORTE P-11 ÉCHOUÉE : $1" >&2; exit 1; }

modules=$(uv run python -c "import grimp; print(len(grimp.build_graph('api', 'modules').modules))")
[ "$modules" -gt 0 ] || echec "aucun module inspecté"

if ! sortie=$(uv run pytest tests/frontieres/test_declarations.py -q -p no:cacheprovider 2>&1); then
  echo "$sortie" | grep -E "^E  " >&2 || echo "$sortie" >&2
  echec "verrou de déclaration — un paquet déclare le module cloisonné"
fi
if ! sortie=$(uv run lint-imports --contract protection 2>&1); then
  echo "$sortie" | grep -E -- "->|imported" >&2 || echo "$sortie" >&2
  echec "verrou du graphe — un import atteint le module cloisonné"
fi
if ! sortie=$(uv run pytest tests/frontieres/test_chaines.py -q -p no:cacheprovider 2>&1); then
  echo "$sortie" | grep -E "^E  " >&2 || echo "$sortie" >&2
  echec "verrou du graphe — un chemin vers le module cloisonné est écrit en chaîne"
fi
if ! sortie=$(uv run pytest tests/frontieres/test_surface_protection.py -q -p no:cacheprovider 2>&1); then
  echo "$sortie" | grep -E "^E  " >&2 || echo "$sortie" >&2
  echec "verrou de surface — le module cloisonné expose plus que son interface"
fi

echo "PORTE P-11 : 3 verrous, $modules modules, 0 chaîne suspecte"
