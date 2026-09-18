"""Le service du module `personnes` : des fonctions, une transaction par opération, des accès nommés.

Le noyau de T1a : lire une identité, en lire plusieurs, en créer une pour les seeds et les tests.
Aucune route ne l'expose ici ; T3a livre le dossier de la personne et son cycle de vie.
"""

import re
import uuid
from uuid import UUID

from modules.shared import ErreurMetier, transaction
from modules.socle.personnes import acces
from modules.socle.personnes.schemas import MOTIF_LANGUE, Identite

_LANGUE = re.compile(MOTIF_LANGUE)


async def creer_personne(
    tenant_id: UUID,
    nom: str,
    prenoms: str,
    langue: str,
    telephone: str | None = None,
) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T1a. Rend l'identifiant créé."""
    if _LANGUE.match(langue) is None:
        raise ErreurMetier(
            "VAL_SCHEMA_INVALIDE",
            "la langue préférée n'est pas un code de deux lettres minuscules",
            champ="langue",
            details={"motif": MOTIF_LANGUE},
        )
    personne_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_personne(
            connexion, personne_id, tenant_id, nom, prenoms, langue, telephone
        )
    return personne_id


async def lire_identite(tenant_id: UUID, personne_id: UUID) -> Identite | None:
    """Nom, prénoms et langue ; `None` si la personne est inconnue du tenant."""
    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_personne(connexion, tenant_id, personne_id)
    return _identite(ligne) if ligne is not None else None


async def lire_identites(tenant_id: UUID, personne_ids: list[UUID]) -> dict[UUID, Identite]:
    """Les identités trouvées, par identifiant ; une personne inconnue est simplement absente."""
    if not personne_ids:
        return {}
    async with transaction(tenant_id) as connexion:
        lignes = await acces.lire_personnes(connexion, tenant_id, personne_ids)
    return {ligne["id"]: _identite(ligne) for ligne in lignes}


def _identite(ligne) -> Identite:
    return Identite(nom=ligne["nom"], prenoms=ligne["prenoms"], langue=ligne["langue_preferee"])
