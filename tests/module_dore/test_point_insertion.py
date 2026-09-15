"""R-16 — la route d'écriture traverse le point d'insertion de capacité ; la sonde, jamais."""

from api import capacites
from tests.module_dore.outils import poser


async def test_la_route_put_exige_sa_capacite(client, tenants_ab, monkeypatch):
    appels: list[str] = []
    monkeypatch.setattr(capacites, "exiger_capacite", appels.append)

    reponse = await poser(
        client, tenants_ab.etab_a, "assistance.suspendue", "ETABLISSEMENT", tenants_ab.etab_a, True
    )
    assert reponse.status_code == 200, reponse.text
    assert appels == ["tenant.parametre.definir"]

    await client.get("/api/v1/sante")
    assert appels == ["tenant.parametre.definir"]
