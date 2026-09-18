"""US3-4, l'événement s'écrit dans la transaction du changement d'état : un échec emporte tout."""

from sqlalchemy import text

from modules.shared import transaction
from modules.socle.tenants import acces
from tests.module_dore.outils import poser


async def test_rollback_n_ecrit_aucun_evenement(
    client, sessions_ab, tenants_ab, valkey, monkeypatch
):
    inserer_evenement = acces.inserer_evenement

    async def puis_echoue(*args, **kwargs):
        await inserer_evenement(*args, **kwargs)
        raise RuntimeError("panne simulée : SELECT secret FROM tenants.parametre_valeur")

    monkeypatch.setattr(acces, "inserer_evenement", puis_echoue)
    reponse = await poser(
        client,
        sessions_ab.a,
        tenants_ab.etab_a,
        "absence.delai_notification_minutes",
        "ETABLISSEMENT",
        tenants_ab.etab_a,
        40,
    )
    assert reponse.status_code == 500
    corps = reponse.json()
    assert corps["code"] == "API_ERREUR_INTERNE"
    assert "SELECT" not in corps["message"] and "panne" not in corps["message"]
    assert corps["details"] == {}

    async with transaction(tenants_ab.tenant_a) as connexion:
        assert (
            await connexion.scalar(
                text(
                    "SELECT count(*) FROM tenants.evenement_outbox WHERE charge->>'cle' = 'absence.delai_notification_minutes'"
                )
            )
            == 0
        )
        assert (
            await connexion.scalar(
                text(
                    "SELECT count(*) FROM tenants.parametre_valeur WHERE cle = 'absence.delai_notification_minutes'"
                )
            )
            == 0
        )
