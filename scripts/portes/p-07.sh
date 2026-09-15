#!/usr/bin/env bash
# PORTE P-07 — aucune dépendance sous licence copyleft fort, ni de licence inconnue.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
uv run --frozen python -m scripts.portes.p07_licences
