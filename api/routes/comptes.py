"""Les routes d'administration des comptes : créer, inviter, suspendre, changer le numéro.

Fines, comme toutes les autres : la règle vit dans `modules.socle.habilitations`. Chacune traverse
le point d'insertion de capacité avec le code qu'elle exige ; en T1a, ce point journalise et
laisse passer, et T1b le remplit sans que ces routes changent.
"""

from uuid import UUID

from fastapi import APIRouter, Request, Response

from api import capacites
from modules.shared import EnveloppeErreur
from modules.socle import habilitations

routeur = APIRouter()

SESSION = {
    "model": EnveloppeErreur,
    "description": "`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`, `AUT_SESSION_REVOQUEE`",
}
INTROUVABLE = {
    "model": EnveloppeErreur,
    "description": "`TEN_RESSOURCE_INTROUVABLE` : le compte n'existe pas dans le périmètre du tenant",
}
NON_AUTORISE = {
    "model": EnveloppeErreur,
    "description": "`TEN_ETABLISSEMENT_NON_AUTORISE` : le compte n'est pas affecté à l'établissement de l'en-tête",
}


@routeur.post(
    "/comptes/{id}/suspension",
    operation_id="suspendre_compte",
    status_code=204,
    summary="Suspendre un compte : ses sessions tombent, ses appareils l'oublient, et la levée n'est pas livrée",
    responses={
        204: {"description": "Compte suspendu ; la requête suivante de ce compte répond 401"},
        401: SESSION,
        403: NON_AUTORISE,
        404: INTROUVABLE,
    },
)
async def suspendre_compte(id: UUID, request: Request) -> Response:
    capacites.exiger_capacite("habilitations.compte.suspendre")
    await habilitations.suspendre(
        request.state.tenant_id, id, request.state.compte_id, valkey=request.app.state.valkey
    )
    return Response(status_code=204)


@routeur.post(
    "/comptes",
    operation_id="creer_compte",
    status_code=201,
    summary="Créer le compte d'une personne du tenant : il naît invité, et son lien part par SMS",
    response_model=habilitations.CompteCree,
    responses={
        201: {
            "description": "Compte créé, invitation envoyée. **Jamais le lien** : il part par message",
            "headers": {"Location": {"schema": {"type": "string"}}},
        },
        401: SESSION,
        403: NON_AUTORISE,
        404: INTROUVABLE,
        409: {
            "model": EnveloppeErreur,
            "description": "`TEN_RESSOURCE_DEJA_EXISTANTE` : cette personne a déjà un compte",
        },
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_IDENTIFIANT_DEJA_UTILISE` (`details.partage_familial_requis`), `AUT_NUMERO_INVALIDE`, `VAL_SCHEMA_INVALIDE`",
        },
    },
)
async def creer_compte(
    corps: habilitations.CorpsCreationCompte, request: Request, reponse: Response
) -> habilitations.CompteCree:
    capacites.exiger_capacite("habilitations.compte.gerer")
    configuration = request.app.state.configuration
    identifiant = habilitations.normaliser(corps.identifiant, configuration.indicatif_defaut)
    cree = await habilitations.creer_compte(
        request.state.tenant_id,
        corps.personne_id,
        identifiant,
        corps.partage_familial,
        request.state.compte_id,
        request.state.etablissement_id,
        valkey=request.app.state.valkey,
    )
    reponse.headers["Location"] = f"/comptes/{cree.id}"
    return cree


@routeur.post(
    "/comptes/verification",
    operation_id="verifier_creation_compte",
    summary="Ce qui bloquerait la création, dit pendant la saisie : aucune écriture, aucun envoi",
    response_model=habilitations.VerificationCreationCompte,
    responses={
        200: {
            "description": "Les bloquages et leurs issues ; une liste vide veut dire « rien ne s'y oppose »"
        },
        401: SESSION,
        403: NON_AUTORISE,
    },
)
async def verifier_creation_compte(
    corps: habilitations.CorpsCreationCompte, request: Request
) -> habilitations.VerificationCreationCompte:
    capacites.exiger_capacite("habilitations.compte.gerer")
    configuration = request.app.state.configuration
    identifiant = habilitations.normaliser(corps.identifiant, configuration.indicatif_defaut)
    return await habilitations.verifier_creation(
        request.state.tenant_id, corps.personne_id, identifiant, corps.partage_familial
    )


@routeur.post(
    "/comptes/{id}/invitation",
    operation_id="renvoyer_invitation",
    summary="Renvoyer un lien d'activation : le précédent cesse aussitôt de valoir",
    response_model=habilitations.CompteCree,
    responses={
        200: {"description": "Invitation renvoyée ; la réponse dit la date, jamais le lien"},
        401: SESSION,
        403: NON_AUTORISE,
        404: INTROUVABLE,
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_COMPTE_DEJA_ACTIF`, `AUT_COMPTE_SUSPENDU`",
        },
    },
)
async def renvoyer_invitation(id: UUID, request: Request) -> habilitations.CompteCree:
    capacites.exiger_capacite("habilitations.compte.gerer")
    return await habilitations.renvoyer_invitation(
        request.state.tenant_id, id, request.state.etablissement_id, valkey=request.app.state.valkey
    )


@routeur.post(
    "/comptes/{id}/telephone",
    operation_id="changer_telephone_administratif",
    status_code=204,
    summary="Changer le numéro d'un compte sans vérification préalable : toutes ses sessions tombent",
    responses={
        204: {
            "description": "Numéro changé, sessions révoquées, appareils oubliés, ancien numéro informé"
        },
        401: SESSION,
        403: NON_AUTORISE,
        404: INTROUVABLE,
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_IDENTIFIANT_DEJA_UTILISE`, `AUT_NUMERO_INVALIDE`",
        },
    },
)
async def changer_telephone_administratif(
    id: UUID, corps: habilitations.CorpsChangementAdministratif, request: Request
) -> Response:
    capacites.exiger_capacite("habilitations.compte.gerer")
    configuration = request.app.state.configuration
    nouveau = habilitations.normaliser(corps.nouvel_identifiant, configuration.indicatif_defaut)
    await habilitations.changer_identifiant_administratif(
        request.state.tenant_id,
        id,
        nouveau,
        request.state.compte_id,
        valkey=request.app.state.valkey,
    )
    return Response(status_code=204)
