"""Toutes les fonctions d'accès aux données du module `tenants`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)` — elle n'en ouvre jamais. **Chaque fonction est exercée par la suite de
tests contre une base fraîchement migrée, ou la porte P-12 échoue en la nommant.**
"""

import uuid
from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.shared import Evenement
from modules.socle.tenants.tables import (
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


async def appeler_tenant_de_etablissement(
    connexion: AsyncConnection, etablissement_id: UUID
) -> UUID | None:
    return await connexion.scalar(select(func.tenants.tenant_de_etablissement(etablissement_id)))


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
    """L'établissement s'il est visible du tenant courant ; `None` sinon — inexistant ou d'un autre."""
    resultat = await connexion.execute(
        select(etablissement).where(etablissement.c.id == etablissement_id)
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


async def inserer_evenement(
    connexion: AsyncConnection, tenant_id: UUID, evenement: Evenement
) -> UUID:
    evenement_id = uuid.uuid7()
    await connexion.execute(
        insert(evenement_outbox).values(
            id=evenement_id, tenant_id=tenant_id, type=evenement.type, charge=evenement.charge
        )
    )
    return evenement_id


async def prendre_evenements(
    connexion: AsyncConnection, tenant_id: UUID, n: int
) -> list[RowMapping]:
    """Les `n` plus anciens événements en attente, verrouillés puis passés à `pris`, dans l'ordre.

    La sélection est une CTE `MATERIALIZED`, évaluée **une seule fois** : placée dans un
    `IN (SELECT … LIMIT n FOR UPDATE SKIP LOCKED)`, PostgreSQL peut la réévaluer selon le plan et
    passer à `pris` plus de `n` lignes — celles qu'on ne rend pas resteraient bloquées.
    """
    candidats = (
        select(evenement_outbox.c.id)
        .where(evenement_outbox.c.tenant_id == tenant_id, evenement_outbox.c.etat == "en_attente")
        .order_by(evenement_outbox.c.ecrit_le, evenement_outbox.c.id)
        .limit(n)
        .with_for_update(skip_locked=True)
        .cte("candidats")
        .prefix_with("MATERIALIZED")
    )
    resultat = await connexion.execute(
        update(evenement_outbox)
        .where(evenement_outbox.c.id == candidats.c.id)
        .values(etat="pris", pris_le=func.now())
        .returning(
            evenement_outbox.c.id,
            evenement_outbox.c.type,
            evenement_outbox.c.charge,
            evenement_outbox.c.ecrit_le,
        )
    )
    return sorted(resultat.mappings(), key=lambda e: (e["ecrit_le"], e["id"]))


async def marquer_traite(connexion: AsyncConnection, evenement_id: UUID) -> None:
    await connexion.execute(
        update(evenement_outbox)
        .where(evenement_outbox.c.id == evenement_id)
        .values(etat="traite", traite_le=func.now())
    )


async def marquer_echec(connexion: AsyncConnection, evenement_id: UUID, erreur: str) -> None:
    await connexion.execute(
        update(evenement_outbox)
        .where(evenement_outbox.c.id == evenement_id)
        .values(
            etat="en_echec",
            tentatives=evenement_outbox.c.tentatives + 1,
            derniere_erreur=erreur,
        )
    )


async def reprendre_pris_orphelins(
    connexion: AsyncConnection, tenant_id: UUID, delai: timedelta
) -> int:
    """Un `pris` dont le processus est mort repasse `en_attente` passé le délai : jamais perdu."""
    resultat = await connexion.execute(
        update(evenement_outbox)
        .where(
            evenement_outbox.c.tenant_id == tenant_id,
            evenement_outbox.c.etat == "pris",
            evenement_outbox.c.pris_le < func.now() - delai,
        )
        .values(etat="en_attente", pris_le=None)
    )
    return resultat.rowcount


async def reprendre_en_echec(connexion: AsyncConnection, tenant_id: UUID) -> int:
    resultat = await connexion.execute(
        update(evenement_outbox)
        .where(evenement_outbox.c.tenant_id == tenant_id, evenement_outbox.c.etat == "en_echec")
        .values(etat="en_attente", pris_le=None)
    )
    return resultat.rowcount
