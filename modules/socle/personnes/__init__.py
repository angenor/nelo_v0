"""Le noyau des personnes : nom, prénoms, langue préférée.

L'interface de service, et rien d'autre : ni tables, ni accès aux données, ni moteur.
"""

from modules.socle.personnes.schemas import Identite
from modules.socle.personnes.service import creer_personne, lire_identite, lire_identites

__all__ = ["Identite", "lire_identite", "lire_identites", "creer_personne"]
