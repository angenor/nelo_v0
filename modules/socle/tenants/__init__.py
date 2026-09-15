"""Le module doré — tenants, établissements, catalogue de paramètres.

L'interface de service, et rien d'autre : ni tables, ni accès aux données, ni moteur.
"""

from modules.socle.tenants.service import (
    creer_etablissement,
    creer_tenant,
    tenant_de_etablissement,
)

__all__ = ["creer_tenant", "creer_etablissement", "tenant_de_etablissement"]
