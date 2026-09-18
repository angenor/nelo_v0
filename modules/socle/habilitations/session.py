"""La session : ce qui prouve qu'une personne est déjà entrée, et ce qui l'en fait sortir.

La session vit **dans Valkey**, jamais en base : perdre Valkey ne coûte que des reconnexions
(ADR 007, FR-016). Le jeton d'accès est un JWT signé de soixante minutes ; il n'est pas un secret
durable, et **sa révocation est l'absence de `session:{sid}`**, consultée à chaque requête
(FR-026). C'est pourquoi rien d'autre n'entre dans le jeton : ni nom, ni capacité, ni statut. Le
contexte est la seule source de ce que la personne peut faire.

Le jeton de rafraîchissement est opaque, trente-deux octets tirés au hasard ; Valkey n'en garde
que l'empreinte. Il **tourne à chaque usage** : le présenter deux fois hors de la fenêtre de
concurrence est le signe qu'il a été volé, et fait tomber la session entière (research.md R-06).
"""

import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt

from modules.socle.habilitations.politique import PolitiqueSecurite
from modules.socle.habilitations.schemas import CanalOuverture, JetonAcces

ALGORITHME = "HS256"


def _empreinte(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def cle_session(session_id: UUID) -> str:
    return f"session:{session_id}"


def cle_sessions_compte(compte_id: UUID) -> str:
    return f"sessions_compte:{compte_id}"


def cle_refresh(jeton: str) -> str:
    return f"refresh:{_empreinte(jeton)}"


def signer_jeton_acces(
    compte_id: UUID, tenant_id: UUID, session_id: UUID, secret: str, duree: timedelta
) -> str:
    emis_le = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(compte_id),
            "ten": str(tenant_id),
            "sid": str(session_id),
            "iat": int(emis_le.timestamp()),
            "exp": int((emis_le + duree).timestamp()),
            "jti": secrets.token_urlsafe(16),
        },
        secret,
        algorithm=ALGORITHME,
    )


def verifier_jeton_acces(jeton: str, secret: str) -> JetonAcces:
    """Le contenu du jeton si la signature et l'expiration tiennent ; `ValueError` sinon.

    Le middleware traduit ce `ValueError` en `401 AUT_JETON_INVALIDE` : la raison exacte ne sort
    pas du serveur, elle n'apprendrait rien à une personne légitime et beaucoup à une autre.
    """
    try:
        charge = jwt.decode(jeton, secret, algorithms=[ALGORITHME])
    except jwt.PyJWTError as erreur:
        raise ValueError("jeton d'accès invalide") from erreur
    try:
        return JetonAcces(
            compte_id=UUID(charge["sub"]),
            tenant_id=UUID(charge["ten"]),
            session_id=UUID(charge["sid"]),
            emis_le=datetime.fromtimestamp(charge["iat"], UTC),
            expire_le=datetime.fromtimestamp(charge["exp"], UTC),
        )
    except (KeyError, ValueError, TypeError) as erreur:
        raise ValueError("jeton d'accès mal formé") from erreur


async def ouvrir_session(
    compte_id: UUID,
    tenant_id: UUID,
    canal: CanalOuverture,
    *,
    valkey,
    secret: str,
    politique: PolitiqueSecurite,
    duree: timedelta,
) -> tuple[UUID, str, str]:
    """Ouvre la session et rend `(session_id, jeton_acces, refresh)`.

    `duree` est celle du paramètre `securite.duree_session_minutes` du tenant, **figée à
    l'ouverture** : un changement de réglage vaut pour les sessions suivantes, et c'est dit.
    """
    # Tiré au hasard, et non en v7 comme les identifiants de table : celui-ci voyage dans un
    # jeton, et un v7 dirait l'heure exacte de l'ouverture à qui le lit.
    session_id = UUID(bytes=secrets.token_bytes(16), version=4)
    ouverte_le = datetime.now(UTC)
    secondes = max(int(duree.total_seconds()), 1)
    await valkey.set(
        cle_session(session_id),
        json.dumps(
            {
                "compte_id": str(compte_id),
                "tenant_id": str(tenant_id),
                "ouverte_le": ouverte_le.isoformat(),
                "canal": canal.value,
            }
        ),
        ex=secondes,
    )
    await valkey.sadd(cle_sessions_compte(compte_id), str(session_id))
    await valkey.expire(cle_sessions_compte(compte_id), secondes)
    refresh = await poser_refresh(session_id, valkey=valkey, duree=duree, generation=1)
    jeton = signer_jeton_acces(compte_id, tenant_id, session_id, secret, politique.JETON_ACCES)
    return session_id, jeton, refresh


