"""Le catalogue des paramètres — docs/02-domaine.md § 17, ligne pour ligne.

Lu par la migration qui alimente `tenants.parametre_catalogue`. Les clés dont § 17 dit « country
pack » sont posées à la portée `TENANT`, avec `origine_defaut = COUNTRY_PACK` : leur défaut viendra
du pack quand sa table existera. `description_cle` est une clé i18n, jamais un texte affiché.
"""

from typing import Any, TypedDict


class EntreeCatalogue(TypedDict):
    cle: str
    portee_la_plus_basse: str
    type: str
    valeur_defaut: Any
    origine_defaut: str
    description_cle: str


def _entree(cle: str, portee: str, type_: str, defaut: Any, origine: str) -> EntreeCatalogue:
    return {
        "cle": cle,
        "portee_la_plus_basse": portee,
        "type": type_,
        "valeur_defaut": defaut,
        "origine_defaut": origine,
        "description_cle": f"parametre.{cle}.description",
    }


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
]
