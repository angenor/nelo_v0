"""US3 : quatre chiffres suffisent, parce qu'il faut aussi cet appareil, et cinq essais seulement.

Le code personnel n'a aucune entropie. Ce qui protège le compte est la **conjonction** : la
possession de l'appareil (un secret dans un cookie que le script ne lit pas), cinq tentatives, puis
un verrou durable que seule une ouverture par code reçu lève. Chacune de ces trois protections est
vérifiée ici séparément : retirer l'une doit faire tomber un test.
"""

import httpx
import pytest

from modules.shared import transaction
from modules.socle.habilitations import acces
from tests.authentification.outils import (
    PREFIXE,
    cle_de_requete,
    en_tetes,
    evenements,
    ouvrir,
    semer_compte_neuf,
    vider_envois,
)

PIN = "1234"
AUTRE_PIN = "5678"


async def definir(client, session, pin=PIN, pin_courant=None) -> httpx.Response:
    corps: dict = {"pin": pin}
    if pin_courant is not None:
        corps["pin_courant"] = pin_courant
    return await client.post(
        f"{PREFIXE}/auth/pin/definition",
        headers={**en_tetes(session), "X-Nelo-Requete": cle_de_requete()},
        json=corps,
    )


async def ouvrir_par_pin(client, compte_id, pin=PIN) -> httpx.Response:
    return await client.post(
        f"{PREFIXE}/auth/pin",
        headers={"X-Nelo-Requete": cle_de_requete()},
        json={"compte_id": str(compte_id), "pin": pin},
    )


async def empreinte_en_base(tenant_id, compte_id) -> str | None:
    async with transaction(tenant_id) as connexion:
        ligne = await acces.lire_compte(connexion, compte_id)
    return ligne["pin_empreinte"]


# --- Définir son code personnel ------------------------------------------------------------------


async def test_definir_un_code_personnel_ne_le_renvoie_jamais(client, application, tenants_ab):
    session = await ouvrir(client, application, tenants_ab.numero_a)
    reponse = await definir(client, session)

    assert reponse.status_code == 204
    assert not reponse.content
    empreinte = await empreinte_en_base(tenants_ab.tenant_a, tenants_ab.compte_a)
    assert empreinte is not None
    # Ni le code, ni son empreinte ne sortent : l'un ouvrirait le compte, l'autre se casse hors ligne.
    assert PIN not in reponse.text
    assert empreinte not in reponse.text
    assert empreinte.startswith("$argon2id$")

    ecrits = await evenements(tenants_ab.tenant_a, "habilitations.pin.defini")
    assert len(ecrits) == 1
    assert ecrits[0]["charge"]["remplace"] is False


@pytest.mark.parametrize("pin", ["123", "12345", "abcd", "", "12 34"])
async def test_un_code_qui_n_a_pas_quatre_chiffres_est_refuse(client, application, tenants_ab, pin):
    session = await ouvrir(client, application, tenants_ab.numero_a)
    reponse = await definir(client, session, pin)
    assert reponse.status_code == 422
    assert reponse.json()["code"] == "VAL_SCHEMA_INVALIDE"


async def test_changer_son_code_dans_la_dispense_n_exige_pas_l_ancien(
    client, application, tenants_ab
):
    """Dix minutes après une ouverture par code reçu : c'est ce qui permet de rouvrir un oubli."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    assert (await definir(client, session)).status_code == 204
    assert (await definir(client, session, AUTRE_PIN)).status_code == 204

    ecrits = await evenements(tenants_ab.tenant_a, "habilitations.pin.defini")
    assert [e["charge"]["remplace"] for e in ecrits] == [False, True]


async def vieillir_la_session(valkey, compte_id, minutes: int) -> None:
    """Recule l'heure d'ouverture de la session : la dispense de code courant s'évalue dessus."""
    import json
    from datetime import UTC, datetime, timedelta

    from modules.socle.habilitations import session as session_module

    for membre in await valkey.smembers(session_module.cle_sessions_compte(compte_id)):
        session_id = membre.decode() if isinstance(membre, bytes) else membre
        cle = f"session:{session_id}"
        charge = json.loads(await valkey.get(cle))
        charge["ouverte_le"] = (datetime.now(UTC) - timedelta(minutes=minutes)).isoformat()
        await valkey.set(cle, json.dumps(charge), keepttl=True)


async def test_hors_dispense_le_code_courant_est_exige(client, application, tenants_ab, valkey):
    session = await ouvrir(client, application, tenants_ab.numero_a)
    assert (await definir(client, session)).status_code == 204
    await vieillir_la_session(valkey, tenants_ab.compte_a, minutes=30)

    sans_courant = await definir(client, session, AUTRE_PIN)
    assert sans_courant.status_code == 422
    assert sans_courant.json()["code"] == "AUT_PIN_ABSENT"

    faux_courant = await definir(client, session, AUTRE_PIN, pin_courant="0000")
    assert faux_courant.status_code == 422
    assert faux_courant.json()["code"] == "AUT_PIN_INVALIDE"

    assert (await definir(client, session, AUTRE_PIN, pin_courant=PIN)).status_code == 204


# --- Ouvrir par code personnel -------------------------------------------------------------------


