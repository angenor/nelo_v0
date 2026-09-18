"""FR-003 à FR-009 : demander un code ne dit jamais si le numéro est connu.

C'est la règle de la tranche, et elle se prouve des deux côtés : la réponse est la même pour un
numéro que personne ne porte, **et** le message ne part que si un compte actif ou invité le porte.
Un produit qui refuserait poliment un numéro inconnu offrirait au premier venu la liste des
familles inscrites dans l'école ; un produit qui enverrait le code sur le chemin de la réponse
dirait la même chose par son `503` quand la passerelle tombe.

La suite vérifie aussi les trois limites de débit, qui protègent la facture de messages autant que
les comptes, et l'écriture de l'événement : le code part par l'outbox, et l'outbox est un grand
livre où un secret en clair n'entre pas.
"""

import json

import pytest

from modules.socle.habilitations import gabarits
from modules.socle.habilitations.politique import POLITIQUE
from tests.authentification.outils import (
    cle_de_requete,
    code_recu,
    demander,
    evenements,
    semer_compte_neuf,
    tourner,
    vider_envois,
)
from tests.conftest import numero_de_test


def envois_vers(application, numero: str) -> list:
    return [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]


def sans_date(reponse) -> dict[str, str]:
    """Les en-têtes qui font la réponse, l'horloge exceptée : elle change à chaque seconde."""
    return {nom: valeur for nom, valeur in reponse.headers.items() if nom.lower() != "date"}


