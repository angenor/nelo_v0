"""L'outbox, une seule fois : la prise, le marquage et la reprise, paramétrés par la table.

Chaque module porte sa propre table `evenement_outbox`, copie conforme de celle de `tenants`. Les
tables se copient, les requêtes non : elles vivent ici, et chaque module les appelle sur sa
`Table` SQLAlchemy. Les fonctions d'accès n'ouvrent aucune transaction : elles reçoivent une
connexion ouverte par `transaction(tenant_id)`, comme toute fonction d'accès.

`consommer_lot` fait exception, et c'est son objet : il **ordonne** les transactions d'un tour de
travailleur, une par étape, pour qu'un événement passé au consommateur soit marqué même si le
consommateur a été long. C'est le seul ordonnanceur, et il est ici pour n'exister qu'une fois.

Ce module n'est pas exporté par `modules.shared` : on l'importe par son chemin,
`modules.shared.outbox`, pour que l'appel se voie.
"""

import uuid
from collections.abc import Awaitable, Callable
from datetime import timedelta
from uuid import UUID

from sqlalchemy import RowMapping, Table, func, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.shared.bd import transaction
from modules.shared.evenement import Evenement

# Ce qu'un consommateur d'événements reçoit : le tenant, l'identifiant de l'événement, l'événement.
type Consommateur = Callable[[UUID, UUID, Evenement], Awaitable[None]]


async def inserer(
    connexion: AsyncConnection, table: Table, tenant_id: UUID, evenement: Evenement
) -> UUID:
    """L'événement du changement d'état, écrit dans la transaction qui le produit (règle 10)."""
    evenement_id = uuid.uuid7()
    await connexion.execute(
        insert(table).values(
            id=evenement_id, tenant_id=tenant_id, type=evenement.type, charge=evenement.charge
        )
    )
    return evenement_id


async def prendre(
    connexion: AsyncConnection, table: Table, tenant_id: UUID, n: int
) -> list[RowMapping]:
    """Les `n` plus anciens événements en attente, verrouillés puis passés à `pris`, dans l'ordre.

    La sélection est une CTE `MATERIALIZED`, évaluée **une seule fois** : placée dans un
    `IN (SELECT ... LIMIT n FOR UPDATE SKIP LOCKED)`, PostgreSQL peut la réévaluer selon le plan et
    passer à `pris` plus de `n` lignes ; celles qu'on ne rend pas resteraient bloquées.
    """
    candidats = (
        select(table.c.id)
        .where(table.c.tenant_id == tenant_id, table.c.etat == "en_attente")
        .order_by(table.c.ecrit_le, table.c.id)
        .limit(n)
        .with_for_update(skip_locked=True)
        .cte("candidats")
        .prefix_with("MATERIALIZED")
    )
    resultat = await connexion.execute(
        update(table)
        .where(table.c.id == candidats.c.id)
        .values(etat="pris", pris_le=func.now())
        .returning(table.c.id, table.c.type, table.c.charge, table.c.ecrit_le)
    )
    return sorted(resultat.mappings(), key=lambda e: (e["ecrit_le"], e["id"]))


async def marquer_traite(connexion: AsyncConnection, table: Table, evenement_id: UUID) -> None:
    await connexion.execute(
        update(table).where(table.c.id == evenement_id).values(etat="traite", traite_le=func.now())
    )


async def marquer_echec(
    connexion: AsyncConnection, table: Table, evenement_id: UUID, erreur: str
) -> None:
    await connexion.execute(
        update(table)
        .where(table.c.id == evenement_id)
        .values(etat="en_echec", tentatives=table.c.tentatives + 1, derniere_erreur=erreur)
    )


async def reprendre_pris_orphelins(
    connexion: AsyncConnection, table: Table, tenant_id: UUID, delai: timedelta
) -> int:
    """Un `pris` dont le processus est mort repasse `en_attente` passé le délai : jamais perdu."""
    resultat = await connexion.execute(
        update(table)
        .where(
            table.c.tenant_id == tenant_id,
            table.c.etat == "pris",
            table.c.pris_le < func.now() - delai,
        )
        .values(etat="en_attente", pris_le=None)
    )
    return resultat.rowcount


async def reprendre_en_echec(connexion: AsyncConnection, table: Table, tenant_id: UUID) -> int:
    resultat = await connexion.execute(
        update(table)
        .where(table.c.tenant_id == tenant_id, table.c.etat == "en_echec")
        .values(etat="en_attente", pris_le=None)
    )
    return resultat.rowcount


async def consommer_lot(tenant_id: UUID, table: Table, consommateur: Consommateur, n: int) -> int:
    """Jusqu'à `n` événements du tenant, un par un, dans l'ordre d'écriture.

    Chaque événement est pris dans sa transaction, passé au consommateur **hors** transaction,
    puis marqué dans une autre : un consommateur qui appelle une passerelle ne tient pas une
    transaction ouverte pendant ce temps. Au premier échec, le lot s'arrête : l'événement suivant
    ne passe pas devant celui qui a échoué, qui sera repris au tour suivant. Rend le nombre
    d'événements traités.
    """
    traites = 0
    for _ in range(n):
        async with transaction(tenant_id) as connexion:
            pris = await prendre(connexion, table, tenant_id, 1)
        if not pris:
            break
        ligne = pris[0]
        try:
            await consommateur(tenant_id, ligne["id"], Evenement(ligne["type"], ligne["charge"]))
        except Exception as erreur:
            async with transaction(tenant_id) as connexion:
                await marquer_echec(
                    connexion, table, ligne["id"], f"{type(erreur).__name__} : {erreur}"[:500]
                )
            break
        async with transaction(tenant_id) as connexion:
            await marquer_traite(connexion, table, ligne["id"])
        traites += 1
    return traites
