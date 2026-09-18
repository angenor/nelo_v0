"""L'idempotence des écritures — `X-Nelo-Requete`, docs/03-api.md § 1.3, research.md R-06.

Middleware ASGI pur, placé **à l'intérieur** du middleware d'établissement : le tenant est connu,
et la mémorisation lui est bornée. La réponse d'une écriture est mémorisée 24 h dans Valkey sous
`idem:{tenant_id}:{requete_id}`, ou `idem:auth:{requete_id}` sur un chemin libre, avant qu'un
tenant ne soit connu :

- clé inconnue → l'écriture s'exécute, sa réponse est mémorisée ;
- même clé, même empreinte, exécution terminée → la réponse mémorisée est rendue, rien ne se
  réexécute ;
- même clé, autre empreinte → `409 REQUETE_REJOUEE_DIFFEREMMENT` ;
- même clé, première exécution non terminée → `409 REQUETE_EN_COURS`.

L'empreinte est un SHA-256 de la méthode, du chemin et du corps brut. Perdre Valkey dégrade en
réexécution, jamais en corruption (ADR 007).
"""

import base64
import hashlib
import json
from datetime import timedelta
from uuid import UUID

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from api.erreurs import envoyer_erreur_asgi

METHODES_ECRITURE = frozenset({"POST", "PUT", "PATCH", "DELETE"})
DUREE = timedelta(hours=24)


def est_uuid_v7(valeur: str) -> bool:
    try:
        return UUID(valeur).version == 7
    except ValueError:
        return False


async def lire_corps(receive: Receive) -> bytes:
    morceaux = []
    while True:
        message = await receive()
        if message["type"] != "http.request":
            break
        morceaux.append(message.get("body", b""))
        if not message.get("more_body", False):
            break
    return b"".join(morceaux)


class Idempotence:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in METHODES_ECRITURE:
            await self.app(scope, receive, send)
            return
        etat = scope.setdefault("state", {})
        requete_id = etat.get("requete_id")
        if requete_id is None:
            await envoyer_erreur_asgi(
                send, 400, "REQUETE_CLE_MANQUANTE", "l'en-tête X-Nelo-Requete est absent", None
            )
            return
        if not est_uuid_v7(requete_id):
            await envoyer_erreur_asgi(
                send,
                400,
                "REQUETE_CLE_INVALIDE",
                "l'en-tête X-Nelo-Requete n'est pas un UUID v7",
                requete_id,
            )
            return

        valkey = scope["app"].state.valkey
        # Sur un chemin libre, aucun tenant n'est connu : la personne n'est pas encore
        # entrée. La mémorisation est alors globale, et c'est sans danger : la clé de requête
        # est tirée au hasard par le client.
        portee = etat["tenant_id"] if "tenant_id" in etat else "auth"
        cle = f"idem:{portee}:{requete_id}"
        corps = await lire_corps(receive)
        empreinte = hashlib.sha256(
            scope["method"].encode() + b" " + scope["path"].encode() + b"\n" + corps
        ).hexdigest()

        marqueur = json.dumps({"en_cours": True, "empreinte": empreinte})
        if not await valkey.set(cle, marqueur, nx=True, ex=DUREE):
            memorisee = await valkey.get(cle)
            if memorisee is not None:
                await self._rejouer(json.loads(memorisee), empreinte, requete_id, send)
                return
            # La clé a expiré entre les deux lectures : on la reprend.
            await valkey.set(cle, marqueur, ex=DUREE)

        await self._executer(scope, corps, receive, send, valkey, cle, empreinte)

    async def _rejouer(self, memorisee: dict, empreinte: str, requete_id: str, send: Send) -> None:
        if memorisee["en_cours"]:
            await envoyer_erreur_asgi(
                send,
                409,
                "REQUETE_EN_COURS",
                "la première exécution de cette requête n'est pas terminée",
                requete_id,
            )
            return
        if memorisee["empreinte"] != empreinte:
            await envoyer_erreur_asgi(
                send,
                409,
                "REQUETE_REJOUEE_DIFFEREMMENT",
                "cette clé de requête a déjà servi pour une autre requête",
                requete_id,
            )
            return
        await send(
            {
                "type": "http.response.start",
                "status": memorisee["statut"],
                "headers": [
                    (base64.b64decode(n), base64.b64decode(v)) for n, v in memorisee["en_tetes"]
                ],
            }
        )
        await send({"type": "http.response.body", "body": base64.b64decode(memorisee["corps"])})

    async def _executer(
        self, scope: Scope, corps: bytes, receive: Receive, send: Send, valkey, cle, empreinte
    ) -> None:
        corps_rendu = False

        async def rejouer_corps() -> Message:
            nonlocal corps_rendu
            if not corps_rendu:
                corps_rendu = True
                return {"type": "http.request", "body": corps, "more_body": False}
            return await receive()

        debut: Message = {}
        morceaux: list[bytes] = []

        async def capturer(message: Message) -> None:
            nonlocal debut
            if message["type"] == "http.response.start":
                debut = message
            elif message["type"] == "http.response.body":
                morceaux.append(message.get("body", b""))
                if not message.get("more_body", False):
                    await valkey.set(
                        cle,
                        json.dumps(
                            {
                                "en_cours": False,
                                "empreinte": empreinte,
                                "statut": debut["status"],
                                "en_tetes": [
                                    [base64.b64encode(n).decode(), base64.b64encode(v).decode()]
                                    for n, v in debut.get("headers", [])
                                ],
                                "corps": base64.b64encode(b"".join(morceaux)).decode(),
                            }
                        ),
                        ex=DUREE,
                    )
            await send(message)

        try:
            await self.app(scope, rejouer_corps, capturer)
        except BaseException:
            # Une exécution interrompue ne laisse pas de marqueur : un rejeu la réexécutera.
            await valkey.delete(cle)
            raise
