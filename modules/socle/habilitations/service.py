"""Le service du module `habilitations` : ouvrir une session, et ne rien dire de plus qu'il ne faut.

La règle de cette tranche tient en une phrase : **la demande d'un code répond de la même façon
quel que soit le numéro**. Un numéro que personne ne porte reçoit le même `204`, après le même
travail, dans le même temps. C'est pourquoi le code part par l'outbox et non sur le chemin de la
réponse : une passerelle en panne publierait autrement l'existence des comptes.

Le service reçoit `valkey` et la politique en paramètres : il n'importe ni `api`, ni la
configuration. Il lit les deux modules voisins par leur interface, jamais par leurs tables :
`personnes` pour l'identité, `tenants` pour le nom de l'établissement et la durée de session.
"""

import hashlib
import json
import logging
import secrets
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from modules.shared import ErreurMetier, Evenement, outbox, transaction
from modules.shared.bd import sans_tenant
from modules.socle import personnes, tenants
from modules.socle.habilitations import acces, gabarits
from modules.socle.habilitations import appareil as appareil_module
from modules.socle.habilitations import session as session_module
from modules.socle.habilitations.politique import PolitiqueSecurite
from modules.socle.habilitations.schemas import (
    Bloquage,
    CanalOuverture,
    ChoixCompte,
    ChoixRequis,
    CompteConnu,
    CompteCree,
    CompteSession,
    DescriptionCompte,
    MotifFermeture,
    Rattachement,
    ReponseAppareil,
    SessionOuverte,
    StatutCompte,
    VerificationCreationCompte,
)
from modules.socle.habilitations.tables import evenement_outbox

journal = logging.getLogger("nelo.habilitations")

# Les types d'événements du module, tous préfixés par son nom (docs/02-domaine.md § 3.6).
EVENEMENT_OTP_DEMANDE = "habilitations.otp.demande"
EVENEMENT_COMPTE_ACTIVE = "habilitations.compte.active"
EVENEMENT_SESSION_OUVERTE = "habilitations.session.ouverte"
EVENEMENT_SESSION_FERMEE = "habilitations.session.fermee"
EVENEMENT_PIN_DEFINI = "habilitations.pin.defini"
EVENEMENT_COMPTE_SUSPENDU = "habilitations.compte.suspendu"
EVENEMENT_COMPTE_CREE = "habilitations.compte.cree"
EVENEMENT_COMPTE_INVITE = "habilitations.compte.invite"
EVENEMENT_IDENTIFIANT_CHANGE = "habilitations.identifiant.change"

# Les clés de l'éphémère (data-model.md). Elles ne survivent pas à une panne de Valkey, et c'est
# le contrat : perdre Valkey ne coûte que des reconnexions.
CLE_OTP = "otp:{identifiant}"
CLE_OTP_TEXTE = "otp_texte:{envoi_id}"
CLE_OTP_RENVOI = "otp_renvoi:{identifiant}"
CLE_OTP_DEBIT = "otp_debit:{identifiant}"
CLE_OTP_DEBIT_CLIENT = "otp_debit_client:{adresse}"
CLE_PIN_TENTATIVES = "pin_tentatives:{compte_id}"
CLE_CHANGEMENT = "changement:{compte_id}"
CLE_INVITATION_TEXTE = "invitation_texte:{envoi_id}"
CLE_CHANGEMENT_TEXTE = "changement_texte:{envoi_id}"

# La clé du paramètre réglable, lu au catalogue du tenant et non ici.
CLE_DUREE_SESSION = "securite.duree_session_minutes"
CLE_APPAREIL_JOURS = "securite.appareil_connu_jours"
CLE_PIN_TENTATIVES_MAX = "securite.pin_tentatives_max"
CLE_INVITATION_JOURS = "securite.invitation_validite_jours"

# Les statuts qui peuvent recevoir un code : un compte suspendu n'en reçoit aucun, et ne le dit pas.
STATUTS_OUVRABLES = (StatutCompte.ACTIF.value, StatutCompte.INVITE.value)

type Limiteur = Callable[[Any, str, int, timedelta], Awaitable[int | None]]


@dataclass(frozen=True, slots=True)
class SecretsDeSession:
    """Ce qui part en cookies, et que le corps de la réponse ne porte jamais.

    La route les pose ; ni l'écran, ni le client, ni un script ne les voient. La durée du cookie
    d'appareil est celle du réglage du tenant, pour que le cookie et Valkey expirent ensemble.
    """

    refresh: str
    secret_appareil: str
    duree_appareil: timedelta


def _aujourd_hui() -> date:
    return datetime.now(UTC).date()


def _json(valeur: dict) -> str:
    return json.dumps(valeur)


def _charge(brut) -> dict:
    return json.loads(brut)


def _empreinte_code(code: str, envoi_id: UUID) -> str:
    """Le code n'est jamais conservé en clair ailleurs que dans `otp_texte`, effacé à l'envoi.

    Le sel est l'identifiant de l'envoi : deux demandes du même code sur deux numéros ne donnent
    pas la même empreinte, et une empreinte volée ne se rejoue pas ailleurs.
    """
    return hashlib.sha256(f"{code}:{envoi_id}".encode()).hexdigest()


def _limite_atteinte(reprise_dans: int) -> ErreurMetier:
    return ErreurMetier(
        "API_LIMITE_DEBIT",
        "trop de demandes pour ce numéro ou depuis ce client",
        statut=429,
        details={"reprise_dans": reprise_dans},
        en_tetes={"Retry-After": str(reprise_dans)},
    )


# --- Les seeds : ce qu'aucune route n'expose en T1a --------------------------------------------


async def semer_compte(
    tenant_id: UUID,
    personne_id: UUID,
    identifiant: str,
    statut: str = StatutCompte.ACTIF.value,
) -> UUID:
    """Pour les seeds et les tests ; la création par route est `creer_compte` (US6)."""
    compte_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_compte(
            connexion, compte_id, tenant_id, personne_id, identifiant, statut
        )
    return compte_id


async def creer_affectation(
    tenant_id: UUID,
    compte_id: UUID,
    annee_id: UUID,
    etablissement_id: UUID,
    debut: date,
    fin: date | None = None,
) -> UUID:
    """Pour les seeds et les tests ; T1b livre l'affectation avec son modèle de rôle."""
    affectation_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_affectation(
            connexion, affectation_id, tenant_id, compte_id, annee_id, etablissement_id, debut, fin
        )
    return affectation_id


async def decrire_compte(tenant_id: UUID, compte_id: UUID) -> DescriptionCompte | None:
    """Le compte tel que le contexte et les autres modules le lisent ; `None` s'il est invisible."""
    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
    if ligne is None:
        return None
    return DescriptionCompte(
        id=ligne["id"],
        personne_id=ligne["personne_id"],
        identifiant=ligne["identifiant"],
        statut=StatutCompte(ligne["statut"]),
        pin_defini=ligne["pin_empreinte"] is not None,
    )


