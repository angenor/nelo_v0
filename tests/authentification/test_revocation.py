"""US5 : suspendre coupe à la requête suivante, et la coupure ne tient pas à un magasin éphémère.

« Le départ d'un membre du personnel coupe l'accès le jour même » est un invariant du domaine, et
le jeton d'accès vaut soixante minutes : sans liste de révocation, une personne suspendue à neuf
heures travaillerait encore à dix heures moins cinq. Deux mécanismes le tiennent, et il en faut
deux : la **liste de révocation**, consultée à chaque requête, qui rend le refus immédiat ; et le
**statut du compte**, qui est en base, et qui rend la suspension durable. Retirer l'un des deux
doit faire tomber un test d'ici.

Ce que la suite regarde aussi, c'est ce qui ne tombe pas : une session dont Valkey a perdu la clé
est révoquée, sans qu'on ait besoin de savoir pourquoi la clé a disparu (US5-7).
"""

import httpx

from modules.shared import transaction
from modules.socle.habilitations import acces
from modules.socle.habilitations import appareil as appareil_module
from modules.socle.habilitations import session as session_module
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    demander,
    en_tetes,
    evenements,
    ouvrir,
    semer_compte_neuf,
    tourner,
    vider_envois,
)

CHEMIN_PROTEGE = f"{PREFIXE}/parametres"
PIN = "2468"


async def suspendre(client, session_administrative, etablissement_id, compte_id) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/comptes/{compte_id}/suspension",
        headers=en_tetes(session_administrative, etablissement_id, ecriture=True),
    )


async def definir_pin(client, session) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/auth/pin/definition",
        headers={**en_tetes(session), "X-Nelo-Requete": cle_de_requete()},
        json={"pin": PIN},
    )


async def ouvrir_par_pin(client, compte_id, pin=PIN) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/auth/pin",
        headers={"X-Nelo-Requete": cle_de_requete()},
        json={"compte_id": str(compte_id), "pin": pin},
    )


def session_id_du_jeton(application, session):
    secret = application.state.configuration.secret_jeton
    return session_module.verifier_jeton_acces(session.jeton, secret).session_id


async def statut_en_base(tenant_id, compte_id) -> str:
    async with transaction(tenant_id) as connexion:
        return await acces.lire_statut(connexion, compte_id)


# --- La requête suivante, et toutes celles d'après -----------------------------------------------


async def test_la_requete_suivante_est_refusee_bien_que_le_jeton_tienne_encore(
    client, application, sessions_ab, tenants_ab
):
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    avant = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert avant.status_code == 200, avant.text

    assert (await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)).status_code == 204

    # Le même jeton, non expiré, signé du même secret : c'est la liste de révocation qui refuse.
    apres = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert apres.status_code == 401
    assert apres.json()["code"] == "AUT_SESSION_REVOQUEE"
    assert await statut_en_base(tenants_ab.tenant_a, compte) == "suspendu"


async def test_le_rafraichissement_d_un_compte_suspendu_est_refuse(
    client, application, sessions_ab, tenants_ab
):
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    await ouvrir(client, application, numero)

    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)

    reponse = await client.post(
        f"{PREFIXE}/auth/rafraichissement", headers={"X-Nelo-Requete": cle_de_requete()}
    )
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_SESSION_REVOQUEE"


async def test_le_code_personnel_n_ouvre_plus_rien_et_l_appareil_a_oublie_le_compte(
    client, application, sessions_ab, tenants_ab
):
    """La suspension oublie d'abord les appareils (FR-027) : il ne reste plus rien à vérifier.

    Le refus est donc `AUT_APPAREIL_INCONNU` et non `AUT_COMPTE_SUSPENDU` : le compte a disparu de
    l'appareil au moment de la suspension, et l'écran d'ouverture ne proposera plus son nom.
    `AUT_COMPTE_SUSPENDU` reste le refus quand l'appareil est encore connu, ce que la perte de
    l'éphémère met en scène plus bas.
    """
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    assert (await definir_pin(client, session)).status_code == 204

    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)

    reponse = await ouvrir_par_pin(client, compte)
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_APPAREIL_INCONNU"

    connus = (await client.get(f"{PREFIXE}/auth/appareil")).json()["comptes"]
    assert str(compte) not in {c["compte_id"] for c in connus}


