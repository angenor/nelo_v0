#!/usr/bin/env bash
# PORTE P-06 : aucune littérale d'interface en dur (chaîne visible, valeur de couleur, appel direct
# de plateforme, rôle) ; les clés fr et en existent toutes les deux ; les copies du design sont
# intactes (docs/01-stack.md § 7, research.md R-11).
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
[ -d web/node_modules ] || { echo "PORTE P-06 ÉCHOUÉE : web/node_modules absent, lancer pnpm install" >&2; exit 1; }
node scripts/portes/p06_interface.mjs