# --- Ce que les middlewares d'établissement et d'année lisent ----------------------------------


async def affectation_vivante(
    tenant_id: UUID, compte_id: UUID, etablissement_id: UUID, annee_id: UUID | None = None
) -> bool:
    """Le compte est-il rattaché à cet établissement aujourd'hui, et pour cette année ?"""
    async with transaction(tenant_id) as connexion:
        return await acces.affectation_vivante(
            connexion, compte_id, etablissement_id, annee_id, _aujourd_hui()
        )


async def rattachements(tenant_id: UUID, compte_id: UUID) -> list[Rattachement]:
    """Les couples (établissement, année) vivants ; le contexte et les middlewares en dérivent."""
    async with transaction(tenant_id) as connexion:
        lignes = await acces.lire_rattachements(connexion, compte_id, _aujourd_hui())
    return [
        Rattachement(etablissement_id=ligne["etablissement_id"], annee_id=ligne["annee_id"])
        for ligne in lignes
    ]


# --- Demander un code ---------------------------------------------------------------------------


async def demander_code(
    identifiant: str,
    adresse_client: str,
    *,
    valkey,
    politique: PolitiqueSecurite,
    compter: Limiteur,
) -> None:
    """Toujours silencieuse : ni retour, ni refus, quoi que porte le numéro.

    `compter` est injecté par la composition (`api/limitation.py`) : un module du socle ne remonte
    pas vers `api/`. Les trois limites sont appliquées **avant** toute lecture de la base, celle
    par client d'abord : c'est elle qui protège du balayage de numéros.
    """
    for cle, plafond, fenetre in (
        (
            CLE_OTP_DEBIT_CLIENT.format(adresse=adresse_client),
            politique.OTP_PAR_HEURE_PAR_CLIENT,
            timedelta(hours=1),
        ),
        (
            CLE_OTP_DEBIT.format(identifiant=identifiant),
            politique.OTP_PAR_HEURE_PAR_NUMERO,
            timedelta(hours=1),
        ),
        (CLE_OTP_RENVOI.format(identifiant=identifiant), 1, politique.OTP_RENVOI),
    ):
        reprise = await compter(valkey, cle, plafond, fenetre)
        if reprise is not None:
            raise _limite_atteinte(reprise)

    async with sans_tenant() as connexion:
        trouves = await acces.appeler_comptes_par_identifiant(connexion, identifiant)
    comptes = [c for c in trouves if c["statut"] in STATUTS_OUVRABLES]

    # Le même travail dans les deux cas : générer, saler, calculer. Ce qui change est ce qui
    # s'écrit, et le temps de réponse ne doit pas le dire (SC-003).
    code = f"{secrets.randbelow(10**politique.OTP_LONGUEUR):0{politique.OTP_LONGUEUR}d}"
    envoi_id = uuid.uuid7()
    empreinte = _empreinte_code(code, envoi_id)
    if not comptes:
        return

    langue = await _langue_du_compte(comptes[0])
    validite = int(politique.OTP_VALIDITE.total_seconds())
    await valkey.set(
        CLE_OTP.format(identifiant=identifiant),
        _json(
            {
                "empreinte": empreinte,
                "tentatives": 0,
                "envoi_id": str(envoi_id),
                "comptes": [
                    {"id": str(c["id"]), "tenant_id": str(c["tenant_id"])} for c in comptes
                ],
            }
        ),
        ex=validite,
    )
    await valkey.set(CLE_OTP_TEXTE.format(envoi_id=envoi_id), code, ex=validite)

    premier = comptes[0]
    async with transaction(premier["tenant_id"]) as connexion:
        await acces.inserer_evenement(
            connexion,
            premier["tenant_id"],
            Evenement(
                EVENEMENT_OTP_DEMANDE,
                {
                    "compte_id": str(premier["id"]),
                    "identifiant": identifiant,
                    "envoi_id": str(envoi_id),
                    "langue": langue,
                },
            ),
        )


async def _langue_du_compte(compte) -> str:
    identite = await personnes.lire_identite(compte["tenant_id"], compte["personne_id"])
    return identite.langue if identite is not None else gabarits.LANGUE_DE_SECOURS


# --- Vérifier le code, et ouvrir la session -----------------------------------------------------


async def verifier_code(
    identifiant: str,
    code: str,
    compte_id: UUID | None,
    *,
    valkey,
    politique: PolitiqueSecurite,
    secret_jeton: str,
) -> tuple[SessionOuverte | ChoixRequis, SecretsDeSession | None]:
    """Rend `(réponse, secrets)` ; les secrets partent en cookies, jamais dans le corps.

    Quatre refus, tous `401` : le code a expiré, il est faux, les tentatives sont épuisées, le
    compte est suspendu. Aucun ne dit si le numéro existe : à ce stade, la personne a déjà prouvé
    qu'elle reçoit les messages de ce numéro.
    """
    cle = CLE_OTP.format(identifiant=identifiant)
    brut = await valkey.get(cle)
    if brut is None:
        raise ErreurMetier(
            "AUT_OTP_EXPIRE", "le code a expiré ou n'a jamais été demandé", statut=401
        )
    charge = _charge(brut)

    if not secrets.compare_digest(
        charge["empreinte"], _empreinte_code(code, UUID(charge["envoi_id"]))
    ):
        charge["tentatives"] += 1
        restantes = politique.OTP_TENTATIVES - charge["tentatives"]
        if restantes <= 0:
            await valkey.delete(cle)
            raise ErreurMetier(
                "AUT_OTP_TENTATIVES_EPUISEES",
                "le code a été refusé trop de fois ; il est détruit",
                statut=401,
            )
        await valkey.set(cle, _json(charge), keepttl=True)
        raise ErreurMetier(
            "AUT_OTP_INVALIDE",
            "le code ne correspond pas",
            statut=401,
            details={"tentatives_restantes": restantes},
        )

    comptes = [{"id": UUID(c["id"]), "tenant_id": UUID(c["tenant_id"])} for c in charge["comptes"]]
    if compte_id is None and len(comptes) > 1:
        # Le code reste valide : la personne n'a pas encore ouvert sa session.
        return await _choix_requis(comptes), None

    if compte_id is not None:
        choisi = next((c for c in comptes if c["id"] == compte_id), None)
        if choisi is None:
            # Un compte hors de la liste n'est pas une erreur de saisie : c'est une tentative.
            raise ErreurMetier("AUT_OTP_INVALIDE", "le compte choisi n'est pas proposé", statut=401)
    else:
        choisi = comptes[0]

    session, secrets_de_session = await _ouvrir_pour(
        choisi["id"],
        choisi["tenant_id"],
        CanalOuverture.CODE,
        valkey=valkey,
        politique=politique,
        secret_jeton=secret_jeton,
        choix_parmi=len(comptes),
    )
    await valkey.delete(cle)
    return session, secrets_de_session


