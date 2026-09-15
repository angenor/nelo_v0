"""Le contrat d'un événement outbox.

`shared` ne porte pas de bus : chaque module écrit ses événements dans la table `evenement_outbox`
de son propre schéma, dans la transaction du changement d'état.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Evenement:
    type: str
    charge: dict[str, Any]
