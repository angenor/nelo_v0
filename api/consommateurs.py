"""L'aiguilleur du travailleur d'événements : qui traite quoi (research.md R-08).

Une fermeture, construite par la composition, qui reçoit les dépendances externes et les remet au
module propriétaire de l'événement. Ce n'est pas un bus : il n'y a ni registre global, ni
abonnement, ni découverte. Une ligne par type qui envoie un message, et le journal pour tout le
reste.

Livraison **au moins une fois** : un consommateur doit supporter de recevoir deux fois le même
événement. Celui de l'envoi le fait par construction, puisque le texte à envoyer est effacé après
le premier passage.
"""

import logging
from uuid import UUID

from modules.shared import Evenement
from modules.socle import habilitations

journal = logging.getLogger("nelo.travailleur")

# Les types dont le traitement est un envoi de message court. Les autres vont au journal :
# ce sont des faits, écrits pour être lus, pas pour déclencher quelque chose.
TYPES_D_ENVOI = frozenset(
    {
        "habilitations.otp.demande",
        "habilitations.compte.invite",
        "habilitations.identifiant.change",
    }
)


def aiguilleur(passerelle, valkey, configuration):
    """Rend le consommateur que le travailleur appelle pour chaque événement pris."""

    async def consommer(tenant_id: UUID, evenement_id: UUID, evenement: Evenement) -> None:
        if evenement.type in TYPES_D_ENVOI:
            await habilitations.consommer_envoi(
                tenant_id,
                evenement,
                passerelle,
                valkey,
                nom_produit=configuration.nom_produit,
                politique=habilitations.POLITIQUE,
                url_publique=configuration.url_publique,
            )
            return
        journal.info(
            "événement %s (%s) du tenant %s : %s",
            evenement.type,
            evenement_id,
            tenant_id,
            evenement.charge,
        )

    return consommer
