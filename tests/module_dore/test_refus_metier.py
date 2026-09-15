"""US1-5 — les refus métier : même statut que le refus de schéma, code différent."""

import pytest

from tests.module_dore.outils import poser


async def refus(reponse) -> dict:
    assert reponse.status_code == 422, reponse.text
    corps = reponse.json()
    assert corps["code"] != "VAL_SCHEMA_INVALIDE"
    return corps


async def test_cle_inconnue(client, tenants_ab):
    corps = await refus(
        await poser(client, tenants_ab.etab_a, "inconnue.cle", "TENANT", tenants_ab.tenant_a, 1)
    )
    assert corps["code"] == "TEN_PARAMETRE_INCONNU"
    assert "assistance.suspendue" in corps["details"]["cles_connues"]
    assert len(corps["details"]["cles_connues"]) == 17


async def test_portee_plus_basse_que_permise(client, tenants_ab):
    corps = await refus(
        await poser(
            client,
            tenants_ab.etab_a,
            "securite.duree_session_minutes",
            "ETABLISSEMENT",
            tenants_ab.etab_a,
            60,
        )
    )
    assert corps["code"] == "TEN_PORTEE_INVALIDE"
    assert corps["details"]["portee_la_plus_basse"] == "TENANT"


@pytest.mark.parametrize("portee", ["SITE", "CYCLE"])
async def test_portee_sans_entite(client, tenants_ab, portee):
    corps = await refus(
        await poser(
            client, tenants_ab.etab_a, "assistance.suspendue", portee, tenants_ab.etab_a, True
        )
    )
    assert corps["code"] == "TEN_PORTEE_INVALIDE"
    assert corps["details"]["portees_disponibles"] == ["TENANT", "ETABLISSEMENT"]


async def test_portee_tenant_hors_tenant(client, tenants_ab):
    corps = await refus(
        await poser(
            client, tenants_ab.etab_a, "assistance.suspendue", "TENANT", tenants_ab.tenant_b, True
        )
    )
    assert corps["code"] == "TEN_PORTEE_INVALIDE"
    assert corps["details"]["motif"] == "HORS_TENANT"


@pytest.mark.parametrize(
    ("cle", "valeur", "type_attendu"),
    [
        ("assistance.suspendue", "oui", "BOOLEEN"),
        ("assistance.suspendue", None, "BOOLEEN"),
        ("absence.delai_notification_minutes", True, "ENTIER"),
        ("absence.delai_notification_minutes", "15", "ENTIER"),
        ("finance.penalite_retard_taux", "douze", "DECIMAL"),
        ("finance.penalite_retard_taux", 12, "DECIMAL"),
        ("sms.fenetre_envoi", "7h-19h", "PLAGE_HORAIRE"),
        ("absence.regroupement_recapitulatif", 3, "CHAINE"),
    ],
)
async def test_valeur_du_mauvais_type(client, tenants_ab, cle, valeur, type_attendu):
    corps = await refus(
        await poser(client, tenants_ab.etab_a, cle, "ETABLISSEMENT", tenants_ab.etab_a, valeur)
    )
    assert corps["code"] == "TEN_VALEUR_INVALIDE"
    assert corps["champ"] == "valeur"
    assert corps["details"]["type_attendu"] == type_attendu


@pytest.mark.parametrize(
    ("cle", "valeur"),
    [
        ("finance.penalite_retard_taux", "2.5"),
        ("sms.fenetre_envoi", "06:30-20:00"),
        ("sms.plafond_mensuel", 500),
    ],
)
async def test_valeur_du_bon_type(client, tenants_ab, cle, valeur):
    reponse = await poser(
        client, tenants_ab.etab_a, cle, "ETABLISSEMENT", tenants_ab.etab_a, valeur
    )
    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["valeur"] == valeur