def message_attendu(application, langue: str, code: str) -> str:
    """Le texte que la passerelle doit avoir reçu : le gabarit de la tranche, et rien d'autre."""
    return gabarits.rendre(
        "otp",
        langue,
        produit=application.state.configuration.nom_produit,
        code=code,
        minutes=int(POLITIQUE.OTP_VALIDITE.total_seconds() // 60),
    )


async def oublier_le_delai_de_renvoi(valkey, numero: str) -> None:
    """Le délai de soixante secondes, levé à la main : la suite étudie ici la limite horaire."""
    await valkey.delete(f"otp_renvoi:{numero}")


# --- La réponse ne distingue personne ------------------------------------------------------------


async def test_un_numero_connu_et_un_inconnu_recoivent_la_meme_reponse(client, tenants_ab, valkey):
    """FR-004 : même statut, même corps, mêmes en-têtes ; rien n'apprend qui balaie des numéros."""
    connu = await demander(client, tenants_ab.numero_a)
    inconnu = await demander(client, numero_de_test())

    assert connu.status_code == inconnu.status_code == 204
    assert connu.content == inconnu.content == b""
    assert sans_date(connu) == sans_date(inconnu)


async def test_seul_le_numero_connu_recoit_un_message(client, application, tenants_ab, valkey):
    """La réponse est la même des deux côtés ; ce qui diffère est le message, reçu par son porteur."""
    inconnu = numero_de_test()
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    await vider_envois(application)

    assert (await demander(client, numero)).status_code == 204
    assert (await demander(client, inconnu)).status_code == 204
    await tourner(application)

    assert len(envois_vers(application, numero)) == 1
    assert envois_vers(application, inconnu) == []
    assert code_recu(application, numero).isdigit()


async def test_un_compte_suspendu_ne_recoit_rien_et_ne_le_dit_pas(
    client, application, tenants_ab, valkey
):
    """FR-005 : la suspension est immédiate, silencieuse, et ne se déduit pas de la réponse."""
    numero, _ = await semer_compte_neuf(tenants_ab.a, statut="suspendu")
    await vider_envois(application)

    reponse = await demander(client, numero)
    await tourner(application)

    assert reponse.status_code == 204 and reponse.content == b""
    assert envois_vers(application, numero) == []
    assert await evenements(tenants_ab.tenant_a, "habilitations.otp.demande") == []


async def test_un_compte_invite_recoit_son_code(client, application, tenants_ab, valkey):
    """FR-005 : un compte invité n'a pas encore ouvert son lien, et reçoit pourtant son code."""
    numero, _ = await semer_compte_neuf(tenants_ab.a, statut="invite")
    await vider_envois(application)

    assert (await demander(client, numero)).status_code == 204
    await tourner(application)

    assert len(envois_vers(application, numero)) == 1


# --- Le numéro mal formé -------------------------------------------------------------------------


@pytest.mark.parametrize("brut", ["0708", "+999"])
async def test_un_numero_mal_forme_est_refuse_sans_rien_dire_des_comptes(client, valkey, brut):
    """FR-003 : le refus porte sur la forme du numéro, jamais sur ce que la base contient."""
    reponse = await demander(client, brut)

    assert reponse.status_code == 422
    charge = reponse.json()
    assert charge["code"] == "AUT_NUMERO_INVALIDE"
    assert charge["champ"] == "identifiant"
    assert charge["details"] == {}


# --- Les trois limites de débit -------------------------------------------------------------------


async def test_un_second_envoi_dans_la_minute_est_refuse_avec_son_delai(client, tenants_ab, valkey):
    """FR-007 : le délai avant renvoi protège la facture de messages autant que la personne."""
    assert (await demander(client, tenants_ab.numero_a)).status_code == 204
    reponse = await demander(client, tenants_ab.numero_a)

    assert reponse.status_code == 429
    assert reponse.json()["code"] == "API_LIMITE_DEBIT"
    reprise = int(reponse.headers["Retry-After"])
    assert 0 < reprise <= int(POLITIQUE.OTP_RENVOI.total_seconds())


async def test_la_sixieme_demande_de_l_heure_pour_un_numero_est_refusee(client, tenants_ab, valkey):
    """FR-007 : cinq codes par heure et par numéro ; le sixième attend, et rien n'est suspendu."""
    for _ in range(POLITIQUE.OTP_PAR_HEURE_PAR_NUMERO):
        await oublier_le_delai_de_renvoi(valkey, tenants_ab.numero_a)
        assert (await demander(client, tenants_ab.numero_a)).status_code == 204

    await oublier_le_delai_de_renvoi(valkey, tenants_ab.numero_a)
    reponse = await demander(client, tenants_ab.numero_a)

    assert reponse.status_code == 429
    # La reprise dépasse la minute du renvoi : c'est bien la fenêtre horaire qui refuse.
    assert int(reponse.headers["Retry-After"]) > int(POLITIQUE.OTP_RENVOI.total_seconds())


async def test_la_vingt_et_unieme_demande_d_un_meme_client_est_refusee(client, valkey):
    """FR-007 : la limite par client, appliquée **avant** toute lecture, arrête le balayage.

    Vingt numéros différents ne réveillent aucune des deux autres limites : seule celle du client
    peut refuser le vingt-et-unième, et c'est donc bien elle que ce test mesure.
    """
    for _ in range(POLITIQUE.OTP_PAR_HEURE_PAR_CLIENT):
        reponse = await demander(client, numero_de_test())
        assert reponse.status_code == 204, reponse.text

    reponse = await demander(client, numero_de_test())

    assert reponse.status_code == 429
    assert reponse.json()["details"]["reprise_dans"] > 0
    assert "Retry-After" in reponse.headers


# --- L'idempotence et l'événement ------------------------------------------------------------------


async def test_le_rejeu_de_la_meme_cle_n_envoie_pas_un_second_message(
    client, application, tenants_ab, valkey
):
    """FR-008 : un réseau qui réémet la requête ne coûte ni un second message, ni un refus."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    await vider_envois(application)
    requete_id = cle_de_requete()

    premiere = await demander(client, numero, requete_id)
    rejeu = await demander(client, numero, requete_id)
    await tourner(application)

    assert premiere.status_code == rejeu.status_code == 204
    assert rejeu.content == b""
    assert len(envois_vers(application, numero)) == 1
    assert len(await evenements(tenants_ab.tenant_a, "habilitations.otp.demande")) == 1


async def test_l_evenement_ecrit_porte_l_envoi_et_jamais_le_code(client, tenants_ab, valkey):
    """FR-005 et principe X : l'outbox est un grand livre, un code en clair n'y entre pas.

    L'événement ne porte que la référence de l'envoi ; le texte vit dix minutes dans l'éphémère,
    et le consommateur l'y lit puis l'efface.
    """
    numero, compte_id = await semer_compte_neuf(tenants_ab.a)

    assert (await demander(client, numero)).status_code == 204

    ecrits = await evenements(tenants_ab.tenant_a, "habilitations.otp.demande")
    assert len(ecrits) == 1
    charge = ecrits[0]["charge"]
    assert set(charge) == {"compte_id", "identifiant", "envoi_id", "langue"}
    assert charge["identifiant"] == numero
    assert charge["compte_id"] == str(compte_id)
    assert charge["langue"] == "fr"

    code = await valkey.get(f"otp_texte:{charge['envoi_id']}")
    assert code is not None, "le texte de l'envoi vit dans l'éphémère, pas dans l'événement"
    assert code.decode() not in json.dumps(charge)


async def test_un_numero_inconnu_n_ecrit_ni_evenement_ni_code(client, tenants_ab, valkey):
    """Le silence va jusqu'au bout : rien en base, rien dans l'éphémère, rien à consommer."""
    inconnu = numero_de_test()

    assert (await demander(client, inconnu)).status_code == 204

    assert await evenements(tenants_ab.tenant_a, "habilitations.otp.demande") == []
    assert await evenements(tenants_ab.tenant_b, "habilitations.otp.demande") == []
    assert await valkey.get(f"otp:{inconnu}") is None


async def test_l_evenement_part_dans_le_tenant_du_compte_et_nulle_part_ailleurs(
    client, tenants_ab, valkey
):
    """Un tenant n'apprend jamais qu'un numéro rattaché à un autre tenant a demandé un code."""
    numero, _ = await semer_compte_neuf(tenants_ab.b, langue="en")

    assert (await demander(client, numero)).status_code == 204

    assert len(await evenements(tenants_ab.tenant_b, "habilitations.otp.demande")) == 1
    assert await evenements(tenants_ab.tenant_a, "habilitations.otp.demande") == []


async def test_le_message_est_rendu_dans_la_langue_de_la_personne(
    client, application, tenants_ab, valkey
):
    """FR-009 : la langue est celle du compte, jamais celle du serveur ; le tenant B écrit en anglais."""
    numero, _ = await semer_compte_neuf(tenants_ab.b, langue="en")
    await vider_envois(application)

    assert (await demander(client, numero)).status_code == 204
    await tourner(application)

    envois = envois_vers(application, numero)
    assert len(envois) == 1
    assert envois[0].texte == message_attendu(application, "en", code_recu(application, numero))
    assert len(envois[0].texte) <= gabarits.LONGUEUR_MAXIMALE
