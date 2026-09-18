"""La passerelle SMS : l'interface dessinée pour un fournisseur réel, et sa simulation.

Le SMS est un canal de premier rang (constitution, XIII). Chez un fournisseur réel, la soumission
rend un identifiant tout de suite, et le rapport de remise (DLR) arrive **plus tard** par webhook,
en retard, en double, ou jamais. T4a remplace la simulation ; ce sera un remplacement, pas une
découverte.
"""

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
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


@dataclass(frozen=True, slots=True)
class EnvoiSimule:
    """Ce qu'un envoi simulé garde : de quoi le relire en test, jamais en production."""

    destinataire_e164: str
    texte: str
    reference: ReferenceEnvoi
    envoye_le: datetime


class PasserelleSms(Protocol):
    async def envoyer(self, destinataire_e164: str, texte: str, reference: UUID) -> ReferenceEnvoi:
        """Fournisseur réel : soumission d'un message (ex. POST /messages) → identifiant fournisseur."""
        ...

    async def attendre_accuse(
        self, reference: ReferenceEnvoi, delai_max: timedelta
    ) -> AccuseSms | None:
        """Fournisseur réel : rapport de remise reçu par webhook (DLR). None à l'échéance, jamais de blocage."""
        ...


class SimulationPasserelleSms:
    """La simulation garde ses envois : les tests y lisent le code, le journal sert aux e2e.

    `journal` est un chemin de développement et de test seulement (`NELO_SMS_JOURNAL`) : une ligne
    JSON par envoi, à laquelle le navigateur de Playwright va lire le dernier code reçu. Sans
    chemin, rien ne s'écrit sur le disque.
    """

    def __init__(self, mode: ModeSimulation, delai: timedelta, journal: Path | None = None) -> None:
        self.mode = mode
        self.journal = journal
        self.envoyes: list[EnvoiSimule] = []
        self._accuses: AccusesSimules[AccuseSms] = AccusesSimules(mode, delai)

    async def envoyer(self, destinataire_e164: str, texte: str, reference: UUID) -> ReferenceEnvoi:
        if self.mode == ModeSimulation.INDISPONIBLE:
            raise DependanceIndisponible("PASSERELLE_SMS")
        envoi = ReferenceEnvoi(reference, f"simulation-{reference}")
        simule = EnvoiSimule(destinataire_e164, texte, envoi, datetime.now(UTC))
        self.envoyes.append(simule)
        self._journaliser(simule)
        self._accuses.annoncer(envoi, AccuseSms(envoi, "REMIS"))
        return envoi

    def _journaliser(self, envoi: EnvoiSimule) -> None:
        if self.journal is None:
            return
        ligne = json.dumps(
            {
                "destinataire": envoi.destinataire_e164,
                "texte": envoi.texte,
                "reference": str(envoi.reference.reference),
                "envoye_le": envoi.envoye_le.isoformat(),
            },
            ensure_ascii=False,
        )
        with self.journal.open("a", encoding="utf-8") as fichier:
            fichier.write(ligne + "\n")

    async def attendre_accuse(
        self, reference: ReferenceEnvoi, delai_max: timedelta
    ) -> AccuseSms | None:
        return await self._accuses.attendre(reference, delai_max)
