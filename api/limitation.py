"""La limitation de débit, en Valkey, avant toute lecture de la base (research.md R-05).

Deux fonctions, et rien d'autre : compter un usage dans une fenêtre glissante, et savoir de quel
client vient la requête. La **règle** (combien, sur quelle fenêtre, pour quelle clé) appartient au
service qui appelle ; `api/` ne fait que fournir le compteur.

Perdre Valkey ne coûte qu'une fenêtre : les compteurs repartent de zéro, personne n'est bloqué,
et rien n'est corrompu (ADR 007).
"""

from datetime import timedelta

from starlette.types import Scope

from api.asgi import en_tete


async def compter(valkey, cle: str, plafond: int, fenetre: timedelta) -> int | None:
    """Compte un usage de plus. Rend les secondes avant reprise si le plafond est dépassé, sinon `None`.

    `INCR` crée la clé à 1 si elle n'existe pas ; `EXPIRE ... NX` ne pose la durée qu'à la
    première, pour que la fenêtre parte du premier usage et non du dernier : sinon un client qui
    frappe sans arrêt repousserait sa propre fenêtre indéfiniment.
    """
    secondes = int(fenetre.total_seconds())
    usages = int(await valkey.incr(cle))
    if usages == 1:
        await valkey.expire(cle, secondes)
    else:
        # La clé peut avoir perdu sa durée si le processus est mort entre `incr` et `expire`.
        await valkey.expire(cle, secondes, nx=True)
    if usages <= plafond:
        return None
    restant = int(await valkey.ttl(cle))
    return restant if restant > 0 else secondes


def adresse_client(scope: Scope, relais_de_confiance: str | None) -> str:
    """L'adresse du client, vue à travers le relais quand il est celui qu'on attend.

    Derrière le relais Nuxt (research.md R-09), toutes les requêtes portent la même adresse
    source : sans `X-Forwarded-For`, la limite par client bloquerait tout le monde d'un coup. On ne
    fait confiance à cet en-tête **que** s'il vient de l'adresse déclarée : n'importe qui peut
    l'écrire.
    """
    connexion = scope.get("client")
    adresse = connexion[0] if connexion else "inconnu"
    if relais_de_confiance is not None and adresse == relais_de_confiance:
        transmise = en_tete(scope, b"x-forwarded-for")
        if transmise:
            # Le premier de la liste est le client d'origine ; les suivants sont les relais.
            return transmise.split(",")[0].strip() or adresse
    return adresse
