"""La passerelle SMS — l'interface dessinée pour un fournisseur réel, et sa simulation.

Le SMS est un canal de premier rang (constitution, XIII). Chez un fournisseur réel, la soumission
rend un identifiant tout de suite, et le rapport de remise (DLR) arrive **plus tard** par webhook —
en retard, en double, ou jamais. T4a remplace la simulation ; ce sera un remplacement, pas une
découverte.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, Protocol
from uuid import UUID

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.shared.simulation import AccusesSimules


@dataclass(frozen=True, slots=True)
class ReferenceEnvoi:
    reference: UUID
    identifiant_fournisseur: str


@dataclass(frozen=True, slots=True)
class AccuseSms:
    reference: ReferenceEnvoi
    statut: Literal["REMIS", "NON_REMIS"]


class PasserelleSms(Protocol):
    async def envoyer(self, destinataire_e164: str, texte: str, reference: UUID) -> ReferenceEnvoi:
        """Fournisseur réel : soumission d'un message (ex. POST /messages) → identifiant fournisseur."""
        ...

    async def attendre_accuse(
        self, reference: ReferenceEnvoi, delai_max: timedelta
    ) -> AccuseSms | None:
        """Fournisseur réel : rapport de remise reçu par webhook (DLR). None à l'échéance — jamais de blocage."""
        ...


class SimulationPasserelleSms:
    def __init__(self, mode: ModeSimulation, delai: timedelta) -> None:
        self.mode = mode
        self._accuses: AccusesSimules[AccuseSms] = AccusesSimules(mode, delai)

    async def envoyer(self, destinataire_e164: str, texte: str, reference: UUID) -> ReferenceEnvoi:
        if self.mode == ModeSimulation.INDISPONIBLE:
            raise DependanceIndisponible("PASSERELLE_SMS")
        envoi = ReferenceEnvoi(reference, f"simulation-{reference}")
        self._accuses.annoncer(envoi, AccuseSms(envoi, "REMIS"))
        return envoi

    async def attendre_accuse(
        self, reference: ReferenceEnvoi, delai_max: timedelta
    ) -> AccuseSms | None:
        return await self._accuses.attendre(reference, delai_max)
