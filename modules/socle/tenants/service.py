"""Le service du module doré : tenants, établissements, catalogue de paramètres.

Aucune classe de base, aucun dépôt générique (FR-010) : des fonctions, une transaction par
opération, des accès nommés.
"""

import uuid
from uuid import UUID

from modules.shared import transaction
from modules.shared.bd import sans_tenant
from modules.socle.tenants import acces


async def creer_tenant(
    nom: str,
    pays_code: str,
    *,
    country_pack_version: int = 1,
    raison_sociale: str | None = None,
) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T0a. `pays_code` est une donnée."""
    tenant_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_tenant(
            connexion, tenant_id, nom, pays_code, country_pack_version, raison_sociale
        )
    return tenant_id


async def creer_etablissement(tenant_id: UUID, nom: str, fuseau_horaire: str) -> UUID:
    """Pour les seeds et les tests ; aucune route ne l'expose en T0a."""
    etablissement_id = uuid.uuid7()
    async with transaction(tenant_id) as connexion:
        await acces.inserer_etablissement(
            connexion, etablissement_id, tenant_id, nom, fuseau_horaire
        )
    return etablissement_id


async def tenant_de_etablissement(etablissement_id: UUID) -> UUID | None:
    """PROVISOIRE jusqu'à T1a — passe par la fonction SECURITY DEFINER du schéma."""
    async with sans_tenant() as connexion:
        return await acces.appeler_tenant_de_etablissement(connexion, etablissement_id)


async def tenants_pour_travailleur() -> list[UUID]:
    """Les tenants que le travailleur d'événements parcourt — fonction SECURITY DEFINER."""
    async with sans_tenant() as connexion:
        return await acces.appeler_tenants_pour_travailleur(connexion)