async def _choix_requis(comptes: list[dict]) -> ChoixRequis:
    """Qui ouvre la session ? Des noms et des établissements ; **jamais** un numéro."""
    propositions: list[ChoixCompte] = []
    for compte in comptes:
        tenant_id = compte["tenant_id"]
        async with transaction(tenant_id) as connexion:
            ligne = await acces.lire_compte(connexion, compte["id"])
            attaches = await acces.lire_rattachements(connexion, compte["id"], _aujourd_hui())
        if ligne is None:
            continue
        identite = await personnes.lire_identite(tenant_id, ligne["personne_id"])
        etablissements = await tenants.lire_etablissements(
            tenant_id, [a["etablissement_id"] for a in attaches]
        )
        propositions.append(
            ChoixCompte(
                compte_id=compte["id"],
                nom=identite.nom if identite else "",
                prenoms=identite.prenoms if identite else "",
                etablissement_nom=etablissements[0].nom if etablissements else "",
            )
        )
    return ChoixRequis(comptes=propositions)


async def _ouvrir_pour(
    compte_id: UUID,
    tenant_id: UUID,
    canal: CanalOuverture,
    *,
    valkey,
    politique: PolitiqueSecurite,
    secret_jeton: str,
    choix_parmi: int = 1,
) -> tuple[SessionOuverte, SecretsDeSession]:
    """L'ouverture proprement dite : le statut est relu, le compte activé s'il était invité."""
    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
        if ligne is None:
            raise ErreurMetier("AUT_OTP_INVALIDE", "le compte n'existe plus", statut=401)
        if ligne["statut"] == StatutCompte.SUSPENDU.value:
            raise ErreurMetier("AUT_COMPTE_SUSPENDU", "ce compte est suspendu", statut=401)
        active = ligne["statut"] == StatutCompte.INVITE.value
        if active:
            # FR-033 : un compte invité qui reçoit son code n'a pas besoin du lien.
            await acces.poser_statut(connexion, compte_id, StatutCompte.ACTIF.value)
            await acces.inserer_evenement(
                connexion,
                tenant_id,
                Evenement(
                    EVENEMENT_COMPTE_ACTIVE,
                    {"compte_id": str(compte_id), "canal": canal.value},
                ),
            )
        await acces.poser_derniere_connexion(connexion, compte_id)

    duree = await _duree_de_session(tenant_id)
    session_id, jeton, refresh = await session_module.ouvrir_session(
        compte_id,
        tenant_id,
        canal,
        valkey=valkey,
        secret=secret_jeton,
        politique=politique,
        duree=duree,
    )
    jours = await _appareil_connu_jours(tenant_id)
    secret_appareil = await appareil_module.connaitre(
        compte_id, tenant_id, valkey=valkey, jours=jours
    )

    async with transaction(tenant_id) as connexion:
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_SESSION_OUVERTE,
                {
                    "compte_id": str(compte_id),
                    "session_id": str(session_id),
                    "canal": canal.value,
                    "choix_parmi": choix_parmi,
                    "appareil_connu": True,
                },
            ),
        )

    identite = await personnes.lire_identite(tenant_id, ligne["personne_id"])
    return (
        SessionOuverte(
            jeton_acces=jeton,
            expire_dans=int(politique.JETON_ACCES.total_seconds()),
            compte=CompteSession(
                id=compte_id,
                nom=identite.nom if identite else "",
                prenoms=identite.prenoms if identite else "",
                langue=identite.langue if identite else gabarits.LANGUE_DE_SECOURS,
                pin_defini=ligne["pin_empreinte"] is not None,
            ),
            appareil_connu=True,
        ),
        SecretsDeSession(
            refresh=refresh, secret_appareil=secret_appareil, duree_appareil=timedelta(days=jours)
        ),
    )


async def _valeur_entiere(tenant_id: UUID, cle: str, defaut: int) -> int:
    effective = await tenants.valeur_effective(tenant_id, cle, tenants.Portee.TENANT, tenant_id)
    valeur = effective.valeur
    return int(valeur) if isinstance(valeur, int) else defaut


async def _duree_de_session(tenant_id: UUID) -> timedelta:
    """Réglée par le tenant, **figée à l'ouverture** : un changement vaut pour les suivantes."""
    return timedelta(minutes=await _valeur_entiere(tenant_id, CLE_DUREE_SESSION, 480))


async def _appareil_connu_jours(tenant_id: UUID) -> int:
    return await _valeur_entiere(tenant_id, CLE_APPAREIL_JOURS, 90)


async def session_valide(session_id: UUID, compte_id: UUID, tenant_id: UUID, *, valkey) -> bool:
    """Ce que chaque requête protégée consulte avant d'être servie (FR-026).

    **Deux barrières, et il en faut deux.** La première est la liste de révocation : une session
    dont la clé n'existe plus est fermée, et c'est immédiat. La seconde est le statut du compte,
    relu en base : la suspension écrit ce statut dans sa transaction, puis efface les sessions
    **après** le `COMMIT`, parce que Valkey ne participe pas à la transaction. Une panne entre les
    deux laisserait, sans cette relecture, un compte suspendu dont la session vit encore.

    C'est l'écart nommé au contrôle de constitution du plan, et voici ce qui le couvre.
    """
    if not await session_module.session_valide(session_id, compte_id, valkey=valkey):
        return False
    description = await decrire_compte(tenant_id, compte_id)
    return description is not None and description.statut != StatutCompte.SUSPENDU


def verifier_jeton_acces(jeton: str, secret: str):
    return session_module.verifier_jeton_acces(jeton, secret)


# --- La rotation, la fermeture, la suspension --------------------------------------------------


