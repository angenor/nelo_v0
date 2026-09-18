"""Le noyau des années scolaires : le libellé, l'état, l'établissement.

L'interface de service, et rien d'autre : ni tables, ni accès aux données, ni moteur.
"""

from modules.socle.annees.schemas import Annee
from modules.socle.annees.service import creer_annee, etablissement_de_annee, lire_annees

__all__ = ["Annee", "lire_annees", "etablissement_de_annee", "creer_annee"]
