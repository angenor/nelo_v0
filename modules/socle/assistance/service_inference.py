"""Le service d'inférence — l'interface dessinée pour un fournisseur réel, et sa simulation.

Ce n'est **pas un service de la composition** : c'est une dépendance externe comme les autres, et
cette abstraction est sa seule existence en T0a (FR-002, ADR 017).
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Protocol
from uuid import UUID, uuid7

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.shared.simulation import AccusesSimules


@dataclass(frozen=True, slots=True)
class RequeteInference:
    capacite: str
    entree: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReferenceInference:
    reference: UUID


@dataclass(frozen=True, slots=True)
class ResultatInference:
    reference: ReferenceInference
    sortie: dict[str, Any]


class ServiceInference(Protocol):
    async def soumettre(self, requete: RequeteInference) -> ReferenceInference:
        """Fournisseur réel : création d'une complétion ou d'un lot → identifiant."""
        ...

    async def attendre_resultat(
        self, reference: ReferenceInference, delai_max: timedelta
    ) -> ResultatInference | None:
        """Fournisseur réel : lecture du résultat. Un fournisseur synchrone est servi en rendant le résultat
        dès le premier appel ; un fournisseur par lot est servi tel quel. None à l'échéance."""
        ...


class SimulationServiceInference:
    def __init__(self, mode: ModeSimulation, delai: timedelta) -> None:
        self.mode = mode
        self._resultats: AccusesSimules[ResultatInference] = AccusesSimules(mode, delai)

    async def soumettre(self, requete: RequeteInference) -> ReferenceInference:
        if self.mode == ModeSimulation.INDISPONIBLE:
            raise DependanceIndisponible("SERVICE_INFERENCE")
        reference = ReferenceInference(uuid7())
        self._resultats.annoncer(reference, ResultatInference(reference, {"simulation": True}))
        return reference

    async def attendre_resultat(
        self, reference: ReferenceInference, delai_max: timedelta
    ) -> ResultatInference | None:
        return await self._resultats.attendre(reference, delai_max)