async def poser_refresh(session_id: UUID, *, valkey, duree: timedelta, generation: int) -> str:
    """Un jeton de rafraîchissement neuf pour cette session ; Valkey n'en garde que l'empreinte."""
    refresh = secrets.token_urlsafe(32)
    await valkey.set(
        cle_refresh(refresh),
        json.dumps({"session_id": str(session_id), "generation": generation}),
        ex=max(int(duree.total_seconds()), 1),
    )
    return refresh


async def lire_refresh(refresh: str, *, valkey) -> dict | None:
    brut = await valkey.get(cle_refresh(refresh))
    return json.loads(brut) if brut is not None else None


async def tourner_refresh(
    ancien: str, session_id: UUID, *, valkey, duree: timedelta, politique: PolitiqueSecurite
) -> str:
    """Produit le jeton suivant, et marque l'ancien comme **remplacé**, sans l'effacer.

    L'ancien survit le temps de la fenêtre de concurrence, avec la trace de son remplaçant : deux
    onglets qui rafraîchissent en même temps reçoivent alors la même réponse. Passé ce délai, le
    représenter est le signe qu'une copie circule, et la session tombe.
    """
    charge = await lire_refresh(ancien, valkey=valkey) or {}
    neuf = await poser_refresh(
        session_id,
        valkey=valkey,
        duree=duree,
        generation=int(charge.get("generation", 1)) + 1,
    )
    await valkey.set(
        cle_refresh(ancien),
        json.dumps(
            {
                "session_id": str(session_id),
                "generation": charge.get("generation", 1),
                "remplace_le": datetime.now(UTC).isoformat(),
                "remplace_par": neuf,
            }
        ),
        ex=max(int(politique.FENETRE_CONCURRENCE_REFRESH.total_seconds()), 1),
    )
    return neuf


async def lire_session(session_id: UUID, *, valkey) -> dict | None:
    brut = await valkey.get(cle_session(session_id))
    return json.loads(brut) if brut is not None else None


async def session_valide(session_id: UUID, compte_id: UUID, *, valkey) -> bool:
    """**La liste de révocation** : la clé existe, et elle porte ce compte.

    Consultée à chaque requête. Une session absente est une session révoquée : la suspension, la
    fermeture et la réutilisation d'un refresh effacent toutes cette clé.
    """
    session = await lire_session(session_id, valkey=valkey)
    return session is not None and session["compte_id"] == str(compte_id)


async def revoquer_session(session_id: UUID, *, valkey) -> None:
    """La session cesse d'exister : c'est **cela**, la révocation, et rien d'autre."""
    session = await lire_session(session_id, valkey=valkey)
    await valkey.delete(cle_session(session_id))
    if session is not None:
        await valkey.srem(cle_sessions_compte(UUID(session["compte_id"])), str(session_id))


async def revoquer_toutes(compte_id: UUID, *, valkey) -> list[UUID]:
    """Suspension, changement administratif : toutes les sessions du compte tombent d'un coup."""
    membres = await valkey.smembers(cle_sessions_compte(compte_id))
    sessions = [UUID(m.decode() if isinstance(m, bytes) else m) for m in membres]
    for session_id in sessions:
        await valkey.delete(cle_session(session_id))
    await valkey.delete(cle_sessions_compte(compte_id))
    return sessions
