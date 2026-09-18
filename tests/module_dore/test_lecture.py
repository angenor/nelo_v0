"""US1-2 : lire les paramètres effectifs, résolus à la portée de l'établissement de l'en-tête."""

import uuid

from tests.authentification.outils import en_tetes
from tests.module_dore.outils import PREFIXE, lire, poser

NON_DEFINIES = {
    "sms.plafond_mensuel",
    "conseil.delai_recours_jours",
    "conservation.dossier_eleve_annees",
    "conservation.signalement_annees",
}
# Le reparcours sous suspension pose cette clé au tenant : le module doré ne dépend pas de sa valeur.
HORS_ASSERTION = {"assistance.suspendue"}


async def test_vingt_cles_et_leurs_sources(client, sessions_ab, tenants_ab):
    parametres = await lire(client, sessions_ab.a, tenants_ab.etab_a)
    assert len(parametres) == 20
    for cle, parametre in parametres.items():
        if cle in HORS_ASSERTION:
            continue
        assert parametre["portee_resolue"] is None, cle
        assert parametre["portee_id"] is None, cle
        if cle in NON_DEFINIES:
            assert parametre["source"] == "NON_DEFINIE", cle
            assert parametre["valeur"] is None, cle
        else:
            assert parametre["source"] == "DEFAUT", cle
    assert parametres["absence.delai_notification_minutes"]["valeur"] == 15
    assert parametres["finance.penalite_retard_taux"]["valeur"] == "0"
    assert parametres["finance.penalite_retard_taux"]["type"] == "DECIMAL"


async def test_la_surcharge_locale_gagne(client, sessions_ab, tenants_ab):
    cle = "absence.delai_notification_minutes"
    reponse = await poser(
        client, sessions_ab.a, tenants_ab.etab_a, cle, "TENANT", tenants_ab.tenant_a, 20
    )
    assert reponse.status_code == 200, reponse.text
    parametre = (await lire(client, sessions_ab.a, tenants_ab.etab_a))[cle]
    assert (parametre["valeur"], parametre["source"], parametre["portee_resolue"]) == (
        20,
        "VALEUR",
        "TENANT",
    )
    assert parametre["portee_id"] == str(tenants_ab.tenant_a)

    reponse = await poser(
        client, sessions_ab.a, tenants_ab.etab_a, cle, "ETABLISSEMENT", tenants_ab.etab_a, 25
    )
    assert reponse.status_code == 200, reponse.text
    parametre = (await lire(client, sessions_ab.a, tenants_ab.etab_a))[cle]
    assert (parametre["valeur"], parametre["portee_resolue"]) == (25, "ETABLISSEMENT")
    assert parametre["portee_id"] == str(tenants_ab.etab_a)
    # Une surcharge partielle : les autres clés gardent leur défaut.
    assert (await lire(client, sessions_ab.a, tenants_ab.etab_a))["note.taille_lot_enregistrement"][
        "valeur"
    ] == 5


async def test_sans_en_tete_etablissement(client, sessions_ab):
    """La session est ouverte : ce qui est mesuré ici est le refus d'établissement, pas celui de session."""
    reponse = await client.get(f"{PREFIXE}/parametres", headers=en_tetes(sessions_ab.a))
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_REQUIS"

    reponse = await client.get(
        f"{PREFIXE}/parametres",
        headers={**en_tetes(sessions_ab.a), "X-Nelo-Etablissement": "abc"},
    )
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_REQUIS"


async def test_etablissement_inconnu(client, sessions_ab):
    """Depuis T1a, un établissement auquel le compte n'est pas rattaché est un `403`, jamais un `404`.

    L'en-tête d'établissement est la seule exception au principe « hors périmètre, c'est
    introuvable » (principe XII, docs/03-api.md § 1.2) : inexistant, d'un autre tenant ou
    simplement non rattaché donnent la même réponse, au mot près. L'enveloppe, elle, ne change
    pas : cinq champs, ni plus ni moins.
    """
    reponse = await client.get(
        f"{PREFIXE}/parametres", headers=en_tetes(sessions_ab.a, uuid.uuid7())
    )
    assert reponse.status_code == 403
    corps = reponse.json()
    assert corps["code"] == "TEN_ETABLISSEMENT_NON_AUTORISE"
    assert set(corps) == {"code", "message", "champ", "details", "requete_id"}
