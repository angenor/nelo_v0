"""US1-3 — poser une valeur, la relire, et l'événement écrit dans la même transaction."""

from sqlalchemy import text

from modules.shared import transaction
from tests.module_dore.outils import lire, poser

CLE = "assistance.suspendue"


async def compter_evenements(tenant_id) -> int:
    async with transaction(tenant_id) as connexion:
        return await connexion.scalar(
            text(
                "SELECT count(*) FROM tenants.evenement_outbox "
                "WHERE type = 'tenants.parametre.pose' AND charge->>'portee' = 'ETABLISSEMENT'"
            )
        )


async def test_poser_puis_relire(client, tenants_ab):
    reponse = await poser(client, tenants_ab.etab_a, CLE, "ETABLISSEMENT", tenants_ab.etab_a, True)
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["cle"] == CLE
    assert corps["portee"] == "ETABLISSEMENT"
    assert corps["portee_id"] == str(tenants_ab.etab_a)
    assert corps["valeur"] is True
    assert corps["pose_le"]

    parametre = (await lire(client, tenants_ab.etab_a))[CLE]
    assert (parametre["valeur"], parametre["source"], parametre["portee_resolue"]) == (
        True,
        "VALEUR",
        "ETABLISSEMENT",
    )

    assert await compter_evenements(tenants_ab.tenant_a) == 1
    async with transaction(tenants_ab.tenant_a) as connexion:
        charge = await connexion.scalar(
            text(
                "SELECT charge FROM tenants.evenement_outbox "
                "WHERE type = 'tenants.parametre.pose' AND charge->>'portee' = 'ETABLISSEMENT'"
            )
        )
    assert charge == {
        "cle": CLE,
        "portee": "ETABLISSEMENT",
        "portee_id": str(tenants_ab.etab_a),
        "valeur": True,
    }


async def test_second_put_met_a_jour_sans_doublon(client, tenants_ab):
    for valeur in (True, False):
        reponse = await poser(
            client, tenants_ab.etab_a, CLE, "ETABLISSEMENT", tenants_ab.etab_a, valeur
        )
        assert reponse.status_code == 200, reponse.text
    async with transaction(tenants_ab.tenant_a) as connexion:
        lignes = await connexion.scalar(
            text(
                "SELECT count(*) FROM tenants.parametre_valeur "
                "WHERE cle = :cle AND portee = 'ETABLISSEMENT'"
            ),
            {"cle": CLE},
        )
    assert lignes == 1
    assert (await lire(client, tenants_ab.etab_a))[CLE]["valeur"] is False
