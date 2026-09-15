#!/usr/bin/env bash
# PORTE P-12 — toute fonction d'accès aux données est exercée contre une base fraîchement migrée,
# et le schéma migré ne s'écarte pas du schéma déclaré.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
source scripts/env.sh

rm -f .coverage coverage.json
set +e
uv run --frozen coverage run -m pytest -q -p no:cacheprovider >/tmp/nelo-p12-$$.log 2>&1
code_tests=$?
set -e
if [ "$code_tests" -ne 0 ]; then
  grep -E "^(FAILED|ERROR)" /tmp/nelo-p12-$$.log | head -10 >&2 || tail -20 /tmp/nelo-p12-$$.log >&2
fi
rm -f /tmp/nelo-p12-$$.log
uv run --frozen coverage json -q -o coverage.json
uv run --frozen python -m scripts.portes.p12_acces_exerces "$code_tests"
