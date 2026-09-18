"""US6 : le secrétariat ouvre un compte, un lien part par SMS, et il ne sert qu'une fois.

C'est par là que les familles entrent dans le produit : quelqu'un qui n'a jamais vu l'application
reçoit un message court, l'ouvre, et se retrouve avec une session et un code personnel à définir.
Tout tient donc à ce que le lien soit **un secret jetable** : il ne revient dans aucune réponse, il
part par l'outbox et nulle part ailleurs, il vaut un temps réglé par le tenant, et le renvoyer
invalide le précédent. Consommé, expiré ou remplacé, il donne le même refus : dire lequel des trois
apprendrait à qui essaie si le lien a existé.

Et parce qu'un message se perd, le numéro reste une preuve suffisante : un compte encore invité qui
ouvre par code reçu s'active tout autant (FR-033).
"""

import re
from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy import update

from modules.shared import transaction
from modules.socle import habilitations, personnes
from modules.socle.habilitations import acces
from modules.socle.habilitations.tables import compte as table_compte
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    en_tetes,
    evenements,
    ouvrir,
    semer_compte_neuf,
    tourner,
    vider_envois,
)
from tests.conftest import numero_de_test

MOTIF_LIEN = re.compile(r"/activation/(\S+)")


async def creer(
    client, session, etablissement_id, personne_id, identifiant, *, partage=False, requete_id=None
) -> httpx.Response:
    entetes = en_tetes(session, etablissement_id, ecriture=True)
    if requete_id is not None:
        entetes["X-Nelo-Requete"] = requete_id
    return await client.post(
        f"{PREFIXE}/comptes",
        headers=entetes,
        json={
            "personne_id": str(personne_id),
            "identifiant": identifiant,
            "partage_familial": partage,
        },
    )


async def verifier_creation(
    client, session, etablissement_id, personne_id, identifiant, *, partage=False
) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/comptes/verification",
        headers=en_tetes(session, etablissement_id, ecriture=True),
        json={
            "personne_id": str(personne_id),
            "identifiant": identifiant,
            "partage_familial": partage,
        },
    )


async def renvoyer(client, session, etablissement_id, compte_id) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/comptes/{compte_id}/invitation",
        headers=en_tetes(session, etablissement_id, ecriture=True),
    )


async def activer(client, jeton: str) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/auth/invitation/{jeton}", headers={"X-Nelo-Requete": cle_de_requete()}
    )


async def personne_neuve(tenant, nom: str = "Diarra") -> tuple:
    """Une personne du tenant qui n'a pas encore de compte, et un numéro libre."""
    numero = numero_de_test()
    personne_id = await personnes.creer_personne(tenant.tenant, nom, "Ama", "fr", numero)
    return personne_id, numero


def envoi_vers(application, numero: str):
    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert envois, f"aucun message envoyé à {numero}"
    return envois[-1]


def lien_recu(application, numero: str) -> str:
    trouve = MOTIF_LIEN.search(envoi_vers(application, numero).texte)
    assert trouve, f"aucun lien d'activation dans « {envoi_vers(application, numero).texte} »"
    return trouve.group(1)


async def evenements_du_compte(tenant_id, compte_id) -> list[str]:
    return [
        e["type"]
        for e in await evenements(tenant_id)
        if e["charge"].get("compte_id") == str(compte_id)
    ]


async def peremer_l_invitation(tenant_id, compte_id) -> None:
    """L'échéance du lien est en base, pas dans l'éphémère : c'est elle qu'on recule."""
    async with transaction(tenant_id) as connexion:
        await connexion.execute(
            update(table_compte)
            .where(table_compte.c.id == compte_id)
            .values(invitation_expire_le=datetime.now(UTC) - timedelta(days=1))
        )


# --- Créer un compte -----------------------------------------------------------------------------


async def test_la_creation_invite_et_le_lien_part_par_message(
    client, application, sessions_ab, tenants_ab
):
    personne_id, numero = await personne_neuve(tenants_ab.a)
    await vider_envois(application)

    reponse = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)

    assert reponse.status_code == 201, reponse.text
    charge = reponse.json()
    assert charge["statut"] == "invite"
    assert charge["invite_le"] is not None
    assert reponse.headers["Location"] == f"/comptes/{charge['id']}"

    await tourner(application, tenants_ab.tenant_a)
    envoi = envoi_vers(application, numero)
    assert len(envoi.texte) <= 160, envoi.texte
    assert "École A" in envoi.texte
    lien = lien_recu(application, numero)
    assert f"{application.state.configuration.url_publique}/activation/{lien}" in envoi.texte
    # Le lien ne revient **jamais** dans la réponse : il n'existe que dans le message.
    assert lien not in reponse.text
    assert "activation" not in reponse.text


