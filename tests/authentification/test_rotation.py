"""US5 : le rafraîchissement tourne à chaque usage, et un jeton rejoué signale un vol.

Un jeton de rafraîchissement vaut la session entière : s'il ne changeait jamais, le voler une fois
suffirait à entrer aussi longtemps que la personne travaille, sans qu'aucune trace ne le dise. La
rotation rend le vol **détectable** : deux usages du même jeton, et l'un des deux est de trop.

Reste que deux onglets rafraîchissent parfois à la même seconde, et ce n'est pas un vol. D'où la
fenêtre de concurrence, courte et nommée : dedans, l'ancien jeton rend la même réponse que le neuf ;
dehors, la session tombe entièrement, jeton neuf compris. Cette suite mesure les deux côtés de la
fenêtre, la borne de durée que le tenant fixe, et la fermeture volontaire, qui révoque tout **sauf**
l'appareil : celui-ci reste le sien, et c'est ce qui permet de revenir par quatre chiffres.
"""

import json
from datetime import UTC, datetime, timedelta

import httpx

from modules.socle.habilitations import session as session_module
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    en_tetes,
    evenements,
    ouvrir,
    semer_compte_neuf,
)
from tests.module_dore.outils import poser

CHEMIN_PROTEGE = f"{PREFIXE}/parametres"
COOKIE_REFRESH = "nelo_refresh"
CLE_DUREE = "securite.duree_session_minutes"


async def rafraichir(application, refresh: str | None) -> httpx.Response:
    """Le rafraîchissement tel qu'un navigateur le fait : le jeton n'est que dans un cookie.

    Le client est neuf à chaque appel, pour que le jeton présenté soit exactement celui qu'on veut
    présenter, et non celui que le bocal à cookies a retenu.
    """
    en_tetes_envoyes = {"X-Nelo-Requete": cle_de_requete()}
    if refresh is not None:
        en_tetes_envoyes["Cookie"] = f"{COOKIE_REFRESH}={refresh}"
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as neuf:
        return await neuf.post(f"{PREFIXE}/auth/rafraichissement", headers=en_tetes_envoyes)


def refresh_recu(reponse: httpx.Response) -> str:
    recu = reponse.cookies.get(COOKIE_REFRESH)
    assert recu, f"aucun cookie {COOKIE_REFRESH} dans la réponse"
    return recu


def session_id_du_jeton(application, jeton: str):
    secret = application.state.configuration.secret_jeton
    return session_module.verifier_jeton_acces(jeton, secret).session_id


async def vieillir_le_remplacement(valkey, refresh: str, secondes: int) -> None:
    """Recule l'heure du remplacement : la fenêtre de concurrence s'évalue dessus.

    On ne peut pas attendre dix secondes dans une suite de tests, et la fenêtre est une constante
    de sécurité du produit : c'est donc l'horodatage qu'on déplace, pas le délai.
    """
    cle = session_module.cle_refresh(refresh)
    charge = json.loads(await valkey.get(cle))
    charge["remplace_le"] = (datetime.now(UTC) - timedelta(seconds=secondes)).isoformat()
    await valkey.set(cle, json.dumps(charge), keepttl=True)


# --- La rotation ---------------------------------------------------------------------------------


async def test_le_rafraichissement_rend_un_jeton_neuf_et_un_cookie_neuf(
    client, application, tenants_ab
):
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    ancien = session.cookies[COOKIE_REFRESH]

    reponse = await rafraichir(application, ancien)

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["resultat"] == "SESSION"
    assert charge["jeton_acces"] != session.jeton
    assert refresh_recu(reponse) != ancien
    # Le jeton neuf porte la même session : rafraîchir n'en ouvre pas une seconde.
    assert session_id_du_jeton(application, charge["jeton_acces"]) == session_id_du_jeton(
        application, session.jeton
    )


