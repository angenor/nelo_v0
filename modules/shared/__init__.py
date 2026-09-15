"""Ce que tout le monde partage : la transaction, les erreurs, les modes de simulation, l'événement."""

from modules.shared.bd import transaction
from modules.shared.erreurs import DependanceIndisponible, EnveloppeErreur, ErreurMetier
from modules.shared.evenement import Evenement
from modules.shared.simulation import ModeSimulation

__all__ = [
    "transaction",
    "EnveloppeErreur",
    "ErreurMetier",
    "DependanceIndisponible",
    "ModeSimulation",
    "Evenement",
]
