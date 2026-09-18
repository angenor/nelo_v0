"""Le contexte qui compose l'interface : une requête, et l'écran sait ce qui existe.

`GET /moi/capacites` (docs/03-api.md § 1.9) est la seule source de ce que la personne peut faire.
La route **compose** : chaque morceau vient du module qui le possède, par son interface, jamais
par ses tables. Aucun calcul de composition n'est laissé au client, et aucune capacité n'est
inventée ici : en T1a, `capacites`, `acces_nominatifs` et `alertes` sont vides, et la coquille de
T0b en dérive l'écran « aucun domaine » qui nomme l'administrateur.

Le middleware d'établissement a déjà vérifié que le compte est rattaché à celui de l'en-tête :
cette route ne refuse rien, elle décrit.
"""

from fastapi import APIRouter, Request, Response
from sqlalchemy import select

from api import limitation
from modules.shared import EnveloppeErreur
from modules.shared.bd import transaction
from modules.shared.contexte import (
    Administrateur,
    AnneeContexte,
    Compte,
    ContexteCapacites,
    CountryPackContexte,
    Devise,
    EtablissementContexte,
)
from modules.socle import annees, habilitations, personnes, tenants
from modules.socle.tenants.tables import tenant as table_tenant

routeur = APIRouter()

# Le pack de pays du tenant. Sa version est celle que le tenant porte ; un bulletin réédité trois
# ans plus tard lira la sienne, pas la dernière publiée.
LANGUE_DE_SECOURS = "fr"