async def test_la_creation_ecrit_la_naissance_puis_l_invitation(
    client, application, sessions_ab, tenants_ab
):
    personne_id, numero = await personne_neuve(tenants_ab.a)

    reponse = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)

    ecrits = await evenements_du_compte(tenants_ab.tenant_a, reponse.json()["id"])
    assert ecrits == ["habilitations.compte.cree", "habilitations.compte.invite"]


async def test_la_creation_traverse_le_point_d_insertion_de_capacite(
    client, application, sessions_ab, tenants_ab, monkeypatch
):
    exiges: list[str] = []
    monkeypatch.setattr("api.capacites.exiger_capacite", exiges.append)
    personne_id, numero = await personne_neuve(tenants_ab.a)

    assert (
        await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)
    ).status_code == 201

    assert exiges == ["habilitations.compte.gerer"]


async def test_le_rejeu_de_la_meme_cle_ne_cree_ni_second_compte_ni_second_message(
    client, application, sessions_ab, tenants_ab
):
    """Une secrétaire qui appuie deux fois ne doit pas ouvrir deux comptes ni coûter deux SMS."""
    personne_id, numero = await personne_neuve(tenants_ab.a)
    await vider_envois(application)
    cle = cle_de_requete()

    premiere = await creer(
        client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero, requete_id=cle
    )
    seconde = await creer(
        client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero, requete_id=cle
    )

    assert premiere.status_code == 201
    assert seconde.status_code == 201
    assert seconde.json() == premiere.json()
    await tourner(application, tenants_ab.tenant_a)
    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert len(envois) == 1


async def test_une_personne_d_un_autre_tenant_est_introuvable(
    client, application, sessions_ab, tenants_ab
):
    """Hors périmètre, c'est introuvable : la réponse ne dit pas que cette personne existe."""
    reponse = await creer(
        client, sessions_ab.a, tenants_ab.etab_a, tenants_ab.personne_b, numero_de_test()
    )

    assert reponse.status_code == 404
    assert reponse.json()["code"] == "TEN_RESSOURCE_INTROUVABLE"


async def test_une_personne_deja_titulaire_d_un_compte_est_un_conflit(
    client, application, sessions_ab, tenants_ab
):
    reponse = await creer(
        client, sessions_ab.a, tenants_ab.etab_a, tenants_ab.personne_a, numero_de_test()
    )

    assert reponse.status_code == 409
    assert reponse.json()["code"] == "TEN_RESSOURCE_DEJA_EXISTANTE"


async def test_la_verification_dit_les_bloquages_sans_rien_ecrire_ni_envoyer(
    client, application, sessions_ab, tenants_ab
):
    """E-04 : dire « cette personne a déjà un compte » pendant la saisie vaut mieux qu'après."""
    await vider_envois(application)

    reponse = await verifier_creation(
        client, sessions_ab.a, tenants_ab.etab_a, tenants_ab.personne_a, numero_de_test()
    )

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert [b["code"] for b in charge["bloquages"]] == ["TEN_RESSOURCE_DEJA_EXISTANTE"]
    assert charge["issues"]
    await tourner(application, tenants_ab.tenant_a)
    assert application.state.passerelle_sms.envoyes == []


async def test_la_verification_ne_dit_rien_quand_rien_ne_s_y_oppose(
    client, application, sessions_ab, tenants_ab
):
    personne_id, numero = await personne_neuve(tenants_ab.a)

    reponse = await verifier_creation(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)

    assert reponse.json() == {"bloquages": [], "issues": []}


# --- Activer par le lien -------------------------------------------------------------------------


