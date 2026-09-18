"""La configuration du processus — variables d'environnement préfixées `NELO_`, `.env` en secours."""

from datetime import timedelta
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

from modules.shared import ModeSimulation

RACINE = Path(__file__).resolve().parents[1]


class Configuration(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NELO_", env_file=RACINE / ".env", extra="ignore")

    # Le secret de signature des jetons d'accès : **aucun défaut**. Un serveur sans
    # NELO_SECRET_JETON ne démarre pas, plutôt que de signer avec une valeur connue de tous.
    secret_jeton: str
    # L'indicatif proposé avant toute session (FR-002) : une donnée de déploiement, jamais une
    # littérale de pays dans le code (principe V).
    indicatif_defaut: str
    # Levé en développement local sur http://localhost, jamais en production.
    cookies_secure: bool = True
    nom_produit: str = "Nelo"
    url_publique: str = "http://localhost:3000"
    # Un journal des messages courts en simulation, pour le développement et les tests seulement.
    sms_journal: Path | None = None
    # L'adresse du mandataire inverse dont X-Forwarded-For fait foi ; sans lui, l'adresse du
    # client est celle de la connexion (research.md R-05).
    relais_de_confiance: str | None = None

    bd_url: str = "postgresql+asyncpg://nelo_app:nelo_app@localhost:5432/nelo"
    bd_url_proprietaire: str = (
        "postgresql+asyncpg://nelo_proprietaire:nelo_proprietaire@localhost:5432/nelo"
    )
    bd_nom: str | None = None
    bd_taille_pool: int = 5
    valkey_url: str = "valkey://localhost:6379/0"

    travailleur_intervalle_ms: int = 500
    travailleur_delai_orphelin_ms: int = 300_000
    travailleur_taille_lot: int = 50
    travailleur_delai_arret_ms: int = 10_000

    simulation_sms_mode: ModeSimulation = ModeSimulation.SUCCES
    simulation_paiement_mode: ModeSimulation = ModeSimulation.SUCCES
    simulation_inference_mode: ModeSimulation = ModeSimulation.SUCCES
    simulation_delai_ms: int = 100

    @property
    def bd_url_application(self) -> str:
        """L'URL du rôle nelo_app, dont la base est surchargée par NELO_BD_NOM s'il est posé."""
        url = make_url(self.bd_url)
        if self.bd_nom:
            url = url.set(database=self.bd_nom)
        return url.render_as_string(hide_password=False)

    @property
    def travailleur_intervalle(self) -> timedelta:
        return timedelta(milliseconds=self.travailleur_intervalle_ms)

    @property
    def travailleur_delai_arret(self) -> timedelta:
        return timedelta(milliseconds=self.travailleur_delai_arret_ms)

    @property
    def travailleur_delai_orphelin(self) -> timedelta:
        return timedelta(milliseconds=self.travailleur_delai_orphelin_ms)

    @property
    def simulation_delai(self) -> timedelta:
        return timedelta(milliseconds=self.simulation_delai_ms)
