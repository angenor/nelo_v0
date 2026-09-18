"""Les modèles Pydantic du module `personnes` : la frontière de l'API.

Le noyau n'expose qu'une forme, l'identité : ce que le contexte affiche d'une personne, et rien
de plus. T3a livre le dossier complet et ses routes.
"""

from pydantic import BaseModel, Field

# Une langue est un code de deux lettres minuscules, comme la contrainte de la table le dit.
MOTIF_LANGUE = r"^[a-z]{2}$"


class Identite(BaseModel):
    """Nom, prénoms et langue : les trois seules colonnes que le contexte lit d'une personne."""

    nom: str = Field(min_length=1)
    prenoms: str
    langue: str = Field(pattern=MOTIF_LANGUE)
