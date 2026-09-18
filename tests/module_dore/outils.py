"""Petits outils partagés par les tests du module doré.

Depuis T1a, toute route hors chemins libres passe par une session : les en-têtes portent
`Authorization`, et l'établissement est celui auquel le compte de la session est rattaché.
"""

from uuid import UUID

import httpx

from tests.authentification.outils import Session, cle_de_requete

PREFIXE = "/api/v1"


def en_tetes(
    session: Session,
    etablissement_id: UUID,
    *,
    ecriture: bool = False,
    annee_id: UUID | None = None,
) -> dict[str, str]:
    en_tetes = {
        "Authorization": f"Bearer {session.jeton}",
        "X-Nelo-Etablissement": str(etablissement_id),
    }
    if annee_id is not None:
        en_tetes["X-Nelo-Annee"] = str(annee_id)
    if ecriture:
        en_tetes["X-Nelo-Requete"] = cle_de_requete()
    return en_tetes


async def poser(
    client: httpx.AsyncClient,
    session: Session,
    etablissement_id: UUID,
    cle: str,
    portee: str,
    portee_id: UUID,
    valeur,
) -> httpx.Response:
    return await client.put(
        f"{PREFIXE}/parametres/{cle}",
        headers=en_tetes(session, etablissement_id, ecriture=True),
        json={"portee": portee, "portee_id": str(portee_id), "valeur": valeur},
    )


async def lire(
    client: httpx.AsyncClient, session: Session, etablissement_id: UUID
) -> dict[str, dict]:
    reponse = await client.get(f"{PREFIXE}/parametres", headers=en_tetes(session, etablissement_id))
    assert reponse.status_code == 200, reponse.text
    return {p["cle"]: p for p in reponse.json()["parametres"]}
