"""Le contexte qui compose l'interface : docs/03-api.md § 1.9.

T0b l'enregistrait dans les composants du contrat OpenAPI, sans route, pour que le client en
dérive son type au lieu de l'écrire (specs/002-socle-interface/research.md R-05) ; depuis T1a,
`GET /moi/capacites` le sert, et FastAPI le publie lui-même.

Aucun rôle, aucune littérale de pays : la personne est décrite par ses capacités, le pays par son
pack. C'est la **seule** source de ce que l'interface a le droit de rendre.
"""

import re
from datetime import date
from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

type CodeNeutre = str
type EtatAnnee = Literal["PREPARATION", "ACTIVE", "CLOTUREE", "ARCHIVEE"]
type Gravite = Literal["INFO", "ALERTE", "CRITIQUE"]

MOTIF_CODE_NEUTRE = r"^[A-Z][A-Z0-9_]*$"
MOTIF_CAPACITE = r"^[a-z_]+\.[a-z_]+\.[a-z_]+$"
MOTIF_LANGUE = r"^[a-z]{2}$"


def _correspond(motif: str, valeur: str) -> bool:
    return re.fullmatch(motif, valeur) is not None


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Compte(Strict):
    id: UUID
    nom: str = Field(min_length=1)
    prenoms: str = Field(min_length=1)
    langue: str = Field(pattern=MOTIF_LANGUE, description="Code de langue à deux lettres")


class Site(Strict):
    id: UUID
    nom: str = Field(min_length=1)


class Administrateur(Strict):
    """Qui peut attribuer ses domaines à une personne sans capacité : l'écran le nomme.

    À défaut de personne désignée, c'est l'établissement lui-même qu'on appelle (FR-049) : son
    nom, son téléphone, et des **prénoms vides**, parce qu'une institution n'en a pas. Le champ
    n'est jamais absent : un écran qui dit « demandez à quelqu'un » sans dire à qui ne sert à rien.
    """

    nom: str = Field(min_length=1)
    prenoms: str = Field(description="Vides quand l'administrateur est l'établissement lui-même")
    telephone: str = Field(
        description=(
            "Au format du pack. Vide seulement quand personne n'est désigné et que "
            "l'établissement lui-même n'a pas de téléphone enregistré : l'écran nomme alors "
            "l'école sans pouvoir donner de numéro, ce qui vaut mieux qu'un refus du serveur"
        )
    )


class EtablissementContexte(Strict):
    id: UUID
    nom: str = Field(min_length=1)
    sites: list[Site]
    cycles_actifs: list[CodeNeutre]
    modules_actifs: list[CodeNeutre]
    administrateur: Administrateur

    @field_validator("cycles_actifs", "modules_actifs")
    @classmethod
    def codes_neutres(cls, codes: list[str]) -> list[str]:
        for code in codes:
            if not _correspond(MOTIF_CODE_NEUTRE, code):
                raise ValueError(f"« {code} » n'est pas un code neutre")
        return codes


class AnneeContexte(Strict):
    id: UUID
    libelle: str = Field(min_length=1)
    etat: EtatAnnee


class CapaciteContexte(Strict):
    code: str = Field(pattern=MOTIF_CAPACITE, description="domaine.objet.verbe")
    perimetre: dict[str, list[UUID]] = Field(description="Listes d'identifiants nommées `*_ids`")

    @field_validator("perimetre")
    @classmethod
    def listes_nommees(cls, perimetre: dict[str, list[UUID]]) -> dict[str, list[UUID]]:
        for nom in perimetre:
            if not nom.endswith("_ids"):
                raise ValueError(f"« {nom} » : une liste de périmètre se nomme `*_ids`")
        return perimetre


class AccesNominatif(Strict):
    code: str = Field(pattern=MOTIF_CAPACITE)
    fin: date = Field(description="Date scolaire de fin, incluse")


class Devise(Strict):
    code: str = Field(pattern=r"^[A-Z]{3}$")
    exposant: int = Field(ge=0, le=4, description="Nombre de chiffres de l'unité mineure")
    symbole: str = Field(min_length=1, description="Ce que l'interface écrit après un montant")


class CountryPackContexte(Strict):
    pays: str = Field(pattern=r"^[A-Z]{2}$")
    version: int = Field(ge=1)
    devise: Devise
    langues: list[str] = Field(min_length=1)
    decoupage: CodeNeutre = Field(pattern=MOTIF_CODE_NEUTRE)
    vocabulaire: dict[CodeNeutre, dict[str, str]] = Field(
        description="Codes neutres de docs/02-domaine.md § 15, un libellé par langue du pack"
    )

    @field_validator("langues")
    @classmethod
    def langues_valides(cls, langues: list[str]) -> list[str]:
        for langue in langues:
            if not _correspond(MOTIF_LANGUE, langue):
                raise ValueError(f"« {langue} » n'est pas un code de langue")
        return langues

    @model_validator(mode="after")
    def vocabulaire_complet(self) -> Self:
        for code, libelles in self.vocabulaire.items():
            if not _correspond(MOTIF_CODE_NEUTRE, code):
                raise ValueError(f"« {code} » n'est pas un code neutre")
            manquantes = set(self.langues) - set(libelles)
            if manquantes:
                raise ValueError(f"{code} : aucun libellé en {', '.join(sorted(manquantes))}")
        return self


class AlerteContexte(Strict):
    type: CodeNeutre = Field(pattern=MOTIF_CODE_NEUTRE)
    gravite: Gravite
    details: dict[str, Any]


class ContexteCapacites(Strict):
    """Une seule requête au démarrage : tout ce qu'il faut pour ne rendre que ce qui existe."""

    compte: Compte
    etablissements: list[EtablissementContexte] = Field(min_length=1)
    etablissement_actif: UUID
    annees: list[AnneeContexte] = Field(min_length=1)
    annee_active: UUID
    capacites: list[CapaciteContexte]
    acces_nominatifs: list[AccesNominatif]
    country_pack: CountryPackContexte
    parametres_effectifs: dict[str, Any]
    alertes: list[AlerteContexte]

    @model_validator(mode="after")
    def actifs_coherents(self) -> Self:
        if self.etablissement_actif not in {e.id for e in self.etablissements}:
            raise ValueError("etablissement_actif n'est pas dans etablissements")
        if self.annee_active not in {a.id for a in self.annees}:
            raise ValueError("annee_active n'est pas dans annees")
        return self
