"""US6 — la passerelle SMS simulée réussit, et sait échouer comme la vraie."""

import time
import uuid
from datetime import timedelta

import pytest

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.socle.communication import SimulationPasserelleSms

DELAI = timedelta(milliseconds=100)
DELAI_MAX = timedelta(milliseconds=200)


async def envoyer(mode):
    passerelle = SimulationPasserelleSms(mode, DELAI)
    envoi = await passerelle.envoyer("+2250700000000", "Rappel", uuid.uuid7())
    return passerelle, envoi


async def test_succes():
    passerelle, envoi = await envoyer(ModeSimulation.SUCCES)
    debut = time.monotonic()
    accuse = await passerelle.attendre_accuse(envoi, DELAI_MAX)
    assert accuse is not None and accuse.statut == "REMIS"
    assert accuse.reference == envoi
    assert time.monotonic() - debut < 0.05


async def test_accuse_en_retard():
    passerelle, envoi = await envoyer(ModeSimulation.ACCUSE_EN_RETARD)
    assert await passerelle.attendre_accuse(envoi, timedelta(milliseconds=20)) is None
    debut = time.monotonic()
    accuse = await passerelle.attendre_accuse(envoi, DELAI_MAX)
    assert accuse is not None and accuse.statut == "REMIS"
    assert time.monotonic() - debut >= 0.05


async def test_accuse_en_double():
    passerelle, envoi = await envoyer(ModeSimulation.ACCUSE_EN_DOUBLE)
    premier = await passerelle.attendre_accuse(envoi, DELAI_MAX)
    second = await passerelle.attendre_accuse(envoi, DELAI_MAX)
    assert premier is not None and second is not None
    assert premier.reference == second.reference == envoi


async def test_jamais_recu_ne_bloque_pas():
    passerelle, envoi = await envoyer(ModeSimulation.JAMAIS_RECU)
    debut = time.monotonic()
    assert await passerelle.attendre_accuse(envoi, DELAI_MAX) is None
    assert time.monotonic() - debut <= 0.25


async def test_indisponible():
    passerelle = SimulationPasserelleSms(ModeSimulation.INDISPONIBLE, DELAI)
    with pytest.raises(DependanceIndisponible) as erreur:
        await passerelle.envoyer("+2250700000000", "Rappel", uuid.uuid7())
    assert erreur.value.dependance == "PASSERELLE_SMS"
