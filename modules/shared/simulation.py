"""Les modes d'une dépendance externe simulée : un succès, et les quatre manières d'échouer.

Une simulation doit savoir échouer aussi bien que réussir (docs/01-stack.md § 3) : l'accusé
différé est le cas nominal, l'accusé en double et l'accusé jamais reçu aussi.
"""

import asyncio
import time
from collections.abc import Hashable
from datetime import timedelta
from enum import StrEnum


class ModeSimulation(StrEnum):
    SUCCES = "SUCCES"
    ACCUSE_EN_RETARD = "ACCUSE_EN_RETARD"
    ACCUSE_EN_DOUBLE = "ACCUSE_EN_DOUBLE"
    JAMAIS_RECU = "JAMAIS_RECU"
    INDISPONIBLE = "INDISPONIBLE"


class AccusesSimules[T]:
    """Les accusés que la simulation livrera pour chaque référence, et quand.

    `annoncer` programme les accusés d'un envoi selon le mode ; `attendre` rend le prochain dès
    qu'il est disponible, ou `None` à l'échéance — jamais de blocage au-delà de `delai_max`.
    """

    def __init__(self, mode: ModeSimulation, delai: timedelta) -> None:
        self.mode = mode
        self.delai = delai
        self._files: dict[Hashable, list[tuple[float, T]]] = {}

    def annoncer(self, reference: Hashable, accuse: T) -> None:
        maintenant = time.monotonic()
        match self.mode:
            case ModeSimulation.SUCCES:
                prevus = [(maintenant, accuse)]
            case ModeSimulation.ACCUSE_EN_RETARD:
                prevus = [(maintenant + self.delai.total_seconds(), accuse)]
            case ModeSimulation.ACCUSE_EN_DOUBLE:
                prevus = [(maintenant, accuse), (maintenant, accuse)]
            case _:
                prevus = []
        self._files[reference] = prevus

    async def attendre(self, reference: Hashable, delai_max: timedelta) -> T | None:
        echeance = time.monotonic() + delai_max.total_seconds()
        file = self._files.get(reference, [])
        if not file:
            await asyncio.sleep(max(0.0, echeance - time.monotonic()))
            return None
        disponible_le, accuse = file[0]
        if disponible_le > echeance:
            await asyncio.sleep(max(0.0, echeance - time.monotonic()))
            return None
        await asyncio.sleep(max(0.0, disponible_le - time.monotonic()))
        file.pop(0)
        return accuse
