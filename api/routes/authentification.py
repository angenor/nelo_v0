"""Les routes qui ouvrent une session : fines, **aucune règle métier ici**.

La normalisation du numéro, les limites, la validité du code, les transitions du compte et la
rotation vivent dans `modules.socle.habilitations`. La route lit des en-têtes et des cookies, pose
des cookies, et appelle le service.

Ce que ces routes ne font jamais : dire si un numéro est connu. `POST /auth/otp` répond `204` de
la même façon dans tous les cas, et le code part par l'outbox, pas sur le chemin de la réponse.
"""

from fastapi import APIRouter, Request, Response

from api import limitation
from modules.shared import EnveloppeErreur, ErreurMetier
from modules.socle import habilitations
from modules.socle.habilitations import Appareil

routeur = APIRouter()

COOKIE_REFRESH = "nelo_refresh"
COOKIE_APPAREILS = "nelo_appareils"
# Le chemin des deux cookies : ils ne servent qu'aux routes d'authentification, et ne partent donc
# nulle part ailleurs.
CHEMIN_COOKIES = "/api/v1/auth"

LIMITE_DEBIT = {
    "model": EnveloppeErreur,
    "description": "`API_LIMITE_DEBIT` : trop de demandes pour ce numéro ou depuis ce client ; `Retry-After` dit la reprise",
}
REFUS_DE_PREUVE = {
    "model": EnveloppeErreur,
    "description": "`AUT_OTP_INVALIDE` (`details.tentatives_restantes`), `AUT_OTP_EXPIRE`, `AUT_OTP_TENTATIVES_EPUISEES`, `AUT_COMPTE_SUSPENDU`",
}


def _poser_cookie(
    reponse: Response, nom: str, valeur: str, *, secure: bool, duree: int | None = None
) -> None:
    """Un cookie que le script ne lit pas, qui ne voyage pas entre sites, et qui reste sur son chemin."""
    reponse.set_cookie(
        nom,
        valeur,
        httponly=True,
        secure=secure,
        samesite="strict",
        path=CHEMIN_COOKIES,
        max_age=duree,
    )


@routeur.post(
    "/auth/otp",
    operation_id="demander_code",
    status_code=204,
    summary="Demander un code par SMS. Répond 204 quel que soit le numéro bien formé ; le code ne part que si un compte actif ou invité le porte, par l'outbox",
    responses={
        204: {"description": "Accusé sans contenu, identique pour tout numéro bien formé"},
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_NUMERO_INVALIDE` (règle) ou `VAL_SCHEMA_INVALIDE` (schéma)",
        },
        429: LIMITE_DEBIT,
    },
)
async def demander_code(corps: habilitations.CorpsDemandeCode, request: Request) -> Response:
    configuration = request.app.state.configuration
    identifiant = habilitations.normaliser(corps.identifiant, configuration.indicatif_defaut)
    await habilitations.demander_code(
        identifiant,
        limitation.adresse_client(request.scope, configuration.relais_de_confiance),
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        compter=limitation.compter,
    )
    return Response(status_code=204)


@routeur.post(
    "/auth/otp/verification",
    operation_id="verifier_code",
    summary="Échanger le code contre une session ; si le numéro porte plusieurs comptes, renvoie le choix à faire",
    response_model=habilitations.ReponseVerificationCode,
    responses={
        200: {
            "description": "`SessionOuverte` (jeton d'accès dans le corps, rafraîchissement et appareil en cookies) ou `ChoixRequis`",
            "headers": {
                "Set-Cookie": {
                    "description": "`nelo_refresh` et `nelo_appareils`, HttpOnly, Secure, SameSite=Strict",
                    "schema": {"type": "string"},
                }
            },
        },
        401: REFUS_DE_PREUVE,
    },
)
async def verifier_code(
    corps: habilitations.CorpsVerificationCode, request: Request, reponse: Response
) -> habilitations.ReponseVerificationCode:
    configuration = request.app.state.configuration
    identifiant = habilitations.normaliser(corps.identifiant, configuration.indicatif_defaut)
    resultat, secrets_de_session = await habilitations.verifier_code(
        identifiant,
        corps.code,
        corps.compte_id,
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        secret_jeton=configuration.secret_jeton,
    )
    if secrets_de_session is not None:
        poser_secrets(reponse, request, secrets_de_session, secure=configuration.cookies_secure)
    return habilitations.ReponseVerificationCode(resultat)


def poser_secrets(
    reponse: Response,
    request: Request,
    secrets_de_session: habilitations.SecretsDeSession,
    *,
    secure: bool,
) -> None:
    """Les deux cookies d'une session qui s'ouvre : le rafraîchissement, et l'appareil.

    Le cookie d'appareil **s'ajoute** à ceux qu'il porte déjà : un même téléphone peut être connu
    de deux comptes, et la personne qui vient d'entrer ne fait pas oublier l'autre.
    """
    _poser_cookie(reponse, COOKIE_REFRESH, secrets_de_session.refresh, secure=secure)
    appareil = Appareil.depuis_cookie(request.cookies.get(COOKIE_APPAREILS))
    _poser_cookie(
        reponse,
        COOKIE_APPAREILS,
        appareil.avec(secrets_de_session.secret_appareil).en_cookie(),
        secure=secure,
        duree=int(secrets_de_session.duree_appareil.total_seconds()),
    )


@routeur.post(
    "/auth/pin",
    operation_id="ouvrir_par_pin",
    summary="Ouvrir une session par code personnel, sur un appareil connu du compte",
    response_model=habilitations.SessionOuverte,
    responses={
        200: {"description": "`SessionOuverte`"},
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_APPAREIL_INCONNU`, `AUT_PIN_ABSENT`, `AUT_PIN_INVALIDE` (`details.tentatives_restantes`), `AUT_PIN_TENTATIVES_EPUISEES`, `AUT_COMPTE_SUSPENDU` (et l'appareil oublie le compte)",
        },
    },
)
async def ouvrir_par_pin(
    corps: habilitations.CorpsOuverturePin, request: Request, reponse: Response
) -> habilitations.SessionOuverte:
    configuration = request.app.state.configuration
    session, secrets_de_session = await habilitations.ouvrir_par_pin(
        corps.compte_id,
        corps.pin,
        _appareil(request),
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        secret_jeton=configuration.secret_jeton,
    )
    poser_secrets(reponse, request, secrets_de_session, secure=configuration.cookies_secure)
    return session


