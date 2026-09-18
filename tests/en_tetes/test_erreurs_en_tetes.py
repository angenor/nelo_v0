"""Une erreur métier porte ses en-têtes jusqu'à la réponse : `Retry-After` sur une limite de débit.

Le module dit ce que le protocole exige, `api/` le pose. Deux chemins existent : le gestionnaire
d'exception de FastAPI, et le refus d'un middleware ASGI pur, avant que FastAPI ne voie la requête.
"""

import httpx
import pytest
from fastapi import FastAPI

from api import erreurs
from api.erreurs import envoyer_erreur_asgi
from modules.shared import ErreurMetier


@pytest.fixture
def application_d_essai() -> FastAPI:
    application = FastAPI()

    @application.get("/essai")
    async def essai() -> None:
        raise ErreurMetier(
            "API_LIMITE_DEBIT",
            "trop de demandes",
            statut=429,
            en_tetes={"Retry-After": "42"},
        )

    erreurs.installer(application)
    return application


async def test_l_en_tete_sort_avec_le_refus_metier(application_d_essai: FastAPI):
    transport = httpx.ASGITransport(app=application_d_essai, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as client:
        reponse = await client.get("/essai")
    assert reponse.status_code == 429
    assert reponse.headers["retry-after"] == "42"
    assert reponse.json()["code"] == "API_LIMITE_DEBIT"


async def test_une_erreur_sans_en_tete_n_en_pose_aucun():
    application = FastAPI()

    @application.get("/essai")
    async def essai() -> None:
        raise ErreurMetier("TEN_VALEUR_INVALIDE", "valeur refusée")

    erreurs.installer(application)
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as client:
        reponse = await client.get("/essai")
    assert reponse.status_code == 422
    assert "retry-after" not in reponse.headers


async def test_le_refus_asgi_pose_aussi_ses_en_tetes():
    """Le chemin des middlewares purs : la réponse est construite à la main."""
    envoyes = []

    async def send(message) -> None:
        envoyes.append(message)

    await envoyer_erreur_asgi(
        send, 429, "API_LIMITE_DEBIT", "trop de demandes", None, en_tetes={"Retry-After": "7"}
    )
    en_tetes = dict(envoyes[0]["headers"])
    assert en_tetes[b"Retry-After"] == b"7"
    assert envoyes[0]["status"] == 429