async def test_dans_la_fenetre_deux_onglets_recoivent_le_meme_jeton(
    client, application, tenants_ab
):
    """Le second onglet n'a rien fait de mal : il reçoit ce que le premier a déjà reçu."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    ancien = session.cookies[COOKIE_REFRESH]

    premiere = await rafraichir(application, ancien)
    seconde = await rafraichir(application, ancien)

    assert seconde.status_code == 200, seconde.text
    assert refresh_recu(seconde) == refresh_recu(premiere)


async def test_hors_fenetre_le_jeton_rejoue_fait_tomber_toute_la_session(
    client, application, valkey, tenants_ab
):
    """Une copie qui circule : on ne sait pas laquelle est la bonne, donc aucune ne l'est."""
    numero, _ = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    session_id = session_id_du_jeton(application, session.jeton)
    ancien = session.cookies[COOKIE_REFRESH]
    neuf = refresh_recu(await rafraichir(application, ancien))

    await vieillir_le_remplacement(valkey, ancien, secondes=30)
    rejeu = await rafraichir(application, ancien)

    assert rejeu.status_code == 401
    assert rejeu.json()["code"] == "AUT_JETON_INVALIDE"

    # Le jeton neuf tombe avec le reste : c'est la session entière qui est fermée.
    suite = await rafraichir(application, neuf)
    assert suite.status_code == 401
    assert suite.json()["code"] == "AUT_SESSION_REVOQUEE"

    protege = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert protege.status_code == 401
    assert protege.json()["code"] == "AUT_SESSION_REVOQUEE"

    fermetures = await evenements(tenants_ab.tenant_a, "habilitations.session.fermee")
    miennes = [e for e in fermetures if e["charge"]["session_id"] == str(session_id)]
    assert [e["charge"]["motif"] for e in miennes] == ["REUTILISATION"]


async def test_un_jeton_de_rafraichissement_inconnu_est_refuse(application):
    reponse = await rafraichir(application, "un-jeton-que-personne-n-a-jamais-emis")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_JETON_INVALIDE"


async def test_sans_cookie_le_rafraichissement_dit_que_le_jeton_manque(application):
    reponse = await rafraichir(application, None)

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_JETON_MANQUANT"


# --- La borne de durée, réglée par le tenant ------------------------------------------------------


async def test_la_duree_de_session_du_tenant_borne_le_rafraichissement(
    client, application, valkey, sessions_ab, tenants_ab
):
    """US5-5 : passé la durée que le tenant a fixée, on rouvre, on ne prolonge pas."""
    pose = await poser(
        client, sessions_ab.a, tenants_ab.etab_a, CLE_DUREE, "TENANT", tenants_ab.tenant_a, 1
    )
    assert pose.status_code == 200, pose.text

    numero, _ = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    session_id = session_id_du_jeton(application, session.jeton)
    cle = session_module.cle_session(session_id)
    # La durée du réglage est figée à l'ouverture, et c'est le TTL de la clé qui la porte.
    assert 0 < await valkey.ttl(cle) <= 60

    # `EXPIRE` à zéro fait ce que le terme du TTL aurait fait : la clé cesse d'exister.
    await valkey.expire(cle, 0)
    reponse = await rafraichir(application, session.cookies[COOKIE_REFRESH])

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_SESSION_REVOQUEE"


# --- La fermeture volontaire ----------------------------------------------------------------------


async def test_fermer_sa_session_revoque_tout_mais_l_appareil_reste_connu(
    client, application, tenants_ab
):
    """US5-3 : le poste partagé se quitte d'un geste, et le téléphone reste le sien."""
    numero, compte = await semer_compte_neuf(tenants_ab.a)
    session = await ouvrir(client, application, numero)
    session_id = session_id_du_jeton(application, session.jeton)
    refresh = session.cookies[COOKIE_REFRESH]

    fermeture = await client.delete(
        f"{PREFIXE}/auth/session", headers=en_tetes(session, ecriture=True)
    )

    assert fermeture.status_code == 204
    poses = fermeture.headers.get_list("set-cookie")
    efface = [entete for entete in poses if entete.startswith(f"{COOKIE_REFRESH}=")]
    assert efface, "le cookie de rafraîchissement n'est pas effacé"
    assert "Max-Age=0" in efface[0]

    protege = await client.get(CHEMIN_PROTEGE, headers=en_tetes(session, tenants_ab.etab_a))
    assert protege.status_code == 401
    assert protege.json()["code"] == "AUT_SESSION_REVOQUEE"

    suite = await rafraichir(application, refresh)
    assert suite.status_code == 401
    assert suite.json()["code"] == "AUT_SESSION_REVOQUEE"

    connus = (await client.get(f"{PREFIXE}/auth/appareil")).json()["comptes"]
    assert str(compte) in {c["compte_id"] for c in connus}

    fermetures = await evenements(tenants_ab.tenant_a, "habilitations.session.fermee")
    miennes = [e for e in fermetures if e["charge"]["session_id"] == str(session_id)]
    assert [e["charge"]["motif"] for e in miennes] == ["DECONNEXION"]
