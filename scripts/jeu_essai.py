"""Le jeu d'essai : deux tenants, A et B, avec un établissement chacun.

    uv run python -m scripts.jeu_essai

Imprime les identifiants en forme `export`, à évaluer dans le shell. Le code pays et le fuseau
horaire sont des **données** du tenant et de l'établissement, jamais des constantes du code.
"""

import asyncio

from api.configuration import Configuration
from modules.shared import bd
from modules.socle import tenants


async def principal() -> None:
    configuration = Configuration()
    bd.configurer(configuration.bd_url_application, taille_pool=1)
    try:
        tenant_a = await tenants.creer_tenant("Établissement d'essai A", "CI")
        etab_a = await tenants.creer_etablissement(tenant_a, "École A", "Africa/Abidjan")
        tenant_b = await tenants.creer_tenant("Établissement d'essai B", "CI")
        etab_b = await tenants.creer_etablissement(tenant_b, "École B", "Africa/Abidjan")
    finally:
        await bd.fermer()
    print(f"export ETAB_A={etab_a} ETAB_B={etab_b}")


if __name__ == "__main__":
    asyncio.run(principal())
