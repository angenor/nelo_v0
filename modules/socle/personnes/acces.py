"""Toutes les fonctions d'accès aux données du module `personnes`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)`, elle n'en ouvre jamais. **Chaque fonction est exercée par la suite
de tests contre une base fraîchement migrée, ou la porte P-12 échoue en la nommant.**
"""

from uuid import UUID

from sqlalchemy import RowMapping, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.socle.personnes.tables import personne


async def inserer_personne(
    connexion: AsyncConnection,
    personne_id: UUID,
    tenant_id: UUID,
    nom: str,
    prenoms: str,
    langue_preferee: str,
    telephone_principal: str | None,
) -> None:
    await connexion.execute(
        insert(personne).values(
            id=personne_id,
            tenant_id=tenant_id,
            nom=nom,
            prenoms=prenoms,
            langue_preferee=langue_preferee,
            telephone_principal=telephone_principal,
        )
    )


async def lire_personne(
    connexion: AsyncConnection, tenant_id: UUID, personne_id: UUID
) -> RowMapping | None:
    """La personne si elle appartient au tenant courant ; `None` sinon : inexistante ou d'un autre.

    Le `tenant_id` est redit dans la clause, alors que la RLS le pose déjà : double barrière
    (règle 5), jamais une seule.
    """
    resultat = await connexion.execute(
        select(personne).where(personne.c.tenant_id == tenant_id, personne.c.id == personne_id)
    )
    return resultat.mappings().one_or_none()


async def lire_personnes(
    connexion: AsyncConnection, tenant_id: UUID, personne_ids: list[UUID]
) -> list[RowMapping]:
    """Les personnes du tenant parmi les identifiants demandés ; les inconnues sont absentes."""
    resultat = await connexion.execute(
        select(personne).where(personne.c.tenant_id == tenant_id, personne.c.id.in_(personne_ids))
    )
    return list(resultat.mappings())
