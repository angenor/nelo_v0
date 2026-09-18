"""Toutes les fonctions d'accès aux données du module `annees`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)`, elle n'en ouvre jamais. **Chaque fonction est exercée par la suite
de tests contre une base fraîchement migrée, ou la porte P-12 échoue en la nommant.**
"""

from datetime import date
from uuid import UUID

from sqlalchemy import RowMapping, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.socle.annees.tables import annee_scolaire


async def inserer_annee(
    connexion: AsyncConnection,
    annee_id: UUID,
    tenant_id: UUID,
    etablissement_id: UUID,
    libelle: str,
    debut: date,
    fin: date,
    etat: str,
) -> None:
    await connexion.execute(
        insert(annee_scolaire).values(
            id=annee_id,
            tenant_id=tenant_id,
            etablissement_id=etablissement_id,
            libelle=libelle,
            debut=debut,
            fin=fin,
            etat=etat,
        )
    )


async def lire_annees_etablissement(
    connexion: AsyncConnection, tenant_id: UUID, etablissement_id: UUID
) -> list[RowMapping]:
    """Les années de l'établissement, de la plus récente à la plus ancienne.

    Le `tenant_id` est redit dans la clause, alors que la RLS le pose déjà : double barrière
    (règle 5), jamais une seule.
    """
    resultat = await connexion.execute(
        select(annee_scolaire)
        .where(
            annee_scolaire.c.tenant_id == tenant_id,
            annee_scolaire.c.etablissement_id == etablissement_id,
        )
        .order_by(annee_scolaire.c.debut.desc(), annee_scolaire.c.id)
    )
    return list(resultat.mappings())


async def lire_annee(
    connexion: AsyncConnection, tenant_id: UUID, annee_id: UUID
) -> RowMapping | None:
    """L'année si elle appartient au tenant courant ; `None` sinon : inexistante ou d'un autre."""
    resultat = await connexion.execute(
        select(annee_scolaire).where(
            annee_scolaire.c.tenant_id == tenant_id, annee_scolaire.c.id == annee_id
        )
    )
    return resultat.mappings().one_or_none()
