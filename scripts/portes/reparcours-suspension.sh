#!/usr/bin/env bash
# REPARCOURS SOUS SUSPENSION — l'assistance désactivée est un test, pas une hypothèse
# (docs/01-stack.md § 3, research.md R-15, SC-008).
#
# La suite du module doré tourne une fois normalement, puis une fois avec NELO_TEST_SUSPENSION=1 :
# la fixture pose alors assistance.suspendue=true au tenant de test par PUT /parametres avant chaque
# test. Le produit doit rester pleinement opérationnel : même nombre de tests passés, aucun échec.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."

echec() { echo "REPARCOURS SOUS SUSPENSION ÉCHOUÉ : $1" >&2; exit 1; }

bilan() { # sortie de pytest -q → « passés échoués »
  local passes echoues
  passes=$(grep -Eo '[0-9]+ passed' <<<"$1" | tail -1 | cut -d' ' -f1)
  echoues=$(grep -Eo '[0-9]+ (failed|error|errors)' <<<"$1" | awk '{s += $1} END {print s + 0}')
  echo "${passes:-0} ${echoues:-0}"
}

normal=$(uv run --frozen pytest tests/module_dore -q -p no:cacheprovider 2>&1) || true
suspendu=$(NELO_TEST_SUSPENSION=1 uv run --frozen pytest tests/module_dore -q -p no:cacheprovider 2>&1) || true
read -r passes_normal echecs_normal <<<"$(bilan "$normal")"
read -r passes_suspendu echecs_suspendu <<<"$(bilan "$suspendu")"

[ "$passes_normal" -gt 0 ] || echec "aucun test du module doré n'a passé"
[ "$echecs_normal" -eq 0 ] || echec "$echecs_normal échec(s) sans suspension"
if [ "$echecs_suspendu" -ne 0 ] || [ "$passes_suspendu" -ne "$passes_normal" ]; then
  grep -E "^(FAILED|ERROR)" <<<"$suspendu" | head -10 >&2 || true
  echec "$passes_normal tests passés sans suspension, $passes_suspendu avec ($echecs_suspendu échec(s))"
fi

echo "REPARCOURS SOUS SUSPENSION : $passes_normal tests, résultat identique"
