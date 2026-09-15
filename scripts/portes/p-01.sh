#!/usr/bin/env bash
# PORTE P-01 — les migrations s'appliquent sur base vierge, un dossier par module, réversibles ;
# chaque table porte ENABLE + FORCE ROW LEVEL SECURITY et sa politique ; aucune clé étrangère
# ne traverse un schéma de module.
#
# Travaille sur une base logique à part (NELO_BD_NOM, défaut nelo_verification) : la base de
# développement n'est jamais touchée.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
source scripts/env.sh
export NELO_BD_NOM="${NELO_BD_NOM:-nelo_verification}"

echec() { echo "PORTE P-01 ÉCHOUÉE : $1" >&2; exit 1; }

scripts/bd-vierge.sh >/dev/null || echec "base vierge ou upgrade head en échec"
for dossier in migrations/*/; do
  ini="${dossier}alembic.ini"
  [ -f "$ini" ] || echec "le dossier $dossier n'a pas d'alembic.ini"
  uv run alembic -c "$ini" downgrade base >/dev/null || echec "downgrade base en échec ($dossier)"
  uv run alembic -c "$ini" upgrade head >/dev/null || echec "second upgrade head en échec ($dossier)"
done

uv run python -m scripts.portes.p01_schema
