#!/usr/bin/env bash
# La vérification — une seule commande (docs/01-stack.md § 7).
#
#   ruff → P-02 → P-07 → P-04 → P-11 → P-01 → P-12 → P-03 → reparcours sous suspension
#
# Du moins coûteux au plus coûteux (research.md R-18). Sort au premier contrôle rouge, en nommant
# la porte et le motif. Cible : moins de trois minutes (SC-010) — mesurée à 19 s sur le dépôt
# conforme le 2026-09-15 (poste de développement, base PostgreSQL déjà levée).
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

debut=$(date +%s)
portes_vertes=0

etape() { # nom commande...
  local nom="$1"; shift
  if ! "$@"; then
    echo "VÉRIFICATION ÉCHOUÉE : $nom" >&2
    exit 1
  fi
}

etape_muette() { # nom commande... : la sortie ne s'imprime qu'en cas d'échec
  local nom="$1"; shift
  local sortie
  if ! sortie=$("$@" 2>&1); then
    echo "$sortie" | tail -30 >&2
    echo "VÉRIFICATION ÉCHOUÉE : $nom" >&2
    exit 1
  fi
  echo "$nom : ok"
}

porte() { # P-XX
  local numero="$1"
  local script
  script="scripts/portes/$(echo "$numero" | tr 'P' 'p').sh"
  if ! "$script"; then
    echo "VÉRIFICATION ÉCHOUÉE : $numero" >&2
    exit 1
  fi
  portes_vertes=$((portes_vertes + 1))
}

etape "ruff check" uv run --frozen ruff check .
etape "ruff format" uv run --frozen ruff format --check .
porte P-02
porte P-07
porte P-04
porte P-11
porte P-06
porte P-01
porte P-12
porte P-03
etape "reparcours sous suspension" scripts/portes/reparcours-suspension.sh
etape_muette "typecheck" pnpm --filter nelo-web typecheck
etape_muette "vitest" pnpm --filter nelo-web test:unit
etape_muette "construction" pnpm --filter nelo-web build

duree=$(( $(date +%s) - debut ))
echo "VÉRIFICATION : $portes_vertes portes vertes en $((duree / 60)) min $((duree % 60)) s"
