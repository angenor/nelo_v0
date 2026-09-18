"""FR-006, FR-010, FR-011, FR-014 et FR-033 : échanger un code contre une session, ou se voir refuser.

Ce que cette suite prouve tient en deux moitiés. La première : un code juste ouvre **une** session,
avec un jeton que le serveur sait relire, et deux cookies que le script de la page ne lit jamais.
La seconde : les quatre refus possibles disent tous la même chose du numéro, c'est-à-dire rien, et
comptent les essais jusqu'à détruire le code.

Cela compte parce que c'est ici que la preuve devient un droit. Un code qui survivrait à cinq
essais faux serait forçable en une nuit ; un jeton rangé dans un cookie lisible par script serait
volé par la première extension venue ; une session qui ne laisserait aucune clé dans l'éphémère ne
pourrait plus être révoquée, et la suspension d'un compte ne vaudrait plus rien.
"""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import Response
from sqlalchemy import select
from starlette.requests import Request

from api.routes.authentification import COOKIE_APPAREILS, COOKIE_REFRESH, poser_secrets
from modules.shared import transaction
from modules.socle.habilitations import SecretsDeSession
from modules.socle.habilitations.politique import POLITIQUE
from modules.socle.habilitations.session import cle_session, cle_sessions_compte
from modules.socle.habilitations.tables import compte as table_compte
from tests.authentification.outils import (
    code_recu,
    demander,
    evenements,
    semer_compte_neuf,
    tourner,
    verifier,
    vider_envois,
)

CHEMIN_DES_COOKIES = "/api/v1/auth"


async def code_pour(client, application, numero: str) -> str:
    """Le parcours d'avant : demander, laisser partir le message, y lire les six chiffres."""
    await vider_envois(application)
    reponse = await demander(client, numero)
    assert reponse.status_code == 204, reponse.text
    await tourner(application)
    return code_recu(application, numero)


def attributs_du_cookie(reponse, nom: str) -> dict[str, str]:
    """Les attributs du `Set-Cookie` de ce nom, en minuscules ; un drapeau vaut la chaîne vide."""
    for brut in reponse.headers.get_list("set-cookie"):
        if not brut.startswith(f"{nom}="):
            continue
        morceaux = [morceau.strip() for morceau in brut.split(";")[1:]]
        return {
            (m.split("=", 1)[0].lower()): (m.split("=", 1)[1] if "=" in m else "") for m in morceaux
        }
    raise AssertionError(f"aucun cookie « {nom} » dans la réponse")


async def lire_le_compte(tenant_id, compte_id):
    async with transaction(tenant_id) as connexion:
        resultat = await connexion.execute(
            select(table_compte).where(table_compte.c.id == compte_id)
        )
        return resultat.mappings().one()


# --- Le code juste ouvre une session --------------------------------------------------------------


async def test_le_bon_code_ouvre_une_session_et_rend_un_jeton_que_le_serveur_relit(
    client, application, tenants_ab, valkey
):
    """FR-011 : le jeton est signé HS256 et ne porte que l'identité de la session, rien de plus."""
    numero, compte_id = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)

    reponse = await verifier(client, numero, code)

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "SESSION"
    assert charge["expire_dans"] == int(POLITIQUE.JETON_ACCES.total_seconds()) == 3600
    assert charge["compte"]["id"] == str(compte_id)
    assert charge["compte"]["pin_defini"] is False
    assert charge["appareil_connu"] is True

    secret = application.state.configuration.secret_jeton
    jeton = jwt.decode(charge["jeton_acces"], secret, algorithms=["HS256"])
    assert set(jeton) == {"sub", "ten", "sid", "iat", "exp", "jti"}
    assert jeton["sub"] == str(compte_id)
    assert jeton["ten"] == str(tenants_ab.tenant_a)
    assert jeton["exp"] - jeton["iat"] == int(POLITIQUE.JETON_ACCES.total_seconds())


