"""Les outils des tests d'authentification : demander un code, le lire, ouvrir une session.

Tout passe par l'API, jamais par le service : ce que ces tests vérifient est le comportement du
produit vu du dehors, en-têtes et cookies compris.
"""

import re
import uuid
from dataclasses import dataclass
from datetime import date
from uuid import UUID

import httpx

PREFIXE = "/api/v1"
MOTIF_CODE = re.compile(r"\b(\d{6})\b")


@dataclass(frozen=True)
class Session:
    """Ce qu'une ouverture rend : le jeton, les cookies, et le compte qui vient d'entrer."""

    jeton: str
    cookies: dict[str, str]
    compte: dict


def cle_de_requete() -> str:
    return str(uuid.uuid7())


async def demander(
    client: httpx.AsyncClient, numero: str, requete_id: str | None = None
) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/auth/otp",
        headers={"X-Nelo-Requete": requete_id or cle_de_requete()},
        json={"identifiant": numero},
    )


def code_recu(application, numero: str) -> str:
    """Le dernier code envoyé à ce numéro par la passerelle simulée.

    Le code ne passe **jamais** par la réponse de l'API : il part par l'outbox, et le test le lit
    là où une personne le lirait, dans le message.
    """
    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert envois, f"aucun message envoyé à {numero}"
    trouve = MOTIF_CODE.search(envois[-1].texte)
    assert trouve, f"aucun code à six chiffres dans « {envois[-1].texte} »"
    return trouve.group(1)


async def vider_envois(application) -> None:
    application.state.passerelle_sms.envoyes.clear()


async def tenants_du_numero(numero: str) -> list[UUID]:
    """Les tenants dont un compte porte ce numéro, par la fonction qui répond avant tout tenant."""
    from modules.shared.bd import sans_tenant
    from modules.socle.habilitations import acces

    async with sans_tenant() as connexion:
        trouves = await acces.appeler_comptes_par_identifiant(connexion, numero)
    return list(dict.fromkeys(compte["tenant_id"] for compte in trouves))


async def tourner(application, *tenants: UUID) -> int:
    """Un tour du travailleur : l'outbox est vidée, les messages partent.

    Sans tenant nommé, le tour parcourt **tous** ceux de la base, comme en production. La base de
    test en accumule deux par test : un tour complet à chaque ouverture de session rendrait la
    suite quadratique. Un test qui sait de quel tenant relève son événement le dit, et le tour ne
    regarde que celui-là.
    """
    from api.travailleur import Travailleur

    travailleur = Travailleur(application.state.configuration, _aiguilleur(application))
    if not tenants:
        return await travailleur.un_tour()
    return await travailleur.un_tour_de(list(tenants))


def _aiguilleur(application):
    from api import consommateurs

    return consommateurs.aiguilleur(
        application.state.passerelle_sms, application.state.valkey, application.state.configuration
    )


async def semer_compte_neuf(tenant, statut: str = "actif", langue: str = "fr") -> tuple[str, UUID]:
    """Une personne, son compte dans l'état voulu et son affectation vivante ; rend `(numéro, compte)`.

    Le numéro vient de `numero_de_test()` : un seul compte le porte, et la vérification du code
    ouvre donc une session sans passer par le choix de US8.
    """
    from modules.socle import habilitations, personnes
    from tests.conftest import numero_de_test

    numero = numero_de_test()
    personne_id = await personnes.creer_personne(
        tenant.tenant, f"Semé {numero[-4:]}", "Awa", langue, numero
    )
    compte_id = await habilitations.semer_compte(tenant.tenant, personne_id, numero, statut)
    await habilitations.creer_affectation(
        tenant.tenant, compte_id, tenant.annee, tenant.etablissement, date.today(), None
    )
    return numero, compte_id


async def verifier(
    client: httpx.AsyncClient,
    numero: str,
    code: str,
    compte_id: UUID | None = None,
) -> httpx.Response:
    """La vérification telle quelle : les suites qui étudient les refus lisent la réponse brute."""
    corps: dict = {"identifiant": numero, "code": code}
    if compte_id is not None:
        corps["compte_id"] = str(compte_id)
    return await client.post(
        f"{PREFIXE}/auth/otp/verification",
        headers={"X-Nelo-Requete": cle_de_requete()},
        json=corps,
    )


async def evenements(tenant_id: UUID, type_recherche: str | None = None) -> list[dict]:
    """Les événements écrits dans l'outbox de `habilitations` pour ce tenant, dans l'ordre.

    Ils se lisent en base et non dans la réponse : un changement d'état qui n'écrit pas son
    événement dans la même transaction est une saisie perdue (règle 10).
    """
    from sqlalchemy import select

    from modules.shared import transaction
    from modules.socle.habilitations.tables import evenement_outbox

    async with transaction(tenant_id) as connexion:
        resultat = await connexion.execute(
            select(evenement_outbox)
            .where(evenement_outbox.c.tenant_id == tenant_id)
            .order_by(evenement_outbox.c.ecrit_le, evenement_outbox.c.id)
        )
        lignes = [dict(ligne) for ligne in resultat.mappings()]
    if type_recherche is None:
        return lignes
    return [ligne for ligne in lignes if ligne["type"] == type_recherche]


async def ouvrir(
    client: httpx.AsyncClient,
    application,
    numero: str,
    compte_id: UUID | None = None,
) -> Session:
    """Le parcours entier : demander, lire le message, vérifier. Rend la session ouverte."""
    reponse = await demander(client, numero)
    assert reponse.status_code == 204, reponse.text
    await tourner(application, *await tenants_du_numero(numero))
    reponse = await verifier(client, numero, code_recu(application, numero), compte_id)
    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "SESSION", charge
    return Session(
        jeton=charge["jeton_acces"],
        cookies=dict(reponse.cookies),
        compte=charge["compte"],
    )


def en_tetes(
    session: Session,
    etablissement_id: UUID | None = None,
    *,
    ecriture: bool = False,
    annee_id: UUID | None = None,
) -> dict[str, str]:
    """Les en-têtes d'une requête authentifiée, tels que les middlewares les attendent."""
    en_tetes = {"Authorization": f"Bearer {session.jeton}"}
    if etablissement_id is not None:
        en_tetes["X-Nelo-Etablissement"] = str(etablissement_id)
    if annee_id is not None:
        en_tetes["X-Nelo-Annee"] = str(annee_id)
    if ecriture:
        en_tetes["X-Nelo-Requete"] = cle_de_requete()
    return en_tetes