async def test_le_lien_active_le_compte_et_ouvre_la_session(
    client, application, sessions_ab, tenants_ab
):
    personne_id, numero = await personne_neuve(tenants_ab.a)
    creation = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)
    compte_id = creation.json()["id"]
    await tourner(application, tenants_ab.tenant_a)
    lien = lien_recu(application, numero)

    reponse = await activer(client, lien)

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "SESSION"
    assert charge["compte"]["pin_defini"] is False
    assert charge["appareil_connu"] is True

    async with transaction(tenants_ab.tenant_a) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
    assert ligne["statut"] == "actif"
    # Le lien est consommé : son empreinte ne vaut plus rien, et rien ne la remplace.
    assert ligne["invitation_empreinte"] is None

    connus = (await client.get(f"{PREFIXE}/auth/appareil")).json()["comptes"]
    assert compte_id in {c["compte_id"] for c in connus}

    activations = [
        e
        for e in await evenements(tenants_ab.tenant_a, "habilitations.compte.active")
        if e["charge"]["compte_id"] == compte_id
    ]
    assert [e["charge"]["canal"] for e in activations] == ["LIEN"]


async def test_un_lien_deja_consomme_ne_vaut_plus_rien(
    client, application, sessions_ab, tenants_ab
):
    personne_id, numero = await personne_neuve(tenants_ab.a)
    await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)
    await tourner(application, tenants_ab.tenant_a)
    lien = lien_recu(application, numero)
    assert (await activer(client, lien)).status_code == 200

    reponse = await activer(client, lien)

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_INVITATION_INVALIDE"


async def test_un_lien_expire_ne_vaut_plus_rien(client, application, sessions_ab, tenants_ab):
    personne_id, numero = await personne_neuve(tenants_ab.a)
    creation = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)
    await tourner(application, tenants_ab.tenant_a)
    lien = lien_recu(application, numero)
    await peremer_l_invitation(tenants_ab.tenant_a, creation.json()["id"])

    reponse = await activer(client, lien)

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_INVITATION_INVALIDE"


async def test_un_lien_inconnu_donne_le_meme_refus(client, application):
    reponse = await activer(client, "un-lien-que-personne-n-a-jamais-recu")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_INVITATION_INVALIDE"


# --- Renvoyer une invitation ---------------------------------------------------------------------


async def test_un_lien_renvoye_remplace_le_precedent(client, application, sessions_ab, tenants_ab):
    personne_id, numero = await personne_neuve(tenants_ab.a)
    creation = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)
    await tourner(application, tenants_ab.tenant_a)
    premier = lien_recu(application, numero)
    await vider_envois(application)

    renvoi = await renvoyer(client, sessions_ab.a, tenants_ab.etab_a, creation.json()["id"])
    await tourner(application, tenants_ab.tenant_a)
    second = lien_recu(application, numero)

    assert renvoi.status_code == 200, renvoi.text
    assert renvoi.json()["statut"] == "invite"
    assert second != premier
    assert (await activer(client, premier)).status_code == 401
    assert (await activer(client, second)).status_code == 200


async def test_un_renvoi_sur_un_compte_deja_actif_est_refuse(
    client, application, sessions_ab, tenants_ab
):
    """Le versant positif du refus est le parcours par code reçu : rien n'est perdu."""
    _, compte = await semer_compte_neuf(tenants_ab.a)

    reponse = await renvoyer(client, sessions_ab.a, tenants_ab.etab_a, compte)

    assert reponse.status_code == 422
    assert reponse.json()["code"] == "AUT_COMPTE_DEJA_ACTIF"


async def test_un_renvoi_sur_un_compte_suspendu_est_refuse(
    client, application, valkey, sessions_ab, tenants_ab
):
    _, compte = await semer_compte_neuf(tenants_ab.a, statut="invite")
    await habilitations.suspendre(tenants_ab.tenant_a, compte, tenants_ab.compte_a, valkey=valkey)

    reponse = await renvoyer(client, sessions_ab.a, tenants_ab.etab_a, compte)

    assert reponse.status_code == 422
    assert reponse.json()["code"] == "AUT_COMPTE_SUSPENDU"


# --- Le numéro reste une preuve suffisante --------------------------------------------------------


async def test_un_compte_invite_qui_ouvre_par_code_recu_devient_actif(
    client, application, tenants_ab
):
    """FR-033 : posséder le numéro est la preuve, quel que soit le canal. Le message perdu ne l'est plus."""
    numero, compte = await semer_compte_neuf(tenants_ab.a, statut="invite")

    session = await ouvrir(client, application, numero)

    assert session.compte["id"] == str(compte)
    async with transaction(tenants_ab.tenant_a) as connexion:
        assert (await acces.lire_statut(connexion, compte)) == "actif"
    activations = [
        e
        for e in await evenements(tenants_ab.tenant_a, "habilitations.compte.active")
        if e["charge"]["compte_id"] == str(compte)
    ]
    assert [e["charge"]["canal"] for e in activations] == ["CODE"]