async def test_les_cles_de_session_du_compte_disparaissent(
    client, application, valkey, sessions_ab, tenants_ab
):
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    session_id = session_id_du_jeton(application, session)
    assert await valkey.get(session_module.cle_session(session_id)) is not None

    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)

    assert await valkey.get(session_module.cle_session(session_id)) is None
    assert not await valkey.smembers(session_module.cle_sessions_compte(compte))


async def test_la_suspension_et_la_fermeture_sont_toutes_deux_ecrites(
    client, application, sessions_ab, tenants_ab
):
    """Règle 10 : un changement d'état sans événement dans la transaction est une saisie perdue."""
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    session_id = session_id_du_jeton(application, session)

    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)

    suspensions = await evenements(tenants_ab.tenant_a, "habilitations.compte.suspendu")
    mienne = [e for e in suspensions if e["charge"]["compte_id"] == str(compte)]
    assert len(mienne) == 1
    assert mienne[0]["charge"]["suspendu_par"] == str(tenants_ab.compte_a)

    fermetures = await evenements(tenants_ab.tenant_a, "habilitations.session.fermee")
    miennes = [e for e in fermetures if e["charge"]["session_id"] == str(session_id)]
    assert [e["charge"]["motif"] for e in miennes] == ["SUSPENSION"]


async def test_la_route_de_suspension_traverse_le_point_d_insertion_de_capacite(
    client, application, sessions_ab, tenants_ab, monkeypatch
):
    """T1b remplira le point d'insertion ; ce qui doit être vrai dès T1a, c'est qu'il est traversé."""
    exiges: list[str] = []
    monkeypatch.setattr("api.capacites.exiger_capacite", exiges.append)
    _, compte = await semer_compte_neuf(tenants_ab.a)

    assert (await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)).status_code == 204

    assert exiges == ["habilitations.compte.suspendre"]


# --- Ce qui est durable, et ce qui ne l'est pas ---------------------------------------------------


async def test_la_suspension_survit_a_la_perte_de_l_ephemere(
    client, application, valkey, sessions_ab, tenants_ab
):
    """La liste de révocation est jetable ; le statut du compte, non (FR-028, US5-7).

    On efface tout l'éphémère, puis on refait connaître l'appareil du compte : c'est la seule
    chose que la perte de Valkey coûte. Le refus, lui, doit rester, parce qu'il vient de la base.
    """
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    assert (await definir_pin(client, session)).status_code == 204
    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)

    await valkey.flushdb()
    secret = await appareil_module.connaitre(compte, tenants_ab.tenant_a, valkey=valkey, jours=90)

    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as neuf:
        reponse = await neuf.post(
            f"{PREFIXE}/auth/pin",
            headers={"X-Nelo-Requete": cle_de_requete(), "Cookie": f"nelo_appareils={secret}"},
            json={"compte_id": str(compte), "pin": PIN},
        )

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_COMPTE_SUSPENDU"


async def test_un_compte_suspendu_ne_recoit_plus_aucun_code(
    client, application, valkey, sessions_ab, tenants_ab
):
    """Et la demande répond `204` comme pour tout numéro : rien à l'écran ne l'annonce (FR-064)."""
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    await suspendre(client, sessions_ab.a, tenants_ab.etab_a, compte)
    await vider_envois(application)
    await valkey.delete(f"otp_renvoi:{numero}")

    reponse = await demander(client, numero)
    await tourner(application, tenants_ab.tenant_a)

    assert reponse.status_code == 204
    assert application.state.passerelle_sms.envoyes == []


async def test_une_session_dont_la_cle_a_disparu_est_revoquee(
    client, application, valkey, tenants_ab
):
    """Le compte est resté `actif` : c'est bien l'absence de la clé qui refuse, et rien d'autre."""
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)

    await valkey.flushdb()

    reponse = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_SESSION_REVOQUEE"
    assert await statut_en_base(tenants_ab.tenant_a, compte) == "actif"