@routeur.get(
    "/moi/capacites",
    operation_id="lire_contexte",
    summary="Le contexte qui compose l'interface ; capacités et accès nominatifs vides jusqu'à T1b",
    response_model=ContexteCapacites,
    responses={
        200: {"description": "Tout ce qu'il faut pour ne rendre que ce qui existe"},
        400: {
            "model": EnveloppeErreur,
            "description": "`TEN_ETABLISSEMENT_REQUIS` : en-tête absent ou malformé. `details.etablissements` rappelle au compte ses propres rattachements",
        },
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`, `AUT_SESSION_REVOQUEE`",
        },
        403: {
            "model": EnveloppeErreur,
            "description": "`TEN_ETABLISSEMENT_NON_AUTORISE` : le compte n'est pas affecté à cet établissement",
        },
    },
)
async def lire_contexte(request: Request) -> ContexteCapacites:
    etat = request.state
    tenant_id, compte_id = etat.tenant_id, etat.compte_id
    etablissement_actif = etat.etablissement_id

    attaches = await habilitations.rattachements(tenant_id, compte_id)
    etablissements_ids = list(dict.fromkeys(r.etablissement_id for r in attaches))
    etablissements = await tenants.lire_etablissements(tenant_id, etablissements_ids)

    compte = await _compte(tenant_id, compte_id)
    annees_actives = await _annees(tenant_id, etablissement_actif, attaches)
    pack = await _pack(tenant_id)
    parametres = await tenants.lire_parametres_effectifs(tenant_id, etablissement_actif)

    return ContexteCapacites(
        compte=compte,
        etablissements=[await _etablissement(tenant_id, e) for e in etablissements],
        etablissement_actif=etablissement_actif,
        annees=annees_actives,
        annee_active=_annee_active(annees_actives),
        # T1b livre les capacités et les accès nominatifs ; T2a et au-delà, les alertes.
        capacites=[],
        acces_nominatifs=[],
        country_pack=pack,
        parametres_effectifs={p.cle: p.valeur for p in parametres},
        alertes=[],
    )


@routeur.post(
    "/moi/telephone",
    operation_id="demander_changement_telephone",
    status_code=204,
    summary="Demander le changement de son numéro : un code part vers le **nouveau** numéro",
    responses={
        204: {
            "description": "Code envoyé au nouveau numéro. L'identifiant ne change qu'à la vérification"
        },
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_JETON_MANQUANT`, `AUT_JETON_INVALIDE`, `AUT_SESSION_REVOQUEE`",
        },
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_NUMERO_INVALIDE`, `VAL_SCHEMA_INVALIDE`",
        },
        429: {
            "model": EnveloppeErreur,
            "description": "`API_LIMITE_DEBIT` ; `Retry-After` dit la reprise",
        },
    },
)
async def demander_changement_telephone(
    corps: habilitations.CorpsChangementTelephone, request: Request
) -> Response:
    configuration = request.app.state.configuration
    nouveau = habilitations.normaliser(corps.nouvel_identifiant, configuration.indicatif_defaut)
    await habilitations.demander_changement(
        request.state.tenant_id,
        request.state.compte_id,
        nouveau,
        limitation.adresse_client(request.scope, configuration.relais_de_confiance),
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
        compter=limitation.compter,
    )
    return Response(status_code=204)


@routeur.post(
    "/moi/telephone/verification",
    operation_id="verifier_changement_telephone",
    status_code=204,
    summary="Vérifier le code reçu sur le nouveau numéro : l'identifiant change, l'ancien numéro est informé",
    responses={
        204: {"description": "Identifiant changé ; la session courante survit"},
        401: {
            "model": EnveloppeErreur,
            "description": "`AUT_OTP_INVALIDE`, `AUT_OTP_EXPIRE`, `AUT_OTP_TENTATIVES_EPUISEES`, ou la session",
        },
        422: {
            "model": EnveloppeErreur,
            "description": "`AUT_IDENTIFIANT_DEJA_UTILISE` : ce numéro est déjà celui d'un autre compte",
        },
    },
)
async def verifier_changement_telephone(
    corps: habilitations.CorpsVerificationChangement, request: Request
) -> Response:
    await habilitations.verifier_changement(
        request.state.tenant_id,
        request.state.compte_id,
        corps.code,
        valkey=request.app.state.valkey,
        politique=habilitations.POLITIQUE,
    )
    return Response(status_code=204)


async def _compte(tenant_id, compte_id) -> Compte:
    description = await habilitations.decrire_compte(tenant_id, compte_id)
    identite = await personnes.lire_identite(tenant_id, description.personne_id)
    return Compte(
        id=compte_id,
        nom=identite.nom,
        prenoms=identite.prenoms,
        langue=identite.langue,
    )


async def _etablissement(tenant_id, etablissement) -> EtablissementContexte:
    return EtablissementContexte(
        id=etablissement.id,
        nom=etablissement.nom,
        # Aucune table de site, de cycle ni de module n'existe avant les tranches qui les créent :
        # le contexte porte des listes vides, et la coquille de T0b l'accepte.
        sites=[],
        cycles_actifs=[],
        modules_actifs=[],
        administrateur=await _administrateur(tenant_id, etablissement),
    )


async def _administrateur(tenant_id, etablissement) -> Administrateur:
    """La personne désignée, ou l'établissement lui-même (FR-049). Jamais un champ absent.

    Un écran qui dit « demandez à quelqu'un » sans dire à qui ne sert à rien. Si personne n'est
    désigné, ou si le compte désigné est suspendu, c'est l'école qu'on appelle, et ses prénoms
    sont vides : c'est une institution, pas une personne.
    """
    compte_id = etablissement.administrateur_compte_id
    if compte_id is not None:
        designe = await habilitations.decrire_compte(tenant_id, compte_id)
        if designe is not None and designe.statut != habilitations.StatutCompte.SUSPENDU:
            identite = await personnes.lire_identite(tenant_id, designe.personne_id)
            if identite is not None:
                return Administrateur(
                    nom=identite.nom, prenoms=identite.prenoms, telephone=designe.identifiant
                )
    return Administrateur(
        nom=etablissement.nom,
        prenoms="",
        telephone=etablissement.telephone or "",
    )


async def _annees(tenant_id, etablissement_actif, attaches) -> list[AnneeContexte]:
    """Les années de l'établissement actif auxquelles le compte est rattaché, et elles seules."""
    rattachees = {r.annee_id for r in attaches if r.etablissement_id == etablissement_actif}
    toutes = await annees.lire_annees(tenant_id, etablissement_actif)
    return [
        AnneeContexte(id=a.id, libelle=a.libelle, etat=a.etat.upper())
        for a in toutes
        if a.id in rattachees
    ]


def _annee_active(liste: list[AnneeContexte]):
    """Celle qui est `ACTIVE` ; à défaut la première, pour qu'un écran ait toujours où travailler."""
    for annee in liste:
        if annee.etat == "ACTIVE":
            return annee.id
    return liste[0].id if liste else None


async def _pack(tenant_id) -> CountryPackContexte:
    async with transaction(tenant_id) as connexion:
        resultat = await connexion.execute(
            select(table_tenant.c.pays_code, table_tenant.c.country_pack_version).where(
                table_tenant.c.id == tenant_id
            )
        )
        ligne = resultat.mappings().one()
    pack = await tenants.lire_pack(tenant_id, ligne["pays_code"], ligne["country_pack_version"])
    return CountryPackContexte(
        pays=pack.pays_code,
        version=pack.version,
        devise=Devise(**pack.devise.model_dump()),
        langues=pack.langues,
        decoupage=pack.decoupage,
        vocabulaire=pack.vocabulaire,
    )