async def rafraichir(
    refresh: str, *, valkey, politique: PolitiqueSecurite, secret_jeton: str
) -> tuple[SessionOuverte, str]:
    """Rend un jeton d'accès neuf et **un rafraîchissement neuf** ; l'ancien ne vaut plus rien.

    La rotation est ce qui rend un vol détectable : un jeton présenté deux fois hors de la fenêtre
    de concurrence est le signe qu'une copie circule, et fait tomber **toute** la session. La
    fenêtre existe parce que deux onglets peuvent rafraîchir en même temps : dans ces dix
    secondes, l'ancien jeton rend la même réponse que le neuf, au lieu de détruire la session de
    quelqu'un qui n'a rien fait de mal.
    """
    charge = await session_module.lire_refresh(refresh, valkey=valkey)
    if charge is None:
        raise ErreurMetier(
            "AUT_JETON_INVALIDE", "le jeton de rafraîchissement est inconnu", statut=401
        )
    session_id = UUID(charge["session_id"])

    if charge.get("remplace_par") is not None:
        # Déjà tourné. Dans la fenêtre, on rend la même chose ; hors fenêtre, la session tombe.
        remplace_le = datetime.fromisoformat(charge["remplace_le"])
        if datetime.now(UTC) - remplace_le <= politique.FENETRE_CONCURRENCE_REFRESH:
            return await _reprendre_rotation(
                charge, valkey=valkey, politique=politique, secret_jeton=secret_jeton
            )
        await _fermer(session_id, MotifFermeture.REUTILISATION, valkey=valkey)
        raise ErreurMetier(
            "AUT_JETON_INVALIDE",
            "ce jeton de rafraîchissement a déjà servi ; la session est fermée",
            statut=401,
        )

    session = await session_module.lire_session(session_id, valkey=valkey)
    if session is None:
        raise ErreurMetier("AUT_SESSION_REVOQUEE", "la session n'existe plus", statut=401)
    compte_id, tenant_id = UUID(session["compte_id"]), UUID(session["tenant_id"])

    # Le statut est relu à chaque rotation : une suspension survenue entre-temps ferme ici.
    description = await decrire_compte(tenant_id, compte_id)
    if description is None or description.statut == StatutCompte.SUSPENDU:
        await _fermer(session_id, MotifFermeture.SUSPENSION, valkey=valkey)
        raise ErreurMetier("AUT_SESSION_REVOQUEE", "la session n'existe plus", statut=401)

    reste = await valkey.ttl(session_module.cle_session(session_id))
    duree = timedelta(seconds=max(int(reste), 1))
    neuf = await session_module.tourner_refresh(
        refresh, session_id, valkey=valkey, duree=duree, politique=politique
    )
    return (
        await _session_ouverte(
            compte_id, tenant_id, session_id, description, secret_jeton, politique
        ),
        neuf,
    )


async def _reprendre_rotation(
    charge: dict, *, valkey, politique: PolitiqueSecurite, secret_jeton: str
) -> tuple[SessionOuverte, str]:
    """Dans la fenêtre de concurrence : le jeton déjà produit est rendu tel quel.

    Deux onglets qui rafraîchissent en même temps reçoivent alors la même réponse, au lieu que le
    second détruise la session du premier.
    """
    session_id = UUID(charge["session_id"])
    session = await session_module.lire_session(session_id, valkey=valkey)
    if session is None:
        raise ErreurMetier("AUT_SESSION_REVOQUEE", "la session n'existe plus", statut=401)
    compte_id, tenant_id = UUID(session["compte_id"]), UUID(session["tenant_id"])
    description = await decrire_compte(tenant_id, compte_id)
    return (
        await _session_ouverte(
            compte_id, tenant_id, session_id, description, secret_jeton, politique
        ),
        charge["remplace_par"],
    )


async def _session_ouverte(
    compte_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    description: DescriptionCompte,
    secret_jeton: str,
    politique: PolitiqueSecurite,
) -> SessionOuverte:
    """La réponse d'une session déjà ouverte : un jeton d'accès neuf, et qui la porte.

    Le rafraîchissement ne touche **pas** à l'appareil : il est déjà connu, ou il ne l'est pas, et
    renouveler son secret à chaque heure n'en ferait qu'accumuler dans le magasin éphémère.
    """
    identite = await personnes.lire_identite(tenant_id, description.personne_id)
    return SessionOuverte(
        jeton_acces=session_module.signer_jeton_acces(
            compte_id, tenant_id, session_id, secret_jeton, politique.JETON_ACCES
        ),
        expire_dans=int(politique.JETON_ACCES.total_seconds()),
        compte=CompteSession(
            id=compte_id,
            nom=identite.nom if identite else "",
            prenoms=identite.prenoms if identite else "",
            langue=identite.langue if identite else gabarits.LANGUE_DE_SECOURS,
            pin_defini=description.pin_defini,
        ),
        appareil_connu=True,
    )


async def fermer_session(session_id: UUID, *, valkey) -> None:
    """La personne ferme sa session. L'appareil, lui, **reste connu** : c'est le sien."""
    await _fermer(session_id, MotifFermeture.DECONNEXION, valkey=valkey)


async def _fermer(session_id: UUID, motif: MotifFermeture, *, valkey) -> None:
    session = await session_module.lire_session(session_id, valkey=valkey)
    await session_module.revoquer_session(session_id, valkey=valkey)
    if session is None:
        return
    tenant_id = UUID(session["tenant_id"])
    async with transaction(tenant_id) as connexion:
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_SESSION_FERMEE,
                {
                    "compte_id": session["compte_id"],
                    "session_id": str(session_id),
                    "motif": motif.value,
                },
            ),
        )


async def suspendre(tenant_id: UUID, compte_id: UUID, par: UUID, *, valkey) -> None:
    """Le compte ne sert plus rien, à la requête suivante.

    Le statut et l'événement sont écrits dans la même transaction ; la révocation des sessions et
    l'oubli des appareils sont des effets sur l'**éphémère**, faits après le `COMMIT`, parce que
    Valkey ne participe pas à la transaction. C'est l'écart nommé du contrôle de constitution : une
    panne entre les deux laisse un compte suspendu dont les sessions tombent tout de même, parce
    que le statut est relu à chaque rotation et à chaque ouverture.
    """
    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "compte introuvable", statut=404)
    async with transaction(tenant_id) as connexion:
        await acces.poser_statut(connexion, compte_id, StatutCompte.SUSPENDU.value)
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_COMPTE_SUSPENDU,
                {"compte_id": str(compte_id), "suspendu_par": str(par)},
            ),
        )
    fermees = await session_module.revoquer_toutes(compte_id, valkey=valkey)
    await appareil_module.oublier(compte_id, valkey=valkey)
    if fermees:
        async with transaction(tenant_id) as connexion:
            for session_id in fermees:
                await acces.inserer_evenement(
                    connexion,
                    tenant_id,
                    Evenement(
                        EVENEMENT_SESSION_FERMEE,
                        {
                            "compte_id": str(compte_id),
                            "session_id": str(session_id),
                            "motif": MotifFermeture.SUSPENSION.value,
                        },
                    ),
                )


# --- Le code personnel : quatre chiffres, et tout ce qui les rend suffisants --------------------


def _hacheur():
    """Argon2id aux paramètres minimaux recommandés (research.md R-13).

    Le produit tourne sur des serveurs contraints : plus coûteux, la vérification ferait attendre
    à chaque ouverture. Ce n'est pas l'empreinte qui protège quatre chiffres, c'est la conjonction
    de l'appareil connu, des cinq essais et du verrou durable.
    """
    from argon2 import PasswordHasher

    return PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def _sel_du_compte(pin: str, compte_id: UUID) -> str:
    """Le code est haché **avec l'identifiant du compte** : deux comptes au même code personnel
    n'ont pas la même empreinte, et une empreinte volée ne se rejoue pas sur un autre compte."""
    return f"{pin}:{compte_id}"


