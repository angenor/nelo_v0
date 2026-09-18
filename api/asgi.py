"""Les utilitaires que partagent les middlewares ASGI purs.

Repris de l'ancien `api/tenant_provisoire.py` : les chemins que personne n'a à traverser, la
lecture d'un en-tête depuis le `scope`, et le chemin d'une route sans son préfixe de montage.

**Les chemins libres** sont la seule liste devant laquelle le middleware de session s'efface. Elle
est courte, et chaque entrée se justifie : la sonde, la documentation, et les routes par lesquelles
on ouvre une session, puisqu'on ne peut pas exiger une session pour en obtenir une.
"""

from starlette.types import Scope

CHEMINS_LIBRES = frozenset(
    {
        "/sante",
        "/openapi.json",
        "/docs",
        "/docs/oauth2-redirect",
        "/redoc",
    }
)

# Les préfixes libres : les routes d'ouverture de session. `/auth/pin/definition` en est
# **exclue** : changer son code personnel exige d'être déjà connecté.
PREFIXES_LIBRES = (
    "/auth/otp",
    "/auth/pin",
    "/auth/rafraichissement",
    "/auth/invitation/",
    "/auth/appareil",
)
PREFIXES_PROTEGES = ("/auth/pin/definition",)

# Protégées par la session, mais **sans établissement** : elles parlent du compte lui-même, pas
# d'une école. Exiger un établissement pour définir son code personnel ou changer son numéro
# obligerait à en choisir un avant d'avoir de quoi le faire.
PREFIXES_SANS_ETABLISSEMENT = ("/auth/", "/moi/telephone")


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


def exige_un_etablissement(chemin: str) -> bool:
    """Vrai si la route parle des données d'un établissement, et doit donc savoir lequel."""
    return not est_libre(chemin) and not chemin.startswith(PREFIXES_SANS_ETABLISSEMENT)


def est_libre(chemin: str) -> bool:
    """Vrai si le chemin se traverse sans session."""
    if any(chemin.startswith(prefixe) for prefixe in PREFIXES_PROTEGES):
        return False
    return chemin in CHEMINS_LIBRES or any(
        chemin == prefixe or chemin.startswith(prefixe) for prefixe in PREFIXES_LIBRES
    )
