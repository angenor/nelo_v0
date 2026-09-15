"""US3 — SC-005 : un rejeu identique rend la même réponse sans réexécuter ; un rejeu divergent est refusé."""

import json
import uuid

from sqlalchemy import text

from modules.shared import transaction
from modules.socle import tenants

CHEMIN = "/api/v1/parametres/absence.delai_notification_minutes"


def en_tetes(etab, requete_id):
    return {"X-Nelo-Etablissement": str(etab), "X-Nelo-Requete": requete_id}


def corps(etab, valeur):
    return {"portee": "ETABLISSEMENT", "portee_id": str(etab), "valeur": valeur}


async def evenements(tenant_id) -> int:
    async with transaction(tenant_id) as connexion:
        return await connexion.scalar(
            text(
                "SELECT count(*) FROM tenants.evenement_outbox "
                "WHERE charge->>'cle' = 'absence.delai_notification_minutes'"
            )
        )


def espionner(monkeypatch) -> list:
    appels = []
    original = tenants.poser_parametre

    async def espion(*args, **kwargs):
        appels.append(args)
        return await original(*args, **kwargs)

    monkeypatch.setattr(tenants, "poser_parametre", espion)
    return appels


async def test_rejeu_identique_octet_pour_octet(
    client, tenants_ab, valkey, requete_id, monkeypatch
):
    appels = espionner(monkeypatch)
    premiere = await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_a, requete_id), json=corps(tenants_ab.etab_a, 20)
    )
    seconde = await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_a, requete_id), json=corps(tenants_ab.etab_a, 20)
    )
    assert premiere.status_code == seconde.status_code == 200
    assert premiere.content == seconde.content
    assert premiere.headers["content-type"] == seconde.headers["content-type"]
    assert len(appels) == 1
    assert await evenements(tenants_ab.tenant_a) == 1

    cle = f"idem:{tenants_ab.tenant_a}:{requete_id}"
    assert 0 < await valkey.ttl(cle) <= 24 * 3600


async def test_rejeu_divergent_refuse(client, tenants_ab, valkey, requete_id):
    await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_a, requete_id), json=corps(tenants_ab.etab_a, 20)
    )
    for _ in range(2):
        reponse = await client.put(
            CHEMIN,
            headers=en_tetes(tenants_ab.etab_a, requete_id),
            json=corps(tenants_ab.etab_a, 21),
        )
        assert reponse.status_code == 409
        assert reponse.json()["code"] == "REQUETE_REJOUEE_DIFFEREMMENT"
        assert reponse.json()["requete_id"] == requete_id
    assert await evenements(tenants_ab.tenant_a) == 1


async def test_borne_au_tenant(client, tenants_ab, valkey, requete_id):
    reponse_a = await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_a, requete_id), json=corps(tenants_ab.etab_a, 20)
    )
    reponse_b = await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_b, requete_id), json=corps(tenants_ab.etab_b, 30)
    )
    assert reponse_a.status_code == reponse_b.status_code == 200
    assert reponse_b.json()["valeur"] == 30
    assert await evenements(tenants_ab.tenant_b) == 1


async def test_rejeu_apres_expiration(client, tenants_ab, valkey, requete_id):
    for _ in range(2):
        reponse = await client.put(
            CHEMIN,
            headers=en_tetes(tenants_ab.etab_a, requete_id),
            json=corps(tenants_ab.etab_a, 20),
        )
        assert reponse.status_code == 200
        await valkey.delete(f"idem:{tenants_ab.tenant_a}:{requete_id}")
    # Valkey vidé : la réexécution pose la même valeur et écrit un second événement (ADR 007).
    assert await evenements(tenants_ab.tenant_a) == 2


async def test_requete_en_cours(client, tenants_ab, valkey, requete_id):
    await valkey.set(
        f"idem:{tenants_ab.tenant_a}:{requete_id}",
        json.dumps({"en_cours": True, "empreinte": "quelconque"}),
        ex=60,
    )
    reponse = await client.put(
        CHEMIN, headers=en_tetes(tenants_ab.etab_a, requete_id), json=corps(tenants_ab.etab_a, 20)
    )
    assert reponse.status_code == 409
    assert reponse.json()["code"] == "REQUETE_EN_COURS"
    assert await evenements(tenants_ab.tenant_a) == 0


async def test_un_refus_se_rejoue_aussi(client, tenants_ab, valkey):
    requete_id = str(uuid.uuid7())
    for _ in range(2):
        reponse = await client.put(
            CHEMIN,
            headers=en_tetes(tenants_ab.etab_a, requete_id),
            json=corps(tenants_ab.etab_a, "vingt"),
        )
        assert reponse.status_code == 422
        assert reponse.json()["code"] == "TEN_VALEUR_INVALIDE"
