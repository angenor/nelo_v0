"""La résolution du tenant depuis `X-Nelo-Etablissement` — **PROVISOIRE jusqu'à T1a**.

Middleware ASGI pur (research.md R-05, R-16). Avant l'authentification, aucun compte n'est affecté
à un établissement : l'en-tête suffit à désigner le tenant. T1a remplace cette résolution par celle
du compte authentifié, et le `403 TEN_ETABLISSEMENT_NON_AUTORISE` prend alors son objet.

- en-tête absent ou pas un UUID → `400 TEN_ETABLISSEMENT_REQUIS` ;
- établissement inconnu (ou d'un autre tenant, indistinguable) → `404 TEN_RESSOURCE_INTROUVABLE` ;
- sinon `tenant_id` et `etablissement_id` sont déposés dans l'état de la requête.

La sonde et la documentation ne le traversent pas.
"""

from collections.abc import Awaitable, Callable
from uuid import UUID

from starlette.types import ASGIApp, Receive, Scope, Send

from api.erreurs import envoyer_erreur_asgi

type Resolveur = Callable[[UUID], Awaitable[UUID | None]]

CHEMINS_LIBRES = frozenset({"/sante", "/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"})


def en_tete(scope: Scope, nom: bytes) -> str | None:
    for cle, valeur in scope.get("headers", []):
        if cle == nom:
            return valeur.decode("latin-1")
    return None


def chemin_de_route(scope: Scope) -> str:
    chemin = scope["path"]
    racine = scope.get("root_path", "")
    if racine and chemin.startswith(racine):
        chemin = chemin[len(racine) :]
    return chemin or "/"


class TenantProvisoire:
    def __init__(self, app: ASGIApp, resolveur: Resolveur) -> None:
        self.app = app
        self.resolveur = resolveur

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        etat = scope.setdefault("state", {})
        etat["requete_id"] = en_tete(scope, b"x-nelo-requete")
        if chemin_de_route(scope) in CHEMINS_LIBRES:
            await self.app(scope, receive, send)
            return

        brut = en_tete(scope, b"x-nelo-etablissement")
        try:
            etablissement_id = UUID(brut) if brut is not None else None
        except ValueError:
            etablissement_id = None
        if etablissement_id is None:
            await envoyer_erreur_asgi(
                send,
                400,
                "TEN_ETABLISSEMENT_REQUIS",
                "l'en-tête X-Nelo-Etablissement est absent ou n'est pas un UUID",
                etat["requete_id"],
            )
            return

        tenant_id = await self.resolveur(etablissement_id)
        if tenant_id is None:
            await envoyer_erreur_asgi(
                send,
                404,
                "TEN_RESSOURCE_INTROUVABLE",
                "établissement introuvable",
                etat["requete_id"],
            )
            return

        etat["tenant_id"] = tenant_id
        etat["etablissement_id"] = etablissement_id
        await self.app(scope, receive, send)
