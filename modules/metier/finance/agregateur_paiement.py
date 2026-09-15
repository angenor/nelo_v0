"""L'agrégateur de paiement — l'interface dessinée pour un fournisseur réel, et sa simulation.

Chez un agrégateur de mobile money, l'initiation rend un identifiant de transaction ; la
confirmation arrive par webhook. **Le webhook qui n'arrive jamais est le cas nominal** (ADR 009).
Le montant est un entier d'unité mineure, l'exposant appartient à la devise (règle 2). T8b
remplace la simulation.
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal, Protocol
from uuid import UUID

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.shared.simulation import AccusesSimules


@dataclass(frozen=True, slots=True)
class ReferencePaiement:
    reference: UUID
    identifiant_fournisseur: str


@dataclass(frozen=True, slots=True)
class ConfirmationPaiement:
    reference: ReferencePaiement
    statut: Literal["CONFIRME", "REFUSE"]
    montant_unite_mineure: int
    devise: str


class AgregateurPaiement(Protocol):
    async def initier(
        self, montant_unite_mineure: int, devise: str, reference: UUID, payeur_e164: str
    ) -> ReferencePaiement:
        """Fournisseur réel : initiation d'un paiement mobile → identifiant de transaction. Le montant
        est un entier d'unité mineure, l'exposant appartient à la devise (R2)."""
        ...

    async def attendre_confirmation(
        self, reference: ReferencePaiement, delai_max: timedelta
    ) -> ConfirmationPaiement | None:
        """Fournisseur réel : webhook de confirmation. None à l'échéance — le webhook qui n'arrive jamais
        est le cas nominal (ADR 009)."""
        ...


class SimulationAgregateurPaiement:
    def __init__(self, mode: ModeSimulation, delai: timedelta) -> None:
        self.mode = mode
        self._confirmations: AccusesSimules[ConfirmationPaiement] = AccusesSimules(mode, delai)

    async def initier(
        self, montant_unite_mineure: int, devise: str, reference: UUID, payeur_e164: str
    ) -> ReferencePaiement:
        if not isinstance(montant_unite_mineure, int) or isinstance(montant_unite_mineure, bool):
            raise TypeError("le montant est un entier d'unité mineure, jamais un flottant")
        if self.mode == ModeSimulation.INDISPONIBLE:
            raise DependanceIndisponible("AGREGATEUR_PAIEMENT")
        paiement = ReferencePaiement(reference, f"simulation-{reference}")
        self._confirmations.annoncer(
            paiement, ConfirmationPaiement(paiement, "CONFIRME", montant_unite_mineure, devise)
        )
        return paiement

    async def attendre_confirmation(
        self, reference: ReferencePaiement, delai_max: timedelta
    ) -> ConfirmationPaiement | None:
        return await self._confirmations.attendre(reference, delai_max)
