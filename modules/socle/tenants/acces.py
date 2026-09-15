"""Toutes les fonctions d'accès aux données du module `tenants`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)` — elle n'en ouvre jamais. **Chaque fonction est exercée par la suite de
tests contre une base fraîchement migrée, ou la porte P-12 échoue en la nommant.**
"""

from uuid import UUID

from sqlalchemy import func, insert, select
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.socle.tenants.tables import etablissement, tenant


async def inserer_tenant(
    connexion: AsyncConnection,
    tenant_id: UUID,
    nom: str,
    pays_code: str,
    country_pack_version: int,
    raison_sociale: str | None,
) -> None:
    await connexion.execute(
        insert(tenant).values(
            id=tenant_id,
            nom=nom,
            pays_code=pays_code,
            country_pack_version=country_pack_version,
            raison_sociale=raison_sociale,
        )
    )


async def inserer_etablissement(
    connexion: AsyncConnection,
    etablissement_id: UUID,
    tenant_id: UUID,
    nom: str,
    fuseau_horaire: str,
) -> None:
    await connexion.execute(
        insert(etablissement).values(
            id=etablissement_id, tenant_id=tenant_id, nom=nom, fuseau_horaire=fuseau_horaire
        )
    )


async def appeler_tenant_de_etablissement(
    connexion: AsyncConnection, etablissement_id: UUID
) -> UUID | None:
    return await connexion.scalar(select(func.tenants.tenant_de_etablissement(etablissement_id)))


async def appeler_tenants_pour_travailleur(connexion: AsyncConnection) -> list[UUID]:
    resultat = await connexion.execute(
        select(func.tenants.tenants_pour_travailleur().column_valued("tenant_id"))
    )
    return list(resultat.scalars())
