"""La composition : l'application, ses middlewares, ses gestionnaires, ses routes, son cycle de vie.

`api/` importe tout ce dont il a besoin et **ne porte aucune règle métier** : la validation du
catalogue, la résolution des portées et l'écriture de l'événement vivent dans `tenants`. Les
dépendances sont injectées ici, jamais importées d'un module à l'autre.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api import erreurs
from api.configuration import Configuration
from api.idempotence import Idempotence
from api.tenant_provisoire import TenantProvisoire
from modules.shared import bd
from modules.socle import tenants

journal = logging.getLogger("nelo.api")


def creer_application(configuration: Configuration | None = None) -> FastAPI:
    configuration = configuration or Configuration()

    @asynccontextmanager
    async def cycle_de_vie(application: FastAPI) -> AsyncIterator[None]:
        bd.configurer(configuration.bd_url_application, taille_pool=configuration.bd_taille_pool)
        # Point d'accroche : le travailleur d'événements (T060).
        try:
            yield
        finally:
            await bd.fermer()

    application = FastAPI(
        title="Nelo — API", version="1", root_path="/api/v1", lifespan=cycle_de_vie
    )
    application.state.configuration = configuration

    # Le dernier ajouté est le plus extérieur : l'établissement d'abord, l'idempotence ensuite.
    application.add_middleware(Idempotence)
    application.add_middleware(TenantProvisoire, resolveur=tenants.tenant_de_etablissement)
    erreurs.installer(application)
    return application


app = creer_application()
