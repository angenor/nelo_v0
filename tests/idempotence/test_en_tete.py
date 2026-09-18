"""docs/03-api.md § 1.2 : X-Nelo-Requete est lu par un middleware : 400, jamais 422.

La session est ouverte dans chacun de ces tests, et l'établissement est celui du compte : sans
cela, le refus tomberait plus tôt, en `401` ou en `400 TEN_ETABLISSEMENT_REQUIS`, et le middleware
d'idempotence ne serait jamais atteint. Ce qui est mesuré ici est bien le refus de la clé de
requête, et lui seul.
"""

import uuid

import pytest

from tests.authentification.outils import en_tetes

CHEMIN = "/api/v1/parametres/assistance.suspendue"
CHAMPS = {"code", "message", "champ", "details", "requete_id"}


def corps(etab):
    return {"portee": "ETABLISSEMENT", "portee_id": str(etab), "valeur": True}


async def test_sans_en_tete(client, sessions_ab, tenants_ab):
    reponse = await client.put(
        CHEMIN,
        headers=en_tetes(sessions_ab.a, tenants_ab.etab_a),
        json=corps(tenants_ab.etab_a),
    )
    assert reponse.status_code == 400
    assert set(reponse.json()) == CHAMPS
    assert reponse.json()["code"] == "REQUETE_CLE_MANQUANTE"
    assert reponse.json()["requete_id"] is None


@pytest.mark.parametrize("valeur", [str(uuid.uuid4()), "abc"])
async def test_pas_un_uuid_v7(client, sessions_ab, tenants_ab, valeur):
    reponse = await client.put(
        CHEMIN,
        headers={
            **en_tetes(sessions_ab.a, tenants_ab.etab_a),
            "X-Nelo-Requete": valeur,
        },
        json=corps(tenants_ab.etab_a),
    )
    assert reponse.status_code == 400
    assert set(reponse.json()) == CHAMPS
    assert reponse.json()["code"] == "REQUETE_CLE_INVALIDE"
    assert reponse.json()["requete_id"] == valeur


async def test_une_lecture_n_exige_rien(client, sessions_ab, tenants_ab):
    reponse = await client.get(
        "/api/v1/parametres", headers=en_tetes(sessions_ab.a, tenants_ab.etab_a)
    )
    assert reponse.status_code == 200