@routeur.post(
    "/auth/pin/definition",
    operation_id="definir_pin",
    status_code=204,
    summary="Définir ou changer son code personnel. Le code courant est exigé s'il existe, sauf dans les dix minutes suivant une ouverture par code reçu ou par lien",
    responses={
        204: {"description": "Code personnel défini ; rien n'est renvoyé"},
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`, `AUT_SESSION_REVOQUEE`",
        },
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_PIN_ABSENT` ou `AUT_PIN_INVALIDE` (code courant), `VAL_SCHEMA_INVALIDE` (pas quatre chiffres)",
        },
    },
)
async def definir_pin(corps: habilitations.CorpsDefinitionPin, request: Request) -> Response:
    etat = request.state
    await habilitations.definir_pin(
        etat.compte_id,
        etat.tenant_id,
        etat.session_id,
        corps.pin,
        corps.pin_courant,
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
    )
    return Response(status_code=204)


@routeur.get(
    "/auth/appareil",
    operation_id="comptes_de_l_appareil",
    summary="Les comptes connus de cet appareil (nom, prénoms, code personnel défini ou non). Jamais un numéro",
    response_model=habilitations.ReponseAppareil,
    responses={200: {"description": "Vide si l'appareil n'est connu d'aucun compte"}},
)
async def comptes_de_l_appareil(request: Request) -> habilitations.ReponseAppareil:
    return await habilitations.comptes_de_l_appareil(
        _appareil(request), valkey=request.app.state.valkey
    )


@routeur.post(
    "/auth/rafraichissement",
    operation_id="rafraichir",
    summary="Rotation du rafraîchissement (cookie nelo_refresh) : un jeton d'accès neuf dans le corps, un rafraîchissement neuf dans le cookie",
    response_model=habilitations.SessionOuverte,
    responses={
        200: {
            "description": "`SessionOuverte`",
            "headers": {"Set-Cookie": {"schema": {"type": "string"}}},
        },
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_JETON_MANQUANT` (pas de cookie), `AUT_JETON_INVALIDE` (inconnu, ou réutilisé hors fenêtre, ce qui ferme la session), `AUT_SESSION_REVOQUEE`",
        },
    },
)
async def rafraichir(request: Request, reponse: Response) -> habilitations.SessionOuverte:
    configuration = request.app.state.configuration
    refresh = request.cookies.get(COOKIE_REFRESH)
    if not refresh:
        raise ErreurMetier(
            "AUT_JETON_MANQUANT",
            "aucun jeton de rafraîchissement n'accompagne la requête",
            statut=401,
        )
    session, refresh_neuf = await habilitations.rafraichir(
        refresh,
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        secret_jeton=configuration.secret_jeton,
    )
    _poser_cookie(reponse, COOKIE_REFRESH, refresh_neuf, secure=configuration.cookies_secure)
    return session


@routeur.delete(
    "/auth/session",
    operation_id="fermer_session",
    status_code=204,
    summary="Fermer la session courante : jeton d'accès et rafraîchissement révoqués, cookie effacé, appareil toujours connu",
    responses={
        204: {"description": "Session fermée"},
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`, `AUT_SESSION_REVOQUEE`",
        },
    },
)
async def fermer_session(request: Request, reponse: Response) -> Response:
    await habilitations.fermer_session(request.state.session_id, valkey=request.app.state.valkey)
    sortie = Response(status_code=204)
    # `Max-Age=0` : le navigateur oublie le cookie tout de suite, sans attendre son échéance.
    sortie.delete_cookie(COOKIE_REFRESH, path=CHEMIN_COOKIES, httponly=True, samesite="strict")
    return sortie


@routeur.post(
    "/auth/invitation/{jeton}",
    operation_id="activer_par_invitation",
    summary="Activer un compte depuis un lien à usage unique : la session s'ouvre, l'appareil devient connu",
    response_model=habilitations.SessionOuverte,
    responses={
        200: {"description": "`SessionOuverte`"},
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_INVITATION_INVALIDE` (consommé, expiré, remplacé, inconnu), `AUT_COMPTE_SUSPENDU`",
        },
    },
)
async def activer_par_invitation(
    jeton: str, request: Request, reponse: Response
) -> habilitations.SessionOuverte:
    configuration = request.app.state.configuration
    session, secrets_de_session = await habilitations.activer_par_invitation(
        jeton,
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        secret_jeton=configuration.secret_jeton,
    )
    poser_secrets(reponse, request, secrets_de_session, secure=configuration.cookies_secure)
    return session


def _appareil(request: Request) -> Appareil:
    """Les secrets d'appareil lus du cookie. La route les lit ; le service ne voit que cet objet."""
    return Appareil.depuis_cookie(request.cookies.get(COOKIE_APPAREILS))
