"""La politique de sécurité porte les valeurs de la spécification, et ne lit aucune configuration."""

import dataclasses
from datetime import timedelta

from modules.socle.habilitations.politique import POLITIQUE, PolitiqueSecurite

ATTENDUES = {
    "OTP_LONGUEUR": 6,
    "OTP_VALIDITE": timedelta(minutes=10),
    "OTP_TENTATIVES": 5,
    "OTP_RENVOI": timedelta(seconds=60),
    "OTP_PAR_HEURE_PAR_NUMERO": 5,
    "OTP_PAR_HEURE_PAR_CLIENT": 20,
    "PIN_LONGUEUR": 4,
    "DISPENSE_PIN_COURANT": timedelta(minutes=10),
    "FENETRE_CONCURRENCE_REFRESH": timedelta(seconds=10),
    "JETON_ACCES": timedelta(minutes=60),
}


def test_chaque_valeur_est_celle_de_la_specification():
    for nom, valeur in ATTENDUES.items():
        assert getattr(POLITIQUE, nom) == valeur, nom


def test_aucune_constante_n_est_oubliee():
    declarees = {champ.name for champ in dataclasses.fields(PolitiqueSecurite)}
    assert declarees == set(ATTENDUES)


def test_la_politique_est_gelee():
    import pytest

    with pytest.raises(dataclasses.FrozenInstanceError):
        POLITIQUE.OTP_LONGUEUR = 4  # type: ignore[misc]


def test_le_module_ne_lit_aucune_configuration():
    """Ni `os.environ`, ni `Configuration` : ce sont des choix de produit, pas de déploiement."""
    import ast
    import pathlib

    source = pathlib.Path(
        modules_politique := __import__(
            "modules.socle.habilitations.politique", fromlist=["politique"]
        ).__file__
    ).read_text(encoding="utf-8")
    assert modules_politique is not None
    arbre = ast.parse(source)
    importes = {
        noeud.module
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.ImportFrom) and noeud.module
    } | {
        alias.name
        for noeud in ast.walk(arbre)
        if isinstance(noeud, ast.Import)
        for alias in noeud.names
    }
    assert importes <= {"dataclasses", "datetime"}