async def definir_pin(
    compte_id: UUID,
    tenant_id: UUID,
    session_id: UUID,
    pin: str,
    pin_courant: str | None,
    *,
    valkey,
    politique: PolitiqueSecurite,
) -> None:
    """Définit ou change le code personnel. Exige le code courant, sauf dispense récente.

    La dispense (dix minutes après une ouverture par code reçu ou par lien) est ce qui permet de
    **redéfinir un code oublié** : sans elle, oublier son code personnel enfermerait dehors.
    """
    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "compte introuvable", statut=404)

    if description.pin_defini and not await _dispense_de_pin_courant(
        session_id, valkey=valkey, politique=politique
    ):
        if pin_courant is None:
            raise ErreurMetier(
                "AUT_PIN_ABSENT",
                "le code personnel courant est exigé pour en définir un nouveau",
                champ="pin_courant",
            )
        if not await _pin_correct(tenant_id, compte_id, pin_courant):
            raise ErreurMetier(
                "AUT_PIN_INVALIDE",
                "le code personnel courant ne correspond pas",
                champ="pin_courant",
            )

    empreinte = _hacheur().hash(_sel_du_compte(pin, compte_id))
    async with transaction(tenant_id) as connexion:
        await acces.poser_pin(connexion, compte_id, empreinte)
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_PIN_DEFINI,
                {"compte_id": str(compte_id), "remplace": description.pin_defini},
            ),
        )
    await valkey.delete(CLE_PIN_TENTATIVES.format(compte_id=compte_id))


async def _dispense_de_pin_courant(session_id: UUID, *, valkey, politique) -> bool:
    session = await session_module.lire_session(session_id, valkey=valkey)
    if session is None or session["canal"] not in (
        CanalOuverture.CODE.value,
        CanalOuverture.LIEN.value,
    ):
        return False
    ouverte_le = datetime.fromisoformat(session["ouverte_le"])
    return datetime.now(UTC) - ouverte_le <= politique.DISPENSE_PIN_COURANT


async def _pin_correct(tenant_id: UUID, compte_id: UUID, pin: str) -> bool:
    """La vérification est à temps constant, et une empreinte absente n'est jamais « correcte »."""
    from argon2.exceptions import VerificationError, VerifyMismatchError

    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
    if ligne is None or ligne["pin_empreinte"] is None:
        return False
    try:
        return _hacheur().verify(ligne["pin_empreinte"], _sel_du_compte(pin, compte_id))
    except VerifyMismatchError, VerificationError:
        return False


async def comptes_de_l_appareil(appareil: appareil_module.Appareil, *, valkey) -> ReponseAppareil:
    """Ce que l'écran d'ouverture propose : des noms, et **jamais** un numéro (FR-021)."""
    comptes = []
    for _, compte_id, tenant_id in await appareil_module.comptes_connus(appareil, valkey=valkey):
        description = await decrire_compte(tenant_id, compte_id)
        if description is None or description.statut == StatutCompte.SUSPENDU:
            continue
        identite = await personnes.lire_identite(tenant_id, description.personne_id)
        if identite is None:
            continue
        comptes.append(
            CompteConnu(
                compte_id=compte_id,
                nom=identite.nom,
                prenoms=identite.prenoms,
                pin_defini=description.pin_defini,
            )
        )
    return ReponseAppareil(comptes=comptes)


async def ouvrir_par_pin(
    compte_id: UUID,
    pin: str,
    appareil: appareil_module.Appareil,
    *,
    valkey,
    politique: PolitiqueSecurite,
    secret_jeton: str,
) -> tuple[SessionOuverte, SecretsDeSession]:
    """Six refus, et une session. Le code seul n'ouvre rien : il faut cet appareil, et cinq essais.

    Un compte suspendu disparaît de l'appareil au moment où il essaie : la personne ne verra plus
    son nom à l'écran suivant, et c'est ce qu'il faut dire.
    """
    connu = None
    for secret, compte_connu, tenant_id in await appareil_module.comptes_connus(
        appareil, valkey=valkey
    ):
        if compte_connu == compte_id:
            connu = (secret, tenant_id)
            break
    if connu is None:
        raise ErreurMetier(
            "AUT_APPAREIL_INCONNU", "cet appareil n'est pas connu de ce compte", statut=401
        )
    _, tenant_id = connu

    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("AUT_APPAREIL_INCONNU", "compte introuvable", statut=401)
    if description.statut == StatutCompte.SUSPENDU:
        await appareil_module.oublier(compte_id, valkey=valkey)
        raise ErreurMetier("AUT_COMPTE_SUSPENDU", "ce compte est suspendu", statut=401)
    if not description.pin_defini:
        raise ErreurMetier(
            "AUT_PIN_ABSENT", "aucun code personnel n'est défini pour ce compte", statut=401
        )

    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
    if ligne["pin_verrouille_le"] is not None:
        raise ErreurMetier(
            "AUT_PIN_TENTATIVES_EPUISEES",
            "le code personnel est verrouillé ; une ouverture par code reçu le rouvre",
            statut=401,
        )

    plafond = await _valeur_entiere(tenant_id, CLE_PIN_TENTATIVES_MAX, 5)
    if not await _pin_correct(tenant_id, compte_id, pin):
        cle = CLE_PIN_TENTATIVES.format(compte_id=compte_id)
        faux = int(await valkey.incr(cle))
        await valkey.expire(cle, 3600, nx=True)
        if faux >= plafond:
            async with transaction(tenant_id) as connexion:
                await acces.poser_verrou_pin(connexion, compte_id, datetime.now(UTC))
            await valkey.delete(cle)
            raise ErreurMetier(
                "AUT_PIN_TENTATIVES_EPUISEES",
                "le code personnel est verrouillé ; une ouverture par code reçu le rouvre",
                statut=401,
            )
        raise ErreurMetier(
            "AUT_PIN_INVALIDE",
            "le code personnel ne correspond pas",
            statut=401,
            details={"tentatives_restantes": plafond - faux},
        )

    await valkey.delete(CLE_PIN_TENTATIVES.format(compte_id=compte_id))
    return await _ouvrir_pour(
        compte_id,
        tenant_id,
        CanalOuverture.PIN,
        valkey=valkey,
        politique=politique,
        secret_jeton=secret_jeton,
    )


# --- Créer un compte, l'inviter, l'activer par lien ---------------------------------------------


def _empreinte_jeton(jeton: str) -> str:
    return hashlib.sha256(jeton.encode()).hexdigest()


