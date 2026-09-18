"""Toutes les fonctions d'accès aux données du module `habilitations`.

SQLAlchemy Core, valeurs liées, aucune concaténation. Chaque fonction reçoit une connexion ouverte
par `transaction(tenant_id)`, ou par `sans_tenant()` pour les trois fonctions `SECURITY DEFINER` ;
elle n'en ouvre jamais. **Chaque fonction est exercée par la suite de tests contre une base
fraîchement migrée, ou la porte P-12 échoue en la nommant.**

Les trois appels `SECURITY DEFINER` répondent **avant que le tenant ne soit connu** : un numéro,
un lien ou un appareil ne disent pas de quel tenant ils relèvent. Ils ne rendent que des
identifiants et un statut.
"""

from datetime import date, datetime, timedelta
from uuid import UUID

from sqlalchemy import RowMapping, and_, func, or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncConnection

from modules.shared import Evenement
from modules.shared import outbox as outbox_partagee
from modules.socle.habilitations.tables import affectation, compte, evenement_outbox

# --- Le compte ---------------------------------------------------------------------------------


async def inserer_compte(
    connexion: AsyncConnection,
    compte_id: UUID,
    tenant_id: UUID,
    personne_id: UUID,
    identifiant: str,
    statut: str,
) -> None:
    await connexion.execute(
        insert(compte).values(
            id=compte_id,
            tenant_id=tenant_id,
            personne_id=personne_id,
            identifiant=identifiant,
            statut=statut,
        )
    )


async def lire_compte(connexion: AsyncConnection, compte_id: UUID) -> RowMapping | None:
    """Le compte s'il est visible du tenant courant ; `None` sinon, inexistant ou d'un autre."""
    resultat = await connexion.execute(select(compte).where(compte.c.id == compte_id))
    return resultat.mappings().one_or_none()


async def lire_compte_par_personne(
    connexion: AsyncConnection, personne_id: UUID
) -> RowMapping | None:
    resultat = await connexion.execute(select(compte).where(compte.c.personne_id == personne_id))
    return resultat.mappings().one_or_none()


async def compter_meme_identifiant(connexion: AsyncConnection, identifiant: str) -> int:
    """Combien de comptes du tenant courant portent ce numéro : la règle de partage s'en déduit."""
    return int(
        await connexion.scalar(
            select(func.count()).select_from(compte).where(compte.c.identifiant == identifiant)
        )
    )


async def poser_statut(connexion: AsyncConnection, compte_id: UUID, statut: str) -> None:
    await connexion.execute(update(compte).where(compte.c.id == compte_id).values(statut=statut))


async def poser_derniere_connexion(connexion: AsyncConnection, compte_id: UUID) -> None:
    await connexion.execute(
        update(compte).where(compte.c.id == compte_id).values(derniere_connexion=func.now())
    )


async def lire_statut(connexion: AsyncConnection, compte_id: UUID) -> str | None:
    return await connexion.scalar(select(compte.c.statut).where(compte.c.id == compte_id))


async def poser_pin(connexion: AsyncConnection, compte_id: UUID, empreinte: str) -> None:
    """L'empreinte Argon2id du code personnel. Le code en clair n'entre nulle part, et le verrou
    tombe : définir un code, c'est repartir de zéro."""
    await connexion.execute(
        update(compte)
        .where(compte.c.id == compte_id)
        .values(pin_empreinte=empreinte, pin_verrouille_le=None)
    )


async def poser_verrou_pin(
    connexion: AsyncConnection, compte_id: UUID, verrouille_le: datetime | None
) -> None:
    """Le verrou **durable** des cinq codes faux : une perte du magasin éphémère ne le lève pas."""
    await connexion.execute(
        update(compte).where(compte.c.id == compte_id).values(pin_verrouille_le=verrouille_le)
    )


async def poser_invitation(
    connexion: AsyncConnection,
    compte_id: UUID,
    empreinte: str | None,
    expire_le: datetime | None,
    invite_le: datetime | None,
) -> None:
    """Le lien en cours, par son empreinte. `None` l'efface : un lien consommé ne vaut plus rien."""
    await connexion.execute(
        update(compte)
        .where(compte.c.id == compte_id)
        .values(
            invitation_empreinte=empreinte,
            invitation_expire_le=expire_le,
            invite_le=invite_le,
        )
    )


