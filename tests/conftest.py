"""Les fixtures communes : une base de test migrée sur base vierge, deux tenants, un client HTTP.

Les tests d'intégration s'exécutent contre la base logique `nelo_test` (surchargeable par
`NELO_BD_NOM_TEST`), recréée par `scripts/bd-vierge.sh` au début de la session — jamais contre un
schéma résiduel. Valkey est pris sur sa base 1, pour ne pas vider celle du serveur de développement.
"""

import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

RACINE = Path(__file__).resolve().parents[1]

os.environ["NELO_BD_NOM"] = os.environ.get("NELO_BD_NOM_TEST", "nelo_test")

from api.configuration import Configuration  # noqa: E402

_configuration = Configuration()
os.environ["NELO_VALKEY_URL"] = _configuration.valkey_url.rsplit("/", 1)[0] + "/1"

SUSPENSION = os.environ.get("NELO_TEST_SUSPENSION") == "1"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "suspension: la suite tourne avec assistance.suspendue posée au tenant de test"
    )


@pytest.fixture(scope="session")
def configuration() -> Configuration:
    return Configuration()


@pytest.fixture(scope="session")
def base_migree(configuration: Configuration) -> str:
    """Recrée la base de test et applique les migrations ; rend l'URL du rôle applicatif."""
    subprocess.run(
        [str(RACINE / "scripts" / "bd-vierge.sh")],
        cwd=RACINE,
        check=True,
        env={**os.environ, "NELO_BD_NOM": configuration.bd_nom or "nelo_test"},
        stdout=subprocess.DEVNULL,
    )
    return configuration.bd_url_application


@pytest.fixture(scope="session")
def url_proprietaire(configuration: Configuration, base_migree: str) -> str:
    from sqlalchemy.engine import make_url

    url = make_url(configuration.bd_url_proprietaire).set(database=configuration.bd_nom)
    return url.render_as_string(hide_password=False)


@pytest_asyncio.fixture(scope="session")
async def moteur_application(base_migree: str) -> AsyncIterator[AsyncEngine]:
    """Le moteur du processus, configuré sur la base de test sous le rôle nelo_app."""
    from modules.shared import bd

    moteur = bd.configurer(base_migree, taille_pool=5)
    yield moteur
    await bd.fermer()


@pytest_asyncio.fixture
async def moteur_pool_un(base_migree: str) -> AsyncIterator[AsyncEngine]:
    """Un moteur à une seule connexion : sa réutilisation est forcée."""
    moteur = create_async_engine(base_migree, pool_size=1, max_overflow=0)
    yield moteur
    await moteur.dispose()


@pytest.fixture(scope="session")
def application(moteur_application: AsyncEngine):
    from api.main import app

    return app


@pytest_asyncio.fixture
async def client(application) -> AsyncIterator[httpx.AsyncClient]:
    transport = httpx.ASGITransport(app=application, raise_app_exceptions=False)
    async with httpx.AsyncClient(transport=transport, base_url="http://nelo") as client:
        yield client


@pytest_asyncio.fixture
async def valkey(application) -> AsyncIterator:
    client = application.state.valkey
    await client.flushdb()
    yield client


@pytest.fixture
def requete_id() -> str:
    return str(uuid.uuid7())


@dataclass(frozen=True)
class DeuxTenants:
    tenant_a: UUID
    etab_a: UUID
    tenant_b: UUID
    etab_b: UUID


@pytest_asyncio.fixture
async def tenants_ab(moteur_application: AsyncEngine, client: httpx.AsyncClient) -> DeuxTenants:
    """Deux tenants neufs, un établissement chacun — neufs à chaque test, rien ne se partage."""
    from modules.socle import tenants

    tenant_a = await tenants.creer_tenant("Tenant A", "CI")
    etab_a = await tenants.creer_etablissement(tenant_a, "École A", "Africa/Abidjan")
    tenant_b = await tenants.creer_tenant("Tenant B", "CI")
    etab_b = await tenants.creer_etablissement(tenant_b, "École B", "Africa/Abidjan")
    if SUSPENSION:
        for tenant_id, etab_id in ((tenant_a, etab_a), (tenant_b, etab_b)):
            reponse = await client.put(
                "/api/v1/parametres/assistance.suspendue",
                headers={"X-Nelo-Etablissement": str(etab_id), "X-Nelo-Requete": str(uuid.uuid7())},
                json={"portee": "TENANT", "portee_id": str(tenant_id), "valeur": True},
            )
            assert reponse.status_code == 200, reponse.text
    return DeuxTenants(tenant_a, etab_a, tenant_b, etab_b)