async def identifiant_partage(tenant_id: UUID, compte_id: UUID) -> bool:
    """Plus d'un compte du tenant porte ce numéro (FR-040). Aucune colonne ne le duplique.

    T1b le lira avant de poser un rattachement de personnel : un numéro partagé entre deux parents
    ne doit pas devenir la porte d'entrée d'un compte qui a des capacités sur l'établissement.
    """
    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        return False
    async with transaction(tenant_id) as connexion:
        return await acces.compter_meme_identifiant(connexion, description.identifiant) > 1


async def _bloquages_de_creation(
    tenant_id: UUID, personne_id: UUID, identifiant: str, partage_familial: bool
) -> list[Bloquage]:
    bloquages: list[Bloquage] = []
    identite = await personnes.lire_identite(tenant_id, personne_id)
    if identite is None:
        bloquages.append(
            Bloquage(code="TEN_RESSOURCE_INTROUVABLE", details={"champ": "personne_id"})
        )
        return bloquages
    async with transaction(tenant_id) as connexion:
        deja = await acces.lire_compte_par_personne(connexion, personne_id)
        porteurs = await acces.compter_meme_identifiant(connexion, identifiant)
    if deja is not None:
        bloquages.append(
            Bloquage(code="TEN_RESSOURCE_DEJA_EXISTANTE", details={"compte_id": str(deja["id"])})
        )
    if porteurs > 0 and not partage_familial:
        bloquages.append(
            Bloquage(
                code="AUT_IDENTIFIANT_DEJA_UTILISE",
                details={"partage_familial_requis": True, "comptes": porteurs},
            )
        )
    return bloquages


async def verifier_creation(
    tenant_id: UUID, personne_id: UUID, identifiant: str, partage_familial: bool
) -> VerificationCreationCompte:
    """Le pendant de la création : ce qui bloquerait, **sans rien écrire ni envoyer** (E-04).

    Le secrétariat l'appelle pendant la saisie : dire « ce numéro est déjà celui d'un autre parent,
    déclarez le partage » avant le bouton vaut mieux qu'un refus après.
    """
    bloquages = await _bloquages_de_creation(tenant_id, personne_id, identifiant, partage_familial)
    issues = []
    for bloquage in bloquages:
        if bloquage.code == "AUT_IDENTIFIANT_DEJA_UTILISE":
            issues.append("compte.creation.declarer_partage")
        elif bloquage.code == "TEN_RESSOURCE_DEJA_EXISTANTE":
            issues.append("compte.creation.ouvrir_le_compte_existant")
        else:
            issues.append("compte.creation.choisir_une_autre_personne")
    return VerificationCreationCompte(bloquages=bloquages, issues=issues)


async def _nom_de_l_etablissement(tenant_id: UUID, etablissement_id: UUID) -> str | None:
    """Le nom que le message d'invitation porte : une famille reconnaît son école, pas le produit."""
    trouves = await tenants.lire_etablissements(tenant_id, [etablissement_id])
    return trouves[0].nom if trouves else None


async def creer_compte(
    tenant_id: UUID,
    personne_id: UUID,
    identifiant: str,
    partage_familial: bool,
    cree_par: UUID,
    etablissement_id: UUID,
    *,
    valkey,
) -> CompteCree:
    """Le compte naît `invite`, et son lien part par l'outbox. Le jeton ne sort jamais d'ici.

    Le partage d'un numéro n'est pas interdit : il est **déclaré**. La déclaration est l'événement
    de création, avec son auteur et sa date ; sans elle, le second compte sur un même numéro est
    refusé, parce que le plus souvent c'est une erreur de saisie.
    """
    bloquages = await _bloquages_de_creation(tenant_id, personne_id, identifiant, partage_familial)
    if bloquages:
        premier = bloquages[0]
        statut = 404 if premier.code == "TEN_RESSOURCE_INTROUVABLE" else 409
        if premier.code == "AUT_IDENTIFIANT_DEJA_UTILISE":
            statut = 422
        raise ErreurMetier(
            premier.code,
            "la création du compte est refusée",
            statut=statut,
            details=dict(premier.details),
        )

    compte_id = uuid.uuid7()
    jours = await _valeur_entiere(tenant_id, CLE_INVITATION_JOURS, 7)
    jeton = secrets.token_urlsafe(32)
    envoi_id = uuid.uuid7()
    expire_le = datetime.now(UTC) + timedelta(days=jours)
    identite = await personnes.lire_identite(tenant_id, personne_id)
    langue = identite.langue if identite else gabarits.LANGUE_DE_SECOURS
    ecole = await _nom_de_l_etablissement(tenant_id, etablissement_id)

    async with transaction(tenant_id) as connexion:
        await acces.inserer_compte(
            connexion,
            compte_id,
            tenant_id,
            personne_id,
            identifiant,
            StatutCompte.INVITE.value,
        )
        await acces.poser_invitation(
            connexion, compte_id, _empreinte_jeton(jeton), expire_le, datetime.now(UTC)
        )
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_COMPTE_CREE,
                {
                    "compte_id": str(compte_id),
                    "personne_id": str(personne_id),
                    "identifiant": identifiant,
                    "partage_familial": partage_familial,
                    "cree_par": str(cree_par),
                },
            ),
        )
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_COMPTE_INVITE,
                {
                    "compte_id": str(compte_id),
                    "identifiant": identifiant,
                    "envoi_id": str(envoi_id),
                    "langue": langue,
                    "etablissement": ecole,
                    "expire_le": expire_le.isoformat(),
                    "jours": jours,
                },
            ),
        )
    await valkey.set(
        CLE_INVITATION_TEXTE.format(envoi_id=envoi_id),
        jeton,
        ex=int(timedelta(hours=1).total_seconds()),
    )
    return CompteCree(id=compte_id, statut=StatutCompte.INVITE, invite_le=datetime.now(UTC))


