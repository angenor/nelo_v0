"""FR-011, FR-026 : ce qui ouvre une session, ce qui la ferme, et ce qui n'ouvre rien.

La révocation n'est pas une liste noire à écrire : c'est **l'absence** de la clé de session, lue à
chaque requête. Ces tests le prouvent dans les deux sens.
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from modules.socle.habilitations import session as ses
from modules.socle.habilitations.politique import POLITIQUE
from modules.socle.habilitations.schemas import CanalOuverture

SECRET = "secret-de-test-sans-valeur-de-production"
DUREE = timedelta(minutes=480)


async def ouvrir(valkey, compte_id=None, tenant_id=None, canal=CanalOuverture.CODE):
    return await ses.ouvrir_session(
        compte_id or uuid.uuid7(),
        tenant_id or uuid.uuid7(),
        canal,
        valkey=valkey,
        secret=SECRET,
        politique=POLITIQUE,
        duree=DUREE,
    )


async def test_une_session_ouverte_porte_son_jeton_son_refresh_et_ses_clefs(valkey):
    compte_id, tenant_id = uuid.uuid7(), uuid.uuid7()
    session_id, jeton, refresh = await ouvrir(valkey, compte_id, tenant_id)

    lu = ses.verifier_jeton_acces(jeton, SECRET)
    assert (lu.compte_id, lu.tenant_id, lu.session_id) == (compte_id, tenant_id, session_id)
    assert lu.expire_le - lu.emis_le == POLITIQUE.JETON_ACCES

    assert await ses.session_valide(session_id, compte_id, valkey=valkey)
    membres = await valkey.smembers(ses.cle_sessions_compte(compte_id))
    assert {m.decode() for m in membres} == {str(session_id)}
    assert await valkey.get(ses.cle_refresh(refresh)) is not None
    # Le refresh n'est jamais gardé en clair : seule son empreinte sert de clé.
    assert refresh not in ses.cle_refresh(refresh)


async def test_le_jeton_ne_porte_que_l_identite_de_la_session(valkey):
    _, jeton, _ = await ouvrir(valkey)
    charge = jwt.decode(jeton, SECRET, algorithms=["HS256"])
    assert set(charge) == {"sub", "ten", "sid", "iat", "exp", "jti"}


async def test_un_jeton_falsifie_est_refuse(valkey):
    _, jeton, _ = await ouvrir(valkey)
    with pytest.raises(ValueError):
        ses.verifier_jeton_acces(jeton, SECRET + "-mais-pas-tout-a-fait")
    with pytest.raises(ValueError):
        ses.verifier_jeton_acces(jeton[:-2] + "xy", SECRET)
    with pytest.raises(ValueError):
        ses.verifier_jeton_acces("pas-un-jeton", SECRET)


def test_un_jeton_expire_est_refuse():
    passe = datetime.now(UTC) - timedelta(hours=2)
    jeton = jwt.encode(
        {
            "sub": str(uuid.uuid7()),
            "ten": str(uuid.uuid7()),
            "sid": str(uuid.uuid7()),
            "iat": int(passe.timestamp()),
            "exp": int((passe + timedelta(minutes=60)).timestamp()),
            "jti": "x",
        },
        SECRET,
        algorithm="HS256",
    )
    with pytest.raises(ValueError):
        ses.verifier_jeton_acces(jeton, SECRET)


def test_un_jeton_signe_mais_mal_forme_est_refuse():
    jeton = jwt.encode({"sub": "pas-un-uuid"}, SECRET, algorithm="HS256")
    with pytest.raises(ValueError):
        ses.verifier_jeton_acces(jeton, SECRET)


async def test_une_session_absente_est_une_session_revoquee(valkey):
    compte_id = uuid.uuid7()
    session_id, _, _ = await ouvrir(valkey, compte_id)
    await ses.revoquer_session(session_id, valkey=valkey)
    assert not await ses.session_valide(session_id, compte_id, valkey=valkey)
    assert not await valkey.smembers(ses.cle_sessions_compte(compte_id))


async def test_une_session_qui_porte_un_autre_compte_ne_vaut_pas(valkey):
    """Un jeton dont le `sub` ne correspond plus à la session : la session ne le reconnaît pas."""
    session_id, _, _ = await ouvrir(valkey, uuid.uuid7())
    assert not await ses.session_valide(session_id, uuid.uuid7(), valkey=valkey)


async def test_revoquer_toutes_ferme_chaque_session_du_compte(valkey):
    compte_id = uuid.uuid7()
    premieres = [(await ouvrir(valkey, compte_id))[0] for _ in range(3)]
    fermees = await ses.revoquer_toutes(compte_id, valkey=valkey)
    assert set(fermees) == set(premieres)
    for session_id in premieres:
        assert not await ses.session_valide(session_id, compte_id, valkey=valkey)
    assert await valkey.exists(ses.cle_sessions_compte(compte_id)) == 0


async def test_revoquer_toutes_sur_un_compte_sans_session_ne_leve_pas(valkey):
    assert await ses.revoquer_toutes(uuid.uuid7(), valkey=valkey) == []


async def test_la_duree_de_session_borne_les_clefs(valkey):
    """La durée vient du paramètre du tenant, figée à l'ouverture."""
    session_id, _, refresh = await ses.ouvrir_session(
        uuid.uuid7(),
        uuid.uuid7(),
        CanalOuverture.CODE,
        valkey=valkey,
        secret=SECRET,
        politique=POLITIQUE,
        duree=timedelta(minutes=5),
    )
    assert 0 < int(await valkey.ttl(ses.cle_session(session_id))) <= 300
    assert 0 < int(await valkey.ttl(ses.cle_refresh(refresh))) <= 300


async def test_un_refresh_neuf_remplace_la_generation(valkey):
    session_id, _, premier = await ouvrir(valkey)
    second = await ses.poser_refresh(session_id, valkey=valkey, duree=DUREE, generation=2)
    assert second != premier
    charge = json.loads(await valkey.get(ses.cle_refresh(second)))
    assert charge == {"session_id": str(session_id), "generation": 2}


async def test_deux_sessions_du_meme_compte_coexistent(valkey):
    """Deux appareils, deux sessions : fermer l'une ne ferme pas l'autre."""
    compte_id = uuid.uuid7()
    une, _, _ = await ouvrir(valkey, compte_id)
    autre, _, _ = await ouvrir(valkey, compte_id)
    await ses.revoquer_session(une, valkey=valkey)
    assert not await ses.session_valide(une, compte_id, valkey=valkey)
    assert await ses.session_valide(autre, compte_id, valkey=valkey)
