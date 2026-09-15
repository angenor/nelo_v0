"""L'idempotence des écritures — `X-Nelo-Requete`, docs/03-api.md § 1.3, research.md R-06.

Middleware ASGI pur, placé **à l'intérieur** du middleware d'établissement : le tenant est connu,
et la mémorisation lui est bornée.
"""

from uuid import UUID

from starlette.types import ASGIApp, Receive, Scope, Send

from api.erreurs import envoyer_erreur_asgi

METHODES_ECRITURE = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def est_uuid_v7(valeur: str) -> bool:
    try:
        return UUID(valeur).version == 7
    except ValueError:
        return False


class Idempotence:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] not in METHODES_ECRITURE:
            await self.app(scope, receive, send)
            return
        requete_id = scope.setdefault("state", {}).get("requete_id")
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
        # Point d'accroche : la mémorisation Valkey (T057).
        await self.app(scope, receive, send)
