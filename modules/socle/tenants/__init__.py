"""Le module doré — tenants, établissements, catalogue de paramètres.

L'interface de service, et rien d'autre : ni tables, ni accès aux données, ni moteur.
"""

from modules.socle.tenants.schemas import (
    CorpsPoserParametre,
    Devise,
    Etablissement,
    Pack,
    ParametreEffectif,
    ParametrePose,
    Portee,
    ReponseParametres,
    ReponseSante,
)
from modules.socle.tenants.service import (
    Consommateur,
    consommer_lot,
    creer_etablissement,
    creer_tenant,
    designer_administrateur,
    lire_etablissements,
    lire_pack,
    lire_parametres_effectifs,
    poser_parametre,
    reprendre_evenements,
    tenants_pour_travailleur,
    valeur_effective,
)

__all__ = [
    "lire_parametres_effectifs",
    "poser_parametre",
    "valeur_effective",
    "ParametreEffectif",
    "ParametrePose",
    "Portee",
    "creer_tenant",
    "creer_etablissement",
    "tenants_pour_travailleur",
    "CorpsPoserParametre",
    "ReponseParametres",
    "ReponseSante",
    "Consommateur",
    "consommer_lot",
    "reprendre_evenements",
    "lire_etablissements",
    "designer_administrateur",
    "lire_pack",
    "Pack",
    "Devise",
    "Etablissement",
]
