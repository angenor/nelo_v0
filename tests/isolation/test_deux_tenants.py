"""US2-1 — A ne voit jamais B : ni par l'API, ni sur aucune table du schéma."""

from modules.shared import transaction
from tests.isolation.schema import colonne, compter, tables_du_schema
from tests.module_dore.outils import lire, poser

CLE = "absence.delai_notification_minutes"


async def test_a_ne_voit_aucune_valeur_de_b(client, tenants_ab):
    reponse = await poser(client, tenants_ab.etab_b, CLE, "ETABLISSEMENT", tenants_ab.etab_b, 99)
    assert reponse.status_code == 200, reponse.text
    reponse = await poser(client, tenants_ab.etab_b, CLE, "TENANT", tenants_ab.tenant_b, 98)
    assert reponse.status_code == 200, reponse.text

    parametre = (await lire(client, tenants_ab.etab_a))[CLE]
    assert (parametre["source"], parametre["portee_resolue"], parametre["valeur"]) == (
        "DEFAUT",
        None,
        15,
    )


async def test_une_ressource_de_b_est_introuvable_jamais_interdite(client, tenants_ab):
    reponse = await poser(client, tenants_ab.etab_a, CLE, "ETABLISSEMENT", tenants_ab.etab_b, 1)
    assert reponse.status_code == 404
    assert reponse.json()["code"] == "TEN_RESSOURCE_INTROUVABLE"


async def test_chaque_table_ne_montre_que_le_tenant_courant(client, tenants_ab):
    # Chaque tenant porte des lignes dans chaque table : un zéro ne peut pas être un vide.
    for etab in (tenants_ab.etab_a, tenants_ab.etab_b):
        reponse = await poser(client, etab, CLE, "ETABLISSEMENT", etab, 7)
        assert reponse.status_code == 200, reponse.text

    async with transaction(tenants_ab.tenant_a) as connexion:
        for nom in await tables_du_schema(connexion):
            if nom == "parametre_catalogue":
                # Référentiel commun : visible dans toute transaction tenantée, sans tenant_id.
                assert await connexion.scalar(compter(nom)) == 17
                continue
            cle_tenant = colonne("id") if nom == "tenant" else colonne("tenant_id")
            etrangeres = await connexion.scalar(compter(nom, cle_tenant != tenants_ab.tenant_a))
            assert etrangeres == 0, f"tenants.{nom} montre des lignes d'un autre tenant"
            assert await connexion.scalar(compter(nom)) >= 1, f"tenants.{nom} : rien à inspecter"