async def test_le_corps_de_la_reponse_ne_porte_aucun_secret_durable(
    client, application, tenants_ab, valkey
):
    """Le rafraîchissement et le secret d'appareil partent en cookies, jamais dans le corps lisible."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)

    reponse = await verifier(client, numero, code)

    corps = reponse.text
    for cookie in (COOKIE_REFRESH, COOKIE_APPAREILS):
        valeur = reponse.cookies[cookie]
        assert valeur, f"le cookie {cookie} est vide"
        assert valeur not in corps, f"le secret du cookie {cookie} est aussi dans le corps"
    assert "pin_empreinte" not in corps and "refresh" not in corps


async def test_les_deux_cookies_de_session_restent_hors_de_portee_du_script(
    client, application, tenants_ab, valkey
):
    """FR-011 et FR-012 : non lisibles par script, sans voyage entre sites, et bornés à leur chemin."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)

    reponse = await verifier(client, numero, code)

    for nom in (COOKIE_REFRESH, COOKIE_APPAREILS):
        attributs = attributs_du_cookie(reponse, nom)
        assert "httponly" in attributs, nom
        assert attributs["samesite"].lower() == "strict", nom
        assert attributs["path"] == CHEMIN_DES_COOKIES, nom
        # `Secure` est levé en développement local par la configuration, jamais en production.
        assert ("secure" in attributs) is application.state.configuration.cookies_secure, nom

    # Le cookie d'appareil expire avec la connaissance de l'appareil ; celui du rafraîchissement
    # tombe avec l'onglet, sa durée réelle étant celle de la clé dans l'éphémère.
    assert int(attributs_du_cookie(reponse, COOKIE_APPAREILS)["max-age"]) > 0


def test_le_drapeau_secure_suit_le_reglage_du_deploiement():
    """En production, `NELO_COOKIES_SECURE` vaut vrai et les deux cookies ne partent qu'en TLS."""
    reponse = Response()
    requete = Request({"type": "http", "method": "POST", "path": "/", "headers": []})
    secrets_de_session = SecretsDeSession(
        refresh="rafraichissement", secret_appareil="appareil", duree_appareil=timedelta(days=90)
    )

    poser_secrets(reponse, requete, secrets_de_session, secure=True)

    poses = reponse.headers.getlist("set-cookie")
    assert len(poses) == 2
    for brut in poses:
        assert "Secure" in brut
        assert "HttpOnly" in brut
        assert "SameSite=strict" in brut.replace("SameSite=Strict", "SameSite=strict")


async def test_l_ouverture_ecrit_les_clefs_qui_permettront_de_revoquer(
    client, application, tenants_ab, valkey
):
    """FR-016 : la session vit dans l'éphémère ; sans ces deux clés, plus rien ne se révoque."""
    numero, compte_id = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)

    reponse = await verifier(client, numero, code)

    secret = application.state.configuration.secret_jeton
    session_id = jwt.decode(reponse.json()["jeton_acces"], secret, algorithms=["HS256"])["sid"]
    assert await valkey.exists(cle_session(session_id)) == 1
    membres = {m.decode() for m in await valkey.smembers(cle_sessions_compte(compte_id))}
    assert membres == {session_id}


async def test_l_ouverture_pose_la_derniere_connexion(client, application, tenants_ab, valkey):
    """FR-059 : le compte garde la trace de sa dernière entrée, et elle est datée d'aujourd'hui."""
    numero, compte_id = await semer_compte_neuf(tenants_ab.a)
    avant = await lire_le_compte(tenants_ab.tenant_a, compte_id)
    assert avant["derniere_connexion"] is None

    code = await code_pour(client, application, numero)
    assert (await verifier(client, numero, code)).status_code == 200

    apres = await lire_le_compte(tenants_ab.tenant_a, compte_id)
    assert apres["derniere_connexion"] is not None
    assert datetime.now(UTC) - apres["derniere_connexion"] < timedelta(minutes=5)


async def test_un_code_deja_echange_ne_rouvre_pas_de_session(
    client, application, tenants_ab, valkey
):
    """Un code est à usage unique : le second échange trouve une clé effacée, donc un code expiré."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)
    assert (await verifier(client, numero, code)).status_code == 200

    rejoue = await verifier(client, numero, code)

    assert rejoue.status_code == 401
    assert rejoue.json()["code"] == "AUT_OTP_EXPIRE"
    assert await valkey.get(f"otp:{numero}") is None


# --- Un compte invité devient actif en prouvant qu'il reçoit ses messages ---------------------------


async def test_un_compte_invite_devient_actif_en_verifiant_son_code(
    client, application, tenants_ab, valkey
):
    """FR-033 : recevoir le code prouve autant que le lien ; l'invitation n'a plus lieu d'être."""
    numero, compte_id = await semer_compte_neuf(tenants_ab.a, statut="invite")
    code = await code_pour(client, application, numero)

    reponse = await verifier(client, numero, code)

    assert reponse.status_code == 200, reponse.text
    assert (await lire_le_compte(tenants_ab.tenant_a, compte_id))["statut"] == "actif"

    actives = await evenements(tenants_ab.tenant_a, "habilitations.compte.active")
    assert len(actives) == 1
    assert actives[0]["charge"] == {"compte_id": str(compte_id), "canal": "CODE"}