async def renvoyer_invitation(
    tenant_id: UUID, compte_id: UUID, etablissement_id: UUID, *, valkey
) -> CompteCree:
    """Un lien neuf, et l'ancien cesse de valoir. Un compte déjà actif n'en a pas besoin."""
    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "compte introuvable", statut=404)
    if description.statut == StatutCompte.ACTIF:
        raise ErreurMetier(
            "AUT_COMPTE_DEJA_ACTIF",
            "ce compte est déjà actif ; une ouverture par code reçu suffit",
        )
    if description.statut == StatutCompte.SUSPENDU:
        raise ErreurMetier("AUT_COMPTE_SUSPENDU", "ce compte est suspendu", statut=422)

    jours = await _valeur_entiere(tenant_id, CLE_INVITATION_JOURS, 7)
    jeton = secrets.token_urlsafe(32)
    envoi_id = uuid.uuid7()
    expire_le = datetime.now(UTC) + timedelta(days=jours)
    identite = await personnes.lire_identite(tenant_id, description.personne_id)
    ecole = await _nom_de_l_etablissement(tenant_id, etablissement_id)
    invite_le = datetime.now(UTC)
    async with transaction(tenant_id) as connexion:
        await acces.poser_invitation(
            connexion, compte_id, _empreinte_jeton(jeton), expire_le, invite_le
        )
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_COMPTE_INVITE,
                {
                    "compte_id": str(compte_id),
                    "identifiant": description.identifiant,
                    "envoi_id": str(envoi_id),
                    "langue": identite.langue if identite else gabarits.LANGUE_DE_SECOURS,
                    "etablissement": ecole,
                    "expire_le": expire_le.isoformat(),
                    "jours": jours,
                },
            ),
        )
    await valkey.set(
        CLE_INVITATION_TEXTE.format(envoi_id=envoi_id),
        jeton,
        ex=int(timedelta(hours=1).total_seconds()),
    )
    return CompteCree(id=compte_id, statut=StatutCompte.INVITE, invite_le=invite_le)


async def activer_par_invitation(
    jeton: str, *, valkey, politique: PolitiqueSecurite, secret_jeton: str
) -> tuple[SessionOuverte, SecretsDeSession]:
    """Le lien ouvre une session, une seule fois. Consommé, expiré ou remplacé, il ne vaut rien.

    Le refus est le même dans les trois cas : le dire autrement apprendrait à qui essaie si le lien
    a existé.
    """
    async with sans_tenant() as connexion:
        trouve = await acces.appeler_compte_par_invitation(connexion, _empreinte_jeton(jeton))
    refus = ErreurMetier(
        "AUT_INVITATION_INVALIDE",
        "ce lien n'est plus valable",
        statut=401,
    )
    if trouve is None:
        raise refus
    expire_le = trouve["invitation_expire_le"]
    if expire_le is None or expire_le < datetime.now(UTC):
        raise refus
    if trouve["statut"] == StatutCompte.SUSPENDU.value:
        raise ErreurMetier("AUT_COMPTE_SUSPENDU", "ce compte est suspendu", statut=401)

    compte_id, tenant_id = trouve["id"], trouve["tenant_id"]
    async with transaction(tenant_id) as connexion:
        # Le lien est consommé **avant** l'ouverture : deux clics ne valent pas deux activations.
        await acces.poser_invitation(connexion, compte_id, None, None, None)
    return await _ouvrir_pour(
        compte_id,
        tenant_id,
        CanalOuverture.LIEN,
        valkey=valkey,
        politique=politique,
        secret_jeton=secret_jeton,
    )


# --- Changer de numéro : en libre-service, ou par le secrétariat --------------------------------


async def demander_changement(
    tenant_id: UUID,
    compte_id: UUID,
    nouveau: str,
    adresse_client: str,
    *,
    valkey,
    politique: PolitiqueSecurite,
    compter: Limiteur,
) -> None:
    """Un code part vers le **nouveau** numéro, toujours, même s'il est déjà pris (E-04, FR-036).

    Une demande n'est donc jamais un oracle : seule la personne qui possède réellement ce numéro
    apprendra, à la vérification, qu'il est déjà celui d'un autre compte.
    """
    for cle, plafond, fenetre in (
        (
            CLE_OTP_DEBIT_CLIENT.format(adresse=adresse_client),
            politique.OTP_PAR_HEURE_PAR_CLIENT,
            timedelta(hours=1),
        ),
        (
            CLE_OTP_DEBIT.format(identifiant=nouveau),
            politique.OTP_PAR_HEURE_PAR_NUMERO,
            timedelta(hours=1),
        ),
        (CLE_OTP_RENVOI.format(identifiant=nouveau), 1, politique.OTP_RENVOI),
    ):
        reprise = await compter(valkey, cle, plafond, fenetre)
        if reprise is not None:
            raise _limite_atteinte(reprise)

    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "compte introuvable", statut=404)
    identite = await personnes.lire_identite(tenant_id, description.personne_id)

    code = f"{secrets.randbelow(10**politique.OTP_LONGUEUR):0{politique.OTP_LONGUEUR}d}"
    envoi_id = uuid.uuid7()
    validite = int(politique.OTP_VALIDITE.total_seconds())
    await valkey.set(
        CLE_CHANGEMENT.format(compte_id=compte_id),
        _json(
            {
                "nouveau": nouveau,
                "empreinte": _empreinte_code(code, envoi_id),
                "tentatives": 0,
                "envoi_id": str(envoi_id),
            }
        ),
        ex=validite,
    )
    await valkey.set(CLE_OTP_TEXTE.format(envoi_id=envoi_id), code, ex=validite)
    async with transaction(tenant_id) as connexion:
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_OTP_DEMANDE,
                {
                    "compte_id": str(compte_id),
                    "identifiant": nouveau,
                    "envoi_id": str(envoi_id),
                    "langue": identite.langue if identite else gabarits.LANGUE_DE_SECOURS,
                },
            ),
        )


async def verifier_changement(
    tenant_id: UUID, compte_id: UUID, code: str, *, valkey, politique: PolitiqueSecurite
) -> None:
    """L'identifiant change ici, et pas avant. La session courante survit : rien ne la menace."""
    cle = CLE_CHANGEMENT.format(compte_id=compte_id)
    brut = await valkey.get(cle)
    if brut is None:
        raise ErreurMetier(
            "AUT_OTP_EXPIRE", "le code a expiré ou n'a jamais été demandé", statut=401
        )
    charge = _charge(brut)
    if not secrets.compare_digest(
        charge["empreinte"], _empreinte_code(code, UUID(charge["envoi_id"]))
    ):
        charge["tentatives"] += 1
        restantes = politique.OTP_TENTATIVES - charge["tentatives"]
        if restantes <= 0:
            await valkey.delete(cle)
            raise ErreurMetier(
                "AUT_OTP_TENTATIVES_EPUISEES", "le code a été refusé trop de fois", statut=401
            )
        await valkey.set(cle, _json(charge), keepttl=True)
        raise ErreurMetier(
            "AUT_OTP_INVALIDE",
            "le code ne correspond pas",
            statut=401,
            details={"tentatives_restantes": restantes},
        )

    nouveau = charge["nouveau"]
    description = await decrire_compte(tenant_id, compte_id)
    async with transaction(tenant_id) as connexion:
        # Le refus arrive ici, après la preuve de possession : jamais à la demande (E-04).
        if await acces.compter_meme_identifiant(connexion, nouveau) > 0:
            raise ErreurMetier(
                "AUT_IDENTIFIANT_DEJA_UTILISE",
                "ce numéro est déjà celui d'un autre compte",
                champ="nouvel_identifiant",
            )
    await _changer_identifiant(
        tenant_id, compte_id, description.identifiant, nouveau, "PERSONNE", valkey=valkey
    )
    await valkey.delete(cle)


