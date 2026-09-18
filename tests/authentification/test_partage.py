"""US8 : deux parents, un téléphone, et chacun son compte, parce que chacun a son lien avec l'élève.

Le partage d'un numéro n'est ni interdit ni tacite : il se **déclare**, et la déclaration est un
événement qui porte son auteur. Sans elle, un second compte sur un même numéro est presque toujours
une erreur de saisie, et le refus le dit avec son versant positif.

Une fois déclaré, tout le reste en découle : un seul code part vers le téléphone, l'écran demande
**qui** ouvre la session, et l'ouverture porte la trace du choix, sans quoi le journal d'accès ne
voudrait plus rien dire. Le même mécanisme sert la vacataire qui travaille dans deux groupes
scolaires : une session appartient toujours à un seul compte d'un seul tenant.

Ce que T1a garantit à T1b, enfin, tient en une fonction : « ce numéro est partagé » est **lisible**
par l'interface de service, pour qu'aucun rattachement de personnel ne se pose dessus (FR-040).
"""

from datetime import date

import httpx

from modules.socle import habilitations, personnes
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    code_recu,
    demander,
    en_tetes,
    evenements,
    semer_compte_neuf,
    tourner,
    verifier,
    vider_envois,
)


async def creer(
    client, session, etablissement_id, personne_id, identifiant, *, partage=False
) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/comptes",
        headers=en_tetes(session, etablissement_id, ecriture=True),
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


async def personne_neuve(tenant, nom: str):
    return await personnes.creer_personne(tenant.tenant, nom, "Ama", "fr", None)


async def premier_parent(tenant):
    """Un compte actif sur un numéro neuf, rattaché : le point de départ de chaque cas."""
    return await semer_compte_neuf(tenant)


async def second_parent(client, session, tenant, numero: str, nom: str = "Traoré"):
    """Le second compte sur le même numéro, déclaré et rattaché à l'école du premier."""
    personne_id = await personne_neuve(tenant, nom)
    reponse = await creer(client, session, tenant.etablissement, personne_id, numero, partage=True)
    assert reponse.status_code == 201, reponse.text
    compte_id = reponse.json()["id"]
    await habilitations.creer_affectation(
        tenant.tenant, compte_id, tenant.annee, tenant.etablissement, date.today(), None
    )
    return compte_id


async def compte_jumeau_dans_l_autre_tenant(tenant, numero: str, nom: str = "Vacataire"):
    """Le même numéro dans un second tenant : aucune route ne le fait, c'est la vie qui le fait."""
    personne_id = await personnes.creer_personne(tenant.tenant, nom, "Ama", "en", numero)
    compte_id = await habilitations.semer_compte(tenant.tenant, personne_id, numero)
    await habilitations.creer_affectation(
        tenant.tenant, compte_id, tenant.annee, tenant.etablissement, date.today(), None
    )
    return compte_id


# --- La déclaration ------------------------------------------------------------------------------


async def test_un_second_compte_sur_le_meme_numero_sans_declaration_est_refuse(
    client, application, sessions_ab, tenants_ab
):
    numero, _ = await premier_parent(tenants_ab.a)
    personne_id = await personne_neuve(tenants_ab.a, "Konaté")

    reponse = await creer(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)

    assert reponse.status_code == 422
    assert reponse.json()["code"] == "AUT_IDENTIFIANT_DEJA_UTILISE"
    assert reponse.json()["details"]["partage_familial_requis"] is True


async def test_la_declaration_ouvre_le_second_compte_et_laisse_sa_trace(
    client, application, sessions_ab, tenants_ab
):
    """Sans trace de qui a déclaré le partage, le journal d'accès ne voudrait plus rien dire."""
    numero, _ = await premier_parent(tenants_ab.a)
    personne_id = await personne_neuve(tenants_ab.a, "Konaté")

    reponse = await creer(
        client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero, partage=True
    )

    assert reponse.status_code == 201, reponse.text
    naissances = [
        e["charge"]
        for e in await evenements(tenants_ab.tenant_a, "habilitations.compte.cree")
        if e["charge"]["compte_id"] == reponse.json()["id"]
    ]
    assert len(naissances) == 1
    assert naissances[0]["partage_familial"] is True
    assert naissances[0]["cree_par"] == str(tenants_ab.compte_a)


