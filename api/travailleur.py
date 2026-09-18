"""Le travailleur d'événements : une tâche `asyncio` dans le processus du serveur (research.md R-09).

Sa boucle : lister les tenants, et pour chacun, **module par module**, reprendre les orphelins et
les échecs, puis consommer un lot dans l'ordre d'écriture. Chaque module porte sa propre table
d'outbox et expose `consommer_lot` et `reprendre_evenements` sur elle : le travailleur ne connaît
pas les tables, seulement les modules qui en ont une.

Livraison au moins une fois : un consommateur doit savoir qu'un événement peut lui arriver deux
fois. **Aucune file de messages, aucun autre processus.**
"""

import asyncio
import contextlib
import logging
from uuid import UUID

from api.configuration import Configuration
from modules.shared import Evenement
from modules.shared import outbox as outbox_partagee
from modules.socle import habilitations, tenants

# Les modules qui portent une table d'outbox. `personnes` et `annees` en ont une, vide en T1a :
# elle existe pour que P-01 et le travailleur les traitent comme les autres, et pour que la
# tranche qui y écrira n'ait rien à changer ici.
MODULES_AVEC_OUTBOX = (tenants, habilitations)

journal = logging.getLogger("nelo.travailleur")


async def consommateur_journal(tenant_id: UUID, evenement_id: UUID, evenement: Evenement) -> None:
    journal.info(
        "événement %s (%s) du tenant %s : %s",
        evenement.type,
        evenement_id,
        tenant_id,
        evenement.charge,
    )


class Travailleur:
    def __init__(
        self,
        configuration: Configuration,
        consommateur: outbox_partagee.Consommateur = consommateur_journal,
    ) -> None:
        self.configuration = configuration
        self.consommateur = consommateur
        self._tache: asyncio.Task | None = None
        self._arret = asyncio.Event()

    async def un_tour(self) -> int:
        return await self.un_tour_de(await tenants.tenants_pour_travailleur())

    async def un_tour_de(self, tenants_a_parcourir: list[UUID]) -> int:
        """Le tour, borné aux tenants donnés. `un_tour` les prend tous ; les tests en nomment un."""
        traites = 0
        for tenant_id in tenants_a_parcourir:
            for module in MODULES_AVEC_OUTBOX:
                await module.reprendre_evenements(
                    tenant_id, self.configuration.travailleur_delai_orphelin
                )
                traites += await module.consommer_lot(
                    tenant_id, self.consommateur, self.configuration.travailleur_taille_lot
                )
        return traites

    async def _boucle(self) -> None:
        # L'arrêt est demandé par un signal, jamais par une annulation : un tour commencé se
        # termine, pour qu'un événement passé au consommateur soit marqué avant que le processus
        # ne s'éteigne. Annulé entre les deux, il resterait `pris` jusqu'au délai des orphelins.
        while not self._arret.is_set():
            try:
                await self.un_tour()
            except asyncio.CancelledError:
                raise
            except Exception:
                journal.exception("tour du travailleur d'événements en échec")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(
                    self._arret.wait(), self.configuration.travailleur_intervalle.total_seconds()
                )

    async def demarrer(self) -> None:
        if self._tache is None:
            self._arret.clear()
            self._tache = asyncio.create_task(self._boucle(), name="travailleur-evenements")
            journal.info("travailleur d'événements démarré")

    async def arreter(self) -> None:
        """Signale l'arrêt et attend la fin du tour en cours ; n'annule qu'au-delà du délai d'arrêt."""
        if self._tache is not None:
            self._arret.set()
            try:
                await asyncio.wait_for(
                    self._tache, self.configuration.travailleur_delai_arret.total_seconds()
                )
            except TimeoutError:
                journal.warning("travailleur d'événements : tour trop long à l'arrêt, annulé")
                self._tache.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._tache
            self._tache = None
            journal.info("travailleur d'événements arrêté")
