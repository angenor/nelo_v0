"""US2 : l'en-tête d'établissement est vérifié contre les affectations du compte, pas contre lui-même.

Deux refus qui ne disent pas la même chose : `400` quand le client n'a pas posé la question,
`403` quand il l'a posée et que la réponse est non. Ce `403` est la seule exception au principe
« hors périmètre, c'est introuvable », et il est **identique** dans les trois cas où il tombe :
l'établissement d'un autre tenant, un établissement inexistant, un établissement du bon tenant
auquel le compte n'est pas rattaché. Comparer les trois réponses ne doit rien apprendre.
"""

import uuid
from datetime import date, timedelta

import pytest

from modules.socle import annees, habilitations, tenants
from tests.authentification.outils import en_tetes

CHEMIN = "/api/v1/parametres"


async def lire(client, session, etablissement_id) -> object:
    return await client.get(CHEMIN, headers=en_tetes(session, etablissement_id))


async def test_l_etablissement_rattache_passe(client, sessions_ab, tenants_ab):
    reponse = await lire(client, sessions_ab.a, tenants_ab.etab_a)
    assert reponse.status_code == 200, reponse.text


@pytest.mark.parametrize("valeur", [None, "", "abc", "12345"])
async def test_en_tete_absent_ou_malforme_est_un_400(client, sessions_ab, valeur):
    en_tetes_essai = {"Authorization": f"Bearer {sessions_ab.a.jeton}"}
    if valeur is not None:
        en_tetes_essai["X-Nelo-Etablissement"] = valeur
    reponse = await client.get(CHEMIN, headers=en_tetes_essai)
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "TEN_ETABLISSEMENT_REQUIS"


async def test_le_400_rappelle_au_compte_ses_propres_rattachements(client, sessions_ab, tenants_ab):
    """Une donnée du compte lui-même, jamais d'un tiers : où **il** travaille."""
    reponse = await client.get(CHEMIN, headers={"Authorization": f"Bearer {sessions_ab.a.jeton}"})
    assert reponse.json()["details"]["etablissements"] == [str(tenants_ab.etab_a)]


async def test_les_trois_refus_sont_indistinguables(client, sessions_ab, tenants_ab):
    """Un autre tenant, un inexistant, un non rattaché : la même réponse, au mot près."""
    non_rattache = await tenants.creer_etablissement(
        tenants_ab.tenant_a, "École A2", "Africa/Abidjan"
    )
    reponses = [
        await lire(client, sessions_ab.a, tenants_ab.etab_b),
        await lire(client, sessions_ab.a, uuid.uuid7()),
        await lire(client, sessions_ab.a, non_rattache),
    ]
    corps = []
    for reponse in reponses:
        assert reponse.status_code == 403
        charge = reponse.json()
        assert charge["code"] == "TEN_ETABLISSEMENT_NON_AUTORISE"
        charge.pop("requete_id", None)
        corps.append(charge)
    assert corps[0] == corps[1] == corps[2]


async def test_une_affectation_terminee_ne_rattache_plus(client, sessions_ab, tenants_ab):
    """Vivante veut dire commencée et pas encore finie : `fin` est exclue."""
    second = await tenants.creer_etablissement(tenants_ab.tenant_a, "École A3", "Africa/Abidjan")
    annee = await annees.creer_annee(
        tenants_ab.tenant_a,
        second,
        "2026-2027",
        date.today() - timedelta(days=400),
        date.today() + timedelta(days=100),
        "active",
    )
    await habilitations.creer_affectation(
        tenants_ab.tenant_a,
        tenants_ab.compte_a,
        annee,
        second,
        date.today() - timedelta(days=300),
        date.today(),
    )
    reponse = await lire(client, sessions_ab.a, second)
    assert reponse.status_code == 403


async def test_une_affectation_qui_commence_demain_ne_rattache_pas_encore(
    client, sessions_ab, tenants_ab
):
    second = await tenants.creer_etablissement(tenants_ab.tenant_a, "École A4", "Africa/Abidjan")
    annee = await annees.creer_annee(
        tenants_ab.tenant_a,
        second,
        "2027-2028",
        date.today() + timedelta(days=1),
        date.today() + timedelta(days=300),
        "active",
    )
    await habilitations.creer_affectation(
        tenants_ab.tenant_a,
        tenants_ab.compte_a,
        annee,
        second,
        date.today() + timedelta(days=1),
        None,
    )
    assert (await lire(client, sessions_ab.a, second)).status_code == 403
