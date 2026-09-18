"""US1, R-08 : l'aiguilleur donne l'événement au module qui sait quoi en faire, et rien de plus.

Le code à usage unique ne part jamais sur le chemin de la réponse : la route écrit un événement,
et c'est le travailleur qui envoie. Tout ce que la règle du silence promet repose donc sur ce
consommateur, et cette suite en vérifie les quatre points qui comptent.

Il lit le texte en clair **dans l'éphémère**, par la référence de l'envoi, puis l'efface : le
grand livre ne conserve aucun secret, et un second passage n'a plus rien à envoyer. C'est ainsi
que la livraison « au moins une fois » de l'outbox ne coûte pas deux messages à la personne.

Une passerelle indisponible ne perd pas l'événement : il passe `en_echec`, et le tour suivant le
reprend. C'est le contraire d'un envoi synchrone, qui aurait rendu `503` à la route et publié, par
ce seul refus, l'existence du compte.
"""

import logging
import uuid
from uuid import UUID

import pytest
from sqlalchemy import select, update

from modules.shared import Evenement, ModeSimulation, transaction
from modules.shared import outbox as file
from modules.socle.habilitations import gabarits
from modules.socle.habilitations.politique import POLITIQUE
from modules.socle.habilitations.tables import evenement_outbox
from tests.authentification.outils import tourner, vider_envois
from tests.conftest import numero_de_test

TYPE_DEMANDE = "habilitations.otp.demande"
CODE = "428913"


async def ecrire_demande(
    valkey, tenant_id: UUID, compte_id: UUID, numero: str, langue: str = "fr"
) -> tuple[UUID, UUID]:
    """Ce que `POST /auth/otp` laisse derrière lui : un texte dans l'éphémère, un événement en base."""
    envoi_id = uuid.uuid7()
    await valkey.set(f"otp_texte:{envoi_id}", CODE, ex=int(POLITIQUE.OTP_VALIDITE.total_seconds()))
    async with transaction(tenant_id) as connexion:
        evenement_id = await file.inserer(
            connexion,
            evenement_outbox,
            tenant_id,
            Evenement(
                TYPE_DEMANDE,
                {
                    "compte_id": str(compte_id),
                    "identifiant": numero,
                    "envoi_id": str(envoi_id),
                    "langue": langue,
                },
            ),
        )
    return evenement_id, envoi_id


async def ecrire_evenement(tenant_id: UUID, type_evenement: str, charge: dict) -> UUID:
    async with transaction(tenant_id) as connexion:
        return await file.inserer(
            connexion, evenement_outbox, tenant_id, Evenement(type_evenement, charge)
        )


async def etat(tenant_id: UUID, evenement_id: UUID):
    async with transaction(tenant_id) as connexion:
        resultat = await connexion.execute(
            select(evenement_outbox).where(evenement_outbox.c.id == evenement_id)
        )
        return resultat.mappings().one()


async def remettre_en_attente(tenant_id: UUID, evenement_id: UUID) -> None:
    """Une seconde livraison du même événement, telle que l'outbox en produit au moins une fois."""
    async with transaction(tenant_id) as connexion:
        await connexion.execute(
            update(evenement_outbox)
            .where(evenement_outbox.c.id == evenement_id)
            .values(etat="en_attente", pris_le=None, traite_le=None)
        )


def envois_vers(application, numero: str) -> list:
    return [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]


# --- Le chemin nominal ----------------------------------------------------------------------------


