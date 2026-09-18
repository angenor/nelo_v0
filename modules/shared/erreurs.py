"""L'enveloppe d'erreur et les deux exceptions que tout module peut lever.

L'enveloppe est celle de docs/03-api.md § 1.6 : `code` est ce que le client teste, jamais `message`.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

type NomDependance = Literal["PASSERELLE_SMS", "AGREGATEUR_PAIEMENT", "SERVICE_INFERENCE"]


class EnveloppeErreur(BaseModel):
    """docs/03-api.md § 1.6 — `code` est ce que le client teste, jamais `message`."""

    code: str = Field(description="Stable, préfixé par domaine")
    message: str = Field(description="Français, factuel, destiné au journal — pas affiché tel quel")
    champ: str | None
    details: dict[str, Any] = Field(
        description=(
            "De quoi construire l'issue — pour `VAL_SCHEMA_INVALIDE`, `champs` est une liste de "
            "`{chemin, motif}`"
        )
    )
    requete_id: str | None = Field(
        description="L'`X-Nelo-Requete` reçu ; `null` si la requête n'en portait pas"
    )


class ErreurMetier(Exception):
    """Un refus de règle métier sur un corps valide : son code, son statut, de quoi construire l'issue."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        statut: int = 422,
        champ: str | None = None,
        details: dict[str, Any] | None = None,
        en_tetes: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.statut = statut
        self.champ = champ
        self.details = details or {}
        # Les en-têtes que la réponse doit porter : `Retry-After` sur une limite de débit. Le
        # module dit ce que le protocole exige ; `api/` le pose sans le décider.
        self.en_tetes = en_tetes or {}


class DependanceIndisponible(Exception):
    """Une dépendance externe ne répond pas. L'API la traduit en `503 API_DEPENDANCE_INDISPONIBLE`."""

    def __init__(self, dependance: NomDependance) -> None:
        super().__init__(f"dépendance indisponible : {dependance}")
        self.dependance = dependance
