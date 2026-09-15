"""La composition : l'application, ses middlewares, ses gestionnaires, ses routes, son cycle de vie.

`api/` importe tout ce dont il a besoin et **ne porte aucune règle métier** : la validation du
catalogue, la résolution des portées et l'écriture de l'événement vivent dans `tenants`. Les
dépendances sont injectées ici, jamais importées d'un module à l'autre.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import valkey.asyncio as valkey
from fastapi import FastAPI

from api import contrat, erreurs
from api.configuration import Configuration
from api.idempotence import Idempotence
from api.routes import parametres, sante
from api.tenant_provisoire import TenantProvisoire
from api.travailleur import Travailleur
from modules.shared import bd
from modules.socle import tenants

journal = logging.getLogger("nelo.api")


def creer_application(configuration: Configuration | None = None) -> FastAPI:
    configuration = configuration or Configuration()

    @asynccontextmanager
    async def cycle_de_vie(application: FastAPI) -> AsyncIterator[None]:
        bd.configurer(configuration.bd_url_application, taille_pool=configuration.bd_taille_pool)
        travailleur = Travailleur(configuration)
        await travailleur.demarrer()
        try:
            yield
        finally:
            await travailleur.arreter()
            await application.state.valkey.aclose()
            await bd.fermer()

    application = FastAPI(
        title="Nelo — API",
        version="1",
        root_path="/api/v1",
        servers=[{"url": "/api/v1"}],
        lifespan=cycle_de_vie,
    )
    application.state.configuration = configuration
    application.state.valkey = valkey.from_url(configuration.valkey_url)

    # Le dernier ajouté est le plus extérieur : l'établissement d'abord, l'idempotence ensuite.
    application.add_middleware(Idempotence)
    application.add_middleware(TenantProvisoire, resolveur=tenants.tenant_de_etablissement)
    erreurs.installer(application)
    application.include_router(sante.routeur)
    application.include_router(parametres.routeur)
    contrat.installer(application)
    return application


app = creer_application()
