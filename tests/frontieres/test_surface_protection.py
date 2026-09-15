"""US4 — P-11, surface : le module cloisonné n'expose que son interface de service."""

import ast
import inspect
from pathlib import Path

from sqlalchemy import MetaData, Table
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

import modules.metier.protection as protection

PREFIXES_ACCES = ("lire_", "inserer_", "upsert_", "prendre_", "marquer_")


def test_all_ne_contient_que_l_interface():
    assert protection.__all__ == ["ServiceProtection"]


def test_aucun_attribut_public_n_est_un_acces_aux_donnees():
    for nom, valeur in vars(protection).items():
        if nom.startswith("_"):
            continue
        assert not isinstance(valeur, (Table, MetaData, Engine, AsyncEngine)), nom
        if inspect.isfunction(valeur):
            assert not nom.startswith(PREFIXES_ACCES), nom


def test_n_importe_pas_le_moteur():
    dossier = Path(protection.__file__).parent
    for chemin in dossier.rglob("*.py"):
        for noeud in ast.walk(ast.parse(chemin.read_text(encoding="utf-8"))):
            if isinstance(noeud, ast.ImportFrom) and noeud.module:
                assert noeud.module != "modules.shared.bd", chemin
                assert not (
                    noeud.module == "modules.shared" and any(a.name == "bd" for a in noeud.names)
                ), chemin
            if isinstance(noeud, ast.Import):
                assert all(a.name != "modules.shared.bd" for a in noeud.names), chemin