async def test_la_verification_annonce_le_partage_a_declarer(
    client, application, sessions_ab, tenants_ab
):
    """E-04 : le secrétariat l'apprend pendant la saisie, pas après avoir appuyé."""
    numero, _ = await premier_parent(tenants_ab.a)
    personne_id = await personne_neuve(tenants_ab.a, "Konaté")

    reponse = await verifier_creation(client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero)

    charge = reponse.json()
    assert [b["code"] for b in charge["bloquages"]] == ["AUT_IDENTIFIANT_DEJA_UTILISE"]
    assert charge["bloquages"][0]["details"]["partage_familial_requis"] is True
    assert "compte.creation.declarer_partage" in charge["issues"]

    # Déclaré, plus rien ne s'y oppose, et toujours sans rien écrire.
    declare = await verifier_creation(
        client, sessions_ab.a, tenants_ab.etab_a, personne_id, numero, partage=True
    )
    assert declare.json() == {"bloquages": [], "issues": []}


async def test_le_partage_d_un_identifiant_est_lisible_par_le_module(
    client, application, sessions_ab, tenants_ab
):
    """FR-040 : c'est tout ce que T1a doit à T1b, et c'est une lecture, pas une colonne."""
    numero, premier = await premier_parent(tenants_ab.a)
    second = await second_parent(client, sessions_ab.a, tenants_ab.a, numero)

    assert await habilitations.identifiant_partage(tenants_ab.tenant_a, premier) is True
    assert await habilitations.identifiant_partage(tenants_ab.tenant_a, second) is True
    assert (
        await habilitations.identifiant_partage(tenants_ab.tenant_a, tenants_ab.compte_a) is False
    )


# --- Un seul code, et la question « qui ouvre la session ? » --------------------------------------


async def test_un_seul_message_part_pour_les_deux_comptes(
    client, application, sessions_ab, tenants_ab
):
    numero, _ = await premier_parent(tenants_ab.a)
    await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    # L'invitation du second parent part d'abord : elle ne doit pas se compter avec le code.
    await tourner(application, tenants_ab.tenant_a)
    await vider_envois(application)

    assert (await demander(client, numero)).status_code == 204
    await tourner(application, tenants_ab.tenant_a)

    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert len(envois) == 1


async def test_la_verification_demande_qui_ouvre_la_session_sans_montrer_un_numero(
    client, application, sessions_ab, tenants_ab
):
    numero, premier = await premier_parent(tenants_ab.a)
    second = await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    await demander(client, numero)
    await tourner(application, tenants_ab.tenant_a)

    reponse = await verifier(client, numero, code_recu(application, numero))

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "CHOIX"
    assert {c["compte_id"] for c in charge["comptes"]} == {str(premier), second}
    assert all(c["nom"] for c in charge["comptes"])
    assert all(c["etablissement_nom"] == "École A" for c in charge["comptes"])
    assert numero not in reponse.text


async def test_le_choix_ouvre_la_session_du_compte_choisi_et_en_garde_la_trace(
    client, application, sessions_ab, tenants_ab
):
    numero, _ = await premier_parent(tenants_ab.a)
    second = await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    await demander(client, numero)
    await tourner(application, tenants_ab.tenant_a)
    code = code_recu(application, numero)
    assert (await verifier(client, numero, code)).json()["resultat"] == "CHOIX"

    reponse = await verifier(client, numero, code, second)

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "SESSION"
    assert charge["compte"]["id"] == second

    ouvertures = [
        e["charge"]
        for e in await evenements(tenants_ab.tenant_a, "habilitations.session.ouverte")
        if e["charge"]["compte_id"] == second
    ]
    assert [o["choix_parmi"] for o in ouvertures] == [2]


