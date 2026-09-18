#!/usr/bin/env bash
# Tests négatifs de P-12 : quatre mutations, une par argument, chacune doit faire échouer la porte.
#
#   scripts/portes/negatifs/p-12.sh          # le schéma migré s'écarte du schéma déclaré
#   scripts/portes/negatifs/p-12.sh a        # la session n'est plus consultée à chaque requête
#   scripts/portes/negatifs/p-12.sh b        # la demande de code dit si un numéro est connu
#   scripts/portes/negatifs/p-12.sh c        # l'année absente se replie sur l'année active
#
# Les trois dernières ne cassent aucune déclaration : elles cassent une **règle de sécurité**, et
# c'est la suite de tests, exécutée par P-12, qui doit s'en apercevoir. Une porte qui ne verrait
# pas ces mutations ne prouverait rien de ce que la tranche promet.
set -euo pipefail

muter() { python3 scripts/portes/negatifs/muter.py "$@"; }

case "${1:-schema}" in
  schema)
    # Une colonne renommée dans la migration, sans toucher tables.py ni acces.py.
    muter migrations/tenants/versions/0001_socle_tenants.py \
      'sa.Column("valeur", JSONB, nullable=False)' \
      'sa.Column("valeur_json", JSONB, nullable=False)'
    ;;
  a)
    # La liste de révocation n'est plus consultée : un jeton encore valable rouvrirait une porte
    # qu'une suspension vient de fermer.
    muter api/session.py \
      'if not await session_module.session_valide(' \
      'if False and not await session_module.session_valide('
    ;;
  b)
    # La demande de code répond autrement quand personne ne porte le numéro : la réponse devient
    # un oracle, et l'existence des comptes se lit en comparant deux réponses.
    muter modules/socle/habilitations/service.py \
      '    if not comptes:
        return' \
      '    if not comptes:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "aucun compte", statut=404)'
    ;;
  c)
    # L'en-tête d'année absent se replierait silencieusement : une note s'écrirait dans l'année
    # d'à côté, et personne ne le verrait avant les bulletins.
    muter api/annee.py \
      '            if pedagogique:' \
      '            if False and pedagogique:'
    ;;
  *)
    echo "mutation inconnue : $1" >&2
    exit 2
    ;;
esac
