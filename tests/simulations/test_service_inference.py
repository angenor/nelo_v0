"""US6 — le service d'inférence simulé : soumission, résultat différé, échec borné."""

import time
from datetime import timedelta

import pytest

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.socle.assistance.service_inference import RequeteInference, SimulationServiceInference

DELAI = timedelta(milliseconds=100)
DELAI_MAX = timedelta(milliseconds=200)
REQUETE = RequeteInference(capacite="C1_REDACTION_ASSISTEE", entree={"texte": "essai"})


@pytest.mark.parametrize(
    ("mode", "resultats"),
    [
        (ModeSimulation.SUCCES, 1),
        (ModeSimulation.ACCUSE_EN_RETARD, 1),
        (ModeSimulation.ACCUSE_EN_DOUBLE, 2),
        (ModeSimulation.JAMAIS_RECU, 0),
    ],
)
async def test_modes(mode, resultats):
    service = SimulationServiceInference(mode, DELAI)
    reference = await service.soumettre(REQUETE)
    recus = []
    debut = time.monotonic()
    for _ in range(3):
        resultat = await service.attendre_resultat(reference, DELAI_MAX)
        if resultat is None:
            break
        assert resultat.reference == reference
        recus.append(resultat)
    assert len(recus) == resultats
    if mode == ModeSimulation.JAMAIS_RECU:
        assert time.monotonic() - debut <= 0.25


async def test_indisponible():
    service = SimulationServiceInference(ModeSimulation.INDISPONIBLE, DELAI)
    with pytest.raises(DependanceIndisponible) as erreur:
        await service.soumettre(REQUETE)
    assert erreur.value.dependance == "SERVICE_INFERENCE"
