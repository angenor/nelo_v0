"""Les modèles Pydantic du module `annees` : la frontière de l'API.

Le noyau n'expose qu'une forme, l'année telle que le contexte la lit. Les états sont ceux de la
contrainte de la table, en minuscules ; la mise en majuscules appartient au contrat HTTP
(`modules/shared/contexte.py`), jamais au module.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

type EtatAnnee = Literal["preparation", "active", "cloturee", "archivee"]


class Annee(BaseModel):
    """Ce que T1a lit d'une année scolaire : de quoi la nommer et dire où elle en est."""

    id: UUID
    libelle: str = Field(min_length=1)
    etat: EtatAnnee
