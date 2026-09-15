"""docs/03-api.md § 1.2 — X-Nelo-Requete est lu par un middleware : 400, jamais 422."""

import uuid

import pytest

CHEMIN = "/api/v1/parametres/assistance.suspendue"
CHAMPS = {"code", "message", "champ", "details", "requete_id"}


def corps(etab):
    return {"portee": "ETABLISSEMENT", "portee_id": str(etab), "valeur": True}


async def test_sans_en_tete(client, tenants_ab):
    reponse = await client.put(
        CHEMIN,
        headers={"X-Nelo-Etablissement": str(tenants_ab.etab_a)},
        json=corps(tenants_ab.etab_a),
    )
    assert reponse.status_code == 400
    assert set(reponse.json()) == CHAMPS
    assert reponse.json()["code"] == "REQUETE_CLE_MANQUANTE"
    assert reponse.json()["requete_id"] is None


@pytest.mark.parametrize("valeur", [str(uuid.uuid4()), "abc"])
async def test_pas_un_uuid_v7(client, tenants_ab, valeur):
    reponse = await client.put(
        CHEMIN,
        headers={"X-Nelo-Etablissement": str(tenants_ab.etab_a), "X-Nelo-Requete": valeur},
        json=corps(tenants_ab.etab_a),
    )
    assert reponse.status_code == 400
    assert set(reponse.json()) == CHAMPS
    assert reponse.json()["code"] == "REQUETE_CLE_INVALIDE"
    assert reponse.json()["requete_id"] == valeur


async def test_une_lecture_n_exige_rien(client, tenants_ab):
    reponse = await client.get(
        "/api/v1/parametres", headers={"X-Nelo-Etablissement": str(tenants_ab.etab_a)}
    )
    assert reponse.status_code == 200
