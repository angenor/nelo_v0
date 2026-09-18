"""US3-4 : l'outbox est une seule mécanique, paramétrée par la table de chaque module.

La même prise, le même marquage, la même reprise sur `tenants.evenement_outbox` et sur
`habilitations.evenement_outbox` : si les deux tables se comportaient différemment, un module
aurait sa propre file, et la règle 10 tiendrait sur l'un et pas sur l'autre.
"""

from datetime import timedelta

import pytest

from modules.shared import Evenement, transaction
from modules.shared import outbox as file
from modules.socle.annees.tables import evenement_outbox as outbox_annees
from modules.socle.habilitations.tables import evenement_outbox as outbox_habilitations
from modules.socle.personnes.tables import evenement_outbox as outbox_personnes
from modules.socle.tenants.tables import evenement_outbox as outbox_tenants

TABLES = [outbox_tenants, outbox_habilitations, outbox_personnes, outbox_annees]
LES_DEUX = [outbox_tenants, outbox_habilitations]


def nommer(table) -> str:
    return f"{table.schema}.{table.name}"


@pytest.mark.parametrize("table", LES_DEUX, ids=nommer)
async def test_la_meme_prise_sur_les_deux_tables(tenants_ab, table):
    tenant = tenants_ab.tenant_a
    async with transaction(tenant) as connexion:
        premier = await file.inserer(connexion, table, tenant, Evenement("essai.un", {"rang": 1}))
        second = await file.inserer(connexion, table, tenant, Evenement("essai.deux", {"rang": 2}))

    async with transaction(tenant) as connexion:
        pris = await file.prendre(connexion, table, tenant, 1)
    assert [ligne["id"] for ligne in pris] == [premier]
    assert pris[0]["type"] == "essai.un" and pris[0]["charge"] == {"rang": 1}

    async with transaction(tenant) as connexion:
        suivants = await file.prendre(connexion, table, tenant, 10)
    assert [ligne["id"] for ligne in suivants] == [second]

    async with transaction(tenant) as connexion:
        assert await file.prendre(connexion, table, tenant, 10) == []


@pytest.mark.parametrize("table", LES_DEUX, ids=nommer)
async def test_le_traite_ne_revient_pas_l_echec_est_repris(tenants_ab, table):
    tenant = tenants_ab.tenant_a
    async with transaction(tenant) as connexion:
        traite = await file.inserer(connexion, table, tenant, Evenement("essai.traite", {}))
        echoue = await file.inserer(connexion, table, tenant, Evenement("essai.echec", {}))
        await file.prendre(connexion, table, tenant, 10)
        await file.marquer_traite(connexion, table, traite)
        await file.marquer_echec(connexion, table, echoue, "passerelle indisponible")

    async with transaction(tenant) as connexion:
        assert await file.prendre(connexion, table, tenant, 10) == []
        assert await file.reprendre_en_echec(connexion, table, tenant) == 1
        repris = await file.prendre(connexion, table, tenant, 10)
    assert [ligne["id"] for ligne in repris] == [echoue]


@pytest.mark.parametrize("table", LES_DEUX, ids=nommer)
async def test_le_pris_orphelin_repasse_en_attente(tenants_ab, table):
    tenant = tenants_ab.tenant_a
    async with transaction(tenant) as connexion:
        orphelin = await file.inserer(connexion, table, tenant, Evenement("essai.orphelin", {}))
        await file.prendre(connexion, table, tenant, 10)

    # Le processus qui l'avait pris est mort. `now()` est l'heure d'ouverture de la transaction :
    # la reprise se juge dans une transaction postérieure à la prise, jamais dans la sienne.
    async with transaction(tenant) as connexion:
        assert await file.reprendre_pris_orphelins(connexion, table, tenant, timedelta(0)) == 1
        revenus = await file.prendre(connexion, table, tenant, 10)
    assert [ligne["id"] for ligne in revenus] == [orphelin]


@pytest.mark.parametrize("table", TABLES, ids=nommer)
async def test_aucun_tenant_ne_prend_l_evenement_d_un_autre(tenants_ab, table):
    async with transaction(tenants_ab.tenant_a) as connexion:
        a_lui = await file.inserer(
            connexion, table, tenants_ab.tenant_a, Evenement("essai.isolation", {})
        )
    async with transaction(tenants_ab.tenant_b) as connexion:
        assert await file.prendre(connexion, table, tenants_ab.tenant_b, 10) == []
        assert await file.reprendre_en_echec(connexion, table, tenants_ab.tenant_b) == 0
    async with transaction(tenants_ab.tenant_a) as connexion:
        pris = await file.prendre(connexion, table, tenants_ab.tenant_a, 10)
    assert [ligne["id"] for ligne in pris] == [a_lui]
