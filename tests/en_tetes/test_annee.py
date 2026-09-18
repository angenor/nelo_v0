"""US2 : sur une route pédagogique, l'année est exigée, jamais devinée.

Un repli silencieux sur l'année active écrirait une note dans l'année d'à côté, et personne ne le
verrait avant les bulletins. La règle vaut **même quand le compte n'est rattaché qu'à une seule
année** : c'est exactement le cas où le repli serait tentant.

Aucune route pédagogique n'existe en T1a. La suite en enregistre une, d'essai, sur une
application neuve : la règle doit exister avant la première route qui en dépend.
"""

import uuid

import httpx
import pytest
import pytest_asyncio

from api.annee import ROUTES_PEDAGOGIQUES
from api.main import creer_application
from tests.authentification.outils import en_tetes

CHEMIN_PEDAGOGIQUE = "/essai-pedagogique"
CHEMIN_ORDINAIRE = "/essai-ordinaire"


@pytest_asyncio.fixture
async def client_avec_route_d_essai(moteur_application):
    """Une application neuve, deux routes d'essai, dont une déclarée pédagogique."""
    application = creer_application()

    async def essai() -> dict:
        return {"etat": "OK"}

    application.add_api_route(CHEMIN_PEDAGOGIQUE, essai, methods=["GET"])
    application.add_api_route(CHEMIN_ORDINAIRE, essai, methods=["GET"])
    ROUTES_PEDAGOGIQUES.add(CHEMIN_PEDAGOGIQUE)
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as client:
        yield client
    ROUTES_PEDAGOGIQUES.discard(CHEMIN_PEDAGOGIQUE)


async def appeler(client, session, etablissement_id, annee_id=None, chemin=CHEMIN_PEDAGOGIQUE):
    return await client.get(
        f"/api/v1{chemin}", headers=en_tetes(session, etablissement_id, annee_id=annee_id)
    )


async def test_l_annee_rattachee_passe(client_avec_route_d_essai, sessions_ab, tenants_ab):
    reponse = await appeler(
        client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a, tenants_ab.annee_a
    )
    assert reponse.status_code == 200, reponse.text


async def test_absente_sur_une_route_pedagogique_est_un_400(
    client_avec_route_d_essai, sessions_ab, tenants_ab
):
    """Même avec une seule année rattachée : c'est là que le repli serait tentant."""
    reponse = await appeler(client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a)
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "ANN_ANNEE_REQUISE"


@pytest.mark.parametrize("chemin", [CHEMIN_PEDAGOGIQUE, CHEMIN_ORDINAIRE])
async def test_malformee_est_refusee_partout(
    client_avec_route_d_essai, sessions_ab, tenants_ab, chemin
):
    reponse = await client_avec_route_d_essai.get(
        f"/api/v1{chemin}",
        headers={
            **en_tetes(sessions_ab.a, tenants_ab.etab_a),
            "X-Nelo-Annee": "pas-un-uuid",
        },
    )
    assert reponse.status_code == 400
    assert reponse.json()["code"] == "ANN_ANNEE_REQUISE"


async def test_une_route_ordinaire_ignore_l_absence(
    client_avec_route_d_essai, sessions_ab, tenants_ab
):
    reponse = await appeler(
        client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a, chemin=CHEMIN_ORDINAIRE
    )
    assert reponse.status_code == 200, reponse.text


async def test_l_annee_d_un_autre_tenant_est_introuvable(
    client_avec_route_d_essai, sessions_ab, tenants_ab
):
    reponse = await appeler(
        client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a, tenants_ab.annee_b
    )
    assert reponse.status_code == 404
    assert reponse.json()["code"] == "TEN_RESSOURCE_INTROUVABLE"


async def test_une_annee_inexistante_est_introuvable(
    client_avec_route_d_essai, sessions_ab, tenants_ab
):
    reponse = await appeler(
        client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a, uuid.uuid7()
    )
    assert reponse.status_code == 404


async def test_une_annee_du_bon_tenant_mais_d_un_autre_etablissement_est_introuvable(
    client_avec_route_d_essai, sessions_ab, tenants_ab
):
    """US2-9 : le couple établissement et année est vérifié, pas chacun de son côté."""
    from datetime import date

    from modules.socle import annees, habilitations
    from modules.socle import tenants as module_tenants

    second = await module_tenants.creer_etablissement(
        tenants_ab.tenant_a, "École A5", "Africa/Abidjan"
    )
    annee_ailleurs = await annees.creer_annee(
        tenants_ab.tenant_a, second, "2026-2027", date(2026, 9, 1), date(2027, 7, 31), "active"
    )
    await habilitations.creer_affectation(
        tenants_ab.tenant_a, tenants_ab.compte_a, annee_ailleurs, second, date.today(), None
    )
    reponse = await appeler(
        client_avec_route_d_essai, sessions_ab.a, tenants_ab.etab_a, annee_ailleurs
    )
    assert reponse.status_code == 404
