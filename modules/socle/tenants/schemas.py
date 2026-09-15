"""Les modèles Pydantic du contrat — contracts/openapi-attendu.yaml.

Un `DECIMAL` voyage en chaîne (docs/03-api.md § 1.4) ; aucune valeur numérique à virgule ne passe
par un flottant.
"""

from datetime import datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Portee(StrEnum):
    TENANT = "TENANT"
    ETABLISSEMENT = "ETABLISSEMENT"
    SITE = "SITE"
    CYCLE = "CYCLE"


class TypeParametre(StrEnum):
    ENTIER = "ENTIER"
    DECIMAL = "DECIMAL"
    BOOLEEN = "BOOLEEN"
    CHAINE = "CHAINE"
    PLAGE_HORAIRE = "PLAGE_HORAIRE"


type ValeurParametre = bool | int | str | None


class ParametreEffectif(BaseModel):
    cle: str
    type: TypeParametre
    valeur: ValeurParametre = Field(
        description="La valeur brute, typée par le catalogue. Un DECIMAL voyage en chaîne."
    )
    portee_resolue: Portee | None = Field(
        description="La portée à laquelle la valeur a été trouvée ; `null` si aucune valeur n'est posée"
    )
    portee_id: UUID | None
    source: Literal["VALEUR", "DEFAUT", "NON_DEFINIE"]


class ReponseParametres(BaseModel):
    etablissement_id: UUID
    parametres: list[ParametreEffectif]


class CorpsPoserParametre(BaseModel):
    model_config = ConfigDict(extra="forbid")

    portee: Portee
    portee_id: UUID
    valeur: ValeurParametre


class ParametrePose(BaseModel):
    cle: str
    portee: Portee
    portee_id: UUID
    valeur: ValeurParametre
    pose_le: datetime


class ReponseSante(BaseModel):
    etat: Literal["OK"]
