#!/usr/bin/env bash
# La vérification — une seule commande (docs/01-stack.md § 7).
#
# Enchaîne tout ce qui doit passer et sort au premier contrôle rouge, en nommant la porte et le motif.
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

porte() { # P-XX
  local numero="$1"
  local script="scripts/portes/$(echo "$numero" | tr 'P' 'p').sh"
  if ! "$script"; then
    echo "VÉRIFICATION ÉCHOUÉE : $numero" >&2
    exit 1
  fi
  portes_vertes=$((portes_vertes + 1))
}

etape "ruff check" uv run ruff check .
etape "ruff format" uv run ruff format --check .

duree=$(( $(date +%s) - debut ))
echo "VÉRIFICATION : $portes_vertes portes vertes en ${duree} s"
