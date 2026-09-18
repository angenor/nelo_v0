"""Le catalogue des paramètres : docs/02-domaine.md § 17, ligne pour ligne.

Lu par les migrations qui alimentent `tenants.parametre_catalogue`. Les clés dont § 17 dit
« country pack » sont posées à la portée `TENANT`, avec `origine_defaut = COUNTRY_PACK` : leur
défaut viendra du pack quand sa table existera. `description_cle` est une clé i18n, jamais un
texte affiché.

Chaque entrée porte la **révision qui l'introduit** : une migration appliquée ne se modifie
jamais, et `entrees_de("0002")` ne rend que ce que la révision 0002 a ajouté. Une tranche qui
pose une clé l'ajoute ici avec sa révision, et l'insère dans sa propre migration.
"""

from typing import Any, TypedDict


class EntreeCatalogue(TypedDict):
    cle: str
    portee_la_plus_basse: str
    type: str
    valeur_defaut: Any
    origine_defaut: str
    description_cle: str


def _entree(
    cle: str, portee: str, type_: str, defaut: Any, origine: str, depuis: str = "0001"
) -> EntreeCatalogue:
    entree: EntreeCatalogue = {
        "cle": cle,
        "portee_la_plus_basse": portee,
        "type": type_,
        "valeur_defaut": defaut,
        "origine_defaut": origine,
        "description_cle": f"parametre.{cle}.description",
    }
    _REVISIONS[cle] = depuis
    return entree


# La révision de `tenants` qui a introduit chaque clé ; hors de la ligne insérée en base.
_REVISIONS: dict[str, str] = {}


def entrees_de(revision: str) -> list[EntreeCatalogue]:
    """Les entrées introduites par cette révision, et elles seules."""
    return [e for e in CATALOGUE if _REVISIONS[e["cle"]] == revision]


CATALOGUE: list[EntreeCatalogue] = [
    _entree("absence.delai_notification_minutes", "ETABLISSEMENT", "ENTIER", 15, "LITTERALE"),
    _entree(
        "absence.regroupement_recapitulatif", "ETABLISSEMENT", "CHAINE", "HEBDOMADAIRE", "LITTERALE"
    ),
    _entree("note.taille_lot_enregistrement", "TENANT", "ENTIER", 5, "LITTERALE"),
    _entree("note.tolerance_hors_bornes", "TENANT", "CHAINE", "AUCUNE", "LITTERALE"),
    _entree("bulletin.publication_apres_conseil", "ETABLISSEMENT", "BOOLEEN", True, "LITTERALE"),
    _entree("finance.penalite_retard_taux", "ETABLISSEMENT", "DECIMAL", "0", "LITTERALE"),
    _entree("finance.remise_fratrie_taux", "ETABLISSEMENT", "DECIMAL", "0", "LITTERALE"),
    _entree("finance.seuil_alerte_impaye_jours", "ETABLISSEMENT", "ENTIER", 30, "LITTERALE"),
    _entree("sms.plafond_mensuel", "ETABLISSEMENT", "ENTIER", None, "OBLIGATOIRE"),
    _entree("sms.fenetre_envoi", "ETABLISSEMENT", "PLAGE_HORAIRE", "07:00-19:00", "LITTERALE"),
    _entree("conseil.delai_recours_jours", "TENANT", "ENTIER", None, "COUNTRY_PACK"),
    _entree(
        "inscription.derogation_dossier_incomplet", "ETABLISSEMENT", "BOOLEEN", False, "LITTERALE"
    ),
    _entree("securite.duree_session_minutes", "TENANT", "ENTIER", 480, "LITTERALE"),
    _entree("securite.expiration_delegation_max_jours", "TENANT", "ENTIER", 90, "LITTERALE"),
    _entree("assistance.suspendue", "ETABLISSEMENT", "BOOLEEN", False, "LITTERALE"),
    _entree("conservation.dossier_eleve_annees", "TENANT", "ENTIER", None, "COUNTRY_PACK"),
    _entree("conservation.signalement_annees", "TENANT", "ENTIER", None, "COUNTRY_PACK"),
    # Les trois clés de sécurité de T1a (docs/02-domaine.md § 17, diff de `specify`).
    _entree("securite.pin_tentatives_max", "ETABLISSEMENT", "ENTIER", 5, "LITTERALE", "0002"),
    _entree("securite.appareil_connu_jours", "ETABLISSEMENT", "ENTIER", 90, "LITTERALE", "0002"),
    _entree(
        "securite.invitation_validite_jours", "ETABLISSEMENT", "ENTIER", 7, "LITTERALE", "0002"
    ),
]
