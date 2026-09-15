"""Le travailleur d'événements — une tâche `asyncio` dans le processus du serveur (research.md R-09).

Sa boucle : lister les tenants, et pour chacun reprendre les orphelins et les échecs, puis
consommer un lot dans l'ordre d'écriture. Livraison au moins une fois : un consommateur doit
savoir qu'un événement peut lui arriver deux fois. **Aucune file de messages, aucun autre
processus.** Le consommateur de T0a est le journal applicatif.
"""

import asyncio
import contextlib
import logging
from uuid import UUID

from api.configuration import Configuration
from modules.shared import Evenement
from modules.socle import tenants

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
        consommateur: tenants.Consommateur = consommateur_journal,
    ) -> None:
        self.configuration = configuration
        self.consommateur = consommateur
        self._tache: asyncio.Task | None = None

    async def un_tour(self) -> int:
        traites = 0
        for tenant_id in await tenants.tenants_pour_travailleur():
            await tenants.reprendre_evenements(
                tenant_id, self.configuration.travailleur_delai_orphelin
            )
            traites += await tenants.consommer_lot(
                tenant_id, self.consommateur, self.configuration.travailleur_taille_lot
            )
        return traites

    async def _boucle(self) -> None:
        while True:
            try:
                await self.un_tour()
            except asyncio.CancelledError:
                raise
            except Exception:
                journal.exception("tour du travailleur d'événements en échec")
            await asyncio.sleep(self.configuration.travailleur_intervalle.total_seconds())

    async def demarrer(self) -> None:
        if self._tache is None:
            self._tache = asyncio.create_task(self._boucle(), name="travailleur-evenements")
            journal.info("travailleur d'événements démarré")

    async def arreter(self) -> None:
        if self._tache is not None:
            self._tache.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._tache
            self._tache = None
            journal.info("travailleur d'événements arrêté")
