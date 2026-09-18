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


class Devise(BaseModel):
    """Ce que le pack dit de la monnaie ; l'exposant porte les décimales, jamais le montant."""

    code: str = Field(pattern=r"^[A-Z]{3}$")
    exposant: int = Field(ge=0, le=4)
    symbole: str = Field(min_length=1)


class Pack(BaseModel):
    """Le country pack, tel que T1a le lit : ce que le contexte projette, et le format de numéro.

    `contenu` porte davantage en base (docs/02-domaine.md § 1.3) ; cette forme est le
    sous-ensemble dont la tranche a besoin. Une tranche qui en lit plus l'ajoute ici.
    """

    pays_code: str = Field(pattern=r"^[A-Z]{2}$")
    version: int = Field(ge=1)
    devise: Devise
    langues: list[str] = Field(min_length=1)
    decoupage: str
    indicatif: str = Field(min_length=1)
    vocabulaire: dict[str, dict[str, str]]


class Etablissement(BaseModel):
    """L'établissement tel que le contexte le lit, et le repli quand aucun administrateur n'est désigné."""

    id: UUID
    nom: str = Field(min_length=1)
    telephone: str | None
    fuseau_horaire: str
    administrateur_compte_id: UUID | None