async def test_le_code_part_par_la_passerelle_puis_son_texte_est_efface(
    application, tenants_ab, valkey
):
    """L'aiguilleur reconnaît le type, le consommateur lit, compose, envoie, efface, et marque."""
    numero = numero_de_test()
    evenement_id, envoi_id = await ecrire_demande(
        valkey, tenants_ab.tenant_a, tenants_ab.compte_a, numero
    )
    await vider_envois(application)

    await tourner(application)

    envois = envois_vers(application, numero)
    assert len(envois) == 1
    assert envois[0].texte == gabarits.rendre(
        "otp",
        "fr",
        produit=application.state.configuration.nom_produit,
        code=CODE,
        minutes=int(POLITIQUE.OTP_VALIDITE.total_seconds() // 60),
    )
    # La référence de l'envoi est celle de l'événement : la passerelle et le grand livre se relient.
    assert envois[0].reference.reference == envoi_id

    assert await valkey.get(f"otp_texte:{envoi_id}") is None
    ligne = await etat(tenants_ab.tenant_a, evenement_id)
    assert ligne["etat"] == "traite" and ligne["traite_le"] is not None


async def test_le_message_est_compose_dans_la_langue_portee_par_l_evenement(
    application, tenants_ab, valkey
):
    """La langue voyage dans la charge : le travailleur n'a aucun tenant ni aucune personne à relire."""
    numero = numero_de_test()
    await ecrire_demande(valkey, tenants_ab.tenant_b, tenants_ab.compte_b, numero, langue="en")
    await vider_envois(application)

    await tourner(application)

    envois = envois_vers(application, numero)
    assert len(envois) == 1
    assert envois[0].texte == gabarits.rendre(
        "otp",
        "en",
        produit=application.state.configuration.nom_produit,
        code=CODE,
        minutes=int(POLITIQUE.OTP_VALIDITE.total_seconds() // 60),
    )


async def test_une_seconde_livraison_du_meme_evenement_n_envoie_rien(
    application, tenants_ab, valkey
):
    """Livraison au moins une fois : le texte effacé fait du second passage un non-événement."""
    numero = numero_de_test()
    evenement_id, _ = await ecrire_demande(valkey, tenants_ab.tenant_a, tenants_ab.compte_a, numero)
    await vider_envois(application)
    await tourner(application)
    assert len(envois_vers(application, numero)) == 1

    await remettre_en_attente(tenants_ab.tenant_a, evenement_id)
    await tourner(application)

    assert len(envois_vers(application, numero)) == 1, "la personne a reçu deux fois le même code"
    assert (await etat(tenants_ab.tenant_a, evenement_id))["etat"] == "traite"


# --- La passerelle tombe ---------------------------------------------------------------------------


async def test_une_passerelle_indisponible_met_l_evenement_en_echec_et_le_tour_suivant_le_reprend(
    application, tenants_ab, valkey, monkeypatch
):
    """Rien n'est perdu, et rien n'a été dit à la route : le silence tient même en panne."""
    numero = numero_de_test()
    evenement_id, envoi_id = await ecrire_demande(
        valkey, tenants_ab.tenant_a, tenants_ab.compte_a, numero
    )
    await vider_envois(application)

    monkeypatch.setattr(
        application.state.passerelle_sms, "mode", ModeSimulation.INDISPONIBLE, raising=False
    )
    await tourner(application)

    ligne = await etat(tenants_ab.tenant_a, evenement_id)
    assert ligne["etat"] == "en_echec"
    assert ligne["tentatives"] == 1
    assert "PASSERELLE_SMS" in ligne["derniere_erreur"]
    assert envois_vers(application, numero) == []
    # Le texte est intact : il n'est effacé qu'après un envoi réussi.
    assert await valkey.get(f"otp_texte:{envoi_id}") is not None

    monkeypatch.setattr(
        application.state.passerelle_sms, "mode", ModeSimulation.SUCCES, raising=False
    )
    await tourner(application)

    assert len(envois_vers(application, numero)) == 1
    assert (await etat(tenants_ab.tenant_a, evenement_id))["etat"] == "traite"


# --- Ce qui n'est pas un envoi ----------------------------------------------------------------------


async def test_un_evenement_d_un_autre_type_va_au_journal(application, tenants_ab, valkey, caplog):
    """Les faits s'écrivent pour être lus : `session.ouverte` ne déclenche rien, et c'est voulu."""
    evenement_id = await ecrire_evenement(
        tenants_ab.tenant_a,
        "habilitations.session.ouverte",
        {"compte_id": str(tenants_ab.compte_a), "session_id": str(uuid.uuid7()), "canal": "CODE"},
    )
    await vider_envois(application)

    with caplog.at_level(logging.INFO, logger="nelo.travailleur"):
        await tourner(application)

    assert application.state.passerelle_sms.envoyes == []
    assert (await etat(tenants_ab.tenant_a, evenement_id))["etat"] == "traite"
    assert any("habilitations.session.ouverte" in message for message in caplog.messages)


async def test_un_evenement_d_envoi_sans_reference_est_ignore_sans_faire_tomber_le_tour(
    application, tenants_ab, valkey, caplog
):
    """Un événement mal formé ne bloque pas la file : il est journalisé et marqué traité."""
    evenement_id = await ecrire_evenement(
        tenants_ab.tenant_a, TYPE_DEMANDE, {"compte_id": str(tenants_ab.compte_a)}
    )
    await vider_envois(application)

    with caplog.at_level(logging.INFO, logger="nelo.habilitations"):
        await tourner(application)

    assert application.state.passerelle_sms.envoyes == []
    assert (await etat(tenants_ab.tenant_a, evenement_id))["etat"] == "traite"


@pytest.mark.parametrize("langue", ["fr", "en"])
async def test_le_message_envoye_tient_dans_un_message_court(
    application, tenants_ab, valkey, langue
):
    """ADR 013 : ce qui part réellement, et pas seulement le gabarit, tient sous 160 caractères."""
    numero = numero_de_test()
    await ecrire_demande(valkey, tenants_ab.tenant_a, tenants_ab.compte_a, numero, langue=langue)
    await vider_envois(application)

    await tourner(application)

    envois = envois_vers(application, numero)
    assert len(envois) == 1
    assert len(envois[0].texte) <= gabarits.LONGUEUR_MAXIMALE
