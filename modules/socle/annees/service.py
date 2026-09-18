"""Le service du module `annees` : des fonctions, une transaction par opération, des accès nommés.

Le noyau de T1a : lire les années d'un établissement, retrouver l'établissement d'une année, en
créer une pour les seeds et les tests. **Aucune transition** : ni ouverture, ni activation, ni
clôture ; T2a livre le cycle de vie de docs/02-domaine.md § 4.
"""

import uuid
from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError

from modules.shared import ErreurMetier, transaction
from modules.socle.annees import acces
from modules.socle.annees.schemas import Annee, EtatAnnee

# Les deux index partiels de la table portent l'invariant de docs/02-domaine.md § 4.5 : au plus
# une année active et une en préparation par établissement. La base refuse, le service traduit.
INDEX_UNICITE = {"uq_annee_active": "active", "uq_annee_preparation": "preparation"}


async def creer_annee(
    tenant_id: UUID,
    etablissement_id: UUID,
    libelle: str,
    debut: date,
    fin: date,
    etat: EtatAnnee,
) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T1a. Rend l'identifiant créé."""
    annee_id = uuid.uuid7()
    try:
        async with transaction(tenant_id) as connexion:
            await acces.inserer_annee(
                connexion, annee_id, tenant_id, etablissement_id, libelle, debut, fin, etat
            )
    except IntegrityError as erreur:
        etat_en_double = _etat_en_double(erreur)
        if etat_en_double is None:
            raise
        raise ErreurMetier(
            "ANN_ANNEE_ACTIVE_UNIQUE",
            f"l'établissement a déjà une année en état {etat_en_double}",
            statut=409,
            champ="etat",
            details={"etat": etat_en_double, "etablissement_id": str(etablissement_id)},
        ) from erreur
    return annee_id


def _etat_en_double(erreur: IntegrityError) -> str | None:
    """L'état dont l'unicité est violée, ou `None` si la violation est d'une autre nature."""
    texte = str(erreur.orig)
    return next((etat for index, etat in INDEX_UNICITE.items() if index in texte), None)


async def lire_annees(tenant_id: UUID, etablissement_id: UUID) -> list[Annee]:
    """Les années de l'établissement, de la plus récente à la plus ancienne."""
    async with transaction(tenant_id) as connexion:
        lignes = await acces.lire_annees_etablissement(connexion, tenant_id, etablissement_id)
    return [Annee(id=ligne["id"], libelle=ligne["libelle"], etat=ligne["etat"]) for ligne in lignes]


async def etablissement_de_annee(tenant_id: UUID, annee_id: UUID) -> UUID | None:
    """L'établissement de l'année ; `None` si l'année est inconnue du tenant.

    Ce que l'affectation copie (research.md R-03), et ce que le middleware d'année vérifie.
    """
    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_annee(connexion, tenant_id, annee_id)
    return ligne["etablissement_id"] if ligne is not None else None