async def test_le_code_ne_vaut_que_jusqu_au_choix_et_une_seule_fois(
    client, application, sessions_ab, tenants_ab
):
    """Le choix ne consomme le code qu'au moment où une session s'ouvre vraiment."""
    numero, premier = await premier_parent(tenants_ab.a)
    await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    await demander(client, numero)
    await tourner(application, tenants_ab.tenant_a)
    code = code_recu(application, numero)

    assert (await verifier(client, numero, code)).json()["resultat"] == "CHOIX"
    assert (await verifier(client, numero, code, premier)).status_code == 200

    rejeu = await verifier(client, numero, code, premier)
    assert rejeu.status_code == 401
    assert rejeu.json()["code"] == "AUT_OTP_EXPIRE"


async def test_un_compte_hors_de_la_liste_proposee_est_une_tentative(
    client, application, sessions_ab, tenants_ab
):
    """Ce n'est pas une faute de frappe : quelqu'un a nommé un compte que le code ne couvre pas."""
    numero, _ = await premier_parent(tenants_ab.a)
    await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    await demander(client, numero)
    await tourner(application, tenants_ab.tenant_a)

    reponse = await verifier(client, numero, code_recu(application, numero), tenants_ab.compte_a)

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_OTP_INVALIDE"


# --- Le même numéro dans deux tenants -------------------------------------------------------------


async def test_le_meme_numero_dans_deux_tenants_propose_les_deux_ecoles(
    client, application, sessions_ab, tenants_ab
):
    """Une session appartient à **un seul** compte d'un seul tenant : c'est l'écran qui tranche."""
    numero, premier = await premier_parent(tenants_ab.a)
    ailleurs = await compte_jumeau_dans_l_autre_tenant(tenants_ab.b, numero)
    await vider_envois(application)

    assert (await demander(client, numero)).status_code == 204
    # L'événement est écrit dans le tenant du premier compte trouvé : le tour regarde les deux.
    await tourner(application, tenants_ab.tenant_a, tenants_ab.tenant_b)
    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert len(envois) == 1

    code = code_recu(application, numero)
    choix = await verifier(client, numero, code)
    assert choix.json()["resultat"] == "CHOIX"
    assert {c["etablissement_nom"] for c in choix.json()["comptes"]} == {"École A", "École B"}

    reponse = await verifier(client, numero, code, ailleurs)

    assert reponse.status_code == 200, reponse.text
    assert reponse.json()["compte"]["id"] == str(ailleurs)
    # Rien n'a été ouvert pour l'autre tenant : un code, un choix, une session.
    ouvertures = await evenements(tenants_ab.tenant_a, "habilitations.session.ouverte")
    assert str(premier) not in {e["charge"]["compte_id"] for e in ouvertures}


async def test_une_demande_sur_un_numero_partage_ne_porte_qu_une_cle_de_requete(
    client, application, sessions_ab, tenants_ab
):
    """Le rejeu de la même clé n'ajoute pas un second message, partage ou non."""
    numero, _ = await premier_parent(tenants_ab.a)
    await second_parent(client, sessions_ab.a, tenants_ab.a, numero)
    # L'invitation du second parent part d'abord : elle ne doit pas se compter avec le code.
    await tourner(application, tenants_ab.tenant_a)
    await vider_envois(application)
    cle = cle_de_requete()

    assert (await demander(client, numero, cle)).status_code == 204
    assert (await demander(client, numero, cle)).status_code == 204
    await tourner(application, tenants_ab.tenant_a)

    envois = [e for e in application.state.passerelle_sms.envoyes if e.destinataire_e164 == numero]
    assert len(envois) == 1
