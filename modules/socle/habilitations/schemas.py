"""Les modèles Pydantic du module `habilitations` : la frontière de l'API.

Les formes exactes sont dans specs/003-connexion-contexte/contracts/openapi-attendu.yaml. Tout
corps entrant est `extra="forbid"` : un champ inconnu est un client qui croit parler à autre
chose, et le lui dire tôt vaut mieux que l'ignorer.

Ce qui ne sort **jamais** d'ici : l'empreinte du code personnel, celle du lien d'invitation, le
code en clair, le jeton de rafraîchissement (il vit dans un cookie que le script ne lit pas).
"""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Corps(BaseModel):
    """Tout corps entrant : rien d'autre que ce qui est déclaré."""

    model_config = ConfigDict(extra="forbid")


class CanalOuverture(StrEnum):
    """Par quoi la session a été ouverte ; l'événement le porte, la dispense de code le lit."""

    CODE = "CODE"
    PIN = "PIN"
    LIEN = "LIEN"


class MotifFermeture(StrEnum):
    DECONNEXION = "DECONNEXION"
    REUTILISATION = "REUTILISATION"
    SUSPENSION = "SUSPENSION"
    CHANGEMENT_NUMERO = "CHANGEMENT_NUMERO"
    EXPIRATION = "EXPIRATION"


class StatutCompte(StrEnum):
    INVITE = "invite"
    ACTIF = "actif"
    SUSPENDU = "suspendu"


# --- Ouvrir une session par un code reçu -------------------------------------------------------


class CorpsDemandeCode(Corps):
    identifiant: str = Field(
        min_length=1,
        max_length=32,
        description="Le numéro de téléphone, dans n'importe quelle écriture ; le serveur le normalise",
    )


class CorpsVerificationCode(Corps):
    identifiant: str = Field(min_length=1, max_length=32)
    code: str = Field(pattern=r"^\d{6}$", description="Les six chiffres reçus par message court")
    compte_id: UUID | None = Field(
        default=None,
        description="Le compte choisi, quand le numéro en porte plusieurs (partage familial)",
    )


class CompteSession(BaseModel):
    """Ce que l'écran a besoin de savoir du compte qui vient d'ouvrir sa session."""

    id: UUID
    nom: str
    prenoms: str
    langue: str = Field(pattern=r"^[a-z]{2}$")
    pin_defini: bool = Field(description="L'écran propose de définir un code personnel, ou non")


class SessionOuverte(BaseModel):
    """La session est ouverte. Le jeton de rafraîchissement n'est **pas** ici : il est en cookie."""

    resultat: Literal["SESSION"] = "SESSION"
    jeton_acces: str = Field(
        description="JWT signé, soixante minutes ; le relais le range en cookie"
    )
    expire_dans: int = Field(description="Secondes avant l'expiration du jeton d'accès")
    compte: CompteSession
    appareil_connu: bool


class ChoixCompte(BaseModel):
    """Un des comptes que ce numéro porte. Aucun numéro ici : la personne le connaît déjà."""

    compte_id: UUID
    nom: str
    prenoms: str
    etablissement_nom: str


class ChoixRequis(BaseModel):
    """Le code est bon, mais le numéro porte plusieurs comptes : qui ouvre la session ?"""

    resultat: Literal["CHOIX"] = "CHOIX"
    comptes: list[ChoixCompte] = Field(min_length=2)


class ReponseVerificationCode(
    RootModel[Annotated[SessionOuverte | ChoixRequis, Field(discriminator="resultat")]]
):
    """Une session, ou un choix à faire : `resultat` dit lequel, le client n'a pas à deviner."""


# --- Le code personnel, sur un appareil connu ---------------------------------------------------


class CorpsOuverturePin(Corps):
    compte_id: UUID = Field(description="Le compte choisi parmi ceux que l'appareil connaît")
    pin: str = Field(pattern=r"^\d{4}$", description="Les quatre chiffres du code personnel")


class CorpsDefinitionPin(Corps):
    pin: str = Field(pattern=r"^\d{4}$")
    pin_courant: str | None = Field(
        default=None,
        description="Exigé quand un code existe déjà, sauf dans les dix minutes suivant une ouverture par code reçu ou par lien",
    )


class CompteConnu(BaseModel):
    """Un compte que cet appareil connaît. **Jamais un numéro** : un nom suffit à se reconnaître."""

    compte_id: UUID
    nom: str
    prenoms: str
    pin_defini: bool


class ReponseAppareil(BaseModel):
    """Les comptes connus de cet appareil ; vide quand il ne l'est d'aucun."""

    comptes: list[CompteConnu]


class Rattachement(BaseModel):
    """Une affectation vivante, réduite à ce dont les middlewares et le contexte ont besoin."""

    etablissement_id: UUID
    annee_id: UUID


class JetonAcces(BaseModel):
    """Le contenu vérifié d'un jeton d'accès. Aucune capacité, aucun nom : le contexte les sert."""

    compte_id: UUID
    tenant_id: UUID
    session_id: UUID
    emis_le: datetime
    expire_le: datetime


class DescriptionCompte(BaseModel):
    """Ce qu'un autre module, ou la composition, a le droit de savoir d'un compte.

    Ni empreinte, ni verrou, ni jeton : ce que le contexte affiche, et le statut qui dit si le
    compte compte encore. `identifiant` est le numéro, et il ne sort que vers celui qui a déjà le
    droit de le voir : l'administrateur que l'écran « aucun domaine » invite à appeler.
    """

    id: UUID
    personne_id: UUID
    identifiant: str
    statut: StatutCompte
    pin_defini: bool


# --- Créer un compte, l'inviter, changer son numéro ---------------------------------------------


class CorpsCreationCompte(Corps):
    personne_id: UUID = Field(description="Une personne du tenant, qui n'a pas encore de compte")
    identifiant: str = Field(min_length=1, max_length=32)
    partage_familial: bool = Field(
        default=False,
        description="Déclare que ce numéro est sciemment partagé avec un autre compte du tenant",
    )


class CompteCree(BaseModel):
    """Ce que la création rend. **Jamais le lien** : il part par message, et nulle part ailleurs."""

    id: UUID
    statut: StatutCompte
    invite_le: datetime | None


class Bloquage(BaseModel):
    """Ce qui empêcherait la création, dit **avant** la saisie plutôt qu'après (E-04, FR-063)."""

    code: str
    details: dict[str, object] = Field(default_factory=dict)


class VerificationCreationCompte(BaseModel):
    bloquages: list[Bloquage]
    issues: list[str] = Field(
        description="Les clés d'issue à proposer : ce qu'on peut faire, pas seulement ce qui est refusé"
    )


class CorpsChangementTelephone(Corps):
    nouvel_identifiant: str = Field(min_length=1, max_length=32)


class CorpsVerificationChangement(Corps):
    code: str = Field(pattern=r"^\d{6}$")


class CorpsChangementAdministratif(Corps):
    nouvel_identifiant: str = Field(min_length=1, max_length=32)