async def changer_identifiant_administratif(
    tenant_id: UUID, compte_id: UUID, nouveau: str, par: UUID, *, valkey
) -> None:
    """Le secrétariat change le numéro sans vérification préalable, et **tout tombe**.

    C'est le geste qui répare un numéro perdu : la personne ne peut plus recevoir de code sur
    l'ancien. Toutes les sessions se ferment et les appareils oublient le compte, parce que rien ne
    prouve encore que le nouveau numéro est le sien ; sa première ouverture par code reçu le
    prouvera.
    """
    description = await decrire_compte(tenant_id, compte_id)
    if description is None:
        raise ErreurMetier("TEN_RESSOURCE_INTROUVABLE", "compte introuvable", statut=404)
    async with transaction(tenant_id) as connexion:
        if await acces.compter_meme_identifiant(connexion, nouveau) > 0:
            raise ErreurMetier(
                "AUT_IDENTIFIANT_DEJA_UTILISE",
                "ce numéro est déjà celui d'un autre compte du tenant",
                champ="nouvel_identifiant",
            )
    await _changer_identifiant(
        tenant_id, compte_id, description.identifiant, nouveau, "ADMINISTRATION", valkey=valkey
    )
    fermees = await session_module.revoquer_toutes(compte_id, valkey=valkey)
    await appareil_module.oublier(compte_id, valkey=valkey)
    if fermees:
        async with transaction(tenant_id) as connexion:
            for session_id in fermees:
                await acces.inserer_evenement(
                    connexion,
                    tenant_id,
                    Evenement(
                        EVENEMENT_SESSION_FERMEE,
                        {
                            "compte_id": str(compte_id),
                            "session_id": str(session_id),
                            "motif": MotifFermeture.CHANGEMENT_NUMERO.value,
                        },
                    ),
                )


async def _changer_identifiant(
    tenant_id: UUID, compte_id: UUID, ancien: str, nouveau: str, par: str, *, valkey
) -> None:
    """L'écriture et l'événement dans la même transaction ; l'ancien numéro est informé, toujours."""
    description = await decrire_compte(tenant_id, compte_id)
    identite = await personnes.lire_identite(tenant_id, description.personne_id)
    envoi_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.poser_identifiant(connexion, compte_id, nouveau)
        await acces.inserer_evenement(
            connexion,
            tenant_id,
            Evenement(
                EVENEMENT_IDENTIFIANT_CHANGE,
                {
                    "compte_id": str(compte_id),
                    "ancien": ancien,
                    "nouveau": nouveau,
                    "par": par,
                    "identifiant": ancien,
                    "envoi_id": str(envoi_id),
                    "langue": identite.langue if identite else gabarits.LANGUE_DE_SECOURS,
                },
            ),
        )
    # Le texte de l'information est composé à l'envoi ; ce qu'il dit est le nouveau numéro.
    await valkey.set(
        CLE_CHANGEMENT_TEXTE.format(envoi_id=envoi_id),
        nouveau,
        ex=int(timedelta(hours=1).total_seconds()),
    )


# --- Le travailleur : envoyer ce que l'outbox a écrit -------------------------------------------


async def consommer_envoi(
    tenant_id: UUID,
    evenement: Evenement,
    passerelle,
    valkey,
    *,
    nom_produit: str,
    politique: PolitiqueSecurite,
    url_publique: str,
) -> None:
    """Lit le secret en clair dans Valkey par `envoi_id`, compose, envoie, efface.

    Idempotent par construction : un texte déjà effacé fait du second passage un non-événement.
    C'est ce que « livraison au moins une fois » exige du consommateur.
    """
    envoi_id = evenement.charge.get("envoi_id")
    if envoi_id is None:
        journal.info("événement d'envoi sans envoi_id, ignoré : %s", evenement.type)
        return
    gabarit, cle_texte = _GABARIT_PAR_TYPE.get(evenement.type, (None, None))
    if gabarit is None:
        journal.info("type d'envoi inconnu, ignoré : %s", evenement.type)
        return
    cle = cle_texte.format(envoi_id=envoi_id)
    secret = await valkey.get(cle)
    if secret is None:
        journal.info("envoi %s déjà traité ou expiré : rien à envoyer", envoi_id)
        return
    valeur = secret.decode() if isinstance(secret, bytes) else secret
    message = gabarits.rendre(
        gabarit,
        evenement.charge.get("langue", gabarits.LANGUE_DE_SECOURS),
        **_parametres(gabarit, valeur, evenement, nom_produit, politique, url_publique),
    )
    # La référence de l'envoi est celle de l'événement : un second passage la réutilise.
    await passerelle.envoyer(evenement.charge["identifiant"], message, UUID(str(envoi_id)))
    await valkey.delete(cle)


# Le gabarit et la clé du secret, par type d'événement. Le secret ne voyage jamais dans la charge
# de l'événement : l'outbox est un grand livre, et un grand livre se conserve.
_GABARIT_PAR_TYPE = {
    EVENEMENT_OTP_DEMANDE: ("otp", CLE_OTP_TEXTE),
    EVENEMENT_COMPTE_INVITE: ("invitation", CLE_INVITATION_TEXTE),
    EVENEMENT_IDENTIFIANT_CHANGE: ("changement_ancien_numero", CLE_CHANGEMENT_TEXTE),
}


def _parametres(
    gabarit: str,
    valeur: str,
    evenement: Evenement,
    nom_produit: str,
    politique: PolitiqueSecurite,
    url_publique: str,
) -> dict[str, object]:
    """Ce que chaque gabarit attend. Le secret lu dans Valkey y entre, et nulle part ailleurs."""
    if gabarit == "otp":
        return {
            "produit": nom_produit,
            "code": valeur,
            "minutes": int(politique.OTP_VALIDITE.total_seconds() // 60),
        }
    if gabarit == "invitation":
        return {
            "etablissement": evenement.charge.get("etablissement", nom_produit),
            "jours": evenement.charge.get("jours", 7),
            "lien": f"{url_publique.rstrip('/')}/activation/{valeur}",
        }
    return {"produit": nom_produit, "nouveau": valeur}


async def consommer_lot(tenant_id: UUID, consommateur: outbox.Consommateur, n: int) -> int:
    """Le même parcours que `tenants`, sur la table d'outbox de ce module."""
    return await outbox.consommer_lot(tenant_id, evenement_outbox, consommateur, n)


async def reprendre_evenements(tenant_id: UUID, delai_orphelin: timedelta) -> None:
    async with transaction(tenant_id) as connexion:
        await acces.reprendre_pris_orphelins(connexion, tenant_id, delai_orphelin)
        await acces.reprendre_en_echec(connexion, tenant_id)
