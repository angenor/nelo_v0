"""Le middleware de session : la première frontière, avant que FastAPI ne voie la requête.

Trois refus, tous `401`, et rien d'autre (docs/03-api.md § 1.2) :

- `Authorization` absent, ou sans `Bearer` : `AUT_JETON_MANQUANT` ;
- signature fausse, jeton mal formé ou expiré : `AUT_JETON_INVALIDE` ;
- session absente de Valkey, compte différent, **ou compte suspendu** : `AUT_SESSION_REVOQUEE`.

Ce troisième refus est **la liste de révocation, consultée à chaque requête** (FR-026) : suspendre
un compte efface ses sessions, et la requête suivante tombe, jeton encore valable ou non. Le
statut du compte est relu avec elle, pour que la suspension tienne même si l'effacement des
sessions n'a pas eu lieu.

Le middleware ne décide d'aucune règle métier : il lit un en-tête, vérifie une signature, consulte
Valkey, et dépose `compte_id`, `tenant_id` et `session_id` dans l'état de la requête.
"""

from starlette.types import ASGIApp, Receive, Scope, Send

from api.asgi import chemin_de_route, en_tete, est_libre
from api.erreurs import envoyer_erreur_asgi
from modules.socle import habilitations
from modules.socle.habilitations import session as session_module

PREFIXE = "Bearer "


class Session:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        etat = scope.setdefault("state", {})
        # Le middleware le plus extérieur pose la clé de requête : les refus qui suivent la
        # portent, et le client retrouve sa trace même quand rien n'a été exécuté.
        etat["requete_id"] = en_tete(scope, b"x-nelo-requete")

        if est_libre(chemin_de_route(scope)):
            await self.app(scope, receive, send)
            return

        entete = en_tete(scope, b"authorization")
        if entete is None or not entete.startswith(PREFIXE):
            await envoyer_erreur_asgi(
                send,
                401,
                "AUT_JETON_MANQUANT",
                "l'en-tête Authorization est absent ou ne porte pas de jeton Bearer",
                etat["requete_id"],
            )
            return

        configuration = scope["app"].state.configuration
        try:
            jeton = session_module.verifier_jeton_acces(
                entete.removeprefix(PREFIXE).strip(), configuration.secret_jeton
            )
        except ValueError:
            # La raison exacte ne sort pas : elle n'apprendrait rien à une personne légitime.
            await envoyer_erreur_asgi(
                send,
                401,
                "AUT_JETON_INVALIDE",
                "le jeton d'accès est invalide ou expiré",
                etat["requete_id"],
            )
            return

        valkey = scope["app"].state.valkey
        if not await habilitations.session_valide(
            jeton.session_id, jeton.compte_id, jeton.tenant_id, valkey=valkey
        ):
            await envoyer_erreur_asgi(
                send,
                401,
                "AUT_SESSION_REVOQUEE",
                "la session n'existe plus",
                etat["requete_id"],
            )
            return

        etat["compte_id"] = jeton.compte_id
        etat["tenant_id"] = jeton.tenant_id
        etat["session_id"] = jeton.session_id
        await self.app(scope, receive, send)
