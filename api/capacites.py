"""Le point d'insertion de la vérification de capacité.

**Point d'insertion vide jusqu'à T1b**, jamais retiré : chaque route d'écriture l'appelle avec le
code de capacité qu'elle exige. En T0a, il journalise le code et laisse passer ; T1b le remplit.
"""

import logging

journal = logging.getLogger("nelo.capacites")


def exiger_capacite(code: str) -> None:
    journal.info("capacite exigée : %s", code)
