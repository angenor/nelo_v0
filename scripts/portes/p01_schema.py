"""PORTE P-01 — lecture du catalogue PostgreSQL de la base fraîchement migrée.

Échoue en **nommant la table** : RLS non activée ou non forcée, aucune politique, clé étrangère
vers un autre schéma, ou schéma de module sans dossier de migrations.
"""

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

RACINE = Path(__file__).resolve().parents[2]
SCHEMAS_SYSTEME = ("pg_catalog", "information_schema", "public", "pg_toast")
# La table de version d'Alembic vit dans le schéma du module ; elle n'est pas une table du produit.
HORS_PRODUIT = {"alembic_version"}


def echec(motif: str) -> None:
    print(f"PORTE P-01 ÉCHOUÉE : {motif}", file=sys.stderr)
    sys.exit(1)


async def inspecter() -> None:
    url = make_url(os.environ["NELO_BD_URL_PROPRIETAIRE"]).set(database=os.environ["NELO_BD_NOM"])
    moteur = create_async_engine(url)
    async with moteur.connect() as connexion:
        schemas = list(
            (
                await connexion.execute(
                    text(
                        "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\\_%' "
                        "AND nspname <> ALL(:systeme) ORDER BY nspname"
                    ),
                    {"systeme": list(SCHEMAS_SYSTEME)},
                )
            ).scalars()
        )
        tables = (
            await connexion.execute(
                text(
                    "SELECT n.nspname, c.relname, c.relrowsecurity, c.relforcerowsecurity, "
                    "(SELECT count(*) FROM pg_policies p "
                    " WHERE p.schemaname = n.nspname AND p.tablename = c.relname) "
                    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE c.relkind IN ('r', 'p') AND n.nspname = ANY(:schemas) "
                    "ORDER BY n.nspname, c.relname"
                ),
                {"schemas": schemas},
            )
        ).all()
        traversantes = (
            await connexion.execute(
                text(
                    "SELECT con.conname, sn.nspname, sc.relname, tn.nspname, tc.relname "
                    "FROM pg_constraint con "
                    "JOIN pg_class sc ON sc.oid = con.conrelid JOIN pg_namespace sn ON sn.oid = sc.relnamespace "
                    "JOIN pg_class tc ON tc.oid = con.confrelid JOIN pg_namespace tn ON tn.oid = tc.relnamespace "
                    "WHERE con.contype = 'f' AND sn.nspname = ANY(:schemas) AND sn.nspname <> tn.nspname"
                ),
                {"schemas": schemas},
            )
        ).all()
    await moteur.dispose()

    if not schemas:
        echec("aucun schéma de module inspecté")
    for schema in schemas:
        if not (RACINE / "migrations" / schema).is_dir():
            echec(f"le schéma {schema} n'a pas de dossier migrations/{schema}/")

    inspectees = [t for t in tables if t[1] not in HORS_PRODUIT]
    if not inspectees:
        echec("aucune table inspectée")
    politiques = 0
    for schema, nom, active, forcee, nb_politiques in inspectees:
        if not active:
            echec(f"{schema}.{nom} : ROW LEVEL SECURITY non activée")
        if not forcee:
            echec(f"{schema}.{nom} : ROW LEVEL SECURITY non forcée")
        if nb_politiques == 0:
            echec(f"{schema}.{nom} : aucune politique")
        politiques += nb_politiques
    for contrainte, s_schema, s_table, c_schema, c_table in traversantes:
        echec(
            f"{s_schema}.{s_table} : la clé étrangère {contrainte} traverse vers {c_schema}.{c_table}"
        )

    print(
        f"PORTE P-01 : {len(inspectees)} tables, {politiques} politiques, "
        f"0 clé étrangère traversante"
    )


if __name__ == "__main__":
    asyncio.run(inspecter())
