"""Toutes les fonctions d'accès aux données du module `tenants`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)`, elle n'en ouvre jamais. **Chaque fonction est exercée par la suite de
tests contre une base fraîchement migrée, ou la porte P-12 échoue en la nommant.**
"""

import uuid
from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.shared import Evenement, outbox
from modules.socle.tenants.tables import (
    country_pack,
    etablissement,
    evenement_outbox,
    parametre_catalogue,
    parametre_valeur,
    tenant,
)


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


async def appeler_tenants_pour_travailleur(connexion: AsyncConnection) -> list[UUID]:
    resultat = await connexion.execute(
        select(func.tenants.tenants_pour_travailleur().column_valued("tenant_id"))
    )
    return list(resultat.scalars())


async def lire_catalogue(connexion: AsyncConnection) -> list[RowMapping]:
    resultat = await connexion.execute(
        select(parametre_catalogue).order_by(parametre_catalogue.c.cle)
    )
    return list(resultat.mappings())


async def lire_valeurs_posees(
    connexion: AsyncConnection, tenant_id: UUID, cles: list[str]
) -> list[RowMapping]:
    resultat = await connexion.execute(
        select(
            parametre_valeur.c.cle,
            parametre_valeur.c.portee,
            parametre_valeur.c.portee_id,
            parametre_valeur.c.valeur,
        ).where(parametre_valeur.c.tenant_id == tenant_id, parametre_valeur.c.cle.in_(cles))
    )
    return list(resultat.mappings())


async def lire_etablissement(
    connexion: AsyncConnection, etablissement_id: UUID
) -> RowMapping | None:
    """L'établissement s'il est visible du tenant courant ; `None` sinon : inexistant ou d'un autre."""
    resultat = await connexion.execute(
        select(etablissement).where(etablissement.c.id == etablissement_id)
    )
    return resultat.mappings().one_or_none()


async def lire_etablissements_par_ids(
    connexion: AsyncConnection, ids: list[UUID]
) -> list[RowMapping]:
    """Les établissements visibles du tenant courant parmi ceux demandés, dans l'ordre du nom."""
    resultat = await connexion.execute(
        select(etablissement).where(etablissement.c.id.in_(ids)).order_by(etablissement.c.nom)
    )
    return list(resultat.mappings())


async def poser_administrateur(
    connexion: AsyncConnection, etablissement_id: UUID, compte_id: UUID | None
) -> int:
    """Désigne (ou retire) qui attribue ses domaines dans cet établissement."""
    resultat = await connexion.execute(
        update(etablissement)
        .where(etablissement.c.id == etablissement_id)
        .values(administrateur_compte_id=compte_id)
    )
    return resultat.rowcount


async def lire_pack(connexion: AsyncConnection, pays_code: str, version: int) -> RowMapping | None:
    """Un pack publié ; il n'appartient à aucun tenant, mais ne se lit que d'une transaction tenantée."""
    resultat = await connexion.execute(
        select(country_pack).where(
            country_pack.c.pays_code == pays_code, country_pack.c.version == version
        )
    )
    return resultat.mappings().one_or_none()


async def upsert_valeur(
    connexion: AsyncConnection,
    tenant_id: UUID,
    cle: str,
    portee: str,
    portee_id: UUID,
    valeur: bool | int | str,
) -> RowMapping:
    """La clé naturelle `(tenant_id, cle, portee, portee_id)` rend l'écriture idempotente par nature.

    Une table de *faits* (une présence, une note, un encaissement) porte en plus une colonne
    `cle_idempotence` et sa contrainte d'unicité `(tenant_id, cle_idempotence)` : les tranches qui
    en créent une la copient de là, pas d'ici (research.md R-06).
    """
    instruction = insert(parametre_valeur).values(
        id=uuid.uuid7(),
        tenant_id=tenant_id,
        cle=cle,
        portee=portee,
        portee_id=portee_id,
        valeur=valeur,
    )
    instruction = instruction.on_conflict_do_update(
        constraint="uq_valeur_cle_naturelle",
        set_={"valeur": instruction.excluded.valeur, "pose_le": func.now()},
    ).returning(
        parametre_valeur.c.cle,
        parametre_valeur.c.portee,
        parametre_valeur.c.portee_id,
        parametre_valeur.c.valeur,
        parametre_valeur.c.pose_le,
    )
    resultat = await connexion.execute(instruction)
    return resultat.mappings().one()


# L'outbox du module : les requêtes vivent dans `modules.shared.outbox`, paramétrées par la
# table ; ces fonctions les appellent sur celle de `tenants`, et rien d'autre.
async def inserer_evenement(
    connexion: AsyncConnection, tenant_id: UUID, evenement: Evenement
) -> UUID:
    return await outbox.inserer(connexion, evenement_outbox, tenant_id, evenement)


async def prendre_evenements(
    connexion: AsyncConnection, tenant_id: UUID, n: int
) -> list[RowMapping]:
    return await outbox.prendre(connexion, evenement_outbox, tenant_id, n)


async def reprendre_pris_orphelins(
    connexion: AsyncConnection, tenant_id: UUID, delai: timedelta
) -> int:
    return await outbox.reprendre_pris_orphelins(connexion, evenement_outbox, tenant_id, delai)


async def reprendre_en_echec(connexion: AsyncConnection, tenant_id: UUID) -> int:
    return await outbox.reprendre_en_echec(connexion, evenement_outbox, tenant_id)