async def poser_identifiant(connexion: AsyncConnection, compte_id: UUID, identifiant: str) -> None:
    await connexion.execute(
        update(compte).where(compte.c.id == compte_id).values(identifiant=identifiant)
    )


# --- Les trois fonctions qui répondent avant tout tenant ---------------------------------------


async def appeler_comptes_par_identifiant(
    connexion: AsyncConnection, identifiant: str
) -> list[RowMapping]:
    """Les comptes qui portent ce numéro, **tous tenants confondus**. Sur `sans_tenant()`."""
    resultat = await connexion.execute(
        select("*").select_from(func.habilitations.comptes_par_identifiant(identifiant))
    )
    return list(resultat.mappings())


async def appeler_compte_par_invitation(
    connexion: AsyncConnection, empreinte: str
) -> RowMapping | None:
    resultat = await connexion.execute(
        select("*").select_from(func.habilitations.compte_par_invitation(empreinte))
    )
    return resultat.mappings().one_or_none()


# --- L'affectation : ce que les deux middlewares lisent à chaque requête ------------------------


async def inserer_affectation(
    connexion: AsyncConnection,
    affectation_id: UUID,
    tenant_id: UUID,
    compte_id: UUID,
    annee_id: UUID,
    etablissement_id: UUID,
    debut: date,
    fin: date | None,
) -> None:
    await connexion.execute(
        insert(affectation).values(
            id=affectation_id,
            tenant_id=tenant_id,
            compte_id=compte_id,
            annee_id=annee_id,
            etablissement_id=etablissement_id,
            debut=debut,
            fin=fin,
        )
    )


def _vivante(aujourd_hui: date):
    """Commencée, pas encore finie. `fin` est exclue : le dernier jour est `fin - 1`."""
    return and_(
        affectation.c.debut <= aujourd_hui,
        or_(affectation.c.fin.is_(None), affectation.c.fin > aujourd_hui),
    )


async def affectation_vivante(
    connexion: AsyncConnection,
    compte_id: UUID,
    etablissement_id: UUID,
    annee_id: UUID | None,
    aujourd_hui: date,
) -> bool:
    """Le compte est-il rattaché à cet établissement, à cette date, et pour cette année ?"""
    filtres = [
        affectation.c.compte_id == compte_id,
        affectation.c.etablissement_id == etablissement_id,
        _vivante(aujourd_hui),
    ]
    if annee_id is not None:
        filtres.append(affectation.c.annee_id == annee_id)
    return (
        await connexion.scalar(
            select(func.count()).select_from(affectation).where(*filtres).limit(1)
        )
    ) > 0


async def lire_rattachements(
    connexion: AsyncConnection, compte_id: UUID, aujourd_hui: date
) -> list[RowMapping]:
    """Les couples (établissement, année) des affectations vivantes ; le contexte en dérive."""
    resultat = await connexion.execute(
        select(affectation.c.etablissement_id, affectation.c.annee_id)
        .where(affectation.c.compte_id == compte_id, _vivante(aujourd_hui))
        .order_by(affectation.c.etablissement_id, affectation.c.annee_id)
    )
    return list(resultat.mappings())


# --- L'outbox du module, sur la table du module ------------------------------------------------


async def inserer_evenement(
    connexion: AsyncConnection, tenant_id: UUID, evenement: Evenement
) -> UUID:
    return await outbox_partagee.inserer(connexion, evenement_outbox, tenant_id, evenement)


async def reprendre_pris_orphelins(
    connexion: AsyncConnection, tenant_id: UUID, delai: timedelta
) -> int:
    return await outbox_partagee.reprendre_pris_orphelins(
        connexion, evenement_outbox, tenant_id, delai
    )


async def reprendre_en_echec(connexion: AsyncConnection, tenant_id: UUID) -> int:
    return await outbox_partagee.reprendre_en_echec(connexion, evenement_outbox, tenant_id)
