"""US6 : la passerelle SMS simulée réussit, sait échouer comme la vraie, et garde ses envois.

Ce qu'elle garde sert aux tests (`envoyes`) et aux parcours de bout en bout (le journal, lu par
Playwright). Le journal est un chemin de développement et de test ; sans lui, rien ne s'écrit.
"""

import json
import time
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from modules.shared import DependanceIndisponible, ModeSimulation
from modules.socle.communication import EnvoiSimule, SimulationPasserelleSms

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


async def test_les_envoyes_gardent_destinataire_et_texte():
    passerelle = SimulationPasserelleSms(ModeSimulation.SUCCES, DELAI)
    reference = uuid.uuid7()
    envoi = await passerelle.envoyer("+2250700000001", "Votre code Nelo : 123456", reference)

    assert len(passerelle.envoyes) == 1
    garde = passerelle.envoyes[0]
    assert isinstance(garde, EnvoiSimule)
    assert garde.destinataire_e164 == "+2250700000001"
    assert garde.texte == "Votre code Nelo : 123456"
    assert garde.reference == envoi
    assert garde.envoye_le.tzinfo is not None
    assert garde.envoye_le <= datetime.now(UTC)

    await passerelle.envoyer("+2250700000002", "Votre code Nelo : 654321", uuid.uuid7())
    assert [e.destinataire_e164 for e in passerelle.envoyes] == [
        "+2250700000001",
        "+2250700000002",
    ]


async def test_le_journal_s_ecrit_quand_le_chemin_est_pose(tmp_path):
    chemin = tmp_path / "sms.jsonl"
    passerelle = SimulationPasserelleSms(ModeSimulation.SUCCES, DELAI, chemin)
    reference = uuid.uuid7()
    await passerelle.envoyer("+2250700000001", "Votre code Nelo : 123456", reference)
    await passerelle.envoyer("+2250700000002", "Votre code Nelo : 654321", uuid.uuid7())

    lignes = [json.loads(ligne) for ligne in chemin.read_text(encoding="utf-8").splitlines()]
    assert len(lignes) == 2
    assert lignes[0]["destinataire"] == "+2250700000001"
    assert lignes[0]["texte"] == "Votre code Nelo : 123456"
    assert lignes[0]["reference"] == str(reference)
    assert datetime.fromisoformat(lignes[0]["envoye_le"]).tzinfo is not None
    assert lignes[1]["destinataire"] == "+2250700000002"


async def test_aucun_journal_sans_chemin(tmp_path):
    chemin = tmp_path / "sms.jsonl"
    passerelle = SimulationPasserelleSms(ModeSimulation.SUCCES, DELAI)
    await passerelle.envoyer("+2250700000001", "Votre code Nelo : 123456", uuid.uuid7())
    assert not chemin.exists()
    assert list(tmp_path.iterdir()) == []


async def test_un_envoi_refuse_ne_laisse_aucune_trace(tmp_path):
    chemin = tmp_path / "sms.jsonl"
    passerelle = SimulationPasserelleSms(ModeSimulation.INDISPONIBLE, DELAI, chemin)
    with pytest.raises(DependanceIndisponible):
        await passerelle.envoyer("+2250700000001", "Votre code Nelo : 123456", uuid.uuid7())
    assert passerelle.envoyes == []
    assert not chemin.exists()
