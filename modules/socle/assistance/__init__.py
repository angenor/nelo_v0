"""L'assistance — un paquet du socle, six capacités, aucune livrée, suspendue par un réglage."""

from modules.socle.assistance.service import (
    Assistance,
    AssistanceSuspendue,
    Capacite,
    CapaciteNonLivree,
    EtatCapacite,
)
from modules.socle.assistance.service_inference import ServiceInference, SimulationServiceInference

__all__ = [
    "Assistance",
    "Capacite",
    "EtatCapacite",
    "CapaciteNonLivree",
    "AssistanceSuspendue",
    "ServiceInference",
    "SimulationServiceInference",
]
