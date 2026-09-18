"""US7 : changer de numéro sans perdre son compte, et sans qu'une demande dise jamais oui ou non.

Un numéro change souvent, et c'est l'identifiant : sans procédure, un numéro perdu est un compte
perdu. Deux chemins, et ils n'ont pas les mêmes conséquences.

En libre-service, la personne possède encore son ancien téléphone : le code part vers le
**nouveau** numéro, l'identifiant ne bouge qu'une fois ce code vérifié, l'ancien numéro est informé,
et la session en cours survit. Le refus d'un numéro déjà pris tombe à la **vérification**, jamais à
la demande (E-04, FR-036) : autrement, saisir des numéros au hasard dirait lesquels sont des
comptes.

Par le secrétariat, la carte SIM est perdue : rien ne prouve encore que le nouveau numéro est le
sien, donc tout tombe, sessions et appareils compris, et sa première ouverture par code reçu tient
lieu de vérification.
"""

import httpx

from modules.shared import transaction
from modules.socle.habilitations import acces
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    code_recu,
    en_tetes,
    evenements,
    ouvrir,
    semer_compte_neuf,
    tourner,
    vider_envois,
)
from tests.conftest import numero_de_test

CHEMIN_PROTEGE = f"{PREFIXE}/parametres"
PIN = "1357"


async def demander_changement(client, session, nouveau: str) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/moi/telephone",
        headers=en_tetes(session, ecriture=True),
        json={"nouvel_identifiant": nouveau},
    )


async def verifier_changement(client, session, code: str) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/moi/telephone/verification",
        headers=en_tetes(session, ecriture=True),
        json={"code": code},
    )


async def changer_par_le_secretariat(
    client, session, etablissement_id, compte_id, nouveau: str
) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/comptes/{compte_id}/telephone",
        headers=en_tetes(session, etablissement_id, ecriture=True),
        json={"nouvel_identifiant": nouveau},
    )


async def identifiant_en_base(tenant_id, compte_id) -> str:
    async with transaction(tenant_id) as connexion:
        return (await acces.lire_compte(connexion, compte_id))["identifiant"]


def envois_vers(application, numero: str) -> list:
    return [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]


async def changements_ecrits(tenant_id, compte_id) -> list[dict]:
    return [
        e["charge"]
        for e in await evenements(tenant_id, "habilitations.identifiant.change")
        if e["charge"]["compte_id"] == str(compte_id)
    ]


# --- En libre-service : le code part vers le nouveau numéro ---------------------------------------


async def test_la_demande_envoie_le_code_au_nouveau_numero_sans_rien_changer(
    client, application, valkey, sessions_ab, tenants_ab
):
    nouveau = numero_de_test()
    await vider_envois(application)

    reponse = await demander_changement(client, sessions_ab.a, nouveau)
    await tourner(application, tenants_ab.tenant_a)

    assert reponse.status_code == 204
    assert not reponse.content
    assert code_recu(application, nouveau)
    # L'ancien numéro n'apprend rien tant que rien n'est fait : il sera informé à la vérification.
    assert envois_vers(application, tenants_ab.numero_a) == []
    assert (
        await identifiant_en_base(tenants_ab.tenant_a, tenants_ab.compte_a) == tenants_ab.numero_a
    )
    # La clé de l'éphémère est celle de data-model.md, et elle porte le changement en attente.
    assert await valkey.get(f"changement:{tenants_ab.compte_a}") is not None


async def test_deux_demandes_dans_la_minute_sont_limitees(client, application, sessions_ab):
    """Le délai avant renvoi est celui du code reçu : un changement ne l'escamote pas."""
    nouveau = numero_de_test()
    assert (await demander_changement(client, sessions_ab.a, nouveau)).status_code == 204

    seconde = await demander_changement(client, sessions_ab.a, nouveau)

    assert seconde.status_code == 429
    assert seconde.json()["code"] == "API_LIMITE_DEBIT"
    assert int(seconde.headers["Retry-After"]) > 0


async def test_un_code_faux_dit_les_tentatives_restantes(client, application, sessions_ab):
    nouveau = numero_de_test()
    await demander_changement(client, sessions_ab.a, nouveau)

    reponse = await verifier_changement(client, sessions_ab.a, "000000")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_OTP_INVALIDE"
    assert reponse.json()["details"]["tentatives_restantes"] == 4


async def test_cinq_codes_faux_detruisent_le_changement_en_cours(
    client, application, sessions_ab, tenants_ab
):
    nouveau = numero_de_test()
    await demander_changement(client, sessions_ab.a, nouveau)
    for _ in range(4):
        await verifier_changement(client, sessions_ab.a, "000000")

    cinquieme = await verifier_changement(client, sessions_ab.a, "000000")

    assert cinquieme.status_code == 401
    assert cinquieme.json()["code"] == "AUT_OTP_TENTATIVES_EPUISEES"
    assert (
        await identifiant_en_base(tenants_ab.tenant_a, tenants_ab.compte_a) == tenants_ab.numero_a
    )


async def test_sans_demande_en_cours_la_verification_dit_que_le_code_a_expire(
    client, application, sessions_ab
):
    reponse = await verifier_changement(client, sessions_ab.a, "123456")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_OTP_EXPIRE"


