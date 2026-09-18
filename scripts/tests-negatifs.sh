#!/usr/bin/env bash
# Chaque porte prouve qu'elle mord (docs/01-stack.md § 7, research.md R-13).
#
# Pour chaque porte : une copie de travail git temporaire sur HEAD, la mutation de
# scripts/portes/negatifs/p-XX.sh, la porte seule, qui doit échouer en se nommant. Le dépôt
# d'origine n'est jamais muté : son `git status` est comparé avant et après. Pour P-05 et P-10,
# la copie construit l'interface après la mutation, et sert sur des ports à elle.
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"

# Une entrée par mutation, pas par porte : P-12 en a quatre, et chacune doit la faire échouer
# séparément. Le script de porte reste le même ; l'argument dit quelle règle est cassée.
PORTES=(P-01 P-02 P-03 P-04 P-05 P-06 P-07 P-10 P-11 P-12 P-12a P-12b P-12c)
INTERFACE_CONSTRUITE=" P-05 P-10 "
etat_initial=$(git status --porcelain)
base=$(mktemp -d "${TMPDIR:-/tmp}/nelo-negatifs.XXXXXX")
obtenus=0
debut=$(date +%s)

nettoyer() {
  for copie in "$base"/*/; do
    [ -d "$copie" ] && git worktree remove --force "$copie" >/dev/null 2>&1 || true
  done
  rm -rf "$base"
  git worktree prune
}
trap nettoyer EXIT

for porte in "${PORTES[@]}"; do
  # « P-12b » casse la porte P-12 par la mutation « b » : le suffixe est l'argument du script.
  numero=$(echo "${porte%%[a-z]}" | tr 'P' 'p')
  mutation="${porte#"${porte%%[a-z]}"}"
  copie="$base/$(echo "$porte" | tr 'P' 'p')"
  git worktree add --detach --quiet "$copie" HEAD
  [ -f .env ] && cp .env "$copie/.env"
  (
    cd "$copie"
    uv sync --frozen --offline --quiet >/dev/null 2>&1
    pnpm install --frozen-lockfile --offline --silent >/dev/null 2>&1
  )

  sortie=$(
    cd "$copie" &&
    "scripts/portes/negatifs/$numero.sh" $mutation &&
    if [[ "$INTERFACE_CONSTRUITE" == *" $porte "* ]]; then
      # La même construction que `verifier.sh` : sans NELO_DEMONSTRATION, les écrans à persona
      # redirigent vers /connexion, et P-05 mesurerait des redirections au lieu des écrans.
      env NELO_DEMONSTRATION=1 pnpm --filter nelo-web build >/dev/null 2>&1 \
        || echo "construction de la copie échouée"
    fi &&
    NELO_BD_NOM=nelo_negatif NELO_BD_NOM_TEST=nelo_negatif_test \
      NELO_WEB_PORT=4320 NELO_WEB_PORT_DEV=4321 "scripts/portes/$numero.sh" 2>&1
  ) && code=0 || code=$?

  attendu="PORTE ${porte%%[a-z]} ÉCHOUÉE"
  if [ "$code" -ne 0 ] && grep -q "$attendu" <<<"$sortie"; then
    obtenus=$((obtenus + 1))
    echo "✓ $porte cassée : $(grep "$attendu" <<<"$sortie" | head -1)"
  else
    echo "✗ $porte cassée, mais la porte n'a pas échoué en se nommant (code $code)" >&2
    echo "$sortie" | tail -5 >&2
  fi
  git worktree remove --force "$copie"
done

if [ "$(git status --porcelain)" != "$etat_initial" ]; then
  echo "TESTS NÉGATIFS ÉCHOUÉS : le dépôt d'origine a été modifié" >&2
  exit 1
fi

duree=$(( $(date +%s) - debut ))
if [ "$obtenus" -ne "${#PORTES[@]}" ]; then
  echo "TESTS NÉGATIFS ÉCHOUÉS : ${#PORTES[@]} portes cassées, $obtenus échecs obtenus" >&2
  exit 1
fi
echo "${#PORTES[@]} portes cassées, $obtenus échecs obtenus, dépôt intact (${duree} s)"
