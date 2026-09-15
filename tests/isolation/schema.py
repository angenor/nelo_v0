"""Les tables du schéma `tenants`, énumérées depuis la base — jamais depuis une liste écrite."""

from sqlalchemy import column, func, select, table, text
from sqlalchemy.ext.asyncio import AsyncConnection

SCHEMA = "tenants"
# La table de version d'Alembic vit dans le schéma du module ; elle n'est pas une table du produit.
HORS_PRODUIT = {"alembic_version"}


async def tables_du_schema(connexion: AsyncConnection) -> list[str]:
    resultat = await connexion.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_type = 'BASE TABLE' ORDER BY table_name"
        ),
        {"schema": SCHEMA},
    )
    noms = [n for n in resultat.scalars() if n not in HORS_PRODUIT]
    assert noms, "aucune table inspectée"
    return noms


def compter(nom: str, *filtre):
    requete = select(func.count()).select_from(table(nom, schema=SCHEMA))
    return requete.where(*filtre) if filtre else requete


def colonne(nom: str):
    return column(nom)
