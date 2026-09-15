"""Les deux routes du catalogue de paramètres — fines, **aucune règle métier ici**.

La validation du catalogue, la résolution des portées et l'écriture de l'événement sont dans
`modules.socle.tenants`. La route lit le tenant posé par le middleware, traverse le point
d'insertion de capacité, et appelle le service.
"""

from fastapi import APIRouter, Request

from api import capacites
from modules.shared import EnveloppeErreur
from modules.socle import tenants
from modules.socle.tenants import CorpsPoserParametre, ParametrePose, ReponseParametres

routeur = APIRouter()

INTROUVABLE = {
    "model": EnveloppeErreur,
    "description": "`TEN_RESSOURCE_INTROUVABLE` — ressource inexistante dans le périmètre du tenant ; jamais `403`",
}
ERREUR_INTERNE = {
    "model": EnveloppeErreur,
    "description": "`API_ERREUR_INTERNE` — aucun détail technique dans `message` ; `requete_id` suffit à retrouver la trace",
}


@routeur.get(
    "/parametres",
    operation_id="lire_parametres",
    summary="Paramètres effectifs du catalogue, résolus à la portée de l'établissement de l'en-tête",
    response_model=ReponseParametres,
    responses={
        200: {
            "description": "Chaque clé du catalogue, sa valeur effective et la portée où elle a été résolue"
        },
        400: {
            "model": EnveloppeErreur,
            "description": "`TEN_ETABLISSEMENT_REQUIS` — en-tête absent ou malformé, refusé par le middleware",
        },
        404: INTROUVABLE,
        500: ERREUR_INTERNE,
    },
)
async def lire_parametres(request: Request) -> ReponseParametres:
    etat = request.state
    parametres = await tenants.lire_parametres_effectifs(etat.tenant_id, etat.etablissement_id)
    return ReponseParametres(etablissement_id=etat.etablissement_id, parametres=parametres)


@routeur.put(
    "/parametres/{cle}",
    operation_id="poser_parametre",
    summary="Poser une valeur à une portée — capacité `tenant.parametre.definir` (point d'insertion jusqu'à T1b)",
    response_model=ParametrePose,
    responses={
        200: {
            "description": "Valeur posée — une écriture qui ne crée rien de nouveau au sens du contrat (UPSERT)"
        },
        400: {
            "model": EnveloppeErreur,
            "description": "Refusé par un middleware, avant toute validation : `REQUETE_CLE_MANQUANTE`, `REQUETE_CLE_INVALIDE`, `TEN_ETABLISSEMENT_REQUIS`",
        },
        404: INTROUVABLE,
        409: {
            "model": EnveloppeErreur,
            "description": "`REQUETE_REJOUEE_DIFFEREMMENT` (même clé, corps différent) · `REQUETE_EN_COURS` (même clé, première exécution non terminée)",
        },
        422: {
            "model": EnveloppeErreur,
            "description": "Deux natures, un statut, distinguées par `code` : `VAL_SCHEMA_INVALIDE` (corps invalide, `details.champs` liste le chemin de chaque champ fautif) — ou règle métier sur un corps valide : `TEN_PARAMETRE_INCONNU`, `TEN_PORTEE_INVALIDE`, `TEN_VALEUR_INVALIDE`",
        },
        500: ERREUR_INTERNE,
    },
)
async def poser_parametre(cle: str, corps: CorpsPoserParametre, request: Request) -> ParametrePose:
    capacites.exiger_capacite("tenant.parametre.definir")
    return await tenants.poser_parametre(
        request.state.tenant_id, cle, corps.portee, corps.portee_id, corps.valeur
    )
