"""Les tables des schémas du produit, énumérées depuis la base, jamais depuis une liste écrite.

Une liste tenue à la main vieillit : une table ajoutée par une migration sans politique de
sécurité au niveau ligne n'y figurerait pas, et le test d'isolation la laisserait passer sans un
mot. Ici, c'est le catalogue de PostgreSQL qui dit ce qui existe, schéma par schéma (FR-045).
"""

from sqlalchemy import column, func, select, table, text
from sqlalchemy.ext.asyncio import AsyncConnection

# Les quatre schémas migrés, dans l'ordre des noyaux puis de ce qui les référence.
SCHEMAS = ("tenants", "personnes", "annees", "habilitations")
# Le schéma inspecté quand aucun n'est nommé : celui du module doré, le seul que les suites de
# T0a regardent.
SCHEMA = SCHEMAS[0]
# La table de version d'Alembic vit dans le schéma du module ; elle n'est pas une table du produit.
HORS_PRODUIT = {"alembic_version"}


async def tables_du_schema(connexion: AsyncConnection, schema: str = SCHEMA) -> list[str]:
    resultat = await connexion.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = :schema AND table_type = 'BASE TABLE' ORDER BY table_name"
        ),
        {"schema": schema},
    )
    noms = [n for n in resultat.scalars() if n not in HORS_PRODUIT]
    assert noms, f"aucune table inspectée dans le schéma {schema}"
    return noms


def compter(nom: str, *filtre, schema: str = SCHEMA):
    requete = select(func.count()).select_from(table(nom, schema=schema))
    return requete.where(*filtre) if filtre else requete


def colonne(nom: str):
    return column(nom)
