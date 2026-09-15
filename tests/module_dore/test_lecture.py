"""US1-2 — lire les paramètres effectifs, résolus à la portée de l'établissement de l'en-tête."""

import uuid

from tests.module_dore.outils import PREFIXE, lire, poser

NON_DEFINIES = {
    "sms.plafond_mensuel",
    "conseil.delai_recours_jours",
    "conservation.dossier_eleve_annees",
    "conservation.signalement_annees",
}
# Le reparcours sous suspension pose cette clé au tenant : le module doré ne dépend pas de sa valeur.
HORS_ASSERTION = {"assistance.suspendue"}


async def test_dix_sept_cles_et_leurs_sources(client, tenants_ab):
    parametres = await lire(client, tenants_ab.etab_a)
    assert len(parametres) == 17
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


async def test_la_surcharge_locale_gagne(client, tenants_ab):
    cle = "absence.delai_notification_minutes"
    reponse = await poser(client, tenants_ab.etab_a, cle, "TENANT", tenants_ab.tenant_a, 20)
    assert reponse.status_code == 200, reponse.text
    parametre = (await lire(client, tenants_ab.etab_a))[cle]
    assert (parametre["valeur"], parametre["source"], parametre["portee_resolue"]) == (
        20,
        "VALEUR",
        "TENANT",
    )
    assert parametre["portee_id"] == str(tenants_ab.tenant_a)

    reponse = await poser(client, tenants_ab.etab_a, cle, "ETABLISSEMENT", tenants_ab.etab_a, 25)
    assert reponse.status_code == 200, reponse.text
    parametre = (await lire(client, tenants_ab.etab_a))[cle]
    assert (parametre["valeur"], parametre["portee_resolue"]) == (25, "ETABLISSEMENT")
    assert parametre["portee_id"] == str(tenants_ab.etab_a)
    # Une surcharge partielle : les autres clés gardent leur défaut.
    assert (await lire(client, tenants_ab.etab_a))["note.taille_lot_enregistrement"]["valeur"] == 5


async def test_sans_en_tete_etablissement(client, tenants_ab):
    reponse = await client.get(f"{PREFIXE}/parametres")
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_REQUIS"

    reponse = await client.get(f"{PREFIXE}/parametres", headers={"X-Nelo-Etablissement": "abc"})
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_REQUIS"


async def test_etablissement_inconnu(client, tenants_ab):
    reponse = await client.get(
        f"{PREFIXE}/parametres", headers={"X-Nelo-Etablissement": str(uuid.uuid7())}
    )
    assert reponse.status_code == 404
    corps = reponse.json()
    assert corps["code"] == "TEN_RESSOURCE_INTROUVABLE"
    assert set(corps) == {"code", "message", "champ", "details", "requete_id"}
