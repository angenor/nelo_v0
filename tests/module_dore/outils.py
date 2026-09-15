"""Petits outils partagés par les tests du module doré."""

import uuid
from uuid import UUID

import httpx

PREFIXE = "/api/v1"


def en_tetes(etablissement_id: UUID, *, ecriture: bool = False) -> dict[str, str]:
    en_tetes = {"X-Nelo-Etablissement": str(etablissement_id)}
    if ecriture:
        en_tetes["X-Nelo-Requete"] = str(uuid.uuid7())
    return en_tetes


async def poser(
    client: httpx.AsyncClient,
    etablissement_id: UUID,
    cle: str,
    portee: str,
    portee_id: UUID,
    valeur,
) -> httpx.Response:
    return await client.put(
        f"{PREFIXE}/parametres/{cle}",
        headers=en_tetes(etablissement_id, ecriture=True),
        json={"portee": portee, "portee_id": str(portee_id), "valeur": valeur},
    )


async def lire(client: httpx.AsyncClient, etablissement_id: UUID) -> dict[str, dict]:
    reponse = await client.get(f"{PREFIXE}/parametres", headers=en_tetes(etablissement_id))
    assert reponse.status_code == 200, reponse.text
    return {p["cle"]: p for p in reponse.json()["parametres"]}
