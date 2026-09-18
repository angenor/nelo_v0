#!/usr/bin/env bash
# La vérification : une seule commande, dix portes (docs/01-stack.md § 7).
#
#   ruff → P-02 → P-07 → P-04 → P-11 → P-06 → P-01 → P-12 → P-03 → reparcours sous suspension
#   → typecheck → vitest → construction → P-05 → P-10 → e2e
#
# Du moins coûteux au plus coûteux (T0a research.md R-18, T0b research.md R-15) : les contrôles
# statiques d'abord, la base ensuite, puis l'interface, construite une seule fois et partagée par
# les trois dernières étapes. Sort au premier contrôle rouge, en nommant la porte et le motif.
# Cible : moins de trois minutes (SC-010, SC-011) ; la durée mesurée est au journal.
#
# La construction porte NELO_DEMONSTRATION=1 (research.md R-10) : sans elle, les personas sont
# élagués et P-05, P-10 et les e2e de composition n'auraient plus de contexte à montrer.
#
# NELO_SESSION_SEMEE=1 ajoute la session semée (research.md R-11) : scripts/avec-serveur-dev.sh
# lance alors l'API de test sur sa base semée, et le projet Playwright « setup » ouvre une vraie
# session avant les autres projets. Tant qu'US1 n'a livré aucune route d'authentification, la
# variable reste vide et rien ne dépend de l'API ; US1 la posera par défaut.
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
etape_muette "construction" env NELO_DEMONSTRATION=1 pnpm --filter nelo-web build
porte P-05
porte P-10
etape_muette "e2e" scripts/avec-serveur-dev.sh pnpm --filter nelo-web test:e2e

duree=$(( $(date +%s) - debut ))
echo "VÉRIFICATION : $portes_vertes portes vertes en $((duree / 60)) min $((duree % 60)) s"
