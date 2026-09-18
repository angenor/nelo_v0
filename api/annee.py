"""Le middleware d'année : `X-Nelo-Annee` sur les routes qui parlent de pédagogie.

L'année n'est pas un filtre, c'est une clé : **toute entité pédagogique porte son année**
(principe VII). Une route pédagogique sans en-tête d'année est un `400`, **jamais** un repli sur
l'année active : un repli silencieux écrirait une note dans l'année d'à côté, et personne ne le
verrait avant les bulletins.

`ROUTES_PEDAGOGIQUES` est alimentée par les routeurs qui en livrent : elle est **vide en T1a**,
et un test enregistre une route d'essai pour exercer les trois refus, afin que la règle existe
avant la première route qui en dépend.
"""

import re
from uuid import UUID

from starlette.types import ASGIApp, Receive, Scope, Send

from api.asgi import chemin_de_route, en_tete, exige_un_etablissement
from api.erreurs import envoyer_erreur_asgi
from modules.socle import habilitations

# Des motifs de chemin, comparés par `re.fullmatch` au chemin de la route sans son préfixe.
ROUTES_PEDAGOGIQUES: set[str] = set()


def est_pedagogique(chemin: str) -> bool:
    return any(re.fullmatch(motif, chemin) for motif in ROUTES_PEDAGOGIQUES)


class Annee:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        chemin = chemin_de_route(scope)
        if not exige_un_etablissement(chemin):
            await self.app(scope, receive, send)
            return
        etat = scope.setdefault("state", {})
        brut = en_tete(scope, b"x-nelo-annee")
        pedagogique = est_pedagogique(chemin)

        if brut is None:
            if pedagogique:
                await envoyer_erreur_asgi(
                    send,
                    400,
                    "ANN_ANNEE_REQUISE",
                    "l'en-tête X-Nelo-Annee est absent sur une route pédagogique",
                    etat.get("requete_id"),
                )
                return
            await self.app(scope, receive, send)
            return

        try:
            annee_id = UUID(brut)
        except ValueError:
            # Un en-tête malformé est refusé partout, pédagogique ou non : il dit une intention
            # que le serveur ne sait pas lire.
            await envoyer_erreur_asgi(
                send,
                400,
                "ANN_ANNEE_REQUISE",
                "l'en-tête X-Nelo-Annee n'est pas un UUID",
                etat.get("requete_id"),
            )
            return

        if not await habilitations.affectation_vivante(
            etat["tenant_id"], etat["compte_id"], etat["etablissement_id"], annee_id
        ):
            # Introuvable, et non « interdit » : une année hors du périmètre du compte n'a pas à
            # se signaler comme existante.
            await envoyer_erreur_asgi(
                send,
                404,
                "TEN_RESSOURCE_INTROUVABLE",
                "année introuvable dans le périmètre du compte",
                etat.get("requete_id"),
            )
            return

        etat["annee_id"] = annee_id
        await self.app(scope, receive, send)
