"""Les fixtures communes : une base de test migrée sur base vierge, deux tenants, un client HTTP.

Les tests d'intégration s'exécutent contre la base logique `nelo_test` (surchargeable par
`NELO_BD_NOM_TEST`), recréée par `scripts/bd-vierge.sh` au début de la session — jamais contre un
schéma résiduel. Valkey est pris sur sa base 1, pour ne pas vider celle du serveur de développement.
"""

import itertools
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
# Les deux variables sans défaut, posées avant l'import de la configuration : la suite doit
# tourner sur un poste neuf, sans `.env`.
os.environ.setdefault("NELO_SECRET_JETON", "secret-de-test-sans-valeur-de-production")
os.environ.setdefault("NELO_INDICATIF_DEFAUT", "225")

from api.configuration import Configuration  # noqa: E402

_configuration = Configuration()
os.environ["NELO_VALKEY_URL"] = _configuration.valkey_url.rsplit("/", 1)[0] + "/1"

SUSPENSION = os.environ.get("NELO_TEST_SUSPENSION") == "1"


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "suspension: la suite tourne avec assistance.suspendue posée au tenant de test"
    )
    config.addinivalue_line(
        "markers", "lent: la suite mesure un temps et répète beaucoup ; elle dure des secondes"
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


@pytest_asyncio.fixture(autouse=True)
async def valkey_vierge(application) -> AsyncIterator:
    """L'éphémère ne se transmet pas d'un test au suivant.

    Sans cela, les compteurs de débit d'un test compteraient dans le suivant : vingt demandes de
    code par heure et par client suffisent à faire tomber une suite entière, et le motif serait
    introuvable. Les sessions, les codes et les appareils s'effacent de même.
    """
    await application.state.valkey.flushdb()
    yield application.state.valkey


@pytest_asyncio.fixture
async def valkey(valkey_vierge) -> AsyncIterator:
    yield valkey_vierge


@pytest.fixture
def requete_id() -> str:
    return str(uuid.uuid7())


@dataclass(frozen=True)
class UnTenant:
    """Tout ce qu'un tenant de test porte : de quoi ouvrir une session et lire un contexte."""

    tenant: UUID
    etablissement: UUID
    personne: UUID
    compte: UUID
    numero: str
    annee: UUID
    annee_preparation: UUID


@dataclass(frozen=True)
class DeuxTenants:
    tenant_a: UUID
    etab_a: UUID
    tenant_b: UUID
    etab_b: UUID
    a: UnTenant
    b: UnTenant

    # Les raccourcis que les suites de T0a et de T1a lisent le plus souvent.
    @property
    def personne_a(self) -> UUID:
        return self.a.personne

    @property
    def compte_a(self) -> UUID:
        return self.a.compte

    @property
    def numero_a(self) -> str:
        return self.a.numero

    @property
    def annee_a(self) -> UUID:
        return self.a.annee

    @property
    def annee_prep_a(self) -> UUID:
        return self.a.annee_preparation

    @property
    def personne_b(self) -> UUID:
        return self.b.personne

    @property
    def compte_b(self) -> UUID:
        return self.b.compte

    @property
    def numero_b(self) -> str:
        return self.b.numero

    @property
    def annee_b(self) -> UUID:
        return self.b.annee

    @property
    def annee_prep_b(self) -> UUID:
        return self.b.annee_preparation


# Le tenant A porte le pack du pays du pilote, le tenant B le pack fictif : le test d'agnosticité
# tourne ainsi sur chaque suite qui lit un contexte, sans fixture de plus.
PACKS_DE_TEST = {"a": "CI", "b": "ZZ"}
LANGUES_DE_TEST = {"a": "fr", "b": "en"}

# Un numéro neuf par tenant et par test. La base de test n'est recréée qu'une fois par session,
# et un numéro se résout **tous tenants confondus** (c'est le sujet même de la tranche) : deux
# tests qui réutiliseraient le même numéro se retrouveraient avec deux comptes dessus, et une
# demande de code y verrait un partage familial qu'aucun des deux n'a voulu.
_NUMEROS = itertools.count(1)


def numero_de_test() -> str:
    return f"+225070000{next(_NUMEROS):04d}"


async def _semer_tenant(cle: str, nom: str, numero: str) -> UnTenant:
    """Un tenant complet : un établissement, une personne, deux années, un compte, ses affectations."""
    from datetime import date

    from modules.socle import annees, habilitations, tenants

    tenant_id = await tenants.creer_tenant(f"Tenant {nom}", PACKS_DE_TEST[cle])
    etablissement = await tenants.creer_etablissement(tenant_id, f"École {nom}", "Africa/Abidjan")
    personne = await personnes_creer(tenant_id, nom, LANGUES_DE_TEST[cle], numero)
    debut = date(date.today().year, 9, 1)
    annee = await annees.creer_annee(
        tenant_id, etablissement, "2026-2027", debut, date(debut.year + 1, 7, 31), "active"
    )
    annee_preparation = await annees.creer_annee(
        tenant_id,
        etablissement,
        "2027-2028",
        date(debut.year + 1, 9, 1),
        date(debut.year + 2, 7, 31),
        "preparation",
    )
    compte = await habilitations.semer_compte(tenant_id, personne, numero)
    for annee_id in (annee, annee_preparation):
        await habilitations.creer_affectation(
            tenant_id, compte, annee_id, etablissement, date.today(), None
        )
    await tenants.designer_administrateur(tenant_id, etablissement, compte)
    return UnTenant(
        tenant=tenant_id,
        etablissement=etablissement,
        personne=personne,
        compte=compte,
        numero=numero,
        annee=annee,
        annee_preparation=annee_preparation,
    )


async def personnes_creer(tenant_id: UUID, nom: str, langue: str, numero: str) -> UUID:
    from modules.socle import personnes

    return await personnes.creer_personne(tenant_id, f"Koné {nom}", "Awa", langue, numero)


@pytest_asyncio.fixture
async def tenants_ab(moteur_application: AsyncEngine, client: httpx.AsyncClient) -> DeuxTenants:
    """Deux tenants neufs et complets : neufs à chaque test, rien ne se partage.

    Les deux numéros sont distincts, et **neufs à chaque test** : un numéro se résout tous tenants
    confondus, et deux tests qui partageraient le leur se gêneraient. Le partage volontaire d'un
    numéro entre deux comptes est le sujet d'US8, et se sème dans le test qui l'étudie.
    """
    a = await _semer_tenant("a", "A", numero_de_test())
    b = await _semer_tenant("b", "B", numero_de_test())
    tenant_a, etab_a = a.tenant, a.etablissement
    tenant_b, etab_b = b.tenant, b.etablissement
    if SUSPENSION:
        # Le paramètre est posé par le service, pas par la route : une fixture prépare un état,
        # elle ne teste pas une route, et celle-ci exige désormais une session que la fixture
        # n'a pas encore ouverte (c'est `sessions_ab` qui le fait, et elle dépend de celle-ci).
        from modules.socle import tenants

        for tenant_id in (tenant_a, tenant_b):
            await tenants.poser_parametre(
                tenant_id, "assistance.suspendue", tenants.Portee.TENANT, tenant_id, True
            )
    return DeuxTenants(tenant_a, etab_a, tenant_b, etab_b, a, b)


@dataclass(frozen=True)
class DeuxSessions:
    """Une session ouverte par tenant, par l'API : jeton, cookies, compte."""

    a: object
    b: object


@pytest_asyncio.fixture
async def sessions_ab(client: httpx.AsyncClient, application, tenants_ab: DeuxTenants):
    """Ouvre une session par tenant **par l'API**, comme une personne le ferait.

    Rien n'est fabriqué à la main : la fixture demande un code, lit le message sur la passerelle
    simulée, et le vérifie. Une suite qui passerait par un jeton forgé ne prouverait pas que le
    parcours d'ouverture fonctionne, et c'est lui la première frontière de sécurité.
    """
    from tests.authentification.outils import ouvrir

    a = await ouvrir(client, application, tenants_ab.numero_a)
    b = await ouvrir(client, application, tenants_ab.numero_b)
    return DeuxSessions(a=a, b=b)
