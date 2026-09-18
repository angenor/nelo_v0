"""US2 : ce qui se traverse sans session est une liste courte, et tout le reste répond 401.

Le parcours est mécanique : on interroge **chaque** route enregistrée, et on vérifie qu'aucune ne
s'est glissée hors de la liste. Une route ajoutée demain sans y penser fera tomber ce test.
"""

import pytest
from fastapi.routing import APIRoute

from api.asgi import est_libre

PREFIXE = "/api/v1"


def routes(application) -> list[tuple[str, str]]:
    """Chaque route enregistrée, routeurs inclus compris : la liste vient de l'application.

    Elle n'est écrite nulle part : une route ajoutée demain sans y penser apparaît ici d'office.
    """
    trouvees = []

    def parcourir(niveau) -> None:
        for route in niveau:
            if isinstance(route, APIRoute):
                trouvees.extend(
                    (route.path, methode) for methode in sorted(route.methods - {"HEAD", "OPTIONS"})
                )
            # Un routeur inclus range ses routes derrière `original_router` ; les versions
            # antérieures les plaçaient directement dans `routes`. Les deux se parcourent.
            interne = getattr(route, "original_router", None)
            parcourir(getattr(interne, "routes", None) or getattr(route, "routes", []))

    parcourir(application.routes)
    return trouvees


@pytest.mark.parametrize("chemin", ["/sante", "/openapi.json", "/docs"])
async def test_la_sonde_et_la_documentation_repondent_sans_jeton(client, chemin):
    reponse = await client.get(f"{PREFIXE}{chemin}")
    assert reponse.status_code == 200, chemin


async def test_les_routes_d_ouverture_de_session_repondent_sans_jeton(client):
    """Elles refusent peut-être la demande, mais jamais pour absence de jeton."""
    reponse = await client.post(
        f"{PREFIXE}/auth/otp",
        headers={"X-Nelo-Requete": "01900000-0000-7000-8000-000000000000"},
        json={"identifiant": "+2250700000000"},
    )
    assert reponse.status_code != 401


async def test_toute_autre_route_repond_401_sans_jeton(client, application):
    protegees = [(c, m) for c, m in routes(application) if not est_libre(c)]
    assert protegees, "aucune route protégée : le parcours ne prouverait rien"
    for chemin, methode in protegees:
        reponse = await client.request(
            methode, f"{PREFIXE}{chemin.replace('{cle}', 'assistance.suspendue')}"
        )
        assert reponse.status_code == 401, f"{methode} {chemin}"
        assert reponse.json()["code"] == "AUT_JETON_MANQUANT", f"{methode} {chemin}"


async def test_un_jeton_sans_bearer_est_un_jeton_manquant(client):
    reponse = await client.get(
        f"{PREFIXE}/parametres", headers={"Authorization": "un-jeton-tout-nu"}
    )
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_JETON_MANQUANT"


async def test_un_jeton_falsifie_est_un_jeton_invalide(client):
    reponse = await client.get(
        f"{PREFIXE}/parametres", headers={"Authorization": "Bearer eyJ-pas-un-jeton"}
    )
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_JETON_INVALIDE"


async def test_une_session_revoquee_est_refusee(client, sessions_ab, valkey, tenants_ab):
    from modules.socle.habilitations import session as session_module

    await session_module.revoquer_toutes(tenants_ab.compte_a, valkey=valkey)
    reponse = await client.get(
        f"{PREFIXE}/parametres",
        headers={
            "Authorization": f"Bearer {sessions_ab.a.jeton}",
            "X-Nelo-Etablissement": str(tenants_ab.etab_a),
        },
    )
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_SESSION_REVOQUEE"
