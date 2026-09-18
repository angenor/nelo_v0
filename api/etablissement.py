"""Le middleware d'établissement : `X-Nelo-Etablissement` contre les affectations du compte.

Deux refus, et ils ne disent pas la même chose (docs/03-api.md § 1.2) :

- en-tête absent ou malformé : `400 TEN_ETABLISSEMENT_REQUIS`, le client n'a pas posé la question ;
- en-tête bien formé mais sans affectation vivante : `403 TEN_ETABLISSEMENT_NON_AUTORISE`.

Ce `403` est **la seule exception** au principe « hors périmètre, c'est introuvable » : l'en-tête
d'établissement est nommé par le principe XII. Il est identique que l'établissement soit d'un
autre tenant, inexistant, ou simplement non rattaché : la requête ne les distingue pas, et c'est
voulu. Comparer les trois réponses ne doit rien apprendre.

Le tenant vient **du compte de la session**, jamais de l'en-tête : une session du tenant A qui
présente un établissement du tenant B ne voit rien, et se fait refuser avant même de chercher.

Les routes qui parlent du compte lui-même (`/auth/*`, `/moi/telephone*`) n'en exigent aucun : on ne
choisit pas une école pour définir son code personnel.
"""

from uuid import UUID

from starlette.types import ASGIApp, Receive, Scope, Send

from api.asgi import chemin_de_route, en_tete, exige_un_etablissement
from api.erreurs import envoyer_erreur_asgi
from modules.socle import habilitations


def _uuid_ou_none(brut: str | None) -> UUID | None:
    if brut is None:
        return None
    try:
        return UUID(brut)
    except ValueError:
        return None


class Etablissement:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not exige_un_etablissement(chemin_de_route(scope)):
            await self.app(scope, receive, send)
            return
        etat = scope.setdefault("state", {})
        etablissement_id = _uuid_ou_none(en_tete(scope, b"x-nelo-etablissement"))
        if etablissement_id is None:
            await envoyer_erreur_asgi(
                send,
                400,
                "TEN_ETABLISSEMENT_REQUIS",
                "l'en-tête X-Nelo-Etablissement est absent ou n'est pas un UUID",
                etat.get("requete_id"),
                details=await _rattachements_du_compte(etat),
            )
            return

        if not await habilitations.affectation_vivante(
            etat["tenant_id"], etat["compte_id"], etablissement_id
        ):
            await envoyer_erreur_asgi(
                send,
                403,
                "TEN_ETABLISSEMENT_NON_AUTORISE",
                "le compte n'est pas affecté à cet établissement",
                etat.get("requete_id"),
            )
            return

        etat["etablissement_id"] = etablissement_id
        await self.app(scope, receive, send)


async def _rattachements_du_compte(etat: dict) -> dict:
    """Les établissements du compte lui-même, pour que le client sache lequel demander.

    C'est une donnée du compte, jamais d'un tiers : il ne s'agit pas de dire ce qui existe, mais
    de rappeler à quelqu'un où il travaille (diff sur docs/03-api.md § 1.2, ajouté par T1a).
    """
    if "compte_id" not in etat:
        return {}
    attaches = await habilitations.rattachements(etat["tenant_id"], etat["compte_id"])
    return {
        "etablissements": sorted({str(rattachement.etablissement_id) for rattachement in attaches})
    }
