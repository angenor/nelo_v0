"""L'assistance — un paquet du socle, six capacités, un réglage (docs/02-domaine.md § 13).

Aucune capacité n'est livrée en T0a : l'appel est un **refus explicite**, jamais un silence ni une
simulation qui réussit. La suspension se lit par la valeur effective de `assistance.suspendue` à la
portée de l'établissement, obtenue d'un **lecteur injecté** à la construction — ce paquet n'importe
jamais `tenants` (FR-007). L'état est une valeur que l'interface utilise pour **ne pas afficher**
une affordance, jamais pour la griser.
"""

from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, NoReturn
from uuid import UUID

from modules.socle.assistance.service_inference import ServiceInference


class Capacite(StrEnum):
    C1_REDACTION_ASSISTEE = "C1_REDACTION_ASSISTEE"
    C2_QUESTION_REPONSE_DOCUMENTAIRE = "C2_QUESTION_REPONSE_DOCUMENTAIRE"
    C3_PLANIFICATION_SOUS_CONTRAINTES = "C3_PLANIFICATION_SOUS_CONTRAINTES"
    C4_ANALYSE_ET_DETECTION_DE_SIGNAUX = "C4_ANALYSE_ET_DETECTION_DE_SIGNAUX"
    C5_EXTRACTION_DOCUMENTAIRE = "C5_EXTRACTION_DOCUMENTAIRE"
    C6_ASSISTANCE_A_L_APPRENTISSAGE = "C6_ASSISTANCE_A_L_APPRENTISSAGE"

    @property
    def description_cle(self) -> str:
        """La clé i18n de la capacité — jamais un texte affiché."""
        return f"assistance.capacite.{self.value.lower()}"


class EtatCapacite(StrEnum):
    NON_LIVREE = "NON_LIVREE"
    SUSPENDUE = "SUSPENDUE"
    DISPONIBLE = "DISPONIBLE"


class CapaciteNonLivree(Exception):
    def __init__(self, capacite: Capacite) -> None:
        super().__init__(f"capacité non livrée : {capacite.value}")
        self.capacite = capacite


class AssistanceSuspendue(Exception):
    def __init__(self, capacite: Capacite) -> None:
        super().__init__(f"assistance suspendue à cette portée : {capacite.value}")
        self.capacite = capacite


type LecteurSuspension = Callable[[UUID, UUID], Awaitable[bool]]
"""(tenant_id, etablissement_id) → l'assistance est-elle suspendue à cette portée ?"""

# Aucune capacité n'est livrée en T0a ; C1 et C5 le seront au MVP, chacune par sa tranche.
LIVREES: frozenset[Capacite] = frozenset()


class Assistance:
    def __init__(self, lecteur_suspension: LecteurSuspension, inference: ServiceInference) -> None:
        self._suspendue = lecteur_suspension
        self._inference = inference

    async def etat_des_capacites(
        self, tenant_id: UUID, etablissement_id: UUID
    ) -> dict[Capacite, EtatCapacite]:
        """SUSPENDUE pour les six si assistance.suspendue est vrai à cette portée ; sinon NON_LIVREE en T0a."""
        if await self._suspendue(tenant_id, etablissement_id):
            return dict.fromkeys(Capacite, EtatCapacite.SUSPENDUE)
        return {
            c: EtatCapacite.DISPONIBLE if c in LIVREES else EtatCapacite.NON_LIVREE
            for c in Capacite
        }

    async def appeler(
        self, capacite: Capacite, tenant_id: UUID, etablissement_id: UUID, **entree: Any
    ) -> NoReturn:
        """Lève AssistanceSuspendue si suspendue, sinon CapaciteNonLivree. Aucune capacité ne répond en T0a."""
        if await self._suspendue(tenant_id, etablissement_id):
            raise AssistanceSuspendue(capacite)
        raise CapaciteNonLivree(capacite)
