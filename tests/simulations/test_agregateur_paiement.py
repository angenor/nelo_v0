"""US6 — l'agrégateur de paiement simulé : montant entier d'unité mineure, confirmation différée."""

import inspect
import time
import uuid
from datetime import timedelta

import pytest

from modules.metier.finance import AgregateurPaiement, SimulationAgregateurPaiement
from modules.shared import DependanceIndisponible, ModeSimulation

DELAI = timedelta(milliseconds=100)
DELAI_MAX = timedelta(milliseconds=200)


async def initier(mode):
    agregateur = SimulationAgregateurPaiement(mode, DELAI)
    paiement = await agregateur.initier(150_000, "XOF", uuid.uuid7(), "+2250700000000")
    return agregateur, paiement


def test_le_montant_est_un_entier_d_unite_mineure():
    parametre = inspect.signature(AgregateurPaiement.initier).parameters["montant_unite_mineure"]
    assert parametre.annotation in (int, "int")


async def test_un_flottant_est_refuse():
    agregateur = SimulationAgregateurPaiement(ModeSimulation.SUCCES, DELAI)
    with pytest.raises(TypeError):
        await agregateur.initier(1500.50, "XOF", uuid.uuid7(), "+2250700000000")


@pytest.mark.parametrize(
    ("mode", "confirmations"),
    [
        (ModeSimulation.SUCCES, 1),
        (ModeSimulation.ACCUSE_EN_RETARD, 1),
        (ModeSimulation.ACCUSE_EN_DOUBLE, 2),
        (ModeSimulation.JAMAIS_RECU, 0),
    ],
)
async def test_modes(mode, confirmations):
    agregateur, paiement = await initier(mode)
    recues = []
    debut = time.monotonic()
    for _ in range(3):
        confirmation = await agregateur.attendre_confirmation(paiement, DELAI_MAX)
        if confirmation is None:
            break
        assert confirmation.reference == paiement
        recues.append(confirmation)
    assert len(recues) == confirmations
    if mode == ModeSimulation.ACCUSE_EN_RETARD:
        assert time.monotonic() - debut >= 0.05
    if mode == ModeSimulation.JAMAIS_RECU:
        assert time.monotonic() - debut <= 0.25


async def test_indisponible():
    agregateur = SimulationAgregateurPaiement(ModeSimulation.INDISPONIBLE, DELAI)
    with pytest.raises(DependanceIndisponible) as erreur:
        await agregateur.initier(100, "XOF", uuid.uuid7(), "+2250700000000")
    assert erreur.value.dependance == "AGREGATEUR_PAIEMENT"