async def test_un_compte_deja_actif_n_ecrit_aucune_activation(
    client, application, tenants_ab, valkey
):
    """Un événement d'activation par ouverture de session serait un grand livre qui bavarde."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)

    assert (await verifier(client, numero, code)).status_code == 200

    assert await evenements(tenants_ab.tenant_a, "habilitations.compte.active") == []
    assert len(await evenements(tenants_ab.tenant_a, "habilitations.session.ouverte")) == 1


# --- Les refus ---------------------------------------------------------------------------------------


async def test_un_code_faux_dit_combien_d_essais_restent(client, application, tenants_ab, valkey):
    """FR-010 : la personne sait où elle en est, ce qui lui évite de redemander un code pour rien."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    await code_pour(client, application, numero)

    restantes = []
    for _ in range(POLITIQUE.OTP_TENTATIVES - 1):
        reponse = await verifier(client, numero, "000000")
        assert reponse.status_code == 401
        charge = reponse.json()
        assert charge["code"] == "AUT_OTP_INVALIDE"
        restantes.append(charge["details"]["tentatives_restantes"])

    assert restantes == list(range(POLITIQUE.OTP_TENTATIVES - 1, 0, -1))


async def test_le_cinquieme_refus_detruit_le_code(client, application, tenants_ab, valkey):
    """FR-006 : au-delà, forcer six chiffres ne coûterait qu'une nuit ; le code cesse d'exister."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    juste = await code_pour(client, application, numero)

    for _ in range(POLITIQUE.OTP_TENTATIVES - 1):
        assert (await verifier(client, numero, "000000")).status_code == 401
    dernier = await verifier(client, numero, "000000")

    assert dernier.status_code == 401
    assert dernier.json()["code"] == "AUT_OTP_TENTATIVES_EPUISEES"
    assert await valkey.get(f"otp:{numero}") is None
    # Le bon code lui-même ne vaut plus rien : ce qui est détruit l'est pour tout le monde.
    tardif = await verifier(client, numero, juste)
    assert tardif.json()["code"] == "AUT_OTP_EXPIRE"


async def test_un_code_expire_est_refuse(client, application, tenants_ab, valkey):
    """FR-006 : dix minutes, et la durée est portée par la clé elle-même, pas par une colonne."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    code = await code_pour(client, application, numero)
    cle = f"otp:{numero}"
    assert 0 < int(await valkey.ttl(cle)) <= int(POLITIQUE.OTP_VALIDITE.total_seconds())

    # L'échéance est rapprochée à la main, plutôt que d'attendre dix minutes.
    await valkey.pexpire(cle, 10)
    await _laisser_expirer(valkey, cle)

    reponse = await verifier(client, numero, code)
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_OTP_EXPIRE"


async def _laisser_expirer(valkey, cle: str) -> None:
    import asyncio

    for _ in range(50):
        if await valkey.exists(cle) == 0:
            return
        await asyncio.sleep(0.02)
    raise AssertionError(f"la clé {cle} n'a jamais expiré")


async def test_un_second_code_remplace_le_premier(client, application, tenants_ab, valkey):
    """FR-006 : demander un code de plus invalide le précédent ; deux codes vivants seraient deux portes."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    premier = await code_pour(client, application, numero)
    await valkey.delete(f"otp_renvoi:{numero}")
    second = await code_pour(client, application, numero)
    assert premier != second, "deux tirages identiques : rejouer la suite"

    refus = await verifier(client, numero, premier)
    assert refus.status_code == 401
    assert refus.json()["code"] == "AUT_OTP_INVALIDE"

    assert (await verifier(client, numero, second)).status_code == 200


async def test_un_code_jamais_demande_est_refuse_comme_un_code_expire(client, tenants_ab, valkey):
    """Le refus est le même : savoir qu'aucun code n'a été demandé pour ce numéro n'apprend rien."""
    reponse = await verifier(client, tenants_ab.numero_a, "123456")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_OTP_EXPIRE"


@pytest.mark.parametrize("mauvais", ["12345", "1234567", "abcdef", ""])
async def test_un_code_qui_n_a_pas_six_chiffres_est_refuse_par_le_schema(
    client, tenants_ab, valkey, mauvais
):
    """Le schéma refuse avant toute lecture de l'éphémère : une saisie n'use pas une tentative."""
    reponse = await verifier(client, tenants_ab.numero_a, mauvais)

    assert reponse.status_code == 422
    assert reponse.json()["code"] == "VAL_SCHEMA_INVALIDE"
