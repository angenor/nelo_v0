"""US7-2, US7-3 — assistance.suspendue, posée par la route d'écriture, suspend à sa portée."""

import pytest

from modules.socle import tenants
from modules.socle.assistance import AssistanceSuspendue, Capacite, EtatCapacite
from tests.module_dore.outils import poser

CLE = "assistance.suspendue"


async def etats(application, tenant_id, etab_id):
    return set((await application.state.assistance.etat_des_capacites(tenant_id, etab_id)).values())


async def test_suspendue_a_l_etablissement(client, application, tenants_ab):
    second = await tenants.creer_etablissement(tenants_ab.tenant_b, "École B2", "Africa/Abidjan")
    reponse = await poser(client, tenants_ab.etab_b, CLE, "ETABLISSEMENT", tenants_ab.etab_b, True)
    assert reponse.status_code == 200, reponse.text

    assert await etats(application, tenants_ab.tenant_b, tenants_ab.etab_b) == {
        EtatCapacite.SUSPENDUE
    }
    for capacite in Capacite:
        with pytest.raises(AssistanceSuspendue):
            await application.state.assistance.appeler(
                capacite, tenants_ab.tenant_b, tenants_ab.etab_b
            )
    attendu = EtatCapacite.SUSPENDUE if _sous_suspension() else EtatCapacite.NON_LIVREE
    assert await etats(application, tenants_ab.tenant_b, second) == {attendu}


async def test_suspendue_au_tenant_puis_surcharge_locale(client, application, tenants_ab):
    second = await tenants.creer_etablissement(tenants_ab.tenant_b, "École B2", "Africa/Abidjan")
    reponse = await poser(client, tenants_ab.etab_b, CLE, "TENANT", tenants_ab.tenant_b, True)
    assert reponse.status_code == 200, reponse.text
    for etab in (tenants_ab.etab_b, second):
        assert await etats(application, tenants_ab.tenant_b, etab) == {EtatCapacite.SUSPENDUE}

    reponse = await poser(client, tenants_ab.etab_b, CLE, "ETABLISSEMENT", second, False)
    assert reponse.status_code == 200, reponse.text
    assert await etats(application, tenants_ab.tenant_b, tenants_ab.etab_b) == {
        EtatCapacite.SUSPENDUE
    }
    assert await etats(application, tenants_ab.tenant_b, second) == {EtatCapacite.NON_LIVREE}


async def test_l_etat_est_une_valeur_jamais_un_libelle(application, tenants_ab):
    valeurs = await application.state.assistance.etat_des_capacites(
        tenants_ab.tenant_a, tenants_ab.etab_a
    )
    for capacite, etat in valeurs.items():
        assert capacite.value.isupper() and etat.value.isupper()
        assert capacite.description_cle.startswith("assistance.capacite.")


def _sous_suspension() -> bool:
    import os

    return os.environ.get("NELO_TEST_SUSPENSION") == "1"
