"""L'appareil connu : ce qui, avec quatre chiffres, suffit à rouvrir une session.

Un code personnel de quatre chiffres n'a aucune entropie. Ce qui protège le compte est la
**conjonction** : la possession de cet appareil, cinq essais, puis un verrou durable
(research.md R-13). Le secret d'appareil vit dans le cookie `nelo_appareils`, que le script ne lit
pas ; Valkey n'en garde que l'empreinte, et la liste des appareils de chaque compte, pour tout
oublier d'un coup quand un compte est suspendu.

Un cookie peut porter **plusieurs** secrets, un par compte connu : deux parents qui partagent un
téléphone se reconnaissent chacun sur le même appareil (US8).
"""

import hashlib
import json
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

SEPARATEUR = "."


def _empreinte(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def cle_appareil(secret: str) -> str:
    return f"appareil:{_empreinte(secret)}"


def cle_appareils_compte(compte_id: UUID) -> str:
    return f"appareils_compte:{compte_id}"


@dataclass(frozen=True, slots=True)
class Appareil:
    """Les secrets lus du cookie, tels quels. La route les lit ; le service ne voit que ceci."""

    secrets_connus: tuple[str, ...] = ()

    @classmethod
    def depuis_cookie(cls, valeur: str | None) -> Appareil:
        if not valeur:
            return cls()
        return cls(tuple(morceau for morceau in valeur.split(SEPARATEUR) if morceau))

    def en_cookie(self) -> str:
        return SEPARATEUR.join(self.secrets_connus)

    def avec(self, secret: str) -> Appareil:
        if secret in self.secrets_connus:
            return self
        return Appareil((*self.secrets_connus, secret))

    def sans(self, secret: str) -> Appareil:
        return Appareil(tuple(s for s in self.secrets_connus if s != secret))


async def connaitre(compte_id: UUID, tenant_id: UUID, *, valkey, jours: int) -> str:
    """Rend un secret neuf qui désigne cet appareil pour ce compte, valable `jours` jours."""
    secret = secrets.token_urlsafe(32)
    secondes = max(int(timedelta(days=jours).total_seconds()), 1)
    await valkey.set(
        cle_appareil(secret),
        json.dumps(
            {
                "compte_id": str(compte_id),
                "tenant_id": str(tenant_id),
                "connu_le": datetime.now(UTC).isoformat(),
            }
        ),
        ex=secondes,
    )
    await valkey.sadd(cle_appareils_compte(compte_id), _empreinte(secret))
    await valkey.expire(cle_appareils_compte(compte_id), secondes)
    return secret


async def comptes_connus(appareil: Appareil, *, valkey) -> list[tuple[str, UUID, UUID]]:
    """Les `(secret, compte_id, tenant_id)` du cookie que Valkey reconnaît encore.

    Un secret périmé, ou dont le compte a été oublié, disparaît simplement de la liste : le cookie
    n'a pas à être juste, c'est Valkey qui fait foi.
    """
    connus = []
    for secret in appareil.secrets_connus:
        brut = await valkey.get(cle_appareil(secret))
        if brut is None:
            continue
        charge = json.loads(brut)
        connus.append((secret, UUID(charge["compte_id"]), UUID(charge["tenant_id"])))
    return connus


async def secret_du_compte(appareil: Appareil, compte_id: UUID, *, valkey) -> str | None:
    for secret, connu, _ in await comptes_connus(appareil, valkey=valkey):
        if connu == compte_id:
            return secret
    return None


async def oublier(compte_id: UUID, *, valkey) -> None:
    """Tous les appareils de ce compte cessent d'être connus : suspension, changement de numéro."""
    empreintes = await valkey.smembers(cle_appareils_compte(compte_id))
    for empreinte in empreintes:
        texte = empreinte.decode() if isinstance(empreinte, bytes) else empreinte
        await valkey.delete(f"appareil:{texte}")
    await valkey.delete(cle_appareils_compte(compte_id))
