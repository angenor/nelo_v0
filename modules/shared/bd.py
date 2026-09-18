"""L'accès à PostgreSQL : un moteur, et l'unique point d'entrée transactionnel.

**Aucun autre code n'ouvre de transaction.** `transaction(tenant_id)` ouvre la transaction, pose
`app.current_tenant` par `set_config(..., true)` — l'équivalent de `SET LOCAL`, qui n'accepte pas de
valeur liée —, rend la connexion, et referme. La variable meurt avec la transaction : une connexion
rendue au pool ne porte plus aucun tenant (research.md R-07).
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, create_async_engine

_moteur: AsyncEngine | None = None


def configurer(url: str, *, taille_pool: int = 5) -> AsyncEngine:
    """Crée le moteur du processus. Appelé par la composition (`api/`) et par les tests."""
    global _moteur
    _moteur = create_async_engine(url, pool_size=taille_pool, max_overflow=0, pool_pre_ping=True)
    return _moteur


def moteur() -> AsyncEngine:
    if _moteur is None:
        raise RuntimeError("le moteur de base de données n'est pas configuré")
    return _moteur


async def fermer() -> None:
    global _moteur
    if _moteur is not None:
        await _moteur.dispose()
        _moteur = None


@asynccontextmanager
async def transaction(tenant_id: UUID) -> AsyncIterator[AsyncConnection]:
    """L'unique point d'entrée : ouvre la transaction, pose app.current_tenant, la rend, referme."""
    async with moteur().begin() as connexion:
        await connexion.execute(
            text("SELECT set_config('app.current_tenant', :tenant, true)"),
            {"tenant": str(tenant_id)},
        )
        yield connexion


@asynccontextmanager
async def sans_tenant() -> AsyncIterator[AsyncConnection]:
    """Une transaction **sans** tenant, pour les seules fonctions `SECURITY DEFINER` du schéma.

    Sous la RLS forcée, elle ne voit aucune ligne et n'écrit rien : elle ne sert qu'aux fonctions
    qui répondent **avant que le tenant ne soit connu**, et qui ne renvoient que des identifiants
    et un statut : `tenants.tenants_pour_travailleur`, `habilitations.comptes_par_identifiant`,
    `compte_par_invitation`, `compte_par_id_sans_tenant`. Un test les énumère et échoue si une
    cinquième apparaît.
    """
    async with moteur().begin() as connexion:
        yield connexion