async def test_rouvrir_par_code_personnel_n_envoie_aucun_message(client, application, tenants_ab):
    """C'est tout l'objet du code personnel : revenir sans attendre un SMS, ni en coûter un."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)
    await vider_envois(application)

    reponse = await ouvrir_par_pin(client, tenants_ab.compte_a)

    assert reponse.status_code == 200, reponse.text
    charge = reponse.json()
    assert charge["compte"]["pin_defini"] is True
    assert charge["jeton_acces"]
    assert application.state.passerelle_sms.envoyes == []

    ouvertures = await evenements(tenants_ab.tenant_a, "habilitations.session.ouverte")
    assert ouvertures[-1]["charge"]["canal"] == "PIN"


async def test_sur_un_appareil_inconnu_le_code_personnel_n_ouvre_rien(
    client, application, tenants_ab
):
    """Le code seul ne vaut rien : sans le secret d'appareil, il n'y a rien à vérifier."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)

    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as neuf:
        reponse = await ouvrir_par_pin(neuf, tenants_ab.compte_a)
        appareils = await neuf.get(f"{PREFIXE}/auth/appareil")

    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_APPAREIL_INCONNU"
    assert appareils.json()["comptes"] == []


async def test_un_compte_sans_code_personnel_le_dit(client, application, tenants_ab):
    await ouvrir(client, application, tenants_ab.numero_a)
    reponse = await ouvrir_par_pin(client, tenants_ab.compte_a)
    assert reponse.status_code == 401
    assert reponse.json()["code"] == "AUT_PIN_ABSENT"


async def test_un_code_faux_dit_les_tentatives_restantes(client, application, tenants_ab):
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)

    for restantes in (4, 3, 2, 1):
        reponse = await ouvrir_par_pin(client, tenants_ab.compte_a, "0000")
        assert reponse.status_code == 401
        assert reponse.json()["code"] == "AUT_PIN_INVALIDE"
        assert reponse.json()["details"]["tentatives_restantes"] == restantes


async def test_cinq_codes_faux_verrouillent_durablement(client, application, tenants_ab, valkey):
    """Le verrou est en base, pas dans l'éphémère : perdre Valkey ne déverrouille personne."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)
    for _ in range(4):
        await ouvrir_par_pin(client, tenants_ab.compte_a, "0000")

    cinquieme = await ouvrir_par_pin(client, tenants_ab.compte_a, "0000")
    assert cinquieme.status_code == 401
    assert cinquieme.json()["code"] == "AUT_PIN_TENTATIVES_EPUISEES"

    async with transaction(tenants_ab.tenant_a) as connexion:
        ligne = await acces.lire_compte(connexion, tenants_ab.compte_a)
    assert ligne["pin_verrouille_le"] is not None

    # Même avec le bon code, et même après la perte du magasin éphémère : le verrou tient.
    await valkey.flushdb()
    assert (await ouvrir_par_pin(client, tenants_ab.compte_a)).status_code == 401


async def test_une_ouverture_par_code_recu_leve_le_verrou(client, application, tenants_ab, valkey):
    """Le versant positif du verrou : la personne n'est pas enfermée dehors, elle reçoit un SMS."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)
    for _ in range(5):
        await ouvrir_par_pin(client, tenants_ab.compte_a, "0000")

    # La minute de délai avant renvoi est réelle : le test la laisse passer plutôt que d'attendre.
    await valkey.delete(f"otp_renvoi:{tenants_ab.numero_a}")
    session = await ouvrir(client, application, tenants_ab.numero_a)
    assert (await definir(client, session, AUTRE_PIN)).status_code == 204
    assert (await ouvrir_par_pin(client, tenants_ab.compte_a, AUTRE_PIN)).status_code == 200


# --- Les comptes connus de l'appareil ------------------------------------------------------------


async def test_l_appareil_propose_des_noms_jamais_un_numero(client, application, tenants_ab):
    """FR-021 : afficher un numéro sur l'écran d'accueil le donnerait à qui tient le téléphone."""
    session = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, session)

    reponse = await client.get(f"{PREFIXE}/auth/appareil")

    assert reponse.status_code == 200
    comptes = reponse.json()["comptes"]
    assert len(comptes) == 1
    assert set(comptes[0]) == {"compte_id", "nom", "prenoms", "pin_defini"}
    assert comptes[0]["nom"]
    assert tenants_ab.numero_a not in reponse.text


async def test_sans_cookie_l_appareil_ne_connait_personne(client, application):
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as neuf:
        reponse = await neuf.get(f"{PREFIXE}/auth/appareil")
    assert reponse.status_code == 200
    assert reponse.json()["comptes"] == []


async def test_deux_comptes_connus_du_meme_appareil_ont_chacun_leur_code(
    client, application, tenants_ab
):
    """US8-4 : deux parents, un téléphone. Chacun son code, et l'un n'ouvre pas le compte de l'autre."""
    premiere = await ouvrir(client, application, tenants_ab.numero_a)
    await definir(client, premiere, PIN)
    numero, second_compte = await semer_compte_neuf(tenants_ab.a)
    seconde = await ouvrir(client, application, numero)
    await definir(client, seconde, AUTRE_PIN)

    comptes = (await client.get(f"{PREFIXE}/auth/appareil")).json()["comptes"]
    assert {c["compte_id"] for c in comptes} == {
        str(tenants_ab.compte_a),
        str(second_compte),
    }

    assert (await ouvrir_par_pin(client, tenants_ab.compte_a, PIN)).status_code == 200
    assert (await ouvrir_par_pin(client, second_compte, AUTRE_PIN)).status_code == 200
    # Le code de l'un n'ouvre pas le compte de l'autre.
    assert (await ouvrir_par_pin(client, second_compte, PIN)).status_code == 401
