"""La composition : l'application, ses middlewares, ses gestionnaires, ses routes, son cycle de vie.

`api/` importe tout ce dont il a besoin et **ne porte aucune règle métier** : la validation du
catalogue, la résolution des portées et l'écriture de l'événement vivent dans `tenants`. Les
dépendances sont injectées ici, jamais importées d'un module à l'autre.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

import valkey.asyncio as valkey
from fastapi import FastAPI

from api import consommateurs, contrat, erreurs
from api.annee import Annee
from api.configuration import Configuration
from api.etablissement import Etablissement
from api.idempotence import Idempotence
from api.routes import authentification, comptes, moi, parametres, sante
from api.session import Session
from api.travailleur import Travailleur
from modules.metier.finance import SimulationAgregateurPaiement
from modules.shared import bd
from modules.socle import tenants
from modules.socle.assistance import Assistance, SimulationServiceInference
from modules.socle.communication import SimulationPasserelleSms

journal = logging.getLogger("nelo.api")


def configurer_journal() -> None:
    """Le journal applicatif `nelo.*` au niveau INFO, sans toucher à celui du serveur ASGI."""
    racine = logging.getLogger("nelo")
    if not racine.handlers:
        gestionnaire = logging.StreamHandler()
        gestionnaire.setFormatter(logging.Formatter("%(levelname)s:     %(name)s — %(message)s"))
        racine.addHandler(gestionnaire)
        racine.setLevel(logging.INFO)


def creer_application(configuration: Configuration | None = None) -> FastAPI:
    configuration = configuration or Configuration()

    @asynccontextmanager
    async def cycle_de_vie(application: FastAPI) -> AsyncIterator[None]:
        configurer_journal()
        bd.configurer(configuration.bd_url_application, taille_pool=configuration.bd_taille_pool)
        # L'aiguilleur reçoit ici ses dépendances externes : le module qui traite l'événement ne
        # les importe jamais lui-même.
        travailleur = Travailleur(
            configuration,
            consommateurs.aiguilleur(
                application.state.passerelle_sms, application.state.valkey, configuration
            ),
        )
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
    # Les trois dépendances externes, simulées par défaut ; aucune route de T0a ne les appelle —
    # elles existent pour être remplacées (T4a, T8b).
    delai = configuration.simulation_delai
    application.state.passerelle_sms = SimulationPasserelleSms(
        configuration.simulation_sms_mode, delai, configuration.sms_journal
    )
    application.state.agregateur_paiement = SimulationAgregateurPaiement(
        configuration.simulation_paiement_mode, delai
    )
    application.state.service_inference = SimulationServiceInference(
        configuration.simulation_inference_mode, delai
    )

    async def assistance_suspendue(tenant_id: UUID, etablissement_id: UUID) -> bool:
        effective = await tenants.valeur_effective(
            tenant_id, "assistance.suspendue", tenants.Portee.ETABLISSEMENT, etablissement_id
        )
        return effective.valeur is True

    # L'injection se fait ici : l'assistance n'importe jamais tenants.
    application.state.assistance = Assistance(
        assistance_suspendue, application.state.service_inference
    )

    # Le dernier ajouté est le plus extérieur, donc exécuté le premier : la session dit qui
    # parle, l'établissement et l'année disent d'où et de quand, l'idempotence mémorise, une fois
    # le tenant connu. Aucun de ces quatre middlewares ne décide d'une règle métier.
    application.add_middleware(Idempotence)
    application.add_middleware(Annee)
    application.add_middleware(Etablissement)
    application.add_middleware(Session)
    erreurs.installer(application)
    application.include_router(sante.routeur)
    application.include_router(authentification.routeur)
    application.include_router(moi.routeur)
    application.include_router(comptes.routeur)
    application.include_router(parametres.routeur)
    contrat.installer(application)
    return application


app = creer_application()
