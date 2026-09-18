"""US1-4 : le refus de schéma cite chaque champ fautif, et précède toute règle métier."""

from modules.socle.tenants import acces
from tests.authentification.outils import en_tetes


async def test_deux_champs_fautifs(client, sessions_ab, tenants_ab, requete_id, monkeypatch):
    appels = []
    lire_catalogue = acces.lire_catalogue

    async def espion(*args, **kwargs):
        appels.append(args)
        return await lire_catalogue(*args, **kwargs)

    monkeypatch.setattr(acces, "lire_catalogue", espion)

    reponse = await client.put(
        "/api/v1/parametres/assistance.suspendue",
        headers={
            **en_tetes(sessions_ab.a, tenants_ab.etab_a),
            "X-Nelo-Requete": requete_id,
        },
        json={"portee": "NULLE_PART", "valeur": True},
    )
    assert reponse.status_code == 422
    corps = reponse.json()
    assert corps["code"] == "VAL_SCHEMA_INVALIDE"
    chemins = [c["chemin"] for c in corps["details"]["champs"]]
    assert set(chemins) == {"portee", "portee_id"}
    assert all(c["motif"] for c in corps["details"]["champs"])
    assert corps["champ"] == chemins[0]
    assert corps["requete_id"] == requete_id
    assert appels == []