async def test_un_numero_deja_pris_recoit_le_code_et_le_refus_vient_apres(
    client, application, sessions_ab, tenants_ab
):
    """E-04, FR-036 : seule la personne qui possède réellement ce numéro apprend qu'il est pris."""
    occupe, _ = await semer_compte_neuf(tenants_ab.a)
    await vider_envois(application)

    demande = await demander_changement(client, sessions_ab.a, occupe)
    await tourner(application, tenants_ab.tenant_a)
    code = code_recu(application, occupe)
    verification = await verifier_changement(client, sessions_ab.a, code)

    assert demande.status_code == 204
    assert verification.status_code == 422
    assert verification.json()["code"] == "AUT_IDENTIFIANT_DEJA_UTILISE"
    assert (
        await identifiant_en_base(tenants_ab.tenant_a, tenants_ab.compte_a) == tenants_ab.numero_a
    )


async def test_la_verification_change_l_identifiant_et_informe_l_ancien_numero(
    client, application, sessions_ab, tenants_ab
):
    ancien = tenants_ab.numero_a
    nouveau = numero_de_test()
    await vider_envois(application)
    await demander_changement(client, sessions_ab.a, nouveau)
    await tourner(application, tenants_ab.tenant_a)

    reponse = await verifier_changement(client, sessions_ab.a, code_recu(application, nouveau))
    await tourner(application, tenants_ab.tenant_a)

    assert reponse.status_code == 204
    assert await identifiant_en_base(tenants_ab.tenant_a, tenants_ab.compte_a) == nouveau

    information = envois_vers(application, ancien)
    assert len(information) == 1
    assert nouveau in information[0].texte

    # La session courante n'est pas menacée : la personne n'a rien à refaire.
    suite = await client.get(CHEMIN_PROTEGE, headers=en_tetes(sessions_ab.a, tenants_ab.etab_a))
    assert suite.status_code == 200, suite.text

    ecrits = await changements_ecrits(tenants_ab.tenant_a, tenants_ab.compte_a)
    assert [c["par"] for c in ecrits] == ["PERSONNE"]
    assert ecrits[0]["ancien"] == ancien
    assert ecrits[0]["nouveau"] == nouveau


# --- Par le secrétariat : tout tombe, et la première ouverture vérifie -----------------------------


async def test_le_secretariat_change_le_numero_et_toutes_les_sessions_tombent(
    client, application, sessions_ab, tenants_ab
):
    ancien, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, ancien)
    assert (
        await client.post(
            f"{PREFIXE}/auth/pin/definition",
            headers={**en_tetes(session), "X-Nelo-Requete": cle_de_requete()},
            json={"pin": PIN},
        )
    ).status_code == 204
    nouveau = numero_de_test()
    await vider_envois(application)

    reponse = await changer_par_le_secretariat(
        client, sessions_ab.a, tenants_ab.etab_a, compte, nouveau
    )
    await tourner(application, tenants_ab.tenant_a)

    assert reponse.status_code == 204
    assert await identifiant_en_base(tenants_ab.tenant_a, compte) == nouveau

    coupee = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert coupee.status_code == 401
    assert coupee.json()["code"] == "AUT_SESSION_REVOQUEE"

    connus = (await client.get(f"{PREFIXE}/auth/appareil")).json()["comptes"]
    assert str(compte) not in {c["compte_id"] for c in connus}

    information = envois_vers(application, ancien)
    assert len(information) == 1
    assert nouveau in information[0].texte

    ecrits = await changements_ecrits(tenants_ab.tenant_a, compte)
    assert [c["par"] for c in ecrits] == ["ADMINISTRATION"]


async def test_la_premiere_ouverture_sur_le_nouveau_numero_tient_lieu_de_verification(
    client, application, sessions_ab, tenants_ab
):
    ancien, compte = await semer_compte_neuf(tenants_ab.a)
    nouveau = numero_de_test()
    await changer_par_le_secretariat(client, sessions_ab.a, tenants_ab.etab_a, compte, nouveau)

    session = await ouvrir(client, application, nouveau)

    assert session.compte["id"] == str(compte)
    # Un message vers chacun : l'information sur l'ancien numéro, le code sur le nouveau.
    assert len(envois_vers(application, ancien)) == 1
    assert len(envois_vers(application, nouveau)) == 1


async def test_le_secretariat_refuse_un_numero_deja_porte(
    client, application, sessions_ab, tenants_ab
):
    """Sans déclaration de partage, un second compte sur un numéro est presque toujours une faute."""
    _, compte = await semer_compte_neuf(tenants_ab.a)

    reponse = await changer_par_le_secretariat(
        client, sessions_ab.a, tenants_ab.etab_a, compte, tenants_ab.numero_a
    )

    assert reponse.status_code == 422
    assert reponse.json()["code"] == "AUT_IDENTIFIANT_DEJA_UTILISE"


async def test_la_route_du_secretariat_traverse_le_point_d_insertion_de_capacite(
    client, application, sessions_ab, tenants_ab, monkeypatch
):
    exiges: list[str] = []
    monkeypatch.setattr("api.capacites.exiger_capacite", exiges.append)
    _, compte = await semer_compte_neuf(tenants_ab.a)

    reponse = await changer_par_le_secretariat(
        client, sessions_ab.a, tenants_ab.etab_a, compte, numero_de_test()
    )

    assert reponse.status_code == 204
    assert exiges == ["habilitations.compte.gerer"]
