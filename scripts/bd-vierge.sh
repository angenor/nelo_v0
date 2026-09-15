#!/usr/bin/env bash
# Recrée la base logique sur le PostgreSQL de la composition, sans toucher au conteneur.
#
#   scripts/bd-vierge.sh                      # base « nelo », migrations appliquées
#   scripts/bd-vierge.sh --avec-jeu-d-essai   # et deux tenants de test, A et B
#   NELO_BD_NOM=nelo_negatif scripts/bd-vierge.sh
#
# Le rôle applicatif nelo_app est créé s'il n'existe pas : LOGIN, NOSUPERUSER, NOBYPASSRLS.
set -euo pipefail

RACINE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RACINE"
source scripts/env.sh

export NELO_BD_NOM="${NELO_BD_NOM:-nelo}"
avec_jeu_d_essai=0
for argument in "$@"; do
  case "$argument" in
    --avec-jeu-d-essai) avec_jeu_d_essai=1 ;;
    *) echo "argument inconnu : $argument" >&2; exit 2 ;;
  esac
done

psql_proprietaire() {
  docker compose exec -T postgres psql -v ON_ERROR_STOP=1 -q -U nelo_proprietaire -d postgres "$@"
}

for _ in $(seq 1 60); do
  if docker compose exec -T postgres pg_isready -U nelo_proprietaire -d postgres >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker compose exec -T postgres pg_isready -U nelo_proprietaire -d postgres >/dev/null

psql_proprietaire <<SQL >/dev/null
DROP DATABASE IF EXISTS "${NELO_BD_NOM}" WITH (FORCE);
CREATE DATABASE "${NELO_BD_NOM}";
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'nelo_app') THEN
    CREATE ROLE nelo_app LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE PASSWORD 'nelo_app';
  END IF;
END
\$\$;
SQL

uv run alembic -c migrations/tenants/alembic.ini upgrade head

if [ "$avec_jeu_d_essai" -eq 1 ]; then
  uv run python -m scripts.jeu_essai
fi
