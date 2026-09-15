"""US6 — une dépendance indisponible répond 503 avec l'enveloppe, sur une route déclarée par le test."""

from datetime import timedelta

import httpx

from api.main import creer_application
from modules.shared import ModeSimulation
from modules.socle.communication import SimulationPasserelleSms


async def test_503_avec_enveloppe(moteur_application, tenants_ab, requete_id):
    application = creer_application()
    passerelle = SimulationPasserelleSms(ModeSimulation.INDISPONIBLE, timedelta(milliseconds=10))

    async def essai_dependance():
        await passerelle.envoyer("+2250700000000", "essai", requete_id)

    application.add_api_route("/essai-dependance", essai_dependance, methods=["GET"])
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as client:
        reponse = await client.get(
            "/api/v1/essai-dependance",
            headers={"X-Nelo-Etablissement": str(tenants_ab.etab_a), "X-Nelo-Requete": requete_id},
        )
    assert reponse.status_code == 503
    corps = reponse.json()
    assert corps["code"] == "API_DEPENDANCE_INDISPONIBLE"
    assert corps["details"] == {"dependance": "PASSERELLE_SMS"}
    assert corps["requete_id"] == requete_id
    assert set(corps) == {"code", "message", "champ", "details", "requete_id"}
